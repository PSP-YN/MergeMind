from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.core.store import store
from backend.app.main import SwitchRegistrationRequest, app
from backend.app.models.workflow import Workflow, WorkflowStatus
from backend.app.switch.client import websocket_url
from backend.app.agents.patch_safety import UnsafePatch, validate_unified_diff
from backend.app.agents.repository import RepositoryError, parse_repository_url
from backend.app.core.config import settings

client = TestClient(app)


def setup_function():
    store.delete_all()
    settings.admin_token = "test-admin-token"
    settings.encryption_key = ""


def headers():
    return {"X-MergeMind-Admin-Token": "test-admin-token"}


def test_health_is_public():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_admin_routes_reject_missing_token():
    response = client.get("/api/switch/status")
    assert response.status_code == 401


def test_dashboard_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "MergeMind" in response.text


def test_workflow_creation_requires_switch_agents():
    response = client.post(
        "/api/workflows",
        headers=headers(),
        json={
            "title": "Fix pagination",
            "description": "Fix the pagination bug when filters are active.",
            "repository": "https://github.com/example/project",
            "mode": "switch",
        },
    )
    assert response.status_code == 409


def test_workflow_model_keeps_human_approval_gate():
    workflow = Workflow(
        title="Fix pagination",
        description="Fix the pagination bug when filters are active.",
        repository="https://github.com/example/project",
    )
    assert workflow.status == WorkflowStatus.CREATED
    assert workflow.approval_required is True
    assert workflow.approved_by_human is False


def test_approval_is_blocked_before_review():
    workflow = Workflow(
        title="Fix pagination",
        description="Fix the pagination bug when filters are active.",
        repository="https://github.com/example/project",
    )
    store.save_workflow(workflow)
    response = client.post(f"/api/workflows/{workflow.id}/approve", headers=headers())
    assert response.status_code == 409


def test_approval_records_human_decision_without_applying_patch():
    workflow = Workflow(
        title="Fix pagination",
        description="Fix the pagination bug when filters are active.",
        repository="https://github.com/example/project",
        status=WorkflowStatus.AWAITING_APPROVAL,
        artifacts={"patch": "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-a\n+b"},
    )
    store.save_workflow(workflow)
    response = client.post(f"/api/workflows/{workflow.id}/approve", headers=headers())
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["approved_by_human"] is True
    assert body["artifacts"]["patch"].startswith("diff --git")


def test_repository_url_validation():
    assert parse_repository_url("https://github.com/owner/repo") == ("owner", "repo")
    try:
        parse_repository_url("https://example.com/owner/repo")
        assert False, "expected RepositoryError"
    except RepositoryError:
        pass


def test_websocket_url_uses_tls_for_https():
    url = websocket_url(
        "https://switch.example",
        "agent-1",
        {"connection_id": "abc", "rooms": "room-1"},
    )
    assert url.startswith("wss://switch.example/agents/agent-1/connection/ws?")
    assert "connection_id=abc" in url


def test_patch_validator_rejects_non_diff_output():
    try:
        validate_unified_diff("Here is your patch")
        assert False, "expected UnsafePatch"
    except UnsafePatch:
        pass


def test_patch_validator_accepts_unified_diff():
    patch = "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-a\n+b"
    assert validate_unified_diff(patch) == patch


def test_patch_validator_rejects_parent_path():
    patch = "diff --git a/../secret b/../secret\n--- a/../secret\n+++ b/../secret\n@@ -1 +1 @@\n-a\n+b"
    try:
        validate_unified_diff(patch)
        assert False, "expected UnsafePatch"
    except UnsafePatch:
        pass



def test_switch_agent_api_keys_are_encrypted_at_rest():
    from cryptography.fernet import Fernet
    from backend.app.core.config import settings

    settings.encryption_key = Fernet.generate_key().decode("ascii")
    store.save_switch_agent("planner", "mergemind-planner", "agent-id", "sensitive-agent-api-key")
    saved = store.get_switch_agent("planner")
    assert saved is not None
    assert saved["api_key"] == "sensitive-agent-api-key"
    with store._connection() as db:
        row = db.execute("SELECT secret FROM switch_agents WHERE role='planner'").fetchone()
    assert "sensitive-agent-api-key" not in row["secret"]



def test_dashboard_assets_are_local_and_security_policy_is_strict():
    page = client.get("/")
    script = client.get("/static/app.js")
    stylesheet = client.get("/static/styles.css")
    assert script.status_code == 200
    assert stylesheet.status_code == 200
    assert "unsafe-inline" not in page.headers.get("content-security-policy", "")
    assert "X-Frame-Options" in page.headers



def test_approval_is_blocked_when_implementer_produced_no_patch():
    workflow = Workflow(
        title="Fix pagination",
        description="Fix the pagination bug when filters are active.",
        repository="https://github.com/example/project",
        status=WorkflowStatus.AWAITING_APPROVAL,
        artifacts={"patch": "NO_PATCH"},
    )
    store.save_workflow(workflow)
    response = client.post(f"/api/workflows/{workflow.id}/approve", headers=headers())
    assert response.status_code == 409
    assert "valid patch" in response.json()["detail"]



def test_patch_validator_unwraps_a_markdown_diff_fence():
    fenced = "```diff\ndiff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n```"
    assert validate_unified_diff(fenced).startswith("diff --git")



def test_switch_registration_url_rejects_embedded_credentials():
    try:
        SwitchRegistrationRequest(
            base_url="https://user:password@switch.example",
            registration_key="registration-key-long-enough",
            room_id="room-123",
        )
        assert False, "expected ValidationError"
    except ValidationError:
        pass


def test_switch_registration_url_rejects_query_parameters():
    try:
        SwitchRegistrationRequest(
            base_url="https://switch.example?token=secret",
            registration_key="registration-key-long-enough",
            room_id="room-123",
        )
        assert False, "expected ValidationError"
    except ValidationError:
        pass
