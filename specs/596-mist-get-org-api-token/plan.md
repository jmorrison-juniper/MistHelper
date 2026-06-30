# Implementation Plan: GetOrgApiToken Menu Item

**Branch**: `596-mist-get-org-api-token` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/596-mist-get-org-api-token/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/apitokens/{apitoken_id}` (operationId `getOrgApiToken`)
to retrieve the metadata for a single Organization API Token. The menu method
prompts the user for an `org_id` and an `apitoken_id` via `safe_input()`, invokes
the `mistapi` SDK at `mistapi.api.v1.orgs.apitokens.getOrgApiToken`, flattens the
single returned object (including the embedded `privileges[]` and `src_ips[]`
arrays) into one summary row plus zero-or-more privilege rows, and persists the
result through `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A natural-PK entry on
the token `id` is added to `ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs
upsert cleanly. The new operation is proposed as menu number **195** -- the
next available integer above the destructive cluster ending at 194; all slots
1-194 are currently allocated.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
only permitted transport to Mist Cloud); `requests` (transitive transport);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache backend
when configured. The existing `listOrgApiTokens` operation already creates the
`org_api_tokens` SQLite table; the new menu item upserts into the same table
because both operations share the natural primary key `id` and an identical
response object schema (the list endpoint returns an array of these objects).
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using `MIST_ORG_ID` and a newly-introduced
`MIST_APITOKEN_ID` value loaded from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The default test sweep skip list
(14, 18, 63-65, 90-100) is unaffected; menu 195 sits above the destructive
range but is read-only and self-contained, so it is included by default.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH on port
2200; both must work without code change. Path joins use `os.path.join` /
`pathlib.Path`; logs are ASCII only.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: A single GET against `getOrgApiToken` completes in
<=5 seconds for any token (the endpoint is non-paginated and returns a single
small JSON object). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; no endpoint-specific tuning is
required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; the
returned `key` field (which the API documents as not containing the actual
secret, only an obfuscated preview) is still treated as sensitive and never
logged at any level; all output under `data/`; Windows-safe path joining.
**Scale/Scope**: One new public static method (~20 lines) on the existing
`OrgAdminExporter` class -- the same class that already owns
`OrgAdminExporter.api_tokens()` (menu 47). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. One CSV/SQLite write into the existing
`org_api_tokens` table plus one new `org_api_token_privileges` flattening
table. One menu registration entry. One README operation-count bump. One
CHANGELOG line. No new dependencies, modules, or directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `OrgAdminExporter.api_token_detail()`
  stays under 25 lines, takes <=3 parameters (`org_id`, `apitoken_id`,
  `apisession`), and contains <=5 logical blocks (prompt org -> prompt token
  id -> API call -> flatten summary + flatten privileges -> DataExporter
  calls). Hierarchy is unchanged: one new method on an existing class. No new
  packages, modules, or top-level constants are introduced. A private helper
  `_flatten_token_privileges()` is added if the privilege fan-out grows past
  five lines.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgAdminExporter` class (the same class that owns `api_tokens` for menu 47,
  plus `admins`, `sso`, and `licenses`). No standalone wrapper function is
  introduced. The menu dispatch table in `MistHelper.py` (~line 21550) gains a
  direct reference to the bound method. Variable names use full words
  (`token_record`, `privilege_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_api_token_detail:org_id"`,
  `"org_api_token_detail:apitoken_id"`) so SSH / container EOF exits with code
  0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  destructive-confirmation gate is required. Both `org_id` and `apitoken_id`
  are validated against the Mist UUID shape via the existing
  `is_valid_uuid()` helper before the API call; on validation failure the
  method logs a `WARNING` and returns early. The API token loaded from `.env`
  is consumed by `mistapi.APISession` and never logged. The response field
  `key` (token preview) is treated as sensitive: it is written to the
  configured backend only, never to logs or stdout.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 195
  getOrgApiToken` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs validation + build ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container with mounted `data/` and `.env` ->
  `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching API token detail for org
  %s token %s"); `DEBUG` after the call with a structural summary that
  excludes the `key` field ("Token detail: name=%s privileges=%d
  src_ips=%d"); `WARNING` on 404 / empty payload; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. The `key` field, the
  raw API token from `.env`, and the full request URL with query string are
  never logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the new menu registration line will carry an
  inline `#` comment explaining *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing api-tokens / admins / sso cluster on `OrgAdminExporter`) gain
  comments in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after
  pattern: `logging.info(...)` before each `safe_input()`, the SDK call,
  each flatten step, and each DataExporter write; `logging.debug(...)` after
  each with a result count summary. The DataExporter call already emits its
  own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/596-mist-get-org-api-token/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_api_token.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgAdminExporter class + PK strategy + menu 195
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 195
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 195 addition
data/                    # Runtime output target (existing dir, no migration needed; the
                         # org_api_tokens SQLite table already exists from menu 47's
                         # listOrgApiTokens operation. A new org_api_token_privileges
                         # table is created on first write by DataExporter.)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public `@staticmethod` on the existing `OrgAdminExporter` class in
`MistHelper.py` (line ~11920), immediately adjacent to the existing
`api_tokens` static method that backs menu 47. The menu-number proposal is
**195**, chosen because all integers 1-194 are currently allocated in the
dispatch dictionary. The destructive cluster ends at 194; this new read-only
menu is appended at 195 with a clearly labeled "Safe Org Read" prefix in the
menu table to prevent any risk-level mis-signaling for a junior NOC engineer.
The number is provisional -- at `/speckit.tasks` time, MistHelper.py is grepped
for the latest allocated integer and 195 is shifted forward if a conflicting
feature branch landed first.

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

- **Principle I (Five-Item Rule)**: PASS -- the detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` change is a single dictionary insert (the
  structure of that dict is unchanged).
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgAdminExporter`.
  No wrappers introduced. Flattening helpers, when needed, are added as
  private methods on the same class.
- **Principle III (Safety-First)**: PASS -- the Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call. The
  `key` field is documented in the contract as a non-secret preview but is
  still treated as sensitive: written to the configured backend, never
  logged.
- **Principle IV (Pipeline)**: PASS -- no deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- log statements in the design are
  ASCII-only with `%s` formatting and never include the API token, the `.env`
  raw value, or the response `key` field.
- **Principle VI (Inline Comments)**: PASS -- the Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- the Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action (prompt,
  validate, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
