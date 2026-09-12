# Phase 0 Research: countOrgUserMacs

**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)
**Endpoint**: `GET /api/v1/orgs/{org_id}/usermacs/count`
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_usermacs_count.md`

## Research Task 1: SDK Function Signature & Behavior

### Decision

Invoke the endpoint via the `mistapi` SDK call:

```python
from mistapi.api.v1.orgs.user_macs import countOrgUserMacs  # SDK module uses snake_case

response = countOrgUserMacs(
    mist_session,        # mistapi.APISession instance from session bootstrap
    org_id,              # str, UUID of the org (path parameter, required)
    distinct,            # str enum: mac | name | labels | org_id (query, required)
    limit=100,           # int, optional, default 100 per Mist API
    start=None,          # str/int, optional epoch or relative (e.g. "-1d")
    end=None,            # str/int, optional epoch or relative (e.g. "now")
)
data = response.data    # dict matching the documented 200 schema
```

The response is a single JSON object with shape:

```json
{
  "distinct": "mac",
  "total": 1234,
  "limit": 100,
  "start": 1719600000,
  "end": 1719686400,
  "results": [
    { "count": 42, "mac": "5684dae9ac8b" },
    ...
  ]
}
```

`results[]` is a list of `{<distinct_field>: <value>, "count": <int>}` aggregate rows.
The schema in the enriched doc shows the broader `user_mac` object for type reference,
but for a count endpoint the relevant runtime fields per result row are the distinct
attribute value and the count.

### Rationale

The enriched API doc
(`documentation/api/orgs/GET_orgs_org_id_usermacs_count.md`) names the SDK as
`mistapi.api.v1.orgs.user_macs.countOrgUserMacs()`. The `mistapi` 0.59+ convention is
`<module_snake_case>.<operationIdCamelCase>` and the SDK module file for User MACs is
`user_macs.py` (underscored), even though the URL segment is `/usermacs/`. Time params
accept both epoch seconds and Mist-style relative strings (`-1d`, `-1w`, `now`).

### Alternatives Considered

- **Raw `requests.get(...)`**: Rejected. Bypasses `mistapi`'s built-in adaptive rate
  limiting, retry policy, and session/token handling. Violates Constitution-aligned
  guidance that all Mist API access goes through the SDK.
- **Wrapping the SDK call inside a new helper module**: Rejected. Adds a wrapper layer
  in violation of Principle II (Class-Based, No Wrappers). The SDK call is invoked
  directly inside a single exporter class method.

---

## Research Task 2: Primary Key Strategy

### Decision

Use the `composite_pk` strategy for the per-result detail table and
`auto_increment_with_unique` for the envelope/summary row.

`ENDPOINT_PRIMARY_KEY_STRATEGIES['countOrgUserMacs']` registers the
detail-table strategy (the row-bearing payload):

```python
'countOrgUserMacs': {
    'type': 'composite_pk',
    'primary_key': ['org_id', 'distinct', 'group_value', 'window_start', 'window_end'],
    'indexes': ['org_id', 'distinct', 'group_value'],
}
```

The envelope row (one per invocation, holds the totals and window) uses an
internal autoincrement key plus a UNIQUE constraint on
`(org_id, distinct, window_start, window_end)` so re-running the same query against the
same window upserts rather than duplicates.

### Rationale

- The endpoint returns aggregate counts per distinct value, scoped to a time window.
- There is no stable Mist-issued UUID for an aggregate row; the natural identity is the
  tuple `(org_id, distinct_attribute, group_value, window_start, window_end)`.
- `composite_pk` is the documented strategy in `ENDPOINT_PRIMARY_KEY_STRATEGIES` for
  time-windowed aggregate data (matches the pattern used for `search*` and `count*`
  family endpoints).
- The envelope table uses `auto_increment_with_unique` because its identity is the
  (org, distinct, window) tuple, which can repeat across runs only when the user
  intentionally re-queries the same window -- upsert via UNIQUE is the desired
  behavior.

### Alternatives Considered

- **`natural_pk` on the `id` field**: Rejected. Per-result aggregate rows do not carry
  the user_mac `id` UUID; the count rows have only the distinct attribute value and a
  count.
- **`auto_increment_with_unique` for both tables**: Rejected. The detail table has a
  well-defined natural composite identity; relying on autoincrement would allow
  duplicates whenever a user re-runs the same window.
- **Single denormalized table**: Rejected. Mixing envelope-level totals (one row) with
  per-group detail (N rows) in the same table forces nullable columns and makes
  SQLite upserts ambiguous. Two tables keep the schema flat and the PK strategy clean.

---

## Research Task 3: Output Filename and SQLite Table

### Decision

- **CSV filenames** (under `data/`):
  - Envelope: `org_<org_id>_usermacs_count_envelope_<timestamp>.csv`
  - Detail: `org_<org_id>_usermacs_count_<distinct>_<timestamp>.csv`
- **SQLite tables** (in `data/mist_data.db`):
  - `org_usermacs_count_envelope` (envelope row)
  - `org_usermacs_count_results` (detail rows)
- **DataExporter `api_function_name`**: `"countOrgUserMacs"` -- passed verbatim to
  `DataExporter.write_with_format_selection()` so the exporter looks up the PK strategy
  by operationId.

### Rationale

- Filenames follow the existing convention in `data/` of
  `org_<scope>_<operation>_<timestamp>.csv`, keeping discoverability for NOC engineers
  who already know how to find license/inventory exports.
- SQLite table names use the `org_usermacs_count_*` prefix so they sort adjacent to
  related tables (`org_usermacs_search_*`, `org_usermacs_*`) and are immediately
  identifiable in tools like DB Browser for SQLite.
- Splitting envelope from results matches the two-table PK strategy from Research
  Task 2.

### Alternatives Considered

- **One CSV file with all rows mixed**: Rejected. Forces nullable columns and breaks
  CSV-to-Excel pivoting workflows that the NOC team uses.
- **Filename includes the `distinct` value as a column rather than a filename token**:
  Rejected. Including `<distinct>` in the filename makes it trivially obvious which
  attribute was counted without opening the file.

---

## Research Task 4: Menu Category Placement and Next Available Menu Number

### Decision

- **Menu number**: **59**
- **Category**: Safe Org Exports - Misc (slots 56-59 per `.github/copilot-instructions.md`
  Menu Categories table).
- **Target class**: The existing user-MACs / NAC org-export class in `MistHelper.py`. If
  no dedicated class exists yet for usermacs operations, the new method is added to the
  class that already owns the related `searchOrgUserMacs` and `listOrgUserMacs`
  exports, identified at implementation time by grep
  (`rg "searchOrgUserMacs|listOrgUserMacs" MistHelper.py`). If those operations live on
  the same class as other NAC exports (likely `NacExportUtils` or
  `OrgUserMacsExporter`), the new `export_org_usermacs_count()` method joins them.

### Rationale

- Slot 59 is the last open slot in the Safe Org Exports / Misc tail (56-59), keeping
  the user-MAC count operation co-located with other org-wide, read-only, low-cost
  exports that NOC engineers expect to find in the 1-59 block.
- The interactive site-scoped block starts at 60; placing this org-only operation in
  the 60+ block would mislead users into expecting a site prompt.
- Adding the method to an existing class satisfies Principle II (Class-Based, No
  Wrappers) and keeps the file diff small.

### Alternatives Considered

- **Menu number 30 (clients cluster)**: Rejected. User MACs are NAC-specific identity
  records, not connected-client records; placing them with wireless/wired clients
  would confuse users.
- **Menu number 100+ (resource-intensive)**: Rejected. The endpoint is a single count
  call bounded by `limit`; classifying it as resource-intensive is incorrect.
- **Creating a new `UserMacsExporter` class**: Rejected unless grep at implementation
  time confirms there is no existing home for related operations. Creating a new class
  just for one method violates the "do not introduce new top-level classes
  unnecessarily" interpretation of the hierarchy principle.

---

## Research Task 5: Required User Prompts

### Decision

Prompts collected via `safe_input()` (all with explicit `context=` strings):

| Order | Prompt label | Source | Required | Validation | Default if blank |
|-------|--------------|--------|----------|------------|------------------|
| 1 | `org_id` | `safe_input` (user) OR `.env` `MIST_ORG_ID` if present | Yes | Must match Mist UUID regex `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}` | none (re-prompt) |
| 2 | `distinct` | `safe_input` (user) | Yes | Must be one of `mac`, `name`, `labels`, `org_id` | `mac` |
| 3 | `limit` | `safe_input` (user) | No | Must parse as positive int <=1000 | `100` (Mist API default) |
| 4 | `start` | `safe_input` (user) | No | Empty -> omit; else epoch int or Mist relative string (`-1d`, `-1w`, `-2h`, `now`) | empty (omit) |
| 5 | `end` | `safe_input` (user) | No | Same as `start` | empty (omit) |

API token (`MIST_API_TOKEN`) and host (`MIST_HOST`) come from `.env` via the existing
`mistapi.APISession` bootstrap -- never prompted, never logged.

### Rationale

- `org_id` is the only path parameter and must be available. Falling back to
  `MIST_ORG_ID` from `.env` (the existing project convention) keeps non-interactive
  test mode (`--test`) working without manual input.
- `distinct` is the only required query parameter. Defaulting to `mac` matches the
  most common NOC question ("how many distinct MAC addresses do we track?") and keeps
  the prompt friendly for junior engineers.
- `limit`, `start`, `end` are optional. Empty input means omit from the SDK call so the
  Mist API applies its own defaults.
- All prompts use `safe_input()` per Principle III (Safety-First, NON-NEGOTIABLE). EOF
  in SSH / container contexts exits 0 cleanly.

### Alternatives Considered

- **Single combined prompt string parsed with regex**: Rejected. Junior NOC engineers
  benefit from one question at a time. Combined prompts hide validation failures.
- **No defaults; force user to type every parameter**: Rejected. Increases friction for
  the common case. Defaults are clearly logged at INFO so the user always sees what was
  applied.
- **Read `distinct` from a CLI flag instead of an interactive prompt**: Rejected for
  the interactive path; `--menu 59 --distinct mac` may be added later as a
  non-interactive convenience but is out of scope for this spec.
