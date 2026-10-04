# Quickstart: Subscription Contract Expiry Report

## Prerequisites

1. Use Python 3.13 or newer.
2. Bootstrap the worktree before running tests.
3. Activate the virtual environment.
4. Set Mist API credentials only when you run live menu validation.

## Unit validation

Run these checks after implementation.

```powershell
python -m pytest tests\unit\reports\subscription_expiry
python -m ruff check src\mist\intelligence\reports\subscription_expiry tests\unit\reports\subscription_expiry
python -m black --check src\mist\intelligence\reports\subscription_expiry tests\unit\reports\subscription_expiry
```

Expected result:

- All subscription bands are covered.
- All contract buckets are covered.
- Missing end dates remain visible.
- Empty source data still creates both report outputs.
- Console summary counts match scored rows.

## Local menu validation

Run this validation only after the later wiring branch connects menu 271.

```powershell
python MistHelper.py --menu 271
```

Expected result:

- The command resolves one organization.
- The command creates `data\SubscriptionExpiry.csv`.
- The command creates `data\ContractExpiry.csv`.
- The console prints counts for every subscription band.
- The console prints counts for every contract bucket.

## Manual review checklist

1. Open `data\SubscriptionExpiry.csv`.
2. Confirm one row exists for each subscription type.
3. Confirm each row has status, end date, days remaining, and band.
4. Open `data\ContractExpiry.csv`.
5. Confirm one row exists for each device.
6. Confirm each row has contract status, contract state, end date, and bucket.
7. Compare the console summary counts with the CSV row counts.

## Wiring boundary

Do not complete menu integration in this branch. Use [wiring.md](wiring.md) for
the deferred menu, registry, documentation, generated reference, and primary key
work.
