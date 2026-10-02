# Tasks: Canonical Corpus Documents

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), and [storage contract](contracts/storage.md).

**Template**: [.specify/templates/tasks-template.md](../../.specify/templates/tasks-template.md).

**Validation guide**: [quickstart.md](quickstart.md).

## Execution boundary

This work implements the available code-prevention portion of issue 2977.
The app owns `jmorrison-juniper-canonical-corpus-documents`.
Legacy branch validation refused that name.
The workflow therefore uses the authorized file-only fallback.
It changes no shared `.specify` state, branch hooks, dependency manifests, baselines, or exclusions.

The initial main revision is `b7ce8eecea305c20b498e12b3f3446ae662663ea`.
Position 30 follows issue 3575.
An initial revision or another session's result is not remote permission.
No push or pull request is authorized before the parent's full verified main-SHA grant.

The initial harvest suite had 183 passes and three historical-manifest skips.
Those skips require the absent `data/juniper_corpus_smoke/manifest.json`.
All committed parser fixtures exist.
Keep the historical tests and parser fixtures unchanged.
Every new prevention case must run without a skip.

## Format

Each task has one ID and an evidence path.
`[P]` identifies independent file work, not permission to create another agent.
Keep blocked remote and historical tasks unchecked.
Record the local commit receipt outside tracked files.
Do not create another commit to record that receipt.

## Phase 1: Setup

- [x] T001 Verify issue ownership, the authenticated account, and every open pull request's exact file list.
  Claim issue 2977 and reserve this worktree's exact scope. (delivered: issue 2977 reservation comment)
- [x] T002 Generate the unique specification and design through the current SpecKit templates.
  Preserve the app branch and use the file-only fallback. (delivered: specs/2977-canonical-corpus-documents/spec.md)
- [x] T003 Record the pre-change suite and reproduce the actual duplicate write before production edits.
  Two URLs, names, and categories produce two files, 68 bytes, and two writes.
  (delivered: tests/unit/juniper_docs/canonical/test_download_flow.py)

## Phase 2: Shared foundation

- [x] T004 Add nullable digest/name fields without changing natural source URL keys.
  (delivered: src/juniper_docs/models.py)
- [x] T005 Implement atomic version-1 migration with a WAL-safe SQLite backup.
  Reject unsupported or incompatible input and retain existing backups.
  (delivered: src/juniper_docs/harvest/state_store.py)
- [x] T006 Persist validated path metadata and independently verify required alias transactions.
  Preserve original candidates, categories, labels, reasons, and stages.
  (delivered: src/juniper_docs/harvest/state_store.py)
- [x] T007 Prove migration, backup contents, rejected writes, and independent verification failures.
  Compare complete legacy values through actual SQLite connections.
  (delivered: tests/unit/juniper_docs/canonical/test_state_migration.py)

## Phase 3: US1 - Store equal content once

- [x] T008 Select full SHA256 content before collision-safe filename allocation.
  Preserve different bytes, occupied variants, relative paths, and original names.
  (delivered: src/juniper_docs/acquire/pdf_paths.py)
- [x] T009 Retain atomic `.part` publication and the existing four-item download result.
  Verify required state before a successful download or skip.
  (delivered: src/juniper_docs/acquire/downloader.py)
- [x] T010 Prove actual equal-content, distinct-content, HTTP, invalid-body, and interruption behavior.
  Preserve the existing prefix check without a new EOF or parser rule.
  (delivered: tests/unit/juniper_docs/canonical/test_download_flow.py)

## Phase 4: US2 - Resume with valid evidence

- [x] T011 Validate current URL pointers, full stat identity, and expected content after restart.
  Detect missing files, restored-mtime corruption, unstable reads, and access failures.
  (delivered: src/juniper_docs/acquire/pdf_paths.py)
- [x] T012 Use native Windows `FILE_BASIC_INFO` change time, not creation time.
  Reject unavailable clocks and unrepresentable SQLite identity values.
  Prove the ABI and actual download decisions with a local native-interface test double.
  (delivered: tests/unit/juniper_docs/canonical/test_content_index.py)
- [x] T013 Validate classified files before the runner accepts a completed resume.
  Restore valid content or record an explicit failure.
  Count success only after durable state completion.
  (delivered: src/juniper_docs/harvest/runner.py)
- [x] T014 Repair all expected-digest aliases without redirecting other URLs after a changed response.
  (delivered: tests/unit/juniper_docs/canonical/test_state_migration.py)

## Phase 5: US3 - Preserve provenance and path consumers

- [x] T015 Append manifest digest/name fields and preserve every source entry.
  Count equivalent canonical paths once and reject conflicting recorded byte counts.
  (delivered: src/juniper_docs/harvest/manifest_writer.py)
- [x] T016 [P] Keep shared payloads in place during alias-specific reclassification.
  Use each original URL name for its label.
  (delivered: src/juniper_docs/classify/reclassifier.py)
- [x] T017 [P] Sort one physical payload and update every affected alias.
  Preserve default dry runs, equal-content historical files, and repeated-pass idempotence.
  (delivered: src/juniper_docs/classify/manual_sorter.py)
- [x] T018 Prove every existing crawl source, safe moves, alias lookup after moves, and failed persistence.
  Use original constructed PDF data and the existing real parser.
  (delivered: tests/unit/juniper_docs/canonical/test_path_consumers.py)
- [x] T019 Render and inspect actual JSON and CSV contracts, including failed response records.
  (delivered: tests/contract/juniper_docs/test_canonical_manifest.py)

## Phase 6: US4 - Bound discovery, hashing, and memory

- [x] T020 Measure 1,000 novel URLs for 20 original 8 KiB payloads.
  Require one walk, 20 writes, 20 physical files, and 163,840 stored bytes.
  Measure fetched and stored hash work separately.
  (delivered: tests/unit/juniper_docs/canonical/test_content_index.py)
- [x] T021 Reopen the store, allocator, and downloader, then verify all 1,000 aliases.
  Require one walk and zero new fetches, writes, or stored hashes.
  Independently measure cold-cache `S + U + C` hash bytes with pre-existing larger payloads.
  Enforce 1 MiB reads and measured allocation limits.
  (delivered: tests/unit/juniper_docs/canonical/test_content_index.py)

## Phase 7: Local quality and documentation

- [x] T022 Add the operator guide and one issue-owned release fragment.
  State the transfer and historical limits.
  (delivered: documentation/free-juniper-corpus.md)
- [x] T023 Run every prevention case and the complete harvest regression suite.
  Require at least 90 percent package coverage and 80 percent for every changed production method.
  Keep the three unavailable historical cases separate.
  (delivered: tests/unit/juniper_docs/canonical)
- [x] T024 Run full configured Ruff, Black, exact CI mypy, Bandit, complexity, Pylint, Vulture, and documentation gates.
  Run required-input preflight before the unchanged full test-quality ratchet.
  Verify citations, diagrams, local Markdown links, and configured STE.
  (delivered: specs/2977-canonical-corpus-documents/quickstart.md)
- [x] T025 Attempt the strict standard dependency audit and record its `ensurepip` abort.
  Resolve all unchanged runtime dependencies with complete UV hashes.
  Require a strict `--require-hashes --no-deps --disable-pip` audit.
  Report that the Git-only devtools tree and absent licensed STE dictionary remain outside verified scope.
  (delivered: specs/2977-canonical-corpus-documents/quickstart.md)

## Local receipt procedure

Complete final checks before the single local Conventional Commit.
Stage only the exact reservation.
Use `Refs #2977`, not an issue-closing statement.
Include this trailer:

```text
Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>
```

Verify clean relevant content and the complete committed file list.
Repeat the packaged link check after commit.
Record SHA, commands, results, measured counts, and limits in session artifacts and the parent message.
Do not amend the commit or create a progress-only commit.
Stop before remote actions.

## Blocked acceptance

- [ ] T026 Obtain the parent's full verified main-SHA grant after position 29 proof.
  Recheck ownership and open pull request file lists.
  (blocked: no remote grant)
- [ ] T027 Fetch and verify the granted `origin/main`, then rebase only this app branch if needed.
  Restore current requirements only if needed and repeat affected local checks.
  Run required-input preflight before the required committed-scope analyzer.
  The fetch destination, resolved reference, granted SHA, and comparison reference must agree.
  (blocked: T026)
- [ ] T028 Push once and use the full repository pull request template.
  Require title, STE, CodeQL analysis/status, and every quality check.
  Squash only exact approved heads through protected main without an administrator override.
  (blocked: T027)
- [ ] T029 Verify the actual merged SHA and exact-main local tests in this isolated workspace.
  Do not use a predicted merge revision or another child's result.
  (blocked: T028)
- [ ] T030 Measure the original historical corpus only after separate data authorization.
  Do not delete, rename, consolidate, or fabricate historical evidence.
  Keep issue 2977 open while its historical acceptance remains unproved.
  (blocked: the historical Windows corpus is absent and unauthorized)

## Dependencies and execution order

Setup and the real-flow red proof precede production edits.
Foundation supplies durable identity for content lookup and resume.
Content lookup precedes alias-safe consumer integration.
Measured tests precede final gates and the local commit.
Only T016 and T017 permit independent file work after the common state operations exist.
T026 through T029 require their preceding blocked task.
T030 has independent historical-data authorization.

## Exact reservation

```text
src/juniper_docs/acquire/pdf_paths.py
src/juniper_docs/acquire/downloader.py
src/juniper_docs/harvest/state_store.py
src/juniper_docs/harvest/manifest_writer.py
src/juniper_docs/harvest/runner.py
src/juniper_docs/models.py
src/juniper_docs/classify/reclassifier.py
src/juniper_docs/classify/manual_sorter.py
tests/unit/juniper_docs/canonical/conftest.py
tests/unit/juniper_docs/canonical/test_download_flow.py
tests/unit/juniper_docs/canonical/test_content_index.py
tests/unit/juniper_docs/canonical/test_path_consumers.py
tests/unit/juniper_docs/canonical/test_state_migration.py
tests/contract/juniper_docs/test_canonical_manifest.py
documentation/free-juniper-corpus.md
changelog.d/issue-2977-canonical-corpus-documents.md
specs/2977-canonical-corpus-documents/spec.md
specs/2977-canonical-corpus-documents/plan.md
specs/2977-canonical-corpus-documents/tasks.md
specs/2977-canonical-corpus-documents/research.md
specs/2977-canonical-corpus-documents/data-model.md
specs/2977-canonical-corpus-documents/quickstart.md
specs/2977-canonical-corpus-documents/contracts/storage.md
specs/2977-canonical-corpus-documents/checklists/requirements.md
```

These 24 files are the complete intended commit scope.
Keep README, CHANGELOG, shared instructions, parser fixtures, dependency pins, baselines, and exclusions unchanged.
