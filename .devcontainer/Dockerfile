FROM mcr.microsoft.com/devcontainers/base:trixie

RUN install -d -m 0755 /etc/apt/keyrings \
    && curl -fsSL https://downloads.claude.ai/keys/claude-code.asc \
        -o /etc/apt/keyrings/claude-code.asc \
    && echo "deb [signed-by=/etc/apt/keyrings/claude-code.asc] https://downloads.claude.ai/claude-code/apt/stable stable main" \
        > /etc/apt/sources.list.d/claude-code.list \
    && apt-get update \
    && apt-get install -y claude-code \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /home/vscode/.claude

COPY --chown=vscode:vscode claude-code-config/.claude/settings.json /home/vscode/.claude/settings.json
COPY --chown=vscode:vscode claude-code-config/.claude.json /home/vscode/.claude.json
