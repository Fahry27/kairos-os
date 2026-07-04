# Provider Session Specification

## 1. Objective
To manage authentication and session lifecycles for disparate AI providers without assuming identical authentication mechanisms (e.g., OAuth for Gemini, API Keys/OAuth for OpenAI, unauthenticated local for Ollama).

## 2. Functional Requirements
- Must securely persist authentication tokens or keys per provider.
- Must support background token refresh for OAuth-based providers (Gemini, OpenAI).
- Must seamlessly support providers that require no authentication (Ollama).
- Must provide an explicit logout/revocation flow to scrub credentials.

## 3. Non-functional Requirements
- **Security**: Credentials must be encrypted at rest.
- **Reliability**: Token refresh must occur preemptively before expiry to prevent mid-Mission auth failures.

## 4. Domain Interactions
- **Workspace**: Surfaces the login/auth flow UI to the Operator.
- **Provider Router**: Consumes active session tokens to inject into HTTP headers during dispatch.

## 5. API Implications
- Provider adapters must expose a generic `authenticate()` and `refresh()` interface that the session manager can call agnostically.
- Expose endpoints for the UI to query provider authentication status.

## 6. UI Implications
- The UI must dynamically render authentication requirements based on the selected provider (e.g., a simple toggle for Ollama, but an "Authorize via Google" button for Gemini).

## 7. State Transitions
- **Disconnected** -> **Authenticating** -> **Connected** -> **Refreshing** -> **Connected**
- **Connected** -> **Expired/Revoked** -> **Disconnected**

## 8. Security Considerations
- OAuth refresh tokens are highly privileged and must not be exposed to the client UI.
- Revocation must actively call the upstream provider's revoke endpoint, not just delete the local record.

## 9. Acceptance Criteria
- An Operator can authorize Gemini via OAuth, and the system can maintain connectivity for 48 hours without manual intervention, handling token refreshes automatically.
- Connecting Ollama requires no authentication parameters.

## 10. Out of Scope
- User identity management for Kairos DOS itself. This spec only handles authentication *outbound* to AI providers.
