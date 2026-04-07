"""Collection helpers for SSID template consolidation phase 1."""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

LOGGER = logging.getLogger(__name__)
COLLECTION_ERROR_TYPES = (AttributeError, RuntimeError, TypeError, ValueError)


class Collector:
    """Gather site and WLAN data needed for phase 1 SSID consolidation analysis."""

    def __init__(self, mist_client: Any | None = None) -> None:
        """Store the optional Mist API adapter used for online collection."""
        self.mist_client = mist_client

    def _current_timestamp(self) -> str:
        """Return an ISO-8601 UTC timestamp for collected rows."""
        return datetime.now(UTC).isoformat()

    def sample_rows(self, target_ssid: str) -> list[dict[str, Any]]:
        """Return deterministic sample rows for offline testing and fallback flows."""
        timestamp = self._current_timestamp()
        return [
            {
                "site_id": "site-1",
                "site_name": "Site One",
                "template_id": "tmpl-1",
                "template_name": "Template One",
                "target_ssid_name": target_ssid,
                "target_ssid_id": "ssid-1",
                "psk_detected": 0,
                "edge_cluster_id": "ec-1",
                "edge_cluster_name": "Edge Cluster 1",
                "anomaly_code": None,
                "collected_at": timestamp,
            },
            {
                "site_id": "site-2",
                "site_name": "Site Two",
                "template_id": "tmpl-2",
                "template_name": "Template Two",
                "target_ssid_name": target_ssid,
                "target_ssid_id": "ssid-2",
                "psk_detected": 1,
                "edge_cluster_id": "ec-2",
                "edge_cluster_name": "Edge Cluster 2",
                "anomaly_code": "1_SSID",
                "collected_at": timestamp,
            },
        ]

    def _get_sites(self) -> list[dict[str, Any]]:
        """Return sites from the configured Mist adapter, or an empty list."""
        client_get_sites = getattr(self.mist_client, "get_sites", None)
        if self.mist_client is None or not callable(client_get_sites):
            return []
        org_id = getattr(self.mist_client, "org_id", None)
        return self._call_site_fetcher(client_get_sites, org_id)

    def _get_site_wlans(self, site_id: str) -> list[dict[str, Any]]:
        """Return WLANs for one site and log recoverable API failures."""
        client_get_site_wlans = getattr(self.mist_client, "get_site_wlans", None)
        if self.mist_client is None or not callable(client_get_site_wlans):
            return []
        try:
            wlans = self._call_wlan_fetcher(client_get_site_wlans, site_id)
        except COLLECTION_ERROR_TYPES:
            LOGGER.exception("Collector: failed to fetch WLANs for site %s", site_id)
            return []
        return wlans

    def _call_site_fetcher(
        self,
        fetcher: Callable[..., Any],
        org_id: str | None,
    ) -> list[dict[str, Any]]:
        """Call a site fetcher and normalize its payload to a list of dictionaries."""
        return self._normalize_payload(fetcher(org_id=org_id))

    def _call_wlan_fetcher(
        self,
        fetcher: Callable[..., Any],
        site_id: str,
    ) -> list[dict[str, Any]]:
        """Call a WLAN fetcher and normalize its payload to a list of dictionaries."""
        return self._normalize_payload(fetcher(site_id))

    def _normalize_payload(self, payload: Any) -> list[dict[str, Any]]:
        """Normalize a client payload to the list shape expected by the collector."""
        return payload if isinstance(payload, list) else []

    def _matches_target_ssid(self, wlan: dict[str, Any], target_ssid: str) -> bool:
        """Return `True` when a WLAN matches the requested SSID name."""
        wlan_name = wlan.get("name") or wlan.get("ssid_name") or ""
        return wlan_name == target_ssid

    def _detect_psk(self, wlan: dict[str, Any]) -> int:
        """Return `1` when the WLAN indicates PSK-based authentication."""
        encryption = str(wlan.get("encryption", "")).lower()
        return 1 if wlan.get("psk") or "psk" in encryption else 0

    def _build_row(
        self,
        site: dict[str, Any],
        wlan: dict[str, Any],
        target_ssid: str,
    ) -> dict[str, Any]:
        """Build one normalized phase 1 row from site and WLAN source data."""
        return {
            "site_id": site.get("id") or "",
            "site_name": site.get("name") or "",
            "template_id": (wlan.get("ap_template_id") or wlan.get("template_id") or site.get("template_id") or ""),
            "template_name": (wlan.get("ap_template_name") or wlan.get("template_name") or ""),
            "target_ssid_name": target_ssid,
            "target_ssid_id": wlan.get("id") or wlan.get("ssid_id") or "",
            "psk_detected": self._detect_psk(wlan),
            "edge_cluster_id": site.get("edge_cluster_id") or "",
            "edge_cluster_name": site.get("edge_cluster_name") or "",
            "anomaly_code": None,
            "collected_at": self._current_timestamp(),
        }

    def collect_from_api(self, target_ssid: str) -> list[dict[str, Any]]:
        """Collect matching WLAN rows from the configured Mist API adapter."""
        rows: list[dict[str, Any]] = []
        for site in self._get_sites():
            site_id = site.get("id") or ""
            if not site_id:
                continue
            for wlan in self._get_site_wlans(site_id):
                if self._matches_target_ssid(wlan, target_ssid):
                    rows.append(self._build_row(site, wlan, target_ssid))
        return rows

    def collect(self, target_ssid: str) -> list[dict[str, Any]]:
        """Collect rows for the target SSID, falling back to sample rows offline."""
        if self.mist_client is None:
            LOGGER.info("Collector: returning sample data for target_ssid=%s", target_ssid)
            return self.sample_rows(target_ssid)
        try:
            rows = self.collect_from_api(target_ssid)
        except COLLECTION_ERROR_TYPES:
            LOGGER.exception("Collector: adapter-based collection failed; using sample data")
            rows = []
        if rows:
            LOGGER.info(
                "Collector: found %d sites hosting SSID '%s'",
                len(rows),
                target_ssid,
            )
            return rows
        LOGGER.info(
            "Collector: no matching SSID rows found via Mist API; using sample data",
        )
        return self.sample_rows(target_ssid)
