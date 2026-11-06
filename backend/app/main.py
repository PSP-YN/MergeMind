from fastapi import FastAPI, HTTPException

from backend.app.agents.registry import list_agents
from backend.app.models.workflow import Workflow, WorkflowCreate, WorkflowEvent, WorkflowStatus
from backend.app.switch.adapter import switch_status

app = FastAPI(
    title="MergeMind API",
    description="Switch-powered multi-agent software engineering workflow.",
    version="0.1.0",
)

# In-memory storage is intentionally temporary for the prototype.
workflows: dict[str, Workflow] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "MergeMind", "stage": "prototype"}


@app.get("/api/agents")
def agents() -> list[dict[str, str]]:
    return list_agents()


@app.get("/api/switch/status")
def get_switch_status():
    return switch_status()


@app.post("/api/workflows", response_model=Workflow, status_code=201)
def create_workflow(payload: WorkflowCreate) -> Workflow:
    workflow = Workflow(
        title=payload.title.strip(),
        description=payload.description.strip(),
        repository=payload.repository,
        mode=payload.mode,
    )
    workflow.events.append(
        WorkflowEvent(
            actor="system",
            kind="workflow_created",
            message=(
                "Workflow created in local demo mode."
                if payload.mode == "demo"
                else "Workflow created in Switch mode; Switch dispatch is not implemented yet."
            ),
            metadata={"mode": payload.mode, "switch_dispatch": False},
        )
    )
    workflows[workflow.id] = workflow
    return workflow


@app.get("/api/workflows", response_model=list[Workflow])
def list_workflows() -> list[Workflow]:
    return list(workflows.values())


@app.get("/api/workflows/{workflow_id}", response_model=Workflow)
def get_workflow(workflow_id: str) -> Workflow:
    workflow = workflows.get(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@app.post("/api/workflows/{workflow_id}/approve", response_model=Workflow)
def approve_workflow(workflow_id: str) -> Workflow:
    workflow = workflows.get(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.status != WorkflowStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=409,
            detail="Workflow is not awaiting human approval. No changes were applied.",
        )
    workflow.approved_by_human = True
    workflow.status = WorkflowStatus.APPROVED
    workflow.events.append(
        WorkflowEvent(
            actor="human",
            kind="approval",
            message="Human approval recorded. This prototype does not apply patches.",
        )
    )
    return workflow
