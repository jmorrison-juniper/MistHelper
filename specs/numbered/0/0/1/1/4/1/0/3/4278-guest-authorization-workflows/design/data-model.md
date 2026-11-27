# Data Model: Guest authorization workflows

**Record**: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows`

**Storage rule**: Mist stores each authorization record. The portal stores only intent rows, outcome rows, and batch summaries in `data/mist_data.db`. The portal stores no full MAC address and no personal field.

## 1. Entities and Natural Keys

| Entity | Attributes | Natural key | Storage |
| --- | --- | --- | --- |
| Scope | `organization_id`, `site_id`, `wlan_id`, `action` | `(organization_id, site_id, wlan_id)` | Memory only |
| Target | `normalized_mac` (12 lowercase hexadecimal characters), `masked_mac` | `(site_id, wlan_id, normalized_mac)` | Masked form only in storage |
| Authorization observation | `masked_mac`, `authorized` (true, false, or unknown), `expires_at` (UTC ISO 8601 or unknown) | Derived from the target key | Memory only |
| Review digest | SHA-256 of canonical JSON for action, scope, payload, and revision | Digest value | Memory only |
| Write intent | `operation_id`, `action`, `organization_id`, `site_id`, `wlan_id`, `masked_target`, `requested_minutes`, `operator_identity`, `intent_utc` | `operation_id` | SQLite table `guest_authorization_audit` |
| Write outcome | `outcome`, `http_status`, `outcome_utc`, `error_category` | Same row as the intent | SQLite table `guest_authorization_audit` |
| Import batch | `batch_id`, `file_sha256`, `byte_count`, `row_count`, `rows_sha256`, `state`, `created_utc` | `batch_id` | Memory and audit table reference |
| Import row | `row_number`, `site_id`, `wlan_id`, `masked_mac`, `minutes`, `writable_fields`, `validation`, `outcome` | `(batch_id, row_number)` | Memory and audit table reference |

**Why an artificial key exists**: The audit row stores the masked target only. A natural key that contains the full MAC address would store personal data. The `operation_id` value is a UUID version 4. It names one intent row. It is the only generated key in the store.

## 2. Write Request States

| From | Event | To | Rule |
| --- | --- | --- | --- |
| drafted | Operator opens review | reviewed | Scope and payload pass validation (D-5, D-7, D-8) |
| reviewed | Operator submits the typed word and digest | confirmed | Word matches the action. Digest matches the review (D-12) |
| reviewed | Cancel, wrong word, or changed digest | cancelled | No intent row and no call |
| confirmed | Intent row inserted | intent_recorded | In-flight check passes (D-16) |
| confirmed | Intent insert fails | cancelled | No call. Error category `audit_unavailable` (D-15) |
| intent_recorded | One SDK call returns a response | outcome_recorded | Outcome is `succeeded`, `failed`, or `rejected` |
| intent_recorded | SDK returns HTTP 429 after its retries | outcome_recorded | Outcome is `rate_limited` and the batch stops (D-15) |
| intent_recorded | Timeout, connection error, server error, or no response | outcome_recorded | Outcome is `unknown`. No retry (D-15) |
| intent_recorded | Outcome insert fails | audit_failed | The cloud result is reported with the audit failure. Later writes stop (D-15) |
| intent_recorded without outcome | Portal restarts | open_intent | The intent stays visible. The in-flight check blocks a new write to the same target until review (D-14, D-16) |

## 3. Import Batch States

| From | Event | To | Rule |
| --- | --- | --- | --- |
| (none) | File upload accepted | previewed | At most 262144 bytes and 200 data rows (D-13) |
| previewed | Typed word IMPORT and matching digest | confirmed | `rows_sha256` matches the reviewed rows |
| confirmed | Run starts | running | Rows run one at a time (FR-023) |
| running | Each row finishes | running | One outcome for the row |
| running | Rate limit, unknown outcome, or audit failure | stopped | Later rows become `not_attempted` (FR-024) |
| running | Last row finishes | completed | Every row has one outcome |

## 4. Relationships

- One scope has many targets.
- One target has at most one open intent at a time (D-16).
- One write intent has one outcome row. The outcome can be missing only in `open_intent`.
- One import batch has many import rows. Each import row can produce one write intent when it runs.

## 5. Field Rules

- `normalized_mac` accepts 12 hexadecimal characters after removing `:` and `-`. Other values reject (TEST-021).
- `masked_mac` shows `xx:xx:xx:xx:AA:BB`, where `AA:BB` are the last two octets (R063, R064).
- `minutes` is an integer from 1 through 259200 for a grant. Zero rejects (D-8).
- `authorized` is true, false, or unknown. A missing value is unknown. It never becomes false or true (FR-007).
- `expires_at` is a UTC ISO 8601 string or unknown. A missing timestamp is unknown (R064).
- `operator_identity` comes from the trusted header under D-4. A missing or untrusted identity rejects the request.
- Log lines never include `normalized_mac`, `name`, `email`, field values, tokens, or passwords (FR-025, D-17).

## 6. Not Applicable Parts

- The feature stores no export file. The export boundary rule does not apply.
- The feature adds no menu and no primary-key strategy entry for a menu operation.
