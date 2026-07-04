"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getProjects, type ApiResult, type Project } from "../lib/api";

function formatDate(value?: string | null) {
  return value ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value)) : "-";
}

export function ActiveMissionsHomeCard() {
  const [result, setResult] = useState<ApiResult<Project[]> | null>(null);

  useEffect(() => {
    let mounted = true;
    getProjects().then((res) => {
      if (mounted) setResult(res);
    });
    return () => { mounted = false; };
  }, []);

  const activeProjects = result?.ok 
    ? result.data.filter(p => p.status !== "done").slice(0, 5) 
    : [];

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Active Missions</p>
          <h2>Mission Control</h2>
        </div>
        <Link href="/missions" className="btnSmall btnOutline" style={{ textDecoration: 'none' }}>
          Manage Missions
        </Link>
      </div>

      {!result && <p className="stateText">Loading missions...</p>}
      {result && !result.ok && <p className="errorText">Unable to load missions: {result.error}</p>}
      
      {result?.ok && activeProjects.length === 0 && (
        <p className="stateText">No active missions right now.</p>
      )}

      {result?.ok && activeProjects.length > 0 && (
        <div className="stack">
          {activeProjects.map((project) => (
            <article className="record" key={project.id}>
              <div className="recordHeader">
                <h3>{project.name}</h3>
                <span className="pill">{project.status}</span>
              </div>
              <p>{project.description ?? "No description"}</p>
              <div className="metaRow">
                <span>Priority: {project.priority}</span>
                <span>Updated: {formatDate(project.updated_at)}</span>
              </div>
              <div className="recordActions">
                <Link 
                  href={`/workspace?project_id=${encodeURIComponent(project.id)}`}
                  className="btnSmall btnSave" 
                  style={{ textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
                >
                  Continue Mission
                </Link>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
