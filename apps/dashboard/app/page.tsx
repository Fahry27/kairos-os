import { Suspense } from "react";
import { HealthCard } from "../components/HealthCard";
import { AIRuntimeCard } from "../components/AIRuntimeCard";
import { ApprovalsCard } from "../components/ApprovalsCard";
import { ExtensionsCard } from "../components/ExtensionsCard";
import { ConnectorsCard } from "../components/ConnectorsCard";
import { MemoriesList } from "../components/MemoriesList";
import { ProjectsList } from "../components/ProjectsList";
import { StatsOverview } from "../components/StatsOverview";
import { TasksList } from "../components/TasksList";
import { KAIROS_API_URL } from "../lib/api";

export default function DashboardPage() {
  return (
    <main className="page">
      <header className="topBar">
        <div>
          <p className="eyebrow">Kairos OS</p>
          <h1>Local-first Personal AI Operating System</h1>
          <p className="subtitle">Dashboard connected to {KAIROS_API_URL}</p>
        </div>
        <div className="apiBadge">API base URL: {KAIROS_API_URL}</div>
      </header>

      <div className="dashboardGrid">
        <HealthCard />
        <Suspense fallback={<p className="stateText">Loading AI runtime...</p>}>
          <AIRuntimeCard />
        </Suspense>
        <Suspense fallback={<p className="stateText">Loading approvals...</p>}>
          <ApprovalsCard />
        </Suspense>
        <Suspense fallback={<p className="stateText">Loading extensions...</p>}>
          <ExtensionsCard />
        </Suspense>
        <Suspense fallback={<p className="stateText">Loading connectors...</p>}>
          <ConnectorsCard />
        </Suspense>
        <Suspense fallback={<p className="stateText">Loading stats...</p>}>
          <StatsOverview />
        </Suspense>
        <Suspense fallback={<p className="stateText">Loading projects...</p>}>
          <ProjectsList />
        </Suspense>
        <Suspense fallback={<p className="stateText">Loading tasks...</p>}>
          <TasksList />
        </Suspense>
        <Suspense fallback={<p className="stateText">Loading memories...</p>}>
          <MemoriesList />
        </Suspense>
      </div>
    </main>
  );
}
