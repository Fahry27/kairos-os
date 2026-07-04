# Provider Platform Specification

## 1. Objective
To establish a provider-agnostic platform that seamlessly integrates multiple AI providers (OpenAI, Gemini, Ollama) into Kairos DOS, ensuring that the `PlannerEngine` and internal business logic remain entirely decoupled from vendor-specific API structures.

## 2. Functional Requirements
- Must provide a standardized `AIProviderRouter` interface for dispatching requests.
- Must support dynamic capability querying (e.g., "does this provider support vision?").
- Must abstract request payloads into a unified Kairos format before dispatch.
- Must translate provider-specific JSON responses back into standard Kairos `DecisionPlan` data structures.

## 3. Non-functional Requirements
- **Extensibility**: Adding a new provider must require zero changes to the `PlannerEngine` or core domains.
- **Latency**: The abstraction layer must add < 5ms of overhead to API calls.

## 4. Domain Interactions
- **Mission/Decision**: Requests planning capabilities through the Provider Platform.
- **Knowledge**: Injected into the standardized prompt payload.
- **Operator**: Can override platform defaults via `Workspace` settings.

## 5. API Implications
- Internal APIs must only accept and return the generic `AIProviderRouterDispatchRequest` and `AIProviderRouterDispatchResponse`.
- Vendor-specific endpoints (e.g., `/v1/chat/completions` vs `/v1beta/models/...`) are strictly isolated within Provider Adapters.

## 6. UI Implications
- The UI must display the abstract capabilities of the platform without tightly coupling UI components to specific vendors (e.g., show a generic "AI Status" rather than "OpenAI Status").

## 7. State Transitions
- **Uninitialized** -> **Initializing** (Loading adapters) -> **Ready** -> **Degraded** (If one or more providers fail).

## 8. Security Considerations
- The platform must scrub internal system metrics or sensitive headers before passing payloads to third-party cloud providers.
- Local provider payloads (Ollama) can be subjected to less strict scrubbing due to local data residency.

## 9. Acceptance Criteria
- A `DecisionPlan` can be generated successfully by swapping the underlying provider from OpenAI to Gemini without modifying the `PlannerEngine` code.

## 10. Out of Scope
- Managing the explicit retry logic or fallback sequence (handled by Routing/Fallback policies).
- Auth implementation (handled by Provider Session).
