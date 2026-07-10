"""OrgConfigExporter -- organization config exporters (PSK/webhook/WLAN/MX Edge/MSP).

Extracted from MistHelper.py during initiative 1013 (Cat B, position 31).
Backs menu options 44 (PSKs), 45 (webhooks), 46 (WLANs), 50 (MX Edges), plus
the interactive MSP-orgs export. Direct imports cover stdlib + installed
packages (mistapi). Live-global reads (``apisession``, ``msp_privileges``,
``OrgExportUtils``, ``InputUtils``, ``DataExporter``, ``DataProcessingUtils``)
are resolved via lazy ``mh = importlib.import_module("MistHelper")`` inside
each helper. Callers continue to reach the class through the
``MistHelper.OrgConfigExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: PEP 604 unions for return types.

import importlib  # WHY: lazy MistHelper import avoids circular load at module init.
import logging  # WHY: structured trace for MSP export lifecycle events.
from typing import Any  # WHY: mistapi response payloads are duck-typed here.

import mistapi  # WHY: direct calls to orgs.psks/webhooks/wlans/mxedges list endpoints.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).


class OrgConfigExporter:
    """Organization Configuration Exporter.

    Handles PSK, webhook, WLAN, MX Edge, and MSP config exports.
    Extracted from OrgExportUtils.
    """

    @staticmethod
    def psks() -> None:  # Export PSKs.
        """Export organization PSKs to OrgPsks.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of OrgExportUtils facade.
        mh.OrgExportUtils.export_data(api_call=mistapi.api.v1.orgs.psks.listOrgPsks, data_type="psks", sort_key="name")

    @staticmethod
    def webhooks() -> None:  # Export webhooks.
        """Export organization webhooks to OrgWebhooks.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of OrgExportUtils facade.
        mh.OrgExportUtils.export_data(
            api_call=mistapi.api.v1.orgs.webhooks.listOrgWebhooks, data_type="webhooks", sort_key="name"
        )

    @staticmethod
    def wlans() -> None:  # Export WLANs.
        """Export organization WLANs to OrgWlans.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of OrgExportUtils facade.
        mh.OrgExportUtils.export_data(
            api_call=mistapi.api.v1.orgs.wlans.listOrgWlans, data_type="wlans", sort_key="ssid"
        )

    @staticmethod
    def mx_edges() -> None:  # Export Mist Edges (MSP flow).
        """Export MX Edge data to OrgMxEdges.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of OrgExportUtils facade.
        mh.OrgExportUtils.export_data(
            api_call=mistapi.api.v1.orgs.mxedges.listOrgMxEdges, data_type="mx edges", sort_key="name"
        )

    @staticmethod
    def msp() -> None:
        """Export MSP data -- lists organizations under the selected MSP to MspOrganizations.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of msp_privileges cache.
        if not mh.msp_privileges:  # No MSP-level access.
            OrgConfigExporter._show_no_msp_access_guidance()  # Print the guidance banner.
            return  # Abort -- nothing to query.
        selected_msp = OrgConfigExporter._select_msp_to_query()  # Pick or prompt for an MSP.
        if not selected_msp:  # User cancelled or input invalid.
            return  # Abort -- nothing selected.
        OrgConfigExporter._fetch_and_export_msp_orgs(selected_msp)  # Fetch + flatten + CSV write.

    @staticmethod
    def _show_no_msp_access_guidance() -> None:
        """Print the 'MSP access not available' guidance banner with login + token tips."""
        logging.warning("MSP data requires MSP-level privileges (not detected)")  # Log why we can't query.
        print("")  # Spacer.
        print("=" * 60)  # Top border.
        print("  MSP ACCESS NOT AVAILABLE")  # Title.
        print("=" * 60)  # Bottom border.
        print("")  # Spacer.
        print("  MSP-level API access requires one of the following:")  # Intro.
        print("")  # Spacer.
        print("  1. Interactive login with MSP admin credentials:")  # Option 1.
        print("     python MistHelper.py --login")  # The login command.
        print("")  # Spacer.
        print("  2. A personal API token from an MSP Super User")  # Option 2.
        print("     (The token inherits the user's MSP privileges)")  # Clarify token semantics.
        print("")  # Spacer.
        print("  Note: Organization-scoped API tokens CANNOT access MSP APIs.")  # Common pitfall.
        print("  The token must be from a user who has MSP-level access.")  # Restate.
        print("")  # Spacer.
        print("  MSP API Endpoints available with proper access:")  # Endpoint list intro.
        print("    - GET /api/v1/msps/{msp_id}/orgs (list organizations)")  # Org listing endpoint.
        print("    - GET /api/v1/msps/{msp_id}/licenses (MSP licenses)")  # License endpoint.
        print("    - GET /api/v1/msps/{msp_id}/stats/orgs (org statistics)")  # Org stats endpoint.
        print("    - GET /api/v1/msps/{msp_id}/inventory/{mac} (cross-org device lookup)")  # Inventory.
        print("")  # Spacer.

    @staticmethod
    def _select_msp_to_query() -> dict | None:  # type: ignore[type-arg]
        """Auto-pick the single MSP or prompt the user when several are available."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of msp_privileges + InputUtils.
        print("")  # Spacer.
        print("=" * 60)  # Divider.
        print("  MSP ORGANIZATION EXPORT")  # Section title.
        print("=" * 60)  # Divider.
        print("")  # Spacer.
        if len(mh.msp_privileges) == 1:  # Exactly one MSP.
            selected = mh.msp_privileges[0]  # Auto-select it.
            print(f"  Using MSP: {selected['msp_name']}")  # Tell the user.
            return selected  # type: ignore[no-any-return]  # Return the single MSP.
        print("  Available MSPs:")  # List MSPs.
        for idx, msp in enumerate(mh.msp_privileges, start=1):  # Enumerate MSPs.
            print(f"    {idx}. {msp['msp_name']} (role: {msp['role']})")  # Print each option.
        print("")  # Spacer.
        try:
            choice = mh.InputUtils.safe_input("  Select MSP (number): ", context="msp_export").strip()
            choice_idx = int(choice) - 1  # Parse the index.
        except (ValueError, SystemExit):  # Bad input.
            print("X Invalid input")  # Tell the user.
            return None  # Abort.
        if not 0 <= choice_idx < len(mh.msp_privileges):  # Out of range.
            print("X Invalid selection")  # Tell the user.
            return None  # Abort.
        return mh.msp_privileges[choice_idx]  # type: ignore[no-any-return]  # Return chosen MSP.

    @staticmethod
    def _fetch_and_export_msp_orgs(selected_msp: dict) -> None:  # type: ignore[type-arg]
        """Fetch orgs under ``selected_msp`` and write MspOrganizations.csv with the MSP tags."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of live apisession.
        msp_id = selected_msp["msp_id"]  # MSP id.
        msp_name = selected_msp["msp_name"]  # MSP name.
        print(f"  Fetching organizations for MSP: {msp_name}...")  # Tell the user.
        logging.info("Fetching MSP organizations for %s (ID: %s)", msp_name, msp_id)  # Log fetch.
        if mh.apisession is None:  # No session.
            print("X No active API session")  # Tell the user.
            logging.error("Cannot fetch MSP orgs - apisession is None")  # Log it.
            return  # Abort.
        try:
            import mistapi.api.v1.msps.orgs as msp_orgs_api  # noqa: PLC0415  # Import MSP orgs API.

            response = msp_orgs_api.listMspOrgs(mh.apisession, msp_id)  # Call API.
            orgs_data = OrgConfigExporter._extract_msp_orgs_payload(response)  # Validate.
            if orgs_data is not None:  # API call succeeded.
                OrgConfigExporter._write_msp_orgs_csv(orgs_data, msp_id, msp_name)  # Persist.
        except Exception as e:  # Fetch failed.
            print(f"X Error fetching MSP organizations: {e}")  # Tell the user.
            logging.error("Failed to fetch MSP organizations: %s", e)  # Log it.

    @staticmethod
    def _write_msp_orgs_csv(orgs_data: list, msp_id: str, msp_name: str) -> None:  # type: ignore[type-arg]
        """Process ``orgs_data``, write MspOrganizations.csv, and print the summary."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of DataExporter facade.
        if not orgs_data:  # No orgs.
            print("  No organizations found under this MSP")  # Tell the user.
            logging.info("MSP has no organizations")  # Log it.
            mh.DataExporter.write_with_format_selection([], "MspOrganizations.csv")  # Empty write.
            return  # Done.
        processed = OrgConfigExporter._process_msp_orgs(orgs_data, msp_id, msp_name)  # Flatten + tag.
        mh.DataExporter.write_with_format_selection(processed, "MspOrganizations.csv")  # Persist.
        print(f"  + {len(processed)} organizations exported to MspOrganizations.csv")  # Tell.
        logging.info("Exported %s MSP organizations to MspOrganizations.csv", len(processed))  # Log.
        OrgConfigExporter._print_msp_orgs_summary(msp_name, orgs_data)  # Show first 10.

    @staticmethod
    def _extract_msp_orgs_payload(response: Any) -> list | None:  # type: ignore[type-arg]
        """Validate the MSP-orgs API response and return a normalized list (or None on failure)."""
        if not response or not hasattr(response, "data"):  # No data.
            print("X Failed to retrieve MSP organizations")  # Tell the user.
            logging.error("listMspOrgs returned no data")  # Log it.
            return None  # Abort.
        orgs_data = response.data  # Read the payload.
        if not isinstance(orgs_data, list):  # Normalize to a list.
            return [orgs_data] if orgs_data else []  # Wrap single item.
        return orgs_data  # type: ignore[no-any-return]  # Already a list.

    @staticmethod
    def _process_msp_orgs(orgs_data: list, msp_id: str, msp_name: str) -> list:  # type: ignore[type-arg]
        """Flatten + escape + tag each org dict with its parent ``msp_id`` and ``msp_name``."""
        processed = DataProcessingUtils.flatten_nested_fields(orgs_data)  # Flatten nested fields.
        processed = DataProcessingUtils.escape_multiline(processed)  # Escape multiline text.
        for record in processed:  # Tag each org.
            record["msp_id"] = msp_id  # Add MSP id.
            record["msp_name"] = msp_name  # Add MSP name.
        return processed  # type: ignore[no-any-return]  # Return enriched list.

    @staticmethod
    def _print_msp_orgs_summary(msp_name: str, orgs_data: list) -> None:  # type: ignore[type-arg]
        """Print the first 10 org names + a trailing 'and N more' note when applicable."""
        print("")  # Spacer.
        print(f"  Organizations under {msp_name}:")  # Header.
        for org in orgs_data[:10]:  # Show first 10.
            org_name = org.get("name", "Unknown")  # Org name.
            org_id = org.get("id", "N/A")  # Org id.
            print(f"    - {org_name} ({org_id[:8]}...)")  # Print the org.
        if len(orgs_data) > 10:  # More than shown.
            print(f"    ... and {len(orgs_data) - 10} more")  # Note the remainder.
        print("")  # Spacer.
