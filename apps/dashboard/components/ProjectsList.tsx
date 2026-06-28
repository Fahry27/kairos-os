"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";
import {
  createProject,
  deleteProject,
  getProjects,
  updateProject,
  type ApiResult,
  type Project,
} from "../lib/api";

function formatDate(value?: string | null) {
  return value ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value)) : "-";
}

function ProjectItem({
  project,
  onMutated,
  isFocused,
  onFocus,
}: {
  project: Project;
  onMutated: () => void;
  isFocused: boolean;
  onFocus: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const [editName, setEditName] = useState(project.name);
  const [editDescription, setEditDescription] = useState(project.description ?? "");
  const [editPriority, setEditPriority] = useState(project.priority);

  function startEditing() {
    setEditName(project.name);
    setEditDescription(project.description ?? "");
    setEditPriority(project.priority);
    setEditError(null);
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
    setEditError(null);
  }

  async function handleSave() {
    const trimmed = editName.trim();
    if (!trimmed) {
      setEditError("Name is required.");
      return;
    }

    setIsSaving(true);
    const result = await updateProject(project.id, {
      name: trimmed,
      description: editDescription.trim() || null,
      priority: editPriority,
    });

    if (result.ok) {
      setEditing(false);
      onMutated();
    } else {
      setEditError(`Save failed: ${result.error}`);
    }
    setIsSaving(false);
  }

  async function handleDelete() {
    if (!window.confirm(`Delete project "${project.name}"? This cannot be undone.`)) {
      return;
    }

    const result = await deleteProject(project.id);
    if (result.ok) {
      onMutated();
    } else {
      setEditError(`Delete failed: ${result.error}`);
    }
  }

  if (editing) {
    return (
      <article className="record" key={project.id}>
        <div className="editForm">
          <label>
            <span>Name</span>
            <input
              maxLength={255}
              onChange={(e) => setEditName(e.target.value)}
              value={editName}
            />
          </label>
          <label>
            <span>Description</span>
            <textarea
              onChange={(e) => setEditDescription(e.target.value)}
              rows={2}
              value={editDescription}
            />
          </label>
          <div className="editFormFooter">
            <label>
              <span>Priority</span>
              <select onChange={(e) => setEditPriority(e.target.value)} value={editPriority}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </label>
            <button className="btnSmall btnSave" disabled={isSaving} onClick={handleSave} type="button">
              {isSaving ? "Saving..." : "Save"}
            </button>
            <button className="btnSmall btnOutline" disabled={isSaving} onClick={cancelEditing} type="button">
              Cancel
            </button>
          </div>
          {editError && <p className="errorText">{editError}</p>}
        </div>
      </article>
    );
  }

  return (
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
        {!isFocused && (
          <button className="btnSmall btnOutline" onClick={onFocus} type="button">
            View
          </button>
        )}
        <button className="btnSmall btnOutline" onClick={startEditing} type="button">
          Edit
        </button>
        <button className="btnSmall btnDanger" onClick={handleDelete} type="button">
          Delete
        </button>
      </div>
      {editError && <p className="errorText">{editError}</p>}
    </article>
  );
}

export function ProjectsList() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const focusedProjectId = searchParams.get("project_id");

  const [result, setResult] = useState<ApiResult<Project[]> | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");

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

  async function refresh() {
    setResult(await loadProjects());
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
      await refresh();
    } else {
      setSubmitError(`Unable to create project: ${created.error}`);
    }

    setIsSubmitting(false);
  }

  function handleFocus(projectId: string) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("project_id", projectId);
    router.push(`/?${params.toString()}`);
  }

  function handleClearFocus() {
    const params = new URLSearchParams(searchParams.toString());
    params.delete("project_id");
    router.push(`/?${params.toString()}`);
  }

  const filteredProjects = result?.ok
    ? result.data.filter((p) => {
        if (focusedProjectId && p.id !== focusedProjectId) return false;
        const q = searchQuery.toLowerCase();
        return (
          p.name.toLowerCase().includes(q) ||
          (p.description?.toLowerCase() || "").includes(q)
        );
      })
    : [];

  const focusedProject = result?.ok && focusedProjectId
    ? result.data.find((p) => p.id === focusedProjectId)
    : null;

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Projects</p>
          <h2>Active Work</h2>
        </div>
      </div>

      {focusedProjectId && (
        <div style={{
          marginBottom: 16,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          background: "var(--accent-soft)",
          padding: "12px",
          borderRadius: "6px"
        }}>
          <strong>Focused on: {focusedProject?.name ?? "Unknown Project"}</strong>
          <button className="btnSmall btnOutline" onClick={handleClearFocus} type="button" style={{ background: "white" }}>
            Clear focus
          </button>
        </div>
      )}

      {!focusedProjectId && (
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
      )}

      {!result && <p className="stateText">Loading projects...</p>}
      {result && !result.ok && <p className="errorText">Unable to load projects: {result.error}</p>}
      {result?.ok && result.data.length === 0 && (
        <p className="stateText">No projects yet. When projects exist, they will appear here.</p>
      )}
      {result?.ok && result.data.length > 0 && !focusedProjectId && (
        <div className="filtersRow">
          <label>
            <span>Search Projects</span>
            <input
              placeholder="Search by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </label>
        </div>
      )}
      {result?.ok && result.data.length > 0 && filteredProjects.length === 0 && (
        <p className="stateText">No projects found matching your criteria.</p>
      )}
      {result?.ok && filteredProjects.length > 0 && (
        <div className="stack">
          {filteredProjects.map((project) => (
            <ProjectItem
              key={project.id}
              isFocused={project.id === focusedProjectId}
              onFocus={() => handleFocus(project.id)}
              onMutated={refresh}
              project={project}
            />
          ))}
        </div>
      )}
    </section>
  );
}
