"""Data browser routes for the MistHelper web portal.

Provides file listing, CSV/SQLite preview with pagination,
and file download endpoints.
"""

from flask import Blueprint, current_app, jsonify, render_template, request, send_file

data_bp = Blueprint("data", __name__)


@data_bp.route("/data")
def data_browser():
    """Render the data browser page."""
    sort_by = request.args.get("sort", "modified")
    order = request.args.get("order", "desc")
    return render_template(
        "data_browser.html",
        sort_by=sort_by,
        order=order,
    )


@data_bp.route("/api/data/files")
def list_files():
    """Return JSON list of all data files with metadata."""
    from web_portal.services.data_browser import DataBrowserService
    data_dir = current_app.config.get("DATA_DIR", "data")
    service = DataBrowserService(data_dir)
    files = service.list_files()
    return jsonify({"files": files, "total_count": len(files)})


@data_bp.route("/api/data/preview/<path:filepath>")
def preview_file(filepath):
    """Return paginated preview of a CSV or SQLite table list."""
    from web_portal.services.data_browser import DataBrowserService
    data_dir = current_app.config.get("DATA_DIR", "data")
    service = DataBrowserService(data_dir)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    per_page = min(per_page, 200)
    search = request.args.get("search", "")
    result = service.preview_file(filepath, page, per_page, search)
    if "error" in result:
        status = 404 if "not found" in result["error"].lower() else 400
        return jsonify(result), status
    return jsonify(result)


@data_bp.route("/api/data/preview/<path:filepath>/<table_name>")
def preview_table(filepath, table_name):
    """Return paginated preview of a specific SQLite table."""
    from web_portal.services.data_browser import DataBrowserService
    data_dir = current_app.config.get("DATA_DIR", "data")
    service = DataBrowserService(data_dir)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    per_page = min(per_page, 200)
    search = request.args.get("search", "")
    result = service.preview_sqlite_table(filepath, table_name, page, per_page, search)
    if "error" in result:
        status = 404 if "not found" in result["error"].lower() else 400
        return jsonify(result), status
    return jsonify(result)


@data_bp.route("/api/data/download/<path:filepath>")
def download_file(filepath):
    """Download a file from the data directory."""
    from web_portal.services.data_browser import DataBrowserService
    data_dir = current_app.config.get("DATA_DIR", "data")
    service = DataBrowserService(data_dir)
    resolved = service.resolve_safe_path(filepath)
    if resolved is None:
        return jsonify({"error": "File not found"}), 404
    return send_file(resolved, as_attachment=True)
