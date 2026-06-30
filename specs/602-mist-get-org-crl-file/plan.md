# Implementation Plan: GetOrgCrlFile Menu Item

**Branch**: `602-mist-get-org-crl-file` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/602-mist-get-org-crl-file/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/crl` (operationId `getOrgCrlFile`) to retrieve the
organization's Certificate Revocation List (CRL) file used by Mist NAC to validate
client certificates. The menu item prompts for the `org_id` via `safe_input()`,
invokes the `mistapi` SDK, decodes the single base64 response into a binary blob,
computes lightweight metadata (length and SHA-256 fingerprint), writes the raw
`.crl` blob to `data/` for downstream tooling, and persists a metadata row through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive a consistent audit record. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated polls. The
new operation is proposed as menu number **96** -- the next available slot in the
safe-org / certificates / NAC area, sitting adjacent to other org-level read-only
viewer operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `base64` (stdlib, decode the response);
`hashlib` (stdlib, SHA-256 fingerprint); `python-dotenv` for `.env` loading
of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend. The raw
CRL blob itself is written as a sibling file under `data/` (not stored inside
SQLite) so downstream NAC tooling can consume it directly.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using `MIST_ORG_ID` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 96 sits inside the default
test sweep range (Viewers cluster 92-96).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds; CRL files
are typically small (<1 MB) so base64 decode and SHA-256 hash are sub-second.
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue
to govern back-off; this endpoint is light enough that no special tuning is
required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs; CRL bytes (raw or base64) never logged at any level; all
output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgConfigExportUtils` class (or a new `OrgSecurityExportUtils` class if no
sibling org-security exporter already exists -- verified at task generation
time), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new
CSV/SQLite metadata table (`org_crl_metadata`), one new raw-blob file pattern
under `data/` (`org_<short>_crl.crl`), one menu registration entry, one README
operation-count bump, one CHANGELOG line. No new pip dependencies, no new
modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_crl_file()` stays under
  25 lines, takes <=2 parameters (`self`, optional `org_id`), and contains
  <=5 logical blocks (prompt -> API call -> decode + hash -> write raw blob
  -> DataExporter call for metadata). Hierarchy is unchanged: one new method
  on an existing class. No new packages, modules, or top-level constants are
  introduced. Decoding and hashing are two short statements, not extracted
  helpers; if either grows past 5 lines during implementation, it is extracted
  to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgConfigExportUtils` class (the same class that owns adjacent org-level
  read-only exporters such as certificate and NAC configuration). No standalone
  wrapper function is introduced. The menu dispatch in the main loop references
  the class method directly. Variable names use full words (`crl_bytes`,
  `crl_sha256`, `crl_length`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  an explicit `context="org_crl_file:org_id"` string so SSH / container EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly read-only
  (HTTP GET), so no typed destructive-confirmation gate is required. Org ID is
  validated against the Mist UUID shape via `is_valid_uuid()` before the API
  call; on validation failure the method logs a warning and returns early. API
  token comes from `.env` via the existing `mistapi.APISession` and is never
  logged. The CRL itself, while not a secret in the credential sense, is also
  never logged in full -- only its length and SHA-256 fingerprint appear at
  DEBUG.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` -> `ruff check`
  -> `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96
  getOrgCrlFile` -> `git push origin main` -> `.github/workflows/container-build.yml`
  runs -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching CRL file for org %s");
  `DEBUG` after the call with metadata only ("CRL fetched: length=%d bytes
  sha256=%s") -- never the bytes themselves; `WARNING` on 404 / empty payload;
  `ERROR` on unexpected exception with full traceback via `logging.exception`.
  No secrets, tokens, or raw CRL bytes are logged at any level.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing org-config exporter cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a metadata-only summary, `logging.info(...)` before the raw blob
  write, `logging.debug(...)` after the blob write with the written path,
  `logging.info(...)` before the metadata DataExporter write, `logging.debug(...)`
  after. The DataExporter call already emits its own per-backend log lines;
  the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/602-mist-get-org-crl-file/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_crl_file.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgConfigExportUtils class + PK strategy +
                         # menu 96 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run by
                         # DataExporter, plus a new raw-blob filename pattern
                         # org_<short>_crl.crl)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the existing `OrgConfigExportUtils` class in
`MistHelper.py` (the class that owns adjacent org-level read-only configuration
exporters; if no such class exists yet, the new method instead joins the
`SafeOrgExports` cluster class -- final class binding confirmed at task
generation by grepping for sibling operationIds `getOrgCert` and
`listOrgSettingMistNacCrls`). The menu number proposal is **96**, chosen because
operations 92-96 form the Viewers cluster of safe org-level read-only menus
and 96 is the next available slot below the resource-intensive block at 97-101.
The full menu list will be re-verified at task generation time; if 96 collides
with an in-flight feature branch (the 6XX spec series may compete for the
same slot), the next free integer in the same cluster is used.

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
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks.
  The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on a single existing
  class (`OrgConfigExportUtils` or sibling, confirmed at task time). No
  wrappers introduced. Decoding and hashing are inline; if they grow, they
  move to private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation happens before the SDK call.
  Raw CRL bytes are never logged.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or CRL
  bytes; only length and SHA-256 fingerprint appear at DEBUG.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before/after log pairs for every meaningful action (prompt, API call,
  decode + hash, raw-blob write, metadata export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
