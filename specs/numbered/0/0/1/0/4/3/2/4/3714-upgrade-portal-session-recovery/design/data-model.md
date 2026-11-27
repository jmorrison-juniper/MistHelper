# Data Model: Upgrade Portal Session Recovery

This feature adds one persisted entity, the store record. The other entities already exist in memory. They appear here only to define the keys and the transitions.

## Entities

### E-1 Operator session (existing, in memory)

- **Source**: `OperatorSession` (`src/interfaces/portals/upgrade_portal/runtime/identity.py:469`).
- **Fields**: `owner` (E-2), `cloud_session` (a `mistapi.APISession` reference), `credential_mode` (E-5), `created_at` (UTC), `selected_site_ids` (tuple of site identifiers).
- **Persistence**: none. The registry holds the record in one process (`identity.py:516`). The store record (E-3) is the only persisted copy.
- **Rule**: The record holds no password and no API token (`identity.py:470` to `477`).

### E-2 Owner (existing, in memory)

- **Source**: `SessionOwner` (`identity.py:389`).
- **Fields**: `actor_email` (the normalized email, or the token name for a token identity), `browser_id` (the first-party browser identifier), `identity_kind` (`email` or `token_name`, `identity.py:371`).
- **Natural key**: the owner key, built as `email digest:browser identifier` (`identity.py:457`). The signed cookie holds the owner key (`identity.py:727`).

### E-3 Store record (new, persisted)

- **Scope**: one record for each environment token session. Browser token and provider login sessions have no record (D-1, FR-009).
- **Natural key**: the store key, built as `misthelper:capture:session:` followed by the 64-character lowercase SHA-256 digest of the owner key (FR-003).
- **Value**: one Fernet token (ASCII text) that encrypts a UTF-8 JSON object. The object fields appear in `design/contracts/store-record.md`.
- **Lifetime**: the Redis key expires at the absolute deadline. The idle deadline lives inside the value.

### E-4 Lifetime window (new, inside E-3)

- **Fields**: `absolute_expires_at` and `idle_expires_at`, both UTC ISO 8601 text.
- **Rule**: The absolute deadline equals `created_at` plus `CAPTURE_SESSION_TTL_SECONDS`. The idle deadline equals the last refresh plus `CAPTURE_SESSION_IDLE_SECONDS`. The idle deadline never exceeds the absolute deadline.
- **Refresh**: The idle deadline moves forward at most once each 60 seconds (FR-013).

### E-5 Credential mode (existing enumeration)

- **Source**: `CredentialMode` (`identity.py:355`).
- **Values**: `environment_token`, `browser_token`, `provider_login`.
- **Use in this feature**: Only `environment_token` appears in E-3.

## Transitions

| From | Event | To | Effect on the store |
| - | - | - | - |
| Absent | Successful environment token sign-in | Active | Write E-3 with the TTL set to the absolute lifetime (FR-001) |
| Active | Protected request inside both deadlines, registry hit | Active | Refresh the idle deadline at most once each 60 seconds |
| Active | Protected request after a worker replacement, registry miss | Active (rebuilt) | Read E-3, decrypt it, validate the fields, and refresh the idle deadline |
| Active | Failed validation during recovery | Absent | Delete E-3 (FR-008, FR-024) |
| Active | Idle or absolute deadline passed | Absent | Delete E-3 on the next read (FR-008, FR-013) |
| Active | Sign-out | Absent | Delete E-3 once. A failed delete logs an error (FR-012) |
| Active | Second sign-in from the same browser | Active (replaced) | Overwrite E-3 for the same key |
| Absent | Store outage on read | Absent | Return 503 `session_store_unavailable`. No local session (FR-011) |
| Absent | Store outage on write during sign-in | Absent | Return 503 `session_store_unavailable`. No local session (FR-010) |

## Validation Rules for a Read

A read accepts a record only when every rule holds:

1. The key exists and the value decrypts with the active key or the previous key.
2. The `version` field equals 1.
3. The `mode` field equals `environment_token`.
4. The `browser_digest` field equals the SHA-256 digest of the current browser identifier.
5. The `identity_kind` field equals `token_name`.
6. The current time is earlier than `idle_expires_at` and earlier than `absolute_expires_at`.
7. The token name returned by `getSelf` after `login` equals the `identity` field.

A failed rule deletes the record and returns 401 `not_authenticated` (FR-008). A decrypt failure for an absent key also deletes the record.

## Natural Keys and Identifiers in Logs

- Logs use the first 12 characters of the owner key digest. They never use the full owner key.
- Logs use the first 12 characters of the browser digest. They never use the browser identifier.
- Logs never use the token value, the encryption key, or the cloud session.
