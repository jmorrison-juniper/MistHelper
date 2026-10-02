# Data Model: Canonical Corpus Documents

## Ownership and identity

`HarvestStateStore` owns schema version 2 and its transactions.
`PdfPathAllocator` owns the derived in-memory path and digest maps.
No other component writes an independent content index.

A corpus is one authorized output root and its existing state.
Resolve the root to its real absolute directory before cache use.
Resolve each cache path to its actual local file inside that root.
Use `pathlib.Path` for path operations on Windows, macOS, and Linux.
Reject traversal, outside-root paths, and symlink-dependent payload associations.
Do not share a payload across corpus roots.

The content identity is a full SHA256 digest within that corpus.
The URL identity remains the natural `root_url`.
The cache identity is the natural pair `(corpus_root, local_path)`.
Do not create an artificial document ID.
Do not select a canonical owner from the first URL row returned for a path.

## 1. URL record: `documents`

Keep the existing table and primary key.
Keep every existing column declaration, default, null rule, and permitted value.
The following mapping defines preservation, not a replacement schema.

| Existing field | Version 2 mapping and validation |
| --- | --- |
| `root_url` | Unchanged natural primary key. Preserve the source URL and one row per root. |
| `doc_type` | Preserve the existing document type and enum meaning. |
| `stage` | Preserve `discovered`, `resolved`, `downloaded`, `classified`, `failed`, `dropped`, and `no_pdf`. |
| `resolved_pdf_url` | Preserve the selected resolved URL. A changed response does not change this URL. |
| `category` | Preserve the individual URL record's category. It need not match the physical folder. |
| `sub_category` | Preserve the individual URL record's sub-category. |
| `is_fallback` | Preserve the existing flag and its representation. |
| `local_path` | Preserve the public path serialization. Successful association or relocation can update the canonical pointer. |
| `file_size` | Preserve existing null behavior. A verified complete association requires the actual positive byte count. |
| `error_reason` | Preserve error and drop semantics. Do not clear another alias's reason during pointer repair. |
| `updated_at` | Preserve the timestamp format. Use the existing update policy for a real record update. |

Add these two fields in version 2.
Add the corresponding optional fields to the existing document model.

| New field | Type | Null/default | Permitted values and origin |
| --- | --- | --- | --- |
| `content_sha256` | SQLite `TEXT`, model `str` or `None` | Nullable, default `NULL` | Exactly 64 lowercase hexadecimal characters after verified association. |
| `original_pdf_name` | SQLite `TEXT`, model `str` or `None` | Nullable, default `NULL` | Nonempty original PDF basename from authoritative source metadata or the resolved PDF URL. |

Capture `original_pdf_name` before local sanitization, collision suffixes, or classification placement.
Never derive it from a canonical filename or a collision-renamed legacy path.
Unknown names remain null.
Do not use the original name as a filesystem path without the existing input validation.

A nullable digest does not prove invalid content.
It means the row lacks trusted content evidence.
Legacy downloaded or classified rows retain their stage but cannot skip validation.
Non-payload rows retain their existing nullable file fields.
Do not fabricate a digest for failed, dropped, or unresolved records.

## 2. Validated file metadata: `content_cache`

Store this table in the existing corpus SQLite database.
Schema version 2 owns every field below.

| Field | SQLite type | Null/default | Permitted values |
| --- | --- | --- | --- |
| `corpus_root` | `TEXT` | Required, no default | Resolved absolute authorized corpus directory. |
| `local_path` | `TEXT` | Required, no default | Resolved absolute path of a complete regular file inside `corpus_root`. |
| `content_sha256` | `TEXT` | Required, no default | Full lowercase hexadecimal SHA256, exactly 64 characters. |
| `file_size` | `INTEGER` | Required, no default | Positive byte count equal to the validated file size. |
| `device` | `INTEGER` | Required, no default | Nonnegative device identity from the validated stat result. |
| `inode` | `INTEGER` | Required, no default | Nonnegative inode/file identity from the validated stat result. |
| `mtime_ns` | `INTEGER` | Required, no default | Exact signed nanosecond modification time. Do not round it. |
| `ctime_ns` | `INTEGER` | Required, no default | Exact signed nanosecond change time. Do not treat it as portable creation time. |

On Windows, read change time from native `FILE_BASIC_INFO`.
Do not use Python's Windows creation-time value as the change clock.
Use an open file handle and verify the native result.
If the filesystem lacks that capability, fail explicitly.
Require each identity value to fit a signed SQLite integer.

Use `(corpus_root, local_path)` as the composite primary key.
A digest is not a unique key for this table.
Pre-existing physical duplicates can have separate path entries.
A nonunique `(corpus_root, content_sha256)` SQLite index can support lookup within this same table.
It does not create a second persistent store.

Require values that SQLite and the host can represent reliably.
Reject missing or unreliable stat identity rather than granting an unsupported cached skip.
Zero-valued identity fields are not proof of reliability.
Do not store partial entries with null identity fields.

Persist only metadata.
Do not store bodies, PDF copies, samples, extracted text, pointer documents, or byte arrays.
Use the existing state retention scope.
No separate expiry policy or background cleanup is introduced.

## 3. Relationships and derived maps

Each complete URL row logically refers to:

1. Its expected `content_sha256`.
2. Its canonical `local_path`.
3. The cache entry for that real path under the configured corpus root.

Keep the current public `documents.local_path` representation.
Resolve it through the existing corpus path rules for cache lookup.
Do not bulk-rewrite unrelated path strings during migration.
The cache's absolute real path is an internal identity key, not a new manifest path format.

Multiple root rows can share one resolved URL.
Multiple resolved URLs can share one digest and canonical file.
Each root retains its own candidates, scores, stages, category, and source name.
Do not use a one-row-by-path lookup as ownership evidence.

The allocator derives these metadata-only maps:

| Map | Key | Value and lifetime |
| --- | --- | --- |
| Path metadata | Resolved local path under one root | Digest, five-field stat identity, and validation outcome. One allocator lifetime. |
| Content lookup | Full digest | Verified candidate paths and the selected canonical path. One allocator lifetime. |
| Discovery state | The allocator's corpus root | Whether its single discovery walk has completed. Never reset per document or move. |

Prefer an established valid canonical association.
If none exists, choose a stable normalized-path order among verified matching files.
If established legacy pointers conflict, use a verified state operation to align their canonical association.
Do not infer ownership from query order.
Do not delete the old duplicate files.

No new public document stage represents cache status.
`untrusted`, `verified`, `invalid`, and `pending persistence` describe internal evidence only.

## 4. File validation transitions

| Initial evidence | Action | Result |
| --- | --- | --- |
| Complete persisted cache and matching expected digest | Confirm containment, regular-file status, readability, and all five unchanged stat fields. | Trusted reuse without stored-body reads. |
| Missing or incomplete cache entry | Open the file and stream SHA256 with before/after identity checks. | Persist trusted metadata only after a stable valid read. |
| Changed stat identity | Stream and compare the current digest with the alias's expected digest. | Matching content can regain trust. Different content invalidates that association. |
| Missing expected path | Do not skip. Use verified recovery or report failure. | All aliases of that missing payload remain untrusted until repair. |
| Unreadable, empty, non-PDF, or unstable file | Reject the input explicitly. | No successful alias or completed receipt. |
| `.part` file | Exclude it from complete-file discovery and reuse. | Never canonical or successful resume evidence. |
| Cache persistence or verification failure | Stop the run with an explicit durable-state error. | No successful download or skip count. |

For hashing, compare both path and open-descriptor identities.
Read blocks of at most 1,048,576 bytes.
Check the existing `%PDF` prefix during the same streamed validation pass.
Reject an identity change before, during, or after that read.
Do not replace an expected digest with the digest of corrupted local bytes.

On an unchanged restart, load cache metadata and perform the single discovery walk.
Use metadata checks for unchanged files.
Do not read stored bodies for those files.
Readability checks may open a file without consuming its body.

## 5. Association and response transitions

| Event | Document updates | Physical and cache updates |
| --- | --- | --- |
| New unique valid response | Associate applicable roots with the verified path, digest, size, and their own original names. | Publish one complete payload, then persist its verified cache entry. |
| Equal valid response from another URL | Associate the new roots with the existing canonical path. Preserve their own metadata. | No payload write and no repeated hash of an unchanged stored file. |
| Saved valid URL repeat | Preserve its association and source history. | No fetch, payload write, or unchanged stored hash. |
| Verified recovery with the expected digest | Repair every corresponding alias path and size for that digest. | Install or reuse one valid canonical file and replace stale cache references. |
| Changed response for a resolved URL | Update all roots for that resolved URL to the new digest and path. | Publish or reuse the new digest. Keep other URLs' old-digest associations. |
| Required state failure after publication | Do not report the association as successful. Preserve explicit failure evidence. | A complete unassociated file may remain for later verified recovery. |

Pointer repair changes only association fields and normal update timestamps.
It does not merge root rows or replace category, candidate, score, stage, or reason history.
The runner applies each requested row's normal stage transition only after verified state completion.
Existing downloaded and classified rows still undergo resume validation.

## 6. Placement and classification transitions

The first canonical payload may move into its classification folder before later aliases attach.
Later aliases retain that canonical path, even when their categories differ.
Reclassification can retain the shared path and change only the intended alias's derived labels.

An authorized real move has these effects:

1. Validate the current canonical file and a safe destination.
2. Move the physical payload once without overwriting different content.
3. Validate the destination identity.
4. Commit every affected alias pointer and cache key through `HarvestStateStore`.
5. Refresh active in-memory references after verified persistence.

These are operation boundaries, not one oversized method.
Use bounded methods and grouped metadata values.
If the source equals the destination, retain the file and treat placement as a no-op.
If an occupied destination has different bytes, allocate another deterministic safe path.
A collision check must not delete a shared canonical source.

Manual sorting processes one group per real physical payload.
The group contains all aliases, not a selected owner row.
Preserve each alias's independent classification.
Repeated passes produce no extra moves, copies, or lost rows.

A physical move and a database commit cannot form one cross-system transaction.
On a failed update, use verified recovery or report failure.
Never report successful reuse of a stale path.

## 7. Schema lifecycle and old-to-new mapping

| Store state | Version 2 behavior |
| --- | --- |
| New empty store | Initialize version 2 and its required schema atomically. |
| Recognized version 1 | Verify a consistent backup, then migrate atomically. |
| Complete valid version 2 | Open without another migration or duplicate records. |
| Version 2 with missing cache rows | Treat those paths as untrusted and rebuild metadata through validation. |
| Version 2 with incompatible required schema | Fail explicitly. Do not silently repair an incompatible declaration. |
| Unknown, malformed, or newer version | Fail before schema or version writes. |
| Read-only dry run on version 1 | Read legacy records without migration, backup creation, or durable adoption. |

During migration:

- Retain the `documents` primary key and every old column value.
- Initialize both new nullable fields to null.
- Create an empty `content_cache`.
- Preserve every `pdf_candidates`, `content_scores`, `dropped_release_notes`, and `run_meta` record.
- Change only the existing schema-version value from 1 to 2.

Do not rebuild or reinterpret the unchanged tables.
Their field names, types, defaults, natural relationships, and row values remain the legacy contract.
Candidate choices, rejection reasons, scores, and stages keep their meaning.
Version 2 adds no column to those tables.

During explicit legacy adoption, validate the existing file locally.
Fill a missing digest only from stable valid bytes.
Fill an original name only from authoritative source metadata.
Keep the stage and unrelated metadata.
Do not fetch or delete historical files.

## 8. Backup, transaction, and recovery boundaries

Before version 1 migration, create a new backup with the SQLite backup API.
Do not overwrite an unrelated backup or copy only the main database file.
Verify the backup through a fresh connection.
Check integrity, version 1, schema, and all retained records, including committed WAL records.

Acquire the existing serialized writer boundary.
Begin one migration transaction and recheck the version.
Apply additive schema changes.
Verify old values and the new schema inside the transaction.
Update the version last, then commit.
Verify the committed result through an independent connection before opening the store for use.

Roll back any in-transaction failure.
If committed verification fails, stop and retain the verified version 1 backup.
Restore through the SQLite backup API only under explicit recovery authority with writers quiescent.
Do not restore over subsequent accepted version 2 writes.

Association, digest repair, and path relocation each use one state-store transaction.
Each transaction includes the required cache and affected root-row changes.
Read back the committed values before success.
If persistence cannot be verified, fail closed.

Version 1 executables are unsupported on version 2 state.
Do not claim that old writers enforce the new version guard.
Do not downgrade by editing the version value.
Use an authorized backup restoration for rollback.

## 9. Manifest and counter projections

The [storage contract](contracts/storage.md) defines the public JSON and CSV fields.
Both formats preserve one entry per root/source URL.
Unknown additive values remain null in JSON and empty in CSV.

Count documents, categories, stages, downloads, and skips by their documented URL/write semantics.
Count `total_bytes` once per valid referenced canonical real path.
Resolve equivalent path strings before counting.
Reject conflicting sizes or unverifiable complete references instead of guessing a total.
Exclude `.part` files and unassociated historical duplicates from the canonical inventory total.
Do not present that total as a measurement of all historical files on disk.

## Requirement coverage

| Model area | Requirements |
| --- | --- |
| Content and natural URL identity | FR-001 through FR-007 |
| Manifest projection and counters | FR-008, FR-017 |
| Validation and publication evidence | FR-009 through FR-014 |
| Placement, sorting, and dry run | FR-015, FR-016 |
| Bounded discovery and reads | FR-018 through FR-020 |
| Compatibility, migration, and recovery | FR-021 through FR-025 |
| Validation evidence and scope | FR-026 through FR-032, [quickstart.md](quickstart.md) |
