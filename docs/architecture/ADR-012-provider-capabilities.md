# ADR 012: Provider Capabilities and Resilience

## Status
Proposed

## Context
With multiple AI providers integrated into the Kairos ecosystem, we face heterogeneous feature sets. Some providers support vision or structured tool-calling while others do not. Furthermore, cloud endpoints are susceptible to rate limits and generate direct financial costs, unlike local models.

## Decision
We will formalize capabilities, ratings, and cost-awareness directly into the provider routing mechanism.

### Capability Comparison & Ratings

The `AIProviderMetadata` will track explicit feature flags and qualitative benchmark ratings (0-100) to allow intelligent model selection.

| Provider / Model | Vision | Tool Calling | JSON Schema | Coding Score | Planning Score | Cost |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **OpenAI / gpt-4o** | Yes | Yes | Yes | 95 | 92 | High |
| **Gemini / 1.5-pro** | Yes | Yes | Yes | 91 | 94 | Medium |
| **Ollama / llama3.2** | No | Partial | No | 70 | 65 | Free (Local) |

### Resilience and Cost Awareness
1. **Cost Awareness**: The router will track the estimated token cost per provider. Workloads will specify their acceptable cost tier (e.g., `background-task=low-cost`, `active-dev=high-cost`). The router will prefer the most capable model within the requested cost tier.
2. **Health Checking**: The provider router will proactively poll provider health endpoints (e.g., `/api/tags` for Ollama) to continuously assess functional status. Unhealthy providers are excised from the active pool.
3. **Retry Strategy**: We will implement standard resilience patterns (exponential backoff, jitter) for cloud network requests.
4. **Fallback Flow**: If a primary provider exhausts its retry budget, the router automatically fails over to the next available provider matching the required capability and cost constraints.

## Consequences
- **Positive**: Intelligent, workload-appropriate model selection saves costs and improves reliability.
- **Positive**: The system naturally avoids sending unsupported requests (e.g., vision tasks) to text-only models.
- **Negative**: Requires maintaining and periodically updating the benchmark ratings and cost tier tables.
