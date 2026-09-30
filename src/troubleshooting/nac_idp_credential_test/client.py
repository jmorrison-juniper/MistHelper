"""Mist API client for menu 285, the NAC identity provider credential test."""

from __future__ import annotations  # WHY: enable PEP 604 types on Python 3.13.

import logging  # WHY: log each API action without exposing credentials.
from collections.abc import Mapping  # WHY: API response bodies are dictionary-like in tests and SDK objects.
from typing import Any  # WHY: mistapi responses are dynamic runtime objects.

import mistapi  # WHY: use the installed SDK and pagination helper.
from mistapi.api.v1.orgs import mist_nac, setting, ssos  # WHY: these modules own the required org APIs.

from src.troubleshooting.nac_idp_credential_test.model import (
    CredentialTestRequest,
    CredentialTestResult,
    IdentityProviderChoice,
)

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter this feature.

HTTP_OK = 200  # WHY: mistapi returns 200 for a successful read or validation request.
SSO_PAGE_LIMIT = 1000  # WHY: use the normal maximum page size for organization lists.
SOURCE_NAC_SETTINGS = "mist_nac.idps"  # WHY: label the primary provider source.
SOURCE_ORG_SSOS = "listOrgSsos"  # WHY: label the fallback provider source.


class NacIdpCredentialClient:
    """Read identity providers and validate one credential through Mist."""

    def __init__(self, apisession: Any, org_id: str) -> None:
        """Store the active Mist session and organization identifier."""
        self._apisession = apisession  # WHY: the shared authenticated session sends every request.
        self._org_id = str(org_id)  # WHY: Mist API paths require the organization identifier as text.

    def list_identity_providers(self) -> list[IdentityProviderChoice]:
        """Return selectable identity providers for the organization."""
        providers = self._read_nac_setting_idps()  # WHY: NAC settings hold Access Assurance provider IDs.
        if providers:  # WHY: the primary source is the correct source for this feature.
            return providers  # WHY: do not mix SSO rows into a valid NAC provider list.
        return self._read_sso_idps()  # WHY: fallback gives evidence when NAC settings are empty.

    def validate_credential(
        self,
        request: CredentialTestRequest,
        provider: IdentityProviderChoice,
    ) -> CredentialTestResult:
        """Send one credential validation request to Mist."""
        logger.info("Validating NAC identity provider credential for org %s", self._org_id)  # WHY: action log.
        response = mist_nac.validateOrgIdpCredential(  # WHY: SDK wrapper owns the documented endpoint path.
            self._apisession,
            self._org_id,
            request.as_body(),
        )
        status_code = self._status_code(response)  # WHY: status drives failure normalization.
        payload = self._payload_mapping(response)  # WHY: result model only accepts mappings.
        logger.debug("NAC identity provider credential validation returned HTTP %s", status_code)  # WHY: summary.
        return CredentialTestResult.from_response(provider, request.username, status_code, payload)  # WHY: safe result.

    def _read_nac_setting_idps(self) -> list[IdentityProviderChoice]:
        """Read NAC identity providers from organization settings."""
        logger.info("Reading NAC identity providers from organization settings for org %s", self._org_id)  # WHY.
        response = setting.getOrgSettings(self._apisession, self._org_id)  # WHY: settings hold `mist_nac.idps`.
        status_code = self._status_code(response)  # WHY: log the HTTP outcome without body secrets.
        payload = self._payload_mapping(response)  # WHY: settings response must be a mapping to parse.
        logger.debug("Organization settings read returned HTTP %s", status_code)  # WHY: result summary.
        if status_code != HTTP_OK or payload is None:  # WHY: failed settings reads cannot produce safe choices.
            return []  # WHY: caller can try the fallback list.
        rows = self._mist_nac_idp_rows(payload)  # WHY: isolate the schema path in one helper.
        return self._choices_from_rows(rows, SOURCE_NAC_SETTINGS)  # WHY: normalize rows for the prompt.

    def _read_sso_idps(self) -> list[IdentityProviderChoice]:
        """Read organization SSO providers as fallback evidence."""
        logger.info("Reading organization SSO identity providers for org %s", self._org_id)  # WHY: action log.
        response = ssos.listOrgSsos(self._apisession, self._org_id, limit=SSO_PAGE_LIMIT)  # WHY: read page one.
        status_code = self._status_code(response)  # WHY: guard failed list reads.
        if status_code != HTTP_OK:  # WHY: fallback failed, so no provider can be listed safely.
            logger.debug("Organization SSO provider read returned HTTP %s", status_code)  # WHY: result summary.
            return []  # WHY: operation will report that no providers were found.
        rows = mistapi.get_all(response=response, mist_session=self._apisession)  # WHY: collect every SSO page.
        logger.debug("Organization SSO provider read returned rows=%d", len(rows))  # WHY: result summary.
        return self._choices_from_rows(rows, SOURCE_ORG_SSOS)  # WHY: normalize fallback rows for the prompt.

    @staticmethod
    def _mist_nac_idp_rows(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        """Return the raw `mist_nac.idps` rows from settings."""
        mist_nac_data = payload.get("mist_nac")  # WHY: organization settings nest NAC values here.
        if not isinstance(mist_nac_data, Mapping):  # WHY: absent settings mean no configured NAC providers.
            return []  # WHY: caller can report no providers or use fallback.
        idp_rows = mist_nac_data.get("idps")  # WHY: OpenAPI names this list as the NAC IDP collection.
        if not isinstance(idp_rows, list):  # WHY: a non-list cannot be safely presented as choices.
            return []  # WHY: caller can report no providers or use fallback.
        return [row for row in idp_rows if isinstance(row, Mapping)]  # WHY: skip malformed list entries.

    @staticmethod
    def _choices_from_rows(rows: list[Mapping[str, Any]], source: str) -> list[IdentityProviderChoice]:
        """Normalize raw provider rows into prompt choices."""
        choices: list[IdentityProviderChoice] = []  # WHY: preserve the API order for operator selection.
        for row in rows:  # WHY: each API row can become one prompt choice.
            choice = IdentityProviderChoice.from_mapping(row, source)  # WHY: centralize provider normalization.
            if choice is not None:  # WHY: discard rows that have no identifier.
                choices.append(choice)  # WHY: keep only testable providers.
        return choices  # WHY: caller displays these rows.

    @staticmethod
    def _status_code(response: Any) -> int:
        """Return the integer HTTP status from a response."""
        status_code = getattr(response, "status_code", HTTP_OK)  # WHY: tests can use small fake responses.
        return int(status_code) if isinstance(status_code, int) else HTTP_OK  # WHY: non-integers should not fail.

    @staticmethod
    def _payload_mapping(response: Any) -> Mapping[str, Any] | None:
        """Return response data when it is a mapping."""
        data = getattr(response, "data", None)  # WHY: mistapi stores parsed JSON on `data`.
        return data if isinstance(data, Mapping) else None  # WHY: caller parses only dictionary payloads.
