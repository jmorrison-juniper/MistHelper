# Implementation Plan: Canonical Corpus Documents

**Branch**: `jmorrison-juniper-canonical-corpus-documents` (reported app-managed branch, not revalidated or changed)

**Date**: 2026-10-01

**Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/2977-canonical-corpus-documents/spec.md`

**Template**: [.specify/templates/plan-template.md](../../.specify/templates/plan-template.md)

**Constitution**: Version 1.5.0, amended 2026-09-11

## Summary

Prevent new duplicate corpus payload writes while preserving every natural source URL record.
Extend `PdfPathAllocator` and `HarvestStateStore`, not a parallel persistent index.
Use full SHA256 lookup before name allocation.
Keep different bytes separate through the existing deterministic URL-hash collision policy.

The allocator owns metadata-only maps and one corpus walk per lifetime.
The existing SQLite store owns schema version 2, path-keyed content metadata, and alias transactions.
Trust complete unchanged stat identities after restart.
Stream changed or uncached stored files in blocks no larger than 1 MiB.
Keep the existing one-body-in-memory `fetch_bytes` behavior.

Preserve downloader results, source history, manifests, resume safety, classification, and default dry runs.
Report success only after atomic publication and verified required persistence.
Do not clean historical files or claim bandwidth savings for two fetched URLs.

### File-only execution boundary

This invocation writes only:

```text
specs/2977-canonical-corpus-documents/plan.md
specs/2977-canonical-corpus-documents/research.md
specs/2977-canonical-corpus-documents/data-model.md
specs/2977-canonical-corpus-documents/quickstart.md
specs/2977-canonical-corpus-documents/contracts/storage.md
```

The prior read-only branch validator refused the app-managed branch.
That refusal does not authorize branch creation or renaming.
The required PowerShell setup entrypoint was attempted but could not start because `pwsh` is unavailable.
Its explicit feature-directory path also persists `.specify/feature.json`.
Use the supplied issue directory directly instead of another writing setup path.

Do not change `.specify/feature.json`, `.spec-context.json`, instructions, source, tests, dependency manifests, or Git state.
Do not fetch, commit, push, open a pull request, download documents, or launch agents.
Agent-context and mandatory companion writes are outside this grant.
Record their dispatch results without weakening this scope.
The five artifacts are a file-only planning result, not completion of the normal hooked workflow.

## Technical Context

**Language/Version**: Python 3.13.13 in the existing worktree `.venv`.
The constitution requires Python 3.13 or newer.

**Primary Dependencies**: Existing harvest/client/parser stack and standard-library `hashlib`, `pathlib`, `os`, and `sqlite3`.
Keep `fetch_bytes`, SDK pins, requirements, and parser dependencies unchanged.
No new package is required.

**Storage**: Existing corpus SQLite database and complete PDFs under the authorized output root.
Schema version 2 adds nullable document digest/name fields and `content_cache`.
Cache rows use `(resolved corpus_root, actual local_path)` as their natural key.
Persist size, device, inode, `mtime_ns`, `ctime_ns`, and full SHA256.
Use SQLite backup API protection for version 1 migration, including committed WAL data.

**Testing**: Actual downloader/state/manifest/path-consumer tests using original synthetic local payloads and a fake client.
Use pytest, coverage, full configured Ruff and Black, exact CI mypy scope, Bandit, complexity, quality ratchet, links, and STE.
Audit unchanged runtime dependencies through the strict standard resolver and a complete hashed `uv` compilation.
Require zero required skips and at least 80 percent executable-line coverage per changed production method.

**Target Platform**: Existing Windows-compatible Python CLI/library behavior, Linux containers, and local macOS proof.
Use portable paths and reliable host stat identity.
No new service, container, or platform is required.

**Project Type**: Existing Python corpus acquisition, classification, and inventory feature.
The external contracts are the downloader tuple and JSON/CSV inventory.
The operational state contract remains in `HarvestStateStore`.

**Performance Goals**: One discovery walk per allocator lifetime.
Stored-file digest bytes are bounded by `S + U + C`.
Each fetched body has at most one deduplication digest pass.
Unchanged aliases add no stored-file hash work.
An unchanged validated restart has zero document fetches, writes, and stored digest bytes.

**Constraints**: Serialized writer model, no different-content overwrite, stable full stat checks, and fail-closed durable writes.
Finish `.part` write and replacement before accepting cache/state success.
Keep metadata memory proportional to paths and URL records, not stored PDF bytes.
Do not add body text, payload copies, symlinks, conversion, artificial IDs, or historical cleanup.

**Scale/Scope**: Local proof uses 1,000 distinct URLs and 20 payloads of at most 8 KiB each.
The reserved implementation touches eight existing production files, five canonical unit files, one contract file, and two documentation files.
All committed parser fixtures exist.
The three existing skips require the absent historical smoke manifest.
Do not modify those tests or create historical evidence.
This planning invocation touches only the five artifacts above.

All design choices are resolved in [research.md](research.md).
Implementation evidence and release permission remain pending, not technical design unknowns.

## Constitution Check

*Gate: Check before Phase 0 and again after Phase 1.*

Use [.specify/memory/constitution.md](../../.specify/memory/constitution.md) as the authority.
The table distinguishes design compliance from later implementation and deployment evidence.

| Principle or constraint | Before Phase 0 | After Phase 1 |
| --- | --- | --- |
| I. Structural discipline | Bounded existing-class extension and exact reserved leaf layout selected. Existing directory debt is recorded below. | Justified bounded documentation/test additions are recorded. New methods must meet five parameters, five logical blocks, five operations per block, and 25 lines. |
| II. Class-based architecture | Existing allocator and state-store ownership retained. No wrapper or parallel store selected. | Validation, lookup, publication, migration, and alias updates remain class-owned. |
| III. Safety-first | No destructive or network operation authorized now. Paths and fetched bytes require validation. | Complete-file validation, traversal rejection, explicit failures, and no secret/body logging are designed. Existing confirmation and EOF behavior remain unchanged. |
| IV. Deployment pipeline | Planning-only, with no code, fragment, commit, or remote mutation. | Local proof and the later protected pipeline remain pending. No release step is reported complete. |
| V. Observability | ASCII, metadata-only logging required. | Log I/O boundaries with counts, paths subject to redaction, statuses, and errors. Never log bodies or credentials. |
| VI. Inline comments | No implementation code is produced here. | Use rare, meaningful comments for non-obvious safety and identity decisions. |
| VII. Action logging | No implementation code is produced here. | Before/after action logging and full exception context are required in each touched block. Use `%s` formatting. |
| Technology and output boundary | Python 3.13+, unchanged dependencies, no new Mist API operation. | Existing `ManifestWriter` remains additive. Internal coordination uses the declared operational store without weakening API export backends. |
| Natural keys and verified persistence | Root URL key retained. Cache key uses real root/path. | No artificial IDs. Transactions, read-back, backup, recovery, and retention are defined in the storage contract. |
| Documentation and release scope | No shared README, CHANGELOG, or instruction edit. | Later operator guidance and one issue fragment are the bounded documentation exception. |
| Local commit and protected release | No commit authorized in this invocation. | A later single Conventional Commit needs the exact requested trailer. Protected main-SHA permission and release checks remain separate prerequisites. |

**Pre-research result**: PASS for bounded file-only planning with the scope-specific justifications below.
Do not claim strict existing hierarchy compliance or a normal branch-hook pass.

**Post-design result**: PASS for the same bounded design.
No technical clarification remains.
No safety or persistence failure is waived.
Implementation must measure touched method/class limits before editing and record any further existing violation.
Stop for an unjustified scope or gate violation.
The normal hooked workflow and all implementation acceptance remain incomplete.

### Existing debt and bounded extension

Read-only directory-name inspection found these existing visible child counts:

- Repository root: 38.
- `src/juniper_docs`: 6.
- `src/juniper_docs/acquire`: 6.
- `src/juniper_docs/classify`: 7.
- `src/juniper_docs/harvest`: 5.
- `tests/unit/juniper_docs`: 21.
- `tests/contract`: 12.
- `documentation`: 59.
- `changelog.d`: 44.

These counts are working-directory observations, not a claim of verified Git-tracked debt.
No production file body was re-explored.
Existing class and method limit violations were not remeasured during this stage.
Before implementation, inventory every touched violation without expanding this feature into general refactoring.

Edit only the eight reserved production children.
Do not add a production module, top-level package, service, or persistent-index class.
Keep helper operations bounded and class-owned.
Use grouped identity values instead of long argument lists.
The five identity values form one coherent stat record.
Cache entries group root, path, digest, and that identity.

The new canonical unit leaf has exactly five files.
The new contract leaf has one file.
Their required parent additions and the fixed planning hierarchy require the justifications below.
These exceptions do not authorize another unrelated child or a weakened quality gate.

Separate remediation must group existing broad source, test, and documentation hierarchies in a later authorized change.
That change needs its own scope, compatibility checks, and reservation.
Do not perform it here.

## Project Structure

### Documentation for this feature

```text
specs/2977-canonical-corpus-documents/
|-- spec.md                         # Preserved input
|-- checklists/requirements.md      # Preserved input
|-- plan.md                         # This planning output
|-- research.md                     # Phase 0 output
|-- data-model.md                   # Phase 1 output
|-- quickstart.md                   # Phase 1 validation guide
`-- contracts/storage.md            # Phase 1 storage/interface contract
```

`tasks.md` belongs to a separately authorized `speckit.tasks` stage.
Do not create it, a feature manifest, or a companion context file in this invocation.

### Reserved later implementation paths

```text
src/juniper_docs/
|-- acquire/pdf_paths.py
|-- acquire/downloader.py
|-- harvest/state_store.py
|-- harvest/manifest_writer.py
|-- harvest/runner.py
|-- models.py
|-- classify/reclassifier.py
`-- classify/manual_sorter.py

tests/unit/juniper_docs/canonical/
|-- conftest.py
|-- test_download_flow.py
|-- test_content_index.py
|-- test_path_consumers.py
`-- test_state_migration.py

tests/contract/juniper_docs/
`-- test_canonical_manifest.py

documentation/free-juniper-corpus.md
changelog.d/issue-2977-canonical-corpus-documents.md
```

**Structure Decision**: Extend the existing Python feature.
Use its current acquisition, harvest, model, and classification files.
Add the exact bounded test leaves and documentation paths only during implementation.
Do not create another project, store, or shared record.

## Phase 0: Research

**Output**: [research.md](research.md).

The supplied technical findings resolve ownership, identity, cache lifetime, migration, publication, alias repair, and placement.
Standard-library hashing and SQLite transactions need no new dependency choice.
Configured gate reads establish the exact validation commands.
No source-algorithm re-exploration, live document download, or research agent is needed or authorized.

Key decisions:

1. Store durable path metadata through `HarvestStateStore` schema version 2.
2. Perform digest lookup before name allocation through one shared `PdfPathAllocator`.
3. Trust only matching unchanged full identity, and stream all required revalidation.
4. Separate same-digest repair from a changed response for one resolved URL.
5. Preserve URL inventories and shared physical placement without cleanup.

## Phase 1: Design and Contracts

**Outputs**:

- [data-model.md](data-model.md): Fields, natural keys, relationships, validation, transitions, migration, retention, and recovery.
- [contracts/storage.md](contracts/storage.md): Downloader, state, publication, alias, manifest, count, and compatibility contracts.
- [quickstart.md](quickstart.md): Runnable later proof scenarios and configured gates.

### Download and restart design

Try a validated persisted resolved-URL association before fetching.
If bytes are fetched, calculate their full SHA256 regardless of URL history.
Look up content before choosing a filename.
Reuse valid equal content across categories or publish a unique safe payload.
Keep the four-item downloader result unchanged.

Store complete metadata only after stable validation.
Finish atomic `.part` publication before the verified association transaction.
Cache, URL receipts, and successful counters must not precede that boundary.
Treat durable state failure as fatal.

### Migration and alias design

Back up version 1 through the SQLite backup API and verify committed WAL records.
Apply nullable digest/name fields and the path-keyed cache atomically.
Preserve all existing document and related-table values.
Advance the version last and verify the committed result.
Reject unsupported newer versions before writes.

During explicit indexing adoption, validate legacy local files and fill missing digests without fetching.
Unknown original names stay null.
A successful expected-digest replacement repairs every corresponding alias pointer.
A changed response updates roots for its resolved URL without redirecting different-URL old-digest aliases.

### Inventory and placement design

Keep every existing JSON and CSV field and every root/source entry.
Add `original_pdf_name` and `content_sha256` with documented null behavior.
Count canonical bytes once per valid real local path.
Keep URL and classification totals row-based.

Allow the first canonical placement before aliases attach.
Later aliases retain the shared path.
Reclassification may update an alias's label without relocation.
Any real move updates all affected aliases through the state store.
Manual sorting processes the physical group once and remains idempotent.
Dry runs do not write files, backups, schema, aliases, or cache.

### Agent context and hooks

Do not update instructions under this file-only grant.
The required agent-context entrypoint was attempted and failed because `pwsh` is unavailable.
No instruction file changed.
Do not use an alternative writer.

The optional Git commit hooks remain unexecuted.
The mandatory `speckit.companion.after-plan` dispatch was attempted after re-reading the hook configuration.
It failed because no executable or local companion implementation is installed.
Its intended context-write behavior also exceeds this grant.
The failed dispatch leaves the normal hooked stage incomplete.
Do not create `.spec-context.json` to conceal that condition.

### File-only artifact validation

All five artifacts passed ASCII, placeholder, and Markdown fence checks.
Direct filesystem validation resolved all 20 repository-local links across the five files.
The packaged link checker selected zero files because these artifacts are untracked.
Its zero exit is not counted as link evidence.

Configured STE grading met the numeric threshold for all five files.
The configured dictionary was absent, so record `dictionary_unavailable`.
This is not a dictionary-backed STE pass.
Do not change the dictionary configuration or stage files to manufacture a check result.

A read-only metadata snapshot confirmed that all 6,678 scanned non-artifact files remained unchanged.
The scan excludes Git storage, virtual environments, installed modules, and tool caches.
Content hashes also confirmed unchanged spec, checklist, feature state, and hook configuration.
No companion context or task list was created.
No source acceptance test, dependency audit, Git mutation, or document download ran.

## Phase 2: Planning Handoff

This section orders later work.
It is not an implementation result or a generated task list.

1. Add and record the real-flow red regression.
   Use two URLs, two names, two categories, and identical synthetic bytes.
2. Extend the existing model and state store.
   Implement schema-2 backup/migration, cache ownership, verified associations, digest repair, and all-alias relocation.
3. Extend allocator and downloader behavior.
   Enforce one walk, streamed validation, digest-first reuse, safe collisions, publication order, and the unchanged tuple.
4. Integrate runner, manifests, reclassifier, and manual sorter.
   Preserve labels, alias groups, default dry runs, original names, and physical counters.
5. Complete proof, documentation, and local gates.
   Require the full relevant harvest regressions, per-method coverage, measured stress work, strict audits, and clean exact scope.

Keep the existing parser fixtures and historical tests unchanged.
No README, CHANGELOG, suppressions, baselines, exclusions, shared records, SDK pins, or dependency changes are permitted.

### Evidence and requirement mapping

| Reserved area | Required proof |
| --- | --- |
| Allocator/downloader | FR-001 through FR-004, FR-009 through FR-014, FR-018 through FR-021 |
| Model/state store | FR-005 through FR-007, FR-022 through FR-025, FR-031 |
| Manifests/runner counters | FR-008, FR-017 |
| Runner/reclassifier/manual sorter | FR-015, FR-016 |
| Canonical unit and manifest contract tests | FR-026 through FR-030 and SC-001 through SC-008 |
| User guide and issue fragment | FR-032, evidence limits, safe resume, and operator compatibility |

Required failure cases include changed same-size bytes with restored mtime, inode/device changes, unstable reads, and `.part` interruptions.
Inject permission, stat, hash, write, replacement, store, migration, and read-back faults.
Required cases must not skip because host privileges allow access.

Stress evidence separates physical PDFs, bytes, writes, fetches, digest calls/bytes, maximum read size, and corpus walks.
Unchanged-restart and cold-cache evidence are separate.
Neither a package coverage average nor 183 reported baseline passes replaces required changed-method proof.
The three historical-manifest skips remain unavailable historical evidence.
They do not replace the new prevention proofs, which must have zero skips.

### Local and protected acceptance

The reported initial main revision is `b7ce8eecea305c20b498e12b3f3446ae662663ea`.
The protected position is 30, after issue 3575.
No remote grant exists.

A later authorized local receipt is one Conventional Commit with the exact requested `Co-authored-by` trailer.
Do not invent the trailer or commit during planning.
Run all local checks before that commit.
Then verify clean exact scope and rerun required-input preflight plus the committed-scope quality check.

Stop before push or pull request until the parent sends a full verified main SHA.
The later protected pipeline must identify the granted base and exact tested candidate.
Changed base or candidate content requires new affected evidence.
Protected merge, exact actual-main tests, image revision checks, deployment, and health checks remain conditional.
Do not claim those steps, issue closure, historical cleanup, or historical measurement as complete.

## Complexity Tracking

| Violation or exception | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Existing broad root and `src/juniper_docs` acquisition/classification hierarchies | Existing code owns the required behavior. Edit only reserved existing files. | General hierarchy restructuring crosses reservations and cannot prove this bounded fix more directly. |
| Existing class/method debt not remeasured here | The user supplied source findings and prohibited repeated source exploration. The implementation must inventory each touched limit. | Claiming compliant counts without inspection would fabricate evidence. Broad refactoring is not authorized. |
| Necessary extension of existing document, allocator, and state-store responsibilities | Two additive document fields and grouped identity metadata are required for safe persistent aliases. | A parallel index/store duplicates ownership. Artificial IDs replace natural keys. Unbounded methods are not accepted. |
| Canonical test leaf under an existing 21-child parent and one contract leaf under a 12-child parent | Exact reserved test paths give five unit files and one contract file, with bounded leaf contents. | Moving existing tests or selecting other parents violates scope. These parent additions need the recorded bounded exception, not unrelated new children. |
| Fixed feature documentation hierarchy grows from two to seven direct children | The current template requires all five named artifacts while preserving the existing spec and checklist. | Nesting or renaming artifacts breaks the explicit file-only paths. Removing prior inputs is forbidden. |
| Existing documentation/release-fragment breadth | Later work needs the existing corpus guide and one issue-owned release fragment. | README, shared CHANGELOG, and shared-record edits are forbidden. General document reorganization is unrelated. |
| Local Conventional Commit versus versioned protected release format | The user requires one local Conventional Commit. The release coordinator retains later versioned release responsibility. | Creating a release commit or claiming a full deployment now would exceed authorization. Confirm governance before an unresolved commit-format conflict. |
| No README update and no normal branch/companion-context writes | The explicit file-only fallback protects shared files and the app-managed branch. Operator changes use the reserved guide later. | Updating shared context, renaming the branch, or editing instructions would violate this grant. The normal hooked workflow remains incomplete. |

The exceptions are bounded design justifications, not proof that new implementation passes every structural rule.
Resolve any further governance conflict before implementation or commit.
Keep separate hierarchy remediation outside this issue's reserved prevention work.
