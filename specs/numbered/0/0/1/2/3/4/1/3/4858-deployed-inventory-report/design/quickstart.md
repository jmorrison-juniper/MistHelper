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
- `CrossOrgInventorySummary.csv`
- `CrossOrgStockInventory.csv`
- `CrossOrgSubscriptionPurchase.csv`
- `CrossOrgSubscriptionBalance.csv`
- `CrossOrgOrganizationStatus.csv`
- `CrossOrgContractEvidence.csv`

T-Mobile USA Retail must show separate deployed detail and summary evidence. The 2026-11-11 snapshot is a comparison baseline of 27,030 deployed devices. The live count may differ but must come from the live inventory source.
Each 020003 or 020004 virtual switch identity must include the physical chassis serial in `serial` and `chassis_serial`.

## Logging Validation

Set these values in `.env`:

```text
CONSOLE_LOG_LEVEL=30
LOGGING_LOG_LEVEL=30
```

Run the no-argument script and enter `0` when prompted:

```text
python MistHelper.py
```

Verify:
- The console shows no structlog or standard INFO or DEBUG records.
- The console shows WARNING and ERROR records only.
- `script.log` shows no structlog or standard INFO or DEBUG records.
- A WARNING record appears once in the console and once in `script.log`.
- Key-value database diagnostics remain present where the selected threshold permits them.
- A token or password never appears in output.
