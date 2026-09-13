# Implementation Plan: countOrgOtherDeviceEvents Menu Item

**Branch**: `524-mist-count-org-other-device-events` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/524-mist-count-org-other-device-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/otherdevices/events/count` (operationId
`countOrgOtherDeviceEvents`) to retrieve grouped counts of non-Juniper
("other") device events for an organization. The menu item prompts the user
for an `org_id` (with `MIST_ORG_ID` from `.env` as the default) via
`safe_input()`, plus optional `distinct`, `type`, `start`, `end`, `duration`,
and `limit` query parameters; invokes the `mistapi` SDK; flattens the
response (a summary header plus a `results` array of `{count, <dynamic
group key>}` objects) into one summary row plus N detail rows; and
persists the result through `DataExporter.write_with_format_selection()`
so CSV, SQLite, and ArangoDB+Redis backends all receive consistent
output. Two new entries are registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
for clean SQLite upserts on repeated runs. The new operation is proposed
as menu number **58** -- the next available slot in the Misc Safe Org
Exports sub-cluster (56-59), sitting adjacent to the existing safe org
event search/listing operations. The number is provisional and is
reconciled at `/speckit.tasks` time against the actual menu allocation
in `MistHelper.py`.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and
optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache
backend. Two new tables are introduced: `org_other_device_events_count_summary`
and `org_other_device_events_count_results`.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using the default org from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check
MistHelper.py`, `python -m black --check MistHelper.py`. Heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- new item
58 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for
typical group-count responses (this is a Mist `/count` endpoint with a
small bounded payload -- `total` plus up to `limit` group rows, default
`limit=100`). The adaptive delay system (`delay_metrics.json` and
`tuning_data.json`) governs back-off; no special tuning required for
this endpoint.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); `--fast` mode honored via existing
retry/concurrency knobs.
**Scale/Scope**: One new public menu method (~25 lines) on a focused new
class `OtherDeviceEventsCountExporter` (or, if a suitable "Other Devices"
export class already exists in `MistHelper.py`, an additional method on
that class -- decided at task time by grep). Two new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables, one menu
registration entry, one README operation-count bump, one CHANGELOG line.
No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_other_device_events_count()` stays under 25 lines, takes
  <=5 parameters (`self`, `org_id`, `distinct`, `type_filter`,
  `time_window`), and contains <=5 logical blocks (prompt -> validate ->
  API call -> flatten summary + results -> DataExporter writes). The two
  flatten helpers (`_flatten_count_summary`, `_flatten_count_results`)
  are inlined initially and extracted to private methods on the same
  class when either grows past 5 lines. Hierarchy is unchanged at the
  package and module levels: one new (or extended) class on the existing
  single-file monolith.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a
  semantically named class (`OtherDeviceEventsCountExporter`, or the
  existing "Other Devices" export class if grep finds one at task time).
  No standalone wrapper function is introduced. The menu dispatch in the
  main loop references the class method directly. Variable names use
  full words (`distinct_field`, `group_value`, `count_row`) -- no
  single-letter iterators. No `...existing code...` markers appear in
  the committed output.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with explicit `context=` strings
  (`"org_other_dev_events_count:org_id"`,
  `"org_other_dev_events_count:distinct"`,
  `"org_other_dev_events_count:type"`,
  `"org_other_dev_events_count:time_window"`,
  `"org_other_dev_events_count:limit"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. Org ID is validated against the Mist UUID shape via
  `is_valid_uuid()` before the API call; on validation failure the
  method logs a warning and returns early. API token comes from `.env`
  via the existing `mistapi.APISession` and is never logged. The
  optional `start`/`end`/`duration` inputs are sanitized to strings
  before being passed to the SDK to prevent path-traversal-style
  injection into URL query construction.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `ruff check` -> `black --check` -> commit with `version YY.MM.DD.HH.MM
  - add menu 58 countOrgOtherDeviceEvents` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification. No
  step is skipped.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call ("Counting other
  device events for org %s distinct=%s type=%s"); `DEBUG` after the
  call with summary counts ("Count response: total=%d distinct=%s
  result_rows=%d"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`.
  No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  PK strategy dictionary entries, and the menu registration line will
  carry an inline comment that explains *why* the line exists, not
  merely what it does. Blank lines, closing parentheses, and decorators
  are exempt per the constitution. Any uncommented adjacent lines in
  the touched block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each user prompt, `logging.debug(...)`
  after with normalized answer; `logging.info(...)` before the SDK
  call, the call itself, `logging.debug(...)` after with response
  counts; `logging.info(...)` before each flatten, `logging.debug(...)`
  after with row counts; `logging.info(...)` before each DataExporter
  write. The DataExporter call already emits its own per-backend log
  lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in
the Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/524-mist-count-org-other-device-events/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── count_org_other_device_events.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OtherDeviceEventsCountExporter class
                         # (or existing Other Devices class), + two PK strategy
                         # entries, + menu 58 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as
a new public method on a semantically named class. At task generation time,
`MistHelper.py` is grepped for any existing "Other Devices" export class
(e.g. `OtherDevicesExportUtils`, `OtherDevicesEventsExporter`); if found,
the new method joins that class. If not, a focused new class
`OtherDeviceEventsCountExporter` is introduced -- this is consistent with
the project's class-based architecture and avoids wrappers (Principle II).
The menu number proposal is **58**, chosen because operations 56-59 are
the Misc Safe Org Exports cluster and 58 is currently free (verified via
`grep -nE "^\s*58\s*[:,]" MistHelper.py` at task time; if 58 is already
allocated, the next free integer in 56-59 is used, falling back to the
next free slot inside the 20-26 Events sub-cluster).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline
  in `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical
  blocks. Two `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries are simple
  dict inserts (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on a single
  class. No wrappers introduced. Flatten helpers are private methods on
  the same class. Variable names are full words.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms
  the endpoint is GET only, with no destructive side effect.
  `safe_input()` is the documented prompt path. UUID validation
  happens before the SDK call. Optional query inputs are sanitized to
  strings.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design
  are ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows
  the expected comment density on every executable line, including the
  PK strategy entries and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action
  (each prompt, the API call, each flatten, each export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready
for `/speckit.tasks` to produce a task breakdown.
