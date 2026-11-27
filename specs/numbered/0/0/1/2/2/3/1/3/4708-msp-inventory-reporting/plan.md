# Implementation Plan: MSP inventory batch coverage

**Branch**: `fix/4708-msp-inventory-reporting` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record `specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/spec.md`. The route is the eight-digit base-5 form of 4708, which is `0 0 1 2 2 3 1 3`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place the supporting artifacts under `design/`.

## Summary

The MSP batch prints a processed count that equals the number of organization records. A skipped record and a failing runner both count. The change counts successful results instead. A partial batch gets a partial footer, partial heading labels, and a `_Partial` marker in each export name. A complete batch keeps its current output.

## Technical Context

- **Language/Version**: Python 3.15 or newer. `pyproject.toml` line 23 sets `requires-python = ">=3.15"`.
- **Primary Dependencies**: `mistapi>=0.64.0,<0.65` with 0.64.1 installed locally, `PrettyTable` for console tables, and the injected `DataExporter` writer.
- **Storage**: No new storage. Exports use `DataExporter.write_with_format_selection` at `src/mist/resources/inventory/org_device_inventory_msp.py` lines 382, 415, and 426.
- **Testing**: pytest with mocked collaborators, blocked sockets, and blocked DNS lookups. The test module holds 41 test functions today.
- **Target Platform**: Windows 11, macOS, and Linux.
- **Project Type**: Menu operation 13, batch mode 3, in the command-line tool.
- **Performance Goals**: No change. The batch stays sequential.
- **Constraints**: Existing test lines keep their positions. The baseline file `.github/test-quality-baseline.json` holds 30 lines that name this test module. New tests append at the end of the module.
- **Scale/Scope**: One source module, one test module, one changelog fragment, and this record. The source change adds about 60 lines.

## Constitution Check

Source: `.specify/memory/constitution.md`, version 1.9.0.

| Rule | Result | Reason |
| --- | --- | --- |
| Principle I, five-item rule | PASS with recorded debt | `OrgDeviceInventoryMSPOrchestrator` holds 18 methods, from line 227. The module holds 15 top-level functions. The change touches both. A separate remediation issue owns the split. |
| Principle II, class-based design | PASS | The change adds `_BatchCoverage`, a class with derived properties. It adds no wrapper function. |
| Principle III, safety-first | PASS | The change adds no keyboard input and no destructive operation. |
| Principle IV, deployment pipeline | PASS | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. |
| Principle V, ASCII logging | PASS | Each new log line and console line uses ASCII text. |
| Principle VI, inline comments | PASS | Each new executable line carries an inline comment that gives its purpose. |
| Principle VII, action logging | PASS | `_announce_batch_coverage` writes an info line before printing and a debug line after printing. |
| Mist Cloud constraints | PASS | The batch keeps `listMspOrgs` through mistapi. The change adds no direct HTTP request. |
| Output backends and data directory | PASS | Exports keep the `DataExporter` path. The exporter owns the `data/` location. |
| Natural keys | PASS | The organization `id` stays the key. The change adds no new key. |
| Release note | PASS | The change adds one fragment, `changelog.d/issue-4708-msp-inventory-reporting.md`. |
| SpecKit escalation | PASS | The change touches three files and changes an output contract. |
| Multi-agent git | PASS | Issue #4708 exists with the labels `bug`, `tests`, and `in-progress`. The branch name uses the type, the issue number, and a slug, as `AGENTS.md` requires. |
| Five children per directory | PASS | The feature root holds five children. The `design` folder holds five children. |

## Architecture

Call path on `main`:

1. Menu 13 registers `OrgDeviceInventorySummary.dispatch` in `MistHelper.py` line 6391.
2. The facade binds the batch to `OrgDeviceInventorySummary.execute_msp` in `src/mist/resources/inventory/org_device_inventory_summary_facade.py` lines 80-83.
3. `OrgDeviceInventoryMSPOrchestrator.execute_msp` (`org_device_inventory_msp.py` line 502) loads organizations through `_fetch_org_list` (line 245) and `_call_list_msp_orgs` (line 130). The SDK call sits at line 135.
4. `_process_orgs_batch` (line 488) calls `_process_org` (line 469) for each record. `_run_org_and_collect` (line 447) calls the per-organization runner `OrgDeviceInventorySummaryCore.run_for_org` in `src/mist/resources/inventory/org_device_inventory_summary.py` line 425.
5. The batch builds the coverage value and prints the footer. The combined reports use the value for headings and export names.

Design of the change:

| Component | Current state | Change |
| --- | --- | --- |
| `_COMPLETE_COVERAGE_LABEL` (new constant) | Not present | Holds `All Orgs`. Every default heading label uses this constant. |
| `_BatchCoverage` (new class, module level) | Not present | Frozen dataclass with `total` and `successful`. Properties: `skipped_or_failed`, `is_partial`, `heading_label`, and `file_marker`. |
| `_announce_batch_coverage` (new static method) | Not present | Logs an info line, prints the complete or partial footer, and logs a debug line. |
| `_process_org` (line 469) | Prints no line for a skipped record | Prints `Skipping {name}: missing organization ID`, where the name falls back to `unnamed record`. |
| `execute_msp` (line 502) | Prints `Processed {record count} organizations` | Builds `_BatchCoverage` from the record count and the result count. Calls `_announce_batch_coverage`. |
| `_build_combined_reports` (line 433) | Fixed prefix and fixed label | Adds a `coverage` argument with default `None`. Uses `file_marker` in the prefix and `heading_label` in the headings. |
| `_print_combined_model_report` (line 183), `_print_combined_version_report` (line 195), `_print_and_export_pivot` (line 369), `_display_combined_pivot_and_export` (line 391), `_emit_combined_model` (line 411), `_emit_combined_version` (line 422) | Print the literal `(All Orgs)` | Each adds a final `label` argument with default `_COMPLETE_COVERAGE_LABEL`. |

Constraints on the design:

- Each function keeps five parameters or fewer. `_print_and_export_pivot` takes five parameters after the change.
- `execute_msp` and `_announce_batch_coverage` each keep 25 lines or fewer.
- Existing calls in the test module stay valid through default arguments.
- New tests append at the end of the test module.

## File-by-File Change Map

| Path | Action | Purpose |
| --- | --- | --- |
| `src/mist/resources/inventory/org_device_inventory_msp.py` | Modify | Count successful results, print the partial footer and skipped lines, label partial headings, and add the `_Partial` export marker. |
| `tests/unit/inventory/test_org_device_inventory_msp.py` | Modify by appending | Add the `block_network` fixture and eight tests at the end of the module. Existing lines keep their positions. |
| `changelog.d/issue-4708-msp-inventory-reporting.md` | Add | One `Fixed` bullet that names issue #4708. |
| `specs/numbered/0/0/1/2/2/3/1/3/4708-msp-inventory-reporting/` | Add | This record. |

No documentation page changes. A search of `documentation/` and `README.md` finds no page that quotes the footer or the headings. The operator guide describes only the MSP scope lines, in `documentation/operator-guide.md` lines 566-617.

## Dependencies

The change adds no package, no environment variable, and no configuration key.

## Risks and Mitigations

| ID | Risk | Mitigation |
| --- | --- | --- |
| RK-01 | An operator script parses the old footer text. | The complete footer keeps its text. Only a partial batch prints the new text. The changelog names the change. |
| RK-02 | A consumer matches export names exactly. | Only a partial batch uses the `_Partial` name. `design/contracts/export.md` lists both name forms. |
| RK-03 | The test baseline records old line numbers. | New tests append at the end. Existing line numbers stay in place. The test-quality gate checks the diff. |
| RK-04 | The branch publishes before owner authorization. | Tasks T-PR and T-MERGE wait for owner authorization, as decision D-9 records. |
| RK-05 | Legacy commits leak into the repair. | The branch starts from `main`. No legacy commit is cherry-picked, as decision D-8 records. |
| RK-06 | The follow-up test content is unavailable. | FR-009 adds a new assertion test. The record does not depend on blob `841d9397`, as checks R-09 and R-10 show. |
| RK-07 | The live `listMspOrgs` response pages differently than the tool expects. | The live behavior stays unverified. Analysis item AN-10 names the gap. |
| RK-08 | A function exceeds the size or complexity limits. | Keep each function at 25 lines or fewer. Run the radon and pylint gates in T-LOCAL-GATES. |
| RK-09 | The full test gates run for a long time on Windows. | Run the focused module tests first. Run the full gates before the push. |

## Rollback

1. Revert the squash commit on `main` with a new pull request. Do not force-push.
2. The revert also removes `changelog.d/issue-4708-msp-inventory-reporting.md`.
3. Warning: a partial export that this change wrote carries `_Partial` in its name. Delete such a file only by its exact name, after the operator confirms that the file is not needed. Deletion removes data from `data/`.

## Verification

Run each gate in `design/quickstart.md` that applies to the changed files. Record each result in the pull request body, as `AGENTS.md` requires in its pull request section.
