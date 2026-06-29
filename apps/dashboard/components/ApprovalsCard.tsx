"use client";

import { useEffect, useMemo, useState } from "react";
import {
  approveApproval,
  getApproval,
  listApprovals,
  rejectApproval,
  type ApiResult,
  type ApprovalListStatus,
  type ApprovalRequest,
} from "../lib/api";

const STATUS_FILTERS: ApprovalListStatus[] = [
  "pending",
  "approved",
  "rejected",
  "expired",
  "all",
];

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function summarizeDescription(value?: string | null) {
  if (!value) return "No description provided.";
  return value.length > 140 ? `${value.slice(0, 137)}...` : value;
}

function renderPayload(value?: Record<string, unknown> | null) {
  if (!value) return "No payload summary provided.";
  return JSON.stringify(value, null, 2);
}

function isGateDisabled(error: string) {
  return error.startsWith("403") && error.toLowerCase().includes("approval gate");
}

function StatusBadge({ approval }: { approval: ApprovalRequest }) {
  return (
    <span className={`approvalBadge approvalBadge-${approval.status}`}>
      {approval.status}
    </span>
  );
}

function RiskBadge({ risk }: { risk: ApprovalRequest["risk_level"] }) {
  return <span className={`approvalBadge approvalRisk-${risk}`}>{risk}</span>;
}

function SafetyFlag({ label, value }: { label: string; value: boolean }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value ? "true" : "false"}</dd>
    </div>
  );
}

function ApprovalDetails({
  approval,
  actionError,
  isDeciding,
  rejectionReason,
  onApprove,
  onReject,
  onReasonChange,
}: {
  approval: ApprovalRequest;
  actionError: string | null;
  isDeciding: boolean;
  rejectionReason: string;
  onApprove: () => void;
  onReject: () => void;
  onReasonChange: (value: string) => void;
}) {
  const isPending = approval.status === "pending";

  return (
    <div className="approvalDetails">
      <div className="approvalDetailsHeader">
        <div>
          <p className="eyebrow">Inspection</p>
          <h3>{approval.title}</h3>
        </div>
        <div className="approvalBadgeRow">
          <StatusBadge approval={approval} />
          <RiskBadge risk={approval.risk_level} />
        </div>
      </div>

      <p>{approval.description ?? "No description provided."}</p>

      <dl className="approvalMetaGrid">
        <div>
          <dt>Action Type</dt>
          <dd>{approval.action_type}</dd>
        </div>
        <div>
          <dt>Proposed Action ID</dt>
          <dd>{approval.proposed_action_id ?? "-"}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>{approval.source}</dd>
        </div>
        <div>
          <dt>Created</dt>
          <dd>{formatDateTime(approval.created_at)}</dd>
        </div>
        <div>
          <dt>Expires</dt>
          <dd>{formatDateTime(approval.expires_at)}</dd>
        </div>
        <div>
          <dt>Decided</dt>
          <dd>{formatDateTime(approval.decided_at)}</dd>
        </div>
      </dl>

      <div className="approvalSafetyNote">
        Approving changes only this approval request status. It does not execute commands,
        call connectors, trigger n8n, Hermes, or OpenClaw, call cloud providers, or mutate
        domain data. The execution layer is not implemented.
      </div>

      <div className="approvalDetailBlock">
        <h4>Payload Summary</h4>
        <pre>{renderPayload(approval.payload_summary)}</pre>
      </div>

      <div className="approvalDetailBlock">
        <h4>Safety Notes</h4>
        {approval.safety_notes.length > 0 ? (
          <ul>
            {approval.safety_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        ) : (
          <p>No safety notes provided.</p>
        )}
      </div>

      {(approval.decision_reason || approval.decided_at) && (
        <div className="approvalDetailBlock">
          <h4>Decision</h4>
          <p>{approval.decision_reason ?? "No decision reason recorded."}</p>
        </div>
      )}

      <dl className="statGrid approvalFlagGrid">
        <SafetyFlag label="Execution Enabled" value={approval.execution_enabled} />
        <SafetyFlag label="Execution Performed" value={approval.execution_performed} />
        <SafetyFlag label="Connector Calls" value={approval.connector_calls_performed} />
        <SafetyFlag label="Data Mutation" value={approval.data_mutation_performed} />
      </dl>

      {isPending ? (
        <div className="approvalDecisionBox">
          <label>
            <span>Rejection reason</span>
            <textarea
              onChange={(event) => onReasonChange(event.target.value)}
              placeholder="Required when rejecting this approval request"
              rows={2}
              value={rejectionReason}
            />
          </label>
          <div className="recordActions">
            <button
              className="btnSmall btnSave"
              disabled={isDeciding}
              onClick={onApprove}
              type="button"
            >
              {isDeciding ? "Saving..." : "Approve"}
            </button>
            <button
              className="btnSmall btnDanger"
              disabled={isDeciding}
              onClick={onReject}
              type="button"
            >
              {isDeciding ? "Saving..." : "Reject"}
            </button>
          </div>
          {actionError && <p className="errorText">{actionError}</p>}
        </div>
      ) : (
        <p className="stateText">Only pending approval requests can be approved or rejected.</p>
      )}
    </div>
  );
}

export function ApprovalsCard() {
  const [statusFilter, setStatusFilter] = useState<ApprovalListStatus>("pending");
  const [result, setResult] = useState<ApiResult<ApprovalRequest[]> | null>(null);
  const [selected, setSelected] = useState<ApprovalRequest | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isDeciding, setIsDeciding] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");

  async function loadApprovals(nextStatus = statusFilter) {
    setIsRefreshing(true);
    const nextResult = await listApprovals(nextStatus);
    setResult(nextResult);
    setIsRefreshing(false);
    return nextResult;
  }

  useEffect(() => {
    let mounted = true;
    setResult(null);
    setSelected(null);
    setSuccessMessage(null);
    setActionError(null);
    setRejectionReason("");

    listApprovals(statusFilter).then((nextResult) => {
      if (mounted) {
        setResult(nextResult);
      }
    });

    return () => {
      mounted = false;
    };
  }, [statusFilter]);

  const approvals = useMemo(() => (result?.ok ? result.data : []), [result]);

  async function inspectApproval(approvalId: string) {
    setActionError(null);
    setSuccessMessage(null);
    setRejectionReason("");
    const detail = await getApproval(approvalId);
    if (detail.ok) {
      setSelected(detail.data);
    } else {
      setActionError(`Unable to load approval details: ${detail.error}`);
      const fallback = approvals.find((approval) => approval.id === approvalId) ?? null;
      setSelected(fallback);
    }
  }

  async function handleRefresh() {
    setSuccessMessage(null);
    setActionError(null);
    await loadApprovals();
  }

  async function handleApprove() {
    if (!selected) return;
    setIsDeciding(true);
    setActionError(null);

    const decision = await approveApproval(selected.id);
    if (decision.ok) {
      setSelected(decision.data);
      setSuccessMessage(`Approved "${decision.data.title}". No execution was performed.`);
      await loadApprovals();
    } else {
      setActionError(`Approve failed: ${decision.error}. Refresh to check current status.`);
      await loadApprovals();
    }

    setIsDeciding(false);
  }

  async function handleReject() {
    if (!selected) return;
    const reason = rejectionReason.trim();
    if (!reason) {
      setActionError("Rejection reason is required.");
      return;
    }

    setIsDeciding(true);
    setActionError(null);

    const decision = await rejectApproval(selected.id, reason);
    if (decision.ok) {
      setSelected(decision.data);
      setRejectionReason("");
      setSuccessMessage(`Rejected "${decision.data.title}". No execution was performed.`);
      await loadApprovals();
    } else {
      setActionError(`Reject failed: ${decision.error}. Refresh to check current status.`);
      await loadApprovals();
    }

    setIsDeciding(false);
  }

  if (!result) {
    return (
      <section className="card cardWide">
        <p className="eyebrow">Approval Management</p>
        <h2>Loading approval requests...</h2>
      </section>
    );
  }

  if (!result.ok && isGateDisabled(result.error)) {
    return (
      <section className="card cardWide">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Approval Management</p>
            <h2>Safety-Gated</h2>
          </div>
          <button className="btnSmall btnOutline" onClick={handleRefresh} type="button">
            Refresh
          </button>
        </div>
        <div className="approvalSafetyNote">
          Approval Gate is disabled by configuration, so approval requests are unavailable in
          the dashboard. This is a safe control-plane state; no execution layer is enabled.
        </div>
      </section>
    );
  }

  if (!result.ok) {
    return (
      <section className="card cardWide">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Approval Management</p>
            <h2>Unavailable</h2>
          </div>
          <button className="btnSmall btnOutline" onClick={handleRefresh} type="button">
            Refresh
          </button>
        </div>
        <p className="errorText">{result.error}</p>
      </section>
    );
  }

  return (
    <section className="card cardWide">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Approval Management</p>
          <h2>Approval Requests</h2>
          <p className="stateText">
            Review v2.6 Approval Gate requests. Approving is metadata-only and does not
            execute anything.
          </p>
        </div>
        <button
          className="btnSmall btnOutline"
          disabled={isRefreshing}
          onClick={handleRefresh}
          type="button"
        >
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="approvalSafetyNote">
        Execution is not implemented in v2.7. This dashboard can only inspect requests and
        mark pending approval metadata as approved or rejected.
      </div>

      <div className="approvalFilters" role="tablist" aria-label="Approval status filters">
        {STATUS_FILTERS.map((status) => (
          <button
            aria-selected={statusFilter === status}
            className={`btnSmall ${statusFilter === status ? "btnSave" : "btnOutline"}`}
            key={status}
            onClick={() => setStatusFilter(status)}
            role="tab"
            type="button"
          >
            {status}
          </button>
        ))}
      </div>

      {successMessage && <p className="successText">{successMessage}</p>}

      {approvals.length === 0 ? (
        <p className="stateText">
          {statusFilter === "all"
            ? "No approval requests found."
            : `No ${statusFilter} approval requests found.`}
        </p>
      ) : (
        <div className="approvalLayout">
          <div className="approvalList">
            {approvals.map((approval) => (
              <article
                className={`record approvalRecord ${selected?.id === approval.id ? "approvalRecordSelected" : ""}`}
                key={approval.id}
              >
                <div className="recordHeader">
                  <h3>{approval.title}</h3>
                  <div className="approvalBadgeRow">
                    <StatusBadge approval={approval} />
                    <RiskBadge risk={approval.risk_level} />
                  </div>
                </div>
                <p>{summarizeDescription(approval.description)}</p>
                <div className="metaRow">
                  <span>Action: {approval.action_type}</span>
                  <span>ID: {approval.proposed_action_id ?? "-"}</span>
                  <span>Source: {approval.source}</span>
                  <span>Created: {formatDateTime(approval.created_at)}</span>
                  <span>Expires: {formatDateTime(approval.expires_at)}</span>
                </div>
                <div className="recordActions">
                  <button
                    className="btnSmall btnOutline"
                    onClick={() => inspectApproval(approval.id)}
                    type="button"
                  >
                    Inspect
                  </button>
                </div>
              </article>
            ))}
          </div>

          <div className="approvalDetailPane">
            {selected ? (
              <ApprovalDetails
                actionError={actionError}
                approval={selected}
                isDeciding={isDeciding}
                onApprove={handleApprove}
                onReject={handleReject}
                onReasonChange={setRejectionReason}
                rejectionReason={rejectionReason}
              />
            ) : (
              <div className="approvalDetails approvalDetailsEmpty">
                <p className="eyebrow">Inspection</p>
                <h3>Select an approval request</h3>
                <p>
                  Inspect payload summary, safety notes, and non-execution flags before
                  deciding a pending request.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
