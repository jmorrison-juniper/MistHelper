# Implementation Plan: GetOrgTicketAttachment Menu Item

**Branch**: `501-mist-get-org-ticket-attachment` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/501-mist-get-org-ticket-attachment/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/tickets/{ticket_id}/attachments/{attachment_id}`
(operationId `GetOrgTicketAttachment`) to retrieve metadata for a single attachment on a
support ticket. The endpoint returns one JSON object containing a short-lived signed
`content_url` (a forward-download URL with an embedded JWT) that the user or downstream
tooling can use to fetch the underlying binary file. The new menu method prompts the
user for `org_id`, `ticket_id`, and `attachment_id` via `safe_input()`, optionally
captures a time-range filter (`start` / `end` / `duration` query parameters), invokes the
`mistapi` SDK, flattens the single-object response into one row that also carries the
poll timestamp, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **96** -- the next available slot in the Interactive
Safe cluster (60-96), immediately adjacent to the safe-org-exports block and well above
the resource-intensive block at 97.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`). No new dependencies are added.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using known IDs from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. Heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected --
new item 96 sits inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds for typical
attachments (the endpoint is non-paginated and the response is a single JSON object
holding one URL string). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; the signed
`content_url` JWT is sensitive and is NEVER logged at any level (only the boolean
"url present / absent" is logged); all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`SupportTicketUtils` class (created in spec 188 for prior ticket endpoints; if not
present at implementation time, a new `SupportTicketUtils` class is added in lieu of a
standalone wrapper -- consistent with the class-based-architecture principle). One new
entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV/SQLite table
(`org_ticket_attachments`). One menu registration entry. One README operation-count
bump. One CHANGELOG line. No new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_ticket_attachment()` stays under 25 lines, takes <=5 parameters
  (`self`, `org_id`, `ticket_id`, `attachment_id`, `time_filter`), and contains <=5
  logical blocks (prompt -> validate -> API call -> flatten -> DataExporter call).
  Hierarchy is unchanged: one new method on an existing (or one minimal new) class. No
  new packages, modules, or top-level constants are introduced. The flattener stays
  inline as a 3-line dict comprehension; if it grows past 5 lines during implementation,
  it is extracted to a private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the
  `SupportTicketUtils` class (the same class that owns the existing
  ticket-list, ticket-detail, and ticket-comment export operations from spec 188).
  If `SupportTicketUtils` does not yet exist at implementation time, it is created as a
  proper class in the same single-file monolith rather than as a standalone wrapper
  function. The menu dispatch in the main loop references the class method directly.
  Variable names use full words (`attachment_row`, `time_filter_value`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"org_ticket_attachment:org_id"`,
  `"org_ticket_attachment:ticket_id"`, `"org_ticket_attachment:attachment_id"`,
  `"org_ticket_attachment:time_filter"`) so SSH / container EOF exits cleanly with code
  0 and no traceback. The endpoint is strictly read-only (HTTP GET) and the only
  state-changing side effect (logging) is bounded -- no typed destructive-confirmation
  gate is required. All three UUID-shaped IDs are validated against the
  `is_valid_uuid()` helper before the API call; on validation failure the method logs a
  warning and returns early. API token comes from `.env` via the existing
  `mistapi.APISession` and is never logged. The returned `content_url` carries an
  embedded JWT and is treated as sensitive: only its presence/absence is logged at
  `DEBUG`, never the URL itself.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 GetOrgTicketAttachment`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove /
  re-run container -> `podman ps` verification. No deviation from the documented
  deployment workflow.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching attachment %s for ticket %s in org %s");
  `DEBUG` after the call with a non-sensitive summary ("Received attachment metadata:
  content_url present=%s"); `WARNING` on 404 / empty payload; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. The signed `content_url` JWT
  is excluded from every log line at every level. No secrets, tokens, or full request
  URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block (the existing support-ticket menu cluster) get comments
  added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each prompt, `logging.info(...)` before the SDK call, the call itself,
  `logging.debug(...)` after with a presence summary, `logging.info(...)` before
  flatten, `logging.debug(...)` after flatten, `logging.info(...)` before write,
  `logging.debug(...)` after write. The DataExporter call already emits its own
  per-backend log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/501-mist-get-org-ticket-attachment/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org_ticket_attachment.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SupportTicketUtils class + PK strategy + menu 96
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the `SupportTicketUtils` class in `MistHelper.py` (the same class that owns
the other support-ticket exports from spec 188). The menu number proposal is **96**,
chosen because operations 60-96 are the Interactive Safe cluster (this endpoint requires
three user-supplied UUID prompts, placing it firmly in the interactive-safe block) and
96 is the next available integer below the resource-intensive cluster that begins at
97. The number is provisional -- at `/speckit.tasks` time, `MistHelper.py` is grep'd
for the latest allocated menu integer and 96 is shifted forward if an in-flight branch
has consumed it.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary gets a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `SupportTicketUtils`. No
  wrappers introduced. The flattener helper, if extracted, is added as a private method
  on the same class.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path. UUID validation happens before the SDK call. The signed `content_url` JWT is
  never logged.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting, never include the API token, and never include the signed
  `content_url`.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (each prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
