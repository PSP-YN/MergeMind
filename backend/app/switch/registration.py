from urllib.parse import urlparse

import httpx

from backend.app.agents.registry import AGENTS
from backend.app.core.store import store


class SwitchRegistrationError(RuntimeError):
    pass


async def register_mergemind_agents(base_url: str, registration_key: str, room_id: str) -> dict:
    base_url = base_url.rstrip("/")
    parsed = urlparse(base_url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise SwitchRegistrationError("Switch server URL must be a clean HTTP(S) URL without credentials or query parameters")
    if not room_id.strip():
        raise SwitchRegistrationError("Switch room ID is required")
    existing_base = store.get_setting("switch_base_url")
    if existing_base and existing_base != base_url and store.get_switch_agents():
        raise SwitchRegistrationError(
            "MergeMind already has agent credentials for a different Switch server. Do not reuse those keys on a new server; reset the local agent store before registering a different server."
        )

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        try:
            health = await client.get(f"{base_url}/health")
            health.raise_for_status()
        except httpx.HTTPError as exc:
            raise SwitchRegistrationError("Switch server health check failed. Use the agent bridge base URL, not the Gateway URL.") from exc

        created = []
        for role in AGENTS:
            saved = store.get_switch_agent(role.id)
            if saved is None:
                body = {
                    "name": role.switch_name,
                    "display_name": role.name,
                    "description": role.purpose,
                    "connector_type": "mergemind",
                    "integration_profile": {
                        "connection_model": "always_on",
                        "message_exchange": True,
                        "pre_invocation_mediation": [],
                        "post_invocation_mediation": [],
                        "event_reporting": [],
                    },
                    "metadata": {"application": "MergeMind", "role": role.id},
                    "overwrite": False,
                }
                response = None
                try:
                    response = await client.post(
                        f"{base_url}/agents",
                        headers={"Authorization": f"Bearer {registration_key}"},
                        json=body,
                    )
                    response.raise_for_status()
                    result = response.json()
                    saved = {
                        "role": role.id,
                        "name": role.switch_name,
                        "agent_id": result["id"],
                        "api_key": result["api_key"],
                    }
                    # Store the key immediately: a later failure must not make it unrecoverable.
                    store.save_switch_agent(role.id, role.switch_name, result["id"], result["api_key"])
                    created.append(role.id)
                except (httpx.HTTPError, KeyError, ValueError) as exc:
                    detail = response.text[:500] if response is not None else str(exc)
                    raise SwitchRegistrationError(
                        f"Could not register {role.name}. Existing agents are retained; correct the cause and retry. {detail}"
                    ) from exc

            # Each agent must be allowed to receive handoffs from the owner's other agents.
            try:
                response = await client.post(
                    f"{base_url}/agents/{saved['agent_id']}/ops/update_agent_detail",
                    headers={"Authorization": f"Bearer {saved['api_key']}"},
                    json={"agent_id": saved["agent_id"], "addressing": "owner_and_owner_agents"},
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                raise SwitchRegistrationError(
                    f"Registered {role.name}, but could not set owner-and-owner-agents addressing. Retry registration to repair it."
                ) from exc

    store.set_setting("switch_base_url", base_url)
    store.set_setting("switch_room_id", room_id.strip())
    return {
        "registered_roles": created,
        "total_roles": len(AGENTS),
        "room_id": room_id.strip(),
        "base_url": base_url,
        "next_step": "Invite all five MergeMind agents into this Switch room. Workers will connect when the app restarts or reloads its workers.",
    }
