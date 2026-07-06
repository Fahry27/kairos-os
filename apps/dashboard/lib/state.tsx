/**
 * Kairos Core — Application State.
 *
 * Lightweight state management via React Context + useReducer.
 * No external state library. Every surface reads from this single source.
 *
 * State slices:
 *   missions          — active missions (full Mission Engine domain model)
 *   decisions         — open decisions
 *   workspaces        — workspace sessions
 *   memories          — full Memory entities (Memory Engine)
 *   memoryRefs        — lightweight MemoryReference list for cards/surfaces
 *   memoryCollections — named groups of memories
 *   pinnedMemoryIds   — IDs of pinned memories for quick access
 *   selectedMemoryId  — currently focused memory
 *   memorySearchQuery — active search query
 *   missionTimeline    — per-mission timeline events (legacy, retained for Mission Engine)
 *   timelineEvents     — unified Timeline Engine events
 *   timelineFilter     — active filter state for the timeline view
 *   selectedTimelineEventId — currently focused timeline event
 *   navigation        — sidebar + active surface
 *   assistant         — Ask Kai conversation context
 *   selectedMissionId — currently focused mission
 *   todayDate         — today's date context
 *   missionFilter     — active filter for the mission list
 */

import React, { createContext, useContext, useReducer, type Dispatch, type ReactNode } from "react";

import type {
  Mission,
  MissionStatus,
  MissionApproval,
  MissionArtifact,
  MissionTimelineEvent,
  TimelineEvent,
  TimelineFilter,
  KnowledgeItem,
  KnowledgeCollection,
  KnowledgeContext,
  KnowledgeQuery,
  AIProvider,
  AIRequest,
  AIResponse,
  AIExecutionContext,
  AIRoutePolicy,
  AIUsageEstimate,
  Command,
  CommandCapability,
  Automation,
  AutomationRun,
  AutomationPolicy,
  Decision,
  Workspace,
  Memory,
  MemoryCollection,
  MemoryReference,
  TimelineItem,
  AssistantContext,
  NavigationState,
  ShellSurface,
} from "./types";

// ---------------------------------------------------------------------------
// State shape
// ---------------------------------------------------------------------------

export type MissionFilter = "all" | MissionStatus;

export interface KairosState {
  missions: Mission[];
  selectedMissionId: string | null;
  missionFilter: MissionFilter;
  missionTimeline: MissionTimelineEvent[];
  /** Unified Timeline Engine events. */
  timelineEvents: TimelineEvent[];
  /** Active timeline filter. */
  timelineFilter: TimelineFilter;
  /** Selected timeline event ID for detail view. */
  selectedTimelineEventId: string | null;
  /** Knowledge Engine items. */
  knowledgeItems: KnowledgeItem[];
  /** Named collections of knowledge items. */
  knowledgeCollections: KnowledgeCollection[];
  /** Selected knowledge item ID for detail view. */
  selectedKnowledgeId: string | null;
  /** Active knowledge query state. */
  knowledgeQuery: KnowledgeQuery;
  /** Last assembled knowledge context. */
  knowledgeContext: KnowledgeContext | null;
  /** Configured AI providers. */
  aiProviders: AIProvider[];
  /** Active route policy. */
  aiRoutePolicy: AIRoutePolicy;
  /** Active AI request. */
  aiRequest: AIRequest | null;
  /** Last AI response. */
  aiResponse: AIResponse | null;
  /** AI execution context. */
  aiExecutionContext: AIExecutionContext | null;
  /** Whether an AI request is in flight. */
  aiRequestPending: boolean;
  /** Abort controller reference for in-flight requests (not serialized). */
  aiAbortControllerId: string | null;
  /** Available command capabilities. */
  commandCapabilities: CommandCapability[];
  /** Command entities (history and pending). */
  commands: Command[];
  /** Currently selected command ID. */
  selectedCommandId: string | null;
  /** Automations. */
  automations: Automation[];
  /** Selected automation ID. */
  selectedAutomationId: string | null;
  /** Automation runs. */
  automationRuns: AutomationRun[];
  decisions: Decision[];
  workspaces: Workspace[];
  memories: Memory[];
  memoryRefs: MemoryReference[];
  memoryCollections: MemoryCollection[];
  pinnedMemoryIds: string[];
  selectedMemoryId: string | null;
  memorySearchQuery: string;
  timeline: TimelineItem[];
  navigation: NavigationState;
  assistant: AssistantContext;
  todayDate: string;
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

export type KairosAction =
  | { type: "SET_MISSIONS"; payload: Mission[] }
  | { type: "SELECT_MISSION"; payload: string | null }
  | { type: "SET_MISSION_FILTER"; payload: MissionFilter }
  | { type: "ADD_MISSION"; payload: Mission }
  | { type: "ADD_MISSION_APPROVAL"; payload: MissionApproval }
  | { type: "UPDATE_MISSION_APPROVAL"; payload: { approvalId: string; status: MissionApproval["status"]; reason?: string } }
  | { type: "ADD_MISSION_ARTIFACT"; payload: MissionArtifact }
  | { type: "ADD_MISSION_TIMELINE_EVENT"; payload: MissionTimelineEvent }
  | { type: "SET_DECISIONS"; payload: Decision[] }
  | { type: "SET_WORKSPACES"; payload: Workspace[] }
  | { type: "SET_MEMORIES"; payload: Memory[] }
  | { type: "SET_MEMORY_REFS"; payload: MemoryReference[] }
  | { type: "SET_MEMORY_COLLECTIONS"; payload: MemoryCollection[] }
  | { type: "SELECT_MEMORY"; payload: string | null }
  | { type: "SET_MEMORY_SEARCH_QUERY"; payload: string }
  | { type: "PIN_MEMORY"; payload: string }
  | { type: "UNPIN_MEMORY"; payload: string }
  | { type: "ADD_TIMELINE_EVENT"; payload: TimelineEvent }
  | { type: "SET_TIMELINE_EVENTS"; payload: TimelineEvent[] }
  | { type: "SELECT_TIMELINE_EVENT"; payload: string | null }
  | { type: "SET_TIMELINE_FILTER"; payload: Partial<TimelineFilter> }
  | { type: "SET_KNOWLEDGE_ITEMS"; payload: KnowledgeItem[] }
  | { type: "SET_KNOWLEDGE_COLLECTIONS"; payload: KnowledgeCollection[] }
  | { type: "SELECT_KNOWLEDGE"; payload: string | null }
  | { type: "SET_KNOWLEDGE_QUERY"; payload: Partial<KnowledgeQuery> }
  | { type: "SET_KNOWLEDGE_CONTEXT"; payload: KnowledgeContext | null }
  | { type: "SET_AI_PROVIDERS"; payload: AIProvider[] }
  | { type: "SET_AI_ROUTE_POLICY"; payload: Partial<AIRoutePolicy> }
  | { type: "SET_AI_REQUEST"; payload: AIRequest | null }
  | { type: "SET_AI_RESPONSE"; payload: AIResponse | null }
  | { type: "SET_AI_EXECUTION_CONTEXT"; payload: AIExecutionContext }
  | { type: "SET_AI_REQUEST_PENDING"; payload: boolean }
  | { type: "SET_AI_ABORT_CONTROLLER_ID"; payload: string | null }
  | { type: "SET_COMMAND_CAPABILITIES"; payload: CommandCapability[] }
  | { type: "SET_COMMANDS"; payload: Command[] }
  | { type: "ADD_COMMAND"; payload: Command }
  | { type: "SELECT_COMMAND"; payload: string | null }
  | { type: "SET_AUTOMATIONS"; payload: Automation[] }
  | { type: "SELECT_AUTOMATION"; payload: string | null }
  | { type: "ADD_AUTOMATION_RUN"; payload: AutomationRun }
  | { type: "SET_AUTOMATION_RUNS"; payload: AutomationRun[] }
  | { type: "ADD_TIMELINE_ITEM"; payload: TimelineItem }
  | { type: "SET_ACTIVE_SURFACE"; payload: ShellSurface }
  | { type: "TOGGLE_SIDEBAR" }
  | { type: "SET_ASSISTANT_CONTEXT"; payload: Partial<AssistantContext> }
  | { type: "RESET_ASSISTANT_CONTEXT" };

// ---------------------------------------------------------------------------
// Initial state
// ---------------------------------------------------------------------------

const today = new Date();
const todayDate = today.toISOString().slice(0, 10);

const initialAssistantContext: AssistantContext = {
  activeMissionId: null,
  activeWorkspaceId: null,
  recentDecisions: [],
  recentMemories: [],
  userNotes: "",
};

const initialState: KairosState = {
  missions: [],
  selectedMissionId: null,
  missionFilter: "all",
  missionTimeline: [],
  timelineEvents: [],
  timelineFilter: { types: [], missionId: null, workspaceId: null, scopes: [], minSeverity: null, query: "" },
  selectedTimelineEventId: null,
  knowledgeItems: [],
  knowledgeCollections: [],
  selectedKnowledgeId: null,
  knowledgeQuery: { query: "", types: [], minConfidence: null, missionId: null, workspaceId: null, limit: 25 },
  knowledgeContext: null,
  aiProviders: [],
  aiRoutePolicy: { mode: "auto", preferredProviderId: null, preferredModel: null, fallbackEnabled: true, fallbackOrder: ["ollama"], budgetTier: "free", offlineOnly: false },
  aiRequest: null,
  aiResponse: null,
  aiExecutionContext: null,
  aiRequestPending: false,
  aiAbortControllerId: null,
  commandCapabilities: [],
  commands: [],
  selectedCommandId: null,
  automations: [],
  selectedAutomationId: null,
  automationRuns: [],
  decisions: [],
  workspaces: [],
  memories: [],
  memoryRefs: [],
  memoryCollections: [],
  pinnedMemoryIds: [],
  selectedMemoryId: null,
  memorySearchQuery: "",
  timeline: [],
  navigation: {
    activeSurface: null,
    sidebarCollapsed: false,
  },
  assistant: initialAssistantContext,
  todayDate,
};

// ---------------------------------------------------------------------------
// Reducer
// ---------------------------------------------------------------------------

function kairosReducer(state: KairosState, action: KairosAction): KairosState {
  switch (action.type) {
    // ------ Missions ------
    case "SET_MISSIONS":
      return { ...state, missions: action.payload };

    case "SELECT_MISSION": {
      const mission = action.payload
        ? state.missions.find((m) => m.id === action.payload) ?? null
        : null;
      return {
        ...state,
        selectedMissionId: action.payload,
        missionTimeline: mission
          ? state.missionTimeline.filter((e) => e.missionId === mission.id)
          : [],
      };
    }

    case "SET_MISSION_FILTER":
      return { ...state, missionFilter: action.payload };

    case "ADD_MISSION":
      return { ...state, missions: [action.payload, ...state.missions] };

    case "ADD_MISSION_APPROVAL":
      return {
        ...state,
        missions: state.missions.map((m) =>
          m.id === action.payload.missionId
            ? { ...m, approvals: [...m.approvals, action.payload] }
            : m,
        ),
      };

    case "UPDATE_MISSION_APPROVAL":
      return {
        ...state,
        missions: state.missions.map((m) =>
          m.approvals.some((a) => a.id === action.payload.approvalId)
            ? {
                ...m,
                approvals: m.approvals.map((a) =>
                  a.id === action.payload.approvalId
                    ? {
                        ...a,
                        status: action.payload.status,
                        decisionReason: action.payload.reason ?? null,
                        decidedAt: new Date().toISOString(),
                      }
                    : a,
                ),
              }
            : m,
        ),
      };

    case "ADD_MISSION_ARTIFACT":
      return {
        ...state,
        missions: state.missions.map((m) =>
          m.id === action.payload.missionId
            ? { ...m, artifacts: [...m.artifacts, action.payload] }
            : m,
        ),
      };

    case "ADD_MISSION_TIMELINE_EVENT":
      return {
        ...state,
        missionTimeline: [action.payload, ...state.missionTimeline].slice(0, 200),
      };

    // ------ Memory Engine ------
    case "SET_MEMORIES":
      return { ...state, memories: action.payload };

    case "SET_MEMORY_REFS":
      return { ...state, memoryRefs: action.payload };

    case "SET_MEMORY_COLLECTIONS":
      return { ...state, memoryCollections: action.payload };

    case "SELECT_MEMORY":
      return { ...state, selectedMemoryId: action.payload };

    case "SET_MEMORY_SEARCH_QUERY":
      return { ...state, memorySearchQuery: action.payload };

    case "PIN_MEMORY":
      return {
        ...state,
        pinnedMemoryIds: [...state.pinnedMemoryIds, action.payload].filter((id, i, arr) => arr.indexOf(id) === i),
        memories: state.memories.map((m) =>
          m.id === action.payload ? { ...m, isPinned: true } : m,
        ),
      };

    case "UNPIN_MEMORY":
      return {
        ...state,
        pinnedMemoryIds: state.pinnedMemoryIds.filter((id) => id !== action.payload),
        memories: state.memories.map((m) =>
          m.id === action.payload ? { ...m, isPinned: false } : m,
        ),
      };

    // ------ Timeline Engine ------

    case "ADD_TIMELINE_EVENT":
      return {
        ...state,
        timelineEvents: [action.payload, ...state.timelineEvents].slice(0, 500),
      };

    case "SET_TIMELINE_EVENTS":
      return { ...state, timelineEvents: action.payload };

    case "SELECT_TIMELINE_EVENT":
      return { ...state, selectedTimelineEventId: action.payload };

    case "SET_TIMELINE_FILTER":
      return { ...state, timelineFilter: { ...state.timelineFilter, ...action.payload } };

    // ------ Knowledge Engine ------

    case "SET_KNOWLEDGE_ITEMS":
      return { ...state, knowledgeItems: action.payload };

    case "SET_KNOWLEDGE_COLLECTIONS":
      return { ...state, knowledgeCollections: action.payload };

    case "SELECT_KNOWLEDGE":
      return { ...state, selectedKnowledgeId: action.payload };

    case "SET_KNOWLEDGE_QUERY":
      return { ...state, knowledgeQuery: { ...state.knowledgeQuery, ...action.payload } };

    case "SET_KNOWLEDGE_CONTEXT":
      return { ...state, knowledgeContext: action.payload };

    // ------ AI Router ------

    case "SET_AI_PROVIDERS":
      return { ...state, aiProviders: action.payload };

    case "SET_AI_ROUTE_POLICY":
      return { ...state, aiRoutePolicy: { ...state.aiRoutePolicy, ...action.payload } };

    case "SET_AI_REQUEST":
      return { ...state, aiRequest: action.payload };

    case "SET_AI_RESPONSE":
      return { ...state, aiResponse: action.payload };

    case "SET_AI_EXECUTION_CONTEXT":
      return { ...state, aiExecutionContext: action.payload };

    case "SET_AI_REQUEST_PENDING":
      return { ...state, aiRequestPending: action.payload };

    case "SET_AI_ABORT_CONTROLLER_ID":
      return { ...state, aiAbortControllerId: action.payload };

    // ------ Command Engine ------

    case "SET_COMMAND_CAPABILITIES":
      return { ...state, commandCapabilities: action.payload };

    case "SET_COMMANDS":
      return { ...state, commands: action.payload };

    case "ADD_COMMAND":
      return { ...state, commands: [action.payload, ...state.commands] };

    case "SELECT_COMMAND":
      return { ...state, selectedCommandId: action.payload };

    // ------ Automation Engine ------

    case "SET_AUTOMATIONS":
      return { ...state, automations: action.payload };

    case "SELECT_AUTOMATION":
      return { ...state, selectedAutomationId: action.payload };

    case "ADD_AUTOMATION_RUN":
      return { ...state, automationRuns: [action.payload, ...state.automationRuns].slice(0, 200) };

    case "SET_AUTOMATION_RUNS":
      return { ...state, automationRuns: action.payload };

    case "SET_DECISIONS":
      return { ...state, decisions: action.payload };

    case "SET_WORKSPACES":
      return { ...state, workspaces: action.payload };

    // ------ Existing actions ------

    case "ADD_TIMELINE_ITEM":
      return { ...state, timeline: [action.payload, ...state.timeline] };

    case "SET_ACTIVE_SURFACE":
      return {
        ...state,
        navigation: { ...state.navigation, activeSurface: action.payload },
      };

    case "TOGGLE_SIDEBAR":
      return {
        ...state,
        navigation: { ...state.navigation, sidebarCollapsed: !state.navigation.sidebarCollapsed },
      };

    case "SET_ASSISTANT_CONTEXT":
      return { ...state, assistant: { ...state.assistant, ...action.payload } };

    case "RESET_ASSISTANT_CONTEXT":
      return { ...state, assistant: initialAssistantContext };

    default:
      return state;
  }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const KairosStateContext = createContext<KairosState>(initialState);
const KairosDispatchContext = createContext<Dispatch<KairosAction>>(() => {});

export function KairosStateProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(kairosReducer, initialState);

  return (
    <KairosStateContext.Provider value={state}>
      <KairosDispatchContext.Provider value={dispatch}>
        {children}
      </KairosDispatchContext.Provider>
    </KairosStateContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useKairosState(): KairosState {
  return useContext(KairosStateContext);
}

export function useKairosDispatch(): Dispatch<KairosAction> {
  return useContext(KairosDispatchContext);
}
