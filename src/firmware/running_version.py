"""Read the running firmware version of a Mist device from an endpoint that reports it.

Why:
    Three cloud endpoints report a firmware version for one device, and they do
    not agree. ``listSiteDevices`` returns the device configuration object, so
    its ``version`` field names the configured version. That value can name a
    release the device left long ago, or it can be ``None``.
    ``listSiteDevicesStats`` and ``getOrgInventory`` report the running state,
    and they agree with the device.

    A firmware decision that reads the configured version can turn a one-step
    upgrade into an apparent multi-release jump. An operator then plans the
    wrong change on production hardware. This module gives every firmware
    decision one reader that returns the running version, or that marks the
    value as stale.

Endpoint rule:
    - ``listSiteDevicesStats`` reports the running version. Use it for a site.
    - ``getOrgInventory`` reports the running version. Use it for an org.
    - ``listSiteDevices`` reports the configured version. Never use it for a
      firmware decision.

Second trap:
    ``listSiteDevices`` and ``listSiteDevicesStats`` both default to access
    points. A switch or a gateway needs ``type="all"``. This module always
    sends ``type="all"`` so no device type is dropped.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

DEVICE_LISTING_ENDPOINT = "listSiteDevices"  # WHY: name the endpoint that reports the configured version
SITE_STATS_ENDPOINT = "listSiteDevicesStats"  # WHY: name the site endpoint that reports the running version
ORG_INVENTORY_ENDPOINT = "getOrgInventory"  # WHY: name the org endpoint that reports the running version

RUNNING_VERSION_ENDPOINTS = frozenset(
    {SITE_STATS_ENDPOINT, ORG_INVENTORY_ENDPOINT}
)  # WHY: one allow list keeps every caller on the same rule

DEFAULT_STATS_PAGE_LIMIT = 1000  # WHY: one large page keeps the site call to a single request


@dataclass(frozen=True)
class FirmwareVersionReading:
    """One firmware version value with the endpoint that produced it.

    Attributes:
        value: The version string. It is empty when no endpoint reported one.
        source: The endpoint name that produced the value.
        is_running: True when the source reports the running version.
    """

    value: str  # WHY: the caller displays this string and compares it to the target
    source: str  # WHY: the caller records which endpoint produced the value
    is_running: bool  # WHY: the caller must refuse a stale value for a firmware decision


class RunningFirmwareVersionResolver:
    """Return the running firmware version of a device, or mark the value stale.

    Why:
        A firmware decision needs the version the device runs now. This class
        holds the single rule about which endpoint reports that value, so no
        caller has to remember the trap.
    """

    def __init__(self, apisession: Any, stats_fn: Callable[..., Any] | None = None) -> None:
        """Store the session and the stats callable.

        Args:
            apisession: The live mistapi session.
            stats_fn: The callable that reads the site stats endpoint. Leave it
                unset to use ``mistapi.api.v1.sites.stats.listSiteDevicesStats``.
        """
        self._apisession = apisession  # WHY: every endpoint call needs the live session
        self._stats_fn = stats_fn  # WHY: a test injects a stand-in without a network call

    @staticmethod
    def reports_running_version(source: str) -> bool:
        """Return True when the named endpoint reports the running version.

        Args:
            source: The endpoint name to check.

        Returns:
            True when a firmware decision may read the version of that endpoint.
        """
        return source in RUNNING_VERSION_ENDPOINTS  # WHY: one allow list decides for every caller

    @staticmethod
    def index_stats_rows(rows: list[dict[str, Any]]) -> dict[str, str]:
        """Index stats rows by device id and by MAC address.

        Why:
            A device listing row and a stats row do not always share the same
            identifier field. Two keys let the caller join on either one.

        Args:
            rows: The stats rows returned by the stats endpoint.

        Returns:
            A map of device id or MAC address to the running version string.
        """
        logging.info("Indexing device stats rows for a running version lookup rows=%d", len(rows))  # WHY: entry audit
        running_by_key: dict[str, str] = {}  # WHY: accumulate one map that both key shapes can reach
        for row in rows:  # WHY: a single pass keeps the cost linear in the row count
            version = str(row.get("version") or "")  # WHY: normalize a missing version to an empty string
            if not version:  # WHY: an empty version cannot support a firmware decision
                continue  # WHY: skip the row rather than store a false reading
            for key in (row.get("id"), row.get("device_id"), row.get("mac")):  # WHY: accept every join key shape
                if key:  # WHY: skip an absent identifier
                    running_by_key[str(key)] = version  # WHY: store the running version under each usable key
        logging.debug("Indexed running versions keys=%d", len(running_by_key))  # WHY: exit audit
        return running_by_key  # WHY: the caller joins device rows against this map

    def fetch_site_running_versions(self, site_id: str) -> dict[str, str]:
        """Read the running version of every device at one site.

        Args:
            site_id: The site to read.

        Returns:
            A map of device id or MAC address to the running version string. The
            map is empty when the endpoint fails, so the caller can fall back.
        """
        logging.info("Reading running firmware versions from %s site=%s", SITE_STATS_ENDPOINT, site_id)  # WHY: audit
        stats_fn = self._resolve_stats_fn()  # WHY: pick the injected callable or the real endpoint
        try:  # WHY: a network call can raise, and a firmware flow must not stop here
            response = stats_fn(
                self._apisession, site_id, type="all", limit=DEFAULT_STATS_PAGE_LIMIT
            )  # WHY: type=all keeps switches and gateways in the result
        except Exception as error:  # WHY: a broad guard keeps the caller on its fallback path
            logging.error("Failed to read %s for site %s: %s", SITE_STATS_ENDPOINT, site_id, error)  # WHY: audit
            return {}  # WHY: an empty map tells the caller that no running version was read
        rows = self._rows_from_response(response, site_id)  # WHY: one helper handles the status and payload shape
        running_by_key = self.index_stats_rows(rows)  # WHY: build the join map for the caller
        logging.debug("Read running versions site=%s keys=%d", site_id, len(running_by_key))  # WHY: exit audit
        return running_by_key  # WHY: the caller overlays these values onto its device rows

    def read(self, device_row: dict[str, Any], running_by_key: dict[str, str]) -> FirmwareVersionReading:
        """Return the running version for one device row, or a stale reading.

        Why:
            The ``version`` field of a device listing row names the configured
            version. This method never presents that value as running.

        Args:
            device_row: One device row, which may come from the device listing.
            running_by_key: The map built by ``fetch_site_running_versions``.

        Returns:
            A reading whose ``is_running`` flag states whether the caller may
            use the value for a firmware decision.
        """
        for key in (device_row.get("id"), device_row.get("device_id"), device_row.get("mac")):  # WHY: try each key
            running = running_by_key.get(str(key)) if key else None  # WHY: only look up a present identifier
            if running:  # WHY: the first hit is the running version
                return FirmwareVersionReading(running, SITE_STATS_ENDPOINT, True)  # WHY: safe for a decision
        listed = str(device_row.get("version") or "")  # WHY: the listing value is the only value that remains
        logging.warning(
            "No running version for device %s. The %s value %s is stale.",
            device_row.get("id", "unknown"),
            DEVICE_LISTING_ENDPOINT,
            listed or "None",
        )  # WHY: an operator must see that this value did not come from the running state
        return FirmwareVersionReading(listed, DEVICE_LISTING_ENDPOINT, False)  # WHY: mark the value as stale

    def _resolve_stats_fn(self) -> Callable[..., Any]:
        """Return the injected stats callable, or the real mistapi endpoint."""
        if self._stats_fn is not None:  # WHY: an injected callable wins so a test needs no network
            return self._stats_fn  # WHY: hand back the stand-in
        import mistapi.api.v1.sites.stats as _site_stats  # WHY: a lazy import keeps module load cheap

        stats_fn: Callable[..., Any] = _site_stats.listSiteDevicesStats  # WHY: narrow the untyped module attribute
        return stats_fn  # WHY: the real endpoint that reports the running version

    @staticmethod
    def _rows_from_response(response: Any, site_id: str) -> list[dict[str, Any]]:
        """Return the stats rows of a response, or an empty list.

        Args:
            response: The object returned by the stats endpoint.
            site_id: The site under read, used only for the log line.

        Returns:
            The list of stats rows.
        """
        status = getattr(response, "status_code", 200)  # WHY: a stand-in response may omit the status
        if status != 200:  # WHY: a non-200 status carries no usable rows
            logging.error("The %s call for site %s returned %s", SITE_STATS_ENDPOINT, site_id, status)  # WHY: audit
            return []  # WHY: an empty list drives the caller onto its fallback
        data = getattr(response, "data", None) or []  # WHY: normalize a missing payload to an empty list
        return [row for row in data if isinstance(row, dict)]  # WHY: drop any row shape the caller cannot read
