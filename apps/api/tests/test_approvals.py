from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.base import initialize_database
from app.db.session import SessionLocal
from app.main import app

# Initialize SQLite tables before running these tests
initialize_database()

client = TestClient(app)

def test_approval_gate_disabled(monkeypatch):
    def get_settings_override():
        from app.core.config import Settings
        settings = Settings()
        settings.kairos_approval_gate_enabled = False
        return settings
        
    app.dependency_overrides[get_settings] = get_settings_override
    try:
        response = client.get("/api/v1/approvals")
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_settings, None)

def test_create_approval():
    payload = {
        "title": "Test Command",
        "description": "Running test",
        "action_type": "command",
        "proposed_action_id": "test_command",
        "source": "pytest",
        "risk_level": "medium",
        "requires_manual_review": True,
        "payload_summary": {"foo": "bar"}
    }
    response = client.post("/api/v1/approvals", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Command"
    assert data["status"] == "pending"
    assert data["action_type"] == "command"
    assert data["payload_summary"] == {"foo": "bar"}
    assert data["execution_enabled"] is False

def test_list_and_get_approval():
    # create one
    post_res = client.post("/api/v1/approvals", json={
        "title": "List Test",
        "action_type": "command",
        "source": "pytest",
        "risk_level": "low"
    })
    appr_id = post_res.json()["id"]

    # list
    list_res = client.get("/api/v1/approvals")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(x["id"] == appr_id for x in items)

    # get
    get_res = client.get(f"/api/v1/approvals/{appr_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "List Test"

def test_get_missing_returns_404():
    random_id = str(uuid4())
    res = client.get(f"/api/v1/approvals/{random_id}")
    assert res.status_code == 404

def test_approve_request():
    post_res = client.post("/api/v1/approvals", json={
        "title": "Approve Me",
        "action_type": "generic",
        "source": "pytest",
        "risk_level": "low"
    })
    appr_id = post_res.json()["id"]

    app_res = client.post(f"/api/v1/approvals/{appr_id}/approve")
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "approved"
    assert app_res.json()["decided_at"] is not None

def test_reject_request():
    post_res = client.post("/api/v1/approvals", json={
        "title": "Reject Me",
        "action_type": "generic",
        "source": "pytest",
        "risk_level": "high"
    })
    appr_id = post_res.json()["id"]

    rej_res = client.post(f"/api/v1/approvals/{appr_id}/reject", json={"reason": "too risky"})
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"
    assert rej_res.json()["decision_reason"] == "too risky"

def test_invalid_transitions():
    post_res = client.post("/api/v1/approvals", json={
        "title": "State Test",
        "action_type": "generic",
        "source": "pytest",
        "risk_level": "low"
    })
    appr_id = post_res.json()["id"]

    # approve it
    client.post(f"/api/v1/approvals/{appr_id}/approve")

    # try to approve again
    res2 = client.post(f"/api/v1/approvals/{appr_id}/approve")
    assert res2.status_code == 409

    # try to reject approved
    res3 = client.post(f"/api/v1/approvals/{appr_id}/reject", json={"reason": ""})
    assert res3.status_code == 409

def test_max_pending():
    def get_settings_override():
        from app.core.config import Settings
        settings = Settings()
        settings.kairos_approval_max_pending = 1
        return settings
        
    app.dependency_overrides[get_settings] = get_settings_override
    try:
        # We need to clear previous pending requests to test the exact count of 1
        with SessionLocal() as db:
            from app.models.approval import Approval
            from app.schemas.approval import ApprovalStatus
            from sqlalchemy import update
            db.execute(update(Approval).where(Approval.status == ApprovalStatus.pending.value).values(status=ApprovalStatus.rejected.value))
            db.commit()

        client.post("/api/v1/approvals", json={
            "title": "Pending 1",
            "action_type": "generic",
            "source": "pytest",
            "risk_level": "low"
        })
        
        # second one should fail with 429
        res2 = client.post("/api/v1/approvals", json={
            "title": "Pending 2",
            "action_type": "generic",
            "source": "pytest",
            "risk_level": "low"
        })
        assert res2.status_code == 429
    finally:
        app.dependency_overrides.pop(get_settings, None)
