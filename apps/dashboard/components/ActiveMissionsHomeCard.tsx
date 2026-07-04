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
            <Link 
              href={`/workspace?project_id=${encodeURIComponent(project.id)}`} 
              key={project.id}
              style={{ textDecoration: 'none', color: 'inherit', display: 'block' }}
            >
              <article className="record" style={{ cursor: "pointer", transition: "transform 0.2s, box-shadow 0.2s" }} 
                       onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.05)" }}
                       onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "none" }}>
                <div className="recordHeader">
                  <h3>{project.name}</h3>
                  <span className="pill" style={{ background: "var(--background)", borderColor: "var(--panel-border)" }}>{project.status}</span>
                </div>
                <p>{project.description ?? "No description"}</p>
                <div className="metaRow">
                  <span>Priority: {project.priority}</span>
                  <span>Updated: {formatDate(project.updated_at)}</span>
                  <span style={{ marginLeft: "auto", color: "var(--accent)", fontWeight: 500 }}>Open Workspace &rarr;</span>
                </div>
              </article>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
