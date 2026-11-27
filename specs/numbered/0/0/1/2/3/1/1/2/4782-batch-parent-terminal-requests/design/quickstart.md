# Quickstart: Batch Parent Terminal Requests

**Issue**: #4782. **Spec**: `spec.md`. **Tasks**: `tasks.md`.

Run these commands in PowerShell from the repository root or from a worktree of it. The bootstrap installs Playwright and Chromium (`documentation/development-setup.md` line 265, R-09).

## Prerequisites

- The GitHub CLI signs in with the owner account.
- Python 3.15 and the project virtual environment are active.
- The ownership hold release (T001) is recorded before any edit.

## Scenario 1: Confirm the guard on main

This is a read-only check. The expected blob is `c0b4f439743280511cf82c00e9ca23a2e1c2a9d4` (R-17).

```powershell
$env:GH_HOST = "github.com"
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api "repos/jmorrison-juniper/MistHelper/contents/src/mist/realtime/websocket_streams/web/static/websockets.js?ref=main" --jq ".sha"
```

## Scenario 2: Confirm the retained commit lacks the guard

This is a read-only check. `isTerminalSession` at line 1652 has no `multi_site` check in the retained commit (R-55). The expected blob is `696c5d52b198e1d1bd86869a35567c71640a1395`.

```powershell
$env:GH_HOST = "github.com"
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh api "repos/jmorrison-juniper/MistHelper/contents/src/mist/realtime/websocket_streams/web/static/websockets.js?ref=c07cb9f8616568ca55ed5933960be2282aeadd93" --jq ".sha"
```

## Scenario 3: Prove that the regression tests can fail

Use a throwaway worktree. Do not edit the main checkout.

1. Create a detached worktree at `origin/main`.

```powershell
git worktree add --detach ..\MistHelper-4782-proof origin/main
```

2. In the worktree copy of `src\mist\realtime\websocket_streams\web\static\websockets.js`, remove the guard line at line 1894. The guard line returns false for `session.mode` equal to `multi_site`. Use the edit tool.

3. Run the batch parent tests in the worktree. Both tests must fail.

```powershell
cd ..\MistHelper-4782-proof
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
python -m pytest tests/e2e/websockets_tab/test_websockets_page.py -k batch_parent -v
```

4. Restore the file in the worktree. Run the same tests again. Both tests must pass.

```powershell
git restore -- src/mist/realtime/websocket_streams/web/static/websockets.js
python -m pytest tests/e2e/websockets_tab/test_websockets_page.py -k batch_parent -v
```

5. Remove the throwaway worktree.

```powershell
cd ..\MistHelper
git worktree remove ..\MistHelper-4782-proof
```

## Scenario 4: Run the changed tests

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
python -m pytest tests/e2e/websockets_tab/test_websockets_page.py -k batch_parent -v
python -m pytest tests/e2e/websockets_tab/test_websockets_page.py -k restored_after_reload -v
```

Expected result: each command reports all selected tests as passed.

## Scenario 5: Run the existing terminal journeys

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
python -m pytest tests/e2e/websockets_tab/test_websockets_terminal.py -k "j5_resize or not_terminal" -v
```

Expected result: `test_j5_resize` and the `not_terminal` case pass (R-50, R-51).

## Scenario 6: Run the local gates

Run the ordered list in `tasks.md`, task T-LOCAL-GATES. Each command has its expected result there.

## Scenario 7: Confirm the pull request file list

Replace `<number>` with the pull request number.

```powershell
$env:GH_HOST = "github.com"
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh pr view <number> -R jmorrison-juniper/MistHelper --json files --jq ".files[].path"
```

Expected result: only the test module and the record paths appear.

## Scenario 8: Live staging smoke (not run)

This scenario waits for the owner decision D-8. Do not run it without an approved credential source.
