# Implementation Plan: GetMspSamlMetadata Menu Item

**Branch**: `586-mist-get-msp-saml-metadata` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/586-mist-get-msp-saml-metadata/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/ssos/{sso_id}/metadata` (operationId `getMspSamlMetadata`)
to retrieve the SAML Service Provider metadata for a specific MSP SSO configuration. The
menu item prompts the user for both `msp_id` and `sso_id` via `safe_input()`, invokes the
`mistapi` SDK once, normalizes the single returned JSON object into one row (augmented with
the two path parameters so the row is self-describing), and persists the result through
`DataExporter.write_with_format_selection()` so the CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES`
keyed on `(msp_id, sso_id)` so repeated runs upsert cleanly into SQLite. The new operation is
proposed as menu number **58** -- the next available slot in the Misc cluster (56-59), which
is the closest existing home for MSP-scoped administrative reads.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive mode
using a known MSP ID and SSO ID from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
Heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected -- new item 58 sits
inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is
non-paginated, returns a single JSON object (typically <8 KB even with the embedded SAML
XML blob), and is not subject to per-tenant fan-out, so adaptive delay overhead is
negligible. Existing back-off via `delay_metrics.json` and `tuning_data.json` applies
unchanged.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`);
the embedded `metadata` string contains raw XML and must be written verbatim (no
re-encoding) so downstream IdP administrators can import it directly.
**Scale/Scope**: One new public menu method (~20 lines) on an existing administrative
class (`OrgAdminExportUtils` or the closest MSP-scoped peer -- see Structure Decision
below), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table
(`msp_saml_metadata`), one menu registration line, one README operation-count bump, one
CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_msp_saml_metadata()` stays under 25
  lines, takes <=3 parameters (`self`, `msp_id`, `sso_id`), and contains <=5 logical
  blocks (validate IDs -> API call -> augment row with path params -> DataExporter call
  -> return). Hierarchy is unchanged: one new method on an existing class, one new dict
  entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new menu registration line. No new
  packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  administrative-exports class (preferred: `OrgAdminExportUtils`, or the nearest existing
  MSP/SSO-scoped peer if one is present in MistHelper.py at task generation time). No
  standalone wrapper function is introduced. The menu dispatch in the main loop
  references the class method directly. Variable names use full words
  (`msp_identifier`, `sso_identifier`, `saml_metadata_row`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"msp_saml_metadata:msp_id"`, `"msp_saml_metadata:sso_id"`) so SSH
  and container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET), so no typed destructive-confirmation gate is required. Both
  identifiers are validated against the Mist UUID shape before the API call; on
  validation failure the method logs a warning and returns early. API token comes from
  `.env` via the existing `mistapi.APISession` and is never logged. The embedded SAML XML
  is treated as opaque content -- never parsed, never executed, only persisted.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 58 getMspSamlMetadata` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs validation + build ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching MSP SAML metadata for msp %s sso %s"); `DEBUG`
  after the call with size summary ("MSP SAML metadata received: metadata_bytes=%d
  acs_url=%s"); `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with
  full traceback via `logging.exception`. The full XML blob and full ACS URL are *not*
  logged at INFO -- only at DEBUG and only when explicitly requested. No secrets,
  tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing admin-export menu cluster) get comments
  added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a size summary,
  `logging.info(...)` before write, `logging.debug(...)` after write. The DataExporter
  call already emits its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/586-mist-get-msp-saml-metadata/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_msp_saml_metadata.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the existing admin/MSP exports class +
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 58
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing administrative-exports class in `MistHelper.py`. At task generation
time the implementer will pick the closest existing MSP/SSO-scoped peer class; if no such
class exists, the method lands on `OrgAdminExportUtils` (or its equivalent) since MSP SSO
configuration is conceptually adjacent to org-level admin / SSO operations. Creating a new
class is explicitly rejected: there is only one method to add and the constitution's
"class-based architecture" principle does not require one-class-per-endpoint. The menu
number proposal is **58**, chosen because it sits in the Misc cluster (56-59) which is the
documented home for read-only administrative reads that do not fit the Site / Device /
License clusters. The full menu list will be re-verified at task generation time; if 58
collides with an in-flight feature branch, the next free integer in the same cluster (or
the next contiguous free integer above 50) is used.

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
- **Principle II (Class-Based)**: PASS -- All work lives on a single existing class. No
  wrappers introduced. The lone augmentation helper (injecting `msp_id` / `sso_id` into
  the response row) is two assignments inline -- no extraction needed.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is GET
  only, with no destructive side effect. `safe_input()` is the documented prompt path
  for both IDs. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token. The full XML blob is logged
  only at DEBUG level.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
