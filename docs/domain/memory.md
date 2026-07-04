# Memory Domain

The `Memory` domain acts as the long-term context engine for Kairos DOS. It persists valuable operational heuristics and lessons so the AI does not repeat mistakes.

## 1. Purpose
While `Knowledge` represents static, pre-existing documentation, `Memory` is dynamic, experiential context generated directly from the AI's lived experiences (via `Reflection`). It acts as contextual reinforcement learning.

## 2. Ownership
- **Parent**: `Memory` operates at the global/system level, unbound by a specific `Mission`, though individual fragments maintain lineage traces to the `Mission` that spawned them.
- **Children**: None.

## 3. Responsibilities
- Storing extracted heuristics, facts, and preferences.
- Surfacing relevant contextual fragments to the AI Provider Router during future `DecisionPlan` drafts.

## 4. Lifecycle
- **Proposed**: A new fragment is proposed by a `Reflection`.
- **Approved**: The `Operator` has explicitly authorized the memory to be committed to the long-term store.
- **Active**: The memory is queryable and actively injected into relevant contexts.
- **Deprecated**: The memory has been proven obsolete or false by subsequent events and is removed from active context retrieval.

## 5. Invariants
- A `Memory` MUST ONLY be created from an approved `Reflection`. It is NEVER created directly from raw AI output or unverified chat logs.
- The transition from `Proposed` to `Active` MUST require explicit `Operator` permission.
- A `Memory` fragment MUST maintain a lineage pointer back to its originating `Decision`.

## 6. Relationships
- **Reflection**: The sole generator of new `Memory` fragments.
- **Operator**: The gatekeeper who approves `Memory` persistence.
- **Knowledge**: `Memory` supplements static `Knowledge`, acting as an experiential override when system realities deviate from documentation.

## 7. Success Criteria
- Accurately surfacing relevant `Memory` fragments during a future, similar `Mission`, preventing the AI from repeating a past error.

## 8. Examples
- **Memory Fragment**: "The production database host `db.internal.corp` requires connecting over port `5433`, not the default `5432`." 
- **Context Injection**: On a future mission to "Dump the DB", the AI router includes this Memory in the prompt, resulting in a flawless first-try `DecisionPlan`.

## 9. Future Extensibility
- **Memory Decay**: Automatically deprecating or down-ranking older `Memory` fragments if they haven't been referenced in a long time.
- **Vector Search**: Backing the `Memory` store with a vector database (e.g., Chroma, Qdrant) for semantic contextual retrieval.

## 10. Out of Scope
- Storing static manuals or API documentation (this belongs to `Knowledge`).
- Retaining full chat logs or conversation history.
