# Implementation Plan: countSiteOspfStats Menu Item

**Branch**: `555-mist-count-site-ospf-stats` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/555-mist-count-site-ospf-stats/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/stats/ospf_peers/count` (operationId `countSiteOspfStats`)
to retrieve aggregated counts of OSPF peer statistics grouped by a distinct attribute
(for example `neighbor`, `state`, `area`, `vrf_name`, `mac`). The menu item prompts the
user for `site_id` plus an optional `distinct` attribute and time window via
`safe_input()`, walks the cursor-paginated response using the `search_after` token,
flattens each `results[]` bucket into a flat row, and persists the rows through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and the polyglot
ArangoDB + Redis backend all stay consistent. A new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` registers a composite primary key so re-running the
menu item upserts cleanly rather than appending duplicates. The new operation is
proposed as menu number **89** -- the next available slot in the Safe Site Stats
cluster, adjacent to the existing site BGP/OSPF stat exports.

## Technical Context

**Language/Version**: Python 3.13+ per the Constitution's Technology & Compatibility
Constraints section. No new language features required.
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's SDK; the only permitted
interface to the Mist Cloud REST API); `requests` (transport, transitive); `python-dotenv`
for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers handle the graph + cache backend with no schema change
beyond the new primary-key strategy entry.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using `MIST_SITE_ID` from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy/destructive skip list (14, 18, 63-65, 90-100) is unchanged --
proposed menu 89 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both must
work without code change. Paths are joined via `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single page (`limit=100`, the API default) completes in <=5s.
Full paginated retrieval is bounded by the Mist API rate limit (5000 calls / token /
hour) and the adaptive delay system. The aggregate response is small (one row per
distinct attribute value), so total runtime is typically a few seconds.
**Constraints**: ASCII-only logging (no Unicode or emoji); `safe_input()` for every
prompt; API token never logged; all output under `data/`; Windows-safe path joining;
5-Item Rule for any new function (<=25 lines, <=5 params, <=5 nesting blocks).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SiteStatsExportUtils` class (the same class that already owns site BGP and site OSPF
search exports), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite
table (`site_ospf_peers_count`), one new menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules, no new
directories. If a `SiteStatsExportUtils` class does not yet exist by that exact name,
the method attaches to the closest analog (the class that owns
`searchSiteOspfStats` / `countSiteBgpStats`); a brand-new class is rejected to
avoid wrapper-class proliferation per Principle II.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_ospf_peers_count()` stays under
  25 lines, takes <=4 parameters (`self`, `site_id`, `distinct`, `time_window`), and
  contains <=5 logical blocks (prompt -> validate -> paginate-loop -> flatten ->
  DataExporter call). Pagination is a single `while` loop driven by the `next` /
  `search_after` cursor; if that loop's body grows past 5 lines during implementation
  it is extracted to a private helper on the same class. No new packages, modules, or
  top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing site-stats
  export class (the class that owns the related `searchSiteOspfStats` and
  `countSiteBgpStats` exports). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`distinct_attribute`, `pagination_cursor`, `count_row`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"site_ospf_peers_count:site_id"`,
  `"site_ospf_peers_count:distinct"`, `"site_ospf_peers_count:time_window"`) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET) -- no destructive-confirmation gate is required. Site
  ID is validated against the Mist UUID shape via the existing `is_valid_uuid()` helper
  before the API call; on validation failure the method logs `WARNING` and returns
  early. The API token is loaded by `mistapi.APISession` from `.env` and is never
  logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 89 countSiteOspfStats` -> `git push origin main`
  -> `.github/workflows/container-build.yml` runs -> `gh run watch <run-id>` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching OSPF peer count for site %s"),
  before each subsequent page fetch ("Fetching page %d via search_after cursor"),
  before flatten, and before export. `DEBUG` follows each action with a count
  ("Received %d distinct buckets on page %d", "Flattened %d rows total"). `WARNING`
  on HTTP 404 / empty payload; `ERROR` via `logging.exception` on unexpected
  exception. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  carries an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  Constitution. Any uncommented adjacent lines in the touched block (the existing
  site-stats export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before the first SDK call, the call itself, `logging.debug(...)`
  after with a result count; same before/after pair around each pagination iteration;
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten with row
  count; `logging.info(...)` before `DataExporter.write_with_format_selection`, which
  emits its own per-backend log lines (not duplicated by the menu method).

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table at the
bottom of this plan is intentionally empty.

## Project Structure

### Documentation (this feature)

```text
specs/555-mist-count-site-ospf-stats/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_ospf_stats.md   # Phase 1 - full HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the existing site-stats export class
                         # + new ENDPOINT_PRIMARY_KEY_STRATEGIES entry
                         # + menu 89 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 89
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 89 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing site-stats export class in `MistHelper.py` (the same
class that already owns `searchSiteOspfStats` and `countSiteBgpStats`). If the
analogous class name differs at implementation time, the closest existing class that
owns adjacent site stats operations is extended -- creating a fresh
`SiteOspfCountUtils` class would violate Principle II (no wrapper classes). The menu
number proposal is **89**, chosen because operations 80-91 are the Safe Site Stats
cluster, and 89 is the next free integer below the Viewer / Resource-Intensive
boundary at 92-101. The full menu list is re-verified at `/speckit.tasks` time; if
89 collides with an in-flight feature branch, the next free integer in the same
cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No Constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_site_ospf_stats.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method skeleton in `quickstart.md`
  confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary insert is a single literal entry; no
  level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing site-stats
  export class. No wrappers introduced. The pagination helper, if extracted, is a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call. Time-window
  inputs accept either relative strings ("-1d") or epoch seconds -- both validated
  before being passed to the SDK.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- All log statements in the design are
  ASCII-only with `%s` formatting and never include the API token, full URL, or
  pagination cursor (cursor is opaque but is logged only as `len(cursor)` to confirm
  paging without leaking the value).
- **Principle VI (Inline Comments)**: PASS -- `quickstart.md` shows the expected
  comment density on every executable line, including the PK strategy entry and the
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- `quickstart.md` enumerates the
  before/after log pairs for every meaningful action (prompt, validate, per-page API
  call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce the task breakdown.
