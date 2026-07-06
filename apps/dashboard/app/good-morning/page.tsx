"use client";

import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import { useKairosState } from "../../lib/state";
import { useMissions, useDecisions, useTodayTimeline } from "../../lib/runtime";

/**
 * Good Morning — production morning dashboard.
 *
 * Sections:
 *   - Greeting & today's date
 *   - Focus (top 3 priorities from missions/decisions)
 *   - Daily goals
 *   - Mission overview
 *   - Important reminders
 *
 * Connected to runtime via useMissions() and useDecisions(),
 * which fetch live API data and dispatch into shared state.
 */
export default function GoodMorningPage() {
  const state = useKairosState();

  // Runtime hooks — fetch API data and populate state on mount
  const missions = useMissions();
  const decisions = useDecisions();

  const todayEvents = useTodayTimeline();

  const missionCount = state.missions.length;
  const decisionCount = state.decisions.length;
  const hasData = missionCount > 0 || decisionCount > 0;
  const loading = missions.loading || decisions.loading;
  const apiError = missions.error || decisions.error;

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <SurfacePageHeader
        title="Good Morning"
        description={`${new Date(state.todayDate).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}`}
      />

      <div className="dashboardGrid" style={{ marginBottom: 24 }}>
        <SurfaceCard eyebrow="Focus" title="Top Priorities">
          {loading ? (
            <p className="stateText">Loading priorities…</p>
          ) : apiError ? (
            <p className="errorText">API unavailable — {apiError}</p>
          ) : hasData ? (
            <div className="stack">
              {state.missions.slice(0, 2).map((m) => (
                <div key={m.id} className="record" style={{ borderLeft: "3px solid var(--accent)" }}>
                  <div className="recordHeader">
                    <h3 style={{ fontSize: 16 }}>{m.name}</h3>
                    <span className={`pill ${m.priority === "critical" ? "approvalBadge-rejected" : ""}`}>
                      {m.priority}
                    </span>
                  </div>
                  {m.description && <p className="stateText">{m.description}</p>}
                </div>
              ))}
            </div>
          ) : (
            <p className="stateText">
              No active missions yet. Create a mission to see your top priorities here each morning.
            </p>
          )}
        </SurfaceCard>

        <SurfaceCard eyebrow="Today" title="Daily Goals">
          {decisionCount > 0 ? (
            <div className="stack">
              {state.decisions.slice(0, 3).map((d) => (
                <div key={d.id} className="record">
                  <p style={{ fontWeight: 600, margin: 0 }}>{d.title}</p>
                  {d.description && <p className="stateText" style={{ marginTop: 4 }}>{d.description}</p>}
                </div>
              ))}
            </div>
          ) : (
            <p className="stateText">
              Set goals and open decisions to populate your daily focus.
            </p>
          )}
        </SurfaceCard>
      </div>

      <SurfaceCard title="Mission Overview">
        <div className="statGrid">
          <div>
            <dt>Active Missions</dt>
            <dd>{missionCount}</dd>
          </div>
          <div>
            <dt>Open Decisions</dt>
            <dd>{decisionCount}</dd>
          </div>
          <div>
            <dt>Memories</dt>
            <dd>{state.memories.length}</dd>
          </div>
          <div>
            <dt>Today's Events</dt>
            <dd>{todayEvents.length}</dd>
          </div>
        </div>
        <p className="stateText" style={{ marginTop: 12 }}>
          Connect to the Kairos Core API to see live data populate your morning dashboard.
        </p>
      </SurfaceCard>
    </div>
  );
}
