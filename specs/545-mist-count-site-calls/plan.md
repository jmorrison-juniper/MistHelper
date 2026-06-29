# Implementation Plan: countSiteCalls Menu Item

**Branch**: `545-mist-count-site-calls` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/545-mist-count-site-calls/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/stats/calls/count` (operationId `countSiteCalls`) to return
counts of VoIP/UC call statistics grouped by a caller-selected distinct attribute (rating,
app, etc.) for a single site. The menu item prompts the user via `safe_input()` for the
`site_id` (defaulting to `MIST_SITE_ID` from `.env`) plus the optional `distinct`,
`rating`, `app`, `start`, `end`, and `limit` query parameters, invokes the `mistapi` SDK
exactly once, flattens the envelope-plus-results structure into one summary row and zero
or more per-bucket count rows, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **96** -- the next available slot adjacent to the
existing safe Sites Stats exports cluster, sitting below the resource-intensive block at
97-101.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_ORG_ID`, optional `MIST_SITE_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. Two new SQLite tables are emitted on
first run by the DataExporter: `site_calls_count_summary` and `site_calls_count_buckets`.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using `MIST_SITE_ID` from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- menu 96 sits inside the
"Interactive Safe" cluster and is intentionally included in the standard sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change. Path joins use `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical sites
(the response is a single JSON envelope with a bounded `results` array capped at the
caller's `limit`, default 100). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining; 5-Item Rule on the new method
(<=25 lines, <=5 params, <=5 logical blocks).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteStatsExportUtils` class (the same class that owns adjacent
`getSiteCallsSummary`-style exports), two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
(one for the envelope summary, one for the flattened buckets), two new CSV/SQLite tables,
one menu registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_calls_count()` stays under 25
  lines, takes <=5 parameters (`self`, `site_id`, `distinct`, `time_range`, `limit`), and
  contains <=5 logical blocks (prompt -> API call -> flatten summary -> flatten buckets ->
  DataExporter call). Hierarchy is unchanged: one new method on an existing class. No new
  packages, modules, or top-level constants are introduced. If the buckets flatten grows
  past 5 lines during implementation, it is extracted to a private helper
  `_flatten_calls_count_buckets()` on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `SiteStatsExportUtils` class (the same class that owns adjacent Sites Stats exports).
  No standalone wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words (`bucket_row`,
  `distinct_attribute`, `start_epoch`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"site_calls_count:site_id"`, `"site_calls_count:distinct"`,
  `"site_calls_count:rating"`, `"site_calls_count:app"`, `"site_calls_count:start"`,
  `"site_calls_count:end"`, `"site_calls_count:limit"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. `site_id` is validated against
  the Mist UUID shape via the existing `is_valid_uuid()` helper before the API call;
  `limit` is coerced to int with a sane default (100). On validation failure the method
  logs a `WARNING` and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 countSiteCalls` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification. No deviation from the documented
  six-step pipeline.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Counting site calls for site %s by distinct=%s"); `DEBUG`
  after the call with summary counts ("Calls count envelope: total=%d buckets=%d");
  `WARNING` on 404 / empty payload ("No call stats returned for site %s"); `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets, tokens,
  full request URLs, or `.env` values are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entries, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing Sites Stats menu cluster) get comments
  added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result count,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten (for both
  summary and buckets), `logging.info(...)` before each write, `logging.debug(...)` after
  each write. The DataExporter call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/545-mist-count-site-calls/
|-- plan.md              # This file
|-- research.md          # Phase 0 -- SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 -- response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 -- local run + .env + quality gates
|-- contracts/
|   `-- count_site_calls.md   # Phase 1 -- HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteStatsExportUtils class + two PK strategy
                         # entries + menu 96 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite tables created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `SiteStatsExportUtils` class in `MistHelper.py` (the same class
that owns the other Sites Stats exports). If that class name does not yet exist in
`MistHelper.py` at implementation time, the method is added to the nearest existing
sites-stats class (e.g., `SiteExportUtils`), and any new class is justified in the
Complexity Tracking table below. The menu number proposal is **96**, chosen because the
60-96 range is the "Interactive Safe" cluster and 96 is the next available slot before
the resource-intensive block at 97-101. The full menu list will be re-verified at task
generation time; if 96 collides with an in-flight feature branch, the next free integer
in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The two
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` inserts are dictionary entries inside the existing
  literal, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `SiteStatsExportUtils` (or
  the nearest equivalent existing sites-stats class). No wrappers introduced. The
  buckets-flatten helper, if extracted, is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID and integer validation happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token, full URLs, or `.env` values.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entries and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompts, API call, summary
  flatten, buckets flatten, summary export, buckets export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
