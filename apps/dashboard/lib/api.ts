const DEFAULT_API_URL = "http://localhost:8000";

export const KAIROS_API_URL =
  process.env.NEXT_PUBLIC_KAIROS_API_URL?.replace(/\/$/, "") ?? DEFAULT_API_URL;

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

export type Health = {
  status: string;
  service: string;
  version: string;
};

export type Project = {
  id: string;
  name: string;
  description?: string | null;
  status: string;
  priority: string;
  created_at: string;
  updated_at: string;
};

export type Task = {
  id: string;
  project_id?: string | null;
  title: string;
  description?: string | null;
  status: string;
  priority: string;
  due_date?: string | null;
  created_at: string;
  updated_at: string;
};

export type Memory = {
  id: string;
  type: string;
  content: string;
  source?: string | null;
  tags?: string[] | null;
  importance: string;
  created_at: string;
  updated_at: string;
};

export async function fetchFromApi<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${KAIROS_API_URL}${path}`, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      return { ok: false, error: `${response.status} ${response.statusText}` };
    }

    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Unknown request error",
    };
  }
}

export function getHealth() {
  return fetchFromApi<Health>("/health");
}

export function getProjects() {
  return fetchFromApi<Project[]>("/api/v1/projects");
}

export function getTasks() {
  return fetchFromApi<Task[]>("/api/v1/tasks");
}

export function getMemories() {
  return fetchFromApi<Memory[]>("/api/v1/memories");
}
