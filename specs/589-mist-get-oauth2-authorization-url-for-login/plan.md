# Implementation Plan: GetOauth2AuthorizationUrlForLogin Menu Item

**Branch**: `589-mist-get-oauth2-authorization-url-for-login` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/589-mist-get-oauth2-authorization-url-for-login/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/login/oauth/{provider}` (operationId `getOauth2AuthorizationUrlForLogin`)
to retrieve an OAuth2 authorization URL plus the OAuth2 `client_id` for a named identity
provider (for example `google` or `azure`). The menu item prompts the user via
`safe_input()` for the required `provider` path parameter and an optional `forward`
callback URL, invokes the `mistapi` SDK exactly once, and persists the single-row JSON
response through `DataExporter.write_with_format_selection()` so the CSV, SQLite, and
ArangoDB+Redis backends each receive a consistent record. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the operationId so SQLite upserts cleanly on
repeated runs. The new operation is proposed as menu number **195** -- the next free
integer beyond the current 1-194 range, with the alternative slot **50** (tail of the
existing Config/Admin cluster 42-50) reserved as a fallback if 195 conflicts with another
in-flight branch.

## Technical Context

**Language/Version**: Python 3.13+ (Constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the only
permitted interface to Mist Cloud); `requests` (transport, transitive through `mistapi`);
`python-dotenv` for `.env` loading of `MIST_HOST` and `MIST_API_TOKEN`.
**Storage**: Multi-backend through `DataExporter.write_with_format_selection()`. SQLite
file `data/mist_data.db` is the local fallback (new table `login_oauth_authorization_url`);
CSV files land under `data/`; polyglot ArangoDB+Redis containers handle the graph and
cache backend without code change.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known provider (default `google`) sourced from `.env` (`OAUTH_TEST_PROVIDER`
or hard-coded fallback in the test path). Local quality gates: `python -m py_compile
MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check
MistHelper.py`. The heavy / destructive skip list (14, 18, 63-65, 90-100) does not
include 195, so the new item participates in the default test sweep when added at the
proposed slot.
**Target Platform**: Windows 11 + venv for local development; Podman Linux container
`ghcr.io/jmorrison-juniper/misthelper:latest` for production and SSH-on-port-2200 use.
Both surfaces must work without source change.
**Project Type**: CLI tool (single-file Python monolith `MistHelper.py`, approximately
28K lines) with an optional Gunicorn web UI on port 8055. This feature lives entirely
inside the CLI; no web UI surface is added.
**Performance Goals**: A single non-paginated GET request must complete within 5 seconds
on a healthy link. The endpoint returns one JSON object (two scalar fields:
`authorization_url`, `client_id`) so no pagination, batching, or back-pressure tuning is
needed. The shared adaptive delay loop in `delay_metrics.json` plus `tuning_data.json`
continues to govern back-off on 429.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets (API
token, full authorization URL with state, or `client_id`) appear in logs above DEBUG; all
output lands under `data/`; path joining uses `os.path.join()` or `pathlib.Path()` for
Windows / Linux portability.
**Scale/Scope**: One new public menu method (target <=25 lines) added to an existing
class (proposed: `SelfAndLoginExportUtils`, or a freshly created `LoginOAuthExportUtils`
if no class today owns the `/api/v1/login/*` family -- the implementation pass picks
whichever already exists). One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`; one new
SQLite table (`login_oauth_authorization_url`); one new menu registration line; one
README operation-count bump; one CHANGELOG line. No new dependencies, no new modules, no
new top-level directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_oauth2_authorization_url()` stays
  under 25 lines, takes <=3 parameters (`self`, `provider`, `forward`), and contains
  <=5 logical blocks (prompt `provider` -> prompt `forward` -> SDK call -> flatten one
  response row -> `DataExporter` call). Hierarchy is unchanged: one new method on an
  existing or already-required class. No new packages, modules, or top-level constants
  beyond the single `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the class that already
  owns adjacent login / self exports (or on a new `LoginOAuthExportUtils` class created
  for this and the related POST/DELETE OAuth endpoints if no class currently owns this
  family). No standalone wrapper function is introduced. The menu dispatch references
  the class method directly. Variable names use full words (for example
  `provider_name`, `oauth_response_row`, `callback_url`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"oauth_auth_url:provider"` and `"oauth_auth_url:forward"`) so
  SSH / container EOF exits cleanly with code 0 and no traceback. The endpoint is
  strictly read-only (HTTP GET), so no typed destructive-confirmation gate is required.
  The `provider` value is validated against a small allow-list of known OAuth2 provider
  shapes (alphanumeric plus dash, length 1-32) before the SDK call; on validation
  failure the method logs a warning and returns early. The API token is loaded from
  `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 195 getOauth2AuthorizationUrlForLogin`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop /
  remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `logging.info("Fetching OAuth2 authorization URL for provider %s", provider_name)` is
  emitted before the SDK call; `logging.debug("OAuth2 response received: client_id_len=%d
  url_len=%d", ...)` after the call records lengths only -- the full `authorization_url`
  (which carries a `state` token) and the `client_id` are not logged above DEBUG and
  never with the API token. A 401 / 403 / 404 surfaces as `logging.warning(...)`; an
  unexpected exception surfaces as `logging.exception(...)` and returns cleanly.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entry, and the menu registration line
  carries a same-line inline comment explaining *why* the line exists. Blank lines,
  decorators, and closing parentheses are exempt per the constitution. Any uncommented
  adjacent lines in the touched block receive comments in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each meaningful step (prompt, SDK call, flatten, write),
  `logging.debug(...)` after each step with a count or length summary. The
  `DataExporter` call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/589-mist-get-oauth2-authorization-url-for-login/
+-- plan.md              # This file
+-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
+-- data-model.md        # Phase 1 - response entities + DDL + PK registration
+-- quickstart.md        # Phase 1 - local run + .env + quality gates
+-- contracts/
|   +-- get_oauth2_authorization_url_for_login.md   # Phase 1 - HTTP + SDK contract
+-- spec.md              # Pre-existing feature spec (not modified by /speckit.plan)
+-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the login/self export class (or a new
                         # LoginOAuthExportUtils class) + PK strategy entry +
                         # menu 195 registration. Same single-file monolith;
                         # no new modules or directories.
README.md                # Operation count bump + new row in the menu table for op 195
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 195 addition
data/                    # Runtime output target (existing dir). DataExporter creates
                         # data/login_oauth_authorization_url.csv and the matching
                         # SQLite table on first run. No schema migration beyond the
                         # new PK strategy entry.
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing class that owns the adjacent `/api/v1/self/*` and `/api/v1/login/*`
exports. If no class currently owns this family (the endpoint is documented as
"Not currently used by MistHelper" in `documentation/api/admins/GET_login_oauth_provider.md`),
the implementation pass introduces a single new class `LoginOAuthExportUtils` so that the
related POST and DELETE OAuth endpoints have an obvious home for future specs --
explicitly avoiding any standalone wrapper function (Principle II). The menu number
proposal is **195**, the next free integer after the current 1-194 range. If 195 collides
with another in-flight branch, the fallback is **50** (the tail of the Config / Admin
cluster 42-50). The actual integer is re-verified at task generation time.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/get_oauth2_authorization_url_for_login.md`), the seven principles are
re-evaluated against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry is a single insert into an existing dict, so
  no level-4 or level-5 hierarchy explosion. Only one new SQLite table is introduced.
- **Principle II (Class-Based)**: PASS -- All work lives on the chosen login export
  class. No wrappers introduced. If a private flatten helper is needed, it becomes a
  private method on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms HTTP GET with
  no destructive side effect. `safe_input()` is the documented prompt path with explicit
  `context=` strings. Provider input is validated before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard deployment
  pipeline. Container rebuild is triggered by the standard `container-build.yml` flow.
- **Principle V (Observability)**: PASS -- All log statements in the design are
  ASCII-only with `%s` formatting. The full `authorization_url` and `client_id` are
  never logged above DEBUG and never alongside the API token.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the expected
  comment density on every executable line including the PK strategy entry and menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for prompt, SDK call, flatten, and export.

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
