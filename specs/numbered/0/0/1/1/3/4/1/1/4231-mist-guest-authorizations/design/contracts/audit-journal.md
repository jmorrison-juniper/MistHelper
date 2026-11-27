# Contract: Action Journal and Audit Event

## Action journal entry

The collection is `guest_authorization_actions` in the existing `misthelper` ArangoDB database (D-9).

| Field | Type | Rule |
| --- | --- | --- |
| `_key` | string | Internal action identifier. Unique. |
| `operation` | string | One of `grant`, `change`, `extend`, `revoke`, or `import_row` |
| `site_id` | string | Mist site identifier |
| `wlan_id` | string | Mist WLAN identifier |
| `mac` | string | Normalized full MAC address. Used only for reconciliation and the scope lock. Never logged and never shown in tables (FR-026, D-15). |
| `reviewed_hash` | string | Hash shown in the review panel |
| `state` | string | One of `intent_recorded`, `cloud_sent`, `cloud_succeeded`, `cloud_failed`, `cloud_unknown`, `reconciled`, `audit_recorded`, or `audit_failed` |
| `reconciliation` | string | One of `ended`, `not_ended`, `not_found`, or `none` |
| `operator_ref` | string | Opaque operator reference from the identity method (D-11) |
| `created_at` and `updated_at` | string | UTC ISO 8601 time |

Writes read the entry back before the Mist call starts (TC-011). A scope lock covers the site, WLAN, and MAC address. Concurrent writes for the same lock wait or refuse (TC-011 to TC-013).

## Audit event

The collection is `audit_logs`, the same collection the upgrade portal audit logger uses (R-56).

| Field | Type | Rule |
| --- | --- | --- |
| `event_id` | string | Internal identifier. Unique. |
| `operator_ref` | string | Opaque operator reference |
| `site_id` | string | Mist site identifier |
| `wlan_id` | string | Mist WLAN identifier |
| `masked_mac` | string | Masked form only, for example `xx:xx:xx:xx:4f:2a`. Shows the last two octets. |
| `operation` | string | Same values as the journal |
| `cloud_outcome` | string | `succeeded`, `failed`, or `unknown` |
| `audit_outcome` | string | `recorded` or `failed` |
| `occurred_at` | string | UTC ISO 8601 time |

The audit event omits names, email addresses, field values, tokens, raw payloads, and full MAC addresses (FR-026, TC-014, TC-015).

## Failure rules

- A failed journal write refuses the change before any Mist call (FR-019).
- A failed audit write after a cloud success marks the journal entry `audit_failed`. Later writes for the same scope refuse until reconciliation (FR-020, TC-013).
- The application reports success only after the journal read-back succeeds (constitution lines 315 to 317).
