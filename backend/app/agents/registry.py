from dataclasses import dataclass


@dataclass(frozen=True)
class AgentRole:
    id: str
    name: str
    purpose: str
    expected_output: str
    switch_name: str


AGENTS: tuple[AgentRole, ...] = (
    AgentRole("coordinator", "Coordinator", "Accepts engineering tasks, delegates work, and reports the reviewed outcome.", "Workflow orchestration and final summary", "mergemind-coordinator"),
    AgentRole("planner", "Planner", "Breaks the request into scoped steps and acceptance criteria.", "Plan with acceptance criteria", "mergemind-planner"),
    AgentRole("researcher", "Researcher", "Inspects public repository files and reports evidence-backed findings.", "Evidence-backed repository findings", "mergemind-researcher"),
    AgentRole("implementer", "Implementer", "Produces a proposed unified diff without changing repository files.", "Proposed patch and limitations", "mergemind-implementer"),
    AgentRole("reviewer", "Reviewer", "Independently reviews the proposed patch for defects, regressions, and security issues.", "Review findings and verdict", "mergemind-reviewer"),
)


def list_agents() -> list[dict[str, str]]:
    return [
        {
            "id": agent.id,
            "name": agent.name,
            "purpose": agent.purpose,
            "expected_output": agent.expected_output,
            "switch_name": agent.switch_name,
        }
        for agent in AGENTS
    ]
