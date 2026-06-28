"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import {
  getMemories,
  getProjects,
  getTasks,
  type Memory,
  type Project,
  type Task,
} from "../lib/api";

export function StatsOverview() {
  const searchParams = useSearchParams();
  const focusedProjectId = searchParams.get("project_id");

  const [projects, setProjects] = useState<Project[] | null>(null);
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [memories, setMemories] = useState<Memory[] | null>(null);

  useEffect(() => {
    let mounted = true;

    Promise.all([getProjects(), getTasks(), getMemories()]).then(
      ([projectsResult, tasksResult, memoriesResult]) => {
        if (!mounted) return;
        if (projectsResult.ok) setProjects(projectsResult.data);
        if (tasksResult.ok) setTasks(tasksResult.data);
        if (memoriesResult.ok) setMemories(memoriesResult.data);
      },
    );

    return () => {
      mounted = false;
    };
  }, []);

  const loading = projects === null || tasks === null || memories === null;

  if (loading) {
    return (
      <section className="card cardWide">
        <p className="eyebrow">Overview</p>
        <h2>Dashboard Stats</h2>
        <p className="stateText">Loading stats...</p>
      </section>
    );
  }

  // ---- Global stats ----
  const totalProjects = projects.length;
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter((t) => t.status === "done").length;
  const activeTasks = totalTasks - completedTasks;
  const totalMemories = memories.length;

  // ---- Focused project stats ----
  const focusedProject = focusedProjectId
    ? projects.find((p) => p.id === focusedProjectId) ?? null
    : null;

  const linkedTasks = focusedProjectId
    ? tasks.filter((t) => t.project_id === focusedProjectId)
    : [];
  const linkedCompletedTasks = linkedTasks.filter((t) => t.status === "done").length;
  const linkedMemories = focusedProjectId
    ? memories.filter((m) => m.project_id === focusedProjectId)
    : [];

  const completionPct =
    linkedTasks.length > 0
      ? Math.round((linkedCompletedTasks / linkedTasks.length) * 100)
      : 0;

  return (
    <section className="card cardWide">
      <div className="sectionHeader">
        <div>
          <p className="eyebrow">Overview</p>
          <h2>Dashboard Stats</h2>
        </div>
      </div>

      {/* Global stats row */}
      <dl className="statGrid">
        <div>
          <dt>Projects</dt>
          <dd>{totalProjects}</dd>
        </div>
        <div>
          <dt>Total Tasks</dt>
          <dd>{totalTasks}</dd>
        </div>
        <div>
          <dt>Completed</dt>
          <dd>{completedTasks}</dd>
        </div>
        <div>
          <dt>Active</dt>
          <dd>{activeTasks}</dd>
        </div>
        <div>
          <dt>Memories</dt>
          <dd>{totalMemories}</dd>
        </div>
        {!focusedProject && (
          <div>
            <dt>Completion</dt>
            <dd>
              {totalTasks > 0
                ? `${Math.round((completedTasks / totalTasks) * 100)}%`
                : "—"}
            </dd>
          </div>
        )}
      </dl>

      {/* Focused project overview */}
      {focusedProject && (
        <div className="focusedOverview">
          <h3>
            Focused: {focusedProject.name}
            <span className="pill" style={{ marginLeft: 8, fontSize: 12 }}>
              {focusedProject.status}
            </span>
          </h3>
          <dl className="statGrid" style={{ marginTop: 12 }}>
            <div>
              <dt>Linked Tasks</dt>
              <dd>{linkedTasks.length}</dd>
            </div>
            <div>
              <dt>Completed</dt>
              <dd>{linkedCompletedTasks}</dd>
            </div>
            <div>
              <dt>Linked Memories</dt>
              <dd>{linkedMemories.length}</dd>
            </div>
          </dl>
          <div className="progressBar" style={{ marginTop: 12 }}>
            <div
              className="progressFill"
              style={{ width: `${completionPct}%` }}
            />
          </div>
          <p className="progressLabel">
            {linkedTasks.length > 0
              ? `${completionPct}% complete (${linkedCompletedTasks}/${linkedTasks.length} tasks)`
              : "No linked tasks yet"}
          </p>
        </div>
      )}
    </section>
  );
}
