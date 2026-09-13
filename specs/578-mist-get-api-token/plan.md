# Implementation Plan: GetApiToken Menu Item

**Branch**: `578-mist-get-api-token` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/578-mist-get-api-token/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/self/apitokens/{apitoken_id}` (operationId `getApiToken`) to retrieve the
metadata of a single API token belonging to the authenticated admin -- name, creation
time, last-used epoch, and the (redacted) key fingerprint. The menu item prompts the user
for the target `apitoken_id` via `safe_input()`, invokes the `mistapi` SDK call
`mistapi.api.v1.self.api_token.getApiToken()`, normalizes the single-object response into
one row, and persists the result through `DataExporter.write_with_format_selection()` so
CSV, SQLite, and ArangoDB+Redis backends all receive consistent output. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the natural `id` UUID so that
repeated runs upsert cleanly into SQLite. The new operation is proposed as menu number
**96** -- the next available slot in the Interactive Safe / Viewers cluster (60-96),
adjacent to other single-object inspector operations and below the resource-intensive
block at 97-101.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend. The new table is
`self_api_tokens` with natural PK `id`.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known `MIST_API_TOKEN_ID` resolved from `.env` (or the first id returned by
the sibling `listApiTokens` call). Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) leaves menu 96
inside the default test sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change. The endpoint is account-scoped (no org_id required) so the
container's `.env`-supplied token alone is sufficient.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=2 seconds for typical token
lookups (the endpoint is non-paginated and the response is one small JSON object).
Adaptive delay metrics in `delay_metrics.json` and `tuning_data.json` continue to govern
back-off; the endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs
(the redacted `key` fingerprint such as `1qkb...QQCL` is the only token-shaped field
returned and is logged only at DEBUG with the same redaction the API supplies); all
output under `data/`; Windows-safe path joining (`os.path.join` / `pathlib.Path`).
**Scale/Scope**: One new public menu method (~20 lines) on the existing
`SelfAccountUtils` class (or `MiscExportUtils` if no Self cluster exists yet -- to be
confirmed at task time and a new class created on the same monolith if needed), one new
entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table (`self_api_tokens`),
one menu registration entry, one README operation-count bump, one CHANGELOG line. No new
dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_self_api_token()` stays under 25 lines,
  takes <=2 parameters (`self`, `apitoken_id`), and contains <=5 logical blocks (prompt
  -> validate UUID -> API call -> normalize single object to one row ->
  `DataExporter.write_with_format_selection()`). Hierarchy is unchanged: one new method on
  one class. No new packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a Self/account-scoped
  utility class within `MistHelper.py`. If no such class exists today, the implementation
  task introduces `SelfAccountUtils` (a real class, not a wrapper module) and parks the
  three sibling self-* endpoints under it for future cohesion. No standalone wrapper
  function is introduced. The menu dispatch in the main loop references the class method
  directly. Variable names use full words (`token_record`, `redacted_key`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context="self_api_token:apitoken_id"` so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET) and account-scoped, so
  no typed destructive-confirmation gate is required. The `apitoken_id` input is
  validated against the Mist UUID shape before the API call; on validation failure the
  method logs a warning and returns early. The API token used for authentication comes
  from `.env` via the existing `mistapi.APISession` and is never logged. The redacted
  `key` fingerprint returned by the API is persisted to `data/` only because the API
  itself already redacts it; the full secret is never available.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 96 getApiToken` -> `git push origin
  main` -> `.github/workflows/container-build.yml` runs -> `gh run watch` -> `podman
  pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run container
  -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before the API call ("Fetching API token %s", apitoken_id); `DEBUG` after the
  call with non-sensitive summary fields ("API token: name=%s created=%s last_used=%s",
  ...); `WARNING` on 404 / empty payload; `ERROR` on unexpected exception with full
  traceback via `logging.exception`. No raw API tokens, full request URLs with bearer
  headers, or unredacted secrets are logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK strategy
  dictionary entry, and the menu registration line will carry an inline comment that
  explains *why* the line exists, not merely what it does. Blank lines, closing
  parentheses, and decorators are exempt per the constitution. Any uncommented adjacent
  lines in the touched block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern: `logging.info(...)`
  before the SDK call, the call itself, `logging.debug(...)` after with a redacted result
  summary, `logging.info(...)` before write, `logging.debug(...)` after write. The
  `DataExporter` call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/578-mist-get-api-token/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_api_token.md # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on SelfAccountUtils class + PK strategy + menu 96
                         # registration. No new modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the new SQLite table created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on `SelfAccountUtils` (existing or newly introduced) in `MistHelper.py`. The menu
number proposal is **96**, chosen because operations 60-96 form the Interactive Safe /
Viewers cluster and 96 is the next available slot below the resource-intensive block at
97-101. The full menu list will be re-verified at task generation time; if 96 collides
with an in-flight feature branch (notably the parallel `578-...` cohort), the next free
integer in the same cluster is used and recorded in `tasks.md`.

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
  `quickstart.md` confirms <=25 lines, <=2 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on `SelfAccountUtils`. No
  wrappers introduced. If the class is created in this PR it is a real class definition,
  not a thin shim around module-level functions.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint is GET
  only, with no destructive side effect. `safe_input()` is the documented prompt path.
  UUID validation happens before the SDK call. The API never returns the raw secret.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the bearer token or full URLs with auth.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
