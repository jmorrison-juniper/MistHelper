# Quickstart: Raw shell history test failure (issue 3767)

This guide gives the exact steps for the GET-only checks and for the one controlled run. Run the two `GH_HOST` and `GH_TOKEN` lines before each `gh` command. The `GH_TOKEN` line copies a token from a named variable. Do not print that value.

## 1. Confirm the identities (GET only)

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
gh issue view 3767 -R jmorrison-juniper/MistHelper --json number,title,state,labels
gh api repos/jmorrison-juniper/MistHelper/commits/d4d1110352eeab3d9f9d483242232c12f6de4d2d
gh api repos/jmorrison-juniper/MistHelper/commits/12f10ece0901452bd71eb1baa563ee77de5687db
$base = 'd4d1110352eeab3d9f9d483242232c12f6de4d2d'
$head = '12f10ece0901452bd71eb1baa563ee77de5687db'
gh api "repos/jmorrison-juniper/MistHelper/compare/$base%2E%2E%2E$head"
```

Expected results:

- The accepted-main tree is `fc9e37e7ba4d156f40b586211d9486274089c2ef`.
- The candidate tree is `688ec81037a3fe18cab7b4885e6a7040983d0d5f`.
- The compare result has `ahead_by` 2 and `behind_by` 0. Two files differ: the fake cloud server and the new test file.

## 2. Repeat the CI scan (GET only)

```powershell
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
foreach ($page in 1..4) {
    $runs = (gh api "repos/jmorrison-juniper/MistHelper/actions/workflows/ci.yml/runs?status=failure&created=2026-10-03..2026-11-26&per_page=100&page=$page" | ConvertFrom-Json).workflow_runs
    foreach ($run in $runs) {
        $jobs = (gh api "repos/jmorrison-juniper/MistHelper/actions/runs/$($run.id)/jobs?per_page=100" | ConvertFrom-Json).jobs
        $unit = $jobs | Where-Object { $_.name -eq 'pytest coverage shard (root-units)' } | Select-Object -First 1
        if ($unit -and $unit.conclusion -in @('failure', 'cancelled')) {
            gh run view $run.id -R jmorrison-juniper/MistHelper --log-failed | Select-String -CaseSensitive -Pattern 'test_shell_history_preserves_raw_control'
        }
    }
}
```

Expected result: Each matched line reads `PASSED`. A line that reads `FAILED` for this test is a reproduction from CI. Count the runs, the matched lines, and the `FAILED` lines for the research table.

## 3. Confirm the failing run from the CI evidence (GET only)

```powershell
gh run view 45767339705 -R jmorrison-juniper/MistHelper --log-failed | Select-String -CaseSensitive -Pattern 'FAILED tests|test_shell_history_preserves_raw_control'
```

Expected result: The `FAILED` line names `tests/unit/scripts/netcool_runbook_smoke/test_netcool_smoke_client.py`. The raw shell history test shows `PASSED`.

## 4. Prepare the controlled run

Current main differs in source layout from the reported candidate. Run the controlled test on the candidate commit in a separate worktree.

```powershell
git fetch --no-tags origin 12f10ece0901452bd71eb1baa563ee77de5687db
git worktree add ..\MistHelper-3767-candidate 12f10ece0901452bd71eb1baa563ee77de5687db
cd ..\MistHelper-3767-candidate
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
python --version
New-Item -ItemType Directory -Force -Path test-artifacts\3767
```

Expected result: `python --version` prints `Python 3.15.2`. Stop the run if the version differs, because 3.13 is outside the pinned environment.

## 5. Run the controlled reproduction once

```powershell
python -B -m pytest -p no:cacheprovider -x -vv --durations=0 --log-cli-level=DEBUG --cov=src --cov-report= tests\unit\websocket_streams tests\contract\websocket_streams 2>&1 | Tee-Object -FilePath test-artifacts\3767\controlled-run.log
```

Run this command one time only. The issue comments allow one bounded reproduction. Record the summary line and the SHA256 of the log file in `research.md`.

## 6. Classify the signature

```powershell
Select-String -Path test-artifacts\3767\controlled-run.log -CaseSensitive -Pattern '"event":"terminal_connection_closed"|"event":"socket_close_started"|"event":"frame_read_completed"|"event":"keepalive_ping_started"|terminal_unexpected_failure|test_shell_history_preserves_raw_control'
```

Compare the lines before each `terminal_connection_closed` event with the signature table in `data-model.md`. Record the matched signature in the controlled-run section of `research.md`.

## 7. Remove the worktree

```powershell
cd ..\MistHelper
git worktree remove ..\MistHelper-3767-candidate
```

Caution: Removing the worktree deletes `test-artifacts\3767`. Copy `controlled-run.log` to a safe location before the removal.

## 8. Verification commands after authorization

Run these commands only after the owner authorizes task T008.

```powershell
python -m pytest tests/unit/websocket_streams/live/runners/test_ws_shell_runner.py
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
python -m ruff check .
python -m black --check .
python -m mypy $MYPY_PATHS --config-file pyproject.toml
```

Read `MYPY_PATHS` from `.github/workflows/ci.yml` before the type check.

## 9. Writing gate for each Markdown file

```powershell
ste-linter --config .ste-linter.toml --min-score 80 <file>
```

Run the command once for each Markdown file in the record folder. Each file must score 80 or above.
