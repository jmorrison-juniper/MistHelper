# Implementation Plan: GetOrgAptemplate Menu Item

**Branch**: `598-mist-get-org-aptemplate` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/598-mist-get-org-aptemplate/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/aptemplates/{aptemplate_id}` (operationId
`getOrgAptemplate`) to retrieve a single AP template configuration record (radio
defaults, port profile mappings, dynamic VLAN settings, mesh / Wi-Fi knobs, and
the per-model `ap_matching` rule set) for a Juniper Mist organization. The menu
item prompts the user for an `org_id` (defaulting to `MIST_ORG_ID` from `.env`)
and an `aptemplate_id` via `safe_input()`, invokes the `mistapi` SDK exactly
once, normalizes the single-object JSON response into one summary row plus zero
or more `ap_matching` rule rows, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The
new operation is proposed as menu number **96** -- the next available slot
adjacent to the safe-org-exports / viewers cluster (92-96) and immediately
before the resource-intensive band (97-101). The existing Menu 35
`listOrgApTemplates` operation already enumerates AP templates; this new item
delivers full detail for a single template identified by UUID.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_ORG_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; the polyglot ArangoDB + Redis containers handle the graph + cache
backend. Two new SQLite tables are created on first run by `DataExporter`:
`org_aptemplates` (one row per template) and `org_aptemplate_match_rules` (zero
or more rows per template).
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using known `MIST_ORG_ID` + a known template UUID from
`.env` (`MIST_TEST_APTEMPLATE_ID`, optional). Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 96 sits at the top of the
safe-read band immediately before the resource-intensive cluster, well outside
the destructive 154-194 range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
AP templates (the endpoint is non-paginated and the response is a single JSON
object with an embedded rules array). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; this
endpoint is light enough that no special tuning is required. `--fast` mode
respects the existing concurrency cap and retry budget without change.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); never echo the `aptemplate_id` value into a
log line as a URL fragment (log it as `template=%s` only).
**Scale/Scope**: One new public menu method (~22 lines) on the
`OrgTemplateExportUtils` class (existing template-export cluster -- see
Structure Decision below). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`.
Two new CSV / SQLite tables (`org_aptemplates` and
`org_aptemplate_match_rules`). One menu registration entry. One README
operation-count bump. One CHANGELOG line. No new dependencies, no new modules,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_aptemplate_detail()` stays
  under 25 lines, takes <=3 parameters (`self`, `org_id`, `aptemplate_id`), and
  contains <=5 logical blocks (prompt -> API call -> flatten summary row ->
  flatten match-rule rows -> DataExporter call). Hierarchy is unchanged: one
  new method on an existing or freshly-introduced template-export class (no
  package, module, or top-level constant additions). The match-rule flattener
  is one comprehension; if it grows past 5 lines during implementation, it is
  extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  template-export class (`OrgTemplateExportUtils` if already present in
  `MistHelper.py`; otherwise the class is created in the same PR following the
  established `LicenseExportUtils` / `FirmwareManager` / `SFPTransceiverDataProcessor`
  pattern). No standalone wrapper function is introduced. The menu dispatch in
  the main loop references the class method directly. Variable names use full
  words (`template_record`, `match_rule_row`, `port_config_entry`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_aptemplate:org_id"`,
  `"org_aptemplate:aptemplate_id"`) so SSH / container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. Both UUIDs are validated
  against the Mist UUID shape before the API call; on validation failure the
  method logs a warning and returns early. The API token comes from `.env` via
  the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 getOrgAptemplate` -> `git push origin
  main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch <id>` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call (`"Fetching AP template detail for
  org=%s template=%s"`); `DEBUG` after the call with summary counts
  (`"AP template: id=%s rules=%d wifi_enabled=%s"`); `WARNING` on 404 / empty
  payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. No secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing template-export menu cluster around Menu 35) receive comments in
  the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each `safe_input()` prompt, `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a
  result summary, `logging.info(...)` before flatten, `logging.debug(...)`
  after flatten, `logging.info(...)` before write, `logging.debug(...)` after
  write. The `DataExporter` call already emits its own per-backend log lines;
  the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/598-mist-get-org-aptemplate/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_aptemplate.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgTemplateExportUtils class + new
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 96
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the two new SQLite tables created on first
                         # run by DataExporter)
documentation/api/orgs/GET_orgs_org_id_aptemplates_aptemplate_id.md  # Enriched
                         # endpoint reference (read-only; sourced by Phase 0 research)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the `OrgTemplateExportUtils` class in `MistHelper.py`
(the same domain cluster that owns `listOrgApTemplates`, `listOrgNetworkTemplates`,
`listOrgRfTemplates`, and related template-detail GET helpers). If
`OrgTemplateExportUtils` does not yet exist by that exact name, it is created
in the same PR following the established `LicenseExportUtils` / `FirmwareManager`
class pattern -- a new wrapper function is **not** introduced. The menu number
proposal is **96**, chosen because operations 92-96 are the safe-read Viewers
cluster and 96 is the last available slot below the resource-intensive block
at 97-101. The full menu list will be re-verified at `/speckit.tasks` time; if
96 collides with an in-flight feature branch, the next free integer in the same
safe-read band is used.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary insertion is a single entry
  using the existing structure, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `OrgTemplateExportUtils`. No wrappers introduced. Flattening helpers, if
  needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. Both UUIDs are validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or the full
  request URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
