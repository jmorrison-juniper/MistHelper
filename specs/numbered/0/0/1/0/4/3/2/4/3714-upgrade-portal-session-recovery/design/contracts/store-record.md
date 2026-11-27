# Contract: Session Store Record

This contract defines the key, the value, and the payload of one store record. The store holds one record for each environment token session.

## Key

- Prefix: `misthelper:capture:session:`.
- Suffix: the 64-character lowercase hexadecimal SHA-256 digest of the owner key (the UTF-8 text `email digest:browser identifier`).
- The raw owner key never appears in the key name (FR-003).

## Value

- The value is one Fernet token as ASCII text.
- The token encrypts one UTF-8 JSON object with the fields listed below.
- The encryption uses `MultiFernet`. The first key in the key set encrypts each write. Every key in the set can decrypt a read (FR-004).
- The key set contains `CAPTURE_SESSION_ENCRYPTION_KEY`, followed by `CAPTURE_SESSION_ENCRYPTION_KEY_PREVIOUS` when that variable holds a value.

## Payload Fields

| Field | Type | Rule |
| - | - | - |
| `version` | integer | Equals 1 in this contract |
| `mode` | text | Equals `environment_token` in this contract |
| `identity_kind` | text | Equals `token_name` in this contract |
| `identity` | text | The token name that `getSelf` returns after `login` |
| `browser_digest` | text | The 64-character lowercase SHA-256 digest of the browser identifier |
| `host` | text | The cloud host name from the approved catalog (`auth.py:263` resolves it) |
| `created_at` | text | UTC time in ISO 8601 form |
| `absolute_expires_at` | text | UTC time in ISO 8601 form. Equals `created_at` plus the absolute lifetime |
| `idle_expires_at` | text | UTC time in ISO 8601 form. Moves forward at most once each 60 seconds |

The payload holds no password, no API token, no cloud session object, no email address, and no organization identifier (D-4, D-7).

## Operations

| Operation | Redis command | Rule |
| - | - | - |
| Write | `SET key value EX seconds` | `seconds` equals the remaining time to `absolute_expires_at`. A false or failed reply raises the unavailable error. |
| Read | `GET key` | A missing key means no record. A value that fails to decrypt is treated as an invalid record and deleted. |
| Refresh | `SET key value EX seconds` | Runs at most once each 60 seconds for each session. Keeps the same absolute deadline. |
| Delete | `DEL key` | Runs once for each sign-out or validation failure. A failed delete logs an error. |

## Failure Rules

- A write that does not return success fails the sign-in. No session registers (FR-010).
- A read that cannot reach the store returns the unavailable error. No session registers (FR-011).
- A refresh that fails keeps the local session. The stored idle deadline stays earlier than the local deadline (edge case in spec.md).

## Logging Rule

- A log line names an operation and the first 12 characters of the owner key digest.
- A log line never names the token value, the encryption key, the Fernet token, or the decrypted payload.
