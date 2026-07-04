# Fallback Policy Specification

## 1. Objective
To establish the protocol for transparent failover when a primary AI provider fails during a `Mission` or `Decision` cycle, ensuring system resilience without burdening the `Operator` with manual retry tasks.

## 2. Functional Requirements
- Must intercept network timeouts, 5xx HTTP errors, and rate limit (429) errors from the primary provider.
- Must query the `Routing Policy` for the next-best available provider.
- Must seamlessly re-dispatch the exact same `DecisionContext` prompt to the fallback provider.
- Must log the failover event for telemetry and `Reflection`.

## 3. Non-functional Requirements
- **Transparency**: Fallbacks must happen inside the routing layer; the `PlannerEngine` should be completely unaware that a failover occurred.
- **Speed**: Failover detection and re-dispatch must occur instantly upon encountering a terminal error from the primary provider.

## 4. Domain Interactions
- **Provider Router**: Owns the execution of the fallback sequence.
- **Routing Policy**: Consulted to determine the next eligible target.
- **Provider Health**: Updated immediately to mark the failing provider as `Degraded` or `Offline`.

## 5. API Implications
- Internal dispatch methods must implement recursive or loop-based failover mechanisms that consume a bounded retry budget to prevent infinite failover loops.

## 6. UI Implications
- If a fallback occurs, the `Workspace` should temporarily surface a warning (e.g., "OpenAI failed, falling back to Gemini") so the `Operator` is aware of the degradation in primary service.

## 7. State Transitions
- **Dispatch Primary** -> (Error) -> **Mark Primary Degraded** -> **Select Fallback** -> **Dispatch Fallback** -> (Success) -> **Return Payload**

## 8. Security Considerations
- If `Offline Mode` is enabled, the fallback policy MUST NOT fall back to a cloud provider under any circumstance. Fallback is restricted entirely to other local providers (e.g., falling back from a Llama3 model to a Mistral model running locally on Ollama).

## 9. Acceptance Criteria
- While a `Mission` is active using OpenAI, simulating a DNS failure for `api.openai.com` results in the system seamlessly re-routing the prompt to Gemini (or Ollama) and successfully completing the `Decision`, rather than failing the `Mission`.

## 10. Out of Scope
- Attempting to split a single prompt across multiple providers simultaneously. Fallback is strictly sequential.
