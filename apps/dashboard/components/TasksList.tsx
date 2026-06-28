"use client";

import { useSearchParams } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";
import {
  createTask,
  deleteTask,
  getTasks,
  updateTask,
  type ApiResult,
  type Task,
} from "../lib/api";

function formatDate(value?: string | null) {
  return value ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value)) : "-";
}

function TaskRow({
  task,
  onMutated,
}: {
  task: Task;
  onMutated: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const [editTitle, setEditTitle] = useState(task.title);
  const [editDescription, setEditDescription] = useState(task.description ?? "");
  const [editPriority, setEditPriority] = useState(task.priority);
  const [editStatus, setEditStatus] = useState(task.status);

  function startEditing() {
    setEditTitle(task.title);
    setEditDescription(task.description ?? "");
    setEditPriority(task.priority);
    setEditStatus(task.status);
    setActionError(null);
    setEditing(true);
  }

  function cancelEditing() {
    setEditing(false);
    setActionError(null);
  }

  async function handleSave() {
    const trimmed = editTitle.trim();
    if (!trimmed) {
      setActionError("Title is required.");
      return;
    }

    setIsSaving(true);
    const result = await updateTask(task.id, {
      title: trimmed,
      description: editDescription.trim() || null,
      priority: editPriority,
      status: editStatus,
    });

    if (result.ok) {
      setEditing(false);
      onMutated();
    } else {
      setActionError(`Save failed: ${result.error}`);
    }
    setIsSaving(false);
  }

  async function handleDelete() {
    if (!window.confirm(`Delete task "${task.title}"? This cannot be undone.`)) {
      return;
    }

    const result = await deleteTask(task.id);
    if (result.ok) {
      onMutated();
    } else {
      setActionError(`Delete failed: ${result.error}`);
    }
  }

  if (editing) {
    return (
      <tr>
        <td colSpan={6}>
          <div className="editForm">
            <label>
              <span>Title</span>
              <input
                maxLength={255}
                onChange={(e) => setEditTitle(e.target.value)}
                value={editTitle}
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
                <span>Status</span>
                <select onChange={(e) => setEditStatus(e.target.value)} value={editStatus}>
                  <option value="todo">Todo</option>
                  <option value="in_progress">In Progress</option>
                  <option value="done">Done</option>
                  <option value="blocked">Blocked</option>
                </select>
              </label>
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
            {actionError && <p className="errorText">{actionError}</p>}
          </div>
        </td>
      </tr>
    );
  }

  return (
    <tr>
      <td>
        <strong>{task.title}</strong>
      </td>
      <td>{task.status}</td>
      <td>{task.priority}</td>
      <td>{task.project_id ?? "-"}</td>
      <td>{formatDate(task.due_date)}</td>
      <td>
        <div className="recordActions" style={{ marginTop: 0 }}>
          <button className="btnSmall btnOutline" onClick={startEditing} type="button">
            Edit
          </button>
          <button className="btnSmall btnDanger" onClick={handleDelete} type="button">
            Delete
          </button>
        </div>
        {actionError && <p className="errorText">{actionError}</p>}
      </td>
    </tr>
  );
}

export function TasksList() {
  const searchParams = useSearchParams();
  const focusedProjectId = searchParams.get("project_id");

  const [result, setResult] = useState<ApiResult<Task[]> | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterPriority, setFilterPriority] = useState("all");

  useEffect(() => {
    let mounted = true;

    loadTasks().then((nextResult) => {
      if (mounted) {
        setResult(nextResult);
      }
    });

    return () => {
      mounted = false;
    };
  }, []);

  async function loadTasks() {
    return getTasks();
  }

  async function refresh() {
    setResult(await loadTasks());
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setSubmitError("Task title is required.");
      return;
    }

    setIsSubmitting(true);
    const created = await createTask({
      title: trimmedTitle,
      description: description.trim() || undefined,
      priority,
      project_id: focusedProjectId || undefined,
    });

    if (created.ok) {
      setTitle("");
      setDescription("");
      setPriority("medium");
      await refresh();
    } else {
      setSubmitError(`Unable to create task: ${created.error}`);
    }

    setIsSubmitting(false);
  }

  const filteredTasks = result?.ok
    ? result.data.filter((t) => {
        if (focusedProjectId && t.project_id !== focusedProjectId) return false;
        const q = searchQuery.toLowerCase();
        const matchesSearch =
          t.title.toLowerCase().includes(q) ||
          (t.description?.toLowerCase() || "").includes(q);
        const matchesStatus = filterStatus === "all" || t.status === filterStatus;
        const matchesPriority = filterPriority === "all" || t.priority === filterPriority;
        return matchesSearch && matchesStatus && matchesPriority;
      })
    : [];

  return (
    <section className="card">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Tasks</p>
          <h2>Queue</h2>
        </div>
      </div>
      <form className="resourceForm" onSubmit={handleSubmit}>
        <label>
          <span>Title</span>
          <input
            maxLength={255}
            onChange={(event) => setTitle(event.target.value)}
            placeholder="New task"
            value={title}
          />
        </label>
        <label>
          <span>Description</span>
          <textarea
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Optional details"
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
            {isSubmitting ? "Creating..." : "Create Task"}
          </button>
        </div>
        {submitError && <p className="errorText">{submitError}</p>}
      </form>
      {!result && <p className="stateText">Loading tasks...</p>}
      {result && !result.ok && <p className="errorText">Unable to load tasks: {result.error}</p>}
      {result?.ok && result.data.length === 0 && (
        <p className="stateText">No tasks yet. Open work will appear here.</p>
      )}
      {result?.ok && result.data.length > 0 && (
        <div className="filtersRow">
          <label>
            <span>Search Tasks</span>
            <input
              placeholder="Search by title or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </label>
          <label>
            <span>Status</span>
            <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
              <option value="all">All Statuses</option>
              <option value="todo">Todo</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
              <option value="blocked">Blocked</option>
            </select>
          </label>
          <label>
            <span>Priority</span>
            <select value={filterPriority} onChange={(e) => setFilterPriority(e.target.value)}>
              <option value="all">All Priorities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
        </div>
      )}
      {result?.ok && result.data.length > 0 && filteredTasks.length === 0 && (
        <p className="stateText">No tasks found matching your criteria.</p>
      )}
      {result?.ok && filteredTasks.length > 0 && (
        <div className="tableWrap">
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Priority</th>
                <th>Project</th>
                <th>Due</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTasks.map((task) => (
                <TaskRow key={task.id} onMutated={refresh} task={task} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
