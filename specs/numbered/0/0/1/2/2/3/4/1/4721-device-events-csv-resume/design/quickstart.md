# Quickstart: Resumed 52-week device-event CSV export

This page gives the reproduction steps and the verification commands for issue #4721. The authoring agent did not run these steps. Each expected result below comes from reading the code on main.

## Prerequisites

1. Run from the repository root: `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`.
2. Create or refresh the environment with `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`, then run `.venv\Scripts\Activate.ps1`. The bootstrap is in `.github\copilot-instructions.md` section "Language and environment".
3. Use a temporary working directory for every reproduction. Do not run menu 97 against a live organization.

## Reproduction 1: Empty checkpoint replaces the CSV (defect FR-006)

Steps:

1. In a temporary directory, create `data\OrgDeviceEvents_52w.csv` with the text `id` and a line break, then the text `before` and a line break.
2. Create `data\OrgDeviceEvents_52w.fixture-org.checkpoint` with zero bytes.
3. Mock `searchOrgDeviceEvents` to return one page with `{"results": [{"id": "after"}]}`.
4. Construct `DeviceEvents52wExporter` for `fixture-org` with `output_format="csv"`. Call `export()`.
5. Read the CSV file and the checkpoint file.

Expected result on main (predicted): The CSV holds only the header `id` and the row `after`. The row `before` is gone. The run treats the empty checkpoint as no token.

Expected result after the change (T002): `export()` raises `RuntimeError`. The message names the CSV file and says that the checkpoint file is empty. Both files keep their bytes. No page is requested.

The unit test for this reproduction is N1, `test_read_checkpoint_refuses_empty_file_when_csv_exists`.

## Reproduction 2: Checkpoint write truncates the live file (defect FR-007)

Steps:

1. Create `data\OrgDeviceEvents_52w.org-1.checkpoint` with the text `old-token`.
2. Patch `os.replace` to raise `OSError`. Call `_write_checkpoint` with the token `new-token`.
3. Read the checkpoint file.

Expected result on main (predicted): The file holds `new-token`, because the in-place write already replaced the content. The previous token is lost.

Expected result after the change (T003): The file holds `old-token`. A warning names the checkpoint file. The unit test is N4, `test_write_checkpoint_keeps_previous_token_when_replace_fails`.

## Reproduction 3: Resumed run with no rows (defect FR-008)

Steps:

1. Create `data\OrgDeviceEvents_52w.csv` with `id` and `before` on separate lines.
2. Create `data\OrgDeviceEvents_52w.org-1.checkpoint` with the text `fixture-cursor`.
3. Mock `searchOrgDeviceEvents` to return `{"results": []}`. Call `export()`.
4. Read the CSV file and check whether the checkpoint file exists.

Expected result on main (predicted): The checkpoint file stays. The log holds "No device events found for the 52-week period." The CSV bytes do not change.

Expected result after the change (T004): The checkpoint file stays. The log holds "No new device events follow the checkpoint." The CSV bytes do not change. The unit test is N6, `test_resumed_run_without_new_rows_keeps_both_files`.

## Verification commands

Run each command from the repository root. Each command prints a pass or fail summary.

```powershell
python -m pytest tests\unit\test_device_events_52w_exporter_extended.py tests\unit\test_device_events_52w_exporter.py -q -p no:cacheprovider
python -m pytest tests\guardrails\test_nested_package_structure.py -q -p no:cacheprovider
python -m pytest tests\integration\test_mistapi_sdk_compatibility.py -q -p no:cacheprovider
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
symbol-diff --base origin/main src\operations\exporting\export\device_events_52w_exporter.py
```

Expected results:

- The pytest command for the two unit modules passes all tests after T004. Before T002 to T004, tests N1, N4, N5, and N6 fail.
- The guardrail test passes. The total ratchet excess stays the same.
- The SDK compatibility guard passes. The change adds no call site.
- `ruff check` prints `All checks passed`.
- `black --check` reports no file to change.
- `mypy` reports `Success`.
- `symbol-diff` reports `no module-level name changed`.
