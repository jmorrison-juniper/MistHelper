# Data Model: Declared ArangoDB indexes

## Unchanged stored records

The strategy catalog remains read-only.
The repair changes no record field, primary key, `_key`, metadata value, or import option.
The existing replacement import remains responsible for document updates.

## Process-local database scope

The registry key contains the configured server URL, database name, and account name.
It contains no password.
Each registry entry holds one reentrant guard and a mapping of collection names to confirmed fields.
It retains no SDK connection or collection handle.

## Field declaration

The writer reads `strategy.get("indexes", ())`.
A missing or empty list means no secondary index.
A valid declaration is a list or tuple of non-empty strings.
The normalized tuple retains each field's text and first occurrence order.
Invalid declarations raise `ValueError` before a database mutation.

## Confirmation transitions

| State | Event | Next state |
| - | - | - |
| No confirmed fields | All declared requests succeed | Confirm the complete declared set |
| No confirmed fields | Any request fails | Retain no confirmation and propagate the error |
| Earlier confirmed fields | All new requests succeed | Retain earlier fields and confirm the extension |
| Earlier confirmed fields | Any new request fails | Retain earlier fields only and propagate the error |
| Any confirmation | The writer creates a new collection with that name | Clear the old confirmation before the new check |
| Any confirmation | A list reorders or removes fields | Preserve server indexes and send no request for confirmed fields |

The database can retain an index from a partially completed check.
The process does not confirm that check.
A retry requests the unconfirmed fields again.
The database returns an equal existing index without duplication.

## Concurrency boundary

The guard covers the collection existence check, optional creation, live handle retrieval, and index confirmation.
Document preparation and import remain outside this guard.
That boundary prevents duplicate initial schema work without changing the existing document import behavior.
