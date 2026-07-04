# ADR 010: AI Provider Strategy

## Status
Proposed

## Context
Kairos OS initially adopted a local-first approach relying entirely on Ollama to provide AI capabilities. While this guaranteed maximum privacy and offline availability, it constrained the system to local hardware limits and excluded state-of-the-art frontier models.

As the system scales to more complex orchestration and planning workloads, we need a flexible strategy that can leverage both cloud and local AI models intelligently.

## Decision
We are transitioning to a **Cloud-first architecture** with intelligent fallback mechanisms. 

1. **Explicit Provider Priority**: The router will evaluate providers in the following default order:
   - Primary Cloud (e.g., OpenAI `gpt-4o`, Google `gemini-1.5-pro`)
   - Secondary Cloud (e.g., Anthropic `claude-3-5-sonnet`)
   - Local Fallback (e.g., Ollama `llama3.2`)
2. **Manual Override**: Users can pin a specific provider or model for a given workspace session, bypassing the default priority queue. This ensures predictable behavior for specific workloads.
3. **Offline Mode**: A strict toggle that instantly excises all cloud providers from the routing pool. If enabled, the system relies exclusively on local inference (Ollama) and fails fast if no local provider is reachable, rather than attempting network calls.
4. **Provider Selection Policy**: The `AIProviderRouter` will implement a configurable policy engine. Requests will be routed based on priority, provider health, network reachability, and capability requirements.

## Consequences
- **Positive**: Access to frontier AI models greatly enhances the reasoning and planning capabilities of Kairos OS.
- **Positive**: The system remains resilient with the Ollama fallback and respects air-gapped constraints via Offline Mode.
- **Negative**: Increased architectural complexity in managing multiple AI provider APIs and their respective failure modes.
