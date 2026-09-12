# Implementation Plan: GetMspSso Menu Item

**Branch**: `588-mist-get-msp-sso` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/588-mist-get-msp-sso/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/ssos/{sso_id}` (operationId `getMspSso`) to retrieve
the full configuration of a single MSP-scoped SSO/IdP record (SAML, LDAP, OAuth,
mxedge_proxy, or OpenRoaming). The menu item prompts the user for `msp_id` and
`sso_id` via `safe_input()` (both UUIDs, validated client-side), invokes the
`mistapi` SDK, flattens the single-object response into one CSV/SQLite row, and
persists the result through `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends all receive consistent output. A new entry
is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the SSO `id` field
for clean upserts on repeated runs. The new operation is proposed as menu
number **59** -- the next contiguous slot in the Safe Org Exports cluster that
also serves MSP-tier reads, immediately ahead of the Interactive Safe block
that begins at 60.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known MSP and SSO UUID from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check
MistHelper.py`, `python -m black --check MistHelper.py`. The heavy / destructive
skip list (14, 18, 63-65, 90-100) is unaffected -- proposed menu 59 sits inside
the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical
SSO record (the endpoint is non-paginated and returns a single JSON object that
rarely exceeds a few kilobytes -- SAML certs and LDAP CA bundles are the
largest fields). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs (the response carries `ldap_bind_password`, `idp_cert`,
`scim_secret_token`, `oauth_cc_client_secret`, `ldap_client_key` -- these are
persisted to the backend but never echoed to stdout); all output under `data/`;
Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~20 lines) on a `MspExportUtils`
class (new class, justified below; MistHelper has no pre-existing MSP-scoped
export class), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new
SQLite table (`msp_ssos`), one menu registration entry, one README operation
count bump, one CHANGELOG line. No new external dependencies, no new modules,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_msp_sso()` stays under 25
  lines, takes <=3 parameters (`self`, `msp_id`, `sso_id`), and contains <=5
  logical blocks (prompt msp_id -> prompt sso_id -> validate -> API call ->
  DataExporter call). Hierarchy is unchanged: one new method on one new class.
  The new class `MspExportUtils` is the first member of a logical "MSP" cluster
  at level 4 (Classes / Functions / Constants); adjacent MSP endpoints
  cataloged in sibling spec branches will land on the same class, keeping the
  per-class method count well under 5 for the foreseeable future. No new
  packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `MspExportUtils` class introduced in `MistHelper.py` (rationale: MistHelper
  has no existing MSP-scoped export class; placing MSP reads on the existing
  `OrgExportUtils` would mix scopes and break the 5-Item Rule there). No
  standalone wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`msp_identifier`, `sso_record`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"msp_sso:msp_id"`, `"msp_sso:sso_id"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. Both UUIDs are validated against the Mist UUID shape via the
  existing `is_valid_uuid()` helper before the API call; on validation failure
  the method logs a warning and returns early. API token comes from `.env` via
  the existing `mistapi.APISession` and is never logged. The response contains
  sensitive credentials (`ldap_bind_password`, `idp_cert`, `oauth_cc_client_secret`,
  `scim_secret_token`, `ldap_client_key`); these are persisted to the configured
  backend but NEVER included in any `INFO`/`DEBUG` log line -- the after-call
  log records only `id`, `name`, and `idp_type`.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 59
  getMspSso` -> `git push origin main` -> `.github/workflows/container-build.yml`
  runs -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching SSO %s for MSP %s");
  `DEBUG` after the call with non-sensitive summary fields ("SSO retrieved:
  id=%s name=%s idp_type=%s"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets,
  tokens, certificates, or passwords are logged at any level.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, the new class header, and the menu registration
  line carries an inline comment that explains *why* the line exists, not
  merely what it does. Blank lines, closing parentheses, and decorators are
  exempt per the constitution. Any uncommented adjacent lines in the touched
  menu-dispatch block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a non-sensitive result fingerprint, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten with row count, `logging.info(...)`
  before write, `logging.debug(...)` after write. The DataExporter call emits
  its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/588-mist-get-msp-sso/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_msp_sso.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New MspExportUtils class with export_msp_sso() method;
                         # new ENDPOINT_PRIMARY_KEY_STRATEGIES entry; menu 59
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 59
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 59 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on a new `MspExportUtils` class in `MistHelper.py` (the first
MSP-scoped export class -- justification under Principle II above). The menu
number proposal is **59**, chosen because operations 1-59 form the Safe Org
Exports cluster and 59 is the next available integer ahead of the Interactive
Safe block that starts at 60. MSP-scoped reads are operationally identical to
org-scoped reads from a NOC perspective (same auth, same risk profile, same
output backend), so the safe-export cluster is the correct home. The number is
provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd for the
latest allocated menu integer and 59 is shifted forward if a conflict exists.

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

- **Principle I (Five-Item Rule)**: PASS -- The skeleton in `quickstart.md`
  confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion. `MspExportUtils` starts with
  one method, leaving four slots free under the 5-Item Rule for sibling MSP
  endpoints.
- **Principle II (Class-Based)**: PASS -- All work lives on `MspExportUtils`.
  No wrappers introduced. Any flatten helpers (if needed for the deeply
  nested `mxedge_proxy` sub-object) are added as private methods on the same
  class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call. The
  contract enumerates every sensitive field returned by the API and the
  data-model declares those fields are stored but never logged.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token, certificates,
  passwords, or secret tokens.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
