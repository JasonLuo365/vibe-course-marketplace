---
name: "submit-homework"
description: "Preview and submit a Vibe Coding coursework package with the installed vibe-submit MCP tools."
---

# Submit Vibe Coding homework

Use the Vibe submission tools to preview the current coursework package before
sending it. First call `preview_submission`, then `get_preview_contents` with
no path to show the code tree, session list, screenshots, and exclusions. On
request use `code/<path>` or `session:<id>` to expand content. Sessions must
show only prompts and final answers, never tool output or internal reasoning.
Ask the student for confirmation only after the preview.

After explicit confirmation, submit the package with the assignment code supplied
by the student. Never ask the student to paste a server token into the chat, and
never expose tokens in responses.

If the upload cannot reach the server, explain that the submission has been
queued locally and guide the student to retry when their network is available.

## 查看评估反馈

当学生询问成绩、评估或改进建议时，调用 `get_feedback_reports` 查看发布状态；若学生指定作业码，再调用 `get_feedback_report`。报告可包含个人报告和所在小组的报告。仅解释已发布内容；对 `evaluating`、`pending` 或 `awaiting_publication` 状态，不得猜测或泄露草稿分数。

## Fixed groups

When a student asks about groups, call `get_group_status` first. A student
without a group can call `create_group` with a display name and share the
returned join code with teammates. Other students use `join_group`. If groups
are locked, direct the student to their teacher.
