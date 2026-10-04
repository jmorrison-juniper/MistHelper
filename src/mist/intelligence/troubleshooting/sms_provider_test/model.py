"""Pure models for the guest portal SMS provider test operation."""

from __future__ import annotations  # WHY: enable modern annotations for the dataclasses below.

import json  # WHY: convert structured Mist responses into one safe result cell.
from dataclasses import dataclass, fields  # WHY: define stable result rows and column order.
from datetime import UTC, datetime  # WHY: stamp each result in UTC for audit use.

ERROR_TEXT_LIMIT = 300  # WHY: keep the CSV response cell readable in the terminal and spreadsheet tools.
EXPORT_FILENAME = "SmsProviderTest.csv"  # WHY: the assignment requires this exact output file name.
EXPORT_ENDPOINT_NAME = "testSmsProviderSetup"  # WHY: the integration manifest uses this database strategy key.
VERDICT_ACCEPTED = "accepted"  # WHY: a short stable value marks a 2xx answer.
VERDICT_FAILED = "failed"  # WHY: a short stable value marks a non-2xx answer.


@dataclass(frozen=True, slots=True)
class SmsProviderDefinition:
    """Describe one SMS provider test endpoint and its request body."""

    key: str  # WHY: the prompt and dispatcher use a stable lowercase key.
    label: str  # WHY: the operator sees the provider name in output.
    operation_id: str  # WHY: research and wiring name the OpenAPI operation.
    body_fields: tuple[str, ...]  # WHY: body construction preserves the OpenAPI key order.
    secret_fields: frozenset[str]  # WHY: these fields must use hidden input and never reach output.

    def build_body(self, values: dict[str, str]) -> dict[str, str]:
        """Return the request body for this provider.

        Args:
            values: Prompt values keyed by OpenAPI field name.

        Returns:
            The request body with exactly this provider's OpenAPI fields.
        """
        return {field_name: values[field_name] for field_name in self.body_fields}  # WHY: reject missing fields.

    @property
    def public_fields(self) -> tuple[str, ...]:
        """Return the fields that can be entered with visible input."""
        return tuple(field for field in self.body_fields if field not in self.secret_fields)  # WHY: prompt safely.


TWILIO_PROVIDER = SmsProviderDefinition(  # WHY: one definition mirrors the OpenAPI Twilio schema.
    key="twilio",  # WHY: dispatcher key for the Twilio endpoint.
    label="Twilio",  # WHY: operator-facing provider name.
    operation_id="testSiteWlanTwilioSetup",  # WHY: exact OpenAPI operationId.
    body_fields=("from", "to", "twilio_auth_token", "twilio_sid"),  # WHY: exact OpenAPI request keys.
    secret_fields=frozenset({"twilio_auth_token", "twilio_sid"}),  # WHY: both values identify the account.
)
SMSGLOBAL_PROVIDER = SmsProviderDefinition(  # WHY: one definition mirrors the OpenAPI SMSGlobal schema.
    key="smsglobal",  # WHY: dispatcher key for the SMSGlobal endpoint.
    label="SMSGlobal",  # WHY: operator-facing provider name.
    operation_id="testSiteWlanSmsGlobal",  # WHY: exact OpenAPI operationId.
    body_fields=("smsglobal_api_key", "smsglobal_api_secret", "to"),  # WHY: exact OpenAPI request keys.
    secret_fields=frozenset({"smsglobal_api_key", "smsglobal_api_secret"}),  # WHY: both fields are credentials.
)
TELSTRA_PROVIDER = SmsProviderDefinition(  # WHY: one definition mirrors the OpenAPI Telstra schema.
    key="telstra",  # WHY: dispatcher key for the Telstra endpoint.
    label="Telstra",  # WHY: operator-facing provider name.
    operation_id="testSiteWlanTelstraSetup",  # WHY: exact OpenAPI operationId.
    body_fields=("telstra_client_id", "telstra_client_secret", "to"),  # WHY: exact OpenAPI request keys.
    secret_fields=frozenset({"telstra_client_id", "telstra_client_secret"}),  # WHY: both fields are credentials.
)
PROVIDERS = (TWILIO_PROVIDER, SMSGLOBAL_PROVIDER, TELSTRA_PROVIDER)  # WHY: prompt order stays stable.
PROVIDERS_BY_KEY = {provider.key: provider for provider in PROVIDERS}  # WHY: convert a selection into a definition.


@dataclass(frozen=True, slots=True)
class SmsProviderApiResult:
    """Hold the Mist response in a secret-free transport object."""

    status_code: int | None  # WHY: a missing value means no HTTP answer reached MistHelper.
    response_text: str  # WHY: the operator needs the Mist error text on a failed request.

    @property
    def accepted(self) -> bool:
        """Return True when Mist accepted the provider test request."""
        status_code = self.status_code  # WHY: keep the optional value local for the comparison.
        return isinstance(status_code, int) and 200 <= status_code < 300  # WHY: any 2xx response is accepted.


@dataclass(frozen=True, slots=True)
class SmsProviderResultRow:
    """One export row for one SMS provider test."""

    provider: str  # WHY: name which provider was tested.
    destination: str  # WHY: show the phone number that should receive the code.
    verdict: str  # WHY: give spreadsheet users a stable success or failure value.
    http_status: int | None  # WHY: show the Mist response status for troubleshooting.
    response_text: str  # WHY: show the short response without credentials.
    tested_at: str  # WHY: show when the test ran.

    @classmethod
    def column_names(cls) -> list[str]:
        """Return the CSV column names in dataclass order."""
        return [field.name for field in fields(cls)]  # WHY: one source controls the export column order.

    def as_row(self) -> dict[str, str | int | None]:
        """Return this result as a flat export row."""
        return {field.name: getattr(self, field.name) for field in fields(self)}  # WHY: match column_names order.


class SmsProviderCatalog:
    """Resolve provider choices and build provider request bodies."""

    @staticmethod
    def choices_text() -> str:
        """Return the provider choices for a terminal prompt."""
        pairs = [f"{number}) {provider.label}" for number, provider in enumerate(PROVIDERS, start=1)]  # WHY: menu.
        return ", ".join(pairs)  # WHY: one short line keeps the prompt readable.

    @staticmethod
    def by_selection(selection: str) -> SmsProviderDefinition | None:
        """Return the provider selected by number, name, or key.

        Args:
            selection: Operator input from the provider prompt.

        Returns:
            The matching provider, or None when the input is unknown.
        """
        normalized = selection.strip().lower()  # WHY: accept case and surrounding-space differences.
        if normalized.isdigit():  # WHY: numbered choices are easiest for menu users.
            return SmsProviderCatalog._by_number(int(normalized))  # WHY: convert the number to a provider.
        return SmsProviderCatalog._by_key_or_label(normalized)  # WHY: accept typed provider names too.

    @staticmethod
    def _by_number(number: int) -> SmsProviderDefinition | None:
        """Return the provider for a one-based menu number."""
        index = number - 1  # WHY: the operator sees one-based numbers, while tuples are zero-based.
        if 0 <= index < len(PROVIDERS):  # WHY: accept only displayed choices.
            return PROVIDERS[index]  # WHY: return the selected provider.
        return None  # WHY: the caller prints the refusal.

    @staticmethod
    def _by_key_or_label(normalized: str) -> SmsProviderDefinition | None:
        """Return the provider for a normalized key or label."""
        for provider in PROVIDERS:  # WHY: the list is short and stable.
            if normalized in {provider.key, provider.label.lower()}:  # WHY: accept the key or the display name.
                return provider  # WHY: found the provider.
        return None  # WHY: the caller prints the refusal.


class SmsProviderResultBuilder:
    """Build result rows and redact secret values from response text."""

    @staticmethod
    def build(
        provider: SmsProviderDefinition,
        destination: str,
        api_result: SmsProviderApiResult,
        secrets: tuple[str, ...],
    ) -> SmsProviderResultRow:
        """Return the output row for one provider test.

        Args:
            provider: Provider that was tested.
            destination: Destination phone number.
            api_result: Normalized Mist response.
            secrets: Secret values that must not appear in the result text.

        Returns:
            A credential-free export row.
        """
        verdict = VERDICT_ACCEPTED if api_result.accepted else VERDICT_FAILED  # WHY: stable operator verdict.
        response_text = SmsProviderResultBuilder.redact(api_result.response_text, secrets)  # WHY: no secrets.
        tested_at = datetime.now(UTC).isoformat(timespec="seconds")  # WHY: one UTC timestamp for the row.
        return SmsProviderResultRow(
            provider.label, destination, verdict, api_result.status_code, response_text, tested_at
        )

    @staticmethod
    def redact(text: str, secrets: tuple[str, ...]) -> str:
        """Return response text with every known secret replaced."""
        redacted = text[:ERROR_TEXT_LIMIT]  # WHY: cap the response before writing it to a CSV cell.
        for secret in secrets:  # WHY: remove every credential value known to the operation.
            if secret:  # WHY: an empty secret would match every location in the string.
                redacted = redacted.replace(secret, "[REDACTED]")  # WHY: protect the credential from output.
        return redacted  # WHY: the caller stores only this sanitized text.

    @staticmethod
    def response_text(data: object) -> str:
        """Return a short readable string for a Mist response body."""
        if data is None:  # WHY: no body is a valid response form.
            return ""  # WHY: keep the export cell empty rather than writing None.
        if isinstance(data, str):  # WHY: Mist can return a plain text error.
            return data[:ERROR_TEXT_LIMIT]  # WHY: keep the cell short.
        return json.dumps(data, sort_keys=True, default=str)[:ERROR_TEXT_LIMIT]  # WHY: JSON keeps structured errors.
