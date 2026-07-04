# Outcome Domain

The `Outcome` domain represents the definitive, objective result of executing a `Workflow` mapped to an approved `DecisionPlan`.

## 1. Purpose
The `Outcome` serves as the factual record of execution. It answers the question: "What actually happened when we executed this plan?" It captures metrics, stdout/stderr, network responses, and success flags.

## 2. Ownership
- **Parent**: An `Outcome` strictly belongs to a single `Decision`.
- **Children**: None. `Outcome` is a terminal artifact.

## 3. Responsibilities
- Recording the raw execution artifacts produced by the `Workflow`.
- Mapping physical execution errors back to the logical `Decision`.
- Triggering the `Reflection` phase once execution ceases.

## 4. Lifecycle
- **Pending**: The associated `Workflow` is currently executing.
- **Recorded**: The `Workflow` has completed, and the results (success or failure) are permanently logged.

## 5. Invariants
- An `Outcome` is **immutable** after it transitions to `Recorded`. History cannot be edited.
- An `Outcome` MUST trace back to exactly one executed `DecisionPlan`.

## 6. Relationships
- **Decision**: Owns the `Outcome`.
- **Workflow**: The execution engine that generates the raw data for the `Outcome`.
- **Reflection**: Uses the `Outcome` as the baseline ground-truth for post-execution analysis.

## 7. Success Criteria
- Accurately captures 100% of the termination state of the `Workflow` (e.g., exit codes, payload sizes, trace IDs) without dropping context.

## 8. Examples
- A database backup script was run. The `Outcome` contains `exit code: 0`, the filename, and the execution time (4.2 seconds).
- An API call failed. The `Outcome` contains `HTTP 502 Bad Gateway` and the associated stack trace.

## 9. Future Extensibility
- **Diffing**: Automatically generating semantic diffs if an `Outcome` involves modifying a local configuration file.
- **Redaction**: Automated stripping of sensitive PII or credentials from `Outcome` logs before they are written to disk.

## 10. Out of Scope
- Evaluating or analyzing *why* an error happened (this belongs to `Reflection`).
- Interacting with the AI Provider; `Outcome` is purely a data structure representing raw execution reality.
