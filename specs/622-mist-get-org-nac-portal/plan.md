# Implementation Plan: GetOrgNacPortal Menu Item

**Branch**: `622-mist-get-org-nac-portal` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/622-mist-get-org-nac-portal/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/nacportals/{nacportal_id}` (operationId `getOrgNacPortal`)
to retrieve the full configuration of a single NAC (Network Access Control) portal --
including portal type, guest-portal auth settings, SAML SSO bindings, EAP settings,
optional CA certificates, and template / image URLs. The menu item prompts the user
for `org_id` (defaulted from `.env`) and `nacportal_id` via `safe_input()`, invokes
the `mistapi` SDK function `mistapi.api.v1.orgs.nac_portals.getOrgNacPortal()`,
flattens the nested response (top-level scalars plus `portal.*`, `sso.*`, and
`sso.sso_role_matching[]` sub-rows) and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the portal's natural `id` field for
idempotent SQLite upserts. The new operation is proposed as menu number **94** --
the next free slot in the safe-org-exports cluster, adjacent to existing NAC /
template export items.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_ORG_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land under
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org and a known nacportal_id supplied through
`.env` (`MIST_ORG_ID`, optionally `MIST_TEST_NACPORTAL_ID`). Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 94 sits inside the default
test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical
portal (the endpoint is non-paginated and returns a single JSON object, even when
SSO and additional-CA certificates are populated). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; the
endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
(API token, JWT secret, IdP certs) in logs; all output under `data/`;
Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`NacExportUtils` class (or `OrgExportUtils` if the NAC export class is not yet
present -- decision recorded in `research.md`); one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`; three new CSV/SQLite tables
(`org_nac_portal`, `org_nac_portal_sso`, `org_nac_portal_sso_role_matching`);
one menu registration entry; one README operation-count bump; one CHANGELOG line.
No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_nac_portal()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `nacportal_id`), and contains
  <=5 logical blocks (prompt -> validate -> API call -> flatten -> DataExporter
  call). Hierarchy is unchanged: one new method on an existing class. The
  nested SSO and role-matching flatteners are extracted to two short private
  helper methods on the same class if either approaches the 5-line ceiling.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  NAC / Org-export class (final class name decided in `research.md` Task 4).
  No standalone wrapper function is introduced. The menu dispatch in the main
  loop references the class method directly. Variable names use full words
  (`nac_portal_row`, `sso_block`, `role_match`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_nac_portal:org_id"`,
  `"org_nac_portal:nacportal_id"`) so SSH / container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so
  no typed destructive-confirmation gate is required. Both UUIDs are validated
  against the Mist UUID shape before the API call; on validation failure the
  method logs a warning and returns early. The API token comes from `.env`
  via the existing `mistapi.APISession` and is never logged. The response may
  contain a `portal_authorize_jwt_secret`, an `idp_cert`, and `additional_cacerts`;
  these are written to the data backend (which is the user's intent) but are
  never echoed to stdout or log lines.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 94 getOrgNacPortal` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching NAC portal %s for org %s");
  `DEBUG` after the call with a non-sensitive summary
  ("NAC portal type=%s name=%s sso_enabled=%s role_match_count=%d");
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. The `portal_authorize_jwt_secret`,
  `idp_cert`, and `additional_cacerts` values are NEVER included in any log
  line -- they appear only in the persisted output.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an inline
  comment that explains *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched block (the chosen export class
  and the menu registration block) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with the type / name summary,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten with
  the row count, `logging.info(...)` before write, `logging.debug(...)` after
  write. The DataExporter call already emits its own per-backend log lines;
  the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/622-mist-get-org-nac-portal/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_nac_portal.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the NAC / Org-export class + new entry in
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES + menu 94 registration.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 94
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 94 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing NAC-portal / Org-export class in
`MistHelper.py`. The final class name (existing `NacExportUtils` if present,
otherwise the next-closest existing org-config exporter such as
`OrgConfigExportUtils`) is determined in `research.md` Task 4 -- a new class
is **not** introduced; the work attaches to whichever existing class already
owns adjacent NAC list / template exports. The menu number proposal is
**94**, chosen because operations 1-59 / 60-96 form the safe-export cluster
and 94 is the next free integer adjacent to other NAC / template operations,
below the resource-intensive block at 97-101. The full menu list will be
re-verified at task generation time; if 94 collides with an in-flight feature
branch, the next free integer in the same cluster is used.

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
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks.
  The two flattener helpers (`_flatten_sso_block`, `_flatten_role_matching`)
  are each <=10 lines and live on the same class. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the chosen existing
  export class. No wrappers introduced. Flattening helpers are private methods
  on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. Both UUIDs are validated before the SDK call. Secrets
  in the response (JWT secret, IdP cert, CA certs) are persisted but never
  logged.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or any of
  the secret-bearing response fields.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API
  call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
