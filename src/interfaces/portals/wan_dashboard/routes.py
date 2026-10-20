"""Register safe, read-only routes for the WAN dashboard."""

from __future__ import annotations

import io
import logging
from datetime import UTC, datetime
from typing import Any

from flask import Blueprint, current_app, jsonify, render_template, request, send_file

from src.interfaces.portals.wan_dashboard.services import (
    CsvExporter,
    RedisDashboardCache,
    WanDashboardService,
    WanDataNormalizer,
)
from src.interfaces.portals.wan_dashboard.services.worker import WanDashboardWorker

logger = logging.getLogger(__name__)  # Keep feature route records under one module name.
wan_dashboard_bp = Blueprint(
    "wan_dashboard",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/wan-dashboard",
)


class DashboardServiceProvider:
    """Resolve one feature service from the portal's shared dependencies."""

    EXTENSION_KEY = WanDashboardWorker.SERVICE_EXTENSION_KEY

    @classmethod
    def get(cls) -> Any | None:
        """Return an injected test service or build one shared portal service."""
        configured = current_app.config.get("WAN_DASHBOARD_SERVICE")  # Tests inject a local service double.
        if configured is not None:  # Keep production and test routing on the same boundary.
            return configured  # Do not replace the injected service.
        session = current_app.config.get("APISESSION")  # Use only MistHelper's configured Mist session.
        org_id = current_app.config.get("ORG_ID")  # Keep reads scoped to the active organization.
        if not isinstance(org_id, str) or not org_id.strip():
            return None  # Cache reads still require a valid organization scope.
        service = current_app.extensions.get(cls.EXTENSION_KEY)  # Reuse the worker-local service and cooldowns.
        if service is not None:  # The portal app already built its feature service.
            return service  # Avoid one Redis connection attempt per request.
        from src.interfaces.portals.upgrade_portal.runtime.lock import connect_lock_store

        cache = RedisDashboardCache(connect_lock_store())  # Reuse the current shared Redis client only.
        service = WanDashboardService(session, org_id, cache=cache)  # Bind shared portal dependencies.
        current_app.extensions[cls.EXTENSION_KEY] = service  # Preserve local cooldown and stale-result state.
        logger.info("wan dashboard service initialized for the active organization")  # Do not log org credentials.
        return service  # The request uses the registered shared service.


class DashboardPageRoutes:
    """Render the WAN dashboard page inside the existing portal shell."""

    @staticmethod
    def page() -> str:
        """Render the source workflow with shared portal navigation and security."""
        logger.info("wan dashboard page requested")  # Mark the page action without logging user data.
        worker_ready = WanDashboardWorker.EXTENSION_KEY in current_app.extensions
        response = render_template(
            "wan_dashboard/dashboard.html", refresh_enabled=worker_ready
        )  # Keep Refresh unavailable until its leased worker starts.
        logger.debug("wan dashboard page rendered")  # Confirm the page result.
        return response  # The base template supplies portal security and theme assets.


class DashboardRefreshRoutes:
    """Expose worker status and queue requests without collecting Mist data."""

    @staticmethod
    def status() -> Any:
        """Return shared worker progress or an explicit disabled state."""
        worker = current_app.extensions.get(WanDashboardWorker.EXTENSION_KEY)
        if worker is not None:
            return jsonify(worker.status())  # Read only status and queue state from Redis.
        status = current_app.extensions.get(
            WanDashboardWorker.DISABLED_STATUS_KEY, WanDashboardWorker.disabled_status()
        )
        return jsonify(status)  # A missing worker cannot trigger a Mist request.

    @staticmethod
    def enqueue() -> tuple[Any, int]:
        """Queue one worker refresh and return without a Mist API call."""
        worker = current_app.extensions.get(WanDashboardWorker.EXTENSION_KEY)
        if worker is None:
            return jsonify({"status": "disabled", "notice": "Refresh is not configured."}), 503
        outcome = worker.enqueue()  # Redis coalesces requests into one pending follow-up.
        if outcome == "unavailable":
            return jsonify({"status": "error", "notice": "The refresh queue is unavailable."}), 503
        return jsonify({"status": outcome, "notice": "Refresh request accepted."}), 202


class DashboardReadRoutes:
    """Serve validated JSON reads for the overview and selected gateway."""

    @staticmethod
    def overview() -> tuple[Any, int] | Any:
        """Return the complete authorized overview with validated filters."""
        site_id = DashboardReadRoutes._query_value("site_id")  # Validate optional site selection.
        gateway_id = DashboardReadRoutes._query_value("gateway_id")  # Validate optional exact gateway selection.
        search = DashboardReadRoutes._query_value("search", maximum=120)  # Bound operator search text.
        invalid = next((value for value in (site_id, gateway_id, search) if value is False), None)
        if invalid is False:  # Reject malformed query values before the cache lookup.
            return DashboardReadRoutes._json({"status": "invalid", "data": [], "notice": "Filter is invalid."}, 400)
        service = DashboardServiceProvider.get()  # Resolve the organization scope and Redis client.
        if service is None:  # The cache cannot be scoped without an active organization.
            return DashboardReadRoutes._unavailable()
        result = service.get_cached_overview(site_id=site_id, gateway_id=gateway_id, search=search)
        return DashboardReadRoutes._result(result)  # Keep status semantics consistent across reads.

    @staticmethod
    def gateway_ports(gateway_id: str) -> tuple[Any, int] | Any:
        """Return details only for a gateway in the active authorized organization."""
        if not WanDataNormalizer.identifier(gateway_id):  # Reject a malformed path identifier.
            return DashboardReadRoutes._invalid()  # Stop before data collection.
        service = DashboardServiceProvider.get()  # Use the process-local cache service.
        if service is None:  # The cache cannot be scoped without an active organization.
            return DashboardReadRoutes._unavailable()
        return DashboardReadRoutes._result(service.get_cached_gateway_ports(gateway_id))

    @staticmethod
    def traffic(gateway_id: str, port_id: str) -> tuple[Any, int] | Any:
        """Return traffic samples for one supported range."""
        time_range = request.args.get("range", "24h")  # Keep the source dashboard's default period.
        if not WanDataNormalizer.identifier(gateway_id) or not WanDataNormalizer.identifier(port_id, port=True):
            return DashboardReadRoutes._invalid()  # Reject malformed path values before the cache lookup.
        if time_range not in WanDataNormalizer.TRAFFIC_SECONDS:  # Use only the four published options.
            return DashboardReadRoutes._invalid("Traffic range is invalid.")  # Do not pass arbitrary intervals.
        service = DashboardServiceProvider.get()  # Resolve the process-local cache service.
        if service is None:  # Report the missing organization scope instead of empty data.
            return DashboardReadRoutes._unavailable()
        return DashboardReadRoutes._result(service.get_cached_traffic(gateway_id, port_id, time_range))

    @staticmethod
    def insights(gateway_id: str, port_id: str) -> tuple[Any, int] | Any:
        """Return WAN Insights for one supported range."""
        time_range = request.args.get("range", "24h")  # Keep the source dashboard's default period.
        if not WanDataNormalizer.identifier(gateway_id) or not WanDataNormalizer.identifier(port_id, port=True):
            return DashboardReadRoutes._invalid()  # Reject malformed path values before the cache lookup.
        if time_range not in WanDataNormalizer.INSIGHT_SECONDS:  # Use only the five published options.
            return DashboardReadRoutes._invalid("Insights range is invalid.")  # Do not pass arbitrary intervals.
        service = DashboardServiceProvider.get()  # Resolve the process-local cache service.
        if service is None:  # Report the missing organization scope instead of empty data.
            return DashboardReadRoutes._unavailable()
        return DashboardReadRoutes._result(service.get_cached_insights(gateway_id, port_id, time_range))

    @staticmethod
    def _query_value(name: str, maximum: int = 128) -> str | None | bool:
        """Return an optional query value or False when it is unsafe."""
        value = request.args.get(name, "").strip()  # Normalize spaces once at the route boundary.
        if not value:  # An empty filter means no filter.
            return None  # Keep the service contract explicit.
        if len(value) > maximum or any(ord(character) < 32 for character in value):
            return False  # Bound inputs and reject control characters.
        if name != "search" and not WanDataNormalizer.identifier(value):
            return False  # Identifiers use the strict SDK route-safe pattern.
        return value  # Use only validated query input.

    @staticmethod
    def _result(result: dict[str, Any]) -> tuple[Any, int]:
        """Map explicit service states to safe HTTP status codes."""
        status = result.get("status")  # Read the service state, not the payload shape.
        status_key = status if isinstance(status, str) else ""  # Use a safe key for unknown service results.
        code = {
            "invalid": 400,
            "forbidden": 404,
            "rate_limited": 429,
            "error": 502,
            "unavailable": 503,
        }.get(status_key, 200)
        return DashboardReadRoutes._json(result, code)  # Partial and stale views remain visible at 200.

    @staticmethod
    def _json(payload: dict[str, Any], status: int) -> tuple[Any, int]:
        """Serialize one route result and record its non-sensitive status."""
        logger.debug("wan dashboard route completed with status %s", status)  # Record the HTTP result only.
        return jsonify(payload), status  # Flask serializes JSON with the correct content type.

    @staticmethod
    def _invalid(notice: str = "Gateway or port identifier is invalid.") -> tuple[Any, int]:
        """Return a consistent input-validation response."""
        return DashboardReadRoutes._json({"status": "invalid", "data": [], "notice": notice}, 400)

    @staticmethod
    def _unavailable() -> tuple[Any, int]:
        """Return an explicit missing-organization response."""
        return DashboardReadRoutes._json(
            {"status": "error", "data": [], "notice": "The active organization is unavailable."},
            503,
        )


class DashboardExportRoutes:
    """Return selected gateway and hourly metrics as safe CSV files."""

    @staticmethod
    def gateways() -> tuple[Any, int] | Any:
        """Export only overview rows selected by the current filters."""
        service = DashboardServiceProvider.get()  # Use the existing organization-scoped cache service.
        if service is None:  # A missing organization is unavailable, not an empty CSV.
            return DashboardReadRoutes._unavailable()
        filters = {
            "site_id": DashboardReadRoutes._query_value("site_id"),
            "gateway_id": DashboardReadRoutes._query_value("gateway_id"),
            "search": DashboardReadRoutes._query_value("search", maximum=120),
        }  # Keep the export selection aligned with the visible table.
        if False in filters.values():  # Reject the same unsafe filters as the overview.
            return DashboardReadRoutes._invalid("Export filter is invalid.")
        result = service.export_cached_gateways(**filters)  # Read only the selected cached overview rows.
        if result.get("status") not in {"ok", "empty"}:  # Do not export a failed or stale response as current.
            return DashboardReadRoutes._result(result)  # Preserve the explicit service state.
        content = CsvExporter.gateway_csv(result["data"])  # Neutralize formulas and quote cells.
        return DashboardExportRoutes._response(content, "wan_gateways")

    @staticmethod
    def hourly(gateway_id: str, port_id: str) -> tuple[Any, int] | Any:
        """Export the canonical twelve-column hourly port view."""
        time_range = request.args.get("range", "24h")  # Keep the source default.
        if not WanDataNormalizer.identifier(gateway_id) or not WanDataNormalizer.identifier(port_id, port=True):
            return DashboardReadRoutes._invalid()  # Validate route data before the cache lookup.
        if time_range not in WanDataNormalizer.INSIGHT_SECONDS:  # Use one documented range.
            return DashboardReadRoutes._invalid("Insights range is invalid.")  # Reject arbitrary periods.
        service = DashboardServiceProvider.get()  # Resolve the portal's shared cache service.
        if service is None:  # Do not send an empty file for a missing organization.
            return DashboardReadRoutes._unavailable()
        result = service.get_cached_hourly_export(gateway_id, port_id, time_range)
        if result.get("status") not in {"ok", "empty"}:  # Do not export failed or stale data as current.
            return DashboardReadRoutes._result(result)  # Preserve the explicit service state.
        content = CsvExporter.hourly_csv(result["data"])  # Preserve the source's twelve-column layout.
        return DashboardExportRoutes._response(content, "hourly_metrics")

    @staticmethod
    def _response(content: str, prefix: str) -> Any:
        """Send a CSV attachment with a fixed, safe filename."""
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")  # Use the required UTC timestamp format.
        filename = prefix + "_" + stamp + ".csv"  # Keep user input out of the download name.
        stream = io.BytesIO(content.encode("utf-8"))  # Stream a bounded in-memory export.
        logger.info("wan dashboard CSV export started")  # Mark the file output without logging its contents.
        return send_file(stream, mimetype="text/csv; charset=utf-8", as_attachment=True, download_name=filename)


wan_dashboard_bp.add_url_rule("", endpoint="page", view_func=DashboardPageRoutes.page, methods=["GET"])
wan_dashboard_bp.add_url_rule("/api/overview", endpoint="overview", view_func=DashboardReadRoutes.overview)
wan_dashboard_bp.add_url_rule(
    "/api/gateways/<gateway_id>/ports",
    endpoint="gateway_ports",
    view_func=DashboardReadRoutes.gateway_ports,
)
wan_dashboard_bp.add_url_rule(
    "/api/gateways/<gateway_id>/ports/<path:port_id>/traffic",
    endpoint="traffic",
    view_func=DashboardReadRoutes.traffic,
)
wan_dashboard_bp.add_url_rule(
    "/api/gateways/<gateway_id>/ports/<path:port_id>/insights",
    endpoint="insights",
    view_func=DashboardReadRoutes.insights,
)
wan_dashboard_bp.add_url_rule(
    "/api/gateways/export",
    endpoint="gateway_export",
    view_func=DashboardExportRoutes.gateways,
)
wan_dashboard_bp.add_url_rule(
    "/api/gateways/<gateway_id>/ports/<path:port_id>/hourly/export",
    endpoint="hourly_export",
    view_func=DashboardExportRoutes.hourly,
)
wan_dashboard_bp.add_url_rule("/api/refresh-status", endpoint="refresh_status", view_func=DashboardRefreshRoutes.status)
wan_dashboard_bp.add_url_rule(
    "/api/refresh", endpoint="refresh", view_func=DashboardRefreshRoutes.enqueue, methods=["POST"]
)
wan_dashboard_bp.record_once(WanDashboardWorker.register_blueprint)  # Start only the configured in-process worker.
