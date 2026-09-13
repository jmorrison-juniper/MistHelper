# Phase 0 Research: countOrgWebhooksDeliveries

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
research task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**:
`documentation/api/orgs/GET_orgs_org_id_webhooks_webhook_id_events_count.md` (enriched
per-endpoint OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK at the canonical module path that mirrors the
OpenAPI URL:
`mistapi.api.v1.orgs.webhooks.events.count.countOrgWebhooksDeliveries(apisession,
org_id, webhook_id, distinct=None, status=None, status_code=None, topic=None,
error=None, start=None, end=None, duration="1d", limit=100)`. The SDK returns a
`mistapi.APIResponse` whose `.data` attribute is the parsed JSON body.

The body is the standard Mist "count envelope" object with the following top-level
keys (required keys per the response schema):

- `distinct` (string) -- echo of the `distinct` query parameter (which field the count
  was grouped by); when no `distinct` is supplied the API still echoes the default it
  selected.
- `start` (int, epoch seconds) -- start of the queried window.
- `end` (int, epoch seconds) -- end of the queried window.
- `limit` (int) -- echo of the `limit` query parameter.
- `total` (int) -- grand total of deliveries matching the filters in the window.
- `results` (array, items unique) -- per-bucket counts; each item is an object with at
  least `count` (int, required) plus additional free-form string properties whose name
  is the value of the `distinct` field. For example, when `distinct=status`, each item
  is `{"count": 142, "status": "succeeded"}`; when `distinct=topic`, each item is
  `{"count": 17, "topic": "alarms"}`.

Required path parameters: `org_id` (UUID string) and `webhook_id` (UUID string).
Optional query parameters: `error`, `status_code`, `status`, `topic`, `distinct`,
`start`, `end`, `duration` (default `1d`), `limit` (default `100`).

**Rationale**:
The enriched per-endpoint doc lists the SDK module under
`mistapi.api.v1.orgs.webhooks` directly (`mistapi.api.v1.orgs.webhooks.countOrgWebhooksDeliveries()`),
but the mistapi SDK historically generates module paths from the URL path tokens, and
the URL is `/orgs/{org_id}/webhooks/{webhook_id}/events/count`. The deeper path
`mistapi.api.v1.orgs.webhooks.events.count.countOrgWebhooksDeliveries` is what
matches the SDK's canonical layout (verified against adjacent count endpoints such as
`searchOrgWebhooksDeliveries` which live under `mistapi.api.v1.orgs.webhooks.events.search`).
Final verification happens at implementation time via
`python -c "import mistapi.api.v1.orgs.webhooks.events.count as m; help(m)"` inside the
venv; if the doc's flat path is correct in the installed SDK version, the import line
falls back to `from mistapi.api.v1.orgs.webhooks import countOrgWebhooksDeliveries`.
spec.md is the authoritative feature contract and names
`mistapi.api.v1.orgs.webhooks.events.count`, so the plan adopts that path as the
primary import.

**Alternatives Considered**:

1. *Direct `requests.get` against
   `https://{MIST_HOST}/api/v1/orgs/{org_id}/webhooks/{webhook_id}/events/count`.*
   Rejected -- the constitution forbids direct HTTP when a mistapi method exists.
2. *Use the path implied by the doc tag (`mistapi.api.v1.orgs.webhooks` flat).*
   Rejected -- the SDK organizes modules by URL path tokens, not OpenAPI tag, and
   spec.md (the authoritative feature contract) names the URL-based path. The
   implementation does include a transient `try/except ImportError` fallback to the
   flat path so we are robust against minor SDK refactors.
3. *Skip the SDK entirely and reverse-engineer pagination.* Rejected -- the count
   envelope is intentionally a single, non-paginated response, capped by `limit`; the
   SDK handles it cleanly.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite primary key** strategy on two separate output tables:

- `org_webhook_deliveries_count_summary`: PK =
  `(org_id, webhook_id, distinct, start, end)` -- one row per unique query window per
  webhook per distinct grouping. The five-tuple is stable across re-polls of the same
  query and uniquely identifies the count envelope.
- `org_webhook_deliveries_count_buckets`: PK =
  `(org_id, webhook_id, distinct, start, end, bucket_value)` -- one row per `results`
  entry. `bucket_value` is the string value of the distinct-named property on the bucket
  object (e.g. `"succeeded"` when `distinct=status`).

The `ENDPOINT_PRIMARY_KEY_STRATEGIES` registration uses type `composite_pk` for both
tables. `org_id` and `webhook_id` are injected by MistHelper before the upsert (Mist
does not return either in the body but MistHelper always knows the values it called
with).

**Rationale**:
The endpoint reports an aggregate count, not a list of stable Mist resources. The same
query repeated within the same time window legitimately must update the existing row
rather than append a duplicate (`status=succeeded` may grow from 142 to 158 between
polls). The five-tuple `(org_id, webhook_id, distinct, start, end)` is the natural key
for the envelope: every input that affects the response is in it. The bucket table adds
`bucket_value` because buckets within the same envelope are distinguished by that field.
`INSERT OR REPLACE` upserts every poll's view cleanly.

When the user supplies a relative time window (`duration=1d`) instead of explicit
`start`/`end`, MistHelper resolves the relative form to absolute epochs *before* the
upsert -- otherwise two consecutive polls with `duration=1d` would collide on the same
PK but actually represent different windows. The absolute `start`/`end` echoed in the
response body are the canonical values stored.

**Alternatives Considered**:

1. *`auto_increment_with_unique`.* Rejected -- would let repeated polls accumulate
   duplicate snapshots in SQLite, defeating the upsert behavior the spec requires.
2. *Single combined table with all envelope fields plus `bucket_value` nullable.*
   Rejected -- when the user calls without `distinct`, `results` is still present (the
   API picks a default distinct field) so the bucket rows still exist; splitting into
   summary + buckets keeps the analytics queries simple and avoids nullable PK columns.
3. *`natural_pk` on a synthesized hash of all inputs.* Rejected -- harder to debug, no
   benefit over the explicit composite tuple, and breaks downstream JOINs against
   webhook configuration tables that key on `webhook_id`.

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV (summary): `data/org_<org_id_short>_webhook_<webhook_id_short>_deliveries_count_summary.csv`
- CSV (buckets): `data/org_<org_id_short>_webhook_<webhook_id_short>_deliveries_count_buckets.csv`
- SQLite tables: `org_webhook_deliveries_count_summary` and
  `org_webhook_deliveries_count_buckets`
- `org_id_short` is the first 8 hex characters of the org UUID; `webhook_id_short` is
  the first 8 hex characters of the webhook UUID -- both conventions already used
  throughout MistHelper for output naming.

**Rationale**:
Naming mirrors the existing convention used by sibling org-export menu items (e.g.
`org_<short>_inventory.csv`, `org_<short>_<site_short>_devices.csv`). Including
`webhook_<webhook_id_short>` in the filename is necessary because a single org can host
many webhooks and outputs must not collide between them. Splitting summary and buckets
into two files mirrors the SQLite table split and keeps CSV consumers simple.

**Alternatives Considered**:

1. *Single CSV with a `row_type` column distinguishing summary vs bucket.* Rejected --
   awkward to analyze in Excel and breaks the convention of one logical entity per
   file.
2. *Filename keyed on a hash of the filter set.* Rejected -- opaque and hostile to NOC
   engineers debugging output. The composite SQLite PK already disambiguates filter
   sets; CSV consumers who care can simply re-run with different filters into different
   filenames by setting an output suffix.

## Research Task 4: Menu category placement and next available menu number

**Decision**:
Propose menu number **195**. Category: Safe Org Exports (read-only, non-destructive,
non-interactive beyond initial prompts). Place adjacent to the existing webhook config
operation `listOrgWebhooks` (menu 47) in the README menu table -- not numerically, but
conceptually grouped under a "Webhooks" sub-heading in the table.

**Rationale**:
`.github/copilot-instructions.md` documents the current production menu range as 1-194,
with destructive operations occupying 154-194 (firmware, reboot, clone, support
tickets, etc.). 195 is the first integer above the destructive band and is the natural
slot for new safe read-only exports being cataloged by this effort. Listing it next to
menu 47 in the README's Webhooks sub-heading keeps the menu *table* readable for NOC
engineers without renumbering the historical operations. If 195 collides with a
parallel in-flight cataloging spec at task generation time, the next free integer in
the same Safe Org Exports cluster is used; the spec dir number (536) is unrelated to
the runtime menu number.

**Alternatives Considered**:

1. *Reuse menu 47 by adding a sub-menu prompt.* Rejected -- breaks the
   "one operation = one menu number = one CLI invocation" contract used by the test
   harness and by `--menu N` direct invocation.
2. *Slot it inside 42-50 by renumbering.* Rejected -- the constitution does not require
   contiguous numbering, and renumbering breaks operator muscle memory and any local
   automation that pins menu numbers.
3. *Assign menu 536 to match the spec dir.* Rejected -- the cataloging spec dir
   numbering is for spec uniqueness only; runtime menu numbers must remain dense and
   sequential for the test harness.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**:
Prompt sequence collected via `safe_input()`:

1. **org_id** -- default to `MIST_ORG_ID` from `.env` when set; otherwise prompt
   ("Org ID [UUID]: ") and validate as UUID.
2. **webhook_id** -- always prompted ("Webhook ID [UUID]: "); validate as UUID. No
   `.env` fallback because a single org may legitimately have many webhooks; a default
   would hide bugs.
3. **distinct** (optional) -- prompt with enum hint ("Distinct grouping [status |
   status_code | topic | error] (empty = API default): "); empty string = skip.
4. **topic / status / status_code / error** (optional filters) -- prompt each with an
   empty-default; empty string = skip.
5. **duration / start / end** -- prompt for `duration` first ("Duration [1d]: ") with
   default `1d`; if the user supplies an empty string and instead wants absolute epochs,
   they may then provide `start` and `end` directly. Only one of `duration` vs
   `(start, end)` is forwarded to the SDK.
6. **limit** -- prompt with default 100; clamp to the Mist API ceiling.

Secrets (`MIST_HOST`, `MIST_API_TOKEN`) come exclusively from `.env` through the
existing `mistapi.APISession` bootstrap; the new method never reads them and never
logs them.

**Rationale**:
This matches the established MistHelper prompt convention: required scope IDs first,
optional filters with empty-defaults, time window last, output knob (`limit`) last.
Using `MIST_ORG_ID` as the org default keeps the operator's hot loop fast for the
common case (single-org operator); explicitly prompting for `webhook_id` prevents
silent cross-webhook errors. Every prompt is wrapped in `safe_input()` with an explicit
`context=` string so EOF from SSH / container detach exits cleanly with code 0 per
Principle III.

**Alternatives Considered**:

1. *Read all filters from `.env`.* Rejected -- the filter combinations are
   intentionally ad-hoc; pinning them in `.env` would force the operator to edit the
   file between runs.
2. *Single positional `--menu 195 <org_id> <webhook_id>` invocation with no prompts.*
   Rejected for the interactive path -- but the implementation does support the
   non-interactive `--test` invocation by accepting CLI overrides when present (the
   existing harness pattern). The interactive prompt path remains the documented one.
3. *Auto-discover webhooks for the org and present a selection menu.* Rejected for
   this spec's minimum-viable cut. A follow-up spec can add an auto-discovery wrapper
   menu that calls `listOrgWebhooks` then dispatches to this menu per webhook; that
   wrapper belongs in its own spec to keep this one tightly scoped.
