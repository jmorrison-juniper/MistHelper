# Implementation Plan: GetOrgCurrentMatchingClientsOfAWxTag Menu Item

**Branch**: `603-mist-get-org-current-matching-clients-of-a-wx-tag` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/603-mist-get-org-current-matching-clients-of-a-wx-tag/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/wxtags/{wxtag_id}/clients` (operationId
`getOrgCurrentMatchingClientsOfAWxTag`) to retrieve the set of client MAC addresses
currently matching a given WXLAN tag, together with the epoch second timestamp each
client first matched. The menu item prompts the user for an `org_id` and a `wxtag_id`
via `safe_input()`, invokes the `mistapi` SDK exactly once, normalizes the returned JSON
array into one row per matching client (augmented with the parent `org_id` and
`wxtag_id` as foreign-key columns), and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on `(org_id, wxtag_id, mac)` so repeated runs
upsert cleanly. The new operation is proposed as menu number **59** -- the next
available slot in the safe-org-exports cluster (1-59) immediately adjacent to existing
WxTag-related read-only items. If 59 is taken by an in-flight feature branch at task
generation time, the next free integer in the same cluster is used.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers handle the graph + cache backend when enabled.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org and a known WxTag UUID from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 59 sits inside the default test sweep
range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical tags
(the endpoint is non-paginated and returns a flat array of `{mac, since}` objects).
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off; this endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); MAC values normalized to lowercase, colon-free form on insert so
upserts are stable across input casing.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`WxTagExportUtils` class (or a newly introduced `WxTagExportUtils` class if no WxTag-
specific class exists yet -- see Structure Decision below), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table
(`org_wxtag_matching_clients`), one menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new top-level modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_wxtag_matching_clients()` stays under 25 lines, takes <=3 parameters
  (`self`, `org_id`, `wxtag_id`), and contains <=5 logical blocks (prompt -> validate
  -> API call -> flatten / annotate rows -> DataExporter call). Hierarchy is unchanged:
  one new method on a single class. No new packages, modules, or top-level constants
  are introduced. The flattening step is a single list comprehension; if it grows past
  5 lines during implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `WxTagExportUtils` class (the class that owns related WxTag list / detail exports).
  No standalone wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`matching_client_row`, `since_epoch`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_wxtag_clients:org_id"`,
  `"org_wxtag_clients:wxtag_id"`) so SSH / container EOF exits cleanly with code 0 and
  no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both UUIDs are validated against the Mist
  UUID shape before the API call; on validation failure the method logs a warning and
  returns early. API token comes from `.env` via the existing `mistapi.APISession` and
  is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 59 getOrgCurrentMatchingClientsOfAWxTag` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching matching clients for wxtag %s in org %s");
  `DEBUG` after the call with the matching-client count ("WxTag %s returned %d
  matching clients"); `WARNING` on 404 / empty payload; `ERROR` on unexpected exception
  via `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  will carry an inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  WxTag export cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with a result count, `logging.info(...)` before flatten, `logging.debug(...)` after
  flatten, `logging.info(...)` before write, `logging.debug(...)` after write. The
  `DataExporter` call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/603-mist-get-org-current-matching-clients-of-a-wx-tag/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_current_matching_clients_of_a_wx_tag.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on WxTagExportUtils class + PK strategy + menu 59
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 59
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 59
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on `WxTagExportUtils` in `MistHelper.py`. If `WxTagExportUtils` does not
yet exist at implementation time, it is created as a new class collocated with the
other org-scoped export utility classes (`SiteExportUtils`, `LicenseExportUtils`,
`InventoryExportUtils`) -- this preserves Principle II (no wrappers) and keeps related
WxTag operations grouped. Either path is acceptable; the implementing task picks the
correct one after re-reading `MistHelper.py` at that time. The menu number proposal is
**59**, chosen because operations 1-59 are the Safe Org Exports cluster and 59 is the
next available slot adjacent to the existing safe-org-export band. The full menu list
will be re-verified at task generation time; if 59 collides with another in-flight
feature branch, the next free integer in the same cluster is used.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `WxTagExportUtils`. No
  wrappers introduced. Flattening helpers, if needed, are added as private methods on
  the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. Both UUIDs are validated before the SDK call.
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
