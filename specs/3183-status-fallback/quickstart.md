# Quickstart: Status Fallback for Quiet Operation Streams

## Local test

Run this command from the worktree:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\web_portal\test_operation_stream_fallback.py -q
```

Expected result: the test passes and checks one fallback implementation path.

## Manual portal check

1. Start the local portal on port 9602 with the fleet charter launcher.
2. Open `http://127.0.0.1:9602/operations` with Playwright and `channel="chrome"`.
3. Run menu 3 or menu 238.
4. If the badge remains `Running` after the log shows completion, read `/api/operations/status/<run_id>`.
5. Confirm that the page uses the status answer and reaches a terminal badge.
