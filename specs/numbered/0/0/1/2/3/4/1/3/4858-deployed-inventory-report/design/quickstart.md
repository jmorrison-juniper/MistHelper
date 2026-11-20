# Quickstart: Deployed Inventory Report

## Local Synthetic Validation

Run the focused report tests:

```text
python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_model.py
python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py
python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py
python -m pytest tests/unit/export/test_pk_strategies.py
```

The tests must prove:
- Deployed records have a site ID.
- Stock records have no site ID.
- More than 1000 inventory records reconcile across pages.
- Virtual Chassis records remain identifiable.
- Inventory denial preserves Missing.
- Formula text stays neutral in CSV output.

## Live MSP Validation

Run the operation in standalone CSV mode:

```text
python MistHelper.py --standalone --login --menu 308
```

Complete the cloud, email, password, and 2FA prompts in the terminal.

Verify these outputs:
- `CrossOrgDeployedInventory.csv`
- `CrossOrgDeployedInventorySummary.csv`
- `CrossOrgStockInventory.csv`
- `CrossOrgSubscriptionPurchase.csv`
- `CrossOrgSubscriptionBalance.csv`
- `CrossOrgOrganizationStatus.csv`
- `CrossOrgContractEvidence.csv`

T-Mobile USA Retail must show separate deployed detail and summary evidence. The 2026-11-11 snapshot is a comparison baseline of 27,030 deployed devices. The live count may differ but must come from the live inventory source.
