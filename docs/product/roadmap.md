# Product Roadmap

## Current Phase: v3.4 (Foundation & Architecture)
**Status:** In Progress

The goal of this phase is to solidify the foundational Domain Models and establish the architecture required to support a scalable, cloud-first Decision Operating System.

- ✅ Finalize Domain Driven Design models (Mission, Decision, Memory).
- ✅ Define the Provider Platform architecture (OpenAI, Gemini, Ollama).
- ⬜ Implement Provider Router middleware.
- ⬜ Implement OAuth session management for cloud providers.

## Next Phase: v3.5 (The Approval Bridge)
**Status:** Planned

This phase shifts focus to safety and the `Operator` UX, ensuring that autonomous planning can be safely halted and reviewed.

- ⬜ Implement the Approval Bridge logic in the `PlannerEngine`.
- ⬜ Build the Workspace UI for reviewing `DecisionPlans`.
- ⬜ Support manual `DecisionPlan` overrides by the Operator.
- ⬜ Implement strictly bounded Execution Workflows.

## Future Phase: v4.0 (Experiential Memory)
**Status:** Planned

This phase will close the loop on autonomous operation by allowing the system to learn from its execution history.

- ⬜ Implement the Reflection post-mortem engine.
- ⬜ Deploy a local Vector Database (e.g., Chroma) for Memory storage.
- ⬜ Inject Memory context into the Provider Router prompt pipeline.
- ⬜ Implement Memory decay and lifecycle management.
