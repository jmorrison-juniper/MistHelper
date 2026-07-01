# Implementation Plan: GetOrgTemplate Menu Item

**Branch**: `648-mist-get-org-template` | **Date**: 2026-07-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/648-mist-get-org-template/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/templates/{template_id}` (operationId `getOrgTemplate`,
tag `Orgs WLAN Templates`) to retrieve the full detail record for a single WLAN
template inside an organization. The menu item prompts the user for `org_id` and
`template_id` via `safe_input()`, invokes the `mistapi` SDK, flattens the response
(one WLAN-template row plus zero-or-more per-site-scope apply/exception rows) and
persists it through `DataExporter.write_with_format_selection()` so CSV, SQLite,
and ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on
repeated runs. The new operation is proposed as menu number **58** -- the next
available slot inside the Safe Org Exports / Templates cluster (37-41 range for
list-templates neighbours), placed as the detail-lookup companion to the existing
`listOrgTemplates` menu item and safely away from Resource Intensive (97-101) and
Destructive (154-194) blocks.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org / template ID from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- proposed menu 58 sits inside the default test
sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint
is non-paginated and returns a single JSON object; adaptive delay metrics
(`delay_metrics.json` + `tuning_data.json`) continue to govern back-off without
endpoint-specific tuning.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
in logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); no direct HTTP -- only mistapi SDK.
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`WLANTemplateExportUtils` class (or `TemplateExportUtils` if the codebase names
it differently -- verified at task time by grepping for `listOrgTemplates`).
Two new SQLite tables (`org_wlan_templates` and `org_wlan_template_scopes`), one
new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one menu registration line, one
README menu-table row, one CHANGELOG line. No new modules, no new dependencies,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_wlan_template_detail()`
  stays under 25 lines, takes <=3 parameters (`self`, `org_id`, `template_id`),
  and contains <=5 logical blocks (prompt-org -> prompt-template -> API call ->
  flatten summary + scope rows -> two DataExporter calls). Hierarchy is
  unchanged: one new method on an existing class. If the scope-flattener grows
  past 5 lines it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  WLAN-template export class in `MistHelper.py` (the class that owns
  `listOrgTemplates`). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable
  names use full words (`template_row`, `scope_rows`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_template_detail:org_id"`,
  `"org_template_detail:template_id"`) so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET),
  so no typed destructive-confirmation gate is required. Org and template IDs
  are validated against the Mist UUID shape via the existing `is_valid_uuid()`
  helper before the API call; on validation failure the method logs a warning
  and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` -> `python -m black --check
  MistHelper.py` -> commit with `version YY.MM.DD.HH.MM - add menu 58
  getOrgTemplate` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching WLAN template %s in org %s");
  `DEBUG` after the call with a short summary ("Template name=%s
  deviceprofile_count=%d apply_scope_count=%d"); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries, and the menu registration line
  will carry an inline comment that explains *why* the line exists, not merely
  what it does. Blank lines, closing parentheses, and decorators are exempt
  per the constitution. Any uncommented adjacent lines in the touched
  template-export block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result summary; `logging.info(...)` before the two flatten
  steps, `logging.debug(...)` after each with row counts; `logging.info(...)`
  before each write, and the DataExporter's own per-backend log lines close
  the pattern (not duplicated by this method).

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/648-mist-get-org-template/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_template.md  # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on WLANTemplateExportUtils class + two PK
                         # strategy entries + menu 58 registration. No new
                         # modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry for menu 58 addition
data/                    # Runtime output target (existing dir; no schema
                         # migration beyond the new SQLite tables created on
                         # first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing WLAN-template export class in `MistHelper.py`
(the same class that owns `listOrgTemplates`). The menu number proposal is
**58**, chosen because operations 37-41 already host the WLAN/network template
list-export cluster and 58 is the next free integer inside the 1-59 Safe Org
Exports block that keeps template operations visually adjacent without
colliding with in-flight allocations. The full menu list will be re-verified at
task generation time by grepping `MistHelper.py` for `# menu ` markers; if 58
collides, the next free integer in the same 42-59 sub-range is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` update is a two-key insert (existing
  structure), no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing WLAN
  template export class. No wrappers introduced. Scope-flattening helper, if
  needed, is a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including both PK strategy
  entries and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (two prompts, API call,
  two flatten steps, two exports).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
