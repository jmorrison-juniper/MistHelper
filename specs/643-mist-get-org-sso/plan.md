# Implementation Plan: getOrgSso Menu Item

**Branch**: `643-mist-get-org-sso` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/643-mist-get-org-sso/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/ssos/{sso_id}` (operationId `getOrgSso`) to retrieve
the full configuration of a single Single Sign-On (SSO) profile for an
organization. The menu item prompts the user for `org_id` and `sso_id` via
`safe_input()`, invokes the `mistapi` SDK, flattens the nested response (including
the `mxedge_proxy` sub-object with its `acct_servers[]`/`auth_servers[]` arrays and
the `openroaming` sub-object) into a summary row plus zero-or-more child rows, and
persists the result through `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (`natural_pk` on the SSO UUID) for
clean SQLite upserts on repeated polls. The new operation is proposed as menu
number **196** -- the next contiguous integer above the current maximum (195) and
sits outside the destructive block (154-194).

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org + sso from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- new item 196 sits above the destructive block.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. Endpoint is
non-paginated and returns one SSO record; no bulk retrieval concerns. Adaptive
delay metrics in `delay_metrics.json` / `tuning_data.json` continue to govern
back-off; no special tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
in logs (SSO records contain `ldap_bind_password`, `idp_cert`, `oauth_cc_client_secret`,
`scim_secret_token`, `ldap_client_key`, and `wba_cert` -- these must NEVER appear
in `INFO` or `DEBUG` output); all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgExportUtils` class (which already owns `listOrgSsos`), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, up to three new SQLite tables (`org_sso`,
`org_sso_mxedge_proxy_auth_servers`, `org_sso_mxedge_proxy_acct_servers`), one
menu registration entry, one README operation-count bump, one CHANGELOG line. No
new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_sso()` stays under 25 lines,
  takes <=3 parameters (`self`, `org_id`, `sso_id`), and contains <=5 logical
  blocks (prompt org_id -> prompt sso_id -> API call -> flatten summary -> flatten
  radius sub-arrays + DataExporter calls). Hierarchy is unchanged: one new method
  on an existing class. Two flatteners for the `mxedge_proxy.auth_servers[]` /
  `mxedge_proxy.acct_servers[]` sub-arrays are extracted to private helpers on the
  same class if they exceed 5 lines inline.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgExportUtils` class (the same class that owns `listOrgSsos` at line 11890 of
  `MistHelper.py`). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable names
  use full words (`sso_record`, `radius_auth_rows`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_sso:org_id"`, `"org_sso:sso_id"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. Both `org_id` and `sso_id` are validated against the Mist UUID shape
  via the existing `is_valid_uuid()` helper before the API call; on validation
  failure the method logs a `WARNING` and returns early. API token comes from
  `.env` via the existing `mistapi.APISession` and is never logged. SSO secrets
  (`ldap_bind_password`, `idp_cert`, `oauth_cc_client_secret`, `scim_secret_token`,
  `ldap_client_key`, `wba_cert`) are persisted to the configured storage backend
  but redacted from log lines -- `DEBUG` summarizes only `idp_type`, `name`, and
  key presence booleans.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 196 getOrgSso`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching SSO %s for org %s"); `DEBUG`
  after the call with non-sensitive summary ("SSO: name=%s idp_type=%s has_ldap_bind=%s
  has_idp_cert=%s"); `WARNING` on 404 / empty payload; `ERROR` on 401/403;
  unexpected exceptions surface via `logging.exception` (no secrets in the trace
  formatter). No tokens, passwords, private keys, or SAML certificate bodies are
  logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line carries an inline
  comment that explains *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched block (the existing
  `OrgExportUtils.listOrgSsos` region) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, `logging.info(...)` before the SDK
  call, the call itself, `logging.debug(...)` after with a non-sensitive result
  summary, `logging.info(...)` before each flatten, `logging.debug(...)` after
  each flatten with a row count, `logging.info(...)` before each
  `DataExporter.write_with_format_selection` call. The DataExporter emits its
  own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/643-mist-get-org-sso/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_sso.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgExportUtils class + PK strategy entry
                         # + menu 196 registration. No new modules; same
                         # single-file monolith. Extends the class that already
                         # owns listOrgSsos.
README.md                # Operation count bump + new row in the menu table for op 196
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 196 addition
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite tables
                         # created on first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `OrgExportUtils` class in `MistHelper.py` (the same
class that owns the sibling `listOrgSsos` list export -- see line 11890). The
menu number proposal is **196**, chosen because the current maximum registered
menu integer is 195 (verified by regex sweep of `MistHelper.py`) with no gaps
below it, and 196 sits safely above the destructive block (154-194). The number
is provisional -- at `/speckit.tasks` time, MistHelper.py is re-grep'd for the
latest allocated menu integer and 196 is shifted forward if a conflict exists.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion. The two RADIUS sub-array
  flatteners are single-comprehension private helpers on the same class.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgExportUtils`.
  No wrappers introduced. Flattening helpers, if needed, are added as private
  methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. Both UUIDs are validated via `is_valid_uuid()` before
  the SDK call. Secret fields are documented as redacted from logs.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting; SSO secret fields never enter a log line.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (each prompt, API call,
  each flatten, each export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
