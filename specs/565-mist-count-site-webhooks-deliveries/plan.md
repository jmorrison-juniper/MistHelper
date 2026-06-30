# Implementation Plan: countSiteWebhooksDeliveries Menu Item

**Branch**: `565-mist-count-site-webhooks-deliveries` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/565-mist-count-site-webhooks-deliveries/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/sites/{site_id}/webhooks/{webhook_id}/events/count` (operationId
`countSiteWebhooksDeliveries`) to retrieve grouped delivery counts for a specific site
webhook over a configurable time window, optionally filtered by `error`, `status_code`,
`status`, and `topic`, and bucketed by `distinct`. The menu method collects `site_id` and
`webhook_id` from the user via `safe_input()` (with `.env` defaults where available),
prompts for optional filter values and the `distinct` field, invokes the `mistapi` SDK,
flattens the envelope (`distinct/start/end/limit/total`) into one summary row plus zero
or more bucket rows from the `results` array, and persists every backend via
`DataExporter.write_with_format_selection()`. A new pair of entries is registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` so that re-polling the same window upserts cleanly into
SQLite. The new operation is proposed as menu number **86** -- the next free slot in the
Stats sub-cluster (80-91) of the Interactive Safe range, which is the correct semantic
home for a count/aggregation endpoint scoped to a site.

## Technical Context

**Language/Version**: Python 3.13+ (constitution Technology & Compatibility Constraints).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- sole permitted
interface to Mist Cloud); `requests` (transport, transitive); `python-dotenv` (loads
`MIST_HOST`, `MIST_API_TOKEN`, and the optional site/webhook defaults).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback. CSV files land in `data/`. The polyglot
ArangoDB + Redis containers handle the graph + cache backend with identical row shape.
**Testing**: `python MistHelper.py --test` exercises the menu item in non-interactive
mode using known site and webhook IDs supplied via `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy / destructive skip list (14, 18,
63-65, 90-100) is unaffected -- proposed menu 86 sits well inside the default test sweep.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200. Both must
work without code change. Paths use `os.path.join` / `pathlib.Path`.
**Project Type**: CLI tool (single-file monolith `MistHelper.py` ~28K lines) with optional
Gunicorn web UI on port 8055. This feature lives entirely in the CLI.
**Performance Goals**: Single GET request completes in <=5 seconds on the default
`duration=1d` window; the response is bounded by `limit` (default 100, max governed by
Mist) so memory stays tiny. Adaptive delay metrics in `delay_metrics.json` and
`tuning_data.json` govern back-off; no special tuning required.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt; no secrets in logs;
all output under `data/`; Windows-safe path joining.
**Scale/Scope**: One new public menu method (~22 lines) on a webhook-focused class
(`WebhookExportUtils`, extending the existing class that already owns `listSiteWebhooks`
in menu 57 per the per-endpoint doc; if no such class exists today the method is added
to `SiteExportUtils` -- decided in research.md). One private flattener for the `results`
bucket array, one menu registration entry, two new entries in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`, two new SQLite tables
(`site_webhook_deliveries_count_summary` and `site_webhook_deliveries_count_buckets`),
one README operation-count bump, one CHANGELOG line. No new dependencies, no new modules,
no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_site_webhook_deliveries_count()` stays under 25 lines, takes <=5 parameters
  (`self`, `site_id`, `webhook_id`, `distinct`, `filters_dict`), and contains <=5 logical
  blocks (prompt -> filter assembly -> API call -> flatten summary + buckets ->
  DataExporter calls). Hierarchy is unchanged: one new public method plus one private
  helper (`_flatten_webhook_count_buckets`) on the same class. No new packages, modules,
  or top-level constants beyond two `ENDPOINT_PRIMARY_KEY_STRATEGIES` keys. Filter
  assembly is a single dict comprehension; if it grows past 5 lines during implementation
  it is extracted to a second private helper on the same class.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added as a method on the existing webhook
  export class (`WebhookExportUtils` per research.md; if the codebase organizes webhook
  exports inside `SiteExportUtils` the method is added there instead, per the same
  research note). No standalone wrapper function is introduced. The menu dispatch
  references the class method directly. Variable names use full words
  (`bucket_row`, `summary_row`, `distinct_field`) -- no single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input goes through `safe_input()` with explicit `context=`
  strings (`"site_webhook_count:site_id"`, `"site_webhook_count:webhook_id"`,
  `"site_webhook_count:distinct"`, `"site_webhook_count:filters"`) so SSH / container EOF
  exits cleanly with code 0 and no traceback. The endpoint is strictly read-only (GET),
  so no typed destructive confirmation is required. `site_id` and `webhook_id` are
  validated against the Mist UUID shape via the existing `is_valid_uuid()` helper before
  the API call; on validation failure the method logs a warning and returns early. The
  API token comes from `.env` via the existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `ruff check` -> `black --check`
  -> commit with `version YY.MM.DD.HH.MM - add menu 86 countSiteWebhooksDeliveries`
  -> `git push origin main` -> `.github/workflows/container-build.yml` runs ->
  `gh run watch` -> `podman pull ghcr.io/jmorrison-juniper/misthelper:latest` ->
  stop / remove / re-run container -> `podman ps` verification.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting. `INFO` is
  emitted before each prompt and before the SDK call ("Counting webhook deliveries for
  site %s webhook %s distinct=%s"); `DEBUG` after the call with summary counts
  ("Webhook count: total=%d buckets=%d window=%s..%s"); `WARNING` on 404 or empty
  payload; `ERROR` on 401 / 403; `logging.exception` on unexpected exception. The API
  token, full request URL, and any header containing the token are never logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every executable line in the new method, the new flatten helper,
  the two `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary entries, and the menu registration
  line will carry an inline comment that explains *why* the line exists, not merely what
  it does. Blank lines, closing parentheses, and decorators are exempt per the
  constitution. Any uncommented adjacent lines in the touched menu cluster get comments
  added in the same PR per the "edit-the-block" rule.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each user prompt, before the SDK call, before flatten, and
  before each export; `logging.debug(...)` after each step with a count or short summary.
  The `DataExporter` call already emits its own per-backend log lines; the new method
  does not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/565-mist-count-site-webhooks-deliveries/
| - plan.md              # This file
| - research.md          # Phase 0 - SDK signature, PK strategy, naming, menu placement
| - data-model.md        # Phase 1 - response entities + DDL + PK registration
| - quickstart.md        # Phase 1 - local run + .env + quality gates
| - contracts/
|   \ - count_site_webhooks_deliveries.md   # Phase 1 - HTTP + SDK contract
\ - tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New method on WebhookExportUtils (or SiteExportUtils per
                         # research.md) + flatten helper + two PK strategy entries +
                         # menu 86 registration. No new modules; same single-file
                         # monolith.
README.md                # Operation count bump + new row in the menu table for op 86
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 86 addition
data/                    # Runtime output target (existing dir, no schema migration needed
                         # beyond the two new SQLite tables created on first write by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new public
method on the existing webhook export class. The menu number proposal is **86**, the next
available integer inside the Stats sub-cluster (80-91) of the Interactive Safe range
(60-96). This is the correct semantic placement for a *count* endpoint, sits well below
the resource-intensive block at 97-101, and is far from the destructive block at 154-194.
The full menu list will be re-verified at `/speckit.tasks` time; if 86 collides with an
in-flight feature branch, the next free integer in the same Stats sub-cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/`), the seven principles are re-evaluated against the now-concrete design.

- **Principle I (Five-Item Rule)**: PASS -- The method outline in `quickstart.md`
  confirms <=25 lines, <=5 parameters, <=5 logical blocks. The two
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries are single inserts on an existing dict
  literal, so no level-5 hierarchy explosion.
- **Principle II (Class-Based)**: PASS -- All work lives on the chosen webhook export
  class. No wrapper functions are introduced. The flatten helper is a private method on
  the same class.
- **Principle III (Safety-First)**: PASS -- The contract confirms GET only, no destructive
  side effect. `safe_input()` is the documented prompt path. Both UUIDs are validated
  before the SDK call.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- All log statements in the design use ASCII and
  `%s` formatting; none include the API token or full URL.
- **Principle VI (Inline Comments)**: PASS -- `quickstart.md` shows the expected comment
  density on every executable line, including the PK strategy entries and the menu
  registration line.
- **Principle VII (Action Logging)**: PASS -- `quickstart.md` enumerates the before/after
  log pairs for every meaningful action (prompt, API call, flatten, export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
