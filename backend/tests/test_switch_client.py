import asyncio

from backend.app.switch.client import SwitchAgentClient


def test_addressed_event_is_acknowledged_only_after_handler_finishes():
    async def run():
        started = asyncio.Event()
        release = asyncio.Event()
        saved = []

        async def handler(payload, client):
            started.set()
            await release.wait()

        client = SwitchAgentClient(
            base_url="https://switch.example",
            agent_id="agent-1",
            api_key="test-key",
            room_id="room-1",
            handler=handler,
            state_callback=lambda connection_id, cursor, generation: saved.append(
                (connection_id, cursor, generation)
            ),
        )
        await client._handle_event(
            {"event": "connection_state", "data": {"generation": 7, "cursor": 10}}
        )
        consumer = asyncio.create_task(client._consume_events())
        await client._handle_event(
            {
                "event": "message",
                "id": 11,
                "data": {"payload": {"addressed": True, "body": "work"}},
            }
        )
        await started.wait()
        assert client.cursor == 10
        release.set()
        await client._event_queue.join()
        assert client.cursor == 11
        assert saved[-1] == (client.connection_id, 11, 7)
        consumer.cancel()
        await asyncio.gather(consumer, return_exceptions=True)

    asyncio.run(run())


def test_unaddressed_room_messages_advance_cursor_without_running_agent():
    async def run():
        handled = []

        async def handler(payload, client):
            handled.append(payload)

        client = SwitchAgentClient(
            base_url="https://switch.example",
            agent_id="agent-1",
            api_key="test-key",
            room_id="room-1",
            handler=handler,
            runtime_state={"connection_id": "stable-id", "cursor": 20, "generation": 4},
        )
        assert client.connection_id == "stable-id"
        assert client._first_connect is False
        consumer = asyncio.create_task(client._consume_events())
        await client._handle_event(
            {
                "event": "message",
                "id": 21,
                "data": {"payload": {"addressed": False, "body": "not for this agent"}},
            }
        )
        await client._event_queue.join()
        assert client.cursor == 21
        assert handled == []
        consumer.cancel()
        await asyncio.gather(consumer, return_exceptions=True)

    asyncio.run(run())



def test_switch_runtime_cursor_is_persisted_for_process_restarts():
    from backend.app.core.store import store

    store.delete_all()
    store.save_switch_runtime("planner", "persistent-connection", 987, 12)
    assert store.get_switch_runtime("planner") == {
        "connection_id": "persistent-connection",
        "cursor": 987,
        "generation": 12,
    }


def test_switch_event_gap_stops_agent_instead_of_skipping_messages():
    async def run():
        async def handler(payload, client):
            return None

        client = SwitchAgentClient(
            base_url="https://switch.example",
            agent_id="agent-1",
            api_key="test-key",
            room_id="room-1",
            handler=handler,
        )
        try:
            await client._handle_event({"event": "gap", "data": {"reason": "expired"}})
            assert False, "expected SwitchProtocolError"
        except Exception as exc:
            assert "event gap" in str(exc)
            assert client.stopped.is_set()

    asyncio.run(run())
