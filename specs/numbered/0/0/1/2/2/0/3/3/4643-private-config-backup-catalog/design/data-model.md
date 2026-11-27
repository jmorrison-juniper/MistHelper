# Data Model: Private Configuration Backup and Verified Catalog

This model defines the private backup records. It extends the state package records of issue 4636. No database stores these records. Each backup is one sealed JSON file under `data/.cisco-config-converter-backups/`.

## Conventions

- Each timestamp uses UTC with the explicit offset `+00:00`. A naive timestamp is refused (issue 4636, FR-008).
- A backup ID is 32 lowercase hexadecimal characters from `uuid4`. A client never chooses a backup ID.
- An organization ID is a canonical UUID string. The value is `str(UUID(value))` after validation.
- An object ID is a Mist natural ID. A name is a display hint only.
- A digest is the SHA-256 hex value of the canonical JSON form. The canonical form uses sorted keys, the separators `,` and `:`, and `allow_nan=False`. Issue 4636 `CanonicalDigest` implements this form (`ReviewState.digest` in `models.py`, line 88, R-11).
- A seal is the HMAC-SHA256 hex value of the canonical JSON of the document without the `seal` field. The key comes from the `PORTAL_SECRET_KEY` environment variable only (D-8).

## Entities

### BackupDirectory

Natural key: the directory path under the data directory.

| Attribute | Value or rule |
| --- | --- |
| `NAME` | `.cisco-config-converter-backups` |
| Owner | The current account, on POSIX and on Windows |
| Mode | 0700 on POSIX. No group or other access. |
| Windows ACL | Access only for the current account, SYSTEM, and local Administrators |
| Links | No symbolic link and no reparse point |

### BackupFile

Natural key: `backup_id`. The file name is `<backup_id>.json`.

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | integer | `1` in this change. |
| `object_family` | string | One of `service-policy`, `service`, or `network`. |
| `organization_id` | string | Canonical UUID string. |
| `captured_at` | string | UTC timestamp with `+00:00`. |
| `page_limit` | integer | `1000` in this change. |
| `reported_total` | integer | The value of `X-Page-Total` on each page. Zero or greater. |
| `pagination_complete` | boolean | `true` only when the captured count equals `reported_total`. |
| `object_count` | integer | Equals `reported_total` and the length of `objects`. |
| `object_digests` | object | Each Mist object ID maps to one digest. |
| `relationships` | list | Each item holds `from_id`, `target_name`, `relation`, and `key_type`. |
| `objects` | list | The complete Mist objects, sorted by `id`. |
| `seal` | string | HMAC-SHA256 hex value of the canonical document without `seal`. |

Rules for a file:

- Each object ID appears once. A repeated ID refuses the capture (FR-008).
- Each `from_id` appears in `object_digests`.
- Each relationship target name matches exactly one captured object in the target family, or the capture refuses (FR-013).
- A relationship key type is `name` in this change.

### BackupObject

Natural key: the Mist object `id` within one organization and one object family.

| Attribute | Rule |
| --- | --- |
| `id` | The Mist object ID from the list response. |
| `digest` | SHA-256 of the canonical form of the complete object. |
| `body` | The complete object. The file stores it in `objects`. |

### BackupRelationship

Natural key: the tuple `from_id`, `relation`, and `target_name`.

The table below lists the relationship sources that the schemas declare. Each row names a remote check in `design/research.md`.

| Family | Relation | Source property | Target family | Key type | Status |
| --- | --- | --- | --- | --- | --- |
| `network` | `routed-network` | `routed_for_networks` (R-52) | `network` | `name` | Source verified in the schema. Live values unverified (U-05). |
| `service-policy` | `service` | `services` (R-53) | `service`, or a group name | `name` | Source verified. The target includes groups, so the target family is unverified (U-03). |
| `service-policy` | `tenant` | `tenants` (R-54) | Unverified | `name` | Source verified. The target family is unverified (U-03). |
| `network` | none | `tenants` (R-74) | Not a relationship | Not applicable | The property holds address mappings. No relationship is recorded. |
| `service` | none verified | Not read beyond `id` (R-55) | Unverified | Not applicable | Reference fields for this family are unverified (U-03). |

Caution: the capture refuses each family whose relationship rows are unverified. Do not enable a family before issue 4634 records its rows.

### CatalogEntry

Natural key: `backup_id`. The catalog returns entries only for verified files.

| Field | Rule |
| --- | --- |
| `backup_id` | The backup ID from the file name. |
| `object_family` | The family from the verified file. |
| `captured_at` | The UTC capture time from the verified file. |
| `object_count` | The verified object count. |
| `verified` | `true`. |

The catalog returns no object body, no digest, no relationship, and no seal (FR-018).

## Exclusions

The catalog counts each excluded file under one reason. A reason is a fixed text value.

| Reason | Cause |
| --- | --- |
| `name-mismatch` | The file name fails the identifier pattern. |
| `oversize` | The file is larger than 134217728 bytes. The check runs before the read. |
| `unreadable` | The private-access check or the read fails. |
| `corrupt-json` | The content does not parse as JSON. |
| `duplicate-key` | The content repeats one key in an object. |
| `non-finite-number` | The content holds `NaN` or an infinite number. |
| `schema-version` | The schema version is not `1`. |
| `organization-mismatch` | The organization ID differs from the request. |
| `family-mismatch` | The object family differs from the request. |
| `incomplete-pagination` | The pagination flag is false, or the count differs from the reported total. |
| `digest-mismatch` | An object body does not match its digest. |
| `seal-mismatch` | The HMAC-SHA256 seal does not match. |
| `unresolved-relationship` | A relationship target does not resolve inside the file. |

## State Transitions

```text
absent -> written-unverified        exclusive creation and write
written-unverified -> verified      read-back recomputes every check
written-unverified -> unverified-kept   read-back fails. The file stays on disk.
verified -> verified                catalog reads leave the file unchanged
```

Rules for transitions:

- A file in `unverified-kept` never appears in the catalog.
- A file in `verified` appears in the catalog only for a matching organization and family.
- This change has no deletion state. Deletion is out of scope (FR-021).
- A capture that refuses writes no file. The state of such a capture is `absent`.

Not applicable: operation records. Issue 4636 `OperationRecord.backup_ids` stores backup IDs from this model. No code in this change writes an operation record.

## Catalog Result

The catalog returns two values:

| Value | Content |
| --- | --- |
| `entries` | A list of `CatalogEntry` values. |
| `exclusions` | A mapping from each reason in the table above to a count. |

The result holds no file path, no body, and no seal.
