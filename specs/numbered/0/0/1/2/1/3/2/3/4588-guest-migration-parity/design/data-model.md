# Guest data and state model

This is a proposed model, not a delivered schema.
Refer to [requirements](../spec.md) and [API evidence](contracts/api.md).

## Identities and permitted fields

| Entity | Identity and fields | Validation and privacy |
| --- | --- | --- |
| Scope | Operator context, organization ID, site ID, WLAN ID, revision. | Validate UUIDs, permitted organization, site membership, WLAN assignment, and current revision. D1 defines operator identity. |
| Authorization observation | Exact scope and normalized MAC. Observed authorization, expiry, observation time, and permitted details. | Missing fields remain unknown. Scope cannot come from display names. D1 limits personal fields. |
| Offline projection | Existing masked MAC, explicit authorized value, UTC expiry or null. | Preserve the exact three-key contract. It is not an editable identity or database key. |
| Reviewed change | Server-issued operation reference, exact scope/MAC, action, supported payload, observation revision, confirmation digest. | Bind to the reviewed actor and payload. Reject stale, wrong, reused, or canceled confirmation. |
| Import batch | Server-issued batch reference, file digest, scope map revision, normalized rows, duplicate dispositions, limits. | Record every row. D3 approves bounds and duplicate policy. Do not store raw private CSV indefinitely. |
| Audit event | Operation reference, sequence, UTC time, approved actor reference, action, scope reference, dispatch/result category. | D4 approves field disclosure and retention. Never record tokens or full personal payloads in logs. |

Use `(organization_id, site_id, wlan_id, normalized_mac)` as the natural authorization identity where the verified API supports WLAN isolation.
If the API identifies a guest by site and MAC only, D2 must resolve the true scope before schema creation.
Never use masked MAC as an identity because different devices can share its visible suffix.
Operation and batch references identify requests, not replacements for Mist natural keys.

## State transitions

**Review**: unavailable -> loading -> ready, empty, denied, failed, or stale.
Changing scope invalidates records, search results, dialogs, mappings, and confirmations.

**Authorization**: authorized true, authorized false, or unknown.
Expiry may be observed, absent, or invalid.
Time alone cannot replace a missing authorization observation.
Source UI used expiry alone. The target must explain any approved status-semantic deviation.

**Change**: draft -> validated -> reviewed -> confirmed -> durable intent -> dispatched.
Dispatch ends as observed success, explicit rejection, unknown, or reconciliation required.
Before dispatch, failure leaves the operation unstarted.
After ambiguous dispatch, no automatic retry is permitted.
A result is not successful until the approved persistence and observation contract is satisfied.

**CSV row**: parsed -> invalid or resolved -> reviewed -> confirmed -> unstarted or dispatched -> success, rejection, or unknown.
Final accounting partitions every input row, including duplicates and parsing errors.
Canceling a batch stops unstarted work. It cannot undo already-observed cloud results.

Warning: revocation and grant change network access. Recovery must not silently repeat or reverse a cloud operation.

## Shared persistence design

The source has no durable guest database or Redis cache.
No database conversion or source Redis key migration is justified.
Mist remains the record authority. The existing operational store may hold approved coordination.

D4 must verify transactions, durable intent writes, outcome writes, locking, restart recovery, and isolation from existing records.
If the existing store cannot satisfy those contracts, writes remain disabled until an approved design uses existing services.
Redis may provide scoped ephemeral coordination only after its actual target contract is inspected.
Redis cache data cannot become authoritative authorization or the sole durable audit record.

Namespaced keys include feature, organization, site, WLAN, and operation or revision as appropriate.
Do not reuse generic source cache names or cross-feature records.
D4 defines TTL and retention. This plan invents neither.
Backups must contain the approved complete operational shape and restore without overwriting unrelated application data.
Tests use `tmp_path` or isolated in-memory fixtures, never production stores.

## Input contracts

The API contract controls accepted MAC forms, integer duration bounds, and writable fields.
Email and sponsor fields require approved format and length checks.
CSV accepts a declared header set and explicit aliases.
Quoted commas, escaped quotes, embedded newlines, BOM, and CRLF need deterministic parser tests.
Duplicate names, SSIDs, MAC identities, and conflicting aliases require explicit resolution.
Unknown fields, malformed rows, invalid numbers, and excessive inputs must not silently default.
Render every external string as text. Neutralize spreadsheet formula interpretation in downloaded reports where applicable.
