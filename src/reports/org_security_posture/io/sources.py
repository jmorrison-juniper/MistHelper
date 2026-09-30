"""Mist API source collection for the organization security posture report."""

from __future__ import annotations

import logging
from typing import Any

import mistapi

from src.reports.org_security_posture.models import OrganizationSecuritySourceData

logger = logging.getLogger(__name__)


class OrgSecurityPostureSourceClient:
    """Collect each required organization source once."""

    REQUIRED_OPERATION_MODULES = {  # Record verified SDK modules for each OpenAPI operation ID.
        "getOrgSettings": "mistapi.api.v1.orgs.setting",
        "listOrgSsos": "mistapi.api.v1.orgs.ssos",
        "listOrgAdmins": "mistapi.api.v1.orgs.admins",
        "listOrgApiTokens": "mistapi.api.v1.orgs.apitokens",
        "listOrgWebhooks": "mistapi.api.v1.orgs.webhooks",
    }

    def __init__(self, api_session: Any, org_id: str) -> None:
        """Store the Mist API context for source reads."""
        self.api_session = api_session  # Store the Mist API session supplied by the integration layer.
        self.org_id = org_id  # Store the organization identifier for all API calls.

    @classmethod
    def verify_sdk_operations(cls) -> dict[str, bool]:
        """Return whether each required SDK operation is present."""
        operation_map = {  # Bind operation names to the verified nested SDK modules.
            "getOrgSettings": mistapi.api.v1.orgs.setting,
            "listOrgSsos": mistapi.api.v1.orgs.ssos,
            "listOrgAdmins": mistapi.api.v1.orgs.admins,
            "listOrgApiTokens": mistapi.api.v1.orgs.apitokens,
            "listOrgWebhooks": mistapi.api.v1.orgs.webhooks,
        }
        return {name: hasattr(module, name) for name, module in operation_map.items()}  # Report each availability flag.

    def collect(self) -> OrganizationSecuritySourceData:
        """Collect source data from Mist and return one source object."""
        self._raise_when_operations_missing()  # Fail before network reads if SDK names drift.
        logging.info("Fetching organization settings for security posture")  # Log before the settings API call.
        settings = self._response_data(
            mistapi.api.v1.orgs.setting.getOrgSettings(self.api_session, self.org_id)
        )  # Fetch settings.
        logging.debug(
            "Fetched organization settings keys: %s", sorted(settings) if isinstance(settings, dict) else []
        )  # Log shape.
        logging.info("Fetching organization SSO list for security posture")  # Log before the SSO API call.
        ssos = self._response_list(
            mistapi.api.v1.orgs.ssos.listOrgSsos(self.api_session, self.org_id)
        )  # Fetch SSO data.
        logging.debug("Fetched %s organization SSO records", len(ssos))  # Log SSO count.
        logging.info("Fetching organization administrator list for security posture")  # Log before the admin API call.
        admins = self._response_list(
            mistapi.api.v1.orgs.admins.listOrgAdmins(self.api_session, self.org_id)
        )  # Fetch admins.
        logging.debug("Fetched %s organization administrator records", len(admins))  # Log admin count.
        logging.info("Fetching organization API token list for security posture")  # Log before the token API call.
        tokens = self._response_list(
            mistapi.api.v1.orgs.apitokens.listOrgApiTokens(self.api_session, self.org_id)
        )  # Fetch tokens.
        logging.debug("Fetched %s organization API token records", len(tokens))  # Log token count without token values.
        logging.info("Fetching organization webhook list for security posture")  # Log before the webhook API call.
        webhooks = self._response_list(
            mistapi.api.v1.orgs.webhooks.listOrgWebhooks(self.api_session, self.org_id)
        )  # Fetch webhooks.
        logging.debug("Fetched %s organization webhook records", len(webhooks))  # Log webhook count.
        return OrganizationSecuritySourceData(
            settings, ssos, admins, tokens, webhooks
        )  # Return one immutable source bundle.

    @classmethod
    def _raise_when_operations_missing(cls) -> None:
        """Raise when a required SDK operation is absent."""
        results = cls.verify_sdk_operations()  # Check SDK availability before data collection.
        missing = [name for name, present in results.items() if not present]  # Collect missing operation IDs.
        if missing:  # A missing method means the implementation must be updated.
            raise RuntimeError(f"Missing Mist API source operations: {', '.join(missing)}")

    @staticmethod
    def _response_data(response: Any) -> dict[str, Any]:
        """Return a response data mapping, or an empty mapping for unreadable data."""
        if OrgSecurityPostureSourceClient._is_error_response(response):  # Do not trust failed HTTP responses.
            logging.warning("Mist API source returned HTTP status %s", getattr(response, "status_code", "unknown"))
            return {}
        payload = getattr(response, "data", response)  # Support mistapi response objects and test doubles.
        return payload if isinstance(payload, dict) else {}  # Non-mapping settings cannot support direct checks.

    @staticmethod
    def _response_list(response: Any) -> list[dict[str, Any]]:
        """Return a response data list, or an empty list for unreadable data."""
        if OrgSecurityPostureSourceClient._is_error_response(response):  # Do not trust failed HTTP responses.
            logging.warning("Mist API source returned HTTP status %s", getattr(response, "status_code", "unknown"))
            return []
        payload = getattr(response, "data", response)  # Support mistapi response objects and test doubles.
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):  # Some list endpoints page results.
            payload = payload["results"]
        if not isinstance(payload, list):  # Non-list payloads provide no safe iterable evidence.
            return []
        return [item for item in payload if isinstance(item, dict)]  # Keep only mapping rows that checks can read.

    @staticmethod
    def _is_error_response(response: Any) -> bool:
        """Return whether a Mist API response status shows a failed read."""
        status_code = getattr(response, "status_code", None)  # Support mistapi responses and test doubles.
        if not isinstance(status_code, int):  # Objects without an HTTP status use payload-shape validation instead.
            return False
        return 400 <= status_code <= 599  # Treat every client or server error as unusable evidence.
