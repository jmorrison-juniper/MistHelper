# Feature Specification: Canonical Corpus Documents

**Feature Branch**: `jmorrison-juniper-canonical-corpus-documents`

**Created**: 2026-10-01

**Status**: Ready for bounded local planning. Implementation and protected acceptance remain unproved.

**Input**: User description: "Specify the code-prevention portion of issue 2977. Keep one canonical payload per SHA256 within a corpus. Preserve every URL record and safe resume. Produce only the specification and its quality checklist."

**Issue**: https://github.com/jmorrison-juniper/MistHelper/issues/2977

This feature prevents new duplicate payload writes. It does not clean an existing corpus or prove the historical report.
A payload means the raw document bytes. A canonical payload means the one complete stored payload that its URL aliases reference.
SHA256 identifies payload content. An alias means a URL record that refers to a canonical payload without another payload copy.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Store Equal Content Once (Priority: P1)

As a corpus operator, I need equal documents to share one stored payload.
Different URLs, source names, and categories must not cause another payload write.
Different documents must remain separate, even when their names match.

**Why this priority**: Duplicate payloads consume storage. A name collision can also destroy a different document.

**Independent Test**: Use the actual `CorpusDownloader.download_document` flow in an empty temporary corpus.
Use a local fake client for two URLs with different names and categories that return equal original synthetic bytes.
Count complete files, physical bytes, payload writes, and client fetches.

**Acceptance Scenarios**:

1. **Given** two distinct URLs with equal bytes, **When** their names and categories differ, **Then** both requests use one canonical payload.
   The first request returns `downloaded`. The second returns `skipped` after its fetch.
   Two fetches produce one complete file and one payload write.
2. **Given** two distinct URLs with different bytes, **When** their basenames match, **Then** both complete payloads remain intact.
   Neither request overwrites the other payload.
3. **Given** a valid canonical payload outside the requested name or category, **When** another URL returns equal bytes, **Then** no new payload copy appears.
   The alias refers to the existing canonical payload.
4. **Given** an unknown resolved URL, **When** the operator requests it, **Then** the client fetches its bytes before content comparison.
   The result does not claim a bandwidth saving.

---

### User Story 2 - Resume Without False Reuse (Priority: P1)

As a corpus operator, I need valid saved URLs to resume without another document fetch.
I also need a clear failure or verified recovery when a saved payload becomes invalid.

**Why this priority**: A false skip can leave missing or changed documents in a completed inventory.

**Independent Test**: Close the actual state store after a successful download and alias registration.
Start new store, allocator, and downloader instances.
Request the same URL and every persisted alias with a fake client that rejects an unexpected fetch.

**Acceptance Scenarios**:

1. **Given** persisted aliases and an unchanged valid canonical payload, **When** a new process requests each URL, **Then** every request returns `skipped`.
   No request fetches document bytes or writes a payload.
2. **Given** a missing canonical payload, **When** any alias resumes, **Then** the request does not report reuse of that missing payload.
   The request performs verified recovery or reports an explicit failure.
3. **Given** changed canonical bytes, **When** the file size and restored modification time match the cache, **Then** resume still detects the change.
   A change in `ctime_ns` or another identity field prevents a false cached skip.
4. **Given** a replacement file at the same path, **When** its device or inode differs, **Then** the old cache cannot authorize reuse.
   The request validates the current file against the recorded content digest.
5. **Given** only an interrupted `.part` file, **When** the URL resumes, **Then** the request does not treat that file as complete.
   No alias or completed stage refers to the `.part` file.
6. **Given** a completed or classified URL row with an invalid canonical payload, **When** the runner resumes, **Then** the final stage does not bypass validation.
7. **Given** a permission, stat, hash, or store failure, **When** reuse validation fails, **Then** the operation reports an explicit failure.
   The runner does not count the operation as a successful download or skip.

---

### User Story 3 - Keep Every URL in the Inventory (Priority: P1)

As a corpus operator, I need each source URL to retain its own history and classification.
Physical reuse must not combine distinct URL records.
The inventory must show the shared payload and the correct physical storage total.

**Why this priority**: Storage savings must not remove source evidence or misstate the inventory.

**Independent Test**: Register two natural root URLs with equal payload bytes and different metadata.
Render the actual JSON and CSV manifests.
Compare each row with its own saved source record and inspect the shared complete file.

**Acceptance Scenarios**:

1. **Given** two roots that share a canonical payload, **When** the manifest writer renders both formats, **Then** each format contains both URL records.
   Each record retains its source and resolved URLs, original name, category, sub-category, stage, path, size, and candidate URLs.
2. **Given** two aliases for a payload of B bytes, **When** the operator reads the summary, **Then** the physical canonical total is B.
   The document and category counts still count URL records.
3. **Given** a first payload write and a later equal-content request, **When** both state changes succeed, **Then** the runner counts one download and one skip.
   The later request can require a fetch without becoming a new physical download.
4. **Given** saved aliases, **When** the process restarts and renders the manifests again, **Then** every alias still identifies the same valid payload.
   The restart does not replace original names with the canonical filename.

---

### User Story 4 - Move a Shared Payload Safely (Priority: P2)

As a corpus operator, I need classification and sorting to preserve every alias reference.
One record's category change must not replace another record's source metadata or create a category-specific payload copy.

**Why this priority**: The existing runner, reclassifier, and manual sorter move physical paths.
An update to only one URL row can leave other aliases with stale paths.

**Independent Test**: Prepare a synthetic canonical payload with multiple persisted aliases.
Exercise the existing runner placement, `CorpusReclassifier`, and `ManualDocumentSorter` paths separately.
Render manifests and resume each alias after every successful operation and restart.

**Acceptance Scenarios**:

1. **Given** multiple aliases for one payload, **When** an authorized placement moves that payload, **Then** every alias refers to its current valid path.
   The operation updates the canonical identity cache and affected in-memory references.
2. **Given** different category labels for equal content, **When** one record changes classification, **Then** the other records retain their own category labels.
   No second payload copy appears.
3. **Given** repeated requests for the same canonical placement, **When** the source already equals the final path, **Then** the payload remains intact.
   No reuse decision deletes the canonical payload.
4. **Given** a default dry run, **When** either classification tool reports proposed changes, **Then** files, durable state, and cache remain unchanged.
5. **Given** an interruption or failed state update during placement, **When** the operator resumes, **Then** the run validates and repairs references or reports failure.
   The run does not report successful reuse of a stale path.

---

### User Story 5 - Upgrade State With Bounded Work (Priority: P2)

As a corpus operator, I need old saved state to remain usable without losing records.
I need alias processing to avoid repeated reads of unchanged stored documents.

**Why this priority**: Repeated corpus hashing can make storage savings impractical.
An unsafe migration can damage the source inventory or authorize an invalid skip.

**Independent Test**: Create original synthetic version 1 state and small local payloads.
Test upgrade, repeated opening, restart, and migration failures.
Measure 1,000 distinct URL requests that share 20 distinct payloads.

**Acceptance Scenarios**:

1. **Given** version 1 state, **When** an upgrade succeeds, **Then** all natural URL records and existing metadata remain available.
   New content and cache values remain untrusted until validation succeeds.
2. **Given** a successful upgrade, **When** the store opens again, **Then** no duplicate records or repeated migration changes appear.
3. **Given** an unsupported newer version or failed migration, **When** the store opens, **Then** it reports an explicit failure.
   It does not overwrite the version or leave a partially accepted upgrade.
4. **Given** 1,000 URLs for 20 payloads, **When** the actual download flow processes them, **Then** it performs one corpus discovery walk.
   It writes 20 complete payloads and performs 1,000 document fetches.
   Alias count does not cause repeated hashing of unchanged stored payloads.
5. **Given** the validated cache from that run, **When** new instances request all saved aliases, **Then** they perform no document fetches.
   They perform no payload writes or repeat hashing of unchanged stored payloads.

### Edge Cases

- Equal bytes use unrelated names and unrelated category or sub-category folders.
- Different root URLs select the same resolved URL. Both roots retain their own candidate history.
- Different bytes use the same basename, size, category, or collision variant.
- A saved alias requests a category that differs from the canonical payload's physical folder.
- A canonical file disappears, becomes empty, loses its `%PDF` prefix, or differs from its recorded digest.
- A file keeps its size and modification time after a byte change. Its change time still differs.
- A file changes device, inode, or identity during validation.
- A `.part` file contains a `%PDF` prefix or the full expected size. It still is not a complete payload.
- A process stops before replacement, after replacement, or before the required state commit.
- A directory, file read, stat call, hash operation, payload write, or replacement denies access.
- The store becomes locked, damaged, unwritable, or unable to verify a durable update.
- The cache is absent, stale, incomplete, or incompatible with the current state version.
- Old state contains final stages, nullable paths, unrelated metadata, or existing physical duplicates.
- A move receives stale rows for several aliases of the same payload.
- Two separate corpus roots contain equal bytes. Neither corpus may depend on the other's physical files.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harvester MUST select one canonical complete payload per SHA256 within a corpus.
  Selection MUST apply across URL, original name, category, and sub-category.
  Equal content MUST NOT cause another new payload copy.
  Existing physical duplicates do not authorize automatic cleanup.

- **FR-002**: A distinct resolved URL without a persisted validated association MUST fetch its bytes to determine its digest.
  Equal-content reuse MUST prevent the subsequent payload write.
  This reuse saves physical writes and storage bytes, not the first transfer for an unknown URL.

- **FR-003**: `CorpusDownloader.download_document` MUST retain its four-item result contract.
  The contract remains `(downloaded|skipped|failed, path, size, reason)`.
  A new complete payload returns `downloaded`.
  Verified reuse returns `skipped`, including reuse after a fetch.
  A failed document operation reports its failure reason.

- **FR-004**: Different payloads with the same basename MUST receive distinct safe paths.
  Allocation and placement MUST NOT overwrite a different complete payload.
  An occupied name alone MUST NOT establish equal content or URL ownership.

- **FR-005**: The state MUST retain one document row per natural `root_url`.
  It MUST preserve root/source URL, resolved URL, chosen/rejected URLs, original name, category, sub-category, stage, `local_path`, and `file_size`.
  It MUST also preserve current document types, flags, timestamps, candidate reasons, scores, and error/drop reasons.
  Distinct natural URL keys MUST NOT collapse into one document row.

- **FR-006**: Each persisted alias MUST explicitly identify its canonical payload.
  The SHA256 digest is the content identity within one corpus.
  Natural URL keys MUST remain unchanged.
  The feature MUST NOT introduce artificial record IDs.
  Shared payload ownership MUST NOT depend on the first row returned for a path.

- **FR-007**: The state and manifests MUST retain each record's original source name before local collision handling or placement.
  A shared canonical filename MUST NOT replace an alias's original name.
  Categories and sub-categories describe individual URL records.
  An alias's physical folder need not match its category metadata.

- **FR-008**: The actual `ManifestWriter` MUST render every URL row to JSON and CSV.
  It MUST retain existing field names, values, candidate serialization, and stage/status meaning.
  Both formats MUST identify the canonical payload and retain the original name for each alias.
  Any added fields and their null behavior MUST have a documented compatibility contract.

- **FR-009**: A same-URL or alias skip MUST validate the canonical file before reuse.
  Validation MUST include the cached size, device, inode, `mtime_ns`, `ctime_ns`, and expected SHA256 digest.
  The cache MUST identify the corpus and current physical path.
  File existence, stage, filename, or size and modification time alone MUST NOT authorize a skip.

- **FR-010**: A changed, absent, or untrusted identity cache MUST NOT authorize cached reuse.
  Revalidation MUST compare the stored file with its recorded content identity.
  Hash validation MUST reject a file whose identity changes during the read.
  A same-size change with restored modification time MUST remain detectable.
  A matching digest after valid revalidation may restore trusted reuse.

- **FR-011**: A missing, empty, corrupted, or incomplete canonical payload MUST invalidate reuse for every affected alias.
  Final downloaded or classified stages MUST NOT bypass this safeguard during runner resume.
  Recovery MUST restore a verified complete association or report an explicit failure.
  `.part` files MUST never count as canonical payloads, completed downloads, or valid resume evidence.

- **FR-012**: Permission, stat, read, hash, payload write, replacement, cache, and state failures MUST remain explicit.
  Per-document failures MUST return or record a clear reason.
  Durable state failures MUST stop the run with an explicit failure.
  The feature MUST NOT convert an unverifiable payload into a successful skip.

- **FR-013**: New payload publication MUST retain atomic `.part` write and replacement behavior.
  The complete file MUST exist and validate before the state records its complete canonical association.
  Required durable state updates MUST succeed and pass read-back verification before the runner reports success.
  Interrupted publication MUST NOT leave a successful alias to incomplete content.

- **FR-014**: An interruption after file publication but before state completion MAY leave an unassociated complete file.
  A later attempt MUST validate that file before content reuse.
  The attempt MUST verify its durable URL association before success.
  It MUST NOT infer same-URL ownership from the filename or create another equal payload unnecessarily.

- **FR-015**: Runner placement, `CorpusReclassifier`, and `ManualDocumentSorter` MUST preserve canonical references.
  A successful move MUST update every affected persisted alias, canonical path, identity cache, and active in-memory reference.
  Only records with an intended classification change may change category metadata.
  Repeated placement MUST NOT delete the canonical source when it already equals the selected final path.
  A failed move or state update MUST trigger explicit recovery or failure, not stale-path success.

- **FR-016**: Existing default dry-run behavior MUST remain read-only.
  A dry run MUST NOT change payloads, durable records, or the durable cache.
  Alias handling MUST NOT turn a dry run into a move or cleanup.

- **FR-017**: Downloaded and skipped counters MUST retain their current physical-write meaning.
  The first successful new payload publication counts as downloaded.
  A successful valid reuse counts as skipped, even when an unknown URL first requires a fetch.
  Failed state completion MUST NOT count as a successful download or skip.
  Physical canonical bytes MUST count each valid canonical payload once, not once per alias.
  URL, stage, and category counts MUST continue to count document rows.
  `.part` files and claimed historical savings MUST NOT enter the physical canonical total.

- **FR-018**: The shared allocator/downloader lifetime MUST perform no more than one corpus discovery walk.
  The stress proof MUST observe that walk through the actual flow.
  Individual downloads and moves MUST NOT restart whole-corpus discovery.
  Path consumers MUST NOT create one discovery-capable allocator per document.

- **FR-019**: Stored-file SHA256 reads MUST use blocks no larger than 1 MiB, or 1,048,576 bytes.
  Metadata memory may grow with paths and URLs, not total stored PDF bytes.
  The feature MUST preserve the current `fetch_bytes` memory behavior.
  It MUST NOT add a whole-corpus byte load, extra retained payload copies, or PDF conversion for deduplication.

- **FR-020**: Validated content and file identity metadata MUST persist across restarts.
  Unchanged valid cache entries MUST avoid repeat stored-file hashing.
  Let S equal uncached existing file bytes at discovery.
  Let U equal newly published unique payload bytes.
  Let C equal bytes for changed file identities that require revalidation.
  Stored-file hashing within a lifetime MUST not exceed S + U + C.
  Unchanged aliases MUST NOT increase this bound.
  Each fetched payload MUST require at most one digest pass for deduplication.
  An unchanged validated restart MUST require zero stored-file digest bytes.

- **FR-021**: The feature MUST preserve all existing crawl scopes, source choices, URL resolution, and release-note selection behavior.
  It MUST preserve the existing `%PDF` prefix validation.
  It MUST NOT add EOF-only rejection, parser dependency changes, or a PDF usability requirement.
  Issue 3024 remains separate.

- **FR-022**: Migration MUST preserve the complete version 1 state contract.
  This includes all `documents` columns, `pdf_candidates`, `content_scores`, `dropped_release_notes`, and `run_meta` records.
  Existing stage values and candidate selection/rejection reasons MUST retain their meaning.
  A legacy original name may come from a recorded resolved PDF URL.
  An unresolved original name MUST remain unknown until authoritative source metadata becomes available.
  Migration MUST NOT fabricate names from collision-renamed local paths.

- **FR-023**: The later design documentation MUST define every new or changed state and cache field.
  It MUST state field names, types, permitted values, defaults, nullability, natural keys, relationships, and version ownership.
  It MUST define old-to-new mapping, validation rules, upgrade triggers, transaction boundaries, and verified persistence.
  It MUST define JSON/CSV compatibility, repeat opening, restart behavior, cache invalidation, and recovery.
  It MUST state whether older readers or writers remain supported.
  Unsupported downgrade or newer-version access MUST fail explicitly without changing saved state.

- **FR-024**: Migration MUST create and verify a recoverable consistent backup before schema changes.
  Backup recovery MUST include committed state that remains in the store's journal.
  Migration MUST preserve unrelated rows and metadata.
  It MUST advance the schema version only after a verified successful upgrade.
  Repeated opening MUST be idempotent.
  Opening a newer schema MUST NOT overwrite its version with the old value.
  A failed upgrade MUST preserve or restore a consistent recoverable prior state.

- **FR-025**: Old rows, absent cache fields, and incomplete cache entries MUST start as untrusted.
  Local validation may populate trusted content metadata without a document fetch when the existing file is valid.
  Rebuilding the cache MUST preserve URL records and obey the single-walk and bounded-read requirements.
  Losing the cache MUST NOT authorize a false skip or cause silent data loss.
  Migration MUST NOT delete existing physical duplicates as a side effect.

- **FR-026**: The local proof MUST first demonstrate a red regression against the existing actual `download_document` flow.
  Two distinct URLs, two distinct names, and two categories MUST return identical original synthetic bytes.
  The assertion MUST expose duplicate physical files, bytes, or writes before the fix.
  The same regression MUST become green after the fix.
  A helper-only comparison or mocked download result does not satisfy this proof.

- **FR-027**: Green proof MUST use actual state persistence, manifest rendering, alias registration, and restart behavior.
  It MUST cover cross-name/category reuse, distinct bytes with a shared basename, and same-URL no-fetch reuse.
  It MUST cover every persisted alias after a new store, allocator, and downloader start.
  It MUST verify all retained metadata values in both actual manifest formats.
  It MUST exercise each reserved path consumer.
  It MUST verify read-only behavior for the existing reclassifier and manual sorter dry runs.

- **FR-028**: Failure proof MUST cover missing and corrupted canonical files, including same-size changes with restored modification time.
  It MUST cover device/inode changes, unstable reads, zero-byte files, and interrupted `.part` publication.
  It MUST cover failures before replacement, after publication, and before durable state completion.
  It MUST inject permission, stat, hash, write, replacement, and store failures at the relevant boundary.
  It MUST cover migration success, failure, backup recovery, and unsupported versions.
  Required cases MUST NOT skip because the host permits file access.

- **FR-029**: Stress proof MUST process at least 1,000 distinct URLs for 20 distinct original synthetic payloads.
  Each payload MUST be small, with a size no greater than 8 KiB.
  The proof MUST count discovery walks, digest calls, digest bytes, maximum stored-file read size, fetches, writes, files, and physical bytes.
  It MUST report fetched-payload hashing separately from stored-file hashing.
  It MUST show one walk, 20 payload writes, and 1,000 fetches on the first successful run.
  Restart proof MUST show no fetches, writes, or hashing of unchanged stored payloads.
  Separate cold-cache proof MUST verify the S + U + C bound with pre-existing synthetic files.

- **FR-030**: Each changed production method MUST reach at least 80 percent executable-line coverage.
  The evidence MUST identify changed methods and their covered and executable line counts.
  A whole-package average does not replace changed-method coverage.
  Required proof MUST have zero skipped cases.
  Assertions MUST inspect observed outcomes and independently expected values.
  Tautological assertions, expected-failure substitutions, baseline changes, exclusions, and suppressions MUST NOT satisfy the proof.

- **FR-031**: Durable URL and canonical metadata MUST have the same retention scope as the existing corpus state.
  Cache removal or replacement MUST require safe revalidation before trusted reuse.
  Metadata stores, manifests, logs, and proof reports MUST NOT contain document body text or payload copies.
  The cache MUST contain metadata only.

- **FR-032**: The deliverable MUST remain code prevention within the reserved paths and existing package.
  It MUST NOT require a new dependency, artificial IDs, historical cleanup, live downloads, or expanded crawl scope.
  Synthetic local proof MUST NOT claim that historical redundancy is removed.

### Key Entities

- **URL record**: The document record whose natural key is `root_url`.
  Its source URL, resolution history, original name, classification, stage, path, and size remain independent of other URL records.
- **Canonical payload**: The complete local payload identified by its full SHA256 digest within one corpus.
  Multiple URL records may reference its current valid path.
- **Alias association**: The durable relationship between a URL record, its resolved URL, and its canonical payload.
  The relationship survives restart and placement changes without another payload copy.
- **Validated file identity**: The saved size, device, inode, modification time, change time, path, and expected content digest.
  Only a complete validated identity permits cached reuse.
- **Compatibility record**: The schema version, field contract, verified backup, and recovery rules for state and metadata cache.
  It does not replace the natural URL key.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Two new URLs with equal bytes, different names, and different categories produce one complete stored payload.
  The run performs two fetches and one payload write.
  Physical canonical bytes equal the size of that payload.

- **SC-002**: In every shared-basename case with different bytes, both documents remain complete and unchanged.
  No download or placement overwrites either document.

- **SC-003**: After restart, 100 percent of persisted valid aliases and same-URL repeats need zero document fetches and zero payload writes.
  Unchanged saved documents require zero repeat content reads for identity validation.

- **SC-004**: Both inventory formats retain 100 percent of natural URL records and their required metadata.
  Every record with a complete payload refers to its correct canonical payload.
  Records without a payload retain their valid stage and nullable file fields.
  The summary counts physical canonical bytes once.

- **SC-005**: Every required failure case prevents successful reuse of missing, changed, incomplete, or unverifiable content.
  Each case produces verified recovery or a specific visible failure.
  No failed state completion enters successful download or skip totals.

- **SC-006**: After successful placement through each of the three path consumers, zero aliases have stale payload references.
  Restart preserves that result.
  Dry runs perform zero file, state, or cache writes.

- **SC-007**: For 1,000 URLs that share 20 documents, complete payload writes remain 20 and physical bytes equal the 20 distinct payload sizes.
  Each session uses one corpus discovery walk.
  Additional unchanged aliases cause zero repeat reads of stored document content.

- **SC-008**: A successful upgrade retains 100 percent of previous URL records and existing metadata.
  Repeated opening creates zero duplicate records.
  Failed or unsupported upgrades produce zero falsely accepted state changes and preserve a recoverable prior state.

## Assumptions

### Scope and Access

- This invocation creates only these two files:
  - `specs/2977-canonical-corpus-documents/spec.md`
  - `specs/2977-canonical-corpus-documents/checklists/requirements.md`
- The current local `spec-template.md` and `checklist-template.md` define the artifact structure.
  All generated prose uses plain Simplified Technical English and ASCII.
- The historical report states 2,974 source PDFs, 2,623 distinct documents, and 351 redundant files.
  It reports 1.32 GB of redundancy.
  These figures are context, not verified acceptance evidence.
- The historical Windows data files are absent and outside authorized access.
  No reading, renaming, deletion, or cleanup of those files is authorized.
- Local proof uses only original synthetic small payloads, temporary local files, and a local fake client.
  No live Juniper PDF download, corpus crawl, copyrighted fixture, cloud call, or upload is authorized.
- This invocation does not create or rename branches, fetch, commit, push, open a pull request, or claim another issue.
  It does not alter instructions, shared records, or other child files.
- `.specify/feature.json` and `.spec-context.json` remain unchanged.
  Branch and companion context hooks exceed the file-only scope and remain unresolved.
  The optional commit hook does not run.
  This fallback does not claim full completion of the normal hooked stage.

### Existing Dependencies

- The user reports that PR 3084 shipped the tracked `src/juniper_docs` package.
  This stage uses local source evidence and does not verify remote history.
- `CorpusDownloader.download_document` currently prepares the category/name, checks same-URL reuse, fetches valid bytes, allocates a path, and publishes a payload.
  Its atomic publication writes `name.pdf.part` before replacement.
- The existing allocator compares occupied variants of the target name.
  Cross-name and cross-category content therefore need corpus-wide identity handling.
- `HarvestRunner` persists natural URL rows and moves uncategorized payloads.
  `ManifestWriter` renders every URL row.
  `CorpusReclassifier` and `ManualDocumentSorter` also move physical paths.
- The current durable schema reports version `1`.
  Its `documents` columns are `root_url`, `doc_type`, `stage`, `resolved_pdf_url`, `category`, `sub_category`, and `is_fallback`.
  The remaining columns are `local_path`, `file_size`, `error_reason`, and `updated_at`.
  The other tables are `pdf_candidates`, `content_scores`, `dropped_release_notes`, and `run_meta`.
  Existing original names do not have a separate stored field.
- Required stage meanings remain `discovered`, `resolved`, `downloaded`, `classified`, `failed`, `dropped`, and `no_pdf`.
  The new content identity must not become a replacement document stage.
- Planning must document the complete schema and cache migration contract before implementation.
  Required compatibility constraints do not select new field names, a storage layout, or an implementation algorithm.

### Reserved Paths for Later Work

The following paths bound later implementation work.
This reservation does not authorize their modification during this specification-only invocation.

Production paths:

```text
src/juniper_docs/acquire/pdf_paths.py
src/juniper_docs/acquire/downloader.py
src/juniper_docs/harvest/state_store.py
src/juniper_docs/harvest/manifest_writer.py
src/juniper_docs/harvest/runner.py
src/juniper_docs/models.py
src/juniper_docs/classify/reclassifier.py
src/juniper_docs/classify/manual_sorter.py
```

Test paths:

```text
tests/unit/juniper_docs/canonical/conftest.py
tests/unit/juniper_docs/canonical/test_download_flow.py
tests/unit/juniper_docs/canonical/test_content_index.py
tests/unit/juniper_docs/canonical/test_path_consumers.py
tests/unit/juniper_docs/canonical/test_state_migration.py
tests/contract/juniper_docs/test_canonical_manifest.py
```

Documentation paths:

```text
documentation/free-juniper-corpus.md
changelog.d/issue-2977-canonical-corpus-documents.md
```

No README, shared CHANGELOG, checked-in manifest, SDK pin, exclusion, baseline, suppression, shared record, or other child file belongs to this deliverable.
Any later authorized spec artifacts remain inside `specs/2977-canonical-corpus-documents/`.
This invocation creates no plan, task list, feature manifest, or companion context file.

### Coordination and Protected Acceptance

- The user supplied app session `fa52c2c5-afc5-49f7-b300-cfe4b481b7ed` and assignee `jmorrison-juniper`.
  The reported labels are `chore`, `src`, `tests`, and `in-progress`.
  The user reports that the exact reservation comment exists.
  This stage does not claim or revalidate remote ownership.
- The app owns branch `jmorrison-juniper-canonical-corpus-documents`.
  The prior numeric-prefix validator refusal does not authorize branch creation or renaming.
  The issue directory is independent of the branch name.
- The reported initial main revision is `b7ce8eecea305c20b498e12b3f3446ae662663ea`.
  This revision is context, not a push or pull-request grant.
- The reported protected position is 30, after issue 3575.
  The parent must supply a full verified main-SHA grant before any push or pull request.
  Local specification or test results do not replace that grant.
- Later protected acceptance must identify the granted main revision and the exact checked candidate.
  It must verify the reserved change scope and applicable gates against that revision.
  A changed candidate or base requires new affected evidence.
  This stage authorizes no fetch, commit, push, pull request, merge, or deployment.
- Local code-prevention acceptance and protected merge acceptance are separate from historical acceptance.
  Issue 2977 remains open.
  No later code-prevention report may claim historical cleanup or use these results to prove the absent Windows corpus.

### Defaults and Unresolved Acceptance

- A corpus means one authorized local output root and its state.
  Content identity does not share physical files across separate corpora.
- The existing serialized writer model remains the operating assumption.
  Coordinated concurrent independent writers are outside this feature's scope.
- Unknown metadata remains untrusted.
  A filesystem that cannot provide a required reliable identity must not receive an unsupported cached skip.
- The 1,000-URL stress size and 8 KiB payload ceiling define bounded local proof.
  They do not set a production corpus size limit.
- No scope clarification is required before bounded local planning.
  Planning must receive this issue directory explicitly because shared `.specify/feature.json` remains unchanged.
- Red/green regression, manifest/resume proof, failure proof, measured stress work, and changed-method coverage remain unproved in this stage.
  Schema/cache design, migration implementation, backup recovery, and compatibility tests remain later obligations.
  Historical acceptance and the parent main-SHA grant also remain unresolved.
