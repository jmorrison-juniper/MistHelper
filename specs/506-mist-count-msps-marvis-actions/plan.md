# Implementation Plan: countMspsMarvisActions Menu Item

**Branch**: `506-mist-count-msps-marvis-actions` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/506-mist-count-msps-marvis-actions/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/suggestion/count` (operationId `countMspsMarvisActions`)
to retrieve a distinct-attribute breakdown of pending Marvis AI action suggestions
across an MSP's managed organizations. The menu item prompts the user for an
`msp_id` (falling back to the value in `.env`), optionally collects the `distinct`
attribute name and `limit`, invokes the `mistapi` SDK call
`mistapi.api.v1.msps.suggestion.count.countMspsMarvisActions()`, flattens the
`results[]` array (each row contains a `count` plus one dynamic attribute key) into
a single CSV/SQLite-friendly shape, and persists the data through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean upserts on repeated runs. The new
operation is proposed as menu number **96** -- the next available slot adjacent to
the existing MSP/insights cluster (60-96 Interactive Safe range), sitting just
above the Resource Intensive block at 97-101.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints). No syntax features beyond 3.13 are required.
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_MSP_ID` default). No new dependencies introduced.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend
when configured.
**Testing**: `python MistHelper.py --test` exercises the new menu item in
non-interactive mode using the `MIST_MSP_ID` value from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check
MistHelper.py`, `python -m black --check MistHelper.py`. The destructive-skip
list (14, 18, 63-65, 90-100) is unaffected -- menu 96 sits inside the default
sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change. Container detection
(`is_running_in_container()`) drives the session-isolation directory; no impact
on this menu item.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI
menu surface; no web UI changes.
**Performance Goals**: A single GET request completes in <=5 seconds for typical
MSP suggestion datasets (the endpoint returns one JSON document with a bounded
`results[]` array sized by `limit`, default 100). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` govern back-off; this endpoint is
light enough that no special tuning entry is required.
**Constraints**: ASCII-only logging (no Unicode/emoji); `safe_input()` for every
prompt; no secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); no fabricated MSP IDs in tests.
**Scale/Scope**: One new public menu method (~22 lines) on a new
`MspMarvisExportUtils` class (justified below -- the MSP/Marvis domain is not
currently represented and the 5-Item Rule discourages overloading an unrelated
class). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. Two CSV/SQLite
artifacts (one summary row table, one detail row table) written by
`DataExporter` on first run. One menu registration entry. One README operation
count bump. One CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_msp_marvis_actions_count()` stays under 25 lines, takes <=4
  parameters (`self`, `msp_id`, `distinct`, `limit`), and contains <=5
  logical blocks (prompt -> validate -> SDK call -> flatten results ->
  DataExporter call). One new class `MspMarvisExportUtils` is added inside
  `MistHelper.py`; the file's top-level class count stays well under any
  level-5 ceiling and the MSP-Marvis domain is cleanly separated. If the
  flatten step grows past 5 lines during implementation it is extracted to
  a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `MspMarvisExportUtils` class. A new class (rather than a free function)
  is required because no existing class owns MSP-tier Marvis operations,
  and overloading an unrelated class (e.g. `LicenseExportUtils`) would
  violate the 5-Item Rule for cohesion. No standalone wrapper function is
  introduced. The menu dispatch in the main loop references the class
  method directly. Variable names use full words (`marvis_action_row`,
  `distinct_attribute`); no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with explicit `context=` strings
  (`"msp_marvis_actions_count:msp_id"`,
  `"msp_marvis_actions_count:distinct"`,
  `"msp_marvis_actions_count:limit"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP
  GET) and contains no destructive side effects, so no
  typed-confirmation gate is required. `msp_id` is validated against the
  Mist UUID shape before the SDK call; on validation failure the method
  logs a warning and returns early. The `limit` input is coerced to int and
  clamped to the inclusive range [1, 1000]; on parse failure the SDK
  default of 100 is used. The API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` ->
  `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 countMspsMarvisActions` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs
  -> `gh run watch <run-id>` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call ("Fetching Marvis
  actions count for msp %s distinct=%s limit=%d"); `DEBUG` after the call
  with summary counts ("Marvis actions count: total=%d rows=%d");
  `WARNING` on 404, 403, or empty payload (Marvis license missing);
  `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are
  logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu
  registration line will carry an inline comment that explains *why* the
  line exists, not merely what it does. Blank lines, closing parentheses,
  and decorators are exempt per the constitution. Any adjacent uncommented
  lines in the touched menu-registration block get comments added in the
  same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each `safe_input()` prompt cluster,
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after the call with a result count,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write. The `DataExporter` call emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in
the Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/506-mist-count-msps-marvis-actions/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_msps_marvis_actions.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New MspMarvisExportUtils class with
                         # export_msp_marvis_actions_count() method,
                         # PK strategy entry, and menu 96 registration.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite tables created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on a new `MspMarvisExportUtils` class in `MistHelper.py`. The
new class is justified because MistHelper has no existing class that owns MSP +
Marvis operations, and shoehorning the method onto an unrelated class
(`LicenseExportUtils`, `WebSocketManager`, etc.) would violate Principle I's
cohesion guidance. The menu number proposal is **96**, chosen because
operations 60-96 are the Interactive Safe cluster and 96 is the next available
slot below the Resource Intensive block at 97-101. The full menu list will be
re-verified at task generation time; if 96 collides with an in-flight feature
branch, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_msps_marvis_actions.md`), the seven principles
are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion. The new
  `MspMarvisExportUtils` class begins with a single public method.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `MspMarvisExportUtils`. No wrappers introduced. Flattening helpers, if
  needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call. `limit`
  is clamped before transmission.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The quickstart shows the expected
  comment density on every executable line, including the PK strategy entry
  and menu registration line.
- **Principle VII (Action Logging)**: PASS -- The quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, SDK
  call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
