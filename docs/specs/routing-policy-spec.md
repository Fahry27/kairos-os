# Routing Policy Specification

## 1. Objective
To define the rules engine that the AI Provider Router uses to autonomously select the optimal AI provider for a given `Decision`, balancing capability, cost, priority, and manual overrides.

## 2. Functional Requirements
- Must evaluate incoming `Decision` constraints against the Capability Matrix (ADR-012).
- Must respect `Operator` manual overrides (e.g., pinning a specific model).
- Must respect `Offline Mode`, instantly culling all cloud providers from the selection pool.
- Must select the lowest-cost provider that meets the capability requirements unless explicitly directed otherwise.

## 3. Non-functional Requirements
- **Performance**: Routing decisions must execute in memory in < 1ms.
- **Determinism**: Given the same inputs, constraints, and provider health states, the router must consistently pick the same provider.

## 4. Domain Interactions
- **Decision**: Dictates the constraints (e.g., requires vision, requires tool calling).
- **Workspace**: Provides the `Operator` overrides and Offline Mode toggle state.

## 5. API Implications
- Internal routing functions must accept a `DecisionContext` and return a specific `ProviderInstance`.

## 6. UI Implications
- The UI should indicate which provider was selected for a specific `Decision` and explicitly highlight if a fallback or offline routing path was taken.

## 7. State Transitions
- N/A. The routing policy is stateless; it evaluates conditions based on the current snapshot of provider health and configuration.

## 8. Security Considerations
- Routing must NEVER ignore Offline Mode. If Offline Mode is active, ensuring cloud endpoints are excluded is a critical security and privacy boundary.

## 9. Acceptance Criteria
- A `Decision` requiring "vision" capabilities is routed to Gemini, bypassing Ollama, even if Ollama is marked as the default provider, because Ollama lacks vision capabilities in the matrix.
- Toggling "Offline Mode" causes the same `Decision` to immediately fail with a routing exception, rather than sending images to the cloud.

## 10. Out of Scope
- Actually executing the API call (this is the Router's dispatch duty).
- Tracking the health of the providers (this is the Provider Health spec).
