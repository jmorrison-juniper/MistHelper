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
        "CrossOrgStockInventory",
        "CrossOrgContractEvidence",
    ):
        assert operation in ENDPOINT_PRIMARY_KEY_STRATEGIES
        assert ENDPOINT_PRIMARY_KEY_STRATEGIES[operation]["primary_key"]
