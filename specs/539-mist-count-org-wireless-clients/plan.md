# Implementation Plan: countOrgWirelessClients Menu Item

**Branch**: `539-mist-count-org-wireless-clients` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/539-mist-count-org-wireless-clients/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/clients/count` (operationId `countOrgWirelessClients`) to
return aggregate counts of wireless clients in an organization, grouped by a caller-
selected distinct attribute (SSID, hostname, OS, device type, model, AP, VLAN, IP, etc.).
The menu item prompts the user for `org_id`, an optional `distinct` field, an optional
time window (`start`/`end` or `duration`), and a result `limit` via `safe_input()`;
invokes the `mistapi` SDK; flattens the `results` array into one row per distinct bucket
plus a single envelope row capturing `total`, `start`, `end`, `limit`, and the chosen
`distinct` field; and persists everything through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and the ArangoDB+Redis
polyglot backend all receive consistent output. Two new entries are registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **96** -- the next available slot in the Safe Org
Exports / clients cluster, sitting next to the existing client search and event search
operations.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (`.env`
loading of `MIST_HOST`, `MIST_API_TOKEN`, and the optional `MIST_ORG_ID` default).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers handle the graph + cache backend. No schema migrations are
required beyond two new `CREATE TABLE IF NOT EXISTS` statements emitted by DataExporter
on first run.
**Testing**: `python MistHelper.py --test` exercises the new menu item in non-interactive
mode against a known org from `.env`. Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) is unaffected
-- proposed menu 96 sits just outside the skip list and inside the default sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both must
work without code change. Paths use `os.path.join` / `pathlib.Path` exclusively.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request returns aggregated counts with default `limit`
of 100 buckets; expected response time <=5 seconds end-to-end. The endpoint is *not*
paginated in the typical search sense -- `limit` caps the number of bucket rows; full
retrieval is bounded by the standard 5000-calls-per-hour Mist API token budget.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` wraps every
`input()` call with explicit context tags so SSH and container EOF exits cleanly with
code 0; API token loaded from `.env` and never logged; all output stays under `data/`;
Windows-safe path joining throughout.
**Scale/Scope**: One new public menu method (~24 lines) on the existing
`ClientSearchUtils` class (the same class that owns the related `searchOrgWirelessClients`
exports for menus 66-72), one private flattening helper, two new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new CSV/SQLite tables
(`org_wireless_clients_count_envelope` and `org_wireless_clients_count_results`), one
menu registration line, one README.md operation-count bump, and one CHANGELOG.md entry.
No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_wireless_clients_count()` stays under 25 lines, takes <=5 parameters
  (`self`, `org_id`, `distinct`, `time_window`, `limit`), and contains <=5 logical
  blocks (prompt -> validate -> API call -> flatten envelope + results -> DataExporter
  writes). The single new private helper
  `_flatten_wireless_clients_count_results()` also stays under 25 lines. No new package,
  module, or top-level constant is introduced. Hierarchy unchanged: one new public method
  plus one private helper on an existing class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing
  `ClientSearchUtils` class -- the same class that owns adjacent operations such as
  `searchOrgWirelessClients` (menus 66-72). No standalone wrapper function is introduced.
  The menu dispatch references the class method directly. Variable names use full words
  (`distinct_field`, `bucket_row`, `time_window_args`) -- no single-letter iterators or
  ambiguous abbreviations.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"count_org_wireless_clients:org_id"`,
  `"count_org_wireless_clients:distinct"`,
  `"count_org_wireless_clients:duration"`,
  `"count_org_wireless_clients:limit"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET); no destructive
  confirmation gate is required. `org_id` is validated against the Mist UUID shape via
  the existing `is_valid_uuid()` helper before the API call; on validation failure the
  method logs a `WARNING` and returns early. The `distinct` value is whitelisted against
  a fixed enum (`ssid`, `hostname`, `os`, `device`, `model`, `ap`, `vlan`, `ip`, `mac`,
  none) before being passed to the SDK. The API token is loaded from `.env` via
  `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit
  `version YY.MM.DD.HH.MM - add menu 96 countOrgWirelessClients` -> `git push origin
  main` -> `.github/workflows/container-build.yml` runs validation + multi-arch build
  -> `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification. No pipeline steps are
  skipped.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s`-style formatting. `INFO`
  is emitted before each meaningful action ("Fetching wireless client count for org
  %s distinct=%s"); `DEBUG` after the API call with summary counts ("Count response:
  total=%d buckets=%d distinct=%s"); `WARNING` on 400 or 404 or empty payload; `ERROR`
  on unexpected exception with a full traceback via `logging.exception`. No secrets,
  tokens, request URLs, or full request bodies are logged. Output filenames intentionally
  use only the first 8 characters of the org UUID to keep shell history and `ls` output
  clean.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new public method, the new private
  helper, the two new `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries, and the menu
  registration line carries an inline `#` comment explaining *why* the line exists, not
  merely *what* it does. Blank lines, closing parentheses, and decorators are exempt per
  the constitution. Any uncommented adjacent lines in the touched menu cluster get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before each SDK call, prompt, flatten, and write; `logging.debug(...)`
  after each action with a count or status summary. The DataExporter call already emits
  its own per-backend log lines; the new method does not duplicate them. Specifically:
  before-prompt logs for org_id / distinct / duration / limit, before-API-call log, after-
  API-call summary log, before-flatten / after-flatten count logs for both envelope and
  results, before-write / after-write logs for both DataExporter calls.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception at the pre-research gate. No Complexity
Tracking entries are required at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/539-mist-count-org-wireless-clients/
|-- plan.md                                  # This file
|-- research.md                              # Phase 0 -- SDK signature, PK strategy, naming, menu, prompts
|-- data-model.md                            # Phase 1 -- entities + DDL + PK registration
|-- quickstart.md                            # Phase 1 -- local run + .env + quality gates
|-- contracts/
|   `-- count_org_wireless_clients.md        # Phase 1 -- HTTP + SDK contract
`-- tasks.md                                 # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method export_org_wireless_clients_count() on the
                         # existing ClientSearchUtils class, one private flattening
                         # helper, two ENDPOINT_PRIMARY_KEY_STRATEGIES entries, and one
                         # menu registration line. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump and new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite tables that DataExporter creates
                         # on first run)
documentation/api/orgs/  # Existing enriched per-endpoint doc consulted in Phase 0
  GET_orgs_org_id_clients_count.md
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on the existing `ClientSearchUtils` class in `MistHelper.py` (the class
that already owns adjacent wireless-client search and event-search operations -- menus
66-72). The menu number proposal is **96**, chosen because operations 1-95 are the Safe
Org Exports cluster, 96-101 sit at the boundary with the Interactive Safe / Resource-
Intensive range, and 96 is the next available integer that keeps client-related menu
items physically adjacent to their search counterparts. The final number will be re-
verified at `/speckit.tasks` time by grepping the menu table in `MistHelper.py`; if 96
collides with another in-flight branch the next free integer in the same cluster is used
and the README/CHANGELOG entries are adjusted in lockstep.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/count_org_wireless_clients.md`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method skeleton in
  `quickstart.md` confirms <=25 lines, <=5 parameters, <=5 logical blocks for the public
  method, and a single small flattening helper. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` insert is two adjacent dict entries -- no level-5
  hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `ClientSearchUtils`. No
  wrappers. The flatten helper is a private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint is
  GET only, with no destructive side effect. `safe_input()` is the documented prompt
  path; `is_valid_uuid()` validates org_id; `distinct` is whitelisted against a small
  enum before being sent.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  py_compile/ruff/black/commit/push/build/pull/restart pipeline.
- **Principle V (Observability)**: PASS -- All log lines in the design are ASCII-only,
  use `%s` formatting, and never include the API token or query string.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the expected
  comment density on every executable line, including the two PK strategy entries and
  the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompts, API call, flatten
  envelope, flatten results, write envelope, write results).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
