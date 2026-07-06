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

export type Status = "active" | "completed" | "paused" | "archived";

export type Priority = "low" | "medium" | "high" | "critical";

export type ApprovalState = "pending" | "approved" | "rejected" | "expired";

// ---------------------------------------------------------------------------
// Core domain entities
// ---------------------------------------------------------------------------

export interface Mission {
  id: string;
  name: string;
  description: string | null;
  status: Status;
  priority: Priority;
  /** Optional target date for the mission. */
  targetDate: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Decision {
  id: string;
  title: string;
  description: string | null;
  status: Status;
  priority: Priority;
  /** The mission this decision belongs to, if any. */
  missionId: string | null;
  dueDate: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface Workspace {
  id: string;
  /** The goal the user set for this workspace session. */
  goal: string;
  status: "active" | "completed" | "paused";
  createdAt: string;
  updatedAt: string;
}

export interface MemoryReference {
  id: string;
  type: string;
  /** Preview snippet — first ~120 chars. */
  snippet: string;
  tags: string[];
  importance: Priority;
  createdAt: string;
}

// ---------------------------------------------------------------------------
// Timeline
// ---------------------------------------------------------------------------

export interface TimelineItem {
  id: string;
  kind: "mission_update" | "decision" | "memory" | "workspace" | "system";
  title: string;
  summary: string;
  timestamp: string;
  /** Optional link to the related entity. */
  relatedId: string | null;
}

// ---------------------------------------------------------------------------
// Brief / Feed cards
// ---------------------------------------------------------------------------

export interface BriefCard {
  id: string;
  kind: "decision" | "mission" | "memory" | "system" | "approval";
  title: string;
  description: string;
  /** Optional metadata: priority badge, count, etc. */
  meta: string | null;
  timestamp: string | null;
}

// ---------------------------------------------------------------------------
// Assistant context
// ---------------------------------------------------------------------------

export interface AssistantContext {
  activeMissionId: string | null;
  activeWorkspaceId: string | null;
  recentDecisions: string[];
  recentMemories: string[];
  /** Freeform context the user attaches to an Ask Kai prompt. */
  userNotes: string;
}

export interface UserIntent {
  goal: string;
  context: AssistantContext;
  preferredAction: "plan" | "ask" | "review" | "execute";
}

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------

export type ShellSurface = "good-morning" | "continue-working" | "ask-kai" | "todays-brief" | "workspace";

export interface NavigationState {
  activeSurface: ShellSurface | null;
  sidebarCollapsed: boolean;
}
