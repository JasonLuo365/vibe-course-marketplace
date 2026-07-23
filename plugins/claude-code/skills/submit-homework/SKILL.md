---
name: submit-homework
description: Preview and submit coursework from the current Claude Code terminal session.
disable-model-invocation: true
argument-hint: <assignment-code>
---

Use this skill only from a local Claude Code terminal session. Do not use it in
Claude Code web or cloud environments.

First verify that `vibe-submit` is installed and configured. If the command is
missing, tell the student to install the course submission client from the
official course distribution, then start a new Claude Code terminal session.

If the client is installed but not yet configured, tell the student to run this
one-time command in their local terminal:

```sh
vibe-submit setup
```

The terminal registration flow collects the course invitation code, student
number, name, and password locally. Do not ask for, receive, or store any
registration details or password in chat. Once it succeeds, ask the student to
run `/submit-homework <assignment-code>` again.

Run:

```sh
vibe-submit preview --code $ARGUMENTS --session-source claude --project .
```

Show the returned preview summary, including the session, code files,
screenshots, reports, and package size. Clearly warn that the current Claude
Code session transcript is included in the package as raw content.

Wait for an explicit confirmation from the student. Do not upload after an
ambiguous response, and do not interpret silence as confirmation. If the
student cancels, explain that nothing was uploaded and the preview will expire.

Only after explicit confirmation, run:

```sh
vibe-submit submit-preview --preview-id <preview_id> --yes
```

Report the result. For conflicts, explain the conflict and offer the CLI's
`--force` option only if the student explicitly requests replacement. For
network or server failures, tell the student how to retry the saved outbox
submission.
