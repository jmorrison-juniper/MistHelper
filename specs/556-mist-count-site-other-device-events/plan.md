# Implementation Plan: countSiteOtherDeviceEvents Menu Item

**Branch**: `556-mist-count-site-other-device-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/556-mist-count-site-other-device-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/otherdevices/events/count` (operationId
`countSiteOtherDeviceEvents`) to return distinct-attribute event counts for
non-Juniper ("other") devices observed at a site. The menu item prompts the user
for a `site_id` via `safe_input()`, optionally collects the `distinct`, `type`,
`start`, `end`, `duration`, and `limit` query parameters (with documented
defaults), invokes the `mistapi` SDK function
`mistapi.api.v1.sites.otherdevices.events.count.countSiteOtherDeviceEvents()`,
flattens the response (a single summary row plus N grouped count rows) and
persists the result through `DataExporter.write_with_format_selection()` so
CSV, SQLite, and ArangoDB+Redis backends all receive consistent output. A new
entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` to keep SQLite upserts
clean on repeated runs. The new operation is proposed as menu number **197** --
a new slot above the current 194-item ceiling, reserved for the read-only
event/count cataloging cluster created by the broader OpenAPI cataloging
effort. If 197 collides with an in-flight feature branch, the next free
integer above 194 is used.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache
backend. Two new tables: `site_other_device_events_count_summary` (one row per
run) and `site_other_device_events_count_results` (N rows, one per distinct
group).
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known site from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 197 sits outside the documented
heavy / destructive skip list (14, 18, 63-65, 90-100), so the default test
sweep includes it.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
sites. The endpoint is lightweight (returns counts, not full events) so default
adaptive delay metrics (`delay_metrics.json`, `tuning_data.json`) need no
endpoint-specific tuning.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); 5-Item Rule (<=25 lines / <=5 params /
<=5 blocks per method).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteOtherDeviceExportUtils` class (or, if that class does not yet exist,
a single new class of the same name and pattern; see Project Structure
section below for the explicit decision). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. Two new SQLite tables auto-created on
first write by `DataExporter`. One menu registration entry. One README
operation-count bump. One CHANGELOG line. No new third-party dependencies,
no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_site_other_device_events_count()` stays under 25 lines, takes <=4
  parameters (`self`, `site_id`, `distinct`, `time_window`), and contains <=5
  logical blocks (prompt -> validate -> API call -> flatten -> DataExporter
  call). Hierarchy is unchanged: at most one new class is added to the
  existing single-file monolith, holding a single new public method (plus an
  optional inline flatten helper if it exceeds 5 lines during implementation).
  No new packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the
  `SiteOtherDeviceExportUtils` class (extend if present; create if absent --
  see Project Structure decision). No standalone wrapper function is
  introduced. The menu dispatch in the main loop references the class method
  directly. Variable names use full words (`distinct_attribute`,
  `time_window`, `summary_row`, `count_results`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings
  (`"site_other_device_events_count:site_id"`,
  `"site_other_device_events_count:distinct"`,
  `"site_other_device_events_count:duration"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. The
  `site_id` is validated against the Mist UUID shape before the API call; on
  validation failure the method logs a `WARNING` and returns early. The API
  token comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 197 countSiteOtherDeviceEvents` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification. No
  pipeline step is skipped.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style formatting.
  `INFO` is emitted before the API call ("Counting other-device events for
  site %s distinct=%s window=%s"); `DEBUG` after the call with summary counts
  ("Count response: total=%d groups=%d limit=%d"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception via `logging.exception` with full
  traceback. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line
  carries an inline comment that explains *why* the line exists, not merely
  what it does. Blank lines, closing parentheses, and decorators are exempt
  per the constitution. Any uncommented adjacent lines in the touched block
  (the existing site-otherdevice menu cluster or its neighbors) receive
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result count; `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten with row count; `logging.info(...)` before
  write, `logging.debug(...)` after write. The `DataExporter` call already
  emits its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/556-mist-count-site-other-device-events/
+-- plan.md              # This file
+-- spec.md              # Pre-existing feature spec
+-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
+-- data-model.md        # Phase 1 - response entities + DDL + PK registration
+-- quickstart.md        # Phase 1 - local run + .env + quality gates
+-- contracts/
|   +-- count_site_other_device_events.md   # Phase 1 - HTTP + SDK contract
+-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteOtherDeviceExportUtils class +
                         #   PK strategy entry + menu 197 registration.
                         #   No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table
                         #   for op 197.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing
                         #   menu 197 addition.
data/                    # Runtime output target (existing dir, no schema
                         #   migration needed beyond the two new SQLite
                         #   tables auto-created on first run by
                         #   DataExporter).
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the `SiteOtherDeviceExportUtils` class in
`MistHelper.py`. If that class is not yet present in the monolith at
implementation time, it is created in the same PR following the existing
pattern used by sibling classes (e.g. `GatewayExportUtils`, `LicenseExportUtils`)
and is placed adjacent to the other site-scoped export utilities. Creating
this class -- rather than parking the method on an unrelated class -- keeps
Principle II (Class-Based Architecture, No Wrappers) and the Five-Item Rule
both satisfied: each export-utility class owns a small, semantically related
set of methods rather than ballooning a single grab-bag class.

The menu number proposal is **197**. The current menu ceiling is 194, and the
broader OpenAPI cataloging effort (specs 500-599+) adds many new read-only
endpoints. Rather than squeezing into the existing 1-194 layout, this catalog
cluster extends above 194 in a new "Read-only event/count catalog" group.
197 is the proposed slot for this endpoint; the full menu list is re-verified
at task generation time. If 197 collides with an in-flight feature branch,
the next free integer above 194 is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in
  `quickstart.md` and the contract in `contracts/` confirm <=25 lines, <=4
  parameters, <=5 logical blocks. The `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  dictionary entry is a single insert into an existing structure, so no
  level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `SiteOtherDeviceExportUtils`. No wrappers introduced. The optional flatten
  helper, if extracted, becomes a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows
  the expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action
  (prompt, validate, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
