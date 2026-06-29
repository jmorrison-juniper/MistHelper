# Implementation Plan: countOrgUserMacs Menu Item

**Branch**: `533-mist-count-org-user-macs` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/533-mist-count-org-user-macs/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/usermacs/count` (operationId `countOrgUserMacs`) to retrieve
aggregate counts of user-MAC records grouped by a distinct attribute (`mac`, `name`,
`labels`, or `org_id`). The menu method prompts the user for `org_id` and the required
`distinct` attribute via `safe_input()`, optionally accepts `limit`, `start`, and `end`
query parameters with sensible defaults, invokes the `mistapi` SDK, flattens the
aggregate response into one envelope row (totals + window) plus zero or more per-group
detail rows (one per `results[]` item), and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **59** -- the next available slot inside the Safe
Org Exports / Misc cluster, sitting adjacent to the existing NAC / client-side org
exports.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using a known org from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Menu 59
sits well inside the default test sweep range (1-89) and outside the heavy/destructive
skip list (14, 18, 63-65, 90-100, 154-194).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint returns
an aggregate count payload; size is bounded by the `limit` query parameter (default 100,
max governed by Mist API). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgUserMacsExporter` class (or `NacExportUtils` if that is the established home for
NAC-adjacent operations -- see research.md Decision 4 for the chosen target class), one
new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables
(`org_usermacs_count_envelope` and `org_usermacs_count_results`), one menu registration
entry at slot 59, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_usermacs_count()` stays under 25
  lines, takes <=4 parameters (`self`, `org_id`, `distinct`, `time_window`), and
  contains <=5 logical blocks (prompt -> validate `distinct` enum -> API call -> flatten
  envelope + results -> DataExporter call). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are introduced.
  Flatteners are inlined as single comprehension blocks; if either grows past 5 lines
  during implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on an existing class (see
  research.md Decision 4 for the chosen target). No standalone wrapper function is
  introduced. The menu dispatch in the main loop references the class method directly.
  Variable names use full words (`distinct_attribute`, `usermac_count_row`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_usermacs_count:org_id"`,
  `"org_usermacs_count:distinct"`, `"org_usermacs_count:limit"`,
  `"org_usermacs_count:start"`, `"org_usermacs_count:end"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. `org_id` is validated against
  the Mist UUID shape and `distinct` is validated against the enum
  `{mac, name, labels, org_id}` before the SDK call; on validation failure the method
  logs a warning and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 59 countOrgUserMacs` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Counting user MACs for org %s by distinct=%s"); `DEBUG`
  after the call with summary counts ("countOrgUserMacs: total=%d returned=%d
  start=%s end=%s"); `WARNING` on 404 / empty payload or invalid `distinct`; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets, tokens,
  or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing org-export menu cluster around slot 59) get
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
specs/533-mist-count-org-user-macs/
+-- plan.md              # This file
+-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
+-- data-model.md        # Phase 1 - response entities + DDL + PK registration
+-- quickstart.md        # Phase 1 - local run + .env + quality gates
+-- contracts/
|   +-- count_org_user_macs.md   # Phase 1 - HTTP + SDK contract
+-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the chosen exporter class + PK strategy + menu 59
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 59
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 59 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite tables created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing user-MACs / NAC-adjacent exporter class in `MistHelper.py`
(target class confirmed in research.md Decision 4). The menu number proposal is **59**,
chosen because operations 1-59 are the Safe Org Exports cluster (Misc tail at 56-59) and
59 is the next available slot before the interactive site-scoped block begins at 60. The
full menu list will be re-verified at task generation time; if 59 collides with an
in-flight feature branch, the next free integer in the same cluster is used.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the chosen existing class.
  No wrappers introduced. Flatten helpers, if needed, are added as private methods on
  the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation and enum validation happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validation, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
