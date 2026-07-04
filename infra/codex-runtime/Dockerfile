FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install Codex CLI
RUN curl -fsSL https://chatgpt.com/codex/install.sh | sh

# Ensure the PATH is configured for the installed binary
ENV PATH="/root/.local/bin:${PATH}"

# Keep container alive to accept commands
CMD ["tail", "-f", "/dev/null"]
