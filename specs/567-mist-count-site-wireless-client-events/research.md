# Phase 0 Research: countSiteWirelessClientEvents

**Feature**: 567-mist-count-site-wireless-client-events
**Date**: 2026-06-29
**Source of truth**: `documentation/api/sites/GET_sites_site_id_clients_events_count.md`
(enriched OpenAPI doc) and the spec at `specs/567-mist-count-site-wireless-client-events/spec.md`.

---

## Research Task 1: SDK function signature and behavior

### Decision

Use `mistapi.api.v1.sites.clients.events.count.countSiteWirelessClientEvents(
mist_session, site_id, distinct=None, type=None, reason_code=None, ssid=None, ap=None,
proto=None, band=None, wlan_id=None, start=None, end=None, duration="1d", limit=100)`
as the single SDK call. The first positional argument is the `mistapi.APISession`
instance constructed once at MistHelper startup; the second is the `site_id` UUID; all
remaining arguments are optional keyword query parameters mirroring the OpenAPI spec.

The response is a JSON object with the envelope fields `distinct`, `start`, `end`,
`limit`, `total`, and a `results` array. Each element of `results` is an object with a
required `count` integer plus arbitrary string-valued additional properties whose key
matches the supplied `distinct` value (for example `{"count": 17, "type":
"FS_DISCONNECTED"}` when `distinct=type`).

### Rationale

- The enriched doc explicitly lists the path, parameters, response schema, and the
  `mistapi` module path. No SDK guessing required.
- Defaults `duration="1d"` and `limit=100` match the OpenAPI defaults, so the
  implementation can omit them when the user does not supply explicit values.
- The endpoint supports pagination (`limit` / implicit `page`). The implementation will
  use the existing `DEFAULT_API_PAGE_LIMIT=1000` (overridable via `MIST_PAGE_LIMIT` env
  var) and the existing pagination loop pattern from adjacent menu items so the full
  result set is fetched without manual paging by the user.

### Alternatives Considered

- **Direct HTTP via `requests`**: Rejected. The constitution mandates `mistapi` as the
  sole interface to Mist Cloud.
- **Skip pagination, always pass `limit=1000`**: Rejected. The grouping endpoint can
  return more than 1000 distinct buckets (for example when `distinct=ap` on a large
  site with many APs and many client MAC churn events); reusing the existing pagination
  loop keeps behavior consistent with sibling menu items and prevents silent truncation.

---

## Research Task 2: Primary Key Strategy

### Decision

Register `countSiteWirelessClientEvents` in `ENDPOINT_PRIMARY_KEY_STRATEGIES` with
**`composite_pk`** strategy and primary key
`['site_id', 'distinct', 'bucket_key', 'start', 'end']` for the results table, plus a
separate summary table keyed on `['site_id', 'distinct', 'start', 'end']`.

- `site_id`: the site under inspection.
- `distinct`: the grouping attribute the user requested (`type`, `ssid`, `ap`, `band`,
  `proto`, `wlan_id`). Without it, two count runs against the same site over the same
  window would alias each other.
- `bucket_key`: the value of the additional property on each result row (the actual
  group label, for example the SSID name or AP MAC).
- `start` and `end`: the epoch-seconds window resolved by the SDK from the user-supplied
  `start` / `end` / `duration`. Including the window in the key lets repeated runs
  against rolling windows accumulate historical buckets instead of overwriting them.

### Rationale

- The response is fundamentally time-series-shaped: it is a count over an interval. A
  natural UUID primary key does not exist.
- An auto-increment primary key would defeat upsert idempotency: re-running the same
  query for the same window would duplicate every bucket on every run.
- `composite_pk` matches the precedent set by sibling event / stat endpoints in
  `ENDPOINT_PRIMARY_KEY_STRATEGIES` (for example the `searchOrgDeviceEvents` entry
  cited in `.github/copilot-instructions.md`).

### Alternatives Considered

- **`natural_pk` on a synthesized hash**: Rejected. Brittle and unnecessary -- the
  composite of `(site_id, distinct, bucket_key, start, end)` is already canonical.
- **`auto_increment_with_unique` with a UNIQUE index on the same five columns**:
  Functionally equivalent but the constitution-aligned `composite_pk` path is simpler
  to read and keeps the SQLite `INSERT OR REPLACE` upsert path identical to every
  other event-count operation.

---

## Research Task 3: Output filename and SQLite table

### Decision

- **CSV summary file**: `data/site_wireless_client_events_count_summary.csv`
- **CSV results file**: `data/site_wireless_client_events_count_results.csv`
- **SQLite summary table**: `site_wireless_client_events_count_summary`
- **SQLite results table**: `site_wireless_client_events_count_results`
- **ArangoDB collection (results)**: `site_wireless_client_events_count_results`
- **ArangoDB collection (summary)**: `site_wireless_client_events_count_summary`

The two files / tables are emitted by a single
`DataExporter.write_with_format_selection(data, filename, api_function_name=
'countSiteWirelessClientEvents')` invocation per shape; the exporter routes the rows
to the correct backend based on the configured output mode.

### Rationale

- The endpoint returns a small envelope (5 scalar fields) plus an array of grouping
  rows. Splitting into a summary table and a results table avoids storing the envelope
  redundantly on every bucket row, and matches the existing two-table pattern used by
  the org-license async claim status feature (spec 500).
- File names are derived from the operationId by stripping the `count` prefix and
  snake-casing the rest -- consistent with the existing site-scoped event count files
  in `data/`.
- ArangoDB collection names mirror the SQLite table names so cross-backend queries
  remain straightforward.

### Alternatives Considered

- **Single denormalized table**: Rejected. Forces the user to filter out the envelope
  metadata columns on every analytical query and bloats SQLite storage for high-
  cardinality `distinct` choices like `ap`.
- **Filename keyed on the `distinct` value (for example
  `..._count_by_type.csv`)**: Rejected. The user can change `distinct` between runs;
  parameter-keyed filenames would create a sprawling file set under `data/` and break
  the one-operation -> one-file convention.

---

## Research Task 4: Menu category placement and next available menu number

### Decision

Place the new menu item at **menu number 78** in the Insights cluster (73-79). The
operation is registered under the menu category "Site Insights / Event Analytics".

### Rationale

- The MistHelper menu taxonomy in `.github/copilot-instructions.md` partitions
  operations into ranges by behavior:
  - 60-72: Site devices (interactive safe)
  - 73-79: Insights
  - 80-91: Stats
  - 92-96: Viewers
- A count-by-attribute over site wireless client events is fundamentally an
  *analytical / insight* operation, not a per-device action, a raw stats pull, or a
  passive viewer. The Insights cluster (73-79) is the correct semantic bucket.
- Spec 500 already claimed slot 95 in the Org Licenses sub-cluster. The Insights
  cluster has no spec 567 claim yet, and 78 is the next free integer below the
  reserved 79 slot.
- The proposal is re-verified at `/speckit.tasks` time; if 78 collides with another
  in-flight feature branch, the next free integer in 73-79 is used (or 79 if 78 is
  taken). The CHANGELOG entry and README operation-count bump are written against
  whichever number is final at merge time.

### Alternatives Considered

- **Menu in 27-30 Clients cluster (safe org exports)**: Rejected. The 27-30 range is
  org-scoped; this endpoint is site-scoped and interactive (requires a `site_id`
  prompt).
- **Menu in 80-91 Stats cluster**: Rejected. The Stats cluster is for raw per-entity
  metrics; a grouping-aggregate endpoint is better classified as Insights.
- **Menu in 92-96 Viewers cluster**: Rejected. Viewers are passive read-displays of
  static config; this endpoint computes an aggregation.

---

## Research Task 5: Required user prompts (which IDs from the user, which from .env)

### Decision

The implementation collects these inputs at runtime, all through `safe_input()`:

| Input | Source | Required | Prompt context string |
|-------|--------|----------|-----------------------|
| `MIST_HOST` | `.env` | yes | _not prompted_ |
| `MIST_API_TOKEN` | `.env` | yes | _not prompted_ |
| `MIST_ORG_ID` | `.env` (optional default) | optional | _not prompted_ -- listed below as fallback |
| `site_id` | prompt | yes | `count_site_wireless_client_events:site_id` |
| `distinct` | prompt (default `type`) | optional | `count_site_wireless_client_events:distinct` |
| `type` filter | prompt (default blank) | optional | `count_site_wireless_client_events:type` |
| `reason_code` filter | prompt (default blank) | optional | `count_site_wireless_client_events:reason_code` |
| `ssid` filter | prompt (default blank) | optional | `count_site_wireless_client_events:ssid` |
| `ap` filter | prompt (default blank) | optional | `count_site_wireless_client_events:ap` |
| `proto` filter | prompt (default blank) | optional | `count_site_wireless_client_events:proto` |
| `band` filter | prompt (default blank) | optional | `count_site_wireless_client_events:band` |
| `wlan_id` filter | prompt (default blank) | optional | `count_site_wireless_client_events:wlan_id` |
| `start` epoch / relative | prompt (default blank) | optional | `count_site_wireless_client_events:start` |
| `end` epoch / relative | prompt (default blank) | optional | `count_site_wireless_client_events:end` |
| `duration` | prompt (default `1d`) | optional | `count_site_wireless_client_events:duration` |
| `limit` | prompt (default `100`) | optional | `count_site_wireless_client_events:limit` |

The implementation collapses the optional filters into a single `filters_dict` and the
time inputs into a single `time_window_dict` so the public method respects the
5-Item-Rule parameter ceiling.

### Rationale

- `MIST_HOST` and `MIST_API_TOKEN` are credentials and must live in `.env` per
  Constitution Principle III (Safety-First). They are never prompted at runtime and
  never logged.
- `site_id` is not a credential and varies per invocation, so it must be prompted. If
  the user has set a `MIST_DEFAULT_SITE_ID` in `.env`, the prompt offers it as a
  default; pressing Enter accepts it.
- All filter and window parameters are optional in the OpenAPI spec; defaults match
  the spec (`duration=1d`, `limit=100`). Blank input from `safe_input()` means "do not
  pass this argument to the SDK", which lets the Mist API default apply.
- Every prompt uses an explicit `context=` argument so EOF in SSH / container sessions
  produces a clean exit 0 without traceback.

### Alternatives Considered

- **Hard-code `distinct=type` and skip the prompt**: Rejected. The whole utility of
  this endpoint is the grouping-attribute flexibility. Hard-coding it would force the
  user to write custom code for any other grouping, defeating the purpose of cataloging
  the endpoint.
- **Read site_id from a config file rather than prompt**: Rejected. The interactive
  flow is the documented UX for site-scoped menu items, and reusing the existing
  `safe_input()` path keeps SSH / container EOF handling uniform.
- **Pull defaults from `delay_metrics.json`**: Rejected. That file is for adaptive
  rate limiting, not user input defaults.
