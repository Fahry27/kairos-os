# Kairos Roadmap

## Completed Sprints

| Sprint | Name | Key Deliverables |
|---|---|---|
| Sprint 0 | Infrastructure | Docker, Ollama GPU, Portainer, Cockpit, Dozzle, n8n, GitHub, domain |
| Phase B | Foundation Cleanup | Removed dead auth scaffold, marked stale ADRs as superseded |
| Sprint 1 | Kairos Shell | ShellLayout, Sidebar, NavItem, SkipLink, ErrorBoundary, LoadingShell, 5 placeholder surfaces |
| Sprint 2 | Kairos Core | Shared domain model (types.ts), React Context + useReducer state, KairosProvider |
| Sprint 3 | Kairos Runtime | useApi<T> hook (loading/error/refresh/abort), domain runtime hooks, useConversation, workspace/mission/brief runtimes |
| Sprint 4 | Mission Engine | 9-state mission lifecycle, MissionPlan, MissionStep, MissionApproval, MissionStepExecution, MissionArtifact, MissionOutcome, MissionTimelineEvent |
| Sprint 5 | Memory Engine | Memory domain (type, visibility, status, source, relationships, tags, collections), pinning, search, KnowledgeEngine interface |
| Sprint 6 | Timeline Engine | Unified TimelineEvent (24 event types), TimelineActor, TimelineFilter, per-entity timeline hooks, deprecated MissionTimelineEvent |
| Sprint 7 | Knowledge Engine | KnowledgeItem, KnowledgeQuery, KnowledgeContext, relationships derived_from/supports/contradicts, confidence levels, `assembleContext` |
| Sprint 8 | AI Router | AIProvider, AIRoutePolicy (budget tiers), AIRequest, AIResponse, AIExecutionContext, provider health, model selection, 5 frontend hooks |
| Sprint 9 | Command & Automation | Command lifecycle (9 states), CommandCapability, risk/approval gating, Automation with triggers/conditions/actions/policy/runs |
| Sprint 10 | Plugin & Connector | Plugin lifecycle (install state, risk level, execution boundary), Connector (auth types, sync states, health), CapabilityRegistry |

---

## Current Sprint

| Sprint | Name | Key Deliverables |
|---|---|---|
| **Sprint 11** | **Production Hardening** | `KAIROS_CONSTITUTION.md`, `ROADMAP.md`, `ARCHITECTURE.md`, AGENTS.md update, runtime hygiene, surface hardening |

---

## Upcoming Sprints

### Sprint 12 — Kairos v1

**Goal:** Merge `genesis-migration` into `main`. The first stable version of Kairos.

Completion criteria:
- ✅ All 10 feature sprints complete
- ✅ TypeScript clean
- ✅ All frontend tests pass
- ✅ Architecture documentation complete
- ✅ Working tree clean
- No known dead code in `lib/`
- `genesis-migration` passes review

### Sprint 13 — AI Provider Wire-Up

**Goal:** Connect Ask Kai to a real AI provider.

Deliverables:
- Wire `dispatchOllama()` / `dispatchAIProvider()` into `useConversation.sendMessage`
- Add AI response messages to conversation model
- Populate timeline events from actual AI interactions
- Handle streaming responses (ReadableStream)

### Sprint 14 — Provider Streaming

**Goal:** Real-time AI response streaming in Ask Kai.

Deliverables:
- `ReadableStream` reader integration
- Progress indicators during streaming
- Abort controller for mid-stream cancellation
- Streaming state tracking in Timeline

### Sprint 15 — Mission Execution

**Goal:** Execute mission steps through the Command Engine.

Deliverables:
- Wire mission plan steps to Command creation
- Step-by-step execution with approval gates
- Execution tracking in Timeline
- Artifact generation from step outputs

---

## Post-v1 Roadmap

| Area | Description |
|---|---|
| Memory Extraction | Auto-extract knowledge from mission outcomes, decisions, and conversations |
| Knowledge Indexing | Build search index over knowledge items (without embeddings first) |
| Timeline Automation | Auto-record events from mission transitions, command execution |
| Operator Console | Approval dashboard with batch operations and risk overview |
| Provider Parity | OpenAI, Gemini, DeepSeek, 9Router provider adapters |
| Plugin Marketplace | Plugin installation, capability registration, sandboxed execution |
| Calendar Integration | External calendar sync for Good Morning and scheduling |
| Mobile Shell | Responsive/progressive web app for mobile access |
