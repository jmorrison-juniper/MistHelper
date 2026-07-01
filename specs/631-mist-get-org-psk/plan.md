# Implementation Plan: GetOrgPsk Menu Item

**Branch**: `631-mist-get-org-psk` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/631-mist-get-org-psk/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/psks/{psk_id}` (operationId `getOrgPsk`) to retrieve a
single Pre-Shared Key record by its PSK UUID. Menu 46 (`listOrgPsks`) already dumps
the full PSK list; this new item complements it by fetching one PSK's full detail
(including passphrase, MAC binding, expiry data) when the user already knows the
target PSK UUID. The menu prompts for `org_id` (default from `.env`) and `psk_id`
via `safe_input()`, invokes `mistapi.api.v1.orgs.psks.getOrgPsk()`, wraps the single
returned object into a one-row list, and persists it through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` under the natural-PK strategy (`id`) so repeat
runs upsert cleanly into SQLite. The new operation is proposed as menu number
**96** -- the next available slot in the interactive safe cluster (60-96), sitting
adjacent to existing PSK-related tooling.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises safe menu items in
non-interactive mode. Menu 96 requires two identifiers (org + psk), so it is
covered by the interactive-safe test path that reads `MIST_ORG_ID` and a test
`MIST_PSK_ID_TEST` from `.env` when present, otherwise it is skipped gracefully.
Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`.
The destructive skip list (14, 18, 63-65, 90-100) is unaffected -- new item 96
sits inside the default sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200;
both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint
is not paginated and returns a single JSON object. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; the
call is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets
in logs (passphrase field is present in the response and must NOT appear in log
lines -- only counts and non-secret metadata may be logged); all output under
`data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public method (~20 lines) on the existing
`OrgExportUtils` class (which already owns `listOrgPsks` at menu 46), one new
entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed `getOrgPsk`, one new SQLite
table `org_psk_detail`, one menu registration entry, one README operation-count
bump, one CHANGELOG line. No new dependencies, no new modules, no new
directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_psk_detail()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `psk_id`), and contains <=5
  logical blocks (prompt -> validate UUID -> API call -> wrap-to-list ->
  DataExporter call). Hierarchy is unchanged: one new method on an existing
  class. No new packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `OrgExportUtils` class -- the same class that already owns the related
  `listOrgPsks` bulk export at menu 46. No standalone wrapper function is
  introduced. Menu dispatch in the main loop references the class method
  directly. Variable names use full words (`psk_record`, `org_uuid`,
  `psk_uuid`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_psk_detail:org_id"`,
  `"org_psk_detail:psk_id"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both `org_id` and `psk_id` are
  validated against the Mist UUID shape before the API call; on validation
  failure the method logs a warning and returns early. API token comes from
  `.env` via the existing `mistapi.APISession` and is never logged. The
  passphrase field returned by the endpoint is NEVER emitted to any log
  statement -- only the record count (0 or 1) and non-secret metadata (id,
  name, ssid) may appear in DEBUG output.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` ->
  `black --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96 getOrgPsk`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `INFO` is emitted before the API call ("Fetching PSK detail for org %s psk %s");
  `DEBUG` after the call with non-secret summary ("PSK detail: id=%s name=%s
  ssid=%s usage=%s"); `WARNING` on 404 / empty payload; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. The `passphrase` and
  `old_passphrase` response fields are explicitly excluded from every log
  statement.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any adjacent uncommented lines in the touched block (the
  existing PSK menu cluster around line 11993) get comments added in the same
  PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a result summary (non-secret fields only), `logging.info(...)`
  before the export, `logging.debug(...)` after the export. The DataExporter
  call already emits its own per-backend log lines; the new method does not
  duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/631-mist-get-org-psk/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_psk.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on OrgExportUtils class + PK strategy entry
                         # keyed "getOrgPsk" + menu 96 registration. No new
                         # modules; same single-file monolith.
README.md                # Operation count bump + new row in menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir). New SQLite table
                         # org_psk_detail auto-created on first run by DataExporter.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `OrgExportUtils` class in `MistHelper.py` (the same
class that owns `listOrgPsks` at menu 46 -- see `MistHelper.py:11993`). The menu
number proposal is **96**, chosen because operations 60-96 are the Interactive
Safe cluster and 96 is the next available slot below the Resource-Intensive block
at 97-101. The full menu list will be re-verified at task generation time; if 96
collides with an in-flight feature branch, the next free integer in the same
cluster is used.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` update is a single insert into the existing
  dictionary (no level-5 hierarchy explosion).
- **Principle II (Class-Based)**: PASS -- All work lives on `OrgExportUtils`.
  No wrappers introduced. UUID validation is a private helper on the same class
  if it grows beyond a one-line call.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only with no destructive side effect. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call. The
  passphrase response field is redacted from every log statement.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting, never include the API token, and never
  include the PSK passphrase.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 `quickstart.md` shows the
  expected comment density on every executable line, including the PK strategy
  entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 `quickstart.md`
  enumerates the before/after log pairs for every meaningful action (prompt,
  API call, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
