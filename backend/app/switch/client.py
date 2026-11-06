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
StateCallback = Callable[[str, int, int | None], None]


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
        runtime_state: dict | None = None,
        state_callback: StateCallback | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        self.api_key = api_key
        self.room_id = room_id
        self.handler = handler
        runtime_state = runtime_state or {}
        self.connection_id = runtime_state.get("connection_id") or str(uuid4())
        self.cursor = int(runtime_state.get("cursor") or 0)
        self.generation = runtime_state.get("generation")
        self._first_connect = not bool(runtime_state.get("connection_id"))
        self._state_callback = state_callback
        self.ready = asyncio.Event()
        self.stopped = asyncio.Event()
        self._event_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=256)
        self._queued_ids: set[int] = set()
        self._socket = None

    def _persist_state(self) -> None:
        if self._state_callback is None:
            return
        try:
            self._state_callback(self.connection_id, self.cursor, self.generation)
        except Exception:
            logger.exception("Could not persist Switch cursor for %s", self.agent_id)

    async def operation(self, name: str, arguments: dict) -> dict:
        if self.stopped.is_set():
            raise SwitchProtocolError("This Switch agent connection has been stopped")
        if not self.ready.is_set():
            try:
                await asyncio.wait_for(self.ready.wait(), timeout=30)
            except TimeoutError as exc:
                raise SwitchProtocolError("Switch agent connection did not recover in time") from exc
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
        event = frame.get("event")
        data = frame.get("data") or {}
        if event == "connection_state":
            self.generation = data.get("generation")
            server_cursor = data.get("cursor")
            if isinstance(server_cursor, int):
                self.cursor = max(self.cursor, server_cursor)
            self.ready.set()
            self._persist_state()
            return
        if event == "ping":
            return
        if event == "evicted":
            code = data.get("code")
            if code == "taken_over":
                self.stopped.set()
                raise SwitchProtocolError("Switch connection was taken over by another client")
            raise SwitchProtocolError(f"Switch evicted the connection: {code or 'unknown'}")
        if event == "refused":
            detail = json.dumps(data)
            if "taken_over" in detail:
                self.stopped.set()
            raise SwitchProtocolError(f"Switch refused the connection: {detail[:1000]}")
        if event == "gap":
            self.stopped.set()
            raise SwitchProtocolError("Switch reported an event gap; stopped rather than silently skipping work")
        if event == "room_released":
            self.stopped.set()
            raise SwitchProtocolError("Switch released this agent's room claim")
        event_id = frame.get("id")
        if isinstance(event_id, int):
            if event_id <= self.cursor or event_id in self._queued_ids:
                return
        try:
            self._event_queue.put_nowait(frame)
        except asyncio.QueueFull as exc:
            raise SwitchProtocolError("Switch event backlog exceeded the local queue; reconnecting from the last processed cursor") from exc
        if isinstance(event_id, int):
            self._queued_ids.add(event_id)

    async def _consume_events(self) -> None:
        while not self.stopped.is_set():
            frame = await self._event_queue.get()
            event_id = frame.get("id")
            try:
                if frame.get("event") == "message":
                    payload = (frame.get("data") or {}).get("payload") or {}
                    if payload.get("addressed") is True:
                        # The reader remains free to answer Switch pings while an LLM call runs.
                        await self.handler(payload, self)
                if isinstance(event_id, int):
                    self.cursor = max(self.cursor, event_id)
                    self._persist_state()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Message handler failed for Switch agent %s; stopping to preserve the cursor", self.agent_id)
                self.stopped.set()
                self.ready.clear()
                if self._socket is not None:
                    await self._socket.close(code=1011, reason="MergeMind handler failed")
                return
            finally:
                if isinstance(event_id, int):
                    self._queued_ids.discard(event_id)
                self._event_queue.task_done()

    async def run_forever(self) -> None:
        consumer = asyncio.create_task(self._consume_events(), name=f"switch-events-{self.agent_id}")
        try:
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
                        self._socket = socket
                        async for raw in socket:
                            try:
                                frame = json.loads(raw)
                            except (TypeError, json.JSONDecodeError):
                                logger.warning("Ignored malformed Switch frame for %s", self.agent_id)
                                continue
                            if frame.get("event") == "ping":
                                # Answer immediately, independently of queued LLM work.
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
                except (ConnectionClosed, InvalidStatus, OSError, TimeoutError, httpx.HTTPError) as exc:
                    logger.info("Switch connection for %s interrupted: %s", self.agent_id, exc)
                    self.ready.clear()
                except Exception:
                    logger.exception("Unexpected Switch worker error for %s", self.agent_id)
                    self.ready.clear()
                finally:
                    self._socket = None
                if not self.stopped.is_set():
                    await asyncio.sleep(settings.switch_reconnect_seconds)
        finally:
            consumer.cancel()
            await asyncio.gather(consumer, return_exceptions=True)
            self.ready.clear()

    async def stop(self) -> None:
        self.stopped.set()
        self.ready.clear()
        if self._socket is not None:
            await self._socket.close()
