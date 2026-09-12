"""Top-level orchestrator for the WAN-override compliance report."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import csv  # Standard library CSV reader for the cached source-of-truth files
import logging  # Standard library structured logging
from typing import Any  # Generic typing for nested CSV rows and lookup dicts

from . import _deps  # Sibling runtime dependency container set by configure_gateway_override_dependencies
from .device_data_fetcher import DeviceDataFetcher  # Live API data fetcher used in the second pass
from .override_classifier import OverrideClassifier  # Per-row classifier used in the first and third passes
from .override_report_writer import OverrideReportWriter  # Final CSV + console output writer


class WanOverrideWalker:
    """End-to-end orchestrator for `with_wan_overrides`: cache, classify, fetch, report."""

    @staticmethod
    def walk(fast: bool = False) -> None:
        """Generate the GatewayOverriddenPorts.csv compliance report end-to-end."""
        logging.info("WAN override walker starting (fast=%s)", fast)  # Trace entry for operator timeline
        logging.info("Gateway Ports Overridden from Template (Compliance Outliers):")  # Legacy header preserved
        logging.info(  # Legacy info line preserved verbatim for downstream log parsers
            " Identifying gateway ports with template overrides (outliers for compliance correction)..."
        )
        target_ports = _deps.MIST_WAN_TARGET_PORTS  # Read from configured module-level dependency
        if not target_ports:  # Early exit when operator has not configured WAN ports to audit
            logging.warning(  # legacy operator banner preserved verbatim for downstream log parsers
                " MIST_WAN_TARGET_PORTS not configured in .env - skipping port override analysis"
            )
            logging.warning("MIST_WAN_TARGET_PORTS environment variable not set")  # operator hint in logs
            return  # No work possible without target ports. Abort the walker
        WanOverrideWalker._run_pipeline(fast=fast, target_ports=target_ports)  # Delegate the full pipeline

    @staticmethod
    def _run_pipeline(fast: bool, target_ports: list[str]) -> None:
        """Run the three-pass pipeline once target_ports is known to be non-empty."""
        logging.debug("Pipeline starting for %d target ports (fast=%s)", len(target_ports), fast)  # trace
        configs, sites, templates = WanOverrideWalker._load_source_csvs(fast)  # First pass input rows
        lookups = WanOverrideWalker._build_lookups(sites, templates)  # site_id->name + template_id->name maps
        devices_with_overrides = WanOverrideWalker._identify_devices(configs, lookups, target_ports)  # 1st pass
        logging.info(  # Legacy info log preserved verbatim for downstream log parsers
            "! Found %d devices with port overrides out of %d total gateway devices",
            len(devices_with_overrides),
            len(configs),
        )
        if not devices_with_overrides:  # Fleet fully compliant: emit empty CSV and exit
            OverrideReportWriter.write_empty()  # Header-only CSV plus the legacy compliance console message
            return  # Done. No live API calls needed
        WanOverrideWalker._run_live_passes(  # Delegate 2nd/3rd passes + final write to keep this fn short
            fast=fast,
            target_ports=target_ports,
            configs=configs,
            devices_with_overrides=devices_with_overrides,
        )

    @staticmethod
    def _run_live_passes(
        fast: bool,
        target_ports: list[str],
        configs: list[dict[str, str]],
        devices_with_overrides: dict[str, dict[str, Any]],
    ) -> None:  # Extracted so _run_pipeline stays under STRUCT-LENGTH limit.
        """Run second/third passes + report write when overrides are present."""
        # WHY: pulls the post-first-pass block out of _run_pipeline to drop it from 27 to <25 lines.
        logging.info(  # Legacy info log preserved verbatim for downstream log parsers
            "! Second pass: Fetching device configs and stats for %d devices with overrides...",
            len(devices_with_overrides),
        )
        cache = DeviceDataFetcher.fetch_all(devices_with_overrides, fast)  # 2nd pass: live device data
        logging.info(" Third pass: Processing overridden ports with live data...")  # legacy log line preserved
        entries = WanOverrideWalker._assemble_entries(devices_with_overrides, cache)  # 3rd pass: build rows
        OverrideReportWriter.write_full(  # Persist via DataExporter + print legacy operator summary block
            entries=entries,
            total_gateways=len(configs),
            devices_with_overrides_count=len(devices_with_overrides),
            target_ports=target_ports,
        )

    @staticmethod
    def _load_source_csvs(
        fast: bool,
    ) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
        """Refresh CSV caches if stale and return the three lists used by the first pass."""
        logging.info("Loading source CSVs (AllSiteGatewayConfigs, SiteList_ListAPI, OrgGatewayTemplates)")  # before
        _deps.CacheUtils.check_and_generate_csv(  # Refresh gateway-device-config cache if missing/stale
            "AllSiteGatewayConfigs.csv",
            lambda: _deps.GatewayExportUtilsRef.device_configs(fast=fast),
        )
        _deps.CacheUtils.check_and_generate_csv(  # Refresh site-list cache if missing/stale
            "SiteList_ListAPI.csv", _deps.OrgSiteExporter.sites_list_api
        )
        _deps.CacheUtils.check_and_generate_csv(  # Refresh gateway-template cache if missing/stale
            "OrgGatewayTemplates.csv", _deps.GatewayExportUtilsRef.templates
        )
        configs = WanOverrideWalker._read_csv("AllSiteGatewayConfigs.csv")  # Flattened device configs
        sites = WanOverrideWalker._read_csv("SiteList_ListAPI.csv")  # Site lookup source
        templates = WanOverrideWalker._read_csv("OrgGatewayTemplates.csv")  # Template lookup source
        logging.debug("Loaded %d configs, %d sites, %d templates", len(configs), len(sites), len(templates))
        return configs, sites, templates  # Hand off to lookup-build + first-pass classification

    @staticmethod
    def _read_csv(filename: str) -> list[dict[str, str]]:
        """Read one cached CSV from the project's standard csv path into a list of dicts."""
        logging.debug("Reading cached CSV %s", filename)  # trace before read
        path = _deps.FilePathUtils.get_csv_path(filename)  # Resolve via project path helper
        with open(path, encoding="utf-8") as csvfile:  # UTF-8 matches the writer used elsewhere
            rows = list(csv.DictReader(csvfile))  # Materialize so we can iterate twice if needed
        return rows  # Hand back to caller for first-pass + lookup-building

    @staticmethod
    def _build_lookups(
        sites: list[dict[str, str]],
        templates: list[dict[str, str]],
    ) -> dict[str, dict[str, str]]:
        """Build the three lookup dicts (site->name, site->template_id, template->name) once."""
        logging.debug("Building site/template lookups from %d sites and %d templates", len(sites), len(templates))
        site_lookup = {site.get("id", ""): site.get("name", "Unknown Site") for site in sites}  # site UUID->name
        site_to_template = {  # site UUID -> assigned gateway template UUID (empty string if unassigned)
            site.get("id", ""): site.get("gatewaytemplate_id", "") for site in sites
        }
        template_lookup = {  # template UUID -> template name (empty when site has no template)
            template.get("id", ""): template.get("name", "Unknown Template") for template in templates
        }
        return {  # Bundle into one dict so downstream helpers can stay under the 5-param limit
            "site_name": site_lookup,
            "site_template": site_to_template,
            "template_name": template_lookup,
        }

    @staticmethod
    def _identify_devices(
        configs: list[dict[str, str]],
        lookups: dict[str, dict[str, str]],
        target_ports: list[str],
    ) -> dict[str, dict[str, Any]]:
        """First pass: build the device-with-overrides dict keyed by device_id."""
        logging.info("First pass: Identifying devices with port overrides...")  # legacy log line preserved
        site_lookup = lookups["site_name"]  # Alias for readability of the loop body below
        site_to_template = lookups["site_template"]  # Alias for readability of the loop body below
        template_lookup = lookups["template_name"]  # Alias for readability of the loop body below
        devices_with_overrides: dict[str, dict[str, Any]] = {}  # Result keyed by device UUID
        for row in configs:  # One row per flattened gateway-device config
            entry = WanOverrideWalker._classify_row(  # Classify the row and (maybe) record its override info
                row=row,
                site_lookup=site_lookup,
                site_to_template=site_to_template,
                template_lookup=template_lookup,
                target_ports=target_ports,
            )
            if entry is not None:  # Helper returns None when the row should be skipped or has no overrides
                devices_with_overrides[entry["device_id"]] = entry  # Key by device UUID for second-pass fetch
        logging.debug("Identified %d devices needing live data", len(devices_with_overrides))  # after
        return devices_with_overrides  # Hand back to orchestrator for the second-pass fetch

    @staticmethod
    def _extract_row_identifiers(row: dict[str, str]) -> tuple[str, str, str] | None:  # Guard helper.
        """Return (device_name, site_id, device_id) or None if any required field is empty."""
        # WHY: collapses three not-empty checks into one, dropping _classify_row CC from 6 to <=5.
        device_name = row.get("name", "").strip()  # Required identifying field for the report
        site_id = row.get("site_id", "").strip()  # Required for downstream API calls
        device_id = row.get("id", "").strip()  # Required as the dict key
        if not device_name or not site_id or not device_id:  # Skip rows missing any required identifier
            return None  # Signal "skip this row" without leaking blank fields downstream
        return device_name, site_id, device_id  # Bundle identifiers for the caller

    @staticmethod
    def _resolve_template_name(
        site_id: str,
        site_to_template: dict[str, str],
        template_lookup: dict[str, str],
    ) -> tuple[str, str]:  # Extracted to keep _classify_row short.
        """Return (template_id, template_name) resolved from the site->template lookups."""
        # WHY: pulls the template-name lookup out of _classify_row to shrink it under 25 lines.
        template_id = site_to_template.get(site_id, "")  # Resolve template UUID (may be empty)
        template_name = template_lookup.get(template_id, "No Template") if template_id else "No Template"  # Label
        return template_id, template_name  # Caller stores both in the returned device-info dict

    @staticmethod
    def _classify_row(
        row: dict[str, str],
        site_lookup: dict[str, str],
        site_to_template: dict[str, str],
        template_lookup: dict[str, str],
        target_ports: list[str],
    ) -> dict[str, Any] | None:
        """Return a populated device-info dict if the row has overrides, else None to skip it."""
        identifiers = WanOverrideWalker._extract_row_identifiers(row)  # Guard: skip incomplete rows
        if identifiers is None:  # Helper returned None because at least one identifier was blank
            return None  # Caller treats None as "no entry to add"
        overridden_ports = OverrideClassifier.classify(row, target_ports)  # Decide which ports are overridden
        if not overridden_ports:  # Skip devices with zero overrides to save API calls in the second pass
            return None  # Caller treats None as "no entry to add"
        _, site_id, _ = identifiers  # Only site_id is needed here. The rest flow through the builder
        template_id, template_name = WanOverrideWalker._resolve_template_name(  # Resolve template metadata
            site_id, site_to_template, template_lookup
        )
        return WanOverrideWalker._build_device_info(  # Delegate dict construction to keep this fn <=25 lines
            identifiers=identifiers,
            row=row,
            site_lookup=site_lookup,
            template=(template_id, template_name),
            overridden_ports=overridden_ports,
        )

    @staticmethod
    def _build_device_info(
        identifiers: tuple[str, str, str],
        row: dict[str, str],
        site_lookup: dict[str, str],
        template: tuple[str, str],
        overridden_ports: list[str],
    ) -> dict[str, Any]:  # Extracted so _classify_row stays under STRUCT-LENGTH limit.
        """Assemble the 8-key device-info dict consumed by the second and third passes."""
        # WHY: pulls the dict literal out of _classify_row to drop it from 28 to <25 lines.
        device_name, site_id, device_id = identifiers  # Unpack the guarded identifier triple
        template_id, template_name = template  # Unpack precomputed template metadata
        return {  # Bundle every field the third pass needs so the orchestrator does not pass extra args
            "device_name": device_name,
            "site_id": site_id,
            "device_id": device_id,
            "site_name": site_lookup.get(site_id, "Unknown Site"),
            "template_id": template_id,
            "template_name": template_name,
            "row_data": row,
            "overridden_ports": overridden_ports,
        }

    @staticmethod
    def _assemble_entries(
        devices_with_overrides: dict[str, dict[str, Any]],
        cache: dict[str, tuple[dict[str, Any], dict[str, Any]]],
    ) -> list[dict[str, Any]]:
        """Third pass: build one CSV row per (device, overridden_port) using cached live data."""
        logging.debug("Assembling entries for %d devices using cached live data", len(devices_with_overrides))
        entries: list[dict[str, Any]] = []  # Accumulator for the final CSV rows
        for device_id, device_info in devices_with_overrides.items():  # Walk every override-flagged device
            port_configs, interface_stats = cache.get(device_id, ({}, {}))  # Empty dicts when fetch failed
            for port_name in device_info["overridden_ports"]:  # Walk every port flagged in pass one
                entry = OverrideClassifier.build_port_entry(  # Build one CSV row per (device, port) pair
                    device_info=device_info,
                    port_name=port_name,
                    port_config=port_configs.get(port_name, {}),  # Empty dict when port absent from live API
                    interface_stat=interface_stats.get(port_name, {}),  # Empty dict when stats unavailable
                )
                entries.append(entry)  # Accumulate for the report writer
        logging.info("Assembled %d total override entries", len(entries))  # after action summary
        return entries  # Hand off to OverrideReportWriter.write_full
