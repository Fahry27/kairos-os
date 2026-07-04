import { Suspense } from "react";
import { ContinueHero } from "../components/ContinueHero";
import { ConnectedProvidersCard } from "../components/ConnectedProvidersCard";
import { ApprovalsCard } from "../components/ApprovalsCard";
import { ActiveMissionsHomeCard } from "../components/ActiveMissionsHomeCard";
import { NeedsDecisionHomeCard } from "../components/NeedsDecisionHomeCard";
import { WorkflowRunsCard } from "../components/WorkflowRunsCard";
import { KAIROS_API_URL } from "../lib/api";

export default function DashboardPage() {
  return (
    <main className="page" style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <header className="topBar" style={{ borderBottom: 'none', paddingBottom: '0' }}>
        <div>
          <p className="eyebrow">Kairos OS</p>
          <h1>Mission Home</h1>
          <p className="subtitle">Daily Operator Console • connected to {KAIROS_API_URL}</p>
        </div>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: "32px", marginTop: "16px" }}>
        
        <ContinueHero />
        
        <ConnectedProvidersCard />

        <div className="dashboardGrid">
          <Suspense fallback={<p className="stateText">Loading missions...</p>}>
            <ActiveMissionsHomeCard />
          </Suspense>

          <Suspense fallback={<p className="stateText">Loading decisions...</p>}>
            <NeedsDecisionHomeCard />
          </Suspense>
        </div>

        <div className="dashboardGrid">
          <Suspense fallback={<p className="stateText">Loading approvals...</p>}>
            <ApprovalsCard />
          </Suspense>
          <Suspense fallback={<p className="stateText">Loading outcomes...</p>}>
            <WorkflowRunsCard />
          </Suspense>
        </div>
        
      </div>
    </main>
  );
}
