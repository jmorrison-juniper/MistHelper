# Phase 0 Research: countOrgJsiPbn

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-06-29

This document resolves the unknowns required before design and implementation. Each
task follows the Decision / Rationale / Alternatives Considered format.

## Research Task 1: SDK function signature and behavior

**Source consulted**: `documentation/api/orgs/GET_orgs_org_id_jsi_pbn_count.md`
(enriched OpenAPI doc).

**Decision**:
Invoke the endpoint via the mistapi SDK as
`mistapi.api.v1.orgs.jsi.countOrgJsiPbn(apisession, org_id, distinct, limit=100,
start=None, end=None)`. The SDK returns a `mistapi.APIResponse` object whose
`.data` attribute is the parsed JSON body. The body is a single JSON object
shaped as a count envelope with these top-level keys:

- `distinct` (string -- echoes the request grouping field).
- `start` (int -- epoch seconds, window start used by the server).
- `end` (int -- epoch seconds, window end used by the server).
- `limit` (int -- maximum result rows the server honored).
- `total` (int -- total advisories matching the filter across all groups).
- `results` (array of objects, `uniqueItems: true`). Each element has a required
  `count` integer plus arbitrary additional string properties whose name is the
  grouping field (e.g. `{"count": 12, "versions": "23.4R1"}` when
  `distinct=versions`).

Required path parameter: `org_id` (UUID string).
Required query parameter: `distinct` (enum:
`versions | models | customer_risk | bug_type`).
Optional query parameters: `limit` (int, default 100), `start` / `end`
(epoch seconds or relative strings such as `-1d`, `-1w`, `now`).

**Rationale**:
The enriched per-endpoint doc lists the SDK module as
`mistapi.api.v1.orgs.jsi.countOrgJsiPbn()` -- shorter than the URL path
(`/api/v1/orgs/{org_id}/jsi/pbn/count`) because the mistapi SDK groups several
PBN-related endpoints under a single `jsi` submodule rather than mirroring every
URL token. The spec.md notes the canonical path
`mistapi.api.v1.orgs.jsi.pbn.count` but the SDK doc is authoritative for the
actual import location; final verification happens at implementation time via
`python -c "from mistapi.api.v1.orgs.jsi import countOrgJsiPbn; help(countOrgJsiPbn)"`
inside the venv. The doc-stated path is what the implementation will call.

**Alternatives Considered**:

1. *Direct `requests.get` against the URL.* Rejected -- the constitution forbids
   direct HTTP when a mistapi method exists.
2. *Probe both candidate module paths
   (`mistapi.api.v1.orgs.jsi.pbn.count.countOrgJsiPbn` vs
   `mistapi.api.v1.orgs.jsi.countOrgJsiPbn`) at runtime with `try/except
   ImportError`.* Rejected -- adds complexity for a single-line import; the doc
   path is canonical and a single `help()` probe at implementation time settles
   it.

## Research Task 2: Primary Key Strategy

**Decision**:
Use a **composite_pk** strategy on a single output table `org_jsi_pbn_count`.
Composite key columns:
`(org_id, distinct_field, group_value, window_start, window_end)`.

- `org_id` -- caller-supplied UUID, injected by MistHelper.
- `distinct_field` -- the value of the `distinct` query parameter (e.g.
  `versions`).
- `group_value` -- the per-row grouping value pulled from the additional property
  whose key equals `distinct_field` (e.g. the actual version string).
- `window_start` / `window_end` -- the echoed `start` / `end` integers from the
  response so re-runs against the same window upsert cleanly, but a different
  time window produces a fresh history row.

**Rationale**:
The endpoint returns an aggregate count, not a stable entity with a server-issued
UUID, so `natural_pk` is wrong. The endpoint is also not pure time-series in the
event sense (no per-event row), so a pure `composite_pk` keyed on a free-floating
`timestamp` would over-write history. The chosen 5-column composite preserves
history across distinct time windows while still upserting when the same window
is re-queried -- the documented behavior pattern for count / aggregate endpoints
elsewhere in MistHelper (see `ENDPOINT_PRIMARY_KEY_STRATEGIES` entries for the
adjacent `count*` operations).

**Alternatives Considered**:

1. *`auto_increment_with_unique` keyed on `misthelper_internal_id`.* Rejected --
   would let duplicates accumulate on every re-poll of the same window.
2. *`natural_pk` on `(org_id, distinct_field, group_value)` only.* Rejected --
   different time windows would over-write each other, losing trend history.
3. *Two-table split (envelope + results).* Rejected -- the envelope is tiny (six
   scalars) and worth denormalizing onto each result row for query simplicity.

## Research Task 3: Output filename and SQLite table

**Decision**:
- CSV file: `data/org_jsi_pbn_count.csv`
- SQLite table: `org_jsi_pbn_count`
- ArangoDB collection: `org_jsi_pbn_count`
- `api_function_name` keyword passed to
  `DataExporter.write_with_format_selection(..., api_function_name="countOrgJsiPbn")`
  so the multi-backend dispatcher picks up the registered PK strategy.

**Rationale**:
Matches the existing snake_case naming convention for count/aggregate endpoints
under `data/` (e.g. analogous `org_*_count.csv` files). The operationId
`countOrgJsiPbn` is preserved verbatim as the `api_function_name` so
`ENDPOINT_PRIMARY_KEY_STRATEGIES` lookups succeed.

**Alternatives Considered**:

1. *Append the `distinct` value to the filename (e.g.
   `org_jsi_pbn_count_versions.csv`).* Rejected -- the `distinct_field` column is
   inside the row, so a single file with mixed groupings stays consistent with
   how other multi-grouping count endpoints are stored.
2. *Per-window filename suffix.* Rejected -- the window is captured in the row,
   filename churn would break tooling that watches a stable path.

## Research Task 4: Menu category placement and next available menu number

**Decision**: **Menu number 78** in the *Safe Org Exports / Insights* cluster
(73-79 per `.github/copilot-instructions.md` menu category table).

**Rationale**:
The endpoint is read-only, org-scoped, and returns an insight count -- so it
belongs alongside the existing insight / SLE / JSI operations in the 73-79 band,
not in the 80-91 statistics block or the 97-101 resource-intensive block. Number
78 is the next available integer in that band based on the menu category table.
If a parallel feature branch claims 78 first, fall back to the next free integer
(79, then 80) at task generation time.

**Alternatives Considered**:

1. *Place in the 80-91 statistics block.* Rejected -- the band is reserved for
   `*_stats` endpoints, not count aggregates.
2. *Place in the 73 / 74 insights slot.* Rejected -- those slots are already in
   use; we pick the next free integer rather than re-shuffle existing operations.

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**: Three required prompts and three optional prompts.

| Prompt | Source                                         | Required | safe_input context           |
|--------|------------------------------------------------|----------|------------------------------|
| Mist host       | `.env` (`MIST_HOST`)                  | --       | (no prompt)                  |
| API token       | `.env` (`MIST_API_TOKEN`)             | --       | (no prompt)                  |
| `org_id`        | user prompt; default to `.env` `MIST_ORG_ID` if present | Yes | `org_jsi_pbn_count:org_id` |
| `distinct`      | user prompt (enum choice menu)        | Yes      | `org_jsi_pbn_count:distinct` |
| `limit`         | user prompt; default `100`            | No       | `org_jsi_pbn_count:limit`    |
| `start` (epoch) | user prompt; default empty (server picks default window) | No | `org_jsi_pbn_count:start` |
| `end` (epoch)   | user prompt; default empty (server picks default window) | No | `org_jsi_pbn_count:end`   |

**Rationale**:
The `org_id` is the only mandatory identifier the user has to know; pre-loading
from `.env` (when MistHelper is configured for a single primary org) saves a
prompt. The `distinct` enum is short (four values) so we present a numbered choice
menu rather than free-form text, validated against the documented enum before the
API call. Time window is optional and accepts both epoch seconds and relative
strings (`-1d`, `-1w`, `now`) -- pass-through to mistapi, which accepts both.

**Alternatives Considered**:

1. *Auto-pick `distinct=versions` without prompting.* Rejected -- the choice of
   grouping is the entire point of the endpoint; defaulting hides functionality.
2. *Accept site_id instead of org_id.* Rejected -- the endpoint is org-scoped per
   the OpenAPI path.
