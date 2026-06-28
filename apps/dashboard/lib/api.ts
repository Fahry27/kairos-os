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

export type ProjectCreate = {
  name: string;
  description?: string;
  priority?: string;
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

export type TaskCreate = {
  title: string;
  description?: string;
  priority?: string;
  project_id?: string;
};

export type Memory = {
  id: string;
  project_id?: string | null;
  type: string;
  content: string;
  source?: string | null;
  tags?: string[] | null;
  importance: string;
  created_at: string;
  updated_at: string;
};

export type MemoryCreate = {
  project_id?: string;
  type?: string;
  content: string;
  source?: string;
  tags?: string[];
  importance?: string;
};

function getHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...extraHeaders,
  };
  const apiKey = process.env.NEXT_PUBLIC_KAIROS_API_KEY;
  if (apiKey) {
    headers["X-Kairos-API-Key"] = apiKey;
  }
  return headers;
}

export async function fetchFromApi<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${KAIROS_API_URL}${path}`, {
      headers: getHeaders(),
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

export async function postToApi<T, TPayload extends object>(
  path: string,
  payload: TPayload,
): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${KAIROS_API_URL}${path}`, {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
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

export function createProject(payload: ProjectCreate) {
  return postToApi<Project, ProjectCreate>("/api/v1/projects", payload);
}

export function getTasks() {
  return fetchFromApi<Task[]>("/api/v1/tasks");
}

export function createTask(payload: TaskCreate) {
  return postToApi<Task, TaskCreate>("/api/v1/tasks", payload);
}

export function getMemories() {
  return fetchFromApi<Memory[]>("/api/v1/memories");
}

export function createMemory(payload: MemoryCreate) {
  return postToApi<Memory, MemoryCreate>("/api/v1/memories", payload);
}

export type PluginManifest = {
  id: string;
  name: string;
  version: string;
  description: string;
  category: string;
  enabled: boolean;
  commands?: any[];
};

export function getPlugins() {
  return fetchFromApi<PluginManifest[]>("/api/v1/plugins");
}

export type ConnectorManifest = {
  id: string;
  name: string;
  version: string;
  description: string;
  category: string;
  enabled: boolean;
  service_type: string;
  base_url?: string | null;
  auth_type: string;
  capabilities?: string[];
  tags?: string[];
};

export function getConnectors() {
  return fetchFromApi<ConnectorManifest[]>("/api/v1/connectors");
}

export type AICapabilities = {
  ai_enabled: boolean;
  provider: string;
  model: string | null;
  planning_enabled: boolean;
  execution_enabled: boolean;
  available_plugins: number;
  available_commands: number;
  available_connectors: number;
  dangerous_commands: number;
  provider_reachable: boolean | null;
  provider_checked: boolean;
  provider_readiness_message: string | null;
};

export function getAICapabilities() {
  return fetchFromApi<AICapabilities>("/api/v1/ai/capabilities");
}

// ---------------------------------------------------------------------------
// Update types
// ---------------------------------------------------------------------------

export type ProjectUpdate = {
  name?: string;
  description?: string | null;
  priority?: string;
  status?: string;
};

export type TaskUpdate = {
  title?: string;
  description?: string | null;
  priority?: string;
  status?: string;
  project_id?: string | null;
  due_date?: string | null;
};

export type MemoryUpdate = {
  project_id?: string | null;
  type?: string;
  content?: string;
  source?: string | null;
  tags?: string[] | null;
  importance?: string;
};

// ---------------------------------------------------------------------------
// Generic PATCH / DELETE helpers
// ---------------------------------------------------------------------------

export async function patchToApi<T, TPayload extends object>(
  path: string,
  payload: TPayload,
): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${KAIROS_API_URL}${path}`, {
      method: "PATCH",
      headers: getHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
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

export async function deleteFromApi(path: string): Promise<ApiResult<null>> {
  try {
    const response = await fetch(`${KAIROS_API_URL}${path}`, {
      method: "DELETE",
      headers: getHeaders(),
    });

    if (!response.ok) {
      return { ok: false, error: `${response.status} ${response.statusText}` };
    }

    return { ok: true, data: null };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Unknown request error",
    };
  }
}

// ---------------------------------------------------------------------------
// Update / Delete operations
// ---------------------------------------------------------------------------

export function updateProject(id: string, payload: ProjectUpdate) {
  return patchToApi<Project, ProjectUpdate>(`/api/v1/projects/${id}`, payload);
}

export function deleteProject(id: string) {
  return deleteFromApi(`/api/v1/projects/${id}`);
}

export function updateTask(id: string, payload: TaskUpdate) {
  return patchToApi<Task, TaskUpdate>(`/api/v1/tasks/${id}`, payload);
}

export function deleteTask(id: string) {
  return deleteFromApi(`/api/v1/tasks/${id}`);
}

export function updateMemory(id: string, payload: MemoryUpdate) {
  return patchToApi<Memory, MemoryUpdate>(`/api/v1/memories/${id}`, payload);
}

export function deleteMemory(id: string) {
  return deleteFromApi(`/api/v1/memories/${id}`);
}
