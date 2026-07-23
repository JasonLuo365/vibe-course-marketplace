"""Strict discovery of the active Claude Code transcript."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .sessions import SessionInfo, _parse_iso


class ClaudeSessionError(Exception):
    """Raised when the active Claude Code transcript cannot be verified."""


def _claude_config_dir() -> Path:
    configured = os.environ.get("CLAUDE_CONFIG_DIR")
    return Path(configured) if configured else Path.home() / ".claude"


def _active_session_id() -> str:
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if not session_id:
        raise ClaudeSessionError("CLAUDE_CODE_SESSION_ID is required for Claude Code submission")
    return session_id


def _find_transcript(config_dir: Path, session_id: str) -> Path:
    projects_dir = config_dir / "projects"
    matches = list(projects_dir.glob(f"**/{session_id}.jsonl")) if projects_dir.exists() else []
    if not matches:
        raise ClaudeSessionError(f"Claude transcript not found for active session {session_id}")
    if len(matches) != 1:
        raise ClaudeSessionError(f"multiple Claude transcripts found for active session {session_id}")
    return matches[0]


def _read_metadata(path: Path, session_id: str) -> SessionInfo:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as transcript:
            for line_number, raw in enumerate(transcript, start=1):
                line = raw.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ClaudeSessionError(
                        f"malformed Claude transcript {path} at line {line_number}"
                    ) from exc
                if not isinstance(event, dict) or event.get("sessionId") != session_id:
                    continue
                cwd = event.get("cwd")
                timestamp = event.get("timestamp")
                if not isinstance(cwd, str) or not cwd or not isinstance(timestamp, str) or not timestamp:
                    raise ClaudeSessionError(
                        f"Claude transcript {path} has insufficient metadata for session {session_id}"
                    )
                try:
                    started_at = _parse_iso(timestamp)
                except (TypeError, ValueError) as exc:
                    raise ClaudeSessionError(
                        f"Claude transcript {path} has an invalid timestamp for session {session_id}"
                    ) from exc
                return SessionInfo(path=path, session_id=session_id, cwd=cwd, started_at=started_at)
    except OSError as exc:
        raise ClaudeSessionError(f"unable to read Claude transcript {path}: {exc}") from exc
    raise ClaudeSessionError(f"Claude transcript {path} has insufficient metadata for session {session_id}")


def find_claude_session(project_root: Path) -> SessionInfo:
    """Return the sole active Claude Code session for ``project_root``.

    This deliberately accepts no historical fallback: the environment-selected
    session must map to exactly one transcript under Claude's projects store.
    """
    session_id = _active_session_id()
    transcript = _find_transcript(_claude_config_dir(), session_id)
    info = _read_metadata(transcript, session_id)
    try:
        actual_root = Path(info.cwd).resolve()
        expected_root = Path(project_root).resolve()
    except OSError as exc:
        raise ClaudeSessionError(f"unable to resolve Claude session project path: {exc}") from exc
    if actual_root != expected_root:
        raise ClaudeSessionError(
            f"active Claude session {session_id} does not belong to project {expected_root}"
        )
    return info
