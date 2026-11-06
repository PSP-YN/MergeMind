from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowStatus(StrEnum):
    CREATED = "created"
    PLANNING = "planning"
    RESEARCH = "research"
    IMPLEMENTATION = "implementation"
    REVIEW = "review"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=10000)
    repository: str | None = Field(default=None, max_length=300)
    mode: str = Field(default="demo", pattern="^(demo|switch)$")


class WorkflowEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=utc_now)
    actor: str
    kind: str
    message: str
    metadata: dict[str, str | int | bool | None] = Field(default_factory=dict)


class Workflow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    repository: str | None = None
    mode: str = "demo"
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: datetime = Field(default_factory=utc_now)
    events: list[WorkflowEvent] = Field(default_factory=list)
    approval_required: bool = True
    approved_by_human: bool = False
