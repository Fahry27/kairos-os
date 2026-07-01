from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.db.base import initialize_database
from app.db.session import SessionLocal
from app.main import app

# Initialize SQLite tables before running these tests
initialize_database()

client = TestClient(app)


N8N_URL = "http://n8n.local/webhook/kairos"
OPERATOR_TOKEN = "operator-test-token"
API_KEY = "api-test-key"


def _override_settings(
    *,
    api_key: str | None = None,
    operator_token: str | None = None,
    n8n_enabled: bool = False,
    n8n_url: str = "",
):
    def get_settings_override():
        settings = Settings()
        settings.kairos_api_key = api_key
        settings.kairos_operator_token = operator_token
        settings.n8n_webhook_trigger_enabled = n8n_enabled
        settings.n8n_webhook_url = n8n_url
        settings.n8n_webhook_timeout_seconds = 3
        return settings

    app.dependency_overrides[get_settings] = get_settings_override


def _clear_overrides():
    app.dependency_overrides.pop(get_settings, None)


def _create_approval(
    *,
    action_type: str = "workflow",
    proposed_action_id: str | None = "n8n_webhook",
    payload_summary: dict | None = None,
    expires_in_minutes: int | None = None,
    api_key: str | None = None,
) -> str:
    payload = {
        "title": "Controlled n8n trigger",
        "description": "Metadata-only approval for pytest.",
        "action_type": action_type,
        "proposed_action_id": proposed_action_id,
        "source": "pytest",
        "risk_level": "medium",
        "requires_manual_review": True,
    }
    if payload_summary is not None:
        payload["payload_summary"] = payload_summary
    if expires_in_minutes is not None:
        payload["expires_in_minutes"] = expires_in_minutes

    headers = {"X-Kairos-API-Key": api_key} if api_key else {}
    response = client.post("/api/v1/approvals", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()["id"]


def _approve(
    approval_id: str,
    *,
    api_key: str | None = None,
    token: str | None = None,
):
    headers = {}
    if api_key:
        headers["X-Kairos-API-Key"] = api_key
    if token:
        headers["X-Kairos-Operator-Token"] = token
    return client.post(f"/api/v1/approvals/{approval_id}/approve", headers=headers)


def test_openapi_approval_operator_actions_include_dual_header_security():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    security_schemes = schema["components"]["securitySchemes"]
    assert security_schemes["KairosApiKey"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-Kairos-API-Key",
    }
    assert security_schemes["KairosOperatorToken"] == {
        "type": "apiKey",
        "in": "header",
        "name": "X-Kairos-Operator-Token",
    }
    assert API_KEY not in response.text
    assert OPERATOR_TOKEN not in response.text

    for path in (
        "/api/v1/approvals/{approval_id}/approve",
        "/api/v1/approvals/{approval_id}/reject",
        "/api/v1/approvals/{approval_id}/trigger-n8n",
    ):
        security = schema["paths"][path]["post"]["security"]
        assert security == [{"KairosApiKey": [], "KairosOperatorToken": []}]

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


def test_operator_token_required_for_approve_and_reject_when_configured():
    _override_settings(operator_token=OPERATOR_TOKEN)
    try:
        approve_id = _create_approval(action_type="generic", proposed_action_id=None)

        missing = client.post(f"/api/v1/approvals/{approve_id}/approve")
        assert missing.status_code == 403
        assert "operator-test-token" not in missing.text

        invalid = client.post(
            f"/api/v1/approvals/{approve_id}/approve",
            headers={"X-Kairos-Operator-Token": "wrong-token"},
        )
        assert invalid.status_code == 403

        valid = client.post(
            f"/api/v1/approvals/{approve_id}/approve",
            headers={"X-Kairos-Operator-Token": OPERATOR_TOKEN},
        )
        assert valid.status_code == 200
        assert valid.json()["status"] == "approved"

        reject_id = _create_approval(action_type="generic", proposed_action_id=None)
        rejected = client.post(
            f"/api/v1/approvals/{reject_id}/reject",
            json={"reason": "not needed"},
            headers={"X-Kairos-Operator-Token": OPERATOR_TOKEN},
        )
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "rejected"
    finally:
        _clear_overrides()


def test_api_key_and_operator_token_required_for_operator_actions_when_configured(monkeypatch):
    _override_settings(
        api_key=API_KEY,
        operator_token=OPERATOR_TOKEN,
        n8n_enabled=True,
        n8n_url=N8N_URL,
    )
    try:
        approve_id = _create_approval(
            action_type="generic",
            proposed_action_id=None,
            api_key=API_KEY,
        )

        missing_api_key = client.post(
            f"/api/v1/approvals/{approve_id}/approve",
            headers={"X-Kairos-Operator-Token": OPERATOR_TOKEN},
        )
        assert missing_api_key.status_code == 401

        invalid_api_key = client.post(
            f"/api/v1/approvals/{approve_id}/approve",
            headers={
                "X-Kairos-API-Key": "wrong-key",
                "X-Kairos-Operator-Token": OPERATOR_TOKEN,
            },
        )
        assert invalid_api_key.status_code == 401

        missing_operator_token = client.post(
            f"/api/v1/approvals/{approve_id}/approve",
            headers={"X-Kairos-API-Key": API_KEY},
        )
        assert missing_operator_token.status_code == 403
        assert API_KEY not in missing_operator_token.text
        assert OPERATOR_TOKEN not in missing_operator_token.text

        invalid_operator_token = client.post(
            f"/api/v1/approvals/{approve_id}/approve",
            headers={
                "X-Kairos-API-Key": API_KEY,
                "X-Kairos-Operator-Token": "wrong-token",
            },
        )
        assert invalid_operator_token.status_code == 403

        approved = client.post(
            f"/api/v1/approvals/{approve_id}/approve",
            headers={
                "X-Kairos-API-Key": API_KEY,
                "X-Kairos-Operator-Token": OPERATOR_TOKEN,
            },
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"

        reject_id = _create_approval(
            action_type="generic",
            proposed_action_id=None,
            api_key=API_KEY,
        )
        reject_missing_api_key = client.post(
            f"/api/v1/approvals/{reject_id}/reject",
            json={"reason": "no api key"},
            headers={"X-Kairos-Operator-Token": OPERATOR_TOKEN},
        )
        assert reject_missing_api_key.status_code == 401

        rejected = client.post(
            f"/api/v1/approvals/{reject_id}/reject",
            json={"reason": "not needed"},
            headers={
                "X-Kairos-API-Key": API_KEY,
                "X-Kairos-Operator-Token": OPERATOR_TOKEN,
            },
        )
        assert rejected.status_code == 200
        assert rejected.json()["status"] == "rejected"

        trigger_id = _create_approval(api_key=API_KEY)
        assert _approve(trigger_id, api_key=API_KEY, token=OPERATOR_TOKEN).status_code == 200
        calls = []

        def fake_post(*args, **kwargs):
            calls.append((args, kwargs))
            return httpx.Response(204, content=b"accepted")

        monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

        trigger_missing_api_key = client.post(
            f"/api/v1/approvals/{trigger_id}/trigger-n8n",
            headers={"X-Kairos-Operator-Token": OPERATOR_TOKEN},
        )
        assert trigger_missing_api_key.status_code == 401
        assert calls == []

        trigger_missing_operator_token = client.post(
            f"/api/v1/approvals/{trigger_id}/trigger-n8n",
            headers={"X-Kairos-API-Key": API_KEY},
        )
        assert trigger_missing_operator_token.status_code == 403
        assert calls == []

        triggered = client.post(
            f"/api/v1/approvals/{trigger_id}/trigger-n8n",
            headers={
                "X-Kairos-API-Key": API_KEY,
                "X-Kairos-Operator-Token": OPERATOR_TOKEN,
            },
        )
        assert triggered.status_code == 200
        assert triggered.json()["status"] == "succeeded"
        assert len(calls) == 1
    finally:
        _clear_overrides()


def test_operator_token_unset_disables_operator_gate():
    _override_settings(operator_token="", n8n_enabled=True, n8n_url=N8N_URL)
    try:
        approval_id = _create_approval()
        approved = client.post(f"/api/v1/approvals/{approval_id}/approve")
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
    finally:
        _clear_overrides()


def test_trigger_n8n_requires_operator_token_when_configured(monkeypatch):
    _override_settings(operator_token=OPERATOR_TOKEN, n8n_enabled=True, n8n_url=N8N_URL)
    try:
        approval_id = _create_approval()
        assert _approve(approval_id, token=OPERATOR_TOKEN).status_code == 200
        calls = []

        def fake_post(*args, **kwargs):
            calls.append((args, kwargs))
            return httpx.Response(204, content=b"accepted")

        monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

        missing = client.post(f"/api/v1/approvals/{approval_id}/trigger-n8n")
        assert missing.status_code == 403
        assert calls == []

        invalid = client.post(
            f"/api/v1/approvals/{approval_id}/trigger-n8n",
            headers={"X-Kairos-Operator-Token": "wrong-token"},
        )
        assert invalid.status_code == 403
        assert calls == []

        valid = client.post(
            f"/api/v1/approvals/{approval_id}/trigger-n8n",
            headers={"X-Kairos-Operator-Token": OPERATOR_TOKEN},
        )
        assert valid.status_code == 200
        assert valid.json()["status"] == "succeeded"
        assert len(calls) == 1
    finally:
        _clear_overrides()


def test_trigger_n8n_success_stores_sanitized_workflow_run(monkeypatch):
    _override_settings(n8n_enabled=True, n8n_url=N8N_URL)
    try:
        approval_id = _create_approval()
        assert _approve(approval_id).status_code == 200
        calls = []

        def fake_post(url, json, timeout):
            calls.append({"url": url, "json": json, "timeout": timeout})
            return httpx.Response(202, content=b"raw-secret-response")

        monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

        response = client.post(f"/api/v1/approvals/{approval_id}/trigger-n8n")
        assert response.status_code == 200
        data = response.json()

        assert data["approval_id"] == approval_id
        assert data["target_type"] == "n8n_webhook"
        assert data["status"] == "succeeded"
        assert data["http_status_code"] == 202
        assert data["sanitized_error"] is None
        assert data["request_summary"]["approval_id"] == approval_id
        assert data["request_summary"]["workflow_type"] == "n8n_webhook"
        assert data["response_summary"] == {"result": "succeeded", "body_bytes": 19}
        assert "raw-secret-response" not in response.text
        assert N8N_URL not in response.text

        assert calls == [
            {
                "url": N8N_URL,
                "json": data["request_summary"],
                "timeout": 3,
            }
        ]
        assert "payload_summary" not in calls[0]["json"]
    finally:
        _clear_overrides()


def test_trigger_n8n_accepts_payload_summary_workflow_type(monkeypatch):
    _override_settings(n8n_enabled=True, n8n_url=N8N_URL)
    try:
        approval_id = _create_approval(
            proposed_action_id="workflow.reviewed",
            payload_summary={"workflow_type": "n8n_webhook", "ignored_field": "do-not-copy"},
        )
        assert _approve(approval_id).status_code == 200

        def fake_post(url, json, timeout):
            return httpx.Response(200, content=b"ok")

        monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

        response = client.post(f"/api/v1/approvals/{approval_id}/trigger-n8n")
        assert response.status_code == 200
        assert response.json()["status"] == "succeeded"
        assert "do-not-copy" not in response.text
    finally:
        _clear_overrides()


def test_trigger_n8n_blocks_pending_rejected_and_expired(monkeypatch):
    _override_settings(n8n_enabled=True, n8n_url=N8N_URL)
    try:
        calls = []

        def fake_post(*args, **kwargs):
            calls.append((args, kwargs))
            return httpx.Response(200, content=b"ok")

        monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

        pending_id = _create_approval()
        pending = client.post(f"/api/v1/approvals/{pending_id}/trigger-n8n")
        assert pending.status_code == 409

        rejected_id = _create_approval()
        rejected = client.post(f"/api/v1/approvals/{rejected_id}/reject", json={"reason": "no"})
        assert rejected.status_code == 200
        rejected_trigger = client.post(f"/api/v1/approvals/{rejected_id}/trigger-n8n")
        assert rejected_trigger.status_code == 409

        expired_id = _create_approval(expires_in_minutes=-1)
        expired = client.post(f"/api/v1/approvals/{expired_id}/trigger-n8n")
        assert expired.status_code == 409

        assert calls == []
    finally:
        _clear_overrides()


def test_trigger_n8n_blocks_non_workflow_or_non_n8n_approvals(monkeypatch):
    _override_settings(n8n_enabled=True, n8n_url=N8N_URL)
    try:
        calls = []

        def fake_post(*args, **kwargs):
            calls.append((args, kwargs))
            return httpx.Response(200, content=b"ok")

        monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

        command_id = _create_approval(action_type="command", proposed_action_id="n8n_webhook")
        assert _approve(command_id).status_code == 200
        command_trigger = client.post(f"/api/v1/approvals/{command_id}/trigger-n8n")
        assert command_trigger.status_code == 409

        workflow_id = _create_approval(
            action_type="workflow",
            proposed_action_id="other_workflow",
            payload_summary={"workflow_type": "other"},
        )
        assert _approve(workflow_id).status_code == 200
        workflow_trigger = client.post(f"/api/v1/approvals/{workflow_id}/trigger-n8n")
        assert workflow_trigger.status_code == 409

        assert calls == []
    finally:
        _clear_overrides()


def test_trigger_n8n_requires_enabled_trigger_and_configured_url(monkeypatch):
    calls = []

    def fake_post(*args, **kwargs):
        calls.append((args, kwargs))
        return httpx.Response(200, content=b"ok")

    monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

    _override_settings(n8n_enabled=False, n8n_url=N8N_URL)
    try:
        disabled_id = _create_approval()
        assert _approve(disabled_id).status_code == 200
        disabled = client.post(f"/api/v1/approvals/{disabled_id}/trigger-n8n")
        assert disabled.status_code == 403
    finally:
        _clear_overrides()

    _override_settings(n8n_enabled=True, n8n_url="")
    try:
        missing_url_id = _create_approval()
        assert _approve(missing_url_id).status_code == 200
        missing_url = client.post(f"/api/v1/approvals/{missing_url_id}/trigger-n8n")
        assert missing_url.status_code == 503
    finally:
        _clear_overrides()

    assert calls == []


def test_trigger_n8n_blocks_duplicate_success(monkeypatch):
    _override_settings(n8n_enabled=True, n8n_url=N8N_URL)
    try:
        approval_id = _create_approval()
        assert _approve(approval_id).status_code == 200
        calls = []

        def fake_post(*args, **kwargs):
            calls.append((args, kwargs))
            return httpx.Response(200, content=b"ok")

        monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

        first = client.post(f"/api/v1/approvals/{approval_id}/trigger-n8n")
        assert first.status_code == 200
        assert first.json()["status"] == "succeeded"

        second = client.post(f"/api/v1/approvals/{approval_id}/trigger-n8n")
        assert second.status_code == 409
        assert len(calls) == 1
    finally:
        _clear_overrides()


def test_trigger_n8n_failed_runs_require_explicit_retry(monkeypatch):
    _override_settings(n8n_enabled=True, n8n_url=N8N_URL)
    try:
        approval_id = _create_approval()
        assert _approve(approval_id).status_code == 200
        statuses = [500, 200]
        calls = []

        def fake_post(*args, **kwargs):
            calls.append((args, kwargs))
            return httpx.Response(statuses.pop(0), content=b"raw-n8n-body")

        monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

        first = client.post(f"/api/v1/approvals/{approval_id}/trigger-n8n")
        assert first.status_code == 200
        assert first.json()["status"] == "failed"
        assert first.json()["http_status_code"] == 500
        assert first.json()["sanitized_error"] == "n8n_webhook_non_2xx_response"
        assert "raw-n8n-body" not in first.text

        denied = client.post(f"/api/v1/approvals/{approval_id}/trigger-n8n")
        assert denied.status_code == 409

        retried = client.post(
            f"/api/v1/approvals/{approval_id}/trigger-n8n",
            json={"retry_failed": True},
        )
        assert retried.status_code == 200
        assert retried.json()["status"] == "succeeded"
        assert len(calls) == 2
    finally:
        _clear_overrides()


def test_trigger_n8n_timeout_stores_sanitized_error(monkeypatch):
    _override_settings(n8n_enabled=True, n8n_url=N8N_URL)
    try:
        approval_id = _create_approval()
        assert _approve(approval_id).status_code == 200

        def fake_post(*args, **kwargs):
            raise httpx.TimeoutException("secret timeout details")

        monkeypatch.setattr("app.services.approval_service.httpx.post", fake_post)

        response = client.post(f"/api/v1/approvals/{approval_id}/trigger-n8n")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["http_status_code"] is None
        assert data["sanitized_error"] == "n8n_webhook_timeout"
        assert data["response_summary"] == {"result": "timeout"}
        assert "secret timeout details" not in response.text
        assert N8N_URL not in response.text
    finally:
        _clear_overrides()
