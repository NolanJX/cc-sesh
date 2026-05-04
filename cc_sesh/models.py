from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SessionMeta:
    session_id: str
    title: str | None
    summary: str | None
    project_dir: str | None
    created_at: int | None
    last_active_at: int | None
    source_path: str


@dataclass
class SessionMessage:
    role: str
    content: str
    ts: int | None
