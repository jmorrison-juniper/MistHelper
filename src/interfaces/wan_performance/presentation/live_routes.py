"""Serve explicit cached live journeys and a bounded CSRF-protected operator refresh."""

import logging
import sqlite3
from datetime import UTC, datetime, timedelta

from arango.exceptions import ArangoError
from flask import Blueprint, abort, current_app, redirect, render_template, request, url_for
from redis.exceptions import RedisError
from werkzeug.wrappers import Response

from src.foundation.persistence.db import DatabaseConfig
from src.interfaces.wan_performance.collection.live_service import LiveService
from src.interfaces.wan_performance.collection.request_admission import AdmittedAdapter
from src.interfaces.wan_performance.collection.snapshot_records import SnapshotRecords, SnapshotStates
from src.interfaces.wan_performance.domain.calendar import CalendarWindow
from src.interfaces.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    IdentityValidator,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.wan_performance.domain.measurement import HourlyMeasurement, MeasurementIdentity
from src.interfaces.wan_performance.domain.summary import CalendarSummaries, PeriodSummary
from src.interfaces.wan_performance.integration.history_repository import HistoryRepository, HistorySelection
from src.interfaces.wan_performance.integration.refresh_store import RefreshStore
from src.interfaces.wan_performance.presentation.inspection.sle_routes import SlePages
from src.interfaces.wan_performance.presentation.inspection.table import RecordTable, TableOptions

logger = logging.getLogger(__name__)
live_bp = Blueprint("live", __name__, url_prefix="/live", template_folder="inspection/templates")
STORE_ERRORS = (ConnectionError, OSError, RedisError, ArangoError, sqlite3.Error, ValueError, KeyError, TypeError)


class LiveHistory:
    """Select detail history without treating storage failures as empty results."""

    @staticmethod
    def read(
        service: LiveService, records: tuple[HourlyMeasurement, ...], kind: str, cache_only: bool = False
    ) -> tuple[tuple[PeriodSummary, ...], str | None]:
        """Read bounded persisted observations only for a selected detail identity."""
        if cache_only or kind not in {"gateway", "port", "peer"}:
            return (), None
        identity = LiveHistory._select_identity(service, records, kind)
        if identity is None:
            message = (
                "Select records for exactly one full gateway identity to read history."
                if kind == "gateway"
                else "Select one port or peer path to read history."
            )
            return (), message
        if service.history is None:
            return (), "History is unavailable. The selected application store is not available."
        try:
            end = datetime.now(UTC)
            start, end = CalendarWindow.thirteen_months_ending(end)
            history = service.history.read(identity, start, end)
            return CalendarSummaries.build(history, identity), None
        except STORE_ERRORS:
            logger.exception("WAN history is unavailable for the selected identity.")
            return (), "History is unavailable. The selected application store did not return valid records."

    @staticmethod
    def _select_identity(
        service: LiveService, records: tuple[HourlyMeasurement, ...], kind: str
    ) -> MeasurementIdentity | None:
        """Resolve one tenant-scoped gateway from gateway, circuit, or peer rows."""
        if kind != "gateway":
            if len(records) != 1:
                return None
            selected = records[0].identity
            gateway = selected if isinstance(selected, GatewayIdentity) else selected.gateway
            return selected if gateway.site.org_id == service.org_id else None
        gateways = {
            record.identity if isinstance(record.identity, GatewayIdentity) else record.identity.gateway
            for record in records
            if isinstance(record.identity, (GatewayIdentity, CircuitIdentity, PeerPathIdentity))
        }
        if len(gateways) != 1:
            return None
        gateway = next(iter(gateways))
        return gateway if gateway.site.org_id == service.org_id else None


class LivePages:
    """Use server-selected org context and public storage boundaries only."""

    @staticmethod
    def service() -> LiveService:
        """Use the portal session and active DataExporter-selected history backend."""
        injected = current_app.config.get("WAN_LIVE_SERVICE")
        if isinstance(injected, LiveService):
            if injected.org_id != current_app.config.get("ORG_ID"):
                raise ValueError("The WAN service organization does not match the portal.")
            return injected
        session = current_app.config.get("APISESSION")
        if session is None:
            raise ConnectionError("The portal has no configured Mist session.")
        transport = getattr(session, "_session", None)
        if transport is None or not isinstance(transport.get_adapter("https://"), AdmittedAdapter):
            raise ConnectionError("Configure shared Redis admission and restart to permit bounded live refresh.")
        org_id = current_app.config.get("ORG_ID")
        if not isinstance(org_id, str):
            raise ValueError("The portal has no selected organization.")
        IdentityValidator.identifier(org_id, "org_id")
        history: HistoryRepository | None
        try:
            history = HistorySelection.open()
        except STORE_ERRORS:
            logger.exception("The selected WAN history store is unavailable.")
            history = None
        return LiveService(session, org_id, RefreshStore.connect(DatabaseConfig.from_env()), history)

    @classmethod
    def render(cls, kind: str, filters: dict[str, str] | None = None, error: str | None = None) -> str | Response:
        """Read cached data, validate route membership, and never start a Mist request."""
        records: tuple[HourlyMeasurement, ...] = ()
        summaries: tuple[PeriodSummary, ...] = ()
        states: dict[tuple[str, ...], dict[str, str]] = {}
        gateways: tuple[GatewayIdentity, ...] = ()
        history_error, instant, partial = None, None, False
        options = TableOptions.from_request()
        try:
            service = cls.service()
            snapshot = service.store.cached(service.org_id)
            if snapshot is not None:
                if snapshot.get("org_id") != service.org_id:
                    raise ValueError("The cached WAN organization does not match the portal.")
                records = SnapshotRecords.build(snapshot)
                states = SnapshotStates.build(snapshot, records)
                gateways = SnapshotStates.gateways(records)
                instant = datetime.fromisoformat(str(snapshot["collected_at_utc"]))
                partial = bool(snapshot.get("partial"))
            records = cls.select(records, kind, filters)
            if filters and not records:
                abort(404, description="The requested WAN identity is absent from the cached organization.")
            summaries, history_error = LiveHistory.read(service, records, kind, request.args.get("download") == "csv")
        except STORE_ERRORS:
            logger.exception("The WAN live view is unavailable.")
            error = cls.unavailable(error)
        table = RecordTable.build(records, options)
        exported = table.export(error)
        if exported is not None:
            return exported
        return render_template(
            "wan_performance/live.html",
            kind=kind,
            records=records,
            table=table,
            summaries=summaries,
            states=states,
            gateways=gateways,
            error=error,
            history_error=history_error,
            instant=instant,
            partial=partial,
            filters=filters or {},
            stale=instant is not None and datetime.now(UTC) - instant > timedelta(minutes=5),
        )

    @staticmethod
    def unavailable(error: str | None) -> str:
        """Preserve actionable session errors without exposing exception content."""
        if current_app.config.get("APISESSION") is None and not current_app.config.get("WAN_LIVE_SERVICE"):
            return "The portal has no configured Mist session."
        return error or "Live data is unavailable. Check the configured session, cache, and history store."

    @staticmethod
    def refresh_target(org_id: str) -> GatewayIdentity | None:
        """Keep scoped gateway refresh under the server-selected organization."""
        gateway_id, site_id = request.form.get("gateway_id"), request.form.get("site_id")
        if not gateway_id and not site_id:
            return None
        if not gateway_id or not site_id:
            raise ValueError("Gateway refresh requires the complete site and gateway identity.")
        return GatewayIdentity(SiteIdentity(org_id, site_id), gateway_id)

    @staticmethod
    def select(
        records: tuple[HourlyMeasurement, ...], kind: str, filters: dict[str, str] | None
    ) -> tuple[HourlyMeasurement, ...]:
        """Match complete decoded source identifiers, including slash-bearing ports."""
        selected = tuple(record for record in records if LivePages.matches(record, filters or {}))
        if kind == "port":
            return tuple(record for record in selected if isinstance(record.identity, CircuitIdentity))
        if kind == "peer":
            return tuple(record for record in selected if isinstance(record.identity, PeerPathIdentity))
        return selected

    @staticmethod
    def matches(record: HourlyMeasurement, filters: dict[str, str]) -> bool:
        """Match source identifiers exactly instead of accepting partial tenant keys."""
        return all(record.identity.to_dict().get(name) == value for name, value in filters.items())


live_bp.add_url_rule("/sle", endpoint="sle", view_func=SlePages(LivePages.service).render, methods=["GET", "POST"])


@live_bp.get("/")
def overview() -> str | Response:
    """Show the server-selected organization without automatic live calls."""
    return LivePages.render("overview")


@live_bp.get("/gateway/<gateway_id>")
def gateway(gateway_id: str) -> str | Response:
    """Show only gateway identities found in the selected organization's cache."""
    return LivePages.render("gateway", {"gateway_id": gateway_id, "site_id": request.args.get("site_id", "")})


@live_bp.get("/port/<site_id>/<path:port_name>")
def port(site_id: str, port_name: str) -> str | Response:
    """Keep exact port names and the gateway/site query context."""
    return LivePages.render(
        "port", {"site_id": site_id, "port_name": port_name, "gateway_id": request.args.get("gateway_id", "")}
    )


@live_bp.get("/vpn/<site_id>/<peer_mac>")
def peer(site_id: str, peer_mac: str) -> str | Response:
    """Show distinct VPN paths rather than selecting an arbitrary same-MAC tunnel."""
    filters = {"site_id": site_id, "peer_mac": peer_mac}
    if request.args.get("path_key"):
        filters["tunnel_identity"] = request.args["path_key"]
    return LivePages.render("peer", filters)


@live_bp.post("/refresh")
def refresh() -> tuple[str | Response, int] | Response:
    """Run an explicit protected refresh, preserving previous cache on failure."""
    try:
        service = LivePages.service()
        target = LivePages.refresh_target(service.org_id)
        service.refresh(target)
    except STORE_ERRORS:
        logger.exception("The operator WAN refresh failed.")
        return (
            LivePages.render(
                "overview", error="WAN refresh failed. Check the shared cooldown, API admission, and configured stores."
            ),
            503,
        )
    if target is not None:
        return redirect(
            url_for("wan_performance.live.gateway", gateway_id=target.gateway_id, site_id=target.site.site_id)
        )
    return redirect(url_for("wan_performance.live.overview"))


@live_bp.post("/refresh-port")
def refresh_port() -> tuple[str | Response, int] | Response:
    """Collect one selected port insight hour through existing CSRF and shared ownership."""
    try:
        service = LivePages.service()
        gateway_target = LivePages.refresh_target(service.org_id)
        if gateway_target is None:
            raise ValueError("Port history refresh requires a site and gateway.")
        target = CircuitIdentity(gateway_target, request.form.get("port_name", ""))
        service.refresh_port(target)
    except STORE_ERRORS:
        logger.exception("The operator port history refresh failed.")
        return (
            LivePages.render(
                "overview", error="Port history refresh failed. Check the selected port, quota, and store."
            ),
            503,
        )
    return redirect(
        url_for(
            "wan_performance.live.port",
            site_id=target.gateway.site.site_id,
            gateway_id=target.gateway.gateway_id,
            port_name=target.port_name,
        )
    )


@live_bp.post("/refresh-peer")
def refresh_peer() -> tuple[str | Response, int] | Response:
    """Collect one selected peer quality hour through portal and shared API controls."""
    try:
        service = LivePages.service()
        gateway = LivePages.refresh_target(service.org_id)
        if gateway is None:
            raise ValueError("Peer history refresh requires a site and gateway.")
        target = PeerPathIdentity(
            gateway,
            request.form.get("port_name", ""),
            request.form.get("peer_port_id", ""),
            request.form.get("peer_mac", ""),
            request.form.get("tunnel_identity", ""),
        )
        service.refresh_peer(target)
    except STORE_ERRORS:
        logger.exception("The operator peer history refresh failed.")
        return (
            LivePages.render(
                "overview", error="Peer history refresh failed. Check the selected path, quota, and store."
            ),
            503,
        )
    return redirect(
        url_for(
            "wan_performance.live.peer",
            site_id=target.gateway.site.site_id,
            peer_mac=target.peer_mac,
            path_key=target.tunnel_identity,
        )
    )
