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
// Mission timeline events
// ---------------------------------------------------------------------------

/**
 * MissionTimelineEvent — a single event in the mission's history.
 * Every status transition, approval decision, and execution state change
 * produces an event.
 */
export interface MissionTimelineEvent {
  id: string;
  missionId: string;
  /** Time the event occurred. */
  timestamp: string;
  kind:
    | "created"
    | "status_change"
    | "plan_generated"
    | "plan_revised"
    | "approval_requested"
    | "approval_granted"
    | "approval_rejected"
    | "step_queued"
    | "step_started"
    | "step_completed"
    | "step_failed"
    | "step_retried"
    | "artifact_created"
    | "outcome_recorded"
    | "archived";
  title: string;
  description: string;
  /** The status after this event, if applicable. */
  resultingStatus: MissionStatus | null;
  /** Related entity reference. */
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
