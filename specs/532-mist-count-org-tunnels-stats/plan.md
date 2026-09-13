# Implementation Plan: countOrgTunnelsStats Menu Item

**Branch**: `532-mist-count-org-tunnels-stats` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/532-mist-count-org-tunnels-stats/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/stats/tunnels/count` (operationId `countOrgTunnelsStats`)
to return aggregate counts of tunnel stats grouped by a distinct attribute (per-tunnel
type: wxtunnel or wan). The menu item prompts the user for `org_id`, the `distinct`
group-by attribute, the optional `type` filter, and an optional row `limit` via
`safe_input()`, invokes the `mistapi` SDK, flattens the `results` array into one row per
distinct value (with the original distinct field name preserved alongside `org_id`,
`type`, and `count`), and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated polls upsert cleanly. The new operation is
proposed as menu number **91** -- the next available slot in the Stats cluster
(80-91), sitting adjacent to the existing org-tunnels search and peer-path stats
exports.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65, 90-100) needs review:
operation 91 currently falls *inside* the test skip range. Implementation will either
shift the proposed number to a slot outside the skip list (e.g. 92, the next viewer
slot) or, if 91 is kept, the test sweep is invoked manually for this op.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical tunnel
counts (the endpoint returns a small aggregate object; default `limit` is 100, with no
pagination beyond `limit`). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on an existing
`OrgStatsExportUtils`-style class (the same class cluster that owns the adjacent
`searchOrgTunnelsStats`, `searchOrgPeerPathsStats`, and `searchOrgBgpStats` exports;
exact class name confirmed at task-generation time), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table
(`org_tunnels_stats_count`), one menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `count_org_tunnels_stats()` stays under 25
  lines, takes <=5 parameters (`self`, `org_id`, `distinct`, `tunnel_type`, `limit`),
  and contains <=5 logical blocks (prompt -> validate -> API call -> flatten results
  -> DataExporter write). Hierarchy is unchanged: one new method on an existing class.
  The flatten step is a single comprehension; if it grows past 5 lines during
  implementation it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  org-tunnels-stats class (the same class that owns `searchOrgTunnelsStats`). No
  standalone wrapper function is introduced. The menu dispatch references the class
  method directly. Variable names use full words (`distinct_attribute`, `tunnel_row`)
  -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"count_org_tunnels_stats:org_id"`,
  `"count_org_tunnels_stats:distinct"`, `"count_org_tunnels_stats:type"`,
  `"count_org_tunnels_stats:limit"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Org ID is validated against the Mist UUID
  shape, `distinct` is constrained to the enum lists for each tunnel type per the
  enriched OpenAPI doc, and `limit` is coerced to a positive integer before the API
  call. On validation failure the method logs a warning and returns early. API token
  comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit with `version YY.MM.DD.HH.MM - add menu 91 countOrgTunnelsStats`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Counting org tunnel stats for org %s distinct=%s
  type=%s limit=%d"); `DEBUG` after the call with summary counts ("Tunnel count
  response: distinct=%s total=%d returned_rows=%d"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched block (the existing org-tunnels stats cluster) get
  comments added in the same PR.

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
specs/532-mist-count-org-tunnels-stats/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_tunnels_stats.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the org-tunnels-stats class + PK strategy +
                         # menu 91 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 91
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 91
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing org-tunnels-stats class in `MistHelper.py` (the same
class that owns `searchOrgTunnelsStats`). The menu number proposal is **91**, chosen
because operations 80-91 are the Stats cluster per
`.github/copilot-instructions.md` (Stats include `org_devices`, `org_bgp`, `org_ospf`,
`org_peer_paths`, `org_ports`, `org_tunnels`, plus their site equivalents) and 91 is
the next contiguous integer below the Viewer cluster at 92-96. If 91 collides with an
in-flight feature branch or falls inside the test skip block (14, 18, 63-65, 90-100),
the next free integer in the same cluster (e.g. 92) is used; final number is locked
at `/speckit.tasks` time after grep'ing `MistHelper.py` for the latest allocated menu
integer.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the org-tunnels-stats
  class. No wrappers introduced. The flatten helper, if needed, is added as a private
  method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation and enum validation for `distinct` / `type` happen before the
  SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
