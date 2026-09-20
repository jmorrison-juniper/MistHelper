---
description: "Task list for Juniper Documentation Corpus Harvester"
---

# Tasks: Juniper Documentation Corpus Harvester

**Feature Branch**: `2738-juniper-doc-corpus-harvester`

**Input**: Design documents in `specs/2738-juniper-doc-corpus-harvester/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ (cli.md, state-store.md, manifest.md, classification.md), quickstart.md

**Tests**: Tests ARE included. The feature owner requires them. The SQLite state
store, the manifest writer, and both classifiers each get their own test. One test
proves the privacy invariant. The coverage floor is 80 percent; the repository gate is
`fail_under = 90`, which also meets the floor.

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: The task can run in parallel. It touches a different file and has no
  dependency on an unfinished task.
- **[Story]**: The user story the task serves (US1, US2, US3). Setup, Foundational,
  and Polish tasks carry no story label.
- Tick a task only after you verify the delivered file. Add an evidence note in this
  form: `(delivered: path/to/file.py)`.

## Implementation constraints (apply to every source task)

- Python 3.13 or newer. Class-based design. No wrapper function that only delegates to
  a class method.
- Five-Item Rule. At most 5 parameters, 5 logical blocks, 5 operations per block, and
  25 lines per function.
- Every executable line carries an inline comment that explains the reason.
- `logging.info` before each action. `logging.debug` after each action with a count, a
  status, or a size. Percent-style formatting. ASCII only.
- Simplified Technical English for every prose string and every log message.
- Build every path with `pathlib.Path`. Write every output under `data/`.
- Content text stays in memory only. No layer writes the extracted body text.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the package skeleton, the test skeleton, and the recorded fixtures.

- [X] T001 Create the feature package skeleton `src/juniper_docs/` with `__init__.py`, an empty `models.py`, and the four sub-package folders `discovery/`, `acquire/`, `classify/`, and `harvest/`, each with its own `__init__.py`. Confirm the package holds exactly five real children (models.py + the four sub-packages).
- [X] T002 [P] Create the test package `tests/unit/juniper_docs/` with `__init__.py` and a `fixtures/` subfolder with `__init__.py`.
- [X] T003 [P] Add recorded fixtures under `tests/unit/juniper_docs/fixtures/`: `sitemap_index.xml` (index that names child sitemaps), `sitemap_subset.xml` (one US and EN child), a root index page HTML that names one `.pdf`, a second root index page HTML that names several `.pdf` references, a sample `__toc.js`, a minimal valid file that starts with `%PDF`, and an HTML error page served with status 200 (a non-PDF body).
- [X] T004 [P] Confirm the repository quality gates in `pyproject.toml` cover `src/juniper_docs` and `tests/unit/juniper_docs` (coverage `source`, and the ruff, black, mypy, pydocstyle, interrogate, radon, and vulture paths). Record any addition the new package needs.

**Checkpoint**: The package tree, the test tree, and the fixtures exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared models, the HTTP and TLS configuration, the class promotion out of
`scripts/`, and the durable state store. Every user story depends on this phase.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Shared models and HTTP configuration

- [X] T005 [P] Implement `src/juniper_docs/models.py`: the `HarvestStage` enum (discovered, resolved, downloaded, classified, failed, dropped), the `DocumentType` enum (html_root, direct_pdf), and the dataclasses `InventoryRecord`, `PdfCandidate`, `ManifestEntry`, and `ContentAnalysisResult`. The `ContentAnalysisResult` dataclass holds `sub_category`, `detected_signals`, `scores`, and `is_fallback` and has NO field for body text (FR-024, SC-005). (depends on T001)
- [X] T006 Create `src/juniper_docs/acquire/http_config.py` with `HttpConfig`: the base origin (`SITE`), the request `HEADERS`, `TIMEOUT_SECONDS`, and `DELAY_SECONDS`. Move these constants out of `scripts/crawl_jvd.py`. (depends on T001)

### TLS decision (explicit)

- [X] T007 In `src/juniper_docs/acquire/http_config.py`, add the SSL-context builder for `--tls-mode` (`auto`, `verify`, `insecure`). `auto` and `verify` build the context from the repository root CA file `zscaler-root-ca.crt` and verify normally. The `insecure` fallback disables verification, logs a loud `logging.warning`, and carries exactly one justified `# nosec B323` annotation. Prefer the fix (certificate verification through the Zscaler root CA) over a blanket suppression. (depends on T006)
- [X] T008 [P] Unit test `tests/unit/juniper_docs/test_http_config.py`: `auto` selects the CA-verified context when `zscaler-root-ca.crt` is present; the `insecure` fallback emits the warning; only the fallback path carries the annotation. (depends on T007)

### Promote the reused classes (no compatibility shim)

- [X] T009 [P] Move `JvdCatalogClient` into `src/juniper_docs/acquire/catalog_client.py`. Source the base origin, headers, timeout, and SSL context from `HttpConfig`. Reuse the proven class; do not rewrite it (FR-018). (depends on T006, T007)
- [X] T010 [P] Move `JvdPdfResolver` into `src/juniper_docs/acquire/pdf_resolver.py`. Keep the proven index-page-then-`__toc.js` read order (FR-013). (depends on T006, T007)
- [X] T011 [P] Move `JvdDownloader` into `src/juniper_docs/acquire/downloader.py`. Keep the write, the skip, and the `%PDF` check (FR-018). (depends on T006, T007)
- [X] T012 [P] Move `ReleaseNoteSelector` and `ReleaseNoteKey` into `src/juniper_docs/discovery/release_note_selector.py`. Reuse the proven class; do not rewrite it (FR-008). (depends on T005)
- [X] T013 Update `scripts/crawl_jvd.py` to import `JvdCatalogClient`, `JvdPdfResolver`, `JvdDownloader`, and the shared constants from `src/juniper_docs/acquire`, and keep only `JvdCatalogWalker` and `JvdCrawlRunner`. Update `scripts/jvd_doc_selector.py` to import `ReleaseNoteSelector` from `src/juniper_docs/discovery`. Use a direct import. Add NO re-export stub and NO compatibility shim. (depends on T009, T010, T011, T012)
- [X] T014 Re-verify the existing 46-file JVD crawl still works after the move. Run `scripts/crawl_jvd.py` (against the recorded fixtures or a bounded live run) and confirm the crawl resolves and downloads the same 46 files as before the move. Record the evidence. (depends on T013)

### Durable state store

- [X] T015 Implement `HarvestStateStore` in `src/juniper_docs/harvest/state_store.py`: the full schema (`documents`, `pdf_candidates`, `content_scores` with NO text column, `dropped_release_notes`, `run_meta`), the pragmas (`journal_mode=WAL`, `synchronous=FULL`, `foreign_keys=ON`), one transaction per stage change, the file-before-state durable write, the verified read-back, the resume query for non-final rows, and the fail-closed behavior on a locked or damaged store (FR-031, FR-032, FR-033, FR-034). (depends on T005)
- [X] T016 [P] Unit test `tests/unit/juniper_docs/test_state_store.py`: assert `content_scores` has no text column; verify the durable write plus verified read-back; the resume query returns only non-final rows; a repeated run reprocesses only new, failed, or non-final rows; the store fails closed on a locked database. (depends on T015)

**Checkpoint**: The shared foundation is ready. `scripts/crawl_jvd.py` still works. User
story implementation can now begin.

---

## Phase 3: User Story 1 - Download the filtered corpus with a manifest (Priority: P1) 🎯 MVP

**Goal**: From a cold start, read the sitemap index and the 16 US and EN child sitemaps,
build the inventory, drop each superseded release note, resolve one companion PDF for
each root, download and validate each PDF, sort each file into a slug category, and write
the manifest and the final summary.

**Independent Test**: Point the runner at the recorded sitemap subset. Confirm it builds
the inventory and applies the release-note filter, resolves and downloads each companion
PDF, sorts the files by slug category, and writes a manifest where each document shows a
source URL, a category, a file size, and a status.

### Tests for User Story 1 (write first; confirm they fail before implementation)

- [X] T017 [P] [US1] Unit test `tests/unit/juniper_docs/test_sitemap_reader.py`: the reader parses the index and a child sitemap and extracts every URL (FR-001, FR-002).
- [X] T018 [P] [US1] Unit test `tests/unit/juniper_docs/test_inventory_builder.py`: the builder maps a `/topics/` chapter to its parent root, removes a URL that appears in two child sitemaps, and splits the inventory into html_root and direct_pdf (FR-003, FR-004).
- [X] T019 [P] [US1] Unit test `tests/unit/juniper_docs/test_release_note_selector.py`: the selector keeps the newest note for each product and major train, keeps a note with no parseable version, and records each dropped root with a reason (FR-006, FR-007, FR-009).
- [X] T020 [P] [US1] Unit test `tests/unit/juniper_docs/test_companion_pdf_resolver.py`: on a multi-PDF index page the resolver applies the fixed order (name match, then same-folder first, then largest), returns exactly one chosen candidate, and records each rejected candidate; a root with no PDF yields a "no PDF found" result (FR-010a, FR-010b, FR-012).
- [X] T021 [P] [US1] Unit test `tests/unit/juniper_docs/test_corpus_downloader.py`: the downloader accepts a body that starts with `%PDF`, skips a target that already exists with more than zero bytes, and rejects a zero-byte or non-PDF response as failed (FR-014, FR-015, FR-019).
- [X] T022 [P] [US1] Unit test `tests/unit/juniper_docs/test_slug_classifier.py`: the classifier matches each of the nine categories, applies the fixed precedence when two keywords match, and returns `uncategorized` when no keyword matches (FR-020, FR-021).
- [X] T023 [P] [US1] Unit test `tests/unit/juniper_docs/test_manifest_writer.py`: the writer renders JSON and CSV from the store, covers 100 percent of the inventory, records the chosen PDF and each rejected candidate, lists each dropped release note, and writes no body-text field (FR-028, SC-004).
- [X] T024 [P] [US1] Unit test `tests/unit/juniper_docs/test_runner.py`: with mocked HTTP and the fixture subset, the cold run records the inventory before any download, then resolves, downloads, classifies, and writes the manifest and the summary (SC-001).

### Implementation for User Story 1

- [X] T025 [P] [US1] Implement `SitemapReader` in `src/juniper_docs/discovery/sitemap_reader.py`: read the index, read each of the 16 US and EN child sitemaps, and extract every URL (FR-001, FR-002).
- [X] T026 [P] [US1] Implement `InventoryBuilder` in `src/juniper_docs/discovery/inventory_builder.py`: map each `/topics/` chapter to its parent root, remove a duplicate URL, split into html_root and direct_pdf, and save the inventory to the store before any download (FR-003, FR-004, FR-005).
- [X] T027 [US1] Add `CorpusReleaseNoteSelector(ReleaseNoteSelector)` to `src/juniper_docs/discovery/release_note_selector.py`: keep the newest note for each product and major train, keep an unparseable note, and record each dropped root and reason in the store (FR-006, FR-007, FR-009). (depends on T012)
- [X] T028 [P] [US1] Add `CompanionPdfResolver(JvdPdfResolver)` to `src/juniper_docs/acquire/pdf_resolver.py`: read the index page first and the `__toc.js` second, collect every `.pdf` reference, select by the fixed order, and return the chosen URL plus the rejected candidates; record a "no PDF found" result when none is found (FR-010, FR-010a, FR-010b, FR-011, FR-012). (depends on T010)
- [X] T029 [P] [US1] Add `CorpusDownloader(JvdDownloader)` to `src/juniper_docs/acquire/downloader.py`: reuse the base write, skip, and `%PDF` check; mark a zero-byte or non-PDF response as failed; never count it as a success (FR-014, FR-015, FR-019). (depends on T011)
- [X] T030 [P] [US1] Implement `SlugClassifier` in `src/juniper_docs/classify/slug_classifier.py`: the keyword map for the nine categories, the fixed precedence order, and the `uncategorized` fallback (FR-020, FR-021).
- [X] T031 [P] [US1] Implement `ManifestWriter` in `src/juniper_docs/harvest/manifest_writer.py`: render `manifest.json` and `manifest.csv` from the store, cover every inventory document with a final status, record the chosen PDF and each rejected candidate, and list each dropped release note. The manifest has no body-text field (FR-028, FR-024, SC-004, SC-005). (depends on T015)
- [X] T032 [US1] Implement `HarvestConfig` and `HarvestRunner` in `src/juniper_docs/harvest/runner.py` for the cold run: build the config from the arguments with safe defaults, wire `--tls-mode` to `HttpConfig`, then orchestrate discovery, the release-note filter, PDF resolution, download, slug classification, and the durable per-stage write to the store. Arrange each file under `data/juniper_corpus/<category>/` with a Windows-safe, sanitized name built from `pathlib.Path`. Log the progress (the current stage and the completed count out of the total) and print the final summary (the count for each category, the downloaded, skipped, failed, and dropped counts, and the total bytes) (FR-016 default, FR-027, FR-029, FR-030, FR-035, FR-036). (depends on T025, T026, T027, T028, T029, T030, T031, T015, T007)
- [X] T033 [US1] Add the thin entry block to `src/juniper_docs/harvest/runner.py` (`HarvestRunner(HarvestConfig.from_args()).run()`), and confirm `python -m src.juniper_docs.harvest.runner --sitemap-source tests/unit/juniper_docs/fixtures/sitemap_subset.xml` runs the cold pipeline end to end. (depends on T032)

**Checkpoint**: User Story 1 is a working MVP. The harvester downloads the filtered
corpus, sorts it by slug category, and writes the manifest and the summary.

---

## Phase 4: User Story 2 - Content-derived sub-categories for uncategorized documents (Priority: P2)

**Goal**: For each `uncategorized` document, read a bounded PDF text sample in memory,
derive a reproducible sub-category label from the content signals, persist only the label,
the detected signal names, and the numeric scores, and place the file in a sub-category
folder. Keep no body text anywhere.

**Independent Test**: Give the runner a set of downloaded uncategorized PDFs. Confirm each
document gets a sub-category label, detected signal names, and numeric scores in the store,
the output tree gains a folder for each sub-category, and no document body text exists on
disk.

### Tests for User Story 2 (write first; confirm they fail before implementation)

- [X] T034 [P] [US2] Unit test `tests/unit/juniper_docs/test_content_sampler.py`: the sampler reads the title page, the table-of-contents pages, and the first few body pages up to `--max-sample-pages`, returns one local string, and returns empty text for an image-only or malformed PDF (FR-022, FR-025).
- [X] T035 [P] [US2] Unit test `tests/unit/juniper_docs/test_signal_scorer.py`: the scorer scores the three signal groups, builds the `<product_family>__<task_type>__<technology_domain>` label, returns the `unclassified-content` fallback with empty scores when no group reaches the `2.0` threshold, and never gives a low-confidence document a wrong label (FR-023, FR-023a, FR-023b, FR-025a).
- [X] T036 [P] [US2] Unit test `tests/unit/juniper_docs/test_privacy_invariant.py` (explicit privacy proof): assert `ContentAnalysisResult` has no text field; assert the `content_scores` table has no text column; assert `manifest.json` and `manifest.csv` have no body-text field; after a classify run on a fixture PDF, assert the sampled body-text string appears in NO file under the output tree and in NO store row (FR-024, SC-005).

### Implementation for User Story 2

- [X] T037 [P] [US2] Implement `ContentSampler` in `src/juniper_docs/classify/content_sampler.py`: use `pdfplumber` to read the bounded sample (title page, table-of-contents pages, and the first few body pages up to `--max-sample-pages`, default 8), return one local string, and add no network load. The repository already declares `pdfplumber>=0.11.0` (FR-022, FR-026).
- [X] T038 [P] [US2] Implement `SignalScorer` in `src/juniper_docs/classify/signal_scorer.py`: score the product-family, task-type, and technology-domain groups by keyword frequency, build the reproducible label from the highest-scoring signal in each group, apply the `2.0` confidence threshold, and return the fixed `unclassified-content` fallback with empty scores for weak or unreadable input (FR-023, FR-023a, FR-023b, FR-025, FR-025a).
- [X] T039 [US2] Wire the content sub-category step into `HarvestRunner`: for each `uncategorized` document, sample the PDF, score the sample, persist the label, the detected signal names, and the numeric scores to `content_scores`, set `documents.sub_category` and `is_fallback`, arrange the file under `data/juniper_corpus/uncategorized/<label>/`, and set the manifest `sub_category`. Let the text string go out of scope; write it nowhere (FR-024, FR-027, SC-005, SC-007). (depends on T032, T037, T038, T015)
- [X] T040 [US2] Extend the final summary in `HarvestRunner` with the count for each derived sub-category (FR-036, SC-009). (depends on T039)

**Checkpoint**: User Stories 1 and 2 both work. Uncategorized documents now carry a
content-derived sub-category, and the privacy invariant holds.

---

## Phase 5: User Story 3 - A resumable, polite, and fault-tolerant long run (Priority: P3)

**Goal**: Make the multi-hour, thousands-of-document run practical. Resume from the tracked
state with no re-download, pace the requests, and let one bad document fail without a stop
to the whole run.

**Independent Test**: Interrupt a run and start it again; confirm zero completed documents
re-download. Inject a 404 error and a timeout on single documents; confirm the run
continues, records the failures, and exits 0. Measure the delay between two requests.

### Tests for User Story 3 (write first; confirm they fail before implementation)

- [X] T041 [US3] Add resume, politeness, and fault-tolerance cases to `tests/unit/juniper_docs/test_runner.py`: a restart re-downloads zero completed documents (SC-003); the runner waits at least the configured minimum delay between two requests (SC-008); an injected 404, timeout, and non-PDF body are each recorded and the run continues with exit code 0 (SC-006); `--retry-failed` reprocesses only failed documents; a partial file is not marked complete (edge case). (depends on T032; same file as T024, so not parallel)

### Implementation for User Story 3

- [X] T042 [US3] Add resume orchestration to `HarvestRunner`: on start, query the store for non-final rows and continue each document from its current stage; never re-download a completed document; a repeated run reprocesses only new, failed, or non-final documents (FR-031, FR-032, FR-034, SC-003). (depends on T032, T015)
- [X] T043 [US3] Add politeness pacing to `HarvestRunner`: wait at least `--delay-seconds` (default 1.0) between two requests to the Juniper host (FR-016, SC-008). (depends on T032)
- [X] T044 [US3] Add per-document fault tolerance to `HarvestRunner`: wrap each per-document step in a try and except block that records the failure (a 404, a timeout, a connection reset, or a non-PDF body) against that document and continues; one bad document never stops the run (FR-017, SC-006). (depends on T032)
- [X] T045 [US3] Wire the `--retry-failed` flag in `HarvestConfig` and `HarvestRunner`: reprocess a document whose stage is `failed` (cli.md, FR-034). (depends on T042)
- [X] T046 [US3] Add the fail-closed exit behavior to `HarvestRunner`: exit 0 when every document reaches a final stage even if failures are recorded; exit 1 when the store is locked or damaged or the disk is full; exit 2 on an invalid argument. Never report progress the tool cannot confirm (cli.md, FR-033, SC-006, SC-010). (depends on T032, T015)

**Checkpoint**: All three user stories work independently. The full 2,225-document run is
resumable, polite, and fault tolerant.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: The release-note fragment, the repository quality gates, and the quickstart
validation.

- [X] T047 [P] Add the release-note fragment `changelog.d/issue-2738-juniper-doc-corpus-harvester.md`. Write one `###` heading and `Added`, `Changed`, and `Security` bullets that name issue #2738. Do NOT edit `CHANGELOG.md`.
- [X] T048 [P] Gate: `ruff check src/juniper_docs tests/unit/juniper_docs` reports no error.
- [X] T049 [P] Gate: `black --check src/juniper_docs tests/unit/juniper_docs` reports no change (line length 120).
- [X] T050 [P] Gate: `mypy src/juniper_docs` reports no error.
- [X] T051 [P] Gate: `pydocstyle src/juniper_docs` reports no error (google convention).
- [X] T052 [P] Gate: `interrogate src/juniper_docs` passes (`fail_under = 90`).
- [X] T053 [P] Gate: `radon cc src/juniper_docs -nc` shows every function at complexity 10 or below.
- [X] T054 [P] Gate: `vulture src/juniper_docs` reports no dead code.
- [X] T055 [P] Gate: `bandit -r src/juniper_docs` reports only the single justified `# nosec B323` on the TLS fallback and no other suppression.
- [X] T056 [P] Gate: `pylint src/juniper_docs` scores 9.5 or above (research.md section 11).
- [X] T057 [P] Gate: `pytest tests/unit/juniper_docs --cov=src/juniper_docs --cov-report=term-missing`. Every test passes and coverage is 90 percent or higher, which also meets the 80 percent floor. Every HTTP read is mocked; no test makes a live network call.
- [X] T058 Run the `quickstart.md` validation: the cold run on the fixture subset, the resume check, the politeness check, and the privacy audit commands. Confirm each expected outcome. (depends on all earlier phases)

---

## Phase 7: Post-plan discoveries and repairs

**Purpose**: Record the extra corpus sources and the repairs. These changes came
after the plan. Each task states the current state. The [X] mark means the code shows
the change now. The [ ] mark means a follow-up remains. The validation covered 46
real PDF files. The content classifier labeled 46 of 46, used no fallback bucket, and
produced 18 distinct labels. The mean cost was 1.243 seconds for each file, so the
full corpus adds about 46 minutes.

- [X] T059 Add the marketing sitemap source. `SitemapReader.read_pdf_urls` reads the flat marketing sitemap and keeps every direct PDF URL. `MarketingAssetClassifier` sorts each asset by its asset-type path segment. `HarvestRunner` gains the `--source` option (`documentation`, `marketing`, `both`) and the `--marketing-sitemap-source` option, and it removes a marketing PDF that the documentation sitemap already lists (FR-005a, FR-005b, FR-005c, FR-005e). (delivered: src/juniper_docs/discovery/sitemap_reader.py, src/juniper_docs/classify/asset_classifier.py, src/juniper_docs/harvest/runner.py)
- [ ] T060 Add the product landing family source. Read the 363 landing pages under `/documentation/product/`, extract each linked PDF, and add each PDF to the inventory. A sample of 10 pages found 25 unique PDF files, so 25 is a measured lower bound while the full 244-page scan is pending (FR-005d).
- [X] T061 Repair the release-note train key. `ReleaseNoteSelector` reads the product family from the document name, keys the train by product, major, minor, and X-build, parses the D revision, and skips a locale segment. The `collapse_to_major` option collapses the train to the major version. The repaired filter keeps 822 notes and drops 151 on the current corpus. Before the repair it kept 589 and dropped 384. No drop was wrong (FR-006, FR-006a). (delivered: src/juniper_docs/discovery/release_note_selector.py)
- [X] T062 Repair the content classifier product-family signal (Defect A). `SignalScorer` counts each keyword on a word boundary, so a short token no longer matches inside a longer, unrelated word. A file-name hit outweighs a body hit by `NAME_WEIGHT`, so a file named for SRX no longer scores as Mist. (delivered: src/juniper_docs/classify/signal_scorer.py)
- [ ] T063 Wire the file name into the content classifier (Defect A). `HarvestRunner._classify_content` still calls `self.classify.scorer.score(text)` with no file name. Change the call to `self.classify.scorer.score(text, Path(local_path).name)`, so the scorer reads the reliable subject hint from the file name (src/juniper_docs/harvest/runner.py).
- [X] T064 Repair the constant task-type segment (Defect B). `SignalScorer` keeps the task segment only when the top task type leads the second task type by `TASK_MARGIN`. A common `configuration` token no longer forces a constant middle segment. (delivered: src/juniper_docs/classify/signal_scorer.py)
- [X] T065 Add the missing technology-domain signals (Defect C). `SignalScorer` gains a `gpu-cluster` signal for the AI cluster topic and an `evpn-vxlan` signal for the fabric topic, so the main data-center documents keep a distinct subject. (delivered: src/juniper_docs/classify/signal_scorer.py)
- [X] T066 Normalize the confidence score (Defect D). `SignalScorer` divides the weighted hit count by the sample length in thousands of characters, so the score means the strength of the match, not the length of the document. The `CONFIDENCE_THRESHOLD` constant is `0.25`. (delivered: src/juniper_docs/classify/signal_scorer.py)
- [ ] T067 Align the runner confidence threshold with the normalized score (Defect D). `TuningConfig.confidence_threshold` and the `--confidence-threshold` default are still `2.0`, which is the pre-repair scale. `HarvestRunner` builds `SignalScorer(config.tuning.confidence_threshold)`, so the run passes `2.0` to the normalized scorer. Set the default to the normalized scale (src/juniper_docs/harvest/runner.py).
- [X] T068 Repair the HTML root normalization. `InventoryBuilder._root_of` keeps a legacy `.html` page as the root and never appends a trailing slash, so no resolved URL ends in `.html/`. The live smoke run after the repair shows zero URLs that end in `.html/`. That run classified 298 documents and recorded 45 no-PDF, 41 dropped, and 16 failed. (delivered: src/juniper_docs/discovery/inventory_builder.py)
- [ ] T069 Repair the `auto` TLS fallback. `HttpConfig._auto_context` falls back to the insecure context only when the CA file is absent, not when verification fails, which does not match the name `auto`. The production run uses `verify`, so this is a tracked follow-up (src/juniper_docs/acquire/http_config.py). See research.md section 15.

**Checkpoint**: The marketing sitemap source and the four repairs are in the code. The
product landing source, the two classifier wiring tasks, and the `auto` TLS repair
remain.

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (Phase 1)**: No dependency. Start immediately.
- **Foundational (Phase 2)**: Depends on Setup. Blocks every user story.
- **User Stories (Phase 3, 4, 5)**: Each depends on Foundational. After Foundational,
  the stories may proceed in parallel (if staffed) or in priority order P1, then P2,
  then P3. US2 and US3 extend the `HarvestRunner` that US1 delivers.
- **Polish (Phase 6)**: Depends on the desired user stories being complete.

### Critical path

- The class promotion (T009 to T013) and the JVD re-verify (T014) sequence the move so
  `scripts/crawl_jvd.py` keeps working with a direct import and no shim.
- The state store (T015) blocks every stage write, the manifest, and the resume.
- The runner (T032) is the integration point that US2 (T039, T040) and US3 (T042 to
  T046) extend.

### User story dependencies

- **US1 (P1)**: Starts after Foundational. No dependency on US2 or US3.
- **US2 (P2)**: Starts after Foundational. Extends the US1 runner (T039 depends on T032).
- **US3 (P3)**: Starts after Foundational. Extends the US1 runner (T042 to T046 depend
  on T032).

### Within each user story

- Write the tests first and confirm they fail before the implementation.
- Discovery and models before the runner. The runner before US2 and US3 wiring.
- A story is testable on its own once its tasks pass.

### Parallel opportunities

- Setup tasks T002, T003, and T004 run in parallel.
- Foundational: T005 runs in parallel with the move; the four move tasks T009, T010,
  T011, and T012 run in parallel (each writes a different new file), then T013 joins
  them; T008 and T016 run in parallel with other tests.
- US1 tests T017 to T024 run in parallel. US1 implementations T025, T026, T028, T029,
  T030, and T031 run in parallel (different files); T027 waits for T012; T032 joins them.
- US2 tests T034, T035, and T036 run in parallel; implementations T037 and T038 run in
  parallel, then T039 joins them.
- Polish gates T047 to T057 run in parallel.

---

## Parallel Example: User Story 1 tests

```bash
# Launch every US1 test file together (they touch different files):
Task: "Unit test tests/unit/juniper_docs/test_sitemap_reader.py"
Task: "Unit test tests/unit/juniper_docs/test_inventory_builder.py"
Task: "Unit test tests/unit/juniper_docs/test_release_note_selector.py"
Task: "Unit test tests/unit/juniper_docs/test_companion_pdf_resolver.py"
Task: "Unit test tests/unit/juniper_docs/test_corpus_downloader.py"
Task: "Unit test tests/unit/juniper_docs/test_slug_classifier.py"
Task: "Unit test tests/unit/juniper_docs/test_manifest_writer.py"
Task: "Unit test tests/unit/juniper_docs/test_runner.py"
```

## Parallel Example: the class promotion

```bash
# Move the four reused classes into the package in parallel (different new files):
Task: "Move JvdCatalogClient into src/juniper_docs/acquire/catalog_client.py"
Task: "Move JvdPdfResolver into src/juniper_docs/acquire/pdf_resolver.py"
Task: "Move JvdDownloader into src/juniper_docs/acquire/downloader.py"
Task: "Move ReleaseNoteSelector into src/juniper_docs/discovery/release_note_selector.py"
# Then run T013 (update the scripts) and T014 (re-verify the 46-file crawl).
```

---

## Implementation Strategy

### MVP first (User Story 1 only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational (the move, the JVD re-verify, and the state store).
3. Complete Phase 3: User Story 1.
4. STOP and VALIDATE. Run the cold pipeline on the fixture subset. Confirm the inventory,
   the release-note filter, the download, the slug categories, and the manifest.
5. This is a shippable MVP: the whole filtered corpus on disk with a manifest.

### Incremental delivery

1. Setup and Foundational give the shared base and keep the JVD crawl working.
2. Add User Story 1. Test it. Ship the corpus and the manifest.
3. Add User Story 2. Test it. Ship the content-derived sub-categories and the privacy proof.
4. Add User Story 3. Test it. Ship the resumable, polite, fault-tolerant run.
5. Run the Polish gates and the quickstart validation.
