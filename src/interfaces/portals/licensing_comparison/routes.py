"""Serve licensing comparisons through a blueprint for the existing portal."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from flask import Response, current_app, jsonify, render_template, request, send_file

from src.foundation.models.dataclasses.export_backend_options import ExportBackendOptions
from src.interfaces.portals.licensing_comparison import licensing_comparison_bp
from src.interfaces.portals.licensing_comparison.service import LicensingComparisonService, ServiceContext
from src.mist.access.api import api_usage_cache
from src.operations.exporting.export.data_exporter import DataExporter
from web_portal.services.data_browser import DataBrowserService

logger = logging.getLogger(__name__)


def _service() -> LicensingComparisonService:
    """Build the service from the shared Mist session and rate-limit cache."""
    context = ServiceContext(
        current_app.config.get("APISESSION"),
        current_app.config.get("ORG_ID"),
        current_app.config.get("ORG_NAME"),
        api_usage_cache.api_usage_cache,
    )
    return LicensingComparisonService(context)


@licensing_comparison_bp.get("/license-comparison")
def comparison_page() -> tuple[str, int]:
    """Render the dashboard and identify a missing shared session."""
    session_available = current_app.config.get("APISESSION") is not None
    status = 200 if session_available else 503
    return render_template("licensing_comparison.html", session_available=session_available), status


@licensing_comparison_bp.get("/api/license-comparison/organizations")
def organizations() -> tuple[Response, int]:
    """Return only organizations discovered through the shared Mist session."""
    choices, errors = _service().discover_organizations()
    session_missing = current_app.config.get("APISESSION") is None
    status = 503 if session_missing else 502 if errors and not choices else 200
    logger.debug("Returned %d organization choices with %d discovery errors.", len(choices), len(errors))
    return jsonify({"organizations": choices, "errors": [error.as_dict() for error in errors]}), status


@licensing_comparison_bp.post("/api/license-comparison")
def compare_organizations() -> tuple[Response, int]:
    """Compare authorized Mist organizations and validated manual rows."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "The request body must be a JSON object."}), 400
    result, error, status = _service().compare(
        payload.get("organization_ids"),
        payload.get("manual_rows", []),
        payload.get("purchased_amounts", {}),
    )
    if error:
        logger.warning("Rejected licensing comparison with HTTP %d: %s", status, error)
        return jsonify({"error": error}), status
    return jsonify(result), status


@licensing_comparison_bp.post("/api/license-comparison/export")
def export_comparison() -> Response | tuple[Response, int]:
    """Write an operator-requested CSV through the shared data exporter."""
    payload = request.get_json(silent=True)
    rows, error = LicensingComparisonService.export_rows(payload)
    if error:
        return jsonify({"error": error}), 400
    data_dir = Path(current_app.config.get("DATA_DIR", "data")).resolve()
    filename = f"mist_org_licensing_comparison_{datetime.now(UTC):%Y%m%dT%H%M%SZ}_{uuid4().hex[:8]}.csv"
    target = data_dir / filename
    logger.info("Writing %d licensing comparison rows to CSV.", len(rows))
    written = DataExporter.write_with_format_selection(
        rows,
        str(target),
        api_function_name=None,  # type: ignore[arg-type]  # CSV export must not mirror operator input to a database.
        fieldnames=[
            "organization",
            "organization_id",
            "source",
            "source_attribution",
            "request_status",
            "license_summary",
            "license_use_by_site",
            "inventory",
            "balances",
        ],
        backend_options=ExportBackendOptions(format_override="csv"),
    )
    if not written:
        logger.error("The licensing comparison CSV write failed.")
        return jsonify({"error": "The CSV export failed. Try again."}), 500
    resolved = DataBrowserService(str(data_dir)).resolve_safe_path(filename)
    if resolved is None:
        logger.error("The licensing comparison CSV could not be resolved below the data directory.")
        return jsonify({"error": "The CSV export could not be read from the data directory."}), 500
    logger.debug("Prepared the licensing comparison CSV download.")
    return send_file(resolved, as_attachment=True, download_name=filename, mimetype="text/csv")
