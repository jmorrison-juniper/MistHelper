"""Pure models for menu 285, the NAC identity provider credential test."""

from __future__ import annotations  # WHY: allow compact type syntax in Python 3.13.

import json  # WHY: export rows store returned attributes as stable JSON text.
from collections.abc import Mapping  # WHY: Mist responses can add fields without a code change.
from dataclasses import dataclass, field  # WHY: result objects are small immutable records.
from datetime import UTC, datetime  # WHY: export rows need an unambiguous UTC timestamp.
from typing import Any  # WHY: Mist responses can add fields with dynamic values.

SECRET_KEYS = {"password", "passphrase", "secret", "token"}  # WHY: these fields must never reach exports.
RESULT_FIELD_NAMES = (  # WHY: fixed field order keeps CSV output stable for operators.
    "tested_at",
    "idp_id",
    "idp_name",
    "idp_type",
    "idp_source",
    "username",
    "verdict",
    "reason",
    "attributes",
)


@dataclass(frozen=True, slots=True)
class IdentityProviderChoice:
    """Represent one identity provider that an operator can select."""

    idp_id: str  # WHY: Mist uses this value to identify the provider.
    name: str  # WHY: operators need a readable selection label.
    idp_type: str = ""  # WHY: the API may return ldap, oauth, or another type.
    source: str = "mist_nac.idps"  # WHY: the source explains how the row was found.
    realms: tuple[str, ...] = field(default_factory=tuple)  # WHY: realms help an operator pick the right provider.

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any], source: str) -> IdentityProviderChoice | None:
        """Build one provider choice from a Mist row."""
        idp_id = str(row.get("id") or row.get("idp_id") or "").strip()  # WHY: both field names appear in Mist data.
        if not idp_id:  # WHY: a provider without an identifier cannot be tested.
            return None  # WHY: skip unusable rows before the prompt.
        name_value = row.get("name") or row.get("display_name") or idp_id  # WHY: settings rows may not have names.
        idp_type = str(row.get("type") or row.get("idp_type") or "").strip()  # WHY: show the provider class if known.
        realms = NacIdpCredentialModel.read_realms(row)  # WHY: user realms help identify the provider.
        return cls(idp_id, str(name_value).strip(), idp_type, source, realms)  # WHY: one normalized prompt row.

    def display_label(self, index: int) -> str:
        """Return the safe prompt label for this provider."""
        type_text = f" [{self.idp_type}]" if self.idp_type else ""  # WHY: omit empty brackets when type is unknown.
        realm_text = ", ".join(self.realms) if self.realms else "no realms listed"  # WHY: explain sparse rows.
        return f"{index}. {self.name}{type_text} - {realm_text}"  # WHY: one line per provider for the prompt.


@dataclass(frozen=True, slots=True)
class CredentialTestRequest:
    """Represent the credential validation request body."""

    idp_id: str  # WHY: tie the credential test to the selected provider.
    username: str  # WHY: Mist validates this identity against the provider.
    password: str  # WHY: Mist needs the password, but exports must never store it.

    def as_body(self) -> dict[str, str]:
        """Return the body sent to `validateOrgIdpCredential`."""
        return {"idp_id": self.idp_id, "username": self.username, "password": self.password}  # WHY: API body.


@dataclass(frozen=True, slots=True)
class CredentialTestResult:
    """Represent a safe validation result."""

    provider: IdentityProviderChoice  # WHY: export rows must name the tested provider.
    username: str  # WHY: export rows must name the tested user.
    status: str  # WHY: the verdict is the primary operator result.
    reason: str  # WHY: failure output must preserve the API reason.
    attributes: Mapping[str, Any]  # WHY: Mist can return groups and other safe attributes.
    tested_at: str  # WHY: exports need the time of the validation.

    @classmethod
    def from_response(
        cls,
        provider: IdentityProviderChoice,
        username: str,
        status_code: int,
        payload: Mapping[str, Any] | None,
    ) -> CredentialTestResult:
        """Normalize one Mist response into a safe result."""
        data = dict(payload or {})  # WHY: copy the response so secret filtering cannot mutate caller data.
        status = NacIdpCredentialModel.read_status(status_code, data)  # WHY: one rule handles HTTP and body status.
        reason = NacIdpCredentialModel.read_reason(status_code, data)  # WHY: failures must print the Mist reason.
        attributes = NacIdpCredentialModel.safe_attributes(data)  # WHY: export only non-secret response fields.
        return cls(provider, username, status, reason, attributes, NacIdpCredentialModel.utc_now())  # WHY: safe row.

    def as_row(self) -> dict[str, str]:
        """Return the password-free export row."""
        attributes = json.dumps(dict(self.attributes), sort_keys=True, default=str)  # WHY: keep one stable CSV cell.
        return {  # WHY: the exporter accepts flat string dictionaries.
            "tested_at": self.tested_at,
            "idp_id": self.provider.idp_id,
            "idp_name": self.provider.name,
            "idp_type": self.provider.idp_type,
            "idp_source": self.provider.source,
            "username": self.username,
            "verdict": self.status,
            "reason": self.reason,
            "attributes": attributes,
        }


class NacIdpCredentialModel:
    """Hold pure helpers for provider and response normalization."""

    @staticmethod
    def read_realms(row: Mapping[str, Any]) -> tuple[str, ...]:
        """Return the provider realms as a tuple of strings."""
        raw_realms = row.get("user_realms") or row.get("domains") or row.get("domain") or []  # WHY: APIs differ.
        if isinstance(raw_realms, str):  # WHY: SSO rows can hold one domain string.
            return (raw_realms,)  # WHY: the prompt code expects an iterable.
        if isinstance(raw_realms, list | tuple):  # WHY: NAC settings use a list of realms.
            return tuple(str(realm) for realm in raw_realms if realm)  # WHY: skip blank realm values.
        return ()  # WHY: unknown realm shapes should not break a credential test.

    @staticmethod
    def read_status(status_code: int, data: Mapping[str, Any]) -> str:
        """Return `success`, `failure`, or `unknown` from response data."""
        body_status = str(data.get("status") or "").lower()  # WHY: the endpoint examples use status text.
        if body_status in {"success", "failure"}:  # WHY: preserve known verdict words.
            return body_status  # WHY: the body status is more precise than HTTP 200.
        if status_code >= 400:  # WHY: an HTTP error is a failed validation call.
            return "failure"  # WHY: make the export verdict explicit.
        return "unknown"  # WHY: keep unexpected success bodies visible to operators.

    @staticmethod
    def read_reason(status_code: int, data: Mapping[str, Any]) -> str:
        """Return the readable reason from one response."""
        reason = data.get("error") or data.get("reason") or data.get("message")  # WHY: Mist errors vary by endpoint.
        if reason:  # WHY: prefer the API reason when it exists.
            return str(reason)  # WHY: export rows need text.
        if status_code >= 400:  # WHY: an HTTP error without a body still needs a reason.
            return f"HTTP {status_code}"  # WHY: include the only failure evidence we have.
        return ""  # WHY: success responses often have no reason.

    @classmethod
    def safe_attributes(cls, data: Mapping[str, Any]) -> dict[str, Any]:
        """Return non-secret response attributes for display and export."""
        attributes: dict[str, Any] = {}  # WHY: build a sanitized copy for the result.
        for key, value in data.items():  # WHY: preserve unknown future attributes from Mist.
            if key in {"status", "error", "reason", "message"}:  # WHY: these fields have dedicated columns.
                continue  # WHY: avoid duplicate data in the attributes cell.
            if cls.is_secret_key(key):  # WHY: defensive filtering blocks accidental credential echoes.
                continue  # WHY: never export secret-like fields.
            attributes[str(key)] = value  # WHY: the remaining value is safe operational evidence.
        return attributes  # WHY: caller serializes this mapping for the export row.

    @staticmethod
    def is_secret_key(key: str) -> bool:
        """Return True when a response key must not be exported."""
        lowered = key.lower()  # WHY: Mist keys can vary in case.
        return any(secret in lowered for secret in SECRET_KEYS)  # WHY: block password-like fields by substring.

    @staticmethod
    def utc_now() -> str:
        """Return the current time in UTC ISO 8601 format."""
        return datetime.now(tz=UTC).replace(microsecond=0).isoformat()  # WHY: seconds precision is enough for CSV.
