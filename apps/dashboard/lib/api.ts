const LOCAL_DEV_API_URL = "http://localhost:8000";
const configuredApiUrl = process.env.NEXT_PUBLIC_KAIROS_API_URL?.trim();

export const KAIROS_API_URL =
  (configuredApiUrl ||
    (process.env.NODE_ENV === "development" ? LOCAL_DEV_API_URL : "")
  ).replace(/\/$/, "");

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

export type RuntimeProviderStatus = {
  id: string;
  name: string;
  status: string;
  message: string;
};

export type RuntimeStatusResponse = {
  runtimes: RuntimeProviderStatus[];
};

export function getRuntimeStatus() {
  return fetchFromApi<RuntimeStatusResponse>("/api/v1/runtime-status");
}

export type OllamaModelDetails = {
  parent_model?: string | null;
  format?: string | null;
  family?: string | null;
  families?: string[] | null;
  parameter_size?: string | null;
  quantization_level?: string | null;
};

export type OllamaModelManifest = {
  name: string;
  model: string;
  modified_at?: string | null;
  size?: number | null;
  digest?: string | null;
  details?: OllamaModelDetails | null;
  metadata?: Record<string, unknown>;
};

export type AIProviderModelsResponse = {
  provider_id: string;
  checked: boolean;
  reachable?: boolean | null;
  models: OllamaModelManifest[];
  model_count: number;
  configured_model_available?: boolean | null;
  error_type?: string | null;
  message?: string | null;
};

export type AIProviderMetadata = {
  id: string;
  name: string;
  provider_type: string;
  enabled: boolean;
  functional: boolean;
  status: string;
  auth_type: string;
  oauth_implemented: boolean;
  external_api_calls_enabled: boolean;
  default_model?: string | null;
  configured_model?: string | null;
  supports_local: boolean;
  supports_chat: boolean;
  supports_tools: boolean;
  supports_vision: boolean;
  priority: number;
  capabilities: string[];
  notes: string[];
};

export type AIProviderSelectionPolicy = {
  mode: "auto" | "manual";
  requested_provider_id?: string | null;
  selected_provider_id?: string | null;
  fallback_enabled: boolean;
  fallback_order: string[];
  attempts: string[];
  reason: string;
};

export type AIProviderRouteResponse = {
  providers: AIProviderMetadata[];
  selected_provider?: AIProviderMetadata | null;
  policy: AIProviderSelectionPolicy;
  auto_mode: boolean;
  dispatch_enabled: boolean;
};

export type AIProviderRouterModelsResponse = {
  provider_id: string;
  provider_name: string;
  policy: AIProviderSelectionPolicy;
  checked: boolean;
  reachable?: boolean | null;
  models: OllamaModelManifest[];
  model_count: number;
  configured_model_available?: boolean | null;
  error_type?: string | null;
  message?: string | null;
};

export type AIPromptDryRunRequest = {
  user_goal: string;
  context?: Record<string, unknown>;
  preferred_model?: string | null;
  include_commands?: boolean;
  include_plugins?: boolean;
  include_connectors?: boolean;
};

export type AIPromptDryRunResponse = {
  dry_run: boolean;
  provider_id: string;
  model?: string | null;
  user_goal: string;
  system_instructions: string[];
  context_summary: string;
  included_commands: Record<string, unknown>[];
  included_plugins: Record<string, unknown>[];
  included_connectors: Record<string, unknown>[];
  safety_policy: string[];
  estimated_context_items: number;
  warnings: string[];
  execution_enabled: boolean;
  network_call_performed: boolean;
};

export type AIPlanCommand = {
  command_id: string;
  command_name: string;
  description: string;
  category: string;
  execution_required: boolean;
  requires_approval: boolean;
  dangerous: boolean;
};

export type AIPlanStep = {
  step: number;
  action: string;
  rationale: string;
  commands: AIPlanCommand[];
};

export type AIPlanResponse = {
  goal: string;
  summary: string;
  available_context: Record<string, unknown>;
  suggested_steps: AIPlanStep[];
  suggested_commands: AIPlanCommand[];
  safety_notes: string[];
  execution_enabled: boolean;
  requires_approval: boolean;
};

export type AIOllamaDispatchRequest = {
  user_goal: string;
  context?: Record<string, unknown>;
  model?: string | null;
  dry_run_first?: boolean;
  include_commands?: boolean;
  include_plugins?: boolean;
  include_connectors?: boolean;
  parse_response?: boolean;
  create_approval_requests?: boolean;
};

export type AIProviderRouterDispatchRequest = AIOllamaDispatchRequest & {
  provider_id?: string | null;
  fallback_enabled?: boolean | null;
};

export type AIParsedPlanStep = {
  index: number;
  title: string;
  description: string;
  requires_approval: boolean;
  dangerous: boolean;
  related_command_id?: string | null;
  confidence?: number | null;
};

export type AIParsedCommandSuggestion = {
  command_id: string;
  reason: string;
  requires_approval: boolean;
  dangerous: boolean;
  execution_required: boolean;
};

export type AIParsedPlan = {
  source: string;
  model?: string | null;
  user_goal: string;
  summary: string;
  steps: AIParsedPlanStep[];
  command_suggestions: AIParsedCommandSuggestion[];
  safety_notes: string[];
  parser_warnings: string[];
  approval_requests: Record<string, unknown>[];
  execution_enabled: boolean;
  command_execution_performed: boolean;
  connector_calls_performed: boolean;
  data_mutation_performed: boolean;
};

export type AIOllamaDispatchResponse = {
  provider_id: string;
  model: string;
  prompt_sent: boolean;
  response_text: string;
  raw_response_metadata: Record<string, unknown>;
  safety_notes: string[];
  latency_ms: number;
  truncated: boolean;
  parsed_plan?: AIParsedPlan | null;
  approval_requests: Record<string, unknown>[];
  execution_enabled: boolean;
  command_execution_performed: boolean;
  connector_calls_performed: boolean;
  data_mutation_performed: boolean;
  network_call_performed: boolean;
};

export type AIProviderRouterDispatchResponse = AIOllamaDispatchResponse & {
  selected_provider_id: string;
  selected_provider_name: string;
  policy: AIProviderSelectionPolicy;
  fallback_used: boolean;
  provider_attempts: string[];
};

export type AIParsePlanRequest = {
  user_goal: string;
  model?: string | null;
  response_text: string;
  create_approval_requests?: boolean;
};

export function getAIModels() {
  return fetchFromApi<AIProviderModelsResponse>("/api/v1/ai/models");
}

export function getAIProviderRoute(providerId?: string) {
  const params = new URLSearchParams();
  if (providerId && providerId !== "auto") {
    params.set("provider_id", providerId);
  }
  const query = params.toString();
  return fetchFromApi<AIProviderRouteResponse>(
    `/api/v1/ai/provider-router/route${query ? `?${query}` : ""}`,
  );
}

export function getAIProviderRouterModels(providerId?: string) {
  const params = new URLSearchParams();
  if (providerId && providerId !== "auto") {
    params.set("provider_id", providerId);
  }
  const query = params.toString();
  return fetchFromApi<AIProviderRouterModelsResponse>(
    `/api/v1/ai/provider-router/models${query ? `?${query}` : ""}`,
  );
}

export function createAIPlan(userGoal: string, context: Record<string, unknown>) {
  return postToApi<AIPlanResponse, { user_goal: string; context: Record<string, unknown> }>(
    "/api/v1/ai/plan",
    { user_goal: userGoal, context },
  );
}

export function createPromptDryRun(payload: AIPromptDryRunRequest) {
  return postToApi<AIPromptDryRunResponse, AIPromptDryRunRequest>(
    "/api/v1/ai/prompt/dry-run",
    payload,
  );
}

export function dispatchOllama(payload: AIOllamaDispatchRequest) {
  return postToApi<AIOllamaDispatchResponse, AIOllamaDispatchRequest>(
    "/api/v1/ai/ollama/dispatch",
    payload,
  );
}

export function dispatchAIProvider(payload: AIProviderRouterDispatchRequest) {
  return postToApi<AIProviderRouterDispatchResponse, AIProviderRouterDispatchRequest>(
    "/api/v1/ai/provider-router/dispatch",
    payload,
  );
}

export function parseAIPlan(payload: AIParsePlanRequest) {
  return postToApi<AIParsedPlan, AIParsePlanRequest>("/api/v1/ai/parse-plan", payload);
}

export type DecisionPlanStatus = "draft" | "generating" | "validating" | "proposed";

export type DecisionCapabilityRef = {
  type: "plugin" | "command" | "connector" | "workflow";
  id: string;
};

export type DecisionPath = {
  title: string;
  summary: string;
  steps: string[];
  capability_refs: DecisionCapabilityRef[];
};

export type DecisionEvidence = {
  source: string;
  summary: string;
  reference_id?: string | null;
};

export type DecisionRisk = {
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  mitigation?: string | null;
};

export type DecisionProviderTrace = {
  provider_id?: string | null;
  model?: string | null;
  dispatch_used: boolean;
  fallback_used: boolean;
  warnings: string[];
};

export type DecisionSafetyFlags = {
  execution_enabled: false;
  approval_mutation_performed: false;
  approval_requests_created: false;
  workflow_triggered: false;
  workflow_runs_created: false;
  connector_calls_performed: false;
  data_mutation_performed: false;
};

export type DecisionPlan = {
  id: string;
  schema_version: "decision_plan.v1";
  goal: string;
  status: DecisionPlanStatus;
  revision: number;
  root_decision_id?: string | null;
  parent_decision_plan_id?: string | null;
  workspace_session_id?: string | null;
  primary_path: DecisionPath;
  alternatives: DecisionPath[];
  rationale: string;
  evidence: DecisionEvidence[];
  confidence: number;
  assumptions: string[];
  risks: DecisionRisk[];
  constraints: string[];
  success_definition: string;
  provider_trace: DecisionProviderTrace;
  safety_flags: DecisionSafetyFlags;
  approval_request_id?: string | null;
  created_at: string;
  updated_at: string;
};

export type DecisionPlanCreateRequest = {
  goal: string;
  context?: Record<string, unknown>;
  provider_id?: string | null;
  model?: string | null;
  workspace_session_id?: string | null;
  fallback_enabled?: boolean | null;
};

export function createDecisionPlan(payload: DecisionPlanCreateRequest) {
  return postToApi<DecisionPlan, DecisionPlanCreateRequest>("/api/v1/decision-plans", payload);
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
