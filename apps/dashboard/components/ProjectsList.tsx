"use client";

import { type FormEvent, useEffect, useState } from "react";
import { createProject, getProjects, type ApiResult, type Project } from "../lib/api";

function formatDate(value?: string | null) {
  return value ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value)) : "-";
}

export function ProjectsList() {
  const [result, setResult] = useState<ApiResult<Project[]> | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    let mounted = true;

    loadProjects().then((nextResult) => {
      if (mounted) {
        setResult(nextResult);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  async function loadProjects() {
    return getProjects();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    const trimmedName = name.trim();
    if (!trimmedName) {
      setSubmitError("Project name is required.");
      return;
    }

    setIsSubmitting(true);
    const created = await createProject({
      name: trimmedName,
      description: description.trim() || undefined,
      priority,
    });

    if (created.ok) {
      setName("");
      setDescription("");
      setPriority("medium");
      setResult(await loadProjects());
    } else {
      setSubmitError(`Unable to create project: ${created.error}`);
    }

    setIsSubmitting(false);
  }

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Projects</p>
          <h2>Active Work</h2>
        </div>
      </div>
      <form className="resourceForm" onSubmit={handleSubmit}>
        <label>
          <span>Name</span>
          <input
            maxLength={255}
            onChange={(event) => setName(event.target.value)}
            placeholder="New project"
            value={name}
          />
        </label>
        <label>
          <span>Description</span>
          <textarea
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Optional context"
            rows={2}
            value={description}
          />
        </label>
        <div className="formFooter">
          <label>
            <span>Priority</span>
            <select onChange={(event) => setPriority(event.target.value)} value={priority}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Creating..." : "Create Project"}
          </button>
        </div>
        {submitError && <p className="errorText">{submitError}</p>}
      </form>
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
