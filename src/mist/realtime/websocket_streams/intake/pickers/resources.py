"""Site map, asset, and SDK client picker behavior."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import logging  # Structured records write through standard repository handlers.

from src.mist.realtime.websocket_streams.intake.pickers.records import PickerRuntime  # Shared state and row shaping.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Reuse the shared bounded JSON boundary.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep resource logs bounded and identifier-free.


class ResourcePicker(PickerRuntime):
    """List site resources used by start request fields."""

    def maps(self, site_id: str) -> dict[str, object]:
        """Return map rows for one site."""
        return self._site_picker(site_id, "maps", "listSiteMaps", "The site has no maps.")  # Use the shared SDK flow.

    def assets(self, site_id: str) -> dict[str, object]:
        """Return BLE asset rows for one site."""
        return self._site_picker(site_id, "assets", "listSiteAssets", "The site has no assets.")  # Use shared flow.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return SDK client rows for one map."""
        logger.emit(logging.INFO, "intake_sdkclient_picker_started", {"action": "list"})  # Log no identifiers.
        try:
            import mistapi  # Import here so focused tests can replace the SDK seam.

            response = mistapi.api.v1.sites.stats.getSiteSdkStatsByMap(
                self._apisession, site_id, map_id
            )  # Read clients.
            rows = [
                self._row(item, ("name", "hostname", "mac"), ("mac", "status"), None)
                for item in self._records(response)
            ]
            logger.emit(logging.DEBUG, "intake_sdkclient_picker_finished", {"count": len(rows)})  # Log safe count.
            return self._payload(rows, "The map has no SDK clients.")  # Explain an empty list.
        except Exception as error:
            logger.emit(logging.ERROR, "intake_sdkclient_picker_failed", {"detail": type(error).__name__})  # Safe type.
            return self._payload([], "The portal could not list SDK clients from Mist.")  # Keep the form usable.

    def _site_picker(self, site_id: str, family: str, function_name: str, empty_reason: str) -> dict[str, object]:
        """Return rows from one simple site SDK list."""
        logger.emit(logging.INFO, "intake_site_picker_started", {"detail": family})  # Log the fixed picker family.
        try:
            import mistapi  # Import here so focused tests can replace the SDK seam.

            namespace = getattr(mistapi.api.v1.sites, family)  # Select the fixed SDK namespace.
            response = getattr(namespace, function_name)(self._apisession, site_id)  # Call the fixed read function.
            rows = [self._row(item, ("name", "id"), ("type", "status"), None) for item in self._records(response)]
            logger.emit(
                logging.DEBUG, "intake_site_picker_finished", {"detail": family, "count": len(rows)}
            )  # Safe data.
            return self._payload(rows, empty_reason)  # Return the common contract shape.
        except Exception as error:
            logger.emit(logging.ERROR, "intake_site_picker_failed", {"detail": type(error).__name__})  # Log safe type.
            return self._payload([], "The portal could not list this data from Mist.")  # Keep the form usable.


class EdgePicker(PickerRuntime):
    """List Mist Edges for a site or organization."""

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return Mist Edge rows for the selected scope."""
        logger.emit(logging.INFO, "intake_edge_picker_started", {"status": "site" if site_id else "organization"})
        try:
            rows = [
                self._row(item, ("name", "id"), ("model", "status"), "mxedge") for item in self._edge_records(site_id)
            ]
            logger.emit(logging.DEBUG, "intake_edge_picker_finished", {"count": len(rows)})  # Log safe count only.
            return self._payload(rows, "No Mist Edge matches this scope.")  # Explain an empty list.
        except Exception as error:
            logger.emit(logging.ERROR, "intake_edge_picker_failed", {"detail": type(error).__name__})  # Log safe type.
            return self._payload([], "The portal could not list Mist Edges from Mist.")  # Keep the form usable.

    def _edge_records(self, site_id: str | None) -> list[dict[str, object]]:
        """Read Mist Edge records from one SDK scope."""
        import mistapi  # Import here so focused tests can replace the SDK seam.

        if site_id:  # A selected site narrows the list.
            response = mistapi.api.v1.sites.mxedges.listSiteMxEdges(self._apisession, site_id)  # Read site edges.
        else:
            response = mistapi.api.v1.orgs.mxedges.listOrgMxEdges(self._apisession, self._org_id)  # Read org edges.
        return self._records(response)  # Normalize the SDK response.
