# Implementation Plan: getOrgNacTag Menu Item

**Branch**: `625-mist-get-org-nac-tag` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/625-mist-get-org-nac-tag/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/nactags/{nactag_id}` (operationId `getOrgNacTag`) to
retrieve a single NAC (Network Access Control) tag by its UUID. The menu item
prompts the user via `safe_input()` for the `org_id` (with `.env` `MIST_ORG_ID`
as default) and the `nactag_id`, validates both as UUIDs, invokes the mistapi
SDK, and persists the returned NAC tag record through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs.
The new operation is proposed as menu number **89** -- an available slot in
the Interactive Safe cluster adjacent to existing single-object viewers, and
paired with the existing list-tags menu (44) so operators can drill from list
to single-record detail.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend
when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using values sourced from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14,
18, 63-65, 90-100) is unaffected -- new item 89 sits inside the default test
sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change. Podman is the documented runtime; Docker
is compatible but not exercised in CI.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a
single NAC tag lookup (endpoint is non-paginated and returns one small JSON
object). Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json`
continue to govern back-off; this endpoint is light enough that no per-endpoint
tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); 5-Item Rule (<=25 lines, <=5 params, <=5
nesting blocks per function).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`NacTagExportUtils` class (creating it if it does not yet exist, alongside the
current `listOrgNacTags` handler in menu 44 -- see Structure Decision below),
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`org_nac_tags`), one menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_nac_tag()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `nactag_id`), and contains
  <=5 logical blocks (prompt org_id -> prompt nactag_id -> validate UUIDs ->
  API call -> DataExporter call). Hierarchy is unchanged: one new method on an
  existing (or newly-introduced-alongside-listOrgNacTags) class. No new
  packages, modules, or top-level constants are introduced. The response is a
  single JSON object; a single dict-to-row flattening comprehension keeps the
  flattener well under the 5-line ceiling and does not need to be extracted.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the
  `NacTagExportUtils` class -- the same semantic owner that already handles
  the sibling `listOrgNacTags` behavior in menu 44. If the current
  MistHelper.py locates that handler as a standalone function rather than a
  class method, this feature's PR refactors it into a class in the same
  commit, per the "no wrappers" project convention. The menu dispatch in the
  main loop references the class method directly. Variable names use full
  words (`nac_tag_record`, `nactag_id`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_nac_tag:org_id"`,
  `"org_nac_tag:nactag_id"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both `org_id` and `nactag_id`
  are validated against the Mist UUID shape before the API call; on
  validation failure the method logs a `WARNING` and returns early. API token
  comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 89 getOrgNacTag` -> `git push origin
  main` -> `.github/workflows/container-build.yml` runs -> `gh run watch`
  -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching NAC tag %s for org %s");
  `DEBUG` after the call summarizing the tag ("NAC tag: name=%s type=%s
  match=%s"); `WARNING` on 404 or empty payload; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. No secrets, tokens,
  or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched menu-dispatch
  block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, `logging.info(...)` before the SDK
  call, the call itself, `logging.debug(...)` after with a result summary,
  `logging.info(...)` before write, `logging.debug(...)` after write. The
  `DataExporter` call already emits its own per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/625-mist-get-org-nac-tag/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_nac_tag.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on NacTagExportUtils class + PK strategy + menu 89
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 89
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 89 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the `NacTagExportUtils` class in `MistHelper.py`. This is
the same semantic owner that already handles `listOrgNacTags` (menu 44); if
that handler currently exists as a standalone function, this PR relocates it
onto the same class as part of the change so both list and get-single share a
class per the project's no-wrapper convention. The proposed menu number is
**89**, chosen because menu ranges 60-96 are the Interactive Safe cluster (per
copilot-instructions.md), 89 is currently unused, and single-object viewers
such as menus 92-96 already sit inside that block. The number is provisional
-- at `/speckit.tasks` time, MistHelper.py is grep'd for the latest allocated
menu integer and 89 is shifted forward if a conflict exists.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` addition is a single dict entry
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `NacTagExportUtils`. No wrappers introduced. If the sibling list handler
  currently sits at module scope, the same PR relocates it onto the class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation for both `org_id` and
  `nactag_id` happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
