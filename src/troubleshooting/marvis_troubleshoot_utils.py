"""Marvis troubleshooting utilities extracted from MistHelper.py."""

from __future__ import annotations  # WHY: postpone annotation evaluation for forward-ref friendly typing.

import json  # WHY: JSON formatting for verbose debug dumps of Marvis responses.
import logging  # WHY: structured logging at info/debug/error levels per coding standards.
from dataclasses import dataclass  # WHY: frozen container for injected collaborators.
from typing import Any  # WHY: loose typing for opaque mistapi response objects.


@dataclass(frozen=True, slots=True)  # WHY: immutable+slotted deps bundle avoids per-instance dict overhead.
class MarvisTroubleshootDeps:
    """Dependency container for MarvisTroubleshootUtils."""

    apisession: Any  # WHY: authenticated mistapi session object.
    mistapi: Any  # WHY: mistapi module reference (injected for testability).
    config_utils: Any  # WHY: provides cached org_id resolution.
    prompt_client_utils: Any  # WHY: prompts the user to select a client (wired/wireless).
    prompt_utils: Any  # WHY: prompts the user to select a site / device.
    data_exporter: Any  # WHY: writes CSV output.
    marvis_data_utils: Any  # WHY: formats raw Marvis responses for CSV export.
    data_processing_utils: Any  # WHY: generic flatten / escape helpers for nested JSON.


_MARVIS_ERROR_GUIDANCE: dict[str, tuple[str, ...]] = {  # WHY: canned guidance bullets per failure category.
    "client": (
        "   - Marvis (VNA) is not enabled for your organization",
        "   - The client is not currently active or found",
        "   - Insufficient permissions for Marvis troubleshooting",
        "   - API connectivity issues",
    ),
    "device": (
        "   - The device is not found or not supported by Marvis",
        "   - Marvis (VNA) is not enabled for your organization",
        "   - Insufficient permissions for device troubleshooting",
    ),
    "network": (
        "   - Marvis (VNA) is not enabled for your organization",
        "   - The site has no devices or insufficient data for analysis",
        "   - Insufficient permissions for network troubleshooting",
    ),
}

_HEADER_SEP: str = "=" * 50  # WHY: repeated banner divider across workflow entry points.
_MENU_HEADER_CLIENT: str = "\n  Client Connectivity Troubleshooting"  # WHY: client workflow banner.
_MENU_HEADER_DEVICE: str = "\n  Device Performance Troubleshooting"  # WHY: device workflow banner.
_MENU_HEADER_NETWORK: str = "\n  Network Connectivity Troubleshooting"  # WHY: network workflow banner.
_MENU_HEADER_INSIGHTS: str = "\n  Marvis (VNA) Insights & Capabilities"  # WHY: view-insights workflow banner.
_MARVIS_FEATURE_KEYWORDS: tuple[str, ...] = ("marvis", "vna", "insight")  # WHY: Marvis feature toggle markers.
_MAX_PREVIEW_INSIGHTS: int = 5  # WHY: bound console preview to keep insight output readable.
_MAX_RAW_PREVIEW_KEYS: int = 5  # WHY: bound raw-key preview identically to insight preview.
_MAX_RAW_VALUE_LEN: int = 100  # WHY: truncate raw values to keep console lines short.
_MAX_RAW_RESPONSE_LEN: int = 200  # WHY: truncate raw response bodies before printing.
_UNKNOWN_DEVICE: str = "Unknown Device"  # WHY: fallback device name when API omits it.
_INSIGHTS_LABEL_DEFAULT: str = "Marvis Insights"  # WHY: default section header for insights blocks.
_SITES_SLE_ENDPOINT: str = "Organization Sites SLE"  # WHY: only endpoint currently registered for org insights.

_USAGE_GUIDE_LINES: tuple[str, ...] = (  # WHY: static guidance rendered as one consolidated record.
    "\n  Marvis (VNA - Virtual Network Assistant) Usage Guide:",
    "   Targeted Troubleshooting:",
    "     !? Use client troubleshooting for specific device connectivity issues",
    "     !? Use device troubleshooting for AP, switch, or gateway performance",
    "     !? Use network troubleshooting for site-wide connectivity analysis",
    "   Requirements:",
    "     !? Marvis must be enabled for your organization",
    "     !? Devices must be actively managed and reporting data",
    "     !? Sufficient data history for meaningful analysis",
    "   Best Practices:",
    "     !? Run troubleshooting when issues are actively occurring",
    "     !? Provide specific timeframes when prompted",
    "     !? Review saved CSV files for detailed analysis results",
)


class MarvisTroubleshootUtils:
    """Extracted implementation for Marvis troubleshooting workflows."""

    # ---- public workflow entry points ----------------------------------------

    @staticmethod
    def client_connectivity(deps: MarvisTroubleshootDeps) -> None:
        """Troubleshoot client connectivity issues using Marvis AI.

        Why:
            Entry point for the client-scoped Marvis workflow. Routes user
            selection into the API-call wrapper and error boundary.

        Args:
            deps: injected dependency container.
        """
        logging.warning("%s\n%s", _MENU_HEADER_CLIENT, _HEADER_SEP)  # WHY: user-facing menu banner.
        client_mac, client_type, site_id = deps.prompt_client_utils.select_client()  # WHY: pick target client.
        if not client_mac:  # WHY: guard against user cancelling the prompt.
            logging.warning(" No client selected. Returning to main menu.")  # WHY: cancel-path message.
            return  # WHY: exit before any API call.
        org_id = deps.config_utils.get_cached_or_prompted_org_id()  # WHY: resolve org id (cached or prompt).
        params = MarvisTroubleshootUtils._build_client_params(client_mac, client_type, site_id)  # WHY: build kwargs.
        MarvisTroubleshootUtils._announce_client_run(client_mac, client_type, site_id)  # WHY: print+log banner.
        MarvisTroubleshootUtils._invoke_client_troubleshoot(  # WHY: run API call inside error boundary.
            deps, org_id, params, client_mac, client_type
        )

    @staticmethod
    def device_performance(deps: MarvisTroubleshootDeps) -> None:
        """Troubleshoot device performance issues using Marvis AI.

        Why:
            Entry point for the device-scoped Marvis workflow. Wraps site +
            device selection prompts, device metadata lookup, and API dispatch.

        Args:
            deps: injected dependency container.
        """
        logging.debug("MARVIS DEBUG: Entering device_performance()")  # WHY: trace entry per existing convention.
        logging.warning("%s\n%s", _MENU_HEADER_DEVICE, _HEADER_SEP)  # WHY: user-facing menu banner.
        site_id = deps.prompt_utils.select_site()  # WHY: prompt for target site.
        if not site_id:  # WHY: user cancelled site selection.
            logging.warning(" No site selected.")  # WHY: cancel-path message.
            return  # WHY: exit early.
        device_id = deps.prompt_utils.select_device_id_from_inventory(site_id)  # WHY: canonical device chooser.
        if not device_id:  # WHY: user cancelled device selection.
            logging.warning(" No device selected.")  # WHY: cancel-path message.
            return  # WHY: exit early.
        org_id = deps.config_utils.get_cached_or_prompted_org_id()  # WHY: resolve org id once for API call.
        device_info = MarvisTroubleshootUtils._lookup_device(deps, site_id, device_id)  # WHY: fetch mac+name.
        if device_info is None:  # WHY: lookup failed or missing MAC — helper already messaged.
            return  # WHY: exit without invoking Marvis.
        MarvisTroubleshootUtils._invoke_device_troubleshoot(deps, org_id, site_id, device_info)  # WHY: run.
        logging.debug("MARVIS DEBUG: Exiting device_performance()")  # WHY: trace exit per existing convention.

    @staticmethod
    def network_connectivity(deps: MarvisTroubleshootDeps) -> None:
        """Troubleshoot general network connectivity issues using Marvis AI.

        Why:
            Entry point for site-wide Marvis analysis. Dispatches into API
            wrapper after user-facing site selection.

        Args:
            deps: injected dependency container.
        """
        logging.debug("MARVIS DEBUG: Entering network_connectivity()")  # WHY: trace entry.
        logging.warning("%s\n%s", _MENU_HEADER_NETWORK, _HEADER_SEP)  # WHY: user-facing menu banner.
        site_id = deps.prompt_utils.select_site()  # WHY: prompt for site to analyse.
        if not site_id:  # WHY: user cancelled.
            logging.warning(" No site selected.")  # WHY: cancel-path message.
            return  # WHY: exit early.
        org_id = deps.config_utils.get_cached_or_prompted_org_id()  # WHY: resolve org id (cached or prompt).
        MarvisTroubleshootUtils._announce_network_run(site_id)  # WHY: print + log run banner.
        MarvisTroubleshootUtils._invoke_network_troubleshoot(deps, org_id, site_id)  # WHY: run inside boundary.
        logging.debug("MARVIS DEBUG: Exiting network_connectivity()")  # WHY: trace exit.

    # ---- API-call wrappers (isolate try/except so entry points stay <= 25 lines) ----

    @staticmethod
    def _invoke_client_troubleshoot(
        deps: MarvisTroubleshootDeps,
        org_id: str,
        params: dict[str, Any],
        client_mac: str,
        client_type: str,
    ) -> None:
        """Execute the client troubleshoot API call and dispatch response/error paths.

        Why:
            Centralises the try/except boundary around the Marvis client
            troubleshoot SDK call so the calling entry point stays small.

        Args:
            deps: injected dependency container.
            org_id: Mist organisation id.
            params: kwargs forwarded to ``troubleshootOrg``.
            client_mac: MAC address of the selected client.
            client_type: ``wired``/``wireless``/``unknown``.
        """
        try:  # WHY: funnel SDK errors to user guidance.
            logging.info("Invoking Marvis troubleshootOrg for client %s", client_mac)  # WHY: pre-action log.
            response = deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(  # WHY: call Marvis API.
                deps.apisession, org_id, **params
            )
            logging.debug("Marvis client response received (has_data=%s)", bool(response.data))  # WHY: post log.
            MarvisTroubleshootUtils._handle_client_response(deps, response, client_mac, client_type)  # WHY: dispatch.
        except Exception as error:  # noqa: BLE001 - Marvis SDK raises bare Exception subclasses.
            logging.error("Failed to troubleshoot client %s: %s", client_mac, error)  # WHY: log full context.
            MarvisTroubleshootUtils._print_error_guidance(  # WHY: user-visible guidance banner.
                "client", f"! Failed to troubleshoot client: {error}"
            )

    @staticmethod
    def _invoke_device_troubleshoot(
        deps: MarvisTroubleshootDeps,
        org_id: str,
        site_id: str,
        device_info: tuple[str, str],
    ) -> None:
        """Execute the device troubleshoot API call and dispatch response/error paths.

        Why:
            Centralises the try/except boundary around the Marvis device
            troubleshoot SDK call so the calling entry point stays small.

        Args:
            deps: injected dependency container.
            org_id: Mist organisation id.
            site_id: site id the device belongs to.
            device_info: ``(mac, name)`` pair returned by ``_lookup_device``.
        """
        device_mac, device_name = device_info  # WHY: unpack tuple for use in logging + API kwargs.
        MarvisTroubleshootUtils._announce_device_run(site_id, device_mac, device_name)  # WHY: print+log banner.
        try:  # WHY: funnel SDK errors to guidance.
            logging.info(  # WHY: pre-call log identifying device.
                "Invoking Marvis troubleshootOrg for device %s (mac=%s)", device_name, device_mac
            )
            response = deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(  # WHY: Marvis device analysis call.
                deps.apisession, org_id, mac=device_mac, site_id=site_id
            )
            logging.debug("Marvis device response received (has_data=%s)", bool(response.data))  # WHY: post log.
            MarvisTroubleshootUtils._handle_device_response(deps, response, device_mac, device_name)  # WHY: dispatch.
        except Exception as error:  # noqa: BLE001 - bare Exception is the SDK contract.
            logging.exception("Exception in device_performance: %s", error)  # WHY: log with traceback.
            MarvisTroubleshootUtils._print_error_guidance(  # WHY: user-visible guidance banner.
                "device", f"! Failed to troubleshoot device: {error}"
            )

    @staticmethod
    def _invoke_network_troubleshoot(deps: MarvisTroubleshootDeps, org_id: str, site_id: str) -> None:
        """Execute the network troubleshoot API call and dispatch response/error paths.

        Why:
            Centralises the try/except boundary around the site-wide Marvis
            troubleshoot SDK call so the calling entry point stays small.

        Args:
            deps: injected dependency container.
            org_id: Mist organisation id.
            site_id: site id being analysed.
        """
        try:  # WHY: funnel SDK errors to guidance.
            logging.info("Invoking Marvis troubleshootOrg for network site %s", site_id)  # WHY: pre-call log.
            response = deps.mistapi.api.v1.orgs.troubleshoot.troubleshootOrg(  # WHY: site-wide Marvis analysis.
                deps.apisession, org_id, site_id=site_id
            )
            logging.debug("Marvis network response received (has_data=%s)", bool(response.data))  # WHY: post log.
            MarvisTroubleshootUtils._handle_network_response(deps, response, site_id)  # WHY: dispatch into display.
        except Exception as error:  # noqa: BLE001 - bare Exception is the SDK contract.
            logging.exception("Exception in network_connectivity: %s", error)  # WHY: log with traceback.
            MarvisTroubleshootUtils._print_error_guidance(  # WHY: user-visible guidance banner.
                "network", f"! Failed to troubleshoot network: {error}"
            )

    # ---- per-workflow response handlers (small, CC <= 5 each) ----------------

    @staticmethod
    def _handle_client_response(
        deps: MarvisTroubleshootDeps,
        response: Any,
        client_mac: str,
        client_type: str,
    ) -> None:
        """Process the Marvis API response for a client troubleshoot run.

        Why:
            Splits healthy-vs-issue rendering off the API wrapper so each
            path stays small and testable.

        Args:
            deps: injected dependency container.
            response: raw SDK response object.
            client_mac: MAC address of the target client.
            client_type: ``wired``/``wireless``/``unknown``.
        """
        if not response.data:  # WHY: Marvis returned no findings — treat as healthy.
            logging.warning(  # WHY: healthy-path message consolidated into one record.
                " No specific connectivity issues found for this client.\n"
                " This could indicate the client is functioning normally."
            )
            return  # WHY: nothing left to save.
        logging.warning(  # WHY: success banner + follow-up prompt as one record.
            " Marvis AI analysis completed!\n! Analysis results available."
        )
        data = deps.marvis_data_utils.format_for_csv(response.data, "client")  # WHY: flatten for CSV export.
        filename = f"MarvisInsights_Client_{client_mac.replace(':', '')}_{client_type}.csv"  # WHY: stable name.
        MarvisTroubleshootUtils._persist_csv(deps, data, filename, "client")  # WHY: write + log.
        MarvisTroubleshootUtils._display_response_summary(  # WHY: render bullet summary for user.
            response.data, data, "Marvis Analysis Summary"
        )

    @staticmethod
    def _handle_device_response(
        deps: MarvisTroubleshootDeps,
        response: Any,
        device_mac: str,
        device_name: str,
    ) -> None:
        """Process the Marvis API response for a device troubleshoot run.

        Why:
            Splits healthy-vs-issue rendering off the API wrapper so each
            path stays small and testable.

        Args:
            deps: injected dependency container.
            response: raw SDK response object.
            device_mac: MAC address of the target device.
            device_name: friendly device name for filenames.
        """
        if not response.data:  # WHY: healthy device — no findings.
            logging.warning(  # WHY: healthy-path message consolidated into one record.
                " No performance issues detected for this device.\n"
                " This could indicate the device is operating within normal parameters."
            )
            return  # WHY: nothing to save.
        logging.warning(" Marvis AI device analysis completed!")  # WHY: success banner.
        data = deps.marvis_data_utils.format_for_csv(response.data, "device")  # WHY: CSV-friendly rows.
        safe_name = device_name.replace(" ", "_")  # WHY: sanitise device name for filesystem.
        filename = f"MarvisInsights_Device_{device_mac.replace(':', '')}_{safe_name}.csv"  # WHY: deterministic.
        MarvisTroubleshootUtils._persist_csv(deps, data, filename, "device")  # WHY: write + log.
        MarvisTroubleshootUtils._display_response_summary(  # WHY: render bullet summary.
            response.data, data, "Device Performance Analysis", insights_label="Marvis Device Insights"
        )

    @staticmethod
    def _handle_network_response(deps: MarvisTroubleshootDeps, response: Any, site_id: str) -> None:
        """Process the Marvis API response for a site-wide troubleshoot run.

        Why:
            Splits healthy-vs-issue rendering off the API wrapper so each
            path stays small and testable.

        Args:
            deps: injected dependency container.
            response: raw SDK response object.
            site_id: site id being analysed.
        """
        if not response.data:  # WHY: healthy site — no findings.
            logging.warning(  # WHY: healthy-path message consolidated into one record.
                " No network connectivity issues detected for this site.\n"
                " This indicates the network is operating within normal parameters."
            )
            return  # WHY: nothing to save.
        logging.warning(" Marvis AI network analysis completed!")  # WHY: success banner.
        data = deps.marvis_data_utils.format_for_csv(response.data, "network")  # WHY: flatten for CSV.
        filename = f"MarvisInsights_Network_{site_id}.csv"  # WHY: per-site filename.
        MarvisTroubleshootUtils._persist_csv(deps, data, filename, "network")  # WHY: write + log.
        if not isinstance(response.data, dict):  # WHY: non-dict response → render raw preview only.
            MarvisTroubleshootUtils._print_raw_response_preview(response.data)  # WHY: bounded preview helper.
            return  # WHY: no structured summary available.
        MarvisTroubleshootUtils._display_response_summary(  # WHY: render summary with network labels.
            response.data,
            data,
            "Network Connectivity Analysis",
            insights_label="Marvis Network Insights",
            show_raw_keys=True,
        )

    @staticmethod
    def _persist_csv(deps: MarvisTroubleshootDeps, data: Any, filename: str, kind: str) -> None:
        """Write a Marvis CSV artifact with symmetric info/debug logging around the call.

        Why:
            Centralises the info+debug logging bracket so per-workflow
            handlers do not repeat the same three-line pattern.

        Args:
            deps: injected dependency container.
            data: CSV-ready row payload.
            filename: output filename (already sanitised).
            kind: human-readable category (``client``/``device``/``network``).
        """
        logging.info("Saving Marvis %s CSV to %s", kind, filename)  # WHY: pre-write log with category.
        deps.data_exporter.write_with_format_selection(data, filename)  # WHY: persist results.
        row_count = len(data) if data else 0  # WHY: guard against None/empty rows before len().
        logging.debug("Marvis %s CSV saved (rows=%s)", kind, row_count)  # WHY: post-write log.
        logging.warning("! Results saved to %s", filename)  # WHY: user confirmation.

    # ---- shared display / dispatch helpers (each CC <= 5) --------------------

    @staticmethod
    def _display_response_summary(
        response_data: Any,
        data: Any,
        results_header: str,
        insights_label: str = _INSIGHTS_LABEL_DEFAULT,
        show_raw_keys: bool = False,
    ) -> None:
        """Render a results / insights summary from a Marvis response dict.

        Why:
            Common dispatch for the three response handlers so schema-branch
            logic lives in one place.

        Args:
            response_data: raw response ``data`` field.
            data: CSV-formatted rows already produced from ``response_data``.
            results_header: header for the ``results`` branch.
            insights_label: header for the ``insights`` branch.
            show_raw_keys: whether to render a raw-key preview in fallback.
        """
        if not isinstance(response_data, dict):  # WHY: non-dict responses are rendered raw elsewhere.
            return  # WHY: nothing structured to summarise.
        if "results" in response_data:  # WHY: standard Marvis results schema.
            MarvisTroubleshootUtils._render_results_section(
                response_data["results"], results_header
            )  # WHY: results branch.
            return  # WHY: matched schema already rendered.
        if "insights" in response_data:  # WHY: alternate insights schema.
            MarvisTroubleshootUtils._render_insights_section(
                response_data["insights"], insights_label
            )  # WHY: insights branch.
            return  # WHY: matched schema already rendered.
        MarvisTroubleshootUtils._render_summary_fallback(response_data, data, show_raw_keys)  # WHY: fallback path.

    @staticmethod
    def _render_summary_fallback(response_data: dict, data: Any, show_raw_keys: bool) -> None:
        """Fallback renderer when neither ``results`` nor ``insights`` keys are present.

        Why:
            Ensures unknown Marvis schemas still surface item counts and, for
            the network workflow, a bounded key preview.

        Args:
            response_data: raw response dict.
            data: CSV-formatted rows.
            show_raw_keys: whether to render the raw-key preview.
        """
        items_processed = len(data) if data else 0  # WHY: how many flattened rows resulted.
        logging.warning("\n  Analysis Data: %s items processed", items_processed)  # WHY: user-facing count.
        if show_raw_keys and response_data:  # WHY: network workflow opted into raw-key preview.
            MarvisTroubleshootUtils._print_raw_keys_preview(response_data)  # WHY: bounded preview.

    @staticmethod
    def _render_results_section(results: Any, results_header: str) -> None:
        """Print bullet list for a Marvis ``results`` array.

        Why:
            Consumers want a single dispatch that emits header + bullets even
            when the API returns ``None`` or an empty list.

        Args:
            results: iterable of finding dicts / raw scalars.
            results_header: heading to render before bullets.
        """
        logging.warning("\n  %s:", results_header)  # WHY: section header.
        for result in results or []:  # WHY: iterate. Treat missing list as empty.
            MarvisTroubleshootUtils._print_result_bullet(result)  # WHY: per-result renderer.

    @staticmethod
    def _print_result_bullet(result: Any) -> None:
        """Print a single result bullet, including recommended action when present.

        Why:
            Isolates per-result rendering so the loop stays tight and dict/
            non-dict fallbacks stay together.

        Args:
            result: dict finding or raw scalar.
        """
        if not isinstance(result, dict):  # WHY: non-dict finding — stringify directly.
            logging.warning("  !? %s", result)  # WHY: fallback rendering.
            return  # WHY: nothing more to display.
        description = result.get("description", "Analysis result")  # WHY: cache lookup for downstream branches.
        action = result.get("action")  # WHY: optional recommended action.
        if action:  # WHY: only show action when the API supplied one.
            logging.warning("  !? %s\n    Recommended Action: %s", description, action)  # WHY: bullet + action.
            return  # WHY: rendered together to keep one record per finding.
        logging.warning("  !? %s", description)  # WHY: dict finding without action.

    @staticmethod
    def _render_insights_section(insights: Any, insights_label: str) -> None:
        """Print bullet list for a Marvis ``insights`` array.

        Why:
            Parallel to results dispatch. Keeps the insights-vs-results branch
            symmetrical for maintenance.

        Args:
            insights: iterable of insight dicts / raw scalars.
            insights_label: heading to render before bullets.
        """
        logging.warning("\n  %s:", insights_label)  # WHY: section header.
        for insight in insights or []:  # WHY: iterate. Treat missing list as empty.
            description = MarvisTroubleshootUtils._insight_description(insight)  # WHY: consistent renderer.
            logging.warning("  !? %s", description)  # WHY: bullet output.

    @staticmethod
    def _insight_description(insight: Any) -> str:
        """Return a human-readable description string for a raw insight payload.

        Why:
            Consumers need a single stringification rule regardless of whether
            the API returns a dict or a scalar.

        Args:
            insight: raw insight (dict or scalar).

        Returns:
            String description suitable for a bullet render.
        """
        if isinstance(insight, dict):  # WHY: dicts expose a preferred description field.
            return str(insight.get("description", insight))  # WHY: fallback to repr when missing.
        return str(insight)  # WHY: non-dicts stringify directly.

    @staticmethod
    def _print_raw_keys_preview(response_data: dict) -> None:
        """Print up to five raw key/value pairs for diagnostic visibility.

        Why:
            Gives operators a bounded look at unknown Marvis payloads without
            dumping potentially unbounded content.

        Args:
            response_data: raw response dict.
        """
        lines = [f"! Raw response keys: {list(response_data.keys())}"]  # WHY: show top-level keys.
        for key, value in list(response_data.items())[:_MAX_RAW_PREVIEW_KEYS]:  # WHY: bounded preview.
            text = str(value)  # WHY: stringify for length check + truncation.
            suffix = "..." if len(text) > _MAX_RAW_VALUE_LEN else ""  # WHY: mark truncation.
            lines.append(f"   {key}: {text[:_MAX_RAW_VALUE_LEN]}{suffix}")  # WHY: truncated preview line.
        logging.warning("%s", "\n".join(lines))  # WHY: emit consolidated preview as one record.

    @staticmethod
    def _print_raw_response_preview(response_data: Any) -> None:
        """Print a bounded stringified preview of a non-dict Marvis response body.

        Why:
            Non-dict payloads still deserve visibility. Truncation avoids
            flooding the log with huge bodies.

        Args:
            response_data: raw response body.
        """
        text = str(response_data)  # WHY: stringify once for length checks.
        suffix = "..." if len(text) > _MAX_RAW_RESPONSE_LEN else ""  # WHY: mark truncation.
        logging.warning("\n  Raw response: %s%s", text[:_MAX_RAW_RESPONSE_LEN], suffix)  # WHY: bounded preview.

    @staticmethod
    def _print_error_guidance(kind: str, failure_message: str | None = None) -> None:
        """Print canned guidance bullets for a known Marvis failure category.

        Why:
            Collapses the failure banner + guidance bullets into one atomic
            record. Callers optionally prepend a workflow-specific failure
            message so users see the error and remediation together.

        Args:
            kind: workflow key (``client``/``device``/``network``).
            failure_message: optional workflow-specific failure banner
                prepended above the shared "This may indicate:" intro.
        """
        lines: list[str] = []  # WHY: assemble multi-line record.
        if failure_message:  # WHY: workflow wrappers pass ``! Failed to troubleshoot ...``.
            lines.append(failure_message)  # WHY: user-visible failure banner first.
        lines.append(" This may indicate:")  # WHY: shared guidance intro.
        lines.extend(_MARVIS_ERROR_GUIDANCE.get(kind, ()))  # WHY: guidance bullets for known kinds.
        logging.warning("%s", "\n".join(lines))  # WHY: emit consolidated guidance as one record.

    # ---- workflow-specific micro helpers (one job each, CC <= 3) -------------

    @staticmethod
    def _build_client_params(client_mac: str, client_type: str, site_id: str | None) -> dict[str, Any]:
        """Assemble keyword arguments for the Marvis client troubleshoot call.

        Why:
            Kept as a pure builder so the invocation wrapper stays free of
            optional-parameter branching.

        Args:
            client_mac: MAC address (mandatory).
            client_type: ``wired``/``wireless``/``unknown``.
            site_id: optional site scope.

        Returns:
            Kwargs dict ready for ``**params`` expansion into the SDK call.
        """
        params: dict[str, Any] = {"mac": client_mac}  # WHY: mandatory MAC parameter.
        if site_id:  # WHY: scope to a site when one was selected.
            params["site_id"] = site_id  # WHY: attach site filter.
        if client_type in ("wired", "wireless"):  # WHY: optional explicit client type filter.
            params["type"] = client_type  # WHY: attach type filter.
        logging.debug("Built Marvis client params: %s", params)  # WHY: trace the assembled kwargs.
        return params  # WHY: hand back to caller for **params expansion.

    @staticmethod
    def _announce_client_run(client_mac: str, client_type: str, site_id: str | None) -> None:
        """Print and log the start of a client troubleshoot run.

        Why:
            Users need a visible confirmation of which client is about to be
            analysed. A paired structured log captures the same context for
            operators reading the logs.

        Args:
            client_mac: MAC of the selected client.
            client_type: ``wired``/``wireless``/``unknown``.
            site_id: optional site scope (omitted from the banner when None).
        """
        lines = [  # WHY: assemble consolidated banner for one record.
            f"! Running Marvis AI analysis for client {client_mac}...",
            f"   Client Type: {client_type}",
        ]
        if site_id:  # WHY: only echo site when provided (test verifies omission).
            lines.append(f"   Site ID: {site_id}")  # WHY: echo site id.
        logging.warning("%s", "\n".join(lines))  # WHY: user banner as single record.
        logging.info(  # WHY: structured pre-run record.
            "Starting Marvis client troubleshooting (mac=%s, type=%s, site=%s)",
            client_mac,
            client_type,
            site_id,
        )

    @staticmethod
    def _announce_device_run(site_id: str, device_mac: str, device_name: str) -> None:
        """Print and log the start of a device troubleshoot run.

        Why:
            Users need a visible confirmation of which device is about to be
            analysed. A paired structured log captures the same context for
            operators reading the logs.

        Args:
            site_id: site id the device belongs to.
            device_mac: MAC address of the device.
            device_name: friendly device name.
        """
        logging.warning(  # WHY: user banner consolidated into one record.
            "! Running Marvis AI performance analysis...\n" "   Device: %s (%s)\n" "   Site ID: %s",
            device_name,
            device_mac,
            site_id,
        )
        logging.info(  # WHY: structured pre-run record.
            "Starting Marvis device performance analysis (device=%s, mac=%s, site=%s)",
            device_name,
            device_mac,
            site_id,
        )

    @staticmethod
    def _announce_network_run(site_id: str) -> None:
        """Print and log the start of a network troubleshoot run.

        Why:
            Users need a visible confirmation of which site is about to be
            analysed. A paired structured log captures the same context for
            operators reading the logs.

        Args:
            site_id: site id being analysed.
        """
        logging.warning(  # WHY: user banner consolidated into one record.
            "! Running Marvis AI network analysis...\n" "   Analyzing site-level connectivity\n" "   Site ID: %s",
            site_id,
        )
        logging.info("Starting Marvis network connectivity analysis for site=%s", site_id)  # WHY: structured log.

    @staticmethod
    def _lookup_device(deps: MarvisTroubleshootDeps, site_id: str, device_id: str) -> tuple[str, str] | None:
        """Fetch a device record and return (mac, name). Print + return None on failure.

        Why:
            Marvis needs a MAC to run. The device lookup lives in its own
            helper so the entry point stays small and testable.

        Args:
            deps: injected dependency container.
            site_id: site id the device belongs to.
            device_id: Mist device id.

        Returns:
            ``(mac, name)`` on success, else ``None`` after emitting a
            user-facing warning describing the failure.
        """
        logging.info("Looking up device %s in site %s", device_id, site_id)  # WHY: pre-call log.
        logging.warning("! Looking up device details...")  # WHY: user progress message.
        device_response = deps.mistapi.api.v1.sites.devices.getSiteDevice(  # WHY: fetch device details.
            deps.apisession, site_id, device_id
        )
        if not device_response.data:  # WHY: device API returned nothing.
            logging.warning(" Could not retrieve device details.")  # WHY: user message.
            logging.debug("Device lookup returned empty data for %s", device_id)  # WHY: diagnostic.
            return None  # WHY: signal failure to caller.
        device_mac = device_response.data.get("mac")  # WHY: extract MAC for downstream Marvis call.
        device_name = device_response.data.get("name", _UNKNOWN_DEVICE)  # WHY: friendly name fallback.
        logging.debug("Resolved device: name=%s mac=%s", device_name, device_mac)  # WHY: post-call log.
        if not device_mac:  # WHY: cannot Marvis-query without a MAC.
            logging.warning(" Could not determine device MAC address.")  # WHY: user message.
            return None  # WHY: signal failure to caller.
        logging.debug("Device payload: %s", json.dumps(device_response.data, indent=2, default=str))  # WHY: dump.
        return device_mac, device_name  # WHY: hand back tuple for downstream API call.

    # ---- view_insights workflow (unchanged surface) --------------------------

    @staticmethod
    def view_insights(deps: MarvisTroubleshootDeps) -> None:
        """View available Marvis insights and capabilities.

        Why:
            Entry point that orchestrates the org metadata + insights + usage
            guide render pipeline under a single error boundary.

        Args:
            deps: injected dependency container.
        """
        logging.warning("%s\n%s", _MENU_HEADER_INSIGHTS, _HEADER_SEP)  # WHY: user-facing menu banner.
        org_id = deps.config_utils.get_cached_or_prompted_org_id()  # WHY: resolve org id.
        try:  # WHY: funnel unexpected errors to shared handler.
            org_info = MarvisTroubleshootUtils._fetch_org_info(deps, org_id)  # WHY: pull org metadata.
            if org_info is None:  # WHY: helper already reported the failure.
                return  # WHY: exit without rendering downstream sections.
            MarvisTroubleshootUtils._display_org_features(org_info)  # WHY: show Marvis-related features.
            MarvisTroubleshootUtils._fetch_org_insights(org_id, deps)  # WHY: pull live insights endpoints.
            MarvisTroubleshootUtils._display_usage_guide()  # WHY: static usage guidance footer.
        except Exception as error:  # noqa: BLE001 - surface to UI via shared error handler.
            MarvisTroubleshootUtils._handle_insights_error(error)  # WHY: standard error path.

    @staticmethod
    def _fetch_org_info(deps: MarvisTroubleshootDeps, org_id: str) -> dict | None:
        """Return org metadata dict or None if the API call produced no data.

        Why:
            Isolates the metadata call so ``view_insights`` stays flat.

        Args:
            deps: injected dependency container.
            org_id: Mist organisation id.

        Returns:
            Org metadata dict on success, else ``None`` after logging a
            user-facing warning.
        """
        logging.warning(" Checking Marvis availability and organizational insights...")  # WHY: progress message.
        logging.info("Fetching org metadata for Marvis insights view (org=%s)", org_id)  # WHY: pre-call log.
        org_response = deps.mistapi.api.v1.orgs.orgs.getOrg(deps.apisession, org_id)  # WHY: org metadata call.
        logging.debug("Org metadata fetched (has_data=%s)", bool(org_response.data))  # WHY: post-call log.
        if not org_response.data:  # WHY: empty response — cannot render insights.
            logging.warning(" Could not retrieve organization information.")  # WHY: user message.
            return None  # WHY: signal failure.
        return org_response.data  # WHY: hand back raw dict to caller.

    @staticmethod
    def _display_org_features(org_info: dict) -> None:
        """Print the org name and any detected Marvis/VNA feature toggles.

        Why:
            Provides quick visibility into whether Marvis features are
            enabled for the current organisation.

        Args:
            org_info: org metadata dict from the API.
        """
        logging.warning("! Organization: %s", org_info.get("name", "Unknown"))  # WHY: org banner.
        marvis_features = MarvisTroubleshootUtils._filter_marvis_features(org_info.get("features", []))  # WHY: filter.
        if not marvis_features:  # WHY: no toggles found.
            logging.warning("\n  No specific Marvis/VNA features detected in organization settings.")  # WHY: message.
            return  # WHY: nothing to enumerate.
        lines = ["\n  Marvis/VNA Features Available:"]  # WHY: section header.
        for feature in marvis_features:  # WHY: enumerate detected toggles.
            lines.append(f"  !? {feature}")  # WHY: bullet output.
        logging.warning("%s", "\n".join(lines))  # WHY: emit consolidated section as one record.

    @staticmethod
    def _filter_marvis_features(features: Any) -> list[str]:
        """Return org feature entries whose name mentions any Marvis/VNA keyword.

        Why:
            Central filter so both the enumeration and any future callers use
            identical keyword matching.

        Args:
            features: raw features list from the API.

        Returns:
            List of feature names that matched a Marvis/VNA keyword.
        """
        return [  # WHY: comprehension keeps the caller free of branching.
            feature
            for feature in (features or [])  # WHY: tolerate None/empty input.
            if isinstance(feature, str)  # WHY: only string names participate in the keyword match.
            and MarvisTroubleshootUtils._is_marvis_feature(feature)  # WHY: substring match helper.
        ]

    @staticmethod
    def _is_marvis_feature(feature: str) -> bool:
        """Return True if the feature name contains any known Marvis/VNA keyword.

        Why:
            Central keyword scanner keeps the substring set in one place.

        Args:
            feature: feature name (case-insensitive match applied).

        Returns:
            True if any known Marvis/VNA keyword substring is present.
        """
        lowered = feature.lower()  # WHY: case-insensitive matching.
        return any(keyword in lowered for keyword in _MARVIS_FEATURE_KEYWORDS)  # WHY: keyword scan.

    @staticmethod
    def _fetch_org_insights(org_id: str, deps: MarvisTroubleshootDeps) -> None:
        """Fetch and display organization-level insights.

        Why:
            Wraps the insight-endpoint iteration in a broad try/except so a
            single failure does not abort the surrounding view.

        Args:
            org_id: Mist organisation id.
            deps: injected dependency container.
        """
        try:  # WHY: bound errors from insight collection so usage guide still renders.
            logging.warning("\n Attempting to retrieve organization-level insights...")  # WHY: progress message.
            insights_found = MarvisTroubleshootUtils._iter_insight_endpoints(org_id, deps)  # WHY: loop dispatch.
            if not insights_found:  # WHY: tell user when no endpoint produced data.
                logging.warning("\n  No organization-level insights currently available.")  # WHY: user message.
        except Exception as error:  # noqa: BLE001 - broad SDK exception surface.
            logging.warning("Could not retrieve organization insights: %s", error)  # WHY: log context.
            logging.warning("! Could not retrieve insights: %s", error)  # WHY: user-facing failure.

    @staticmethod
    def _iter_insight_endpoints(org_id: str, deps: MarvisTroubleshootDeps) -> bool:
        """Iterate registered insight endpoints and return True if any yielded data.

        Why:
            Loop dispatch pulled out so ``_fetch_org_insights`` stays small.

        Args:
            org_id: Mist organisation id.
            deps: injected dependency container.

        Returns:
            True if at least one endpoint yielded and rendered data.
        """
        insights_found = False  # WHY: track whether anything produced output.
        for endpoint_name, endpoint_func in MarvisTroubleshootUtils._insight_endpoints(org_id, deps):  # WHY: table.
            if MarvisTroubleshootUtils._try_insight_endpoint(endpoint_name, endpoint_func, deps):  # WHY: guarded.
                insights_found = True  # WHY: at least one endpoint yielded data.
        return insights_found  # WHY: caller renders "no insights" message on False.

    @staticmethod
    def _insight_endpoints(org_id: str, deps: MarvisTroubleshootDeps) -> tuple[tuple[str, Any], ...]:
        """Return the registered ``(name, callable)`` insight endpoint table.

        Why:
            Centralises endpoint registration so future insight sources can
            be added in one place.

        Args:
            org_id: Mist organisation id.
            deps: injected dependency container.

        Returns:
            Tuple of ``(display_name, zero_arg_callable)`` pairs.
        """
        return (  # WHY: single entry today. Tuple keeps future additions localised.
            (
                _SITES_SLE_ENDPOINT,
                lambda: deps.mistapi.api.v1.orgs.insights.getOrgSitesSle(deps.apisession, org_id),
            ),
        )

    @staticmethod
    def _try_insight_endpoint(endpoint_name: str, endpoint_func: Any, deps: MarvisTroubleshootDeps) -> bool:
        """Invoke one insight endpoint and process its response. Return True if data was rendered.

        Why:
            Per-endpoint try/except keeps the iteration loop resilient — a
            403/404 on one endpoint must not stop the others.

        Args:
            endpoint_name: display name of the endpoint.
            endpoint_func: zero-arg callable that returns an SDK response.
            deps: injected dependency container.

        Returns:
            True if data was rendered, False on empty/error responses.
        """
        try:  # WHY: individual endpoint errors must not abort the loop.
            logging.debug("Testing insight endpoint: %s", endpoint_name)  # WHY: trace which endpoint runs.
            response = endpoint_func()  # WHY: live API call.
            if not response.data:  # WHY: skip empty responses.
                return False  # WHY: nothing to render.
            return MarvisTroubleshootUtils._process_insight_response(endpoint_name, response.data, deps)  # WHY: render.
        except Exception as endpoint_error:  # noqa: BLE001 - logged via helper.
            MarvisTroubleshootUtils._log_endpoint_error(endpoint_name, endpoint_error)  # WHY: classify + log.
            return False  # WHY: treat as no data.

    @staticmethod
    def _process_insight_response(endpoint_name: str, data: Any, deps: MarvisTroubleshootDeps) -> bool:
        """Process and display one insight endpoint response.

        Why:
            Normalises list vs scalar payloads and dispatches into the
            appropriate formatter + persistence path.

        Args:
            endpoint_name: endpoint display name (drives CSV filename).
            data: raw response ``data`` payload.
            deps: injected dependency container.

        Returns:
            True if a CSV was written and a preview rendered, else False.
        """
        insights_data = data if isinstance(data, list) else [data]  # WHY: normalise to list.
        logging.debug("%s insights data length: %s", endpoint_name, len(insights_data))  # WHY: diagnostic.
        if not insights_data:  # WHY: nothing to display.
            return False  # WHY: no rows written.
        MarvisTroubleshootUtils._print_insight_preview(endpoint_name, insights_data)  # WHY: bounded preview.
        formatted_insights = MarvisTroubleshootUtils._format_insights(endpoint_name, data, insights_data, deps)  # WHY.
        filename = f"MarvisInsights_{endpoint_name.replace(' ', '_')}.csv"  # WHY: stable per-endpoint filename.
        MarvisTroubleshootUtils._persist_insight_csv(deps, formatted_insights, filename)  # WHY: write + log.
        return True  # WHY: signal that this endpoint produced data.

    @staticmethod
    def _print_insight_preview(endpoint_name: str, insights_data: list[Any]) -> None:
        """Print a bounded preview of insight descriptions plus overflow count.

        Why:
            Consolidates the preview + overflow marker into a single record
            so operators see the section header, bullets, and the ``... and
            N more`` line grouped together.

        Args:
            endpoint_name: endpoint display name used as section header.
            insights_data: full insights list (used for overflow computation).
        """
        lines = [f"\n  {endpoint_name}:"]  # WHY: section header.
        for insight in insights_data[:_MAX_PREVIEW_INSIGHTS]:  # WHY: bounded preview.
            description = MarvisTroubleshootUtils._describe_insight(insight)  # WHY: consistent renderer.
            lines.append(f"  !? {description}")  # WHY: bullet output.
        overflow = len(insights_data) - _MAX_PREVIEW_INSIGHTS  # WHY: how many rows are hidden.
        if overflow > 0:  # WHY: tell the user there is more in the CSV.
            lines.append(f"  ... and {overflow} more insights")  # WHY: overflow message.
        logging.warning("%s", "\n".join(lines))  # WHY: emit consolidated preview as one record.

    @staticmethod
    def _describe_insight(insight: Any) -> Any:
        """Return the best-effort description string for an insight payload.

        Why:
            The Marvis SDK returns heterogeneous shapes. This helper picks
            the most informative field available.

        Args:
            insight: raw insight (dict or scalar).

        Returns:
            The most descriptive field found (``description``/``type``/
            ``name``) or ``str(insight)`` as final fallback.
        """
        if not isinstance(insight, dict):  # WHY: non-dicts render as-is.
            return insight  # WHY: fallback to raw value.
        return insight.get("description", insight.get("type", insight.get("name", str(insight))))  # WHY: chain.

    @staticmethod
    def _format_insights(endpoint_name: str, data: Any, insights_data: list[Any], deps: MarvisTroubleshootDeps) -> Any:
        """Return CSV-ready rows using the SLE-specific formatter when applicable.

        Why:
            SLE data has a dedicated formatter. Every other endpoint gets a
            generic flatten + escape pass.

        Args:
            endpoint_name: endpoint display name (selects formatter branch).
            data: raw response ``data`` payload.
            insights_data: normalised list form of the payload.
            deps: injected dependency container.

        Returns:
            CSV-ready row iterable ready for the data exporter.
        """
        if "Sites SLE" in endpoint_name:  # WHY: SLE has a dedicated formatter.
            return deps.marvis_data_utils.format_for_csv(data, "sites")  # WHY: SLE-aware CSV rows.
        flattened = deps.data_processing_utils.flatten_nested_fields(insights_data)  # WHY: generic flatten.
        return deps.data_processing_utils.escape_multiline(flattened)  # WHY: escape for CSV safety.

    @staticmethod
    def _persist_insight_csv(deps: MarvisTroubleshootDeps, formatted_insights: Any, filename: str) -> None:
        """Persist a formatted insights payload with symmetric info/debug logs.

        Why:
            Mirrors ``_persist_csv``: pre-write info, post-write debug, and
            a user-visible confirmation line.

        Args:
            deps: injected dependency container.
            formatted_insights: CSV-ready rows.
            filename: output filename (already sanitised).
        """
        logging.info("Saving insights CSV: %s", filename)  # WHY: pre-write log.
        deps.data_exporter.write_with_format_selection(formatted_insights, filename)  # WHY: persist.
        row_count = len(formatted_insights) if formatted_insights else 0  # WHY: guard against None/empty.
        logging.debug("Insights CSV saved (rows=%s)", row_count)  # WHY: post-write log.
        logging.warning("  Full insights saved to %s", filename)  # WHY: user confirmation.

    @staticmethod
    def _log_endpoint_error(endpoint_name: str, exception: Exception) -> None:
        """Log endpoint-specific insight fetch errors.

        Why:
            Classifies known error signatures (404 disabled, 403 permission)
            so operators can distinguish "not enabled" from "misconfigured".

        Args:
            endpoint_name: endpoint display name for the log message.
            exception: caught exception.
        """
        error_message = str(exception)  # WHY: stringified once for the substring checks below.
        if "404" in error_message:  # WHY: endpoint not enabled for this org.
            logging.debug("Endpoint %s not available for this organization (404): %s", endpoint_name, exception)
        elif "403" in error_message:  # WHY: permission issue.
            logging.debug("Access denied to %s (403): %s", endpoint_name, exception)
        else:  # WHY: anything else — keep as generic debug.
            logging.debug("Could not fetch %s: %s", endpoint_name, exception)

    @staticmethod
    def _display_usage_guide() -> None:
        """Display Marvis usage guidance.

        Why:
            Emits the entire static guide as one consolidated log record so
            operators see a single atomic block rather than 14 fragmented
            print lines.
        """
        logging.warning("%s", "\n".join(_USAGE_GUIDE_LINES))  # WHY: single consolidated record.

    @staticmethod
    def _handle_insights_error(exception: Exception) -> None:
        """Handle and display insights retrieval errors.

        Why:
            Consolidates the error banner + guidance bullets into a single
            ``logging.error`` record so downstream log aggregation groups
            them as one event.

        Args:
            exception: raised exception surfaced by ``view_insights``.
        """
        logging.error(  # WHY: single consolidated error record with banner + guidance.
            "Failed to get Marvis insights: %s\n"
            "! Failed to get Marvis insights: %s\n"
            " This may indicate:\n"
            "   - Marvis (VNA) is not enabled for your organization\n"
            "   - Insufficient permissions to view organization details\n"
            "   - API connectivity issues",
            exception,
            exception,
        )
