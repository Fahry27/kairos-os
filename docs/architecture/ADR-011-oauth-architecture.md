# ADR 011: Provider Session Architecture

## Status
Proposed

## Context
With the transition to a cloud-first provider strategy (ADR 010), Kairos OS must securely authenticate against commercial APIs. Previously considered as a simple OAuth integration, this requirement has expanded into a full Provider Session Architecture to handle identity, long-lived access, and secure token lifecycle management without forcing users to handle static API keys.

## Decision
We will implement a robust **Provider Session Architecture** utilizing OAuth 2.0 and OpenID Connect (OIDC) where applicable.

1. **Identity & Scopes**: Kairos will authenticate the user identity via OAuth and request strictly scoped access (e.g., `model.read`, `model.execute`). This ensures Kairos only operates within the bounds explicitly granted by the user.
2. **Session Lifecycle (Refresh)**: The system will securely persist access and refresh tokens. Background workers will preemptively rotate and refresh tokens before expiry, ensuring uninterrupted background planning and execution.
3. **Logout & Revocation**: Users will have a definitive "Disconnect" action which explicitly revokes the tokens at the provider level (e.g., calling OpenAI's or Google's token revocation endpoints) and scrubs the session data from local storage.
4. **Future Extensibility**: The `AIProviderMetadata` structure standardizes `auth_type` to natively support diverse authentication profiles, seamlessly onboarding future providers.

## Consequences
- **Positive**: Highly secure, zero-touch authentication experience.
- **Positive**: Strict scoping limits blast radius if the local system is compromised.
- **Negative**: High complexity in managing asynchronous refresh loops, network failures during refresh, and session state consistency.
