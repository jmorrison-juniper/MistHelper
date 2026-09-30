# Quickstart: PSK Hygiene Report

## Prerequisites

- Use Python `3.13` or newer.
- Bootstrap the worktree before tests.
- Use a Mist token with the least scope that can read organization PSKs, WLANs, and templates.
- Do not use production secrets in unit tests.

## Setup

```powershell
Set-Location "C:\Users\jmorrison\mh-fleet\3555-psk-hygiene-report"
python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## Unit validation

Run the feature unit tests after implementation.

```powershell
python -m pytest tests\unit\reports\psk_hygiene
```

Expected result:

- Tests use fake clients only.
- Tests do not call the Mist API.
- Tests cover each finding: `expired`, `expires_soon`, `uncapped_multi_use`, `rotation_pending`, and `orphan_ssid`.
- Tests prove that `passphrase` and `old_passphrase` do not appear in rows, logs, or console text.

## CLI validation after the integration pull request

Run menu `274` in test mode after the integration pull request registers the menu.

```powershell
python MistHelper.py --test --menu 274
```

Expected result:

- The operation completes without a prompt.
- The operation writes `data\PskHygiene.csv`.
- The CSV has one row per PSK.
- The console summary shows counts for expired keys, keys that expire in `30` days, uncapped multi-use keys, pending rotations, and orphan SSIDs.
- The console summary states that site-level WLANs are outside scope.

## Safety validation

Search generated output for exact forbidden column names and known fake secret values. Permit `old_passphrase_present`.

```powershell
$csv = Import-Csv "data\PskHygiene.csv"
$csv[0].PSObject.Properties.Name -contains "passphrase"
$csv[0].PSObject.Properties.Name -contains "old_passphrase"
Select-String -Path "data\PskHygiene.csv" -Pattern "fake-secret-value","old-secret-value"
```

Expected result:

- Both column-name checks return `False`.
- No passphrase value appears.
- No old passphrase value appears.
- The report includes only `old_passphrase_present`.

## Local gates

Run the smallest gates that cover the implementation.

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py src\reports\psk_hygiene tests\unit\reports\psk_hygiene
python -m black --check MistHelper.py src\reports\psk_hygiene tests\unit\reports\psk_hygiene
```

Expected result:

- Syntax validation passes.
- Ruff reports no violations.
- Black reports no files to reformat.
