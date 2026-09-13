# Implementation Plan: countSiteGuestAuthorizations Menu Item

**Branch**: `551-mist-count-site-guest-authorizations` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/551-mist-count-site-guest-authorizations/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/guests/count` (operationId `countSiteGuestAuthorizations`)
to retrieve count aggregates of authorized guests at a site, grouped by a caller-selected
distinct attribute (e.g. `ssid`, `wlan_id`, `auth_method`). The menu item prompts the user
for a `site_id` and optional `distinct` / time-window arguments via `safe_input()`, invokes
the `mistapi` SDK, flattens the `results` array into one row per distinct bucket plus a
single summary row capturing `total` / `start` / `end` / `limit` / `distinct`, and persists
the result through `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **94** -- the next available slot in the safe-org /
site-stats cluster (51-95), sitting adjacent to the existing `countOrgGuestAuthorizations`
entry already registered in the PK strategy table.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using a known site from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- new item 94 sits inside
the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical sites (the
endpoint returns a single aggregate JSON object, not a paginated entity list; `limit`
defaults to 100 distinct buckets). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~20 lines) on the existing `OrgSiteExporter`
class (which already owns guest-related exports such as `current_guests` at line 9650 of
`MistHelper.py`), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
`countSiteGuestAuthorizations`, one menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `count_site_guest_authorizations()` stays under
  25 lines, takes <=4 parameters (`self`, `site_id`, `distinct`, `duration`), and contains
  <=5 logical blocks (prompt -> validate -> API call -> flatten results -> DataExporter
  call). Hierarchy is unchanged: one new method on an existing class. The flatten step is
  a single list comprehension; if it grows past 5 lines during implementation it will be
  extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgSiteExporter` class (the same class that owns `current_guests` and other guest-data
  exports). No standalone wrapper function is introduced. The menu dispatch in the main
  loop references the class method directly. Variable names use full words
  (`bucket_row`, `summary_row`, `distinct_attr`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"count_site_guest_authorizations:site_id"`,
  `"count_site_guest_authorizations:distinct"`,
  `"count_site_guest_authorizations:duration"`) so SSH / container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. `site_id` is validated against the Mist UUID
  shape before the API call; on validation failure the method logs a warning and returns
  early. API token comes from `.env` via the existing `mistapi.APISession` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 94 countSiteGuestAuthorizations` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Counting guest authorizations for site %s distinct=%s");
  `DEBUG` after the call with summary counts ("Guest auth count: total=%d buckets=%d");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full traceback
  via `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line will
  carry an inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the existing `OrgSiteExporter` guest
  cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result count,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write, `logging.debug(...)` after write. The DataExporter
  call already emits its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/551-mist-count-site-guest-authorizations/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_guest_authorizations.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgSiteExporter class + PK strategy + menu 94
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 94
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 94 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `OrgSiteExporter` class in `MistHelper.py` (the same class that
owns `current_guests` and the other guest exports at lines ~9572-9670). The menu number
proposal is **94**, chosen because operations 51-95 are the Safe Org / Site Exports /
SLE cluster and 94 is the next available slot below the resource-intensive block at
96-101. The full menu list will be re-verified at task generation time; if 94 collides
with an in-flight feature branch, the next free integer below 95 is used.

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
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert into an existing
  structure, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgSiteExporter`. No
  wrappers introduced. Flatten helper, if needed, is a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is GET
  only, with no destructive side effect. `safe_input()` is the documented prompt path.
  UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
