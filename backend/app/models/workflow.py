from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


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
    FAILED = "failed"


class WorkflowCreate(BaseModel):
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(min_length=10, max_length=10000)
    repository: str = Field(min_length=19, max_length=300)
    mode: str = Field(default="switch", pattern="^switch$")

    @field_validator("repository")
    @classmethod
    def validate_github_repository(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        if not value.startswith("https://github.com/"):
            raise ValueError("Repository must be a public GitHub HTTPS URL")
        parts = value.removeprefix("https://github.com/").removesuffix(".git").split("/")
        if len(parts) != 2 or not all(parts) or any(part in {".", ".."} for part in parts):
            raise ValueError("Repository URL must have the form https://github.com/owner/repo")
        return "https://github.com/" + "/".join(parts)


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
    repository: str
    mode: str = "switch"
    status: WorkflowStatus = WorkflowStatus.CREATED
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    events: list[WorkflowEvent] = Field(default_factory=list)
    artifacts: dict[str, str] = Field(default_factory=dict)
    approval_required: bool = True
    approved_by_human: bool = False
