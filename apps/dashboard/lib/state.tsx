/**
 * Kairos Core — Application State.
 *
 * Lightweight state management via React Context + useReducer.
 * No external state library. Every surface reads from this single source.
 *
 * State slices:
 *   missions        — active missions
 *   decisions       — open decisions
 *   workspaces      — workspace sessions
 *   memories        — memory references
 *   timeline        — timeline items
 *   navigation      — sidebar + active surface
 *   assistant       — Ask Kai conversation context
 *   today           — today's date context
 */

import React, { createContext, useContext, useReducer, type Dispatch, type ReactNode } from "react";

import type {
  Mission,
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

export interface KairosState {
  missions: Mission[];
  decisions: Decision[];
  workspaces: Workspace[];
  memories: MemoryReference[];
  timeline: TimelineItem[];
  navigation: NavigationState;
  assistant: AssistantContext;
  todayDate: string; // ISO date string (YYYY-MM-DD)
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------

export type KairosAction =
  | { type: "SET_MISSIONS"; payload: Mission[] }
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
    case "SET_MISSIONS":
      return { ...state, missions: action.payload };

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
