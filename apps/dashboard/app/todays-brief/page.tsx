"use client";

import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import SurfaceSection from "../../components/shell/SurfaceSection";
import FoundationNotice from "../../components/shell/FoundationNotice";
import { useKairosState } from "../../lib/state";
import { useBriefRuntime } from "../../lib/runtime";

/**
 * Today's Brief — production daily digest with runtime refresh.
 *
 * Sections:
 *   - Priorities
 *   - Calendar (placeholder for future integration)
 *   - Mission Summary
 *   - Pending Decisions
 *   - System Health
 *   - Memory
 *
 * useBriefRuntime() provides refresh coordination across all sections.
 */
export default function TodaysBriefPage() {
  const state = useKairosState();
  const brief = useBriefRuntime();

  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <FoundationNotice label="Today's Brief" />

      <SurfacePageHeader
        title="Today's Brief"
        description={`${new Date(state.todayDate).toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}`}
      >
        <button
          className="btnOutline btnSmall"
          onClick={brief.refresh}
          style={{ borderColor: "var(--panel-border)" }}
        >
          Refresh
        </button>
      </SurfacePageHeader>

      {brief.lastRefreshed && (
        <p className="stateText" style={{ marginTop: -20, marginBottom: 24 }}>
          Last refreshed: {new Date(brief.lastRefreshed).toLocaleTimeString()}
        </p>
      )}

      <div className="dashboardGrid" style={{ marginBottom: 24 }}>
        <SurfaceCard eyebrow="Today" title="Priorities">
          {state.missions.length > 0 ? (
            <div className="stack">
              {state.missions.slice(0, 3).map((m) => (
                <div key={m.id} className="record">
                  <p style={{ fontWeight: 600, margin: 0 }}>{m.name}</p>
                  <span className={`pill ${m.priority === "critical" ? "approvalBadge-rejected" : ""}`} style={{ marginTop: 6 }}>
                    {m.priority}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="stateText">Priorities will appear here once you create missions and decisions.</p>
          )}
        </SurfaceCard>

        <SurfaceCard eyebrow="Upcoming" title="Calendar">
          <p className="stateText">
            Calendar integration coming in a future sprint. Your daily schedule,
            deadlines, and reminders will appear here.
          </p>
        </SurfaceCard>
      </div>

      <SurfaceCard>
        <SurfaceSection title="Mission Summary">
          {state.missions.length > 0 ? (
            <div className="statGrid" style={{ marginBottom: 12 }}>
              <div>
                <dt>Active</dt>
                <dd>{state.missions.filter((m) => m.status === "executing" || m.status === "approved").length}</dd>
              </div>
              <div>
                <dt>Completed</dt>
                <dd>{state.missions.filter((m) => m.status === "completed").length}</dd>
              </div>
              <div>
                <dt>Pending</dt>
                <dd>{state.missions.filter((m) => m.status === "awaiting_approval" || m.status === "planning").length}</dd>
              </div>
            </div>
          ) : (
            <div className="record">
              <p className="stateText">No mission data available. Connect the API to see your mission summary.</p>
            </div>
          )}
        </SurfaceSection>

        <SurfaceSection title="Pending Decisions">
          {state.decisions.length > 0 ? (
            <div className="stack">
              {state.decisions.slice(0, 3).map((d) => (
                <div key={d.id} className="record">
                  <div className="recordHeader">
                    <p style={{ fontWeight: 600, margin: 0 }}>{d.title}</p>
                    <span className="pill" style={{ fontSize: 11 }}>{d.priority}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="record">
              <p className="stateText">Pending decisions and approvals will appear here.</p>
            </div>
          )}
        </SurfaceSection>

        <SurfaceSection title="System Health">
          <div className="record">
            <p className="stateText">
              Provider health, connector status, and infrastructure notifications.
              Kairos will alert you if anything needs attention.
            </p>
          </div>
        </SurfaceSection>

        <SurfaceSection title="Memory">
          {state.memories.length > 0 ? (
            <div className="stack">
              {state.memories.slice(0, 3).map((m) => (
                <div key={m.id} className="record">
                  <p className="stateText">{m.snippet}</p>
                  <div className="metaRow" style={{ marginTop: 6 }}>
                    {m.tags.map((tag) => (
                      <span key={tag} className="pill" style={{ fontSize: 11 }}>{tag}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="record">
              <p className="stateText">Recent memories and knowledge entries will appear here.</p>
            </div>
          )}
        </SurfaceSection>
      </SurfaceCard>
    </div>
  );
}
