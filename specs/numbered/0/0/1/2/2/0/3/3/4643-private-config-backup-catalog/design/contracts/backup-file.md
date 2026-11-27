# Contract: Backup File Format

## Location and Name

- Directory: `data/.cisco-config-converter-backups/`. The directory name is `BackupDirectory.NAME` (D-1).
- File name: `<backup_id>.json`. The identifier has 32 lowercase hexadecimal characters (FR-006).
- Creation: exclusive creation with `os.open` and the flags `O_WRONLY`, `O_CREAT`, and `O_EXCL`. The mode is 0600 on POSIX (FR-002).
- Encoding: UTF-8 JSON. The document holds one top-level object and no content after it.

## Document Fields

| Key | Type | Rule |
| --- | --- | --- |
| `schema_version` | integer | `1`. |
| `object_family` | string | `service-policy`, `service`, or `network`. |
| `organization_id` | string | Canonical UUID string. |
| `captured_at` | string | UTC timestamp with `+00:00`. |
| `page_limit` | integer | `1000`. |
| `reported_total` | integer | Value of `X-Page-Total`, zero or greater. |
| `pagination_complete` | boolean | `true` only when the captured count equals `reported_total`. |
| `object_count` | integer | Equals `reported_total` and the length of `objects`. |
| `object_digests` | object | Mist object ID to SHA-256 hex digest. |
| `relationships` | array | Each item holds `from_id`, `target_name`, `relation`, and `key_type`. |
| `objects` | array | Complete Mist objects, sorted by `id`. |
| `seal` | string | HMAC-SHA256 hex value over the document without the `seal` key. |

Warning: the `objects` array holds complete settings. The file can hold secret-bearing fields. Keep the file private, and never send it to a browser response or a log (FR-019, FR-024).

## Canonical Form

- Serialization for hashing: `json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)`.
- Object digest: SHA-256 hex over the UTF-8 bytes of the canonical form of one complete object. Issue 4636 `CanonicalDigest` provides this form.
- Seal: HMAC-SHA256 hex over the UTF-8 bytes of the canonical form of the document without `seal`. Issue 4636 `RecordSeal` provides the key derivation from `PORTAL_SECRET_KEY`. This change reuses that derivation unchanged.
- The seal key comes from the `PORTAL_SECRET_KEY` environment variable. It never comes from the portal configuration value `secret_key`, because that value falls back to a random value at each start (R-31).

## Read Rules

The catalog applies these checks in order. The first failed check sets the exclusion reason (data model, section Exclusions).

1. The file name matches the identifier pattern. A failure gives `name-mismatch`.
2. The file size is at most 134217728 bytes. A larger file gives `oversize`. The size check runs before any read.
3. The content parses as JSON. A parse error gives `corrupt-json`.
4. The parser refuses duplicate keys. A duplicate gives `duplicate-key`.
5. The parser refuses `NaN`, `Infinity`, and `-Infinity`. Such a value gives `non-finite-number`.
6. `schema_version` equals `1`. Another value gives `schema-version`.
7. `organization_id` equals the requested organization. Another value gives `organization-mismatch`.
8. `object_family` equals the requested family. Another value gives `family-mismatch`.
9. `pagination_complete` is `true`, and `object_count` equals `reported_total` and the length of `objects`. A failure gives `incomplete-pagination`.
10. Each object digest equals the digest of its object. A failure gives `digest-mismatch`.
11. Each relationship target resolves to one captured object of the target family. A failure gives `unresolved-relationship`.
12. The seal equals the recomputed HMAC-SHA256 value. A failure gives `seal-mismatch`.

## Write Rules

1. The writer refuses before any file exists when the seal key is empty (`StateRefused`, FR-014).
2. The writer refuses before any file exists when the directory check fails (`PersistenceUnavailable`, FR-005).
3. The writer builds the document, computes each object digest, computes the seal, and writes the canonical form.
4. The writer flushes the file and calls `os.fsync`.
5. The writer reads the file back and runs the twelve read checks. The result is a success only when every check passes (FR-015).

Caution: a failed read-back keeps the file on disk. The catalog excludes that file with its reason. The writer reports the failure, and no automatic deletion runs (D-14).

## Test Mapping

| Test | Rule |
| --- | --- |
| `test_writer_creates_exclusive_opaque_file_and_never_overwrites` | Name, mode, exclusive creation |
| `test_writer_reports_success_only_after_readback_matches` | Write rule 5 |
| `test_writer_refuses_without_seal_key_and_creates_no_file` | Write rule 1 |
| `test_writer_keeps_unverified_file_and_logs_without_bodies` | Caution about the kept file |
| `test_catalog_lists_only_verified_matching_entries` | Rules 1, 7, 8 |
| `test_catalog_refuses_corrupt_or_oversize_files_before_content_use` | Rules 2 to 5 |
| `test_catalog_refuses_tampered_or_incomplete_backup_files` | Rules 9 to 12 |
