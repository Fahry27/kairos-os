"use client";

import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";
import { useKairosState } from "../../lib/state";
import { useWorkspaceRuntime, useKnowledgeForWorkspace } from "../../lib/runtime";

/**
 * Workspace — production planning and execution surface with runtime.
 *
 * Panels:
 *   - Goal input
 *   - Planning canvas (steps, commands, connectors)
 *   - Approval panel
 *   - Execution panel
 *   - History / results
 *
 * useWorkspaceRuntime() provides workspace selection, panel sync,
 * and approval state management.
 */
export default function WorkspacePage() {
  const state = useKairosState();
  const {
    activeWorkspaceId,
    selectWorkspace,
    activePanel,
    setActivePanel,
    pendingApprovals,
  } = useWorkspaceRuntime();

  const workspaceKnowledge = useKnowledgeForWorkspace(activeWorkspaceId);

  const activeWorkspace = state.workspaces.find((w) => w.id === activeWorkspaceId) ?? null;

  const PANELS = [
    { key: "plan", label: "Plan" },
    { key: "approval", label: "Approval" },
    { key: "execution", label: "Execute" },
    { key: "history", label: "History" },
  ];

  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>
      <FoundationNotice label="Workspace" />

      <SurfacePageHeader
        title="Workspace"
        description={
          activeWorkspace
            ? `Active: ${activeWorkspace.goal}`
            : "Your primary surface for planning and executing work."
        }
      >
        {state.workspaces.length > 0 && (
          <select
            value={activeWorkspaceId ?? ""}
            onChange={(e) => selectWorkspace(e.target.value || null)}
            style={{ maxWidth: 220, fontSize: 13 }}
            aria-label="Select workspace"
          >
            <option value="">New workspace</option>
            {state.workspaces.map((w) => (
              <option key={w.id} value={w.id}>
                {w.goal.slice(0, 40)}
              </option>
            ))}
          </select>
        )}
      </SurfacePageHeader>

      {/* Panel tabs */}
      {activeWorkspace && (
        <div style={{ display: "flex", gap: 4, marginBottom: 24 }}>
          {PANELS.map((panel) => (
            <button
              key={panel.key}
              onClick={() => setActivePanel(panel.key)}
              className={activePanel === panel.key ? "" : "btnOutline"}
              style={{
                fontSize: 13,
                minHeight: 32,
                padding: "4px 14px",
                fontWeight: activePanel === panel.key ? 700 : 500,
              }}
            >
              {panel.label}
              {panel.key === "approval" && pendingApprovals > 0 && (
                <span
                  style={{
                    marginLeft: 6,
                    background: "var(--amber-soft)",
                    color: "var(--amber)",
                    borderRadius: "999px",
                    padding: "1px 7px",
                    fontSize: 11,
                    fontWeight: 700,
                  }}
                >
                  {pendingApprovals}
                </span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Goal panel */}
      <SurfaceCard title="What do you want to accomplish?">
        <div style={{ display: "flex", gap: 8 }}>
          <input
            type="text"
            placeholder="Describe your goal..."
            disabled={!activeWorkspace}
            style={{
              flex: 1,
              fontSize: 15,
              color: activeWorkspace ? undefined : "var(--muted)",
            }}
            aria-label="Workspace goal"
            defaultValue={activeWorkspace?.goal ?? ""}
          />
          <button disabled style={{ minWidth: 100 }}>
            Plan
          </button>
        </div>
      </SurfaceCard>

      {/* Panel content */}
      {activeWorkspace && activePanel === "plan" && (
        <div className="dashboardGrid" style={{ marginTop: 24, marginBottom: 24 }}>
          <SurfaceCard title="Planning Canvas" badge="Approval Required">
            <div className="stack">
              <div className="record" style={{ borderLeft: "3px solid var(--accent)" }}>
                <div className="recordHeader">
                  <h3 style={{ fontSize: 16 }}>Plan steps for this goal</h3>
                  <span className="pill" style={{ fontSize: 11 }}>Draft</span>
                </div>
                <p className="stateText">
                  Kairos will break down this goal into actionable steps with
                  commands, connectors, and safety notes.
                </p>
              </div>
              {workspaceKnowledge.length > 0 && (
                <div className="record">
                  <p className="stateText">
                    {workspaceKnowledge.length} knowledge items available for this workspace.
                  </p>
                </div>
              )}
              <div className="record">
                <p className="stateText">
                  Each step requires approval before execution. Nothing runs without
                  explicit confirmation.
                </p>
              </div>
            </div>
          </SurfaceCard>

          <SurfaceCard title="Results">
            <div className="record">
              <p className="stateText">
                Plan results and execution feedback will appear in this panel.
                Shows parsed steps, command suggestions, and safety analysis.
              </p>
            </div>
          </SurfaceCard>
        </div>
      )}

      {activeWorkspace && activePanel === "approval" && (
        <SurfaceCard title="Approval Panel" badge={pendingApprovals > 0 ? `${pendingApprovals} pending` : undefined}>
          <div className="record">
            <p className="stateText">
              Pending approvals for steps, commands, and actions will appear here.
              Approve or reject each item individually before execution proceeds.
            </p>
          </div>
        </SurfaceCard>
      )}

      {activeWorkspace && activePanel === "execution" && (
        <SurfaceCard title="Execution">
          <div className="record">
            <p className="stateText">
              Execution is gated behind approval. Once steps are approved,
              they will run in sequence with real-time feedback.
            </p>
          </div>
        </SurfaceCard>
      )}

      {activeWorkspace && activePanel === "history" && (
        <SurfaceCard title="History">
          <div className="record">
            <p className="stateText">
              Previous runs and outcomes for this workspace goal will appear here.
            </p>
          </div>
        </SurfaceCard>
      )}

      {/* No workspace selected — show capabilities */}
      {!activeWorkspace && (
        <>
          <div className="dashboardGrid" style={{ marginTop: 24, marginBottom: 24 }}>
            <SurfaceCard title="Planning Canvas" badge="No AI yet">
              <div className="record" style={{ borderLeft: "3px solid var(--accent)" }}>
                <div className="recordHeader">
                  <h3 style={{ fontSize: 16 }}>Plan steps will appear here</h3>
                  <span className="pill" style={{ fontSize: 11 }}>Approval Required</span>
                </div>
                <p className="stateText">
                  Kairos will break down your goal into actionable steps with
                  commands, connectors, and safety notes.
                </p>
              </div>
            </SurfaceCard>
            <SurfaceCard title="Approval Panel">
              <div className="record">
                <p className="stateText">Pending approvals for steps and actions will appear here.</p>
              </div>
            </SurfaceCard>
          </div>

          <div className="dashboardGrid">
            <SurfaceCard title="Available Capabilities">
              <div className="statGrid">
                <div>
                  <dt>Commands</dt>
                  <dd>--</dd>
                </div>
                <div>
                  <dt>Plugins</dt>
                  <dd>--</dd>
                </div>
                <div>
                  <dt>Connectors</dt>
                  <dd>--</dd>
                </div>
                <div>
                  <dt>Workflows</dt>
                  <dd>--</dd>
                </div>
              </div>
              <p className="stateText" style={{ marginTop: 12 }}>
                Available commands, plugins, and connectors will be listed here
                once the provider router is wired to this surface.
              </p>
            </SurfaceCard>

            <SurfaceCard title="History">
              {state.workspaces.length > 0 ? (
                <div className="stack">
                  {state.workspaces.map((w) => (
                    <div
                      key={w.id}
                      className="record"
                      style={{ cursor: "pointer" }}
                      onClick={() => selectWorkspace(w.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") selectWorkspace(w.id);
                      }}
                    >
                      <p style={{ fontWeight: 600, margin: 0 }}>{w.goal}</p>
                      <div className="metaRow" style={{ marginTop: 4 }}>
                        <span>{w.status} &middot; {w.createdAt}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="record">
                  <p className="stateText">
                    Previous workspace sessions and their outcomes will appear here.
                  </p>
                </div>
              )}
            </SurfaceCard>
          </div>
        </>
      )}
    </div>
  );
}
