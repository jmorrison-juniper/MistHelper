# Quickstart: MSP organization list skipped without the listing right

Use this page to reproduce the defect, run the unit tests, and check the operator output. Run each command from the root of the implementation worktree. Do not run commands in the shared working copy that holds uncommitted changes.

## Prerequisites

- Python 3.15 or newer, with the project environment from `documentation/development-setup.md`.
- mistapi 0.64.1 in the environment, as `pyproject.toml` line 29 allows.
- For the operator check only, a Mist API token in `.env`. The unit tests need no token.

## Scenario 1: Reproduce the defect on main (no network)

Issue #4919 gives no reproduction steps. This scenario reproduces the defect with a fake session.

1. Read the current MSP branch on `main`. Run `git show origin/main:src/mist/intelligence/reports/subscription_expiry/client.py` and find line 99. The condition tests `msp_id` only.
2. Add the test function 2 from T005 before the change. Run it:

```powershell
python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py -q -k "org_scope"
```

3. The test fails on `main`, because the fake `listMspOrgs` records one call. A passing test on `main` means the test checks the wrong thing.

## Scenario 2: Listing right rule (no network)

After T001 to T003, run the listing right tests:

```powershell
python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py -q -k "listing or scope or msp"
```

Expected result: every selected test passes, and the output shows no failure.

## Scenario 3: Console summary (no network)

After T004 and T006, run the summary tests:

```powershell
python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_operation.py -q
```

Expected result: the skipped source line names the reason. The organization count excludes the skipped row.

## Scenario 4: Guard for menu 308 names (no network)

The guard reads `operation.py` and checks the stable output names:

```powershell
python -m pytest tests/guardrails/test_endpoint_catalog.py -q
```

Expected result: the test `test_menu308_deployed_inventory_contract_is_named` passes.

## Scenario 5: Operator check with a token (network)

Run this check only with a token that belongs to the operator. Do not paste the token into a log, an issue, or a pull request.

```powershell
python MistHelper.py --menu 308
```

Expected console output, when the profile holds a grant with `msp_id` and a scope other than `msp`:

- The heading `Cross-org subscription inventory summary:` appears.
- The line `  MSP sources skipped: 1` appears, or another count when more sources are skipped.
- One line begins with `  Skipped MSP source` and names the MSP id and the reason.

Then open the status file under `data\` and find the row with `request_status` `skipped`. The file name is `CrossOrgOrganizationStatus.csv`.

## Scenario 6: Pre-merge gates

Run the gates in T-LOCAL-GATES on the changed files. The first command is the lint gate:

```powershell
python -m ruff check .
```

Expected result: the output reads `All checks passed`.

## Scenario 7: Remote evidence check (read-only)

Confirm that `main` still matches the base of the implementation branch:

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api "repos/jmorrison-juniper/MistHelper/contents/src/mist/intelligence/reports/subscription_expiry/client.py?ref=main" --jq ".sha"
```

Expected result: the output is `980b332e7f8be83e4f495cf86913ba3c1b84ac5c` until another pull request changes the file. If the output differs, read the new file before T001.
