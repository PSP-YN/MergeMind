import json
import logging
import re
from datetime import datetime, timezone

from backend.app.agents.llm import LLMClient
from backend.app.agents.patch_safety import UnsafePatch, validate_unified_diff
from backend.app.agents.prompts import (
    IMPLEMENTER_SYSTEM,
    PLANNER_SYSTEM,
    RESEARCHER_SYSTEM,
    REVIEWER_SYSTEM,
)
from backend.app.agents.repository import read_repository_context
from backend.app.agents.sandbox import verify_patch_in_sandbox
from backend.app.core.store import store
from backend.app.models.workflow import Workflow, WorkflowEvent, WorkflowStatus

logger = logging.getLogger(__name__)
HANDOFF_PREFIX = "MERGEMIND/1\n"
ROLE_NAMES = {
    "coordinator": "mergemind-coordinator",
    "planner": "mergemind-planner",
    "researcher": "mergemind-researcher",
    "implementer": "mergemind-implementer",
    "reviewer": "mergemind-reviewer",
}


def _handoff(stage: str, workflow: Workflow, **data) -> str:
    payload = {
        "stage": stage,
        "workflow_id": workflow.id,
        "title": workflow.title,
        "description": workflow.description,
        "repository": workflow.repository,
        **data,
    }
    return HANDOFF_PREFIX + json.dumps(payload, ensure_ascii=False)


def _parse_handoff(body: str) -> dict | None:
    # Switch's send_targeted_message prepends @agent-name to the body.
    # Accept only those mention tokens before our versioned handoff envelope.
    body = body.strip()
    marker = body.find(HANDOFF_PREFIX)
    if marker < 0:
        return None
    leading = body[:marker].strip()
    if leading and not re.fullmatch(r"(?:@[A-Za-z0-9_.-]+[,\s:]*)+", leading):
        return None
    try:
        value = json.loads(body[marker + len(HANDOFF_PREFIX):])
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def _update(workflow_id: str, *, status: WorkflowStatus | None = None, artifact: tuple[str, str] | None = None,
            actor: str, message: str, kind: str = "agent_output") -> Workflow:
    workflow = store.get_workflow(workflow_id)
    if workflow is None:
        raise KeyError(f"Workflow {workflow_id} no longer exists")
    if status is not None:
        workflow.status = status
    if artifact is not None:
        workflow.artifacts[artifact[0]] = artifact[1]
    workflow.updated_at = datetime.now(timezone.utc)
    workflow.events.append(WorkflowEvent(actor=actor, kind=kind, message=message))
    store.save_workflow(workflow)
    return workflow


async def _send(client, role: str, workflow: Workflow, stage: str, **data) -> None:
    await client.send_targeted(ROLE_NAMES[role], _handoff(stage, workflow, **data))


async def handle_agent_message(role: str, event: dict, client) -> None:
    body = str(event.get("body") or "").strip()
    handoff = _parse_handoff(body)
    if role == "coordinator":
        try:
            await _handle_coordinator(handoff, body, client)
        except Exception as exc:
            logger.exception("Coordinator failed while handling a Switch message")
            workflow_id = handoff.get("workflow_id") if handoff else None
            workflow = store.get_workflow(str(workflow_id)) if workflow_id else None
            if workflow is not None:
                try:
                    if handoff and handoff.get("stage") == "complete":
                        _update(
                            workflow.id,
                            actor="Coordinator",
                            kind="room_notification_failed",
                            message="The workflow completed, but the final Switch room notification failed.",
                        )
                    else:
                        _update(
                            workflow.id,
                            status=WorkflowStatus.FAILED,
                            actor="Coordinator",
                            kind="stage_failed",
                            message=f"Coordinator dispatch failed: {type(exc).__name__}: {str(exc)[:250]}",
                        )
                except Exception:
                    logger.exception("Could not persist coordinator failure for %s", workflow.id)
            try:
                await client.post_message(
                    "MergeMind Coordinator encountered an error. Check the dashboard workflow trace for details."
                )
            except Exception:
                logger.exception("Could not post coordinator failure notice")
        return
    if not handoff:
        logger.info("Ignored non-MergeMind message addressed to %s", role)
        return
    workflow_id = handoff.get("workflow_id")
    workflow = store.get_workflow(str(workflow_id))
    if workflow is None:
        await client.post_message("MergeMind could not find the workflow referenced by that handoff.")
        return
    try:
        llm = LLMClient()
        if role == "planner":
            result = await llm.complete(
                PLANNER_SYSTEM,
                f"Engineering task: {workflow.title}\n\n{workflow.description}\n\nRepository: {workflow.repository}",
            )
            workflow = _update(workflow.id, status=WorkflowStatus.RESEARCH, artifact=("plan", result),
                               actor="Planner", message="Produced an implementation plan and acceptance criteria.")
            await _send(client, "researcher", workflow, "research", plan=result)
        elif role == "researcher":
            context = await read_repository_context(workflow.repository)
            result = await llm.complete(
                RESEARCHER_SYSTEM,
                f"Task: {workflow.title}\n\n{workflow.description}\n\nPlan:\n{handoff.get('plan','')}\n\nRepository excerpts:\n{context}",
            )
            workflow = _update(workflow.id, status=WorkflowStatus.IMPLEMENTATION,
                               artifact=("research", result), actor="Researcher",
                               message="Inspected public repository files and summarized evidence.")
            await _send(client, "implementer", workflow, "implement", plan=handoff.get("plan", ""),
                        research=result, repository_context=context)
        elif role == "implementer":
            context = str(handoff.get("repository_context", ""))[:55_000]
            raw_patch = await llm.complete(
                IMPLEMENTER_SYSTEM,
                f"Task: {workflow.title}\n\n{workflow.description}\n\nPlan:\n{handoff.get('plan','')}\n\nResearch:\n{handoff.get('research','')}\n\nRepository context:\n{context}",
                temperature=0.1,
            )
            patch = validate_unified_diff(raw_patch)
            sandbox_result = await verify_patch_in_sandbox(workflow.repository, patch)
            workflow = _update(workflow.id, status=WorkflowStatus.REVIEW,
                               artifact=("patch", patch), actor="Implementer",
                               message=("Generated a proposed unified diff; no repository files were changed."
                                        if patch != "NO_PATCH" else "Could not safely generate a patch from the available context."))
            workflow = _update(workflow.id, artifact=("sandbox", sandbox_result), actor="Sandbox",
                               kind="patch_validation",
                               message="Checked patch applicability and performed restricted syntax validation where Docker was available.")
            await _send(client, "reviewer", workflow, "review", plan=handoff.get("plan", ""),
                        research=handoff.get("research", ""), patch=patch, sandbox=sandbox_result)
        elif role == "reviewer":
            patch = str(handoff.get("patch", "NO_PATCH"))
            result = await llm.complete(
                REVIEWER_SYSTEM,
                f"Task: {workflow.title}\n\n{workflow.description}\n\nPlan:\n{handoff.get('plan','')}\n\nResearch:\n{handoff.get('research','')}\n\nProposed patch:\n{patch}\n\nPatch validation sandbox:\n{handoff.get('sandbox','Not run')}\n\nThe sandbox only applies the patch to a disposable clone and performs git diff --check plus Python syntax compilation in a no-network Docker container. No project test suite was executed. State this distinction explicitly.",
            )
            workflow = _update(workflow.id, status=WorkflowStatus.AWAITING_APPROVAL,
                               artifact=("review", result), actor="Reviewer",
                               message="Completed independent review. Patch remains unapplied pending human approval.")
            await _send(client, "coordinator", workflow, "complete", review=result)
    except Exception as exc:
        logger.exception("Workflow stage %s failed for %s", role, workflow.id)
        try:
            _update(workflow.id, status=WorkflowStatus.FAILED, actor=role.title(),
                    kind="stage_failed", message=f"Stage failed: {type(exc).__name__}: {str(exc)[:300]}")
        except Exception:
            logger.exception("Could not persist stage failure for %s", workflow.id)
        try:
            await client.post_message(
                f"MergeMind {role.title()} stage failed for workflow {workflow.id}. Check the dashboard trace."
            )
        except Exception:
            logger.exception("Could not post stage failure notice")


async def _handle_coordinator(handoff: dict | None, body: str, client) -> None:
    if handoff and handoff.get("stage") == "complete":
        workflow = store.get_workflow(str(handoff.get("workflow_id")))
        if workflow is None:
            return
        await client.post_message(
            f"MergeMind workflow {workflow.id} is ready for human review.\n"
            f"Task: {workflow.title}\nStatus: awaiting approval.\n"
            "The proposed patch has not been applied. Review the workflow dashboard before taking action."
        )
        return

    if handoff and handoff.get("stage") == "task":
        workflow = store.get_workflow(str(handoff.get("workflow_id")))
    else:
        urls = re.findall(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", body)
        if not urls:
            await client.post_message(
                "To start a MergeMind workflow, include a public GitHub repository URL and describe the engineering task."
            )
            return
        repository = urls[0].rstrip("/")
        description = body.replace(repository, "").strip()
        workflow = Workflow(
            title=(description.splitlines()[0][:150] if description else "Engineering task"),
            description=description or body,
            repository=repository,
        )
        store.save_workflow(workflow)
    if workflow is None:
        await client.post_message("MergeMind could not start this task because its workflow record is missing.")
        return
    _update(workflow.id, status=WorkflowStatus.PLANNING, actor="Coordinator",
            kind="workflow_started", message="Accepted task and delegated planning through the Switch room.")
    await _send(client, "planner", workflow, "plan")
