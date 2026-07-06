# Kairos Architecture

> Architecture overview for Kairos — Your AI Operating System.
> Last updated: Sprint 11 (Production Hardening)

---

## 1. System Layers

Kairos is structured in concentric layers. Each layer depends only on layers
below it. No circular dependencies.

```
┌─────────────────────────────────────────┐
│              Shell Surfaces              │
│  GoodMorning / ContinueWorking / AskKai  │
│       Today'sBrief / Workspace           │
├─────────────────────────────────────────┤
│             Runtime Hooks                │
│    useApi / useMissions / useConversation│
├─────────────────────────────────────────┤
│            Application State             │
│     Context + useReducer (state.tsx)     │
├─────────────────────────────────────────┤
│           Domain Models (types.ts)        │
│   Mission, Memory, Timeline, Knowledge,  │
│   AI Router, Command, Plugin, Connector  │
├─────────────────────────────────────────┤
│            Transport (api.ts)            │
│    fetchFromApi / postToApi / endpoints  │
├─────────────────────────────────────────┤
│          Kairos Core API (FastAPI)       │
│   apps/api/ — backend services           │
└─────────────────────────────────────────┘
```

---

## 2. The Seven Engines

### Mission Engine
**File:** `lib/types.ts` (Mission, MissionPlan, MissionStep, MissionApproval, etc.)
**State:** `missions`, `selectedMissionId`, `missionFilter`, `missionTimeline`
**Runtime:** `useMissions()`, `useMissionEngine()`, `usePlanningRuntime()`, `useExecutionRuntime()`

Missions are the primary unit of work. Full lifecycle from `draft` through
`executing` to `completed`/`failed`/`cancelled` and finally `archived`.
Every mission has a plan (versioned steps), approvals, execution records,
and artifacts.

### Memory Engine
**File:** `lib/types.ts` (Memory, MemoryReference, MemoryCollection, etc.)
**State:** `memories`, `memoryRefs`, `pinnedMemoryIds`, `memorySearchQuery`
**Runtime:** `useMemories()`, `useMemoryEngine()`, `useMemoryForMission()`, `useMemoryForWorkspace()`

Memories are durable units of knowledge. They have types (note, decision,
reflection, insight, reference, procedure, fact), visibility scopes,
and structured relationships to other entities.

### Timeline Engine
**File:** `lib/types.ts` (TimelineEvent, TimelineFilter, TimelineActor, etc.)
**State:** `timelineEvents`, `timelineFilter`, `selectedTimelineEventId`
**Runtime:** `useTimelineEngine()`, `useRecentTimeline()`, `useTodayTimeline()`, per-entity hooks

The Timeline is the chronological system-of-record. 40+ event types covering
missions, memory, decisions, workspaces, approvals, executions, system health,
plugins, connectors, and automations.

### Knowledge Engine
**File:** `lib/types.ts` (KnowledgeItem, KnowledgeQuery, KnowledgeContext, etc.)
**State:** `knowledgeItems`, `knowledgeCollections`, `knowledgeQuery`, `knowledgeContext`
**Runtime:** `useKnowledgeEngine()`, `useKnowledgeForMission()`, `useKnowledgeForWorkspace()`, `useKnowledgeForMemory()`

Knowledge sits above Memory and below the AI Router. It structures raw memories
into queryable, contextual knowledge that AI providers consume.
`assembleContext()` builds a KnowledgeContext from filtered items.

### AI Router
**File:** `lib/types.ts` (AIProvider, AIRequest, AIResponse, AIRoutePolicy, etc.)
**State:** `aiProviders`, `aiRoutePolicy`, `aiRequest`, `aiResponse`, `aiExecutionContext`
**Runtime:** `useAIRouter()`, `useAIProviderHealth()`, `useAIModelSelection()`

Centralized provider routing. Budget tiers (`free`/`cheap`/`quality`),
fallback order, offline mode. Provider health aggregation.
`assembleExecutionContext()` builds the full pre-request context.

### Command & Automation Engine
**File:** `lib/types.ts` (Command, Automation, AutomationPolicy, etc.)
**State:** `commands`, `commandCapabilities`, `automations`, `automationRuns`
**Runtime:** `useCommandEngine()`, `useCommandApproval()`, `useAutomationEngine()`, `useAutomationRuns()`

Every action is a governed Command. The pipeline:
`Command → Approval → Execution → Timeline → Memory/Knowledge`.
Automations define triggers, conditions, actions, and safety policies.

### Plugin & Connector Foundation
**File:** `lib/types.ts` (Plugin, Connector, RegisteredCapability, etc.)
**State:** `plugins`, `connectors`, `registeredCapabilities`, `capabilityPolicy`
**Runtime:** `usePluginRegistry()`, `useConnectorRegistry()`, `useCapabilityRegistry()`

Extensions register capabilities into the Command Engine.
`Plugin/Connector → Capability Registry → Command → Approval → Execution`.

---

## 3. Data Flow

### Read Path
```
Surface → useApi() → fetchFromApi() → Kairos Core API → SQLite
                                              ↓
                              dispatch(action) → state update → re-render
```

### Write Path
```
Surface → action handler → postToApi() → Kairos Core API → SQLite
                               ↓
                    dispatch(action) → state update → re-render
```

### AI Request Path
```
User → Mission → Knowledge Context → AI Router → Provider
                                                    ↓
                        AI Response → Timeline → Memory/Knowledge
```

---

## 4. Governance Flow

Every action that modifies state or calls external systems must pass through:

```
Capability Registry (what can be done)
        ↓
Command Creation (what will be done)
        ↓
Risk Assessment (is it safe?)
        ↓
Approval Gate (who approves?)
        ↓
Execution (do it)
        ↓
Audit (record in Timeline)
```

Nothing executes outside this pipeline.

---

## 5. File Organization

```
apps/dashboard/
├── app/                          # Next.js app router pages
│   ├── layout.tsx                # Root layout (KairosProvider + ShellLayout)
│   ├── page.tsx                  # Home / legacy dashboard
│   ├── good-morning/             # Morning briefing
│   ├── continue-working/         # Resume surface
│   ├── ask-kai/                  # Chat interface
│   ├── todays-brief/             # Daily digest
│   ├── workspace/                # Planning & execution
│   ├── decisions/                # Legacy decisions
│   ├── missions/                 # Legacy missions
│   └── settings/                 # Legacy settings
├── components/
│   ├── shell/                    # Shell components (layout, sidebar, nav)
│   ├── ApprovalsCard.tsx         # Legacy approval management
│   ├── AIWorkspace.tsx           # Legacy AI workspace
│   └── ...                       # Other legacy components
├── lib/
│   ├── types.ts                  # Domain model (1155 lines, 80+ types)
│   ├── state.tsx                 # Application state (548 lines, 60+ actions)
│   ├── runtime.ts                # Runtime hooks (1313 lines, 40+ hooks)
│   └── api.ts                    # API transport layer (885 lines)
└── tests/
    └── workspace-decision-planner.test.mjs
```

---

## 6. Key Design Decisions

1. **No external state library.** React Context + useReducer is sufficient
   for the current scale. If performance becomes an issue, the state can be
   split into domain-specific contexts without changing the API.

2. **Type-only domain model.** All types are in `types.ts` with `type` imports.
   Zero runtime dependency between domain modules and UI.

3. **API transport decoupled.** `api.ts` defines wire format types.
   `runtime.ts` maps wire types to domain types before dispatching into state.
   No component imports API types directly.

4. **Runtime is large by design.** All 40+ hooks live in `runtime.ts` to keep
   imports simple (one import = all hooks). When the file becomes unwieldy,
   split into `runtime/mission.ts`, `runtime/memory.ts`, etc. — not yet needed.

5. **ShellLayout is permanent.** Every route renders inside it. The Sidebar
   has two groups: Kairos Shell surfaces (top) and legacy routes (bottom).

---

## 7. Future Architecture Considerations

- **Runtime split:** When `runtime.ts` exceeds ~2000 lines, split into domain files.
- **State split:** If re-render performance degrades, create `MissionContext`,
  `MemoryContext`, etc. instead of one monolithic context.
- **Streaming:** AI Router is ready for `ReadableStream` integration.
- **Knowledge Indexing:** Knowledge Engine is ready for vector/embedding
  integration without changing consumers.
- **Plugin Sandbox:** PluginExecutionBoundary defines the isolation contract.
  Implementation requires a runtime sandbox (Web Worker or server-side).
