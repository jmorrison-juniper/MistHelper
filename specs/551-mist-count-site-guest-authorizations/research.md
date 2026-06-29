# Phase 0 Research: countSiteGuestAuthorizations

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/sites/{site_id}/guests/count`
**SDK module**: `mistapi.api.v1.sites.guests.count`

This file resolves every unknown that the implementation phase will need. Each task is
recorded as Decision / Rationale / Alternatives Considered.

---

## Research Task 1: SDK function signature and behavior

**Source**: `documentation/api/sites/GET_sites_site_id_guests_count.md`

### Decision

The implementation will call:

```python
response = mistapi.api.v1.sites.guests.count.countSiteGuestAuthorizations(
    apisession,
    site_id,
    distinct=distinct,   # optional, default per Mist docs is "wlan_id"
    start=start_epoch,   # optional, epoch seconds or relative string
    end=end_epoch,       # optional, epoch seconds or relative string
    duration=duration,   # optional, e.g. "1d" / "7d" / "2w", default "1d"
    limit=limit,         # optional, integer, default 100
)
data = response.data    # JSON object: {distinct, start, end, limit, total, results[]}
```

The response is a single JSON object (not paginated through `mistapi.get_all`). The
`results` array contains one object per distinct bucket, shape
`{"count": int, "<distinct-attr>": str}` where the second key name varies based on the
`distinct` argument. The object also includes top-level `distinct`, `start`, `end`,
`limit`, and `total` fields.

### Rationale

The enriched endpoint doc at
`documentation/api/sites/GET_sites_site_id_guests_count.md` documents the path, all five
query parameters with their defaults (`duration=1d`, `limit=100`), the 200 response
schema (object with `distinct`, `end`, `limit`, `results[]`, `start`, `total` required),
and explicitly lists the SDK call as `mistapi.api.v1.sites.guests.countSiteGuestAuthorizations()`.
The shape of `results[]` is `count_result` with `count` required and arbitrary additional
string keys -- mirroring the sibling `countOrgGuestAuthorizations` already registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` at `MistHelper.py:4400`.

### Alternatives Considered

- **Using `mistapi.get_all()` for pagination**: rejected. The endpoint returns an
  aggregate count object, not a list of entities. `limit` caps bucket cardinality, not
  pages. Calling `get_all()` would produce an incorrect single-object-in-list shape.
- **Calling the underlying HTTP path directly with `requests`**: rejected. Violates the
  project rule that `mistapi` is the sole permitted Mist Cloud interface and would
  bypass the SDK's auth header / retry / rate-limit handling.

---

## Research Task 2: Primary Key Strategy

### Decision

Use **`auto_increment_with_unique`** with composite uniqueness on
`(site_id, distinct, bucket_value, start, end)`:

```python
"countSiteGuestAuthorizations": {
    "type": "auto_increment_with_unique",
    "primary_key": ["misthelper_internal_id"],
    "indexes": ["site_id", "distinct", "start", "end"],
    "unique_constraints": [["site_id", "distinct", "bucket_value", "start", "end"]],
    "description": "Site-level guest authorization count aggregates",
},
```

### Rationale

This endpoint returns aggregate count data, not stable entities with API-assigned UUIDs.
The sibling `countOrgGuestAuthorizations` at `MistHelper.py:4400` already uses
`auto_increment_with_unique` with the same shape; staying consistent reduces cognitive
load and matches the documented pattern in `.github/copilot-instructions.md` ("Auto-
increment with Unique: Aggregated/summary data without stable keys"). The composite
unique constraint prevents duplicate rows on re-runs over the same time window with the
same `distinct` attribute.

### Alternatives Considered

- **`natural_pk` on `(site_id, distinct, bucket_value)`**: rejected. Two runs with
  different time windows must produce different rows; a window-agnostic natural key
  would clobber prior runs.
- **`composite_pk` including a timestamp**: rejected. Count results carry no per-row
  timestamp; only the window `start`/`end` are available. Expressing this as
  `auto_increment_with_unique` with a unique constraint on the window bounds is the
  documented idiom for this case.

---

## Research Task 3: Output filename and SQLite table

### Decision

- **CSV filename**: `SiteGuestAuthorizationCounts.csv` (CamelCase, ends in `.csv`, lives
  under `data/`).
- **SQLite table name**: `countSiteGuestAuthorizations` (operationId verbatim -- this is
  the project convention used by `DataExporter.write_with_format_selection` when the
  caller passes `api_function_name="countSiteGuestAuthorizations"`).
- **ArangoDB collection** (when polyglot backend active): same as SQLite table name.

### Rationale

Following the existing pattern for sibling count endpoints (e.g. `countOrgGuestAuthorizations`
exports to `OrgGuestAuthorizationCounts.csv` and SQLite table `countOrgGuestAuthorizations`).
The `api_function_name=` kwarg of `DataExporter.write_with_format_selection` keys both
the SQLite table and the PK strategy lookup, so it must equal the operationId.

### Alternatives Considered

- **`site_guest_count.csv` lower-case**: rejected. The repo convention for the existing
  ~190 menu items is CamelCase CSV names readable by NOC engineers at a glance.
- **Per-site filename (`SiteGuestAuthorizationCounts_<site_id>.csv`)**: rejected. The
  SQLite table already stores `site_id` per row, so single-file output keeps the data
  set queryable as one table across many sites without UNION ALL.

---

## Research Task 4: Menu category placement and next available menu number

### Decision

- **Category**: Safe Org Exports / Site Stats cluster (menu range 51-95 per
  `.github/copilot-instructions.md` Menu Categories table).
- **Proposed menu number**: **94** -- the next available integer in the safe-org / site-
  stats cluster, sitting next to `countOrgGuestAuthorizations` (already a sibling) and
  below the resource-intensive block at 96-101.

### Rationale

The `.github/copilot-instructions.md` menu-categories table lists 51-95 as the safe org
exports range and 96-101 as resource intensive. A count endpoint with `limit=100`
default and a single GET round-trip is not resource intensive, so it belongs in 51-95.
Number 94 is adjacent to other guest-related and counts-related operations and is
currently unallocated in this worktree. If another in-flight branch claims 94 before
merge, the next free integer below 95 is used.

### Alternatives Considered

- **Number 92-96 viewers cluster**: rejected. Those are "viewers" (interactive read
  loops), not one-shot exports. This endpoint is a single GET + export.
- **Number 80-91 stats cluster**: rejected. Those are device / port stats, not guest
  counts. Placing it next to `countOrgGuestAuthorizations` is the semantically closest
  fit.

---

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

### Decision

The menu method prompts for, in order:

1. **`site_id`** -- prompted via
   `safe_input("Site ID: ", context="count_site_guest_authorizations:site_id")`.
   Validated against the UUID-shape regex before the SDK call.
2. **`distinct`** -- prompted via
   `safe_input("Distinct attribute (ssid|wlan_id|auth_method|hostname) [wlan_id]: ",
   context="count_site_guest_authorizations:distinct")`. Empty input defaults to
   `wlan_id`. Free-text accepted because the API enum is not formally constrained in the
   OpenAPI schema; the value is forwarded as-is.
3. **`duration`** -- prompted via
   `safe_input("Duration (e.g. 1d, 7d, 2w) [1d]: ",
   context="count_site_guest_authorizations:duration")`. Empty input defaults to `1d`.
4. **`limit`** -- not prompted; hard-coded to the API default of `100` distinct buckets.
   If a NOC engineer needs a different limit they may re-run with `--menu 94` after
   editing the local config; widening the prompt set would violate the 5-Item Rule param
   cap on the implementation method.

From `.env`:

- `MIST_HOST` (e.g. `api.mist.com`) -- consumed by the existing `mistapi.APISession`
  bootstrap; not prompted per-call.
- `MIST_API_TOKEN` -- consumed by `mistapi.APISession`; never logged.

Not prompted, not from `.env`:

- `org_id` -- not required by this endpoint. The site_id alone scopes the call.
- `start` / `end` epochs -- the API accepts `duration` as a convenience that supersedes
  explicit start/end. To keep the param surface within the 5-Item Rule and consistent
  with the spec's "junior NOC engineer" audience, only `duration` is exposed.

### Rationale

Minimizing prompt count keeps the menu item safe for SSH and container EOF contexts and
respects the 5-Item Rule cap (max 4 prompted inputs plus `self` = 5). Defaulting
`distinct` to `wlan_id` matches the most common operator question ("how many guests on
each SSID's underlying WLAN?"). Keeping `limit` at the API default avoids accidentally
truncating bucket lists for sites with many SSIDs while still bounding response size.

### Alternatives Considered

- **Prompting for `start` / `end` epoch directly**: rejected. Junior NOC engineers do
  not think in epoch seconds. `duration` is the friendlier surface and the API supports
  it natively.
- **Prompting for `limit`**: rejected. Adds a fifth interactive prompt for a knob that
  the API default already handles well. The `--fast` mode and adaptive delay system
  already manage throughput.
- **Reading `site_id` from `.env`**: rejected. Sites are per-customer entities; binding
  one in `.env` would make the menu item single-site and break the use case where an
  operator iterates over multiple sites in one session.
