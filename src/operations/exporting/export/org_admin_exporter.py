"""OrgAdminExporter -- org admin/token/SSO/license/usage exports.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 20).
Handles API tokens, admins, SSO, license, and usage exports.  All methods are
static -- no state is kept on the class.  Callers continue to reach it through
the ``MistHelper.OrgAdminExporter`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

import logging  # WHY: structured trace for export lifecycle events.
from typing import Any  # WHY: raw license rows are duck-typed dicts from mistapi.

import mistapi  # WHY: direct SDK access for org admin/license endpoints.

from src.foundation.models.data.data_processing_utils import (
    DataProcessingUtils,
)  # WHY: 1015 T-10 canonical import (eliminates mh.DataProcessingUtils).
from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,  # WHY: resolve source dependencies without importing the root module.
)

logger = logging.getLogger(__name__)  # Name the logger for this module so a reader can filter by source.


class OrgAdminExporter:
    """Organization Admin and License Exporter.

    Handles API tokens, admins, SSO, license, and usage exports.
    Extracted from OrgExportUtils.
    """

    @staticmethod
    def api_tokens() -> None:
        """Export organization API tokens to OrgApiTokens.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Starting export of organization api tokens...")  # Log start.
        mh.APIDataFetcher(  # Fetch and write tokens.
            title="Organization Api Tokens:",
            api_call=mistapi.api.v1.orgs.apitokens.listOrgApiTokens,
            filename="OrgApiTokens.csv",
            sort_key="name",
        ).execute()

    @staticmethod
    def admins() -> None:
        """Export organization admins to OrgAdmins.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Starting export of organization admins...")  # Log start.
        mh.APIDataFetcher(  # Fetch and write admins.
            title="Organization Admins:",
            api_call=mistapi.api.v1.orgs.admins.listOrgAdmins,
            filename="OrgAdmins.csv",
            sort_key="name",
        ).execute()

    @staticmethod
    def sso() -> None:
        """Export organization SSO configuration to OrgSso.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        mh.OrgExportUtils.export_data(  # Delegate to shared org exporter scaffolding.
            api_call=mistapi.api.v1.orgs.ssos.listOrgSsos, data_type="sso", sort_key="name"
        )

    @staticmethod
    def _fetch_license_payload(current_org_id: str) -> list[Any]:
        """Fetch license rows via the wrapper, or fall back to a raw GET when the wrapper is absent."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        license_api = mistapi.api.v1.orgs.licenses  # Locate the SDK namespace before selecting an endpoint.
        logger.info("Requesting organization licenses for org %s", current_org_id)  # Identify the request target.
        if hasattr(license_api, "listOrgLicenses"):  # Check the namespace before accessing its optional member.
            if license_api.listOrgLicenses is not None:  # Preserve the direct request when the wrapper is null.
                response = license_api.listOrgLicenses(mh.apisession, current_org_id, limit=1000)  # Use the wrapper.
                OrgAdminExporter._validate_license_response(response, current_org_id)  # Validate before pagination.
                return mistapi.get_all(response=response, mist_session=mh.apisession) or []  # Preserve SDK pagination.
        logger.debug("listOrgLicenses wrapper not present in mistapi library; performing direct GET /licenses")
        raw_url = f"/api/v1/orgs/{current_org_id}/licenses"  # Compose the existing SDK session path.
        if mh.apisession is None:  # Direct GET requires an initialized session.
            raise ValueError("API session not initialized")
        response = mh.apisession.mist_get(raw_url)  # Preserve the SDK session request.
        OrgAdminExporter._validate_license_response(response, current_org_id)  # Validate before body access.
        return response.data or []  # Preserve empty successful responses.

    @staticmethod
    def _validate_license_response(response: Any, current_org_id: str) -> None:
        """Require a successful initial response before consuming license data."""
        status = getattr(response, "status_code", None)  # A missing status cannot prove request success.
        if not isinstance(status, int) or isinstance(status, bool):  # Boolean values are not HTTP status codes.
            raise RuntimeError(f"License request has no valid HTTP status for org {current_org_id}")
        if not 200 <= status < 300:  # Reject redirects, request failures, and invalid integer statuses.
            raise RuntimeError(f"License request returned HTTP {status} for org {current_org_id}")
        logger.debug("License request returned HTTP %s for org %s", status, current_org_id)  # Confirm initial status.

    @staticmethod
    def _fetch_license_records(current_org_id: str) -> list[Any]:
        """Fetch license rows via wrapper or raw GET fallback, normalized to a list."""
        raw_items = OrgAdminExporter._fetch_license_payload(current_org_id)  # Resolve via wrapper/raw dispatch.
        if not isinstance(raw_items, list):  # Normalize unexpected shapes to a list.
            logger.debug("License endpoint returned non-list payload; normalizing to list")  # Trace normalization.
            raw_items = [raw_items]  # Wrap single item.
        return raw_items  # Caller decides empty/persist.

    @staticmethod
    def licenses() -> None:
        """Export organization licenses to OrgLicenses.csv. Raise RuntimeError when the request or the writer fails."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Starting export of organization licenses (canonical endpoint)...")  # Log start.
        current_org_id = mh.ConfigUtils.get_cached_or_prompted_org_id()  # Resolve the org.
        try:
            raw_items = OrgAdminExporter._fetch_license_records(current_org_id)  # Fetch rows via wrapper/fallback.
            if not raw_items:  # No records.
                logger.info("No license records returned from canonical endpoint. No export was written.")
                return  # The shared writer rejects empty input.
            OrgAdminExporter._write_license_records(raw_items)  # Report the actual writer outcome.
        except Exception as error:  # Preserve existing exception propagation without another write.
            logger.error("Failed to export licenses for org %s: %s", current_org_id, error)  # Identify the failure.
            raise  # Keep the original error for the caller.

    @staticmethod
    def _write_license_records(raw_items: list[Any]) -> None:
        """Process valid license rows and raise when the writer rejects them."""
        mh = SourceDependencyResolver  # Resolve the configured output writer.
        filename = "OrgLicenses.csv"  # Preserve the existing output name.
        logger.info("Processing %s license records", len(raw_items))  # Trace the data transform.
        processed = DataProcessingUtils.flatten_nested_fields(raw_items)  # Preserve nested field processing.
        processed = DataProcessingUtils.escape_multiline(processed)  # Preserve multiline escaping.
        logger.debug("Processed %s license records", len(processed))  # Record the transform result.
        logger.info("Writing %s license records to %s", len(processed), filename)  # Trace the output attempt.
        written = mh.DataExporter.write_with_format_selection(  # Preserve endpoint metadata for every backend.
            processed, filename, api_function_name="listOrgLicenses"
        )
        logger.debug("License writer result for %s: %s", filename, written)  # Record the actual writer result.
        if not written:  # A rejected write must fail the operation, so the menu harness reports it.
            logger.error(
                "Failed to export %d license records to %s: the writer rejected the export.", len(processed), filename
            )  # Log the count and file, as the merged site and webhook exporters do.
            raise RuntimeError(f"The writer rejected {filename}.")  # Raise so the menu runner reports failure.
        logger.info("Exported %s license records to %s.", len(processed), filename)  # Report only accepted output.

    @staticmethod
    def usage() -> None:
        """Export organization usage data to OrgUsage.csv."""
        mh = SourceDependencyResolver  # WHY: resolve source dependencies without importing the root module.
        logger.info("Starting export of organization license usage...")  # Log start.
        exported = mh.APIDataFetcher(  # Fetch and write usage.
            title="Organization License Usage:",
            api_call=mistapi.api.v1.orgs.licenses.getOrgLicensesBySite,
            filename="OrgUsage",
            sort_key="site_id",
        ).execute()
        if exported is False:  # WHY: only an explicit failure skips the completion report.
            return  # WHY: preserve the existing None return contract for this exporter.
        logger.info(" License usage data exported to OrgUsage")  # Log completion.
        # WHY: user-visible completion banner (replaces prior print()).
        logger.warning(" License usage data exported to OrgUsage")
