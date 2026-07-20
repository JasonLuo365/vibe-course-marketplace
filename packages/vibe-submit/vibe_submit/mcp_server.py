"""MCP server exposing vibe-submit tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .api import ApiError, create_student_group, get_meta, get_report, get_reports, get_status, get_student_profile, join_student_group, upload
from .config import Config, ConfigError, load_config
from .outbox import get_outbox, list_outbox, remove_outbox, retry_config, save_outbox
from .preview import PreviewError, create_preview, load_preview, preview_contents, resolve_project_root

mcp = FastMCP("vibe-submit")


def _load_cfg() -> Config:
    """Load global configuration for MCP tool use.

    Project-level server_url differences are rejected in MCP mode; users must
    confirm those via the CLI.
    """
    return load_config()


def _error_dict(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


# ---------------------------------------------------------------------------
# Internal implementation functions (shared with tests / thin MCP wrappers)
# ---------------------------------------------------------------------------


def get_assignment_meta_impl(cfg: Config, assignment_code: str) -> dict[str, Any]:
    """Return assignment metadata from the server."""
    try:
        result = get_meta(cfg, assignment_code)
    except ApiError as exc:
        return _error_dict(exc.code, exc.message)
    return {"ok": True, "meta": result}


def get_submission_status_impl(cfg: Config, assignment_code: str) -> dict[str, Any]:
    """Return the latest submission status for an assignment."""
    try:
        result = get_status(cfg, assignment_code)
    except ApiError as exc:
        return _error_dict(exc.code, exc.message)
    return {"ok": True, "status": result}


def get_feedback_reports_impl(cfg: Config) -> dict[str, Any]:
    try:
        return {"ok": True, "reports": get_reports(cfg).get("reports", [])}
    except ApiError as exc:
        return _error_dict(exc.code, exc.message)


def get_feedback_report_impl(cfg: Config, assignment_code: str) -> dict[str, Any]:
    try:
        return {"ok": True, "report": get_report(cfg, assignment_code)}
    except ApiError as exc:
        return _error_dict(exc.code, exc.message)


def get_group_status_impl(cfg: Config) -> dict[str, Any]:
    try:
        return {"ok": True, "profile": get_student_profile(cfg)}
    except ApiError as exc:
        return _error_dict(exc.code, exc.message)


def create_group_impl(cfg: Config, group_name: str) -> dict[str, Any]:
    try:
        return {"ok": True, "group": create_student_group(cfg, group_name)}
    except ApiError as exc:
        return _error_dict(exc.code, exc.message)


def join_group_impl(cfg: Config, join_code: str) -> dict[str, Any]:
    try:
        return {"ok": True, "profile": join_student_group(cfg, join_code)}
    except ApiError as exc:
        return _error_dict(exc.code, exc.message)


def preview_submission_impl(
    cfg: Config,
    assignment_code: str,
    project_root: str | None = None,
) -> dict[str, Any]:
    """Create a submission preview and return its summary."""
    try:
        return create_preview(cfg, assignment_code, project_root)
    except ApiError as exc:
        return _error_dict(exc.code, exc.message)
    except Exception as exc:
        return _error_dict("PREVIEW_FAILED", str(exc))


def preview_contents_impl(preview_id: str, path: str | None = None) -> dict[str, Any]:
    try:
        return preview_contents(preview_id, path)
    except PreviewError as exc:
        return _error_dict(exc.code, exc.message)


def submit_homework_impl(
    preview_id: str,
    confirmed: bool,
    force_confirmed: bool = False,
    project_root: str | None = None,
    cfg: Config | None = None,
) -> dict[str, Any]:
    """Submit the package referenced by a preview record."""
    try:
        preview = load_preview(preview_id)
    except PreviewError as exc:
        return _error_dict(exc.code, exc.message)

    if project_root is not None:
        canonical = resolve_project_root(project_root)
        if canonical != preview.project_root:
            return _error_dict(
                "PREVIEW_INVALID",
                "project_root does not match the preview binding",
            )

    if confirmed is not True:
        return _error_dict(
            "CONFIRMATION_REQUIRED",
            "submission must be explicitly confirmed by setting confirmed=True",
        )

    if cfg is None:
        try:
            cfg = _load_cfg()
        except ConfigError as exc:
            return _error_dict("CONFIG_ERROR", str(exc))

    try:
        result = upload(cfg, preview.zip_path, preview.manifest, force=False)
    except ApiError as exc:
        if exc.status == 409:
            if force_confirmed is not True:
                return _error_dict("FORCE_REQUIRED", exc.message)
            try:
                result = upload(cfg, preview.zip_path, preview.manifest, force=True)
            except ApiError as retry_exc:
                return _error_dict(retry_exc.code, retry_exc.message)
        elif exc.status == 0 or exc.status >= 500:
            outbox_id = save_outbox(preview.zip_path, preview.manifest, cfg)
            result = _error_dict(exc.code, exc.message)
            result["outbox_id"] = outbox_id
            return result
        else:
            return _error_dict(exc.code, exc.message)

    return {"ok": True, "submission": result}


def retry_submission_impl(
    cfg: Config,
    outbox_id: str | None = None,
    assignment_code: str | None = None,
) -> dict[str, Any]:
    """Retry an outbox submission, or list outbox entries when no id is given."""
    if outbox_id is None and assignment_code is None:
        return {"ok": True, "outbox": list_outbox()}

    if outbox_id is not None:
        try:
            zip_path, manifest = get_outbox(outbox_id)
        except Exception as exc:
            return _error_dict("OUTBOX_NOT_FOUND", str(exc))
        try:
            upload_cfg = retry_config(outbox_id, cfg)
        except Exception as exc:
            return _error_dict("OUTBOX_ERROR", str(exc))
        return _upload_outbox(upload_cfg, zip_path, manifest, outbox_id)

    # assignment_code given: find a single matching entry.
    entries = [
        e for e in list_outbox() if e.get("assignment_code") == assignment_code
    ]
    if len(entries) == 0:
        return _error_dict(
            "OUTBOX_NOT_FOUND",
            f"no outbox entry for assignment {assignment_code}",
        )
    if len(entries) > 1:
        return _error_dict(
            "AMBIGUOUS_OUTBOX",
            f"multiple outbox entries for assignment {assignment_code}",
        )

    outbox_id = entries[0]["id"]
    try:
        zip_path, manifest = get_outbox(outbox_id)
    except Exception as exc:
        return _error_dict("OUTBOX_NOT_FOUND", str(exc))
    try:
        upload_cfg = retry_config(outbox_id, cfg)
    except Exception as exc:
        return _error_dict("OUTBOX_ERROR", str(exc))
    return _upload_outbox(upload_cfg, zip_path, manifest, outbox_id)


def _upload_outbox(
    cfg: Config, zip_path: Path, manifest: dict[str, Any], outbox_id: str
) -> dict[str, Any]:
    """Upload an outbox package using the supplied configuration."""
    try:
        result = upload(cfg, zip_path, manifest, force=False)
    except ApiError as exc:
        return _error_dict(exc.code, exc.message)

    try:
        remove_outbox(outbox_id)
    except Exception as exc:
        return _error_dict("OUTBOX_CLEANUP_FAILED", str(exc))

    return {"ok": True, "submission": result}


# ---------------------------------------------------------------------------
# MCP tool wrappers
# ---------------------------------------------------------------------------


@mcp.tool()
def get_assignment_meta(assignment_code: str) -> dict[str, Any]:
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return get_assignment_meta_impl(cfg, assignment_code)


@mcp.tool()
def preview_submission(assignment_code: str, project_root: str | None = None) -> dict[str, Any]:
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return preview_submission_impl(cfg, assignment_code, project_root)


@mcp.tool()
def get_preview_contents(preview_id: str, path: str | None = None) -> dict[str, Any]:
    return preview_contents_impl(preview_id, path)


@mcp.tool()
def submit_homework(
    preview_id: str,
    confirmed: bool,
    force_confirmed: bool = False,
    project_root: str | None = None,
) -> dict[str, Any]:
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return submit_homework_impl(
        preview_id,
        confirmed,
        force_confirmed=force_confirmed,
        project_root=project_root,
        cfg=cfg,
    )


@mcp.tool()
def retry_submission(
    outbox_id: str | None = None,
    assignment_code: str | None = None,
) -> dict[str, Any]:
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return retry_submission_impl(cfg, outbox_id, assignment_code)


@mcp.tool()
def get_submission_status(assignment_code: str) -> dict[str, Any]:
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return get_submission_status_impl(cfg, assignment_code)


@mcp.tool()
def get_feedback_reports() -> dict[str, Any]:
    """查看自己全部作业的评估反馈发布状态和已发布成绩。"""
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return get_feedback_reports_impl(cfg)


@mcp.tool()
def get_feedback_report(assignment_code: str) -> dict[str, Any]:
    """查看一份作业的个人报告和已发布小组报告。"""
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return get_feedback_report_impl(cfg, assignment_code)


@mcp.tool()
def get_group_status() -> dict[str, Any]:
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return get_group_status_impl(cfg)


@mcp.tool()
def create_group(group_name: str) -> dict[str, Any]:
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return create_group_impl(cfg, group_name)


@mcp.tool()
def join_group(join_code: str) -> dict[str, Any]:
    try:
        cfg = _load_cfg()
    except ConfigError as exc:
        return _error_dict("CONFIG_ERROR", str(exc))
    return join_group_impl(cfg, join_code)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

