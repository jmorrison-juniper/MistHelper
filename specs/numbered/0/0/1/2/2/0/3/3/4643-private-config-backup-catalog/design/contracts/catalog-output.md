# Contract: Catalog Output

## Method

`BackupCatalog.entries` accepts an organization ID and an object family. It returns two values: `entries` and `exclusions`.

## Input Rules

- The organization ID must be a canonical UUID string. Another value raises `StateRefused` before any file is opened (FR-016).
- The object family must be one of `service-policy`, `service`, or `network`. Another value raises `StateRefused` before any file is opened (FR-010).
- The directory check runs before the scan. A refused directory check raises `PersistenceUnavailable` (FR-005).

## Output Rules

`entries` is a list. Each item holds exactly these keys:

| Key | Type | Source |
| --- | --- | --- |
| `backup_id` | string | The file name without `.json`. |
| `object_family` | string | The verified document. |
| `captured_at` | string | The verified document. |
| `object_count` | integer | The verified document. |
| `verified` | boolean | `true` for every entry. |

`exclusions` is a mapping. Each key is one reason from the data model, section Exclusions. Each value is a count.

The output never holds any of these values: an object body, a digest, a relationship, a seal, a file path, or a source text (FR-018). A test checks the set of keys (`test_catalog_returns_only_allowlisted_metadata`).

## Logging Rules

- Before the scan, the catalog logs the action and the requested family at the `info` level.
- After the scan, the catalog logs the entry count and each non-zero exclusion count at the `debug` level.
- A refusal logs the reason name and the backup ID. The log never names an object or a value from an object (FR-024).

## Surface Rules

- The catalog has no route, no template, no static asset, and no menu entry (FR-019, D-10).
- The catalog runs only inside the converter package. No caller in this change invokes it outside the tests (D-17).
- Issue 4636 approves any future operator view before it exists (FR-018 of the issue 4636 draft).
