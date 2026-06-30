# Implementation Plan: GetOrgAlarmTemplate Menu Item

**Branch**: `593-mist-get-org-alarm-template` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/593-mist-get-org-alarm-template/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/alarmtemplates/{alarmtemplate_id}` (operationId
`getOrgAlarmTemplate`) to retrieve the full configuration of a single Org Alarm
Template, including its top-level email-delivery settings and the nested per-alarm-key
`rules` map. The new menu method prompts the user for the `org_id` and the
`alarmtemplate_id` via `safe_input()` (with `.env` defaults where available), calls the
mistapi SDK exactly once, flattens the response into one parent row plus zero-or-more
child `rules` rows, and persists everything through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A natural-key entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the template UUID, plus a composite-key
sub-table entry for the `rules` rows. The new operation is proposed as menu number
**38** -- the next available slot inside the Safe Org Exports / Templates cluster
(37-41), adjacent to the existing `listOrgAlarmTemplates` menu entry.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, and optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org and an alarm template UUID from `.env` (or auto-discovered via
the existing `listOrgAlarmTemplates` plumbing). Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 38 sits inside the standard test sweep
range; the heavy/destructive skip list (14, 18, 63-65, 90-100) is unaffected.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both
must work without code change. All path joins go through `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical alarm
templates (the endpoint is non-paginated and returns one JSON object whose `rules` map
has at most a few dozen keys). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; no special tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token never
logged; all output under `data/`; Windows-safe path joining; inline comment on every
new executable line; `INFO` before / `DEBUG` after every meaningful action.
**Scale/Scope**: One new public menu method (~22 lines) plus two small private flattener
helpers on the existing `TemplateExportUtils` class (the class that already owns
`listOrgAlarmTemplates` and the other template-cluster exports), two new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables (`org_alarm_templates` and
`org_alarm_template_rules`), one menu registration entry, one README operation-count
bump, and one CHANGELOG line. No new dependencies, modules, packages, or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_alarm_template()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `alarmtemplate_id`), and contains
  <=5 logical blocks (prompt for org -> prompt for template -> SDK call -> flatten
  parent -> flatten rules -> DataExporter calls). Hierarchy is unchanged: one new
  method on an existing class plus two small private helpers
  (`_flatten_alarm_template_parent`, `_flatten_alarm_template_rules`), each <=15
  lines. No new packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `TemplateExportUtils` class (the same class that owns `listOrgAlarmTemplates` and
  the adjacent template-cluster exports). No standalone wrapper function is
  introduced. The menu dispatch in the main loop references the class method
  directly. Variable names use full words (`alarm_template_row`, `rule_name`,
  `rule_payload`) -- no single-letter iterators outside trivial comprehensions.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_alarm_template:org_id"`,
  `"org_alarm_template:alarmtemplate_id"`) so SSH / container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both UUID inputs are validated against
  the Mist UUID shape by the existing `is_valid_uuid()` helper before the API call;
  on validation failure the method logs a `WARNING` and returns early. API token
  comes from `.env` via the existing `mistapi.APISession` and is never logged at any
  level.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit with `version YY.MM.DD.HH.MM - add menu 38 getOrgAlarmTemplate`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification. Data dir permission
  fix (`chmod -R 777 data/`) is unchanged.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching alarm template %s for org %s"); `DEBUG`
  after the call with a summary count ("Alarm template %s has %d rules"); `WARNING`
  on 404 or invalid UUID; `ERROR` on 401/403 with no traceback; `logging.exception`
  on unexpected exceptions. No secrets, tokens, or full Authorization headers are
  ever logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the two new private
  flattener helpers, the two new `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
  entries, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched block (the existing template-export menu cluster)
  get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each prompt; `logging.info(...)` before the SDK call; the call itself;
  `logging.debug(...)` after with a result summary (status code + rule count);
  `logging.info(...)` before flatten; `logging.debug(...)` after flatten with the row
  count; `logging.info(...)` before each write; `DataExporter` handles its own
  per-backend log lines and is not duplicated.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/593-mist-get-org-alarm-template/
|-- plan.md              # This file
|-- spec.md              # Pre-existing feature specification (not modified)
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_alarm_template.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method export_org_alarm_template() on the existing
                         # TemplateExportUtils class + 2 private flatteners + 2 new
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entries + menu 38
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 38
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 38
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run
                         # by DataExporter)
documentation/api/orgs/GET_orgs_org_id_alarmtemplates_alarmtemplate_id.md
                         # Source of truth for the response schema (read-only,
                         # referenced by data-model.md and contracts/)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `TemplateExportUtils` class in `MistHelper.py` (the
same class that already owns `listOrgAlarmTemplates` and the other template-cluster
exports). The menu number proposal is **38**, chosen because operations 37-41 are
the Safe Org Exports / Templates cluster per `.github/copilot-instructions.md` and
38 is the next contiguous integer adjacent to `listOrgAlarmTemplates` (documented
as menu 35 in the enriched per-endpoint doc, though the final slot is re-verified
at task generation time by grepping MistHelper.py for the latest allocated menu
integer). If 38 collides with an in-flight feature branch, the next free integer
inside the 37-41 templates cluster is used instead.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. Both
  private flatteners stay under 15 lines. The two
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` additions are simple dict inserts into the
  existing structure -- no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `TemplateExportUtils`. No wrappers introduced. Flattening helpers live on the
  same class as private methods.
- **Principle III (Safety-First)**: PASS -- The Phase 1 endpoint contract confirms
  HTTP `GET` only, with no destructive side effect. `safe_input()` is the
  documented prompt path. Both UUID inputs are validated by `is_valid_uuid()`
  before the SDK call. 404 is handled as a logged warning with zero rows
  written, never a traceback.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or full URL.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart skeleton
  shows the expected comment density on every executable line, including the two
  PK strategy entries and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (org prompt, template
  prompt, validation, API call, parent flatten, rules flatten, parent export,
  rules export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
