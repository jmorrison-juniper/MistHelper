# Implementation Plan: countOrgWirelessClientEvents Menu Item

**Branch**: `538-mist-count-org-wireless-client-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/538-mist-count-org-wireless-client-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/clients/events/count` (operationId
`countOrgWirelessClientEvents`) to count wireless client events grouped by a
caller-supplied `distinct` attribute (event type, SSID, AP MAC, band, WLAN ID,
site ID, reason code, protocol). The menu item prompts the user for `org_id`,
an optional `distinct` field, an optional time window (`start` / `end` /
`duration`), and one or more optional narrowing filters, all via `safe_input()`.
It invokes the `mistapi` SDK once, flattens the count-result array into one row
per distinct bucket, attaches the request envelope (`distinct`, `start`, `end`,
`limit`, `total`) to every row, and persists output through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent records. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so SQLite upserts are clean across repeat
runs. The new operation is proposed as menu number **195** -- the next
available integer above the current top-of-range (194) and the conventional
location for a brand-new safe-org-export cluster member; final assignment is
re-verified during `/speckit.tasks`.

## Technical Context

**Language/Version**: Python 3.13+ (per the Technology & Compatibility
Constraints in `.specify/memory/constitution.md`).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
only permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; ArangoDB graph + Redis cache run as sibling containers when the
polyglot backend is selected. No schema migration is required beyond the new
SQLite table that `DataExporter` will create on first run from the registered
PK strategy.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode against a known org from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The default skip list (14, 18, 63-65,
90-100) is unaffected; menu 195 sits outside the destructive 154-194 block and
is included in the default test sweep.
**Target Platform**: Windows 11 + `.venv` for local dev; Podman Linux
container `ghcr.io/jmorrison-juniper/misthelper:latest` for production and
SSH-on-2200; both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines)
with optional Gunicorn web UI on port 8055. This feature lives entirely in
the CLI; no web-UI surface is added.
**Performance Goals**: Single GET request completes in <=5 seconds for a
24-hour window over a medium-size org. The endpoint returns an aggregate
count payload (one envelope plus up to `limit` distinct buckets, default 100),
so no pagination loop is required for typical use. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` govern back-off; this endpoint is
light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); 5-Item Rule applies to the new method.
**Scale/Scope**: One new public menu method (~22 lines) on a new class
`WirelessClientEventsCountUtils` (justified below), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
`org_wireless_client_events_count`, one menu registration entry, one
README operation-count bump and table row, one CHANGELOG line. No new
external dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_wireless_client_events_count()` stays under 25 lines, takes
  <=5 parameters (`self`, `org_id`, `distinct`, `time_window`, `filters`)
  with the last two being small dataclasses or dicts that aggregate the
  many optional query parameters into a single bag, and contains <=5
  logical blocks (prompt aggregation -> API call -> envelope capture ->
  results flatten -> DataExporter call). Parameter expansion into the SDK
  call happens through dict-unpacking, so the function signature itself
  never exceeds the five-parameter ceiling. Hierarchy is unchanged at
  levels 1-3; the level-4 addition is one new class on the existing
  module. No new top-level constants are introduced beyond the registered
  PK strategy entry.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  semantically named class `WirelessClientEventsCountUtils` rather than as
  a standalone wrapper function. A new class (vs. extending an existing
  one) is justified because the existing `WirelessClientsManager` and
  `EventsExportManager` classes already exceed Principle I limits if
  another method is added, and the count-aggregation behavior is distinct
  from search / listing behaviour and merits its own owner. The class
  follows the project's existing `*Manager` / `*Utils` naming pattern.
  Variable names use full words (`distinct_attribute`, `count_bucket`,
  `event_count_row`) -- no single-letter iterators. Menu dispatch in the
  main loop references the class method directly; no wrapper / shim layer
  is introduced.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with explicit `context=` strings
  (`"wireless_client_events_count:org_id"`,
  `"wireless_client_events_count:distinct"`,
  `"wireless_client_events_count:time_window"`,
  `"wireless_client_events_count:filters"`) so SSH and container EOF exit
  cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET); no typed destructive-confirmation gate is required. `org_id`
  is shape-validated against the Mist UUID pattern before the SDK call; on
  validation failure the method logs an ASCII warning and returns early.
  API token comes from `.env` via `mistapi.APISession` and is never
  logged. Filters that arrive as empty strings are dropped before being
  passed to the SDK so the request URL stays clean.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` ->
  `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 195 countOrgWirelessClientEvents` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs
  -> `gh run watch <run-id>` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call ("Counting wireless
  client events for org %s distinct=%s window=%s"); `DEBUG` after the
  call with summary counts ("Count response: total=%d buckets=%d
  start=%d end=%d"); `WARNING` on 404 / 401 / 403 / 429 / empty payload
  with the HTTP status code but never the token; `ERROR` on unexpected
  exception via `logging.exception(...)`. No tokens, full URLs with
  embedded credentials, or full response bodies are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `WirelessClientEventsCountUtils` class, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu
  registration line will carry an inline comment that explains *why* the
  line exists, not merely *what* it does. Blank lines, closing
  parentheses, decorators, and import lines are exempt per the
  constitution. Any uncommented adjacent lines in the touched block
  receive comments in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after
  pattern: `logging.info(...)` before the SDK call describing the request
  shape, the SDK call itself, `logging.debug(...)` after with response
  counts (envelope total + bucket length), `logging.info(...)` before the
  flatten step, `logging.debug(...)` after the flatten step with row
  count, `logging.info(...)` before
  `DataExporter.write_with_format_selection()`, `logging.debug(...)` after
  with the persisted row count. The DataExporter call already emits its
  own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/538-mist-count-org-wireless-client-events/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_wireless_client_events.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New class WirelessClientEventsCountUtils + menu method
                         # + PK strategy entry + menu 195 registration. Same
                         # single-file monolith; no new modules.
README.md                # Operation count bump and new row in the menu table
                         # for op 195.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing the
                         # menu 195 addition.
data/                    # Runtime output target (existing dir). DataExporter
                         # creates the new SQLite table on first run from the
                         # registered PK strategy. CSV file lands here as
                         # org_wireless_client_events_count_<org_id>_<distinct>.csv.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
public method on the new `WirelessClientEventsCountUtils` class in
`MistHelper.py`. A new class (rather than extension of an existing one) is
chosen because the closest candidates (`WirelessClientsManager`,
`EventsExportManager`) are already at or near their Principle I children-per-
class ceiling, and the count-aggregation behavior is semantically distinct
from search / listing / detail behavior. The menu number proposal is **195**,
the next integer above the current 194 top-of-range; this puts the new safe
read-only export immediately after the documented destructive cluster
(154-194) and keeps the new wireless-client-events count adjacent to its
future siblings (the other endpoint-count operations queued behind specs
539+). The full menu list is re-verified at task generation time; if 195
collides with an in-flight feature branch, the next free integer is used.

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

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary insert is a single
  entry on an existing structure; no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `WirelessClientEventsCountUtils` class. No wrappers introduced. Any
  helper introduced during implementation (e.g. a filter-bag builder)
  is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is
  the documented prompt path for every interactive value (`org_id`,
  `distinct`, `start`, `end`, `duration`, narrowing filters). UUID shape
  validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt
  aggregation, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
