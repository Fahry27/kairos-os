"use client";

import { useEffect, useState } from "react";
import { getTasks, type ApiResult, type Task } from "../lib/api";

function formatDate(value?: string | null) {
  return value ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value)) : "-";
}

export function TasksList() {
  const [result, setResult] = useState<ApiResult<Task[]> | null>(null);

  useEffect(() => {
    let mounted = true;

    getTasks().then((nextResult) => {
      if (mounted) {
        setResult(nextResult);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Tasks</p>
          <h2>Queue</h2>
        </div>
      </div>
      {!result && <p className="stateText">Loading tasks...</p>}
      {result && !result.ok && <p className="errorText">Unable to load tasks: {result.error}</p>}
      {result?.ok && result.data.length === 0 && (
        <p className="stateText">No tasks yet. Open work will appear here.</p>
      )}
      {result?.ok && result.data.length > 0 && (
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Project</th>
                <th>Due</th>
              </tr>
            </thead>
            <tbody>
              {result.data.map((task) => (
                <tr key={task.id}>
                  <td>
                    <strong>{task.title}</strong>
                  </td>
                  <td>{task.status}</td>
                  <td>{task.priority}</td>
                  <td>{task.project_id ?? "-"}</td>
                  <td>{formatDate(task.due_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
