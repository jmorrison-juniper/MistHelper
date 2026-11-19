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
    has_support: bool | None = None  # Preserve JSI support evidence from live payloads.
    claimed: bool | None = None  # Preserve the live claimed state.
    device_name: str | None = None  # Preserve the live inventory name.
    org_id: str | None = None  # Preserve the source organization.
    master: bool | None = None  # Preserve master-device evidence.


@dataclass(frozen=True)
class OrganizationScope:
    """Identify one direct or MSP organization that the report can read."""

    org_id: str  # Scope organization-specific API calls.
    org_name: str  # Display the organization name in reports.
    msp_id: str | None = None  # Attribute MSP-discovered organizations.
    source: str = "direct"  # Name direct, MSP, or configured origin.
    request_status: str = "success"  # Preserve discovery or organization read status.
    error: str | None = None  # Explain a denied or failed request.

    def to_dict(self) -> dict[str, Any]:
        """Return a CSV-ready organization status mapping."""
        return asdict(self)  # Preserve field order for CSV export.


@dataclass(frozen=True)
class SubscriptionPurchaseRow:
    """One purchased or amended subscription record."""

    msp_id: str  # Identify the MSP source when available.
    org_id: str  # Identify the organization source.
    org_name: str  # Display the organization name.
    record_id: str  # Name the stable source record or Missing.
    subscription_id: str  # Name the source subscription or Missing.
    order_id: str  # Name the source order or Missing.
    subscription_type: str  # Name the subscription type.
    quantity: int | str  # Preserve purchased quantity or Missing.
    remaining_quantity: int | str  # Preserve remaining quantity or Missing.
    start_date: str  # Preserve the normalized purchase start date.
    end_date: str  # Preserve the normalized subscription end date.
    created_date: str  # Preserve the normalized purchase creation date.
    deal_period: str  # Mark original-deal or post-original-deal.
    source: str  # Name organization-summary or MSP-license evidence.

    def to_dict(self) -> dict[str, Any]:
        """Return a CSV-ready purchase mapping."""
        return asdict(self)  # Preserve field order for CSV export.


@dataclass(frozen=True)
class SubscriptionBalanceRow:
    """One purchased and used subscription balance."""

    msp_id: str  # Identify the MSP source when available.
    org_id: str  # Identify the organization source.
    org_name: str  # Display the organization name.
    subscription_type: str  # Name the subscription type.
    purchased_quantity: int | str  # Preserve purchased quantity or Missing.
    entitled_quantity: int | str  # Preserve entitlement or Missing.
    in_use_quantity: int | str  # Preserve in-use quantity or Missing.
    unused_entitlement: int | str  # Preserve entitlement minus in-use.
    over_entitlement: int | str  # Preserve in-use above entitlement.
    status: str  # Name Active, Expired, Exceeded, Inactive, or Missing.
    start_date: str  # Preserve earliest valid purchase start date.
    end_date: str  # Preserve latest valid end date.
    days_remaining: int | str  # Preserve remaining days or Missing.
    band: str  # Preserve the expiry band or Missing.

    def to_dict(self) -> dict[str, Any]:
        """Return a CSV-ready balance mapping."""
        return asdict(self)  # Preserve field order for CSV export.


@dataclass(frozen=True)
class StockInventoryRow:
    """One unassigned inventory device that may need a license."""

    msp_id: str  # Identify the MSP source when available.
    org_id: str  # Identify the organization source.
    org_name: str  # Display the organization name.
    serial: str  # Preserve serial or Missing.
    mac: str  # Preserve MAC or Missing.
    model: str  # Preserve model or Missing.
    name: str  # Preserve inventory name or Missing.
    device_type: str  # Name ap, switch, gateway, mxedge, router, or other.
    deployment_status: str  # Mark stock rather than assigned.
    license_review_required: str  # Mark yes or unknown.
    jsi_match_status: str  # Mark matched, no-match, unavailable, or missing.
    contract_status: str  # Preserve JSI status or Missing.
    contract_end_date: str  # Preserve available JSI date or Missing.

    def to_dict(self) -> dict[str, Any]:
        """Return a CSV-ready stock mapping."""
        return asdict(self)  # Preserve field order for CSV export.


@dataclass(frozen=True)
class ContractEvidenceRow:
    """One JSI contract evidence record."""

    msp_id: str  # Identify the MSP source when available.
    org_id: str  # Identify the organization source.
    org_name: str  # Display the organization name.
    serial: str  # Preserve serial or Missing.
    model: str  # Preserve model or Missing.
    status: str  # Preserve JSI status or Missing.
    has_support: bool | str  # Preserve support evidence or Missing.
    claimed: bool | str  # Preserve claim evidence or Missing.
    contract_end_date: str  # Preserve available contract date or Missing.
    request_status: str  # Name success, partial, failed, or unavailable.

    def to_dict(self) -> dict[str, Any]:
        """Return a CSV-ready contract evidence mapping."""
        return asdict(self)  # Preserve field order for CSV export.


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
        except OSError, OverflowError, ValueError:  # Invalid timestamps must not stop the report.
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


class CrossOrgSubscriptionInventoryModel:
    """Score cross-organization subscription and stock evidence."""

    @staticmethod
    def _whole_count(value: Any) -> int | str:
        """Return a non-negative whole count or the missing marker."""
        if type(value) is int and value >= 0:  # Accept only whole integer counts.
            return value  # Return the source count.
        if isinstance(value, str) and value.isdigit():  # Accept numeric strings from exports.
            return int(value)  # Normalize the numeric text.
        return MISSING_VALUE  # Hide neither malformed nor missing counts.

    @staticmethod
    def _text(value: Any) -> str:
        """Return visible text or the missing marker."""
        if value is None:  # A null source value is missing.
            return MISSING_VALUE  # Return the shared missing marker.
        text = str(value).strip()  # Normalize source whitespace.
        return text if text else MISSING_VALUE  # Return only visible text.

    @staticmethod
    def _deal_period(start_date: date | None, created_date: date | None) -> str:
        """Classify purchase evidence against the 2023-12-31 deal boundary."""
        purchase_date = start_date or created_date  # Start date takes precedence over created date.
        if purchase_date is None:  # No reliable purchase date exists.
            return MISSING_VALUE  # Keep the period missing.
        boundary = date(2023, 12, 31)  # Preserve the customer-provided deal boundary.
        return "in-or-before-original-deal" if purchase_date <= boundary else "post-original-deal"

    @staticmethod
    def _inventory_type(record: dict[str, Any]) -> str:
        """Normalize a live inventory type for the stock report."""
        source_type = str(record.get("type") or "").strip().lower()  # Normalize source type text.
        model = str(record.get("model") or "").strip().upper()  # Detect SSR models under gateway type.
        if source_type == "ap":  # AP inventory uses the AP subscription category.
            return "ap"  # Return AP type.
        if source_type == "switch":  # Switch inventory uses switch subscriptions.
            return "switch"  # Return switch type.
        if source_type == "gateway" or model.startswith("SSR"):  # Gateway and SSR share WAN or SSR licensing.
            return "gateway"  # Return gateway type for gateway and SSR rows.
        if source_type == "mxedge":  # Mist Edge has its own inventory type.
            return "mxedge"  # Return Mist Edge type.
        if source_type == "router":  # Router assets need separate inventory review.
            return "router"  # Return router type.
        return source_type or "other"  # Preserve unknown source types or the other bucket.

    @staticmethod
    def build_purchase_rows(
        organization: OrganizationScope,
        license_records: list[dict[str, Any]],
        report_date: date,
    ) -> list[SubscriptionPurchaseRow]:
        """Build one purchase row for each distinct subscription record."""
        logger.info("Building cross-org purchase rows for %s", organization.org_id)  # Log before scoring.
        rows: list[SubscriptionPurchaseRow] = []  # Accumulate purchase evidence.
        seen: set[tuple[str, str, str, str]] = set()  # Deduplicate stable source records.
        for record in license_records:  # Walk every source license record.
            if not isinstance(record, dict):  # Skip malformed records.
                continue  # Keep only mapping evidence.
            subscription_type = CrossOrgSubscriptionInventoryModel._text(record.get("type"))  # Normalize type.
            record_id = CrossOrgSubscriptionInventoryModel._text(record.get("id"))  # Normalize record ID.
            subscription_id = CrossOrgSubscriptionInventoryModel._text(record.get("subscription_id"))  # Normalize.
            order_id = CrossOrgSubscriptionInventoryModel._text(record.get("order_id"))  # Normalize.
            key = (record_id, subscription_id, order_id, subscription_type)  # Build stable duplicate key.
            if key in seen:  # Skip a repeated source record.
                continue  # Keep one row per source record.
            seen.add(key)  # Remember this source record.
            start_date = SubscriptionExpiryModel.normalize_date(record.get("start_time"))  # Normalize start.
            end_date = SubscriptionExpiryModel.normalize_date(record.get("end_time"))  # Normalize end.
            created_date = SubscriptionExpiryModel.normalize_date(record.get("created_time"))  # Normalize created.
            rows.append(
                SubscriptionPurchaseRow(
                    msp_id=organization.msp_id or MISSING_VALUE,
                    org_id=organization.org_id,
                    org_name=organization.org_name,
                    record_id=record_id,
                    subscription_id=subscription_id,
                    order_id=order_id,
                    subscription_type=subscription_type,
                    quantity=CrossOrgSubscriptionInventoryModel._whole_count(record.get("quantity")),
                    remaining_quantity=CrossOrgSubscriptionInventoryModel._whole_count(
                        record.get("remaining_quantity")
                    ),
                    start_date=SubscriptionExpiryModel._date_text(start_date),
                    end_date=SubscriptionExpiryModel._date_text(end_date),
                    created_date=SubscriptionExpiryModel._date_text(created_date),
                    deal_period=CrossOrgSubscriptionInventoryModel._deal_period(start_date, created_date),
                    source="organization-summary",
                )
            )  # Build one purchase row.
        logger.debug("Built %d cross-org purchase rows", len(rows))  # Log purchase count.
        return sorted(rows, key=lambda row: (row.subscription_type, row.start_date, row.record_id))

    @staticmethod
    def build_subscription_balances(
        organization: OrganizationScope,
        summary: LicenseSummarySource,
        usages: list[LicenseUsageSource],
        report_date: date,
    ) -> list[SubscriptionBalanceRow]:
        """Build one purchased and used balance row for each subscription type."""
        usage_by_type: dict[str, int] = {}  # Accumulate usage across all sites.
        for usage in usages:  # Walk each site usage row.
            for subscription_type, usage_value in usage.usages.items():  # Walk each usage map.
                if type(usage_value) is int and usage_value >= 0:  # Accept only whole usage counts.
                    normalized_type = str(subscription_type).upper()  # Normalize the source type.
                    usage_by_type[normalized_type] = usage_by_type.get(normalized_type, 0) + usage_value
        subscription_types = set(summary.entitled) | set(usage_by_type)  # Union entitlement and usage.
        subscription_types.update(
            str(record.get("type")).upper()
            for record in summary.licenses
            if isinstance(record, dict) and record.get("type")
        )  # Add dated purchase types.
        rows: list[SubscriptionBalanceRow] = []  # Accumulate balance rows.
        for subscription_type in sorted(subscription_types):  # Produce stable output.
            license_rows = [
                record
                for record in summary.licenses
                if isinstance(record, dict) and str(record.get("type") or "").upper() == subscription_type
            ]  # Match purchase records.
            purchased_values = [
                CrossOrgSubscriptionInventoryModel._whole_count(record.get("quantity")) for record in license_rows
            ]  # Normalize purchase quantities.
            purchased_quantity = (
                sum(value for value in purchased_values if isinstance(value, int))
                if any(isinstance(value, int) for value in purchased_values)
                else MISSING_VALUE
            )  # Sum valid values or keep Missing.
            entitled_quantity = CrossOrgSubscriptionInventoryModel._whole_count(
                summary.entitled.get(subscription_type)
            )  # Normalize entitlement.
            in_use_quantity = CrossOrgSubscriptionInventoryModel._whole_count(
                usage_by_type.get(subscription_type)
            )  # Normalize usage.
            unused = (
                max(entitled_quantity - in_use_quantity, 0)
                if isinstance(entitled_quantity, int) and isinstance(in_use_quantity, int)
                else MISSING_VALUE
            )  # Calculate unused entitlement.
            over = (
                max(in_use_quantity - entitled_quantity, 0)
                if isinstance(entitled_quantity, int) and isinstance(in_use_quantity, int)
                else MISSING_VALUE
            )  # Calculate over entitlement.
            end_date = SubscriptionExpiryModel._subscription_end_date(license_rows)  # Reuse date logic.
            raw_days = (end_date - report_date).days if end_date else MISSING_VALUE  # Calculate days.
            days_remaining = max(raw_days, 0) if isinstance(raw_days, int) else MISSING_VALUE  # Clamp expired.
            status = SubscriptionExpiryModel._subscription_status(
                license_rows, entitled_quantity, in_use_quantity, raw_days
            )  # Reuse status logic.
            band = SubscriptionExpiryModel._subscription_band(raw_days)  # Reuse band logic.
            start_dates = [
                SubscriptionExpiryModel.normalize_date(record.get("start_time")) for record in license_rows
            ]  # Parse purchase starts.
            valid_starts = [value for value in start_dates if value is not None]  # Keep valid starts.
            start_date = min(valid_starts) if valid_starts else None  # Earliest purchase start.
            rows.append(
                SubscriptionBalanceRow(
                    msp_id=organization.msp_id or MISSING_VALUE,
                    org_id=organization.org_id,
                    org_name=organization.org_name,
                    subscription_type=subscription_type,
                    purchased_quantity=purchased_quantity,
                    entitled_quantity=entitled_quantity,
                    in_use_quantity=in_use_quantity,
                    unused_entitlement=unused,
                    over_entitlement=over,
                    status=status,
                    start_date=SubscriptionExpiryModel._date_text(start_date),
                    end_date=SubscriptionExpiryModel._date_text(end_date),
                    days_remaining=days_remaining,
                    band=band,
                )
            )  # Build one balance row.
        logger.debug("Built %d cross-org balance rows", len(rows))  # Log balance count.
        return rows  # Return stable subscription balances.

    @staticmethod
    def build_stock_rows(
        organization: OrganizationScope,
        inventory: list[dict[str, Any]],
        jsi: list[JsiContractSource] | None,
    ) -> list[StockInventoryRow]:
        """Build one stock row for each unassigned inventory asset."""
        logger.info("Building stock rows for %s", organization.org_id)  # Log before stock scoring.
        jsi_by_serial = (
            {source.serial: source for source in jsi if isinstance(source, JsiContractSource) and source.serial}
            if jsi is not None
            else {}
        )  # Index JSI evidence by serial.
        rows: list[StockInventoryRow] = []  # Accumulate stock evidence.
        seen: set[tuple[str, str, str]] = set()  # Deduplicate inventory records.
        for record in inventory:  # Walk every live inventory record.
            if not isinstance(record, dict) or record.get("site_id"):  # Assigned devices stay out of stock.
                continue  # Skip assigned inventory.
            serial = CrossOrgSubscriptionInventoryModel._text(record.get("serial"))  # Normalize serial.
            mac = CrossOrgSubscriptionInventoryModel._text(record.get("mac"))  # Normalize MAC.
            model = CrossOrgSubscriptionInventoryModel._text(record.get("model"))  # Normalize model.
            key = (serial, mac, model)  # Build a visible duplicate key.
            if key in seen:  # Skip repeated stock records.
                continue  # Keep one row per inventory asset.
            seen.add(key)  # Remember this stock asset.
            jsi_match = jsi_by_serial.get(serial if serial != MISSING_VALUE else "")  # Find serial evidence.
            match_status = (
                "unavailable" if jsi is None else "matched" if jsi_match is not None else "no-match"
            )  # Score JSI evidence availability.
            contract_status = CrossOrgSubscriptionInventoryModel._text(
                jsi_match.status if jsi_match is not None else MISSING_VALUE
            )  # Preserve JSI status.
            if jsi_match is not None and jsi_match.has_support is True and contract_status == MISSING_VALUE:
                contract_status = "Active"  # has_support is evidence of active support.
            contract_end_date = (
                SubscriptionExpiryModel._date_text(SubscriptionExpiryModel._contract_end_date(jsi_match))
                if jsi_match is not None
                else MISSING_VALUE
            )  # Preserve only a valid JSI date.
            rows.append(
                StockInventoryRow(
                    msp_id=organization.msp_id or MISSING_VALUE,
                    org_id=organization.org_id,
                    org_name=organization.org_name,
                    serial=serial,
                    mac=mac,
                    model=model,
                    name=CrossOrgSubscriptionInventoryModel._text(record.get("name")),
                    device_type=CrossOrgSubscriptionInventoryModel._inventory_type(record),
                    deployment_status="stock",
                    license_review_required="yes",
                    jsi_match_status=match_status,
                    contract_status=contract_status,
                    contract_end_date=contract_end_date,
                )
            )  # Build one stock row.
        logger.debug("Built %d cross-org stock rows", len(rows))  # Log stock count.
        return sorted(rows, key=lambda row: (row.device_type, row.model, row.serial))

    @staticmethod
    def build_contract_rows(
        organization: OrganizationScope,
        jsi: list[JsiContractSource] | None,
    ) -> list[ContractEvidenceRow]:
        """Build one contract evidence row for each JSI device."""
        if jsi is None:  # JSI access is unavailable.
            logger.warning("JSI contract evidence unavailable for %s", organization.org_id)  # Log unavailable.
            return []  # No false contract evidence.
        rows: list[ContractEvidenceRow] = []  # Accumulate JSI evidence.
        seen: set[str] = set()  # Deduplicate JSI records by serial.
        for source in jsi:  # Walk JSI evidence.
            serial = CrossOrgSubscriptionInventoryModel._text(source.serial)  # Normalize serial.
            key = serial  # Use serial as the evidence identity.
            if key in seen:  # Skip a repeated JSI serial.
                continue  # Keep one evidence row.
            seen.add(key)  # Remember this serial.
            rows.append(
                ContractEvidenceRow(
                    msp_id=organization.msp_id or MISSING_VALUE,
                    org_id=organization.org_id,
                    org_name=organization.org_name,
                    serial=serial,
                    model=CrossOrgSubscriptionInventoryModel._text(source.model),
                    status=CrossOrgSubscriptionInventoryModel._text(source.status),
                    has_support=source.has_support if source.has_support is not None else MISSING_VALUE,
                    claimed=source.claimed if source.claimed is not None else MISSING_VALUE,
                    contract_end_date=SubscriptionExpiryModel._date_text(
                        SubscriptionExpiryModel._contract_end_date(source)
                    ),
                    request_status="success",
                )
            )  # Build one contract evidence row.
        logger.debug("Built %d contract evidence rows", len(rows))  # Log contract count.
        return sorted(rows, key=lambda row: row.serial)
