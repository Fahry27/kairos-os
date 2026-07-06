/**
 * Kairos Core — Shared Domain Model.
 *
 * These types represent Kairos concepts independently of API transport.
 * They are the vocabulary every surface, component, and state slice speaks.
 * API types in lib/api.ts remain transport-only.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

/** Generic entity status. */
export type Status = "active" | "completed" | "paused" | "archived";

/** Priority levels used across Mission, Decision, and Step. */
export type Priority = "low" | "medium" | "high" | "critical";

/** Approval state for steps and mission-level gates. */
export type ApprovalState = "pending" | "approved" | "rejected" | "expired";

// ---------------------------------------------------------------------------
// Mission Engine — Lifecycle
// ---------------------------------------------------------------------------

/**
 * MissionStatus — the full Mission lifecycle.
 *
 *   draft → planning → awaiting_approval → approved → executing
 *              ↑              ↓                  ↓
 *              └── cancelled  └── rejected       ├── completed
 *                                                 └── failed
 *   Any terminal state → archived
 */
export type MissionStatus =
  | "draft"
  | "planning"
  | "awaiting_approval"
  | "approved"
  | "executing"
  | "completed"
  | "failed"
  | "cancelled"
  | "archived";

/** Execution status for individual steps. */
export type ExecutionStatus =
  | "queued"
  | "running"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled"
  | "retry_ready";

// ---------------------------------------------------------------------------
// Mission domain entities
// ---------------------------------------------------------------------------

/**
 * MissionTrigger — what initiated this mission.
 * A mission can be triggered by a user, a schedule, another mission,
 * or an event from the system.
 */
export interface MissionTrigger {
  kind: "user" | "schedule" | "mission" | "event";
  /** Optional reference to the source entity. */
  sourceId: string | null;
  /** Human-readable description of the trigger. */
  description: string;
}

/**
 * MissionContext — the context in which the mission operates.
 * Used by the planner to understand constraints and available resources.
 */
export interface MissionContext {
  /** Related mission IDs that provide context. */
  relatedMissionIds: string[];
  /** Freeform notes from the user when creating the mission. */
  userNotes: string;
  /** Environment / capability constraints. */
  constraints: string[];
  /** Tags for organization and filtering. */
  tags: string[];
}

/**
 * MissionStep — a single actionable step within a mission plan.
 */
export interface MissionStep {
  id: string;
  /** Display order in the plan. */
  order: number;
  title: string;
  description: string;
  /** Whether this step requires manual approval before execution. */
  requiresApproval: boolean;
  /** Whether this step is flagged as dangerous. */
  dangerous: boolean;
  /** The commands, plugins, or connectors this step depends on. */
  capabilityRefs: string[];
  /** Execution status of this step. */
  executionStatus: ExecutionStatus;
  /** Optional estimated duration for display. */
  estimatedDuration: string | null;
  createdAt: string;
  updatedAt: string;
}

/**
 * MissionPlan — the planning output for a mission.
 * Versioned so plans can be revised without losing history.
 */
export interface MissionPlan {
  /** Plan version (starts at 1, increments on revision). */
  version: number;
  /** Summary of the plan in plain language. */
  summary: string;
  /** Ordered list of steps. */
  steps: MissionStep[];
  /** Safety notes and warnings from the planner. */
  safetyNotes: string[];
  /** What defines success for this mission. */
  successDefinition: string;
  /** AI provider and model that generated this plan. */
  generatedBy: string | null;
  createdAt: string;
}

/**
 * MissionApproval — an approval gate within a mission.
 * Covers both step-level and mission-level approvals.
 */
export interface MissionApproval {
  id: string;
  missionId: string;
  /** Optional step this approval gates (null = mission-level gate). */
  stepId: string | null;
  title: string;
  description: string;
  status: ApprovalState;
  /** Who or what requested the approval. */
  requestedBy: string;
  /** Reason for the decision. */
  decisionReason: string | null;
  requestedAt: string;
  decidedAt: string | null;
}

/**
 * MissionStepExecution — the execution record for a single step.
 */
export interface MissionStepExecution {
  id: string;
  missionId: string;
  stepId: string;
  status: ExecutionStatus;
  startedAt: string | null;
  completedAt: string | null;
  /** Number of retries attempted. */
  retryCount: number;
  /** Sanitized error message (no secrets). */
  error: string | null;
  /** Summary of the execution result. */
  resultSummary: string | null;
}

/**
 * MissionArtifact — an output or artifact produced during mission execution.
 */
export interface MissionArtifact {
  id: string;
  missionId: string;
  stepId: string | null;
  kind: "text" | "decision" | "memory" | "file" | "approval" | "workflow";
  title: string;
  /** Reference to the artifact content (may be an ID or URL). */
  contentRef: string;
  createdAt: string;
}

/**
 * MissionOutcome — the final outcome once a mission reaches a terminal state.
 */
export interface MissionOutcome {
  status: "completed" | "failed" | "cancelled";
  summary: string;
  /** Key lessons or reflections. */
  learnings: string[];
  /** Artifacts produced. */
  artifacts: MissionArtifact[];
  /** Timestamp when the outcome was recorded. */
  recordedAt: string;
}

/**
 * Mission — the core domain entity for the Mission Engine.
 *
 * A Mission is the primary unit of work in Kairos. It flows through:
 *   Trigger → Plan → Approve → Execute → Outcome → Archive
 */
export interface Mission {
  id: string;
  name: string;
  description: string | null;
  status: MissionStatus;
  priority: Priority;
  /** Who or what triggered this mission. */
  trigger: MissionTrigger;
  /** Context for planning and execution. */
  context: MissionContext;
  /** The plan (multiple versions supported). */
  plans: MissionPlan[];
  /** Active plan version. */
  activePlanVersion: number | null;
  /** Pending approvals for this mission. */
  approvals: MissionApproval[];
  /** Execution records for each step. */
  stepExecutions: MissionStepExecution[];
  /** Artifacts produced during execution. */
  artifacts: MissionArtifact[];
  /** Final outcome (set when mission reaches a terminal status). */
  outcome: MissionOutcome | null;
  /** When the mission was triggered. */
  triggeredAt: string;
  createdAt: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Timeline Engine
// ---------------------------------------------------------------------------

/**
 * TimelineEventType — the kind of event in the unified Kairos Timeline.
 *
 * The Timeline is the chronological system-of-record for everything
 * that happens in Kairos: mission transitions, memory changes,
 * decisions, workspace activity, approvals, executions, and
 * future provider events.
 */
export type TimelineEventType =
  // Mission
  | "mission.created"
  | "mission.status_change"
  | "mission.plan_generated"
  | "mission.plan_revised"
  | "mission.outcome_recorded"
  | "mission.archived"
  // Approval
  | "approval.requested"
  | "approval.granted"
  | "approval.rejected"
  // Execution
  | "execution.step_queued"
  | "execution.step_started"
  | "execution.step_completed"
  | "execution.step_failed"
  | "execution.step_retried"
  // Memory
  | "memory.created"
  | "memory.pinned"
  | "memory.archived"
  | "memory.superseded"
  // Decision
  | "decision.created"
  | "decision.resolved"
  | "decision.status_change"
  // Workspace
  | "workspace.created"
  | "workspace.session_started"
  | "workspace.session_ended"
  // System
  | "system.health_check"
  | "system.provider_status_change"
  | "system.connector_event"
  // Command & Automation
  | "command.created"
  | "command.approved"
  | "command.rejected"
  | "command.started"
  | "command.completed"
  | "command.failed"
  | "automation.triggered"
  | "automation.run_started"
  | "automation.run_completed"
  | "automation.run_failed"
  | "automation.paused"
  | "automation.disabled"
  // Plugin & Connector
  | "plugin.installed"
  | "plugin.updated"
  | "plugin.disabled"
  | "plugin.enabled"
  | "plugin.uninstalled"
  | "connector.connected"
  | "connector.disconnected"
  | "connector.synced"
  | "connector.sync_failed"
  | "connector.health_degraded";

/**
 * TimelineActor — who or what initiated the event.
 */
export interface TimelineActor {
  kind: "user" | "mission" | "provider" | "system" | "schedule";
  /** Optional ID of the actor entity. */
  id: string | null;
  /** Human-readable label for the actor. */
  label: string;
}

/**
 * TimelineSource — where the event was recorded from.
 */
export interface TimelineSource {
  kind: "shell" | "api" | "provider" | "scheduler" | "connector";
  /** Optional reference for traceability. */
  reference: string | null;
}

/**
 * TimelineScope — who can see this event.
 */
export type TimelineScope = "private" | "mission" | "workspace" | "global";

/**
 * TimelineSeverity — visual weight for the timeline entry.
 */
export type TimelineSeverity = "info" | "success" | "warning" | "error" | "critical";

/**
 * TimelineAttachment — optional structured data attached to an event.
 */
export interface TimelineAttachment {
  kind: "artifact" | "memory_ref" | "decision_ref" | "mission_ref" | "execution_ref" | "approval_ref" | "text";
  /** Reference to the related entity. */
  refId: string | null;
  /** Human-readable label for display. */
  label: string;
  /** Optional inline data (text summary or preview). */
  inline: string | null;
}

/**
 * TimelineFilter — active filter state for the timeline view.
 */
export interface TimelineFilter {
  /** Filter by event type. Empty = all. */
  types: TimelineEventType[];
  /** Filter by mission ID. Null = all. */
  missionId: string | null;
  /** Filter by workspace ID. Null = all. */
  workspaceId: string | null;
  /** Filter by scope. Empty = all. */
  scopes: TimelineScope[];
  /** Minimum severity to show. Null = all. */
  minSeverity: TimelineSeverity | null;
  /** Text search across title and description. */
  query: string;
}

/**
 * TimelineEvent — a single entry in the unified Kairos Timeline.
 *
 * This replaces the old MissionTimelineEvent with a broader model
 * that covers missions, memories, decisions, workspaces, and
 * system events in one chronological record.
 */
export interface TimelineEvent {
  id: string;
  /** The type of event. */
  type: TimelineEventType;
  /** Human-readable title. */
  title: string;
  /** Longer description of what happened. */
  description: string;
  /** When the event occurred. */
  timestamp: string;
  /** Who or what initiated this event. */
  actor: TimelineActor;
  /** Where the event was recorded from. */
  source: TimelineSource;
  /** Visibility scope. */
  scope: TimelineScope;
  /** Visual weight. */
  severity: TimelineSeverity;
  /** Optional related entity IDs for cross-referencing. */
  missionId: string | null;
  workspaceId: string | null;
  memoryId: string | null;
  decisionId: string | null;
  /** Optional attachments for rich display. */
  attachments: TimelineAttachment[];
}

// ---------------------------------------------------------------------------
// Mission timeline events (deprecated — use TimelineEvent)
// ---------------------------------------------------------------------------

/** @deprecated Use TimelineEvent with type starting with "mission." instead. */
export interface MissionTimelineEvent {
  id: string;
  missionId: string;
  timestamp: string;
  kind: string;
  title: string;
  description: string;
  resultingStatus: MissionStatus | null;
  relatedId: string | null;
}

// ---------------------------------------------------------------------------
// Decision (unchanged)
// ---------------------------------------------------------------------------

export interface Decision {
  id: string;
  title: string;
  description: string | null;
  status: Status;
  priority: Priority;
  missionId: string | null;
  dueDate: string | null;
  createdAt: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Workspace (unchanged)
// ---------------------------------------------------------------------------

export interface Workspace {
  id: string;
  goal: string;
  status: "active" | "completed" | "paused";
  createdAt: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Memory Engine
// ---------------------------------------------------------------------------

/**
 * A memory is a durable unit of knowledge in Kairos.
 * Unlike chat history or transient context, memories persist across sessions
 * and are available to every future Mission and AI provider.
 */

export type MemoryType =
  | "note"
  | "decision"
  | "reflection"
  | "insight"
  | "reference"
  | "procedure"
  | "fact";

export type MemoryVisibility = "private" | "mission" | "workspace" | "global";

export type MemoryStatus = "active" | "archived" | "superseded";

/**
 * MemorySource — tracks where a memory originated.
 */
export interface MemorySource {
  kind: "user" | "mission" | "workspace" | "provider" | "system";
  /** ID of the originating entity, if applicable. */
  sourceId: string | null;
  /** Human-readable label for the source. */
  label: string;
}

/**
 * MemoryRelationship — links a memory to another entity.
 */
export interface MemoryRelationship {
  /** What kind of entity this links to. */
  targetKind: "mission" | "decision" | "workspace" | "memory" | "artifact";
  /** ID of the linked entity. */
  targetId: string;
  /** Optional label for the relationship (e.g., "informs", "contradicts"). */
  label: string | null;
}

/**
 * MemoryTag — structured tag with optional category grouping.
 */
export interface MemoryTag {
  id: string;
  name: string;
  category: string | null;
}

/**
 * MemoryCollection — a named, filterable group of memories.
 */
export interface MemoryCollection {
  id: string;
  name: string;
  description: string | null;
  /** IDs of memories in this collection. */
  memoryIds: string[];
  createdAt: string;
  updatedAt: string;
}

/**
 * Memory — the core domain entity for the Memory Engine.
 */
export interface Memory {
  id: string;
  /** Short title / summary. */
  title: string;
  /** Full content. */
  content: string;
  type: MemoryType;
  importance: Priority;
  visibility: MemoryVisibility;
  status: MemoryStatus;
  /** Where this memory came from. */
  source: MemorySource;
  /** Links to related entities. */
  relationships: MemoryRelationship[];
  /** Tags for organization. */
  tags: MemoryTag[];
  /** Optional collection membership. */
  collectionId: string | null;
  /** Whether this memory is pinned for quick access. */
  isPinned: boolean;
  createdAt: string;
  updatedAt: string;
}

/**
 * MemoryReference — a lightweight pointer to a Memory.
 * Used in mission context, workspace panels, and brief cards
 * where the full Memory payload is unnecessary.
 */
export interface MemoryReference {
  id: string;
  type: MemoryType;
  /** Preview snippet — first ~120 chars. */
  snippet: string;
  importance: Priority;
  isPinned: boolean;
  tags: string[];
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Knowledge Engine
// ---------------------------------------------------------------------------

/**
 * The Knowledge Engine sits above Memory and below the AI Router.
 *
 * Memory stores raw knowledge units. The Knowledge Engine structures them
 * into queryable, contextual knowledge that AI providers can consume.
 *
 * No embeddings. No vector DB. No AI calls. This is the architecture layer.
 */

export type KnowledgeType =
  | "fact"
  | "insight"
  | "procedure"
  | "decision_rationale"
  | "reflection"
  | "context";

export type KnowledgeStatus = "active" | "archived" | "superseded" | "draft";

export type KnowledgeConfidence = "low" | "medium" | "high" | "validated";

export interface KnowledgeSource {
  /** What kind of entity produced this knowledge. */
  kind: "memory" | "mission" | "provider" | "user" | "system";
  /** ID of the source entity. */
  sourceId: string | null;
  /** Human-readable label. */
  label: string;
}

/**
 * KnowledgeRelationship — links knowledge items to other entities.
 */
export interface KnowledgeRelationship {
  kind: "derived_from" | "supports" | "contradicts" | "extends" | "references";
  targetKind: "knowledge" | "memory" | "mission" | "decision" | "workspace";
  targetId: string;
  label: string | null;
}

export interface KnowledgeCollection {
  id: string;
  name: string;
  description: string | null;
  knowledgeIds: string[];
  createdAt: string;
  updatedAt: string;
}

/**
 * KnowledgeItem — the core entity of the Knowledge Engine.
 *
 * A KnowledgeItem is structured understanding, derived from Memory,
 * Missions, or provider analysis. It is indexed and queryable.
 */
export interface KnowledgeItem {
  id: string;
  title: string;
  /** The structured knowledge content. */
  content: string;
  type: KnowledgeType;
  status: KnowledgeStatus;
  confidence: KnowledgeConfidence;
  /** Where this knowledge came from. */
  source: KnowledgeSource;
  /** Relationships to other entities. */
  relationships: KnowledgeRelationship[];
  /** Tags for organization. */
  tags: string[];
  /** Optional collection membership. */
  collectionId: string | null;
  /** The mission context this knowledge is most relevant to. */
  missionId: string | null;
  /** The workspace context this knowledge is most relevant to. */
  workspaceId: string | null;
  createdAt: string;
  updatedAt: string;
}

/**
 * KnowledgeQuery — a structured query against the Knowledge Engine.
 */
export interface KnowledgeQuery {
  /** Freeform query text. */
  query: string;
  /** Filter by knowledge types. */
  types: KnowledgeType[];
  /** Filter by minimum confidence. */
  minConfidence: KnowledgeConfidence | null;
  /** Scope to a specific mission. */
  missionId: string | null;
  /** Scope to a specific workspace. */
  workspaceId: string | null;
  /** Maximum results to return. */
  limit: number;
}

/**
 * KnowledgeResult — a single result from a knowledge query.
 */
export interface KnowledgeResult {
  item: KnowledgeItem;
  /** Relevance score (future: from similarity search). */
  relevance: number;
  /** Why this item was included in results. */
  rationale: string | null;
}

/**
 * KnowledgeContext — a collection of knowledge items assembled for a
 * specific purpose (e.g., providing context to an AI provider, informing
 * a mission plan, populating a workspace panel).
 */
export interface KnowledgeContext {
  /** The query that produced this context. */
  query: KnowledgeQuery;
  /** The knowledge items assembled. */
  items: KnowledgeItem[];
  /** Results from the last search (if query-based). */
  results: KnowledgeResult[];
  /** When this context was assembled. */
  assembledAt: string;
}

// ---------------------------------------------------------------------------
// AI Router
// ---------------------------------------------------------------------------

export type AIProviderType = "ollama" | "openai_compatible" | "9router" | "gemini" | "deepseek";
export type AIProviderStatus = "healthy" | "degraded" | "unavailable" | "unchecked";
export type AIStreamState = "idle" | "connecting" | "streaming" | "complete" | "error" | "aborted";

export interface AIModelCapability {
  supportsChat: boolean;
  supportsTools: boolean;
  supportsVision: boolean;
  supportsLocal: boolean;
  maxContextTokens: number | null;
}

export interface AIModel {
  name: string;
  providerId: string;
  capabilities: AIModelCapability;
  available: boolean;
}

export interface AIRoutePolicy {
  mode: "auto" | "manual";
  preferredProviderId: string | null;
  preferredModel: string | null;
  fallbackEnabled: boolean;
  fallbackOrder: string[];
  budgetTier: "free" | "cheap" | "quality";
  offlineOnly: boolean;
}

export interface AIUsageEstimate {
  providerId: string;
  model: string;
  estimatedTokens: number;
  estimatedCost: number;
  currency: string;
  isAvailable: boolean;
}

export interface AIRequest {
  prompt: string;
  systemInstructions: string[];
  knowledgeContext: KnowledgeContext | null;
  memoryRefs: string[];
  missionId: string | null;
  workspaceId: string | null;
  policy: AIRoutePolicy;
  maxResponseTokens: number;
}

export interface AIResponse {
  providerId: string;
  model: string;
  content: string;
  fallbackUsed: boolean;
  providerAttempts: string[];
  safetyNotes: string[];
  latencyMs: number;
  tokensUsed: number | null;
  streamState: AIStreamState;
  error: string | null;
}

export interface AIProvider {
  id: string;
  name: string;
  type: AIProviderType;
  status: AIProviderStatus;
  models: AIModel[];
  supportsLocal: boolean;
  enabled: boolean;
  lastChecked: string | null;
  healthMessage: string | null;
}

export interface AIExecutionContext {
  request: AIRequest;
  providers: AIProvider[];
  selectedProviderId: string | null;
  estimate: AIUsageEstimate | null;
  assembledAt: string;
}

// ---------------------------------------------------------------------------
// Command & Automation Engine
// ---------------------------------------------------------------------------

/**
 * Commands are the governed execution primitive in Kairos.
 *
 * Every action — whether triggered by a user, a mission, an automation,
 * or an AI provider — is represented as a Command with explicit
 * approval, execution, and audit requirements.
 */

export type CommandType = "shell" | "api_call" | "connector" | "plugin" | "workflow" | "ai_dispatch" | "system";

export type CommandStatus = "draft" | "pending_approval" | "approved" | "rejected" | "queued" | "executing" | "completed" | "failed" | "cancelled";

export type CommandRiskLevel = "none" | "low" | "medium" | "high" | "critical";

export type CommandApprovalRequirement = "none" | "single" | "multi" | "codex";

export type CommandExecutionMode = "sync" | "async" | "scheduled";

export interface CommandInput {
  /** Structured parameters for the command. */
  params: Record<string, unknown>;
  /** Memory references consumed by this command. */
  memoryRefs: string[];
  /** Knowledge context ID, if applicable. */
  knowledgeId: string | null;
  /** Optional mission context. */
  missionId: string | null;
}

export interface CommandOutput {
  /** Raw output from the command (sanitized). */
  result: string | null;
  /** Structured summary for the timeline. */
  summary: string;
  /** Artifacts produced by this command. */
  artifactRefs: string[];
  /** Exit code or status. */
  status: "success" | "failure" | "timeout" | "cancelled";
}

export interface CommandCapability {
  /** Capability identifier (e.g., "file.read", "api.post", "connector.n8n.trigger"). */
  id: string;
  /** Human-readable name. */
  name: string;
  /** The type of command this capability maps to. */
  type: CommandType;
  /** Whether this capability is dangerous and requires elevated approval. */
  dangerous: boolean;
  /** Whether this capability is currently available. */
  available: boolean;
}

export interface Command {
  id: string;
  /** Short display name. */
  title: string;
  /** What this command does. */
  description: string;
  type: CommandType;
  status: CommandStatus;
  riskLevel: CommandRiskLevel;
  approval: CommandApprovalRequirement;
  executionMode: CommandExecutionMode;
  /** What capability does this command use. */
  capability: CommandCapability;
  /** Input parameters. */
  input: CommandInput;
  /** Output (set after execution). */
  output: CommandOutput | null;
  /** Who or what triggered this command. */
  triggeredBy: "user" | "mission" | "automation" | "provider" | "schedule";
  /** When execution was requested. */
  requestedAt: string;
  /** When execution started. */
  startedAt: string | null;
  /** When execution finished. */
  completedAt: string | null;
  /** Optional retry count. */
  retryCount: number;
}

// ---------------------------------------------------------------------------
// Automation
// ---------------------------------------------------------------------------

export type AutomationStatus = "active" | "paused" | "disabled" | "error";
export type AutomationTrigger = "schedule" | "event" | "mission_status_change" | "decision_change" | "memory_created" | "manual";
export type AutomationScope = "global" | "mission" | "workspace" | "personal";

export interface AutomationCondition {
  /** Field to evaluate (e.g., "mission.status"). */
  field: string;
  /** Operator (e.g., "eq", "neq", "contains"). */
  operator: string;
  /** Expected value. */
  value: string;
}

export interface AutomationAction {
  /** Type of command to execute. */
  commandType: CommandType;
  /** The command capability ID. */
  capabilityId: string;
  /** Parameters passed to the command. */
  params: Record<string, unknown>;
}

export interface AutomationPolicy {
  /** Maximum runs per day. */
  maxRunsPerDay: number;
  /** Cooldown between runs in seconds. */
  cooldownSeconds: number;
  /** Whether failures should stop the automation. */
  haltOnFailure: boolean;
  /** Whether to retry on failure. */
  retryOnFailure: boolean;
  /** Maximum retries. */
  maxRetries: number;
}

export interface Automation {
  id: string;
  name: string;
  description: string | null;
  status: AutomationStatus;
  trigger: AutomationTrigger;
  scope: AutomationScope;
  /** When this automation triggers. */
  triggerConfig: Record<string, unknown>;
  /** Conditions that must be met. */
  conditions: AutomationCondition[];
  /** Actions to execute. */
  actions: AutomationAction[];
  /** Safety policy. */
  policy: AutomationPolicy;
  /** Optional related mission. */
  missionId: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface AutomationRun {
  id: string;
  automationId: string;
  status: "running" | "completed" | "failed" | "cancelled";
  startedAt: string;
  completedAt: string | null;
  /** Commands created by this automation. */
  commandIds: string[];
  /** Error message if failed. */
  error: string | null;
  /** The trigger event that started this run. */
  triggerEvent: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Plugin & Connector Foundation
// ---------------------------------------------------------------------------

/**
 * Plugins and Connectors extend Kairos by registering capabilities
 * into the Command Engine. Nothing runs outside the governed pipeline:
 *   Register → Command → Approval → Execution → Timeline
 */

// ---------------------------------------------------------------------------
// Plugin
// ---------------------------------------------------------------------------

export type PluginType = "command" | "ui" | "provider" | "automation" | "memory" | "knowledge";

export type PluginStatus = "installing" | "active" | "disabled" | "error" | "uninstalling";

export type PluginInstallState = "not_installed" | "installing" | "installed" | "updating" | "failed";

export type PluginPermission = "read" | "write" | "execute" | "network" | "filesystem";

export type PluginRiskLevel = "verified" | "reviewed" | "community" | "untrusted";

export interface PluginExecutionBoundary {
  /** Whether this plugin can make network calls. */
  networkAllowed: boolean;
  /** Whether this plugin can access the filesystem. */
  filesystemAllowed: boolean;
  /** Maximum memory in MB. */
  maxMemoryMB: number;
  /** Timeout in seconds. */
  timeoutSeconds: number;
  /** Whether this plugin runs in isolation. */
  sandboxed: boolean;
}

export interface PluginCapability {
  /** Capability identifier registered into the Command Engine. */
  id: string;
  name: string;
  description: string;
  /** The command type this capability maps to. */
  commandType: CommandType;
  /** Whether approval is required to execute. */
  requiresApproval: boolean;
  /** Whether the capability is dangerous. */
  dangerous: boolean;
  /** Permissions needed. */
  permissions: PluginPermission[];
}

export interface PluginManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  type: PluginType;
  /** Author or organization. */
  author: string | null;
  /** The capabilities this plugin registers. */
  capabilities: PluginCapability[];
  /** Execution isolation boundary. */
  boundary: PluginExecutionBoundary;
  /** Minimum Kairos version required. */
  minKairosVersion: string | null;
}

export interface Plugin {
  id: string;
  manifest: PluginManifest;
  status: PluginStatus;
  installState: PluginInstallState;
  riskLevel: PluginRiskLevel;
  /** Error message if status is "error". */
  error: string | null;
  installedAt: string | null;
  updatedAt: string | null;
}

// ---------------------------------------------------------------------------
// Connector
// ---------------------------------------------------------------------------

export type ConnectorType = "n8n" | "webhook" | "api" | "database" | "filesystem" | "message_queue";

export type ConnectorStatus = "connected" | "disconnected" | "degraded" | "unconfigured";

export type ConnectorAuthType = "none" | "api_key" | "oauth2" | "basic" | "token";

export type ConnectorSyncState = "synced" | "syncing" | "stale" | "failed" | "never_synced";

export type ConnectorScope = "global" | "mission" | "workspace";

export interface ConnectorPermission {
  type: "read" | "write" | "execute" | "admin";
  target: string;
}

export interface ConnectorCapability {
  id: string;
  name: string;
  description: string;
  commandType: CommandType;
  requiresApproval: boolean;
  dangerous: boolean;
}

export interface ConnectorHealth {
  /** Last successful health check. */
  lastCheck: string | null;
  /** Whether the connector responded. */
  reachable: boolean | null;
  /** Health check message. */
  message: string | null;
  /** Latency in milliseconds. */
  latencyMs: number | null;
}

export interface Connector {
  id: string;
  name: string;
  version: string;
  description: string;
  type: ConnectorType;
  status: ConnectorStatus;
  authType: ConnectorAuthType;
  /** Whether authentication is configured. */
  authConfigured: boolean;
  /** The capabilities this connector registers. */
  capabilities: ConnectorCapability[];
  /** Sync state for connectors that maintain local state. */
  syncState: ConnectorSyncState;
  /** Health state. */
  health: ConnectorHealth;
  scope: ConnectorScope;
  tags: string[];
  baseUrl: string | null;
  createdAt: string;
  updatedAt: string;
}

// ---------------------------------------------------------------------------
// Capability Registry
// ---------------------------------------------------------------------------

export type CapabilitySource = "plugin" | "connector" | "builtin";

export type CapabilityStatus = "available" | "disabled" | "error";

export interface CapabilityPolicy {
  /** Whether this capability requires approval by default. */
  defaultApproval: boolean;
  /** Maximum allowed risk level for auto-approval. */
  autoApproveBelow: CommandRiskLevel;
  /** Whether capabilities from this source need health verification. */
  requireHealthCheck: boolean;
}

export interface CapabilityRiskAssessment {
  capabilityId: string;
  riskLevel: CommandRiskLevel;
  /** Why this risk level was assigned. */
  rationale: string;
  /** Whether this capability is safe for unattended execution. */
  safeForAutomation: boolean;
  assessedAt: string;
}

export interface RegisteredCapability {
  id: string;
  source: CapabilitySource;
  /** The plugin or connector that registered this. */
  ownerId: string;
  /** The capability definition. */
  definition: PluginCapability | ConnectorCapability;
  status: CapabilityStatus;
  policy: CapabilityPolicy;
  riskAssessment: CapabilityRiskAssessment | null;
  /** When this capability was registered. */
  registeredAt: string;
}

// ---------------------------------------------------------------------------
// Timeline + Brief
// ---------------------------------------------------------------------------

export interface TimelineItem {
  id: string;
  kind: "mission_update" | "decision" | "memory" | "workspace" | "system";
  title: string;
  summary: string;
  timestamp: string;
  relatedId: string | null;
}

export interface BriefCard {
  id: string;
  kind: "decision" | "mission" | "memory" | "system" | "approval";
  title: string;
  description: string;
  meta: string | null;
  timestamp: string | null;
}

// ---------------------------------------------------------------------------
// Assistant context + Navigation (unchanged)
// ---------------------------------------------------------------------------

export interface AssistantContext {
  activeMissionId: string | null;
  activeWorkspaceId: string | null;
  recentDecisions: string[];
  recentMemories: string[];
  userNotes: string;
}

export interface UserIntent {
  goal: string;
  context: AssistantContext;
  preferredAction: "plan" | "ask" | "review" | "execute";
}

export type ShellSurface = "good-morning" | "continue-working" | "ask-kai" | "todays-brief" | "workspace";

export interface NavigationState {
  activeSurface: ShellSurface | null;
  sidebarCollapsed: boolean;
}
