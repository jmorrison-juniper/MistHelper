"""Data browser routes for the MistHelper web portal.

Provides file listing, CSV/SQLite preview with pagination,
and file download endpoints.
"""

from __future__ import annotations

from pathlib import PurePosixPath  # HTTP paths use forward slashes on every supported platform.
from typing import TYPE_CHECKING

from flask import Blueprint, Response, current_app, jsonify, render_template, request, send_file

if TYPE_CHECKING:
    from web_portal.services.data_browser import DataBrowserService
    from web_portal.services.row_sorter import SortSpec


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
def preview_file(filepath: str) -> Response | tuple[Response, int]:  # Use one matcher for files and tables.
    """Preview a complete file path or an explicit SQLite file-and-table path."""
    from web_portal.services.data_browser import DataBrowserService  # Retain the existing file-access guard.
    from web_portal.services.row_sorter import SortSpec  # Preserve the existing optional CSV order.

    data_dir = current_app.config.get("DATA_DIR", "data")  # Keep the configured output boundary.
    service = DataBrowserService(data_dir)  # Apply the same safe-path checks as downloads.
    database_path, _, table_name = filepath.rpartition("/")  # Split only for an explicit SQLite table selection.
    if (  # A directory with a database suffix must still permit nested file previews.
        table_name  # Require an explicit nonempty table selection.
        and PurePosixPath(database_path).suffix.lower() in (".db", ".sqlite")  # Keep supported SQLite extensions.
        and service.resolve_safe_path(database_path) is not None  # Require a guarded file, not a directory.
    ):
        return preview_table(database_path, table_name)  # Keep table validation, pagination, and errors unchanged.
    page = request.args.get("page", 1, type=int)  # Preserve the current page default.
    per_page = request.args.get("per_page", 50, type=int)  # Preserve the current page-size default.
    search = request.args.get("search", "")  # Preserve the existing search contract.
    sort = _read_sort_request(service, filepath, SortSpec)  # Issue #3047 requires the requested CSV order.
    current_app.logger.info("Reading a data file preview.")  # Trace the read without disclosing file contents.
    result = service.preview_file(filepath, page, per_page, search, sort)  # Keep every requested directory segment.
    current_app.logger.debug("Data file preview returned an error: %s.", "error" in result)  # Record only the outcome.
    if "error" in result:  # Keep the existing failure response and status.
        status = 404 if "not found" in result["error"].lower() else 400  # Preserve denial and missing-file behavior.
        return jsonify(result), status  # Return a JSON reason rather than an HTML error.
    return jsonify(result)  # Preserve the existing preview response schema.


def _read_sort_request(service: DataBrowserService, filepath: str, spec_class: type[SortSpec]) -> SortSpec | None:
    """Build the sort request of this call, or None when the caller asked for none.

    The column count comes from the file itself, so a crafted index can never
    reach the row reader.

    Args:
        service: The data browser service that can read the column names.
        filepath: The requested path inside the data directory.
        spec_class: The ``SortSpec`` class, passed in to keep the import local.

    Returns:
        The sort request, or None.
    """
    column = request.args.get("sort_column")
    if column is None or column == "":  # Most calls ask for no order at all.
        return None
    columns = service.read_column_names(filepath)  # An unreadable file yields an empty list.
    return spec_class.from_request(column, request.args.get("sort_dir", "asc"), len(columns))


def preview_table(filepath: str, table_name: str) -> Response | tuple[Response, int]:
    """Return paginated preview of a specific SQLite table."""
    from web_portal.services.data_browser import DataBrowserService

    data_dir = current_app.config.get("DATA_DIR", "data")
    service = DataBrowserService(data_dir)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
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
