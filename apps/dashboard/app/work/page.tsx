"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ProjectsList } from "../../components/ProjectsList";
import { TasksList } from "../../components/TasksList";

type Tab = "missions" | "tasks";

function WorkInner() {
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get("tab") as Tab) || "missions";
  const [activeTab, setActiveTab] = useState<Tab>(initialTab);

  return (
    <>
      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 24 }}>
        {(["missions", "tasks"] as Tab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={activeTab === tab ? "" : "btnOutline"}
            style={{
              fontSize: 14,
              minHeight: 34,
              padding: "6px 16px",
              fontWeight: activeTab === tab ? 700 : 500,
              textTransform: "capitalize",
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "missions" && <ProjectsList />}
      {activeTab === "tasks" && <TasksList />}
    </>
  );
}

export default function WorkPage() {
  return (
    <div style={{ maxWidth: 900, margin: "0 auto" }}>
      <h1 style={{ fontSize: 28, fontWeight: 720, margin: "0 0 8px" }}>Work</h1>
      <p style={{ color: "var(--muted)", margin: "0 0 24px", fontSize: 15 }}>
        Your missions and tasks.
      </p>
      <Suspense fallback={<p style={{ color: "var(--muted)", fontSize: 14 }}>Loading…</p>}>
        <WorkInner />
      </Suspense>
    </div>
  );
}
