# Changelog

## v0.1.8

- Adds Claude Code current-session submission through `/submit-homework`.
- Adds strict Claude transcript compatibility for current terminal metadata.
- Requires `--yes` before a stored preview can be uploaded.
- Adds a PowerShell installer that installs the Claude Skill and preconfigures the production service.

## v0.1.7

- Falls back to the desktop Marketplace configuration when a stale or broken Windows `codex` command is found on `PATH`.

## v0.1.6

- Replaces student submit tokens with password-based registration and HTTP Basic authentication.
- Requests the password twice during bootstrap and stores it in the local client configuration.
- Keeps Marketplace registration working when Codex CLI is unavailable by using the existing desktop configuration fallback.

## v0.1.5

- Adds a dedicated `report/` directory to student submission packages.
- Shows final-report files separately in the pre-submission preview.

## v0.1.3

- Adds self-registration during bootstrap with a course invitation code,
  student number, and name.
- Adds fixed-group tools: create a group, join with a six-character code, and
  inspect current group status.

## v0.1.2

- Adds a clean, immutable release for the safe preview workflow.
- Lets a student inspect the collected code tree, screenshots, and individual
  session prompt/final-answer pairs before confirming an upload.
- Keeps internal tool output and reasoning out of preview responses.

## v0.1.1

- Introduced safe submission-content preview support.
