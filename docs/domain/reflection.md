# Reflection Domain

The `Reflection` domain is the cognitive post-mortem engine of Kairos DOS. It evaluates the delta between what was proposed and what actually happened.

## 1. Purpose
The `Reflection` domain compares the proposed `DecisionPlan` against the actual `Outcome`. It extracts lessons, identifies systemic failures, and drafts persistent context that will help the AI improve in future scenarios.

## 2. Ownership
- **Parent**: `Reflection` is owned by the `Decision`.
- **Children**: None directly, but it proposes data to the `Memory` domain.

## 3. Responsibilities
- Analyzing the gap between the `DecisionPlan`'s predicted success criteria and the `Outcome`'s raw reality.
- Generating a human-readable summary of lessons learned.
- Proposing new `Memory` fragments to be persisted to the global store.

## 4. Lifecycle
- **Analyzing**: AI is actively evaluating the `Outcome` and `DecisionPlan`.
- **Drafted**: A post-mortem summary and proposed `Memory` fragments have been generated.
- **Approved**: The `Operator` has reviewed and approved the extraction of lessons.

## 5. Invariants
- A `Reflection` MUST NEVER edit historical records (e.g., the `Outcome` or the `DecisionPlan`). History is immutable.
- A `Reflection` MUST be anchored to a `Recorded` `Outcome`.

## 6. Relationships
- **Decision**: Owns the `Reflection`.
- **DecisionPlan**: The baseline hypothesis evaluated by the Reflection.
- **Outcome**: The factual reality evaluated by the Reflection.
- **Memory**: The target destination for lessons extracted during Reflection.

## 7. Success Criteria
- Successfully identifies the root cause of an `Outcome` failure, or correctly identifies the key actions that led to a successful `Outcome`.

## 8. Examples
- The AI planned to use `apt-get` but the system is RHEL. The `Outcome` shows a `Command Not Found` error. The `Reflection` states: "System is RHEL, `apt-get` is invalid here. Must use `dnf` or `yum`."
- A backup script ran perfectly. `Reflection` notes: "The backup directory `/mnt/data/` has standard write access, execution was flawless."

## 9. Future Extensibility
- **Automated Re-planning**: If a `Reflection` detects a recoverable failure, it can automatically trigger a new `Decision` draft in the parent `Mission`.
- **Global Sentiment Analysis**: Aggregating reflections across multiple missions to calculate an overall "system stability score".

## 10. Out of Scope
- Actually persisting the extracted lessons into a vector database (that is the job of the `Memory` domain).
- Alerting the user in real-time (the `Workspace` handles notifications).
