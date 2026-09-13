# Implementation Plan: GetOrgCapturingStatus Menu Item

**Branch**: `601-mist-get-org-capturing-status` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/601-mist-get-org-capturing-status/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/pcaps/capture` (operationId `getOrgCapturingStatus`) to
report the live status of any in-flight org-level packet capture job. The menu item
prompts the user for an `org_id` via `safe_input()`, calls the `mistapi` SDK, flattens
the single returned JSON object (a per-capture summary plus a nested `pcap_aps`
per-AP detail map) into one summary row and zero-or-more per-AP rows, and persists
the result through `DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so SQLite upserts cleanly on repeated polls. The new
operation is proposed as menu number **96** -- the last slot in the Interactive Safe
cluster (60-96), directly adjacent to the existing `PacketCaptureManager` menu items
(134-135) by domain and sitting one integer below the Resource-Intensive block at 97.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (loads
`MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_ORG_ID` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land under `data/`; polyglot
ArangoDB + Redis containers (per spec 188) handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the new menu item in non-interactive
mode using `MIST_ORG_ID` from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected
-- menu 96 sits at the top of the Interactive Safe range and inside the default test
sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200 and the
Gunicorn web UI on 8055. Both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with the
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. Endpoint is
non-paginated and returns a single small JSON object (one active capture per scope at
most). Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue
to govern back-off; no special tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); 404 from Mist (no active capture) must surface as a clean WARNING and
exit 0, not a traceback.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`PacketCaptureManager` class, one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for
the summary table plus one MistHelper-internal entry for the per-AP detail sub-table,
two new SQLite tables (`org_pcap_capture_status` and `org_pcap_capture_status_aps`),
one menu registration entry, one README operation-count bump, one CHANGELOG line. No
new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_capturing_status()` stays under
  25 lines, takes <=3 parameters (`self`, `org_id`, `_unused_placeholder_for_future`),
  and contains <=5 logical blocks (prompt -> API call -> flatten summary -> flatten
  per-AP detail -> DataExporter calls). Hierarchy is unchanged: one new method on an
  existing class. The per-AP flattener is a single dict-comprehension; if it grows
  past 5 lines during implementation it is extracted to `_flatten_capture_aps()` on
  the same class. No new packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `PacketCaptureManager` class (the same class that already owns menu 10 -- the
  reference doc `documentation/api/utilities/GET_orgs_org_id_pcaps_capture.md`
  explicitly states "Used by Menu **10** (`PacketCaptureManager.start_org_packet_capture`)
  to check capture status"). No standalone wrapper function is introduced. Menu
  dispatch in the main loop references the class method directly. Variable names use
  full words (`capture_status_row`, `per_ap_detail`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input flows through `safe_input()` with an explicit
  `context=` string (`"org_capturing_status:org_id"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly read-only (HTTP
  GET) -- no typed destructive-confirmation gate is required. Org ID is validated
  against the Mist UUID shape before the API call; on validation failure the method
  logs a WARNING and returns early. API token comes from `.env` via
  `mistapi.APISession` and is never logged. The 404 "no active capture" path is
  handled as a benign warning, not an error, matching the Gotchas listed in the
  enriched per-endpoint doc.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black
  --check` -> commit with `version YY.MM.DD.HH.MM - add menu 96 getOrgCapturingStatus`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh
  run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification. README and CHANGELOG
  are updated in the same commit. The `auto-merge` label is applied only after
  CodeQL goes green per the Multi-Agent Git Workflow section of the constitution.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style formatting. `INFO`
  is emitted before the API call ("Fetching capturing status for org %s"); `DEBUG`
  after the call with a summary line ("Capture id=%s type=%s started_time=%s
  num_packets=%s"); `WARNING` on 404 ("No active capture for org %s") and on empty
  payload; `ERROR` on 401/403 with explicit guidance to check the token; `ERROR` on
  unexpected exception with full traceback via `logging.exception`. No secrets,
  tokens, request URLs, or `Authorization` headers are logged at any level.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entries, and the menu registration
  line will carry an inline comment that explains *why* the line exists, not merely
  what it does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block of
  `PacketCaptureManager` get comments added in the same PR so the entire edited
  region meets the standard.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each meaningful action (prompt, API call, flatten
  summary, flatten per-AP detail, write summary, write detail) and
  `logging.debug(...)` immediately after with a count or key field summary. The
  DataExporter call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/601-mist-get-org-capturing-status/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_capturing_status.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on PacketCaptureManager class + two PK strategy
                         # entries + menu 96 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `PacketCaptureManager` class in `MistHelper.py` -- the
same class that already owns the start/stop org PCAP menu items, so a NOC engineer
will find all PCAP operations grouped under one owner. The menu number proposal is
**96**, chosen because operations 60-96 are the Interactive Safe cluster and 96 is
the last available slot below the Resource-Intensive block at 97-101. The full menu
list will be re-verified at `/speckit.tasks` time; if 96 collides with an in-flight
feature branch, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/get_org_capturing_status.md`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The two
  new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries are dict inserts (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `PacketCaptureManager`. No wrappers introduced. Flattening helpers, if extracted,
  are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation happens before the SDK call. 404 surfaces as a
  WARNING with zero rows written, not a traceback.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or full request
  URL.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entries and
  the menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, summary
  flatten, per-AP flatten, summary export, detail export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
