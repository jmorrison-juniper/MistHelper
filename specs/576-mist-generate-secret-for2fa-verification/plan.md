# Implementation Plan: generateSecretFor2faVerification Menu Item

**Branch**: `576-mist-generate-secret-for2fa-verification` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/576-mist-generate-secret-for2fa-verification/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/self/two_factor/token` (operationId `generateSecretFor2faVerification`,
mistapi SDK path `mistapi.api.v1.self.mfa.generateSecretFor2faVerification`) to retrieve
the TOTP secret that a Mist account holder needs in order to enroll a second factor in an
authenticator app. The endpoint is account-scoped (no `org_id` / `site_id` path
parameters), accepts a single optional query parameter `by` (when set to `qrcode` the
response is a PNG image rather than JSON), and returns a single object
`{"two_factor_secret": "<base32>"}`. The menu item prompts the user for the output mode
via `safe_input()`, invokes the SDK exactly once, flattens the single-field response into
one row, and persists it through `DataExporter.write_with_format_selection()` so CSV,
SQLite, and ArangoDB+Redis backends all receive a consistent record. A new entry is
registered in `ENDPOINT_PRIMARY_KEY_STRATEGIES` (auto-increment with a synthetic
captured-at unique key) so repeated runs do not collide. The new operation is proposed as
menu number **96** -- the next available slot in the Interactive Safe Viewers cluster
(92-96), which is the closest semantic home for an account-utility viewer.

## Technical Context

**Language/Version**: Python 3.13+ (per constitution Technology & Compatibility
Constraints, enforced by `requires-python` in `pyproject.toml`).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (HTTP transport, transitive); `python-dotenv` (for
`.env` loading of `MIST_HOST` and `MIST_API_TOKEN`). No new third-party packages added.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers handle the graph + cache backend. Output filename:
`data/self_two_factor_token.csv` (plus matching SQLite table `self_two_factor_token`).
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using the account credentials in `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- proposed item 96 sits inside the default sweep range.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without source change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with an
optional Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=2 seconds (response is one
small JSON object, not paginated). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning entry is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; the returned
secret string is sensitive -- it MUST NOT be written to the application log, only to the
chosen data backend (per spec FR-006 and the Security non-functional requirement). All
output lands under `data/`. Windows-safe path joining via `os.path.join` / `pathlib.Path`.
**Scale/Scope**: One new public menu method (~20 lines) on a new lightweight
`SelfAccountUtils` class (justified below -- no existing class owns `/self/` endpoints),
one new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`, one new CSV/SQLite table
(`self_two_factor_token`), one menu registration entry, one README operation-count bump,
one CHANGELOG line. No new third-party dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_self_two_factor_token()` stays under
  25 lines, takes <=2 parameters (`self`, `output_mode`), and contains <=5 logical
  blocks (prompt for mode -> SDK call -> branch on JSON vs qrcode bytes -> flatten to
  one row -> DataExporter call). Hierarchy is unchanged at the package level: one new
  small class on the existing monolith, one new method on that class. No new packages,
  modules, or top-level constants beyond a single `ENDPOINT_PRIMARY_KEY_STRATEGIES`
  entry.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on a new
  `SelfAccountUtils` class. A new class is justified (rather than attaching to an
  existing org/site exporter) because no current class owns `/self/` endpoints, and
  there are 5+ sibling `/self/*` endpoints in the OpenAPI spec that will land in
  follow-up specs and need a natural home. Creating the class once now prevents the
  wrapper-function anti-pattern later. No standalone wrapper function is introduced.
  Variable names use full words (`output_mode`, `secret_row`, `captured_at`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context="self_two_factor_token:output_mode"` so SSH / container EOF exits cleanly
  with code 0 and no traceback. The endpoint is strictly read-only (HTTP GET) and only
  exposes data already tied to the calling account's token -- no destructive
  confirmation gate is required. The TOTP secret itself is sensitive: it is written
  only to the chosen data backend (which the operator already trusts with API tokens),
  never to `script.log`, never echoed to stdout. The API token is loaded via the
  existing `mistapi.APISession` from `.env` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with
  `version YY.MM.DD.HH.MM - add menu 96 generateSecretFor2faVerification` ->
  `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the SDK call ("Requesting 2FA secret token for self account"),
  `DEBUG` after the call with a non-sensitive summary ("2FA token response received,
  mode=%s, secret_present=%s") -- the secret value itself is intentionally NOT
  formatted into any log line. `WARNING` is emitted on empty payload or 404; `ERROR`
  with `logging.exception` is emitted on unexpected exceptions. No API tokens, no
  cookies, and no `two_factor_secret` value appear in any log.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line of the new method, the new PK strategy
  dictionary entry, the new class definition, and the menu registration line will
  carry an inline comment explaining *why* the line exists. Blank lines, closing
  parentheses, and decorators are exempt. Any uncommented adjacent lines in the
  touched menu registration block get inline comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the prompt, `logging.debug(...)` after prompt with the
  chosen mode, `logging.info(...)` before the SDK call, `logging.debug(...)` after
  with a redacted result summary (presence flag only, never the secret),
  `logging.info(...)` before the DataExporter write, `logging.debug(...)` after with
  the row count. The DataExporter call already emits per-backend log lines; the new
  method does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/576-mist-generate-secret-for2fa-verification/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement, prompts
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- generate_secret_for2fa_verification.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New SelfAccountUtils class with export_self_two_factor_token
                         # method, new ENDPOINT_PRIMARY_KEY_STRATEGIES entry, and menu 96
                         # registration. Same single-file monolith, no new modules.
README.md                # Operation count bump and new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir). DataExporter creates the
                         # new self_two_factor_token table on first run; no manual
                         # migration needed.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on a new `SelfAccountUtils` class in `MistHelper.py`. A new class (rather than an
existing org/site exporter) is justified because no current class owns `/self/`
endpoints, and creating the natural home once now keeps Principle II clean as the
remaining `/self/*` endpoints land in follow-up specs. The menu number proposal is
**96**, the next available slot in the Interactive Safe Viewers cluster (92-96), which
is the closest semantic match for an account-utility viewer. If 96 collides with an
in-flight feature branch at task-generation time, the next free integer in the same
cluster (or the misc 56-59 range as a fallback) is used.

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
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary gains one entry (existing structure),
  so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `SelfAccountUtils` class. No wrappers introduced. Any future `/self/*` endpoints
  attach as additional methods on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is the
  documented prompt path. The sensitive `two_factor_secret` value is routed only to
  the chosen data backend and never to logs.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or the secret
  value.
- **Principle VI (Inline Comments)**: PASS -- The quickstart shows the expected
  comment density on every executable line, including the new class definition, the
  PK strategy entry, and the menu registration line.
- **Principle VII (Action Logging)**: PASS -- The quickstart enumerates the
  before / after log pairs for every meaningful action (prompt, SDK call, write).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
