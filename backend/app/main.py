import json
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.agents.registry import list_agents
from backend.app.core.config import settings
from backend.app.core.store import store
from backend.app.models.workflow import Workflow, WorkflowCreate, WorkflowEvent, WorkflowStatus
from backend.app.switch.registration import SwitchRegistrationError, register_mergemind_agents
from backend.app.switch.worker import worker_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    await worker_manager.start()
    yield
    await worker_manager.stop()


app = FastAPI(
    title="MergeMind API",
    description="Switch-powered multi-agent software engineering workflow.",
    version="0.2.0",
    lifespan=lifespan,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; "
            "style-src 'self'; img-src 'self' data:; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)


def require_admin(x_mergemind_admin_token: str | None = Header(default=None)):
    if not settings.admin_token:
        raise HTTPException(
            status_code=503,
            detail="Admin token is not configured. Run python -m backend.app.cli init and restart MergeMind.",
        )
    if not x_mergemind_admin_token or not secrets.compare_digest(
        x_mergemind_admin_token, settings.admin_token
    ):
        raise HTTPException(status_code=401, detail="Invalid admin token")


class SwitchRegistrationRequest(BaseModel):
    base_url: str = Field(min_length=8, max_length=500)
    registration_key: str = Field(min_length=10, max_length=1000)
    room_id: str = Field(min_length=3, max_length=300)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        parsed = urlparse(value.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("Enter the Switch agent bridge URL using HTTP or HTTPS")
        return value.strip().rstrip("/")


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": "MergeMind", "version": "0.2.0"}


@app.get("/api/agents")
def agents(_: None = Depends(require_admin)) -> list[dict[str, str]]:
    return list_agents()


@app.get("/api/switch/status")
def get_switch_status(_: None = Depends(require_admin)):
    return {
        "configured": bool(store.get_setting("switch_base_url") and store.get_setting("switch_room_id")),
        "llm_model": settings.llm_model,
        "base_url": store.get_setting("switch_base_url"),
        "room_id": store.get_setting("switch_room_id"),
        "agents": worker_manager.status(),
        "registered_agents": [
            {"role": agent["role"], "name": agent["name"], "agent_id": agent["agent_id"]}
            for agent in store.get_switch_agents()
        ],
    }


@app.post("/api/switch/register")
async def register_switch(
    payload: SwitchRegistrationRequest,
    _: None = Depends(require_admin),
):
    try:
        result = await register_mergemind_agents(
            payload.base_url, payload.registration_key, payload.room_id
        )
        await worker_manager.restart()
        return result
    except SwitchRegistrationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/workflows", response_model=Workflow, status_code=201)
async def create_workflow(
    payload: WorkflowCreate,
    _: None = Depends(require_admin),
) -> Workflow:
    if len(store.get_switch_agents()) < 5:
        raise HTTPException(status_code=409, detail="Register all five MergeMind agents with Switch before starting a workflow.")
    workflow = Workflow(
        title=payload.title.strip(),
        description=payload.description.strip(),
        repository=payload.repository,
    )
    workflow.events.append(
        WorkflowEvent(
            actor="system",
            kind="workflow_created",
            message="Workflow created and queued for Switch-based multi-agent execution.",
        )
    )
    store.save_workflow(workflow)
    handoff = "MERGEMIND/1\n" + json.dumps({
        "stage": "task",
        "workflow_id": workflow.id,
        "title": workflow.title,
        "description": workflow.description,
        "repository": workflow.repository,
    })
    try:
        await worker_manager.dispatch_task(handoff)
    except Exception as exc:
        workflow.status = WorkflowStatus.FAILED
        workflow.events.append(
            WorkflowEvent(actor="system", kind="dispatch_failed", message=str(exc)[:500])
        )
        store.save_workflow(workflow)
        raise HTTPException(status_code=503, detail=f"Workflow was saved but Switch dispatch failed: {exc}") from exc
    return store.get_workflow(workflow.id) or workflow


@app.get("/api/workflows", response_model=list[Workflow])
def list_workflows(_: None = Depends(require_admin)) -> list[Workflow]:
    return store.list_workflows()


@app.get("/api/workflows/{workflow_id}", response_model=Workflow)
def get_workflow(workflow_id: str, _: None = Depends(require_admin)) -> Workflow:
    workflow = store.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@app.post("/api/workflows/{workflow_id}/approve", response_model=Workflow)
def approve_workflow(
    workflow_id: str,
    _: None = Depends(require_admin),
) -> Workflow:
    workflow = store.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.status != WorkflowStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=409, detail="Workflow is not awaiting human approval.")
    workflow.approved_by_human = True
    workflow.status = WorkflowStatus.APPROVED
    workflow.updated_at = datetime.now(timezone.utc)
    workflow.events.append(
        WorkflowEvent(
            actor="human",
            kind="approval",
            message="Human review approval recorded. The proposed patch remains unapplied; repository changes require a separate explicit action.",
        )
    )
    store.save_workflow(workflow)
    return workflow


@app.post("/api/workflows/{workflow_id}/reject", response_model=Workflow)
def reject_workflow(
    workflow_id: str,
    _: None = Depends(require_admin),
) -> Workflow:
    workflow = store.get_workflow(workflow_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    if workflow.status != WorkflowStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=409, detail="Workflow is not awaiting human review.")
    workflow.status = WorkflowStatus.REJECTED
    workflow.updated_at = datetime.now(timezone.utc)
    workflow.events.append(
        WorkflowEvent(
            actor="human",
            kind="rejection",
            message="Human reviewer rejected the proposal. No repository changes were made.",
        )
    )
    store.save_workflow(workflow)
    return workflow


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
