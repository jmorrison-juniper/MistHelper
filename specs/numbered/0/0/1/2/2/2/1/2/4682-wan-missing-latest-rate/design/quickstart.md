# Quickstart: Report a missing latest WAN rate

This guide gives the exact reproduction steps and the exact verification commands. It applies after pull request 4208 merges, unless a step says otherwise.

## Reproduce the Reported Defect

Run this check before the fix. No live Mist call is needed. The steps follow issue 4682.

1. Build a mocked ten-minute response. Use six timestamps, starting at the requested hour, in ten-minute steps.
2. Give the first five intervals numeric `rx_bps` values. Give the sixth interval a null value.
3. Pass the mocked response through `GatewayInsights.collect_for_port`. Patch the mistapi functions, as the existing selected-port tests do.
4. Read `samples[0]["value"]`. Before the fix, the value equals the fifth numeric value. The expected result is None.

Run the two defect tests with this command:

```powershell
python -m pytest tests/unit/wan_performance/test_gateway_insights.py -k "null_latest or absent_latest"
```

Expected result before the fix: both tests fail, and each failure shows the earlier value.

## Apply the Fix

1. Confirm that pull request 4208 merged.

```powershell
gh pr view 4208 -R jmorrison-juniper/MistHelper --json state,mergedAt
```

Expected result: `"state":"MERGED"`. If the state is OPEN, stop. Do not edit `snapshot_client.py`.

2. Create a worktree from main.

```powershell
git worktree add ..\MistHelper-4682 -b fix/4682-wan-missing-latest-rate origin/main
```

3. Bootstrap the environment in the worktree. The commands come from copilot-instructions.md, section "Language and environment".

```powershell
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

4. Confirm the target function. The line numbers in this record refer to pull request 4208 head. Search the post-merge file for the function.

```powershell
Select-String -Path src\interfaces\wan_performance\collection\snapshot_client.py -Pattern "def _sample"
```

5. Run the targeted tests. All tests pass after T003.

```powershell
python -m pytest tests/unit/wan_performance/test_gateway_insights.py
```

6. Run the symbol gate for the touched module.

```powershell
symbol-diff --base origin/main src/interfaces/wan_performance/collection/snapshot_client.py
```

Expected result: `no module-level name changed`, with exit code 0.

7. Run the writing gate for each changed Markdown file.

```powershell
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 documentation\wan-performance.md
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 changelog.d\issue-4682-wan-missing-latest-rate.md
```

Expected result: each file scores 80 or above.

8. Run every other applicable gate from the Local gates table. The table is in `.github/copilot-instructions.md`, section "Local gates", line 50.

9. Push the branch, open the pull request, and watch the remote checks.

```powershell
gh pr checks --watch
```

Expected result: each required check passes.

10. Remove the worktree after the merge.

```powershell
git worktree remove ..\MistHelper-4682
```

Caution: Remove the worktree only after the merge. Earlier removal stops the local test environment.

Warning: Do not delete the branch before its pull request exists. The branch reference may be the only reference to its commits.

## Confirm the Main Path

On main, the portal does not call the builder. The main portal series keep index positions. Check the insight path with this command:

```powershell
Select-String -Path src\interfaces\portals\wan_dashboard\services\__init__.py -Pattern "\[-1\]"
```

Expected result: no output.
