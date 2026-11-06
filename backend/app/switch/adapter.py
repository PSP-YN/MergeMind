"""Switch integration boundary.

The real adapter will implement the official Switch agent protocol. Demo mode
must never claim messages were delivered to Switch. The current implementation
is intentionally a configuration check, not a fake network integration.
"""
from dataclasses import dataclass

from backend.app.core.config import settings


@dataclass(frozen=True)
class SwitchStatus:
    configured: bool
    base_url: str | None
    agent_id: str | None
    note: str


def switch_status() -> SwitchStatus:
    configured = bool(
        settings.switch_base_url
        and settings.switch_agent_id
        and settings.switch_agent_api_key
    )
    return SwitchStatus(
        configured=configured,
        base_url=settings.switch_base_url,
        agent_id=settings.switch_agent_id,
        note=(
            "Switch credentials are configured; connection verification is not implemented yet."
            if configured
            else "Switch is not configured. Demo mode remains local and does not send room messages."
        ),
    )
