# Implementation Plan: GetOrgSettings Menu Item

**Branch**: `639-mist-get-org-settings` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/639-mist-get-org-settings/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/setting` (operationId `getOrgSettings`) to retrieve the
full organization settings object -- a large, flat-but-nested JSON document that
exposes ~50 top-level configuration domains (mist_nac, mgmt, cradlepoint, juniper,
switch, gateway_mgmt, synthetic_test, marvis, security, pcap, vpn_options, etc.).
The menu item prompts the user for an `org_id` via `safe_input()` (defaulting to
`MIST_ORG_ID` from `.env`), invokes the `mistapi` SDK exactly once, flattens the
deeply-nested response into a single wide row (top-level scalars) plus a small
number of side tables for the two nested arrays (`auto_device_naming.rules` and
`auto_deviceprofile_assignment.rules`), and persists results through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly on the org's
own UUID. The new operation is proposed as menu number **58** -- the next
available slot inside the Safe Org Exports cluster (1-59), immediately adjacent
to the other org-config / org-template exports (42-50) and just below the
existing SLE / misc block (51-57).

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, `MIST_ORG_ID` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend when
enabled.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using the org configured in `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 58 sits inside the default
test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200.
Both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint
is not paginated; the response is one JSON object (typically 5-50 KB per org).
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue to
govern back-off; no special tuning required for this endpoint.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token
never logged; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`). Sensitive nested fields (e.g. API keys
embedded under `mist_nac`, `zscaler_setup`, `jse_setup`) are persisted as-is
into the storage backends, but MistHelper never writes them to console or log.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgConfigExportUtils` class (extended if not present -- see Structure
Decision), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (plus two
sub-table entries for the flattened rule arrays), three new SQLite tables
(`org_settings`, `org_settings_auto_device_naming_rules`,
`org_settings_auto_deviceprofile_assignment_rules`), one menu registration
entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_settings()` stays under
  25 lines, takes <=2 parameters (`self`, `org_id`), and contains <=5 logical
  blocks (prompt -> validate -> API call -> flatten -> DataExporter calls).
  Hierarchy is unchanged: one new method on an existing class. Two flatteners
  (`_flatten_org_settings_summary`, `_flatten_org_settings_rule_arrays`) are
  introduced as private helpers on the same class, each also <=25 lines.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgConfigExportUtils` class (the class that owns adjacent org-level config
  exports such as network templates, gateway templates, and site templates).
  No standalone wrapper function is introduced. The menu dispatch in the main
  loop references the class method directly. Variable names are full words
  (`org_settings_body`, `rule_row`, `naming_rules`) -- no single-letter
  iterators. If class discovery at implementation time reveals that
  `OrgConfigExportUtils` does not yet exist under that exact name, the new
  method is placed on the semantically closest existing class (candidate:
  `OrgTemplateExportUtils` or `GlobalImportManager`), never in a new wrapper.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  an explicit `context="org_settings:org_id"` string so SSH / container EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required.
  The `org_id` is validated against the Mist UUID shape via the existing
  `is_valid_uuid()` helper before the API call; on validation failure the
  method logs a warning and returns early. API token comes from `.env` via the
  existing `mistapi.APISession` and is never logged. Sensitive nested fields
  in the response (API keys, cloud connector secrets) are persisted to the
  configured backend but never emitted to stdout or the log stream.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` -> `python -m black --check
  MistHelper.py` -> commit with `version YY.MM.DD.HH.MM - add menu 58
  getOrgSettings` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch <run-id>` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching org settings for org %s");
  `DEBUG` after the call with a summary of populated top-level keys and the
  count of nested rule entries ("Org settings: keys=%d naming_rules=%d
  deviceprofile_rules=%d"); `WARNING` on 404 or empty payload; `ERROR` on
  unexpected exception with `logging.exception`. No secrets, tokens, request
  URLs, or nested credential values are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, in each
  flattening helper, in the new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries, and
  in the menu registration line carries an inline `#` comment explaining *why*
  the line exists (not merely what it does). Blank lines, closing
  parentheses, and decorators are exempt per the Constitution. Any adjacent
  uncommented lines in the touched block (existing org-config export cluster)
  get comments added in the same PR per the "editing existing code" rule in
  Principle VI.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the prompt, `logging.info(...)` before the SDK
  call, the call itself, `logging.debug(...)` after with a result summary,
  `logging.info(...)` before each flatten step, `logging.debug(...)` after
  each flatten step with the row count, `logging.info(...)` before each
  DataExporter write. The DataExporter emits its own per-backend log lines;
  the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/639-mist-get-org-settings/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_settings.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgConfigExportUtils class (or closest
                         # semantic match) + PK strategy entries + menu 58
                         # registration. No new modules; same single-file
                         # monolith (~28K lines).
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
documentation/api/orgs/  # Source doc: GET_orgs_org_id_setting.md (already present)
data/                    # Runtime output target (existing dir). DataExporter creates
                         # org_settings.csv and appends to mist_data.db on first run.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `OrgConfigExportUtils` class in
`MistHelper.py` (the class that owns adjacent org-level configuration exports
such as network templates, gateway templates, alarm templates, site templates,
and site groups). If that exact class name is not present in the monolith at
implementation time, the new method attaches to the semantically closest
existing class -- candidates in order of preference:
`OrgTemplateExportUtils`, `OrgSettingsExportUtils` (created if it does not
exist, still a class -- never a wrapper function), or as a last resort a new
`OrgSettingsExportUtils` class that groups this endpoint with the future
`updateOrgSettings` / `deleteOrgSettings` methods when those specs land. The
menu number proposal is **58**, chosen because operations 42-50 are the
existing org-config / templates cluster and 51-57 are SLE / misc; 58 is the
next contiguous integer inside the Safe Org Exports range (1-59). The full
menu list will be re-verified at task generation time; if 58 collides with an
in-flight feature branch, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/get_org_settings.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks.
  The two flattening helpers each stay under the limit. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` change is a single dict insert per
  sub-table (three inserts total), no structural change.
- **Principle II (Class-Based)**: PASS -- All work lives on an existing class
  (or, if strictly necessary, a new class -- still class-based, never a
  standalone wrapper). Flattening helpers are private methods on the same
  class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation happens before the SDK call.
  Sensitive nested credentials are persisted but never logged.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline. The full pipeline is enumerated in `quickstart.md`.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token, request
  URL, or nested credential values.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entries and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  flatten summary, flatten each rule array, three exports).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
