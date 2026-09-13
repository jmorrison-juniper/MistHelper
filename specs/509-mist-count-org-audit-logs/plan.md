# Implementation Plan: countOrgAuditLogs Menu Item

**Branch**: `509-mist-count-org-audit-logs` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/509-mist-count-org-audit-logs/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/logs/count` (operationId `countOrgAuditLogs`) to retrieve a
distinct-attribute count summary of admin audit log entries for an organization. The menu
item prompts the user for `org_id` and the `distinct` grouping field (with sensible
defaults) via `safe_input()`, optionally accepts time-range filters (`start`, `end`,
`duration`) and the standard server-side filter set (`admin_id`, `admin_name`, `site_id`,
`message`, `limit`), invokes the `mistapi` SDK, flattens the wrapper response into one
summary row plus N detail rows (one per distinct bucket), and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly into SQLite. The new
operation is proposed as menu number **89** -- the next available slot in the
audit-log / org-stats cluster, adjacent to the existing audit-log list operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected
-- menu 89 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for a typical org
(the endpoint is a server-side aggregation, not a paginated event stream). Adaptive
delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern back-off;
this endpoint is light enough that no per-endpoint tuning override is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); `distinct` must be one of the documented enum values, validated before
the SDK call.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`OrgLogsExportUtils` class (the same class that owns `listOrgAuditLogs` /
`searchOrgAuditLogs`; a new class is added only if no audit-log class exists today --
see Structure Decision below), one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, two
new CSV/SQLite tables (`org_audit_logs_count_summary` and `org_audit_logs_count_buckets`),
one menu registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new method `export_org_audit_logs_count()` stays under 25
  lines, takes <=5 parameters (`self`, `org_id`, `distinct`, `time_range`, `filters`),
  and contains <=5 logical blocks (prompt -> validate `distinct` -> API call -> flatten
  summary + buckets -> DataExporter call). Hierarchy is unchanged: one new method on an
  existing class. The bucket flattener is one comprehension; if it grows past 5 lines
  during implementation it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing audit-log
  exporter class (`OrgLogsExportUtils`, or whichever class currently owns
  `listOrgAuditLogs` / `searchOrgAuditLogs`). No standalone wrapper function is
  introduced. The menu dispatch in the main loop references the class method directly.
  Variable names use full words (`distinct_field`, `bucket_row`, `summary_row`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input flows through `safe_input()` with explicit
  `context=` strings (`"org_audit_logs_count:org_id"`,
  `"org_audit_logs_count:distinct"`, `"org_audit_logs_count:duration"`) so SSH /
  container EOF exits cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET) -- no typed destructive-confirmation gate is required. Org ID is
  validated against the Mist UUID shape and `distinct` is validated against the
  documented enum (`admin_id`, `admin_name`, `message`, `site_id`) before the SDK call;
  on validation failure the method logs a warning and returns early. The API token is
  loaded from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 89 countOrgAuditLogs` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Counting org audit logs for org %s by distinct=%s");
  `DEBUG` after the call with summary counts ("Audit-log count: total=%d buckets=%d
  distinct=%s window=%s..%s"); `WARNING` on 404 / empty payload or invalid `distinct`;
  `ERROR` on unexpected exception with full traceback via `logging.exception`. No
  secrets, tokens, or full request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  carries an inline comment explaining *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the constitution.
  Any uncommented adjacent lines in the touched audit-log menu cluster get comments
  added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)` after
  with bucket / total counts, `logging.info(...)` before flatten, `logging.debug(...)`
  after flatten, `logging.info(...)` before write, `logging.debug(...)` after write.
  The DataExporter call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. The Complexity Tracking table is empty.

## Project Structure

### Documentation (this feature)

```text
specs/509-mist-count-org-audit-logs/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_audit_logs.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the audit-log exporter class + PK strategy
                         # entry + menu 89 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 89
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 89 addition
data/                    # Runtime output target (existing dir). DataExporter creates
                         # the two new SQLite tables on first run; no migration script
                         # is required.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method `export_org_audit_logs_count()` on the existing audit-log exporter class
(`OrgLogsExportUtils`, or the equivalent class that currently owns `listOrgAuditLogs` /
`searchOrgAuditLogs`). If no such class exists at implementation time, the method is
added to the closest existing org-export class instead of creating a new class -- a new
class is not justified for a single read-only method (Principle I + II). The menu
number proposal is **89**, chosen because operations 60-91 cluster the
interactive-safe org / site exports and 89 is the next free integer near the existing
audit-log items. The exact integer is re-verified at `/speckit.tasks` time; if 89
collides with a parallel feature branch the next free integer in the same cluster is
used and the README / CHANGELOG numbers updated to match.

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
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry is a single insert into an
  existing structure, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the audit-log exporter
  class. No wrappers introduced. Flatten helpers, if needed, are added as private
  methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID and `distinct` enum validation happen before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
