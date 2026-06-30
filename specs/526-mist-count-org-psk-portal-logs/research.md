# Phase 0 Research: countOrgPskPortalLogs

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-28

This document resolves the unknowns required before design and implementation.
Each task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_pskportals_logs_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical URL-derived module
path: `mistapi.api.v1.orgs.pskportals.logs.count.countOrgPskPortalLogs(
apisession, org_id, distinct=None, start=None, end=None, duration="1d",
limit=100)`. The SDK returns a `mistapi.APIResponse` whose `.data` attribute is
the parsed JSON body. The body is a single JSON object with these top-level
keys per the enriched doc:

- `distinct` (string -- echoes the attribute the caller grouped by)
- `start` (int epoch seconds -- echoes the resolved start of the window)
- `end` (int epoch seconds -- echoes the resolved end of the window)
- `limit` (int -- echoes the cap applied to the `results[]` array)
- `total` (int -- total log events matched in the window)
- `results` (array of objects, each shaped `{count: int, <distinct_attr>: str}`,
  where `<distinct_attr>` is the field the caller chose to group by; the doc
  schema marks the per-row object as `additionalProperties: {type: string}`)

Required path parameter: `org_id` (UUID string).
Optional query parameters: `distinct`, `start`, `end`, `duration` (default
`"1d"`), `limit` (default `100`).

**Rationale**:
The enriched per-endpoint doc lists the SDK as
`mistapi.api.v1.orgs.psk_portals.countOrgPskPortalLogs()` (with underscores in
`psk_portals`), but the OpenAPI URL is `/api/v1/orgs/{org_id}/pskportals/logs/count`
(no underscore). Looking at adjacent count endpoints in mistapi (for example
`mistapi.api.v1.orgs.devices.events.count.countOrgDeviceEvents` mirrors
`/orgs/{org_id}/devices/events/count`) the SDK consistently mirrors the URL path
exactly, including the lack of underscore in compound tokens. The spec.md
(authoritative feature contract) names `mistapi.api.v1.orgs.pskportals.logs.count`
and that path matches the URL one-for-one, so the plan follows the spec. Final
verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs.pskportals.logs import count; help(count)"`
inside the venv. If the import fails, the import path is corrected to whatever
the installed mistapi 0.59+ actually exposes (the operationId
`countOrgPskPortalLogs` is the authoritative anchor; the dotted Python path is
not).

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{host}/api/v1/orgs/{org_id}/pskportals/logs/count`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the dotted path with underscore `...orgs.psk_portals.logs.count` from
   the per-endpoint doc.* Rejected as primary -- but used as the verified
   fallback at implementation time if the no-underscore path is not exposed.
   The operationId remains stable in either case.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on the output table
`org_psk_portal_log_counts`:

- PK = `(org_id, distinct, start, end, distinct_value)` -- one row per
  bucket in the response `results[]` array.

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk`.
`org_id` is injected by MistHelper before the upsert (the API does not echo
`org_id` in the body, but MistHelper always knows which org the call targeted).
`distinct`, `start`, `end` are echoed by the API in the response object;
`distinct_value` is the value of the dynamic per-row attribute selected by the
`distinct` query parameter (for example when `distinct=admin_id`, each row has
an `admin_id` field whose value becomes `distinct_value`).

**Rationale**:
A count-by-distinct response is a snapshot aggregate: re-running the menu item
over the same `(org, distinct, window)` tuple should *replace* the prior
snapshot rather than append duplicate buckets. The tuple
`(org_id, distinct, start, end, distinct_value)` is the natural key because two
otherwise-identical buckets cannot coexist within one (org, attribute, window)
snapshot. `INSERT OR REPLACE` upserts each bucket cleanly on every re-run.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls
   accumulate duplicate snapshots, defeating the upsert behavior implied by
   FR-003 / FR-005 of the spec.
2. *`natural_pk` on `distinct_value` alone.* Rejected -- `distinct_value`
   collides across (a) different distinct attributes within the same org and
   (b) different windows of the same attribute. The PK must include the full
   window and the chosen attribute.
3. *Two-table design (one summary row per window + one detail row per bucket).*
   Rejected -- the API response is already flat (one window header + one
   `results[]` array). Splitting into two tables adds join cost without any
   queryability gain; all summary fields fit naturally on every bucket row
   (denormalized echo of `total`, `limit`, `distinct`, `start`, `end`).

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV: `data/org_<org_id_short>_psk_portal_log_counts_<distinct>_<start>_<end>.csv`
- SQLite table: `org_psk_portal_log_counts`
- `org_id_short` is the first 8 hex characters of the org UUID -- the existing
  convention for human-readable filenames without leaking the full UUID into
  shell history.
- `<distinct>` is the resolved distinct attribute (for example `admin_id`).
- `<start>` and `<end>` are the resolved epoch-second window bounds the API
  echoed in the response, ensuring the filename is unique per snapshot.

The `api_function_name` argument passed to
`DataExporter.write_with_format_selection()` is `"countOrgPskPortalLogs"`
(matching the operationId). The DataExporter uses that string as the lookup
key into `ENDPOINT_PRIMARY_KEY_STRATEGIES`.

**Rationale**:
The filename pattern follows the convention used by adjacent count endpoints
(for example `countOrgDeviceEvents` in MistHelper, when present). Embedding
the distinct attribute and the window in the filename means a single run
directory holds intelligible snapshots side by side without overwriting prior
exports of a different attribute or window. The SQLite table name omits those
variables because the composite PK already discriminates rows within a single
table.

**Alternatives Considered**:

1. *One file per distinct value (one CSV row each).* Rejected -- absurd file
   count, kills CSV utility.
2. *Single file `data/psk_portal_log_counts.csv` with no per-call suffix.*
   Rejected -- repeated calls with different attributes or windows would
   visually collide in `data/` even though the SQLite upsert is clean.
3. *Full org UUID in the filename.* Rejected -- leaks the org UUID into shell
   history. The 8-char short form is enough to disambiguate locally.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Register the new operation as menu number **89**, inside the Interactive Safe
cluster (60-96) under the category label
"Interactive Safe -- PSK Portal Analytics".

**Rationale**:
The `.github/copilot-instructions.md` menu range table places:
1-59 Safe Org Exports, 60-96 Interactive Safe, 97-101 + 153 Resource Intensive,
102-123 WebSocket, 124-152 Interactive, 154-194 Destructive. This endpoint
requires the user to choose a distinct attribute and a time window
interactively, which puts it firmly in 60-96. PSK portal management items
already cluster around the upper end of that band; 89 sits in a free slot far
enough below the resource-intensive boundary at 96 to leave headroom for the
expected follow-on `searchOrgPskPortalLogs` sibling. The number is provisional
-- at `/speckit.tasks` time, `MistHelper.py` is grep'd for the highest currently
allocated menu integer and 89 is shifted forward if a conflict exists.

**Alternatives Considered**:

1. *Put it in 1-59 Safe Org Exports.* Rejected -- the four interactive prompts
   (org_id, distinct, duration, limit) make this an Interactive Safe item by
   the documented criterion, not a Safe Org Export.
2. *Put it in 97-101 Resource Intensive.* Rejected -- the endpoint is a single
   GET that returns a small aggregate object; the default `limit=100` caps
   the response size cheaply.
3. *Slot inside the Destructive band (154-194).* Rejected -- the endpoint is
   read-only; placing it near destructive items mis-signals risk to a junior
   NOC engineer.

## Research Task 5: Required user prompts

**Decision**:
The new menu method asks the user for **exactly four** values via
`safe_input()`. Each prompt accepts a sane default so non-interactive
(`--menu 89`) runs work without further input.

1. `org_id` -- prompt: `"Org ID (UUID): "`, context:
   `"psk_portal_log_counts:org_id"`. Default: the value of `MIST_ORG_ID` in
   `.env` if present. Validated via the existing `is_valid_uuid()` helper
   before the API call; on failure, log `WARNING` and return early.
2. `distinct` -- prompt:
   `"Group by attribute (admin_id|psk_id|ssid|status) [admin_id]: "`,
   context: `"psk_portal_log_counts:distinct"`. Default: `admin_id`. Passed
   verbatim to the API as the `distinct` query parameter. The API tolerates
   any string; MistHelper does not pre-validate against an allow-list
   because the supported attribute set is owned by the Mist API and can
   expand independently.
3. `duration` -- prompt:
   `"Window duration (e.g. 1d, 7d, 2w) [1d]: "`, context:
   `"psk_portal_log_counts:duration"`. Default: `1d`. Sent only when the
   user does not separately provide `start`/`end` (Mist's contract: when
   `duration` is supplied alongside `end`, the server computes
   `start = end - duration`).
4. `limit` -- prompt: `"Max buckets in response (1-1000) [100]: "`, context:
   `"psk_portal_log_counts:limit"`. Default: `100`. Coerced to `int`; on
   `ValueError` the default is used and a `WARNING` is logged. Values
   greater than `1000` are clamped to `1000` to match the documented Mist
   cap.

`.env` values (loaded via the existing `python-dotenv` bootstrap, never
logged):

- `MIST_HOST` (e.g., `api.mist.com`) -- required by `mistapi.APISession`.
- `MIST_API_TOKEN` -- required by `mistapi.APISession`.
- `MIST_ORG_ID` -- optional default for prompt 1.

`start` and `end` are intentionally **not** prompted in the default flow.
Most operators want a rolling window (the `duration` knob handles that), and
adding two more prompts for raw epoch seconds clutters the menu without
operational value. Power users can override by editing the call at task
time -- the SDK signature exposes both parameters.

**Rationale**:
Four prompts is the minimum required to expose the endpoint's expressive
power (distinct grouping over a configurable window with a bucket cap)
without forcing the operator to hand-craft epoch timestamps. The defaults
align with the Mist API's own defaults (`duration=1d`, `limit=100`) so a
non-interactive `--menu 89` invocation reproduces the simplest reasonable
question: "give me the top 100 buckets of PSK portal log activity over the
last 24 hours, grouped by admin."

**Alternatives Considered**:

1. *Single prompt for the distinct attribute, use API defaults for everything
   else.* Rejected -- forecloses time-window analysis, which is the primary
   diagnostic value of a "count by distinct over a window" endpoint.
2. *Six prompts including `start` and `end` epoch seconds.* Rejected -- adds
   keystrokes without value for the common case. `duration` covers 95
   percent of operator intent.
3. *Free-form distinct prompt with no default or example list.* Rejected --
   junior NOC engineers (the target audience) benefit from a short example
   list (`admin_id|psk_id|ssid|status`) in the prompt text without that list
   being enforced as an allow-list.
