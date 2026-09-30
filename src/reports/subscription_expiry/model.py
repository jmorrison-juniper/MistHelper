"""Scoring model for the subscription and contract expiry report."""

from __future__ import annotations  # Keep annotations import-safe on Python 3.13.

import logging  # Record scoring actions for operator traceability.
from dataclasses import asdict, dataclass, field  # Define compact report records with explicit columns.
from datetime import UTC, date, datetime  # Use UTC dates for reproducible report scoring.
from typing import Any  # Type raw Mist SDK fields without importing the SDK.

logger = logging.getLogger(__name__)  # Give this module a stable logger name.

MISSING_VALUE = "Missing"  # Use one visible marker when source data omits a report value.
STATUS_ACTIVE = "Active"  # Match Mist subscription status text.
STATUS_EXPIRED = "Expired"  # Match Mist subscription status text.
STATUS_EXCEEDED = "Exceeded"  # Match Mist subscription status text.
STATUS_INACTIVE = "Inactive"  # Match Mist subscription status text.
STATE_SUPPORTED = "Supported"  # Match Mist contract state text.
STATE_UNSUPPORTED = "Unsupported"  # Match Mist contract state text.
CONTRACT_STATUS_ACTIVE = "Active"  # Match Mist contract status text.
CONTRACT_STATUS_DECLINED = "Declined"  # Match Mist contract status text.
CONTRACT_STATUS_EOS = "EOS"  # Match Mist contract status text.
CONTRACT_STATUS_SERVICE_AVAILABLE = "Service Available"  # Match Mist contract status text.
SUBSCRIPTION_BAND_EXPIRED = "expired"  # Match the requested CSV band text.
SUBSCRIPTION_BAND_30 = "0-30 days"  # Match the requested CSV band text.
SUBSCRIPTION_BAND_90 = "31-90 days"  # Match the requested CSV band text.
SUBSCRIPTION_BAND_LONG = "more than 90 days"  # Match the requested CSV band text.
CONTRACT_BUCKET_EXPIRED = "Expired"  # Match the requested CSV bucket text.
CONTRACT_BUCKET_3_MONTHS = "0-3 months"  # Match the requested CSV bucket text.
CONTRACT_BUCKET_12_MONTHS = "0-12 months"  # Match the requested CSV bucket text.
CONTRACT_BUCKET_LONG = "more than 12 months"  # Match the requested CSV bucket text.
CONTRACT_RECORD_ABSENT_NOTE = "contract record absent"  # Explain unsupported rows with no contract evidence.
SUBSCRIPTION_BANDS = (  # Keep summary order stable for the console.
    SUBSCRIPTION_BAND_EXPIRED,
    SUBSCRIPTION_BAND_30,
    SUBSCRIPTION_BAND_90,
    SUBSCRIPTION_BAND_LONG,
)
CONTRACT_BUCKETS = (  # Keep summary order stable for the console.
    CONTRACT_BUCKET_EXPIRED,
    CONTRACT_BUCKET_3_MONTHS,
    CONTRACT_BUCKET_12_MONTHS,
    CONTRACT_BUCKET_LONG,
)


@dataclass(frozen=True)
class ReportContext:
    """Identify one report run."""

    org_id: str  # Scope every SDK call to one organization.
    report_date: date = field(default_factory=lambda: datetime.now(UTC).date())  # Score with the UTC run date.


@dataclass(frozen=True)
class LicenseSummarySource:
    """Normalized source data from getOrgLicensesSummary."""

    entitled: dict[str, int] = field(default_factory=dict)  # Store entitlement by subscription type.
    licenses: list[dict[str, Any]] = field(default_factory=list)  # Store raw license rows for dates and statuses.
    summary: dict[str, Any] = field(default_factory=dict)  # Preserve source summary values for future use.


@dataclass(frozen=True)
class LicenseUsageSource:
    """Normalized source data from getOrgLicensesBySite."""

    site_id: str | None = None  # Identify the usage source site when Mist sends it.
    num_devices: int | None = None  # Preserve the site device count when Mist sends it.
    usages: dict[str, int] = field(default_factory=dict)  # Store usage by subscription type.
    fully_loaded: dict[str, Any] = field(default_factory=dict)  # Preserve raw fully-loaded source fields.


@dataclass(frozen=True)
class JsiContractSource:
    """Normalized source data from searchOrgJsiAssetsAndContracts."""

    serial: str | None = None  # Identify the device contract row.
    model: str | None = None  # Show the device model when the source has it.
    status: str | None = None  # Preserve Mist contract status when the source sends it.
    end_date: int | str | None = None  # Preserve explicit contract end date when the source sends it.
    sku: str | None = None  # Preserve the source SKU for duplicate tie breaks.
    type: str | None = None  # Preserve the source device type for duplicate tie breaks.
    warranty_type: str | None = None  # Map Mist contract status to support state.
    eol_time: int | str | None = None  # Read an end date when end-of-life is the only source date.
    eos_time: int | str | None = None  # Prefer end-of-support as the contract end date.


@dataclass(frozen=True)
class SubscriptionExpiryRow:
    """One scored row for SubscriptionExpiry.csv."""

    subscription_type: str  # Name the subscription type that this row scores.
    entitled: int | str  # Show entitlement or the missing value marker.
    usage: int | str  # Show usage or the missing value marker.
    status: str  # Show Active, Expired, Exceeded, or Inactive.
    end_date: str  # Show an ISO date or the missing value marker.
    days_remaining: int | str  # Show remaining days or the missing value marker.
    band: str  # Show the dated risk band or the missing value marker.

    def to_dict(self) -> dict[str, Any]:
        """Return a CSV-ready mapping."""
        return asdict(self)  # Preserve dataclass field order for export readability.


@dataclass(frozen=True)
class ContractExpiryRow:
    """One scored row for ContractExpiry.csv."""

    serial: str  # Show the device serial or the missing value marker.
    model: str  # Show the device model or the missing value marker.
    contract_status: str  # Show the Mist contract status or a clear fallback.
    contract_state: str  # Show Supported or Unsupported.
    end_date: str  # Show an ISO date or the missing value marker.
    bucket: str  # Show the expiry bucket or the missing value marker.
    note: str = ""  # Explain special cases without hiding the report row.

    def to_dict(self) -> dict[str, Any]:
        """Return a CSV-ready mapping."""
        return asdict(self)  # Preserve dataclass field order for export readability.


@dataclass(frozen=True)
class ConsoleSummary:
    """Counts printed after the CSV exports."""

    subscription_band_counts: dict[str, int]  # Count rows for every subscription band.
    contract_bucket_counts: dict[str, int]  # Count rows for every contract bucket.


class SubscriptionExpiryModel:
    """Score subscription and contract source rows into report rows."""

    @staticmethod
    def normalize_date(value: Any) -> date | None:
        """Convert a Mist date value to a date, or None when it is absent or invalid."""
        logger.info("Normalizing a source date value")  # Log before parsing a source date.
        parsed_date = SubscriptionExpiryModel._parse_date_value(value)  # Parse supported source date shapes.
        logger.debug("Normalized date present: %s", parsed_date is not None)  # Log only presence, not raw data.
        return parsed_date  # Return the normalized date to the scoring caller.

    @staticmethod
    def score_subscriptions(
        context: ReportContext,
        summary: LicenseSummarySource,
        usages: list[LicenseUsageSource],
    ) -> list[SubscriptionExpiryRow]:
        """Build one subscription row for each subscription type."""
        logger.info("Aggregating license usage for subscription scoring")  # Log before usage aggregation.
        usage_by_type = SubscriptionExpiryModel._aggregate_usage(usages)  # Sum usage across all sites.
        logger.debug("Aggregated usage for %d subscription types", len(usage_by_type))  # Log usage type count.
        logger.info("Collecting subscription types for subscription scoring")  # Log before key collection.
        subscription_types = SubscriptionExpiryModel._subscription_types(summary, usage_by_type)  # Find row keys.
        logger.debug("Collected %d subscription types", len(subscription_types))  # Log output row count.
        return [
            SubscriptionExpiryModel._build_subscription_row(context, summary, usage_by_type, subscription_type)
            for subscription_type in subscription_types
        ]  # Score rows in stable subscription-type order.

    @staticmethod
    def score_contracts(context: ReportContext, contracts: list[JsiContractSource]) -> list[ContractExpiryRow]:
        """Build one contract row for each device."""
        logger.info("Collecting unique devices for contract scoring")  # Log before duplicate reduction.
        unique_contracts = SubscriptionExpiryModel._deduplicate_contracts(contracts)  # Keep one row per serial.
        logger.debug("Collected %d unique contract devices", len(unique_contracts))  # Log unique row count.
        return [
            SubscriptionExpiryModel._build_contract_row(context, contract_source)
            for contract_source in unique_contracts
        ]  # Score rows in stable device order.

    @staticmethod
    def build_summary(
        subscription_rows: list[SubscriptionExpiryRow],
        contract_rows: list[ContractExpiryRow],
    ) -> ConsoleSummary:
        """Count every subscription band and contract bucket."""
        logger.info("Building console summary counts")  # Log before summary count creation.
        subscription_counts = {band: 0 for band in SUBSCRIPTION_BANDS}  # Seed every subscription band with zero.
        contract_counts = {bucket: 0 for bucket in CONTRACT_BUCKETS}  # Seed every contract bucket with zero.
        SubscriptionExpiryModel._count_subscription_bands(subscription_rows, subscription_counts)  # Count bands.
        SubscriptionExpiryModel._count_contract_buckets(contract_rows, contract_counts)  # Count buckets.
        logger.debug("Built summary for %d subscription rows", len(subscription_rows))  # Log subscription count.
        logger.debug("Built summary for %d contract rows", len(contract_rows))  # Log contract count.
        return ConsoleSummary(subscription_counts, contract_counts)  # Return the complete summary.

    @staticmethod
    def _parse_date_value(value: Any) -> date | None:
        """Parse supported source date shapes."""
        if value in (None, "", MISSING_VALUE):  # Treat absent values as missing dates.
            return None  # Missing values cannot produce a date.
        if isinstance(value, datetime):  # Preserve already parsed datetimes from tests or SDK transforms.
            return value.astimezone(UTC).date() if value.tzinfo else value.date()  # Normalize aware values to UTC.
        if isinstance(value, date):  # Preserve already parsed date values.
            return value  # Return the date directly.
        if isinstance(value, int | float):  # Mist can send Unix timestamps.
            return SubscriptionExpiryModel._parse_unix_timestamp(value)  # Normalize seconds or milliseconds.
        if isinstance(value, str):  # Mist can send ISO strings or numeric strings.
            return SubscriptionExpiryModel._parse_date_string(value)  # Parse the string form.
        return None  # Unsupported value types are invalid dates.

    @staticmethod
    def _parse_unix_timestamp(value: int | float) -> date | None:
        """Parse a Unix timestamp in seconds or milliseconds."""
        timestamp = value / 1000 if value > 10_000_000_000 else value  # Detect common millisecond timestamps.
        try:
            return datetime.fromtimestamp(timestamp, UTC).date()  # Convert to a UTC date for report scoring.
        except (OSError, OverflowError, ValueError):  # Invalid timestamps must not stop the report.
            return None  # Return missing date for invalid timestamp input.

    @staticmethod
    def _parse_date_string(value: str) -> date | None:
        """Parse ISO date strings and numeric timestamp strings."""
        cleaned_value = value.strip()  # Remove whitespace that can surround API export values.
        if not cleaned_value:  # Empty strings are missing dates.
            return None  # Return missing date for empty strings.
        if cleaned_value.isdigit():  # Numeric strings are timestamps from some exports.
            return SubscriptionExpiryModel._parse_unix_timestamp(int(cleaned_value))  # Parse timestamp strings.
        try:
            return datetime.fromisoformat(cleaned_value.replace("Z", "+00:00")).date()  # Parse ISO date/time text.
        except ValueError:  # Invalid text must remain visible as a missing date.
            return None  # Return missing date for invalid strings.

    @staticmethod
    def _aggregate_usage(usages: list[LicenseUsageSource]) -> dict[str, int]:
        """Sum usage values by subscription type."""
        usage_by_type: dict[str, int] = {}  # Accumulate usage by subscription type.
        for usage_source in usages:  # Walk each site usage row.
            for subscription_type, usage_value in usage_source.usages.items():  # Walk each source usage value.
                usage_by_type[subscription_type] = usage_by_type.get(subscription_type, 0) + int(
                    usage_value or 0
                )  # Sum.
        return usage_by_type  # Return the aggregated usage map.

    @staticmethod
    def _subscription_types(summary: LicenseSummarySource, usage_by_type: dict[str, int]) -> list[str]:
        """Return every subscription type that must appear in the report."""
        subscription_types = set(summary.entitled) | set(usage_by_type)  # Start with entitlement and usage keys.
        subscription_types.update(str(row.get("type")) for row in summary.licenses if row.get("type"))  # Add licenses.
        return sorted(subscription_types)  # Keep report order stable for reviews and tests.

    @staticmethod
    def _build_subscription_row(
        context: ReportContext,
        summary: LicenseSummarySource,
        usage_by_type: dict[str, int],
        subscription_type: str,
    ) -> SubscriptionExpiryRow:
        """Score one subscription type."""
        license_rows = [row for row in summary.licenses if row.get("type") == subscription_type]  # Match source rows.
        end_date = SubscriptionExpiryModel._subscription_end_date(license_rows)  # Choose the best end date.
        raw_days = (end_date - context.report_date).days if end_date else MISSING_VALUE  # Compute calendar distance.
        days_remaining = max(0, raw_days) if isinstance(raw_days, int) else MISSING_VALUE  # Never export negatives.
        entitled = summary.entitled.get(subscription_type, MISSING_VALUE)  # Keep missing entitlement visible.
        usage = usage_by_type.get(subscription_type, MISSING_VALUE)  # Keep missing usage visible.
        status = SubscriptionExpiryModel._subscription_status(license_rows, entitled, usage, raw_days)  # Score state.
        band = SubscriptionExpiryModel._subscription_band(raw_days)  # Score the dated band before clamping days.
        return SubscriptionExpiryRow(
            subscription_type,
            entitled,
            usage,
            status,
            SubscriptionExpiryModel._date_text(end_date),
            days_remaining,
            band,
        )  # Build row.

    @staticmethod
    def _subscription_end_date(license_rows: list[dict[str, Any]]) -> date | None:
        """Choose the latest subscription end date for one type."""
        dates = [SubscriptionExpiryModel.normalize_date(row.get("end_time")) for row in license_rows]  # Parse dates.
        valid_dates = [parsed_date for parsed_date in dates if parsed_date is not None]  # Ignore invalid dates.
        return max(valid_dates) if valid_dates else None  # Latest end date represents remaining coverage.

    @staticmethod
    def _subscription_status(
        license_rows: list[dict[str, Any]],
        entitled: int | str,
        usage: int | str,
        days_remaining: int | str,
    ) -> str:
        """Score the subscription status."""
        source_statuses = {str(row.get("status")) for row in license_rows if row.get("status")}  # Preserve states.
        if isinstance(entitled, int) and isinstance(usage, int) and usage > entitled:  # Over-use outranks date.
            return STATUS_EXCEEDED  # Entitlement risk must remain visible even before expiry.
        if STATUS_INACTIVE in source_statuses:  # Inactive subscriptions have no support.
            return STATUS_INACTIVE  # Preserve inactive source state.
        if isinstance(days_remaining, int) and days_remaining < 0:  # Past end date is expired.
            return STATUS_EXPIRED  # Mark expired subscriptions.
        if STATUS_EXPIRED in source_statuses:  # Preserve explicit expired source state.
            return STATUS_EXPIRED  # Source state is more direct than a missing date.
        return STATUS_ACTIVE  # Default remaining rows to active.

    @staticmethod
    def _subscription_band(days_remaining: int | str) -> str:
        """Score the subscription date band."""
        if not isinstance(days_remaining, int):  # Missing dates cannot get a dated band.
            return MISSING_VALUE  # Keep the missing date visible.
        if days_remaining < 0:  # Past dates are expired.
            return SUBSCRIPTION_BAND_EXPIRED  # Return expired band.
        if days_remaining <= 30:  # Today through 30 days is grace-period risk.
            return SUBSCRIPTION_BAND_30  # Return near-term band.
        if days_remaining <= 90:  # Days 31 through 90 are read-only risk.
            return SUBSCRIPTION_BAND_90  # Return medium-term band.
        return SUBSCRIPTION_BAND_LONG  # Later dates are long-term.

    @staticmethod
    def _deduplicate_contracts(contracts: list[JsiContractSource]) -> list[JsiContractSource]:
        """Keep one contract row per device identity."""
        by_identity: dict[str, JsiContractSource] = {}  # Map device identity to the selected source row.
        for contract_source in contracts:  # Walk each source contract row.
            key = contract_source.serial or f"{MISSING_VALUE}:{contract_source.model or MISSING_VALUE}"  # Pick key.
            by_identity.setdefault(key, contract_source)  # Keep the first row so output grain is one per device.
        return [by_identity[key] for key in sorted(by_identity)]  # Return stable device order.

    @staticmethod
    def _build_contract_row(context: ReportContext, contract_source: JsiContractSource) -> ContractExpiryRow:
        """Score one device contract row."""
        end_date = SubscriptionExpiryModel._contract_end_date(contract_source)  # Choose source contract date.
        absent = SubscriptionExpiryModel._contract_record_absent(contract_source, end_date)  # Detect no contract.
        status = SubscriptionExpiryModel._contract_status(contract_source, absent)  # Choose visible status.
        state = SubscriptionExpiryModel._contract_state(status, absent)  # Score support state.
        bucket = SubscriptionExpiryModel._contract_bucket(context.report_date, end_date, absent)  # Score bucket.
        note = CONTRACT_RECORD_ABSENT_NOTE if absent else ""  # Explain rows with no contract source data.
        return ContractExpiryRow(
            contract_source.serial or MISSING_VALUE,
            contract_source.model or MISSING_VALUE,
            status,
            state,
            SubscriptionExpiryModel._date_text(end_date),
            bucket,
            note,
        )  # Build row.

    @staticmethod
    def _contract_end_date(contract_source: JsiContractSource) -> date | None:
        """Choose an end-of-support or end-of-life date."""
        explicit_date = SubscriptionExpiryModel.normalize_date(contract_source.end_date)  # Prefer contract end date.
        eos_date = SubscriptionExpiryModel.normalize_date(contract_source.eos_time)  # Prefer end-of-support.
        eol_date = SubscriptionExpiryModel.normalize_date(contract_source.eol_time)  # Use end-of-life if needed.
        return explicit_date or eos_date or eol_date  # Return the first reliable contract date.

    @staticmethod
    def _contract_record_absent(contract_source: JsiContractSource, end_date: date | None) -> bool:
        """Return true when no contract evidence exists for a device."""
        return not contract_source.warranty_type and end_date is None  # Missing status and dates means no record.

    @staticmethod
    def _contract_status(contract_source: JsiContractSource, absent: bool) -> str:
        """Return the visible contract status."""
        if absent:  # A missing contract must be explicit for the operator.
            return STATE_UNSUPPORTED  # Use the same unsupported term that Mist uses.
        return contract_source.status or contract_source.warranty_type or STATE_UNSUPPORTED  # Preserve status source.

    @staticmethod
    def _contract_state(status: str, absent: bool) -> str:
        """Score supported or unsupported contract state."""
        if absent:  # A missing contract record cannot prove support.
            return STATE_UNSUPPORTED  # Mark the row unsupported.
        if status == CONTRACT_STATUS_ACTIVE:  # Active contracts are supported.
            return STATE_SUPPORTED  # Return supported state.
        return STATE_UNSUPPORTED  # Every other visible source status is unsupported.

    @staticmethod
    def _contract_bucket(report_date: date, end_date: date | None, absent: bool) -> str:
        """Score the contract expiry bucket."""
        if absent:  # A missing contract record is treated as expired risk by requirement.
            return CONTRACT_BUCKET_EXPIRED  # Return the highest-risk bucket.
        if end_date is None:  # Missing dates cannot get a dated bucket.
            return MISSING_VALUE  # Keep the missing date visible.
        days_remaining = (end_date - report_date).days  # Compute simple UTC calendar-day distance.
        if days_remaining < 0:  # Past end dates are expired.
            return CONTRACT_BUCKET_EXPIRED  # Return expired bucket.
        if days_remaining <= 92:  # Three calendar months can be 90 to 92 days.
            return CONTRACT_BUCKET_3_MONTHS  # Return near-term bucket.
        if days_remaining <= 366:  # Twelve calendar months can include a leap day.
            return CONTRACT_BUCKET_12_MONTHS  # Return annual bucket.
        return CONTRACT_BUCKET_LONG  # Later dates are long-term.

    @staticmethod
    def _date_text(value: date | None) -> str:
        """Return an ISO date string or the missing value marker."""
        return value.isoformat() if value else MISSING_VALUE  # Keep missing dates visible in CSV output.

    @staticmethod
    def _count_subscription_bands(rows: list[SubscriptionExpiryRow], counts: dict[str, int]) -> None:
        """Add subscription row counts into a seeded map."""
        for row in rows:  # Walk scored subscription rows.
            if row.band in counts:  # Count only dated bands.
                counts[row.band] += 1  # Increment the matching band count.

    @staticmethod
    def _count_contract_buckets(rows: list[ContractExpiryRow], counts: dict[str, int]) -> None:
        """Add contract row counts into a seeded map."""
        for row in rows:  # Walk scored contract rows.
            if row.bucket in counts:  # Count only dated buckets.
                counts[row.bucket] += 1  # Increment the matching bucket count.
