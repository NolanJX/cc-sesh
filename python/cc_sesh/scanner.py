from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cc_sesh.models import SessionMeta

SESSIONS_ROOT = Path.home() / ".claude" / "projects"
TITLE_MAX = 80
SUMMARY_MAX = 160


def parse_ts(val: object) -> int | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        ms = int(val)
        return ms if ms > 1_000_000_000_000 else ms * 1000
    if isinstance(val, str):
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1000)
    return None


def _extract_text_from_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p)
    if isinstance(content, dict):
        return content.get("text", "")
    return ""


def _is_system_message(text: str) -> bool:
    return (
        "<local-command-caveat>" in text
        or text.startswith("<command-name>")
        or text.startswith("<command-message>")
    )


def _parse_session(path: Path) -> SessionMeta | None:
    lines = path.read_text().splitlines()

    session_id: str | None = None
    project_dir: str | None = None
    created_at: int | None = None
    last_active_at: int | None = None
    first_user_msg: str | None = None
    custom_title: str | None = None
    summary: str | None = None

    for line in lines:
        rec = json.loads(line)

        ts = parse_ts(rec.get("timestamp"))
        if ts is not None:
            if created_at is None:
                created_at = ts
            last_active_at = ts

        if session_id is None and "sessionId" in rec:
            session_id = rec["sessionId"]

        if project_dir is None and "cwd" in rec:
            project_dir = rec["cwd"]

        if rec.get("type") == "custom-title" and "customTitle" in rec:
            custom_title = rec["customTitle"]

        msg = rec.get("message")
        if msg and msg.get("role") == "user" and not rec.get("isMeta"):
            text = _extract_text_from_content(msg.get("content"))
            if text and first_user_msg is None and not _is_system_message(text):
                first_user_msg = text
            if text:
                summary = text

        if msg and msg.get("role") == "assistant":
            text = _extract_text_from_content(msg.get("content"))
            if text:
                summary = text

    if session_id is None:
        session_id = path.stem

    title = custom_title or first_user_msg
    if title:
        title = title[:TITLE_MAX] + ("..." if len(title) > TITLE_MAX else "")
    elif project_dir:
        title = project_dir.rstrip("/").rsplit("/", 1)[-1]
    else:
        title = session_id[:8]

    if summary:
        summary = summary[:SUMMARY_MAX] + ("..." if len(summary) > SUMMARY_MAX else "")

    return SessionMeta(
        session_id=session_id,
        title=title,
        summary=summary,
        project_dir=project_dir,
        created_at=created_at,
        last_active_at=last_active_at,
        source_path=str(path),
    )


def scan_sessions() -> list[SessionMeta]:
    sessions: list[SessionMeta] = []
    for path in SESSIONS_ROOT.rglob("*.jsonl"):
        if path.name.startswith("agent-"):
            continue
        session = _parse_session(path)
        if session is not None:
            sessions.append(session)

    sessions.sort(key=lambda s: s.last_active_at or s.created_at or 0, reverse=True)
    return sessions
