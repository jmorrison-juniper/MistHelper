# Implementation Plan: GetOauth2UrlForLinking Menu Item

**Branch**: `590-mist-get-oauth2-url-for-linking` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/590-mist-get-oauth2-url-for-linking/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/self/oauth/{provider}` (operationId `getOauth2UrlForLinking`) to retrieve the
OAuth2 authorization URL used to link an external identity provider (Google, Azure AD,
etc.) to the currently authenticated Mist admin account. The menu item prompts the user
for the OAuth `provider` slug via `safe_input()`, optionally collects the `forward`
query parameter (post-link redirect target), invokes the `mistapi` SDK function
`mistapi.api.v1.self.oauth2.getOauth2UrlForLinking()`, flattens the small two-field
response (`authorization_url`, `linked`) into a single row, and persists the result
through `DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output. A new entry is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so repeated runs upsert cleanly on the natural
`provider` key. The new operation is proposed as menu number **149** -- the next
available slot in the Config cluster (148-150), adjacent to other account / admin
configuration helpers. The endpoint is account-scoped (no `org_id` required) and is
documented by Juniper as the first leg of an OAuth2 linking handshake; MistHelper does
not follow the returned URL, it merely captures it for the operator to paste into a
browser session.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (for `.env`
loading of `MIST_HOST` and `MIST_API_TOKEN`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; polyglot ArangoDB
+ Redis containers handle the graph + cache backend.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using a known `provider` value from `.env` (`MISTHELPER_TEST_OAUTH_PROVIDER`, with
sensible default `google`). Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. Heavy /
destructive skip list (14, 18, 63-65, 90-100) is unaffected -- menu 149 sits inside
the Interactive / Config cluster which is part of the default `--test` sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200; both must
work without code change.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=2 seconds for typical OAuth
linking URL fetches (the endpoint is non-paginated and the response is a tiny JSON
object: one string + one boolean). Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` continue to govern back-off; this endpoint is light enough that no
special tuning is required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in
logs; all output under `data/`; Windows-safe path joining (`os.path.join` /
`pathlib.Path`); the returned `authorization_url` may contain a one-time CSRF / state
token -- it is persisted to local storage (`data/`) like any other API payload, but is
NEVER emitted to logs (the file path is logged, not the URL itself).
**Scale/Scope**: One new public menu method (~20 lines) on a new
`SelfOauthExportUtils` class (no existing class owns "self / OAuth" operations, so a
new class is justified by Principle II -- see Constitution Check below). One new entry
in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new CSV/SQLite table
(`self_oauth_link_url`). One menu registration entry. One README operation-count bump.
One CHANGELOG line. No new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_self_oauth_link_url()` stays under
  25 lines, takes <=3 parameters (`self`, `provider`, `forward`), and contains <=5
  logical blocks (prompt provider -> prompt forward -> API call -> flatten one row ->
  DataExporter call). One new class (`SelfOauthExportUtils`) is created to host this
  and the sibling POST endpoint that will follow in a separate spec; this keeps the
  hierarchy at the documented 5-level cap (project -> module -> class -> method ->
  expression). No new packages or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- A new class `SelfOauthExportUtils` is created in `MistHelper.py`
  because no existing class owns "Self OAuth2" tag operations -- the closest matches
  (`LicenseExportUtils`, `AdminExportUtils` if present) operate at the org or admin
  scope, not at the authenticated-self scope. The constitution explicitly permits new
  classes when the operation is a distinct domain; "Self OAuth2" is one of the Mist
  API tag namespaces. The menu dispatch in the main loop references the class method
  directly. No standalone wrapper function is introduced. Variable names use full
  words (`provider_slug`, `forward_url`, `oauth_response_row`) -- no single-letter
  iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"self_oauth_link_url:provider"`,
  `"self_oauth_link_url:forward"`) so SSH / container EOF exits cleanly with code 0
  and no traceback. The endpoint is strictly read-only (HTTP GET) -- it returns a URL
  to display, it does NOT perform the link itself -- so no typed
  destructive-confirmation gate is required. The `provider` value is validated
  against a small allow-list (`google`, `azure`, `microsoft`, `okta`, ...) before the
  API call; on validation failure the method logs a warning and returns early. API
  token comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 149 getOauth2UrlForLinking`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs -> `gh run
  watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove
  / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO`
  is emitted before the API call ("Fetching OAuth2 link URL for provider %s");
  `DEBUG` after the call with linked-flag only ("OAuth2 link URL fetched: linked=%s,
  url_length=%d"); `WARNING` on 404 / unknown provider; `ERROR` on unexpected
  exception with full traceback via `logging.exception`. The `authorization_url`
  string itself is NEVER logged because it carries a one-time CSRF / state token;
  only its length and the boolean `linked` flag are logged. No secrets, tokens, or
  full request URLs are emitted to log streams.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new
  `SelfOauthExportUtils` class definition, the new PK strategy dictionary entry, and
  the menu registration line will carry an inline comment that explains *why* the
  line exists, not merely what it does. Blank lines, closing parentheses, and class
  decorators are exempt per the constitution. Any uncommented adjacent lines in the
  touched menu-dispatch block get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with the result `linked` flag and URL length (not URL content),
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten,
  `logging.info(...)` before write, `logging.debug(...)` after write. The
  DataExporter call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/590-mist-get-oauth2-url-for-linking/
├── plan.md              # This file
├── research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
├── data-model.md        # Phase 1 - response entity + DDL + PK registration
├── quickstart.md        # Phase 1 - local run + .env + quality gates
├── contracts/
│   └── get_oauth2_url_for_linking.md   # Phase 1 - HTTP + SDK contract
└── tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New SelfOauthExportUtils class + new menu method 149 +
                         # PK strategy entry + menu registration. Single-file monolith
                         # remains intact.
README.md                # Operation count bump + new row in the menu table for op 149
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 149
                         # addition
data/                    # Runtime output target (existing dir, no schema migration
                         # needed beyond the new SQLite table created on first run
                         # by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method `export_self_oauth_link_url()` on a new
`SelfOauthExportUtils` class created in `MistHelper.py`. A new class is justified
under Principle II because no existing class owns the "Self OAuth2" Mist API tag
namespace; reusing `LicenseExportUtils` or any org-scoped class would mis-categorize
the operation. The menu number proposal is **149**, chosen because operations 148-150
form the Config cluster in the Interactive range (124-150) and 149 is the next
available slot adjacent to existing account / admin configuration helpers. The full
menu list will be re-verified at task generation time; if 149 collides with an
in-flight feature branch, the next free integer in the same cluster (148, 150, or
the next free integer in 124-147) is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally
empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against the
now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary is a single insert (existing
  structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the new
  `SelfOauthExportUtils` class. No wrappers introduced. The class is sized for one
  GET method now and one POST method later (when its companion spec lands), keeping
  it well under the 5-method ceiling.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. Provider allow-list validation happens before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` formatting and never include the API token or the
  `authorization_url` string content.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry and
  menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompts, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
