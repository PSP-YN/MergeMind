import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from urllib.parse import urlencode, urlparse, urlunparse
from uuid import uuid4

import httpx
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosed, InvalidStatus

from backend.app.core.config import settings

logger = logging.getLogger(__name__)
MessageHandler = Callable[[dict, "SwitchAgentClient"], Awaitable[None]]


def websocket_url(base_url: str, agent_id: str, query: dict[str, str]) -> str:
    parsed = urlparse(base_url.rstrip("/"))
    scheme = "wss" if parsed.scheme == "https" else "ws"
    path = parsed.path.rstrip("/") + f"/agents/{agent_id}/connection/ws"
    return urlunparse((scheme, parsed.netloc, path, "", urlencode(query), ""))


class SwitchProtocolError(RuntimeError):
    pass


class SwitchAgentClient:
    def __init__(
        self,
        *,
        base_url: str,
        agent_id: str,
        api_key: str,
        room_id: str,
        handler: MessageHandler,
    ):
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        self.api_key = api_key
        self.room_id = room_id
        self.handler = handler
        self.connection_id = str(uuid4())
        self.cursor = 0
        self.generation: int | None = None
        self.ready = asyncio.Event()
        self.stopped = asyncio.Event()
        self._handler_lock = asyncio.Semaphore(1)
        self._first_connect = True

    async def operation(self, name: str, arguments: dict) -> dict:
        if not self.connection_id:
            raise SwitchProtocolError("Switch connection is not ready")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Switch-Connection-Id": self.connection_id,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/agents/{self.agent_id}/ops/{name}",
                headers=headers,
                json=arguments,
            )
            if response.is_error:
                detail = response.text[:1000]
                raise SwitchProtocolError(f"Switch operation {name} failed ({response.status_code}): {detail}")
            data = response.json()
            return data.get("result", data)

    async def send_targeted(self, role_name: str, body: str) -> dict:
        return await self.operation(
            "send_targeted_message",
            {"body": body, "target_names": [role_name]},
        )

    async def post_message(self, body: str) -> dict:
        return await self.operation("post_message", {"body": body})

    async def _handle_event(self, frame: dict) -> None:
        event_id = frame.get("id")
        if isinstance(event_id, int):
            self.cursor = max(self.cursor, event_id)
        event = frame.get("event")
        data = frame.get("data") or {}
        if event == "connection_state":
            self.generation = data.get("generation")
            self.ready.set()
            return
        if event == "ping":
            # Heartbeats are handled in the reader loop, never behind an LLM call.
            return
        if event == "evicted":
            code = (data or {}).get("code")
            if code == "taken_over":
                self.stopped.set()
                raise SwitchProtocolError("Switch connection was taken over by another client")
            raise SwitchProtocolError(f"Switch evicted the connection: {code or 'unknown'}")
        if event == "refused":
            raise SwitchProtocolError(f"Switch refused the connection: {json.dumps(data)[:1000]}")
        if event != "message":
            return
        payload = data.get("payload") or {}
        if payload.get("addressed") is not True:
            return
        async with self._handler_lock:
            await self.handler(payload, self)

    async def run_forever(self) -> None:
        while not self.stopped.is_set():
            query = {
                "connection_id": self.connection_id,
                "scope": "single",
                "filter": "all",
                "start_from": "head" if self._first_connect else str(self.cursor),
                "rooms": self.room_id,
                "client": "mergemind",
                "client_version": "0.1.0",
            }
            if self.generation is not None:
                query["expected_generation"] = str(self.generation)
            url = websocket_url(self.base_url, self.agent_id, query)
            try:
                async with connect(
                    url,
                    additional_headers={"Authorization": f"Bearer {self.api_key}"},
                    open_timeout=15,
                    ping_interval=None,
                    close_timeout=5,
                    max_size=2_000_000,
                ) as socket:
                    self._first_connect = False
                    async for raw in socket:
                        try:
                            frame = json.loads(raw)
                        except (TypeError, json.JSONDecodeError):
                            logger.warning("Ignored malformed Switch frame for %s", self.agent_id)
                            continue
                        if frame.get("event") == "ping":
                            await socket.send(json.dumps({"type": "pong", "cursor": self.cursor}))
                            continue
                        await self._handle_event(frame)
            except asyncio.CancelledError:
                raise
            except SwitchProtocolError as exc:
                if self.stopped.is_set():
                    break
                logger.warning("Switch worker %s: %s", self.agent_id, exc)
                self.ready.clear()
                if "taken over" in str(exc).lower():
                    break
            except (ConnectionClosed, InvalidStatus, OSError, TimeoutError, httpx.HTTPError) as exc:
                logger.info("Switch connection for %s interrupted: %s", self.agent_id, exc)
                self.ready.clear()
            except Exception:
                logger.exception("Unexpected Switch worker error for %s", self.agent_id)
                self.ready.clear()
            if not self.stopped.is_set():
                await asyncio.sleep(settings.switch_reconnect_seconds)

    async def stop(self) -> None:
        self.stopped.set()
        self.ready.clear()
