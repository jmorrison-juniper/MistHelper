# Implementation Plan: downloadOrgNacPortalSamlMetadata Menu Item

**Branch**: `572-mist-download-org-nac-portal-saml-metadata` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/572-mist-download-org-nac-portal-saml-metadata/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/nacportals/{nacportal_id}/saml_metadata.xml`
(operationId `downloadOrgNacPortalSamlMetadata`) to download the SAML SP metadata
XML document for a single NAC portal. The new method prompts the user for an
`org_id` (defaulting to `MIST_ORG_ID` from `.env`) and a `nacportal_id` via
`safe_input()`, invokes the `mistapi` SDK, and persists the response through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. Because the upstream response is an
opaque XML blob rather than a structured collection, the data row stored to all
backends is a single summary record containing identifying metadata
(`org_id`, `nacportal_id`, `entity_id`, `valid_until`, `retrieved_at`,
`metadata_xml`); the raw XML is additionally written to a sibling `.xml` file
under `data/` for direct IdP import. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` with a `natural_pk` strategy keyed on
`(org_id, nacportal_id)` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **96** -- the next available slot inside
the safe-org-exports / interactive-safe cluster (60-96), sitting adjacent to
the existing NAC and portal-related viewers and immediately below the
resource-intensive block at 97-101.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the
sole permitted interface to the Mist Cloud); `requests` (transport,
transitive); `python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`,
`MIST_ORG_ID` from `.env`). No new dependencies are added by this feature.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers provide the optional graph +
cache backend. A new SQLite table `org_nac_portal_saml_metadata` is created
on first run by `DataExporter`. The raw XML payload is also written
verbatim to `data/orgs_<org_id>_nacportals_<nacportal_id>_saml_metadata.xml`
for direct upload into an IdP that expects a `.xml` file.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known `MIST_ORG_ID` and a discovered
`nacportal_id` from `.env` (or skips with a logged INFO line if no portal
exists). Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
The heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected --
new item 96 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200.
Both must work without code change. Path construction uses `os.path.join` /
`pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on port 8055. This feature lives entirely in
the CLI.
**Performance Goals**: Single non-paginated GET completes in <=5 seconds for
typical NAC portals. Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; the endpoint is light enough
that no special tuning is required. The XML payload is bounded in practice
(<=64 KB for the published example structure).
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()`
wraps every prompt; the API token is never logged; XML content is written
verbatim but is **not** echoed to stdout or to log records (logged only as
byte count); all output lands under `data/`; Windows-safe path joining.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgNacPortalsExporter` class (or, if absent, on a small new
`NacPortalSamlExporter` class -- see the Project Structure Decision below);
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`; one new SQLite table
`org_nac_portal_saml_metadata`; one new XML file emitted per invocation; one
menu registration entry; one README menu-table row + operation-count bump;
one CHANGELOG line. No new top-level modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_nac_portal_saml_metadata()` stays under 25 lines, takes <=3
  parameters (`self`, `org_id`, `nacportal_id`), and contains <=5 logical
  blocks (prompt -> validate UUIDs -> SDK call -> flatten 1-row summary +
  write raw XML -> DataExporter call). Hierarchy is unchanged: one new
  method on a single class. No new packages, modules, or top-level constants
  are introduced. The XML-to-summary flattener is a single inline regex /
  ElementTree pass; if it grows past 5 lines during implementation it is
  extracted to a private `_summarize_saml_metadata()` helper on the same
  class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgNacPortalsExporter` class (the same class that owns
  `listOrgNacPortals`, `getOrgNacPortal`, and `getOrgNacPortalSamlMetadata`
  JSON exports). If that class is not already present in `MistHelper.py`,
  the implementation introduces a new `NacPortalSamlExporter` class -- not
  a standalone wrapper function -- and registers its menu entries through
  the same dispatch pattern used by the adjacent NAC exporters. The menu
  dispatch in the main loop references the class method directly. Variable
  names use full words (`portal_summary_row`, `xml_payload_bytes`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with explicit `context=` strings
  (`"download_org_nac_portal_saml_metadata:org_id"`,
  `"download_org_nac_portal_saml_metadata:nacportal_id"`) so SSH / container
  EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. Both `org_id` and `nacportal_id` are validated against the
  Mist UUID shape before the SDK call; on validation failure the method
  logs a WARNING and returns early. The API token comes from `.env` via
  the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` ->
  `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 downloadOrgNacPortalSamlMetadata`
  -> `git push origin main` -> `.github/workflows/container-build.yml`
  runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `INFO` is emitted before the API call
  ("Downloading SAML metadata for org %s nacportal %s"); `DEBUG` after
  the call with size in bytes ("SAML metadata received: %d bytes,
  entity_id=%s"); `WARNING` on 404 / 401 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. The
  XML body itself is **not** logged -- only its length and the parsed
  `entityID` / `validUntil` attributes. The API token is never logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched NAC-export
  block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with the byte count and parsed entityID,
  `logging.info(...)` before the XML file write, `logging.debug(...)`
  after the write with the on-disk path, `logging.info(...)` before the
  DataExporter call, `logging.debug(...)` after with the row count
  (always 1). The DataExporter call already emits its own per-backend log
  lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/572-mist-download-org-nac-portal-saml-metadata/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- download_org_nac_portal_saml_metadata.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgNacPortalsExporter class (or new
                         # NacPortalSamlExporter class if absent) + PK strategy
                         # + menu 96 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table
                         # for op 96.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing
                         # menu 96 addition.
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite table
                         # created on first run by DataExporter). New file
                         # per invocation:
                         #   data/orgs_<org_id>_nacportals_<nacportal_id>_saml_metadata.xml
```

**Structure Decision**: Single-file monolith. The new menu item is added as
a new public method on the existing `OrgNacPortalsExporter` class in
`MistHelper.py` (the same class that owns the other org-NAC-portal
exporters). If `grep -n "class OrgNacPortalsExporter" MistHelper.py` returns
no match during implementation, the method is hosted on a small new
`NacPortalSamlExporter` class adjacent to the other org-NAC exporter
classes, not on a standalone wrapper function -- this preserves Principle II.
The menu number proposal is **96**, chosen because operations 60-96 are the
Interactive Safe cluster and 96 is the next available slot below the
resource-intensive block at 97-101; the new operation is read-only and
therefore belongs in the safe cluster, not in the destructive 154-194 range.
The full menu list will be re-verified at task generation time; if 96
collides with an in-flight feature branch, the next free integer in the
same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert
  (existing structure), so no level-5 hierarchy explosion. The
  `data-model.md` entity count is 1 (single summary row), well inside the
  5-Item Rule.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `OrgNacPortalsExporter` (or `NacPortalSamlExporter` if the former is
  absent). No wrappers introduced. The optional `_summarize_saml_metadata()`
  helper, if needed, is a private method on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation happens before the SDK call.
  The raw XML is written to disk under `data/` only -- never to stdout, log
  records, or any backend that would expose the IdP-trust document
  outside the local environment.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design
  are ASCII-only with `%s` formatting and never include the API token or
  the raw XML body (only its length and the parsed `entityID`).
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows
  the expected comment density on every executable line, including the
  PK strategy entry and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action
  (prompt, SDK call, XML file write, DataExporter call).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
