# Implementation Plan: countMspTickets Menu Item

**Branch**: `505-mist-count-msp-tickets` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/505-mist-count-msp-tickets/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/msps/{msp_id}/tickets/count` (operationId `countMspTickets`) to retrieve
distinct-attribute count aggregates of support tickets across an MSP-managed
organization set. The menu method prompts the user for an `msp_id` and an optional
`distinct` attribute (with sane default) via `safe_input()`, calls the `mistapi` SDK,
flattens the `results` array into one row per distinct bucket plus a single summary
row, and persists results via `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends each receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (one for the bucket rows, one for the
summary snapshot) so repeated polls upsert cleanly. The new operation is proposed as
menu number **88** -- the next provisional slot inside the Interactive Safe range
(60-96), where MSP-tag read-only counts sit naturally alongside other safe enumerations
and well clear of the resource-intensive (97-101) and destructive (154-194) clusters.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, and the optional `MIST_MSP_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis container backend handles the graph + cache path. New SQLite tables
`msp_tickets_count_summary` and `msp_tickets_count_buckets` are created on first write
by the DataExporter (no manual DDL run).
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively
using `MIST_MSP_ID` from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Menu 88
sits inside the default test sweep range (heavy/destructive skip list is 14, 18, 63-65,
90-100; 88 is not on that list).
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both
targets must work without code change; path handling uses `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET completes in <=5 seconds for typical MSPs (the endpoint
returns a small JSON object: one summary plus a `results` array bounded by the `limit`
query parameter, default 100). Adaptive delay state in `delay_metrics.json` and
`tuning_data.json` continues to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all outputs under `data/`; Windows-safe path joining; no direct `requests` calls
(must go through `mistapi`).
**Scale/Scope**: One new public menu method (~22 lines) on a new `MspTicketsExportUtils`
class that owns MSP-tag ticket operations going forward; two new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (summary + buckets); two new SQLite tables created on
first write; one menu registration line; one README operation-count bump; one CHANGELOG
line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_msp_tickets_count()` stays under 25
  lines, takes <=3 parameters (`self`, `msp_id`, `distinct_attr`), and contains <=5
  logical blocks (prompt -> validate -> API call -> flatten summary + buckets ->
  DataExporter writes). Hierarchy adds one new class (`MspTicketsExportUtils`) on the
  module, one new public method, and one private flattening helper -- all comfortably
  inside the 5-children limit at every hierarchy level. No new packages, modules, or
  top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `MspTicketsExportUtils` class. A new class is justified because MistHelper currently
  has no MSP-tag class and the MSP path-prefix is a distinct domain (the constitution
  permits new classes; it forbids standalone wrapper functions). The menu dispatch in
  the main loop references the class method directly. Variable names use full words
  (`bucket_row`, `distinct_attr`, `summary_row`) -- no single-letter iterators or hidden
  wrappers.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input flows through `safe_input()` with explicit
  `context=` strings (`"msp_tickets_count:msp_id"`, `"msp_tickets_count:distinct"`,
  `"msp_tickets_count:limit"`) so SSH / container EOF exits cleanly with code 0 and no
  traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. `msp_id` is validated against the Mist UUID
  shape via the existing `is_valid_uuid()` helper before the API call; on validation
  failure the method logs a `WARNING` and returns early. The API token comes from
  `.env` via `mistapi.APISession` and is never written to any log line.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 88 countMspTickets` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching MSP ticket counts for msp %s distinct=%s");
  `DEBUG` after the call with summary counts ("MSP ticket count: total=%d buckets=%d
  limit=%d"); `WARNING` on 404 or empty payload; `ERROR` on unexpected exception with
  full traceback via `logging.exception`. The API token, the full request URL, and any
  cookie value are never logged at any level.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `MspTicketsExportUtils` class definition, the new PK strategy dictionary entries,
  and the menu registration line will carry an inline `#` comment that explains *why*
  the line exists, not merely what it does. Blank lines, closing parentheses, and
  decorators are exempt per the constitution. Any uncommented adjacent lines in the
  touched block (the menu dispatch table) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each `safe_input()` prompt, `logging.info(...)` before the SDK call, the call
  itself, `logging.debug(...)` after with result counts, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten, `logging.info(...)` before each
  DataExporter write. The DataExporter call already emits its own per-backend log lines;
  the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage. A new class is introduced but this aligns with -- not
violates -- Principle II.

## Project Structure

### Documentation (this feature)

```text
specs/505-mist-count-msp-tickets/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- count_msp_tickets.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New MspTicketsExportUtils class + new method
                         # export_msp_tickets_count() + 2 new
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entries + menu 88
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 88
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 88 add
data/                    # Runtime output target (existing dir, no schema migration
                         # required beyond two new SQLite tables created on first
                         # write by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a method on
a new `MspTicketsExportUtils` class in `MistHelper.py`. A new class (rather than reusing
an existing class) is justified because MistHelper has no prior MSP-tag class, and the
class-based-architecture principle prefers a new cohesive class over forcing MSP
behavior into an unrelated existing class such as `LicenseExportUtils` or
`OrganizationDataUtils`. The menu number proposal is **88**, chosen because operations
60-96 form the Interactive Safe cluster and 88 is a currently-free slot well clear of
the heavy/destructive test skip list (90-100). The number is provisional -- at
`/speckit.tasks` time, `MistHelper.py` is grep'd for the latest allocated menu integer
and 88 is shifted to the next free integer in the same cluster if a conflict exists
with an in-flight feature branch.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/count_msp_tickets.md`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The new
  class has one public method plus one private helper (`_flatten_bucket_rows`), so
  level-5 hierarchy stays inside the limit. The two `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  inserts are flat dict entries (existing structure), so no nested explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `MspTicketsExportUtils` class. No wrappers introduced. The flattening helper is a
  private method on the same class, not a module-level function.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. The optional `distinct` and
  `limit` query parameters are sanitized (whitespace stripped, integer-cast with
  exception handling) before being passed to the SDK.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token, request URL, or msp_id beyond
  the first eight characters where appropriate.
- **Principle VI (Inline Comments)**: PASS -- The quickstart skeleton shows the
  expected `#` comment density on every executable line, including the new class header,
  PK strategy dictionary entries, and menu registration line.
- **Principle VII (Action Logging)**: PASS -- The quickstart skeleton enumerates the
  before/after log pairs for every meaningful action (each prompt, validation, API
  call, flatten step, summary export, bucket export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
