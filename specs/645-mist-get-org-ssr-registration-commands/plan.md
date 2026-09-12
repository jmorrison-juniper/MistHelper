# Implementation Plan: GetOrgSsrRegistrationCommands Menu Item

**Branch**: `645-mist-get-org-ssr-registration-commands` | **Date**: 2026-06-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/645-mist-get-org-ssr-registration-commands/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/ssr/register_cmd` (operationId `getOrgSsrRegistrationCommands`)
to retrieve the shell commands, registration code, and conductor command a junior NOC
engineer needs to adopt a Session Smart Router (SSR / 128T) into the Mist Cloud. The menu
item prompts for `org_id` via `safe_input()`, optionally accepts a `ttl` override and a
comma-separated `asset_ids` list, invokes the `mistapi` SDK, wraps the single-object JSON
response into one row per invocation, and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis backends
all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly. The new operation is
proposed as menu number **95** -- the next available slot in the Safe Org Exports / Config
/ Admin cluster (menu 42-59, extended by recent adds).

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (`.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land under `data/`; the polyglot
ArangoDB + Redis containers handle graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item non-interactively using
the org UUID from `.env`. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. The heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- menu 95 sits inside the
default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds. The endpoint is not
paginated and returns a single JSON object (three string fields), so back-off tuning is
inherited from `delay_metrics.json` and `tuning_data.json` -- no special adjustment.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; API token never
logged; the returned `registration_code` and `router_shell_cmd` values are treated as
short-lived credentials -- logged only at DEBUG level with the token value redacted, and
written to `data/` under the operator's normal file protection.
**Scale/Scope**: One new public menu method (~22 lines) on the existing
`DeviceUtilityCommandsUtils` class (the class already responsible for the sibling
`128routers/register_cmd` endpoint per spec 014). One new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV/SQLite table
(`org_ssr_registration_commands`). One menu registration entry. One README operation-count
bump. One CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_ssr_registration_commands()` stays
  under 25 lines, takes <=4 parameters (`self`, `org_id`, `ttl`, `asset_ids`), and
  contains <=5 logical blocks (prompt collection -> optional query-param parsing -> API
  call -> single-row shape -> DataExporter call). Hierarchy unchanged: one new method on
  an existing class. No new packages, modules, or top-level constants.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- Behavior is added as a method on the existing
  `DeviceUtilityCommandsUtils` class -- the same class that already owns the sibling
  `getOrg128TRoutersRegistrationCmd` export (spec 014). No standalone wrapper function is
  introduced. Menu dispatch references the class method directly. Variable names use full
  words (`registration_row`, `asset_id_list`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"ssr_register_cmd:org_id"`, `"ssr_register_cmd:ttl"`,
  `"ssr_register_cmd:asset_ids"`) so SSH / container EOF exits cleanly with code 0 and no
  traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Org UUID is validated against the Mist UUID
  shape before the SDK call; on validation failure the method logs a warning and returns
  early. The `ttl` value is bounds-checked (1 <= ttl <= 31536000) before being passed to
  the SDK. `asset_ids` are split on commas and each token is UUID-validated. The
  registration secret returned by the API is written only to the operator's `data/` output
  and never emitted in INFO logs.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- Standard pipeline applies without modification: `python -m
  py_compile MistHelper.py` -> `ruff check` -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 95 getOrgSsrRegistrationCommands` -> `git push
  origin main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` ->
  `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching SSR registration command for org %s ttl=%s
  asset_ids=%d"); `DEBUG` after the call with a redacted summary
  ("SSR registration: conductor_cmd_len=%d router_shell_cmd_len=%d code_present=%s") --
  the actual command strings and the registration code are not printed. `WARNING` on 404
  or empty payload; `ERROR` on unexpected exception with `logging.exception`. No secrets,
  tokens, or request URLs are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line will
  carry an inline comment explaining *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the constitution. Any
  uncommented adjacent lines in the touched cluster receive comments in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before each `safe_input()` prompt, `logging.debug(...)` after with the received value
  length (never the value itself for secrets), `logging.info(...)` before the SDK call,
  `logging.debug(...)` after with response-shape counts, `logging.info(...)` before write,
  `logging.debug(...)` after write. `DataExporter` continues to emit its own per-backend
  log lines; the new method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries required in the Complexity
Tracking table.

## Project Structure

### Documentation (this feature)

```text
specs/645-mist-get-org-ssr-registration-commands/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_ssr_registration_commands.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on DeviceUtilityCommandsUtils class +
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry + menu 95 registration.
                         # No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 95
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 95 addition
data/                    # Runtime output target (existing dir). First run creates the
                         # `org_ssr_registration_commands` SQLite table via DataExporter.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing `DeviceUtilityCommandsUtils` class in `MistHelper.py` -- the same
class that owns the sibling 128T register-command export (spec 014). Menu number **95** is
proposed as the next available slot below the resource-intensive block at 96-101 and
alongside adjacent Safe Org Exports. If 95 collides with a concurrent in-flight branch at
task-generation time, the next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=4 parameters, <=5 logical blocks. The new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry is a single insert; the response is one flat
  object so no nested flatten helper is needed.
- **Principle II (Class-Based)**: PASS -- All work lives on `DeviceUtilityCommandsUtils`.
  No wrappers introduced.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms GET only with no
  destructive side effect. `safe_input()` is the documented prompt path. Org UUID, TTL
  range, and per-asset UUID validation all happen before the SDK call. Returned secret
  material is redacted in logs.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token, `registration_code`, or full
  command strings.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and the menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, validate, API call, write).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
