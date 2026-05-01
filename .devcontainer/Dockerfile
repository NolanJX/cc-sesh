FROM mcr.microsoft.com/devcontainers/base:trixie

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

RUN install -d -m 0755 /etc/apt/keyrings \
    && curl -fsSL https://downloads.claude.ai/keys/claude-code.asc \
        -o /etc/apt/keyrings/claude-code.asc \
    && echo "deb [signed-by=/etc/apt/keyrings/claude-code.asc] https://downloads.claude.ai/claude-code/apt/stable stable main" \
        > /etc/apt/sources.list.d/claude-code.list \
    && apt-get update \
    && apt-get install -y claude-code \
    && rm -rf /var/lib/apt/lists/*

# Pre-seed Superpowers plugin at build time
RUN CLAUDE_CODE_PLUGIN_CACHE_DIR=/opt/claude-seed \
    claude plugin marketplace add obra/superpowers-marketplace \
    && CLAUDE_CODE_PLUGIN_CACHE_DIR=/opt/claude-seed \
    claude plugin install superpowers@superpowers-marketplace

RUN mkdir -p /home/vscode/.claude \
    && chown vscode:vscode /home/vscode/.claude

COPY --chown=vscode:vscode .devcontainer/claude-code-config/.claude/CLAUDE.md /home/vscode/.claude/CLAUDE.md
COPY --chown=vscode:vscode .devcontainer/claude-code-config/.claude/settings.json /home/vscode/.claude/settings.json
COPY --chown=vscode:vscode .devcontainer/claude-code-config/.claude.json /home/vscode/.claude.json
