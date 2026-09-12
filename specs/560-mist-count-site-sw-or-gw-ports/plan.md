# Implementation Plan: countSiteSwOrGwPorts Menu Item

**Branch**: `560-mist-count-site-sw-or-gw-ports` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/560-mist-count-site-sw-or-gw-ports/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/stats/ports/count` (operationId `countSiteSwOrGwPorts`)
to retrieve aggregate counts of switch and gateway ports at a site, optionally grouped
by a `distinct` attribute (for example `up`, `speed`, `poe_on`, `neighbor_system_name`).
The menu item prompts the user for a `site_id` and an optional `distinct` field via
`safe_input()`, invokes the `mistapi` SDK at
`mistapi.api.v1.sites.stats.ports.count.countSiteSwOrGwPorts()`, flattens the envelope
plus the nested `results[]` array into two related output streams (one summary row +
N bucket rows), and persists both through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts. The new operation is
proposed as menu number **89** -- the next contiguous integer in the Stats cluster
(80-91), adjacent to the existing port-search and switch-metrics operations.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend on Podman Quadlet.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known site from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy/destructive skip list (14, 18, 63-65, 90-100) is unaffected --
new item 89 sits squarely inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical sites
(the endpoint returns counts, not raw port records, and the default `limit=100` keeps
the result set bounded). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` govern back-off; this endpoint is light enough that no special
tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); 5-Item Rule applies to the new method (<=25 lines, <=5 params, <=5
blocks).
**Scale/Scope**: One new public menu method (~20 lines) on the existing site-stats
class that owns port-search and switch-metrics (or a new `SitePortStatsExporter` class
if the existing site-stats class is already at the Five-Item Rule cap -- see Project
Structure below). Two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. Two new
CSV/SQLite tables (`site_port_count_summary` and `site_port_count_results`). One menu
registration entry. One README operation-count bump. One CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_site_port_counts()` stays under 25
  lines, takes <=4 parameters (`self`, `site_id`, `distinct_field`, `extra_filters`),
  and contains <=5 logical blocks (prompt -> validate -> API call -> flatten
  summary + buckets -> DataExporter calls). Hierarchy is unchanged: one new method on
  an existing class (or one small new class if the existing class is already at the
  child-count cap). No new packages, modules, or top-level constants are introduced.
  Two flattening helpers are inlined as single comprehension blocks; if either grows
  past 5 lines during implementation, they are extracted to private helpers on the
  same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing site-stats
  class that owns the related `searchSiteSwOrGwPorts` export (the class referenced by
  Menus 14, 29, 31 per the enriched API doc's "MistHelper Notes"). No standalone
  wrapper function is introduced; the menu dispatch in the main loop references the
  class method directly. If the existing class is already at five children (a level-4
  Five-Item Rule cap), a new `SitePortStatsExporter` class is created in
  `MistHelper.py`, named with full words per Principle II, and the existing
  port-search and switch-metrics methods are moved into it during the same edit so the
  cluster remains cohesive. Variable names use full words (`distinct_field`,
  `bucket_row`, `port_count_summary`); no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"site_port_count:site_id"`, `"site_port_count:distinct"`,
  `"site_port_count:limit"`) so SSH / container EOF exits cleanly with code 0 and no
  traceback. The endpoint is strictly read-only (HTTP GET) with no destructive side
  effect, so no typed destructive-confirmation gate is required. The `site_id` is
  validated against the Mist UUID shape via the existing `is_valid_uuid()` helper
  before the API call; on validation failure the method logs a `WARNING` and returns
  early. API token is loaded from `.env` via the existing `mistapi.APISession` and is
  never logged. The `distinct` field, when supplied, is validated against the enum of
  query-parameter names declared in `spec.md` to avoid sending arbitrary user input
  unchecked.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 89 countSiteSwOrGwPorts` -> `git
  push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch`
  -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Counting site %s ports distinct=%s"); `DEBUG`
  after the call with bucket counts ("Port count: total=%d buckets=%d");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. No secrets, tokens, or full request URLs are
  logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, in the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries, and in the menu registration line will
  carry an inline `#` comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  site-port-stats menu cluster, including the `searchSiteSwOrGwPorts` method invoked
  by Menus 14, 29, 31) receive comments in the same PR to keep the block coherent
  per the editing-existing-code clause of Principle VI.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each prompt, before the SDK call, before each flatten,
  before each DataExporter write; `logging.debug(...)` after each with a result count
  or summary. The `DataExporter` call already emits its own per-backend log lines;
  the new method does not duplicate them. Adjacent uncommented `searchSiteSwOrGwPorts`
  log statements (if any are missing the after-log pair) are repaired in the same
  PR per the editing-existing-code clause of Principle VII.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/560-mist-count-site-sw-or-gw-ports/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_site_sw_or_gw_ports.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the site-port-stats class (existing class that
                         # owns searchSiteSwOrGwPorts; promoted to SitePortStatsExporter
                         # only if the existing class is at the Five-Item Rule cap),
                         # plus two new ENDPOINT_PRIMARY_KEY_STRATEGIES entries and the
                         # menu 89 registration line. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 89.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 89.
data/                    # Runtime output target (existing dir; no schema migration
                         # required beyond the new SQLite tables created on first
                         # write by DataExporter).
documentation/api/sites/GET_sites_site_id_stats_ports_count.md  # Source of truth for
                         # the HTTP and response schema; consulted, not modified.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing site-port-stats class in `MistHelper.py` (the same class
that owns `searchSiteSwOrGwPorts`, used by Menus 14, 29, 31 per the enriched API doc).
If that class is already at the Five-Item Rule cap of five public methods, a new
`SitePortStatsExporter` class is created and the related port methods are moved into
it during the same edit, keeping the cluster cohesive and the Five-Item Rule satisfied
at the class level. The menu number proposal is **89**, chosen because operations 80-91
are the Stats cluster and 89 is the next contiguous integer that pairs naturally with
the existing port-search and switch-metrics operations. The full menu list is
re-verified at task generation time; if 89 collides with an in-flight feature branch,
the next free integer in the 80-91 cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified.**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/count_site_sw_or_gw_ports.md`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The skeleton in `quickstart.md` confirms
  <=25 lines, <=4 parameters, <=5 logical blocks. The two new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries are simple dict inserts (no level-5
  hierarchy explosion). If the existing site-port-stats class is at five public
  methods, `SitePortStatsExporter` keeps each class node at <=5 children.
- **Principle II (Class-Based)**: PASS -- All work lives on a single class. No
  wrappers introduced. Flattening helpers (`_flatten_port_count_summary`,
  `_flatten_port_count_buckets`), if needed, are added as private methods on the
  same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call. The
  `distinct` parameter is validated against the spec.md enum before being passed
  to the SDK.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The `quickstart.md` skeleton shows the
  expected comment density on every executable line, including the two PK strategy
  entries and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The `quickstart.md` skeleton enumerates
  the before/after log pairs for every meaningful action (prompt, validate, API
  call, flatten summary, flatten buckets, export summary, export buckets).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
