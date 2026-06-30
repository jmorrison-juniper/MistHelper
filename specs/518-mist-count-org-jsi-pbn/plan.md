# Implementation Plan: countOrgJsiPbn Menu Item

**Branch**: `518-mist-count-org-jsi-pbn` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/518-mist-count-org-jsi-pbn/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes
`GET /api/v1/orgs/{org_id}/jsi/pbn/count` (operationId `countOrgJsiPbn`) to retrieve
the count of JSI PBN (Proactive Bug Notification / Policy-Based Networking) advisories
for an organization, grouped by a caller-selected `distinct` field
(`versions`, `models`, `customer_risk`, or `bug_type`). The menu item prompts the
user with `safe_input()` for the `org_id` and the `distinct` grouping (and optionally
`limit`, `start`, `end` time-window inputs), invokes the `mistapi` SDK
`mistapi.api.v1.orgs.jsi.countOrgJsiPbn()`, flattens the response's `results` array
into one row per group (with the request envelope captured in a second summary row),
and persists everything through `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated
runs. The new operation is proposed as menu number **78** -- the next available slot
in the Safe Org Exports / Insights cluster, sitting adjacent to existing JSI
inventory and insights operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot
ArangoDB + Redis containers handle the graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The new item sits inside the default test
sweep range (skip list 14, 18, 63-65, 90-100 is unaffected by op 78).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The response
is a small count envelope (one `results` array bounded by `limit`, default 100), so
no special tuning is required. Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`InsightsExportUtils` class (the same class that owns the related JSI-inventory and
SLE export operations), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new
CSV/SQLite table (`org_jsi_pbn_count`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new dependencies, no new modules, no
new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_jsi_pbn_count()` stays under 25 lines, takes <=4 parameters
  (`self`, `org_id`, `distinct`, optional `time_window`), and contains <=5 logical
  blocks (prompt -> validate -> API call -> flatten results -> DataExporter call).
  Hierarchy is unchanged: one new method on an existing class. No new packages,
  modules, or top-level constants are introduced. If the flatten block grows past 5
  lines during implementation, it is extracted to a private `_flatten_pbn_count_row`
  helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `InsightsExportUtils` class (the same class that owns adjacent JSI / insights
  exports). No standalone wrapper function is introduced. The menu dispatch in the
  main loop references the class method directly. Variable names use full words
  (`distinct_field`, `pbn_count_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_jsi_pbn_count:org_id"`,
  `"org_jsi_pbn_count:distinct"`, `"org_jsi_pbn_count:limit"`,
  `"org_jsi_pbn_count:start"`, `"org_jsi_pbn_count:end"`) so SSH / container EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. The
  `distinct` value is validated against the documented enum
  (`versions`, `models`, `customer_risk`, `bug_type`) before the API call; the
  `org_id` is checked against the Mist UUID shape; on validation failure the method
  logs a warning and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 78
  countOrgJsiPbn` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run container
  -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching JSI PBN count for org %s
  grouped by %s"); `DEBUG` after the call with summary counts ("PBN count:
  distinct=%s total=%d results=%d"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets,
  tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment
  that explains *why* the line exists, not merely what it does. Blank lines,
  closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the existing JSI-insights menu
  cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result count, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before write,
  `logging.debug(...)` after write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/518-mist-count-org-jsi-pbn/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_jsi_pbn.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on InsightsExportUtils class + PK strategy +
                         # menu 78 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 78
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 78
                         # addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run
                         # by DataExporter)
documentation/api/orgs/GET_orgs_org_id_jsi_pbn_count.md
                         # Existing enriched OpenAPI doc -- read-only reference
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `InsightsExportUtils` class in `MistHelper.py`. The
menu number proposal is **78**, chosen because operations 73-79 are the
Insights / SLE / JSI cluster in the Safe Interactive range and 78 is the next
available slot before the resource-intensive block at 97-101 and the destructive
block at 154-194. The full menu list will be re-verified at task generation time;
if 78 collides with an in-flight feature branch, the next free integer in the same
cluster (79, then 80) is used.

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

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `InsightsExportUtils`. No wrappers introduced. Flattening helper, if needed, is
  a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. Enum validation on `distinct` and UUID validation on `org_id`
  happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
