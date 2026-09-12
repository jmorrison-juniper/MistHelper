# Phase 0 Research: countOrgGuestAuthorizations

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-06-28

This document resolves every implementation unknown for the new menu item before any
code is written. Each task uses the Decision / Rationale / Alternatives Considered
format mandated by the SpecKit research phase.

---

## Research Task 1: SDK function signature & behavior

**Decision**: The new menu method invokes
`mistapi.api.v1.orgs.guests.count.countOrgGuestAuthorizations(mist_session, org_id,
distinct="ssid", ssid=None, wlan_id=None, auth_method=None, start=None, end=None,
duration="1d", limit=100)`. The first positional argument is always the active
`mistapi.APISession`; `org_id` is the required path parameter; the remaining
keyword arguments map one-to-one to the OpenAPI query parameters. The return value
is an `APIResponse` whose `.data` attribute holds the JSON body, shaped as
`{"distinct": "<field>", "start": <epoch>, "end": <epoch>, "limit": <int>,
"total": <int>, "results": [ {"<field>": "<value>", "count": <int>}, ... ]}`.

**Rationale**: The enriched per-endpoint documentation under
`documentation/api/orgs/GET_orgs_org_id_guests_count.md` is currently a placeholder
(1 byte), so the contract is reconstructed from three converging sources: (a) the
spec.md inputs list (which enumerates the path and query parameter set), (b) the
`mistapi` SDK convention -- every count endpoint in the SDK follows the same
`(session, parent_id, distinct=..., start=..., end=..., duration=..., limit=...)`
calling convention, observed in adjacent modules `mistapi.api.v1.orgs.clients.count`,
`mistapi.api.v1.orgs.devices.count`, and `mistapi.api.v1.orgs.nac_clients.count`,
and (c) the Mist OpenAPI 3 specification under
`documentation/mist-api-openapi3*.yaml` which defines the canonical `count`
response envelope.

**Alternatives Considered**:

1. Treat the response as a flat list of `{value, count}` tuples (older Mist API
   shape). Rejected -- the modern `/count` endpoints all return the envelope above;
   flattening to a tuple list would lose the `distinct`, `start`, `end`, `limit`,
   and `total` fields needed for the composite primary key.
2. Call the lower-level `mistapi.APISession.mist_get()` directly to bypass the SDK
   wrapper. Rejected -- the constitution requires `mistapi` as the sole interface
   to Mist Cloud, and the SDK wrapper handles pagination, retries, and the adaptive
   delay system automatically.

---

## Research Task 2: Primary Key Strategy

**Decision**: Register `countOrgGuestAuthorizations` in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` as type `composite_pk` with the composite key
`("org_id", "distinct", "value", "start", "end")` and supplementary indexes on
`org_id`, `distinct`, and `end`.

**Rationale**: A count result is server-side aggregated over a user-supplied time
window. The same `(org_id, distinct, value)` triple yields a different count for
every distinct `(start, end)` window, so a natural UUID does not exist. Including
`start` and `end` in the composite key lets repeated runs over identical windows
upsert cleanly without duplicates while preserving historical buckets over
non-identical windows. The supplementary indexes accelerate the most common
operator queries (per-org rollups, per-distinct-field rollups, recent-window
queries) without bloating the table.

**Alternatives Considered**:

1. `natural_pk` on a synthetic concatenation `org_id + ":" + distinct + ":" +
   value`. Rejected -- collapses time windows and loses historical buckets.
2. `auto_increment_with_unique` on `(org_id, distinct, value, start, end)`.
   Rejected -- the composite five-tuple is already stable and meaningful; an
   auto-increment surrogate adds no value and breaks the documented "use natural
   business keys where they exist" rule in the MistHelper instructions.
3. `composite_pk` without `start`/`end` (just `org_id`, `distinct`, `value`).
   Rejected -- every re-run with a different window would silently overwrite the
   previous window's count, destroying history.

---

## Research Task 3: Output filename and SQLite table

**Decision**:

- CSV filename pattern: `data/org_<org_id_short>_guest_authorization_counts_<distinct>_<timestamp>.csv`
  (consistent with adjacent guest-authorization exports), where `<org_id_short>` is
  the first 8 characters of the org UUID and `<timestamp>` is `YYYYMMDD_HHMMSS`
  UTC.
- SQLite table name: `org_guest_authorization_counts`.
- ArangoDB collection name: `org_guest_authorization_counts` (mirrors SQLite name;
  edges to the existing `orgs` vertex collection are added by the existing
  DataExporter ArangoDB writer based on the `org_id` column).
- The `api_function_name` parameter passed to
  `DataExporter.write_with_format_selection()` is the literal string
  `"countOrgGuestAuthorizations"` so the exporter looks up the registered PK
  strategy by operationId.

**Rationale**: Existing guest-authorization exports use the
`org_<short>_guest_authorization_*` filename family; following that convention
keeps the `data/` directory navigable for NOC engineers and keeps DataExporter's
glob-based discovery logic happy. The SQLite table name matches the operation
domain ("guest authorization counts") and uses snake_case per project style.
Embedding `<distinct>` in the CSV filename prevents accidental overwrite when the
same org is exported with different distinct fields in succession.

**Alternatives Considered**:

1. A single shared `org_guest_authorizations` table with a `record_type` column
   distinguishing rows from `searchOrgGuestAuthorization` vs
   `countOrgGuestAuthorizations`. Rejected -- the column sets are too different;
   one table per shape is the established pattern.
2. Putting the file in a per-org subdirectory `data/<org_id>/`. Rejected -- no
   other menu item does this and changing it now would create a one-off
   inconsistency.

---

## Research Task 4: Menu category placement and next available menu number

**Decision**: Register the new operation as **menu number 96** under the
Interactive Safe / Insights category (60-96), immediately adjacent to the existing
guest-authorization listings and one slot below the Resource Intensive block at
97-101.

**Rationale**: The MistHelper menu map (documented in `agents.md` and
`.github/copilot-instructions.md`) reserves 1-59 for safe org exports, 60-96 for
interactive safe operations, 97-101 for resource-intensive operations, and
102-194 for everything else. A guest-authorization count is interactive (it
prompts for `distinct` and `duration`) and safe (read-only), so it sits naturally
at the upper edge of 60-96. Slot 96 is currently the last free position before
the resource-intensive block. The exact integer is re-verified at task generation
time -- if a competing in-flight feature branch consumes 96 first, the next free
integer in the 60-96 range is used.

**Alternatives Considered**:

1. Place it inside the safe-org-exports cluster (1-59) alongside other "count by
   X" operations. Rejected -- the user prompts for `distinct` and `duration` make
   it interactive, not a one-shot export.
2. Place it inside resource-intensive (97-101). Rejected -- the count endpoint is
   server-side aggregated and returns in <=5s; it is not heavy enough to warrant
   resource-intensive classification or `--test` skip-list inclusion.

---

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

**Decision**:

| Input         | Source                | Default        | Validation                                     |
|---------------|-----------------------|----------------|------------------------------------------------|
| `MIST_HOST`   | `.env`                | (none)         | Loaded by `mistapi.APISession` at startup      |
| `MIST_API_TOKEN` | `.env`              | (none)         | Loaded by `mistapi.APISession` at startup      |
| `org_id`      | `safe_input()` prompt | (none)         | Mist UUID regex `^[0-9a-f-]{36}$`              |
| `distinct`    | `safe_input()` prompt | `ssid`         | Enum: `ssid`, `wlan_id`, `auth_method`         |
| `duration`    | `safe_input()` prompt | `1d`           | Duration string accepted by mistapi (e.g. `1h`, `1d`, `7d`) |
| `limit`       | not prompted          | `100`          | SDK default; advanced users override via `.env` |

The user is prompted only for the three runtime-variable values (`org_id`,
`distinct`, `duration`). All credentials come from `.env` via
`mistapi.APISession`. The Mist `org_id` is *not* pulled from `.env` even when
`DEFAULT_ORG_ID` is set, because count operations are frequently run against
non-default orgs in support scenarios; presenting the prompt empty and validating
the input keeps the user in control.

**Rationale**: This matches the input model used by adjacent count menu items
(`countOrgClients`, `countOrgDevices`, `countOrgNacClients`) and avoids surprising
the user with hidden defaults. Using `safe_input(prompt, context=...)` for every
prompt is the Constitution Principle III requirement and ensures EOF in SSH /
container sessions exits cleanly with code 0.

**Alternatives Considered**:

1. Auto-load `org_id` from `.env`'s `DEFAULT_ORG_ID` and skip the prompt.
   Rejected -- support engineers need to target arbitrary orgs without editing
   `.env`.
2. Add a `start`/`end` epoch prompt pair instead of `duration`. Rejected --
   `duration` is the operator-friendly shorthand and the Mist API computes
   `start`/`end` from it server-side; offering both would double the prompt
   surface for no real flexibility gain.
3. Skip the `distinct` prompt and default unconditionally to `ssid`. Rejected --
   the whole value of the `/count` endpoint is the ability to group by different
   attributes; hiding the choice defeats the menu item's purpose.