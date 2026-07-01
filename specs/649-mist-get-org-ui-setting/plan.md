# Implementation Plan: GetOrgUiSetting Menu Item

**Branch**: `649-mist-get-org-ui-setting` | **Date**: 2026-07-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/649-mist-get-org-ui-setting/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/uisettings/{uisetting_id}` (operationId `getOrgUiSetting`) to
retrieve a single Organization UI-settings / Marvis databoard object -- name, purpose,
scope flags (`for_site`, `site_id`), and the ordered list of tiles (each with an
`nl_query` and grid `position`). The menu item prompts the user for `org_id` and
`uisetting_id` via `safe_input()`, invokes the `mistapi` SDK, flattens the response into
one summary row plus one row per tile, and persists both through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. Two new entries are registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **58** -- the next available slot in the "Misc"
sub-cluster (56-59) of the Safe Org Exports range, adjacent to other org-level
configuration read operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using known `org_id` / `uisetting_id` values sourced from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 58 sits inside the default test sweep
range (skip list is 14, 18, 63-65, 90-100).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds; the endpoint is not
paginated and returns a single JSON object with an inline `tiles` array (typically <50
tiles). Adaptive delay via `delay_metrics.json` and `tuning_data.json` continues to
govern back-off; this endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`).
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`ConfigExportUtils` class (the class that already owns other org-level configuration
read operations); two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (one for the
databoard summary row, one for the per-tile detail row); two new CSV/SQLite tables
(`org_ui_setting` and `org_ui_setting_tiles`); one menu registration entry; one README
operation-count bump; one CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_ui_setting()` stays under 25
  lines, takes <=3 parameters (`self`, `org_id`, `uisetting_id`), and contains <=5
  logical blocks (prompt -> API call -> flatten summary -> flatten tiles -> two
  DataExporter calls). Hierarchy is unchanged: one new method on an existing class. The
  tile flattener is a single list comprehension; if it grows past 5 lines during
  implementation it is extracted to a private helper `_flatten_ui_tiles()` on the same
  class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `ConfigExportUtils` class alongside other org-level configuration reads. No standalone
  wrapper function is introduced. The menu dispatch in the main loop references the
  class method directly. Variable names use full words (`databoard_row`, `tile_row`,
  `tiles_list`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- Both prompts (`org_id`, `uisetting_id`) go through `safe_input()`
  with explicit `context=` strings (`"org_ui_setting:org_id"`,
  `"org_ui_setting:uisetting_id"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both UUIDs are validated against the Mist
  UUID shape before the API call; on validation failure the method logs a warning and
  returns early. API token comes from `.env` via the existing `mistapi.APISession` and
  is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 58 getOrgUiSetting` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  emitted before the API call ("Fetching UI setting %s for org %s"); `DEBUG` after the
  call with tile count ("UI setting: name=%s purpose=%s tiles=%d"); `WARNING` on 404 or
  empty payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new PK strategy
  dictionary entries, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing config-export menu cluster) get comments
  added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with tile count, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten, `logging.info(...)` before write, `logging.debug(...)` after write. The
  `DataExporter` call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/649-mist-get-org-ui-setting/
- plan.md              # This file
- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
- data-model.md        # Phase 1 - response entities + DDL + PK registration
- quickstart.md        # Phase 1 - local run + .env + quality gates
- contracts/
  - get_org_ui_setting.md   # Phase 1 - HTTP + SDK contract
- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method export_org_ui_setting() on the existing
                         # ConfigExportUtils class + two PK strategy entries + menu 58
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the two new SQLite tables created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `ConfigExportUtils` class in `MistHelper.py`. The menu
number proposal is **58**, chosen because operations 56-59 are the "Misc" sub-cluster
of the Safe Org Exports range (see agents.md menu category table) and this endpoint is
an org-level configuration read that does not fit the site / inventory / event / client
/ gateway / template / config-admin / SLE clusters. The full menu list will be
re-verified at task generation time; if 58 collides with an in-flight feature branch,
the next free integer in the same cluster (57, 59, or a new appended safe-org slot) is
used, and the change is noted in `research.md` before implementation.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The two
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary inserts are single-statement additions
  to an existing structure, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `ConfigExportUtils`. No
  wrappers introduced. The tile flattener, if longer than a single comprehension, is
  added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the two PK strategy entries and
  the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
