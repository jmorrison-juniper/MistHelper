# Quickstart: Endpoint family per-choice prompts

## Local checks

Run these commands from the worktree:

```powershell
python -m py_compile web_portal\services\operation.py
python -m ruff check web_portal\services\operation.py tests\unit\web_portal\test_portal_required_answers.py
python -m black --check web_portal\services\operation.py tests\unit\web_portal\test_portal_required_answers.py
python -m pytest tests\unit\web_portal\test_portal_required_answers.py -q
```

## Browser check

Start the private portal on port 9606:

```powershell
& "c:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Scripts\python.exe" "C:\Users\jmorrison\.misthelper-coordination\serve_local_portal.py" --checkout "<worktree>" --port 9606
```

Open `http://127.0.0.1:9606/operations`.

For each menu 263 through 268:

1. Select the row.
2. Confirm that Run is disabled before an endpoint is selected.
3. Select one endpoint.
4. Confirm that the dynamic controls match the selected operation.
5. Fill the controls with safe test values.
6. Confirm that Run becomes enabled.
