# Implementation Plan: GetOrgSamlMetadata Menu Item

**Branch**: `634-mist-get-org-saml-metadata` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/634-mist-get-org-saml-metadata/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/ssos/{sso_id}/metadata` (operationId `getOrgSamlMetadata`)
to retrieve the JSON-format SAML/SSO metadata (ACS URL, entity ID, logout URL, raw XML
metadata blob, and optional SCIM base URL) for a single SSO configuration within an
organization. The menu item prompts the user for `org_id` and `sso_id` via
`safe_input()`, invokes the `mistapi` SDK exactly once, flattens the single-object
response (with the multi-line XML blob preserved as a single quoted column value), and
persists the result through `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated
runs. The new operation is proposed as menu number **58** -- the next available slot
in the Safe Org Exports cluster (1-59) and adjacent to the existing SSO-related and
config/admin exports (menu range 42-50).

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org and SSO ID from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 58 sits inside the default test
sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single non-paginated GET request completes in <=5 seconds. The
response is a small JSON object (5 top-level fields; the largest is the embedded XML
metadata blob at typically a few KB). No pagination and no long-running work. Adaptive
delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off; this endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`). The embedded XML metadata blob (`metadata` field) must be preserved
byte-for-byte in the SQLite TEXT column so downstream IdP tooling can round-trip it;
CSV output uses standard `csv.QUOTE_ALL` quoting to survive the embedded newlines.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`ConfigAdminExportUtils` class (or a new `SsoExportUtils` class if that class does not
already own SSO-related methods -- decided at implementation time via grep of
`MistHelper.py`; the class choice is orthogonal to the plan). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV file per invocation
(`data/org_<short>_sso_<short>_saml_metadata.csv`) and one new SQLite table
(`org_sso_saml_metadata`). One menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_saml_metadata()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `sso_id`), and contains
  <=5 logical blocks (prompt org -> prompt sso -> validate -> API call -> flatten +
  DataExporter call). Hierarchy is unchanged: one new method on an existing class. No
  new packages, modules, or top-level constants are introduced. The flattener is a
  single dict-literal expression inlined into the method body; if it grows past 5
  lines during implementation it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on an existing class that
  already owns adjacent org-scoped read-only exports (candidate:
  `ConfigAdminExportUtils`; final class chosen at implementation time by locating the
  class that currently owns the closest SSO / admin exports). No standalone wrapper
  function is introduced. The menu dispatch in the main loop references the class
  method directly. Variable names use full words (`sso_metadata_row`, `raw_xml_blob`)
  -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_saml_metadata:org_id"`,
  `"org_saml_metadata:sso_id"`) so SSH / container EOF exits cleanly with code 0 and
  no traceback. The endpoint is strictly read-only (HTTP GET) and returns
  configuration metadata, so no typed destructive-confirmation gate is required.
  Both `org_id` and `sso_id` are validated against the Mist UUID shape via the
  existing `is_valid_uuid()` helper before the API call; on validation failure the
  method logs a `WARNING` and returns early. API token comes from `.env` via the
  existing `mistapi.APISession` and is never logged. The embedded XML `metadata`
  blob may contain X.509 certificate fingerprints or SP entity IDs, but no secret
  key material -- only public SAML SP metadata -- so no additional redaction is
  required.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 58 getOrgSamlMetadata` -> `git push origin main`
  -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching SAML metadata for org %s sso %s");
  `DEBUG` after the call with a small summary ("SAML metadata: entity_id=%s
  metadata_bytes=%d has_scim=%s"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets,
  tokens, ACS URL query strings, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will
  carry an inline `#` comment that explains *why* the line exists, not merely what
  it does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the existing
  SSO / admin export menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each prompt, `logging.info(...)` before the SDK call,
  the call itself, `logging.debug(...)` after with a result summary,
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/634-mist-get-org-saml-metadata/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_saml_metadata.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the class that owns adjacent org-SSO/admin
                         # read-only exports (candidate: ConfigAdminExportUtils) plus
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry plus menu 58
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing MistHelper class that already owns the closest set of
org-scoped SSO or admin read-only exports (leading candidate:
`ConfigAdminExportUtils`; grep for the current owner of adjacent SSO-related
operations at implementation time). The menu number proposal is **58**, chosen
because the Safe Org Exports cluster (1-59) currently ends near 59, and 58 sits
comfortably inside the safe range alongside the Config/Admin sub-cluster (roughly
menu 42-50). The number is provisional -- at `/speckit.tasks` time, `MistHelper.py`
is grep'd for the latest allocated menu integer and 58 is shifted to the next free
integer in the same cluster if a conflict exists. In any case, the final number will
remain within the 1-59 Safe Org Exports band so the menu risk grouping stays
correct for the junior NOC engineer audience.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on a single existing
  class. No wrappers introduced. The flattener, if broken out, is added as a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation happens before the SDK call. Both path parameters
  are validated.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or the raw
  XML metadata blob (only its byte length is logged at DEBUG).
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt org, prompt sso, API
  call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
