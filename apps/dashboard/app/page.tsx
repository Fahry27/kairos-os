import { Suspense } from "react";
import { HealthCard } from "../components/HealthCard";
import { MemoriesList } from "../components/MemoriesList";
import { ProjectsList } from "../components/ProjectsList";
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
