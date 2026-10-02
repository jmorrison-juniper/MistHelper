# Storage Contract: Canonical Corpus Documents

**Status**: Design contract for schema version 2. Not implemented or accepted by this planning stage.

This contract covers local payloads, the existing state store, downloader results, and both inventory formats.
It does not add a network API, a CLI command, or another persistent index.
Field definitions are in [data-model.md](../data-model.md).
Validation commands are in [quickstart.md](../quickstart.md).

## 1. Scope and invariants

- Keep one selected canonical complete payload per SHA256 within one resolved corpus root.
- Keep one document row and manifest entry per natural `root_url`.
- Preserve source URLs, resolved URLs, candidates, scores, stages, labels, flags, timestamps, and reasons.
- Use complete original PDF bytes. Keep the existing `%PDF` prefix validation.
- Do not introduce artificial IDs, pointer PDFs, symlinks, copies, conversion, or document-body fields.
- Do not change crawl scope, URL selection, parser dependencies, or release-note selection.
- Do not delete or consolidate pre-existing physical duplicates as historical cleanup.

The operating model remains the existing serialized writer.
Coordinated independent concurrent writers are outside this feature.
Validate paths and destination occupancy even under that model.
Never overwrite different complete bytes.

## 2. `CorpusDownloader.download_document` result

Keep the four-item result:

`(downloaded|skipped|failed, path, size, reason)`

| Result | Required evidence | Counter meaning |
| --- | --- | --- |
| `downloaded` | A new complete payload was published. Its file and required durable association were verified. | One successful physical payload publication. |
| `skipped` | A valid canonical payload was reused. Its required durable association was verified. | One successful reuse, with or without a fetch. |
| `failed` | The document operation failed explicitly. The reason identifies the failing boundary without secrets or body data. | No successful download or skip. |

Successful results return the current canonical path and its positive byte size.
Keep the current path type and failure path/size conventions.
The path must not refer to a `.part` file.
Keep existing reason semantics for normal outcomes.
Add clear reasons for new validation failures.

A required durable-state failure is fatal to the run.
It must reach the runner as an explicit failure or exception.
The runner must stop, not replace its state store with an optional in-memory mode.
Do not increment successful counters before verified durable completion.

## 3. Request sequence

### Saved resolved URL

1. Find the persisted association for the resolved URL and applicable roots.
2. Validate its expected digest and canonical path.
3. If the association is valid, preserve or register the requesting root's alias.
4. Verify the required durable association.
5. Return `skipped` without a document fetch or payload write.

Do not treat the stage or URL alone as proof.
The runner must validate downloaded and classified rows during resume.
Different roots for the same resolved URL remain independent rows.

### Unknown or unvalidated resolved URL

1. Fetch one response through the existing `fetch_bytes` client.
2. Apply the existing prefix validation and calculate one full SHA256.
3. Look up that digest before name allocation.
4. Validate and reuse a matching canonical file, or select a safe new path.
5. Publish when needed, then verify the required state transaction.

An equal response from an unknown URL returns `skipped` after its fetch.
It saves the next payload write, not that HTTP transfer.
Every fetched response needs its own digest, even for a previously known URL.

The client still holds one complete HTTP body in memory.
Metadata and stored-file hashing must not add a whole-corpus body load.
Do not retain a second complete payload copy for comparison.

## 4. Content lookup and path allocation

`PdfPathAllocator` owns the in-memory metadata maps and one discovery walk.
Reuse that allocator for the runner's whole operation.
Path consumers must not create a discovery-capable allocator for each document.
Moves and new downloads update the maps directly.

Exclude `.part` files from complete-file discovery.
Use the existing naming, sanitization, URL-hash suffix, and deterministic variant policy.
Inspect occupied paths through validated metadata or a bounded streamed read.
Filename or URL ownership does not establish byte equality.

Prefer a valid established canonical association.
Otherwise select a verified candidate through stable normalized-path ordering.
If invalid or ambiguous references cannot be repaired, report an explicit failure.
Do not select an owner through a one-row-by-path query.

Different-byte collisions retain both complete payloads.
A changed response for the same URL must not overwrite the old payload.
If its URL-hash variant is occupied, select another deterministic safe variant.

## 5. Trusted file validation

The complete cache entry must match:

- The resolved corpus root and actual local path.
- The alias's expected full SHA256.
- `file_size`, `device`, `inode`, `mtime_ns`, and `ctime_ns`.

Confirm a regular readable complete file.
Check path containment and the open descriptor's identity.
An unchanged complete entry permits reuse without reading stored body bytes.
This rule applies after restart.

If the identity changed or the entry is absent, stream SHA256 in blocks of at most 1,048,576 bytes.
Verify the prefix and compare identity before and after the read.
A stable matching digest can restore trust.
An unstable file, read error, or mismatching expected digest cannot authorize reuse.

Explicitly reject missing, empty, non-PDF, unreadable, replaced, or changing expected paths.
Detect same-size changes when modification time was restored.
Use change time, device, and inode as required identity fields.
Do not weaken validation when a host lacks reliable identity.

On Windows, obtain change time through `GetFileInformationByHandleEx` with `FILE_BASIC_INFO`.
Python's Windows creation time cannot detect a restored-mtime overwrite.
If the native change clock is unavailable, fail explicitly.
Keep every integer within SQLite's signed range.

For a missing or corrupted canonical payload, use verified recovery or return failure.
The invalidity affects every alias of that expected payload.
Do not silently accept the current corrupted bytes as the old content identity.

## 6. Publication and association transaction

The publication order is mandatory:

1. Select a safe destination without overwriting different complete content.
2. Write the original response to that destination's `.part` file.
3. Finish the write and atomic replacement.
4. Validate the complete file and stable identity.
5. Commit and read back the cache entry and required URL associations.

Use bounded methods for these boundaries.
Do not report cache or document success before replacement finishes.
Do not associate a final stage with `.part` content.

`HarvestStateStore` performs the transaction.
The existing runner makes applicable natural root rows available before association.
Keep the downloader's public tuple unchanged.
Pass internal metadata through existing class ownership, not a new public result shape.

The association transaction includes:

- The path-keyed cache entry under the resolved corpus root.
- The expected digest, canonical path, and size for applicable root rows.
- Original source names when authoritative values are available.
- Required same-digest repairs or same-resolved-URL response updates.

Read back the committed expected fields and affected row set through an independent connection.
Compare values, not only the number of affected rows.
Update active in-memory references after verification.

If publication fails, do not create a successful durable association.
If persistence fails after publication, stop with a visible error.
The complete file may remain unassociated.
The next attempt must validate it and verify a durable association before reuse.
It must not infer URL ownership from its filename.

Clean only the operation's authorized transient `.part` file when safe.
Do not perform a corpus cleanup.

## 7. Alias-update boundaries

### Expected-digest recovery

When a verified complete file restores an expected digest, repair every corresponding alias pointer.
Use the digest and corpus scope to identify the affected set.
Do not update only one row returned for the path.
Update canonical paths, sizes, cache keys, and active references consistently.
Keep unrelated source and classification history.

A corrupt occupied path does not grant overwrite authority.
Recovery can publish to a free safe path and rebind all corresponding aliases.
Leave unrelated and historical files untouched.

### Changed response for one resolved URL

When the new response has a different digest, update all roots for that resolved URL.
Retain their natural keys and independent source metadata.
Do not redirect different-URL aliases of the old digest.
Those aliases still expect the old payload.
Their next operation requires valid reuse, verified recovery, or explicit failure.

When the new digest already has a valid canonical file, reuse it.
Do not publish a second copy.

## 8. Placement, reclassification, and manual sorting

The first canonical payload may enter its classification folder before later aliases attach.
An alias's category does not require another physical file or a matching folder.
Later aliases must not relocate or delete the shared file merely to match their labels.

`HarvestRunner`, `CorpusReclassifier`, and `ManualDocumentSorter` share this rule.
Reclassification can retain the physical path and update only the intended aliases' derived labels.
Other aliases keep their labels and source history.

An authorized real move must:

- Validate the current canonical source and safe destination.
- Move one physical payload without overwriting different content.
- Verify the destination and its new identity.
- Update every affected alias path and the cache in one state-store transaction.
- Verify persistence, then refresh active references.

Equal source and destination means no physical action.
Never unlink the canonical source as collision handling.
An occupied equal-content destination does not authorize historical deletion.

Manual sorting groups all rows for one real physical path.
Process that group once.
Preserve all aliases and independent metadata.
Repeated passes must not duplicate payloads, delete aliases, or repeat an already completed placement.

A failed physical move or state update requires verified repair or explicit failure.
A stale path must not become a successful skip.

Default dry runs remain read-only.
They must not migrate, create backups, adopt legacy rows, repair pointers, move files, or persist cache changes.

## 9. Schema version 2 compatibility

Add only:

- Nullable `documents.content_sha256`, default `NULL`.
- Nullable `documents.original_pdf_name`, default `NULL`.
- The `content_cache` table defined in [data-model.md](../data-model.md).
- An optional nonunique digest lookup index within that table.
- The existing schema-version value changing from 1 to 2.

Do not change `documents.root_url`, old column declarations, or other table schemas.
Preserve every row in `documents`, `pdf_candidates`, `content_scores`, `dropped_release_notes`, and `run_meta`.
Preserve candidates, scores, flags, stages, categories, timestamps, and reasons.

New empty stores initialize version 2 atomically.
Recognized version 1 stores require the migration below.
Repeated version 2 opening is idempotent.
Unknown, malformed, or newer versions fail before writes.
Missing required version 2 schema fails explicitly.
Missing cache rows alone require revalidation, not a schema downgrade.

Version 1 readers and writers are unsupported for version 2 state.
Do not claim an old executable implements the new version guard.
An unsupported downgrade must not edit the version or rebuild URL rows.

### Version 1 migration

1. Read and validate the existing version without overwriting it.
2. Create a new consistent backup with the SQLite backup API.
3. Verify integrity, schema, version, and complete row values through a fresh backup connection.
4. Begin one serialized migration transaction and recheck version 1.
5. Apply additive changes, verify preserved values, set version 2 last, and commit.

After commit, verify the supported schema and preserved rows through another connection.
Only then permit normal store operations.
Committed WAL records must appear in the verified backup.
Copying only the main SQLite file is not acceptable.

Roll back failures before commit.
For failed committed verification, stop and retain the verified backup.
Restore through the backup API only with explicit recovery authority and no active writers.
Do not restore over later accepted writes.
Do not return a partially accepted upgrade.

### Legacy adoption

The migration starts new fields as null and cache entries as absent.
Explicit adoption during the single indexing pass can validate existing local files.
Populate missing digests from stable valid bytes without fetching.
Populate original names from authoritative metadata or recorded resolved PDF URLs.
Keep unknown original names null.
Do not derive them from local collision names.
Do not delete existing duplicates.

## 10. JSON and CSV manifest compatibility

`ManifestWriter` continues to emit every natural URL row.
Keep the existing top-level format, fields, values, and candidate serialization.
Keep resolved URLs, categories, stages, paths, sizes, and source metadata.

| Additive field | JSON value | CSV value |
| --- | --- | --- |
| `original_pdf_name` | Original name string, or `null` when unknown. | Original name string, or an empty cell when unknown. |
| `content_sha256` | Full lowercase digest string, or `null` when untrusted or absent. | Full lowercase digest string, or an empty cell when untrusted or absent. |

Append new CSV columns after existing columns.
Keep all existing column names and order.
Do not replace existing status or stage meanings.
The canonical basename must not replace an alias's original source name.
`local_path` points to the canonical file, even in another alias's category.

The additive manifest contract supports readers that ignore unknown fields.
Readers that require an exact header need an explicit update.
This manifest compatibility does not make old SQLite writers compatible.

Do not include body text, payload copies, parser samples, or embedded PDF data.

## 11. Counts and bounded work

Calculate `total_bytes` once per valid referenced canonical real local path.
Do not count it once per URL alias.
Keep document, category, and stage totals based on URL rows.
Exclude `.part` and unassociated historical files from the canonical inventory total.
Fail explicitly on unverifiable complete references or inconsistent size evidence.

Within one allocator lifetime, stored-file digest bytes must not exceed `S + U + C`.
Unchanged aliases add no stored digest bytes.
Use at most one fetched-payload digest pass per response.
An unchanged validated restart has zero fetches, payload writes, and stored digest bytes.

For the clean synthetic stress proof:

- First run: 1,000 distinct URLs, 20 payloads, one discovery walk, 1,000 fetches, and 20 payload writes.
- Physical files and bytes equal the 20 unique payloads.
- Stored hashing and fetched hashing are measured separately.
- Maximum stored-file read size is 1,048,576 bytes.
- Restart: every alias remains valid, with zero fetches, writes, and stored hashing.

Do not present this proof as historical cleanup or a bandwidth saving after both URLs were fetched.
