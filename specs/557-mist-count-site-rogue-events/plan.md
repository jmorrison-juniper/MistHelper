# Implementation Plan: countSiteRogueEvents Menu Item

**Branch**: `557-mist-count-site-rogue-events` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/557-mist-count-site-rogue-events/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/rogues/events/count` (operationId `countSiteRogueEvents`)
to return a Count-by-Distinct-Attribute aggregation over rogue AP detection events for
a single site. The menu item prompts the user for a `site_id` and the `distinct`
attribute (default `type`), optionally accepts `start`/`end`/`duration` time-window
overrides and the standard filter set (`ssid`, `bssid`, `ap_mac`, `channel`,
`seen_on_lan`, `type`), invokes the `mistapi` SDK function
`mistapi.api.v1.sites.rogues.events.count.countSiteRogueEvents()`, and persists the
response through `DataExporter.write_with_format_selection()`. The response is a
summary object plus a `results` array of `{count, <distinct-value>}` rows; both are
flattened so CSV, SQLite, and ArangoDB+Redis backends all receive consistent output.
A new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` registers the
`auto_increment_with_unique` strategy with a uniqueness tuple of
`(site_id, distinct, distinct_value, start, end)` so repeated runs upsert cleanly.
The new operation is proposed as menu number **197** -- the next free slot above the
current destructive cluster ceiling at 194, kept in the safe-site-reads neighborhood
of existing rogue endpoints.

## Technical Context

**Language/Version**: Python 3.13+ (per Constitution Technology & Compatibility
constraints and `pyproject.toml`).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the only
permitted interface to Mist Cloud), `requests` (transitive transport), `python-dotenv`
(loading `MIST_HOST` and `MIST_API_TOKEN` from `.env`).
**Storage**: Multi-backend through `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
the ArangoDB + Redis polyglot backend handles graph + cache for sites with that
profile enabled.
**Testing**: `python MistHelper.py --test` exercises the menu item against a known
site loaded from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Menu
197 sits outside the heavy / destructive skip set (14, 18, 63-65, 90-100) so it is
included in the default `--test` sweep.
**Target Platform**: Windows 11 + venv for local development; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
must work without code change; pathing uses `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature is CLI-only; the web UI is not
touched.
**Performance Goals**: Single GET request <=5 seconds for a one-day window
(`duration=1d`, `limit=100`). The endpoint is a server-side aggregation, not a row
scan, so it returns a small payload; no pagination tuning is required. Adaptive
delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` wraps every
prompt; API token from `.env` is never logged; all output lands under `data/`;
hostnames and UUIDs validated before SDK calls; `--fast` mode honored via existing
concurrency limits.
**Scale/Scope**: One new public menu method (~22 lines) added to the existing
`RogueDataProcessor` class (the class that already owns adjacent rogue exports). One
new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. Two SQLite tables auto-created on
first run: `site_rogue_events_count_summary` (one row per invocation) and
`site_rogue_events_count_results` (N rows per invocation, one per distinct value).
One menu registration entry. One README operation-count bump. One CHANGELOG line.
No new dependencies, modules, or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_rogue_events_count()` stays
  under 25 lines, takes <=5 parameters (`self`, `site_id`, `distinct`, `duration`,
  `extra_filters_dict`), and contains <=5 logical blocks (prompt -> build kwargs ->
  API call -> flatten summary + results -> DataExporter write). Hierarchy is
  unchanged: one new method on an existing class, no new packages or modules. If the
  flatten step grows past 5 lines during implementation, it is extracted to a
  private helper on the same class (`_flatten_count_response`).

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The behavior is added as a method on the existing
  `RogueDataProcessor` class (same class that already owns the rogue inventory and
  rogue events search exports). No standalone wrapper function is introduced. The
  menu dispatch table in the main loop references the bound method directly.
  Identifier names are spelled in full (`distinct_attribute`, `count_result_row`)
  per the readability rule -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every prompt uses `safe_input(prompt, context=...)` with
  explicit context strings (`"site_rogue_count:site_id"`,
  `"site_rogue_count:distinct"`, `"site_rogue_count:duration"`) so SSH and container
  EOF paths exit cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET); no destructive confirmation gate is required.
  `site_id` is validated against the Mist UUID shape (regex
  `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`) before the SDK
  call; on validation failure the method logs a warning and returns early without
  hitting the API.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies unchanged:
  `python -m py_compile MistHelper.py` -> `python -m ruff check MistHelper.py` ->
  `python -m black --check MistHelper.py` -> commit with message
  `version YY.MM.DD.HH.MM - add menu 197 countSiteRogueEvents` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch <run-id>` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log statements use ASCII text and `%s` style formatting.
  `INFO` is emitted before the SDK call (`"Counting rogue events at site %s grouped
  by %s"`); `DEBUG` after the call with the total + result count (`"Rogue event count
  returned total=%d results=%d"`); `WARNING` on 404 or empty payload; `ERROR` with
  `logging.exception` on unexpected exceptions. No tokens, full URLs with secrets,
  or PII are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line carries an
  inline comment explaining the *why*, not just the *what*. Blank lines, lone
  closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines inside the touched block get comments added in the
  same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  immediately after with a result count, `logging.info(...)` before the flatten
  step, `logging.debug(...)` after the flatten with row counts,
  `logging.info(...)` before the DataExporter write. The DataExporter call already
  emits its own per-backend log lines and is not duplicated by the new method.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/557-mist-count-site-rogue-events/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md        # Phase 1 - response entities + DDL + PK registration entry
├── quickstart.md        # Phase 1 - local run + .env + example invocation + quality gates
├── contracts/
│   └── count_site_rogue_events.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on RogueDataProcessor class + new
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 197
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 197
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 197
data/                    # Runtime output target (existing directory). SQLite tables
                         # site_rogue_events_count_summary and
                         # site_rogue_events_count_results are auto-created by
                         # DataExporter on first run; no manual migration required.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `RogueDataProcessor` class in `MistHelper.py` (the
same class that owns the rogue inventory and rogue events search exports). The menu
number proposal is **197** -- the next free integer above the destructive cluster
ceiling at 194. This keeps the safe-site-reads neighbors (rogues, insights) close
together while leaving 195-196 free for any in-flight parallel specs that may land
first. The full menu list is re-verified at `/speckit.tasks` time; if 197 collides,
the next free integer in the same neighborhood is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_site_rogue_events.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` insert is one dictionary entry on the existing
  structure, so no hierarchy explosion at level 5.
- **Principle II (Class-Based)**: PASS -- All new work lives on
  `RogueDataProcessor`. No wrappers introduced. Flatten helper, if extracted, is a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- The contract confirms the endpoint is
  GET only with no destructive side effect. `safe_input()` wraps every prompt with
  named contexts. UUID validation precedes the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard deployment
  pipeline; menu 197 is in scope for the default `--test` sweep.
- **Principle V (Observability)**: PASS -- All log calls are ASCII with `%s`
  formatting and never include the API token or full request URL.
- **Principle VI (Inline Comments)**: PASS -- The quickstart shows the expected
  comment density on every executable line of the new method, including the PK
  strategy entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
