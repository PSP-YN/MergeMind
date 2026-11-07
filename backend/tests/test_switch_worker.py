import asyncio

import backend.app.switch.worker as worker
from backend.app.switch.worker import AgentWorkerManager


class FakeClient:
    def __init__(self):
        self.ready = asyncio.Event()
        self.ready.set()


def test_dispatch_enters_coordinator_locally_before_switch_handoff(monkeypatch):
    manager = AgentWorkerManager()
    client = FakeClient()
    manager.clients["coordinator"] = client
    calls = []

    async def fake_handle(role, event, received_client):
        calls.append((role, event["body"], received_client))

    monkeypatch.setattr(worker, "handle_agent_message", fake_handle)

    asyncio.run(manager.dispatch_task("MERGEMIND/1\n{\"stage\":\"task\",\"workflow_id\":\"demo\"}"))

    assert calls == [
        (
            "coordinator",
            "MERGEMIND/1\n{\"stage\":\"task\",\"workflow_id\":\"demo\"}",
            client,
        )
    ]
