const DEFAULT_API_URL = "http://localhost:8000";

export const KAIROS_API_URL =
  process.env.NEXT_PUBLIC_KAIROS_API_URL?.replace(/\/$/, "") ?? DEFAULT_API_URL;

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

export const WORKFLOW_RUNS_REFRESH_EVENT = "kairos:workflow-runs-refresh";

type ApiRequestOptions = {
  operatorToken?: string;
};

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

function getHeaders(
  extraHeaders: Record<string, string> = {},
  options: ApiRequestOptions = {},
): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...extraHeaders,
  };
  const apiKey = process.env.NEXT_PUBLIC_KAIROS_API_KEY;
  if (apiKey) {
    headers["X-Kairos-API-Key"] = apiKey;
  }
  const operatorToken = options.operatorToken?.trim();
  if (operatorToken) {
    headers["X-Kairos-Operator-Token"] = operatorToken;
  }
  return headers;
}

async function formatApiError(response: Response): Promise<string> {
  let detail = "";
  try {
    const payload = (await response.clone().json()) as { detail?: unknown };
    if (typeof payload.detail === "string") {
      detail = payload.detail;
    }
  } catch {
    try {
      detail = await response.clone().text();
    } catch {
      detail = "";
    }
  }

  return detail
    ? `${response.status} ${response.statusText}: ${detail}`
    : `${response.status} ${response.statusText}`;
}

export async function fetchFromApi<T>(path: string): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${KAIROS_API_URL}${path}`, {
      headers: getHeaders(),
    });

    if (!response.ok) {
      return { ok: false, error: await formatApiError(response) };
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
  options: ApiRequestOptions = {},
): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${KAIROS_API_URL}${path}`, {
      method: "POST",
      headers: getHeaders({ "Content-Type": "application/json" }, options),
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      return { ok: false, error: await formatApiError(response) };
    }

    return { ok: true, data: (await response.json()) as T };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Unknown request error",
    };
  }
}

export async function postEmptyToApi<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${KAIROS_API_URL}${path}`, {
      method: "POST",
      headers: getHeaders({}, options),
    });

    if (!response.ok) {
      return { ok: false, error: await formatApiError(response) };
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
  model_count: number | null;
  discovered_models_enabled: boolean;
  configured_model_available: boolean | null;
  dry_run_enabled: boolean;
  max_context_commands: number;
  max_context_connectors: number;
  max_context_plugins: number;
  ollama_dispatch_enabled: boolean;
  ollama_generate_path: string;
  ollama_request_timeout_seconds: number;
  ollama_max_prompt_chars: number;
  ollama_max_response_chars: number;
  response_parser_enabled: boolean;
  max_parsed_steps: number;
  max_parsed_commands: number;
  approval_gate_enabled: boolean;
  approval_default_ttl_minutes: number;
  approval_max_pending: number;
};

export function getAICapabilities() {
  return fetchFromApi<AICapabilities>("/api/v1/ai/capabilities");
}

export type ApprovalActionType =
  | "command"
  | "connector"
  | "workflow"
  | "memory"
  | "project"
  | "task"
  | "generic";

export type ApprovalStatus = "pending" | "approved" | "rejected" | "expired";

export type ApprovalRiskLevel = "low" | "medium" | "high" | "critical";

export type ApprovalRequest = {
  id: string;
  title: string;
  description?: string | null;
  action_type: ApprovalActionType;
  proposed_action_id?: string | null;
  source: string;
  risk_level: ApprovalRiskLevel;
  requires_manual_review: boolean;
  payload_summary?: Record<string, unknown> | null;
  safety_notes: string[];
  status: ApprovalStatus;
  created_at: string;
  expires_at: string;
  decided_at?: string | null;
  decision_reason?: string | null;
  execution_enabled: boolean;
  execution_performed: boolean;
  connector_calls_performed: boolean;
  data_mutation_performed: boolean;
};

export type ApprovalDecisionRequest = {
  reason?: string | null;
};

export type ApprovalListStatus = ApprovalStatus | "all";

export function listApprovals(status: ApprovalListStatus = "pending") {
  const params = new URLSearchParams({ offset: "0", limit: "100" });
  if (status !== "all") {
    params.set("status", status);
  }
  return fetchFromApi<ApprovalRequest[]>(`/api/v1/approvals?${params.toString()}`);
}

export function getApproval(approvalId: string) {
  return fetchFromApi<ApprovalRequest>(`/api/v1/approvals/${approvalId}`);
}

export function approveApproval(approvalId: string, operatorToken?: string) {
  return postEmptyToApi<ApprovalRequest>(`/api/v1/approvals/${approvalId}/approve`, {
    operatorToken,
  });
}

export function rejectApproval(approvalId: string, reason: string, operatorToken?: string) {
  return postToApi<ApprovalRequest, ApprovalDecisionRequest>(
    `/api/v1/approvals/${approvalId}/reject`,
    { reason },
    { operatorToken },
  );
}

export type WorkflowRunStatus = "running" | "succeeded" | "failed";

export type WorkflowRunTargetType = "n8n_webhook";

export type WorkflowRun = {
  id: string;
  approval_id: string;
  target_type: WorkflowRunTargetType;
  status: WorkflowRunStatus;
  started_at: string;
  finished_at?: string | null;
  http_status_code?: number | null;
  sanitized_error?: string | null;
  request_summary?: Record<string, unknown> | null;
  response_summary?: Record<string, unknown> | null;
};

export type WorkflowRunListStatus = WorkflowRunStatus | "all";

export type WorkflowRunTriggerRequest = {
  retry_failed?: boolean;
};

export function listWorkflowRuns(
  status: WorkflowRunListStatus = "all",
  approvalId?: string,
  targetType?: WorkflowRunTargetType,
) {
  const params = new URLSearchParams({ offset: "0", limit: "100" });
  if (status !== "all") {
    params.set("status", status);
  }
  if (approvalId?.trim()) {
    params.set("approval_id", approvalId.trim());
  }
  if (targetType) {
    params.set("target_type", targetType);
  }
  return fetchFromApi<WorkflowRun[]>(`/api/v1/workflow-runs?${params.toString()}`);
}

export function getWorkflowRun(runId: string) {
  return fetchFromApi<WorkflowRun>(`/api/v1/workflow-runs/${runId}`);
}

export function triggerN8nApproval(
  approvalId: string,
  retryFailed: boolean,
  operatorToken?: string,
) {
  return postToApi<WorkflowRun, WorkflowRunTriggerRequest>(
    `/api/v1/approvals/${approvalId}/trigger-n8n`,
    { retry_failed: retryFailed },
    { operatorToken },
  );
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
      return { ok: false, error: await formatApiError(response) };
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
      return { ok: false, error: await formatApiError(response) };
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
