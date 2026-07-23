# Claude Code Submission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide a provider-neutral setup flow and a Claude Code `/submit-homework` command that uploads the current Claude terminal session alongside normal coursework files.

**Architecture:** `vibe-submit` remains the only packager and HTTP client. A strict Claude session adapter feeds the existing persistent preview workflow; a Claude project Skill only invokes the CLI, displays the preview, and waits for confirmation. The upgraded password-authenticated service is reused unchanged.

**Tech Stack:** Python, argparse, pytest, httpx, Claude Code Skills, FastAPI/SQLite.

---

## File map

- `packages/vibe-submit/vibe_submit/claude_sessions.py`: strict active-Claude-transcript lookup.
- `packages/vibe-submit/vibe_submit/sessions.py`: existing Codex collector plus source dispatch.
- `packages/vibe-submit/vibe_submit/preview.py`: source-aware stored previews.
- `packages/vibe-submit/vibe_submit/package.py`: session-source manifest metadata.
- `packages/vibe-submit/vibe_submit/cli.py`: new CLI entry points.
- `packages/vibe-submit/vibe_submit/bootstrap.py`: shared `setup` behavior.
- `packages/vibe-submit/tests/test_claude_sessions.py`, `test_preview_cli.py`, `test_setup.py`: coverage.
- `plugins/claude-code/skills/submit-homework/SKILL.md`: Claude Code command.
- `README.md`: installation and usage.

### Task 1: Strict Claude session adapter

**Files:** Create `packages/vibe-submit/vibe_submit/claude_sessions.py`; modify `packages/vibe-submit/vibe_submit/sessions.py`; create `packages/vibe-submit/tests/test_claude_sessions.py`.

- [ ] **Step 1: Write failing tests for exact-session selection.**

```python
def test_finds_exact_active_session(tmp_path):
    project = tmp_path / "project"; project.mkdir()
    config = tmp_path / ".claude"
    write_transcript(config / "projects" / "project" / "active.jsonl", "active", project)
    write_transcript(config / "projects" / "project" / "old.jsonl", "old", project)
    found = find_current_claude_session(project, {"CLAUDE_CODE_SESSION_ID": "active", "CLAUDE_CONFIG_DIR": str(config)})
    assert found.session_id == "active"
    assert found.path.name == "active.jsonl"


def test_rejects_missing_or_other_project_session(tmp_path):
    with pytest.raises(ClaudeSessionError, match="CLAUDE_CODE_SESSION_ID"):
        find_current_claude_session(tmp_path, {})
```

- [ ] **Step 2: Run `Set-Location packages/vibe-submit; pytest tests/test_claude_sessions.py -v`.** Expected: collection fails because `claude_sessions` is absent.

- [ ] **Step 3: Implement the lookup.** Read `CLAUDE_CODE_SESSION_ID`; search only `$CLAUDE_CONFIG_DIR/projects/**/<id>.jsonl`; scan that file for matching `sessionId`, `cwd`, and `timestamp`; reject missing, duplicate, malformed, or non-current-project records. Return existing `SessionInfo`. Add `find_sessions_for_source(source, project_root, since=None)` that routes `codex` to the current collector and `claude` to a one-element list containing this lookup.

```python
def find_sessions_for_source(source: str, project_root: Path, since: datetime | None = None) -> list[SessionInfo]:
    if source == "codex":
        return find_sessions(_codex_home(), project_root, since)
    if source == "claude":
        return [find_current_claude_session(project_root)]
    raise ValueError(f"unsupported session source: {source}")
```

- [ ] **Step 4: Run the focused tests.** `Set-Location packages/vibe-submit; pytest tests/test_claude_sessions.py -v` — Expected: PASS.
- [ ] **Step 5: Commit.** `git add packages/vibe-submit/vibe_submit/sessions.py packages/vibe-submit/vibe_submit/claude_sessions.py packages/vibe-submit/tests/test_claude_sessions.py; git commit -m "feat: add strict Claude Code session discovery"`

### Task 2: Source-aware persistent previews and CLI commands

**Files:** Modify `packages/vibe-submit/vibe_submit/preview.py`, `package.py`, and `cli.py`; create `packages/vibe-submit/tests/test_preview_cli.py`.

- [ ] **Step 1: Write failing tests.** Assert `create_preview(..., session_source="claude")` packages exactly one fixture transcript and writes `"session_source": "claude_code"` to `manifest.json`. Test `_cmd_submit_preview` loads a saved preview and calls `upload` with that exact saved ZIP; a network `ApiError` must call `save_outbox` with that same ZIP.

```python
record = SimpleNamespace(zip_path=tmp_path / "fixed.zip", manifest={"assignment_code": "HW01"}, project_root=str(tmp_path))
record.zip_path.write_bytes(b"fixed")
monkeypatch.setattr(cli, "load_preview", lambda _: record)
monkeypatch.setattr(cli, "upload", lambda *args, **kwargs: {"submission_id": 7, "attempt_no": 1})
assert cli._cmd_submit_preview(SimpleNamespace(preview_id="p1", force=False)) == 0
```

- [ ] **Step 2: Run `Set-Location packages/vibe-submit; pytest tests/test_preview_cli.py -v`.** Expected: FAIL because the source argument and command do not exist.

- [ ] **Step 3: Implement.** Add `session_source: str = "codex"` to `create_preview`; use `find_sessions_for_source`; preserve `session_source` in package metadata and manifest. Add `_cmd_preview` and `_cmd_submit_preview` that use `create_preview`, `load_preview`, `upload`, and existing outbox rules without rebuilding a package. Register parsers exactly as follows.

```python
preview_parser = sub.add_parser("preview")
preview_parser.add_argument("--code", required=True)
preview_parser.add_argument("--project", default=".")
preview_parser.add_argument("--session-source", choices=["codex", "claude"], default="codex")
submit_preview_parser = sub.add_parser("submit-preview")
submit_preview_parser.add_argument("--preview-id", required=True)
submit_preview_parser.add_argument("--force", action="store_true")
```

- [ ] **Step 4: Run `Set-Location packages/vibe-submit; pytest tests/test_claude_sessions.py tests/test_preview_cli.py -v`.** Expected: PASS, including saved-ZIP outbox behavior.
- [ ] **Step 5: Commit.** `git add packages/vibe-submit/vibe_submit/preview.py packages/vibe-submit/vibe_submit/package.py packages/vibe-submit/vibe_submit/cli.py packages/vibe-submit/tests/test_preview_cli.py; git commit -m "feat: add Claude-aware preview submission commands"`

### Task 3: Provider-neutral setup and Claude Skill

**Files:** Modify `packages/vibe-submit/vibe_submit/bootstrap.py` and `cli.py`; create `packages/vibe-submit/tests/test_setup.py` and `plugins/claude-code/skills/submit-homework/SKILL.md`; modify `README.md`.

- [ ] **Step 1: Write a failing setup test.** Patch `register_student` and `_run_doctor`, invoke `_cmd_setup` with server, course code, student number, name, and matching password, then assert config exists under `VIBE_SUBMIT_HOME/.vibe-submit/config.toml` and no marketplace helper is called.
- [ ] **Step 2: Run `Set-Location packages/vibe-submit; pytest tests/test_setup.py -v`.** Expected: FAIL because `_cmd_setup` is absent.
- [ ] **Step 3: Extract setup from bootstrap.** Implement `_cmd_setup` by calling existing `_configure(...)` and `_run_doctor()`. Keep `bootstrap` responsible for `uv` and Codex Marketplace registration before delegating to `_cmd_setup`. Add a `setup` parser with `--student-no`, `--name`, `--course-code`, `--password`, `--password-confirm`, and `--server`; it must not require `--marketplace-url`.

```python
def _cmd_setup(args: argparse.Namespace) -> int:
    ok = _configure(args.student_no, args.password, args.server, args.name, args.course_code, args.password_confirm)
    return 0 if ok and _run_doctor() == 0 else 1
```

- [ ] **Step 4: Create the Claude project Skill.** Include this frontmatter and instructions to preview, show raw-session warning and summary, wait for explicit user confirmation, then upload the returned preview ID. On a missing CLI/config, point to README and `vibe-submit setup`; never ask for or store passwords in chat.

```markdown
---
name: submit-homework
description: Preview and submit coursework from the current Claude Code terminal session.
disable-model-invocation: true
argument-hint: <assignment-code>
---

Run `vibe-submit preview --code $ARGUMENTS --session-source claude --project .`.
Only after explicit confirmation, run `vibe-submit submit-preview --preview-id <preview_id> --yes`.
```

- [ ] **Step 5: Update README and test.** Add manual install command `uv tool install "git+https://github.com/JasonLuo365/vibe-course-marketplace.git@ZM#subdirectory=packages/vibe-submit"`, then `vibe-submit setup` and `/submit-homework HW01`; document local-terminal-only support. Run `Set-Location packages/vibe-submit; pytest -v; python -m vibe_submit.cli --help`. Expected: tests pass and help lists `setup`, `preview`, and `submit-preview`.
- [ ] **Step 6: Commit.** `git add packages/vibe-submit/vibe_submit/bootstrap.py packages/vibe-submit/vibe_submit/cli.py packages/vibe-submit/tests/test_setup.py plugins/claude-code/skills/submit-homework/SKILL.md README.md; git commit -m "feat: add Claude Code homework submission workflow"`

### Task 4: Verify the upgraded local service

**Files:** Test `packages/vibe-submit/tests/test_preview_cli.py`; test `C:/Users/Lenovo/Desktop/vibe-course-platform-git/server/tests/test_self_registration_groups.py` and `test_student_reports.py`.

- [ ] **Step 1: Add a client-to-server smoke test.** Create a temporary SQLite `create_app` instance, seed one course enrollment code, call `register_student`, construct a Claude-source preview fixture, and post it to `/api/submissions`; assert 201 and that stored `manifest.json` has `session_source == "claude_code"`.
- [ ] **Step 2: Run all relevant tests.** `Set-Location packages/vibe-submit; pytest -v` and `Set-Location C:/Users/Lenovo/Desktop/vibe-course-platform-git/server; .\.venv\Scripts\python.exe -m pytest tests/test_self_registration_groups.py tests/test_student_reports.py -v`. Expected: both commands PASS.
- [ ] **Step 3: Commit.** `git add packages/vibe-submit/tests/test_preview_cli.py; git commit -m "test: verify Claude upload with password server"`

## Final verification

- [ ] Confirm `git status --short` has no unintended marketplace changes.
- [ ] In local Claude Code, run `/submit-homework <assignment-code>`, cancel once, then confirm once; verify exactly one current-session JSONL is previewed and one package reaches the service.
