# Implementation Plan: countOrgTickets Menu Item

**Branch**: `531-mist-count-org-tickets` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/531-mist-count-org-tickets/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/tickets/count` (operationId `countOrgTickets`) to retrieve
aggregated counts of support tickets bucketed by a caller-chosen `distinct` attribute
(for example, `status`, `type`, or `created_by`). The menu method prompts the user for
an `org_id`, an optional `distinct` field, and an optional `limit` via `safe_input()`;
invokes the `mistapi` SDK; flattens the response (a single summary envelope plus an
array of per-bucket count rows) into two row sets; and persists them through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and the polyglot
ArangoDB+Redis backend all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated polls upsert cleanly into SQLite without
duplicating snapshots. The new operation is proposed as menu number **58** -- the next
available slot in the Safe Org Exports / Misc (56-59) cluster, sitting adjacent to
other low-volume org-level aggregate exports.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_ORG_ID` from
`.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback; CSV files land in `data/`; ArangoDB
graph + Redis cache containers handle the polyglot backend. No new schema migrations
beyond the new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries.
**Testing**: `python MistHelper.py --test` exercises the new menu item in
non-interactive mode using `MIST_ORG_ID` from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. Menu 58 sits inside the standard
`--test` sweep range (the skip list is 14, 18, 63-65, 90-100), so a green sweep
confirms the new item end to end.
**Target Platform**: Windows 11 + venv for local development; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
must work without code change. All paths joined with `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical orgs.
The endpoint is non-paginated (returns one summary object with an embedded `results`
array bounded by `limit`, default 100). Adaptive delay metrics in `delay_metrics.json`
and `tuning_data.json` continue to govern back-off; this endpoint is light enough that
no per-endpoint tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt with explicit
`context=` strings; no secrets in logs; all output under `data/`; Windows-safe path
joining; no Unicode/emoji.
**Scale/Scope**: One new public menu method (~22 lines) added to a new
`TicketExportUtils` class (no existing class currently owns ticket operations -- see
Structure Decision); two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (one for
the summary row, one for the per-bucket result rows); two new CSV / SQLite tables
(`org_tickets_count_summary` and `org_tickets_count_results`); one menu registration
entry; one README operation-count bump; one CHANGELOG line. No new third-party
dependencies, no new top-level modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_tickets_count()` stays under 25
  lines, takes <=4 parameters (`self`, `org_id`, `distinct`, `limit`), and contains
  <=5 logical blocks (prompt -> validate -> API call -> flatten summary + results ->
  DataExporter calls). Hierarchy adds at most one new class (`TicketExportUtils`)
  inside `MistHelper.py`; the rest of the project structure is unchanged. Any
  flattener that threatens to exceed 5 lines is extracted to a private helper method
  on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `TicketExportUtils` class. No standalone wrapper function is introduced; the menu
  dispatch in the main loop references the class method directly. A new class is
  justified because no existing class in `MistHelper.py` owns org-tickets operations
  (this is the first ticket-tag endpoint catalogued). Variable names use full words
  (`distinct_field`, `result_row`, `bucket_count`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_tickets_count:org_id"`, `"org_tickets_count:distinct"`,
  `"org_tickets_count:limit"`) so SSH / container EOF exits cleanly with code 0 and
  no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. `org_id` is validated via the existing
  `is_valid_uuid()` helper before the API call; on validation failure the method
  logs a `WARNING` and returns early. The `limit` input is coerced to `int` with a
  try / except guard; bad input falls back to the API default (100) with a logged
  notice. The API token is loaded from `.env` via the shared `mistapi.APISession`
  and is never written to logs or stdout.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  deviation: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 58 countOrgTickets` -> `git push origin main`
  -> `.github/workflows/container-build.yml` runs the validation + build jobs ->
  `gh run watch <run-id>` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest`
  -> stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the SDK call ("Counting org tickets for org %s by %s");
  `DEBUG` after the call with bucket counts ("Tickets count: total=%d buckets=%d");
  `WARNING` on 400 / 404 / empty payload; `ERROR` on unexpected exception with a
  full traceback via `logging.exception`. No secrets, tokens, or fully resolved
  request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new menu method, in the two new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entries, and on the menu registration
  line will carry an inline comment explaining *why* the line exists, not merely
  *what* it does. Blank lines, closing parentheses, and decorators are exempt per
  the constitution. Adjacent untouched lines in the surrounding code remain
  uncommented; only the new and modified block is required to meet the inline-
  comment density rule.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with response counts; `logging.info(...)` before each flatten, `logging.debug
  (...)` after each flatten with the produced row count; `logging.info(...)` before
  each `DataExporter.write_with_format_selection()` call. The DataExporter already
  emits its own per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/531-mist-count-org-tickets/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_org_tickets.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New TicketExportUtils class + new method + 2 PK strategy
                         # entries + menu 58 registration. Same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 58
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 58
data/                    # Runtime output target (existing dir). DataExporter creates
                         # the new SQLite tables on first write via CREATE TABLE IF
                         # NOT EXISTS; no manual migration step.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a public
method on a new `TicketExportUtils` class inside `MistHelper.py`. A new class is
justified per Constitution Principle II: no existing class owns operations under the
`Orgs Tickets` tag, so a wrapper function would be the only alternative -- which the
constitution forbids. The menu number proposal is **58**, chosen because the
1-59 Safe Org Exports range ends at 59 and 58 is the next available integer in the
Misc sub-cluster (56-59) that already hosts other org-level aggregate exports. The
final number is re-verified against `MistHelper.py` at `/speckit.tasks` time; if 58
collides with an in-flight feature branch, the next free integer in the same cluster
is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/count_org_tickets.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=4 parameters, <=5 logical blocks. The two
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries are dict-literal inserts into an existing
  structure; no level-5 hierarchy explosion. The new `TicketExportUtils` class is a
  single level-4 addition, not a new package.
- **Principle II (Class-Based)**: PASS -- All work lives on `TicketExportUtils`. No
  standalone wrapper functions. Flattening helpers, if needed, are added as private
  methods on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET-only with no destructive side effect. `safe_input()` covers every prompt;
  UUID validation runs before the SDK call; the API token is never logged.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- All log statements in the design are
  ASCII-only with `%s` formatting and never include the API token.
- **Principle VI (Inline Comments)**: PASS -- The quickstart skeleton shows the
  expected comment density on every executable line, including the PK strategy
  entries and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The quickstart skeleton enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call,
  flatten summary, flatten results, export summary, export results).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
