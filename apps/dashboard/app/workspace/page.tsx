"use client";

import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";
import { useKairosState } from "../../lib/state";

/**
 * Workspace — production planning and execution surface.
 *
 * Panels:
 *   - Goal input
 *   - Planning canvas (steps, commands, connectors)
 *   - Approval panel
 *   - Execution panel
 *   - History / results panel
 *
 * All data flows through useKairosState(). No backend. No fake execution.
 */
export default function WorkspacePage() {
  const state = useKairosState();

  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>
      <FoundationNotice label="Workspace" />

      <SurfacePageHeader
        title="Workspace"
        description="Your primary surface for planning and executing work."
      />

      {/* Goal panel */}
      <SurfaceCard title="What do you want to accomplish?">
        <div style={{ display: "flex", gap: 8 }}>
          <input
            type="text"
            placeholder="Describe your goal..."
            disabled
            style={{
              flex: 1,
              fontSize: 15,
              color: "var(--muted)",
            }}
            aria-label="Workspace goal"
          />
          <button disabled style={{ minWidth: 100 }}>
            Plan
          </button>
        </div>
      </SurfaceCard>

      {/* Planning canvas + Results */}
      <div className="dashboardGrid" style={{ marginTop: 24, marginBottom: 24 }}>
        <SurfaceCard title="Planning Canvas" badge="No AI yet">
          {state.workspaces.length > 0 ? (
            <div className="stack">
              {state.workspaces.map((w) => (
                <div key={w.id} className="record" style={{ borderLeft: "3px solid var(--accent)" }}>
                  <div className="recordHeader">
                    <h3 style={{ fontSize: 16 }}>{w.goal}</h3>
                    <span className="pill" style={{ fontSize: 11 }}>{w.status}</span>
                  </div>
                  <p className="stateText">
                    Steps and commands will be generated for this goal when the AI router is connected.
                  </p>
                  <div className="metaRow">
                    <span>Created: {w.createdAt}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="stack">
              <div className="record" style={{ borderLeft: "3px solid var(--accent)" }}>
                <div className="recordHeader">
                  <h3 style={{ fontSize: 16 }}>Plan steps will appear here</h3>
                  <span className="pill" style={{ fontSize: 11 }}>Approval Required</span>
                </div>
                <p className="stateText">
                  Kairos will break down your goal into actionable steps with
                  commands, connectors, and safety notes. Each step requires
                  approval before execution.
                </p>
              </div>
              <div className="record">
                <p className="stateText">
                  Execution is gated behind approval. Nothing runs without explicit confirmation.
                </p>
              </div>
            </div>
          )}
        </SurfaceCard>

        <SurfaceCard title="Approval Panel">
          <div className="record">
            <p className="stateText">
              Pending approvals for steps, commands, and actions will appear here.
              Approve or reject each item individually.
            </p>
          </div>
        </SurfaceCard>
      </div>

      {/* Capabilities + History */}
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
                <div key={w.id} className="record">
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
    </div>
  );
}
