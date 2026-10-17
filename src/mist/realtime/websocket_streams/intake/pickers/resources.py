"""Site map, asset, and SDK client picker behavior."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured records write through standard repository handlers.

import src.foundation.runtime.config.runtime_settings as runtime_settings  # Read the live validated page limit.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Report failed discovery as a route error.
from src.mist.realtime.websocket_streams.intake.identifiers.identity_rules import (
    IdentityIdentifierRules,
)  # Validate returned client addresses.
from src.mist.realtime.websocket_streams.intake.pickers.records import PickerRuntime  # Shared state and row shaping.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Reuse the shared bounded JSON boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep resource logs bounded and identifier-free.


class ResourcePicker(PickerRuntime):
    """List site resources used by start request fields."""

    def sites(self) -> dict[str, object]:
        """Return every site in the configured organization."""
        logger.emit(logging.INFO, "intake_site_picker_started", {"detail": "organization"})  # Log the fixed scope.
        try:  # Keep SDK and pagination failures distinct from an empty organization.
            import mistapi  # Import here so focused tests can replace the SDK seam.

            response = mistapi.api.v1.orgs.sites.listOrgSites(
                self._apisession, self._org_id, limit=runtime_settings.DEFAULT_API_PAGE_LIMIT
            )  # Request the configured organization at the validated page limit.
            rows = [
                self._row(record, ("name", "id"), ("address", "country_code"), None)
                for record in self._page_reader.read(response)
            ]  # Normalize all validated organization pages.
            logger.emit(logging.DEBUG, "intake_site_picker_finished", {"count": len(rows)})  # Log safe count only.
            return self._payload(rows, "The organization has no sites.")  # Keep an empty list explicit.
        except StreamRequestError:  # Preserve checked page and target failures.
            raise  # Preserve HTTP, cursor, and response-shape failures.
        except Exception as error:  # Translate unclassified SDK failures.
            logger.emit(logging.ERROR, "intake_site_picker_failed", {"detail": type(error).__name__})  # Safe type only.
            raise StreamRequestError(
                "picker_service_failed", "The portal could not list sites from Mist."
            ) from error  # Do not report an SDK failure as an empty list.

    def maps(self, site_id: str) -> dict[str, object]:
        """Return map rows for one site."""
        return self._site_picker(site_id, "maps", "The site has no maps.")  # Use the shared SDK flow.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return BLE asset rows for one site."""
        return self._site_picker(site_id, "assets", "The site has no assets.")  # Use shared flow.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return SDK client rows for one map."""
        logger.emit(logging.INFO, "intake_sdkclient_picker_started", {"action": "list"})  # Log no identifiers.
        try:  # Keep SDK failures separate from a complete empty map.
            import mistapi  # Import here so focused tests can replace the SDK seam.

            response = mistapi.api.v1.sites.stats.getSiteSdkStatsByMap(
                self._apisession, site_id, map_id
            )  # Read clients.
            rows = [
                self._row(item, ("name", "hostname", "mac"), ("mac", "status"), None)
                for item in self._page_reader.read(response)
            ]  # Normalize every validated map response page.
            logger.emit(logging.DEBUG, "intake_sdkclient_picker_finished", {"count": len(rows)})  # Log safe count.
            return self._payload(rows, "The map has no SDK clients.")  # Explain an empty list.
        except StreamRequestError:  # Preserve checked page and target failures.
            raise  # Preserve HTTP, cursor, and response-shape failures.
        except Exception as error:  # Translate unclassified SDK failures.
            logger.emit(logging.ERROR, "intake_sdkclient_picker_failed", {"detail": type(error).__name__})  # Safe type.
            raise StreamRequestError(
                "picker_service_failed", "The portal could not list SDK clients from Mist."
            ) from error  # Do not report an SDK failure as an empty list.

    def _site_picker(self, site_id: str, family: str, empty_reason: str) -> dict[str, object]:
        """Return rows from one simple site SDK list."""
        logger.emit(logging.INFO, "intake_site_picker_started", {"detail": family})  # Log the fixed picker family.
        try:  # Keep SDK failures separate from a complete empty site resource list.
            import mistapi  # Import here so focused tests can replace the SDK seam.

            if family == "maps":  # Map lists accept the runtime page limit.
                response = mistapi.api.v1.sites.maps.listSiteMaps(
                    self._apisession, site_id=site_id, limit=runtime_settings.DEFAULT_API_PAGE_LIMIT
                )  # Read every map page through the SDK cursor.
            else:  # The only other caller requests site assets.
                response = mistapi.api.v1.sites.assets.listSiteAssets(
                    self._apisession, site_id=site_id, limit=runtime_settings.DEFAULT_API_PAGE_LIMIT
                )  # Read every asset page through the SDK cursor.
            rows = [
                self._row(item, ("name", "id"), ("type", "status"), None) for item in self._page_reader.read(response)
            ]  # Normalize every validated resource page.
            logger.emit(
                logging.DEBUG, "intake_site_picker_finished", {"detail": family, "count": len(rows)}
            )  # Safe data.
            return self._payload(rows, empty_reason)  # Return the common contract shape.
        except StreamRequestError:  # Preserve checked page and target failures.
            raise  # Preserve HTTP, cursor, and response-shape failures.
        except Exception as error:  # Translate unclassified SDK failures.
            logger.emit(logging.ERROR, "intake_site_picker_failed", {"detail": type(error).__name__})  # Log safe type.
            raise StreamRequestError(
                "picker_service_failed", "The portal could not list this data from Mist."
            ) from error  # Do not report an SDK failure as an empty list.


class WiredClientPicker(PickerRuntime):
    """Read client choices for one explicitly selected EX switch."""

    def clients(self, site_id: str, device_mac: str) -> dict[str, object]:
        """Return verified wired clients for one selected EX switch."""
        logger.emit(logging.INFO, "intake_client_picker_started", {"action": "wired"})  # Log no client identifiers.
        try:
            import mistapi  # Import here so focused tests can replace the SDK seam.

            response = mistapi.api.v1.sites.wired_clients.searchSiteWiredClients(
                self._apisession,
                site_id,
                device_mac=device_mac,
                limit=runtime_settings.DEFAULT_API_PAGE_LIMIT,
            )  # Use the selected-device filter and the validated page limit.
            records = self._page_reader.read(response)  # Validate every authenticated cursor page.
            rows = self._verified_client_rows(records, site_id, device_mac)  # Check scope.
            logger.emit(logging.DEBUG, "intake_client_picker_finished", {"count": len(rows)})  # Log only the count.
            return self._payload(rows, "No wired clients are listed for this switch.")  # Keep empty distinct.
        except StreamRequestError:
            raise  # Preserve the explicit scope and upstream failure code.
        except Exception as error:
            logger.emit(logging.ERROR, "intake_client_picker_failed", {"detail": type(error).__name__})  # Safe type.
            raise StreamRequestError(
                "picker_service_failed", "The portal could not read client suggestions from Mist."
            ) from error  # Keep manual entry available with an explicit error.

    def _verified_client_rows(
        self, records: list[dict[str, object]], site_id: str, device_mac: str | None
    ) -> list[dict[str, object]]:
        """Return unique client rows with explicit site and switch association."""
        if device_mac is None:
            raise StreamRequestError("picker_unavailable", "The selected switch has no verified MAC address.")
        rows: dict[str, dict[str, object]] = {}  # Deduplicate records by normalized client MAC.
        for record in records:
            row = self._verified_client_row(record, site_id, device_mac)  # Reject records outside this scope.
            if row is not None:
                rows.setdefault(str(row["id"]), row)  # Keep the first stable choice per normalized MAC.
        return list(rows.values())  # The common payload sorts the operator labels.

    def _verified_client_row(
        self, record: dict[str, object], site_id: str, device_mac: str
    ) -> dict[str, object] | None:
        """Build a choice only when the record proves its site and switch."""
        client_mac = record.get("mac")  # Mist uses the client MAC as the stable choice value.
        if record.get("site_id") != site_id or not IdentityIdentifierRules.is_mac(client_mac):
            return None  # Missing or malformed identity evidence cannot become a choice.
        if not WiredClientAssociation.matches(record, device_mac):
            return None  # A site-wide client is not evidence of switch association.
        normalized = IdentityIdentifierRules.normalize_mac(str(client_mac))  # Match utility input format.
        label = self._first_text(record, ("hostname", "dhcp_hostname", "mac")) or normalized  # Prefer a host name.
        return {"id": normalized, "label": label, "family": "ex", "detail": normalized}  # Show identity clearly.


class WiredClientAssociation:
    """Check explicit site-switch association evidence in wired-client rows."""

    @staticmethod
    def matches(record: dict[str, object], device_mac: str) -> bool:
        """Check the documented wired association fields."""
        return WiredClientAssociation._mac_list_matches(record.get("device_mac"), device_mac) or (
            WiredClientAssociation._port_list_matches(record.get("device_mac_port"), device_mac)
        )  # Require one explicit association source.

    @staticmethod
    def _mac_list_matches(values: object, device_mac: str) -> bool:
        """Check the response's list of associated switch MAC addresses."""
        return isinstance(values, list) and any(
            isinstance(value, str)
            and IdentityIdentifierRules.is_mac(value)
            and IdentityIdentifierRules.normalize_mac(value) == device_mac
            for value in values
        )  # Accept only validated MAC values.

    @staticmethod
    def _port_list_matches(ports: object, device_mac: str) -> bool:
        """Check per-port association records for the selected switch."""
        return isinstance(ports, list) and any(
            isinstance(port, dict) and WiredClientAssociation._mac_list_matches([port.get("device_mac")], device_mac)
            for port in ports
        )  # Require a per-port MAC that matches the selected switch.


class EdgePicker(PickerRuntime):
    """List Mist Edges for a site or organization."""

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return Mist Edge rows for the selected scope."""
        logger.emit(logging.INFO, "intake_edge_picker_started", {"status": "site" if site_id else "organization"})
        try:  # Keep Mist Edge failures separate from a complete empty scope.
            rows = [
                self._row(item, ("name", "id"), ("model", "status"), "mxedge") for item in self._edge_records(site_id)
            ]
            logger.emit(logging.DEBUG, "intake_edge_picker_finished", {"count": len(rows)})  # Log safe count only.
            return self._payload(rows, "No Mist Edge matches this scope.")  # Explain an empty list.
        except StreamRequestError:  # Preserve checked page and target failures.
            raise  # Preserve HTTP, cursor, and response-shape failures.
        except Exception as error:  # Translate unclassified SDK failures.
            logger.emit(logging.ERROR, "intake_edge_picker_failed", {"detail": type(error).__name__})  # Log safe type.
            raise StreamRequestError(
                "picker_service_failed", "The portal could not list Mist Edges from Mist."
            ) from error  # Do not report an SDK failure as an empty list.

    def _edge_records(self, site_id: str | None) -> list[dict[str, object]]:
        """Read Mist Edge records from one SDK scope."""
        import mistapi  # Import here so focused tests can replace the SDK seam.

        if site_id:  # A selected site narrows the list.
            response = mistapi.api.v1.sites.mxedges.listSiteMxEdges(
                self._apisession, site_id, limit=runtime_settings.DEFAULT_API_PAGE_LIMIT
            )  # Read site edges at the configured page limit.
        else:  # An absent site selects the trusted organization scope.
            response = mistapi.api.v1.orgs.mxedges.listOrgMxEdges(
                self._apisession, self._org_id, limit=runtime_settings.DEFAULT_API_PAGE_LIMIT
            )  # Read organization edges at the configured page limit.
        return self._page_reader.read(response)  # Validate and normalize every SDK response page.
