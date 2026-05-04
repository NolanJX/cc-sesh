from __future__ import annotations

import json
from pathlib import Path

from cc_sesh.models import SessionMessage
from cc_sesh.scanner import parse_ts


def extract_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                btype = block.get("type")
                if btype == "text":
                    parts.append(block.get("text", ""))
                elif btype == "tool_use":
                    parts.append(f"[Tool: {block.get('name', 'unknown')}]")
                elif btype == "tool_result":
                    nested = block.get("content", "")
                    parts.append(extract_content(nested))
                else:
                    parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p)
    if isinstance(content, dict):
        return content.get("text", "")
    return ""


def _classify_role(role: str, content: object) -> str:
    if role == "assistant":
        return "assistant"
    if role == "user":
        if isinstance(content, list):
            if all(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
                return "tool"
        return "user"
    return "user"


def load_messages(source_path: str) -> list[SessionMessage]:
    lines = Path(source_path).read_text().splitlines()
    messages: list[SessionMessage] = []

    for line in lines:
        rec = json.loads(line)
        if rec.get("isMeta"):
            continue

        msg = rec.get("message")
        if msg is None:
            continue

        content = msg.get("content")
        role = _classify_role(msg.get("role", "user"), content)
        text = extract_content(content)
        if not text:
            continue

        ts = parse_ts(rec.get("timestamp"))
        messages.append(SessionMessage(role=role, content=text, ts=ts))

    return messages
