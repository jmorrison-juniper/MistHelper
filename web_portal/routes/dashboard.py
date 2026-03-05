"""Dashboard routes for the MistHelper web portal.

Serves the home dashboard page and health check endpoint.
"""

import os
import time

from flask import Blueprint, current_app, jsonify, render_template

dashboard_bp = Blueprint("dashboard", __name__)

_start_time = time.time()


@dashboard_bp.route("/")
def dashboard():
    """Render the dashboard home page."""
    data_dir = current_app.config.get("DATA_DIR", "data")
    summary = _build_data_summary(data_dir)
    return render_template("dashboard.html", summary=summary)


@dashboard_bp.route("/health")
def health():
    """Return JSON health status for container monitoring."""
    data_dir = current_app.config.get("DATA_DIR", "data")
    file_count = _count_data_files(data_dir)
    uptime = int(time.time() - _start_time)
    return jsonify({
        "status": "healthy",
        "services": {"web_portal": "running"},
        "uptime_seconds": uptime,
        "data_directory": data_dir,
        "data_files_count": file_count,
    })


def _build_data_summary(data_dir: str) -> dict:
    """Build summary statistics for the data directory."""
    file_count = _count_data_files(data_dir)
    recent_files = _get_recent_files(data_dir, limit=5)
    return {
        "file_count": file_count,
        "recent_files": recent_files,
        "data_dir": data_dir,
    }


def _count_data_files(data_dir: str) -> int:
    """Count non-hidden files in the data directory."""
    if not os.path.isdir(data_dir):
        return 0
    count = 0
    for entry in os.scandir(data_dir):
        if not entry.name.startswith(".") and entry.is_file():
            count += 1
    return count


def _get_recent_files(data_dir: str, limit: int = 5) -> list:
    """Return the most recently modified files from data dir."""
    if not os.path.isdir(data_dir):
        return []
    files = []
    for entry in os.scandir(data_dir):
        if entry.name.startswith(".") or not entry.is_file():
            continue
        stat = entry.stat()
        files.append({
            "name": entry.name,
            "size_bytes": stat.st_size,
            "last_modified": stat.st_mtime,
        })
    files.sort(key=lambda f: f["last_modified"], reverse=True)
    return files[:limit]
