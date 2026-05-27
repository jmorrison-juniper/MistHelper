"""Marvis troubleshooting utilities extracted from MistHelper.py."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MarvisTroubleshootDeps:
    """Dependency container for MarvisTroubleshootUtils."""

    apisession: Any
    mistapi: Any
    config_utils: Any
    prompt_client_utils: Any
    prompt_utils: Any
    data_exporter: Any
    marvis_data_utils: Any
    data_processing_utils: Any


class MarvisTroubleshootUtils:
    """Extracted implementation for Marvis troubleshooting workflows."""

    @staticmethod
    def client_connectivity(deps: MarvisTroubleshootDeps) -> None:  # noqa: C901, PLR0912, PLR0915
        """Troubleshoot client connectivity issues using Marvis AI."""
        print("\n  Client Connectivity Troubleshooting")
        print("=" * 50)

        client_mac, client_type, site_id = deps.prompt_client_utils.select_client()
        if not client_mac:
            print(" No client selected. Returning to main menu.")
            return

        org_id = deps.config_utils.get_cached_or_prompted_org_id()

        try:
            print(f"! Running Marvis AI analysis for client {client_mac}...")
            print(f"   Client Type: {client_type}")
            if site_id:
                print(f"   Site ID: {site_id}")

            logging.info(
                "Starting Marvis client troubleshooting for MAC: %s, type: %s, site: %s",
                client_mac,
                client_type,
                site_id,
            )

            params: dict[str, Any] = {"mac": client_mac}
            if site_id:
                params["site_id"] = site_id

            if client_type in ["wired", "wireless"]:
                params["type"] = client_type
                logging.debug("MARVIS DEBUG: Added type parameter: %s", client_type)

            logging.debug("MARVIS DEBUG: About to call troubleshootOrg with params: %s", params)
            response = deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(deps.apisession, org_id, **params)

            if response.data:
                print(" Marvis AI analysis completed!")
                print("! Analysis results available.")

                data = deps.marvis_data_utils.format_for_csv(response.data, "client")
                filename = f"MarvisInsights_Client_{client_mac.replace(':', '')}_{client_type}.csv"
                deps.data_exporter.save_data_to_output(data, filename)
                print(f"! Results saved to {filename}")

                if isinstance(response.data, dict):
                    if "results" in response.data:
                        print("\n  Marvis Analysis Summary:")
                        for result in response.data.get("results", []):
                            print(f"  !? {result.get('description', 'Analysis result')}")
                            if result.get("action"):
                                print(f"    Recommended Action: {result['action']}")
                    elif "insights" in response.data:
                        print("\n  Marvis Insights:")
                        insights = response.data.get("insights", [])
                        for insight in insights:
                            print(f"  !? {insight.get('description', insight)}")
                    else:
                        print(f"\n  Analysis Data: {len(data)} items processed")
            else:
                print(" No specific connectivity issues found for this client.")
                print(" This could indicate the client is functioning normally.")

        except Exception as error:  # noqa: BLE001
            logging.error("Failed to troubleshoot client %s: %s", client_mac, error)
            print(f"! Failed to troubleshoot client: {error}")
            print(" This may indicate:")
            print("   - Marvis (VNA) is not enabled for your organization")
            print("   - The client is not currently active or found")
            print("   - Insufficient permissions for Marvis troubleshooting")
            print("   - API connectivity issues")

    @staticmethod
    def device_performance(deps: MarvisTroubleshootDeps) -> None:  # noqa: C901, PLR0912, PLR0915
        """Troubleshoot device performance issues using Marvis AI."""
        logging.debug("MARVIS DEBUG: Entering device_performance()")
        print("\n  Device Performance Troubleshooting")
        print("=" * 50)

        site_id = deps.prompt_utils.select_site()
        if not site_id:
            print(" No site selected.")
            logging.debug("MARVIS DEBUG: No site selected for device troubleshooting")
            return

        logging.debug("MARVIS DEBUG: Selected site_id: %s", site_id)

        device_id = deps.prompt_utils.select_device(site_id)
        if not device_id:
            print(" No device selected.")
            logging.debug("MARVIS DEBUG: No device selected")
            return

        logging.debug("MARVIS DEBUG: Selected device_id: %s", device_id)
        org_id = deps.config_utils.get_cached_or_prompted_org_id()
        logging.debug("MARVIS DEBUG: Using org_id: %s", org_id)

        try:
            print("! Looking up device details...")
            logging.debug("MARVIS DEBUG: About to get device details for device_id: %s in site: %s", device_id, site_id)

            device_response = deps.mistapi.api.v1.sites.devices.getSiteDevice(deps.apisession, site_id, device_id)
            logging.debug(
                "MARVIS DEBUG: Device lookup response status: %s",
                device_response.status if hasattr(device_response, "status") else "unknown",
            )

            if not device_response.data:
                print(" Could not retrieve device details.")
                logging.debug("MARVIS DEBUG: Device response data is None")
                return

            logging.debug(
                "MARVIS DEBUG: Device data keys: %s",
                list(device_response.data.keys()) if isinstance(device_response.data, dict) else "not a dict",
            )

            device_mac = device_response.data.get("mac")
            device_name = device_response.data.get("name", "Unknown Device")

            logging.debug("MARVIS DEBUG: Device MAC: %s", device_mac)
            logging.debug("MARVIS DEBUG: Device name: %s", device_name)

            if not device_mac:
                print(" Could not determine device MAC address.")
                logging.debug("MARVIS DEBUG: Device MAC is None or empty")
                return

            print("! Running Marvis AI performance analysis...")
            print(f"   Device: {device_name} ({device_mac})")
            print(f"   Site ID: {site_id}")

            logging.info(
                "Starting Marvis device performance analysis for device: %s (MAC: %s)",
                device_name,
                device_mac,
            )
            logging.debug("MARVIS DEBUG: About to call troubleshootOrg with mac=%s, site_id=%s", device_mac, site_id)

            response = deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(
                deps.apisession,
                org_id,
                mac=device_mac,
                site_id=site_id,
            )

            logging.debug(
                "MARVIS DEBUG: Device troubleshoot response status: %s",
                response.status if hasattr(response, "status") else "unknown",
            )
            logging.debug("MARVIS DEBUG: Device response data type: %s", type(response.data))
            logging.debug("MARVIS DEBUG: Device response data is None: %s", response.data is None)

            if response.data:
                logging.debug(
                    "MARVIS DEBUG: Device response data keys: %s",
                    list(response.data.keys()) if isinstance(response.data, dict) else "not a dict",
                )
                logging.debug(
                    "MARVIS DEBUG: Device response data: %s", json.dumps(response.data, indent=2, default=str)
                )

                print(" Marvis AI device analysis completed!")

                data = deps.marvis_data_utils.format_for_csv(response.data, "device")
                logging.debug("MARVIS DEBUG: Formatted device data length: %s", len(data) if data else 0)

                filename = f"MarvisInsights_Device_{device_mac.replace(':', '')}_{device_name.replace(' ', '_')}.csv"
                deps.data_exporter.save_data_to_output(data, filename)
                print(f"! Results saved to {filename}")

                if isinstance(response.data, dict):
                    if "results" in response.data:
                        results = response.data.get("results", [])
                        logging.debug("MARVIS DEBUG: Found %s device results", len(results))
                        print("\n  Device Performance Analysis:")
                        for result in results:
                            print(f"  !? {result.get('description', 'Analysis result')}")
                            if result.get("action"):
                                print(f"    Recommended Action: {result['action']}")
                    elif "insights" in response.data:
                        print("\n  Marvis Device Insights:")
                        insights = response.data.get("insights", [])
                        logging.debug("MARVIS DEBUG: Found %s device insights", len(insights))
                        for insight in insights:
                            print(f"  !? {insight.get('description', insight)}")
                    else:
                        logging.debug("MARVIS DEBUG: No results or insights in device response")
                        print(f"\n  Analysis Data: {len(data)} items processed")
            else:
                logging.debug("MARVIS DEBUG: Device response data is None or empty")
                print(" No performance issues detected for this device.")
                print(" This could indicate the device is operating within normal parameters.")

        except Exception as error:  # noqa: BLE001
            logging.error("MARVIS DEBUG: Exception in device_performance: %s", error)
            logging.error("MARVIS DEBUG: Exception type: %s", type(error))
            logging.error("MARVIS DEBUG: Exception traceback: ", exc_info=True)
            print(f"! Failed to troubleshoot device: {error}")
            print(" This may indicate:")
            print("   - The device is not found or not supported by Marvis")
            print("   - Marvis (VNA) is not enabled for your organization")
            print("   - Insufficient permissions for device troubleshooting")

        logging.debug("MARVIS DEBUG: Exiting device_performance()")

    @staticmethod
    def network_connectivity(deps: MarvisTroubleshootDeps) -> None:  # noqa: C901, PLR0912, PLR0915
        """Troubleshoot general network connectivity issues using Marvis AI."""
        logging.debug("MARVIS DEBUG: Entering network_connectivity()")
        print("\n  Network Connectivity Troubleshooting")
        print("=" * 50)

        site_id = deps.prompt_utils.select_site()
        if not site_id:
            print(" No site selected.")
            logging.debug("MARVIS DEBUG: No site selected, exiting network troubleshooting")
            return

        logging.debug("MARVIS DEBUG: Selected site_id: %s", site_id)
        org_id = deps.config_utils.get_cached_or_prompted_org_id()
        logging.debug("MARVIS DEBUG: Using org_id: %s", org_id)

        try:
            print("! Running Marvis AI network analysis...")
            print("   Analyzing site-level connectivity")
            print(f"   Site ID: {site_id}")

            logging.info("Starting Marvis network connectivity analysis for site: %s", site_id)
            logging.debug(
                "MARVIS DEBUG: About to call troubleshootOrg with org_id=%s, site_id=%s",
                org_id,
                site_id,
            )

            response = deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(
                deps.apisession,
                org_id,
                site_id=site_id,
            )

            logging.debug(
                "MARVIS DEBUG: API response received. Status: %s",
                response.status if hasattr(response, "status") else "unknown",
            )
            logging.debug("MARVIS DEBUG: Response data type: %s", type(response.data))
            logging.debug("MARVIS DEBUG: Response data is None: %s", response.data is None)

            if response.data:
                logging.debug(
                    "MARVIS DEBUG: Response data keys: %s",
                    list(response.data.keys()) if isinstance(response.data, dict) else "not a dict",
                )
                logging.debug(
                    "MARVIS DEBUG: Response data length: %s",
                    len(response.data) if hasattr(response.data, "__len__") else "no length",
                )
                logging.debug(
                    "MARVIS DEBUG: Full response data structure: %s",
                    json.dumps(response.data, indent=2, default=str) if response.data else "None",
                )

                print(" Marvis AI network analysis completed!")

                logging.debug("MARVIS DEBUG: About to format data for CSV")
                data = deps.marvis_data_utils.format_for_csv(response.data, "network")
                logging.debug("MARVIS DEBUG: Formatted data length: %s", len(data) if data else 0)
                logging.debug("MARVIS DEBUG: Formatted data sample: %s", data[:1] if data else "empty")

                filename = f"MarvisInsights_Network_{site_id}.csv"
                deps.data_exporter.save_data_to_output(data, filename)
                print(f"! Results saved to {filename}")
                logging.debug("MARVIS DEBUG: Saved data to %s", filename)

                if isinstance(response.data, dict):
                    logging.debug("MARVIS DEBUG: Response data is a dict, checking for results/insights")
                    if "results" in response.data:
                        results = response.data.get("results", [])
                        logging.debug("MARVIS DEBUG: Found 'results' key with %s items", len(results))
                        print("\n  Network Connectivity Analysis:")
                        for idx, result in enumerate(results):
                            logging.debug("MARVIS DEBUG: Processing result %s: %s", idx, result)
                            description = (
                                result.get("description", "Analysis result")
                                if isinstance(result, dict)
                                else str(result)
                            )
                            print(f"  !? {description}")
                            if isinstance(result, dict) and result.get("action"):
                                print(f"    Recommended Action: {result['action']}")
                    elif "insights" in response.data:
                        insights = response.data.get("insights", [])
                        logging.debug("MARVIS DEBUG: Found 'insights' key with %s items", len(insights))
                        print("\n  Marvis Network Insights:")
                        for idx, insight in enumerate(insights):
                            logging.debug("MARVIS DEBUG: Processing insight %s: %s", idx, insight)
                            description = (
                                insight.get("description", insight) if isinstance(insight, dict) else str(insight)
                            )
                            print(f"  !? {description}")
                    else:
                        logging.debug("MARVIS DEBUG: No 'results' or 'insights' keys found in response data")
                        logging.debug("MARVIS DEBUG: Available keys in response: %s", list(response.data.keys()))
                        print(f"\n  Analysis Data: {len(data)} items processed")
                        if response.data:
                            print(f"! Raw response keys: {list(response.data.keys())}")
                            for key, value in list(response.data.items())[:5]:
                                print(f"   {key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}")
                else:
                    logging.debug("MARVIS DEBUG: Response data is not a dict, type: %s", type(response.data))
                    print(
                        f"\n  Raw response: {str(response.data)[:200]}{'...' if len(str(response.data)) > 200 else ''}"
                    )
            else:
                logging.debug("MARVIS DEBUG: Response data is None or empty")
                print(" No network connectivity issues detected for this site.")
                print(" This indicates the network is operating within normal parameters.")

        except Exception as error:  # noqa: BLE001
            logging.error("MARVIS DEBUG: Exception in network_connectivity: %s", error)
            logging.error("MARVIS DEBUG: Exception type: %s", type(error))
            logging.error("MARVIS DEBUG: Exception traceback: ", exc_info=True)
            print(f"! Failed to troubleshoot network: {error}")
            print(" This may indicate:")
            print("   - Marvis (VNA) is not enabled for your organization")
            print("   - The site has no devices or insufficient data for analysis")
            print("   - Insufficient permissions for network troubleshooting")

        logging.debug("MARVIS DEBUG: Exiting network_connectivity()")

    @staticmethod
    def view_insights(deps: MarvisTroubleshootDeps) -> None:
        """View available Marvis insights and capabilities."""
        print("\n  Marvis (VNA) Insights & Capabilities")
        print("=" * 50)

        org_id = deps.config_utils.get_cached_or_prompted_org_id()

        try:
            print(" Checking Marvis availability and organizational insights...")

            org_response = deps.mistapi.api.v1.orgs.orgs.getOrg(deps.apisession, org_id)

            if org_response.data:
                org_info = org_response.data
                print(f"! Organization: {org_info.get('name', 'Unknown')}")

                features = org_info.get("features", [])
                marvis_features = [
                    feature
                    for feature in features
                    if any(keyword in feature.lower() for keyword in ["marvis", "vna", "insight"])
                ]

                if marvis_features:
                    print("\n  Marvis/VNA Features Available:")
                    for feature in marvis_features:
                        print(f"  !? {feature}")
                else:
                    print("\n  No specific Marvis/VNA features detected in organization settings.")

                MarvisTroubleshootUtils._fetch_org_insights(org_id, deps)
                MarvisTroubleshootUtils._display_usage_guide()
            else:
                print(" Could not retrieve organization information.")

        except Exception as error:  # noqa: BLE001
            MarvisTroubleshootUtils._handle_insights_error(error)

    @staticmethod
    def _fetch_org_insights(org_id: str, deps: MarvisTroubleshootDeps) -> None:
        """Fetch and display organization-level insights."""
        try:
            print("\n Attempting to retrieve organization-level insights...")

            insight_endpoints = [
                (
                    "Organization Sites SLE",
                    lambda: deps.mistapi.api.v1.orgs.insights.getOrgSitesSle(deps.apisession, org_id),
                ),
            ]

            insights_found = False
            for endpoint_name, endpoint_func in insight_endpoints:
                try:
                    logging.debug("MARVIS DEBUG: Testing endpoint: %s", endpoint_name)
                    response = endpoint_func()

                    if response.data:
                        insights_found = MarvisTroubleshootUtils._process_insight_response(
                            endpoint_name,
                            response.data,
                            deps,
                        )
                except Exception as endpoint_error:  # noqa: BLE001
                    MarvisTroubleshootUtils._log_endpoint_error(endpoint_name, endpoint_error)
                    continue

            if not insights_found:
                print("\n  No organization-level insights currently available.")

        except Exception as error:  # noqa: BLE001
            logging.warning("Could not retrieve organization insights: %s", error)
            print(f"! Could not retrieve insights: {error}")

    @staticmethod
    def _process_insight_response(endpoint_name: str, data: Any, deps: MarvisTroubleshootDeps) -> bool:
        """Process and display one insight endpoint response."""
        insights_data = data if isinstance(data, list) else [data]
        logging.debug("MARVIS DEBUG: %s insights data length: %s", endpoint_name, len(insights_data))

        if not insights_data:
            return False

        print(f"\n  {endpoint_name}:")
        for insight in insights_data[:5]:
            description = insight.get("description", insight.get("type", insight.get("name", str(insight))))
            print(f"  !? {description}")

        if len(insights_data) > 5:
            print(f"  ... and {len(insights_data) - 5} more insights")

        if "Sites SLE" in endpoint_name:
            formatted_insights = deps.marvis_data_utils.format_for_csv(data, "sites")
        else:
            formatted_insights = deps.data_processing_utils.flatten_nested_fields(insights_data)
            formatted_insights = deps.data_processing_utils.escape_multiline(formatted_insights)

        filename = f"MarvisInsights_{endpoint_name.replace(' ', '_')}.csv"
        deps.data_exporter.save_data_to_output(formatted_insights, filename)
        print(f"  Full insights saved to {filename}")
        return True

    @staticmethod
    def _log_endpoint_error(endpoint_name: str, exception: Exception) -> None:
        """Log endpoint-specific insight fetch errors."""
        error_message = str(exception)
        if "404" in error_message:
            logging.debug("Endpoint %s not available for this organization (404): %s", endpoint_name, exception)
        elif "403" in error_message:
            logging.debug("Access denied to %s (403): %s", endpoint_name, exception)
        else:
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
        print("   - Organization may not have Marvis licensing")
        print()
        print(" Contact your Mist administrator to:")
        print("   !? Verify Marvis/VNA licensing and enablement")
        print("   !? Confirm user permissions for AI troubleshooting")
        print("   !? Check organization feature settings")
