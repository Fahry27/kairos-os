"use client";

import { type FormEvent, useEffect, useState } from "react";
import { createTask, getTasks, type ApiResult, type Task } from "../lib/api";

function formatDate(value?: string | null) {
  return value ? new Intl.DateTimeFormat("en", { dateStyle: "medium" }).format(new Date(value)) : "-";
}

export function TasksList() {
  const [result, setResult] = useState<ApiResult<Task[]> | null>(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

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
    });

    if (created.ok) {
      setTitle("");
      setDescription("");
      setPriority("medium");
      setResult(await loadTasks());
    } else {
      setSubmitError(`Unable to create task: ${created.error}`);
    }

    setIsSubmitting(false);
  }

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
