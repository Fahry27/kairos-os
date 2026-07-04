# ADR 014: Provider Router Architecture

## Status
Proposed

## Context
With the introduction of multiple AI providers (Ollama, OpenAI, Gemini) (ADR 010), the backend logic for interacting with AI models risks becoming fragmented. Each provider has unique API endpoints, payload structures, and error schemas. Hardcoding these integrations directly into the `PlannerEngine` would tightly couple the business logic to external APIs, making it brittle and difficult to maintain.

## Decision
We will implement an abstract **`AIProviderRouter`** as a centralized middleware layer.

1. **Standardized Internal Request/Response**: The rest of the Kairos backend (like the `PlannerEngine`) will only communicate using a standard internal schema (`AIProviderRouterDispatchRequest` and `AIProviderRouterDispatchResponse`). 
2. **Translation Layer**: The Router is responsible for translating the internal schema into the specific payload structure required by the target provider (e.g., formatting tool definitions for OpenAI vs. Gemini).
3. **Policy Enforcement**: The Router owns the `ProviderSelectionPolicy`. It independently decides which physical API to call based on capability requirements, cost constraints, and health checks, abstracting this complexity away from the caller.
4. **Resilience Handling**: The Router implements the circuit breakers and fallback logic (ADR 012). If a request to OpenAI fails, the Router catches the exception, updates the provider's health status, and transparently re-routes the standard request to the fallback provider.

## Consequences
- **Positive**: Clean separation of concerns. Business logic is decoupled from vendor-specific API quirks.
- **Positive**: Adding a new AI provider only requires writing a new translation adapter in the Router, leaving the rest of the system untouched.
- **Negative**: The Router becomes a critical path bottleneck; bugs here affect all AI capabilities.
