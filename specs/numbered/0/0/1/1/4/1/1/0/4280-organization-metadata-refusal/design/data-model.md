# Data Model: Organization metadata refusal

No persistent schema changes.

| Input | Accepted shape | Failure result |
| --- | --- | --- |
| HTTP status | Integer from 200 through 299 | `Unknown` and a warning |
| Metadata | Dictionary without an `error` field | `Unknown` and a warning |
| Name | Nonblank string | `Unknown` and a warning |
| Request failure | `OSError` or `RuntimeError` | `Unknown` and an error |

The returned valid name remains unchanged, including surrounding spaces.
The export stores it in the existing `metadata.source_org_name` field.
The logger records neither the metadata nor the returned name.
