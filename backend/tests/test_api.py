from fastapi.testclient import TestClient

from backend.app.main import app, workflows

client = TestClient(app)


def setup_function():
    workflows.clear()


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_agent_registry_has_expected_roles():
    response = client.get("/api/agents")
    assert response.status_code == 200
    ids = {agent["id"] for agent in response.json()}
    assert {"planner", "researcher", "implementer", "reviewer"} <= ids


def test_create_workflow_requires_valid_description():
    response = client.post(
        "/api/workflows",
        json={"title": "Fix issue", "description": "Please fix this bug safely.", "mode": "demo"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "created"
    assert body["approval_required"] is True
    assert body["approved_by_human"] is False
    assert body["events"][0]["metadata"]["switch_dispatch"] is False


def test_unknown_workflow_returns_404():
    response = client.get("/api/workflows/not-a-workflow")
    assert response.status_code == 404


def test_approval_is_blocked_before_review_stage():
    response = client.post(
        "/api/workflows",
        json={"title": "Fix issue", "description": "Please fix this bug safely.", "mode": "demo"},
    )
    workflow_id = response.json()["id"]
    approval = client.post(f"/api/workflows/{workflow_id}/approve")
    assert approval.status_code == 409
