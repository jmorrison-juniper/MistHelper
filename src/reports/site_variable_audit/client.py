"""Read Mist data for the site variable audit."""

from __future__ import annotations  # Keep annotations lightweight at import time.

import logging  # Log each Mist read for operator traceability.
from collections.abc import Callable, Mapping  # Type injectable Mist API operations.
from typing import Any  # Accept SDK response objects and fixture doubles.

import mistapi  # Use the installed Mist SDK for cloud reads.

logger = logging.getLogger(__name__)  # Keep log records tied to this module.
MistOperation = Callable[..., Any]  # Type one injected Mist SDK operation.


class SiteVariableAuditReadError(RuntimeError):
    """Raised when a required Mist read fails."""


class SiteVariableAuditClient:
    """Read organization-wide inputs for the site variable audit."""

    OPERATION_KEYS = (  # Name each SDK operation the audit needs.
        "listOrgSites",
        "listOrgGatewayTemplates",
        "listOrgNetworkTemplates",
        "listOrgTemplates",
        "listOrgWlans",
        "listOrgDeviceProfiles",
        "searchOrgVars",
    )

    def __init__(
        self,
        apisession: Any,
        org_id: str,
        operations: Mapping[str, MistOperation] | None = None,
        mistapi_module: Any = mistapi,
    ) -> None:
        """Create a client with optional operation injection for tests."""
        self._apisession = apisession  # Store the active Mist API session.
        self._org_id = org_id  # Store the selected organization ID.
        self._mistapi = mistapi_module  # Store the SDK module or a fixture double.
        self._operations = dict(operations or self._default_operations(mistapi_module))  # Store operation callables.

    def fetch(self) -> dict[str, list[dict[str, Any]]]:
        """Fetch each required organization dataset one time."""
        logger.info("Fetching site variable audit input datasets")  # Log before the batch of reads.
        records = {  # Read each endpoint once and keep normalized keys for the model.
            "sites": self._read_all("listOrgSites"),
            "gateway_templates": self._read_all("listOrgGatewayTemplates"),
            "network_templates": self._read_all("listOrgNetworkTemplates"),
            "templates": self._read_all("listOrgTemplates"),
            "wlans": self._read_all("listOrgWlans"),
            "device_profiles": self._read_all("listOrgDeviceProfiles", type="gateway"),
            "site_variables": self._read_all("searchOrgVars", var="*"),
        }
        logger.debug("Fetched %s site variable audit datasets", len(records))  # Log dataset count.
        return records  # Return all raw records to the model layer.

    def _read_all(self, operation_name: str, **query: Any) -> list[dict[str, Any]]:
        """Read one SDK operation and return all paginated rows."""
        logger.info("Reading Mist operation %s", operation_name)  # Log before the SDK call.
        operation = self._operations[operation_name]  # Resolve the injected or default SDK operation.
        try:  # Convert SDK errors into one user-facing audit error type.
            response = operation(self._apisession, self._org_id, **query)  # Call the installed SDK operation.
            rows = self._mistapi.get_all(response=response, mist_session=self._apisession) or []  # Exhaust pagination.
        except Exception as error:  # Convert any SDK or pagination fault into a clear read error.
            logger.exception("Mist operation %s failed", operation_name)  # Log the full exception for triage.
            message = f"Site variable audit could not read {operation_name}."  # Build a clear operator message.
            raise SiteVariableAuditReadError(message) from error  # Stop before any success-shaped output.
        normalized = list(rows)  # Normalize iterables returned by SDK pagination.
        logger.debug("Read %s rows from Mist operation %s", len(normalized), operation_name)  # Log row count.
        return normalized  # Return records for this endpoint.

    @staticmethod
    def _default_operations(mistapi_module: Any) -> dict[str, MistOperation]:
        """Return the installed SDK callables for all required operation IDs."""
        return {  # Resolve installed SDK callables by OpenAPI operation ID.
            "listOrgSites": mistapi_module.api.v1.orgs.sites.listOrgSites,
            "listOrgGatewayTemplates": mistapi_module.api.v1.orgs.gatewaytemplates.listOrgGatewayTemplates,
            "listOrgNetworkTemplates": mistapi_module.api.v1.orgs.networktemplates.listOrgNetworkTemplates,
            "listOrgTemplates": mistapi_module.api.v1.orgs.templates.listOrgTemplates,
            "listOrgWlans": mistapi_module.api.v1.orgs.wlans.listOrgWlans,
            "listOrgDeviceProfiles": mistapi_module.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles,
            "searchOrgVars": mistapi_module.api.v1.orgs.vars.searchOrgVars,
        }
