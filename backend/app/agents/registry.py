from dataclasses import dataclass


@dataclass(frozen=True)
class AgentRole:
    id: str
    name: str
    purpose: str
    expected_output: str


AGENTS: tuple[AgentRole, ...] = (
    AgentRole("planner", "Planner", "Breaks the request into scoped steps and acceptance criteria.", "Plan with acceptance criteria"),
    AgentRole("researcher", "Researcher", "Finds repository context, constraints, and relevant files.", "Evidence-backed repository findings"),
    AgentRole("implementer", "Implementer", "Produces a proposed patch in an isolated workspace.", "Patch proposal and test notes"),
    AgentRole("reviewer", "Reviewer", "Reviews patch quality, security, and test coverage.", "Review findings and verdict"),
)


def list_agents() -> list[dict[str, str]]:
    return [agent.__dict__ for agent in AGENTS]
