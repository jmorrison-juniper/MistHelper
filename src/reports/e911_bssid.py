"""E911 BSSID compliance report generator.

Extracted from MistHelper.py per issue #219.
"""

import json  # WHY: persist checkpoint files across rate-limit resumes
import logging  # WHY: structured logs let ops trace long-running fetch pipelines
import os  # WHY: filesystem probes for checkpoint file lifecycle management
import time  # WHY: measure wall-clock elapsed for report telemetry
from collections.abc import Callable  # WHY: type-annotate injected input/write callbacks
from dataclasses import dataclass, field  # WHY: bundle 7+ related params into ≤5-param call signatures
from datetime import datetime, timedelta  # WHY: timestamp checkpoints and predict rate-limit reset window
from typing import Any, ClassVar  # WHY: mistapi returns untyped JSON dicts; ClassVar for typed static tables


@dataclass  # WHY: promote plain class into an auto-init dataclass
class SiteBatchContext:  # WHY: bundle per-batch state as a single object passed to helpers
    """Bundle per-batch state so helper signatures stay ≤5 params.

    WHY: `_process_site_batch` and `_handle_rate_limit` previously carried
    10 and 7 individual parameters. Grouping them keeps checkpoint state,
    org_data, and progress counters cohesive without changing behavior.
    """

    org_id: str  # WHY: identifies which org's checkpoint file to write
    org_data: dict[str, Any]  # WHY: shared bulk-fetched org data reused across sites
    total_sites: int  # WHY: denominator for progress display and telemetry
    completed_sites: set[str] = field(default_factory=set)  # WHY: skip-set on resume
    map_lookup: dict[str, str] = field(default_factory=dict)  # WHY: map-id -> friendly name
    wlan_band_lookup: dict[str, list[str]] = field(default_factory=dict)  # WHY: SSIDs per site+band
    wlan_context: dict[str, Any] = field(default_factory=dict)  # WHY: 4 wlan sources bundled together


class E911BSSIDReportGenerator:  # WHY: static-method namespace for the Menu 160 report pipeline
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

    BSSIDS_PER_RADIO = 16  # WHY: WiFi spec: each radio broadcasts up to 16 BSSIDs
    NIBBLE_MASK = 0xFFFFFFFFFFF0  # WHY: clear low nibble so we can OR in offsets 0..15
    BAND_MAP = {"24": "band_24", "5": "band_5", "6": "band_6"}  # WHY: numeric API values -> internal keys
    BAND_LABELS = [  # WHY: canonical display order for band summaries
        ("band_24", "2.4 GHz"),
        ("band_5", "5 GHz"),
        ("band_6", "6 GHz"),
    ]
    CHECKPOINT_FILE = os.path.join("data", "e911_checkpoint.json")  # WHY: portable path avoids Windows backslash issues
    CHECKPOINT_INTERVAL = 50  # WHY: balance disk I/O against work-loss on 429 interrupt
    RADIO_BANDS_BY_COUNT = {  # WHY: infer band from radio-array position (Juniper Mist convention)
        3: [
            ("band_6", "6 GHz"),
            ("band_5", "5 GHz"),
            ("band_24", "2.4 GHz"),
        ],
        2: [("band_5", "5 GHz"), ("band_24", "2.4 GHz")],
        1: [("band_24", "2.4 GHz")],
    }

    @staticmethod
    def _format_bssid(radio_base_mac: str) -> list[str]:  # WHY: derive 16 BSSIDs per radio MAC (WiFi spec)
        """Derive 16 colon-separated BSSIDs from a radio base MAC."""
        clean_mac = radio_base_mac.replace(":", "").replace("-", "")  # WHY: normalize to raw hex chars
        base_int = int(clean_mac, 16)  # WHY: enable bitwise math on the MAC value
        cleared_base = base_int & E911BSSIDReportGenerator.NIBBLE_MASK  # WHY: zero the low nibble for offsetting
        bssids: list[str] = []  # WHY: accumulate 16 formatted MAC strings
        for offset in range(E911BSSIDReportGenerator.BSSIDS_PER_RADIO):  # WHY: iterate 0..15 per WiFi spec
            bssid_hex = format(cleared_base | offset, "012x")  # WHY: OR offset then zero-pad to 12 hex chars
            bssids.append(":".join(bssid_hex[i : i + 2] for i in range(0, 12, 2)))  # WHY: reinsert colons
        return bssids  # WHY: caller receives ready-to-print MAC strings

    @staticmethod
    def _fetch_all_sites(  # WHY: paginate the org's site list via mistapi.get_all
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> list[dict[str, Any]]:
        """Fetch all sites with pagination."""
        import mistapi  # noqa: E402  # WHY: lazy import keeps CLI startup fast for non-report menus

        response = mistapi.api.v1.orgs.sites.listOrgSites(apisession, org_id, limit=page_limit)  # WHY: page-1 fetch
        return mistapi.get_all(response=response, mist_session=apisession)  # type: ignore[no-any-return]

    @staticmethod
    def _fetch_org_bulk_data(  # WHY: single entrypoint for expensive one-time org queries
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> dict[str, Any]:
        """Fetch all org-level data in bulk.

        These are the expensive bulk queries that only need to run once.
        Results are cached in the checkpoint file so they survive a 429.
        """
        logging.warning("  Phase 1: Fetching org-level bulk data...")  # Legacy console echo routed via logger.
        sites_data = E911BSSIDReportGenerator._fetch_site_and_ap_bulk(apisession, org_id, page_limit)  # WHY: sites+APs
        wlan_data = E911BSSIDReportGenerator._fetch_wlan_bulk(  # WHY: bulk WLAN + templates fetch
            apisession, org_id, page_limit, sites_data["sites"]
        )
        radio_data = E911BSSIDReportGenerator._fetch_radio_bulk(apisession, org_id, page_limit)  # WHY: radios+bands
        return {  # WHY: single dict passed downstream keeps interfaces small
            "sites": sites_data["sites"],
            "aps": sites_data["aps"],
            "wlan_templates": wlan_data["wlan_templates"],
            "org_wlans": wlan_data["org_wlans"],
            "site_template_cache": wlan_data["site_template_cache"],
            "radio_macs": radio_data["radio_macs"],
            "radio_bands": radio_data["radio_bands"],
        }

    @staticmethod
    def _fetch_site_and_ap_bulk(  # WHY: pair site inventory with AP stats in one grouped call
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> dict[str, Any]:
        """Fetch site inventory and AP stats in one grouped call.

        WHY: extracted from `_fetch_org_bulk_data` to keep parent ≤25 lines.
        """
        logging.warning("    Fetching site information...")  # Legacy console echo routed via logger.
        all_sites = E911BSSIDReportGenerator._fetch_all_sites(apisession, org_id, page_limit)  # WHY: paginated list
        site_lookup = E911BSSIDReportGenerator._build_site_lookup(all_sites)  # WHY: dict for O(1) lookup by id
        logging.info("Sites fetched: %d", len(site_lookup))  # WHY: telemetry for run-size auditing
        logging.warning("    Fetching AP inventory stats...")  # Legacy console echo routed via logger.
        ap_lookup = E911BSSIDReportGenerator._fetch_ap_stats(apisession, org_id, page_limit)  # WHY: MAC-indexed AP data
        logging.info("AP device stats fetched: %d", len(ap_lookup))  # WHY: audit AP inventory size
        return {"sites": site_lookup, "aps": ap_lookup}  # WHY: bundled return keeps caller signature small

    @staticmethod
    def _fetch_wlan_bulk(  # WHY: gather every WLAN source (templates + org + site templates)
        apisession: Any,
        org_id: str,
        page_limit: int,
        site_lookup: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Fetch WLAN templates, org WLANs, and per-template WLAN cache.

        WHY: extracted so `_fetch_org_bulk_data` stays under the 25-line ceiling.
        """
        logging.warning("    Fetching org WLAN templates and org WLANs...")  # Legacy console echo routed via logger.
        wlan_templates, org_wlans = E911BSSIDReportGenerator._fetch_wlan_sources(  # WHY: pair template+wlan fetch
            apisession, org_id, page_limit
        )
        logging.warning("    Pre-fetching unique site template WLANs...")  # Legacy console echo routed via logger.
        cache = E911BSSIDReportGenerator._prefetch_site_templates(  # WHY: cache SSIDs per template
            apisession, org_id, site_lookup
        )
        logging.info("Cached %d unique site templates", len(cache))  # WHY: audit prefetch efficiency
        return {  # WHY: bundle wlan sources for the parent aggregator
            "wlan_templates": wlan_templates,
            "org_wlans": org_wlans,
            "site_template_cache": cache,
        }

    @staticmethod
    def _fetch_wlan_sources(  # WHY: pull templates + org-scope WLANs together to keep parent short
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Fetch WLAN template metadata and org-scope WLAN records as a pair."""
        wlan_templates = E911BSSIDReportGenerator._fetch_org_wlan_templates(  # WHY: template metadata
            apisession, org_id
        )
        org_wlans = E911BSSIDReportGenerator._fetch_org_wlans(apisession, org_id, page_limit)  # WHY: org-scope SSIDs
        logging.info("Org templates: %d, org WLANs: %d", len(wlan_templates), len(org_wlans))  # WHY: audit sizes
        return wlan_templates, org_wlans  # WHY: caller assembles into the bulk WLAN bundle

    @staticmethod
    def _fetch_radio_bulk(  # WHY: fetch radio MACs then infer band from array position
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> dict[str, Any]:
        """Fetch radio MACs and infer band assignments.

        WHY: keeps `_fetch_org_bulk_data` skinny while isolating band inference.
        """
        import mistapi  # noqa: E402  # WHY: lazy import so non-report menus start fast

        logging.warning("    Fetching AP radio MACs...")  # Legacy console echo routed via logger.
        radio_response = mistapi.api.v1.orgs.devices.listOrgApsMacs(apisession, org_id, limit=page_limit)  # WHY: page 1
        radio_macs_data: list[dict[str, Any]] = mistapi.get_all(  # WHY: fetch all remaining pages
            response=radio_response, mist_session=apisession
        )
        logging.info("Radio MAC records fetched: %d", len(radio_macs_data))  # WHY: audit radio-record count
        logging.warning("    Inferring radio bands from MAC positions...")  # Legacy console echo routed via logger.
        radio_band_lookup = E911BSSIDReportGenerator._infer_radio_bands(radio_macs_data)  # WHY: position -> band
        logging.info("Radio bands inferred: %d broadcast radios", len(radio_band_lookup))  # WHY: audit inference
        return {"radio_macs": radio_macs_data, "radio_bands": radio_band_lookup}  # WHY: bundle for parent

    @staticmethod
    def _build_site_lookup(
        all_sites: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Build site lookup dict from raw site list."""
        site_lookup: dict[str, dict[str, Any]] = {}  # WHY: accumulate keyed-by-id output
        for site in all_sites:  # WHY: iterate every paginated site record
            site_id = site.get("id")  # WHY: id may be absent in malformed API responses
            if site_id:  # WHY: guard against missing key before use
                site_lookup[site_id] = {  # WHY: normalize to trimmed subset used downstream
                    "name": site.get("name", ""),
                    "address": site.get("address", ""),
                    "sitegroup_ids": site.get("sitegroup_ids") or [],
                    "sitetemplate_id": site.get("sitetemplate_id") or "",
                }
        return site_lookup  # WHY: caller uses this for name/address resolution

    @staticmethod
    def _fetch_ap_stats(
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> dict[str, dict[str, str]]:
        """Fetch AP inventory stats and build lookup dict."""
        import mistapi  # noqa: E402  # WHY: lazy import for CLI startup performance

        stats_response = mistapi.api.v1.orgs.stats.listOrgDevicesStats(apisession, org_id, type="ap", limit=page_limit)
        all_ap_stats: list[dict[str, Any]] = mistapi.get_all(response=stats_response, mist_session=apisession)
        ap_lookup: dict[str, dict[str, str]] = {}  # WHY: MAC-indexed lookup accelerates row build
        for device in all_ap_stats:  # WHY: each device entry has one AP MAC
            device_mac = device.get("mac")  # WHY: skip records without a MAC field
            if device_mac:  # WHY: only meaningful for BSSID derivation
                ap_lookup[device_mac] = {  # WHY: trimmed dict of only fields we use downstream
                    "name": device.get("name", ""),
                    "site_id": device.get("site_id") or "",
                    "map_id": device.get("map_id") or "",
                }
        return ap_lookup  # WHY: consumer needs O(1) lookup by AP MAC

    @staticmethod
    def _prefetch_site_templates(
        apisession: Any,
        org_id: str,
        site_lookup: dict[str, dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Pre-fetch WLANs for each unique site template."""
        unique_ids = {info["sitetemplate_id"] for info in site_lookup.values() if info.get("sitetemplate_id")}
        cache: dict[str, list[dict[str, Any]]] = {}  # WHY: one entry per template id
        for sitetemplate_id in unique_ids:  # WHY: fetch each template exactly once
            cache[sitetemplate_id] = E911BSSIDReportGenerator._load_template_wlans(apisession, org_id, sitetemplate_id)
        return cache  # WHY: reused for every site that shares this template

    @staticmethod
    def _load_template_wlans(
        apisession: Any,
        org_id: str,
        sitetemplate_id: str,
    ) -> list[dict[str, Any]]:
        """Load WLANs for a single site template with error handling.

        WHY: extracted to shrink `_prefetch_site_templates` complexity below 5.
        """
        import mistapi  # noqa: E402  # WHY: lazy import keeps startup light

        try:  # WHY: any single template can fail without aborting the report
            response = mistapi.api.v1.orgs.sitetemplates.getOrgSiteTemplate(apisession, org_id, sitetemplate_id)
        except Exception as error:  # WHY: log and treat as empty rather than propagate
            logging.debug("Failed to fetch site template %s: %s", sitetemplate_id[:8], error)
            return []  # WHY: caller expects a list even on failure
        if not (hasattr(response, "status_code") and response.status_code == 200):  # WHY: only trust 200 responses
            return []  # WHY: non-200 -> treat template as empty
        template_wlans = response.data.get("wlans", {})  # WHY: nested dict of WLAN records
        if not isinstance(template_wlans, dict):  # WHY: some responses return lists instead of dicts
            return []  # WHY: skip unexpected shape rather than crash
        return list(template_wlans.values())  # WHY: caller only needs the WLAN records, not IDs

    @staticmethod
    def _infer_radio_bands(
        radio_macs_data: list[dict[str, Any]],
    ) -> dict[str, dict[str, str]]:
        """Infer radio band from MAC array position (last radio is always scanning)."""
        band_orders = E911BSSIDReportGenerator.RADIO_BANDS_BY_COUNT  # WHY: alias for readability
        radio_band_lookup: dict[str, dict[str, str]] = {}  # WHY: MAC -> band info result
        for ap_entry in radio_macs_data:  # WHY: each entry is one AP with its radio MACs
            all_radios = ap_entry.get("radio_mac", [])  # WHY: default empty list guards missing key
            if len(all_radios) < 2:  # WHY: 1-radio APs (BLE-only?) have no broadcast radios to map
                continue  # WHY: skip; no bands to infer
            broadcast_radios = all_radios[:-1]  # WHY: last MAC is always the scanning radio (Mist convention)
            bands = band_orders.get(len(broadcast_radios), [])  # WHY: pick canonical order for this count
            for index, radio_mac in enumerate(broadcast_radios):  # WHY: pair each broadcast MAC to a band
                if index < len(bands):  # WHY: guard uneven counts (defensive)
                    band_key, band_label = bands[index]  # WHY: unpack (internal-key, display-label)
                    radio_band_lookup[radio_mac] = {"band": band_label, "band_key": band_key}
        return radio_band_lookup  # WHY: consumer uses this to skip scanning radios in output

    @staticmethod
    def _save_checkpoint(
        org_id: str,
        org_data: dict[str, Any],
        completed_sites: set[str],
        map_lookup: dict[str, str],
        wlan_band_lookup: dict[str, list[str]],
    ) -> None:
        """Save progress to checkpoint file for rate-limit recovery."""
        checkpoint = {  # WHY: single json-serializable dict written to disk
            "org_id": org_id,
            "timestamp": datetime.now().isoformat(),
            "total_sites": len(completed_sites),
            "completed_sites": list(completed_sites),  # WHY: set is not JSON-serializable
            "org_data": org_data,
            "map_lookup": map_lookup,
            "wlan_band_lookup": wlan_band_lookup,
        }
        E911BSSIDReportGenerator._write_checkpoint_file(checkpoint, len(completed_sites))

    @staticmethod
    def _write_checkpoint_file(checkpoint: dict[str, Any], completed_count: int) -> None:
        """Write checkpoint JSON to disk; log OS errors without raising.

        WHY: extracted so `_save_checkpoint` stays under the 25-line ceiling
        and error-handling is isolated from checkpoint-shape construction.
        """
        try:  # WHY: filesystem errors during rate-limit recovery should not crash the report
            with open(E911BSSIDReportGenerator.CHECKPOINT_FILE, "w", encoding="utf-8") as handle:
                json.dump(checkpoint, handle)  # WHY: default separators keep file compact enough
            logging.info("Checkpoint saved: %d sites completed", completed_count)  # WHY: audit progress
        except OSError as error:  # WHY: only OS-level errors (disk full, perms) suppress-and-log
            logging.warning("Failed to save checkpoint: %s", error)  # WHY: user still sees the print output

    @staticmethod
    def _load_checkpoint(org_id: str) -> dict[str, Any] | None:
        """Load checkpoint if it exists and matches the current org."""
        path = E911BSSIDReportGenerator.CHECKPOINT_FILE  # WHY: alias for readability
        if not os.path.exists(path):  # WHY: no checkpoint means fresh run
            return None  # WHY: caller treats None as "start over"
        try:  # WHY: corrupt files should not crash startup
            with open(path, encoding="utf-8") as handle:  # WHY: utf-8 matches write encoding
                checkpoint: dict[str, Any] = json.load(handle)  # WHY: JSON round-trip preserves structure
            if checkpoint.get("org_id") != org_id:  # WHY: stale checkpoint from a different org is unusable
                logging.info("Checkpoint org mismatch -- ignoring stale checkpoint")
                return None  # WHY: force fresh run against current org
            return checkpoint  # WHY: caller extracts state fields
        except (json.JSONDecodeError, OSError) as error:  # WHY: both corrupt-JSON and read-error paths land here
            logging.warning("Failed to load checkpoint: %s", error)  # WHY: user notified via log
            return None  # WHY: fall back to fresh run

    @staticmethod
    def _clear_checkpoint() -> None:
        """Remove checkpoint file after successful completion."""
        path = E911BSSIDReportGenerator.CHECKPOINT_FILE  # WHY: alias for readability
        if os.path.exists(path):  # WHY: cheap check avoids OSError on missing file
            os.remove(path)  # WHY: clean slate for next report run
            logging.info("Checkpoint file removed")  # WHY: audit trail of successful completion

    @staticmethod
    def _fetch_org_wlan_templates(
        apisession: Any,
        org_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch all org-level WLAN templates."""
        import mistapi  # noqa: E402  # WHY: lazy import keeps CLI startup fast

        response = mistapi.api.v1.orgs.templates.listOrgTemplates(apisession, org_id)  # WHY: single-page endpoint
        if hasattr(response, "status_code") and response.status_code == 200:  # WHY: trust only 200 responses
            return response.data if isinstance(response.data, list) else []  # WHY: guard shape
        return []  # WHY: non-200 returns an empty template set

    @staticmethod
    def _fetch_org_wlans(
        apisession: Any,
        org_id: str,
        page_limit: int,
    ) -> list[dict[str, Any]]:
        """Fetch all org-level WLANs."""
        import mistapi  # noqa: E402  # WHY: lazy import keeps startup light

        response = mistapi.api.v1.orgs.wlans.listOrgWlans(apisession, org_id, limit=page_limit)  # WHY: paginated call
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
        import mistapi  # noqa: E402  # WHY: lazy import keeps CLI startup fast

        maps_response = mistapi.api.v1.sites.maps.listSiteMaps(apisession, site_id, limit=page_limit)
        if hasattr(maps_response, "status_code") and maps_response.status_code == 429:  # WHY: 429 == rate-limited
            raise RuntimeError("E911_RATE_LIMIT")  # WHY: sentinel string caught by batch loop
        for site_map in mistapi.get_all(response=maps_response, mist_session=apisession):  # WHY: iterate all pages
            if site_map.get("id"):  # WHY: skip records without map id
                map_lookup[site_map["id"]] = site_map.get("name", "")  # WHY: id -> friendly name

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
        wlan_band_lookup = wlan_context["wlan_band_lookup"]  # WHY: shared mutable target for all three sources
        E911BSSIDReportGenerator._merge_site_wlans(apisession, site_id, page_limit, wlan_band_lookup)
        E911BSSIDReportGenerator._merge_template_wlans(site_id, site_info, wlan_context, wlan_band_lookup)
        E911BSSIDReportGenerator._merge_org_wlans(site_id, site_info, wlan_context, wlan_band_lookup)

    @staticmethod
    def _merge_site_wlans(
        apisession: Any,
        site_id: str,
        page_limit: int,
        wlan_band_lookup: dict[str, list[str]],
    ) -> None:
        """Fetch site-level WLANs and add them to the band lookup.

        WHY: extracted from `_resolve_site_ssids` to shrink parent below 25 lines.
        """
        import mistapi  # noqa: E402  # WHY: lazy import keeps CLI startup fast

        site_wlans_response = mistapi.api.v1.sites.wlans.listSiteWlans(apisession, site_id, limit=page_limit)
        if hasattr(site_wlans_response, "status_code") and site_wlans_response.status_code == 429:
            raise RuntimeError("E911_RATE_LIMIT")  # WHY: sentinel bubbles up to batch loop
        site_wlans = mistapi.get_all(response=site_wlans_response, mist_session=apisession)  # WHY: paginated fetch
        E911BSSIDReportGenerator._add_wlans_to_band_lookup(site_id, site_wlans, wlan_band_lookup)

    @staticmethod
    def _merge_template_wlans(
        site_id: str,
        site_info: dict[str, Any],
        wlan_context: dict[str, Any],
        wlan_band_lookup: dict[str, list[str]],
    ) -> None:
        """Add cached site-template WLANs for this site to the band lookup.

        WHY: extracted so parent stays ≤25 lines and complexity ≤5.
        """
        sitetemplate_id = site_info.get("sitetemplate_id")  # WHY: link to prefetched cache entry
        site_template_cache = wlan_context["site_template_cache"]  # WHY: pre-fetched template WLANs
        if sitetemplate_id and sitetemplate_id in site_template_cache:  # WHY: only if this site has a template
            cached_wlans = site_template_cache[sitetemplate_id]  # WHY: reuse cached WLAN list
            E911BSSIDReportGenerator._add_wlans_to_band_lookup(site_id, cached_wlans, wlan_band_lookup)

    @staticmethod
    def _merge_org_wlans(
        site_id: str,
        site_info: dict[str, Any],
        wlan_context: dict[str, Any],
        wlan_band_lookup: dict[str, list[str]],
    ) -> None:
        """Add org WLANs (via WLAN templates assigned to this site) to the band lookup.

        WHY: extracted so parent stays ≤25 lines and complexity ≤5.
        """
        wlan_templates = wlan_context["wlan_templates"]  # WHY: org-scope templates that may target this site
        org_wlans = wlan_context["org_wlans"]  # WHY: candidate WLANs to filter by template membership
        assigned_template_ids = E911BSSIDReportGenerator._get_assigned_template_ids(site_id, site_info, wlan_templates)
        if not assigned_template_ids:  # WHY: guard clause avoids empty-list filter work
            return  # WHY: nothing to add when no templates apply here
        template_wlans = [w for w in org_wlans if w.get("template_id") in assigned_template_ids]  # WHY: filter
        E911BSSIDReportGenerator._add_wlans_to_band_lookup(site_id, template_wlans, wlan_band_lookup)
        logging.debug(  # WHY: audit which templates contributed which WLANs
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
        assigned: set[str] = set()  # WHY: accumulator of matching template ids
        site_groups = site_info.get("sitegroup_ids") or []  # WHY: normalize None -> [] for `in` checks
        for template in wlan_templates:  # WHY: evaluate each candidate template
            if E911BSSIDReportGenerator._template_applies_to_site(template, site_id, site_groups):  # WHY: match helper
                assigned.add(template["id"])  # WHY: record match by id
        return assigned  # WHY: caller filters org WLANs by these ids

    @staticmethod
    def _template_applies_to_site(
        template: dict[str, Any],
        site_id: str,
        site_groups: list[str],
    ) -> bool:
        """Return True if a template's `applies` clause covers this site.

        WHY: extracted from `_get_assigned_template_ids` to lower complexity below 5.
        """
        applies = template.get("applies", {})  # WHY: default {} keeps `.get` calls safe below
        if not isinstance(applies, dict):  # WHY: some rows have malformed `applies`
            return False  # WHY: treat as non-matching rather than crash
        if applies.get("org_id"):  # WHY: org-wide templates match all sites in the org
            return True  # WHY: shortest-circuit path
        if site_id in applies.get("site_ids", []):  # WHY: explicit site membership check
            return True  # WHY: direct match
        return any(sg in applies.get("sitegroup_ids", []) for sg in site_groups)  # WHY: sitegroup indirect match

    @staticmethod
    def _add_wlans_to_band_lookup(
        site_id: str,
        wlans: list[dict[str, Any]],
        wlan_band_lookup: dict[str, list[str]],
    ) -> None:
        """Add SSID names from a WLAN list into the band lookup dict."""
        band_map = E911BSSIDReportGenerator.BAND_MAP  # WHY: alias for readability in loop
        for wlan in wlans:  # WHY: each WLAN can contribute one SSID name to multiple bands
            E911BSSIDReportGenerator._add_single_wlan(site_id, wlan, band_map, wlan_band_lookup)

    @staticmethod
    def _add_single_wlan(
        site_id: str,
        wlan: dict[str, Any],
        band_map: dict[str, str],
        wlan_band_lookup: dict[str, list[str]],
    ) -> None:
        """Add one WLAN's SSID to every band it belongs to.

        WHY: extracted from `_add_wlans_to_band_lookup` to keep complexity ≤5.
        """
        if not wlan.get("enabled", False):  # WHY: disabled WLANs never broadcast
            return  # WHY: skip disabled record
        ssid_name = wlan.get("ssid", "")  # WHY: required field; skip if missing
        if not ssid_name:  # WHY: empty SSID cannot appear on air
            return  # WHY: skip malformed record
        band_field = wlan.get("band") or ""  # WHY: normalise None to empty string for resolver
        wlan_bands = E911BSSIDReportGenerator._resolve_wlan_bands(band_field, band_map)  # WHY: map to keys
        E911BSSIDReportGenerator._apply_ssid_to_bands(site_id, ssid_name, wlan_bands, wlan_band_lookup)  # WHY: fan-out

    @staticmethod
    def _apply_ssid_to_bands(
        site_id: str,
        ssid_name: str,
        wlan_bands: list[str],
        wlan_band_lookup: dict[str, list[str]],
    ) -> None:
        """Append the SSID name to every ``site::band`` bucket it belongs to.

        WHY: extracted from `_add_single_wlan` to keep complexity ≤5.
        """
        for band_key in wlan_bands:  # WHY: one WLAN can span multiple bands (for example dual-band)
            lookup_key = f"{site_id}::{band_key}"  # WHY: composite key groups SSIDs per site+band
            bucket = wlan_band_lookup.setdefault(lookup_key, [])  # WHY: create then reuse bucket
            if ssid_name not in bucket:  # WHY: prevent duplicate SSID names
                bucket.append(ssid_name)  # WHY: preserve insertion order

    @staticmethod
    def _resolve_wlan_bands(
        wlan_band: str,
        band_map: dict[str, str],
    ) -> list[str]:
        """Resolve a WLAN band string to a list of band keys."""
        if not wlan_band:  # WHY: empty means "all bands" per Mist convention
            return ["band_24", "band_5", "band_6"]  # WHY: all three canonical bands
        if wlan_band == "both":  # WHY: legacy Mist "both" means 2.4 + 5 only
            return ["band_24", "band_5"]  # WHY: excludes 6 GHz by design
        mapped = band_map.get(wlan_band)  # WHY: single-band shortcut ("24", "5", "6") -> None if miss
        if mapped is not None:  # WHY: happy-path single mapping avoids the CSV parse
            return [mapped]  # WHY: single-item list keeps caller loop uniform
        return E911BSSIDReportGenerator._parse_band_csv(wlan_band)  # WHY: comma-separated fallback

    @staticmethod
    def _parse_band_csv(wlan_band: str) -> list[str]:
        """Return band keys parsed from a comma-separated ``wlan_band`` value.

        WHY: extracted so `_resolve_wlan_bands` stays complexity ≤5.
        """
        return [f"band_{token}" for token in (part.strip() for part in wlan_band.split(",")) if token]

    @staticmethod
    def _build_bssid_rows(
        radio_macs_data: list[dict[str, Any]],
        lookups: dict[str, Any],
    ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
        """Build sorted BSSID rows and compliance gaps from radio MAC data.

        Scanning/BLE radios (no band mapping) are excluded from output.
        """
        rows: list[dict[str, str]] = []  # WHY: flat list of BSSID rows for CSV export
        compliance_gaps: list[dict[str, str]] = []  # WHY: separate list highlighting missing assignments
        for ap_entry in radio_macs_data:  # WHY: iterate every AP with radio MAC data
            ap_mac = ap_entry.get("mac", "")  # WHY: primary key into ap_lookup
            ap_info = lookups["aps"].get(ap_mac, {})  # WHY: empty dict when no matching stats record
            gap_reason = E911BSSIDReportGenerator._detect_gap(ap_info, lookups)  # WHY: emit compliance gap once per AP
            if gap_reason:  # WHY: only build gap row when a reason exists
                ap_name = ap_info.get("name") or "Unknown"  # WHY: default label for missing name
                compliance_gaps.append({"ap_name": ap_name, "ap_mac": ap_mac, "reason": gap_reason})
            E911BSSIDReportGenerator._append_ap_rows(ap_entry, ap_info, lookups, rows)  # WHY: expand each AP
        E911BSSIDReportGenerator._sort_rows_inplace(rows)  # WHY: stable order for CSV output
        return rows, compliance_gaps  # WHY: caller writes both to disk/summary

    @staticmethod
    def _sort_rows_inplace(rows: list[dict[str, str]]) -> None:
        """Sort rows by Site, Map, AP, Band, BSSID for consistent CSV output.

        WHY: extracted so `_build_bssid_rows` stays ≤25 lines.
        """
        rows.sort(  # WHY: in-place sort matches the mutable-list pattern used elsewhere
            key=lambda row: (
                row["Site Name"],
                row["Map Name"],
                row["AP Name"],
                row["Band"],
                row["BSSID"],
            )
        )

    _GAP_CHECKS: ClassVar[tuple[tuple[str, str], ...]] = (  # WHY: table-driven so _detect_gap stays ≤5 CC
        ("site_id", "No site assignment"),
        ("map_id", "No map assignment"),
    )

    @staticmethod
    def _detect_gap(
        ap_info: dict[str, str],
        lookups: dict[str, Any],
    ) -> str:
        """Detect compliance gap reason for an AP."""
        if not ap_info:  # WHY: no AP stats -> cannot verify compliance
            return "Not in device stats"  # WHY: matches summary wording
        missing = E911BSSIDReportGenerator._first_missing_field(ap_info)  # WHY: table lookup replaces if-chain
        if missing:  # WHY: first missing field wins
            return missing  # WHY: propagate to caller
        map_id = ap_info.get("map_id") or ""  # WHY: already known present; re-fetch for lookup check
        if map_id not in lookups["maps"]:  # WHY: map id present but stale/deleted
            return "Map ID not found"  # WHY: distinct label for operator triage
        return ""  # WHY: empty string means "no gap"

    @staticmethod
    def _first_missing_field(ap_info: dict[str, str]) -> str:
        """Return the first gap label for a missing AP field, or empty string.

        WHY: extracted so `_detect_gap` stays complexity ≤5.
        """
        for field_name, label in E911BSSIDReportGenerator._GAP_CHECKS:  # WHY: iterate table in priority order
            if not (ap_info.get(field_name) or ""):  # WHY: treat missing/empty as gap
                return label  # WHY: first miss wins
        return ""  # WHY: caller distinguishes empty from real gap

    @staticmethod
    def _append_ap_rows(
        ap_entry: dict[str, Any],
        ap_info: dict[str, str],
        lookups: dict[str, Any],
        rows: list[dict[str, str]],
    ) -> None:
        """Append BSSID rows for one AP to the rows list."""
        ap_mac = ap_entry.get("mac", "")  # WHY: MAC field is the AP identity
        ap_name = ap_info.get("name") or "Unknown"  # WHY: default label for missing name
        site_id = ap_info.get("site_id") or ""  # WHY: normalized for lookup keys
        map_id = ap_info.get("map_id") or ""  # WHY: normalized for lookup keys
        site_name, site_address, map_name = E911BSSIDReportGenerator._resolve_location(site_id, map_id, lookups)
        ap_ctx = {  # WHY: bundle AP-scoped values so radio-row helper stays under 5 params
            "ap_mac": ap_mac,
            "ap_name": ap_name,
            "site_id": site_id,
            "site_name": site_name,
            "site_address": site_address,
            "map_name": map_name,
        }
        for radio_mac in ap_entry.get("radio_mac", []):  # WHY: expand each radio into BSSID rows
            E911BSSIDReportGenerator._append_radio_rows(radio_mac, ap_ctx, lookups, rows)  # WHY: helper per radio

    @staticmethod
    def _append_radio_rows(
        radio_mac: str,
        ap_ctx: dict[str, str],
        lookups: dict[str, Any],
        rows: list[dict[str, str]],
    ) -> None:
        """Append 16 BSSID rows for one radio (skips scanning radios).

        WHY: extracted from `_append_ap_rows` to keep complexity ≤5 and length ≤25.
        """
        band_info = lookups["radio_bands"].get(radio_mac)  # WHY: skip scanning/BLE radios (no band info)
        if not band_info:  # WHY: no band -> not a broadcast radio -> no rows
            return  # WHY: silently skip; noise is handled at build-lookup time
        ssids = E911BSSIDReportGenerator._resolve_ssid_label(ap_ctx["site_id"], band_info, lookups)  # WHY: cell text
        band_label = band_info.get("band", "Unknown")  # WHY: default label preserves row shape
        E911BSSIDReportGenerator._emit_bssid_rows(radio_mac, band_label, ssids, ap_ctx, rows)  # WHY: fan-out 16 rows

    @staticmethod
    def _resolve_ssid_label(
        site_id: str,
        band_info: dict[str, str],
        lookups: dict[str, Any],
    ) -> str:
        """Return the comma-joined SSID label for a radio, or ``N/A`` when unknown.

        WHY: extracted so `_append_radio_rows` stays complexity ≤5.
        """
        band_key = band_info.get("band_key", "")  # WHY: needed to compute SSID lookup key
        if not (site_id and band_key):  # WHY: any missing part -> empty ssid list
            return "N/A"  # WHY: default placeholder for CSV cell
        ssid_key = f"{site_id}::{band_key}"  # WHY: composite key matches build-lookup shape
        return ", ".join(lookups["wlan_bands"].get(ssid_key, [])) or "N/A"  # WHY: preserve N/A on empty list

    @staticmethod
    def _emit_bssid_rows(
        radio_mac: str,
        band_label: str,
        ssids: str,
        ap_ctx: dict[str, str],
        rows: list[dict[str, str]],
    ) -> None:
        """Append the 16 derived BSSID rows for one radio to ``rows``.

        WHY: extracted so `_append_radio_rows` stays ≤25 lines.
        """
        for bssid in E911BSSIDReportGenerator._format_bssid(radio_mac):  # WHY: 16 BSSIDs per radio
            rows.append(  # WHY: append to shared mutable list; single flat row schema
                {
                    "Site Name": ap_ctx["site_name"],
                    "Site Address": ap_ctx["site_address"],
                    "Map Name": ap_ctx["map_name"],
                    "AP Name": ap_ctx["ap_name"],
                    "AP MAC": ap_ctx["ap_mac"],
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
        if not site_id:  # WHY: no site -> unassigned everything
            return "Unassigned", "", "Unassigned"  # WHY: consistent labels for compliance report
        site_info = lookups["sites"].get(site_id, {})  # WHY: empty dict when site_id is stale
        site_name = site_info.get("name") or "Unassigned"  # WHY: default label when name is blank
        site_address = site_info.get("address", "")  # WHY: address optional; empty allowed
        if not map_id:  # WHY: valid site but no floor plan
            return site_name, site_address, "Unassigned"  # WHY: separate map-level label
        if map_id not in lookups["maps"]:  # WHY: map id stale/deleted
            return site_name, site_address, "Unknown Map"  # WHY: distinct label from "Unassigned"
        return site_name, site_address, lookups["maps"][map_id]  # WHY: fully resolved location

    @staticmethod
    def _display_summary(
        total_sites: int,
        total_aps: int,
        total_bssids: int,
        compliance_gaps: list[dict[str, str]],
    ) -> None:
        """Display E911 report summary with compliance gap detection."""
        logging.warning("\n--- E911 BSSID Report Summary ---")  # Legacy console echo routed via logger.
        logging.warning("  Sites processed: %s", f"{total_sites:,}")  # Legacy console echo routed via logger.
        logging.warning("  APs processed: %s", f"{total_aps:,}")  # Legacy console echo routed via logger.
        logging.warning("  BSSIDs generated: %s", f"{total_bssids:,}")  # Legacy console echo routed via logger.
        if not compliance_gaps:  # WHY: happy-path exits with a positive message
            logging.warning(
                "\n  No compliance gaps detected -- all APs are assigned to floor plans."
            )  # Legacy console echo routed via logger.
            return  # WHY: nothing more to print
        logging.warning(
            "\n  Compliance Gaps: %s AP(s) require attention", len(compliance_gaps)
        )  # Legacy console echo routed via logger.
        for gap in compliance_gaps:  # WHY: enumerate each gap with reason
            logging.warning(
                "    - %s (%s): %s", gap["ap_name"], gap["ap_mac"], gap["reason"]
            )  # Legacy console echo routed via logger.

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
        completed_sites = site_state["completed"]  # WHY: mutable set updated as sites finish
        remaining, total_sites = E911BSSIDReportGenerator._compute_remaining_sites(  # WHY: pending vs done
            org_data, completed_sites
        )
        if not remaining:  # WHY: everything cached from a prior run
            logging.warning("  All %s sites already cached.", total_sites)  # Legacy console echo routed via logger.
            return True  # WHY: nothing to do
        logging.warning(
            "  Phase 2: Processing %s sites (%s cached, %s total)...",
            len(remaining),
            len(completed_sites),
            total_sites,
        )  # Legacy console echo routed via logger.
        batch = E911BSSIDReportGenerator._build_batch_context(org_id, org_data, site_state, total_sites)  # WHY: bundle
        return E911BSSIDReportGenerator._process_site_batch(apisession, page_limit, remaining, batch)

    @staticmethod
    def _build_batch_context(
        org_id: str,
        org_data: dict[str, Any],
        site_state: dict[str, Any],
        total_sites: int,
    ) -> "SiteBatchContext":
        """Construct the ``SiteBatchContext`` handed to per-site helpers.

        WHY: extracted so `_process_sites` stays ≤25 lines.
        """
        return SiteBatchContext(  # WHY: 7-field bundle keeps downstream helpers ≤5 params
            org_id=org_id,
            org_data=org_data,
            total_sites=total_sites,
            completed_sites=site_state["completed"],
            map_lookup=site_state["maps"],
            wlan_band_lookup=site_state["wlan_bands"],
            wlan_context=E911BSSIDReportGenerator._build_wlan_context(org_data, site_state),
        )

    @staticmethod
    def _compute_remaining_sites(
        org_data: dict[str, Any],
        completed_sites: set[str],
    ) -> tuple[list[str], int]:
        """Return ``(remaining_site_ids, total_unique_sites)`` for the batch loop.

        WHY: extracted so `_process_sites` stays complexity ≤5 and length ≤25.
        """
        ap_lookup = org_data["aps"]  # WHY: derive unique site ids from AP inventory
        unique_site_ids = sorted({info["site_id"] for info in ap_lookup.values() if info["site_id"]})  # WHY: dedupe
        remaining = [sid for sid in unique_site_ids if sid not in completed_sites]  # WHY: skip cached sites
        return remaining, len(unique_site_ids)  # WHY: caller needs both numbers

    @staticmethod
    def _build_wlan_context(
        org_data: dict[str, Any],
        site_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the wlan_context dict passed to per-site resolution helpers.

        WHY: extracted so `_process_sites` stays under the 25-line ceiling.
        """
        return {  # WHY: unified view of every WLAN source the resolver needs
            "wlan_templates": org_data["wlan_templates"],
            "org_wlans": org_data["org_wlans"],
            "wlan_band_lookup": site_state["wlan_bands"],
            "site_template_cache": org_data["site_template_cache"],
        }

    @staticmethod
    def _process_site_batch(
        apisession: Any,
        page_limit: int,
        remaining: list[str],
        batch: SiteBatchContext,
    ) -> bool:
        """Process remaining sites with checkpoint intervals.

        Returns True if all sites processed, False if rate-limited.
        """
        interval = E911BSSIDReportGenerator.CHECKPOINT_INTERVAL  # WHY: local alias for readability
        for index, site_id in enumerate(remaining, 1):  # WHY: 1-based index for user-facing progress
            outcome = E911BSSIDReportGenerator._process_one_site(apisession, page_limit, site_id, batch, index)
            if outcome is False:  # WHY: explicit False signals rate-limited abort
                return False  # WHY: propagate abort upward so caller stops writing
            if index % interval == 0:  # WHY: periodic checkpoint bounds worst-case work loss
                E911BSSIDReportGenerator._save_checkpoint(
                    batch.org_id, batch.org_data, batch.completed_sites, batch.map_lookup, batch.wlan_band_lookup
                )
                logging.warning(
                    "    Progress: %s/%s sites", len(batch.completed_sites), batch.total_sites
                )  # Legacy console echo routed via logger.
        logging.warning(
            "    Done: %s/%s sites enriched.", len(batch.completed_sites), batch.total_sites
        )  # Legacy console echo routed via logger.
        return True  # WHY: caller writes the report

    @staticmethod
    def _process_one_site(
        apisession: Any,
        page_limit: int,
        site_id: str,
        batch: SiteBatchContext,
        index: int,
    ) -> bool | None:
        """Process a single site; return False on rate-limit, None otherwise.

        WHY: extracted from `_process_site_batch` to keep parent ≤25 lines and complexity ≤5.
        """
        site_info = batch.org_data["sites"].get(site_id, {})  # WHY: empty dict when site missing from lookup
        try:  # WHY: rate-limit is the only path that halts the batch
            E911BSSIDReportGenerator._fetch_site_maps(apisession, site_id, page_limit, batch.map_lookup)
            E911BSSIDReportGenerator._resolve_site_ssids(apisession, site_id, page_limit, site_info, batch.wlan_context)
            batch.completed_sites.add(site_id)  # WHY: mark done on successful path
            return None  # WHY: signal "continue"
        except RuntimeError as error:  # WHY: rate-limit sentinel or unexpected runtime error
            if "E911_RATE_LIMIT" in str(error):  # WHY: only our sentinel triggers checkpoint recovery
                return E911BSSIDReportGenerator._handle_rate_limit(batch, index)  # WHY: save + abort
            raise  # WHY: any other RuntimeError should surface for debugging
        except Exception as error:  # WHY: single-site failure should not abort the whole batch
            logging.warning("Error processing site %s: %s", site_id[:8], error)  # WHY: audit failure
            batch.completed_sites.add(site_id)  # WHY: mark done so we do not retry a broken site
            return None  # WHY: signal "continue"

    @staticmethod
    def _handle_rate_limit(
        batch: SiteBatchContext,
        index: int,
    ) -> bool:
        """Handle HTTP 429 rate limit by saving checkpoint."""
        logging.warning(
            "\n  ! Rate limited (HTTP 429) after %s sites this run.", index
        )  # Legacy console echo routed via logger.
        E911BSSIDReportGenerator._save_checkpoint(
            batch.org_id, batch.org_data, batch.completed_sites, batch.map_lookup, batch.wlan_band_lookup
        )
        next_hour = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)  # WHY: rate reset
        logging.warning(
            "    Checkpoint saved: %s/%s sites.", len(batch.completed_sites), batch.total_sites
        )  # Legacy console echo routed via logger.
        logging.warning(
            "    Run Menu 160 again after %s to resume.", next_hour.strftime("%H:%M")
        )  # Legacy console echo routed via logger.
        return False  # WHY: caller uses False to abort the run cleanly

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
        logging.warning("\n=== E911 BSSID Compliance Report ===")  # Legacy console echo routed via logger.
        logging.info("Starting E911 BSSID compliance report generation...")  # WHY: audit trail entry
        start_time = time.time()  # WHY: elapsed-time telemetry at the end
        site_state = E911BSSIDReportGenerator._restore_or_init(org_id, safe_input_fn)  # WHY: resume or fresh state
        org_data = E911BSSIDReportGenerator._load_or_fetch_org(apisession, page_limit, org_id, site_state)  # WHY: bulk
        radio_macs_data = E911BSSIDReportGenerator._require_radio_macs(org_data)  # WHY: early-exit when empty
        if not radio_macs_data:  # WHY: no APs means nothing to report
            return  # WHY: message + logging already emitted by helper
        all_done = E911BSSIDReportGenerator._process_sites(apisession, org_id, page_limit, org_data, site_state)
        if not all_done:  # WHY: rate-limited or aborted -> skip write
            return  # WHY: partial data would misrepresent compliance
        E911BSSIDReportGenerator._write_report(org_data, radio_macs_data, site_state, write_data_fn, start_time)

    @staticmethod
    def _require_radio_macs(org_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Return the radio-MAC list, printing/logging an early-exit message when empty.

        WHY: extracted so `execute` stays ≤25 lines.
        """
        radio_macs_data: list[dict[str, Any]] = org_data["radio_macs"]  # WHY: primary iteration payload
        if not radio_macs_data:  # WHY: nothing to report -> operator feedback + audit trail
            logging.warning("No APs found in this organization.")  # Legacy console echo routed via logger.
            logging.info("No APs found - skipping E911 report generation")  # WHY: audit trail
        return radio_macs_data  # WHY: caller uses truthiness to short-circuit

    @staticmethod
    def _load_or_fetch_org(
        apisession: Any,
        page_limit: int,
        org_id: str,
        site_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Return org-level bulk data, either from checkpoint or a fresh fetch.

        WHY: extracted so `execute` stays ≤25 lines.
        """
        cached: dict[str, Any] | None = site_state.pop(
            "org_data", None
        )  # WHY: checkpoint may already carry the bulk data
        if cached is not None:  # WHY: happy-path resume avoids the bulk fetch
            return cached  # WHY: reuse checkpointed org data verbatim
        return E911BSSIDReportGenerator._fetch_org_bulk_data(apisession, org_id, page_limit)  # WHY: fresh fetch

    @staticmethod
    def _restore_or_init(
        org_id: str,
        safe_input_fn: Callable[..., str],
    ) -> dict[str, Any]:
        """Restore from checkpoint or initialize empty state."""
        checkpoint = E911BSSIDReportGenerator._load_checkpoint(org_id)  # WHY: may return None on fresh run
        if checkpoint is None:  # WHY: fresh run needs empty state
            return E911BSSIDReportGenerator._blank_state()  # WHY: keep the two paths symmetric
        return E911BSSIDReportGenerator._prompt_resume(checkpoint, safe_input_fn)  # WHY: user decides resume vs reset

    @staticmethod
    def _blank_state() -> dict[str, Any]:
        """Return the default empty site_state dict.

        WHY: named factory keeps `_restore_or_init` shape uniform.
        """
        return {  # WHY: matches shape used by `_process_sites`
            "org_data": None,
            "maps": {},
            "wlan_bands": {},
            "completed": set(),
        }

    @staticmethod
    def _prompt_resume(
        checkpoint: dict[str, Any],
        safe_input_fn: Callable[..., str],
    ) -> dict[str, Any]:
        """Ask the user whether to resume from checkpoint.

        WHY: extracted from `_restore_or_init` so both stay ≤25 lines and complexity ≤5.
        """
        done = len(checkpoint.get("completed_sites", []))  # WHY: for progress display
        total = checkpoint.get("total_sites", "?")  # WHY: total may be missing on very old checkpoints
        logging.warning(
            "  Found checkpoint: %s/%s sites completed.", done, total
        )  # Legacy console echo routed via logger.
        resume = safe_input_fn("  Resume from checkpoint? (y/n): ", context="e911_resume")  # WHY: user consent
        if resume.lower() != "y":  # WHY: any answer besides 'y' discards checkpoint
            E911BSSIDReportGenerator._clear_checkpoint()  # WHY: remove stale file
            return E911BSSIDReportGenerator._blank_state()  # WHY: start fresh
        logging.warning("  Restored org data from checkpoint.")  # Legacy console echo routed via logger.
        return {  # WHY: restored state is what `execute` feeds into `_process_sites`
            "org_data": checkpoint["org_data"],
            "maps": checkpoint.get("map_lookup", {}),
            "wlan_bands": checkpoint.get("wlan_band_lookup", {}),
            "completed": set(checkpoint.get("completed_sites", [])),
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
        lookups = E911BSSIDReportGenerator._build_report_lookups(org_data, radio_macs_data, site_state)  # WHY: unified
        rows, compliance_gaps = E911BSSIDReportGenerator._build_bssid_rows(radio_macs_data, lookups)  # WHY: E911 rows
        filename = E911BSSIDReportGenerator._write_csv(rows, write_data_fn)  # WHY: file naming isolated
        logging.warning(
            "\nCSV saved: data/%s (%s BSSIDs)", filename, f"{len(rows):,}"
        )  # Legacy console echo routed via logger.
        unique_sites = {row["Site Name"] for row in rows} - {"Unassigned"}  # WHY: unique real sites in output
        E911BSSIDReportGenerator._display_summary(len(unique_sites), len(radio_macs_data), len(rows), compliance_gaps)
        E911BSSIDReportGenerator._clear_checkpoint()  # WHY: successful run -> no checkpoint needed
        elapsed = time.time() - start_time  # WHY: telemetry for report duration
        logging.info("E911 BSSID report completed in %.1f seconds", elapsed)  # WHY: audit trail
        logging.warning("\nReport completed in %.1f seconds", elapsed)  # Legacy console echo routed via logger.

    @staticmethod
    def _build_report_lookups(
        org_data: dict[str, Any],
        radio_macs_data: list[dict[str, Any]],
        site_state: dict[str, Any],
    ) -> dict[str, Any]:
        """Bundle every lookup dict passed to `_build_bssid_rows`.

        WHY: extracted so `_write_report` stays ≤25 lines.
        """
        return {  # WHY: single dict keeps `_build_bssid_rows` signature small
            "sites": org_data["sites"],
            "aps": org_data["aps"],
            "maps": site_state["maps"],
            "radio_macs": radio_macs_data,
            "radio_bands": org_data["radio_bands"],
            "wlan_bands": site_state["wlan_bands"],
        }

    @staticmethod
    def _write_csv(
        rows: list[dict[str, str]],
        write_data_fn: Callable[..., bool],
    ) -> str:
        """Write BSSID rows to a timestamped CSV file and return the filename.

        WHY: extracted so `_write_report` stays ≤25 lines and file naming lives in one place.
        """
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")  # WHY: sortable timestamp in filename
        filename = f"E911_BSSID_Report_{timestamp_str}.csv"  # WHY: descriptive name for audit trail
        write_data_fn(  # WHY: exporter handles CSV encoding + directory placement
            data=rows,
            filename_or_table=filename,
            api_function_name="generateE911BSSIDReport",
        )
        logging.info("E911 report saved: data/%s (%d BSSIDs)", filename, len(rows))  # WHY: audit success
        return filename  # WHY: caller prints the path to the operator
