import { Suspense } from "react";
import { TasksList } from "../../components/TasksList";

export default function DecisionsPage() {
  return (
    <main className="page">
      <header className="topBar">
        <div>
          <p className="eyebrow">Kairos OS</p>
          <h1>Manage Decisions</h1>
        </div>
      </header>

      <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
        <Suspense fallback={<p className="stateText">Loading decisions...</p>}>
          <TasksList />
        </Suspense>
      </div>
    </main>
  );
}
