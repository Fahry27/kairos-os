/**
 * Kairos Core — Application State.
 *
 * Lightweight state management via React Context + useReducer.
 * No external state library. Every surface reads from this single source.
 *
 * State slices:
 *   missions         — active missions (full Mission Engine domain model)
 *   decisions        — open decisions
 *   workspaces       — workspace sessions
 *   memories         — memory references
 *   missionTimeline  — per-mission timeline events
 *   navigation       — sidebar + active surface
 *   assistant        — Ask Kai conversation context
 *   selectedMissionId — currently focused mission
 *   todayDate        — today's date context
 *   missionFilter   — active filter for the mission list
 */

import React, { createContext, useContext, useReducer, type Dispatch, type ReactNode } from "react";

import type {
  Mission,
  MissionStatus,
  MissionApproval,
  MissionArtifact,
  MissionTimelineEvent,
  Decision,
  Workspace,
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
  /** Currently selected mission ID for detail view. */
  selectedMissionId: string | null;
  /** Active filter for the mission list. */
  missionFilter: MissionFilter;
  /** Timeline events for the selected mission. */
  missionTimeline: MissionTimelineEvent[];
  decisions: Decision[];
  workspaces: Workspace[];
  memories: MemoryReference[];
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
  | { type: "SET_MEMORIES"; payload: MemoryReference[] }
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
  decisions: [],
  workspaces: [],
  memories: [],
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

    // ------ Existing actions ------
    case "SET_DECISIONS":
      return { ...state, decisions: action.payload };

    case "SET_WORKSPACES":
      return { ...state, workspaces: action.payload };

    case "SET_MEMORIES":
      return { ...state, memories: action.payload };

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
