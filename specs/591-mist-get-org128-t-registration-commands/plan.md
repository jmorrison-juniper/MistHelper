# Implementation Plan: GetOrg128TRegistrationCommands Menu Item

**Branch**: `591-mist-get-org128-t-registration-commands` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/591-mist-get-org128-t-registration-commands/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/128routers/register_cmd` (operationId
`getOrg128TRegistrationCommands`) to fetch the time-limited shell command,
registration code, and conductor command used to adopt a 128T / SSR router
into a Mist organization. The menu method prompts the user for an `org_id`
via `safe_input()`, optionally accepts a `ttl` override and a comma-separated
list of `asset_ids` (both query parameters exposed by the endpoint), invokes
the `mistapi` SDK once, flattens the single-object response into one row,
and persists the result through
`DataExporter.write_with_format_selection()` so CSV, SQLite, and
ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` so re-runs upsert cleanly on
the composite key `(org_id, registration_code)`. The new operation is
proposed as menu number **96**, the next available slot in the Safe Org
Exports / Org-Device-SSR cluster adjacent to spec 500 (menu 95) and the
related SSR-family endpoints captured by specs 595 and 645. The endpoint is
flagged DEPRECATED upstream, so the plan also documents a clear log warning
on every invocation.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK --
sole permitted interface to Mist Cloud); `requests` (transport, transitive);
`python-dotenv` (`.env` loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`.
SQLite file `data/mist_data.db` is the local fallback; CSV files land in
`data/`; the polyglot ArangoDB + Redis containers handle the graph + cache
backend. A single new SQLite table `org_128t_registration_commands` is
created on first run by `DataExporter` from the registered PK strategy.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known `MIST_ORG_ID` from `.env`. Local quality
gates: `python -m py_compile MistHelper.py`, `python -m ruff check
MistHelper.py`, `python -m black --check MistHelper.py`. The heavy /
destructive skip list (14, 18, 63-65, 90-100) excludes the new item 96
**only if** 96 is treated as a viewer slot; the test sweep is re-validated
during task generation and the menu number is shifted forward to the first
free integer in the 50-95 cluster if 96 still maps to a viewer in
`MistHelper.py` at implementation time.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux
container (`ghcr.io/jmorrison-juniper/misthelper:latest`) for production /
SSH-on-2200; both must work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K
lines) with optional Gunicorn web UI on 8055. This feature lives entirely
in the CLI.
**Performance Goals**: A single non-paginated GET; full round-trip must
complete in <=5 seconds under normal Mist API conditions. Adaptive delay
metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off; no special tuning is required for this endpoint.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no
secrets in logs (the response includes a `registration_code` -- it is
written to `data/` but **never** echoed to stdout and **never** included in
log lines above `DEBUG`); all output under `data/`; Windows-safe path
joining (`os.path.join` / `pathlib.Path`); deprecation warning emitted at
`logging.WARNING` on every invocation to keep operators aware that the
upstream endpoint may disappear.
**Scale/Scope**: One new public menu method (~22 lines) on a dedicated new
class `SSRRegistrationExportUtils` (introduced because no existing class
owns SSR / 128T adoption flows; alternative considered and rejected --
see Principle II below), one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new SQLite table
(`org_128t_registration_commands`), one menu registration entry, one
README operation-count bump, one CHANGELOG line. No new dependencies, no
new modules, no new top-level directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_org_128t_registration_commands()` stays under 25 lines, takes
  <=4 parameters (`self`, `org_id`, `ttl`, `asset_ids`), and contains
  <=5 logical blocks (prompt -> validate -> SDK call -> flatten ->
  `DataExporter` call). Hierarchy is unchanged at the package level:
  one new class file-internal to `MistHelper.py` adjacent to existing
  device-adoption classes. If the flatten logic grows past 5 lines
  during implementation it is extracted to a private helper method on
  the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  class `SSRRegistrationExportUtils` rather than as a wrapper function.
  A new class is justified (and preferred over bolting onto an
  existing one) because: (a) the related endpoints
  `getOrgSsrRegistrationCommands` (spec 645) and
  `getOrgAosRegisterCmd` (spec 595) share the same shape and natural
  owner -- adding all three to one class keeps the SSR-adoption
  surface cohesive; (b) the existing `InventoryExportUtils` and
  `DeviceExportUtils` classes already each carry close to the 5-method
  ceiling under Principle I and would breach it if extended. The
  menu dispatch references the class method directly; no standalone
  wrapper is introduced. Variable names use full words
  (`registration_code`, `router_shell_cmd`).

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()`
  with explicit `context=` strings
  (`"org_128t_register_cmd:org_id"`, `"org_128t_register_cmd:ttl"`,
  `"org_128t_register_cmd:asset_ids"`) so SSH / container EOF exits
  cleanly with code 0 and no traceback. The endpoint is strictly
  read-only (HTTP GET) so no typed destructive-confirmation gate is
  required. Org ID is validated against the Mist UUID shape before
  the API call; on validation failure the method logs a warning and
  returns early. `ttl` is coerced to `int` and bounded to the
  documented Mist range (>=60 seconds, <=31_536_000 seconds);
  `asset_ids` is parsed from a comma-separated string into a clean
  list with trimmed whitespace before being passed to the SDK. The
  API token comes from `.env` via the existing `mistapi.APISession`
  and is never logged. The returned `registration_code` and shell
  commands are written to `data/` but never echoed to stdout to avoid
  leaking adoption credentials in shared-terminal contexts.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline
  applies without modification: `python -m py_compile MistHelper.py`
  -> `ruff check` -> `black --check` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 getOrg128TRegistrationCommands`
  -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs -> `gh run watch`
  -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style
  formatting. `WARNING` is emitted once at method entry noting that
  the upstream endpoint is deprecated. `INFO` is emitted before the
  API call (`"Fetching 128T registration commands for org %s"`);
  `DEBUG` after the call with a redacted summary
  (`"Got registration response: code_len=%d shell_cmd_len=%d
  conductor_cmd_len=%d"` -- lengths only, never the codes themselves);
  `WARNING` on 404 / empty payload; `ERROR` on unexpected exception
  with full traceback via `logging.exception`. No secrets, tokens,
  registration codes, or full request URLs are logged at INFO or
  above.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  PK strategy dictionary entry, and the menu registration line will
  carry an inline comment that explains *why* the line exists, not
  merely what it does. Blank lines, closing parentheses, and
  decorators are exempt per the constitution. Any uncommented
  adjacent lines in the touched block (the menu registration cluster
  and the `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary tail) get
  comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.warning(...)` once on entry for the deprecation notice;
  `logging.info(...)` before the SDK call; the call itself;
  `logging.debug(...)` after with redacted length counts;
  `logging.info(...)` before flatten; `logging.debug(...)` after
  flatten with the resulting row count (always 0 or 1);
  `logging.info(...)` before write; `logging.debug(...)` after write
  with the resolved filename. The `DataExporter` call already emits
  its own per-backend log lines; the new method does not duplicate
  them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required
in the Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/591-mist-get-org128-t-registration-commands/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entities + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_org128_t_registration_commands.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New class SSRRegistrationExportUtils with method
                         # export_org_128t_registration_commands(), new
                         # ENDPOINT_PRIMARY_KEY_STRATEGIES entry, new menu
                         # 96 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table
                         # for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing
                         # menu 96 addition
data/                    # Runtime output target (existing dir, no schema
                         # migration needed beyond the new SQLite table
                         # created on first run by DataExporter)
documentation/api/orgs/GET_orgs_org_id_128routers_register_cmd.md
                         # Pre-existing enriched endpoint doc consulted as
                         # the authoritative request/response source for
                         # this feature
```

**Structure Decision**: Single-file monolith. The new menu item is added
as a new public method on a new class `SSRRegistrationExportUtils` in
`MistHelper.py`, justified above under Principle II to keep the SSR /
128T / AOS adoption family cohesive and to avoid breaching the
Five-Item Rule on already-near-ceiling neighbor classes. The menu
number proposal is **96**, chosen because (a) it sits at the boundary
between the Safe Org Exports cluster and the resource-intensive cluster
that begins at 97, (b) it is adjacent to spec 500's proposed menu 95
(also an org-license / device-adoption read), and (c) it leaves a tight
sibling slot for specs 595 (`getOrgAosRegisterCmd`) and 645
(`getOrgSsrRegistrationCommands`) in the same SSR family. The full
menu list is re-verified at task generation time; if 96 collides with
an in-flight feature branch, the next free integer in the same cluster
is used and `tasks.md` records the shift.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline
  in `quickstart.md` confirms <=25 lines, <=4 parameters, <=5 logical
  blocks. The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single
  insert into an existing dict, so no level-5 hierarchy explosion. The
  new class begins with a single method and is sized to host the two
  sibling SSR endpoints without breaching the five-method ceiling.
- **Principle II (Class-Based)**: PASS -- All work lives on
  `SSRRegistrationExportUtils`. No wrappers introduced. Flattening
  helpers, if needed, are added as private methods on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract
  confirms the endpoint is GET only, with no destructive side effect.
  `safe_input()` is the documented prompt path. UUID validation and
  TTL bounds happen before the SDK call. The `registration_code` is
  treated as sensitive output: written to `data/` only, never echoed
  to stdout, never logged above DEBUG.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the
  design are ASCII-only with `%s` formatting and never include the API
  token or registration code body.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows
  the expected comment density on every executable line, including
  the PK strategy entry, the deprecation warning, and the menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart
  enumerates the before/after log pairs for every meaningful action
  (deprecation warning, prompt, validate, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready
for `/speckit.tasks` to produce a task breakdown.
