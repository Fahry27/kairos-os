"use client";

import { useEffect, useState } from "react";
import { getProjects, type ApiResult, type Project } from "../lib/api";

function formatDate(value?: string | null) {
  return value ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value)) : "-";
}

export function ProjectsList() {
  const [result, setResult] = useState<ApiResult<Project[]> | null>(null);

  useEffect(() => {
    let mounted = true;

    getProjects().then((nextResult) => {
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
          <p className="eyebrow">Projects</p>
          <h2>Active Work</h2>
        </div>
      </div>
      {!result && <p className="stateText">Loading projects...</p>}
      {result && !result.ok && <p className="errorText">Unable to load projects: {result.error}</p>}
      {result?.ok && result.data.length === 0 && (
        <p className="stateText">No projects yet. When projects exist, they will appear here.</p>
      )}
      {result?.ok && result.data.length > 0 && (
        <div className="stack">
          {result.data.map((project) => (
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
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
