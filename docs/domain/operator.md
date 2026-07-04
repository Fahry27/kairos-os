# Operator Domain

The `Operator` domain represents the human user (or authorized external orchestrator) acting as the ultimate authority within Kairos DOS.

## 1. Purpose
The `Operator` injects intent and acts as the ultimate safety backstop. While the AI plans and executes autonomously, the `Operator` sits at the top of the chain of command, dictating the `Mission` and providing manual authorization when the system encounters safety thresholds.

## 2. Ownership
- **Parent**: None. The `Operator` is an external actor bridging into the system.
- **Children**: The `Operator` owns all `Missions` and their underlying state.

## 3. Responsibilities
- Defining the high-level `Goal` that instantiates a `Mission`.
- Reviewing `DecisionPlans` blocked at the `Approval` bridge.
- Providing overrides to the AI's logic (e.g., forcing a specific provider, rejecting a plan).
- Authorizing the persistence of `Memory` fragments.

## 4. Lifecycle
- **Active**: The `Operator` is currently logged in, authenticated, and interacting with the `Workspace`.
- **Idle**: The `Operator` is away. `Missions` may continue background processing but will halt indefinitely if they encounter an `Approval` block.

## 5. Invariants
- An `Operator` is the ONLY entity capable of resolving an `Approval` block. An AI CANNOT approve its own destructive plans.
- The `Operator` maintains final veto power. Any `Mission` or `Decision` can be aborted instantly by the `Operator`.

## 6. Relationships
- **Mission**: Owned by the `Operator`.
- **Approval**: Resolved explicitly by the `Operator`.
- **Memory**: Committed to long-term storage only upon `Operator` consent.
- **Workspace**: The physical/digital interface through which the `Operator` interacts with the system.

## 7. Success Criteria
- The system must provide the `Operator` with sufficient, transparent context to make informed authorizations rapidly without cognitive overload.

## 8. Examples
- The AI proposes a `DecisionPlan` to run `DROP TABLE temp_logs;`. The system blocks. The `Operator` reviews the generated SQL and clicks "Approve".
- The `Operator` configures their profile to force Ollama (local) routing for a highly sensitive medical data `Mission`.

## 9. Future Extensibility
- **RBAC (Role-Based Access Control)**: Supporting different tiers of Operators (e.g., Read-Only Observer, Junior Operator, Admin).
- **Delegated Operators**: Allowing a human to delegate Approval rights to a highly trusted secondary AI agent for specific, low-risk sub-domains.

## 10. Out of Scope
- **Authentication Implementation**: Managing passwords, 2FA, and SSO flows. The system assumes the `Operator` identity is provided by the outer identity provider.
