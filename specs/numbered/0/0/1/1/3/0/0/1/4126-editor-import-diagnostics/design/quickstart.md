# Quickstart: Editor Import Diagnostics (issue #4126)

Use these steps on the machine that holds the worktree and the editor window. The steps follow `documentation/development-setup.md` lines 197 to 260. This record adds only the exact lists and the evidence fields.

Caution: run every terminal step from the worktree root. A run from the main checkout tests the wrong tree and gives a false result.

## Step 1: Confirm the remote evidence (AT-04, AT-05, AT-06)

Run these commands in any checkout with GitHub read access. The first command must print nothing. The other commands print the moved paths, the cited lines, and the `init-hook` line that rows R01 to R36 and R51 record.

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq ".tree[] | select(.path | startswith(\"src/org/juniper_rma/\")) | .path"
```

```powershell
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq ".tree[] | select(.path | startswith(\"src/operations/exporting/juniper_rma/\")) | .path + \" \" + .sha"
$cited = git show f03c6c9b36d612a48d7b9652998c2fd87dd777ca:MistHelper.py; foreach ($number in 474, 480, 543, 699, 779, 3384, 3426, 3678) { "line $number`: " + $cited[$number - 1] }
git grep -n init-hook f03c6c9b36d612a48d7b9652998c2fd87dd777ca -- pyproject.toml
```

## Step 2: Create the worktree environment

Run these commands in the worktree root. The bootstrap creates `.venv` and selects Python 3.15.2 through UV.

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

If the worktree still uses `src/org/juniper_rma/`, rebase onto `main` before step 3 (decision D-8).

## Step 3: Check the root and the interpreter (AT-03)

Run these commands in the worktree root. Each printed path must sit inside the worktree. Redact the user-profile segment before you copy a path into evidence (FR-014).

```powershell
python -c "import sys; from pathlib import Path; print('root:', Path.cwd()); print('interpreter:', sys.executable); print('environment:', sys.prefix)"
python -c "import src, requests.adapters, mistapi.api.v1.sites.devices; print(src.__file__); print(requests.adapters.__file__); print(mistapi.api.v1.sites.devices.__file__)"
```

## Step 4: Run the terminal check for each current path (AT-02)

This check supports the live check. It does not replace the live check (FR-011). Each path must print `PASS`.

```powershell
$paths = @('MistHelper.py', 'web_portal/services/operation.py', 'src/operations/exporting/juniper_rma/workflows/correlation.py', 'src/operations/exporting/juniper_rma/workflows/asset_lookup.py', 'src/operations/exporting/juniper_rma/workflows/lookup.py', 'tests/unit/juniper_rma/fixtures/fake_gateway.py', 'src/operations/exporting/juniper_rma/settings.py', 'tests/unit/juniper_rma/workflows/test_lookups.py', 'tests/unit/juniper_rma/api/test_asset_service.py', 'tests/unit/juniper_rma/workflows/test_correlation.py', 'src/operations/exporting/juniper_rma/workflows/access_check.py', 'tests/unit/juniper_rma/api/test_case_service.py', 'tests/unit/juniper_rma/workflows/test_access_check.py', 'tests/unit/juniper_rma/model/test_export_rows.py', 'src/operations/exporting/juniper_rma/api/case_service.py', 'tests/unit/juniper_rma/workflows/test_read_only_boundary.py', 'tests/unit/juniper_rma/api/test_messages.py', 'src/operations/exporting/juniper_rma/api/asset_service.py', 'src/operations/exporting/juniper_rma/model/export_rows.py', 'tests/unit/juniper_rma/api/test_gateway.py', 'tests/unit/juniper_rma/model/test_asset.py', 'tests/unit/juniper_rma/model/test_run_record.py', 'tests/unit/juniper_rma/model/test_service_request.py', 'tests/unit/test_menu_entry_metadata.py', 'src/operations/exporting/juniper_rma/model/asset.py', 'src/operations/exporting/juniper_rma/api/gateway.py', 'tests/unit/juniper_rma/api/test_settings.py')
foreach ($path in $paths) { python -m pylint --disable=all --enable=E0401,E0611 --reports=n --score=n $path; if ($LASTEXITCODE -eq 0) { "PASS $path" } else { "FAIL $path exit=$LASTEXITCODE" } }
```

## Step 5: Run the live editor check (AT-01)

Follow the setup steps in `documentation/development-setup.md` lines 204 to 244. Open only the worktree root. Select the worktree interpreter. Apply the Pylint settings at the workspace scope. Restart the Pylint server.

For each current path in step 4:

1. Open the file in the editor window.
2. Save the file to request new diagnostics.
3. Open the Problems view and filter by the source `Pylint`. Do not use a Pylance filter, because it does not verify Pylint diagnostics (line 250).
4. Count the E0401 and E0611 diagnostics for the file.
5. Record one evidence row that follows `design/contracts/editor-evidence.md`.

If the Pylint output shows a different working directory or interpreter, record `fail` and the cause. Do not change production imports to pass the check (line 244).

If a native permission is missing, stop the check. Record each remaining path as `unverified` with the cause (FR-015).

## Step 6: Post the evidence (T011)

Post the evidence rows as a comment on issue #4126. Keep the issue open until all 27 paths show zero E0401 and zero E0611 (FR-010). Redact user-profile path segments and credentials in the comment (FR-014).

## Step 7: Check the change before the pull request

Run these checks from the repository root on the change branch.

```powershell
ste-linter --config .ste-linter.toml --min-score 80 (Get-ChildItem -Path specs\numbered\0\0\1\1\3\0\0\1\4126-editor-import-diagnostics -Recurse -File).FullName changelog.d\issue-4126-editor-import-spec.md
Select-String -Path (Get-ChildItem -Path specs\numbered\0\0\1\1\3\0\0\1\4126-editor-import-diagnostics -Recurse -File).FullName -Pattern 'C:\\Users\\|GH_TOKEN|_TOKEN|PASSWORD|SECRET'
git diff --name-only origin/main HEAD
Select-String -Path changelog.d\issue-4126-editor-import-spec.md -Pattern '^### '
Select-String -Path changelog.d\issue-4126-editor-import-spec.md -Pattern '^- '
(Get-ChildItem -Path specs\numbered\0\0\1\1\3\0\0\1\4126-editor-import-diagnostics -Force).Count
```

Expected results:

- The STE command scores each file at 80 or above (FR-012).
- The `Select-String` search for user-profile and credential names prints nothing (AT-07).
- The `git diff` command lists only the eleven record and changelog files (AT-09).
- The fragment shows one `###` heading and one `- ` bullet (AT-10).
- The record folder shows five children (AT-11).

Check the pull request body for the closing keyword rule (AT-08):

```powershell
gh pr view --json body --jq .body | Select-String -Pattern 'Refs #4126'
gh issue view 4126 -R jmorrison-juniper/MistHelper --json state --jq .state
gh issue view 4126 -R jmorrison-juniper/MistHelper --json labels --jq ".labels[].name"
```

The first command must print a match. The second command must print `OPEN` until live evidence exists for all 27 paths. The third command must list `in-progress` and must not list `needs-investigation` after the label change (decision D-9).
