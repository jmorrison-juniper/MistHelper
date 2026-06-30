# Implementation Plan: countSiteWirelessClientSessions Menu Item

**Branch**: `568-mist-count-site-wireless-client-sessions` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/568-mist-count-site-wireless-client-sessions/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/clients/sessions/count` (operationId
`countSiteWirelessClientSessions`) to return aggregated counts of wireless client
sessions at a site, grouped by a user-selected `distinct` attribute (SSID, AP, band,
client_family, client_manufacture, client_model, client_os, or wlan_id) over a chosen
time window. The new menu method prompts the user for `site_id`, the `distinct`
grouping attribute, and a `duration` via `safe_input()`, invokes the mistapi SDK,
splits the response into one summary row plus N result rows, and persists both via
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new pair of entries is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated polls of the
same site/distinct/window tuple. The proposed menu number is **91** -- the next
available slot at the top of the Site Stats cluster (80-91), adjacent to the existing
site-level wireless and session statistics exports.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_SITE_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using the site UUID from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 91 sits inside the default test
sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
must work without code change. Paths normalize through `os.path.join` /
`pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
sites. The endpoint accepts a `limit` query parameter (default 100); MistHelper
passes the user-selected `limit` or the SDK default. No pagination is required for
the count aggregation itself.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); 5-Item Rule on the new method.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteStatsExporter` class (the class that owns the adjacent site-level wireless
client and session exports). Two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`,
two new CSV/SQLite tables (`site_wireless_session_count_summary` and
`site_wireless_session_count_results`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules, no
new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_site_wireless_session_count()` stays under 25 lines, takes <=4
  parameters (`self`, `site_id`, `distinct_field`, `duration`), and contains <=5
  logical blocks (prompts -> validate -> API call -> flatten summary -> flatten
  results -> DataExporter calls; the two write calls share the export block).
  Hierarchy is unchanged: one new method on an existing class. No new packages,
  modules, or top-level constants are introduced. The two flatteners are
  inlined as single comprehension blocks; if either grows past 5 lines during
  implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `SiteStatsExporter` class (the same class that owns adjacent
  `searchSiteClientSessions` and site-level wireless client exports). No
  standalone wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`distinct_field`, `result_rows`, `summary_row`) -- no single-letter
  iterators outside list comprehensions.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings
  (`"site_wireless_session_count:site_id"`,
  `"site_wireless_session_count:distinct"`,
  `"site_wireless_session_count:duration"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. Site UUID
  is validated against the Mist UUID shape via the existing `is_valid_uuid()`
  helper before the API call; on validation failure the method logs a warning
  and returns early. The `distinct_field` value is validated against an allow
  list (`ssid`, `ap`, `band`, `client_family`, `client_manufacture`,
  `client_model`, `client_os`, `wlan_id`) -- any other value is logged as a
  warning and the method returns early. API token comes from `.env` via the
  existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 91
  countSiteWirelessClientSessions` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting wireless sessions for site
  %s by %s"); `DEBUG` after the call with summary counts
  ("Session count: distinct=%s total=%d results=%d"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new PK
  strategy dictionary entries, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing site stats menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, before the SDK call, before each
  flatten step, and before each export write; `logging.debug(...)` after the
  SDK call with a response summary, after each flatten with the row count, and
  after each export with the destination file/table. The DataExporter call
  already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/568-mist-count-site-wireless-client-sessions/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_wireless_client_sessions.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SiteStatsExporter class + 2 PK strategy
                         # entries + menu 91 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 91
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 91 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `SiteStatsExporter` class in `MistHelper.py` (the
same class that owns the other site-level wireless and session exports). The
menu number proposal is **91**, chosen because operations 80-91 are the Site
Stats cluster and 91 is the next available slot at the top of that cluster,
sitting comfortably below the Viewers block (92-96) and far below the
resource-intensive block at 96-101. The full menu list is re-verified at task
generation time; if 91 collides with an in-flight feature branch, the next free
integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` change is two single inserts into the
  existing dictionary, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `SiteStatsExporter`. No wrappers introduced. Flattening helpers, if needed,
  are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation and `distinct` allow-list checking
  happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entries and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (each prompt, API
  call, both flattens, both exports).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
