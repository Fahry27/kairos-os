import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import FoundationNotice from "../../components/shell/FoundationNotice";

/**
 * Continue Working — resume where you left off.
 *
 * Architecture:
 *   - Active missions list
 *   - Open decisions card
 *   - Recent workspace sessions
 *
 * Foundation state: static layout ready for live API wiring.
 */
export default function ContinueWorkingPage() {
  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <FoundationNotice label="Continue Working" />

      <SurfacePageHeader
        title="Continue Working"
        description="Resume active missions, decisions, and workspace sessions."
      />

      <SurfaceCard title="Active Missions" badge="2 in progress">
        <div className="stack">
          <div className="record">
            <div className="recordHeader">
              <h3 style={{ fontSize: 16 }}>Active missions appear here</h3>
              <span className="pill" style={{ fontSize: 11 }}>In Progress</span>
            </div>
            <p className="stateText">
              Your active missions with progress indicators, recent updates,
              and quick-resume actions.
            </p>
            <div className="metaRow">
              <span>Last updated: --</span>
            </div>
          </div>
          <div className="record">
            <div className="recordHeader">
              <h3 style={{ fontSize: 16 }}>Continue where you left off</h3>
            </div>
            <p className="stateText">
              Kairos will track your most recent work across all surfaces
              and let you pick up exactly where you stopped.
            </p>
          </div>
        </div>
      </SurfaceCard>

      <div className="dashboardGrid" style={{ marginTop: 24 }}>
        <SurfaceCard title="Open Decisions">
          <div className="record">
            <p className="stateText">
              Decisions awaiting review or action will be listed here with
              context and next steps.
            </p>
          </div>
        </SurfaceCard>

        <SurfaceCard title="Recent Sessions">
          <div className="record">
            <p className="stateText">
              Your recent workspace sessions and AI conversations will
              appear here for quick resumption.
            </p>
          </div>
        </SurfaceCard>
      </div>
    </div>
  );
}
