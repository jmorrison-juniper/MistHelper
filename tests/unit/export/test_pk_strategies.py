"""Test primary-key strategies for cross-org subscription reports."""

from src.foundation.support.refactors.endpoint_primary_key_strategies import (
    ENDPOINT_PRIMARY_KEY_STRATEGIES,
)


def test_cross_org_report_primary_keys_are_registered() -> None:
    """Every cross-org report API name has a stable database strategy."""
    for operation in (
        "CrossOrgOrganizationStatus",
        "CrossOrgSubscriptionPurchase",
        "CrossOrgSubscriptionBalance",
        "CrossOrgDeployedInventory",
        "CrossOrgDeployedInventorySummary",
        "CrossOrgInventorySummary",
        "CrossOrgStockInventory",
        "CrossOrgContractEvidence",
    ):
        assert operation in ENDPOINT_PRIMARY_KEY_STRATEGIES
        assert ENDPOINT_PRIMARY_KEY_STRATEGIES[operation]["primary_key"]


def test_ex_hardware_inventory_uses_the_natural_key_of_a_device_item() -> None:
    """The EX hardware report keys each row by organization, device, and item path (issue #4920)."""
    strategy = ENDPOINT_PRIMARY_KEY_STRATEGIES["ExHardwareInventory"]  # The entry that the CLI report names.
    assert strategy["type"] == "composite_pk"  # A natural key, so a second run replaces the rows.
    assert strategy["primary_key"] == ["org_id", "device_id", "item_path"]  # The key of the data model.
    assert set(strategy["indexes"]) >= {"site_id", "collection_status", "item_serial_number"}  # Common filters.
