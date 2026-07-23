"""Package building for submission."""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .collect import FileEntry
from .sessions import SessionInfo, session_index


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _section_relpath(relpath: str, section: str) -> str:
    """Remove the project-level section folder from an archived entry."""
    normalized = relpath.replace("\\", "/")
    prefix = f"{section}/"
    return normalized[len(prefix):] if normalized.startswith(prefix) else normalized


def build_package(
    root: Path,
    sessions: list[SessionInfo],
    code_files: list[FileEntry],
    screenshots: list[FileEntry],
    meta: dict[str, Any],
    dest: Path,
    reports: list[FileEntry] | None = None,
) -> tuple[Path, dict, dict]:
    """Build a submission zip and return ``(zip_path, manifest, stats)``.

    The zip contains ``manifest.json``, ``sessions_index.json``,
    ``sessions/{id}.jsonl``, ``code/{relpath}``, ``screenshots/{relpath}``
    and ``report/{relpath}``.
    The manifest lists every archived file with its SHA-256 digest.
    """
    root = Path(root).resolve()
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)

    assignment_code = meta["assignment_code"]
    student_no = meta["student_no"]
    client_version = meta.get("client_version", "0.1.0")
    session_source = meta.get("session_source", "codex")
    submitted_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    zip_path = dest / f"vibe-submit-{assignment_code}-{student_no}.zip"
    if zip_path.exists():
        zip_path.unlink()

    manifest_files: list[dict[str, str]] = []
    session_index_data: dict[str, dict] = {}
    stats_files = 0
    stats_bytes = 0
    reports = reports or []

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Sessions
        for session in sessions:
            data = session.path.read_bytes()
            arcname = f"sessions/{session.session_id}.jsonl"
            zf.writestr(arcname, data)
            manifest_files.append({"path": arcname, "sha256": _sha256(data)})
            session_index_data[session.session_id] = session_index(session.path)

        # Code files
        for entry in code_files:
            data = entry.abspath.read_bytes()
            arcname = f"code/{entry.relpath}"
            zf.writestr(arcname, data)
            manifest_files.append({"path": arcname, "sha256": _sha256(data)})
            stats_files += 1
            stats_bytes += entry.size

        # Screenshots
        for entry in screenshots:
            data = entry.abspath.read_bytes()
            arcname = f"screenshots/{_section_relpath(entry.relpath, 'screenshots')}"
            zf.writestr(arcname, data)
            manifest_files.append({"path": arcname, "sha256": _sha256(data)})
            stats_files += 1
            stats_bytes += entry.size

        # Final report files are a separate teacher-facing deliverable.
        for entry in reports:
            data = entry.abspath.read_bytes()
            arcname = f"report/{_section_relpath(entry.relpath, 'report')}"
            zf.writestr(arcname, data)
            manifest_files.append({"path": arcname, "sha256": _sha256(data)})
            stats_files += 1
            stats_bytes += entry.size

        # Sessions index
        index_json = json.dumps(session_index_data, ensure_ascii=False, indent=2)
        index_bytes = index_json.encode("utf-8")
        zf.writestr("sessions_index.json", index_bytes)
        manifest_files.append(
            {"path": "sessions_index.json", "sha256": _sha256(index_bytes)}
        )

        # Manifest
        manifest = {
            "format_version": "1",
            "assignment_code": assignment_code,
            "student_no": student_no,
            "client_version": client_version,
            "session_source": session_source,
            "submitted_at": submitted_at,
            "files": manifest_files,
            "stats": {
                "sessions": len(sessions),
                "files": stats_files,
                "reports": len(reports),
                "bytes": stats_bytes,
            },
        }
        manifest_bytes = json.dumps(
            manifest, ensure_ascii=False, indent=2
        ).encode("utf-8")
        zf.writestr("manifest.json", manifest_bytes)

    return zip_path, manifest, manifest["stats"]


