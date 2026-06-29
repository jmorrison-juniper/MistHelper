# Implementation Plan: countOrgWebhooksDeliveries Menu Item

**Branch**: `536-mist-count-org-webhooks-deliveries` | **Date**: 2026-06-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/536-mist-count-org-webhooks-deliveries/spec.md`

## Summary

Add a new read-only MistHelper menu item that invokes the Mist API endpoint
`GET /api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/count` (operationId
`countOrgWebhooksDeliveries`) to return the count of webhook delivery events for a single
configured webhook, optionally grouped by a `distinct` field (status, status_code, topic,
error) and optionally filtered by topic / status / status_code / error / time window. The
menu item prompts the user for `org_id` and `webhook_id` via `safe_input()` (falling back
to `MIST_ORG_ID` from `.env` when present), prompts for optional filters with sensible
defaults (`duration=1d`, `limit=100`), invokes the `mistapi` SDK, flattens the count
envelope plus the `results` array into one summary row plus N bucket rows, and persists
the result through `DataExporter.write_with_format_selection()` so CSV, SQLite, and the
ArangoDB+Redis polyglot backend all receive consistent output. A new entry is registered
in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for clean SQLite upserts on repeated runs. The new
operation is proposed as menu number **195** -- the next free integer above the current
production ceiling of 194 documented in `.github/copilot-instructions.md`, placed in the
Safe Org Exports cluster adjacent to other webhook-related operations (existing
`listOrgWebhooks` lives at menu 47).

## Technical Context

**Language/Version**: Python 3.13+ (per constitution Technology & Compatibility
Constraints, enforced by `python_requires` in build metadata and by the container base
image).
**Primary Dependencies**: `mistapi` 0.59+ (Thomas Munzer's Mist API SDK -- the sole
permitted interface to Mist Cloud per the constitution); `requests` (transport,
transitive via mistapi); `python-dotenv` (loads `MIST_HOST`, `MIST_API_TOKEN`, and the
optional `MIST_ORG_ID` from `.env`).
**Storage**: Multi-backend via `DataExporter.write_with_format_selection()`. SQLite file
`data/mist_data.db` is the local fallback; CSV files land in `data/`; the polyglot
ArangoDB + Redis containers receive graph nodes / edges plus cache entries when the
operator selects that backend at startup.
**Testing**: `python MistHelper.py --test` exercises the new menu item in
non-interactive mode using a known org and webhook from `.env`. Local quality gates:
`python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`,
`python -m black --check MistHelper.py`. The heavy / destructive skip list
(14, 18, 63-65, 90-100) is unaffected -- new item 195 sits in the safe-export band and
must run under `--test`.
**Target Platform**: Windows 11 + venv for local dev; Podman Linux container
(`ghcr.io/jmorrison-juniper/misthelper:latest`) for production / SSH-on-2200 / web UI
on 8055; both must work without code change. ASCII-only output is mandatory for the
PowerShell + Linux journald log paths.
**Project Type**: CLI tool (single-file monolith `MistHelper.py`, approximately 28K
lines) with an optional Gunicorn web UI on 8055. This feature lives entirely in the
CLI; no web UI change is in scope.
**Performance Goals**: Single GET request completes in <=5 seconds for typical webhook
configurations (the count endpoint returns a single envelope plus a small `results`
array, capped by the `limit` parameter, default 100). Adaptive delay metrics in
`delay_metrics.json` and `tuning_data.json` continue to govern back-off. This endpoint
is light enough that no special tuning is required and the `--fast` flag will not
exceed Mist's 5000-calls-per-hour ceiling.
**Constraints**: ASCII-only logging; `safe_input()` for every prompt (SSH + container
EOF safety); no API token in logs; all output under `data/`; Windows-safe path joining
(`os.path.join` / `pathlib.Path`); inline comments on every new executable line per
Principle VI; before/after action logging on every meaningful step per Principle VII.
**Scale/Scope**: One new public menu method (target ~22 lines, well under the 25-line
hard cap) on a new dedicated `WebhooksExportUtils` class -- justified below in
Principle II because no existing class owns webhook read operations; one new entry in
`ENDPOINT_PRIMARY_KEY_STRATEGIES`; two new CSV/SQLite tables
(`org_webhook_deliveries_count_summary` and `org_webhook_deliveries_count_buckets`);
one menu registration entry; one README operation-count bump; one CHANGELOG line. No
new dependencies, no new modules, no new directories.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Five-Item Rule (Structural Discipline)

- **STATUS: PASS** -- The new menu method
  `export_count_org_webhooks_deliveries()` stays under 25 lines, takes <=5 parameters
  (`self`, `org_id`, `webhook_id`, `filters`, `time_window`) where `filters` is a single
  dataclass that packs the four optional query knobs (`status`, `status_code`, `topic`,
  `error`, `distinct`) so the parameter count remains within the cap, and `time_window`
  is a single dataclass that packs `start`/`end`/`duration`/`limit`. The method body
  contains exactly 5 logical blocks: prompt -> build filter object -> API call ->
  flatten (summary + buckets) -> DataExporter call. Hierarchy is unchanged: one new
  module-level class with one public method plus two private flatteners. No new
  packages, modules, or top-level constants are introduced.

### Principle II: Class-Based Architecture (No Wrappers)

- **STATUS: PASS** -- The new behavior is added on a new
  `WebhooksExportUtils` class in `MistHelper.py`. This is not a wrapper function; it is
  a class with state (the mistapi session, the active output backend) and methods. A
  new class is justified because no existing class in MistHelper currently owns webhook
  read operations -- `listOrgWebhooks` (menu 47) is registered against the generic
  org-config export class, but adding webhook deliveries / events / count operations to
  that class would push it past the 5-method ceiling and violate Principle I. Variable
  names use full words (`delivery_bucket`, `count_summary_row`, `bucket_count`) -- no
  single-letter iterators.

### Principle III: Safety-First (NON-NEGOTIABLE)

- **STATUS: PASS** -- All user input is collected through `safe_input()` with explicit
  `context=` strings (`"count_webhook_deliveries:org_id"`,
  `"count_webhook_deliveries:webhook_id"`,
  `"count_webhook_deliveries:topic"`, etc.) so SSH and container EOF exits cleanly with
  code 0 and no traceback. The endpoint is strictly read-only (HTTP GET), so no typed
  destructive-confirmation gate is required. Both `org_id` and `webhook_id` are
  validated against the Mist UUID shape before the API call; on validation failure the
  method logs a warning and returns early. The API token comes from `.env` via the
  existing `mistapi.APISession` and is never logged.

### Principle IV: Full Deployment Pipeline (NON-NEGOTIABLE)

- **STATUS: PASS** -- After implementation the standard pipeline applies without
  modification: `python -m py_compile MistHelper.py` -> `python -m ruff check
  MistHelper.py` -> `python -m black --check MistHelper.py` -> commit with `version
  YY.MM.DD.HH.MM - add menu 195 countOrgWebhooksDeliveries` -> `git push origin main`
  -> `.github/workflows/container-build.yml` runs -> `gh run watch` -> `podman pull
  ghcr.io/jmorrison-juniper/misthelper:latest` -> `podman stop misthelper && podman rm
  misthelper && podman run ...` -> `podman ps` verification. No corporate-proxy
  workaround is required because the workflow runs on GitHub infrastructure.

### Principle V: Observability & Logging

- **STATUS: PASS** -- All log calls use ASCII text and `%s` style formatting.
  `logging.info(...)` is emitted before the API call ("Counting webhook deliveries for
  org %s webhook %s"); `logging.debug(...)` after the call with summary counts ("Count
  result: distinct=%s total=%d buckets=%d"); `logging.warning(...)` on 404 / empty
  payload; `logging.error(...)` (via `logging.exception`) on unexpected exception with
  full traceback. No secrets, tokens, or full request URLs containing query strings are
  logged.

### Principle VI: Inline Comments (NON-NEGOTIABLE)

- **STATUS: PASS** -- Every new executable line in the new method, the new dataclass
  definitions, the new `WebhooksExportUtils` class, the new
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` entry, and the menu registration line will carry an
  inline comment that explains *why* the line exists, not merely what it does. Blank
  lines, decorators, and closing parentheses are exempt per the constitution. Any
  uncommented adjacent lines in the touched menu-registration block get comments added
  in the same PR.

### Principle VII: Action Logging (NON-NEGOTIABLE)

- **STATUS: PASS** -- The new method follows the documented before/after pattern:
  `logging.info(...)` before each prompt sequence, `logging.debug(...)` after with the
  collected value (org/webhook only -- no secrets); `logging.info(...)` before the SDK
  call, the call itself, `logging.debug(...)` after with `total` and `len(results)`;
  `logging.info(...)` before flatten, `logging.debug(...)` after flatten with row
  counts; `logging.info(...)` before write, `logging.debug(...)` after write. The
  DataExporter call already emits its own per-backend log lines; the new method does
  not duplicate them.

### Pre-Phase 0 Gate: PASS

All seven principles pass without exception. No entries are required in the Complexity
Tracking table at this stage.

## Project Structure

### Documentation (this feature)

```text
specs/536-mist-count-org-webhooks-deliveries/
|-- plan.md              # This file
|-- research.md          # Phase 0 -- SDK signature, PK strategy, naming, menu placement
|-- data-model.md        # Phase 1 -- response entities + DDL + PK registration
|-- quickstart.md        # Phase 1 -- local run + .env + quality gates
|-- contracts/
|   `-- count_org_webhooks_deliveries.md   # Phase 1 -- HTTP + SDK contract
`-- tasks.md             # Phase 2 (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
MistHelper.py            # New WebhooksExportUtils class with the new method, the new
                         # PK strategy entry, and the new menu 195 registration. No new
                         # modules; same single-file monolith.
README.md                # Operation count bump + new row in the menu table for op 195
CHANGELOG.md             # New "version YY.MM.DD.HH.MM" entry summarizing menu 195
data/                    # Runtime output target (existing dir, no schema migration
                         # beyond the new SQLite tables created on first run by
                         # DataExporter)
```

**Structure Decision**: Single-file monolith. The new menu item is added as a new
public method on a new `WebhooksExportUtils` class in `MistHelper.py`. A new class is
preferred over loading more methods into an existing org-config export class because:
(a) no existing class currently owns webhook delivery / event read operations;
(b) the Webhooks tag has at least three sibling read endpoints in the Mist API
(`listOrgWebhooks` already present at menu 47, `searchOrgWebhooksDeliveries`,
`countOrgWebhooksDeliveries`) so a dedicated class will pay back across future cataloging
specs in this same effort; and (c) Principle I caps any single class at five methods,
which is comfortably consistent with the expected webhook-cluster size. The menu
number proposal is **195**, the next free integer above the documented production
ceiling of 194 (`.github/copilot-instructions.md` "Menu Categories (Full Range:
1-194)"). If 195 collides with a parallel in-flight cataloging spec at task generation
time, the next free integer in the same Safe Org Exports cluster is used.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution exceptions required at the Pre-Phase 0 gate. Table intentionally empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| _(none)_  | _(n/a)_    | _(n/a)_                              |

## Post-Phase 1 Re-Check

After completing Phase 0 (`research.md`) and Phase 1 (`data-model.md`, `quickstart.md`,
`contracts/count_org_webhooks_deliveries.md`), the seven principles are re-evaluated
against the now-concrete design:

- **Principle I (Five-Item Rule)**: PASS -- The detailed method outline in
  `quickstart.md` confirms <=25 lines, <=5 parameters (via two dataclass aggregates),
  and exactly 5 logical blocks. The `ENDPOINT_PRIMARY_KEY_STRATEGIES` dictionary
  insertion is a single literal entry, so no level-5 hierarchy explosion. The
  `WebhooksExportUtils` class begins life with three members (one public method, two
  private flatteners), leaving headroom under the 5-method ceiling.
- **Principle II (Class-Based)**: PASS -- All work lives on `WebhooksExportUtils`. No
  wrappers introduced. Flattening helpers are private methods on the same class.
- **Principle III (Safety-First)**: PASS -- The Phase 1 contract confirms the endpoint
  is GET only, with no destructive side effect. `safe_input()` is the documented
  prompt path. UUID validation happens before the SDK call for both `org_id` and
  `webhook_id`.
- **Principle IV (Pipeline)**: PASS -- No deviation from the standard pipeline.
- **Principle V (Observability)**: PASS -- Log statements in the design are ASCII-only
  with `%s` formatting and never include the API token or full query strings.
- **Principle VI (Inline Comments)**: PASS -- The Phase 1 quickstart shows the expected
  comment density on every executable line, including the PK strategy entry, dataclass
  definitions, and menu registration line.
- **Principle VII (Action Logging)**: PASS -- The Phase 1 quickstart enumerates the
  before/after log pairs for every meaningful action (prompt, API call, flatten,
  export).

### Post-Phase 1 Gate: PASS

All seven principles continue to pass after design. The plan is ready for
`/speckit.tasks` to produce a task breakdown.
