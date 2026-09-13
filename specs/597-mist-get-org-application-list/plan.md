# Implementation Plan: GetOrgApplicationList Menu Item

**Branch**: `597-mist-get-org-application-list` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/597-mist-get-org-application-list/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/wxtags/apps` (operationId `getOrgApplicationList`) to retrieve
the pre-defined application signature catalog (the list of `{group, key, name}` triples)
that WxTags and WxRules use for traffic classification. The menu item prompts the user
for the `org_id` via `safe_input()` (with a fallback to `MIST_ORG_ID` from `.env`),
invokes the `mistapi` SDK once (non-paginated endpoint), and persists the resulting array
through `DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the composite `(org_id, group, key)` so that
repeated runs upsert cleanly into SQLite without duplicates. The new operation is
proposed as menu number **58** -- the next free slot inside the misc safe-org-exports
cluster (56-59), sitting adjacent to the existing WxTags/WxRules-adjacent operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv`
(for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. A single new SQLite table,
`org_wxtag_applications`, is created on first run by `DataExporter` from the registered
primary-key strategy.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using `MIST_ORG_ID` from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy/destructive skip list (14, 18, 63-65, 90-100) is unaffected --
menu 58 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is
non-paginated and returns a bounded catalog (a few hundred application signatures), so
no special concurrency or chunking is required. The adaptive delay system
(`delay_metrics.json` + `tuning_data.json`) continues to govern back-off without
endpoint-specific tuning.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`). Endpoint is strictly read-only -- no destructive-confirmation gate
required.
**Scale/Scope**: One new public menu method (~20 lines) on a configuration-adjacent
export class (`ConfigExportUtils` is the proposed home; if it does not exist a new
`WxTagExportUtils` class is created -- decision deferred to research.md after scanning
the monolith). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new
CSV/SQLite table (`org_wxtag_applications`). One menu registration entry. One README
operation-count bump. One CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_application_list()` stays under
  25 lines, takes <=2 parameters (`self`, `org_id`), and contains <=5 logical blocks
  (prompt -> validate -> API call -> attach `org_id` to each row -> DataExporter call).
  Hierarchy is unchanged: one new method on an existing (or one new) class. No new
  packages, modules, or top-level constants are introduced beyond the single PK
  strategy dict entry.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a configuration-adjacent
  class in `MistHelper.py`. No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`application_row`, `app_catalog`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- The single user prompt (`org_id`) is collected through
  `safe_input()` with explicit `context="org_application_list:org_id"`, so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. The
  `org_id` is validated against the Mist UUID shape before the SDK call; on validation
  failure the method logs a warning and returns early. API token comes from `.env` via
  the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 58 getOrgApplicationList` -> `git
  push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch`
  -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the SDK call ("Fetching WxTag application catalog for org %s");
  `DEBUG` after the call with the row count ("Received %d application signatures from
  Mist API"); `WARNING` on empty payload or 404; `ERROR` on unexpected exception via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will carry
  an inline comment explaining *why* the line exists, not merely *what* it does.
  Blank lines, closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched block get comments added in the same
  PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a result count,
  `logging.info(...)` before write, `logging.debug(...)` after write. The DataExporter
  call already emits its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/597-mist-get-org-application-list/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_application_list.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on a config-adjacent export class + PK strategy
                         # + menu 58 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58
                         # addition
data/                    # Runtime output target (existing dir; SQLite table
                         # `org_wxtag_applications` is auto-created by DataExporter on
                         # first run from the PK strategy)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on an existing configuration-adjacent class in `MistHelper.py`
(provisionally `ConfigExportUtils` -- the same logical home as the existing wxtag /
wxrule listing operations). The menu number proposal is **58**, chosen because the
56-59 band is the misc safe-org-exports cluster and 58 is the next available slot
below the resource-intensive block at 60+. The exact class binding and the exact free
menu integer will be re-verified during `/speckit.tasks` by grepping the monolith; if
58 collides with an in-flight feature branch, the next free integer in the same
cluster is used and recorded in `tasks.md`.

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
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on one class. No wrappers
  introduced. Row enrichment (attaching `org_id` to each catalog entry) is a single
  comprehension inline in the method; if it grows past one line during implementation
  it is extracted to a private helper on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET-only with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
