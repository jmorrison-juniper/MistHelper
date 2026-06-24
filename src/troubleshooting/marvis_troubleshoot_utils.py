"""Marvis troubleshooting utilities extracted from MistHelper.py."""

from __future__ import annotations

import json  # JSON formatting for verbose debug dumps of Marvis responses
import logging  # Structured logging at info/debug/error levels per coding standards
from dataclasses import dataclass  # Frozen container for injected collaborators
from typing import Any  # Loose typing for mistapi response objects


@dataclass(frozen=True)
class MarvisTroubleshootDeps:
    """Dependency container for MarvisTroubleshootUtils."""

    apisession: Any  # Authenticated mistapi session object
    mistapi: Any  # mistapi module reference (injected for testability)
    config_utils: Any  # Provides cached org_id resolution
    prompt_client_utils: Any  # Prompts the user to select a client (wired/wireless)
    prompt_utils: Any  # Prompts the user to select a site / device
    data_exporter: Any  # Writes CSV output
    marvis_data_utils: Any  # Formats raw Marvis responses for CSV export
    data_processing_utils: Any  # Generic flatten / escape helpers for nested JSON


# Marvis-related error guidance shared across client/device/network failure paths
_MARVIS_ERROR_GUIDANCE: dict[str, list[str]] = {
    "client": [
        "   - Marvis (VNA) is not enabled for your organization",
        "   - The client is not currently active or found",
        "   - Insufficient permissions for Marvis troubleshooting",
        "   - API connectivity issues",
    ],
    "device": [
        "   - The device is not found or not supported by Marvis",
        "   - Marvis (VNA) is not enabled for your organization",
        "   - Insufficient permissions for device troubleshooting",
    ],
    "network": [
        "   - Marvis (VNA) is not enabled for your organization",
        "   - The site has no devices or insufficient data for analysis",
        "   - Insufficient permissions for network troubleshooting",
    ],
}


class MarvisTroubleshootUtils:
    """Extracted implementation for Marvis troubleshooting workflows."""

    # ---- public workflow entry points ----------------------------------------

    @staticmethod
    def client_connectivity(deps: MarvisTroubleshootDeps) -> None:
        """Troubleshoot client connectivity issues using Marvis AI."""
        print("\n  Client Connectivity Troubleshooting")  # User-facing header
        print("=" * 50)  # Visual separator for menu output

        client_mac, client_type, site_id = deps.prompt_client_utils.select_client()  # Prompt user for target client
        if not client_mac:  # Guard against user cancelling the prompt
            print(" No client selected. Returning to main menu.")
            return

        org_id = deps.config_utils.get_cached_or_prompted_org_id()  # Resolve current org id (cached or prompt)
        params = MarvisTroubleshootUtils._build_client_params(client_mac, client_type, site_id)  # Build API kwargs

        MarvisTroubleshootUtils._announce_client_run(client_mac, client_type, site_id)  # Print + log run banner

        try:
            logging.info("Invoking Marvis troubleshootOrg for client %s", client_mac)  # Pre-action log
            response = deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(  # Call Marvis API
                deps.apisession, org_id, **params
            )
            logging.debug("Marvis client response received (has_data=%s)", bool(response.data))  # Post-action log
            MarvisTroubleshootUtils._handle_client_response(deps, response, client_mac, client_type)  # Dispatch result
        except Exception as error:  # noqa: BLE001 - Marvis SDK raises bare Exception subclasses
            logging.error("Failed to troubleshoot client %s: %s", client_mac, error)  # Log full context
            print(f"! Failed to troubleshoot client: {error}")  # Show user-facing failure
            MarvisTroubleshootUtils._print_error_guidance("client")  # Show guidance bullets

    @staticmethod
    def device_performance(deps: MarvisTroubleshootDeps) -> None:
        """Troubleshoot device performance issues using Marvis AI."""
        logging.debug("MARVIS DEBUG: Entering device_performance()")  # Trace entry per existing debug convention
        print("\n  Device Performance Troubleshooting")  # User-facing header
        print("=" * 50)

        site_id = deps.prompt_utils.select_site()  # Prompt user for target site
        if not site_id:  # User cancelled — exit cleanly
            print(" No site selected.")
            return

        # Issue #431: inlined deps.prompt_utils.select_device -> canonical select_device_id_from_inventory.
        device_id = deps.prompt_utils.select_device_id_from_inventory(site_id)
        if not device_id:
            print(" No device selected.")
            return

        org_id = deps.config_utils.get_cached_or_prompted_org_id()  # Resolve org id once for the API calls below

        device_info = MarvisTroubleshootUtils._lookup_device(deps, site_id, device_id)  # Fetch device mac+name
        if device_info is None:  # Lookup failed or device has no MAC — message already printed
            return
        device_mac, device_name = device_info  # Unpack tuple for downstream use

        MarvisTroubleshootUtils._announce_device_run(site_id, device_mac, device_name)  # Print + log run banner

        try:
            logging.info("Invoking Marvis troubleshootOrg for device %s (mac=%s)", device_name, device_mac)  # Pre-call
            response = deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(  # Marvis device analysis API call
                deps.apisession, org_id, mac=device_mac, site_id=site_id
            )
            logging.debug("Marvis device response received (has_data=%s)", bool(response.data))  # Post-call summary
            MarvisTroubleshootUtils._handle_device_response(deps, response, device_mac, device_name)  # Dispatch result
        except Exception as error:  # noqa: BLE001 - bare Exception is the SDK contract
            logging.error("Exception in device_performance: %s", error, exc_info=True)  # Log with traceback
            print(f"! Failed to troubleshoot device: {error}")
            MarvisTroubleshootUtils._print_error_guidance("device")

        logging.debug("MARVIS DEBUG: Exiting device_performance()")  # Trace exit per existing convention

    @staticmethod
    def network_connectivity(deps: MarvisTroubleshootDeps) -> None:
        """Troubleshoot general network connectivity issues using Marvis AI."""
        logging.debug("MARVIS DEBUG: Entering network_connectivity()")
        print("\n  Network Connectivity Troubleshooting")
        print("=" * 50)

        site_id = deps.prompt_utils.select_site()  # Prompt user for site to analyse
        if not site_id:  # User cancelled
            print(" No site selected.")
            return

        org_id = deps.config_utils.get_cached_or_prompted_org_id()  # Resolve org id from cache or prompt
        MarvisTroubleshootUtils._announce_network_run(site_id)  # Print + log run banner

        try:
            logging.info("Invoking Marvis troubleshootOrg for network site %s", site_id)  # Pre-call log
            response = deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(  # Site-wide Marvis analysis
                deps.apisession, org_id, site_id=site_id
            )
            logging.debug("Marvis network response received (has_data=%s)", bool(response.data))  # Post-call summary
            MarvisTroubleshootUtils._handle_network_response(deps, response, site_id)  # Dispatch into display/save
        except Exception as error:  # noqa: BLE001
            logging.error("Exception in network_connectivity: %s", error, exc_info=True)
            print(f"! Failed to troubleshoot network: {error}")
            MarvisTroubleshootUtils._print_error_guidance("network")

        logging.debug("MARVIS DEBUG: Exiting network_connectivity()")

    # ---- per-workflow response handlers (small, CC <= 10 each) ---------------

    @staticmethod
    def _handle_client_response(
        deps: MarvisTroubleshootDeps,
        response: Any,
        client_mac: str,
        client_type: str,
    ) -> None:
        """Process the Marvis API response for a client troubleshoot run."""
        if not response.data:  # Marvis returned no findings — treat as healthy
            print(" No specific connectivity issues found for this client.")
            print(" This could indicate the client is functioning normally.")
            return

        print(" Marvis AI analysis completed!")
        print("! Analysis results available.")

        data = deps.marvis_data_utils.format_for_csv(response.data, "client")  # Flatten for CSV export
        filename = f"MarvisInsights_Client_{client_mac.replace(':', '')}_{client_type}.csv"  # Stable per-client name
        logging.info("Saving Marvis client CSV to %s", filename)  # Pre-write log
        deps.data_exporter.write_with_format_selection(data, filename)  # Persist results
        logging.debug("Marvis client CSV saved (rows=%s)", len(data) if data else 0)  # Post-write log
        print(f"! Results saved to {filename}")

        MarvisTroubleshootUtils._display_response_summary(response.data, data, "Marvis Analysis Summary")  # Show user

    @staticmethod
    def _handle_device_response(
        deps: MarvisTroubleshootDeps,
        response: Any,
        device_mac: str,
        device_name: str,
    ) -> None:
        """Process the Marvis API response for a device troubleshoot run."""
        if not response.data:  # Healthy device → no findings
            print(" No performance issues detected for this device.")
            print(" This could indicate the device is operating within normal parameters.")
            return

        print(" Marvis AI device analysis completed!")
        data = deps.marvis_data_utils.format_for_csv(response.data, "device")  # CSV-friendly rows
        safe_name = device_name.replace(" ", "_")  # Sanitise device name for filesystem
        filename = f"MarvisInsights_Device_{device_mac.replace(':', '')}_{safe_name}.csv"  # Deterministic filename
        logging.info("Saving Marvis device CSV to %s", filename)
        deps.data_exporter.write_with_format_selection(data, filename)
        logging.debug("Marvis device CSV saved (rows=%s)", len(data) if data else 0)
        print(f"! Results saved to {filename}")

        MarvisTroubleshootUtils._display_response_summary(  # Render user-visible bullet summary
            response.data, data, "Device Performance Analysis", insights_label="Marvis Device Insights"
        )

    @staticmethod
    def _handle_network_response(deps: MarvisTroubleshootDeps, response: Any, site_id: str) -> None:
        """Process the Marvis API response for a site-wide troubleshoot run."""
        if not response.data:  # Healthy site
            print(" No network connectivity issues detected for this site.")
            print(" This indicates the network is operating within normal parameters.")
            return

        print(" Marvis AI network analysis completed!")
        data = deps.marvis_data_utils.format_for_csv(response.data, "network")  # Flatten for CSV
        filename = f"MarvisInsights_Network_{site_id}.csv"  # Per-site filename
        logging.info("Saving Marvis network CSV to %s", filename)
        deps.data_exporter.write_with_format_selection(data, filename)
        logging.debug("Marvis network CSV saved (rows=%s)", len(data) if data else 0)
        print(f"! Results saved to {filename}")

        if not isinstance(response.data, dict):  # Non-dict response → render raw preview only
            preview = str(response.data)[:200]  # Truncate to avoid log/console flooding
            suffix = "..." if len(str(response.data)) > 200 else ""  # Indicate truncation
            print(f"\n  Raw response: {preview}{suffix}")
            return

        MarvisTroubleshootUtils._display_response_summary(  # Render summary with network-specific labels
            response.data,
            data,
            "Network Connectivity Analysis",
            insights_label="Marvis Network Insights",
            show_raw_keys=True,
        )

    # ---- shared display / dispatch helpers (each CC <= 10) -------------------

    @staticmethod
    def _display_response_summary(
        response_data: Any,
        data: Any,
        results_header: str,
        insights_label: str = "Marvis Insights",
        show_raw_keys: bool = False,
    ) -> None:
        """Render a results / insights summary from a Marvis response dict."""
        if not isinstance(response_data, dict):  # Non-dict responses are rendered raw elsewhere
            return
        if "results" in response_data:  # Standard Marvis "results" schema
            MarvisTroubleshootUtils._render_results_section(response_data["results"], results_header)
            return
        if "insights" in response_data:  # Alternate "insights" schema
            MarvisTroubleshootUtils._render_insights_section(response_data["insights"], insights_label)
            return
        # Fallback: response did not include results or insights — show counts and (optionally) raw keys
        items_processed = len(data) if data else 0  # How many flattened rows resulted
        print(f"\n  Analysis Data: {items_processed} items processed")
        if show_raw_keys and response_data:  # Network workflow opted into raw-key preview
            MarvisTroubleshootUtils._print_raw_keys_preview(response_data)

    @staticmethod
    def _render_results_section(results: Any, results_header: str) -> None:
        """Print bullet list for a Marvis ``results`` array."""
        print(f"\n  {results_header}:")  # Section header
        for result in results or []:  # Iterate over each finding (empty list on None)
            if isinstance(result, dict):  # Dict findings have description + optional action
                print(f"  !? {result.get('description', 'Analysis result')}")
                if result.get("action"):  # Show recommended action when present
                    print(f"    Recommended Action: {result['action']}")
            else:  # Non-dict finding → stringify directly
                print(f"  !? {result}")

    @staticmethod
    def _render_insights_section(insights: Any, insights_label: str) -> None:
        """Print bullet list for a Marvis ``insights`` array."""
        print(f"\n  {insights_label}:")  # Section header
        for insight in insights or []:  # Iterate, treating missing list as empty
            description = insight.get("description", insight) if isinstance(insight, dict) else str(insight)
            print(f"  !? {description}")

    @staticmethod
    def _print_raw_keys_preview(response_data: dict) -> None:
        """Print up to five raw key/value pairs for diagnostic visibility."""
        print(f"! Raw response keys: {list(response_data.keys())}")  # Show top-level keys
        for key, value in list(response_data.items())[:5]:  # Bounded preview to avoid console flooding
            text = str(value)  # Stringify for length check + truncation
            suffix = "..." if len(text) > 100 else ""  # Mark truncation
            print(f"   {key}: {text[:100]}{suffix}")

    @staticmethod
    def _print_error_guidance(kind: str) -> None:
        """Print canned guidance bullets for a known Marvis failure category."""
        print(" This may indicate:")  # User-facing intro
        for line in _MARVIS_ERROR_GUIDANCE.get(kind, []):  # Look up bullets by workflow kind
            print(line)

    # ---- workflow-specific micro helpers (one job each, CC = 1-3) ------------

    @staticmethod
    def _build_client_params(client_mac: str, client_type: str, site_id: str | None) -> dict[str, Any]:
        """Assemble keyword arguments for the Marvis client troubleshoot call."""
        params: dict[str, Any] = {"mac": client_mac}  # Mandatory MAC parameter
        if site_id:  # Scope to a site when one was selected
            params["site_id"] = site_id
        if client_type in ("wired", "wireless"):  # Optional explicit client type filter
            params["type"] = client_type
        logging.debug("Built Marvis client params: %s", params)  # Trace the assembled kwargs
        return params

    @staticmethod
    def _announce_client_run(client_mac: str, client_type: str, site_id: str | None) -> None:
        """Print and log the start of a client troubleshoot run."""
        print(f"! Running Marvis AI analysis for client {client_mac}...")  # User banner
        print(f"   Client Type: {client_type}")
        if site_id:  # Only echo site when provided
            print(f"   Site ID: {site_id}")
        logging.info(
            "Starting Marvis client troubleshooting (mac=%s, type=%s, site=%s)",
            client_mac,
            client_type,
            site_id,
        )

    @staticmethod
    def _announce_device_run(site_id: str, device_mac: str, device_name: str) -> None:
        """Print and log the start of a device troubleshoot run."""
        print("! Running Marvis AI performance analysis...")  # User banner
        print(f"   Device: {device_name} ({device_mac})")
        print(f"   Site ID: {site_id}")
        logging.info(
            "Starting Marvis device performance analysis (device=%s, mac=%s, site=%s)",
            device_name,
            device_mac,
            site_id,
        )

    @staticmethod
    def _announce_network_run(site_id: str) -> None:
        """Print and log the start of a network troubleshoot run."""
        print("! Running Marvis AI network analysis...")  # User banner
        print("   Analyzing site-level connectivity")
        print(f"   Site ID: {site_id}")
        logging.info("Starting Marvis network connectivity analysis for site=%s", site_id)

    @staticmethod
    def _lookup_device(deps: MarvisTroubleshootDeps, site_id: str, device_id: str) -> tuple[str, str] | None:
        """Fetch a device record and return (mac, name); print + return None on failure."""
        logging.info("Looking up device %s in site %s", device_id, site_id)  # Pre-call log
        print("! Looking up device details...")  # User progress message
        device_response = deps.mistapi.api.v1.sites.devices.getSiteDevice(  # Fetch device details
            deps.apisession, site_id, device_id
        )
        if not device_response.data:  # Device API returned nothing
            print(" Could not retrieve device details.")
            logging.debug("Device lookup returned empty data for %s", device_id)
            return None

        device_mac = device_response.data.get("mac")  # Extract MAC for downstream Marvis call
        device_name = device_response.data.get("name", "Unknown Device")  # Friendly name fallback
        logging.debug("Resolved device: name=%s mac=%s", device_name, device_mac)  # Post-call log

        if not device_mac:  # Cannot Marvis-query without a MAC
            print(" Could not determine device MAC address.")
            return None

        # Optional full-response dump for deep debugging — kept behind DEBUG level
        logging.debug("Device payload: %s", json.dumps(device_response.data, indent=2, default=str))
        return device_mac, device_name

    # ---- view_insights workflow (unchanged surface) --------------------------

    @staticmethod
    def view_insights(deps: MarvisTroubleshootDeps) -> None:
        """View available Marvis insights and capabilities."""
        print("\n  Marvis (VNA) Insights & Capabilities")
        print("=" * 50)

        org_id = deps.config_utils.get_cached_or_prompted_org_id()  # Resolve org id

        try:
            print(" Checking Marvis availability and organizational insights...")
            logging.info("Fetching org metadata for Marvis insights view (org=%s)", org_id)
            org_response = deps.mistapi.api.v1.orgs.orgs.getOrg(deps.apisession, org_id)  # Org metadata
            logging.debug("Org metadata fetched (has_data=%s)", bool(org_response.data))

            if not org_response.data:
                print(" Could not retrieve organization information.")
                return

            MarvisTroubleshootUtils._display_org_features(org_response.data)  # Show Marvis-related features
            MarvisTroubleshootUtils._fetch_org_insights(org_id, deps)  # Pull live insights endpoints
            MarvisTroubleshootUtils._display_usage_guide()  # Static usage guidance footer
        except Exception as error:  # noqa: BLE001 - surface to UI via shared error handler
            MarvisTroubleshootUtils._handle_insights_error(error)

    @staticmethod
    def _display_org_features(org_info: dict) -> None:
        """Print the org name and any detected Marvis/VNA feature toggles."""
        print(f"! Organization: {org_info.get('name', 'Unknown')}")  # Org banner
        features = org_info.get("features", [])  # Feature flag list (vendor-specific)
        marvis_features = [
            feature
            for feature in features
            if any(keyword in feature.lower() for keyword in ("marvis", "vna", "insight"))  # Filter terms
        ]
        if marvis_features:  # Show detected toggles
            print("\n  Marvis/VNA Features Available:")
            for feature in marvis_features:
                print(f"  !? {feature}")
        else:  # No toggles found
            print("\n  No specific Marvis/VNA features detected in organization settings.")

    @staticmethod
    def _fetch_org_insights(org_id: str, deps: MarvisTroubleshootDeps) -> None:
        """Fetch and display organization-level insights."""
        try:
            print("\n Attempting to retrieve organization-level insights...")
            insight_endpoints = [  # Currently the SLE endpoint is the only available source
                (
                    "Organization Sites SLE",
                    lambda: deps.mistapi.api.v1.orgs.insights.getOrgSitesSle(deps.apisession, org_id),
                ),
            ]

            insights_found = False  # Track whether anything produced output
            for endpoint_name, endpoint_func in insight_endpoints:  # Iterate over registered insight sources
                try:
                    logging.debug("Testing insight endpoint: %s", endpoint_name)
                    response = endpoint_func()  # Live API call
                    if response.data:  # Only display when the endpoint returned data
                        insights_found = MarvisTroubleshootUtils._process_insight_response(
                            endpoint_name, response.data, deps
                        )
                except Exception as endpoint_error:  # noqa: BLE001 - logged via helper
                    MarvisTroubleshootUtils._log_endpoint_error(endpoint_name, endpoint_error)
                    continue

            if not insights_found:  # Tell the user when no endpoint produced data
                print("\n  No organization-level insights currently available.")
        except Exception as error:  # noqa: BLE001
            logging.warning("Could not retrieve organization insights: %s", error)
            print(f"! Could not retrieve insights: {error}")

    @staticmethod
    def _process_insight_response(endpoint_name: str, data: Any, deps: MarvisTroubleshootDeps) -> bool:
        """Process and display one insight endpoint response."""
        insights_data = data if isinstance(data, list) else [data]  # Normalise to list
        logging.debug("%s insights data length: %s", endpoint_name, len(insights_data))

        if not insights_data:  # Nothing to display
            return False

        print(f"\n  {endpoint_name}:")
        for insight in insights_data[:5]:  # Bounded preview — full data goes to CSV below
            description = insight.get("description", insight.get("type", insight.get("name", str(insight))))
            print(f"  !? {description}")

        if len(insights_data) > 5:  # Tell the user there is more in the CSV
            print(f"  ... and {len(insights_data) - 5} more insights")

        if "Sites SLE" in endpoint_name:  # SLE has a dedicated formatter
            formatted_insights = deps.marvis_data_utils.format_for_csv(data, "sites")
        else:  # Generic flatten + escape for unknown insight schemas
            formatted_insights = deps.data_processing_utils.flatten_nested_fields(insights_data)
            formatted_insights = deps.data_processing_utils.escape_multiline(formatted_insights)

        filename = f"MarvisInsights_{endpoint_name.replace(' ', '_')}.csv"  # Stable per-endpoint filename
        logging.info("Saving insights CSV: %s", filename)
        deps.data_exporter.write_with_format_selection(formatted_insights, filename)
        logging.debug("Insights CSV saved (rows=%s)", len(formatted_insights) if formatted_insights else 0)
        print(f"  Full insights saved to {filename}")
        return True

    @staticmethod
    def _log_endpoint_error(endpoint_name: str, exception: Exception) -> None:
        """Log endpoint-specific insight fetch errors."""
        error_message = str(exception)  # Stringified once for the substring checks below
        if "404" in error_message:  # Endpoint not enabled for this org
            logging.debug("Endpoint %s not available for this organization (404): %s", endpoint_name, exception)
        elif "403" in error_message:  # Permission issue
            logging.debug("Access denied to %s (403): %s", endpoint_name, exception)
        else:  # Anything else
            logging.debug("Could not fetch %s: %s", endpoint_name, exception)

    @staticmethod
    def _display_usage_guide() -> None:
        """Display Marvis usage guidance."""
        print("\n  Marvis (VNA - Virtual Network Assistant) Usage Guide:")
        print("   Targeted Troubleshooting:")
        print("     !? Use client troubleshooting for specific device connectivity issues")
        print("     !? Use device troubleshooting for AP, switch, or gateway performance")
        print("     !? Use network troubleshooting for site-wide connectivity analysis")
        print()
        print("   Requirements:")
        print("     !? Marvis must be enabled for your organization")
        print("     !? Devices must be actively managed and reporting data")
        print("     !? Sufficient data history for meaningful analysis")
        print()
        print("   Best Practices:")
        print("     !? Run troubleshooting when issues are actively occurring")
        print("     !? Provide specific timeframes when prompted")
        print("     !? Review saved CSV files for detailed analysis results")

    @staticmethod
    def _handle_insights_error(exception: Exception) -> None:
        """Handle and display insights retrieval errors."""
        logging.error("Failed to get Marvis insights: %s", exception)
        print(f"! Failed to get Marvis insights: {exception}")
        print(" This may indicate:")
        print("   - Marvis (VNA) is not enabled for your organization")
        print("   - Insufficient permissions to view organization details")
        print("   - API connectivity issues")
