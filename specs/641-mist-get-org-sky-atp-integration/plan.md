# Implementation Plan: GetOrgSkyAtpIntegration Menu Item

**Branch**: `641-mist-get-org-sky-atp-integration` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/641-mist-get-org-sky-atp-integration/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/setting/skyatp/setup` (operationId
`getOrgSkyAtpIntegration`) to retrieve the Juniper Sky ATP (Advanced Threat
Prevention) integration configuration for an organization. The menu item
prompts the user for `org_id` via `safe_input()`, calls the `mistapi` SDK,
flattens the response (one summary row plus zero-or-more third-party threat
feed rows) and persists results through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A new pair of entries
is registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts
on repeated runs. The new operation is proposed as menu number **96** -- the
next available slot in the Safe Org Exports / Config-Admin cluster,
immediately adjacent to other org-setting exports and safely below the
Resource-Intensive block that begins at 97.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK --
the sole permitted interface to Mist Cloud); `requests` (transport,
transitive); `python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, optional
`MIST_ORG_ID` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; polyglot ArangoDB + Redis containers handle the graph + cache
backend. Two new SQLite tables (`org_sky_atp_integration` and
`org_sky_atp_threat_feeds`) are created on first write via `CREATE TABLE IF
NOT EXISTS` inside `DataExporter`.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode against the org configured in `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check
MistHelper.py`, `python -m black --check MistHelper.py`. The heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- menu 96 sits
inside the standard test sweep range.
**Target Platform**: Windows 11 with venv for local dev; Podman Linux
container (`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and
SSH-on-2200. Path handling uses `os.path.join` / `pathlib.Path` so both
platforms work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K
lines) with an optional Gunicorn web UI on port 8055. This feature lives
entirely in the CLI; no web-UI changes.
**Performance Goals**: Single GET completes in <=5 seconds. The endpoint is
non-paginated and returns a small JSON object (secintel config plus two
signed-URL strings), so no per-endpoint tuning is required. Adaptive delay
governance via `delay_metrics.json` + `tuning_data.json` applies.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` on
every prompt; the API token from `.env` is never logged or echoed; the
signed `secintel_allowlist_url` / `secintel_blocklist_url` are treated as
credentials and are logged only at DEBUG with hostname truncation; all
outputs live under `data/`.
**Scale/Scope**: One new public menu method (~22 lines) on a new
`OrgSecuritySettingsUtils` class (justified below under Principle II), two
new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables,
one menu registration line, one README operation-count bump, one CHANGELOG
line. No new third-party dependencies, no new top-level modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method
  `export_org_sky_atp_integration()` stays under 25 lines, takes <=2
  parameters (`self`, `org_id`), and contains <=5 logical blocks (prompt ->
  API call -> flatten summary -> flatten threat-feed list -> DataExporter
  call). Hierarchy is unchanged: one new method on one new (justified) class
  sibling to existing export-utility classes. If either flatten step grows
  past 5 lines during implementation, it is extracted to a private helper
  on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- A new class `OrgSecuritySettingsUtils` is introduced
  to host this method and future org-level security-integration exports
  (SkyATP is one of several: AAMW profiles, IDP profiles, AV profiles,
  service policies referenced from `.github/copilot-instructions.md`). This
  is a class, not a wrapper function. Variable names use full words
  (`threat_feed_row`, `integration_summary`). The menu dispatch in the main
  loop references the class method directly. No standalone wrapper
  functions are introduced.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with an explicit `context="org_sky_atp_integration:org_id"` string so
  SSH / container EOF exits cleanly with code 0 and no traceback. The
  endpoint is strictly read-only (HTTP GET); no typed destructive-
  confirmation gate is required. The org UUID is validated by
  `is_valid_uuid()` before the SDK call; on failure the method logs a
  WARNING and returns early. The `MIST_API_TOKEN` value from `.env` is
  consumed only by `mistapi.APISession` and never logged. The returned
  signed URLs (`secintel_allowlist_url`, `secintel_blocklist_url`) are
  written to CSV/SQLite intentionally (they are the data the user asked
  for) but are only echoed to the console at DEBUG with host portion only.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` -> `python -m black --check
  MistHelper.py` -> `git add MistHelper.py README.md CHANGELOG.md` ->
  `git commit -m "version YY.MM.DD.HH.MM - add menu 96
  getOrgSkyAtpIntegration"` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch <run-id>`
  -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style
  formatting. `INFO` is emitted before the API call ("Fetching Sky ATP
  integration for org %s"); `DEBUG` after the call summarizing feed counts
  ("Sky ATP: third_party_feed_count=%d has_allowlist_url=%s
  has_blocklist_url=%s"); `WARNING` on 404 / empty payload; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No
  secrets, tokens, or full signed URLs appear in INFO/WARN/ERROR lines.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, in both new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries, and in the menu registration
  line will carry an inline comment that explains *why* the line exists,
  not merely what it does. Blank lines, closing parentheses, and
  decorators are exempt per the Constitution. Any previously-uncommented
  adjacent lines in the touched block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call; the call itself;
  `logging.debug(...)` after with a result count summary;
  `logging.info(...)` before each flatten step; `logging.debug(...)` after
  each flatten with row counts; `logging.info(...)` before each
  DataExporter write. The DataExporter emits its own per-backend log
  lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in
the Complexity Tracking table at this stage. The Principle II decision to
introduce `OrgSecuritySettingsUtils` is a first-class class-based
extension, not a violation, because it hosts a family of related security-
integration methods (SkyATP now; AAMW / IDP / AV / service-policy
extensions in follow-up specs).

## Project Structure

### Documentation (this feature)

```text
specs/641-mist-get-org-sky-atp-integration/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_sky_atp_integration.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New OrgSecuritySettingsUtils class with method
                         # export_org_sky_atp_integration(); two new
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entries; one
                         # new menu registration for op 96. No new
                         # modules; same single-file monolith.
README.md                # Operation count bump; new row in the menu
                         # table for op 96.
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing
                         # menu 96 addition.
data/                    # Runtime output target (existing dir; no schema
                         # migration beyond the two new SQLite tables
                         # created on first write by DataExporter).
```

**Structure Decision**: Single-file monolith. The new menu item is added as
a new public method on a new `OrgSecuritySettingsUtils` class in
`MistHelper.py` (see Principle II above for the justification). The menu
number proposal is **96**, chosen because operations 1-59 are Safe Org
Exports, 60-96 are Interactive Safe (with Config/Admin at 42-50), and 96 is
the next available integer immediately before the Resource-Intensive block
at 97-101 + 153. Sky ATP integration retrieval is a single GET returning a
small config object -- it belongs in the safe cluster, not the resource-
intensive block. The number is provisional -- at `/speckit.tasks` time,
`MistHelper.py` is grep'd for the latest allocated menu integer and 96 is
shifted forward if a conflict exists.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty. The new `OrgSecuritySettingsUtils` class is not a
Principle II exception -- it is the constitutionally-preferred class-based
extension pattern (see Principle II verdict).

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks.
  The two `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries are two dict inserts
  into an existing structure, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `OrgSecuritySettingsUtils` class. No wrappers introduced. Flattening
  helpers are private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET-only, with no destructive side effect. `safe_input()` is
  the documented prompt path. UUID validation happens before the SDK call.
  Signed URLs are treated as sensitive material at INFO log level.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline. Container rebuild triggers on push to main via
  `.github/workflows/container-build.yml`.
- **Principle V (Observability)**: PASS -- All log statements in the
  design are ASCII, `%s`-formatted, and free of tokens or full signed URLs.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entries and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action
  (prompt, API call, flatten summary, flatten feeds, export summary,
  export feeds).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
