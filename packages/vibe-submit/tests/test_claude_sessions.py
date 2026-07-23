import json
from pathlib import Path

import pytest

from vibe_submit.claude_sessions import ClaudeSessionError, find_claude_session
from vibe_submit.sessions import find_sessions_for_source


def _write_transcript(path: Path, session_id: str, cwd: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        {"type": "user", "sessionId": session_id, "cwd": str(cwd), "timestamp": "2026-07-23T01:02:03Z"},
        {"type": "assistant", "sessionId": session_id, "cwd": str(cwd), "timestamp": "2026-07-23T01:03:03Z"},
    ]
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")


def test_finds_exact_active_claude_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "claude"
    session_id = "active-session"
    transcript = config_dir / "projects" / "workspace" / f"{session_id}.jsonl"
    _write_transcript(transcript, session_id, project_root)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", session_id)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

    session = find_claude_session(project_root)

    assert session.path == transcript
    assert session.session_id == session_id
    assert session.cwd == str(project_root)
    assert session.started_at.isoformat() == "2026-07-23T01:02:03+00:00"
    assert find_sessions_for_source("claude", project_root) == [session]


def test_ignores_claude_metadata_prefix_without_cwd_or_timestamp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "claude"
    session_id = "active-session"
    transcript = config_dir / "projects" / "workspace" / f"{session_id}.jsonl"
    transcript.parent.mkdir(parents=True, exist_ok=True)
    transcript.write_text(
        "\n".join(
            [
                json.dumps({"type": "mode", "mode": "normal", "sessionId": session_id}),
                json.dumps(
                    {
                        "type": "permission-mode",
                        "permissionMode": "default",
                        "sessionId": session_id,
                    }
                ),
                json.dumps(
                    {
                        "type": "last-prompt",
                        "lastPrompt": "submit homework",
                        "sessionId": session_id,
                    }
                ),
                json.dumps(
                    {
                        "type": "ai-title",
                        "title": "Homework project",
                        "sessionId": session_id,
                    }
                ),
                json.dumps(
                    {
                        "type": "agent-name",
                        "agentName": "claude",
                        "sessionId": session_id,
                    }
                ),
                json.dumps(
                    {
                        "type": "queue-operation",
                        "operation": "enqueue",
                        "sessionId": session_id,
                    }
                ),
                json.dumps(
                    {
                        "type": "user",
                        "sessionId": session_id,
                        "cwd": str(project_root),
                        "timestamp": "2026-07-23T01:02:03Z",
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", session_id)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

    session = find_claude_session(project_root)

    assert session.path == transcript
    assert session.session_id == session_id


def test_requires_claude_code_session_id(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)

    with pytest.raises(ClaudeSessionError, match="CLAUDE_CODE_SESSION_ID"):
        find_claude_session(tmp_path)


def test_does_not_treat_session_id_as_a_glob_pattern(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "claude"
    _write_transcript(config_dir / "projects" / "workspace" / "active.jsonl", "active", project_root)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "*")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

    with pytest.raises(ClaudeSessionError, match="not found"):
        find_claude_session(project_root)


def test_rejects_session_from_another_project(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    other_project = tmp_path / "other"
    project_root.mkdir()
    other_project.mkdir()
    config_dir = tmp_path / "claude"
    session_id = "wrong-project"
    _write_transcript(config_dir / "projects" / "workspace" / f"{session_id}.jsonl", session_id, other_project)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", session_id)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

    with pytest.raises(ClaudeSessionError, match="does not belong to project"):
        find_claude_session(project_root)


def test_rejects_later_active_record_from_another_project(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path / "project"
    other_project = tmp_path / "other"
    project_root.mkdir()
    other_project.mkdir()
    config_dir = tmp_path / "claude"
    session_id = "mixed-project"
    transcript = config_dir / "projects" / "workspace" / f"{session_id}.jsonl"
    _write_transcript(transcript, session_id, project_root)
    with transcript.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "type": "assistant",
                    "sessionId": session_id,
                    "cwd": str(other_project),
                    "timestamp": "2026-07-23T01:04:03Z",
                }
            )
            + "\n"
        )
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", session_id)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

    with pytest.raises(ClaudeSessionError, match="does not belong to project"):
        find_claude_session(project_root)


def test_rejects_later_active_record_with_missing_metadata(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_dir = tmp_path / "claude"
    session_id = "missing-metadata"
    transcript = config_dir / "projects" / "workspace" / f"{session_id}.jsonl"
    _write_transcript(transcript, session_id, project_root)
    with transcript.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"type": "assistant", "sessionId": session_id}) + "\n")
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", session_id)
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(config_dir))

    with pytest.raises(ClaudeSessionError, match="insufficient metadata"):
        find_claude_session(project_root)


def test_rejects_unsupported_session_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unsupported session source"):
        find_sessions_for_source("other", tmp_path)
