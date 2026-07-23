import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from vibe_submit.config import Config
from vibe_submit.errors import ApiError
from vibe_submit.sessions import SessionInfo


def test_claude_preview_uses_one_source_session_and_records_manifest_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from vibe_submit import preview

    project = tmp_path / "project"
    project.mkdir()
    (project / "main.py").write_text("print('hello')\n", encoding="utf-8")
    transcript = tmp_path / "claude-session.jsonl"
    transcript.write_text("{}\n", encoding="utf-8")
    session = SessionInfo(transcript, "claude-session", str(project), datetime.now(timezone.utc))
    captured_source = []
    monkeypatch.setenv("VIBE_SUBMIT_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(preview, "get_meta", lambda *_: {})
    monkeypatch.setattr(
        preview,
        "find_sessions_for_source",
        lambda source, root, since: captured_source.append(source) or [session],
    )

    result = preview.create_preview(
        Config("https://class.example", "s1", "secret", "global"),
        "HW1",
        project,
        session_source="claude",
    )
    record = preview.load_preview(result["preview"]["preview_id"])

    assert result["preview"]["sessions"] == [preview.session_index(transcript)]
    assert captured_source == ["claude"]
    assert record.manifest["session_source"] == "claude_code"


def test_submit_preview_uploads_the_exact_persisted_zip_and_manifest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from vibe_submit import cli
    from vibe_submit.preview import PreviewRecord

    zip_path = tmp_path / "saved.zip"
    zip_path.write_bytes(b"stored package")
    manifest = {"assignment_code": "HW1", "session_source": "claude_code"}
    record = PreviewRecord("p1", str(tmp_path), "f", datetime.now(timezone.utc), datetime.now(timezone.utc), zip_path, manifest, [], 0, 0, 0, 0, [])
    captured = {}
    monkeypatch.setattr(cli, "load_config", lambda: Config("https://class.example", "s1", "secret", "global"))
    monkeypatch.setattr(cli, "load_preview", lambda preview_id: record)
    monkeypatch.setattr(cli, "upload", lambda cfg, actual_zip, actual_manifest, force: captured.update(zip=actual_zip, manifest=actual_manifest, force=force) or {"submission_id": "sub", "attempt_no": 1})

    assert cli._cmd_submit_preview(argparse.Namespace(preview_id="p1", force=True)) == 0
    assert captured == {"zip": zip_path, "manifest": manifest, "force": True}


def test_submit_preview_saves_the_same_zip_to_outbox_on_network_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from vibe_submit import cli
    from vibe_submit.preview import PreviewRecord

    zip_path = tmp_path / "saved.zip"
    zip_path.write_bytes(b"stored package")
    manifest = {"assignment_code": "HW1"}
    record = PreviewRecord("p1", str(tmp_path), "f", datetime.now(timezone.utc), datetime.now(timezone.utc), zip_path, manifest, [], 0, 0, 0, 0, [])
    captured = {}
    monkeypatch.setattr(cli, "load_config", lambda: Config("https://class.example", "s1", "secret", "global"))
    monkeypatch.setattr(cli, "load_preview", lambda preview_id: record)
    monkeypatch.setattr(cli, "upload", lambda *_args, **_kwargs: (_ for _ in ()).throw(ApiError(0, "NETWORK", "offline", None)))
    monkeypatch.setattr(cli, "save_outbox", lambda actual_zip, actual_manifest, cfg: captured.update(zip=actual_zip, manifest=actual_manifest, cfg=cfg) or "outbox-1")

    assert cli._cmd_submit_preview(argparse.Namespace(preview_id="p1", force=False)) == 1
    assert captured["zip"] == zip_path
    assert captured["manifest"] is manifest


def test_preview_claude_without_active_session_returns_clear_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from vibe_submit import cli, preview

    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.setattr(cli, "load_config", lambda *_args, **_kwargs: Config("https://class.example", "s1", "secret", "global"))
    monkeypatch.setattr(preview, "get_meta", lambda *_: {})

    assert cli._cmd_preview(
        argparse.Namespace(code="HW1", project=str(project), session_source="claude")
    ) == 1
    assert "CLAUDE_CODE_SESSION_ID" in capsys.readouterr().err
