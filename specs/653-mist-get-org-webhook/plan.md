# Implementation Plan: GetOrgWebhook Menu Item

**Branch**: `653-mist-get-org-webhook` | **Date**: 2026-07-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/653-mist-get-org-webhook/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/webhooks/{webhook_id}` (operationId `getOrgWebhook`) to
retrieve the full configuration of a single organization webhook by its UUID. The
existing menu 47 (`listOrgWebhooks`) already enumerates webhooks; this new item
consumes that output by letting the user drill into one specific webhook to inspect
sensitive fields (secret, headers, oauth2_* credentials, topics list) that are only
returned in full by the per-item GET. The method prompts the user for an `org_id`
(defaulted from `.env` `MIST_ORG_ID` when present) and a `webhook_id`, both via
`safe_input()`; invokes the `mistapi` SDK once; persists the single-object response
through `DataExporter.write_with_format_selection()` so CSV, SQLite, and ArangoDB+Redis
backends all receive consistent output; and registers a `natural_pk` entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` keyed on the webhook `id` so repeat runs upsert
cleanly with no duplicates. The proposed menu number is **96**, adjacent to menu 47's
webhook-list operation but placed in the interactive-safe cluster (60-96) because the
call requires an interactive per-webhook prompt.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility
Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK, the sole
permitted interface to Mist Cloud); `requests` (transitive HTTP transport);
`python-dotenv` for `.env` loading of `MIST_HOST`, `MIST_API_TOKEN`, and optional
`MIST_ORG_ID`.
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. Local
fallback SQLite file `data/mist_data.db` receives the new `org_webhook_detail`
table; CSV files land in `data/`; polyglot ArangoDB + Redis containers handle the
graph + cache backend when configured.
**Testing**: `python MistHelper.py --test` exercises the menu item in
non-interactive mode using a known org and a webhook UUID sourced from a prior
menu-47 run. Local quality gates: `python -m py_compile MistHelper.py`,
`python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`. The
heavy / destructive skip list (14, 18, 63-65, 90-100) does not affect menu 96 --
it is a read-only single-record GET.
**Target Platform**: Windows 11 + venv for local development; Podman Linux
container (`ghcr.io/jmorrison-juniper/misthelper:latest`) for production and
SSH-on-2200. Both must work without code change.
**Project Type**: CLI tool -- single-file monolith `MistHelper.py` (~28K lines)
with optional Gunicorn web UI on 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request to fetch one webhook completes in <=2
seconds under normal conditions. Response is a single JSON object with no
pagination, so no chunking or streaming is needed. Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off; this
endpoint is light enough that no special tuning is required.
**Constraints**: ASCII-only logging (no Unicode or emoji); `safe_input()` for
every prompt; API token loaded from `.env` and never logged; webhook `secret`,
`oauth2_client_secret`, `oauth2_password`, and `splunk_token` fields are redacted
from log lines but persisted to the storage backends (they are the very fields
the user is asking for); all output under `data/`; Windows-safe path joining via
`os.path.join` / `pathlib.Path`.
**Scale/Scope**: One new public menu method (~20 lines) on an existing webhook
export class in `MistHelper.py` -- the same class that already owns menu 47
`listOrgWebhooks`. One new entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. One new
CSV / SQLite table (`org_webhook_detail`). One menu registration entry. One
README menu-table row. One CHANGELOG line. No new dependencies, no new modules,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method `export_org_webhook_detail()` stays
  under 25 lines, takes <=3 parameters (`self`, `org_id`, `webhook_id`), and
  contains <=5 logical blocks (validate inputs -> API call -> optional secret
  redaction for log line -> single-row flatten -> DataExporter call). Hierarchy
  is unchanged: one new method on an existing class. No new packages, modules,
  or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the same class
  that already owns the related menu 47 `listOrgWebhooks` export
  (`WebhookExporter` or the equivalent already-defined webhook class in
  `MistHelper.py`). No standalone wrapper function is introduced. The menu
  dispatch in the main loop references the class method directly. Variable
  names use full words (`webhook_id`, `webhook_row`, `redacted_summary`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with
  explicit `context=` strings (`"org_webhook_detail:org_id"`,
  `"org_webhook_detail:webhook_id"`) so SSH / container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no
  typed destructive-confirmation gate is required. Both `org_id` and
  `webhook_id` are validated against the Mist UUID shape before the API call;
  on validation failure the method logs a warning and returns early. The API
  token comes from `.env` via `mistapi.APISession` and is never logged.
  Response secrets are redacted from the INFO / DEBUG summary log lines even
  though they are persisted to the storage backends.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies
  without modification: `python -m py_compile MistHelper.py` ->
  `python -m ruff check MistHelper.py` -> `python -m black --check
  MistHelper.py` -> commit with `version YY.MM.DD.HH.MM - add menu 96
  getOrgWebhook` -> `git push origin main` ->
  `.github/workflows/container-build.yml` runs the validation and build ->
  `gh run watch <run-id>` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> stop / remove / re-run the
  container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` / `%d` style
  formatting. `INFO` is emitted before the API call
  (`"Fetching webhook %s for org %s"`); `DEBUG` after the call with summary
  fields (`"Webhook name=%s type=%s enabled=%s topics=%d"`); `WARNING` on 404
  / empty payload; `ERROR` on unexpected exception with full traceback via
  `logging.exception`. Secrets (`secret`, `oauth2_client_secret`,
  `oauth2_password`, `splunk_token`) are never emitted to any log stream --
  they are replaced with the literal string `"<redacted>"` in log arguments
  even when they are written to CSV / SQLite / ArangoDB.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new PK
  strategy dictionary entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does.
  Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched block (the
  existing webhook-export menu cluster) get comments added in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented pattern:
  `logging.info(...)` before the SDK call, the call itself, `logging.debug(...)`
  after with a redacted summary line, `logging.info(...)` before write,
  `logging.debug(...)` after write with the resolved output path. The
  DataExporter call already emits its own per-backend log lines; the new method
  does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the
Complexity Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/653-mist-get-org-webhook/
|-- plan.md              # This file
|-- research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 - response entity + DDL + PK registration
|-- quickstart.md        # Phase 1 - local run + .env + quality gates
|-- contracts/
|   `-- get_org_webhook.md   # Phase 1 - HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on the existing webhook exporter class
                         # (same class that owns menu 47 listOrgWebhooks), plus
                         # a new ENDPOINT_PRIMARY_KEY_STRATEGIES entry and a
                         # menu 96 registration. No new modules; same
                         # single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 96
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 96 addition
data/                    # Runtime output target (existing dir; no schema
                         # migration beyond the new SQLite table created on
                         # first run by DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a
new public method on the same webhook-exporter class that already contains
menu 47 (`listOrgWebhooks`). If the current class is not yet named as a
dedicated `WebhookExporter`, the new method is placed alongside menu 47 in
whatever class currently owns it, keeping the two webhook operations
co-located per Class-Based Architecture (no wrappers, no scattered
functions). The proposed menu number is **96**; it sits in the
interactive-safe cluster (60-96) because the call requires an interactive
per-record prompt for `webhook_id`. The full menu list will be re-verified at
task generation time; if 96 collides with an in-flight feature branch, the
next free integer in the same cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table
intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`,
`quickstart.md`, `contracts/`), the seven principles are re-evaluated against
the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=3 parameters, <=5 logical blocks. The
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary receives a single new key
  (existing structure), so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the existing
  webhook exporter class. No wrappers introduced. No new module files.
- **Principle III (Safety-First)**: PASS -- Phase 1 contract confirms the
  endpoint is GET only, with no destructive side effect. `safe_input()` is
  the documented prompt path for both IDs. UUID validation happens before
  the SDK call. Secret fields are redacted from log lines.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard
  container build + push + pull + restart pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are
  ASCII-only with `%s` / `%d` formatting and never include the API token or
  any response secret material.
- **Principle VI (Inline Comments)**: PASS -- Phase 1 quickstart shows the
  expected comment density on every executable line, including the PK
  strategy entry and menu registration line.
- **Principle VII (Action Logging)**: PASS -- Phase 1 quickstart enumerates
  the before / after log pairs for every meaningful action (prompt, API
  call, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
