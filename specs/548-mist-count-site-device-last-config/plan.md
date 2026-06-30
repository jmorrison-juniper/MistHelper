# Implementation Plan: countSiteDeviceLastConfig Menu Item

**Branch**: `548-mist-count-site-device-last-config` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/548-mist-count-site-device-last-config/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/devices/last_config/count` (operationId
`countSiteDeviceLastConfig`) to return the number of device-config-history entries
at a site, grouped by an optional `distinct` field and bounded by an optional time
window (`start` / `end` / `duration`). The menu item prompts the user for the
`site_id` via `safe_input()`, offers the five optional query parameters with safe
defaults (no `distinct`, no time bounds, `limit=100`), invokes
`mistapi.api.v1.sites.devices.last_config.countSiteDeviceLastConfig()`, flattens
the response object into one summary row plus zero or more per-group count rows,
and persists output through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly. The new
operation is proposed as menu number **72** -- the next available slot at the tail
of the site-devices cluster (60-72) and adjacent to the existing site-device
query operations.

## Technical Context

**Language/Version**: Python 3.13+ per constitution Technology & Compatibility
Constraints.
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
only permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend when
enabled.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode against the org/site identified in `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy/destructive skip list (14, 18,
63-65, 90-100) is unaffected -- menu 72 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200.
Both must work without code change.
**Project Type**: CLI tool. Single-file monolith `MistHelper.py` (~28K lines),
plus the optional Gunicorn web UI on 8055. This feature lives entirely in the
CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for the
default 1-day window; the endpoint returns a small JSON object (a few hundred
bytes when `distinct` is unset, up to a few KB when grouped by a high-cardinality
field bounded by `limit`). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; no special tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteDeviceExportUtils`-style class that owns site-device queries (the same
class that holds adjacent operations in the 60-72 cluster). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. Two SQLite tables on first run
(`site_device_last_config_count_summary` and
`site_device_last_config_count_results`). One menu registration entry, one
README operation-count bump, one CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `count_site_device_last_config()` stays under 25 lines, takes <=5 parameters
  (`self`, `site_id`, `distinct`, `time_window`, `limit`), and contains <=5
  logical blocks (prompt -> validate -> SDK call -> flatten summary + results
  -> DataExporter call). Hierarchy is unchanged: one new method on an existing
  class, one new dict entry, one menu registration. The flatten step is one
  comprehension; if it grows past 5 lines during implementation it is extracted
  to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  class that owns the adjacent site-device export operations in MistHelper.py
  (cluster 60-72). No standalone wrapper function is introduced. The menu
  dispatch references the bound method directly. Variable names use full words
  (`distinct_field`, `result_row`, `count_total`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All input is collected through `safe_input()` with
  explicit `context=` strings (`"count_last_config:site_id"`,
  `"count_last_config:distinct"`, `"count_last_config:duration"`,
  `"count_last_config:limit"`) so SSH/container EOF exits with code 0 and no
  traceback. The endpoint is strictly read-only (HTTP GET), so no destructive
  confirmation gate is required. `site_id` is validated against the Mist UUID
  shape before the API call; on validation failure the method logs a warning
  and returns early. Optional `limit` is clamped to `[1, 1000]` to protect
  against accidental bulk pulls. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 72 countSiteDeviceLastConfig`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs
  -> `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call
  ("Counting last_config history for site %s distinct=%s"); `DEBUG` after the
  call with summary counts ("Count: total=%d groups=%d"); `WARNING` on 404 /
  empty payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will
  carry an inline comment explaining *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a result count, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten, `logging.info(...)` before
  write, `logging.debug(...)` after write. The DataExporter call already emits
  its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table
below is intentionally empty.

## Project Structure

### Documentation (this feature)

```text
specs/548-mist-count-site-device-last-config/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_device_last_config.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the site-device export class + PK
                         # strategy entry + menu 72 registration. No new
                         # modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table
                         # for op 72.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing
                         # menu 72 addition.
data/                    # Runtime output target (existing dir). New SQLite
                         # tables are created on first run by DataExporter;
                         # no manual migration needed.
documentation/api/sites/GET_sites_site_id_devices_last_config_count.md
                         # Already exists; cited by research.md and the
                         # endpoint contract.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing site-device export class in `MistHelper.py`
(the same class that owns the adjacent operations in the 60-72 cluster, e.g.
the device queries and config-history operations). The menu number proposal
is **72** -- the next available slot at the tail of the site-devices cluster
(60-72) per the menu category table in
`.github/copilot-instructions.md`. The full menu list will be re-verified at
task generation time; if 72 collides with an in-flight feature branch, the
next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_site_device_last_config.md`), the seven
principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing
  site-device export class. No wrappers introduced. Flattening helpers, if
  needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation happens before the SDK call.
  `limit` is clamped.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
