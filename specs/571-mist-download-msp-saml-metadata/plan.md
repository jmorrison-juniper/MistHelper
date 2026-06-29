# Implementation Plan: downloadMspSamlMetadata Menu Item

**Branch**: `571-mist-download-msp-saml-metadata` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/571-mist-download-msp-saml-metadata/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/ssos/{sso_id}/metadata.xml` (operationId
`downloadMspSamlMetadata`) to download the SAML Service Provider metadata XML
document for an MSP-level SSO configuration. The metadata XML is the artifact a
NOC engineer imports into the IdP (Okta, Azure AD, ADFS, etc.) during SAML
federation setup. The menu item prompts the user for `msp_id` and `sso_id` via
`safe_input()`, invokes the `mistapi` SDK, persists the raw XML byte-for-byte to
a `.xml` file under `data/`, and *also* registers a flattened summary row through
`DataExporter.write_with_format_selection()` (capturing `entityID`, `validUntil`,
SLO/ACS bindings, and a SHA-256 of the XML body) so CSV, SQLite, and ArangoDB +
Redis backends all retain queryable history of every metadata snapshot. A new
entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed by
`(msp_id, sso_id)` for clean SQLite upserts on repeated runs. The new operation
is proposed as menu number **94** -- the next available slot in the Safe Org
Exports cluster, deliberately *not* placed near the destructive 154-194 range
because this endpoint is strictly read-only.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`); `hashlib` (stdlib, used to fingerprint the
XML body); `xml.etree.ElementTree` (stdlib, used for shallow parse of the metadata to
extract the summary fields that get persisted alongside the raw XML).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB +
Redis containers handle the graph + cache backend. The raw XML document is *also* written
verbatim to a `.xml` file under `data/` because IdP import tools expect a real XML file,
not a CSV cell or a SQLite TEXT column.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using `MIST_MSP_ID` and `MIST_SSO_ID` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65,
90-100) is unaffected -- menu item 94 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change. Path separators are normalized via `pathlib.Path` / `os.path.join`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical SAML
metadata document (well under 10 KB on the wire, non-paginated). Adaptive delay metrics
in `delay_metrics.json` and `tuning_data.json` continue to govern back-off; this endpoint
is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs
(API token never logged; the metadata XML itself is public-by-design but is still treated
as user data and excluded from DEBUG echoes beyond a length / SHA-256 summary); all
output under `data/`; Windows-safe path joining; response body must not be passed through
a JSON decoder (the body is XML).
**Scale/Scope**: One new public menu method (~25 lines) on a new `MspSsoExportUtils`
class added to `MistHelper.py` (rationale below in Principle II), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table (`msp_sso_saml_metadata`), one
menu registration entry, one README operation-count bump, one CHANGELOG line. No new
top-level dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_msp_saml_metadata(self, msp_id=None, sso_id=None)` stays under 25 lines,
  takes exactly 3 parameters (`self`, `msp_id`, `sso_id`), and contains 5 logical
  blocks (prompt msp_id -> prompt sso_id -> API call -> persist raw XML file ->
  flatten + DataExporter summary write). Hierarchy is unchanged: one new class with
  one new method on it. The `_summarize_saml_metadata()` private helper handles the
  XML-to-dict flatten in a single comprehension; if that helper grows past 25 lines
  during implementation, the entity-descriptor parse is split into a second helper on
  the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- A new class `MspSsoExportUtils` is added to `MistHelper.py`
  rather than parking the method on an unrelated existing class. Justification:
  MistHelper currently has no class that owns MSP-level SSO operations (the existing
  `*ExportUtils` classes are scoped to orgs, sites, devices, licenses, etc.). Creating
  a dedicated class keeps future MSP SSO endpoints (list, get, create, delete,
  metadata JSON variant) clustered correctly, in line with the project rule that
  related operations live on a single class. No standalone wrapper function is
  introduced; the menu dispatch in the main loop references the class method
  directly. Variable names use full words (`saml_metadata_xml`, `summary_row`,
  `metadata_sha256`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"msp_saml_metadata:msp_id"`, `"msp_saml_metadata:sso_id"`) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is
  required. Both UUIDs are validated against the Mist UUID shape via the existing
  `is_valid_uuid()` helper before the API call; on validation failure the method logs
  a `WARNING` and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged. The downloaded XML is written to a
  filename derived from `msp_id[:8]` and `sso_id[:8]` (short forms) to avoid leaking
  full UUIDs into shell history.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 94 downloadMspSamlMetadata`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification. CI quality gates
  (Ruff, mypy, Bandit, pip-audit, CodeQL) cover the new code path automatically.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching SAML metadata for msp %s sso %s");
  `DEBUG` after the call with summary counts ("SAML metadata: bytes=%d sha256=%s
  entity_id=%s"); `WARNING` on 404 / empty payload; `ERROR` on unexpected exception
  with full traceback via `logging.exception`. No secrets, tokens, full request URLs,
  or full XML bodies are logged -- only length, SHA-256, and the public `entityID`
  attribute, which is part of the SP metadata contract and not sensitive.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `MspSsoExportUtils` class definition, the new `_summarize_saml_metadata` helper,
  the new PK strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does. Blank
  lines, closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched block (the menu registration cluster
  near operation 94) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each `safe_input()` prompt, `logging.info(...)` before
  the SDK call, `logging.debug(...)` after the call with byte count + SHA-256 +
  entityID, `logging.info(...)` before the raw-XML file write, `logging.debug(...)`
  after with file path, `logging.info(...)` before the DataExporter summary write,
  `logging.debug(...)` after with the row count (always 1). The DataExporter call
  already emits its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/571-mist-download-msp-saml-metadata/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- download_msp_saml_metadata.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New MspSsoExportUtils class + export_msp_saml_metadata
                         # method + _summarize_saml_metadata helper + PK strategy
                         # entry + menu 94 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 94
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 94 addition
data/                    # Runtime output target (existing dir):
                         #   * msp_<8>_sso_<8>_saml_metadata.xml  -- raw XML byte-for-byte
                         #   * msp_<8>_sso_<8>_saml_metadata.csv  -- DataExporter summary row
                         #   * mist_data.db                       -- SQLite, table
                         #     msp_sso_saml_metadata
documentation/api/msps/GET_msps_msp_id_ssos_sso_id_metadata.xml.md   # source schema (read-only)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on a brand-new `MspSsoExportUtils` class in `MistHelper.py`. Creating a new class
(rather than parking the method on an unrelated existing class) is justified above under
Principle II -- MistHelper has no existing class that owns MSP-level SSO operations, and
the constitution's class-based architecture rule explicitly prefers a correctly-scoped
new class over a wrapper or a mis-scoped extension. The menu number proposal is **94**,
chosen because operations 51-95 are the Safe Org Exports cluster, 95 is taken by the
in-flight `getOrgLicenseAsyncClaimStatus` work in spec 500, and 94 is the next available
contiguous integer below 95 that is far from both the resource-intensive block at 96-101
and the destructive block at 154-194. The full menu list is re-verified at task
generation time; if 94 collides with another in-flight feature branch, the next free
integer in the same cluster is used.

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
  `quickstart.md` confirms <=25 lines, 3 parameters, 5 logical blocks. The
  `_summarize_saml_metadata` helper stays under 25 lines because it only extracts six
  attributes from the parsed `EntityDescriptor` element. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `MspSsoExportUtils` class. No wrappers introduced. The new class is correctly
  scoped to MSP-level SSO operations and ready to accept sibling endpoints (e.g.,
  `listMspSsos`, `getMspSso`, JSON-metadata variant) in future PRs without further
  restructuring.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. The raw XML is written to a
  short-form path that does not leak full UUIDs.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or the raw XML
  body (only length, SHA-256, and the public entityID).
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry, the new
  class definition, and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (each prompt, the API call,
  the raw-XML file write, the DataExporter summary write).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
