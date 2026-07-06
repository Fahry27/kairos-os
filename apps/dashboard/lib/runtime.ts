/**
 * Kairos Runtime — request lifecycle and state bridge hooks.
 *
 * useApi<T>           — generic Fetch API hook managing: loading, error,
 *                        data, refresh, isRefreshing, and AbortController.
 *
 * Domain hooks        — bridge lib/api.ts → lib/state.tsx dispatcher.
 *                        Each hook calls the API and dispatches results
 *                        into the shared Kairos state context.
 *
 * useConversation     — Ask Kai conversation runtime (messages, draft, abort).
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useKairosState, useKairosDispatch } from "./state";
import {
  getProjects,
  getTasks,
  getMemories,
  getHealth,
  getAICapabilities,
  type ApiResult,
  type Project,
  type Task,
  type Memory as ApiMemory,
  type Health,
  type AICapabilities,
} from "./api";
import type {
  Mission,
  MissionStatus,
  MissionTimelineEvent,
  TimelineEvent,
  TimelineEventType,
  TimelineFilter,
  Memory,
  MemoryCollection,
  MemoryReference,
  MemoryType,
  Decision,
} from "./types";

// ---------------------------------------------------------------------------
// Generic useApi hook
// ---------------------------------------------------------------------------

export interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  isRefreshing: boolean;
}

export interface UseApiReturn<T> extends UseApiState<T> {
  refresh: () => Promise<void>;
  abort: () => void;
}

/**
 * useApi — generic request lifecycle hook.
 *
 * Calls apiFn on mount and optionally on refresh.
 * Manages AbortController so in-flight requests are canceled on unmount
 * or when manually aborted.
 */
export function useApi<T>(
  apiFn: (signal: AbortSignal) => Promise<ApiResult<T>>,
  deps: unknown[] = [],
): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: true,
    error: null,
    isRefreshing: false,
  });

  const abortRef = useRef<AbortController | null>(null);

  const execute = useCallback(
    async (isRefresh = false) => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
      const controller = new AbortController();
      abortRef.current = controller;

      if (isRefresh) {
        setState((s) => ({ ...s, isRefreshing: true, error: null }));
      } else {
        setState((s) => ({ ...s, loading: true, error: null }));
      }

      try {
        const result = await apiFn(controller.signal);

        if (controller.signal.aborted) return;

        if (result.ok) {
          setState({ data: result.data, loading: false, error: null, isRefreshing: false });
        } else {
          setState({ data: null, loading: false, error: result.error, isRefreshing: false });
        }
      } catch (err) {
        if (controller.signal.aborted) return;

        const message = err instanceof Error ? err.message : "Unknown error";
        setState({ data: null, loading: false, error: message, isRefreshing: false });
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    deps,
  );

  useEffect(() => {
    execute(false);

    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  const refresh = useCallback(() => execute(true), [execute]);
  const abort = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
  }, []);

  return { ...state, refresh, abort };
}

// ---------------------------------------------------------------------------
// API → Domain mappers
// ---------------------------------------------------------------------------

function projectToMission(p: Project): Mission {
  return {
    id: p.id,
    name: p.name,
    description: p.description ?? null,
    status: mapApiStatus(p.status),
    priority: (p.priority as Mission["priority"]) || "medium",
    trigger: { kind: "user", sourceId: null, description: "Created via API" },
    context: { relatedMissionIds: [], userNotes: "", constraints: [], tags: [] },
    plans: [],
    activePlanVersion: null,
    approvals: [],
    stepExecutions: [],
    artifacts: [],
    outcome: null,
    triggeredAt: p.created_at,
    createdAt: p.created_at,
    updatedAt: p.updated_at,
  };
}

function mapApiStatus(apiStatus: string): MissionStatus {
  const statusMap: Record<string, MissionStatus> = {
    active: "executing",
    completed: "completed",
    paused: "cancelled",
    archived: "archived",
  };
  return statusMap[apiStatus] || "draft";
}

function taskToDecision(t: Task): Decision {
  return {
    id: t.id,
    title: t.title,
    description: t.description ?? null,
    status: (t.status as Decision["status"]) || "active",
    priority: (t.priority as Decision["priority"]) || "medium",
    missionId: t.project_id ?? null,
    dueDate: t.due_date ?? null,
    createdAt: t.created_at,
    updatedAt: t.updated_at,
  };
}

function memoryToReference(m: Memory): MemoryReference {
  return {
    id: m.id,
    type: m.type,
    snippet: m.content.slice(0, 120),
    importance: m.importance,
    isPinned: m.isPinned,
    tags: m.tags.map((t) => t.name),
    createdAt: m.createdAt,
  };
}

function apiMemoryToDomain(m: ApiMemory): Memory {
  return {
    id: m.id,
    title: m.content.slice(0, 80),
    content: m.content,
    type: (m.type as MemoryType) || "note",
    importance: (m.importance as Memory["importance"]) || "medium",
    visibility: "mission",
    status: "active",
    source: { kind: "user", sourceId: null, label: m.source ?? "API" },
    relationships: m.project_id ? [{ targetKind: "mission", targetId: m.project_id, label: "belongs_to" }] : [],
    tags: (m.tags ?? []).map((name) => ({ id: name, name, category: null })),
    collectionId: null,
    isPinned: false,
    createdAt: m.created_at,
    updatedAt: m.updated_at,
  };
}

// ---------------------------------------------------------------------------
// Domain runtime hooks — bridge API → state dispatch
// ---------------------------------------------------------------------------

/**
 * useMissions — fetches projects from the API and maps them into
 * the Kairos Mission domain model, dispatching into shared state.
 */
export function useMissions() {
  const dispatch = useKairosDispatch();

  return useApi<Project[]>(
    useCallback(
      async (signal) => {
        void signal;
        const result = await getProjects();
        if (result.ok) {
          dispatch({ type: "SET_MISSIONS", payload: result.data.map(projectToMission) });
        }
        return result;
      },
      [dispatch],
    ),
  );
}

/**
 * useDecisions — fetches tasks from the API and maps them into
 * the Kairos Decision domain model, dispatching into shared state.
 */
export function useDecisions() {
  const dispatch = useKairosDispatch();

  return useApi<Task[]>(
    useCallback(
      async (signal) => {
        void signal;
        const result = await getTasks();
        if (result.ok) {
          dispatch({ type: "SET_DECISIONS", payload: result.data.map(taskToDecision) });
        }
        return result;
      },
      [dispatch],
    ),
  );
}

/**
 * useMemories — fetches memories from the API, maps to domain Memory,
 * dispatching full Memory entities + memory refs into shared state.
 */
export function useMemories() {
  const dispatch = useKairosDispatch();

  return useApi<ApiMemory[]>(
    useCallback(
      async (signal) => {
        void signal;
        const result = await getMemories();
        if (result.ok) {
          const domainMemories = result.data.map(apiMemoryToDomain);
          dispatch({ type: "SET_MEMORIES", payload: domainMemories });
          dispatch({ type: "SET_MEMORY_REFS", payload: domainMemories.map(memoryToReference) });
        }
        return result;
      },
      [dispatch],
    ),
  );
}

/**
 * useHealth — fetches the API health endpoint.
 */
export function useHealth() {
  return useApi<Health>(
    useCallback(async (signal) => {
      void signal;
      return getHealth();
    }, []),
  );
}

/**
 * useAICapabilities — fetches the AI capabilities endpoint.
 */
export function useAICapabilities() {
  return useApi<AICapabilities>(
    useCallback(async (signal) => {
      void signal;
      return getAICapabilities();
    }, []),
  );
}

// ---------------------------------------------------------------------------
// Conversation runtime (Ask Kai)
// ---------------------------------------------------------------------------

export interface ConversationMessage {
  id: string;
  role: "user" | "kairos";
  content: string;
  timestamp: string;
  status: "sent" | "pending" | "error";
}

export interface Conversation {
  id: string;
  title: string;
  messages: ConversationMessage[];
  createdAt: string;
  updatedAt: string;
}

let messageCounter = 0;
function nextMessageId(): string {
  messageCounter += 1;
  return `msg_${Date.now()}_${messageCounter}`;
}
function nextConversationId(): string {
  return `conv_${Date.now()}`;
}

/**
 * useConversation — Ask Kai conversation runtime.
 *
 * Manages:
 *   - current conversation (messages, draft)
 *   - conversation list
 *   - send/receive lifecycle
 *   - abort controller for in-flight requests
 *
 * No mock responses. No fake messages. The architecture is ready
 * for real API wiring.
 */
export function useConversation() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const activeConversation = conversations.find((c) => c.id === activeConversationId) ?? null;

  const newConversation = useCallback(() => {
    const conv: Conversation = {
      id: nextConversationId(),
      title: "New conversation",
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setConversations((prev) => [conv, ...prev]);
    setActiveConversationId(conv.id);
    setDraft("");
    setSendError(null);
  }, []);

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;

      let convId = activeConversationId;

      if (!convId) {
        const conv: Conversation = {
          id: nextConversationId(),
          title: content.slice(0, 40),
          messages: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        setConversations((prev) => [conv, ...prev]);
        convId = conv.id;
        setActiveConversationId(convId);
      }

      const userMessage: ConversationMessage = {
        id: nextMessageId(),
        role: "user",
        content: content.trim(),
        timestamp: new Date().toISOString(),
        status: "sent",
      };

      setConversations((prev) =>
        prev.map((c) =>
          c.id === convId
            ? {
                ...c,
                messages: [...c.messages, userMessage],
                updatedAt: new Date().toISOString(),
                title: c.title === "New conversation" ? content.slice(0, 40) : c.title,
              }
            : c,
        ),
      );
      setDraft("");

      // ARCHITECTURE READY: when the AI API is available, uncomment the block below.
      // const controller = new AbortController();
      // abortRef.current = controller;
      // setIsSending(true);
      // try {
      //   const result = await postToApi("/api/v1/ai/ask", { message: content.trim(), conversationId: convId });
      //   if (!controller.signal.aborted && result.ok) {
      //     const kairosMsg: ConversationMessage = { ... result.data ... };
      //     setConversations((prev) => ... add kairosMsg ...);
      //   }
      // } catch (err) { ... }
      // setIsSending(false);
    },
    [activeConversationId],
  );

  const abortSending = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      setIsSending(false);
    }
  }, []);

  return {
    conversations,
    activeConversation,
    activeConversationId,
    selectConversation: setActiveConversationId,
    newConversation,
    draft,
    setDraft,
    sendMessage,
    isSending,
    sendError,
    abortSending,
  };
}

// ---------------------------------------------------------------------------
// Workspace runtime
// ---------------------------------------------------------------------------

export interface WorkspaceRuntime {
  activeWorkspaceId: string | null;
  selectWorkspace: (id: string | null) => void;
  activePanel: string;
  setActivePanel: (panel: string) => void;
  pendingApprovals: number;
}

/**
 * useWorkspaceRuntime — workspace selection, panel sync, approval state.
 */
export function useWorkspaceRuntime(): WorkspaceRuntime {
  const [activeWorkspaceId, setActiveWorkspaceId] = useState<string | null>(null);
  const [activePanel, setActivePanel] = useState("plan");
  const [pendingApprovals] = useState(0);

  const selectWorkspace = useCallback((id: string | null) => {
    setActiveWorkspaceId(id);
    setActivePanel("plan");
  }, []);

  return {
    activeWorkspaceId,
    selectWorkspace,
    activePanel,
    setActivePanel,
    pendingApprovals,
  };
}

// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Mission Engine runtime
// ---------------------------------------------------------------------------

export interface MissionEngineRuntime {
  /** The currently selected mission, or null. */
  selectedMission: Mission | null;
  /** Select a mission by ID. Pass null to deselect. */
  selectMission: (id: string | null) => void;
  /** Filter value for the mission list. */
  filter: string;
  /** Set the mission filter. */
  setFilter: (filter: string) => void;
  /** Approve a pending approval by ID. */
  approveApproval: (approvalId: string, reason?: string) => void;
  /** Reject a pending approval by ID. */
  rejectApproval: (approvalId: string, reason?: string) => void;
  /** Timeline events for the selected mission. */
  timeline: MissionTimelineEvent[];
}

/**
 * useMissionEngine — full Mission Engine runtime.
 *
 * Delegates to shared Kairos state via dispatch.
 * Provides mission selection, approval management, and timeline access.
 */
export function useMissionEngine(): MissionEngineRuntime {
  const state = useKairosState();
  const dispatch = useKairosDispatch();
  const selectMission = useCallback(
    (id: string | null) => {
      dispatch({ type: "SELECT_MISSION", payload: id });
    },
    [dispatch],
  );

  const setFilter = useCallback(
    (filter: string) => {
      dispatch({ type: "SET_MISSION_FILTER", payload: filter as MissionStatus });
    },
    [dispatch],
  );

  const approveApproval = useCallback(
    (approvalId: string, reason?: string) => {
      dispatch({ type: "UPDATE_MISSION_APPROVAL", payload: { approvalId, status: "approved", reason } });
    },
    [dispatch],
  );

  const rejectApproval = useCallback(
    (approvalId: string, reason?: string) => {
      dispatch({ type: "UPDATE_MISSION_APPROVAL", payload: { approvalId, status: "rejected", reason } });
    },
    [dispatch],
  );

  const selectedMission =
    state.missions.find((m) => m.id === state.selectedMissionId) ?? null;

  return {
    selectedMission,
    selectMission,
    filter: state.missionFilter,
    setFilter,
    approveApproval,
    rejectApproval,
    timeline: state.missionTimeline,
  };
}

// ---------------------------------------------------------------------------
// Planning runtime
// ---------------------------------------------------------------------------

export interface PlanningRuntime {
  /** The active plan for the selected mission. */
  activePlan: Mission["plans"][0] | null;
  /** Generate a placeholder for a new plan version (architecture only). */
  revisionReady: boolean;
}

/**
 * usePlanningRuntime — planning layer for the selected mission.
 *
 * Returns the active plan and signals whether a plan revision can
 * be triggered. No plan generation logic.
 */
export function usePlanningRuntime(): PlanningRuntime {
  const state = useKairosState();
  const mission = state.missions.find((m) => m.id === state.selectedMissionId) ?? null;

  const plans = mission?.plans ?? [];
  const activePlan =
    mission && mission.activePlanVersion !== null
      ? plans.find((p) => p.version === mission.activePlanVersion) ?? null
      : null;

  return {
    activePlan,
    revisionReady: (mission?.status === "draft" || mission?.status === "planning") ?? false,
  };
}

// ---------------------------------------------------------------------------
// Execution runtime
// ---------------------------------------------------------------------------

export interface ExecutionRuntime {
  /** Queued steps for the selected mission. */
  queuedCount: number;
  /** Currently running steps. */
  runningCount: number;
  /** Steps ready for retry. */
  retryReadyCount: number;
  /** Whether the mission is currently executing. */
  isExecuting: boolean;
  /** Whether execution is paused. */
  isPaused: boolean;
}

/**
 * useExecutionRuntime — execution status for the selected mission.
 *
 * No provider execution. Provides counts and status flags
 * for the execution panel.
 */
export function useExecutionRuntime(): ExecutionRuntime {
  const state = useKairosState();
  const mission = state.missions.find((m) => m.id === state.selectedMissionId) ?? null;

  const executions = mission?.stepExecutions ?? [];

  return {
    queuedCount: executions.filter((e) => e.status === "queued").length,
    runningCount: executions.filter((e) => e.status === "running").length,
    retryReadyCount: executions.filter((e) => e.status === "retry_ready").length,
    isExecuting: mission?.status === "executing",
    isPaused: mission?.status !== "executing" && mission?.status === "approved",
  };
}

// ---------------------------------------------------------------------------
// Today's Brief runtime
// ---------------------------------------------------------------------------

export interface BriefRuntime {
  loading: boolean;
  lastRefreshed: string | null;
  refresh: () => void;
}

/**
 * useBriefRuntime — aggregates data fetching for Today's Brief.
 *
 * Future: batch multiple API calls and orchestrate refresh across
 * all sections (priorities, calendar, system health, memory, decisions).
 */
export function useBriefRuntime(): BriefRuntime {
  const [lastRefreshed, setLastRefreshed] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLastRefreshed(new Date().toISOString());
  }, []);

  return { loading: false, lastRefreshed, refresh };
}

// ---------------------------------------------------------------------------
// Memory Engine runtime
// ---------------------------------------------------------------------------

/**
 * useMemoryEngine — full Memory Engine runtime.
 *
 * Provides search, pinning, and collection access via shared state.
 */
export function useMemoryEngine() {
  const state = useKairosState();
  const dispatch = useKairosDispatch();

  const search = useCallback(
    (query: string) => {
      dispatch({ type: "SET_MEMORY_SEARCH_QUERY", payload: query });
    },
    [dispatch],
  );

  const pinMemory = useCallback(
    (id: string) => {
      dispatch({ type: "PIN_MEMORY", payload: id });
    },
    [dispatch],
  );

  const unpinMemory = useCallback(
    (id: string) => {
      dispatch({ type: "UNPIN_MEMORY", payload: id });
    },
    [dispatch],
  );

  const selectMemory = useCallback(
    (id: string | null) => {
      dispatch({ type: "SELECT_MEMORY", payload: id });
    },
    [dispatch],
  );

  const filteredMemories = state.memorySearchQuery
    ? state.memories.filter(
        (m) =>
          m.title.toLowerCase().includes(state.memorySearchQuery.toLowerCase()) ||
          m.content.toLowerCase().includes(state.memorySearchQuery.toLowerCase()),
      )
    : state.memories;

  const pinnedMemories = state.memories.filter((m) => state.pinnedMemoryIds.includes(m.id));
  const selectedMemory = state.memories.find((m) => m.id === state.selectedMemoryId) ?? null;
  const collections = state.memoryCollections;

  return {
    memories: filteredMemories,
    pinnedMemories,
    selectedMemory,
    selectMemory,
    collections,
    searchQuery: state.memorySearchQuery,
    search,
    pinMemory,
    unpinMemory,
  };
}

/**
 * useMemoryForMission — returns memories related to the given mission ID.
 */
export function useMemoryForMission(missionId: string | null) {
  const state = useKairosState();

  if (!missionId) return [];

  return state.memories.filter((m) =>
    m.relationships.some((r) => r.targetKind === "mission" && r.targetId === missionId),
  );
}

/**
 * useMemoryForWorkspace — returns memories related to the given workspace ID.
 */
export function useMemoryForWorkspace(workspaceId: string | null) {
  const state = useKairosState();

  if (!workspaceId) return [];

  return state.memories.filter((m) =>
    m.relationships.some((r) => r.targetKind === "workspace" && r.targetId === workspaceId),
  );
}

// ---------------------------------------------------------------------------
// Knowledge Engine preparation (future interface)
// ---------------------------------------------------------------------------

/**
 * KnowledgeEngine — placeholder interface for the future Knowledge Engine.
 *
 * The Knowledge Engine will:
 *   - Index memories for retrieval
 *   - Build a semantic knowledge graph
 *   - Provide context to AI providers without exposing raw memory data
 *
 * This interface exists as a clean architecture boundary. No implementation yet.
 */
export interface KnowledgeEngine {
  /** Query memories relevant to a context. */
  query: (context: string, limit?: number) => Memory[];
  /** Get all knowledge relevant to a mission. */
  forMission: (missionId: string) => Memory[];
  /** Get all knowledge relevant to a workspace. */
  forWorkspace: (workspaceId: string) => Memory[];
  /** Re-index all memories (future: trigger embedding update). */
  reindex: () => void;
}

/**
 * useKnowledgeEngine — placeholder hook returning null.
 *
 * Architecture boundary for future Knowledge Engine integration.
 * No implementation. No embeddings. No AI calls.
 */
export function useKnowledgeEngine(): KnowledgeEngine | null {
  // Future: wire to actual knowledge index
  return null;
}


// ---------------------------------------------------------------------------
// Timeline Engine runtime
// ---------------------------------------------------------------------------

function idCounter() {
  let n = 0;
  return () => {
    n += 1;
    return `tl_${Date.now()}_${n}`;
  };
}
const nextTimelineId = idCounter();

/**
 * useTimelineEngine — full Timeline Engine runtime.
 *
 * Provides filtered timeline access, event recording, and
 * per-entity timeline slices for missions, memories, workspaces,
 * and decisions.
 */
export function useTimelineEngine() {
  const state = useKairosState();
  const dispatch = useKairosDispatch();

  const selectEvent = useCallback(
    (id: string | null) => {
      dispatch({ type: "SELECT_TIMELINE_EVENT", payload: id });
    },
    [dispatch],
  );

  const setFilter = useCallback(
    (filter: Partial<TimelineFilter>) => {
      dispatch({ type: "SET_TIMELINE_FILTER", payload: filter });
    },
    [dispatch],
  );

  const recordEvent = useCallback(
    (event: Omit<TimelineEvent, "id">) => {
      const full: TimelineEvent = { ...event, id: nextTimelineId() };
      dispatch({ type: "ADD_TIMELINE_EVENT", payload: full });
      return full;
    },
    [dispatch],
  );

  const { timelineEvents: all, timelineFilter: filter, selectedTimelineEventId } = state;

  const filtered = all.filter((e) => {
    if (filter.types.length > 0 && !filter.types.includes(e.type)) return false;
    if (filter.missionId && e.missionId !== filter.missionId) return false;
    if (filter.workspaceId && e.workspaceId !== filter.workspaceId) return false;
    if (filter.scopes.length > 0 && !filter.scopes.includes(e.scope)) return false;
    if (filter.query) {
      const q = filter.query.toLowerCase();
      if (!e.title.toLowerCase().includes(q) && !e.description.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const selectedEvent = all.find((e) => e.id === selectedTimelineEventId) ?? null;

  return {
    events: filtered,
    allEvents: all,
    selectedEvent,
    selectEvent,
    filter,
    setFilter,
    recordEvent,
  };
}

/**
 * useMissionTimeline — returns timeline events for a specific mission.
 */
export function useMissionTimeline(missionId: string | null) {
  const state = useKairosState();
  if (!missionId) return [];
  return state.timelineEvents.filter((e) => e.missionId === missionId);
}

/**
 * useMemoryTimeline — returns timeline events for a specific memory.
 */
export function useMemoryTimeline(memoryId: string | null) {
  const state = useKairosState();
  if (!memoryId) return [];
  return state.timelineEvents.filter((e) => e.memoryId === memoryId);
}

/**
 * useWorkspaceTimeline — returns timeline events for a specific workspace.
 */
export function useWorkspaceTimeline(workspaceId: string | null) {
  const state = useKairosState();
  if (!workspaceId) return [];
  return state.timelineEvents.filter((e) => e.workspaceId === workspaceId);
}

/**
 * useDecisionTimeline — returns timeline events for a specific decision.
 */
export function useDecisionTimeline(decisionId: string | null) {
  const state = useKairosState();
  if (!decisionId) return [];
  return state.timelineEvents.filter((e) => e.decisionId === decisionId);
}

/**
 * useRecentTimeline — returns the most recent N timeline events.
 */
export function useRecentTimeline(limit = 20) {
  const state = useKairosState();
  return state.timelineEvents.slice(0, limit);
}

/**
 * useTodayTimeline — returns timeline events from today only.
 */
export function useTodayTimeline() {
  const state = useKairosState();
  return state.timelineEvents.filter((e) => e.timestamp.startsWith(state.todayDate));
}
