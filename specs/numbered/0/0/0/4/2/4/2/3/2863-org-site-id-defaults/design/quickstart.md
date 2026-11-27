# Quickstart: Organization and site identifier defaults

## Preconditions

1. Use a worktree on branch `fix/2863-tenant-identifier-validation`. Create it from `main` (`AGENTS.md:192-198`).
2. Install Python 3.15.2 and build the environment with these commands (`.github/copilot-instructions.md:25-31`).

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

3. Set the GitHub account variables before each `gh` command. Never print a token value.

```powershell
$env:GH_HOST='github.com'
$env:GH_TOKEN=$env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

4. Do not run a live Mist call. Use mocks only.

## Reproduce the masking default on current main

Run this in an interactive Python session at the repository root, with the environment active.

```python
from types import SimpleNamespace  # Build a plain successful response
from unittest.mock import MagicMock, patch  # Mock the session and the SDK call
from src.mist.access.api.tenant_fetch import APITenantFetchUtils  # Import the class under test

session = MagicMock()  # Mock the session so no request leaves the process
utils = APITenantFetchUtils(session, lambda: "")  # Resolver returns an empty organization identifier
with patch("mistapi.api.v1.orgs.networks.listOrgNetworks") as sdk_call:  # Capture the SDK call
    sdk_call.return_value = SimpleNamespace(data=[], status_code=200)  # Empty successful response
    result = utils.organization_tenants()  # Run the public boundary
    print(result, sdk_call.call_args)  # Show the result and the identifier sent to the SDK
```

Expected result on current main: an empty list. The SDK call receives the empty string as the organization identifier. This result is the defect. The empty list hides the missing input.

Expected result after batch 1: the call raises `ValueError` with the message `org_id must be a non-empty string.`, and the SDK mock records zero calls.

## Verify batch 1

Run these commands from the repository root after the change.

```powershell
python -m py_compile src/mist/access/api/tenant_fetch.py tests/unit/api/test_tenant_identifier_validation.py
python -m pytest tests/unit/api/test_tenant_identifier_validation.py -q
python -m pytest tests/unit/marvis/standalone/mist/access/api/test_api_tenant_fetch.py tests/unit/marvis/standalone/mist/access/api/test_issue_2971_status_before_count.py tests/unit/websocket/test_service_ping_discovery.py tests/unit/websocket/test_service_ping_manager.py tests/unit/api/test_response_integrity.py -q
python -m pytest tests/unit/api/test_tenant_identifier_validation.py --cov=src.mist.access.api.tenant_fetch --cov-branch --cov-report=term-missing --cov-fail-under=90
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
```

The second command runs the new tests. The third command runs the existing tests unchanged. The fourth command checks SC-005.

Then run every command in the T-LOCAL-GATES list in `tasks.md`.

## Verify the placement limits

```powershell
git diff --name-status origin/main -- src/mist/access/api tests/guardrails
```

The output must show no `A` line for a new file under `src/mist/access/api/` or `tests/guardrails/`. Batch 1 modifies one existing file in `src/mist/access/api/` and adds none.

## Verify the blob of a changed file

Use read-only Git to confirm the file that you edited. This command does not write to the object store.

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" hash-object --no-filters -- src\mist\access\api\tenant_fetch.py
```

Record the output with the pull request. The value differs from `ba7e74141e32b6d0a4d4edfbeeff618290a9641f` after the change.

## Verify batch 2 (after remediation)

```powershell
python -m pytest tests/guardrails/org_site_identifier_default/test_ratchet.py -q
```

The guard prints one proof line with the scanned, parsed, finding, and baseline totals. A zero-file or zero-parse result is a failure.

## Verify batch 3

```powershell
python -m pytest tests/unit/prod_readiness/standalone/operations/execution/ssid/test_ssid_template_consolidation.py -q
```

## Verify batch 4

```powershell
python -m pytest tests/unit/test_virtual_chassis.py -q
python -m pytest tests/unit/device/test_device_reboot_manager.py -q
```

Caution: before batch 4 merges, confirm that `tests/unit/test_virtual_chassis.py` is the canonical file. Analysis item A21 records the open question.

## Check the remote state before publication

```powershell
gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main --jq .object.sha
```

Compare the output with the main revision in `research.md`. If the value changed, rerun the remote checks in `research.md` before the pull request.
