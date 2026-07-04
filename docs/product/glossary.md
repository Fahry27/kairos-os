# Glossary

Standardized terminology for Kairos DOS.

- **AI Provider Router**: The internal middleware that translates internal planning requests to specific AI vendor APIs (OpenAI, Gemini, Ollama).
- **Approval Bridge**: A safety mechanism that halts a Mission and requires manual Operator authorization before a dangerous capability is executed.
- **Decision**: An atomic problem or branch point owned by a Mission.
- **DecisionPlan**: A specific, proposed blueprint for resolving a Decision.
- **Knowledge**: Static, authoritative reference documentation (e.g., API specs, runbooks).
- **Memory**: Dynamic, experiential heuristics extracted by the system from past executions.
- **Mission**: The aggregate root of the system representing the overarching user intent/goal.
- **Operator**: The human user (or authorized external agent) who owns Missions and provides ultimate authorization.
- **Outcome**: The immutable, factual record of what happened when a DecisionPlan was executed.
- **Reflection**: The analytical phase that compares a DecisionPlan against its Outcome to extract Memories.
- **Workflow**: The physical execution engine that runs the approved capability.
- **Workspace**: The operational console and UI layer used by the Operator.
