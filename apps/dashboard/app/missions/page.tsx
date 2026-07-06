import { Suspense } from "react";
import { ProjectsList } from "../../components/ProjectsList";

export default function MissionsPage() {
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto" }}>
      <header className="topBar">
        <div>
          <p className="eyebrow">Kairos</p>
          <h1>Manage Missions</h1>
        </div>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <Suspense fallback={<p className="stateText">Loading missions...</p>}>
          <ProjectsList />
        </Suspense>
      </div>
    </div>
  );
}
