"""OrgTemplateExporter -- org gateway/network/RF/site/AP/switch template exports.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 22).
Handles network, RF, AP, switch, site, and gateway template exports.  All
methods are static -- no state is kept on the class.  Callers continue to
reach it through the ``MistHelper.OrgTemplateExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach live helper globals without circular load.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw template rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for org template endpoints.


class OrgTemplateExporter:
    """Organization Template Exporter.

    Handles network, RF, AP, switch, site, and gateway template exports.
    Extracted from OrgExportUtils.
    """

    @staticmethod
    def all_templates() -> None:
        """Export all organization templates (gateway, network, RF, site, AP) to CSV files."""
        logging.info("Starting export of organization templates...")  # Log start.
        for title, api_call, filename, error_label in OrgTemplateExporter._template_export_specs():  # Each type.
            OrgTemplateExporter._export_one_template(title, api_call, filename, error_label)  # Non-fatal per type.
        logging.info(" Organization templates export completed")  # Log completion.

    @staticmethod
    def _template_export_specs() -> list[tuple[str, Any, str, str]]:
        """Return per-template-type export specs, resolving mistapi endpoints at call time.

        Endpoints must be resolved when this runs, not at class-def time (mistapi populated later).
        """
        v1 = mistapi.api.v1.orgs  # Shorten endpoint base for compact spec list.
        return [
            (
                "Gateway Templates:",
                v1.gatewaytemplates.listOrgGatewayTemplates,
                "OrgGatewayTemplates.csv",
                "gateway templates",
            ),
            (
                "Network Templates:",
                v1.networktemplates.listOrgNetworkTemplates,
                "OrgNetworkTemplates.csv",
                "network templates",
            ),
            ("RF Templates:", v1.rftemplates.listOrgRfTemplates, "OrgRfTemplates.csv", "RF templates"),
            ("Site Templates:", v1.sitetemplates.listOrgSiteTemplates, "OrgSiteTemplates.csv", "site templates"),
            ("AP Templates:", v1.aptemplates.listOrgAptemplates, "OrgApTemplates.csv", "AP templates"),
        ]

    @staticmethod
    def _export_one_template(title: str, api_call: Any, filename: str, error_label: str) -> None:
        """Fetch one template type to its CSV; log (do not raise) on failure so other types still export."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APIDataFetcher helper.
        try:
            mh.APIDataFetcher(  # Fetch this template type and write it to CSV.
                title=title,
                api_call=api_call,
                filename=filename,
                sort_key="name",
                limit=1000,
            ).execute()
        except Exception as e:  # This template type failed -- keep going with the rest.
            logging.error("Failed to export %s: %s", error_label, e)  # Log the per-type failure.

    @staticmethod
    def network_templates() -> None:
        """Export network templates to OrgNetworkTemplates.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of OrgExportUtils helper.
        mh.OrgExportUtils.export_data(
            api_call=mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates,
            data_type="network templates",
            sort_key="name",
        )

    @staticmethod
    def rf_templates() -> None:
        """Export RF templates to OrgRfTemplates.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of OrgExportUtils helper.
        mh.OrgExportUtils.export_data(
            api_call=mistapi.api.v1.orgs.rftemplates.listOrgRfTemplates, data_type="rf templates", sort_key="name"
        )

    @staticmethod
    def _persist_ap_template_profiles(ap_profiles: list[Any], filename: str) -> None:
        """Flatten + write AP template profiles to CSV; emit operator + log summary."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter + DataProcessingUtils helpers.
        if not ap_profiles:  # No AP templates in this org.
            print("! 0 AP templates exported to OrgApTemplates.csv (no templates found)")  # Inform user.
            logging.info(
                "No AP templates returned from canonical endpoint; writing empty OrgApTemplates.csv"
            )  # Log empty.
            mh.DataExporter.write_with_format_selection([], filename)  # Write empty file for consistency.
            return
        processed = mh.DataProcessingUtils.flatten_nested_fields(ap_profiles)  # Flatten nested JSON.
        processed = mh.DataProcessingUtils.escape_multiline(processed)  # Escape multiline.
        mh.DataExporter.write_with_format_selection(processed, filename)  # Persist.
        print(f"! {len(processed)} AP templates exported to {filename}")  # Tell user.
        logging.info("Exported %s AP templates to %s.", len(processed), filename)  # Log count.

    @staticmethod
    def ap_templates() -> None:
        """Export AP templates (canonical deviceprofiles type=ap) to OrgApTemplates.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + DataExporter + apisession.
        print("Export Organization AP Templates:")  # Header.
        logging.info("Starting export of organization AP templates (canonical deviceprofiles type=ap)...")  # Log start.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve org.
        filename = "OrgApTemplates.csv"  # Output filename.
        try:
            response = mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles(
                mh.apisession, org_id, type="ap", limit=1000
            )  # Filter to AP profiles.
            ap_profiles = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page all.
            OrgTemplateExporter._persist_ap_template_profiles(ap_profiles, filename)  # Persist + log.
        except Exception as e:  # AP export failed.
            logging.error("Failed to export AP templates: %s", e)  # Log AP error.
            try:
                mh.DataExporter.write_with_format_selection([], filename)  # Best-effort empty file.
            except Exception:  # nosec B110
                pass  # Best-effort cleanup.
            raise  # Re-raise to caller.

    @staticmethod
    def _persist_switch_template_csv(switch_profiles: list[Any], filename: str) -> None:
        """Flatten + escape + write switch-template payload, then log/emit a success line."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter + DataProcessingUtils helpers.
        if not switch_profiles:  # No templates returned from the API.
            print("! 0 switch templates exported to OrgSwitchTemplates.csv (no templates found)")  # User notice.
            logging.info(  # Trace empty-result branch.
                "No switch templates returned from canonical endpoint; writing empty OrgSwitchTemplates.csv"
            )
            mh.DataExporter.write_with_format_selection([], filename)
            return  # Done; empty CSV written.
        processed = mh.DataProcessingUtils.flatten_nested_fields(switch_profiles)  # Flatten nested template fields.
        processed = mh.DataProcessingUtils.escape_multiline(processed)  # CSV-safe.
        mh.DataExporter.write_with_format_selection(processed, filename)  # Persist.
        print(f"! {len(processed)} switch templates exported to {filename}")  # User notice.
        logging.info("Exported %s switch templates to %s.", len(processed), filename)  # Trace count.

    @staticmethod
    def switch_templates() -> None:
        """Export switch templates to OrgSwitchTemplates.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of ConfigUtils + DataExporter + apisession.
        print("Export Organization Switch Templates:")  # Header.
        logging.info("Starting export of organization switch templates (canonical networktemplates)...")  # Log start.
        org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        filename = "OrgSwitchTemplates.csv"  # Build the CSV name.
        try:
            response = mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates(mh.apisession, org_id, limit=1000)
            switch_profiles = mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page all.
            OrgTemplateExporter._persist_switch_template_csv(switch_profiles, filename)  # Persist + log.
        except Exception as e:  # Export failed.
            logging.error("Failed to export switch templates: %s", e)  # Log error.
            try:
                mh.DataExporter.write_with_format_selection([], filename)
            except Exception:  # nosec B110
                pass  # Best-effort cleanup.
            raise  # Re-raise to caller.
