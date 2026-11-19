"""Tests for subscription and contract expiry scoring."""

from __future__ import annotations  # Keep annotations import-safe during test collection.

from datetime import date  # Build deterministic report dates.

from src.mist.intelligence.reports.subscription_expiry.model import (
    CONTRACT_RECORD_ABSENT_NOTE,
    MISSING_VALUE,
    ConsoleSummary,
    CrossOrgSubscriptionInventoryModel,
    JsiContractSource,
    LicenseSummarySource,
    LicenseUsageSource,
    OrganizationScope,
    ReportContext,
    SubscriptionExpiryModel,
)


def test_subscription_bands_days_and_status_values() -> None:
    """Subscription scoring covers every dated band and status."""
    context = ReportContext("org-1", date(2026, 1, 1))  # Use a fixed UTC report date.
    summary = LicenseSummarySource(
        entitled={"LONG": 10, "SOON": 10, "MID": 10, "OLD": 10, "OVER": 1, "OFF": 10},
        licenses=[
            {"type": "LONG", "end_time": "2026-04-15", "status": "Active"},
            {"type": "SOON", "end_time": "2026-01-31", "status": "Active"},
            {"type": "MID", "end_time": "2026-03-15", "status": "Active"},
            {"type": "OLD", "end_time": "2025-12-31", "status": "Active"},
            {"type": "OVER", "end_time": "2026-12-31", "status": "Active"},
            {"type": "OFF", "end_time": "2026-12-31", "status": "Inactive"},
        ],
    )  # Provide all source states in one deterministic fixture.
    usages = [LicenseUsageSource(usages={"LONG": 1, "SOON": 1, "MID": 1, "OLD": 1, "OVER": 2, "OFF": 1})]  # Usage.
    rows = {
        row.subscription_type: row for row in SubscriptionExpiryModel.score_subscriptions(context, summary, usages)
    }  # Score.
    assert rows["LONG"].band == "more than 90 days"  # Dates beyond 90 days use the long band.
    assert rows["SOON"].days_remaining == 30  # The boundary includes 30 days.
    assert rows["SOON"].band == "0-30 days"  # Dates through 30 days use the near band.
    assert rows["MID"].band == "31-90 days"  # Dates through 90 days use the medium band.
    assert rows["OLD"].status == "Expired"  # Past end dates are expired.
    assert rows["OLD"].days_remaining == 0  # Expired rows never export a negative day count.
    assert rows["OLD"].band == "expired"  # Past end dates use the expired band.
    assert rows["OVER"].status == "Exceeded"  # Usage above entitlement outranks a future date.
    assert rows["OFF"].status == "Inactive"  # Inactive source status must survive scoring.


def test_subscription_missing_empty_and_duplicate_inputs_remain_visible() -> None:
    """Missing subscription values stay visible and duplicate types collapse."""
    context = ReportContext("org-1", date(2026, 1, 1))  # Use a fixed UTC report date.
    empty_rows = SubscriptionExpiryModel.score_subscriptions(context, LicenseSummarySource(), [])  # Score no data.
    summary = LicenseSummarySource(
        entitled={"DUP": 5, "NO_USAGE": 3},
        licenses=[{"type": "DUP", "end_time": None}, {"type": "DUP", "end_time": "bad"}],
    )  # Duplicate type and missing dates exercise visible missing values.
    rows = SubscriptionExpiryModel.score_subscriptions(context, summary, [])  # Score the source rows.
    by_type = {row.subscription_type: row for row in rows}  # Index by subscription type for assertions.
    assert empty_rows == []  # Empty source data produces no subscription rows.
    assert len([row for row in rows if row.subscription_type == "DUP"]) == 1  # Duplicate type collapses.
    assert by_type["DUP"].end_date == MISSING_VALUE  # Missing or invalid date stays visible.
    assert by_type["DUP"].usage == MISSING_VALUE  # Missing usage stays visible.
    assert by_type["DUP"].band == MISSING_VALUE  # Missing end date has no dated band.
    assert by_type["NO_USAGE"].usage == MISSING_VALUE  # Entitlement-only rows still export.


def test_contract_buckets_status_state_and_missing_contract_note() -> None:
    """Contract scoring covers every bucket and unsupported missing contracts."""
    context = ReportContext("org-1", date(2026, 1, 1))  # Use a fixed UTC report date.
    contracts = [
        JsiContractSource(serial="A", model="AP", warranty_type="Active", eos_time="2025-12-31"),
        JsiContractSource(serial="B", model="AP", warranty_type="Active", eos_time="2026-03-31"),
        JsiContractSource(serial="C", model="AP", status="Declined", end_date="2026-06-01"),
        JsiContractSource(serial="D", model="AP", status="Active", end_date="2027-02-01"),
        JsiContractSource(serial="E", model="AP"),
    ]  # Provide all contract bucket and support cases.
    rows = {row.serial: row for row in SubscriptionExpiryModel.score_contracts(context, contracts)}  # Score contracts.
    assert rows["A"].bucket == "Expired"  # Past contract dates are expired.
    assert rows["B"].bucket == "0-3 months"  # Dates through three months use the first bucket.
    assert rows["C"].bucket == "0-12 months"  # Dates through twelve months use the second bucket.
    assert rows["D"].bucket == "more than 12 months"  # Later dates use the long bucket.
    assert rows["B"].contract_state == "Supported"  # Active contracts are supported.
    assert rows["C"].contract_state == "Unsupported"  # Declined contracts are unsupported.
    assert rows["E"].contract_state == "Unsupported"  # Missing contract records are unsupported.
    assert rows["E"].bucket == "Expired"  # Missing contract records are urgent renewal risk.
    assert rows["E"].note == CONTRACT_RECORD_ABSENT_NOTE  # The note explains the missing contract record.


def test_contract_missing_values_empty_data_and_duplicate_devices() -> None:
    """Missing contract identity values stay visible and duplicate devices collapse."""
    context = ReportContext("org-1", date(2026, 1, 1))  # Use a fixed UTC report date.
    empty_rows = SubscriptionExpiryModel.score_contracts(context, [])  # Score no contract data.
    contracts = [
        JsiContractSource(serial="A", model=None, warranty_type="Service Available", eos_time=None),
        JsiContractSource(serial="A", model="AP", warranty_type="Active", eos_time="2027-01-01"),
        JsiContractSource(serial=None, model=None, warranty_type="EOS", eol_time="bad"),
    ]  # Include duplicates and missing fields.
    rows = SubscriptionExpiryModel.score_contracts(context, contracts)  # Score the source rows.
    by_serial = {row.serial: row for row in rows}  # Index by serial for assertions.
    assert empty_rows == []  # Empty source data produces no contract rows.
    assert len([row for row in rows if row.serial == "A"]) == 1  # Duplicate serial collapses.
    assert by_serial["A"].model == MISSING_VALUE  # Missing model stays visible.
    assert by_serial[MISSING_VALUE].serial == MISSING_VALUE  # Missing serial stays visible.
    assert by_serial[MISSING_VALUE].bucket == MISSING_VALUE  # Invalid date without absent record has no bucket.


def test_summary_counts_defaults_and_counted_rows() -> None:
    """Summary counts include every band and bucket with zero defaults."""
    context = ReportContext("org-1", date(2026, 1, 1))  # Use a fixed UTC report date.
    subscription_rows = SubscriptionExpiryModel.score_subscriptions(
        context,
        LicenseSummarySource(
            entitled={"OLD": 1, "SOON": 1},
            licenses=[
                {"type": "OLD", "end_time": "2025-12-31"},
                {"type": "SOON", "end_time": "2026-01-02"},
            ],
        ),
        [LicenseUsageSource(usages={"OLD": 1, "SOON": 1})],
    )  # Build two subscription bands.
    contract_rows = SubscriptionExpiryModel.score_contracts(
        context,
        [JsiContractSource(serial="A", model="AP", warranty_type="Active", eos_time="2027-02-01")],
    )  # Build one contract bucket.
    summary = SubscriptionExpiryModel.build_summary(subscription_rows, contract_rows)  # Count scored rows.
    assert isinstance(summary, ConsoleSummary)  # The model returns the documented summary type.
    assert summary.subscription_band_counts["expired"] == 1  # Expired subscription row is counted.
    assert summary.subscription_band_counts["0-30 days"] == 1  # Near subscription row is counted.
    assert summary.subscription_band_counts["31-90 days"] == 0  # Missing bands keep zero default.
    assert summary.contract_bucket_counts["more than 12 months"] == 1  # Long contract row is counted.
    assert summary.contract_bucket_counts["Expired"] == 0  # Missing buckets keep zero default.


def test_cross_org_purchase_and_balance_reconcile() -> None:
    """Purchased, entitled, in-use, unused, and over-entitlement values stay separate."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        msp_id="msp-1",
        source="msp",
        request_status="success",
    )  # Build a synthetic MSP organization.
    summary = LicenseSummarySource(
        entitled={"SUB-SSR": 2},
        licenses=[
            {
                "id": "license-1",
                "type": "SUB-SSR",
                "quantity": 3,
                "remaining_quantity": 2,
                "start_time": "2024-01-31",
                "end_time": "2027-01-31",
                "created_time": "2024-01-30",
            }
        ],
    )  # Build a dated purchase and entitlement fixture.
    usages = [LicenseUsageSource(usages={"SUB-SSR": 1})]  # Build one in-use value.
    purchases = CrossOrgSubscriptionInventoryModel.build_purchase_rows(
        organization, summary.licenses, date(2026, 11, 19)
    )  # Score one purchase row.
    balances = CrossOrgSubscriptionInventoryModel.build_subscription_balances(
        organization, summary, usages, date(2026, 11, 19)
    )  # Score one balance row.
    assert purchases[0].deal_period == "post-original-deal"  # The 2024 start follows the 2023 deal.
    assert purchases[0].start_date == "2024-01-31"  # The purchase start survives normalization.
    assert purchases[0].end_date == "2027-01-31"  # The purchase end survives normalization.
    assert balances[0].purchased_quantity == 3  # Purchased quantity comes from the license record.
    assert balances[0].entitled_quantity == 2  # Entitlement comes from the summary map.
    assert balances[0].in_use_quantity == 1  # In-use quantity is the sum of usage rows.
    assert balances[0].unused_entitlement == 1  # Entitlement minus in-use stays visible.
    assert balances[0].over_entitlement == 0  # No over-entitlement exists in this fixture.


def test_cross_org_stock_and_jsi_join_keep_missing_evidence() -> None:
    """Unassigned stock appears once and JSI evidence stays serial-specific."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        source="direct",
        request_status="success",
    )  # Build a direct organization.
    inventory = [
        {"serial": "SSR1", "mac": "mac-1", "model": "SSR130", "type": "gateway", "name": "branch"},
        {"serial": "AP1", "mac": "mac-2", "model": "AP43", "type": "ap", "site_id": "site-1"},
    ]  # Include one stock record and one assigned record.
    jsi = [
        JsiContractSource(
            serial="OTHER",
            model="AP43",
            status="Active",
            has_support=True,
        )
    ]  # Include JSI evidence that does not match the stock serial.
    stock_rows = CrossOrgSubscriptionInventoryModel.build_stock_rows(organization, inventory, jsi)  # Build stock.
    contract_rows = CrossOrgSubscriptionInventoryModel.build_contract_rows(organization, jsi)  # Build evidence.
    assert len(stock_rows) == 1  # The assigned AP must not enter the stock view.
    assert stock_rows[0].serial == "SSR1"  # The SSR serial identifies the stock asset.
    assert stock_rows[0].model == "SSR130"  # The stock model remains visible.
    assert stock_rows[0].license_review_required == "yes"  # Stock requires a license review.
    assert stock_rows[0].jsi_match_status == "no-match"  # A different JSI serial is not a match.
    assert contract_rows[0].serial == "OTHER"  # Contract evidence keeps its own serial.
    assert contract_rows[0].contract_end_date == MISSING_VALUE  # Missing JSI date remains Missing.
