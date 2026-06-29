from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.base import initialize_database
from app.db.session import SessionLocal
from app.main import app
from app.models.approval import Approval
from app.models.workflow_run import WorkflowRun

initialize_database()

client = TestClient(app)


def _create_approval_and_run(
    *,
    status: str = "succeeded",
    request_summary: dict | None = None,
    response_summary: dict | None = None,
) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    approval = Approval(
        title=f"Workflow audit {uuid4()}",
        description="Workflow run history test approval.",
        action_type="workflow",
        proposed_action_id="n8n_webhook",
        source="pytest",
        risk_level="medium",
        requires_manual_review=True,
        payload_summary={"workflow_type": "n8n_webhook"},
        safety_notes=[],
        status="approved",
        created_at=now,
        expires_at=now + timedelta(hours=1),
        decided_at=now,
    )
    with SessionLocal() as db:
        db.add(approval)
        db.commit()
        db.refresh(approval)

        run = WorkflowRun(
            approval_id=approval.id,
            target_type="n8n_webhook",
            status=status,
            started_at=now,
            finished_at=now + timedelta(seconds=1),
            http_status_code=202 if status == "succeeded" else 500,
            sanitized_error=None if status == "succeeded" else "n8n_webhook_non_2xx_response",
            request_summary=request_summary
            or {
                "source": "kairos",
                "event": "approval.trigger_n8n",
                "approval_id": str(approval.id),
                "workflow_type": "n8n_webhook",
            },
            response_summary=response_summary or {"result": status, "body_bytes": 2},
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return str(approval.id), str(run.id)


def test_list_workflow_runs_returns_sanitized_history():
    approval_id, run_id = _create_approval_and_run()

    response = client.get("/api/v1/workflow-runs")

    assert response.status_code == 200
    runs = response.json()
    run = next(item for item in runs if item["id"] == run_id)
    assert run["approval_id"] == approval_id
    assert run["target_type"] == "n8n_webhook"
    assert run["status"] == "succeeded"
    assert run["request_summary"]["workflow_type"] == "n8n_webhook"


def test_list_workflow_runs_filters_by_status_approval_and_target_type():
    approval_id, run_id = _create_approval_and_run(status="failed")
    _create_approval_and_run(status="succeeded")

    response = client.get(
        "/api/v1/workflow-runs",
        params={
            "status": "failed",
            "approval_id": approval_id,
            "target_type": "n8n_webhook",
        },
    )

    assert response.status_code == 200
    runs = response.json()
    assert [run["id"] for run in runs] == [run_id]
    assert runs[0]["status"] == "failed"
    assert runs[0]["approval_id"] == approval_id


def test_get_workflow_run_returns_sanitized_detail():
    _, run_id = _create_approval_and_run(
        request_summary={
            "source": "kairos",
            "webhook_url": "http://secret-webhook.local",
            "nested": {"operator_token": "secret-token"},
        },
        response_summary={
            "result": "failed",
            "raw_response": "raw n8n body",
            "items": [{"api_key": "secret-key"}],
        },
    )

    response = client.get(f"/api/v1/workflow-runs/{run_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["request_summary"]["source"] == "kairos"
    assert data["request_summary"]["webhook_url"] == "[redacted]"
    assert data["request_summary"]["nested"]["operator_token"] == "[redacted]"
    assert data["response_summary"]["raw_response"] == "[redacted]"
    assert data["response_summary"]["items"][0]["api_key"] == "[redacted]"
    assert "secret-webhook" not in response.text
    assert "secret-token" not in response.text
    assert "raw n8n body" not in response.text
    assert "secret-key" not in response.text


def test_get_workflow_run_missing_returns_404():
    response = client.get(f"/api/v1/workflow-runs/{uuid4()}")

    assert response.status_code == 404
