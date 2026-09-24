# Implementation Plan: Menu 270 mode 4, the closed Marvis Actions report

**Branch**: `feat/3342-marvis-closed-report` | **Date**: 2026-09-24 | **Spec**: [spec.md](./spec.md)

**Issue**: #3342 | **Research**: [research.md](./research.md)

## Summary

Add mode 4 to menu 270. Mode 4 exports the closed Marvis Actions only. It uses
the same three read requests, the same filter prompts, and the same export file
as mode 1. The filter tables show a new Closed column in every mode. In mode 4,
the tables show only the topics that hold a closed action. The export logs one
caution line when a row holds a status key that MistHelper does not know. The
operations portal offers mode 4 as a report-only choice. No control changes, so
the portal answer order stays the same.

## Technical Context

**Language**: Python 3.13 or newer.

**Dependencies**: `mistapi` 0.64 (installed). No new dependency.

**Storage**: No schema change. Mode 4 writes `OrgMarvisActions.csv` and the
strategy `listOrgMarvisActions`, as mode 1 does.

**Testing**: `pytest`, `hypothesis`, and `pytest-playwright`.

**Target platform**: Windows 11 for local work, and the Linux container for the
deployment.

**Performance goal**: A mode 4 run sends the same requests as a mode 1 run. It
sends one schema read and one list read for each 1,000 rows. It also sends one
site read for each 1,000 sites.

**Constraints**: The 5-Item Rule. `selection.py` already holds five classes, and
`MarvisTopicSelector` already holds five public methods. The portal feeds its
answers in position order, so the six controls must not change.

## Constitution Check

| Principle | Verdict | How this plan complies |
| - | - | - |
| I. Five-Item Rule | Pass | No new class, module, or public method. Each changed function stays at 25 lines or fewer. |
| II. Class-Based Architecture | Pass | The change stays inside the current classes. No wrapper function. |
| III. Safety-First | Pass | Mode 4 reads only. The default mode stays mode 1. The resolve path does not change. |
| IV. Full Deployment Pipeline | Pass | Every gate runs locally first, then one pull request runs the required checks. |
| V. Observability | Pass | The export logs the status mix and the caution line before the write. |
| VI. Inline Comments | Pass | Every changed executable line carries an inline comment. |
| VII. Action Logging | Pass | The current action lines stay. The new stop lines and the caution line use `DISPLAY_LEVEL`. |
| Database Keys | Pass | No new endpoint name. The current strategy serves mode 4. |
| Data Directory | Pass | The export lands under `data/`. |

## Complexity Tracking

No deviation. The design adds two constant tables and one property instead of a
new class. Research R8 states the reason.

## Module Design

### `src/marvis/actions/selection.py`

| Item | Change |
| - | - |
| `MODE_EXPORT_CLOSED` | New constant `"4"`. |
| `MODES` | Add `MODE_EXPORT_CLOSED` at the end. |
| `MODE_IS_OPEN_VALUES` | New table. Mode 1 keeps `{True, False}`. Modes 2 and 3 keep `{True}`. Mode 4 keeps `{False}`. |
| `MODE_ACTION_NOUNS` | New table. Mode 1 gives "Marvis Actions". Modes 2 and 3 give "open Marvis Actions". Mode 4 gives "closed Marvis Actions". |
| `MarvisTopicCount.closed_count` | New property: `total - open_count`. |
| `MarvisTopicSelector.__init__` | Take `mode` instead of `open_only`. Keep `MODE_IS_OPEN_VALUES[mode]`. |
| `MarvisTopicSelector.select` | Keep a record when its topic is selected and its `is_open` value is in the kept set. |
| `MarvisTopicSelector._count_topics` | Show a topic when at least one of its records has a kept `is_open` value. |
| `MarvisFilterPrompts.ask_mode` | Log the mode 4 line. Change the prompt text to name four modes. |
| `MarvisFilterPrompts._log_table` | Add the Closed column. Fit each column to its widest cell, and move the Name column to the end. See research R9. |

### `src/marvis/actions/operation.py`

| Item | Change |
| - | - |
| Module docstring | Modes 1, 2, and 4 write the report. |
| `run` | The refusal names four modes. |
| `_load` | Stop when no record has a kept `is_open` value. Name the actions with `MODE_ACTION_NOUNS`. |
| `_filter` | Build the selector with the mode. |
| `_refuse` | Name the actions with `MODE_ACTION_NOUNS`. |
| `_export` | Move the status summary into the new helper `_log_status_mix`. |
| `_log_status_mix` | New private helper. Log the status mix and the caution line for the unknown keys. |

### `web_portal/services/operation.py`

Add the choice `{"value": "4", "label": "4 - Export the closed Marvis Actions
(report only)"}` after mode 3. Change the comments that count the modes.

## Run Flow

1. `ask_mode` logs four mode lines and reads the answer.
2. `run` refuses an answer outside `MODES`, before any API call.
3. `_load` reads the list, the schema, and the site names. If no record holds a
   kept `is_open` value, the run stops. The stop line names the actions of the
   mode.
4. `_filter` builds the selector with the mode. It asks the category prompt and
   the subcategory prompt. It then selects the kept records of the chosen topics.
5. `_export` logs the status mix and the caution line. It then writes the rows.

## Message Contract

| Event | Log line |
| - | - |
| Mode table | `  4. Export the closed Marvis Actions only` |
| Mode prompt | `Enter the mode number (1, 2, 3, or 4) [1]: ` |
| Bad mode | `MistHelper could not match the mode answer '<answer>'. Enter 1, 2, 3, or 4. No file was written.` |
| No closed action | `No closed Marvis Actions exist in this organization. No file was written.` |
| Empty filter | `No closed Marvis Actions match the filter. No file was written.` |
| Unknown status | `Caution: MistHelper does not know these status keys, so the report counts their actions as closed: '<key>'=<count>. Compare these actions with the Mist UI.` |
| Table header | `  No.  Key  Actions  Open  Closed  Name`. Each column fits its widest cell. The Name column comes last and holds no padding. |

The lines for modes 1, 2, and 3 do not change, except the refusal of a bad mode.

## Portal Contract

| Control | Change |
| - | - |
| `marvis_mode` | One new choice, value `4`, label `4 - Export the closed Marvis Actions (report only)`. |
| The other five controls | No change. |

## Test Strategy

| File | New or changed tests |
| - | - |
| `tests/unit/marvis/actions/test_selection.py` | The selector helper takes a mode. The mode 4 tables, the Closed column, the table layout, the mode 4 select, the mode table, and the prompt text. |
| `tests/unit/marvis/actions/test_console_visibility.py` | The mode 4 line, the column headings, the stop line, and the caution line on the SSH console. |
| `tests/unit/marvis/actions/test_operation.py` | The mode 4 export, the kept resolution columns, the stop line, the empty filter, the unknown status, and the new refusal. |
| `tests/unit/marvis/actions/test_portal_contract.py` | The four mode values, the mode 4 label, and two portal runs of mode 4. |
| `tests/unit/marvis/actions/test_properties.py` | Modes 2 and 4 split the mode 1 rows for any status mix. |
| `tests/e2e/test_marvis_actions_portal.py` | Four mode choices, the mode 4 label, and the answers that the browser sends for mode 4. |

## Validation Plan

1. Run `py_compile`, `ruff check .`, `black --check .`, and `mypy` with the
   `MYPY_PATHS` value of `.github/workflows/ci.yml`.
2. Run the menu 270 tests, the guardrail, and the browser tests.
3. Run the STE linter on every changed Markdown file and Python file.
4. Copy the changed files into `misthelper-app` with the class B method. Send HUP
   to the 8055 Gunicorn master only.
5. Run mode 4 and mode 2 from the operations portal with Playwright. Take a
   screenshot of the log viewer, and confirm that each table row holds one line.
6. Run mode 4 through SSH on port 2200.
7. Read `podman logs misthelper-app` and `data/script.log`.
8. Read the CSV file, the SQLite table, and the ArangoDB collection.

## Rollback

Revert the squash commit. Mode 4 adds no data shape, so a revert leaves every
stored row readable. Copy the reverted files into the container, and send HUP to
the 8055 Gunicorn master.

## Risks

| Risk | Mitigation |
| - | - |
| A saved portal answer `4` meant a bad answer before. | No saved answer used `4`. The old refusal test used `4` as an example only. The test now uses `5`. |
| A new open status counts as closed. | The caution line names each unknown key, and the report shows the raw key. |
| The live organization holds no open action. | The unit tests and the property test prove the split with mixed statuses. |
| PR #3284 changes other hunks of the portal file. | The change stays inside the menu 270 block. |
