# Data Model: Stale Portal Response Ownership

The feature uses transient page state only.

| Value | Meaning | Lifetime |
|-------|---------|----------|
| Requested menu number | The operation that started a parameter request | Until its response completes |
| Selected menu number | The operation that owns the visible panels | Until another operation is selected |
| Parameter response | The result or failure for one requested operation | Until its completion handler returns |

The page applies a response only when its requested menu number matches the selected menu number. The feature adds no stored record or data migration.
