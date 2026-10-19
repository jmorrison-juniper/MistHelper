# Data Model: MistCircuitStats Redis Dashboard Migration

**Status**: Proposed contract for planning. Confirm fields with source implementation and the accepted Mist API contracts before writing product code.

## Entities

### Organization

| Field | Type | Rule |
|---|---|---|
| `org_id` | Mist organization identifier | Required. Resolve from the existing MistHelper organization context. |
| `display_name` | Text | Optional. Use only a value returned by an authorized source. |

An organization owns sites and refresh state. A client request cannot select an organization outside the current MistHelper authorization context.

### Site

| Field | Type | Rule |
|---|---|---|
| `site_id` | Mist site identifier | Required. Must belong to the selected organization. |
| `org_id` | Mist organization identifier | Required. Must match the owning organization. |
| `display_name` | Text | Optional. Use only a value returned by Mist. |

An organization has zero or more sites. Site discovery uses the verified SDK contract for `listOrgSites`.

### Gateway

| Field | Type | Rule |
|---|---|---|
| `gateway_id` | Mist device identifier | Required. Use the stable identifier returned by Mist. |
| `site_id` | Mist site identifier | Required. Must match the gateway's returned site. |
| `display_name` | Text | Optional. Do not substitute a MAC address for the gateway identifier. |
| `device_type` | Text | Required when returned. Must identify an eligible gateway. |

A site has zero or more eligible gateways. Verify that the source uses `listSiteDevices` or another exact SDK operation and confirm its device-type filter.

### WAN Port Observation

| Field | Type | Rule |
|---|---|---|
| `org_id` | Mist organization identifier | Required for cache isolation and authorization. |
| `site_id` | Mist site identifier | Required. Must match the gateway. |
| `gateway_id` | Mist device identifier | Required. Must match the observation source. |
| `port_id` | Mist port identifier | Required when the source returns one. Do not infer a port from display text. |
| `metric_name` | Text | Required. Must match an accepted source metric. |
| `value` | Number or missing | Preserve missing values as unknown. Do not replace them with zero. |
| `unit` | Text or missing | Preserve the source unit. Verify it against the API contract. |
| `observed_at` | UTC timestamp or missing | Keep the source timestamp. Do not invent a timestamp for an untimestamped value. |
| `collected_at` | UTC timestamp | Required. Set when the worker collects the record. |

### Peer Path Observation

| Field | Type | Rule |
|---|---|---|
| `org_id` | Mist organization identifier | Required for cache isolation and authorization. |
| `site_id` | Mist site identifier or missing | Preserve the source value. |
| `peer_id` | Stable Mist peer identifier or missing | Use only the identifier returned by a verified API contract. |
| `peer_label` | Text or missing | Display data only. Do not use as the natural key. |
| `metric_name` | Text | Required. Must match an accepted source metric. |
| `value` | Number or missing | Preserve unknown values. |
| `observed_at` | UTC timestamp or missing | Preserve the source timestamp. Do not imply history when the API returns a point-in-time value. |
| `collected_at` | UTC timestamp | Required. Set when the worker collects the record. |

Use source and API contracts to infer peer history, latency, jitter, or state transitions. Require timestamped samples.

### Gateway Insight

| Field | Type | Rule |
|---|---|---|
| `org_id` | Mist organization identifier | Required for cache isolation and authorization. |
| `site_id` | Mist site identifier | Required. |
| `gateway_id` | Mist device identifier | Required. |
| `metric_name` | Text | Required. Must match the verified metric catalog. |
| `value` | Number or missing | Preserve absent values as unknown. |
| `unit` | Text or missing | Preserve the verified source unit. |
| `observed_at` | UTC timestamp or missing | Preserve the API timestamp. |
| `collected_at` | UTC timestamp | Required. Set when the worker collects the record. |

### Snapshot

| Field | Type | Rule |
|---|---|---|
| `schema_version` | Integer | Required. Begin at version 1 only after contract approval. |
| `owner` | Text | Required. Identifies the single feature or collector allowed to write the key. |
| `org_id` | Mist organization identifier | Required. |
| `site_id` | Mist site identifier or organization scope | Required. State the scope in the key and payload. |
| `record_type` | Enumerated text | Required. Use a bounded observation type. |
| `record_id` | Mist natural identifier or stable tuple | Required. Never use a generated random ID. |
| `state` | Enumerated text | Required. One of `complete`, `partial`, `stale`, or `unavailable`. Synthetic preview state is separate. |
| `collected_at` | UTC timestamp | Required for a live snapshot. |
| `expires_at` | UTC timestamp | Required. Must match the approved Redis TTL. |
| `records` | List of observations | Required. Validate shape before publication. |

Historical Redis candidate: `misthelper:wan:mcsr:v1:<org_id>:<site_id>:<record_type>:<record_id>`. This prefix is not reserved or approved. Review the existing cache in [contracts/redis-cache.md](contracts/redis-cache.md) before selecting any target model. Every write requires one approved owner and TTL. No #4220 write path has approval.

### Refresh Result

| Field | Type | Rule |
|---|---|---|
| `org_id` | Mist organization identifier | Required. |
| `started_at` | UTC timestamp | Required. |
| `finished_at` | UTC timestamp or missing | Missing if the process stops before completion. |
| `state` | Enumerated text | One of `complete`, `partial`, `failed`, or `skipped`. |
| `reason` | Safe text or code | Required for non-complete state. Must not contain credentials or raw sensitive responses. |
| `request_count` | Non-negative integer | Required. Count admitted Mist SDK attempts only. |
| `published_snapshot_ids` | List of natural key references | Required. Empty when no complete snapshot was published. |

## Relationships

- One organization owns many sites.
- One site owns many gateways.
- One gateway supplies zero or more WAN port observations and gateway insights.
- An organization or site may own peer-path observations, depending on the verified API response.
- A snapshot contains observations for exactly one organization and one declared scope.
- A refresh result may publish zero or more complete snapshots.

## Validation and State Rules

1. Validate organization, site, gateway, port, and peer identifiers before cache key construction or API calls.
2. Confirm that site and gateway ownership matches the current MistHelper organization context.
3. Enforce bounded pagination and deduplicate records by source natural keys.
4. Preserve missing metrics as unknown. Do not convert missing values to zero.
5. Publish a snapshot only after its structure and ownership pass validation.
6. Keep the previous valid snapshot when refresh fails or returns invalid partial data.
7. Mark data stale by the approved source threshold. Do not choose a threshold from undocumented behavior.
8. Set expiry to the agreed cache TTL. The source guide describes 900 seconds at the default interval, while the implementation review reports 31 days. Do not adopt either value without a target freshness decision.
9. Encode cache values as a documented JSON format. Do not use executable serialization formats.
10. A Redis outage must not trigger an unadmitted Mist request from a portal read.
