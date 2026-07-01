# Implementation Plan: GetOrgSslProxyCert Menu Item

**Branch**: `642-mist-get-org-ssl-proxy-cert` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/642-mist-get-org-ssl-proxy-cert/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/ssl_proxy_cert` (operationId `getOrgSslProxyCert`) to
retrieve the SSL proxy inspection certificate configured for an organization.
The certificate is used by SRX gateways to perform SSL inspection; NOC engineers
need to be able to extract it from the API to verify deployment state and to
compare against what is installed on gateways. The menu item prompts the user
for `org_id` via `safe_input()` (or defaults to `MIST_ORG_ID` in `.env`), calls
`mistapi.api.v1.orgs.cert.getOrgSslProxyCert()` exactly once, normalises the
single-object response into one flat row keyed by `org_id`, and persists it via
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` with `natural_pk` on `org_id` so re-runs
upsert cleanly (one SSL proxy cert per org). The new operation is proposed as
menu number **195** -- the next available integer above the current top
operation (194, `OrgTicketManager.clone_device_config_to_gateway_template`) --
with strong conceptual affinity to the Config/Admin cluster (42-50) where
adjacent org-level cert / setting exports already live.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints; Windows 11 dev host + Podman Linux runtime).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, `MIST_ORG_ID` from
`.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
Local SQLite fallback lives in `data/mist_data.db` (new table
`org_ssl_proxy_cert`). CSV output lands in `data/org_ssl_proxy_cert_<org_id>.csv`.
Polyglot ArangoDB + Redis containers persist the same row as a document keyed
by `org_id` and cached under a matching Redis key.
**Testing**: `python MistHelper.py --test` covers the new menu item in
non-interactive mode using `MIST_ORG_ID` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Skip list (14, 18, 63-65, 90-100) is
unaffected -- new item 195 is outside those ranges and is strictly read-only.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and SSH-on-2200.
Both must work with no code change; PEM output must be safe to write on both
filesystems (no CRLF surprises; use `pathlib.Path.write_text` with explicit
`encoding="utf-8"` inside `DataExporter`).
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single non-paginated GET; wall-clock target <=5 seconds
including SDK auth, TLS handshake, and DataExporter write. No per-endpoint
adaptive-delay tuning required -- the endpoint returns at most one small JSON
object.
**Constraints**: ASCII-only logging; `safe_input()` wraps every prompt; the API
token from `.env` must never appear in any log line; the raw PEM certificate
body is written verbatim to CSV/SQLite but is NOT logged; all output under
`data/`; Windows-safe path joining via `pathlib.Path` / `os.path.join`.
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`OrgConfigExporter` class (line ~11995 in `MistHelper.py`), one new
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, one new SQLite table
`org_ssl_proxy_cert`, one menu registration line in the main dispatch table
(around line ~22267), one README operation-count bump, one CHANGELOG line. No
new modules, no new directories, no new dependencies.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_org_ssl_proxy_cert()` stays under
  25 lines, takes 2 parameters (`self`, `org_id`), and contains <=5 logical
  blocks (prompt -> validate UUID -> API call -> flatten to single-row list
  -> DataExporter call). Class hierarchy is unchanged: one new method on the
  existing `OrgConfigExporter` class. No new packages, modules, or top-level
  constants are introduced. If the flatten step grows past 5 lines during
  implementation, it is extracted to a private `_flatten_cert_row` helper on
  the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behaviour is added as a method on the existing
  `OrgConfigExporter` class -- the same class that already owns adjacent
  org-level config exports (PSK export at menu 44, MSP org config exports,
  license-record helpers). No standalone wrapper function is introduced. The
  menu dispatch table references the class method directly:
  `"195": (OrgConfigExporter.export_org_ssl_proxy_cert, "Export org SSL proxy
  inspection certificate")`. Variable names use full words
  (`ssl_proxy_cert_row`, `cert_response`); no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  an explicit `context="org_ssl_proxy_cert:org_id"` string so SSH and container
  EOF exits with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET); no typed destructive-confirmation gate is required. The `org_id`
  input is validated against the Mist UUID shape via `ValidationUtils` before
  the SDK call; on validation failure the method logs a warning and returns
  early. API token is loaded from `.env` via the existing `mistapi.APISession`
  and is never logged. The PEM certificate body is public-key material by
  definition, but it is still classified as sensitive-adjacent: it is written
  to `data/` only and never emitted through the logger.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies with
  no modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` ->
  `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 195 getOrgSslProxyCert` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs syntax
  validation then builds -> `gh run watch <run-id>` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` / `%d`
  placeholder formatting. `INFO` is emitted before the API call
  ("Fetching SSL proxy certificate for org %s"); `DEBUG` after the call with
  a byte-length summary ("SSL proxy cert response received: cert_len=%d
  bytes"); `WARNING` on 404 / missing cert; `ERROR` on unexpected exception
  via `logging.exception`. No secrets, tokens, PEM bodies, or full request
  URLs (which would echo the org_id path segment) are logged in any level
  above DEBUG.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu
  registration line will carry an inline comment that explains *why* the
  line exists, not merely what it does. Blank lines, closing parentheses,
  and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched blocks (existing `OrgConfigExporter` methods, the
  strategy dict, the menu dispatch table) receive comments added in the
  same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after
  pattern: `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with the certificate byte-length summary,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write. `DataExporter` emits its own per-backend
  log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/642-mist-get-org-ssl-proxy-cert/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, placement
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_ssl_proxy_cert.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method export_org_ssl_proxy_cert() on the
                         # existing OrgConfigExporter class (~line 11995).
                         # New entry in ENDPOINT_PRIMARY_KEY_STRATEGIES
                         # (dict around line ~1672 / ~4324). New menu row
                         # "195" appended to the dispatch table around
                         # line ~22267. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump (194 -> 195) + new row in
                         # the menu table for op 195.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarising
                         # the addition of menu 195.
data/                    # Runtime output target (existing dir).
                         #   New CSV: data/org_ssl_proxy_cert_<org_id>.csv
                         #   New SQLite table: org_ssl_proxy_cert
                         #   (created on first run by DataExporter via
                         #    DatabaseSchemaUtils).
documentation/api/orgs/GET_orgs_org_id_ssl_proxy_cert.md
                         # Existing enriched endpoint doc; used as the
                         # authoritative HTTP + SDK reference for
                         # contracts/get_org_ssl_proxy_cert.md.
```

**Structure Decision**: Single-file monolith. The new menu item is a new
public method on the existing `OrgConfigExporter` class (line ~11995) --
the same class that owns adjacent org-level config exports (PSK at menu 44,
MSP org config, license record helpers). The menu number proposal is
**195**, chosen because it is the next available integer above the current
top operation 194 and remains outside the destructive block (154-194). The
operation is conceptually part of the Config/Admin cluster (42-50); an
alternative placement inside that band (e.g. 46 or 47) was rejected because
the existing numbering is stable across published documentation and
inserting mid-range would renumber every subsequent operation. Menu 195 is
re-verified at task-generation time; if a concurrent branch has already
claimed 195, the next free integer (196, 197, ...) is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/get_org_ssl_proxy_cert.md`), the seven principles
are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, 2 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry is a single insert into an
  existing dict, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `OrgConfigExporter`. No wrappers introduced. Optional `_flatten_cert_row`
  helper (if extracted) is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only with no side effect. `safe_input()` is the documented
  prompt path. UUID validation happens before the SDK call. The PEM body is
  written to `data/` only and never logged.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` / `%d` formatting and never include the API token or
  the PEM body.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows
  the expected comment density on every executable line, including the PK
  strategy entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action (prompt,
  API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
