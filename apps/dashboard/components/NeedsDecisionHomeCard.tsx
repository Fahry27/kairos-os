"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getTasks, type ApiResult, type Task } from "../lib/api";

function formatDate(value?: string | null) {
  return value ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value)) : "-";
}

export function NeedsDecisionHomeCard() {
  const [result, setResult] = useState<ApiResult<Task[]> | null>(null);

  useEffect(() => {
    let mounted = true;
    getTasks().then((res) => {
      if (mounted) setResult(res);
    });
    return () => { mounted = false; };
  }, []);

  const pendingTasks = result?.ok 
    ? result.data.filter(t => t.status === "pending" || t.status === "open").slice(0, 5) 
    : [];

  return (
    <section className="card cardWide">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Needs Decision</p>
          <h2>Decisions Queue</h2>
        </div>
        <Link href="/decisions" className="btnSmall btnOutline" style={{ textDecoration: 'none' }}>
          Manage Decisions
        </Link>
      </div>

      {!result && <p className="stateText">Loading decisions...</p>}
      {result && !result.ok && <p className="errorText">Unable to load decisions: {result.error}</p>}
      
      {result?.ok && pendingTasks.length === 0 && (
        <p className="stateText">No pending decisions.</p>
      )}

      {result?.ok && pendingTasks.length > 0 && (
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Due</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {pendingTasks.map((task) => (
                <tr key={task.id}>
                  <td><strong>{task.title}</strong></td>
                  <td>{task.status}</td>
                  <td>{task.priority}</td>
                  <td>{formatDate(task.due_date)}</td>
                  <td>
                    <Link 
                      href={`/workspace?goal=${encodeURIComponent(task.title)}&mission_id=${encodeURIComponent(task.project_id || '')}`}
                      className="btnSmall btnSave" 
                      style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center', marginTop: 0 }}
                    >
                      Plan Decision
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
