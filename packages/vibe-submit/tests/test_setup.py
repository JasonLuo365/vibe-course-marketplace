import argparse
from pathlib import Path


def test_setup_registers_and_writes_config_without_marketplace_registration(
    monkeypatch, tmp_path: Path
) -> None:
    from vibe_submit import bootstrap

    monkeypatch.setenv("VIBE_SUBMIT_HOME", str(tmp_path / "home"))
    registered = {}
    monkeypatch.setattr(
        bootstrap,
        "register_student",
        lambda server, course, student, name, password, confirm: registered.update(
            server=server,
            course=course,
            student=student,
            name=name,
            password=password,
            confirm=confirm,
        ),
    )
    monkeypatch.setattr(bootstrap, "_run_doctor", lambda: 0)
    monkeypatch.setattr(
        bootstrap,
        "_register_marketplace",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("setup must not register a marketplace")),
    )

    result = bootstrap._cmd_setup(
        argparse.Namespace(
            server="https://class.example",
            course_code="COURSE1",
            student_no="s123",
            name="Ada",
            password="secret",
            password_confirm="secret",
        )
    )

    assert result == 0
    assert registered == {
        "server": "https://class.example",
        "course": "COURSE1",
        "student": "s123",
        "name": "Ada",
        "password": "secret",
        "confirm": "secret",
    }
    config_path = tmp_path / "home" / ".vibe-submit" / "config.toml"
    assert config_path.exists()
    assert 'student_no = "s123"' in config_path.read_text(encoding="utf-8")


def test_setup_and_confirmed_preview_submission_are_registered_cli_commands() -> None:
    from vibe_submit.cli import _build_parser

    parser = _build_parser()
    setup_args = parser.parse_args(["setup", "--server", "https://class.example"])
    submit_args = parser.parse_args(
        ["submit-preview", "--preview-id", "preview-1", "--yes"]
    )

    assert setup_args.command == "setup"
    assert submit_args.yes is True
