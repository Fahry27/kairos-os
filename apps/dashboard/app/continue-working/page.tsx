"use client";

import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";
import { useKairosState } from "../../lib/state";

/**
 * Continue Working — resume where you left off.
 *
 * Sections:
 *   - Recent missions
 *   - Recently opened workspace
 *   - Pending approvals
 *   - Recent AI sessions
 *
 * All data flows through useKairosState(). No fake values.
 */
export default function ContinueWorkingPage() {
  const state = useKairosState();

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <FoundationNotice label="Continue Working" />

      <SurfacePageHeader
        title="Continue Working"
        description="Resume active missions, decisions, and workspace sessions."
      />

      <SurfaceCard title="Recent Missions" badge={state.missions.length > 0 ? `${state.missions.length} active` : undefined}>
        {state.missions.length > 0 ? (
          <div className="stack">
            {state.missions.map((m) => (
              <div key={m.id} className="record">
                <div className="recordHeader">
                  <h3 style={{ fontSize: 16 }}>{m.name}</h3>
                  <span className="pill" style={{ fontSize: 11 }}>{m.status}</span>
                </div>
                {m.description && <p className="stateText">{m.description}</p>}
                <div className="metaRow">
                  <span>Updated: {m.updatedAt}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="stateText">
            Your active missions will appear here. Connect to the Kairos Core API to
            continue where you left off.
          </p>
        )}
      </SurfaceCard>

      <div className="dashboardGrid" style={{ marginTop: 24 }}>
        <SurfaceCard title="Open Decisions">
          {state.decisions.length > 0 ? (
            <div className="stack">
              {state.decisions.slice(0, 3).map((d) => (
                <div key={d.id} className="record">
                  <p style={{ fontWeight: 600, margin: 0 }}>{d.title}</p>
                  <div className="metaRow" style={{ marginTop: 6 }}>
                    <span>Priority: {d.priority}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="stateText">
              Decisions awaiting review. New decisions will appear when the API is connected.
            </p>
          )}
        </SurfaceCard>

        <SurfaceCard title="Recent Sessions">
          {state.workspaces.length > 0 ? (
            <div className="stack">
              {state.workspaces.slice(0, 3).map((w) => (
                <div key={w.id} className="record">
                  <p style={{ fontWeight: 600, margin: 0 }}>{w.goal}</p>
                  <div className="metaRow" style={{ marginTop: 6 }}>
                    <span>{w.status} &middot; {w.updatedAt}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="stateText">
              Your recent workspace sessions and AI conversations will appear here.
            </p>
          )}
        </SurfaceCard>
      </div>
    </div>
  );
}
