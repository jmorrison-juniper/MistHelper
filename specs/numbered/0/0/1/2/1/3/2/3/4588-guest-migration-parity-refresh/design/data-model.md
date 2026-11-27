# Guest data and state model

This model is proposed. It is not a delivered schema. Requirements are in the [spec](../spec.md). API evidence is in the [SDK contract](contracts/api.md). Decisions are in the [decision register](research.md#7-decision-register).

## Identities and permitted fields

| Entity | Identity and fields | Validation and privacy |
| --- | --- | --- |
| Scope | Operator reference, organization ID, site ID, WLAN ID, and revision. | Validate UUIDs, the permitted organization, site membership, WLAN assignment, and the current revision. D-6 defines the operator reference. |
| Authorization observation | Exact scope, normalized MAC, observed authorization state, expiry time, observation time, and permitted fields. | Missing values stay unknown. A display name never selects a scope. D-9 removes read-only fields from writes. |
| Offline projection | Masked MAC, explicit `authorized` value, and UTC expiry or null. The shape matches T01. | Keep the exact three-key shape. The projection is not an editable identity or a database key. |
| Reviewed change | Operation reference, exact scope and MAC, action, supported payload, observation revision, and confirmation digest. | Bind to the reviewed actor and payload. Reject a stale, wrong, reused, or canceled confirmation. |
| Import batch | Batch reference, file digest, scope map revision, normalized rows, duplicate dispositions, and the D-11 limits. | Record each row. Do not store the raw private CSV beyond the approved retention. |
| Audit record | Operation reference, sequence number, UTC time, approved actor reference, action, scope reference, and dispatch or result category. | D-12 defines retention and fields. Never store a token, a credential, or a full personal payload. |

Use `(organization_id, site_id, wlan_id, normalized_mac)` as the natural identity for an authorization record. The API schema provides the WLAN identity through `wlan_id` (T11).

Warning: never use the masked MAC as an identity. Two devices can share the visible suffix. A wrong identity can change the wrong device.

## State transitions

Review state: `unavailable` moves to `loading`, then to `ready`, `empty`, `denied`, `failed`, or `stale`. A scope change moves every record, dialog, mapping, and confirmation to `stale`.

Authorization observation: `authorized` is `true`, `false`, or unknown. Expiry is observed, absent, or invalid. A time value alone never replaces a missing authorization value. The source uses expiry alone for its status badges (S03 L1149 to L1150). The target must document any approved deviation.

Change: `draft` moves to `validated`, then to `reviewed`, `confirmed`, `intent_recorded`, and `dispatched`. Dispatch ends as `success`, `rejected`, `unknown`, or `reconciliation_required`.

- A failure before dispatch leaves the change `unstarted`.
- An ambiguous dispatch never repeats the write automatically.
- A change is successful only after the exact-scope read matches the request.

Warning: a grant or revoke changes device access in the cloud. Recovery must not repeat or reverse a cloud operation without a new confirmation.

CSV row: `parsed` moves to `invalid` or `resolved`, then to `reviewed`, `confirmed`, `unstarted` or `dispatched`, and finally to `success`, `rejected`, or `unknown`. The final accounting partitions every input row. A canceled batch stops only unstarted rows. It cannot undo a cloud result that already exists.

## Shared persistence design (D-12)

- The source keeps no durable guest data. It reads guest records from Mist on each request (S02 L399 to L423). No source database migration is needed.
- Mist remains the authority for authorization records.
- The target stores durable intent and outcome records in the SQLite store `data/mist_data.db` (T17 L309 to L353).
- Write intent before each dispatch. Write the outcome after the observed result.
- Use one writer lock for each batch. Test the lock under the web workers before any write (T030).
- Redis may hold short-lived coordination keys only. Redis data never becomes the authoritative record or the only audit record.
- Namespaced keys include the feature name, organization, site, WLAN, and operation or revision.
- Never delete a record automatically. Manual deletion needs a typed confirmation (D-12, D-14).
- Backups hold the complete approved operational shape. A restore does not overwrite unrelated application data.
- Tests use `tmp_path` or isolated in-memory fixtures. Tests never use a production store.

## Input contracts

- The API contract controls the accepted MAC formats, the integer duration bounds, and the writable fields (api.md).
- Email and sponsor fields need approved format and length checks.
- The CSV file accepts the ten declared headers only (S01 L293 to L303). Reject any other header (D-11).
- Quoted commas, escaped quotes, embedded newlines, BOM, and CRLF need deterministic parser tests (TEST-016).
- Duplicate names, equal SSIDs, duplicate MAC identities, and conflicting values need an explicit ID selection or a rejection (D-11).
- Unknown fields, malformed rows, invalid numbers, and excessive input never default silently (P046).
- Render every external string as text. Neutralize spreadsheet formula text in each CSV output.
