"""Checked payloads, target permission, and identity-scoped SDK capture actions."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from typing import cast

from mistapi.api.v1.orgs import mxedges as org_edges
from mistapi.api.v1.orgs import pcaps as org_pcaps
from mistapi.api.v1.sites import mxedges as site_edges
from mistapi.api.v1.sites import pcaps as site_pcaps
from mistapi.api.v1.sites import sites

from src.websocket_streams.catalog.model import FieldKind, FieldSpec, Safety, UtilityDefinition
from src.websocket_streams.intake.fields import FieldValueChecker, StreamRequestError
from src.websocket_streams.intake.identifiers import IdentifierRules
from src.websocket_streams.intake.start_request import StartRequest
from src.websocket_streams.live.captures.model import CaptureContext, CapturePlan
from src.websocket_streams.live.captures.transport import CaptureHttpSession

logger = logging.getLogger(__name__)


class CaptureBodies:
    """Build the same device payloads as the installed SDK without its short timer."""

    @classmethod
    def build(cls, request: StartRequest) -> CapturePlan:
        """Validate packet limits again at the runner boundary."""
        definition = request.definition
        if not isinstance(definition, UtilityDefinition) or definition.safety is not Safety.CAPTURE:
            raise StreamRequestError("bad_request", "The request is not a packet capture.")
        logger.info("Preparing packet capture key=%s", request.key)
        body = cls._parameters(request)
        builders = {"ap": cls._ap, "ex": cls._cabled, "srx": cls._cabled, "ssr": cls._cabled, "mxedge": cls._edge}
        if definition.family not in builders:
            raise StreamRequestError("bad_request", "The capture device family is not supported.")
        body.update(builders[definition.family](request))
        group = "orgs" if definition.scope == "organization" else "sites"
        identifier = request.target("org_id" if group == "orgs" else "site_id")
        if not IdentifierRules.is_uuid(identifier) or not IdentifierRules.is_uuid(request.target("org_id")):
            raise StreamRequestError("bad_request", "The capture scope is not valid.")
        duration = body["duration"]
        if not isinstance(duration, int):
            raise StreamRequestError("bad_request", "The capture duration is not valid.")
        logger.debug("Prepared packet capture key=%s duration=%s", request.key, duration)
        return CapturePlan(request, f"/{group}/{identifier}/pcaps", duration, body, (group, identifier.lower()))

    @staticmethod
    def _parameters(request: StartRequest) -> dict[str, object]:
        """Keep the explicit duration, packet count, and packet length bounds."""
        checker = FieldValueChecker()
        specs = (
            FieldSpec("duration", "Duration", FieldKind.INTEGER, required=True, minimum=60, maximum=3600),
            FieldSpec("max_pkt_len", "Packet length", FieldKind.INTEGER, required=True, minimum=64, maximum=1536),
            FieldSpec("num_packets", "Packets", FieldKind.INTEGER, required=True, minimum=1, maximum=10000),
        )
        defaults = {"duration": 60, "max_pkt_len": 512, "num_packets": 1024}
        body = {
            spec.name: checker.check(spec, request.parameters.get(spec.name, defaults[spec.name])) for spec in specs
        }
        body["format"] = "stream"
        expression = request.parameters.get("tcpdump_expression")
        if expression is not None:
            body["tcpdump_expression"] = expression
        return body

    @staticmethod
    def _ap(request: StartRequest) -> dict[str, object]:
        """Keep AP captures on the selected device rather than every AP at the site."""
        device_id = request.target("device_id")
        if not IdentifierRules.is_uuid(device_id):
            raise StreamRequestError("bad_request", "The capture device is not valid.")
        selected_mac = device_id.rsplit("-", 1)[-1].lower()
        supplied_mac = request.parameters.get("ap_mac", selected_mac)
        if supplied_mac != selected_mac:
            raise StreamRequestError("bad_request", "The AP MAC must match the selected device.", {"field": "ap_mac"})
        wireless = request.key == "ap.remotePcapWireless"
        body: dict[str, object] = {"type": "radiotap" if wireless else "wired", "ap_mac": selected_mac}
        if wireless:
            band = request.parameters.get("band")
            if band not in ("24", "5", "6"):
                raise StreamRequestError("bad_request", "The radio band is not valid.", {"field": "band"})
            body["band"] = band
        if "ssid" in request.parameters:
            body["ssid"] = request.parameters["ssid"]
        return body

    @staticmethod
    def _cabled(request: StartRequest) -> dict[str, object]:
        """Build the SDK switch or gateway port mapping."""
        device_id, ports = request.target("device_id"), request.parameters.get("port_ids")
        if not IdentifierRules.is_uuid(device_id):
            raise StreamRequestError("bad_request", "The capture needs a device and ports.")
        if not isinstance(ports, list):
            raise StreamRequestError("bad_request", "The capture needs a device and ports.")
        if not 1 <= len(ports) <= 48:
            raise StreamRequestError("bad_request", "The capture ports are not valid.")
        if any(not isinstance(port, str) or not IdentifierRules.is_port(port) for port in ports):
            raise StreamRequestError("bad_request", "The capture ports are not valid.")
        switch = request.key == "ex.remotePcap"
        group = "switches" if switch else "gateways"
        body: dict[str, object] = {
            "type": "switch" if switch else "gateway",
            group: {device_id.rsplit("-", 1)[-1]: {"ports": dict.fromkeys(ports, {})}},
        }
        if request.key == "ssr.remotePcap":
            body["raw"] = False
        return body

    @staticmethod
    def _edge(request: StartRequest) -> dict[str, object]:
        """Build the SDK Mist Edge interface mapping."""
        edge_id, interfaces = request.target("mxedge_id"), request.parameters.get("interfaces")
        if not IdentifierRules.is_uuid(edge_id) or not isinstance(interfaces, list) or not interfaces:
            raise StreamRequestError("bad_request", "The capture needs a Mist Edge and interfaces.")
        if len(interfaces) > 48 or any(
            not isinstance(interface, str) or not IdentifierRules.is_name(interface) for interface in interfaces
        ):
            raise StreamRequestError("bad_request", "The capture interfaces are not valid.")
        return {"type": "mxedge", "mxedges": {edge_id: {"interfaces": dict.fromkeys(interfaces, {})}}}


class CaptureResponses:
    """Reject uncertain SDK results without exposing response content."""

    @staticmethod
    def check(response: object, action: str) -> Mapping[str, object]:
        """Require an HTTP 200 object without a response error."""
        status = getattr(response, "status_code", None)
        code = status if type(status) is int else 0
        if code != 200:
            raise StreamRequestError(
                "not_ready", f"Mist returned HTTP {code or 'unknown'} for {action}. The capture state is uncertain."
            )
        data = getattr(response, "data", None)
        raw = getattr(response, "raw_data", "")
        if not isinstance(data, Mapping):
            raise StreamRequestError("not_ready", f"Mist returned an invalid {action} response.")
        if any(data.get(key) for key in ("error", "detail")):
            raise StreamRequestError("not_ready", f"Mist returned an invalid {action} response.")
        if raw:
            try:
                decoded = json.loads(raw)
            except (json.JSONDecodeError, TypeError) as error:
                raise StreamRequestError("not_ready", f"Mist returned an invalid {action} response.") from error
            if not isinstance(decoded, dict):
                raise StreamRequestError("not_ready", f"Mist returned an invalid {action} response.")
        return data

    @staticmethod
    def capture_id(response: object, plan: CapturePlan) -> str:
        """Require the accepted capture identifier and matching response scope."""
        data = CaptureResponses.check(response, "capture start")
        CaptureResponses.check_scope(data, plan.request)
        capture_id = data.get("id")
        if not isinstance(capture_id, str) or not IdentifierRules.is_uuid(capture_id):
            raise StreamRequestError(
                "not_ready", "The capture start returned no usable identifier. Mist can still capture packets."
            )
        return capture_id.lower()

    @staticmethod
    def check_scope(data: Mapping[str, object], request: StartRequest) -> None:
        """Refuse a response that identifies another site or organization."""
        for name in ("org_id", "site_id"):
            expected, received = request.target(name), data.get(name)
            if (
                expected
                and received is not None
                and (not isinstance(received, str) or received.lower() != expected.lower())
            ):
                raise StreamRequestError("not_ready", "The capture response names another scope.")

    @staticmethod
    def active(response: object, capture_id: str, plan: CapturePlan) -> None:
        """Permit scope-wide stop only for the accepted active capture."""
        data = CaptureResponses.check(response, "capture status")
        CaptureResponses.check_scope(data, plan.request)
        identifier = data.get("id")
        if not isinstance(identifier, str) or identifier.lower() != capture_id:
            raise StreamRequestError("not_ready", "The active capture identifier changed. Mist stop was not sent.")

    @staticmethod
    def stopped(response: object) -> None:
        """Check the documented empty cloud stop response."""
        data = CaptureResponses.check(response, "capture stop")
        if data.get("failed") or data.get("ok") is False or data.get("success") is False:
            raise StreamRequestError("not_ready", "Mist refused the packet capture stop.")


class CapturePermissions:
    """Check the server-owned organization before any capture action."""

    @classmethod
    def check(cls, apisession: object, request: StartRequest) -> None:
        """Retain the real SDK scope and Mist Edge membership checks."""
        logger.info("Checking packet capture target permission key=%s", request.key)
        site_id = request.target("site_id")
        if site_id:
            data = CaptureResponses.check(sites.getSiteInfo(apisession, site_id=site_id), "site permission")
            cls._organization(data, request)
        edge_id = request.target("mxedge_id")
        if edge_id:
            response = (
                site_edges.getSiteMxEdge(apisession, site_id=site_id, mxedge_id=edge_id)
                if site_id
                else org_edges.getOrgMxEdge(apisession, org_id=request.target("org_id"), mxedge_id=edge_id)
            )
            data = CaptureResponses.check(response, "Mist Edge permission")
            cls._organization(data, request)
            if data.get("id") != edge_id:
                raise StreamRequestError("bad_request", "The Mist Edge does not match the selected target.")
        logger.debug("Checked packet capture target permission key=%s", request.key)

    @staticmethod
    def _organization(data: Mapping[str, object], request: StartRequest) -> None:
        """Require an explicit organization match instead of a missing-value fallback."""
        identifier = data.get("org_id")
        if not isinstance(identifier, str) or identifier.lower() != request.target("org_id").lower():
            raise StreamRequestError("bad_request", "The capture target does not belong to the portal organization.")


class CaptureAPI:
    """Own bounded SDK start, active status, and cloud stop actions."""

    def __init__(self, apisession: object, context: CaptureContext) -> None:
        """Create a private HTTP transport without changing other streams."""
        self.source = apisession
        self.context = context
        self.apisession, self.http = CaptureHttpSession.for_api(apisession, context.dependencies.clock)
        self.stop_sent = False

    def authorize(self) -> None:
        """Validate membership through the same SDK and authentication context."""
        self.http.prepare(self.context.events.stopping)
        CapturePermissions.check(self.apisession, self.context.plan.request)

    def start(self) -> str:
        """Send one explicit SDK capture start after confirmed subscription."""
        plan = self.context.plan
        self.http.prepare(self.context.events.stopping)
        logger.info("Sending packet capture start key=%s duration=%s", plan.request.key, plan.duration)
        response = (
            org_pcaps.startOrgPacketCapture(self.apisession, org_id=plan.scope[1], body=plan.body)
            if plan.scope[0] == "orgs"
            else site_pcaps.startSitePacketCapture(self.apisession, site_id=plan.scope[1], body=plan.body)
        )
        identifier = CaptureResponses.capture_id(response, plan)
        logger.debug("Packet capture start accepted key=%s", plan.request.key)
        return identifier

    def stop(self, capture_id: str) -> None:
        """Check active identity before the single cloud stop."""
        if self.stop_sent:
            return
        plan = self.context.plan
        self.http.prepare(None)
        logger.info("Checking active packet capture before stop key=%s", plan.request.key)
        response = (
            org_pcaps.getOrgCapturingStatus(self.apisession, org_id=plan.scope[1])
            if plan.scope[0] == "orgs"
            else site_pcaps.getSiteCapturingStatus(self.apisession, site_id=plan.scope[1])
        )
        CaptureResponses.active(response, capture_id, plan)
        logger.debug("Active packet capture identity matched key=%s", plan.request.key)
        self.http.prepare(None)
        self.stop_sent = True  # A refused or uncertain stop must not cause a repeated scope-wide write.
        logger.info("Sending matching packet capture stop key=%s", plan.request.key)
        response = (
            org_pcaps.stopOrgPacketCapture(self.apisession, org_id=plan.scope[1])
            if plan.scope[0] == "orgs"
            else site_pcaps.stopSitePacketCapture(self.apisession, site_id=plan.scope[1])
        )
        CaptureResponses.stopped(response)
        logger.debug("Mist accepted packet capture stop key=%s", plan.request.key)

    def close(self) -> None:
        """Release the private transport and retain the original SDK request count."""
        logger.info("Closing packet capture HTTP transport")
        self.http.close()
        lock = getattr(self.source, "_token_lock", None)
        count = getattr(self.apisession, "_count", 0)
        if lock is not None and type(count) is int:
            with lock:
                current = getattr(self.source, "_count", 0)
                if type(current) is int:
                    original = cast(CaptureHttpSession.SDKState, self.source)
                    original._count = current + count
        logger.debug("Closed packet capture HTTP transport")
