import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";

/**
 * Good Morning — your morning briefing surface.
 *
 * Architecture:
 *   - Time-based greeting header
 *   - Status overview cards (calendar, tasks, priorities)
 *   - Quick-glance memory / note section
 *
 * Foundation state: static layout ready for live API wiring.
 */
export default function GoodMorningPage() {
  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <FoundationNotice label="Good Morning" />

      <SurfacePageHeader
        title="Good Morning"
        description="Your morning briefing, calendar overview, and priority summary."
      />

      <div className="dashboardGrid" style={{ marginBottom: 24 }}>
        <SurfaceCard eyebrow="Today" title="Calendar">
          <div className="stack">
            <div className="record">
              <p className="stateText">
                Calendar integration will show your upcoming events and
                meetings here.
              </p>
            </div>
          </div>
        </SurfaceCard>

        <SurfaceCard eyebrow="Priority" title="Tasks">
          <div className="stack">
            <div className="record">
              <p className="stateText">
                Your highest-priority tasks and deadlines will appear here
                each morning.
              </p>
            </div>
          </div>
        </SurfaceCard>
      </div>

      <SurfaceCard title="Morning Briefing">
        <div className="stack">
          <div className="record">
            <div className="recordHeader">
              <h3 style={{ fontSize: 16 }}>While you were away</h3>
            </div>
            <p className="stateText">
              Kairos will summarize decisions, mission updates, and
              notifications that arrived since you last logged in.
            </p>
          </div>
          <div className="record">
            <div className="recordHeader">
              <h3 style={{ fontSize: 16 }}>Today&apos;s focus</h3>
            </div>
            <p className="stateText">
              Your top three priorities for the day, drawn from active
              missions and open decisions.
            </p>
          </div>
        </div>
      </SurfaceCard>
    </div>
  );
}
