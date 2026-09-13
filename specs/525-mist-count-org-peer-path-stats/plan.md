# Implementation Plan: countOrgPeerPathStats Menu Item

**Branch**: `525-mist-count-org-peer-path-stats` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/525-mist-count-org-peer-path-stats/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/stats/vpn_peers/count` (operationId `countOrgPeerPathStats`)
to return distinct-attribute counts of WAN-overlay VPN peer-path statistics for an
organization. The menu method prompts the user via `safe_input()` for `org_id`, the
`distinct` attribute to group by, and the time-window parameters (`start`, `end`,
`duration`, `limit`), invokes the `mistapi` SDK, flattens the `results` array (one row
per distinct value plus its `count`) along with the query envelope (`distinct`, `start`,
`end`, `limit`, `total`) into per-row context, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated polls of the
same (org, distinct, window) tuple. The new operation is proposed as menu number
**91** -- the next available slot inside the Stats viewer cluster (80-91), adjacent to
existing org-stats exports and well away from the destructive block at 154-194.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transitive transport); `python-dotenv` (`.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected --
proposed item 91 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local development; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
paths normalize via `pathlib.Path` and `os.path.join`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET completes in <=5 seconds for typical orgs; the
endpoint returns a small aggregate object (the `results` array is bounded by the
`limit` query parameter, default 100). Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` continue to govern back-off; this endpoint is light enough that
no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining; the SDK call MUST be the
only Mist-facing call (no direct `requests`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgStatsExportUtils` class (name verified at implementation time; if absent, a new
`VpnPeerStatsExportUtils` class is added per the no-wrappers rule). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite/CSV table
(`org_vpn_peer_path_stats_counts`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_peer_path_stats_count()` stays
  under 25 lines, takes <=5 parameters (`self`, `org_id`, `distinct`, `time_window`,
  `limit`), and contains <=5 logical blocks (prompt -> validate -> API call -> flatten
  results -> DataExporter call). Hierarchy is unchanged: one new method on an existing
  class. No new packages, modules, or top-level constants are introduced. If the
  flatten step exceeds 5 lines during implementation, it is extracted to a private
  helper `_flatten_peer_path_count_results()` on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgStatsExportUtils` class (the class that owns adjacent org-stats exports). No
  standalone wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`distinct_attribute`, `window_start`, `window_end`, `result_row`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_peer_path_stats_count:org_id"`,
  `"org_peer_path_stats_count:distinct"`,
  `"org_peer_path_stats_count:window"`, `"org_peer_path_stats_count:limit"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. Org ID
  is validated against the Mist UUID shape via the existing `is_valid_uuid()` helper
  before the API call; on validation failure the method logs a `WARNING` and returns
  early. The `limit` value is bounds-checked (1..1000); the `distinct` value is
  bounds-checked against the documented enum at SDK call time. API token comes from
  `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 91 countOrgPeerPathStats` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Counting VPN peer-path stats for org %s distinct=%s
  window=%s"); `DEBUG` after the call with summary counts ("Peer-path count returned
  total=%d result_groups=%d"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets,
  tokens, or full request URLs are logged. The endpoint is not paginated for the
  caller (the `limit` query param caps the `results` array server-side), so no
  per-page log noise.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched org-stats export cluster get comments added in the
  same PR (boy-scout coverage on the modified block).

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result count;
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten;
  `logging.info(...)` before write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/525-mist-count-org-peer-path-stats/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_peer_path_stats.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgStatsExportUtils class + PK strategy + menu
                         # 91 registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 91
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 91
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `OrgStatsExportUtils` class in `MistHelper.py` (the same
class that owns adjacent org-level stats exports). If the verification at
implementation time finds no such class, the implementation adds
`VpnPeerStatsExportUtils` as a new class -- never a standalone wrapper function. The
menu number proposal is **91**, chosen because operations 80-91 are the Stats viewer
cluster per `.github/copilot-instructions.md`, 91 is the last free slot before the
Resource Intensive block at 97-101, and is well separated from the destructive cluster
at 154-194. The final menu list will be re-verified at task generation time; if 91
collides with an in-flight feature branch, the next free integer in the same cluster
is used.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgStatsExportUtils`. No
  wrappers introduced. Flattening helper, if needed, is a private method on the same
  class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID and bounds validation happen before the SDK call.
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
