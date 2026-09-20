# Feature Specification: Juniper Documentation Corpus Harvester

**Feature Branch**: `feat/2738-juniper-doc-corpus-harvester`

**Created**: 2026-09-16

**Status**: Draft

**Input**: User description: "Create a feature specification for a Juniper documentation corpus harvester with content-derived sub-categorization."

## Overview

The Juniper documentation site publishes a sitemap index. The US and EN part holds 16 child sitemaps and about 75,774 URLs. These URLs reduce to about 2,225 documents that the system can download. The set holds about 1,591 HTML document roots and about 634 direct PDF files. Each HTML root publishes one companion PDF that holds every chapter. The estimated total size is 5 to 25 GB.

The documentation sitemap is not the only source. The Juniper marketing sitemap at `https://www.juniper.net/sitemaps/en_US.xml` holds 2,130 entries, and 778 of them are direct PDF files. These marketing assets hold the datasheets, the solution briefs, the case studies, and the white papers that the documentation sitemap does not list. The two sitemaps share 2 files, so the two sitemaps together hold 1,410 unique direct PDF files. A third source, the product landing family under `/documentation/product/`, holds 363 landing pages that cover 244 products. These landing pages link PDF files that neither sitemap lists.

This feature downloads the whole US and EN corpus to local disk. The system keeps every document except an old release note. For a release note, the system keeps only the newest note in each train. A train covers a product family, a major version, and a minor version by default. The system sorts each document into a category from the slug.

About half of the corpus matches no slug keyword. For each of those documents, the system reads the downloaded PDF and derives a sub-category from the content. The run stays polite and resumable. The operator can watch the progress and read a final summary.

## Clarifications

### Session 2026-09-16

- Q: When an index page names more than one `.pdf`, which PDF does the system choose? → A: Prefer the best name match. The best match is the PDF whose name matches the document root slug. If no name matches, prefer the first `.pdf` reference in the same folder as the index page. If a tie remains, choose the largest file. The whole-document PDF is larger than any single-chapter PDF. Record the chosen URL and each rejected candidate in the manifest.
- Q: How does the system derive the sub-category taxonomy for the uncategorized bucket? → A: Derive the taxonomy from the content signals. Extract a bounded text sample from each PDF, which is the title page, the table of contents, and the first few pages. Score the sample against three signal groups: the product family, the task type, and the technology domain. Assign a reproducible, human-readable label, or the fallback label when no signal reaches the confidence threshold. Store only the label, the detected signal names, and the numeric scores. Hold the extracted text only in memory.
- Q: Does the run download the full corpus, or a reduced set? → A: Download the whole US and EN corpus. Reduce only the release notes. Keep the newest note for each product family and major version train.
- Q: How does the release-note filter identify a train, and how many notes does it keep for one major version? → A: The train key names the product family, the major version, the minor version, and the X-build number. The filter reads the product family from the document name, not from a fixed path segment. The name is the reliable source, because Junos OS and Junos OS Evolved share the path segment `junos`, and because a PDF tree can place a locale segment where the product segment would otherwise sit. By default one train covers a major version and a minor version, so 23.1, 23.2, 23.3, and 23.4 each keep their own newest note. This default keeps more history and cannot silently lose a release the operator wanted. The `collapse_to_major` option on the selector collapses a train to the major version only, so major 23 keeps one note. An X-build, such as 23.4X100, is a special branch, not a successor to the mainstream 23.4 line. The filter gives each X-build its own train, so an X-build never evicts a mainstream R note, and the newest D revision wins inside the X-build train. The user wrote "23.x, 24.x", which is ambiguous, and the user could not confirm. The safer major and minor default answers that ambiguity without a silent loss. The failure modes are asymmetric. A few extra PDF files cost little disk space and little time. A lost release note costs a multi-hour re-run of the whole corpus. So the safer default keeps the note.

### Session 2026-09-16 (post-implementation review)

- Q: Does the run read only the documentation sitemap? → A: No. The run reads the documentation sitemap first. The run also reads the marketing sitemap at `https://www.juniper.net/sitemaps/en_US.xml`, which holds the datasheets and the other marketing assets. A third source, the product landing family under `/documentation/product/`, links PDF files that neither sitemap lists. The `--source` option selects `documentation`, `marketing`, or `both`. The marketing sitemap is in the code now. The product landing family is a planned source.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download the filtered corpus with a manifest (Priority: P1)

The operator starts the system with no earlier state. The system reads the sitemap index and every US and EN child sitemap. The system builds a document inventory. The system keeps every document except a superseded release note. The system resolves the companion PDF for each document root. The system downloads each PDF, sorts it into a slug category, and writes a manifest.

**Why this priority**: This story is the core deliverable. The operator needs the whole US and EN documentation set on local disk. The operator needs a manifest that lists each document. Every later story adds value on top of this corpus.

**Independent Test**: Point the system at the sitemap index or at a recorded subset. Confirm that the system builds the inventory and applies the release-note filter. Confirm that the system resolves and downloads each companion PDF and sorts the files by slug category. Confirm that the manifest shows a source URL, a category, a file size, and a status for each document.

**Acceptance Scenarios**:

1. **Given** the sitemap index is reachable, **When** the operator starts a cold run, **Then** the system records the full inventory before any download.
2. **Given** the discovered release-note roots, **When** the system applies the filter, **Then** it keeps only the newest note for each product, major version, and minor version train, and gives each X-build its own train.
3. **Given** an HTML document root, **When** the system resolves the companion PDF, **Then** the system reads the root index page first and the `__toc.js` script second.
4. **Given** a sitemap entry that already names a PDF, **When** the system processes the entry, **Then** the system downloads that PDF with no extra resolution.
5. **Given** a completed run, **When** the operator reads the manifest, **Then** each document shows a source URL, a category, a file size, and a status.
6. **Given** a body that does not start with `%PDF`, **When** the system checks it, **Then** it rejects the file and marks the document failed.

---

### User Story 2 - Content-derived sub-categories for uncategorized documents (Priority: P2)

The system finds many documents that match no slug keyword. The system puts these documents in the uncategorized bucket. For each uncategorized document, the system reads a bounded text sample on the local machine. The system derives a sub-category label from the content signals. The system records the label, the detected signal names, and the numeric scores. The system stores no document body text.

**Why this priority**: About half of the corpus matches no slug keyword. The slug rules cannot sort these documents. Content analysis gives each document a useful sub-category. This work keeps the large corpus usable and searchable.

**Independent Test**: Give the system a set of downloaded uncategorized PDFs. Confirm that each document gets a sub-category label, detected signal names, and numeric scores in the manifest. Confirm that the output tree gains a folder for each sub-category. Confirm that no document body text exists on disk.

**Acceptance Scenarios**:

1. **Given** an uncategorized document, **When** the system reads the downloaded PDF, **Then** the system derives a sub-category label from the content.
2. **Given** a derived label, **When** the system records the result, **Then** the system stores only the label, the detected signal names, and the numeric scores.
3. **Given** any uncategorized document, **When** the system finishes the analysis, **Then** no extracted body text exists as a file or as a manifest field.
4. **Given** a PDF with no readable text, **When** the system processes it, **Then** the system assigns the defined fallback sub-category label and continues.
5. **Given** labeled documents, **When** the system arranges the output, **Then** the system places each document in a folder named for its sub-category.
6. **Given** a low-confidence document, **When** the system assigns a label, **Then** the system uses the defined fallback sub-category label.

---

### User Story 3 - A resumable, polite, and fault-tolerant long run (Priority: P3)

The run covers thousands of documents and takes hours. The operator must stop the run and start it again with no loss. The system must not re-download a completed document. The system must pace the requests so the crawl does not overload the Juniper host. One bad document must not stop the whole run.

**Why this priority**: The full run is long and network-bound. The operator needs to interrupt the run and resume it. The crawl needs to stay polite. The system needs to record a single failure and continue. These properties make the full 2,225-document run practical.

**Independent Test**: Interrupt a run in progress and start it again. Confirm that the system re-downloads no completed document. Inject a 404 error and a timeout on single documents. Confirm that the run continues and records the failures. Measure the delay between two requests.

**Acceptance Scenarios**:

1. **Given** a partly complete run, **When** the operator restarts the system, **Then** it resumes from the tracked state and re-downloads no completed document.
2. **Given** a document that returns a 404 error or a timeout, **When** the system processes it, **Then** it records the failure and continues.
3. **Given** an active crawl, **When** the system sends requests, **Then** the system waits at least the configured minimum delay between two requests.
4. **Given** a run in progress, **When** the operator reads the output, **Then** the system shows the count of completed documents out of the total.
5. **Given** an interrupted download, **When** the system resumes, **Then** the system does not treat the partial file as complete.

---

### Edge Cases

- A document root has no index page and no `__toc.js` script. The system records a "no PDF found" status and continues.
- An index page names more than one PDF. The system selects the companion PDF by the fixed order in FR-010a. The system records the chosen URL and each rejected candidate.
- The site returns an error page with a 200 status. The response body does not start with `%PDF`. The system rejects the file and records the failure.
- A single document returns a 403 error, a timeout, or a reset connection. The system records the failure against that document and continues.
- A release note has no version that the system can parse. The system keeps the note, because the note has no known sibling.
- The same URL appears in more than one child sitemap. The system keeps one copy in the inventory.
- A chapter URL appears without its root in the sitemap. The system maps the chapter to its root and downloads the companion PDF once.
- A download stops early and leaves a partial file. The system does not mark the file as complete. The system downloads the file again on the next run.
- A PDF is encrypted, holds only images, or is malformed. The system assigns the fallback sub-category label, stores empty scores, and continues.
- A single PDF is very large. The system uses a generous timeout and records a failure if the transfer does not finish.
- The disk is full or the target folder is read-only. The system records the failure for that document and stops in a clean state.
- A slug matches more than one category keyword. The system applies a defined precedence order so the result is reproducible.
- A slug holds characters that are not valid in a Windows file name. The system sanitizes the name before it writes the file.
- The state store is locked or damaged. The system fails closed and does not report false progress.

## Requirements *(mandatory)*

### Functional Requirements

#### Inventory discovery

- **FR-001**: The system MUST fetch the sitemap index at `https://www.juniper.net/documentation/sitemap/sitemap.xml` and list the 16 US and EN child sitemaps.
- **FR-002**: The system MUST fetch every US and EN child sitemap and extract every URL that it holds.
- **FR-003**: The system MUST map each chapter page under a `/topics/` path to its parent document root, so the inventory holds each document once.
- **FR-004**: The system MUST split the inventory into HTML document roots and direct PDF URLs. The system MUST remove a URL that appears in more than one child sitemap.
- **FR-005**: The system MUST save the inventory to durable storage before it downloads any file. A later run then reuses the inventory without a fresh sitemap read.

#### Additional corpus sources

- **FR-005a**: The system MUST read the marketing sitemap at `https://www.juniper.net/sitemaps/en_US.xml` and MUST keep every direct PDF URL that it holds. The marketing sitemap holds the datasheets, the solution briefs, the case studies, and the white papers.
- **FR-005b**: The system MUST classify each marketing asset by the asset-type path segment. The segment after `assets` names the type, such as `datasheets` in `/content/dam/www/assets/datasheets/us/en/...`. A marketing asset needs no content analysis.
- **FR-005c**: The system MUST remove a marketing PDF that the documentation sitemap already lists, so a shared file appears once.
- **FR-005d**: The system MUST read the product landing family under `/documentation/product/`. These landing pages link PDF files that neither sitemap lists. The system MUST add each such PDF to the inventory.
- **FR-005e**: The system MUST let the operator select the source set. The `--source` option MUST accept `documentation`, `marketing`, or `both`.

#### Release-note filter

- **FR-006**: The system MUST find each release-note document root and keep only the newest note for each product family and version train.
- **FR-006a**: The system MUST build the release-note train key from the product family, the major version, the minor version, and the X-build number. The system MUST read the product family from the document name, not from a fixed path segment, because Junos OS and Junos OS Evolved share the path segment `junos`. By default one train covers a major version and a minor version. The `collapse_to_major` option collapses a train to the major version only. The system MUST give each X-build its own train, so an X-build never evicts a mainstream R note. The system MUST parse the D revision, so the newest D build wins inside an X-build train.
- **FR-007**: The system MUST keep every document that is not a release note. The system MUST also keep a release note that has no version to parse.
- **FR-008**: The system MUST reuse the `ReleaseNoteSelector` class in `scripts/jvd_doc_selector.py` for this selection, and MUST extend that class rather than rewrite it.
- **FR-009**: The system MUST record each dropped release-note root and the reason, so the audit trail is complete.

#### Companion PDF resolution

- **FR-010**: For each HTML document root, the system MUST resolve the companion PDF. The system MUST read the root index page first. The system MUST read the `__toc.js` script in the same folder second.
- **FR-010a**: When the resolution finds more than one `.pdf` reference, the system MUST select the companion PDF by a fixed order. First, the system MUST prefer the PDF whose file name best matches the document root slug. Second, the system MUST prefer the first `.pdf` reference in the same folder as the index page. Third, the system MUST select the largest file. The whole-document PDF is larger than any single-chapter PDF.
- **FR-010b**: The system MUST record the URL of the chosen companion PDF and each rejected candidate in the manifest. A reader can then audit the choice.
- **FR-011**: For a sitemap entry that already names a `.pdf` file, the system MUST use that URL directly.
- **FR-012**: When the system finds no companion PDF, the system MUST record the document with a "no PDF found" status and continue.
- **FR-013**: The system MUST reuse the `JvdPdfResolver` class in `scripts/crawl_jvd.py` for this resolution, and MUST extend that class rather than rewrite it.

#### Download and validation

- **FR-014**: The system MUST download each resolved PDF and MUST reject a response whose body does not start with the `%PDF` marker.
- **FR-015**: The system MUST skip a document whose target file already exists and holds more than zero bytes.
- **FR-016**: The system MUST pace the requests to the Juniper host, and MUST wait at least a configurable minimum delay between two requests.
- **FR-017**: The system MUST handle a per-document HTTP error, a timeout, and a connection failure without a stop to the whole run. The system MUST record the failure against that document.
- **FR-018**: The system MUST reuse the `JvdDownloader` class in `scripts/crawl_jvd.py` for the write, the skip, and the `%PDF` check, and MUST extend that class rather than rewrite it.
- **FR-019**: The system MUST NOT count a zero-byte file or a non-PDF response as a successful download.

#### Slug classification

- **FR-020**: The system MUST classify each document by a keyword match on the slug. The categories are release notes, configuration guides, administration guides, installation guides, CLI reference, API, security and compliance, migration, and design. The system MUST use the category "uncategorized" when no keyword matches.
- **FR-021**: The system MUST apply a defined precedence order when a slug matches more than one category keyword, so the classification is reproducible.

#### Content-derived sub-categories

- **FR-022**: For each uncategorized document, the system MUST extract text from a bounded sample of the downloaded PDF. The system MUST read the sample on the local machine. The bounded sample holds the title page, the table of contents, and the first few pages. The sample is not the whole document.
- **FR-022a**: The system MUST derive the sub-category taxonomy from the content signals. The system MUST NOT use a fixed list of sub-categories.
- **FR-023**: The system MUST score the bounded sample against three signal groups. The groups are the product family, the task type, and the technology domain.
- **FR-023a**: The product-family signal MUST cover EX, QFX, SRX, MX, ACX, PTX, Mist, Apstra, Junos Space, Paragon, and Contrail. The task-type signal MUST cover configuration, monitoring, troubleshooting, hardware installation, licensing, and interoperability. The technology-domain signal MUST cover routing, switching, security, wireless, automation, and telemetry.
- **FR-023b**: The system MUST assign a label from the numeric scores. The label MUST be reproducible and human-readable. The system MUST derive the sub-category name from the highest-scoring signals.
- **FR-024**: The system MUST store only the derived metadata for each document. The derived metadata is the sub-category label, the detected signal names, and the numeric scores. The system MUST hold the extracted text only in memory. The system MUST discard the text after it derives the label. The system MUST NOT write or keep the extracted body text as an artifact, a file, or a manifest field.
- **FR-025**: When the system cannot extract text from a PDF, the system MUST assign the defined fallback sub-category label and continue without a crash.
- **FR-025a**: When no signal reaches the defined confidence threshold, the system MUST assign the defined fallback sub-category label. The system MUST NOT give a low-confidence document a wrong label.
- **FR-026**: The system MUST use a widely used and well-supported library to extract the PDF text, and the plan MUST justify the choice of library.

#### Output layout and manifest

- **FR-027**: The system MUST arrange the downloaded files in a folder tree by category, and by derived sub-category for an uncategorized document.
- **FR-028**: The system MUST write a manifest for each document. The manifest MUST map the document to its source URL, its category, its sub-category, its file size, and its download status. The manifest MUST also record the chosen companion PDF and each rejected candidate for a document with more than one PDF reference. The manifest MUST also list each dropped release note with the reason.
- **FR-029**: The system MUST write every output under the repository `data/` directory. The system MUST build every path with a platform-neutral method, so the output works on Windows.
- **FR-030**: The system MUST sanitize each slug that becomes a file name or a folder name. The sanitized name MUST be valid on Windows and on other platforms.

#### Resumable state

- **FR-031**: The system MUST track a per-document state in durable storage. The state MUST record the stages discovered, resolved, downloaded, classified, failed, and dropped.
- **FR-032**: The system MUST survive an interruption at any stage and resume without a re-download of a completed document and without a fresh sitemap read.
- **FR-033**: The system MUST make each state update durable and consistent, so an interrupted write does not damage the tracked state. The system MUST NOT report a document as complete until the file and the state are both saved.
- **FR-034**: A repeated run MUST reprocess only a document that is new, failed, or not yet at a final state.

#### Progress and summary

- **FR-035**: The system MUST report progress during the run, and MUST show the current stage and the count of completed documents out of the total.
- **FR-036**: The system MUST print a final summary. The summary MUST show the count for each category and sub-category. The summary MUST also show the downloaded, skipped, failed, and dropped release-note counts, and the total bytes.

### Key Entities *(include if feature involves data)*

- **Sitemap index**: The top file that lists the child sitemaps for a language.
- **Child sitemap**: One of the 16 US and EN files that lists document URLs.
- **Document inventory record**: One document in the plan. It holds the source URL, the root slug, and the type (HTML root or direct PDF). It also holds the resolved PDF URL, the category, the sub-category, the local path, the file size, and the status.
- **Document root**: The parent page for a document. It owns one companion PDF and many chapter pages under `/topics/`.
- **Release-note train key**: The identity of a release-note train. It holds the product family, the major version, the minor version, and the X-build number.
- **Category**: The top-level bucket from the slug keyword match.
- **Marketing asset**: A direct PDF file from the marketing sitemap. Its category comes from the asset-type path segment, such as `datasheets` or `case-studies`. It needs no content analysis.
- **Sub-category**: The label for an uncategorized document that the system derives from the PDF content.
- **Content analysis result**: The derived metadata for one uncategorized document. It holds the sub-category label, the detected signal names, and the numeric scores. It holds no body text.
- **Manifest**: The full record that maps each document to its source URL, category, sub-category, file size, and status. It also records the chosen companion PDF and each rejected candidate.
- **Harvest state record**: The durable per-document state that makes the run resumable.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From a cold start, the system discovers the full US and EN documentation inventory of about 2,225 documents from the 75,774 sitemap URLs. The marketing sitemap adds 778 direct PDF files, and the two sitemaps together hold 1,410 unique direct PDF files. The system records the whole inventory before any download.
- **SC-002**: The release-note filter keeps the newest note for each product family, major version, and minor version train, and gives each X-build its own train. On the current corpus the filter keeps 822 notes and drops 151 superseded notes with no wrong drop. The filter keeps every document that is not a release note.
- **SC-003**: A run that stops at any point and starts again re-downloads zero completed documents.
- **SC-004**: Every document in the manifest shows a source URL, a category, a sub-category value, a file size, and a final status. The coverage is 100 percent.
- **SC-005**: No extracted document body text exists on disk as an artifact. An audit of the output tree and the content analysis records finds only the label, the detected signal names, and the numeric scores.
- **SC-006**: A single document failure, such as a 404 error, a timeout, a non-PDF response, or a text-extraction error, never stops the run. The run completes and records the failure.
- **SC-007**: Every uncategorized document receives a derived sub-category label, including the defined fallback label when the system cannot read the text. The coverage is 100 percent.
- **SC-008**: The crawl stays polite. The measured delay between two requests to the Juniper host is at least the configured minimum.
- **SC-009**: The operator sees the progress during the run and a final summary with counts by category and sub-category and the total bytes.
- **SC-010**: Across one or more runs, every document that the system can resolve reaches a final status, which is downloaded or a recorded failure reason. No document stays in an in-progress state.
- **SC-011**: The run downloads the datasheets. The marketing sitemap holds 124 datasheets, and the run places each one in a `datasheets` category folder. The marketing sitemap also holds 204 case studies, 139 solution briefs, 57 infographics, 52 white papers, 37 flyers, and 31 legal documents.

## Assumptions

- The system writes the corpus under the repository `data/` directory, for example `data/juniper_corpus/`. The exact subfolder name is configurable. The earlier `jvd_pdfs/` output is a separate, earlier artifact.
- The system reuses the `JvdCatalogClient`, `JvdPdfResolver`, and `JvdDownloader` classes in `scripts/crawl_jvd.py`, and the `ReleaseNoteSelector` class in `scripts/jvd_doc_selector.py`. The system extends these classes rather than rewrites them.
- The repository already declares `pdfplumber` as a dependency for the STE dictionary tool. The plan may reuse `pdfplumber` for the content text extraction, which avoids a new dependency and satisfies the "widely used library" rule. The plan states the final choice and the reason.
- Each HTML document root publishes one companion PDF that holds every chapter, as the site structure shows.
- The corporate proxy re-signs TLS. The system verifies the chain through the repository root CA file `zscaler-root-ca.crt` by default. The `verify` mode is the recommended mode for the production run, because it requires a valid certificate with no downgrade path. The `insecure` mode stays as a configurable fallback.
- The scope is the US and EN corpus. The corpus holds the documentation sitemap, the marketing sitemap, and the product landing family.
- The estimated corpus size is 5 to 25 GB. The local machine has enough free disk space for the run.
- The polite delay default is about one request per second, which matches the existing `DELAY_SECONDS` value. The operator can change the delay.
- Content analysis reads only local files. It adds no network load.
- The system derives the sub-category taxonomy from content signals. The signals are the product family, the task type, and the technology domain. The spec does not fix a closed list of sub-categories. The system MUST produce a reproducible label for each document, or the fallback label when no signal reaches the confidence threshold.

## Constraints (from the project constitution)

The plan and the implementation MUST honor these constraints. The constraints come from the project constitution and the repository conventions.

- The code targets Python 3.13 or newer. The design is class-based. The design uses no wrapper function that only delegates to a class method.
- The code obeys the Five-Item Rule. Each function has at most 5 parameters, at most 5 logical blocks, and at most 25 lines.
- Each executable line carries an inline comment that explains the reason for the line.
- The code logs an `info` message before each action and a `debug` message after each action with a short result summary. The code uses percent-style formatting in the log calls. The log text uses ASCII characters only.
- The code builds every path with `pathlib.Path` or `os.path.join`. The code uses no hardcoded separator. The code runs on Windows.
- Every user-facing text and every log message follows Simplified Technical English, as defined in `documentation/ASD-STE100_writing-guide.md`.
- The durable state store follows the operational-store rules. The plan defines the fail-closed behavior, the backup and recovery, the retention, and the verified write. The system does not report success until it confirms the durable write.
- Any new dependency for the PDF text extraction needs a justification. The plan prefers a widely used and well-supported library.
