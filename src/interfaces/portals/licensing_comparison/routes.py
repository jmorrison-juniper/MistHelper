"""Serve licensing comparisons through a blueprint for the existing portal."""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Response, current_app, jsonify, render_template, request

from src.interfaces.portals.licensing_comparison import licensing_comparison_bp
from src.interfaces.portals.licensing_comparison.api import ServiceContext
from src.interfaces.portals.licensing_comparison.export import ComparisonExportRows, CsvExportService
from src.interfaces.portals.licensing_comparison.service import LicensingComparisonService
from src.mist.access.api import api_usage_cache

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
    rows, error = ComparisonExportRows.build(payload)
    if error:
        return jsonify({"error": error}), 400
    response, error = CsvExportService(Path(current_app.config.get("DATA_DIR", "data"))).write(rows)
    if error:
        return jsonify({"error": error}), 500
    if response is None:
        logger.error("The CSV export completed without a download response.")
        return jsonify({"error": "The CSV export failed. Try again."}), 500
    return response
