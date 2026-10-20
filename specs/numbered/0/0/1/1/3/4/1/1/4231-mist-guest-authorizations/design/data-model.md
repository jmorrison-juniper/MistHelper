# Data Model: Guest Authorizations

These entities describe conditional future behavior. They do not create storage or approve a guest-data route.
Mist remains the authorization authority.

## Scope and Observation

| Entity | Fields | Validation |
| --- | --- | --- |
| Scope | Organization ID, scope kind, site ID when applicable, WLAN ID, permitted action | Bind returned membership and operator permission before any disclosure or change |
| Observation | Scoped record, authorization state, reported expiry, observation time | Preserve absent fields as unknown and reject malformed values |
| Connected client | Scoped MAC address, returned hostname and IP address | Search only permitted returned fields |

Do not assume a site selection restricts organization-wide authorization.
G5 must establish the relationship between a WLAN, its portal settings, and the effective authorization resource.
Do not use a MAC address as a globally unique authorization key. Combine it with the verified scope.

The existing offline projection accepts one mapping and validates its MAC, authorization flag, and expiry.
Its exact output is `masked_mac`, `authorized`, and `expires_at`.
It does not validate organization membership, WLAN eligibility, identity, or permission.
It does not accept a new public response schema in this refresh.

## Import Batch

| Field | Meaning | Constraint |
| --- | --- | --- |
| Scope and reviewed content identifier | Binds the operator decision to one batch | Changed content or scope invalidates confirmation |
| Validated rows | Ordered unique scoped targets | Approved byte, row, header, encoding, and cell bounds apply |
| Duration and supported fields | Requested access change | Approved verified contract only |
| Confirmation | Exact operation-specific typed word and current permission | Validate again before submission |
| Row outcome | Rejected, succeeded, failed, unknown, or not attempted | Exactly one final outcome per row |

No raw CSV enters a signed browser cookie, cache, log, or persistent store by default.
If a future preview needs server-side storage, G4 must approve its lifetime, isolation, cleanup, and existing storage mechanism first.
Do not select numeric retention values in implementation without approval.

## States and Failure Boundaries

```text
received -> validated -> previewed -> confirmed -> submitting -> completed
                                                   |
                                                   +-> stopped with per-row outcomes
```

Invalid rows never reach submission.
A rate limit, uncertain cloud result, or audit failure stops later rows.
Completed cloud changes remain completed even when audit persistence fails.
The page must distinguish those facts and must not report overall success.
Do not roll back, repeat, or broaden an uncertain operation automatically.

## Audit Evidence

| Field | Meaning |
| --- | --- |
| Operator attribution | Identity or attribution mechanism approved by G2 and G4 |
| Operation and scope | Exact confirmed action and resource |
| Masked target | Device identifier without a complete MAC address |
| Cloud outcome and audit outcome | Separate facts, including unknown cloud result |
| UTC time and correlation reference | ISO 8601 time and a safe reference for reconciliation |

Exclude tokens, names, email addresses, raw payloads, and full MAC addresses.
The durable sink, retention, failure recovery, and attribution mechanism remain blocked by G4.
