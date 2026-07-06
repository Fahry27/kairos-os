# ADR 015: Authentication Platform Architecture

## Status
**SUPERSEDED** — Phase B of the Genesis Migration removed the unused `auth_platform.py` scaffold (`AuthenticationManager`, `CredentialProvider`, `SessionStore`, `TokenStore`). Only the base `AuthenticationAdapter` interface and `ProviderSession` model survive. This ADR no longer reflects active implementation guidance. See Sprint 1 (Kairos Shell) for current auth approach. (2026-07-06)

## Context
Kairos is a Decision Operating System where AI providers (OpenAI, Google Gemini, Ollama) are treated as pluggable implementation details. While the `AIProviderRouter` (ADR 014) abstracts vendor-specific API request/response translation, it currently lacks a unified, secure foundation to manage authentication. 

AI providers rely on vastly different authentication mechanisms:
*   **Ollama:** Typically unauthenticated or secured locally via network firewalls and basic auth proxies.
*   **OpenAI:** Static developer API keys or Workload Identity Federation.
*   **Google Gemini:** Static API keys (AI Studio) or OAuth 2.0 / Service Accounts (Vertex AI).

To support multi-tenant, multi-account, and enterprise deployments without leaking vendor auth logic into the router, we need a generic, secure, and local-first **Authentication Platform**.

## Decision
We will establish a decentralized **Authentication Platform** built around three core concepts: the `AuthenticationAdapter` interface, the `ProviderSession` abstraction, and a secure server-side credential vault.

### 1. Authentication Adapter Pattern
Each provider registry entry will correspond to a provider-specific `AuthenticationAdapter`. This adapter encapsulates the vendor-specific auth flow:
*   **Google Cloud/Vertex AI Adapter:** Manages the OAuth 2.0 authorization code flow, handling token exchanges and refresh requests.
*   **OpenAI Adapter:** Handles static API key loading and validation.
*   **Ollama Adapter:** Handles local loopback connections or basic authorization headers for local proxies.

### 2. Provider Session Abstraction
The `AIProviderRouter` must remain decoupled from specific auth implementations. It will depend exclusively on the abstract `ProviderSession` object. A `ProviderSession` contains:
*   `session_id`: Unique identifier of the session.
*   `provider_id`: Reference to the provider (e.g., `ai.openai`).
*   `credential_ref`: Opaque reference to the credential stored in the secure vault.
*   `state`: Current state in the session lifecycle (ADR 016).
*   `identity`: User identifier or account reference associated with the session.

### 3. Multi-Provider and Multi-Account Support
The system must support binding multiple accounts to a single provider (e.g., a user holding both personal and enterprise OpenAI API keys). Sessions will map to individual active identities, and the `AIProviderRouter` will select the correct session based on the routing policy.

### 4. Token Ownership & Security Boundaries
*   **Backend Ownership:** Storing, validating, and refreshing tokens or keys is strictly restricted to the backend core service.
*   **No Client Leakage:** Raw credentials or access tokens are never exposed to the `Kairos Dashboard` frontend. The client-side dashboard only receives an opaque `session_id`.
*   **Secure Local Storage:** Credentials are saved in a local, platform-encrypted vault (e.g., system keyring for desktop use, or encrypted env databases for cloud nodes) obeying local-first principles.

### 5. Refresh, Logout, and Revocation
*   **Refresh Strategy:** The `AuthenticationAdapter` implements background refresh tasks for expiring credentials (like OAuth access tokens) using saved refresh tokens.
*   **Logout and Revocation:** Users can explicitly log out. This action invalidates the local session. If the provider supports remote token revocation (OAuth revoke endpoints), the corresponding `AuthenticationAdapter` will issue a revocation HTTP call to clean up permissions on the provider side.

## Consequences
*   **Positive:** Loose coupling. The `AIProviderRouter` does not need to know how credentials are exchanged, refreshed, or stored.
*   **Positive:** Secure-by-default. Credential leakage to the client is impossible since the frontend only deals with opaque session tokens.
*   **Positive:** Local-first compliance. Local models (Ollama) remain usable entirely offline without internet dependencies or cloud token exchanges.
*   **Negative:** Increased system complexity. The backend must now manage session state machines, background token refresh schedules, and credential encryption keys.
