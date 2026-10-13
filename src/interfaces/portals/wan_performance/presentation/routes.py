"""Serve WAN Performance pages without starting unverified live integrations."""

import logging
from typing import Protocol, runtime_checkable

from flask import Blueprint, abort, current_app, render_template, request

from src.interfaces.portals.wan_performance.domain.identity import (
    CircuitIdentity,
    GatewayIdentity,
    IdentityValidator,
    PeerPathIdentity,
    SiteIdentity,
)
from src.interfaces.portals.wan_performance.domain.measurement import HourlyMeasurement

logger = logging.getLogger(__name__)  # Keep portal records on the feature logger.
wan_performance_bp = Blueprint(
    "wan_performance",
    __name__,
    url_prefix="/wan-performance",
    template_folder="templates",
)
PREVIEW_FACTORY_CONFIG_KEY = "WAN_PERFORMANCE_PREVIEW_FACTORY"


@runtime_checkable
class OfflineDashboardData(Protocol):
    """Define the fixture shape that the isolated preview can render."""

    circuit: CircuitIdentity
    peer_path: PeerPathIdentity
    measurements: tuple[HourlyMeasurement, ...]


class RouteSupport:
    """Validate route values and load isolated preview records."""

    @staticmethod
    def load_preview() -> OfflineDashboardData:
        """Load a synthetic fixture only inside an explicitly testing app."""
        provider = current_app.config.get(PREVIEW_FACTORY_CONFIG_KEY)  # Read only the injected test provider.
        if not current_app.testing or not callable(provider):  # Keep synthetic records out of live requests.
            logger.warning("WAN Performance has no verified data provider")
            abort(503, description="WAN Performance requires a verified data provider.")
        logger.info("Loading the isolated synthetic WAN dashboard")  # Log before the fixture transform.
        dashboard = provider()  # Build only the fixture supplied by the test.
        if not isinstance(dashboard, OfflineDashboardData):  # Reject a provider with an unknown record shape.
            logger.error("The WAN preview provider returned an unsupported dashboard shape")
            abort(500, description="WAN Performance preview data has an invalid shape.")
        if any(record.provenance != "synthetic" for record in dashboard.measurements):
            logger.error("The WAN preview provider returned a non-synthetic measurement")
            abort(500, description="WAN Performance preview data must be synthetic.")
        logger.debug("Loaded %d synthetic WAN records", len(dashboard.measurements))
        return dashboard

    @staticmethod
    def identifier(value: str, field_name: str) -> str:
        """Validate a route value and report malformed input as HTTP 400."""
        try:
            return IdentityValidator.identifier(value, field_name)  # Reject unsafe or empty identifiers.
        except ValueError as error:
            logger.warning("Rejected WAN route identifier %s: %s", field_name, error)
            abort(400, description=str(error))

    @staticmethod
    def measurement(
        dashboard: OfflineDashboardData,
        identity: CircuitIdentity | PeerPathIdentity,
    ) -> HourlyMeasurement | None:
        """Select one record by its full natural identity."""
        logger.info("Selecting the synthetic WAN measurement for the requested identity")
        record = next((item for item in dashboard.measurements if item.identity == identity), None)
        logger.debug("Synthetic WAN measurement found: %s", record is not None)
        return record


@wan_performance_bp.get("/")
def overview() -> str:
    """Render the offline overview when a test injects synthetic records."""
    logger.info("Serving the WAN Performance overview")
    dashboard = RouteSupport.load_preview()
    circuit_measurement = RouteSupport.measurement(dashboard, dashboard.circuit)
    peer_measurement = RouteSupport.measurement(dashboard, dashboard.peer_path)
    response = render_template(
        "wan_performance/overview.html",
        dashboard=dashboard,
        circuit_measurement=circuit_measurement,
        peer_measurement=peer_measurement,
    )
    logger.debug("Rendered the synthetic WAN overview")
    return response


@wan_performance_bp.get("/gateway/<gateway_id>")
def gateway(gateway_id: str) -> str:
    """Render one fixture gateway and its child links."""
    logger.info("Serving the WAN gateway route")
    site_id = RouteSupport.identifier(request.args.get("site_id", ""), "site_id")
    requested_gateway_id = RouteSupport.identifier(gateway_id, "gateway_id")
    dashboard = RouteSupport.load_preview()
    gateway_site = SiteIdentity(dashboard.circuit.gateway.site.org_id, site_id)
    gateway_identity = GatewayIdentity(gateway_site, requested_gateway_id)
    if gateway_identity != dashboard.circuit.gateway:
        abort(404, description="The gateway is not present in the offline preview.")
    circuit_measurement = RouteSupport.measurement(dashboard, dashboard.circuit)
    response = render_template(
        "wan_performance/gateway.html",
        dashboard=dashboard,
        circuit_measurement=circuit_measurement,
    )
    logger.debug("Rendered the synthetic WAN gateway")
    return response


@wan_performance_bp.get("/port/<site_id>/<path:port_name>")
def port(site_id: str, port_name: str) -> str:
    """Render a fixture port while preserving its slash-bearing name."""
    logger.info("Serving the WAN port route")
    requested_site_id = RouteSupport.identifier(site_id, "site_id")
    gateway_id = RouteSupport.identifier(request.args.get("gateway_id", ""), "gateway_id")
    dashboard = RouteSupport.load_preview()
    gateway_site = SiteIdentity(dashboard.circuit.gateway.site.org_id, requested_site_id)
    gateway_identity = GatewayIdentity(gateway_site, gateway_id)
    try:
        circuit_identity = CircuitIdentity(gateway_identity, port_name)  # Validate the exact decoded port name.
    except ValueError as error:
        logger.warning("Rejected WAN port route value: %s", error)
        abort(400, description=str(error))
    if circuit_identity != dashboard.circuit:
        abort(404, description="The port is not present in the offline preview.")
    circuit_measurement = RouteSupport.measurement(dashboard, circuit_identity)
    response = render_template(
        "wan_performance/port.html",
        dashboard=dashboard,
        circuit_measurement=circuit_measurement,
    )
    logger.debug("Rendered the synthetic WAN port")
    return response


@wan_performance_bp.get("/vpn/<site_id>/<peer_mac>")
def vpn_peer(site_id: str, peer_mac: str) -> str:
    """Render one fixture VPN peer path with its explicit tunnel identity."""
    logger.info("Serving the WAN VPN peer route")
    requested_site_id = RouteSupport.identifier(site_id, "site_id")
    dashboard = RouteSupport.load_preview()
    if requested_site_id != dashboard.peer_path.gateway.site.site_id:
        abort(404, description="The peer is not present in the offline preview.")
    try:
        requested_peer_mac = IdentityValidator.peer_mac(peer_mac)
    except ValueError as error:
        logger.warning("Rejected WAN peer route value: %s", error)
        abort(400, description=str(error))
    if requested_peer_mac != dashboard.peer_path.peer_mac:
        abort(404, description="The peer is not present in the offline preview.")
    peer_measurement = RouteSupport.measurement(dashboard, dashboard.peer_path)
    response = render_template(
        "wan_performance/vpn_peer.html",
        dashboard=dashboard,
        peer_measurement=peer_measurement,
    )
    logger.debug("Rendered the synthetic WAN VPN peer")
    return response
