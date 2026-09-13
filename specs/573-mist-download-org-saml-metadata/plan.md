# Implementation Plan: downloadOrgSamlMetadata Menu Item

**Branch**: `573-mist-download-org-saml-metadata` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/573-mist-download-org-saml-metadata/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/ssos/{sso_id}/metadata.xml` (operationId
`downloadOrgSamlMetadata`) to retrieve the SAML 2.0 Service Provider metadata document
for a single SSO configuration on an organization. The menu item prompts the user for
`org_id` and `sso_id` via `safe_input()`, calls the `mistapi` SDK, captures the raw XML
payload, wraps it in a flat one-row dictionary (operationId, IDs, XML text, fetch
timestamp, byte size, SHA-256 fingerprint), and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated polls of the
same SSO config. The new operation is proposed as menu number **95** -- the next
contiguous slot in the Safe Org Exports cluster (1-59 / 60-95), sitting adjacent to
existing org-level read operations and well separated from the destructive 154-194
range.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (`.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`); Python stdlib `hashlib` for SHA-256 of the
XML body (no new third-party dependency).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers handle the graph + cache backend. The XML payload is stored
verbatim as a single TEXT column; no XML parsing happens inside MistHelper.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using `MIST_ORG_ID` and `MIST_SSO_ID` from `.env` when present. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy/destructive skip list (14, 18, 63-65,
90-100) does not affect menu 95 -- it sits inside the default sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change. All path handling uses `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET completes in <=5 seconds for a typical SAML metadata
document (a few KB of XML, no pagination, no long-running work). The adaptive delay
system (`delay_metrics.json` + `tuning_data.json`) continues to govern back-off; no
endpoint-specific tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining; the response is XML (not JSON), so
the menu method must not call `response.data` JSON helpers without first checking the
response shape.
**Scale/Scope**: One new public menu method (~22 lines) on an existing org-SSO-adjacent
class (`OrgExportUtils` is the proposed host, with a new `OrgSsoExportUtils` class as
the justified fallback if `OrgExportUtils` already exceeds the 5-Item Rule). One new
entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV/SQLite table
(`org_sso_saml_metadata`). One menu registration entry. One README operation-count
bump. One CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_saml_metadata()` stays under 25
  lines, takes <=3 parameters (`self`, `org_id`, `sso_id`), and contains <=5 logical
  blocks (prompt org_id -> prompt sso_id -> API call -> flatten XML payload into a
  single dict -> DataExporter call). Hierarchy is unchanged: one new method on an
  existing class. No new packages, modules, or top-level constants are introduced. The
  one-row flattener is a single comprehension and stays inline; if it grows past 5 lines
  during implementation, it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on an existing class. The
  host class is `OrgExportUtils` (the same family of classes that own other read-only
  org-level exports). If that class already carries the maximum allowed method count
  under the 5-Item Rule at implementation time, a new `OrgSsoExportUtils` class is
  introduced -- one cohesive class per Org SSO operations cluster, no standalone wrapper
  functions, no module-level helpers. The menu dispatcher in the main loop references
  the class method directly. Variable names use full words (`saml_metadata_xml`,
  `metadata_row`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_saml_metadata:org_id"`, `"org_saml_metadata:sso_id"`) so SSH
  / container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. Both IDs
  are validated against the Mist UUID shape (`is_valid_uuid()`) before the API call; on
  validation failure the method logs a warning and returns early. API token comes from
  `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 95 downloadOrgSamlMetadata` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  before the API call ("Fetching SAML metadata for org %s sso %s"); `DEBUG` after the
  call with byte count ("SAML metadata received: %d bytes"); `WARNING` on 404 / empty
  payload ("No SAML metadata for org %s sso %s"); `ERROR` on unexpected exception via
  `logging.exception`. No secrets, tokens, full request URLs, or raw XML bodies are
  emitted at any level.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block of `MistHelper.py` get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each `safe_input()` prompt, `logging.info(...)` before the SDK call, the call
  itself, `logging.debug(...)` after with a byte count, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten, `logging.info(...)` before write. The
  `DataExporter` call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/573-mist-download-org-saml-metadata/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- download_org_saml_metadata.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method export_org_saml_metadata() on OrgExportUtils class
                         # (or new OrgSsoExportUtils if 5-Item Rule pressure requires),
                         # plus one ENDPOINT_PRIMARY_KEY_STRATEGIES entry, plus the
                         # menu 95 registration line. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 95
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 95
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on `OrgExportUtils` in `MistHelper.py`. If `OrgExportUtils` is already at
the 5-Item Rule method ceiling at implementation time, a new `OrgSsoExportUtils` class
is introduced to host this and any future Org SSO operations (a cohesive grouping that
matches the OpenAPI `Orgs SSO` tag). The menu number proposal is **95**, chosen because
operations 1-95 fall in the Safe Org Exports and Interactive Safe clusters and 95 is
the next contiguous integer below the resource-intensive block at 96-101. The full
menu list will be re-verified at task generation time; if 95 collides with an in-flight
feature branch, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgExportUtils` (or its
  documented fallback `OrgSsoExportUtils`). No wrappers introduced. The XML-to-row
  flattener, if extracted, is added as a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path for both `org_id` and `sso_id`. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token or the raw XML body (only the
  byte count and a SHA-256 fingerprint).
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart skeleton shows the
  expected comment density on every executable line, including the PK strategy entry
  and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompts, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
