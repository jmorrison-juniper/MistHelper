# Data Model: Migrate Mist Guest Authorizations

## Entities

| Entity | Natural key | Fields | Source |
| --- | --- | --- | --- |
| Operator reference | Identity from D-11 | Opaque subject reference. No name or email is stored. | Identity method (pending D-11) |
| Permission scope | Organization, site, WLAN, and action | Allowed actions for one site and one WLAN | Organization and site reads (R-107, R-109) and portal policy |
| Guest authorization | Site, WLAN, and normalized MAC address | Returned fields only: authorized, minutes, expiry, company, email, and field1 to field3. The MAC address appears masked in tables. | Site guest list (R-94). `field4` is never written (D-6). |
| Action journal entry | Internal action identifier, with a scope lock on site, WLAN, and MAC | Operation, site, WLAN, normalized MAC, reviewed-content hash, state, reconciliation result, cloud outcome, audit outcome, and timestamps | `ActionJournal` in the ArangoDB collection `guest_authorization_actions` |
| Audit event | Internal event identifier | Operator reference, site, WLAN, masked MAC, operation, cloud outcome, audit outcome, and timestamp | `AuditRecorder` in the ArangoDB collection `audit_logs` |
| Import batch | Reviewed-content hash | Sanitized file name, byte count, row count, header result, and batch state | `CsvImportParser` |
| Import row | Batch hash and row number | Row number, normalized MAC address, minutes, optional fields, validation result, and row state | `CsvImportParser` |

## Validation rules

- MAC address: accept colon, hyphen, and dotted forms. Normalize to lowercase colon form. Reject malformed, all-zero, broadcast, and multicast values (TC-001 and TC-002).
- Minutes: an integer from 1 to 259200 (TC-004 and TC-005). Import rows reject a missing value. No default applies (TC-020).
- Typed word: an exact, case-sensitive match for the operation word (TC-006).
- Reviewed-content hash: a SHA-256 digest over the reviewed fields. A mismatch refuses the write before any call (TC-007).
- Text fields: company, field1, field2, and field3 accept at most 128 characters. Email accepts at most 254 characters and a valid address format (TC-003 and TC-008). These limits are MistHelper choices under D-8.

## State transitions

Journal entry:

1. `intent_recorded`: the entry exists and reads back. No Mist call has started.
2. `cloud_sent`: the single SDK write call has started.
3. `cloud_succeeded`, `cloud_failed`, or `cloud_unknown`: the write returned a result. A 2xx response gives `cloud_succeeded`. A 4xx response gives `cloud_failed`. A missing status gives `cloud_unknown`.
4. `reconciled`: a single read showed `ended`, `not_ended`, or `not_found`.
5. `audit_recorded` or `audit_failed`: the audit event was written or failed.

Later writes for the same scope refuse while any entry remains `cloud_sent`, `cloud_unknown`, or `audit_failed`.

Import row:

- `validated` or `rejected` after the preview.
- `running`, then `succeeded`, `failed`, or `unknown` during the run.
- `not_attempted` for every row after a stop rule (TC-043).

## Retention and recovery

- Journal and audit records have no automatic expiry (D-10).
- Warning: Deleting journal or audit records removes the only local evidence of Mist changes made by the portal.
- Backup unit: the named volume `misthelper-arangodb-data` (`compose.yml` lines 347 and 348, R-29).
- Restart recovery: entries in `cloud_sent` or `cloud_unknown` block writes. The operator reconciles each entry with one read before a new write runs.
- Logs and audit events hold masked MAC addresses only (FR-026). The journal alone keeps the full normalized address for reconciliation.
