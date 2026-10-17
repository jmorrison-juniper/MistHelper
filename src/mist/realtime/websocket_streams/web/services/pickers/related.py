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
        payload = cast(dict[str, object], self._picker.sites())  # Read all authenticated organization pages.
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
        self._resources = BatchTargetResourceReader(picker)  # Resource selection retains complete picker results.
        self._responses = BatchTargetResponseBuilder()  # One response builder owns stable target ordering.

    def discover(self, site_id: str | None, kind: str, key: str, parents: dict[str, str]) -> dict[str, object]:
        """Return operation targets after complete scope validation."""
        definition, target_field = self._target_field(kind, key, parents)  # Validate server-owned target metadata.
        if site_id is None:
            rows, excluded = self._organization_rows(target_field, parents, definition)
        else:
            rows, excluded = self._site_rows(site_id, target_field, parents, definition)
        return self._responses.build(rows, site_id, excluded)  # Keep the final contract complete and stable.

    def _target_field(self, kind: str, key: str, parents: dict[str, str]) -> tuple[Any, Any | None]:
        """Resolve the catalog operation and validate its parent fields."""
        definition = self._catalog.find(kind, key)  # Resolve only server-owned catalog metadata.
        if definition is None:  # Reject unknown operation keys before any picker call.
            raise StreamRequestError("unknown_key", "The selected catalog operation is not available.")  # Refuse.
        fields = definition.identifiers if isinstance(definition, ChannelDefinition) else definition.targets
        target_field = next((field for field in reversed(fields) if field.name != "site_id"), None)
        allowed_parents = {"map_id"} if target_field is not None and target_field.picker == "sdkclients" else set()
        if set(parents) - allowed_parents:  # Parent values must match the catalog resource relationship.
            raise StreamRequestError("bad_request", "The target request has an unsupported parent.")  # Refuse.
        return definition, target_field  # Keep all further reads inside the selected catalog contract.

    def _organization_rows(
        self, target_field: Any | None, parents: dict[str, str], definition: Any
    ) -> tuple[list[dict[str, object]], int]:
        """Return organization targets only for an organization-scoped operation."""
        if getattr(definition, "scope", "") != "organization":  # Do not widen a site operation.
            raise StreamRequestError("bad_request", "This operation requires a site.", {"field": "site_id"})
        if target_field is None:  # Organization operations without resource targets use one explicit row.
            return [
                {
                    "id": "organization",
                    "label": "Organization",
                    "family": None,
                    "detail": None,
                    "target_type": "organization",
                }
            ], 0
        return self._resources.read(target_field, None, parents, definition)  # Read the selected org resource.

    def _site_rows(
        self, site_id: str, target_field: Any | None, parents: dict[str, str], definition: Any
    ) -> tuple[list[dict[str, object]], int]:
        """Verify organization membership before reading any selected-site resource."""
        sites = self._picker.sites()["rows"]  # Verify scope against every authenticated organization page.
        site = next((row for row in sites if row.get("id") == site_id), None)
        if site is None:  # Reject a foreign site before its resource list is read.
            raise StreamRequestError("bad_request", "The site is not part of this organization.", {"field": "site_id"})
        if target_field is None:
            return [
                {
                    "id": site["id"],
                    "label": site.get("label") or site.get("name") or site["id"],
                    "family": None,
                    "detail": site.get("detail"),
                    "site_id": site["id"],
                    "target_type": "site",
                }
            ], 0
        return self._resources.read(target_field, site_id, parents, definition)  # Read only after scope validation.


class BatchTargetResourceReader:
    """Read picker resources and add their catalog-approved target scope."""

    def __init__(self, picker: Any) -> None:
        """Store the authenticated picker collaborator."""
        self._picker = picker  # Existing picker methods own SDK authentication and pagination.

    def read(
        self, field: Any, site_id: str | None, parents: dict[str, str], definition: Any
    ) -> tuple[list[dict[str, object]], int]:
        """Return scoped target rows or verified SDK clients."""
        if field.picker == "sdkclients" and site_id is not None:  # SDK clients require a selected site and map.
            return self._sdkclient_rows(site_id, parents)  # Keep explicit map association checks.
        payload = self._picker_payload(field.picker, site_id)  # Select only catalog-supported picker methods.
        return self._eligible_rows(payload, field.picker, site_id, definition)  # Filter families and attach scope.

    def _picker_payload(self, picker_name: str, site_id: str | None) -> dict[str, object]:
        """Call the matching authenticated picker or refuse unsupported scope."""
        if picker_name == "devices" and site_id is not None:
            return cast(
                dict[str, object], self._picker.devices(site_id)
            )  # Request the full inventory before family filtering.
        if picker_name == "maps" and site_id is not None:
            return cast(dict[str, object], self._picker.maps(site_id))  # Keep map identity for channel paths.
        if picker_name == "assets" and site_id is not None:
            return cast(dict[str, object], self._picker.assets(site_id))  # Preserve site-scoped asset identity.
        if picker_name == "mxedges":  # Mist Edge operations support site and organization scopes.
            return cast(dict[str, object], self._picker.mxedges(site_id))  # Preserve the selected scope.
        raise StreamRequestError("picker_unavailable", "The catalog target has no supported picker.")  # Refuse.

    def _eligible_rows(
        self, payload: dict[str, object], picker_name: str, site_id: str | None, definition: Any
    ) -> tuple[list[dict[str, object]], int]:
        """Validate picker rows, filter utility families, and attach target scope."""
        rows = BatchTargetResponseBuilder.validate(payload)  # Reject incomplete and malformed picker results.
        eligible = BatchTargetResponseBuilder.family_rows(rows, definition)  # Keep only catalog-compatible targets.
        BatchTargetResponseBuilder.apply_scope(eligible, picker_name, site_id)  # Preserve each target identity.
        return eligible, len(rows) - len(eligible)  # Report every family excluded from the result.

    def _sdkclient_rows(self, site_id: str, parents: dict[str, str]) -> tuple[list[dict[str, object]], int]:
        """Read SDK clients only from maps that belong to the selected site."""
        maps = self._picker.maps(site_id)["rows"]  # Read complete map rows before client discovery.
        map_id = parents.get("map_id")
        if map_id is not None:
            maps = [row for row in maps if row.get("id") == map_id]
            if not maps:  # Reject a map that does not belong to this site.
                raise StreamRequestError("bad_request", "The map is not part of this site.", {"field": "map_id"})
        rows = [
            dict(client) | {"target_type": "sdkclient", "site_id": site_id, "map_id": map_row["id"]}
            for map_row in maps
            for client in self._picker.sdkclients(site_id, str(map_row["id"]))["rows"]
        ]  # Retain each client with its verified map and site association.
        return rows, 0  # SDK client rows have no family exclusions.


class BatchTargetResponseBuilder:
    """Build deterministic, complete target discovery responses."""

    @staticmethod
    def validate(payload: dict[str, object]) -> list[dict[str, object]]:
        """Reject incomplete or malformed picker rows."""
        rows = payload.get("rows")
        if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
            raise StreamRequestError("picker_unavailable", "Mist returned an unsupported target list.")
        return [dict(row) for row in rows]

    @staticmethod
    def family_rows(rows: list[dict[str, object]], definition: Any) -> list[dict[str, object]]:
        """Filter device rows by the catalog family when one applies."""
        family = definition.family if isinstance(definition, UtilityDefinition) else None
        return [row for row in rows if family is None or row.get("family") == family]

    @staticmethod
    def apply_scope(rows: list[dict[str, object]], picker_name: str, site_id: str | None) -> None:
        """Attach the resource type and selected site to each eligible row."""
        target_type = "mxedge" if picker_name == "mxedges" else picker_name.rstrip("s")
        for row in rows:
            row["target_type"] = target_type  # Keep the source resource type on each target.
            if site_id is not None:
                row["site_id"] = site_id  # Keep site identity in every cross-site row.

    @staticmethod
    def build(rows: list[dict[str, object]], site_id: str | None, excluded: int) -> dict[str, object]:
        """Return deduplicated rows and explicit completion metadata."""
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
