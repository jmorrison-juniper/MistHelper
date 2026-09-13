# Implementation Plan: getOrgStats Menu Item

**Branch**: `647-mist-get-org-stats` | **Date**: 2026-07-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/647-mist-get-org-stats/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/stats` (operationId `getOrgStats`) to retrieve the
organization-level statistics snapshot -- device counts (total / connected /
disconnected), site count, inventory count, session expiry, and the per-path SLE
user-minutes health array. The menu item prompts the user for `org_id` via
`safe_input()`, offers optional time-range query parameters (`start`, `end`,
`duration`), invokes `mistapi.api.v1.orgs.stats.getOrgStats()`, flattens the single
response object into one summary row plus zero-or-more SLE rows, and persists the
result through `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A composite-key entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated polls upsert cleanly
without duplicate snapshots. The new operation is proposed as menu number **58** --
the next available slot in the Safe Org Exports range (1-59), adjacent to the
existing org-level summary exports.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using the org UUID from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 58 sits inside the default test
sweep range and outside the heavy/destructive skip list (14, 18, 63-65, 90-100).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
targets must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical org
sizes. The endpoint returns one JSON object, not a list, so pagination cost is
irrelevant in the default case; adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token
never logged; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgExportUtils` class, one revised entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` plus
one new MistHelper-internal sub-table key, two new SQLite tables
(`org_stats_summary` and `org_stats_sle`), one menu registration entry, one
README operation-count bump, one CHANGELOG line. No new dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_stats()` stays under 25
  lines, takes <=3 parameters (`self`, `org_id`, `duration`), and contains <=5
  logical blocks (prompt -> API call -> flatten summary -> flatten SLE array ->
  DataExporter call). Hierarchy is unchanged: one new method on an existing class.
  No new packages, modules, or top-level constants are introduced. If either
  flattener grows past 5 lines it is extracted to a private helper on the same
  class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior lives as a method on the existing
  `OrgExportUtils` class (`MistHelper.py:12165`), which already owns generic
  org-level export helpers. No standalone wrapper function is introduced. The
  menu dispatch in the main loop references the class method directly. Variable
  names use full words (`stats_summary_row`, `sle_rows`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_stats:org_id"`, `"org_stats:duration"`) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET); no destructive-confirmation gate is required.
  Org ID is validated against the Mist UUID shape via the existing
  `is_valid_uuid()` helper before the API call; on failure the method logs a
  warning and returns early. API token comes from `.env` via `mistapi.APISession`
  and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 58 getOrgStats`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching org stats for org %s"); `DEBUG`
  after the call with summary counts ("Org stats: sites=%d devices=%d
  connected=%d disconnected=%d"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets,
  tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the revised PK
  strategy dictionary entry, and the menu registration line will carry an inline
  comment explaining *why* the line exists, not merely what it does. Blank lines,
  closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the existing org-stats PK
  strategy entry at `MistHelper.py:4331` and the surrounding org export cluster)
  get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result count, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before write,
  `logging.debug(...)` after write. The `DataExporter` call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/647-mist-get-org-stats/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_stats.md # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New export_org_stats() method on OrgExportUtils class
                         # (existing class at line 12165) + revised PK strategy
                         # entry at line 4331 + new MistHelper-internal sub-table
                         # key for the SLE array + menu 58 registration. No new
                         # modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables auto-created on
                         # first write by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `OrgExportUtils` class in `MistHelper.py` (the
generic org-export helper class). The menu number proposal is **58**, chosen
because operations 1-59 form the Safe Org Exports cluster and 58 is the next
uncontested integer adjacent to other org-level summary snapshot operations. The
full menu list is re-verified at task generation time; if 58 collides with an
in-flight feature branch, the next free integer in the Safe Org Exports range is
used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method skeleton in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` change is a single dict edit plus one new key,
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgExportUtils`. No
  wrappers introduced. Flattening helpers, if needed, are added as private
  methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entries and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
