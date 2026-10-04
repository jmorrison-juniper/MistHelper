"""The WebSocket channel catalog for the Operations portal.

Why:
    Issue #3551. The portal must start streams from checked catalog keys only.
    This module keeps the 18 channel definitions in page order. It keeps each
    Mist channel path on the server.
"""

from __future__ import annotations  # Postponed annotations keep each hint import-safe.

import logging  # The portal uses standard logging for each action.
from typing import cast  # Row table values need a precise local type.

from src.mist.realtime.websocket_streams.catalog.model import (
    ChannelDefinition,
    FieldKind,
    FieldSpec,
)  # Catalog records.

logger = logging.getLogger(__name__)  # Keep catalog log records under this module name.


class ChannelCatalog:
    """Hold the Mist WebSocket channel definitions."""

    _ROWS = (
        (
            "org.pcaps",
            "organization",
            "Organization packet captures",
            "Live packet capture events for the organization.",
            "/orgs/{org_id}/pcaps",
            (),
            None,
        ),
        (
            "org.insights.summary",
            "organization",
            "Organization insight summary",
            "Live insight summary events for the organization.",
            "/orgs/{org_id}/insights/summary",
            (),
            None,
        ),
        (
            "org.stats.mxedges",
            "organization",
            "Organization Mist Edge statistics",
            "Live Mist Edge statistics for the organization.",
            "/orgs/{org_id}/stats/mxedges",
            (),
            None,
        ),
        (
            "org.mxedges",
            "organization",
            "Organization Mist Edges",
            "Live Mist Edge events for the organization.",
            "/orgs/{org_id}/mxedges",
            (),
            None,
        ),
        (
            "site.stats.clients",
            "site",
            "Client statistics",
            "Live client statistics for each selected site.",
            "/sites/{site_id}/stats/clients",
            (("site_id", "Site", "sites"),),
            "site_id",
        ),
        (
            "site.stats.devices",
            "site",
            "Device statistics",
            "Live device statistics for each selected site.",
            "/sites/{site_id}/stats/devices",
            (("site_id", "Site", "sites"),),
            "site_id",
        ),
        (
            "site.devices",
            "site",
            "Device events",
            "Live device events for each selected site.",
            "/sites/{site_id}/devices",
            (("site_id", "Site", "sites"),),
            "site_id",
        ),
        (
            "site.devices.cmd",
            "site",
            "Device command events",
            "Live command output for each selected device.",
            "/sites/{site_id}/devices/{device_id}/cmd",
            (("site_id", "Site", "sites"), ("device_id", "Device", "devices")),
            "device_id",
        ),
        (
            "site.stats.mxedges",
            "site",
            "Site Mist Edge statistics",
            "Live Mist Edge statistics for each selected site.",
            "/sites/{site_id}/stats/mxedges",
            (("site_id", "Site", "sites"),),
            "site_id",
        ),
        (
            "site.mxedges",
            "site",
            "Site Mist Edges",
            "Live Mist Edge events for each selected site.",
            "/sites/{site_id}/mxedges",
            (("site_id", "Site", "sites"),),
            "site_id",
        ),
        (
            "site.pcaps",
            "site",
            "Site packet captures",
            "Live packet capture events for each selected site.",
            "/sites/{site_id}/pcaps",
            (("site_id", "Site", "sites"),),
            "site_id",
        ),
        (
            "location.assets",
            "location",
            "BLE asset events",
            "Live BLE asset events for each selected map.",
            "/sites/{site_id}/stats/maps/{map_id}/assets",
            (("site_id", "Site", "sites"), ("map_id", "Map", "maps")),
            "map_id",
        ),
        (
            "location.clients",
            "location",
            "Location client events",
            "Live connected client events for each selected map.",
            "/sites/{site_id}/stats/maps/{map_id}/clients",
            (("site_id", "Site", "sites"), ("map_id", "Map", "maps")),
            "map_id",
        ),
        (
            "location.sdkclients",
            "location",
            "SDK client events",
            "Live SDK client events for each selected map.",
            "/sites/{site_id}/stats/maps/{map_id}/sdkclients",
            (("site_id", "Site", "sites"), ("map_id", "Map", "maps")),
            "map_id",
        ),
        (
            "location.unconnected_clients",
            "location",
            "Unconnected client events",
            "Live unconnected client events for each selected map.",
            "/sites/{site_id}/stats/maps/{map_id}/unconnected_clients",
            (("site_id", "Site", "sites"), ("map_id", "Map", "maps")),
            "map_id",
        ),
        (
            "location.discovered_assets",
            "location",
            "Discovered BLE asset events",
            "Live discovered BLE asset events for each selected map.",
            "/sites/{site_id}/stats/maps/{map_id}/discovered_assets",
            (("site_id", "Site", "sites"), ("map_id", "Map", "maps")),
            "map_id",
        ),
        (
            "diag.asset",
            "diagnostics",
            "Asset diagnostics",
            "Live RF Glass diagnostics for one BLE asset.",
            "/sites/{site_id}/assets/{asset_id}/diag",
            (("site_id", "Site", "sites"), ("asset_id", "Asset", "assets")),
            None,
        ),
        (
            "diag.sdkclient",
            "diagnostics",
            "SDK client diagnostics",
            "Live RF Glass diagnostics for one SDK client.",
            "/sites/{site_id}/sdkclients/{sdkclient_id}/diag",
            (("site_id", "Site", "sites"), ("map_id", "Map", "maps"), ("sdkclient_id", "SDK client", "sdkclients")),
            None,
        ),
    )

    def __init__(self) -> None:
        """Build the channel lookup table."""
        logger.info("Building the WebSocket channel catalog")  # Log before building the catalog.
        self._entries = tuple(self._build_entry(row) for row in self._ROWS)  # Build records once.
        self._by_key = {entry.key: entry for entry in self._entries}  # Give constant-time lookup by key.
        logger.debug("Built %s WebSocket channel entries", len(self._entries))  # Log the catalog size.

    def entries(self) -> tuple[ChannelDefinition, ...]:
        """Return all channel definitions in page order.

        Returns:
            The immutable channel records.
        """
        logger.info("Reading the WebSocket channel catalog")  # Log before returning the catalog.
        logger.debug("Read %s WebSocket channel entries", len(self._entries))  # Log the result count.
        return self._entries  # The tuple prevents caller changes.

    def get(self, key: str) -> ChannelDefinition | None:
        """Return one channel definition.

        Args:
            key: The catalog key to find.

        Returns:
            The channel definition, or None when the key is unknown.
        """
        logger.info("Finding WebSocket channel key %s", key)  # Log before lookup.
        entry = self._by_key.get(key)  # Read the immutable lookup table.
        logger.debug("WebSocket channel key %s found: %s", key, entry is not None)  # Log lookup result.
        return entry  # The caller handles an unknown key.

    @classmethod
    def _build_entry(cls, row: tuple[object, ...]) -> ChannelDefinition:
        """Build one channel definition from the row table.

        Args:
            row: One table row from the SDK-backed channel list.

        Returns:
            One channel definition.
        """
        key, scope, name, description, path_template, identifiers, repeatable = row  # Unpack the row by contract order.
        identifier_rows = cast(tuple[tuple[str, str, str], ...], identifiers)  # Give mypy the identifier row shape.
        fields = tuple(
            cls._identifier(*identifier) for identifier in identifier_rows
        )  # Build checked identifier fields.
        safe_repeatable = (
            repeatable if isinstance(repeatable, str) else None
        )  # Keep repeatable absent when the row uses None.
        return ChannelDefinition(
            str(key), str(scope), str(name), str(description), str(path_template), fields, safe_repeatable
        )  # Return the frozen record.

    @staticmethod
    def _identifier(name: str, label: str, picker: str) -> FieldSpec:
        """Build one UUID identifier field.

        Args:
            name: The identifier key in the request body.
            label: The label that the page shows.
            picker: The picker route that fills the value.

        Returns:
            One required UUID field.
        """
        return FieldSpec(
            name=name, label=label, kind=FieldKind.UUID, required=True, picker=picker
        )  # Each target is a required UUID.
