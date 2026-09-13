# Implementation Plan: GetOrgNacCrl Menu Item

**Branch**: `621-mist-get-org-nac-crl` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/621-mist-get-org-nac-crl/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/setting/mist_nac_crls` (operationId `getOrgNacCrl`) to
list every Certificate Revocation List (CRL) file uploaded to an organization's Mist
NAC settings. The menu item prompts the user for an `org_id` via `safe_input()`,
invokes the `mistapi` SDK exactly once, flattens the single-array response
(`{"results": [ {id, name, url, created_time, modified_time}, ... ]}`) into one row
per CRL file, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the API-supplied UUID so repeated runs
upsert cleanly. The new operation is proposed as menu number **58** -- the next
available slot in the Safe Org Exports cluster (1-59), grouped near other org-level
setting exports and well away from any destructive operation.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the only
permitted interface to the Mist Cloud); `requests` (HTTP transport, transitive);
`python-dotenv` (loads `.env` so `MIST_HOST` and `MIST_API_TOKEN` are available to
`mistapi.APISession`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
Local fallback is SQLite at `data/mist_data.db`; CSV files land in `data/`; the
polyglot ArangoDB + Redis backend runs as separate containers when enabled.
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively
against the org configured in `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 58 sits inside the default sweep range
and is not on the heavy / destructive skip list (14, 18, 63-65, 90-100).
**Target Platform**: Windows 11 + venv for local development; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH on port 2200.
Both targets must work without code change (paths via `pathlib.Path` / `os.path.join`,
ASCII-only logging).
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with
optional Gunicorn web UI on port 8055. This feature is CLI-only.
**Performance Goals**: A single GET request completes in <=5 seconds for typical
orgs. The endpoint is non-paginated and the response is a single JSON object whose
`results` array length equals the number of CRL files uploaded (usually <=10). The
existing adaptive delay system (`delay_metrics.json` + `tuning_data.json`) governs
back-off; no endpoint-specific tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` wraps every prompt; secrets
never logged; all output lands under `data/`; Windows-safe path joining; the
implementation method must obey the 5-Item Rule (<=25 lines, <=5 params, <=5 nested
blocks).
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`NacExportUtils` class (or, if no NAC export class yet exists in MistHelper.py, on
the closest org-setting export class -- see Project Structure section for the
decision rule). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV /
SQLite table (`org_nac_crl_files`). One menu registration entry. One README
operation-count bump. One CHANGELOG line. No new dependencies, no new modules, no
new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_nac_crl()` stays under 25
  lines, takes <=2 parameters (`self`, `org_id`), and contains <=5 logical blocks
  (prompt -> validate -> API call -> flatten results -> DataExporter call). The
  hierarchy is unchanged: one new method on one existing class. No new packages,
  modules, or top-level constants are added. The flattener is a single
  list-comprehension expression; if it grows beyond 5 lines during implementation,
  it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  org-setting export class in `MistHelper.py` (named in the Project Structure
  Decision below). No standalone wrapper function is introduced. The menu dispatch
  in the main loop references the class method directly. Variable names use full
  words (`crl_file`, `crl_rows`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with an
  explicit `context="org_nac_crl:org_id"` string so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only (HTTP
  GET) so no typed destructive-confirmation gate is required. `org_id` is validated
  against the Mist UUID shape via the existing `is_valid_uuid()` helper before the
  API call; on validation failure the method logs a `WARNING` and returns early.
  The API token comes from `.env` via `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit with `version YY.MM.DD.HH.MM - add menu 58 getOrgNacCrl` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style formatting.
  `INFO` is emitted before the API call ("Fetching NAC CRL files for org %s");
  `DEBUG` after the call with a result count ("Received %d NAC CRL file rows");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. No secrets, tokens, or full request URLs are
  logged at any level.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment
  that explains *why* the line exists, not merely what it does. Blank lines,
  closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines inside the touched block get comments added in the
  same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with the result count, `logging.info(...)` before flatten,
  `logging.debug(...)` after flatten, `logging.info(...)` before write,
  `logging.debug(...)` after write. The `DataExporter` already emits per-backend
  log lines, so the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/621-mist-get-org-nac-crl/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_nac_crl.md  # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the org-setting export class + new entry in
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES + menu 58 registration.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on an existing class in `MistHelper.py`. The preferred host class is
`NacExportUtils` (the class that owns adjacent NAC / 802.1X read operations such as
`listOrgNacRules`, `getOrgNacTags`, and other `mist_nac_*` setting endpoints). If
that exact class name does not exist at implementation time, the fallback host
class is the existing `OrgSettingExportUtils` class (which owns endpoints under the
`/orgs/{org_id}/setting/*` URL prefix). A new class is **not** introduced: every
adjacent CRL-related operation already belongs to one of those two classes, and the
constitution prohibits wrapper-only classes. Adding the method to either existing
class preserves the single-file architecture and keeps the menu cluster cohesive.
The menu number proposal is **58**, chosen because the 51-59 range is the tail of
the Safe Org Exports cluster (1-59) where miscellaneous read-only org-setting
exports live, and 58 sits below the resource-intensive block at 60+. The final
number is re-verified at `/speckit.tasks` time by grepping `MistHelper.py` for the
highest currently-allocated integer in this cluster; if 58 is taken, the next free
integer in the same cluster is used.

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

- **Principle I (Five-Item Rule)**: PASS -- The detailed method skeleton in
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` addition is a single dict-literal insert; no
  level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All new work lives on the chosen
  existing class (`NacExportUtils` or fallback `OrgSettingExportUtils`). No
  standalone wrappers, no new classes.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- The log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- `quickstart.md` shows the expected
  comment density on every executable line, including the PK strategy entry and
  menu registration.
- **Principle VII (Action Logging)**: PASS -- `quickstart.md` enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
