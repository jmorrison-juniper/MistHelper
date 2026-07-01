# Implementation Plan: getOrgSsrUpgrade Menu Item

**Branch**: `646-mist-get-org-ssr-upgrade` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/646-mist-get-org-ssr-upgrade/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel` (operationId
`getOrgSsrUpgrade`) to retrieve the current status of a single Session Smart
Router (SSR) firmware upgrade job. Despite the `/cancel` suffix in the URL,
this is a status-read GET (documented gotcha in the enriched OpenAPI notes) and
is safe for a P1 read-only menu item. The new method extends the existing
`FirmwareManager` class -- the same class that already owns `listOrgSsrUpgrades`
and its polling helpers -- so no new module or wrapper is introduced. The menu
method prompts for `org_id` and `upgrade_id` via `safe_input()` (both default
to `.env` values when present), invokes the mistapi SDK, flattens the response
into one summary row plus zero-or-more per-target rows (one row per device MAC
in each of the `failed / queued / success / upgrading` buckets), persists both
through `DataExporter.write_with_format_selection()` for CSV / SQLite /
ArangoDB+Redis parity, and registers two entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (natural PK for the summary; composite PK for
the target rows) so repeated polls upsert cleanly. The new operation is
proposed as menu number **96**, the next available slot in the Viewers cluster
(92-96) and adjacent to the existing SSR firmware read paths.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution "Technology & Compatibility
Constraints"; agents.md "Local Development Quick Reference").
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's SDK -- the only
permitted interface to Mist Cloud per project convention); `requests`
(transport, transitive through mistapi); `python-dotenv` (already-loaded
`.env` bootstrap for `MIST_HOST`, `MIST_API_TOKEN`, optional `MIST_ORG_ID`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
Local fallback SQLite database `data/mist_data.db`; CSV files under `data/`;
polyglot ArangoDB + Redis containers handle the graph + cache backend when
enabled. No schema migration beyond two new tables auto-created on first write.
**Testing**: `python MistHelper.py --test` sweeps menu items in non-interactive
mode (heavy/destructive skip list 14, 18, 63-65, 90-100 is unaffected -- menu
96 sits inside the default sweep range). Local quality gates before any
commit: `python -m py_compile MistHelper.py`, `python -m ruff check
MistHelper.py`, `python -m black --check MistHelper.py`.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
`ghcr.io/jmorrison-juniper/misthelper:latest` for production (SSH on 2200, web
UI on 8055). Both paths must work with no source change -- `pathlib.Path` and
`os.path.join()` handle separators.
**Project Type**: CLI tool -- the single-file monolith `MistHelper.py`
(~28K lines) with an optional Gunicorn web UI on 8055. This feature is
CLI-only.
**Performance Goals**: Single GET request to a non-paginated endpoint returning
a compact JSON object; target end-to-end latency <=5 s including flatten and
export. Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json`
continue to govern back-off; no per-endpoint tuning needed.
**Constraints**: ASCII-only logging (no Unicode / emoji); `safe_input()` wraps
every prompt so SSH and container EOF exits 0 without a traceback; API token
loaded from `.env` and never logged; all output under `data/`; Windows-safe
path joining. 5-Item Rule enforced (<=25 lines per function, <=5 parameters,
<=5 nesting blocks).
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`FirmwareManager` class, two private flattener helpers (<=15 lines each) on
the same class, two new entries in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one
menu-registration entry in the main dispatch table, one README operation-count
bump plus a new row in the menu table, one CHANGELOG line. No new
dependencies, no new modules, no new directories, no destructive operations.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_ssr_upgrade_status()`
  stays under 25 lines, takes <=3 parameters (`self`, `org_id`, `upgrade_id`),
  and contains exactly 5 logical blocks (prompt org -> prompt upgrade ->
  SDK call -> flatten summary + targets -> two DataExporter calls). The two
  private helpers `_flatten_ssr_upgrade_summary()` and
  `_flatten_ssr_upgrade_targets()` are each <=15 lines and live on the same
  class. Hierarchy is unchanged: one new public method plus two private
  helpers on an existing class inside the existing single-file monolith. No
  new packages, modules, or top-level constants introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as methods on the existing
  `FirmwareManager` class (the same class that owns `_fetch_ssr_upgrades_payload`,
  `_check_ssr_upgrades`, `_record_ssr_upgrade`, and `_process_ssr_upgrade` --
  see `MistHelper.py` lines 18585, 19104-19144). No standalone wrapper
  function is introduced. The menu dispatch calls the class method directly.
  Variable names use full words (`upgrade_id`, `target_bucket`, `device_mac`);
  no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_ssr_upgrade_status:org_id"`,
  `"org_ssr_upgrade_status:upgrade_id"`) so SSH / container EOF exits code 0
  with no traceback. The endpoint is strictly read-only (HTTP GET), despite
  the misleading `/cancel` URL suffix -- the enriched OpenAPI doc explicitly
  flags this gotcha and the sibling `POST /orgs/{org_id}/ssr/upgrade/{upgrade_id}/cancel`
  is the actual cancel operation (out of scope). No destructive-confirmation
  gate is required. `org_id` and `upgrade_id` are validated against the Mist
  UUID shape via the existing `is_valid_uuid()` helper before the SDK call;
  on validation failure the method logs a `WARNING` and returns early. API
  token comes from `.env` via `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline runs
  unchanged: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 getOrgSsrUpgrade` -> `git push origin
  main` -> `.github/workflows/container-build.yml` triggers automatically
  (validation job runs `py_compile` before the build) -> `gh run watch <id>`
  -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification. No pipeline deviation.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All new log calls use ASCII text and `%s` percent-style
  formatting. `INFO` is emitted before each prompt, before the SDK call
  ("Fetching SSR upgrade status org=%s upgrade=%s"), before each flatten, and
  before each export. `DEBUG` follows every action with result counts
  ("SSR upgrade status=%s targets_success=%d targets_failed=%d
  targets_queued=%d targets_upgrading=%d"). `WARNING` on 400 / 404 or empty
  payload. `ERROR` on 401 / 403 with a token-hygiene reminder. No secrets,
  tokens, MAC-address lists, or full request URLs appear in log lines above
  DEBUG; even at DEBUG the API token is never included.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new public method, in the
  two private flattener helpers, in the two new `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  dictionary entries, and in the single menu-registration line will carry a
  same-line `#` comment explaining *why* the line exists, not merely *what* it
  does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched
  `FirmwareManager` block get comments added in the same PR so the surrounding
  region reaches the same density.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the mandated before/after
  logging pattern: `logging.info(...)` before each prompt, the prompt itself,
  `logging.info(...)` before the SDK call, the call, `logging.debug(...)` after
  the call with a summary count, `logging.info(...)` before each flatten,
  `logging.debug(...)` after with the flattened row count,
  `logging.info(...)` before each export. The DataExporter call emits its own
  per-backend log lines internally; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/646-mist-get-org-ssr-upgrade/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entities + SQLite DDL + PK strategy entries
|-- quickstart.md        # Phase 1 - local run, .env, expected files, quality gates
|-- contracts/
|   `-- get_org_ssr_upgrade.md   # Phase 1 - HTTP contract + mistapi SDK call signature
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New public method + 2 private flatteners on the existing
                         # FirmwareManager class (class defined at line 18585 today),
                         # 2 new ENDPOINT_PRIMARY_KEY_STRATEGIES entries next to the
                         # existing "listOrgSsrUpgrades" key at line 4796, and one
                         # menu-registration line in the main dispatch table.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96
data/                    # Runtime output target (existing dir; two new SQLite tables
                         # auto-created by DataExporter on first write:
                         # org_ssr_upgrade_summary and org_ssr_upgrade_targets)
```

**Structure Decision**: Single-file monolith preserved. The new menu item is
added as one new public method (`export_org_ssr_upgrade_status`) plus two
private helper methods on the existing `FirmwareManager` class. No new class,
no new module, no wrapper. Placement rationale: the class already owns every
other SSR upgrade code path in MistHelper (`_fetch_ssr_upgrades_payload`,
`_check_ssr_upgrades`, `_record_ssr_upgrade`, `_process_ssr_upgrade`), so the
per-upgrade status read belongs beside its siblings. The menu number proposal
is **96**, the next available slot in the Viewers cluster (92-96 per
`.github/copilot-instructions.md`) and safely below the Resource Intensive
block that begins at 97. The number is provisional -- at
`/speckit.tasks` time, `MistHelper.py` is grep'd for the highest currently
allocated menu integer and the proposal is shifted forward if 96 collides
with an in-flight feature branch.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/get_org_ssr_upgrade.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, and exactly 5 logical
  blocks in the public method. The two private helpers are each <=15 lines
  and each has <=3 parameters. Both `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries
  are single dict inserts -- no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `FirmwareManager`.
  No wrappers introduced. Flatteners are private methods on the same class,
  not free functions.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET-only despite the `/cancel` URL suffix. `safe_input()` is the
  documented prompt path. UUID validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline. Container build workflow validation job catches syntax errors
  before the image builds.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or MAC
  arrays at INFO level.
- **Principle VI (Inline Comments)**: PASS -- `quickstart.md` shows the
  expected same-line comment density on every executable line, including the
  two PK strategy entries and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- `quickstart.md` enumerates the
  before/after log pairs for every meaningful action (each prompt, the SDK
  call, each flatten, each export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after Phase 1 design. The plan is ready
for `/speckit.tasks` to produce a task breakdown.
