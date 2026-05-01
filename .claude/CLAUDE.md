# Project-level CLAUDE.md

This file is project-level instructions checked into the repo at `.claude/CLAUDE.md`. It is loaded whenever Claude Code runs in this project.

For user-level instructions inside the Dev Container, see `.devcontainer/claude-code-config/.claude/CLAUDE.md`. That file is copied to `~/.claude/CLAUDE.md` during the Docker image build (see `Dockerfile`), giving every Dev Container user the same baseline environment info.

## Permissions

- Always ask for user approval before executing git commit.
