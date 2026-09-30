"""Pure scoring model for the PSK hygiene report."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any, Literal

FINDING_ORDER = (  # Keep CSV finding labels stable for tests and operators.
    "expired",  # Mark keys that already passed their expire time.
    "expires_soon",  # Mark keys that expire within the warning window.
    "uncapped_multi_use",  # Mark keys that can spread without a binding or cap.
    "rotation_pending",  # Mark keys that still hold an old passphrase value.
    "orphan_ssid",  # Mark keys whose SSID has no organization WLAN source.
)
EXPIRING_SOON_DAYS = 30  # Keep the warning window aligned with the feature contract.
SITE_WLAN_SCOPE_MESSAGE = "Site-level WLANs are outside this report scope."  # State the known scope limit.
UNKNOWN_WLAN_SCOPE_MESSAGE = (  # Explain unknown WLAN matching without exposing PSK details.
    "Organization WLAN data was unavailable; orphan SSID findings are unknown."
)


@dataclass(frozen=True)
class PskInput:
    """Represent one sanitized PSK record."""

    name: str  # Identify the PSK without exposing the secret.
    ssid: str  # Match the PSK to organization WLAN SSIDs.
    role: str  # Preserve the Mist role value for the operator.
    vlan: str | int | None  # Preserve the visible VLAN value from Mist.
    usage: int | None  # Preserve the usage count when Mist sends it.
    max_usage: int | None  # Preserve the usage cap when Mist sends it.
    expire_time: str | None  # Preserve the source expire value for output.
    mac: str | None  # Keep MAC binding state for cap scoring only.
    macs: tuple[str, ...]  # Keep multi-MAC binding state for cap scoring only.
    old_passphrase_present: bool  # Record old passphrase presence without the value.

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> PskInput:
        """Build a sanitized PSK input from a Mist record."""
        old_passphrase_present = _has_value(record.get("old_passphrase"))  # Keep only old-secret presence.
        macs = tuple(str(mac) for mac in record.get("macs", []) if _has_value(mac))  # Normalize MAC list values.
        return cls(  # Return only fields that the scoring model can safely use.
            name=_text(record.get("name")),  # Use an empty name when Mist omits it.
            ssid=normalize_ssid(record.get("ssid")),  # Trim SSID text for matching.
            role=_text(record.get("role")),  # Use an empty role when Mist omits it.
            vlan=record.get("vlan"),  # Preserve the visible VLAN value from Mist.
            usage=_optional_int(record.get("usage")),  # Normalize empty usage to None.
            max_usage=_optional_int(record.get("max_usage")),  # Normalize empty maximum usage to None.
            expire_time=_optional_text(record.get("expire_time")),  # Preserve the visible expire value.
            mac=_optional_text(record.get("mac")),  # Preserve only the binding indicator.
            macs=macs,  # Preserve only normalized binding indicators.
            old_passphrase_present=old_passphrase_present,  # Preserve old secret presence only.
        )


@dataclass(frozen=True)
class WlanReference:
    """Represent one organization WLAN SSID source."""

    ssid: str  # Match PSK SSIDs against this normalized value.
    source: Literal["org_wlan", "template"]  # Identify the organization SSID source.
    source_name: str  # Help tests and future diagnostics identify the source.


@dataclass(frozen=True)
class PskHygieneRow:
    """Represent one safe output row."""

    name: str  # Show the PSK name without a secret.
    ssid: str  # Show the normalized SSID used for matching.
    role: str  # Show the Mist role value.
    vlan: str  # Show the Mist VLAN value or blank.
    usage: int | str  # Show the usage count or blank.
    max_usage: int | str  # Show the usage cap or blank.
    expire_time: str  # Show the original expire time or blank.
    days_remaining: int | str  # Show days remaining or blank.
    rotation_pending: bool  # Show whether rotation still has an old secret.
    old_passphrase_present: bool  # Show old secret presence only.
    wlan_match: bool | str  # Show true, false, or unknown matching state.
    findings: str  # Show stable comma-separated finding labels.

    def as_output_row(self) -> dict[str, str | int | bool]:
        """Return a dictionary safe for output backends."""
        return asdict(self)  # Convert the dataclass into the output row contract.

    @property
    def finding_labels(self) -> tuple[str, ...]:
        """Return finding labels as a tuple."""
        if not self.findings:  # Avoid a one-item tuple containing an empty string.
            return ()  # Represent no findings with an empty tuple.
        return tuple(self.findings.split(","))  # Split the stable CSV label list.


@dataclass(frozen=True)
class HygieneSummary:
    """Represent the sanitized summary for console and logs."""

    total_psks: int  # Count every reviewed PSK.
    expired: int  # Count rows with the expired finding.
    expires_soon: int  # Count rows with the expires_soon finding.
    uncapped_multi_use: int  # Count rows with the uncapped_multi_use finding.
    rotation_pending: int  # Count rows with the rotation_pending finding.
    orphan_ssid: int  # Count rows with the orphan_ssid finding.
    wlan_scope: str  # State the WLAN scope used by the report.

    @classmethod
    def from_rows(cls, rows: list[PskHygieneRow], wlan_scope: str = SITE_WLAN_SCOPE_MESSAGE) -> HygieneSummary:
        """Build summary counts from report rows."""
        labels = [label for row in rows for label in row.finding_labels]  # Flatten row findings for exact counts.
        return cls(  # Return counts that match the findings column exactly.
            total_psks=len(rows),  # Count every output row.
            expired=labels.count("expired"),  # Count expired labels.
            expires_soon=labels.count("expires_soon"),  # Count soon-expiring labels.
            uncapped_multi_use=labels.count("uncapped_multi_use"),  # Count uncapped labels.
            rotation_pending=labels.count("rotation_pending"),  # Count pending rotation labels.
            orphan_ssid=labels.count("orphan_ssid"),  # Count orphan SSID labels.
            wlan_scope=wlan_scope,  # Preserve the scope statement for display.
        )

    def to_lines(self) -> list[str]:
        """Return sanitized summary lines for console output."""
        return [  # Keep summary text free of PSK names and secret values.
            "PSK hygiene summary:",
            f"Total PSKs reviewed: {self.total_psks}",
            f"Expired keys: {self.expired}",
            f"Keys that expire in 30 days: {self.expires_soon}",
            f"Uncapped multi-use keys: {self.uncapped_multi_use}",
            f"Pending rotations: {self.rotation_pending}",
            f"Orphan SSIDs: {self.orphan_ssid}",
            self.wlan_scope,
        ]


def normalize_ssid(value: Any) -> str:
    """Return trimmed SSID text."""
    return "" if value is None else str(value).strip()  # Normalize absent SSIDs to a matchable empty string.


def psk_inputs_from_records(records: list[dict[str, Any]]) -> list[PskInput]:
    """Return sanitized PSK inputs from Mist records."""
    return [PskInput.from_record(record) for record in records]  # Strip secrets before scoring begins.


def wlan_references_from_records(wlans: list[dict[str, Any]], templates: list[dict[str, Any]]) -> list[WlanReference]:
    """Build organization WLAN references from WLAN and template records."""
    org_references = _org_wlan_references(wlans)  # Convert organization WLAN rows into match sources.
    template_references = _template_wlan_references(templates)  # Convert template WLAN rows into match sources.
    return org_references + template_references  # Preserve source order for deterministic diagnostics.


def days_remaining(expire_time: str | None, now: datetime | None = None) -> int | None:
    """Return whole days remaining until the expire time."""
    expire_at = parse_expire_time(expire_time)  # Parse the visible Mist value into a comparable time.
    if expire_at is None:  # Blank or malformed values cannot produce a safe count.
        return None  # Use a blank output value for unknown remaining days.
    current_time = now or datetime.now(UTC)  # Use injected time for tests or current UTC time for runtime.
    current_time = _ensure_utc(current_time)  # Compare aware datetimes consistently.
    total_seconds = (expire_at - current_time).total_seconds()  # Convert the interval into whole-day math.
    return int(total_seconds // 86400)  # Use whole days so a same-day future expiry returns zero.


def parse_expire_time(expire_time: str | None) -> datetime | None:
    """Parse a Mist expire time into UTC."""
    if not expire_time:  # Empty values mean the PSK does not expire.
        return None  # Keep non-expiring keys out of time-based findings.
    candidate = expire_time.strip().replace("Z", "+00:00")  # Accept common UTC suffix values from APIs.
    try:  # Keep malformed API values from stopping a safe report.
        parsed_time = datetime.fromisoformat(candidate)  # Parse ISO date or date-time values.
    except ValueError:  # Treat unexpected formats as unknown rather than risky.
        return None  # Keep unknown dates as blank days remaining.
    return _ensure_utc(parsed_time)  # Normalize naive or offset-aware values to UTC.


def build_hygiene_rows(
    psks: list[PskInput], wlan_references: list[WlanReference] | None, now: datetime | None = None
) -> list[PskHygieneRow]:
    """Build safe report rows from sanitized PSKs."""
    wlan_match_set = _wlan_match_set(wlan_references)  # Precompute SSID matches for linear scoring.
    wlan_known = wlan_references is not None  # Track whether orphan SSID scoring is possible.
    return [_build_hygiene_row(psk, wlan_match_set, wlan_known, now) for psk in psks]  # Score each PSK once.


def _build_hygiene_row(
    psk: PskInput, wlan_match_set: set[str], wlan_known: bool, now: datetime | None
) -> PskHygieneRow:
    """Build one safe report row."""
    remaining_days = days_remaining(psk.expire_time, now)  # Calculate the time finding input once.
    wlan_match = _wlan_match(psk.ssid, wlan_match_set, wlan_known)  # Calculate WLAN match state once.
    findings = _finding_labels(psk, remaining_days, wlan_match)  # Build stable labels without secrets.
    return PskHygieneRow(  # Return only report-safe fields.
        name=psk.name,
        ssid=psk.ssid,
        role=psk.role,
        vlan="" if psk.vlan is None else str(psk.vlan),
        usage="" if psk.usage is None else psk.usage,
        max_usage="" if psk.max_usage is None else psk.max_usage,
        expire_time="" if psk.expire_time is None else psk.expire_time,
        days_remaining="" if remaining_days is None else remaining_days,
        rotation_pending=psk.old_passphrase_present,
        old_passphrase_present=psk.old_passphrase_present,
        wlan_match=wlan_match,
        findings=",".join(findings),
    )


def _finding_labels(psk: PskInput, remaining_days: int | None, wlan_match: bool | str) -> tuple[str, ...]:
    """Return stable finding labels for one PSK."""
    finding_map = {  # Build each rule once so the stable order controls output.
        "expired": remaining_days is not None and remaining_days < 0,
        "expires_soon": remaining_days is not None and 0 <= remaining_days <= EXPIRING_SOON_DAYS,
        "uncapped_multi_use": _is_uncapped_multi_use(psk),
        "rotation_pending": psk.old_passphrase_present,
        "orphan_ssid": wlan_match is False,
    }
    return tuple(label for label in FINDING_ORDER if finding_map[label])  # Filter labels in contract order.


def _is_uncapped_multi_use(psk: PskInput) -> bool:
    """Return true when a PSK has no binding and no usage cap."""
    has_mac_binding = _has_value(psk.mac) or bool(psk.macs)  # Treat either MAC field as a binding.
    return not has_mac_binding and psk.max_usage is None  # Flag only when no binding and no cap exist.


def _wlan_match(ssid: str, wlan_match_set: set[str], wlan_known: bool) -> bool | str:
    """Return the WLAN match state for a normalized SSID."""
    if not wlan_known:  # The client could not supply a trustworthy WLAN scope.
        return "unknown"  # Avoid false orphan findings when scope is unavailable.
    return bool(ssid and ssid in wlan_match_set)  # Empty SSIDs cannot match an organization WLAN.


def _wlan_match_set(wlan_references: list[WlanReference] | None) -> set[str]:
    """Return normalized SSIDs for known WLAN references."""
    if wlan_references is None:  # Unknown WLAN scope must remain unknown.
        return set()  # Return an empty set because matching is disabled by the caller.
    return {reference.ssid for reference in wlan_references if reference.ssid}  # Ignore blank references.


def _org_wlan_references(wlans: list[dict[str, Any]]) -> list[WlanReference]:
    """Return references from organization WLAN records."""
    return [  # Build one reference per WLAN that has a usable SSID.
        WlanReference(ssid=ssid, source="org_wlan", source_name=_text(wlan.get("name")))
        for wlan in wlans
        if (ssid := normalize_ssid(wlan.get("ssid")))
    ]


def _template_wlan_references(templates: list[dict[str, Any]]) -> list[WlanReference]:
    """Return references from organization template WLAN records."""
    references: list[WlanReference] = []  # Accumulate template WLAN references in template order.
    for template in templates:  # Inspect each organization template once.
        references.extend(_references_for_template(template))  # Add each WLAN definition in this template.
    return references  # Return all template references for SSID matching.


def _references_for_template(template: dict[str, Any]) -> list[WlanReference]:
    """Return WLAN references for one template."""
    template_name = _text(template.get("name"))  # Use the template name as the source label.
    return [  # Build references only for WLAN definitions that expose an SSID.
        WlanReference(ssid=ssid, source="template", source_name=template_name)
        for wlan in _template_wlan_records(template)
        if (ssid := normalize_ssid(wlan.get("ssid")))
    ]


def _template_wlan_records(template: dict[str, Any]) -> list[dict[str, Any]]:
    """Return WLAN-like dictionaries from a template."""
    raw_wlans = template.get("wlans", [])  # Mist templates store WLAN definitions under wlans.
    if isinstance(raw_wlans, dict):  # Some API shapes use a map of WLAN names to definitions.
        return [value for value in raw_wlans.values() if isinstance(value, dict)]  # Keep only dict definitions.
    if isinstance(raw_wlans, list):  # Most API shapes use a list of WLAN definitions.
        return [value for value in raw_wlans if isinstance(value, dict)]  # Keep only dict definitions.
    return []  # Unknown template WLAN shapes are ignored safely.


def _optional_int(value: Any) -> int | None:
    """Return an integer value or None for absent input."""
    if value is None or value == "":  # Treat missing and empty values as absent.
        return None  # Preserve absence for cap and usage scoring.
    if isinstance(value, bool):  # Avoid treating booleans as integer counts.
        return None  # Preserve invalid count values as absent.
    try:  # Convert numeric strings from API rows when present.
        return int(value)  # Return the normalized integer count.
    except (TypeError, ValueError):  # Treat malformed API values as absent.
        return None  # Keep scoring deterministic for malformed counts.


def _optional_text(value: Any) -> str | None:
    """Return text or None for absent input."""
    if not _has_value(value):  # Empty values must remain absent.
        return None  # Preserve absence for output blanks and cap scoring.
    return str(value)  # Preserve visible non-empty values as strings.


def _text(value: Any) -> str:
    """Return text or an empty string for absent input."""
    return "" if value is None else str(value)  # Keep output values simple and non-null.


def _has_value(value: Any) -> bool:
    """Return true when a value is present."""
    if value is None:  # None means the API omitted the value.
        return False  # Treat None as absent for scoring.
    if isinstance(value, str):  # Strings need whitespace-aware absence handling.
        return bool(value.strip())  # Treat whitespace-only strings as absent.
    if isinstance(value, (list, tuple, set, dict)):  # Containers need empty-aware absence handling.
        return bool(value)  # Treat empty containers as absent.
    return True  # Treat other scalar values as present.


def _ensure_utc(value: datetime) -> datetime:
    """Return a timezone-aware UTC datetime."""
    if value.tzinfo is None:  # Naive API values need a timezone for safe comparison.
        return value.replace(tzinfo=UTC)  # Treat naive values as UTC.
    return value.astimezone(UTC)  # Normalize aware values to UTC.
