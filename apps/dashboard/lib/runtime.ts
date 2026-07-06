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
import { useKairosDispatch } from "./state";
import {
  getProjects,
  getTasks,
  getMemories,
  getHealth,
  getAICapabilities,
  type ApiResult,
  type Project,
  type Task,
  type Memory,
  type Health,
  type AICapabilities,
} from "./api";
import type {
  Mission,
  Decision,
  MemoryReference,
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
    status: (p.status as Mission["status"]) || "active",
    priority: (p.priority as Mission["priority"]) || "medium",
    targetDate: null,
    createdAt: p.created_at,
    updatedAt: p.updated_at,
  };
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
    tags: m.tags ?? [],
    importance: (m.importance as MemoryReference["importance"]) || "medium",
    createdAt: m.created_at,
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
 * useMemories — fetches memories from the API, maps to MemoryReference,
 * and dispatches into shared state.
 */
export function useMemories() {
  const dispatch = useKairosDispatch();

  return useApi<Memory[]>(
    useCallback(
      async (signal) => {
        void signal;
        const result = await getMemories();
        if (result.ok) {
          dispatch({ type: "SET_MEMORIES", payload: result.data.map(memoryToReference) });
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
// Mission runtime
// ---------------------------------------------------------------------------

export interface MissionRuntime {
  selectedMissionId: string | null;
  selectMission: (id: string | null) => void;
}

/**
 * useMissionRuntime — mission selection and lifecycle.
 */
export function useMissionRuntime(): MissionRuntime {
  const [selectedMissionId, setSelectedMissionId] = useState<string | null>(null);

  const selectMission = useCallback((id: string | null) => {
    setSelectedMissionId(id);
  }, []);

  return { selectedMissionId, selectMission };
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
