---
name: submit-homework
description: Preview and submit coursework from the current Claude Code terminal session.
disable-model-invocation: true
argument-hint: <assignment-code>
---

Use this skill only from a local Claude Code terminal session. Do not use it in
Claude Code web or cloud environments.

First verify that `vibe-submit` is installed and configured. If either is
missing, direct the student to the repository README, where they can install
the CLI and run `vibe-submit setup`. Never ask for, receive, or store a
password in chat.

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
