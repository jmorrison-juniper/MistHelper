# Data model

The [specification](../spec.md) defines the exact ordered key columns.
Request site, scope, scope ID, metric, and classifier identify the selected resource.
Response start and end identify the returned window, including server-selected default windows.

The shared identity helper validates complete nonempty identifiers and finite nonnegative window boundaries.
End must not precede start.
Canonical numeric boundaries produce equal identities for equivalent integer and floating-point timestamps.
A SHA-256 digest of the ordered JSON identity values supplies an Arango-safe key.

SQLite stores the same digest in `misthelper_sle_window_key` for new writes.
The unique index replaces only a new record with the same complete identity.
An existing auto-increment table retains its surrogate primary key.
Legacy rows keep NULL for the added identity column.
No old row is copied, updated, or deleted.

Arango retains every existing UUID document.
New keyed documents replace only a matching deterministic key.
CSV rows gain request identifiers but no SQLite-only identity column.
