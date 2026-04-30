FROM mcr.microsoft.com/devcontainers/base:trixie

RUN curl -fsSL https://claude.ai/install.sh | bash

RUN mkdir -p /home/vscode/.claude

COPY --chown=vscode:vscode claude-code-config/.claude/settings.json /home/vscode/.claude/settings.json
COPY --chown=vscode:vscode claude-code-config/.claude.json /home/vscode/.claude.json
