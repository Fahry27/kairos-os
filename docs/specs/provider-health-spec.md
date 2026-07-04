# Provider Health Specification

## 1. Objective
To standardize continuous health monitoring for all AI providers, allowing the Provider Router to make intelligent routing decisions and avoid black-holing requests into offline or degraded services.

## 2. Functional Requirements
- Must proactively ping provider health endpoints at a configurable interval (e.g., `/api/tags` for Ollama).
- Must track passive health metrics (e.g., catching timeouts or 5xx errors during actual dispatch).
- Must implement a Circuit Breaker pattern to immediately sever traffic to a failing provider.
- Must attempt "half-open" recovery tests to bring a provider back online after a failure period.

## 3. Non-functional Requirements
- **Overhead**: Proactive health checks must run in background threads and not block the main event loop or active `Missions`.
- **Resilience**: The health tracking module must gracefully handle DNS failures and total network loss without crashing the system.

## 4. Domain Interactions
- **Routing Policy**: Reads the health status to filter out degraded providers from the selection pool.
- **Provider Platform**: Reports passive dispatch errors to the health tracker.

## 5. API Implications
- Expose an internal API `get_provider_health(provider_id)` returning `Healthy`, `Degraded`, or `Offline`.
- Provider Adapters must implement a standardized `ping()` method.

## 6. UI Implications
- The Workspace should display real-time status indicators (green/yellow/red dots) for all configured providers so the `Operator` understands system capability at a glance.

## 7. State Transitions
- **Healthy** -> (Consecutive Failures) -> **Offline**
- **Offline** -> (Timeout Expiry) -> **Half-Open**
- **Half-Open** -> (Successful Ping) -> **Healthy**
- **Half-Open** -> (Failed Ping) -> **Offline**

## 8. Security Considerations
- Health check requests must use the same secured `Provider Session` tokens as actual requests to accurately gauge API accessibility, not just network reachability.

## 9. Acceptance Criteria
- Stopping the local Ollama docker container immediately transitions the Ollama health state to `Offline`. Restarting the container transitions it back to `Healthy` within the next polling interval, without requiring a system restart.

## 10. Out of Scope
- Attempting to restart external containers or fix network issues. The health system only observes and reports state.
