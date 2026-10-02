# Research: Canonical Corpus Documents

## Basis and scope

Use [spec.md](spec.md), the user's supplied technical findings, and constitution version 1.5.0.
These findings resolve the design choices below.
This stage did not repeat production-source exploration, download documents, or dispatch agents.
Local reads covered planning inputs, hook configuration, validation configuration, and directory names.
Directory counts do not constitute a new code audit.

This stage writes five design artifacts only.
It does not implement the design, run the acceptance tests, or prove historical savings.
The reported baseline of 183 passed tests and three skipped tests is not a result from this stage.

## 1. Keep ownership in the existing classes

**Decision**: Extend `PdfPathAllocator` and `HarvestStateStore`.
The allocator owns one corpus-scoped, in-memory metadata cache.
The state store owns all durable metadata and alias updates.
Do not introduce another persistent index, sidecar database, or indexing service.

**Rationale**: These classes already control paths and transactional URL state.
One owner prevents conflicting cache and document receipts.
Small class methods can separate validation, lookup, publication, and persistence.

**Alternatives considered**: A separate content-index class with independent persistence would duplicate ownership.
A filename-only allocator cannot find equal bytes across names or categories.

## 2. Identify content before allocating a name

**Decision**: Calculate the fetched payload's full SHA256 before name allocation.
Look up that digest across the resolved corpus root.
Validate a matching complete file before reuse.
Retain the current `%PDF` prefix check.

**Rationale**: Names, categories, and URLs do not establish content equality.
An unknown resolved URL still needs one `fetch_bytes` call.
The second equal response avoids a physical payload write, not its first HTTP transfer.

**Alternatives considered**: URL equality, basename equality, byte length, and shortened content digests cannot authorize reuse.
EOF-only rejection, conversion, and parser usability checks belong outside this feature.

## 3. Preserve the existing name-collision policy

**Decision**: Keep the allocator's existing sanitized names and deterministic URL-hash suffix rules.
If an occupied candidate contains different bytes, select another deterministic safe variant.
This rule also applies when a refetched URL changes its bytes.
Never infer equality from a candidate name or its URL-derived suffix.

**Rationale**: Content lookup prevents duplicates.
Name allocation protects distinct content.
These are separate decisions.

**Alternatives considered**: Overwriting the old same-URL file would break other aliases.
New digest-based public filenames would change existing naming behavior without a requirement.

## 4. Persist path identity in schema version 2

**Decision**: Add nullable `documents.content_sha256` and `documents.original_pdf_name`.
Keep `documents.root_url` as the natural primary key.
Add `content_cache` to the existing SQLite store.
Its composite natural key is `(corpus_root, local_path)`.
Both cache paths identify resolved, real local locations.

The cache stores a full content digest and five stat fields:
`file_size`, `device`, `inode`, `mtime_ns`, and `ctime_ns`.
It contains no document body, PDF copy, artificial document ID, or separate canonical-owner row.

**Rationale**: Multiple URL rows can point to one file without losing their independent source history.
The actual path identifies the cached file.
The root prevents cross-corpus reuse.
The full stat identity detects same-size changes with a restored modification time.

**Alternatives considered**: A digest-only persistent key cannot describe a moved or replaced file.
Size and modification time alone can authorize false reuse.
An artificial document ID would replace a natural relationship without a need.

See [data-model.md](data-model.md) for field definitions.

## 5. Bound discovery and stored-file reads

**Decision**: Perform one corpus discovery walk per allocator lifetime.
Build path and digest lookup maps from metadata.
Exclude `.part` files.
Stream stored-file hashing in blocks of at most 1,048,576 bytes.
Validate each changed, new, or touched uncached path once per stable identity.

Compare path and descriptor identity before and after hashing.
Reject a file that changes during the read.
Check that a cache-hit file is readable without reading its body.
Trust a complete unchanged cache entry when its digest matches the expected alias digest.

**Rationale**: Stored-file work is bounded by `S + U + C`.
Here, `S` is uncached existing bytes, `U` is newly published unique bytes, and `C` is revalidated changed bytes.
Unchanged aliases add metadata checks, not content reads.
An unchanged validated restart needs zero stored-file hash bytes.

**Alternatives considered**: Rewalking or rehashing the corpus for each download scales with alias count.
Loading every stored PDF into memory violates the memory requirement.

The existing client still holds one complete HTTP response body in memory.
The design neither replaces that behavior nor retains another full payload for comparison.

## 6. Treat restart receipts as conditional evidence

**Decision**: Reuse a saved URL only after validating its expected canonical path and digest.
Downloaded and classified stages do not bypass validation.
Missing, unreadable, incomplete, corrupted, or unstable files invalidate reuse.
Incomplete cache entries are untrusted.

**Rationale**: A saved final stage proves a previous operation, not current file health.
A cache hit must match the corpus, path, digest, and all five identity fields.
A filesystem without reliable required identity fields cannot authorize a metadata-only skip.

**Alternatives considered**: Checking only existence, filename, stage, or `.part` size can hide an incomplete corpus.
Silently disabling state writes would make later receipts unverifiable.

## 7. Separate digest repair from changed URL content

**Decision**: A verified replacement of an expected digest repairs every alias pointer for that digest.
Update paths and sizes through `HarvestStateStore`.
Retain each alias's source URLs, categories, stages, candidates, scores, and reasons.

If a fetched response has a new digest, update the roots that use that resolved URL.
Do not redirect different-URL aliases of the old digest.
Those aliases retain their old expected digest and need their own validation or recovery.
Always hash a response that was actually fetched, even when its URL is known.

**Rationale**: A digest establishes equal bytes.
A resolved URL identifies which URL rows received a changed response.
These relationships have different update scopes.

**Alternatives considered**: Rebinding every old alias to a changed response silently changes unrelated source evidence.
Updating only one root leaves other roots for the same resolved URL inconsistent.

## 8. Publish before accepting durable success

**Decision**: Keep atomic `.part` writing and replacement.
Validate the complete published file before accepting its cache entry.
Commit the cache entry and required URL associations together.
Verify those durable values through a read-back before returning successful completion.

**Rationale**: File publication and SQLite commit are separate atomic operations.
A crash between them may leave an unassociated complete file.
The next attempt can validate and adopt that file without another equal payload write.
It must still commit and verify the URL association.

**Alternatives considered**: Marking a row complete before replacement can create a successful pointer to incomplete bytes.
Returning success after an unverified commit can conceal a failed store update.

Persistence failures stop the run.
Do not downgrade them to an in-memory-only mode.
Do not count a published file as a successful download when required state completion failed.

## 9. Upgrade legacy state with a consistent backup

**Decision**: Detect schema version 1 before writing schema version 2.
Create a new recoverable backup through the SQLite backup API.
Verify backup integrity, schema version, and preserved records before migration.
Include committed WAL state through that API.

Apply both nullable columns, the cache table, and the version update in one transaction.
Keep all existing table declarations and old column values.
Set version 2 only after in-transaction validation.
Verify the committed schema and retained records through another connection.

**Rationale**: A raw copy of the main database can omit committed WAL data.
An atomic upgrade cannot accept a partial schema.
An existing verified version 2 store does not repeat the migration.

**Alternatives considered**: Rebuilding URL rows risks losing candidates, scores, flags, stages, or unrelated metadata.
Blindly setting the version on every open can overwrite a newer schema.

Reject malformed, unsupported, or newer versions without changing their state.
Version 1 executables are not supported readers or writers of version 2.
An authorized rollback restores the verified backup rather than editing the version number.

## 10. Adopt legacy files explicitly

**Decision**: During the single discovery pass, validate existing complete files as needed.
Explicit legacy adoption may fill a missing document digest from verified local bytes.
It does not fetch a document.
Derive an old original name only from authoritative source metadata or its recorded resolved PDF URL.
Leave an unresolved original name null.

Retain a valid established canonical path.
If none exists, choose a stable normalized-path order among verified equal files.
Do not assign ownership to the first URL row returned by SQLite.
Rebinding legacy aliases requires a verified state operation.
Leave pre-existing physical duplicates untouched.

**Rationale**: Old rows and missing cache fields must not start trusted.
One discovery pass supplies enough evidence for safe adoption.

**Alternatives considered**: Inferring an original name from a collision-renamed local path fabricates metadata.
Deleting historical duplicates would expand this task into cleanup.

## 11. Preserve URL inventories and correct physical totals

**Decision**: Keep one JSON and CSV entry per natural root/source URL.
Append `original_pdf_name` and `content_sha256` as additive fields.
Represent unknown values as JSON null and empty CSV cells.
Keep all existing fields, candidate serialization, resolved URLs, and labels.

Calculate `total_bytes` once per valid referenced canonical local path.
Keep document, stage, and category counts based on URL rows.
The canonical path can reside in another alias's category.

**Rationale**: Source inventory and physical storage measure different things.
The canonical filename must not replace an alias's original name.

**Alternatives considered**: Combining equal-content URL rows would lose source evidence.
Counting bytes per alias would overstate canonical storage.
Pointer PDFs, symlinks, copies, conversion, and body-text fields are unnecessary.

## 12. Keep placement and sorting alias-safe

**Decision**: The first payload may enter its classification folder before later aliases attach.
Later aliases keep the shared physical path.
Reclassification can update an alias's derived label without moving the shared file.
Any authorized physical move updates every affected alias and cache path through the existing state store.

Manual sorting groups rows by their real physical path.
It processes each payload once and preserves every alias.
Repeated passes are idempotent.
An equal source and destination is a no-op, never a deletion.

**Rationale**: Moving one alias's shared file for a label change can invalidate every other alias.
Independent labels do not require independent files.

**Alternatives considered**: Selecting the first row as owner loses other alias decisions.
Category-specific copies violate canonical storage.

Dry runs do not migrate, back up, adopt, move, repair, or persist cache changes.
They may read metadata and validate local files without changing durable state.

## 13. Prove the behavior through the real flow

**Decision**: Begin with a red regression through `CorpusDownloader.download_document`.
Use two URLs, two names, two categories, and equal original synthetic bytes.
Then require green results with one payload write and two fetches.

Use the actual state store, both manifest writers, restarts, and all three path consumers.
Inject permission, stat, hashing, publication, replacement, and persistence failures.
Do not depend on host permissions to produce a failure.

Measure 1,000 distinct URLs for 20 payloads of at most 8 KiB each.
Separate fetches, fetched digest work, stored digest work, writes, files, physical bytes, and corpus walks.
Measure cold-cache and unchanged-restart work separately.

**Rationale**: A helper-only comparison does not prove write prevention or durable aliases.
An aggregate coverage percentage does not prove each changed method.

**Alternatives considered**: Skips, expected-failure substitutes, tautological assertions, exclusions, or baseline edits do not prove the contract.
Require at least 80 percent executable-line coverage for every changed production method.

## 14. Keep gate and release evidence honest

**Decision**: Use the configured full Ruff, Black, mypy, Bandit, complexity, links, and STE checks.
Use the exact CI `MYPY_PATHS`.
Run required-input preflight before the unchanged test-quality ratchet.
Resolve runtime dependencies with the standard resolver for strict audit.
Then compile complete hashes with `uv` and audit without dependency resolution or pip.

**Rationale**: A narrow package check does not replace the configured gate.
Missing STE dictionary data must remain `dictionary_unavailable`, not a dictionary-backed pass.
A Git-only devtools dependency cannot be covered by a hashable runtime wheel lock.

**Alternatives considered**: Suppressions, dependency changes, or altered baselines would weaken acceptance.
Neither downloading both URLs nor a synthetic test proves historical bandwidth or storage savings.

See [quickstart.md](quickstart.md) for commands, expected outcomes, and audit limits.

## Resolution and remaining authorization

All technical choices needed for this design are resolved.
The planning stage did not implement or validate production changes.
The three initial skips concern absent historical evidence, not parser fixtures.
The implementation must preserve those historical tests and prove every new case without a skip.
The parent must provide the verified main SHA before any push or pull request.
The exact requested `Co-authored-by` trailer must be available before a later authorized local commit.
Do not invent an identity or treat these prerequisites as completed work.

The file-only fallback does not update agent instructions or shared feature context.
It does not claim completion of the normal hooked workflow.
