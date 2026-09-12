"""OrgAdminExporter -- org admin/token/SSO/license/usage exports.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 20).
Handles API tokens, admins, SSO, license, and usage exports.  All methods are
static -- no state is kept on the class.  Callers continue to reach it through
the ``MistHelper.OrgAdminExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import importlib  # WHY: lazy MistHelper import to reach live helper globals without circular load.
import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw license rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for org admin/license endpoints.

from src.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).


class OrgAdminExporter:
    """Organization Admin and License Exporter.

    Handles API tokens, admins, SSO, license, and usage exports.
    Extracted from OrgExportUtils.
    """

    @staticmethod
    def api_tokens() -> None:
        """Export organization API tokens to OrgApiTokens.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APIDataFetcher helper.
        logging.info("Starting export of organization api tokens...")  # Log start.
        mh.APIDataFetcher(  # Fetch and write tokens.
            title="Organization Api Tokens:",
            api_call=mistapi.api.v1.orgs.apitokens.listOrgApiTokens,
            filename="OrgApiTokens.csv",
            sort_key="name",
        ).execute()

    @staticmethod
    def admins() -> None:
        """Export organization admins to OrgAdmins.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APIDataFetcher helper.
        logging.info("Starting export of organization admins...")  # Log start.
        mh.APIDataFetcher(  # Fetch and write admins.
            title="Organization Admins:",
            api_call=mistapi.api.v1.orgs.admins.listOrgAdmins,
            filename="OrgAdmins.csv",
            sort_key="name",
        ).execute()

    @staticmethod
    def sso() -> None:
        """Export organization SSO configuration to OrgSso.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of OrgExportUtils helper.
        mh.OrgExportUtils.export_data(  # Delegate to shared org exporter scaffolding.
            api_call=mistapi.api.v1.orgs.ssos.listOrgSsos, data_type="sso", sort_key="name"
        )

    @staticmethod
    def _fetch_license_payload(current_org_id: str) -> list[Any]:
        """Fetch license rows via the wrapper, or fall back to a raw GET when the wrapper is absent."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of apisession module global.
        list_func = getattr(mistapi.api.v1.orgs.licenses, "listOrgLicenses", None)  # Locate the wrapper if shipped.
        if list_func is None:  # Wrapper missing -> fall back to raw GET.
            logging.debug("listOrgLicenses wrapper not present in mistapi library; performing direct GET /licenses")
            raw_url = f"/api/v1/orgs/{current_org_id}/licenses"  # Compose raw API path.
            if mh.apisession is None:  # Direct GET requires an initialized session.
                raise ValueError("API session not initialized")
            response = mh.apisession.mist_get(raw_url)  # Raw GET fallback.
            return getattr(response, "data", response) or []  # Unwrap .data or response, default empty.
        response = list_func(mh.apisession, current_org_id, limit=1000)  # Use wrapper path.
        return mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Page-all wrapper result.

    @staticmethod
    def _fetch_license_records(current_org_id: str) -> list[Any]:
        """Fetch license rows via wrapper or raw GET fallback, normalized to a list."""
        raw_items = OrgAdminExporter._fetch_license_payload(current_org_id)  # Resolve via wrapper/raw dispatch.
        if not isinstance(raw_items, list):  # Normalize unexpected shapes to a list.
            logging.debug("License endpoint returned non-list payload; normalizing to list")  # Trace normalization.
            raw_items = [raw_items]  # Wrap single item.
        return raw_items  # Caller decides empty/persist.

    @staticmethod
    def licenses() -> None:
        """Export organization licenses to OrgLicenses.csv."""
        mh = importlib.import_module(
            "MistHelper"
        )  # WHY: lazy fetch of ConfigUtils/DataProcessingUtils/DataExporter helpers.
        logging.info("Starting export of organization licenses (canonical endpoint)...")  # Log start.
        filename = "OrgLicenses.csv"  # Build the CSV name.
        current_org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        try:
            raw_items = OrgAdminExporter._fetch_license_records(current_org_id)  # Fetch rows via wrapper/fallback.
            if not raw_items:  # No records.
                logging.info("No license records returned from canonical endpoint; writing empty OrgLicenses.csv")
                mh.DataExporter.write_with_format_selection([], filename, api_function_name="listOrgLicenses")
                return  # Abort.
            processed = DataProcessingUtils.flatten_nested_fields(raw_items)  # Flatten nested fields.
            processed = DataProcessingUtils.escape_multiline(processed)  # CSV-safe.
            mh.DataExporter.write_with_format_selection(processed, filename, api_function_name="listOrgLicenses")
            logging.info("Exported %s license records to %s.", len(processed), filename)  # Log export count.
        except Exception as e:  # Export failed.
            logging.error("Failed to export licenses: %s", e)  # Log the error.
            try:
                mh.DataExporter.write_with_format_selection([], filename)  # Best-effort empty write.
            except Exception:  # nosec B110
                pass  # Best-effort cleanup.
            raise  # Re-raise to caller.

    @staticmethod
    def usage() -> None:
        """Export organization usage data to OrgUsage.csv."""
        mh = importlib.import_module("MistHelper")  # WHY: lazy fetch of APIDataFetcher helper.
        logging.info("Starting export of organization license usage...")  # Log start.
        mh.APIDataFetcher(  # Fetch and write usage.
            title="Organization License Usage:",
            api_call=mistapi.api.v1.orgs.licenses.getOrgLicensesBySite,
            filename="OrgUsage",
            sort_key="site_id",
        ).execute()
        logging.info(" License usage data exported to OrgUsage")  # Log completion.
        # WHY: user-visible completion banner (replaces prior print()).
        logging.warning(" License usage data exported to OrgUsage")
