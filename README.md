# Vibe Course Marketplace

This repository distributes the `vibe-submit` Codex plugin and its Python
client. The plugin installs its client directly from a fixed GitHub tag, so it
does not depend on PyPI being available.

## Version mapping

| Plugin version | Client version | Git tag |
| --- | --- | --- |
| 0.1.8 | 0.1.8 | `v0.1.8` |
| 0.1.7 | 0.1.7 | `v0.1.7` |
| 0.1.6 | 0.1.6 | `v0.1.6` |
| 0.1.5 | 0.1.5 | `v0.1.5` |

Do not overwrite a tag that has been given to students. Publish a new version
and a new immutable tag for every classroom release.

## Validate the GitHub distribution

From a machine that has not previously installed the client:

```powershell
uvx --from "git+https://github.com/JasonLuo365/vibe-course-marketplace.git@v0.1.8#subdirectory=packages/vibe-submit" vibe-submit --help
```

PyPI may later be used as an additional package-distribution channel, but the
Marketplace configuration should continue to use the reviewed GitHub release.

## Claude Code local-terminal setup

Claude Code is supported only in a local terminal session. For classroom use,
distribute a reviewed, immutable release package that installs both the
`vibe-submit` command and the user-level `/submit-homework` Skill. Do not give
students the mutable `ZM` branch as an installation source.

See [the student Claude Code guide](docs/学生使用 Claude Code 提交作业.md) for the
student workflow, and [the launch checklist](docs/上线前检查清单.md) before
releasing a new client version.


