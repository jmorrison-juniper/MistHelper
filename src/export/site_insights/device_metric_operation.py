"""Executes the device-scope insight metric export (menu 76)."""

from __future__ import annotations

import logging

from src.export import site_insights_exporter as _parent  # Parent module exposes globals + classification helpers


class DeviceMetricOperation:
    """Decomposed replacement for SiteInsightsExporter.device_insights()."""

    @staticmethod
    def execute() -> None:
        """Top-level entry point invoked by the menu dispatcher for menu 76."""
        print("Export Site Device Insights:")  # User-facing banner preserved verbatim from the legacy implementation
        logging.info("Starting export of site device insights...")  # Trace operation start for ops visibility

        print("! Refreshing available insight metrics from Mist API...")  # User-facing progress preserved verbatim
        _parent.SiteInsightsExporter.refresh_insight_metrics_cache()  # Refresh ConstInsightMetrics.csv via canonical site-insights exporter path

        prompts = DeviceMetricOperation._prompt_site_and_device()  # Run both selection prompts up front
        if prompts is None:
            return  # Helper logs the cancel reason and we just exit cleanly
        site_id, device_id = prompts

        site_name = DeviceMetricOperation._resolve_site_name(
            site_id
        )  # Best-effort site label for filename and log lines
        device_info = DeviceMetricOperation._resolve_device_info(site_id, device_id)  # Returns dict with name/mac/model
        device_name = device_info["name"]
        device_mac = device_info["mac"]
        device_model = device_info["model"]

        normalized_mac = DeviceMetricOperation._validate_mac(device_id, device_name, device_mac)  # Bail on invalid MAC
        if normalized_mac is None:
            return

        filename = DeviceMetricOperation._build_filename(
            site_id, site_name, device_id, device_name
        )  # Sanitized output path
        device_metrics = DeviceMetricOperation._filter_metrics(
            device_model
        )  # Skip metrics incompatible with this platform
        if not device_metrics:  # Defensive: missing const file should not silently produce an empty CSV
            print(
                "! No metrics found for device scope. Check ConstInsightMetrics.csv file."
            )  # User-facing error preserved
            logging.error("No device-scope metrics found in const insight metrics")  # Persist failure cause in the log
            _parent.DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]  # Emit empty file for consistency
            return

        all_data, metrics_retrieved = DeviceMetricOperation._collect_metrics(  # Run the per-metric API loop
            site_id,
            site_name,
            device_id,
            device_name,
            normalized_mac,
            device_metrics,
        )
        DeviceMetricOperation._finalize(  # Flatten + save + summary print
            all_data,
            metrics_retrieved,
            filename,
            device_name,
            site_name,
        )

    @staticmethod
    def _prompt_site_and_device() -> tuple[str, str] | None:
        """Prompt for site then device; return None on either cancel."""
        site_id = _parent.PromptUtils.select_site()  # Existing prompt utility handles cancel / invalid input
        if not site_id:
            logging.error("No site selected. Exiting.")  # Match legacy error log message verbatim
            return None
        device_id = _parent.PromptUtils.select_device(site_id)  # Device prompt is scoped by site
        if not device_id:
            logging.error("No device selected. Exiting.")  # Match legacy error log message verbatim
            return None
        return site_id, device_id

    @staticmethod
    def _resolve_site_name(site_id: str) -> str:
        """Best-effort site-name lookup; fall back to site_id when API call fails."""
        try:
            response = _parent.mistapi.api.v1.sites.listSites(
                _parent.apisession, site_id
            )  # API call may raise on auth / network
            sites = _parent.mistapi.get_all(
                response=response, mist_session=_parent.apisession
            )  # Materialize paged result list
            return next(
                (site["name"] for site in sites if site["id"] == site_id), site_id
            )  # Match by id; fall back to id on miss
        except Exception:
            return site_id  # Silent fallback preserves legacy behaviour for offline / degraded API

    @staticmethod
    def _resolve_device_info(site_id: str, device_id: str) -> dict:
        """Best-effort device-name / MAC / model lookup; return shaped dict with defaults on failure."""
        try:
            response = (
                _parent.mistapi.api.v1.sites.devices.listSiteDevices(  # type=all is required for switches and gateways
                    _parent.apisession,
                    site_id,
                    type="all",
                )
            )
            devices = _parent.mistapi.get_all(
                response=response, mist_session=_parent.apisession
            )  # Materialize paged result list
            device = next(
                (dev for dev in devices if dev["id"] == device_id), None
            )  # Locate the device by id within the site
            if device:
                return {  # Found the device: extract the three fields we need downstream
                    "name": device["name"],
                    "mac": device["mac"],
                    "model": device.get("model", ""),
                }
        except Exception:
            pass  # Degrade gracefully so the rest of the flow can still emit a friendly error
        return {"name": device_id, "mac": None, "model": ""}  # Defaults match the legacy fallback behaviour exactly

    @staticmethod
    def _validate_mac(device_id: str, device_name: str, device_mac: str | None) -> str | None:
        """Confirm MAC is present and well-formed; print + log error and return None on failure."""
        if not device_mac:
            print(
                f"! Error: Could not find MAC address for device {device_name}"
            )  # User-facing error preserved verbatim
            logging.error("Could not find MAC address for device %s", device_id)  # Persist failure cause
            return None
        normalized = _parent.SiteInsightsExporter._normalize_device_mac_or_none(
            device_mac
        )  # Helper retains MAC normalization
        if not normalized:
            print(f"! Invalid device MAC address format for {device_name}: {device_mac}")  # User-facing error preserved
            logging.error(
                "Invalid device MAC address format for device %s: %s", device_id, device_mac
            )  # Persist failure cause
            return None
        return normalized

    @staticmethod
    def _build_filename(site_id: str, site_name: str, device_id: str, device_name: str) -> str:
        """Build the sanitized output filename used by both CSV and DB exports."""
        sanitized_site = _parent.EnhancedSSHRunner.sanitize_filename(site_name or site_id)  # Reuse filename sanitizer
        sanitized_device = _parent.EnhancedSSHRunner.sanitize_filename(
            device_name or device_id
        )  # Reuse filename sanitizer
        return f"SiteDeviceInsights_{sanitized_site}_{sanitized_device}.csv"  # Filename pattern preserved verbatim

    @staticmethod
    def _filter_metrics(device_model: str) -> list[str]:
        """Filter the device-scope metric list to those compatible with this device's platform."""
        metrics = _parent.InsightMetricsUtils.get_by_scope(
            "device"
        )  # Pull the device-scope metric list from refreshed cache
        platform = _parent.SiteInsightsExporter._classify_device_platform(
            device_model
        )  # AP / switch / gateway / unknown
        return [  # Keep only metrics that the platform classifier deems compatible
            metric
            for metric in metrics
            if _parent.SiteInsightsExporter._metric_compatible_with_platform(metric, platform)
        ]

    @staticmethod
    def _collect_metrics(  # noqa: PLR0913 - 6 ids/labels required by per-row enrichment
        site_id: str,
        site_name: str,
        device_id: str,
        device_name: str,
        normalized_mac: str,
        device_metrics: list[str],
    ) -> tuple[list[dict], int]:
        """Iterate the device-scope metric list and collect any insight data the API returns."""
        all_device_data: list[dict] = []  # Accumulator for every non-empty metric response
        metrics_retrieved = 0  # User-facing counter shown in the final summary line
        # Progress preserved verbatim with original device-name interpolation
        print(f"! Retrieving {len(device_metrics)} different device insight metrics for {device_name}...")
        labels = {  # Bundle annotation labels so the per-metric helper signature stays small
            "site_id": site_id,
            "site_name": site_name,
            "device_id": device_id,
            "device_name": device_name,
            "device_mac": normalized_mac,
        }
        for metric in device_metrics:  # One API call per metric name; individual failures must not abort the batch
            data = DeviceMetricOperation._fetch_one_metric(
                metric, normalized_mac, labels
            )  # Returns enriched dict or None
            if data is not None:
                all_device_data.append(data)  # Append the enriched per-metric record for export
                metrics_retrieved += 1  # Bump only on successful, non-empty payload
        return all_device_data, metrics_retrieved

    @staticmethod
    def _fetch_one_metric(metric: str, normalized_mac: str, labels: dict) -> dict | None:
        """Fetch a single device insight metric, returning the enriched dict or None on miss / error."""
        try:
            response = (
                _parent.mistapi.api.v1.sites.insights.getSiteInsightMetricsForDevice(  # Device-scoped insight endpoint
                    _parent.apisession,
                    labels["site_id"],
                    metric,
                    normalized_mac,
                )
            )
            data = getattr(response, "data", response) or {}  # Mistapi may return either raw dict or object with .data
            if not data:
                logging.debug(
                    "No data available for device metric: %s", metric
                )  # Trace empty payload at debug level only
                return None
            data["metric_type"] = metric  # Annotate row with metric name for export readability
            for label_key, label_value in labels.items():  # Copy every label into the row for downstream joins
                data[label_key] = label_value
            logging.debug("Retrieved device insight data for metric: %s", metric)  # Trace success at debug level only
            return data
        except Exception as exception:
            logging.debug(
                "Failed to get device insight data for metric %s: %s", metric, exception
            )  # Non-fatal per-metric failure
            return None

    @staticmethod
    def _finalize(
        all_device_data: list[dict],
        metrics_retrieved: int,
        filename: str,
        device_name: str,
        site_name: str,
    ) -> None:
        """Flatten, escape, and save collected data; emit summary user output."""
        try:
            if all_device_data:
                processed = _parent.DataProcessingUtils.flatten_nested_fields(
                    all_device_data
                )  # Flatten nested API objects
                processed = _parent.DataProcessingUtils.escape_multiline(processed)  # type: ignore[no-untyped-call]  # CSV-safe text
                _parent.DataExporter.save_data_to_output(processed, filename)  # type: ignore[no-untyped-call]  # Write to disk / DB
                print(
                    f"! {metrics_retrieved} device insight metrics exported to {filename}"
                )  # User-facing summary preserved
                logging.info(  # Persist success summary at info level for ops visibility
                    "Exported %s device insight metrics for %s at %s to %s",
                    metrics_retrieved,
                    device_name,
                    site_name,
                    filename,
                )
                return
            print(
                f"! 0 device insights exported to {filename} (no data available)"
            )  # User-facing summary preserved verbatim
            logging.warning(  # Distinguish empty result from error for ops triage
                "No device insight data available for %s at %s",
                device_name,
                site_name,
            )
            _parent.DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]  # Always emit a file
        except Exception as exception:
            print(f"! Error exporting device insights: {exception}")  # User-facing error preserved verbatim
            logging.error(  # Persist failure cause with both site and device context for triage
                "Failed to export device insights for %s at %s: %s",
                device_name,
                site_name,
                exception,
            )
            _parent.DataExporter.save_data_to_output([], filename)  # type: ignore[no-untyped-call]  # Always emit a file
