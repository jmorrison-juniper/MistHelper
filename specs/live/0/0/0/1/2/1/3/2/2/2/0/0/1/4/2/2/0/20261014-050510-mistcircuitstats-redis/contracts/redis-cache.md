# Redis Cache Contract: MistCircuitStats Redis Dashboard Migration

**Status**: Proposed contract. Do not implement until #4195 and #4200 ownership and existing Redis conventions are reviewed.

## Existing Dashboard Baseline

Merged PR #4252 uses `RedisDashboardCache` with the existing shared Redis client in `src/interfaces/portals/wan_dashboard/services.py`.

| Setting | Existing value | Scope |
|---|---|---|
| `CACHE_PREFIX` | `wan-dashboard:v1:` | Existing dashboard keys |
| `SITE_TTL` | 300 seconds | Site data |
| `ENTITY_TTL` | 600 seconds | Entity data |
| `STALE_TTL` | 86400 seconds | Last-success data |

These values describe existing behavior only. They do not approve a #4220 cache, writer, TTL, lease, or outage policy. Do not alter existing keys during planning.

## Resource Boundary

- Use the existing MistHelper Redis service only.
- Do not add a Redis service, database, port, or Compose group.
- Use Redis only for transient dashboard snapshots and approved refresh coordination.
- Do not treat Redis TTL as durable history or source retention.
- Do not reuse a key owned by another MistHelper feature.

## Namespace and Ownership

Historical candidate only. This prefix is not reserved or approved:

```text
misthelper:wan:mcsr:v1:<org_id>:<site_id>:<record_type>:<record_id>
```

- `mcsr` identifies this migration namespace.
- `v1` identifies the payload schema version.
- The organization and site identifiers isolate tenant data.
- Each key has one named writer. Dashboard routes read the key and do not write snapshots.
- A refresh owner may publish only after it validates the organization, key owner, schema, and complete record set.
- Organization-scoped peer records must use a documented organization scope instead of an empty site identifier.
- The prefix and key parts require review against existing MistHelper Redis keys before implementation.
- Prefer the existing canonical cache when it meets an approved requirement. Do not create a second namespace without an explicit unique-scope decision.

## Serialization

- Encode payloads as UTF-8 JSON with a documented top-level schema version.
- Do not use pickle or another executable serialization format.
- Validate the decoded version and required fields before use.
- Treat malformed or unknown-version data as unavailable. Do not silently substitute defaults.
- Keep credentials, authorization headers, raw API request objects, and secrets out of values and keys.

## Expiry and Refresh

- The source guide documents a 300-second interval and a TTL of three intervals. The implementation review reports a 300-second interval and a 31-day TTL.
- Treat both TTL values as source evidence, not an approved MistHelper policy. The long implementation TTL conflicts with the guide and can retain stale data.
- Before implementation, verify the source interval, TTL calculation, freshness threshold, and maximum allowed MistHelper request rate.
- Select a target TTL from MistHelper freshness and outage requirements. Do not copy a source TTL multiplier without an approved reason.
- A refresh must stage and validate a complete replacement before publishing it.
- A failed or partial refresh must preserve the last valid snapshot and record a safe failure state.
- A scheduler or worker must prove single ownership before requesting Mist data. If ownership cannot be established, skip the refresh.
- An interrupted owner must release or expire its lease. Verify that the current project has a suitable coordination pattern before selecting a lock.

## Outage Behavior

| Condition | Required result |
|---|---|
| Redis read fails | Show an explicit unavailable state. Do not make a fallback Mist request from the page. |
| Redis write fails | Keep any reachable previous snapshot. Mark refresh as failed and do not report new data as saved. |
| Value is malformed | Reject the value, log a safe error, and report unavailable or stale data. |
| Cache key belongs to another owner | Refuse the write and report an ownership conflict. |
| Mist API fails | Preserve the last valid snapshot and mark its age and failure state. |
| Cache expires during a Mist outage | Report unavailable data. Do not label fixtures as live. |

## Required Tests

- Prove that keys for two organizations, sites, and record types do not collide.
- Prove the key version and payload version are checked.
- Prove that the selected TTL meets the approved freshness limit and cannot exceed its maximum.
- Prove that malformed values, wrong owners, and unknown versions fail safely.
- Prove that partial refresh does not replace the previous valid snapshot.
- Prove that a Redis outage causes no page-triggered Mist request.
- Prove that a worker without an ownership lease skips collection.
- Prove logs redact tokens and do not include secret payloads.
