# Implementation Plan: Exported cell values stay out of DEBUG logs

**Branch**: `fix/4775-csv-exporter-aggregate-logging` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/3/1/0/0/4775-csv-exporter-aggregate-logging/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Remove exported cell values from DEBUG output in four exporter files. The shared CSV writer logs counts only. The organization inventory exporter, the site device exporter, and the sites by AP model exporter log no device value, no site address, and no table. Each parse failure logs the error type only. The CSV bytes do not change. The regression tests use synthetic marker values.

## Technical Context

**Language/Version**: Python 3.15 or newer. `pyproject.toml` line 23 sets `requires-python = ">=3.15"`.

**Primary Dependencies**: None new. The change uses the standard `csv` and `logging` modules. `prettytable` stays in the dependency set because other modules use it (`src/interfaces/visualization/ui/display_utils.py`, line 54).

**Storage**: Product CSV files stay under `data/`, written by `DataExporter`. The tests write under `tmp_path` only.

**Testing**: pytest with the `caplog` and `tmp_path` fixtures, plus the local gates in `design/quickstart.md`.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container. The change touches no platform-specific code.

**Project Type**: Bug fix in the exporting package.

**Performance Goals**: No change to throughput. The change removes DEBUG work, such as building summary tables and formatting each row.

**Constraints**: Each line holds 120 characters or fewer (`pyproject.toml` line 202 for ruff, line 559 for black, and line 577 for pylint). Each function holds 25 lines or fewer, five parameters or fewer, and five blocks or fewer.

**Scale/Scope**: Four source files, four test files, one document, and one release-note fragment. That makes ten changed paths, plus this record.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes with the recorded deviation D-7.*

| Principle or rule | Result | Reason and evidence |
| - | - | - |
| I. Five-Item Rule, hierarchy | Pass with recorded debt | The change adds no child to a noncompliant folder, except one fragment. `changelog.d/` holds 335 direct files on `main` (research RV-06). The rule allows one unique record per change in that folder. Remediation is a separate follow-up action. |
| I. Five-Item Rule, tests | Pass | The change adds no file under `tests/unit/export/`. That folder holds 55 entries on `main` (RV-08). The tests join four existing files. |
| I. Five-Item Rule, functions | Pass | `_emit_rows` shrinks to three statements. `_enrich_devices_with_site_info` keeps three blocks and stays under 25 lines. |
| II. Class-based design | Pass | The change removes three static methods and adds none. No wrapper function is added. |
| III. Safety first | Pass | No input path changes. The change removes data from logs, and it adds no secret to a log. |
| IV. Full deployment pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 11. Step 12 (deploy and health check) needs an operator action outside this record. |
| V. Observability and logging | Pass | Every new message uses ASCII text and `%s` formatting. No new module exists, so structured logging is not required. |
| VI. Inline comments | Pass | FR-009 requires an inline comment on each changed line. Task T013 audits the changed lines. |
| VII. Action logging | Pass with deviation D-7 | Each loop action keeps an INFO line before it and a DEBUG line after it. The two pure parse helpers keep no per-call INFO line, because that line would print once for each row. |
| Technology: Python | Pass | `pyproject.toml` line 23 sets Python 3.15 or newer. The change adds no version-specific syntax. |
| Technology: mistapi | Pass | The change calls no SDK function. The pinned SDK path stays read-only (RV-113). |
| Technology: Podman and test containers | Not applicable | The change starts no container. The gates run on the host environment. |
| Technology: file paths | Pass | The tests use `tmp_path` and `monkeypatch.chdir`. The change adds no path string. |
| Technology: output backends | Pass | The CSV path keeps `DataExporter.write_with_format_selection`. |
| Technology: data directory | Pass | The tests keep every file under `tmp_path`. `data/` stays unchanged. |
| Security findings: fix over suppress | Pass | FR-015 forbids a suppression comment. The fix removes the logged values. |
| Documentation | Pass | `documentation/security.md` gains the logging statement (FR-011). `README.md` has no debug text (RV-69), so it stays unchanged. |
| Release notes | Pass | One fragment (FR-012) under `changelog.d/`. |
| Multi-agent workflow: labels and branch | Pass | The branch name follows `fix/<issue>-<slug>`. The orchestrator adds `in-progress` before the branch exists (D-13). |
| Multi-agent workflow: shared files | Pass with precondition | Pull request #4813 edits two of the changed files. FR-014 waits for its merge (D-12). |
| Audience standard | Pass | Messages name counts and error types in plain words. |

For repository structure and generated files:

- Use the Conventional Commits form for the commit subject and the pull request title.
- The change adds only this record under `specs/numbered/` and one fragment under `changelog.d/`.
- Existing folder debt is recorded in Complexity Tracking. The remediation action stays outside this change.
- Product output stays under `data/`. Test output uses `tmp_path`.

For a feature that uses Juniper Mist Cloud:

- Not applicable. The change makes no Mist REST request, opens no WebSocket transport, and changes no `mistapi` call.

## Architecture

The shared CSV path runs from `DataExporter.write_to_csv` to `_emit_rows`. The write helpers sit between them.

- `src/operations/exporting/export/data_exporter.py`, line 389: `write_to_csv`. It calls `_resolve_csv_path` and then the write helpers.
- `src/operations/exporting/export/data_exporter.py`, line 438: `_emit_rows`. It writes each row. This change replaces its per-row DEBUG statement (line 443).
- `src/operations/exporting/export/data_exporter.py`, line 419: `_resolve_csv_path` creates the `data` directory in the working directory. The tests therefore change directory to `tmp_path`.

The organization inventory path runs from `devices_with_site_info` in `src/operations/exporting/export/org_inventory_exporter.py` to `_enrich_devices_with_site_info` (line 604). The gateway path runs from `gateways_with_site_info` to `_enrich_gateways_with_site_info`. Each path ends in a summary table, which this change removes.

Menu entries start these paths. Menu 10 calls `devices_with_site_info`, and menu 11 calls `gateways_with_site_info` (`MistHelper.py`, lines 3871 and 3863, see RV-115 and RV-114). The registry lists both as safe read-only exports (`src/foundation/support/utils/operation_registry.py`, lines 680 and 681, see RV-118 and RV-119). Menu 309 starts the EX hardware inventory report (`MistHelper.py`, line 4838, see RV-116). Menu 88 starts the sites by AP model export (`MistHelper.py`, line 6272, see RV-117). The site device exporter docstring names menus 60, 61, and 62 (line 4, see RV-120).

The site device path runs from `SiteDeviceExporter.device_inventory` to `DataExporter.write_with_format_selection`. It logs an INFO line (`site_device_exporter.py`, line 81). It then builds a summary table (line 82), which this change removes.

The EX hardware inventory report writes through the shared writer. Its count line is at `src/operations/exporting/ex_hardware_inventory/report/export.py`, line 80, and its write call is at line 81.

The DEBUG level reaches the file handler through `_apply_debug_log_level` (`MistHelper.py`, line 7686). The file handler writes `data/script.log` (`MistHelper.py`, line 147).

## File-by-File Change Map

| Repository path | Action | Base lines on `main` | Change |
| - | - | - | - |
| `src/operations/exporting/export/data_exporter.py` | Modify | 410, 437 to 443 | Log the field count at line 410. Replace the per-row DEBUG statement with an INFO line before the writes and a count-only DEBUG line after them. Update the docstring at line 439. |
| `src/operations/exporting/export/org_inventory_exporter.py` | Modify | 28, 32, 604 to 616, 634 to 652, 660, 674, 681, 698, 723, 747 to 766 | Remove the PrettyTable import and both summary tables with their calls. Replace the per-device line with INFO and DEBUG count lines. Log the error type only at line 723. Update the comment at line 28 and the two docstrings. |
| `src/operations/exporting/export/sites_by_ap_model_exporter.py` | Modify | 88 | Log the error type only. Omit the site address. |
| `src/operations/exporting/export/site_device_exporter.py` | Modify | 6, 21, 79, 82, 98 to 110 | Remove the PrettyTable import, the `fields` local, the table call, and the table method. Update the module docstring at line 6. |
| `tests/unit/export/test_data_exporter.py` | Modify | 540 to 548 and the end of the file | Add one absence test to `TestEmitRows`. Add class `TestCsvRedaction` with the round-trip test and the field-count test. |
| `tests/unit/test_org_inventory_exporter_helpers.py` | Modify | 425 to 445 and 575 to 590 | Remove the two table tests. Add the enrichment absence test and the split-failure test. |
| `tests/unit/export/test_sites_by_ap_model_exporter.py` | Modify | 143 to 167 | Add the failure-log absence test to `TestSplitAddress`. |
| `tests/unit/export/test_site_device_exporter.py` | Modify | 53 to 109, 98, 121, 155 to 197 | Add the inventory absence test to `TestDeviceInventory`. Remove the two table patches and class `TestDisplayInventoryTable`. |
| `documentation/security.md` | Modify | 13 | Add exported cell values to the Logging row. |
| `changelog.d/issue-4775-csv-exporter-aggregate-logging.md` | Add | None | One fragment with a Security bullet and a Removed bullet. |

## Dependencies

- No package is added or changed. `requirements.txt` and `requirements-dev.txt` stay unchanged.
- `prettytable` stays in use by other modules (`src/interfaces/visualization/ui/display_utils.py`, line 54).
- The tests use pytest and the `caplog` and `tmp_path` fixtures. Existing tests already use both.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
| - | - | - | - |
| Merge conflict with pull request #4813 | High | Medium | Wait for the merge (FR-014). Rebase after the merge. Read `data_exporter.py` lines 405 to 415 again before editing. |
| Caution: operators lose a summary table | Medium | Low | The INFO lines keep the counts. The changelog fragment names the removal. |
| An obsolete test fails after a table removal | Medium | Low | Task T013 removes the obsolete tests in the same change. |
| `symbol-diff` reports the removed PrettyTable imports | High | Low | Decision D-15 documents the intended removals in the pull request body. |
| Caution: a warning carries exception text that holds a rejected value | Low | Medium | Decision D-8 keeps the warnings. A follow-up audit issue reviews them. |
| Caution: DEBUG tables outside the exporter package still show values | High | Medium | Decision D-9 records the three locations. A follow-up issue owns them. |
| Warning: old log files keep exported values until an operator removes them | High | Medium | Decision D-14 leaves old logs unchanged. Operators review `data/script.log` after the change. |
| Coverage drops below the gate | Low | Low | Each changed branch has a test. The coverage gate runs in T-LOCAL-GATES. |

## Rollback Steps

1. Before the merge, revert the commit on the work branch. Push with `--force-with-lease`, and close the pull request.
2. After the merge, do not push to the branch. Open a new issue and branch again from `main`.
3. Warning: a commit that you push after a squash merge becomes an orphan. Use a new issue for every later change.
4. No data migration exists. The rollback restores the previous log lines only.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| Constitution VII: no per-call INFO line in `_split_full_address` and `_split_address` (D-7) | The issue requires aggregate-only action logs. A per-call line prints once for each row. | A per-row INFO line adds noise and breaks the aggregate-only rule. |
| Folder debt: `changelog.d/` holds 335 direct files (RV-06) | Constitution I allows one unique fragment for each change. | Moving fragments is out of scope. A follow-up issue tracks the remediation. |
| Folder debt: `tests/unit/export/` holds 55 entries (RV-08) | The new tests join existing files. | A new test module adds a child to a noncompliant folder. |
| Class debt: `OrgInventoryExporter` holds 39 method definitions (RV-18) | The change removes two methods and adds none. | Splitting the class is outside this change. |

## Implementation Outline

1. Wait for pull request #4813 to merge. Create the worktree and branch from `main` (T001).
2. Add the absence tests and the round-trip test. Confirm that six tests fail before the fix (T002 to T006).
3. Change the four exporter files (T007 to T010).
4. Remove the obsolete tests and patches in the same change (T011, with parts of T008 and T010).
5. Update the security document and add the changelog fragment (T012 and T013).
6. Audit the changed lines for comments, logging format, and forbidden patterns (T014).
7. Run every applicable local gate, commit, push, open the pull request, wait for CI, and merge (T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE).
