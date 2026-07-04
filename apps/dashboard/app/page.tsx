import { Suspense } from "react";
import { ContinueButton } from "../components/ContinueButton";
import { ApprovalsCard } from "../components/ApprovalsCard";
import { ProjectsList } from "../components/ProjectsList";
import { TasksList } from "../components/TasksList";
import { WorkflowRunsCard } from "../components/WorkflowRunsCard";
import { KAIROS_API_URL } from "../lib/api";

export default function DashboardPage() {
  return (
    <main className="page">
      <header className="topBar">
        <div>
          <p className="eyebrow">Kairos OS</p>
          <h1>Mission Home</h1>
          <p className="subtitle">Daily Operator Console • connected to {KAIROS_API_URL}</p>
        </div>
        <div className="topBarActions">
          <ContinueButton />
        </div>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        
        <Suspense fallback={<p className="stateText">Loading missions...</p>}>
          <ProjectsList />
        </Suspense>

        <Suspense fallback={<p className="stateText">Loading decisions...</p>}>
          <TasksList />
        </Suspense>

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
