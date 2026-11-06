import asyncio

from backend.app.core.store import store
from backend.app.models.workflow import Workflow, WorkflowStatus
from backend.app.workflow_engine import HANDOFF_PREFIX, handle_agent_message
import backend.app.workflow_engine as engine


class FakeClient:
    def __init__(self):
        self.sent = []
        self.posts = []

    async def send_targeted(self, role_name, body):
        self.sent.append((role_name, f"@{role_name} {body}"))
        return {"event_id": "event-1"}

    async def post_message(self, body):
        self.posts.append(body)
        return {"event_id": "event-2"}


class FakeLLM:
    async def complete(self, system, user, temperature=0.2):
        if "unified diff" in system:
            return (
                "diff --git a/app.py b/app.py\n"
                "--- a/app.py\n"
                "+++ b/app.py\n"
                "@@ -1 +1 @@\n"
                "-old\n"
                "+new"
            )
        if "independently review" in system:
            return "Verdict: READY_FOR_HUMAN_REVIEW. Tests were not run."
        if "read-only source excerpts" in system:
            return "Repository evidence: app.py contains the relevant handler."
        return "Plan: inspect handler, update behavior, add regression coverage."


def test_switch_handoff_pipeline_reaches_human_review(monkeypatch):
    store.delete_all()
    workflow = Workflow(
        title="Correct request pagination",
        description="Correct the page cursor when a filter is active and add regression coverage.",
        repository="https://github.com/example/project",
    )
    store.save_workflow(workflow)
    monkeypatch.setattr(engine, "LLMClient", FakeLLM)

    async def fake_repository_context(_url):
        return "Repository: example/project\n--- FILE: app.py ---\ndef handler(): return 'old'"

    monkeypatch.setattr(engine, "read_repository_context", fake_repository_context)

    async def fake_sandbox(_repository, _patch):
        return "Patch application: PASS (controlled test double)"

    monkeypatch.setattr(engine, "verify_patch_in_sandbox", fake_sandbox)
    client = FakeClient()

    async def run_pipeline():
        task = HANDOFF_PREFIX + (
            '{"stage":"task","workflow_id":"' + workflow.id + '","title":"' +
            workflow.title + '","description":"' + workflow.description +
            '","repository":"' + workflow.repository + '"}'
        )
        await handle_agent_message("coordinator", {"body": task}, client)
        assert client.sent[-1][0] == "mergemind-planner"
        planner_handoff = client.sent[-1][1]

        await handle_agent_message("planner", {"body": planner_handoff}, client)
        assert client.sent[-1][0] == "mergemind-researcher"
        researcher_handoff = client.sent[-1][1]

        await handle_agent_message("researcher", {"body": researcher_handoff}, client)
        assert client.sent[-1][0] == "mergemind-implementer"
        implementer_handoff = client.sent[-1][1]

        await handle_agent_message("implementer", {"body": implementer_handoff}, client)
        assert client.sent[-1][0] == "mergemind-reviewer"
        reviewer_handoff = client.sent[-1][1]

        await handle_agent_message("reviewer", {"body": reviewer_handoff}, client)
        assert client.sent[-1][0] == "mergemind-coordinator"
        completion_handoff = client.sent[-1][1]

        await handle_agent_message("coordinator", {"body": completion_handoff}, client)

    asyncio.run(run_pipeline())
    saved = store.get_workflow(workflow.id)
    assert saved is not None
    assert saved.status == WorkflowStatus.AWAITING_APPROVAL
    assert {"plan", "research", "patch", "sandbox", "review"} <= set(saved.artifacts)
    assert saved.artifacts["patch"].startswith("diff --git")
    assert saved.approved_by_human is False
    assert client.posts and "ready for human review" in client.posts[-1].lower()


def test_invalid_handoff_does_not_create_workflow():
    store.delete_all()
    client = FakeClient()
    asyncio.run(handle_agent_message("planner", {"body": "plain message"}, client))
    assert store.list_workflows() == []
