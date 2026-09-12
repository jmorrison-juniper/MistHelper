# Implementation Plan: countOrgBgpStats Menu Item

**Branch**: `510-mist-count-org-bgp-stats` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/510-mist-count-org-bgp-stats/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/stats/bgp_peers/count` (operationId `countOrgBgpStats`) to
return distinct-attribute count buckets over BGP peer statistics across an organization's
WAN edge gateways (SRX / SSR). The menu item prompts the user for the `org_id` (default
from `.env`), the BGP `state` filter, the `distinct` attribute to group by, and the
`limit` cap -- all via `safe_input()` -- then invokes the `mistapi` SDK, flattens the
response into one row per result bucket plus one summary row, and persists through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` to give SQLite a stable composite primary key for
clean upserts on repeated runs. The new operation is proposed as menu number **96** --
the next free slot adjacent to the existing org-stats / viewer cluster (80-95).

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transitive transport); `python-dotenv` (for `.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, and `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. Local
fallback SQLite file `data/mist_data.db`; CSV files land under `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend when active.
**Testing**: `python MistHelper.py --test` exercises the new menu item against the
org configured in `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Heavy /
destructive skip list (14, 18, 63-65, 90-100) intersects 90-95 but the proposed slot
96 sits inside the default test sweep range -- if the task generator must shift to 95
or lower, no change is needed; if it shifts into the 90-95 destructive skip block, the
test sweep must be adjusted to include it explicitly (read-only safe).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET completes in <=5 seconds (count endpoint returns a
small bucketed payload, not raw peer rows). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; this endpoint
is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); 5-Item Rule (<=25 lines, <=5 params, <=5 nesting blocks).
**Scale/Scope**: One new public method (~22 lines) on the existing `StatsExportUtils`
class (the same class that owns the related org-stats exports such as
`searchOrgBgpStats`), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new
SQLite table (`org_bgp_stats_count`) plus one summary table
(`org_bgp_stats_count_runs`), one menu registration line, one README operation-count
bump, one CHANGELOG line. No new dependencies, modules, or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_org_bgp_stats_count()` stays under 25
  lines and takes <=5 parameters (`self`, `org_id`, `state`, `distinct`, `limit`).
  Logical blocks: prompt -> validate -> API call -> flatten -> DataExporter call (5).
  Hierarchy is unchanged: one new method on an existing class. No new packages,
  modules, or top-level constants beyond the single dict entry. If the flattener
  grows past 5 lines during implementation it is extracted to a private helper on the
  same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `StatsExportUtils` class (same class that owns related org-stats exports). No
  standalone wrapper function is introduced. Menu dispatch references the class
  method directly. Variable names use full words (`distinct_field`,
  `bucket_row`, `summary_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_bgp_count:org_id"`, `"org_bgp_count:state"`,
  `"org_bgp_count:distinct"`, `"org_bgp_count:limit"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only (HTTP
  GET), so no typed destructive-confirmation gate is required. Org ID is validated
  against the Mist UUID shape before the API call; on validation failure the method
  logs a warning and returns early. API token comes from `.env` via
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96 countOrgBgpStats`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Counting org BGP stats org=%s state=%s
  distinct=%s"); `DEBUG` after the call with summary counts ("BGP count: total=%d
  buckets=%d"); `WARNING` on 404 / empty results; `ERROR` on unexpected exception
  via `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will
  carry an inline comment explaining *why* the line exists, not merely *what* it
  does. Blank lines, decorators, and closing parentheses are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  org-stats menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with bucket count, `logging.info(...)` before flatten, `logging.debug(...)`
  after flatten with row count, `logging.info(...)` before DataExporter write, and
  the existing DataExporter emits its own per-backend log lines (not duplicated by
  this method).

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/510-mist-count-org-bgp-stats/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_bgp_stats.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on StatsExportUtils class + PK strategy entry +
                         # menu 96 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run
                         # by DataExporter through ENDPOINT_PRIMARY_KEY_STRATEGIES)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `StatsExportUtils` class in `MistHelper.py` (the same
class that owns the related search/list org-stats exports). The menu number proposal
is **96**, chosen because operations 80-95 form the existing stats / viewer cluster
and 96 is the next free integer above spec 500's proposed 95. The full menu list will
be re-verified at task generation time; if 96 collides with an in-flight feature
branch, the next free integer in the same cluster is used.

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
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` insert is a single dict entry on an existing
  structure -- no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All new code lives on `StatsExportUtils`.
  No wrappers introduced. Flattener helper, if extracted, is a private method on the
  same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET-only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation runs before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart and
  `data-model.md` DDL snippet both demonstrate the expected comment density on every
  executable line, including the PK strategy entry.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
