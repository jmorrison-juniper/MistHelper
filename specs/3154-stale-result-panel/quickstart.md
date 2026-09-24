# Quickstart: Clear Stale Operation Results

## Local test

Run this command from the worktree:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\e2e\test_operation_results_table.py -q
```

Expected result: all tests pass. The stale-selection test reports one checked browser state.

## Manual portal check

1. Start the local portal on port 9602 with the fleet charter launcher.
2. Open `http://127.0.0.1:9602/operations` with Playwright and `channel="chrome"`.
3. Select menu 86 and complete the run if credentials permit it.
4. Select menu 241.
5. Confirm that the prior file list and result table are not visible.

If live Mist access is not available, use the regression test as the local proof.
