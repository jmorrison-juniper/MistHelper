"""Tests for subscription and contract expiry scoring."""

from __future__ import annotations  # Keep annotations import-safe during test collection.

from datetime import date  # Build deterministic report dates.

from src.mist.intelligence.reports.subscription_expiry.model import (
    CONTRACT_RECORD_ABSENT_NOTE,
    MISSING_VALUE,
    ConsoleSummary,
    CrossOrgSubscriptionInventoryModel,
    DeployedInventoryRow,
    DeployedInventorySummaryRow,
    JsiContractSource,
    LicenseSummarySource,
    LicenseUsageSource,
    OrganizationScope,
    ReportContext,
    StockInventoryRow,
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


def test_cross_org_deployed_and_stock_inventory_stay_separate() -> None:
    """Assigned devices enter deployed inventory and unassigned devices enter stock inventory."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        msp_id="msp-1",
        source="msp",
        request_status="success",
    )  # Build a synthetic MSP organization.
    inventory = [
        {
            "serial": "AP1",
            "mac": "mac-1",
            "model": "AP43",
            "type": "ap",
            "site_id": "site-1",
            "name": "Retail 1",
            "connected": True,
        },
        {
            "serial": "SSR1",
            "mac": "mac-2",
            "model": "SSR130",
            "type": "gateway",
            "name": "Warehouse",
            "connected": False,
        },
    ]  # Include one assigned and one unassigned device.
    deployed = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_rows(
        organization,
        inventory,
    )  # Build deployed detail rows.
    stock = CrossOrgSubscriptionInventoryModel.build_stock_rows(
        organization,
        inventory,
        None,
    )  # Build stock detail rows.
    summaries = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_summary(
        organization,
        deployed,
        "success",
    )  # Reconcile deployed counts.
    assert isinstance(deployed[0], DeployedInventoryRow)  # The deployed record has the new row type.
    assert len(deployed) == 1  # The stock SSR is excluded from deployed detail.
    assert deployed[0].serial == "AP1"  # The assigned AP serial remains visible.
    assert deployed[0].site_id == "site-1"  # The assigned site survives classification.
    assert deployed[0].deployment_status == "deployed"  # The assigned status is explicit.
    assert len(stock) == 1  # The assigned AP is excluded from stock detail.
    assert stock[0].serial == "SSR1"  # The unassigned SSR remains stock evidence.
    assert isinstance(summaries[0], DeployedInventorySummaryRow)  # The summary has the new row type.
    assert summaries[0].device_type == "ap"  # The summary groups assigned AP devices.
    assert summaries[0].deployed_quantity == 1  # The summary counts one assigned AP.
    assert summaries[0].request_status == "success"  # The successful inventory read stays visible.


def test_cross_org_inventory_summary_combines_deployed_and_stock() -> None:
    """The combined inventory summary adds deployed and stock identities once."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        source="msp",
        request_status="success",
    )  # Build a synthetic MSP organization.
    inventory = [
        {
            "serial": "AP1",
            "mac": "mac-ap",
            "model": "AP43",
            "type": "ap",
            "site_id": "site-1",
        },
        {
            "serial": "SSR1",
            "mac": "mac-ssr",
            "model": "SSR130",
            "type": "gateway",
        },
    ]  # Include one deployed AP and one stock gateway.
    deployed = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_rows(
        organization,
        inventory,
    )  # Build deployed detail once.
    stock = CrossOrgSubscriptionInventoryModel.build_stock_rows(
        organization,
        inventory,
        None,
    )  # Build stock detail once.
    summaries = CrossOrgSubscriptionInventoryModel.build_inventory_summary(
        organization,
        deployed,
        stock,
        "success",
    )  # Build combined organization and device-type totals.
    summary_by_type = {summary.device_type: summary for summary in summaries}  # Index the summary by type.
    assert isinstance(summary_by_type["ap"], DeployedInventorySummaryRow)  # The AP summary has the row type.
    assert summary_by_type["ap"].deployed_quantity == 1  # The deployed AP remains visible.
    assert summary_by_type["ap"].stock_quantity == 0  # The AP is not stock.
    assert summary_by_type["ap"].inventory_quantity == 1  # The AP contributes one combined identity.
    assert summary_by_type["ssr"].deployed_quantity == 0  # The SSR is not deployed.
    assert summary_by_type["ssr"].stock_quantity == 1  # The SSR remains in stock.
    assert summary_by_type["ssr"].inventory_quantity == 1  # The SSR contributes one combined identity.


def test_cross_org_deployed_row_uses_physical_chassis_serial_for_synthetic_virtual_mac() -> None:
    """A synthetic 020003 identity keeps the physical chassis serial in deployed output."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        source="msp",
        request_status="success",
    )  # Build a synthetic MSP organization.
    inventory = [
        {
            "serial": "020003135CBF",
            "mac": "020003135cbf",
            "model": "EX4100-48MP",
            "chassis_serial": "PHYSICAL1",
            "chassis_mac": "38f20d35965b",
            "chassis_model": "EX4100-48MP",
            "vc_mac": "020003135cbf",
            "type": "switch",
            "site_id": "site-1",
        }
    ]  # Supply a synthetic VC virtual device with a physical chassis identity.
    deployed = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_rows(
        organization,
        inventory,
    )  # Build deployed detail.
    assert len(deployed) == 1  # One physical chassis identity remains.
    assert deployed[0].serial == "PHYSICAL1"  # The synthetic virtual serial is not the canonical identity.
    assert deployed[0].mac == "38f20d35965b"  # The physical chassis MAC remains visible.
    assert deployed[0].vc_mac == "020003135cbf"  # The VC parent MAC remains visible.
    assert deployed[0].chassis_serial == "PHYSICAL1"  # The chassis serial remains explicit.


def test_cross_org_deployed_row_keeps_real_member_serial_when_vc_parent_is_present() -> None:
    """A real member serial remains canonical when it differs from the VC parent."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        source="msp",
        request_status="success",
    )  # Build a synthetic MSP organization.
    inventory = [
        {
            "serial": "EY2225AX0590",
            "mac": "38f20d35965b",
            "model": "EX4100-48MP",
            "chassis_serial": "PARENT1",
            "chassis_mac": "020003135cbf",
            "chassis_model": "EX4100-48MP",
            "vc_mac": "020003135cbf",
            "type": "switch",
            "site_id": "site-1",
        }
    ]  # Supply one real member row and one VC parent identity.
    deployed = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_rows(
        organization,
        inventory,
    )  # Build deployed detail.
    assert len(deployed) == 1  # One real member identity remains.
    assert deployed[0].serial == "EY2225AX0590"  # The real member serial wins.
    assert deployed[0].chassis_serial == "PARENT1"  # The parent serial remains explicit.
    assert deployed[0].vc_mac == "020003135cbf"  # The VC parent MAC remains visible.


def test_cross_org_deployed_inventory_expands_nested_vc_members() -> None:
    """Nested VC member records become separate deployed identities."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        source="msp",
        request_status="success",
    )  # Build a synthetic MSP organization.
    inventory = [
        {
            "serial": "020003135CBF",
            "mac": "020003135cbf",
            "model": "EX4100-48MP",
            "vc_mac": "020003135cbf",
            "type": "switch",
            "site_id": "site-1",
            "members": [
                {"serial": "MEMBER1", "mac": "member-mac-1", "model": "EX4100-48MP"},
                {"serial": "MEMBER2", "mac": "member-mac-2", "model": "EX4100-48MP"},
            ],
        }
    ]  # Supply nested member identities under one VC record.
    deployed = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_rows(
        organization,
        inventory,
    )  # Build separate deployed detail rows.
    assert [row.serial for row in deployed] == ["MEMBER1", "MEMBER2"]  # Both physical members remain visible.
    assert all(row.vc_mac == "020003135cbf" for row in deployed)  # Both rows keep the VC parent identity.


def test_cross_org_stock_row_uses_virtual_chassis_identity_fallbacks() -> None:
    """A stock VC row keeps chassis serial, VC MAC, and chassis model."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        source="direct",
        request_status="success",
    )  # Build a synthetic direct organization.
    inventory = [
        {
            "chassis_serial": "CHASSIS1",
            "vc_mac": "vc-mac",
            "chassis_model": "EX4100",
            "type": "switch",
        }
    ]  # Supply physical VC identity fields without a site assignment.
    stock = CrossOrgSubscriptionInventoryModel.build_stock_rows(
        organization,
        inventory,
        None,
    )  # Build the stock detail row.
    assert len(stock) == 1  # One physical stock identity remains visible.
    assert isinstance(stock[0], StockInventoryRow)  # The stock record has the row type.
    assert stock[0].serial == "CHASSIS1"  # The chassis serial survives.
    assert stock[0].mac == "vc-mac"  # The VC MAC survives.
    assert stock[0].model == "EX4100"  # The chassis model survives.


def test_cross_org_deployed_summary_preserves_missing_and_empty_results() -> None:
    """A failed inventory read stays Missing and an empty success stays zero."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        source="direct",
        request_status="success",
    )  # Build a direct organization.
    missing_summary = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_summary(
        organization,
        [],
        "failed",
    )  # Build the failed inventory summary.
    empty_summary = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_summary(
        organization,
        [],
        "success",
    )  # Build the successful empty summary.
    missing_inventory_summary = CrossOrgSubscriptionInventoryModel.build_inventory_summary(
        organization,
        [],
        [],
        "failed",
    )  # Build the failed combined inventory summary.
    empty_inventory_summary = CrossOrgSubscriptionInventoryModel.build_inventory_summary(
        organization,
        [],
        [],
        "success",
    )  # Build the successful empty combined inventory summary.
    assert missing_summary[0].device_type == MISSING_VALUE  # A failed read has no source device type.
    assert missing_summary[0].deployed_quantity == MISSING_VALUE  # A failed read never becomes zero.
    assert missing_summary[0].request_status == "failed"  # The failure status remains visible.
    assert empty_summary[0].device_type == MISSING_VALUE  # A successful empty read has no source type.
    assert empty_summary[0].deployed_quantity == 0  # A successful empty read may use zero.
    assert empty_summary[0].request_status == "success"  # The successful empty read stays successful.
    assert missing_inventory_summary[0].inventory_quantity == MISSING_VALUE  # A failed combined total stays Missing.
    assert missing_inventory_summary[0].request_status == "failed"  # The combined failure stays visible.
    assert empty_inventory_summary[0].inventory_quantity == 0  # A successful empty combined total is zero.


def test_cross_org_deployed_inventory_collapses_duplicates_and_keeps_vc_members() -> None:
    """Duplicate inventory rows collapse while distinct Virtual Chassis members remain."""
    organization = OrganizationScope(
        org_id="org-1",
        org_name="T-Mobile",
        source="msp",
        request_status="success",
    )  # Build a synthetic MSP organization.
    inventory = [
        {
            "serial": "VC1",
            "mac": "mac-1",
            "model": "EX4100",
            "type": "switch",
            "site_id": "site-1",
            "vc_mac": "vc-mac",
            "connected": True,
        },
        {
            "serial": "VC1",
            "mac": "mac-1",
            "model": "EX4100",
            "type": "switch",
            "site_id": "site-1",
            "vc_mac": "vc-mac",
            "connected": True,
        },
        {
            "serial": "VC2",
            "mac": "mac-2",
            "model": "EX4100",
            "type": "switch",
            "site_id": "site-1",
            "vc_mac": "vc-mac",
            "connected": True,
        },
    ]  # Include duplicate evidence and a distinct VC member.
    rows = CrossOrgSubscriptionInventoryModel.build_deployed_inventory_rows(
        organization,
        inventory,
    )  # Build deployed detail rows.
    assert len(rows) == 2  # One duplicate is removed and both distinct members remain.
    assert [row.serial for row in rows] == ["VC1", "VC2"]  # The stable serial identity remains visible.
