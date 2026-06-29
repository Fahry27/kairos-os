"use client";

import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  getWorkflowRun,
  listWorkflowRuns,
  type ApiResult,
  type WorkflowRun,
  type WorkflowRunListStatus,
} from "../lib/api";

const RUN_STATUS_FILTERS: WorkflowRunListStatus[] = ["all", "running", "succeeded", "failed"];

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function renderSummary(value?: Record<string, unknown> | null) {
  if (!value) return "No summary recorded.";
  return JSON.stringify(value, null, 2);
}

function RunStatusBadge({ status }: { status: WorkflowRun["status"] }) {
  return <span className={`workflowRunBadge workflowRunBadge-${status}`}>{status}</span>;
}

function WorkflowRunDetails({ run }: { run: WorkflowRun }) {
  return (
    <div className="approvalDetails">
      <div className="approvalDetailsHeader">
        <div>
          <p className="eyebrow">Inspection</p>
          <h3>{run.target_type}</h3>
        </div>
        <RunStatusBadge status={run.status} />
      </div>

      <dl className="approvalMetaGrid">
        <div>
          <dt>Run ID</dt>
          <dd>{run.id}</dd>
        </div>
        <div>
          <dt>Approval ID</dt>
          <dd>{run.approval_id}</dd>
        </div>
        <div>
          <dt>HTTP Status</dt>
          <dd>{run.http_status_code ?? "-"}</dd>
        </div>
        <div>
          <dt>Started</dt>
          <dd>{formatDateTime(run.started_at)}</dd>
        </div>
        <div>
          <dt>Finished</dt>
          <dd>{formatDateTime(run.finished_at)}</dd>
        </div>
        <div>
          <dt>Error</dt>
          <dd>{run.sanitized_error ?? "-"}</dd>
        </div>
      </dl>

      <div className="approvalDetailBlock">
        <h4>Request Summary</h4>
        <pre>{renderSummary(run.request_summary)}</pre>
      </div>

      <div className="approvalDetailBlock">
        <h4>Response Summary</h4>
        <pre>{renderSummary(run.response_summary)}</pre>
      </div>
    </div>
  );
}

export function WorkflowRunsCard() {
  const [statusFilter, setStatusFilter] = useState<WorkflowRunListStatus>("all");
  const [approvalFilter, setApprovalFilter] = useState("");
  const [activeApprovalFilter, setActiveApprovalFilter] = useState("");
  const [result, setResult] = useState<ApiResult<WorkflowRun[]> | null>(null);
  const [selected, setSelected] = useState<WorkflowRun | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  async function loadRuns(nextStatus = statusFilter, nextApprovalId = activeApprovalFilter) {
    setIsRefreshing(true);
    const nextResult = await listWorkflowRuns(nextStatus, nextApprovalId || undefined);
    setResult(nextResult);
    setIsRefreshing(false);
    return nextResult;
  }

  useEffect(() => {
    let mounted = true;
    setResult(null);
    setSelected(null);
    setActionError(null);

    listWorkflowRuns(statusFilter, activeApprovalFilter || undefined).then((nextResult) => {
      if (mounted) {
        setResult(nextResult);
      }
    });

    return () => {
      mounted = false;
    };
  }, [statusFilter, activeApprovalFilter]);

  const runs = useMemo(() => (result?.ok ? result.data : []), [result]);

  async function inspectRun(runId: string) {
    setActionError(null);
    const detail = await getWorkflowRun(runId);
    if (detail.ok) {
      setSelected(detail.data);
    } else {
      setActionError(`Unable to load workflow run details: ${detail.error}`);
      const fallback = runs.find((run) => run.id === runId) ?? null;
      setSelected(fallback);
    }
  }

  async function handleRefresh() {
    setActionError(null);
    await loadRuns();
  }

  function handleApprovalFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSelected(null);
    setActiveApprovalFilter(approvalFilter.trim());
  }

  function clearApprovalFilter() {
    setApprovalFilter("");
    setSelected(null);
    setActiveApprovalFilter("");
  }

  if (!result) {
    return (
      <section className="card cardWide">
        <p className="eyebrow">Workflow Runs</p>
        <h2>Loading audit trail...</h2>
      </section>
    );
  }

  if (!result.ok) {
    return (
      <section className="card cardWide">
        <div className="sectionHeader">
          <div>
            <p className="eyebrow">Workflow Runs</p>
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
          <p className="eyebrow">Workflow Runs</p>
          <h2>Audit Trail</h2>
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
        Read-only sanitized history. No trigger, retry, approval, or execution controls are
        available here.
      </div>

      <div className="approvalFilters" role="tablist" aria-label="Workflow run status filters">
        {RUN_STATUS_FILTERS.map((status) => (
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

      <form className="workflowRunFilterForm" onSubmit={handleApprovalFilterSubmit}>
        <label>
          <span>Approval ID</span>
          <input
            onChange={(event) => setApprovalFilter(event.target.value)}
            placeholder="Filter by approval UUID"
            value={approvalFilter}
          />
        </label>
        <button className="btnSmall btnSave" type="submit">
          Filter
        </button>
        <button className="btnSmall btnOutline" onClick={clearApprovalFilter} type="button">
          Clear
        </button>
      </form>

      {actionError && <p className="errorText">{actionError}</p>}

      {runs.length === 0 ? (
        <p className="stateText">
          {statusFilter === "all"
            ? "No workflow runs found."
            : `No ${statusFilter} workflow runs found.`}
        </p>
      ) : (
        <div className="approvalLayout">
          <div className="approvalList">
            {runs.map((run) => (
              <article
                className={`record approvalRecord ${selected?.id === run.id ? "approvalRecordSelected" : ""}`}
                key={run.id}
              >
                <div className="recordHeader">
                  <h3>{run.target_type}</h3>
                  <RunStatusBadge status={run.status} />
                </div>
                <div className="metaRow">
                  <span>Approval: {run.approval_id}</span>
                  <span>HTTP: {run.http_status_code ?? "-"}</span>
                  <span>Started: {formatDateTime(run.started_at)}</span>
                  <span>Finished: {formatDateTime(run.finished_at)}</span>
                </div>
                {run.sanitized_error && <p className="errorText">{run.sanitized_error}</p>}
                <div className="recordActions">
                  <button
                    className="btnSmall btnOutline"
                    onClick={() => inspectRun(run.id)}
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
              <WorkflowRunDetails run={selected} />
            ) : (
              <div className="approvalDetails approvalDetailsEmpty">
                <p className="eyebrow">Inspection</p>
                <h3>Select a workflow run</h3>
                <p>Inspect sanitized request and response summaries.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
