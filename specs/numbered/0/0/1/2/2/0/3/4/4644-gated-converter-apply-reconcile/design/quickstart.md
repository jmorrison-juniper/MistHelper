# Quickstart: Gated Converter Apply and Reconciliation

Use these steps to reproduce the gap on `main` and to check the change after implementation. Replace nothing in the commands. The repository path contains spaces, so keep the quotes.

## Reproduce the Gap

These commands are read-only. They use `Select-String` and `git grep`.

1. Confirm that the converter has no apply route on `main`. Run the command from the repository root:

   ```powershell
   git -C "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper" grep -n "/apply" -- src/interfaces/portals/cisco_config_converter
   ```

   Expected result: No output. The command exits with code 1.

2. Confirm that the converter registers four rules only. Run:

   ```powershell
   Select-String -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\src\interfaces\portals\cisco_config_converter\routes.py" -Pattern "add_url_rule"
   ```

   Expected result: Four lines, at lines 61 to 64.

3. Confirm the SDK retry for HTTP 429. Run:

   ```powershell
   Select-String -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Lib\site-packages\mistapi\__api_request.py" -Pattern "_MAX_429_RETRIES: int|status_code == 429"
   ```

   Expected result: Line 59 sets the retry count to 3. Line 229 retries HTTP 429.

4. Confirm that the write calls pass no timeout. Run:

   ```powershell
   Select-String -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Lib\site-packages\mistapi\__api_request.py" -Pattern "_session.put\(url|_session.post\(url"
   ```

   Expected result: Lines 300 and 324 contain no `timeout` argument.

5. Confirm the pinned SDK version:

   ```powershell
   Test-Path -LiteralPath "C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper\.venv\Lib\site-packages\mistapi-0.64.1.dist-info"
   ```

   Expected result: `True`.

## Verify This Record

1. Check the writing gate on each record file:

   ```powershell
   ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile/spec.md
   ```

   Repeat the command for `plan.md`, `tasks.md`, `analysis.md`, and each file under `design`.

2. Check the record file count under the feature root. The root holds five children: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design`.

## Verify the Code After Implementation

Run these commands after the tasks in `tasks.md` land. Each command names a file that the change adds or edits.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_gates.py
python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_executor.py
python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_reconcile.py
python -m pytest tests/integration/web_portal/cisco_config_converter/apply/test_apply_routes.py
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py
symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/routes.py
```

Expected result: Each command reports all tests passed. The `symbol-diff` command reports `no module-level name changed` and exits with code 0.

Warning: Do not run a command that starts a live write. The tests use a recording SDK double. A test that reaches Mist changes the test design and must not merge.
