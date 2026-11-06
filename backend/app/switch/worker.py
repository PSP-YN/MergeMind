import asyncio
import logging

from backend.app.core.store import store
from backend.app.switch.client import SwitchAgentClient
from backend.app.workflow_engine import handle_agent_message

logger = logging.getLogger(__name__)


class AgentWorkerManager:
    def __init__(self):
        self.clients: dict[str, SwitchAgentClient] = {}
        self.tasks: dict[str, asyncio.Task] = {}

    async def start(self) -> None:
        base_url = store.get_setting("switch_base_url")
        room_id = store.get_setting("switch_room_id")
        agents = store.get_switch_agents()
        if not base_url or not room_id or not agents:
            return
        for agent in agents:
            role = agent["role"]
            if role in self.tasks and not self.tasks[role].done():
                continue
            async def handler(payload, client, role_name=role):
                await handle_agent_message(role_name, payload, client)
            client = SwitchAgentClient(
                base_url=base_url,
                agent_id=agent["agent_id"],
                api_key=agent["api_key"],
                room_id=room_id,
                handler=handler,
            )
            self.clients[role] = client
            self.tasks[role] = asyncio.create_task(client.run_forever(), name=f"switch-{role}")
        logger.info("Started %d MergeMind Switch agent workers", len(self.clients))

    async def stop(self) -> None:
        for client in self.clients.values():
            await client.stop()
        for task in self.tasks.values():
            task.cancel()
        if self.tasks:
            await asyncio.gather(*self.tasks.values(), return_exceptions=True)
        self.clients.clear()
        self.tasks.clear()

    async def restart(self) -> None:
        await self.stop()
        await self.start()

    async def dispatch_task(self, handoff: str) -> None:
        client = self.clients.get("coordinator")
        if client is None:
            raise RuntimeError("Coordinator agent is not configured. Register Switch agents first.")
        try:
            await asyncio.wait_for(client.ready.wait(), timeout=20)
        except TimeoutError as exc:
            raise RuntimeError("Coordinator is not connected to the selected Switch room yet.") from exc
        await client.send_targeted("mergemind-coordinator", handoff)

    def status(self) -> dict:
        return {
            role: {
                "name": client.agent_id,
                "connected": client.ready.is_set(),
                "connection_id": client.connection_id,
            }
            for role, client in self.clients.items()
        }


worker_manager = AgentWorkerManager()
