# Quickstart: Ship the preserved admission scope work

Use this file to repeat each step of the ship. Each command names the explicit repository path. Run the commands in PowerShell.

## Prerequisites

- The repository checkout at `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.
- Read access to GitHub through the `gh` command, with the account of `COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper`.
- The environment of the repository, created by `documentation/development-setup.md:26-54`.

## 1. Verify the preserved files (T001)

Hash each file with the raw-content option. The option omits the clean filter. The command writes no object.

```powershell
git --no-pager --no-optional-locks -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" hash-object --no-filters src/foundation/support/utils/logger_utils.py
git --no-pager --no-optional-locks -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" hash-object --no-filters src/interfaces/wan_performance/collection/request_admission.py
git --no-pager --no-optional-locks -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" hash-object --no-filters src/mist/intelligence/reports/subscription_expiry/client.py
git --no-pager --no-optional-locks -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" hash-object --no-filters tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py
git --no-pager --no-optional-locks -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" hash-object --no-filters tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py
```

Expected blob values: `b47036046770f9a36aaecaff1e2821f165ed66df`, `5ee19a82c40acbaf2b6364aebd2561b31fc981da`, `4bc021ea9d089f7c981d6e6be4c02052f1f7329a`, `913247f0e25799656e4df72234f9fac5cbefbf39`, and `526be2c14a388c7cc62a27d3005c33f80f3bb7aa`.

Read the branch tree with the GitHub reader. The tree of commit `5213149d63be00d4c47c0fe8194d4cbf0eca1f1f` is `ec0531b239058f0b9686352f259941518bc9a06d`.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/ec0531b239058f0b9686352f259941518bc9a06d?recursive=1" --jq '.tree[] | select(.path | test("request_admission|logger_utils|subscription_expiry/client|test_client|test_request_admission")) | .path + " " + .sha'
```

## 2. Check the sequencing gate (T002)

```powershell
gh pr view 4208 -R jmorrison-juniper/MistHelper --json state,mergedAt,isDraft,files
```

The task continues only when the state is `MERGED` or `CLOSED`. Otherwise, the task waits.

## 3. Create the worktree and bootstrap it (T003)

```powershell
git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" worktree add ../MistHelper-request-admission-org-scope -b fix/4943-request-admission-org-scope main
Set-Location ../MistHelper-request-admission-org-scope
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## 4. Run the new tests before the repairs (T007)

The red run uses the tests that T005 and T006 add with the branch names.

```powershell
python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py
```

Expected failures: `test_organization_scope_rejects_empty_identifier`, `test_console_renderer_output_has_no_ansi_on_non_terminal`, and `test_msp_listing_logs_info_before_and_debug_after`. Expected passes: `test_nested_organization_scope_restores_outer_value`, `test_organization_scope_resets_after_exception`, and `test_transport_failure_keeps_the_client_error_line`.

## 5. Verify each repair (T008 to T011)

```powershell
python -m pytest tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py
python -m pytest tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py
```

Expected result: each command ends with a summary line that reports zero failures.

## 6. Structure checks (FR-021)

Count the top-level names of each changed module. The count stops at the first line that starts a class, a function, or a module constant.

```powershell
Select-String -LiteralPath "src\interfaces\wan_performance\collection\request_admission.py" -Pattern "^(class |def |\w+ *(:[^=]+)?=)"
Select-String -LiteralPath "src\mist\intelligence\reports\subscription_expiry\client.py" -Pattern "^(class |def |\w+ *(:[^=]+)?=)"
Select-String -LiteralPath "src\mist\intelligence\reports\subscription_expiry\sdk_error_lines.py" -Pattern "^(class |def |\w+ *(:[^=]+)?=)"
```

Expected names: `request_admission.py` lists `logger`, `OrganizationScope`, `RequestLedger`, and `AdmittedAdapter`. `client.py` lists `logger`, `HTTP_BAD_REQUEST`, `JsiAccountNotLinkedError`, `SubscriptionExpiryClientError`, and `SubscriptionExpiryClient`. `sdk_error_lines.py` lists `SdkErrorLineMute` and its module logger, if the module has one.

## 7. Run the gates (T-LOCAL-GATES)

The commands and the expected results are in `design/checklists/gates.md`. Run each applicable gate. Record the output in the pull request body.

## 8. Live check after the merge (decision D-13)

The owner runs this check once. Set the token from the owner secret store in the environment. Never write the token to a file, and never paste it into a log, a comment, or the record.

```powershell
python MistHelper.py --menu 308
```

Expected lines for a denied MSP organization list: one warning line that names HTTP 403, and no SDK error line. The report then lists the direct organizations.

## 9. Remove the worktree after the merge

```powershell
Set-Location "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper"
git worktree remove ../MistHelper-request-admission-org-scope
```

Keep the preservation branch. Decision D-11 keeps it.
