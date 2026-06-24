"""E911 BSSID compliance report generator.

Extracted from MistHelper.py per issue #219.
"""

import json
import logging
import os
import time
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any


class E911BSSIDReportGenerator:
    """E911 BSSID Compliance Report (Menu 160).

    Queries all AP radio MACs across the organization, resolves each AP's
    site name, site address, map/floor name, AP name, radio band info,
    and SSID names, then derives all BSSIDs (16 per radio MAC).  Output
    is a sorted CSV with one row per BSSID for E911 compliance filing.

    Columns: Site Name, Site Address, Map Name, AP Name, AP MAC, Band,
    Radio MAC, BSSID, SSIDs on Band.

    Rate-limit aware: saves progress to a checkpoint file after each
    batch of sites.  On HTTP 429 or resume, reloads the checkpoint and
    skips already-processed sites.  Org-level bulk queries are cached so
    only per-site enrichment (maps + WLANs) costs API calls on resume.
    """

    BSSIDS_PER_RADIO = 16
    NIBBLE_MASK = 0xFFFFFFFFFFF0
    BAND_MAP = {"24": "band_24", "5": "band_5", "6": "band_6"}
    BAND_LABELS = [
        ("band_24", "2.4 GHz"),
        ("band_5", "5 GHz"),
        ("band_6", "6 GHz"),
    ]
    CHECKPOINT_FILE = os.path.join("data", "e911_checkpoint.json")
    CHECKPOINT_INTERVAL = 50
    RADIO_BANDS_BY_COUNT = {
        3: [
            ("band_6", "6 GHz"),
            ("band_5", "5 GHz"),
            ("band_24", "2.4 GHz"),
        ],
        2: [("band_5", "5 GHz"), ("band_24", "2.4 GHz")],
        1: [("band_24", "2.4 GHz")],
    }

    @staticmethod
    def _format_bssid(radio_base_mac: str) -> list[str]:
        """Derive 16 colon-separated BSSIDs from a radio base MAC."""
        clean_mac = radio_base_mac.replace(":", "").replace("-", "")
        base_int = int(clean_mac, 16)
        cleared_base = base_int & E911BSSIDReportGenerator.NIBBLE_MASK
        bssids: list[str] = []
        for offset in range(E911BSSIDReportGenerator.BSSIDS_PER_RADIO):
            bssid_hex = format(cleared_base | offset, "012x")
            bssids.append(":".join(bssid_hex[i : i + 2] for i in range(0, 12, 2)))
        return bssids

    @staticmethod
    def _fetch_all_sites(
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> list[dict[str, Any]]:
        """Fetch all sites with pagination."""
        import mistapi  # noqa: E402  # lazy import

        response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=page_limit)
        return mistapi.get_all(response=response, mist_session=apisession)  # type: ignore[no-any-return]

    @staticmethod
    def _fetch_org_bulk_data(
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> dict[str, Any]:
        """Fetch all org-level data in bulk.

        These are the expensive bulk queries that only need to run once.
        Results are cached in the checkpoint file so they survive a 429.
        """
        import mistapi  # noqa: E402  # lazy import

        print("  Phase 1: Fetching org-level bulk data...")
        print("    Fetching site information...")
        all_sites = E911BSSIDReportGenerator._fetch_all_sites(apisession, org_id, page_limit)
        site_lookup = E911BSSIDReportGenerator._build_site_lookup(all_sites)
        logging.info("Sites fetched: %d", len(site_lookup))

        print("    Fetching AP inventory stats...")
        ap_lookup = E911BSSIDReportGenerator._fetch_ap_stats(apisession, org_id, page_limit)
        logging.info("AP device stats fetched: %d", len(ap_lookup))

        print("    Fetching org WLAN templates and org WLANs...")
        wlan_templates = E911BSSIDReportGenerator._fetch_org_wlan_templates(apisession, org_id)
        org_wlans = E911BSSIDReportGenerator._fetch_org_wlans(apisession, org_id, page_limit)
        logging.info(
            "Org templates: %d, org WLANs: %d",
            len(wlan_templates),
            len(org_wlans),
        )

        print("    Pre-fetching unique site template WLANs...")
        site_template_cache = E911BSSIDReportGenerator._prefetch_site_templates(apisession, org_id, site_lookup)
        logging.info("Cached %d unique site templates", len(site_template_cache))

        print("    Fetching AP radio MACs...")
        radio_response = mistapi.api.v1.orgs.devices.listOrgApsMacs(apisession, org_id, limit=page_limit)
        radio_macs_data: list[dict[str, Any]] = mistapi.get_all(response=radio_response, mist_session=apisession)
        logging.info("Radio MAC records fetched: %d", len(radio_macs_data))

        print("    Inferring radio bands from MAC positions...")
        radio_band_lookup = E911BSSIDReportGenerator._infer_radio_bands(radio_macs_data)
        logging.info("Radio bands inferred: %d broadcast radios", len(radio_band_lookup))

        return {
            "sites": site_lookup,
            "aps": ap_lookup,
            "wlan_templates": wlan_templates,
            "org_wlans": org_wlans,
            "site_template_cache": site_template_cache,
            "radio_macs": radio_macs_data,
            "radio_bands": radio_band_lookup,
        }

    @staticmethod
    def _build_site_lookup(
        all_sites: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Build site lookup dict from raw site list."""
        site_lookup: dict[str, dict[str, Any]] = {}
        for site in all_sites:
            site_id = site.get("id")
            if site_id:
                site_lookup[site_id] = {
                    "name": site.get("name", ""),
                    "address": site.get("address", ""),
                    "sitegroup_ids": site.get("sitegroup_ids") or [],
                    "sitetemplate_id": site.get("sitetemplate_id") or "",
                }
        return site_lookup

    @staticmethod
    def _fetch_ap_stats(
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> dict[str, dict[str, str]]:
        """Fetch AP inventory stats and build lookup dict."""
        import mistapi  # noqa: E402  # lazy import

        stats_response = mistapi.api.v1.orgs.stats.listOrgDevicesStats(apisession, org_id, type="ap", limit=page_limit)
        all_ap_stats: list[dict[str, Any]] = mistapi.get_all(response=stats_response, mist_session=apisession)
        ap_lookup: dict[str, dict[str, str]] = {}
        for device in all_ap_stats:
            device_mac = device.get("mac")
            if device_mac:
                ap_lookup[device_mac] = {
                    "name": device.get("name", ""),
                    "site_id": device.get("site_id") or "",
                    "map_id": device.get("map_id") or "",
                }
        return ap_lookup

    @staticmethod
    def _prefetch_site_templates(
        apisession: Any,
        org_id: str,
        site_lookup: dict[str, dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Pre-fetch WLANs for each unique site template."""
        import mistapi  # noqa: E402  # lazy import

        unique_ids = {info["sitetemplate_id"] for info in site_lookup.values() if info.get("sitetemplate_id")}
        cache: dict[str, list[dict[str, Any]]] = {}
        for sitetemplate_id in unique_ids:
            try:
                response = mistapi.api.v1.orgs.sitetemplates.getOrgSiteTemplate(apisession, org_id, sitetemplate_id)
                if hasattr(response, "status_code") and response.status_code == 200:
                    template_wlans = response.data.get("wlans", {})
                    if isinstance(template_wlans, dict):
                        cache[sitetemplate_id] = list(template_wlans.values())
                    else:
                        cache[sitetemplate_id] = []
                else:
                    cache[sitetemplate_id] = []
            except Exception as error:
                logging.debug(
                    "Failed to fetch site template %s: %s",
                    sitetemplate_id[:8],
                    error,
                )
                cache[sitetemplate_id] = []
        return cache

    @staticmethod
    def _infer_radio_bands(
        radio_macs_data: list[dict[str, Any]],
    ) -> dict[str, dict[str, str]]:
        """Infer radio band from MAC array position (last radio is always scanning)."""
        band_orders = E911BSSIDReportGenerator.RADIO_BANDS_BY_COUNT
        radio_band_lookup: dict[str, dict[str, str]] = {}
        for ap_entry in radio_macs_data:
            all_radios = ap_entry.get("radio_mac", [])
            if len(all_radios) < 2:
                continue
            broadcast_radios = all_radios[:-1]
            bands = band_orders.get(len(broadcast_radios), [])
            for index, radio_mac in enumerate(broadcast_radios):
                if index < len(bands):
                    band_key, band_label = bands[index]
                    radio_band_lookup[radio_mac] = {
                        "band": band_label,
                        "band_key": band_key,
                    }
        return radio_band_lookup

    @staticmethod
    def _save_checkpoint(
        org_id: str,
        org_data: dict[str, Any],
        completed_sites: set[str],
        map_lookup: dict[str, str],
        wlan_band_lookup: dict[str, list[str]],
    ) -> None:
        """Save progress to checkpoint file for rate-limit recovery."""
        checkpoint = {
            "org_id": org_id,
            "timestamp": datetime.now().isoformat(),
            "total_sites": len(completed_sites),
            "completed_sites": list(completed_sites),
            "org_data": org_data,
            "map_lookup": map_lookup,
            "wlan_band_lookup": wlan_band_lookup,
        }
        try:
            with open(
                E911BSSIDReportGenerator.CHECKPOINT_FILE,
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(checkpoint, handle)
            logging.info(
                "Checkpoint saved: %d sites completed",
                len(completed_sites),
            )
        except OSError as error:
            logging.warning("Failed to save checkpoint: %s", error)

    @staticmethod
    def _load_checkpoint(org_id: str) -> dict[str, Any] | None:
        """Load checkpoint if it exists and matches the current org."""
        path = E911BSSIDReportGenerator.CHECKPOINT_FILE
        if not os.path.exists(path):
            return None
        try:
            with open(path, encoding="utf-8") as handle:
                checkpoint: dict[str, Any] = json.load(handle)
            if checkpoint.get("org_id") != org_id:
                logging.info("Checkpoint org mismatch -- ignoring stale checkpoint")
                return None
            return checkpoint
        except (json.JSONDecodeError, OSError) as error:
            logging.warning("Failed to load checkpoint: %s", error)
            return None

    @staticmethod
    def _clear_checkpoint() -> None:
        """Remove checkpoint file after successful completion."""
        path = E911BSSIDReportGenerator.CHECKPOINT_FILE
        if os.path.exists(path):
            os.remove(path)
            logging.info("Checkpoint file removed")

    @staticmethod
    def _fetch_org_wlan_templates(
        apisession: Any,
        org_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch all org-level WLAN templates."""
        import mistapi  # noqa: E402  # lazy import

        response = mistapi.api.v1.orgs.templates.listOrgTemplates(apisession, org_id)
        if hasattr(response, "status_code") and response.status_code == 200:
            return response.data if isinstance(response.data, list) else []
        return []

    @staticmethod
    def _fetch_org_wlans(
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> list[dict[str, Any]]:
        """Fetch all org-level WLANs."""
        import mistapi  # noqa: E402  # lazy import

        response = mistapi.api.v1.orgs.wlans.listOrgWlans(apisession, org_id, limit=page_limit)
        return mistapi.get_all(response=response, mist_session=apisession)  # type: ignore[no-any-return]

    @staticmethod
    def _fetch_site_maps(
        apisession: Any,
        site_id: str,
        page_limit: int,
        map_lookup: dict[str, str],
    ) -> None:
        """Fetch floor plan maps for a site into map_lookup.

        Raises RuntimeError on HTTP 429 (rate limit).
        """
        import mistapi  # noqa: E402  # lazy import

        maps_response = mistapi.api.v1.sites.maps.listSiteMaps(apisession, site_id, limit=page_limit)
        if hasattr(maps_response, "status_code") and maps_response.status_code == 429:
            raise RuntimeError("E911_RATE_LIMIT")
        for site_map in mistapi.get_all(response=maps_response, mist_session=apisession):
            if site_map.get("id"):
                map_lookup[site_map["id"]] = site_map.get("name", "")

    @staticmethod
    def _resolve_site_ssids(
        apisession: Any,
        site_id: str,
        page_limit: int,
        site_info: dict[str, Any],
        wlan_context: dict[str, Any],
    ) -> None:
        """Resolve all SSIDs for a site from three sources.

        Sources: site-level WLANs, cached site template WLANs, and
        org WLANs via WLAN templates assigned to this site.
        Raises RuntimeError on HTTP 429 (rate limit).
        """
        import mistapi  # noqa: E402  # lazy import

        wlan_templates = wlan_context["wlan_templates"]
        org_wlans = wlan_context["org_wlans"]
        wlan_band_lookup = wlan_context["wlan_band_lookup"]
        site_template_cache = wlan_context["site_template_cache"]

        site_wlans_response = mistapi.api.v1.sites.wlans.listSiteWlans(apisession, site_id, limit=page_limit)
        if hasattr(site_wlans_response, "status_code") and site_wlans_response.status_code == 429:
            raise RuntimeError("E911_RATE_LIMIT")
        site_wlans = mistapi.get_all(response=site_wlans_response, mist_session=apisession)
        E911BSSIDReportGenerator._add_wlans_to_band_lookup(site_id, site_wlans, wlan_band_lookup)

        sitetemplate_id = site_info.get("sitetemplate_id")
        if sitetemplate_id and sitetemplate_id in site_template_cache:
            cached_wlans = site_template_cache[sitetemplate_id]
            E911BSSIDReportGenerator._add_wlans_to_band_lookup(site_id, cached_wlans, wlan_band_lookup)

        assigned_template_ids = E911BSSIDReportGenerator._get_assigned_template_ids(site_id, site_info, wlan_templates)
        if assigned_template_ids:
            template_wlans = [w for w in org_wlans if w.get("template_id") in assigned_template_ids]
            E911BSSIDReportGenerator._add_wlans_to_band_lookup(site_id, template_wlans, wlan_band_lookup)
            logging.debug(
                "Site %s: %d org WLANs via %d templates",
                site_id[:8],
                len(template_wlans),
                len(assigned_template_ids),
            )

    @staticmethod
    def _get_assigned_template_ids(
        site_id: str,
        site_info: dict[str, Any],
        wlan_templates: list[dict[str, Any]],
    ) -> set[str]:
        """Determine which WLAN templates are assigned to this site."""
        assigned: set[str] = set()
        site_groups = site_info.get("sitegroup_ids") or []
        for template in wlan_templates:
            applies = template.get("applies", {})
            if not isinstance(applies, dict):
                continue
            if applies.get("org_id"):
                assigned.add(template["id"])
            elif site_id in applies.get("site_ids", []):
                assigned.add(template["id"])
            elif any(sg in applies.get("sitegroup_ids", []) for sg in site_groups):
                assigned.add(template["id"])
        return assigned

    @staticmethod
    def _add_wlans_to_band_lookup(
        site_id: str,
        wlans: list[dict[str, Any]],
        wlan_band_lookup: dict[str, list[str]],
    ) -> None:
        """Add SSID names from a WLAN list into the band lookup dict."""
        band_map = E911BSSIDReportGenerator.BAND_MAP
        for wlan in wlans:
            if not wlan.get("enabled", False):
                continue
            ssid_name = wlan.get("ssid", "")
            if not ssid_name:
                continue
            wlan_band = wlan.get("band") or ""
            wlan_bands = E911BSSIDReportGenerator._resolve_wlan_bands(wlan_band, band_map)
            for band_key in wlan_bands:
                lookup_key = f"{site_id}::{band_key}"
                wlan_band_lookup.setdefault(lookup_key, [])
                if ssid_name not in wlan_band_lookup[lookup_key]:
                    wlan_band_lookup[lookup_key].append(ssid_name)

    @staticmethod
    def _resolve_wlan_bands(
        wlan_band: str,
        band_map: dict[str, str],
    ) -> list[str]:
        """Resolve a WLAN band string to a list of band keys."""
        if not wlan_band:
            return ["band_24", "band_5", "band_6"]
        if wlan_band == "both":
            return ["band_24", "band_5"]
        if wlan_band in band_map:
            return [band_map[wlan_band]]
        return [f"band_{b.strip()}" for b in wlan_band.split(",") if b.strip()]

    @staticmethod
    def _build_bssid_rows(
        radio_macs_data: list[dict[str, Any]],
        lookups: dict[str, Any],
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """Build sorted BSSID rows and compliance gaps from radio MAC data.

        Scanning/BLE radios (no band mapping) are excluded from output.
        """
        rows: list[dict[str, str]] = []
        compliance_gaps: list[dict[str, str]] = []

        for ap_entry in radio_macs_data:
            ap_mac = ap_entry.get("mac", "")
            ap_info = lookups["aps"].get(ap_mac, {})
            gap_reason = E911BSSIDReportGenerator._detect_gap(ap_info, lookups)
            if gap_reason:
                ap_name = ap_info.get("name") or "Unknown"
                compliance_gaps.append({"ap_name": ap_name, "ap_mac": ap_mac, "reason": gap_reason})
            E911BSSIDReportGenerator._append_ap_rows(ap_entry, ap_info, lookups, rows)

        rows.sort(
            key=lambda row: (
                row["Site Name"],
                row["Map Name"],
                row["AP Name"],
                row["Band"],
                row["BSSID"],
            )
        )
        return rows, compliance_gaps

    @staticmethod
    def _detect_gap(
        ap_info: dict[str, str],
        lookups: dict[str, Any],
    ) -> str:
        """Detect compliance gap reason for an AP."""
        if not ap_info:
            return "Not in device stats"
        site_id = ap_info.get("site_id") or ""
        if not site_id:
            return "No site assignment"
        map_id = ap_info.get("map_id") or ""
        if not map_id:
            return "No map assignment"
        if map_id not in lookups["maps"]:
            return "Map ID not found"
        return ""

    @staticmethod
    def _append_ap_rows(
        ap_entry: dict[str, Any],
        ap_info: dict[str, str],
        lookups: dict[str, Any],
        rows: list[dict[str, str]],
    ) -> None:
        """Append BSSID rows for one AP to the rows list."""
        ap_mac = ap_entry.get("mac", "")
        ap_name = ap_info.get("name") or "Unknown"
        site_id = ap_info.get("site_id") or ""
        map_id = ap_info.get("map_id") or ""

        site_name, site_address, map_name = E911BSSIDReportGenerator._resolve_location(site_id, map_id, lookups)

        for radio_mac in ap_entry.get("radio_mac", []):
            band_info = lookups["radio_bands"].get(radio_mac)
            if not band_info:
                continue
            band_label = band_info.get("band", "Unknown")
            band_key = band_info.get("band_key", "")
            ssid_key = f"{site_id}::{band_key}" if site_id and band_key else ""
            ssids = ", ".join(lookups["wlan_bands"].get(ssid_key, [])) or "N/A"
            for bssid in E911BSSIDReportGenerator._format_bssid(radio_mac):
                rows.append(
                    {
                        "Site Name": site_name,
                        "Site Address": site_address,
                        "Map Name": map_name,
                        "AP Name": ap_name,
                        "AP MAC": ap_mac,
                        "Band": band_label,
                        "Radio MAC": radio_mac,
                        "BSSID": bssid,
                        "SSIDs on Band": ssids,
                    }
                )

    @staticmethod
    def _resolve_location(
        site_id: str,
        map_id: str,
        lookups: dict[str, Any],
    ) -> tuple[str, str, str]:
        """Resolve site name, address, and map name from lookups."""
        if not site_id:
            return "Unassigned", "", "Unassigned"
        site_info = lookups["sites"].get(site_id, {})
        site_name = site_info.get("name") or "Unassigned"
        site_address = site_info.get("address", "")
        if not map_id:
            return site_name, site_address, "Unassigned"
        if map_id not in lookups["maps"]:
            return site_name, site_address, "Unknown Map"
        return site_name, site_address, lookups["maps"][map_id]

    @staticmethod
    def _display_summary(
        total_sites: int,
        total_aps: int,
        total_bssids: int,
        compliance_gaps: list[dict[str, str]],
    ) -> None:
        """Display E911 report summary with compliance gap detection."""
        print("\n--- E911 BSSID Report Summary ---")
        print(f"  Sites processed: {total_sites:,}")
        print(f"  APs processed: {total_aps:,}")
        print(f"  BSSIDs generated: {total_bssids:,}")

        if not compliance_gaps:
            print("\n  No compliance gaps detected" " -- all APs are assigned to floor plans.")
            return

        print(f"\n  Compliance Gaps: {len(compliance_gaps)} AP(s)" " require attention")
        for gap in compliance_gaps:
            print(f"    - {gap['ap_name']} ({gap['ap_mac']}): {gap['reason']}")

    @staticmethod
    def _process_sites(
        apisession: Any,
        org_id: str,
        page_limit: int,
        org_data: dict[str, Any],
        site_state: dict[str, Any],
    ) -> bool:
        """Process per-site enrichment (maps + WLANs) with checkpoint support.

        Returns True if all sites processed, False if rate-limited.
        """
        completed_sites = site_state["completed"]
        map_lookup = site_state["maps"]
        wlan_band_lookup = site_state["wlan_bands"]
        ap_lookup = org_data["aps"]
        unique_site_ids = sorted({info["site_id"] for info in ap_lookup.values() if info["site_id"]})
        remaining = [sid for sid in unique_site_ids if sid not in completed_sites]
        total_sites = len(unique_site_ids)

        if not remaining:
            print(f"  All {total_sites} sites already cached.")
            return True

        print(
            f"  Phase 2: Processing {len(remaining)} sites" f" ({len(completed_sites)} cached, {total_sites} total)..."
        )
        wlan_context = {
            "wlan_templates": org_data["wlan_templates"],
            "org_wlans": org_data["org_wlans"],
            "wlan_band_lookup": wlan_band_lookup,
            "site_template_cache": org_data["site_template_cache"],
        }
        return E911BSSIDReportGenerator._process_site_batch(
            apisession,
            org_id,
            page_limit,
            org_data,
            remaining,
            completed_sites,
            map_lookup,
            wlan_band_lookup,
            wlan_context,
            total_sites,
        )

    @staticmethod
    def _process_site_batch(
        apisession: Any,
        org_id: str,
        page_limit: int,
        org_data: dict[str, Any],
        remaining: list[str],
        completed_sites: set[str],
        map_lookup: dict[str, str],
        wlan_band_lookup: dict[str, list[str]],
        wlan_context: dict[str, Any],
        total_sites: int,
    ) -> bool:
        """Process remaining sites with checkpoint intervals.

        Returns True if all sites processed, False if rate-limited.
        """
        site_lookup = org_data["sites"]
        interval = E911BSSIDReportGenerator.CHECKPOINT_INTERVAL
        for index, site_id in enumerate(remaining, 1):
            site_info = site_lookup.get(site_id, {})
            try:
                E911BSSIDReportGenerator._fetch_site_maps(apisession, site_id, page_limit, map_lookup)
                E911BSSIDReportGenerator._resolve_site_ssids(
                    apisession,
                    site_id,
                    page_limit,
                    site_info,
                    wlan_context,
                )
                completed_sites.add(site_id)
            except RuntimeError as error:
                if "E911_RATE_LIMIT" in str(error):
                    return E911BSSIDReportGenerator._handle_rate_limit(
                        org_id,
                        org_data,
                        completed_sites,
                        map_lookup,
                        wlan_band_lookup,
                        total_sites,
                        index,
                    )
                raise
            except Exception as error:
                logging.warning("Error processing site %s: %s", site_id[:8], error)
                completed_sites.add(site_id)

            if index % interval == 0:
                E911BSSIDReportGenerator._save_checkpoint(
                    org_id,
                    org_data,
                    completed_sites,
                    map_lookup,
                    wlan_band_lookup,
                )
                print(f"    Progress: {len(completed_sites)}/{total_sites} sites")

        print(f"    Done: {len(completed_sites)}/{total_sites} sites enriched.")
        return True

    @staticmethod
    def _handle_rate_limit(
        org_id: str,
        org_data: dict[str, Any],
        completed_sites: set[str],
        map_lookup: dict[str, str],
        wlan_band_lookup: dict[str, list[str]],
        total_sites: int,
        index: int,
    ) -> bool:
        """Handle HTTP 429 rate limit by saving checkpoint."""
        print(f"\n  ! Rate limited (HTTP 429) after {index} sites this run.")
        E911BSSIDReportGenerator._save_checkpoint(
            org_id,
            org_data,
            completed_sites,
            map_lookup,
            wlan_band_lookup,
        )
        next_hour = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        print(f"    Checkpoint saved:" f" {len(completed_sites)}/{total_sites} sites.")
        print(f"    Run Menu 160 again after" f" {next_hour.strftime('%H:%M')} to resume.")
        return False

    @staticmethod
    def execute(
        apisession: Any,
        page_limit: int,
        org_id: str,
        safe_input_fn: Callable[..., str],
        write_data_fn: Callable[..., bool],  # DataExporter.write_with_format_selection returns a success bool
    ) -> None:
        """Generate E911 BSSID compliance report (Menu 160).

        Supports checkpoint/resume for large orgs that exceed the
        5000 API calls per clock-hour rate limit.
        """
        print("\n=== E911 BSSID Compliance Report ===")
        logging.info("Starting E911 BSSID compliance report generation...")
        start_time = time.time()

        site_state = E911BSSIDReportGenerator._restore_or_init(org_id, safe_input_fn)
        org_data = site_state.pop("org_data", None)

        if org_data is None:
            org_data = E911BSSIDReportGenerator._fetch_org_bulk_data(apisession, org_id, page_limit)

        radio_macs_data = org_data["radio_macs"]
        if not radio_macs_data:
            print("No APs found in this organization.")
            logging.info("No APs found - skipping E911 report generation")
            return

        all_done = E911BSSIDReportGenerator._process_sites(apisession, org_id, page_limit, org_data, site_state)
        if not all_done:
            return

        E911BSSIDReportGenerator._write_report(
            org_data,
            radio_macs_data,
            site_state,
            write_data_fn,
            start_time,
        )

    @staticmethod
    def _restore_or_init(
        org_id: str,
        safe_input_fn: Callable[..., str],
    ) -> dict[str, Any]:
        """Restore from checkpoint or initialize empty state."""
        checkpoint = E911BSSIDReportGenerator._load_checkpoint(org_id)
        if checkpoint:
            done = len(checkpoint.get("completed_sites", []))
            total = checkpoint.get("total_sites", "?")
            print(f"  Found checkpoint: {done}/{total} sites completed.")
            resume = safe_input_fn("  Resume from checkpoint? (y/n): ", context="e911_resume")
            if resume.lower() == "y":
                print("  Restored org data from checkpoint.")
                return {
                    "org_data": checkpoint["org_data"],
                    "maps": checkpoint.get("map_lookup", {}),
                    "wlan_bands": checkpoint.get("wlan_band_lookup", {}),
                    "completed": set(checkpoint.get("completed_sites", [])),
                }
            E911BSSIDReportGenerator._clear_checkpoint()

        return {
            "org_data": None,
            "maps": {},
            "wlan_bands": {},
            "completed": set(),
        }

    @staticmethod
    def _write_report(
        org_data: dict[str, Any],
        radio_macs_data: list[dict[str, Any]],
        site_state: dict[str, Any],
        write_data_fn: Callable[..., bool],  # Matches execute(): exporter returns a success bool
        start_time: float,
    ) -> None:
        """Build rows, write CSV, display summary, and clean up."""
        lookups = {
            "sites": org_data["sites"],
            "aps": org_data["aps"],
            "maps": site_state["maps"],
            "radio_macs": radio_macs_data,
            "radio_bands": org_data["radio_bands"],
            "wlan_bands": site_state["wlan_bands"],
        }
        rows, compliance_gaps = E911BSSIDReportGenerator._build_bssid_rows(radio_macs_data, lookups)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"E911_BSSID_Report_{timestamp_str}.csv"
        write_data_fn(
            data=rows,
            filename_or_table=filename,
            api_function_name="generateE911BSSIDReport",
        )
        logging.info("E911 report saved: data/%s (%d BSSIDs)", filename, len(rows))
        print(f"\nCSV saved: data/{filename} ({len(rows):,} BSSIDs)")

        unique_sites = {row["Site Name"] for row in rows} - {"Unassigned"}
        E911BSSIDReportGenerator._display_summary(
            len(unique_sites),
            len(radio_macs_data),
            len(rows),
            compliance_gaps,
        )

        E911BSSIDReportGenerator._clear_checkpoint()
        elapsed = time.time() - start_time
        logging.info("E911 BSSID report completed in %.1f seconds", elapsed)
        print(f"\nReport completed in {elapsed:.1f} seconds")
