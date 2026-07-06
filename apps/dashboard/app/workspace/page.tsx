import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";

/**
 * Workspace — your primary surface for planning and executing work.
 *
 * Architecture:
 *   - Goal input area
 *   - Planning canvas (steps, commands, connectors)
 *   - Results / response panel
 *
 * Foundation state: static layout with planning structure.
 * No AI dispatch or decision plan generation yet.
 */
export default function WorkspacePage() {
  return (
    <div style={{ maxWidth: 960, margin: "0 auto" }}>
      <FoundationNotice label="Workspace" />

      <SurfacePageHeader
        title="Workspace"
        description="Your primary surface for planning and executing work."
      />

      {/* Goal input */}
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

      {/* Planning canvas */}
      <div className="dashboardGrid" style={{ marginTop: 24, marginBottom: 24 }}>
        <SurfaceCard title="Plan">
          <div className="stack">
            <div className="record" style={{ borderLeft: "3px solid var(--accent)" }}>
              <div className="recordHeader">
                <h3 style={{ fontSize: 16 }}>Steps will appear here</h3>
                <span className="pill" style={{ fontSize: 11 }}>
                  Approval Required
                </span>
              </div>
              <p className="stateText">
                Kairos will break down your goal into actionable steps with
                commands, connectors, and safety notes.
              </p>
            </div>
            <div className="record">
              <p className="stateText">
                Each step includes a rationale, required capabilities, and
                an approval gate before execution.
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

      {/* Capabilities summary */}
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
    </div>
  );
}
