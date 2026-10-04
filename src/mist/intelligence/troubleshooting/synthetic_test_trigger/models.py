"""Pure models for the on-demand synthetic test trigger."""

from __future__ import annotations  # WHY: keep type annotations import-safe for the menu loader.

from dataclasses import dataclass, field  # WHY: request and result records need immutable value objects.
from time import time  # WHY: export rows need a trigger timestamp without pulling runtime state.
from typing import Final, Literal  # WHY: the Mist payload contains mixed JSON-compatible values.

Scope = Literal["site", "device", "radius"]  # WHY: only three trigger flows are valid for menu 283.

MASKED_VALUE: Final = "********"  # WHY: logs and export rows must never reveal a RADIUS password.
DEFAULT_TIMEOUT_SECONDS: Final = 120  # WHY: the issue names this default timeout for polling.
DEFAULT_POLL_INTERVAL_SECONDS: Final = 5.0  # WHY: polling must be bounded without hammering the API.
EXPORT_FILENAME: Final = "SyntheticTestTrigger.csv"  # WHY: the acceptance criteria name this output file.
EXPORT_ENDPOINT_NAME: Final = "SyntheticTestTrigger"  # WHY: the wiring manifest registers this export key.
IN_PROGRESS_STATUSES: Final = frozenset({"", "inprogress", "in_progress", "pending", "queued", "scheduled"})
SECRET_KEYS: Final = frozenset({"password", "secret", "shared_secret", "token", "passphrase"})


@dataclass(frozen=True)
class SyntheticTestRequest:
    """Describe one safe synthetic test trigger request."""

    scope: Scope  # WHY: the client dispatches to the correct Mist endpoint.
    site_id: str  # WHY: every supported endpoint is scoped to a Mist site.
    body: dict[str, object]  # WHY: the SDK sends this OpenAPI-compliant JSON body.
    summary: dict[str, object]  # WHY: logs and exports need a credential-free request summary.
    device_id: str | None = None  # WHY: site scope has no device while device and RADIUS scopes do.
    poll_query: dict[str, str] = field(default_factory=dict)  # WHY: site searches use optional query filters.
    triggered_at: float = field(default_factory=time)  # WHY: export rows need a stable run time.

    def public_body(self) -> dict[str, object]:
        """Return a masked body that is safe for logs."""
        safe_body = SecretMasker.mask_dict(self.body)  # WHY: credentials can live in the trigger body.
        return safe_body  # WHY: callers must never log the original body.


@dataclass(frozen=True)
class SyntheticTestResult:
    """Hold one synthetic test result or one timeout result."""

    status: str  # WHY: the operator needs the final state in the console and CSV.
    raw: dict[str, object]  # WHY: export rows keep the useful Mist result fields.
    timed_out: bool = False  # WHY: timeout is a local state, not always a Mist status.

    @classmethod
    def timeout(cls, timeout_seconds: int) -> SyntheticTestResult:
        """Build the result used when polling finds no completed record."""
        message = f"No synthetic test result arrived within {timeout_seconds} seconds."  # WHY: clear timeout text.
        raw = {"status": "timeout", "reason": message}  # WHY: the export row needs the same clear message.
        return cls(status="timeout", raw=raw, timed_out=True)  # WHY: caller reports a local timeout.


class SecretMasker:
    """Mask credential values before a record reaches logs or exports."""

    @staticmethod
    def is_secret_key(key: str) -> bool:
        """Return True when a field name carries secret material."""
        normalized_key = key.lower()  # WHY: API fields can differ in case across payloads.
        return normalized_key in SECRET_KEYS  # WHY: one shared list controls all redaction decisions.

    @staticmethod
    def mask_value(key: str, value: object) -> object:
        """Return a masked or recursively sanitized value."""
        if SecretMasker.is_secret_key(key):  # WHY: named secret fields must not leave this process.
            return MASKED_VALUE  # WHY: fixed-length masking avoids leaking secret length.
        if isinstance(value, dict):  # WHY: nested JSON objects can hold credential fields.
            return SecretMasker.mask_dict(value)  # WHY: recurse with the nested field names.
        if isinstance(value, list):  # WHY: Mist payloads can hold arrays of objects.
            return [SecretMasker.mask_value("", item) for item in value]  # WHY: sanitize each array item.
        return value  # WHY: non-secret scalar values are safe to keep.

    @staticmethod
    def mask_dict(source: dict[str, object]) -> dict[str, object]:
        """Return a copy with every secret field masked."""
        return {key: SecretMasker.mask_value(key, value) for key, value in source.items()}  # WHY: never mutate input.

    @staticmethod
    def remove_secret_fields(source: dict[str, object]) -> dict[str, object]:
        """Return a copy with secret fields removed."""
        return {key: value for key, value in source.items() if not SecretMasker.is_secret_key(key)}  # WHY: no export.


class RequestBodyBuilder:
    """Build OpenAPI-compliant synthetic test request bodies."""

    DEVICE_FIELDS: Final = frozenset(
        {
            "host",
            "hostname",
            "ip",
            "password",
            "ping_count",
            "ping_details",
            "ping_size",
            "port_id",
            "protocol",
            "tenant",
            "timeout",
            "traceroute_udp_port",
            "type",
            "url",
            "username",
            "vlan_id",
        }
    )
    INTEGER_FIELDS: Final = frozenset({"ping_count", "ping_size", "timeout", "traceroute_udp_port", "vlan_id"})

    @staticmethod
    def site(email: str = "") -> dict[str, object]:
        """Build a site-level synthetic test request body."""
        clean_email = email.strip()  # WHY: blank input should not create a meaningless JSON field.
        return {"email": clean_email} if clean_email else {}  # WHY: OpenAPI marks the field optional.

    @staticmethod
    def device(test_type: str, fields: dict[str, str]) -> dict[str, object]:
        """Build a device-level synthetic test request body."""
        body: dict[str, object] = {"type": test_type.strip()}  # WHY: OpenAPI requires the test type.
        for key, value in fields.items():  # WHY: optional fields depend on the selected test type.
            RequestBodyBuilder._add_device_field(body, key, value)  # WHY: validate and coerce each field.
        return body  # WHY: the SDK sends this body to Mist.

    @staticmethod
    def radius(user: str, password: str, profile: str = "dot1x") -> dict[str, object]:
        """Build a switch RADIUS synthetic test request body."""
        body = {"user": user.strip(), "password": password, "profile": profile.strip() or "dot1x"}  # WHY: schema.
        return body  # WHY: the RADIUS endpoint requires user and password.

    @staticmethod
    def _add_device_field(body: dict[str, object], key: str, value: str) -> None:
        """Add one valid non-empty device field to a request body."""
        clean_key = key.strip()  # WHY: prompt input can include spaces around a field name.
        clean_value = value.strip()  # WHY: empty values must not override API defaults.
        if not clean_value or clean_key not in RequestBodyBuilder.DEVICE_FIELDS:  # WHY: reject invalid fields early.
            return  # WHY: unknown or empty fields must not reach the API.
        body[clean_key] = RequestBodyBuilder._coerce_value(clean_key, clean_value)  # WHY: schema has integer fields.

    @staticmethod
    def _coerce_value(key: str, value: str) -> object:
        """Return a schema-friendly value for one prompted field."""
        if key in RequestBodyBuilder.INTEGER_FIELDS and value.isdigit():  # WHY: OpenAPI marks these as integers.
            return int(value)  # WHY: send a numeric JSON value when the operator gave one.
        if value.lower() in {"true", "false"}:  # WHY: ping_details is a boolean field.
            return value.lower() == "true"  # WHY: send a boolean JSON value.
        return value  # WHY: all other accepted fields are strings or enum strings.


class ResultNormalizer:
    """Convert Mist SDK responses into safe result dictionaries."""

    @staticmethod
    def response_data(response: object) -> object:
        """Return the SDK data payload or the object itself."""
        return getattr(response, "data", response)  # WHY: tests can pass plain dictionaries.

    @staticmethod
    def first_site_result(response: object) -> dict[str, object] | None:
        """Return the newest site search result when one exists."""
        data = ResultNormalizer.response_data(response)  # WHY: Mist SDK stores JSON under data.
        if not isinstance(data, dict):  # WHY: a non-dict cannot hold search results.
            return None  # WHY: caller continues polling.
        results = data.get("results")  # WHY: the search schema stores rows in results.
        if not isinstance(results, list) or not results:  # WHY: empty search results are not complete.
            return None  # WHY: caller continues polling.
        first_result = results[0]  # WHY: limit=1 asks Mist for the newest matching result.
        return first_result if isinstance(first_result, dict) else None  # WHY: only dictionaries become rows.

    @staticmethod
    def device_result(response: object) -> dict[str, object] | None:
        """Return a device synthetic test result when one exists."""
        data = ResultNormalizer.response_data(response)  # WHY: Mist SDK stores JSON under data.
        return data if isinstance(data, dict) and data else None  # WHY: empty data means keep polling.

    @staticmethod
    def is_complete(result: dict[str, object]) -> bool:
        """Return True when the result is no longer in progress."""
        status = str(result.get("status", "")).lower()  # WHY: status names vary by endpoint.
        return status not in IN_PROGRESS_STATUSES  # WHY: every other status or result row is final enough to export.

    @staticmethod
    def to_result(result: dict[str, object]) -> SyntheticTestResult:
        """Return a normalized result object."""
        safe_result = SecretMasker.remove_secret_fields(result)  # WHY: results should not export credentials.
        status = str(safe_result.get("status", "complete"))  # WHY: site search rows can omit status.
        return SyntheticTestResult(status=status, raw=safe_result)  # WHY: operation code consumes one shape.


class ExportRowBuilder:
    """Build safe CSV rows for one trigger run."""

    FIELDNAMES: Final = [
        "site_id",
        "device_id",
        "scope",
        "test_type",
        "status",
        "failed",
        "reason",
        "latency",
        "rx_mbps",
        "tx_mbps",
        "timestamp",
        "triggered_at",
        "timed_out",
    ]

    @staticmethod
    def build(request: SyntheticTestRequest, result: SyntheticTestResult) -> dict[str, object]:
        """Return one flat export row without credential fields."""
        safe_summary = SecretMasker.remove_secret_fields(request.summary)  # WHY: request summary must stay safe.
        row = {field: "" for field in ExportRowBuilder.FIELDNAMES}  # WHY: stable columns help CSV readers.
        row.update(safe_summary)  # WHY: add site, scope, device, and test type values.
        row.update(SecretMasker.remove_secret_fields(result.raw))  # WHY: add safe result values only.
        row["site_id"] = request.site_id  # WHY: the site column is mandatory for operator filtering.
        row["scope"] = request.scope  # WHY: the operator must know which endpoint ran.
        row["device_id"] = request.device_id or ""  # WHY: site scope has no device identifier.
        row["triggered_at"] = request.triggered_at  # WHY: the row needs the request time.
        row["timed_out"] = result.timed_out  # WHY: a timeout is local state, not always from Mist.
        row["test_type"] = str(result.raw.get("type", row["test_type"]))  # WHY: final result can refine site type.
        row["status"] = result.status  # WHY: normalize the status column after row updates.
        return row  # WHY: DataExporter accepts flat dictionaries.
