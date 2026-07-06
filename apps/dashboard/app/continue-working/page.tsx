"use client";

import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";
import { useKairosState } from "../../lib/state";
import { useMissions, useDecisions, useMissionEngine, useRecentTimeline } from "../../lib/runtime";

/**
 * Continue Working — resume where you left off.
 *
 * Connected to runtime via useMissions(), useDecisions(),
 * and useMissionEngine() for selection.
 */
export default function ContinueWorkingPage() {
  const state = useKairosState();
  const missions = useMissions();
  const decisions = useDecisions();
  const { selectedMission, selectMission } = useMissionEngine();

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <SurfacePageHeader
        title="Continue Working"
        description="Resume active missions, decisions, and workspace sessions."
      />

      <SurfaceCard
        title="Recent Missions"
        badge={state.missions.length > 0 ? `${state.missions.length} active` : undefined}
      >
        {missions.loading ? (
          <p className="stateText">Loading missions…</p>
        ) : missions.error ? (
          <p className="errorText">{missions.error}</p>
        ) : state.missions.length > 0 ? (
          <div className="stack">
            {state.missions.map((m) => (
              <div
                key={m.id}
                className="record"
                style={{
                  cursor: "pointer",
                  borderLeft: selectedMission?.id === m.id ? "3px solid var(--accent)" : "3px solid transparent",
                }}
                onClick={() => selectMission(m.id)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") selectMission(m.id);
                }}
                aria-pressed={selectedMission?.id === m.id}
              >
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
          {decisions.loading ? (
            <p className="stateText">Loading decisions…</p>
          ) : decisions.error ? (
            <p className="errorText">{decisions.error}</p>
          ) : state.decisions.length > 0 ? (
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
