# Implementation Plan: Menu 270 joins each Marvis Action to its Marvis alarm

**Branch**: `feat/3339-marvis-alarm-join` | **Date**: 2026-09-24 | **Spec**: [spec.md](./spec.md)

**Issue**: #3339, phase 1 | **Research**: [research.md](./research.md)

## Summary

Modes 1, 2, and 4 of menu 270 search the Marvis alarms of the organization one
time, after the filter prompts. A new module joins each alarm to its action
through the alarm `action_id` or the alarm `id`. Each export row then holds eight
alarm columns. The CSV file, the SQLite table, and the ArangoDB document receive
the same values. A failed alarm search leaves the columns empty, and the export
continues. The join sends no write request. Mode 3 does not change.

## Technical Context

**Language**: Python 3.13 or newer.

**Dependencies**: `mistapi` 0.64 (installed). No new dependency.

**Storage**: The table `OrgMarvisActions` and the collection
`listOrgMarvisActions` receive eight new columns. The strategy
`listOrgMarvisActions` does not change. The SQLite writer adds the new columns to
an old table, since pull request #3351.

**Testing**: `pytest`, `hypothesis`, and `pytest-playwright`.

**Target platform**: Windows 11 for local work, and the Linux container for the
deployment.

**Performance goal**: The join adds one alarm search request for each 1,000
alarms. The lab organization needs one request.

**Constraints**: The 5-Item Rule. `model.py` holds five classes, and
`operation.py` holds six classes. The portal feeds its answers in position
order, so the six controls must not change.

## Constitution Check

| Principle | Verdict | How this plan complies |
| - | - | - |
| I. Five-Item Rule | Pass | The package gets its fifth module, with two classes. No current module gets a class. Each new function stays at 25 lines or fewer. |
| II. Class-Based Architecture | Pass | The search is a client method. The join and the index are classes. No wrapper function. |
| III. Safety-First | Pass | The join reads only. A failed search leaves the columns empty. Mode 3 does not change. |
| IV. Full Deployment Pipeline | Pass | Every gate runs locally first, then one pull request runs the required checks. |
| V. Observability | Pass | The search logs each page. The join logs two count lines at the display level. |
| VI. Inline Comments | Pass | Every new executable line carries an inline comment. |
| VII. Action Logging | Pass | Each read logs an info line before and a debug line after. |
| Database Keys | Pass | No new endpoint name. The current `natural_pk` strategy on `uuid` serves the new columns. |
| Data Directory | Pass | The export lands under `data/`. |

## Complexity Tracking

`MarvisActionsClient` already holds more than five methods. The search adds one
public method and five private helpers to it. The client docstring states that
one class holds every Mist API call of the feature, and the NOC report depends on
that rule. A second client class would split the API calls, so the plan accepts
the larger class.

## Module Design

### `src/marvis/actions/client.py`

| Item | Change |
| - | - |
| Module docstring | Name the alarm search as a public endpoint. |
| `ALARM_GROUP` | New constant `"marvis"`. |
| `ALARM_PAGE_LIMIT` | New constant `1000`. |
| `MAX_ALARM_PAGES` | New constant `100`. |
| `MarvisListResult` | The docstring names one full read of a paged Mist list. |
| `search_marvis_alarms(start, end)` | New public method. It reads every page, keeps the Marvis rows, and returns a `MarvisListResult`. |
| `_read_first_alarm_page` | New private helper. It calls `searchOrgAlarms`. |
| `_read_next_alarm_page` | New private helper. It calls `mistapi.get_next`. |
| `_alarm_page_problem` | New private helper. A `None` page is a problem. Every other check reuses `_page_problem`. |
| `_marvis_alarms` | New private helper. It keeps the rows that are objects and that hold the group `marvis`. |
| `_alarm_guard_result` | New private helper. It logs the guard warning and returns the rows with `complete` False. |

### `src/marvis/actions/model.py`

| Item | Change |
| - | - |
| `MarvisFieldReader.iso_seconds` | New reader. It turns epoch seconds into ISO text through `iso`. |
| `MarvisActionRecord` | Eight new fields after `exported_at`, each with an empty default. The record then holds 51 columns. |
| `MarvisActionRecordBuilder.build` | The comment states that the alarm columns keep their defaults until the join. |

### `src/marvis/actions/alarms.py` (new)

| Item | Purpose |
| - | - |
| `ALARM_WINDOW_MARGIN_SECONDS` | `86_400`. The window starts one day before the oldest action. |
| `ALARM_MAX_WINDOW_SECONDS` | `400 * 86_400`. The widest window that the live test proved. |
| `ALARM_COLUMNS` | The eight column names, in record order. |
| `MarvisAlarmIndex` | Two maps of the alarm rows. `columns(uuid)` returns the eight values of one action, or an empty map. `unmatched_alarm_count(uuids)` counts the alarms without an action. |
| `MarvisAlarmJoin` | `window(documents, now)` returns the search window. `apply(selected, documents)` searches, joins, logs the counts, and returns the new records and documents. |

### `src/marvis/actions/operation.py`

| Item | Change |
| - | - |
| Imports | Import `MarvisAlarmJoin`. |
| Module docstring | The export rows hold the alarm columns. |
| `_export` | Call `MarvisAlarmJoin(loaded.client).apply(selected, loaded.documents)` after the status mix. Build the rows from the joined records. |

### `src/marvis/actions/__init__.py`

The docstring names five modules and states the purpose of `alarms`.

## Run Flow

1. The `run` method asks the mode. It reads the list and asks the two filter
   prompts.
2. The `_export` method logs the status mix.
3. The `window` method of `MarvisAlarmJoin` computes the window. It reads the
   `start_time` of the selected documents.
4. The `search_marvis_alarms` method of the client reads every alarm page.
5. If the search reports a problem, the join logs one warning. It returns the
   records and the documents without a change.
6. If the search works, `MarvisAlarmIndex` maps the alarms. The join copies the
   eight values into each record and each document. It then logs two count lines.
7. The `_export` method writes the rows and the documents. It then logs the
   completion line.

## Message Contract

| Event | Level | Log line |
| - | - | - |
| Search start | INFO | `Searching the Marvis alarms of org <org_id> from <start> to <end>` |
| Page read | INFO | `Reading Marvis alarm page <n>` |
| Search end | DEBUG | `Read <count> Marvis alarms on <pages> pages` |
| Refused search | WARNING | `The Marvis alarm search returned no usable result. <problem> The alarm columns stay empty.` |
| Guard | WARNING | `The Marvis alarm search stopped at page <n> before its last page. The join holds the first <count> alarms only.` |
| Join count | DISPLAY | `Marvis alarm join: <joined> of <total> exported actions have a Marvis alarm. <missing> have no alarm.` |
| Alarm count | DISPLAY | `Marvis alarms in the search window without an action in the list: <count>` |

No new line holds `could not`, `failed to`, or `error fetching`. The completion
line stays the last line of an export run.

## Data Contract

| Column | Source | Empty value |
| - | - | - |
| `alarm_id` | `id` | `""` |
| `alarm_type` | `type` | `""` |
| `alarm_status` | `status` | `""` |
| `alarm_resolved_time_iso` | `resolved_time`, epoch seconds | `""` |
| `alarm_acked` | `acked`, a JSON boolean | `None` |
| `alarm_acked_time_iso` | `acked_time`, epoch seconds | `""` |
| `alarm_ack_admin_name` | `ack_admin_name` | `""` |
| `alarm_note` | `note` | `""` |

## Test Strategy

| File | New or changed tests |
| - | - |
| `tests/unit/marvis/actions/conftest.py` | The `site_api` fixture returns an empty alarm page by default. |
| `tests/unit/marvis/actions/test_client.py` | The call values, the next links, a refused page, a `None` page, a repeated link, the guard, another group, a row that is not an object, and an empty page with a link. |
| `tests/unit/marvis/actions/test_alarms.py` (new) | The two keys, the key order, the `last_seen` rule, the eight values, the unmatched count, the window, the refused search, and the portal words. |
| `tests/unit/marvis/actions/test_model.py` | 51 columns, the last eight columns, the defaults, and `iso_seconds`. |
| `tests/unit/marvis/actions/test_properties.py` | `iso_seconds` never raises and returns ISO text or an empty string. The join never changes a column of the action. |
| `tests/unit/marvis/actions/test_operation.py` | The alarm columns in the rows and the documents of modes 1, 2, and 4. Mode 3 sends no search. A refused search still writes. The window start. |
| `tests/unit/marvis/actions/test_console_visibility.py` | The two count lines appear on the SSH console. |

## Validation Plan

1. Run `py_compile`, `ruff check .`, `black --check .`, and `mypy` with the
   `MYPY_PATHS` value of `.github/workflows/ci.yml`.
2. Run the menu 270 tests, the guardrail
   `tests/guardrails/test_marvis_actions_portal_exposure.py`, and the ratchet on
   the changed test files.
3. Run `bandit`, `radon cc` with a limit of 10, `pydocstyle`, and `vulture` on
   the changed source files.
4. Run the STE linter on every changed Markdown file and Python file.
5. Copy the changed files into `misthelper-app` with `podman cp`. Send HUP to the
   8055 Gunicorn master only. Log START and DONE lines in the coordination log.
6. Run mode 1 and mode 4 from the operations portal with Playwright.
7. Run mode 4 through SSH on port 2200.
8. Read `podman logs misthelper-app` and `data/script.log`.
9. Read the CSV file, the SQLite table, and the ArangoDB collection. Compare the
   alarm values of one joined action.

## Rollback

Revert the squash commit. Copy the reverted files into the container, and send
HUP to the 8055 Gunicorn master. The eight columns stay in the SQLite table and
in the old ArangoDB documents. A reader that selects its columns by name keeps
working.

## Risks

| Risk | Mitigation |
| - | - |
| Mist changes the join key. | The index reads two keys. The count line shows a join count of zero at once. |
| A next link loses the `search_after` value. | The repeated link check and the guard of 100 pages stop the read. |
| An old action has no alarm. | The count line states the number of actions without an alarm. The NOC report explains the retention limit. |
| The alarm search needs a larger role than the list read. | A refused search leaves the columns empty and logs the HTTP status. The export continues. |
| Pull request #3284 changes other hunks of the portal file. | This feature does not change the portal file. |
