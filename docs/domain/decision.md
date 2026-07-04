# Decision Domain

The `Decision` domain is a core building block of the Kairos Decision Operating System (DOS). It represents a specific, atomic branch point or problem that must be resolved to progress the overarching `Mission`.

## 1. Purpose

The `Decision` represents **WHAT** must be decided. 

While a `Mission` spans an entire asynchronous narrative (e.g., "Deploy the web app"), it is inherently composed of numerous smaller steps. A `Decision` encapsulates one of these discrete problems (e.g., "Which database technology should be provisioned?"). It acts as the container for exploring options, evaluating trade-offs, and ultimately selecting a path forward.

## 2. Ownership

- **Parent**: A `Decision` is strictly owned by a single `Mission`. It cannot exist independently.
- **Children**: A `Decision` owns one or more `DecisionPlans`. 
- **Outcome**: A `Decision` exclusively owns its ultimate **Outcome**. The `Mission` tracks the overarching success, but the specific success/failure result (and artifact generation) of a localized step belongs to the `Decision`.

## 3. Decision Type

Decisions are categorized by type to dictate how they are processed:
- **Navigational**: Determining the next logical step (e.g., "Do we need to install dependencies first?").
- **Capability**: Selecting the best tool for a job (e.g., "Should we use `curl` or a Python script?").
- **Authorization**: Halting execution to explicitly request human approval for a high-risk action.
- **Diagnostic**: Evaluating system state to troubleshoot an error encountered in a previous decision.

## 4. Decision Priority

To allow the planner to order execution, Decisions possess a priority score:
- **Critical**: Must be resolved immediately; the `Mission` is completely blocked.
- **High**: Important sequential step in the primary path.
- **Medium**: Background context gathering or non-blocking preparation.
- **Low**: Optional optimizations or nice-to-have supplementary tasks.

## 5. Lifecycle

A `Decision` progresses through the following state machine:

- **Identified**: The need for a decision has been recognized by the AI during `Mission` planning, but no concrete proposals exist yet.
- **Drafting**: The `Decision` is actively generating candidate `DecisionPlans` via the AI Provider Router.
- **Pending**: Candidate `DecisionPlans` have been generated and are awaiting selection. If a plan hits the Approval Bridge, the `Decision` halts here.
- **Resolved**: A single `DecisionPlan` has been explicitly selected (either automatically by the AI's high confidence, or manually via User Approval) and executed. The Outcome is recorded.
- **Failed**: No valid `DecisionPlan` could be formulated, or the selected plan failed during execution, rendering the `Decision` unsolvable without intervention.

## 6. Decision Context

A `Decision` does not exist in a vacuum. It maintains a scoped `Context` boundary that includes:
- **Upstream Outcomes**: The results and generated data from preceding `Decisions`.
- **Environmental State**: A snapshot of system health, active variables, and available capabilities at the exact moment the `Decision` was `Identified`.
- **Constraint Inheritances**: Strict boundaries passed down from the parent `Mission` (e.g., "Do not exceed $5 API spend").

## 7. Decision Health

To prevent infinite loops or hallucination spirals, a `Decision` tracks its own health:
- **Attempt Count**: How many times the AI has tried and failed to formulate a valid `DecisionPlan`.
- **Staleness**: How much time has elapsed since the `Decision` was `Identified`.
- **Circuit Breaker**: If the health falls below a defined threshold (e.g., 3 failed attempts), the `Decision` automatically transitions to `Failed` and halts the parent `Mission`.

## 8. Invariants

- A `Decision` MUST be contextually bound to a parent `Mission`.
- A `Decision` CANNOT transition to `Resolved` unless exactly one child `DecisionPlan` has been selected and successfully executed.
- A `Decision` MUST have a clearly articulated "problem statement" or sub-goal.

## 9. Relationship with Mission

The `Mission` is the aggregate root that owns the timeline. The `Mission` delegates its execution by spawning one or more `Decisions`. If a `Decision` enters a `Failed` or `Pending` (awaiting approval) state, the parent `Mission` immediately transitions to `Blocked`.

## 10. Relationship with DecisionPlan

If the `Decision` is **WHAT** to do, the `DecisionPlan` is **HOW** to do it.

- A `Decision` acts as a container for multiple competing `DecisionPlans`.
- The AI may propose multiple `DecisionPlans` (e.g., Plan A: Use PostgreSQL, Plan B: Use SQLite) for a single `Decision`.
- Only one `DecisionPlan` can be approved and executed per `Decision`.

## 11. Success Criteria

A `Decision` is considered successful (transitioning to `Resolved`) when:
1. The AI has evaluated the generated `DecisionPlans`.
2. A single `DecisionPlan` has been selected and approved (if safety flags required it).
3. The selected `DecisionPlan`'s workflow has executed, and its localized `Outcome` metrics are verified.

## 12. Examples

**Mission:** "Audit the system logs for security anomalies."

- **Decision 1:** "How should we retrieve the logs?" (Type: Capability, Priority: Critical)
  - *DecisionPlan A*: Run `journalctl -u sshd`. (Selected)
  - *DecisionPlan B*: Read `/var/log/auth.log` directly.
  - *Outcome*: 500 lines of parsed log data.
- **Decision 2:** "How should the admin be alerted?" (Type: Capability, Priority: High)
  - *DecisionPlan A*: Send an email via SMTP connector. (Selected)
  - *DecisionPlan B*: Send a message via Slack webhook.
  - *Outcome*: Delivery confirmation receipt.

## 13. Future Extensibility

- **Parallel Decisions**: Allowing a `Mission` to resolve multiple non-dependent `Decisions` concurrently.
- **A/B Testing Options**: For non-destructive operations, executing multiple `DecisionPlans` and allowing a higher-level heuristic to evaluate which outcome was best.
- **Human-in-the-loop Ideation**: Allowing the user to manually inject a custom `DecisionPlan` into a `Decision` if the AI's generated proposals are unsatisfactory.

## 14. Out of Scope

- **Execution**: A `Decision` does not execute code. It merely selects the `DecisionPlan` that gets handed to the `Workflow` engine.
- **Routing**: Generating the actual JSON blueprint of the plan is out of scope; that is the responsibility of the `AIProviderRouter` and `DecisionPlan` schema.
