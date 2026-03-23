"""Integration tests for the FastAPI REST API."""
import pytest
from fastapi.testclient import TestClient

from nixclaw.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "checks" in data
    assert "uptime_seconds" in data


def test_list_tasks_empty(client):
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_task_not_found(client):
    response = client.get("/api/v1/tasks/nonexistent123")
    assert response.status_code == 404


def test_cancel_task_not_running(client):
    response = client.post("/api/v1/tasks/nonexistent123/cancel")
    assert response.status_code == 400


def test_agents_status(client):
    response = client.get("/api/v1/agents/status")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data


def test_submit_task_schema(client):
    """Verify the submit endpoint accepts the correct request body."""
    # We can't run a real task in tests (needs LLM), but we can verify
    # the endpoint accepts the request format and returns a task_id.
    # The actual task will fail to run in background but the submission should work.
    response = client.post(
        "/api/v1/tasks",
        json={
            "task": "test task for API validation",
            "priority": "normal",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"
    assert len(data["task_id"]) > 0
