# Supported Platforms

Kairos DOS is designed to be highly portable, deploying seamlessly from a developer's laptop to an enterprise Kubernetes cluster.

## 1. Primary Operating Systems
- **macOS (Apple Silicon & Intel)**: Native execution for local development and edge operations.
- **Linux (Ubuntu/Debian, RHEL)**: The primary target for production server deployments.

## 2. Deployment Profiles

### Edge / Local (Docker Compose)
Targeted at individual developers and localized network operations. The entire Kairos stack (API, Dashboard, and optionally local Ollama) boots via a single `docker-compose.yml` file.

### Cloud Native (Kubernetes)
Targeted at enterprise deployments managing large-scale workloads. Kairos is deployed via Helm charts, relying entirely on Cloud AI Providers (OpenAI, Gemini) for inference, and scaling the `Workflow` execution engine dynamically across worker nodes.

## 3. Integration Ecosystem
Kairos DOS interacts with the outside world via its capabilities system, which supports:
- **Local Shell execution** (bash, zsh).
- **REST APIs** (via generic webhook and HTTP connectors).
- **Native Plugins** (PostgreSQL, AWS CLI, GitHub API).
