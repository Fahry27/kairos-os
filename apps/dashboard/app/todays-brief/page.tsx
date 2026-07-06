import SurfacePageHeader from "../../components/shell/SurfacePageHeader";
import SurfaceCard from "../../components/shell/SurfaceCard";
import SurfaceSection from "../../components/shell/SurfaceSection";
import FoundationNotice from "../../components/shell/FoundationNotice";

/**
 * Today's Brief — your daily digest.
 *
 * Architecture:
 *   - Decisions pending review
 *   - Mission status changes
 *   - Memory / knowledge updates
 *   - System notifications
 *
 * Foundation state: static layout with section structure.
 */
export default function TodaysBriefPage() {
  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <FoundationNotice label="Today's Brief" />

      <SurfacePageHeader
        title="Today's Brief"
        description="Your daily digest: decisions, mission updates, and system notifications."
      />

      <SurfaceCard>
        <SurfaceSection title="Decisions Pending Review">
          <div className="record">
            <p className="stateText">
              Decisions that need your attention today will appear here with
              context, risk level, and recommended action.
            </p>
          </div>
        </SurfaceSection>

        <SurfaceSection title="Mission Updates">
          <div className="record">
            <p className="stateText">
              Status changes and progress updates from active missions
              across all your projects.
            </p>
          </div>
        </SurfaceSection>

        <SurfaceSection title="Memory &amp; Knowledge">
          <div className="record">
            <p className="stateText">
              New memories, knowledge entries, and notable reflections
              captured since your last brief.
            </p>
          </div>
        </SurfaceSection>

        <SurfaceSection title="System">
          <div className="record">
            <p className="stateText">
              Provider health, connector status, and infrastructure
              notifications. Kairos will alert you if anything needs attention.
            </p>
          </div>
        </SurfaceSection>
      </SurfaceCard>
    </div>
  );
}
