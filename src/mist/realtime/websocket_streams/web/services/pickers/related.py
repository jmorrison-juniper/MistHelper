"""Own SDK client and Mist Edge picker actions."""

from __future__ import annotations  # Keep collaborator annotations lazy.

import logging  # Structured events use repository handlers.
from typing import Any, cast  # Picker collaborators use behavior types.

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    UtilityDefinition,
)  # Use catalog target metadata as the only eligibility source.
from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Refuse pickers while not ready.
from src.mist.realtime.websocket_streams.live.transport.runtime.logging.structured_logger import (
    StructuredTransportLogger,
)  # Use the shared bounded JSON logger.

logger = StructuredTransportLogger(logging.getLogger(__name__))  # Keep picker fields safe and bounded.


class RelatedPickerService:
    """Read SDK client and Mist Edge picker rows."""

    def __init__(self, picker: Any | None, reason: str | None) -> None:
        """Store the Mist picker and readiness."""
        self._picker = picker  # A not-ready service has no Mist picker.
        self._reason = reason  # A reason blocks every picker action.

    def sdkclients(self, site_id: str, map_id: str) -> dict[str, object]:
        """Return SDK client picker rows."""
        picker = self._ready_picker("sdkclients")  # Require the production picker.
        return cast(dict[str, object], picker.sdkclients(site_id, map_id))  # Preserve map-scoped behavior.

    def mxedges(self, site_id: str | None) -> dict[str, object]:
        """Return Mist Edge picker rows."""
        picker = self._ready_picker("mxedges")  # Require the production picker.
        return cast(dict[str, object], picker.mxedges(site_id))  # Preserve optional site filtering.

    def _ready_picker(self, action: str) -> Any:
        """Return the ready picker or raise the contract error."""
        if self._reason is not None or self._picker is None:  # Pickers need credentials and imports.
            raise StreamRequestError("not_ready", self._reason or "The WebSocket engine is not ready.")  # Refuse.
        logger.emit(logging.DEBUG, "web.picker.read", {"action": action})  # Log only the fixed picker kind.
        return self._picker  # Return the ready Mist picker.


class BatchTargetPickerService:
    """Discover targets that one catalog operation can safely address."""

    def __init__(self, picker: Any | None, catalog: Any | None, reason: str | None) -> None:
        """Store the authenticated picker, catalog, and readiness state."""
        self._picker = picker  # Batch discovery uses existing authenticated picker behavior.
        self._catalog = catalog  # The catalog determines every eligible resource.
        self._reason = reason  # A reason blocks discovery before any Mist request.

    def targets(self, site_id: str | None, kind: str, key: str, parents: dict[str, str]) -> dict[str, object]:
        """Return complete eligible targets for one site or organization."""
        logger.emit(logging.INFO, "web.batch.targets.start", {"kind": kind})  # Log operation type only.
        if self._reason is not None or self._picker is None or self._catalog is None:  # Require all discovery inputs.
            raise StreamRequestError("not_ready", self._reason or "The WebSocket engine is not ready.")  # Refuse.
        result = BatchTargetResolver(self._picker, self._catalog).discover(site_id, kind, key, parents)
        logger.emit(logging.DEBUG, "web.batch.targets.finish", {"count": result["total_count"]})  # Log count only.
        return result  # Return complete rows or let discovery raise a checked error.

    def sites(self, kind: str, key: str) -> dict[str, object]:
        """Return complete organization sites for a site-scoped catalog operation."""
        if self._reason is not None or self._picker is None or self._catalog is None:  # Require ready collaborators.
            raise StreamRequestError("not_ready", self._reason or "The WebSocket engine is not ready.")  # Refuse.
        definition = self._catalog.find(kind, key)  # Resolve the selected operation from the server catalog.
        if definition is None:  # Reject a key that the live catalog does not own.
            raise StreamRequestError("unknown_key", "The selected catalog operation is not available.")  # Refuse.
        fields = definition.identifiers if isinstance(definition, ChannelDefinition) else definition.targets
        if not any(field.name == "site_id" for field in fields):  # Organization operations need no site list.
            raise StreamRequestError(
                "bad_request", "This operation does not use site scope.", {"field": "kind"}
            )  # Keep scope errors explicit.
        logger.emit(logging.INFO, "web.batch.sites.start", {"kind": kind})  # Log before complete site discovery.
        payload = self._picker.sites()  # Read all authenticated organization pages.
        payload["complete"] = True  # The picker returns only after every page passes validation.
        payload["scope"] = {"organization": True}  # Keep the configured organization server-owned.
        logger.emit(logging.DEBUG, "web.batch.sites.finish", {"count": payload["total_count"]})  # Log row count only.
        return payload  # Preserve complete rows and the empty-result reason.


class BatchTargetResolver:
    """Resolve catalog target fields into complete site-scoped picker rows."""

    def __init__(self, picker: Any, catalog: Any) -> None:
        """Store the authenticated picker and server catalog."""
        self._picker = picker  # Existing picker methods own Mist calls and pagination.
        self._catalog = catalog  # Catalog metadata fixes family and target type.

    def discover(self, site_id: str | None, kind: str, key: str, parents: dict[str, str]) -> dict[str, object]:
        """Return operation targets after complete scope validation."""
        definition = self._catalog.find(kind, key)  # Resolve only server-owned catalog metadata.
        if definition is None:  # Reject unknown operation keys before any picker call.
            raise StreamRequestError("unknown_key", "The selected catalog operation is not available.")  # Refuse.
        fields = definition.identifiers if isinstance(definition, ChannelDefinition) else definition.targets
        target_field = next((field for field in reversed(fields) if field.name != "site_id"), None)
        allowed_parents = {"map_id"} if target_field is not None and target_field.picker == "sdkclients" else set()
        if set(parents) - allowed_parents:  # Parent values must match the catalog resource relationship.
            raise StreamRequestError("bad_request", "The target request has an unsupported parent.")  # Refuse.
        if site_id is None:
            if getattr(definition, "scope", "") != "organization":  # Do not widen a site operation to the organization.
                raise StreamRequestError(
                    "bad_request", "This operation requires a site.", {"field": "site_id"}
                )  # Keep scope errors explicit.
            rows, excluded = self._resource_rows(target_field, None, parents, definition)
            return self._response(rows, None, excluded)
        sites = self._picker.sites()["rows"]  # Verify selected scope against all organization pages.
        site = next((row for row in sites if row.get("id") == site_id), None)
        if site is None:  # Reject a foreign site before its resource list is read.
            raise StreamRequestError(
                "bad_request", "The site is not part of this organization.", {"field": "site_id"}
            )  # Keep scope errors explicit.
        if target_field is None:
            rows, excluded = [
                {
                    "id": site["id"],  # Preserve the source site identity.
                    "label": site.get("label") or site.get("name") or site["id"],  # Prefer an operator label.
                    "family": None,  # Sites do not use device utility families.
                    "detail": site.get("detail"),  # Keep safe picker detail.
                    "site_id": site["id"],  # Keep the required target scope.
                    "target_type": "site",  # Identify the target kind.
                }
            ], 0
        else:
            rows, excluded = self._resource_rows(target_field, site_id, parents, definition)
        return self._response(rows, site_id, excluded)

    def _resource_rows(
        self, field: Any | None, site_id: str | None, parents: dict[str, str], definition: Any
    ) -> tuple[list[dict[str, object]], int]:
        """Read the catalog-selected resource and attach its full target identity."""
        picker_name = field.picker if field is not None else None
        if picker_name == "devices" and site_id is not None:  # Device utilities need the full device inventory.
            payload = self._picker.devices(site_id)  # Request every device type for family filtering.
        elif picker_name == "maps" and site_id is not None:  # Location channels target maps.
            payload = self._picker.maps(site_id)  # Preserve map identity for channel paths.
        elif picker_name == "assets" and site_id is not None:  # Diagnostics target site assets.
            payload = self._picker.assets(site_id)  # Preserve site-scoped asset identity.
        elif picker_name == "mxedges":  # Site or organization operations target Mist Edges.
            payload = self._picker.mxedges(site_id)  # Support both site and organization edge scopes.
        elif picker_name == "sdkclients" and site_id is not None:  # SDK clients require a verified map.
            return self._sdkclient_rows(site_id, parents)
        elif field is None and site_id is None:  # A catalog operation with no resource targets the organization.
            return [
                {
                    "id": "organization",
                    "label": "Organization",
                    "family": None,
                    "detail": None,
                    "target_type": "organization",
                }
            ], 0
        else:  # Do not guess an unsupported resource endpoint.
            raise StreamRequestError("picker_unavailable", "The catalog target has no supported picker.")  # Refuse.
        rows = payload.get("rows")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            # A complete response must contain only target mappings.
            raise StreamRequestError(
                "picker_unavailable", "Mist returned an unsupported target list."
            )  # Refuse malformed rows.
        family = definition.family if isinstance(definition, UtilityDefinition) else None
        eligible = [dict(row) for row in rows if family is None or row.get("family") == family]
        excluded = len(rows) - len(eligible)
        target_type = "sdkclient" if picker_name == "sdkclients" else picker_name.rstrip("s")
        for row in eligible:
            row["target_type"] = target_type  # Keep the source resource type on each target.
            if site_id is not None:
                row["site_id"] = site_id  # Keep site identity in every cross-site row.
        return eligible, excluded

    def _sdkclient_rows(self, site_id: str, parents: dict[str, str]) -> tuple[list[dict[str, object]], int]:
        """Read SDK clients only from maps that belong to the selected site."""
        maps = self._picker.maps(site_id)["rows"]  # Read complete map rows before client discovery.
        map_id = parents.get("map_id")
        if map_id is not None:
            maps = [row for row in maps if row.get("id") == map_id]
            if not maps:  # Reject a map that does not belong to this site.
                raise StreamRequestError(
                    "bad_request", "The map is not part of this site.", {"field": "map_id"}
                )  # Keep scope errors explicit.
        rows: list[dict[str, object]] = []
        for map_row in maps:
            clients = self._picker.sdkclients(site_id, str(map_row["id"]))["rows"]
            for client in clients:
                row = dict(client)
                row.update({"target_type": "sdkclient", "site_id": site_id, "map_id": map_row["id"]})  # Keep parents.
                rows.append(row)  # Retain the client with its map association.
        return rows, 0

    def _response(self, rows: list[dict[str, object]], site_id: str | None, excluded: int) -> dict[str, object]:
        """Return the complete target response with explicit exclusions."""
        unique: dict[tuple[object, ...], dict[str, object]] = {}  # Deduplicate by the complete natural target key.
        for row in rows:
            identity = (row.get("target_type"), row.get("site_id"), row.get("map_id"), row.get("id"))
            unique.setdefault(identity, row)  # Keep identical clients separate when their parents differ.
        rows = list(unique.values())
        rows.sort(key=lambda row: (str(row.get("label") or "").casefold(), str(row.get("id") or "")))
        reason = None if rows else "The site has no eligible targets."  # Keep a complete empty result explicit.
        return {
            "rows": rows,  # Return only complete, deduplicated target rows.
            "total_count": len(rows),  # Keep the count aligned with the result.
            "complete": True,  # The resolver returns only after every picker succeeds.
            "reason": reason,  # Distinguish a complete empty list from a failed request.
            "excluded": {"incompatible_family": excluded},  # Report family exclusions separately.
            "scope": {"site_id": site_id} if site_id is not None else {"organization": True},  # Keep scope explicit.
        }
