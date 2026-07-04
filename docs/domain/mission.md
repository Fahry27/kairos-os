# Mission Domain

The `Mission` is the aggregate root of the Kairos Decision Operating System (DOS). It represents the highest level of user intent and orchestrates the autonomous lifecycle of planning, execution, and reflection.

## 1. Why Mission Exists

In a standard script-execution environment, user commands are atomic and immediate. However, in an autonomous AI operating system, complex goals span across time, require external context, demand user approval for dangerous actions, and trigger long-running background tasks. 

The `Mission` exists to encapsulate this entire asynchronous narrative. It bounds the context of a long-term goal, ensuring that all subsequent planning, execution, and memory storage are contextually anchored to the original user intent.

## 2. Mission Lifecycle

A Mission progresses through a strictly controlled state machine:

- **Draft**: The initial state. The Mission is formulated, context is gathered, and the initial `DecisionPlan` is being drafted by the AI Provider Router. No execution can occur.
- **Active**: The Mission is currently being progressed. The AI is actively making decisions, workflows are running, or approvals are being processed.
- **Blocked**: The Mission cannot proceed without external intervention. This typically occurs when a `DecisionPlan` reaches the Approval Bridge and awaits user authorization.
- **Completed**: The Mission's definition of success has been satisfied. All workflows have terminated, and a final state has been achieved.
- **Archived**: A terminal state for historical record-keeping. The Mission is removed from the active view but retained for `Reflection` and `Memory` context.

## 3. Mission Ownership

- A Mission is owned by a single `WorkspaceSession`. 
- Only the authenticated user (or an authorized AI proxy acting on their behalf) can mutate the state of a Mission.
- A Mission exclusively owns its bounded context. Decisions made within one Mission do not implicitly bleed into another unless explicitly persisted to global `Memory`.

## 4. Mission Invariants

- A Mission MUST have a clearly defined `goal`.
- A Mission CANNOT transition from `Draft` to `Active` without a validated `DecisionPlan`.
- A Mission MUST halt (transition to `Blocked`) if any child `Decision` encounters an unhandled exception or requires user authorization.
- A Mission CANNOT be deleted if it has triggered external side-effects (e.g., executing a command or connector); it must be `Archived` instead for auditability.

## 5. Distinction Between Mission, Decision, and DecisionPlan

To ensure clean domain boundaries, the hierarchy is strictly defined as follows:

- **Mission**: The aggregate root. It represents the overarching user goal (e.g., "Deploy the web app"). A Mission owns one or more `Decisions`.
- **Decision**: An atomic branch point within a Mission. It represents a specific problem that needs solving to progress the Mission (e.g., "How should we provision the database?"). A Decision owns one or more `DecisionPlans` (drafts).
- **DecisionPlan**: The proposed blueprint or strategy to resolve a `Decision`. The AI may generate multiple competing `DecisionPlans` for a single `Decision`. Only one `DecisionPlan` can be selected and approved for execution.

## 6. Relationships with Other Domains

As the aggregate root, the Mission coordinates several other sub-domains:

- **Approval**: The explicit user-in-the-loop authorization required for a `DecisionPlan` to execute dangerous capabilities. A Mission blocks until the Approval is resolved.
- **Workflow**: The physical execution engine. Once a plan is approved, it is translated into a `Workflow` (e.g., n8n) that performs the network and system mutations.
- **Reflection**: A post-mortem analysis performed when the Mission reaches `Completed` or `Archived`. The AI evaluates what went well and what failed.
- **Memory**: Persistent context extracted from a Mission's Reflection. This feeds back into the global context store to improve future Missions.

## 7. Mission Success Criteria

A Mission is only considered `Completed` when its explicit success criteria are met. 
- **Definition**: Success criteria are defined during the `Draft` phase based on the user's initial goal.
- **Verification**: The AI must perform a verification step (e.g., querying an API, reading a log file) to objectively prove the success criteria have been satisfied before closing the Mission.
- **Failure**: If the criteria cannot be met after all `Decisions` have been executed, the Mission halts and prompts the user for intervention, preventing a false `Completed` state.

## 8. Mission Metrics

To evaluate system efficiency and AI performance, each Mission tracks core metrics:
- **Time to Completion (TTC)**: The total duration from `Draft` to `Completed`.
- **Approval Latency**: The amount of time the Mission spent in the `Blocked` state waiting for user input.
- **Decision Count**: The total number of `Decisions` required to complete the Mission.
- **Execution Cost**: The estimated token cost or computational cost expended by the AI Provider Router throughout the Mission's lifecycle.

## 9. Example Mission

**Goal:** "Audit the system logs for security anomalies and alert the admin if any are found."

1. **Draft:** The Mission is created with success criteria: "Admin receives alert OR logs prove clean."
2. **Decision 1 (Log Retrieval):** The Mission creates a Decision for how to get the logs. The AI drafts a `DecisionPlan` to run `journalctl`.
3. **Decision 2 (Alerting):** The Mission creates a Decision for alerting. The AI drafts a `DecisionPlan` to send an email via a Connector.
4. **Blocked:** The alerting plan requires data mutation. The Mission halts and awaits Approval.
5. **Active:** The user approves the `DecisionPlan`. The Mission triggers the `Workflow` to run the script and send the email.
6. **Completed:** The email is verified sent. Success criteria are met.
7. **Archived:** The Mission is archived. A `Reflection` creates a `Memory`.

## 10. Future Extensibility

- **Sub-Missions**: Breaking massive, multi-day goals into hierarchical sub-missions.
- **Collaborative Missions**: Allowing multiple users or AI agents to work concurrently on the same aggregate root.
- **Scheduled Missions**: CRON-based instantiation of Missions for recurring operational duties.

## 11. Out of Scope

- **Direct Execution**: A Mission itself does not execute code or make API calls; it delegates to the `Workflow` domain.
- **Authentication/Identity**: Mission assumes the user is already authenticated by the outer application layer.
- **Model Routing**: Choosing between OpenAI or Ollama is the responsibility of the `AIProviderRouter`, not the Mission.
