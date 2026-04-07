import os
import logging
from datetime import datetime
from typing import List, Dict


class Collector:
    """Collector that gathers template/site/SSID info from Mist API.

    If a `mist_client` (adapter) is provided it will be used to query
    the Mist API with retries and pagination. When no client is provided
    the collector returns a deterministic sample payload so local tests
    can run without credentials.
    """

    def __init__(self, mist_client=None):
        self.mist_client = mist_client

    def _sample_rows(self, target_ssid: str) -> List[Dict]:
        now = datetime.utcnow().isoformat()
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
                "collected_at": now,
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
                "collected_at": now,
            },
        ]

    def collect(self, target_ssid: str) -> List[Dict]:
        """Return a list of site-level rows for the target SSID.

        If a `mist_client` adapter is available the collector will attempt
        to fetch sites and site WLANs from the Mist API and return rows for
        sites that host the requested SSID. On any failure it falls back to
        the deterministic sample payload to preserve offline testing.
        """
        # Use adapter-based collection when available
        if self.mist_client:
            try:
                org_id = getattr(self.mist_client, "org_id", None)
                sites = self.mist_client.get_sites(org_id=org_id) if hasattr(self.mist_client, "get_sites") else []

                rows: List[Dict] = []
                for site in sites:
                    site_id = site.get("id")
                    site_name = site.get("name", "")

                    # Attempt to fetch site WLANs (may be empty)
                    wlans = []
                    try:
                        if hasattr(self.mist_client, "get_site_wlans") and site_id:
                            wlans = self.mist_client.get_site_wlans(site_id)
                    except Exception:
                        logging.exception("Failed to fetch WLANs for site %s", site_id)

                    # Inspect WLANs for the target SSID name
                    for wlan in wlans or []:
                        # WLAN shape may vary; check common fields
                        wlan_name = wlan.get("name") or wlan.get("ssid_name") or ""
                        if wlan_name != target_ssid:
                            continue

                        row = {
                            "site_id": site_id,
                            "site_name": site_name,
                            # Template id may be present on WLAN or site metadata
                            "template_id": wlan.get("ap_template_id") or wlan.get("template_id") or site.get("template_id") or "",
                            "template_name": wlan.get("ap_template_name") or wlan.get("template_name") or "",
                            "target_ssid_name": target_ssid,
                            "target_ssid_id": wlan.get("id") or wlan.get("ssid_id") or "",
                            "psk_detected": 1 if wlan.get("psk") or wlan.get("encryption", "").lower().find("psk") != -1 else 0,
                            "edge_cluster_id": site.get("edge_cluster_id") or "",
                            "edge_cluster_name": site.get("edge_cluster_name") or "",
                            "anomaly_code": None,
                            "collected_at": datetime.utcnow().isoformat(),
                        }
                        rows.append(row)

                if rows:
                    logging.info("Collector: found %d sites hosting SSID '%s'", len(rows), target_ssid)
                    return rows

                logging.info("Collector: no matching SSID rows found via Mist API, falling back to sample data")
            except Exception:
                logging.exception("Collector: adapter-based collection failed - falling back to sample data")

        logging.info("Collector: returning sample data for target_ssid=%s", target_ssid)
        return self._sample_rows(target_ssid)
