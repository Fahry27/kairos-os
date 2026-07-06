# Kairos Constitution

> Your AI Operating System — permanent project constitution.
> This document is the source of truth for all future development sessions.

---

## 1. Product Vision

Kairos is a personal AI Operating System. It is not a chatbot, a dashboard,
or a CRUD application. It is an orchestration layer over multiple AI engines,
an extensible platform for personal operations, and production-quality
software intended to evolve for years.

**Kairos IS:**
- Your primary AI Operating System
- A mission-driven execution environment
- An orchestration layer over AI providers
- An extensible platform for personal operations
- Production-quality software with a 3–5 year horizon

**Kairos is NOT:**
- A chatbot or conversational wrapper
- A dashboard for viewing data
- A CRUD application
- A demo or prototype
- An AI-generated project

---

## 2. Architecture Principles

1. **Architecture first.** Design the structure before writing code.
2. **Mission first, AI second.** Everything revolves around Missions.
   Users never interact directly with providers. The flow is:
   `User → Mission → Planning → Approval → Execution → Timeline → Memory → Provider → Result`
3. **No fake backend.** Every architectural boundary must support a real backend.
   No mock data, no simulated responses, no placeholder APIs.
4. **No fake AI.** AI integration points must be wired to real providers.
   No mock responses inline.
5. **No technical debt.** Every change must be production-quality.
6. **Prefer composition over inheritance.** Prefer concrete implementations
   over generic frameworks. Prefer deleting dead code over preserving it.
7. **Keep changes reviewable.** Small, explicit, easy-to-review commits.
8. **Avoid speculative engineering.** Don't build for hypothetical use cases.
9. **Keep modules cohesive.** Keep files small. Avoid large refactors
   unless required for correctness.

---

## 3. Agent Behavior Rules

All AI agents working on Kairos must follow these rules:

1. **Do not restart repository exploration** if prior session knowledge is valid.
2. **Do not run the full test suite** unless explicitly necessary. Prefer targeted module-level tests.
3. **Do not propose ten alternatives.** Recommend the best option and execute.
4. **Do not stop between milestones** unless a stop condition is met.
5. **Do not commit automatically.** Prepare commits, wait for approval.
6. **Commit messages must follow Conventional Commits.**
7. **Append `Co-authored-by: CommandCodeBot <noreply@commandcode.ai>`** to every commit.
8. **Keep API budget efficient.** Avoid repeated exploration, rereading unchanged files,
   generating long explanations, or asking unnecessary questions.
9. **When docs become stale**, mark them as superseded with a clear notice
   rather than deleting them.
10. **Gate risky functionality** behind explicit configuration flags
    rather than removing it outright.

---

## 4. Sprint Roadmap

| Sprint | Name | Status |
|---|---|---|
| Sprint 0 | Infrastructure | ✅ Complete |
| Sprint 1 | Kairos Shell | ✅ Complete |
| Sprint 2 | Kairos Core (State) | ✅ Complete |
| Sprint 3 | Kairos Runtime | ✅ Complete |
| Sprint 4 | Mission Engine | ✅ Complete |
| Sprint 5 | Memory Engine | ✅ Complete |
| Sprint 6 | Timeline Engine | ✅ Complete |
| Sprint 7 | Knowledge Engine | ✅ Complete |
| Sprint 8 | AI Router | ✅ Complete |
| Sprint 9 | Command & Automation | ✅ Complete |
| Sprint 10 | Plugin & Connector Foundation | ✅ Complete |
| Sprint 11 | Production Hardening | 🔄 Current |
| Sprint 12 | Kairos v1 | ⏳ Future |

**Post-v1:**
- AI Provider Wire-Up (real dispatch)
- Streaming responses
- Mission execution runtime
- Memory extraction pipeline
- Knowledge indexing
- Timeline event automation

---

## 5. Stop Conditions

Only stop work for:
- Architecture conflict
- Failing tests
- Merge conflict
- Missing dependency
- Security concern (secrets in code)
- Destructive change (database migration, file deletion, force push)
- Human approval required

Otherwise continue automatically through all milestones.

---

## 6. Engineering Constitution

### Code Quality
- Every change must have a clear reason, be reviewable, be testable,
  and have minimal blast radius.
- Avoid touching unrelated code, unnecessary formatting changes, or
  unrelated refactors.

### Testing
- Prefer targeted tests: module tests, focused verification.
- Run full tests only before merge or major milestones.
- Do not run unrelated backend tests unless those files were touched.

### Git
- Commit messages follow Conventional Commits.
- Never commit automatically. Prepare commits, wait for approval.
- Append co-author trailer to every commit.

### Documentation
- When docs become stale, mark as superseded — don't delete.
- Keep changes minimal. Point to authoritative sources.

---

## 7. AI Provider Philosophy

AI providers (OpenAI, Gemini, Ollama, DeepSeek, 9Router) are **executors**,
not the center of the product. Providers are abstracted behind the AI Router
and never exposed directly to users.

The pipeline is:
`User → Mission → Memory → Timeline → Knowledge → AI Router → Provider → Result → Timeline → Memory/Knowledge`

Providers must never:
- Receive raw user data without Mission context
- Execute commands without Approval
- Store credentials in the frontend
- Be called directly from UI components

---

## 8. Engine Philosophy

### Mission Engine
Missions are the primary unit of work. Every action in Kairos belongs to a Mission.
Mission lifecycle: Draft → Planning → AwaitingApproval → Approved → Executing → Completed/Failed/Cancelled → Archived.

### Memory Engine
Memory is durable knowledge, not chat history. Memories persist across sessions
and are available to every future Mission and AI provider. Visibility: private, mission, workspace, global.

### Timeline Engine
The Timeline is the chronological system-of-record. Every event — mission transitions,
memory creation, decision changes, approvals, executions — is recorded.

### Knowledge Engine
Knowledge sits above Memory and below the AI Router. It structures raw memories into
queryable, contextual knowledge that AI providers can consume. No embeddings yet.

### AI Router
Centralized routing decisions. Provider selection, fallback policy, budget tiers
(free/cheap/quality), offline mode. No provider-specific logic in pages.

### Command Engine
Every action is a governed Command. Pipeline: Command → Approval → Execution → Timeline.
Risk assessment, approval gating, audit trail.

### Plugin & Connector Foundation
Extensions register capabilities into the Command Engine. Nothing bypasses governance.
Plugin → Capability Registry → Command → Approval → Execution.

---

## 9. Repository Structure

```
apps/api/         — FastAPI backend (Kairos Core API)
apps/dashboard/   — Next.js frontend (Kairos Shell)
data/             — Seed data, fixtures, exports, runtime data
docs/             — Product, architecture, development docs
infra/            — Docker Compose, Caddy, Postgres, Qdrant, Redis configs
scripts/          — Development, maintenance, deployment helpers
```

---

## 10. Long-Term Expectations

Kairos is a 3–5 year project. Every engineering decision must optimize for
long-term maintainability. Avoid shortcuts that create future work.

- **No framework lock-in.** Prefer standard React patterns.
- **No vendor lock-in.** Providers are swappable.
- **Local-first.** Works offline with Ollama. Cloud providers are optional.
- **Production from day one.** No "fix later" mentality.
