# Contract: Shared Exclusions in the Integration Pull Request

## Purpose

This contract defines the shared-file change that keeps backup content out of the output scan and the data browser. The change ships in a separate integration pull request (D-13, FR-020). Persistence waits for its merge.

## Files Changed

| File | Change | Existing pattern |
| --- | --- | --- |
| `web_portal/services/output_scan.py` | Import `BackupDirectory` and add `BackupDirectory.NAME` to `EXCLUDED_DIR_NAMES`. | Line 43 imports the firmware constant (R-23). Line 85 excludes it (R-24). |
| `web_portal/services/data_browser.py` | Refuse a candidate path whose relative parts contain `BackupDirectory.NAME`. | Line 154 refuses the firmware constant (R-25). |
| `tests/unit/web_portal/test_output_scan_runtime_files.py` | Add `test_output_scan_prunes_converter_backup_directory`. | Module imports `EXCLUDED_DIR_NAMES` at line 31 (R-26). |
| `tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py` | Add `test_data_browser_refuses_converter_backup_path`. | Module exists (R-27). |
| `changelog.d/pr-<number>.md` | Add one fragment with one `###` heading and one `Changed` bullet that names issue 4643. | Changelog rule in `.github/copilot-instructions.md`, section Git and GitHub in this repository. |

The import path is `src.interfaces.portals.cisco_config_converter.state.lifecycle.backup`. The shared file imports only the constant class `BackupDirectory`. No other name crosses the boundary.

## Files Not Changed

- `web_portal/app.py`. PR 4208 owns it (open pull request scan at drafting time).
- `web_portal/templates/base.html`.
- `web_portal/routes`. No route is added (D-10).

## Test Contract

Test: `test_output_scan_prunes_converter_backup_directory`

- Create a file under `tmp_path` in a directory named `BackupDirectory.NAME`.
- Run the output scanner's directory walk over `tmp_path`.
- Assert that the walk returns no entry under the converter directory.
- The test uses `tmp_path` only. It never writes under the repository data directory.

Test: `test_data_browser_refuses_converter_backup_path`

- Build a candidate path under `tmp_path` that includes `BackupDirectory.NAME`.
- Call the data browser containment check.
- Assert that the check refuses the path.

## Handover Conditions

- The integration owner records the handover in issue 4633 before the change opens (coordinator decision, 2026-11-08T23:37:56Z).
- PR 4615 merged on 2026-11-13T06:20:12Z. It no longer owns `web_portal/services/data_browser.py`.
- No open PR touched `web_portal/services/output_scan.py` or `web_portal/services/data_browser.py` at drafting time. The integration owner repeats the check before the branch starts.
- Persistence stays disabled until this pull request merges (FR-020, FR-026).

Warning: without this change, the output scan and the data browser list the backup directory when a backup exists. Keep persistence disabled until the merge.
