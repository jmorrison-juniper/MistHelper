# Phase 0 Research: Juniper Documentation Corpus Harvester

This document records each design decision. Every entry states the decision, the
reason, and the alternatives that the plan rejected. No open clarification remains.

## 1. Package location and class promotion

**Decision**: Create one new package, `src/juniper_docs/`. Move `JvdCatalogClient`,
`JvdPdfResolver`, and `JvdDownloader` from `scripts/crawl_jvd.py` into
`src/juniper_docs/acquire/`. Move `ReleaseNoteSelector` and `ReleaseNoteKey` from
`scripts/jvd_doc_selector.py` into `src/juniper_docs/discovery/`. Move the module
constants (`SITE`, `HEADERS`, `TIMEOUT_SECONDS`, `DELAY_SECONDS`, the SSL context)
into `src/juniper_docs/acquire/http_config.py`. The new feature classes extend the
base classes: `CompanionPdfResolver(JvdPdfResolver)`,
`CorpusDownloader(JvdDownloader)`, and `CorpusReleaseNoteSelector(ReleaseNoteSelector)`.

**Rationale**: The spec requires reuse and extension, not a rewrite (FR-008, FR-013,
FR-018). A package under `src/` is testable, importable, and covered by the coverage
source root. One shared copy prevents drift. `scripts/crawl_jvd.py` keeps only the
validated-designs classes (`JvdCatalogWalker`, `JvdCrawlRunner`) and imports the base
classes from the package, so the JVD crawl keeps working. This is reuse by direct
import, which the constitution allows, not a legacy shim.

**Alternatives considered**:

- Grow `scripts/` with more modules. Rejected. Scripts are not covered by the gates
  and are hard to unit test. The design direction forbids this.
- Duplicate the classes in the package. Rejected. Two copies drift over time and
  break the single-source rule.
- Keep a re-export stub in `scripts/crawl_jvd.py`. Rejected. The constitution forbids
  a legacy compatibility shim. A direct import of the moved class is the clean form.

## 2. Durable, resumable state store

**Decision**: Use one SQLite database at `data/juniper_corpus/harvest_state.db`. Open
the database in WAL mode. Set `synchronous = FULL`. Use one row per document, keyed
by the document root URL, which is a natural business key. A `stage` column records
the state: `discovered`, `resolved`, `downloaded`, `classified`, `failed`, or
`dropped`. Wrap each state change in a single transaction. Write the PDF bytes to
disk first, then flip the row to `downloaded` and commit. The tool marks a document
complete only after both the file and the row are durable.

**Rationale**: SQLite is already used across this repository, so the choice adds no
dependency. SQLite gives ACID transactions, a single portable file, and safe
concurrent reads. WAL mode plus `synchronous = FULL` gives a crash-safe write. The
natural key lets a repeated run reprocess only a document that is new, failed, or not
yet final (FR-034). The store survives an interruption and needs no fresh sitemap
read (FR-032).

**Alternatives considered**:

- A JSON checkpoint file. Rejected. A partial write can corrupt the whole file. There
  is no atomic multi-record update and no query support.
- A per-document sidecar file. Rejected. The run cannot summarize state without a
  full directory scan. There is no single consistent snapshot.
- A server database such as PostgreSQL. Rejected. A server is heavy for a single
  local batch tool and breaks the offline, single-file goal.

**Fail-closed, backup, retention, verified write** (operational-store rules):

- Fail closed. If the store is locked or damaged, the tool stops and reports the
  error. The tool never reports false progress (edge case in the spec).
- Verified write. After each commit, the tool reads back the row `stage` before it
  counts the document complete.
- Backup and recovery. Before a schema migration, the tool copies the database file
  to `harvest_state.db.bak`. The WAL file allows recovery after a crash.
- Retention. The store persists across runs by design. The operator deletes the
  `data/juniper_corpus/` tree to start a full cold run.

## 3. PDF text sample library and the privacy invariant

**Decision**: Use `pdfplumber` to read a bounded text sample. The sample holds the
title page, the table-of-contents pages, and the first few body pages, up to a fixed
page cap. Hold the sample in one local string variable. Score the sample, derive the
label, and let the variable go out of scope. Persist only the label, the detected
signal names, and the numeric scores.

**Rationale**: The repository already declares `pdfplumber>=0.11.0` for the
ASD-STE100 dictionary tool, so there is no new dependency. `pdfplumber` is widely
used and well supported, which satisfies FR-026. A page cap bounds the memory and the
time per document. The design keeps no body text on disk, which satisfies FR-024 and
SC-005. The `ContentAnalysisResult` dataclass has no text field, so the invariant is
structural, not just a convention.

**Alternatives considered**:

- `PyPDF2` or `pypdf`. Rejected. Text extraction quality is lower for multi-column
  Juniper layouts, and the repository does not already declare it.
- `pdfminer.six` directly. Rejected. `pdfplumber` wraps `pdfminer.six` with a simpler
  page interface and is already present.
- Store the extracted text for reuse. Rejected. The spec forbids any stored body
  text (FR-024).

## 4. TLS verification and the corporate proxy

**Decision**: Prefer to keep TLS verification on. When the corporate root CA file
`zscaler-root-ca.crt` is present in the repository root, build the SSL context from
that certificate authority and verify normally. When the file is absent, fall back to
an unverified context, log a loud warning, and mark the fallback with one justified
`# nosec B323` annotation. Make the mode configurable so the operator can force
verification off or on.

**Rationale**: The constitution requires a fix over a suppression. The proper fix for
a re-signing proxy is to trust the proxy root CA, not to disable verification. The
repository already ships `zscaler-root-ca.crt`, so the verified path is achievable.
The unverified fallback matches the proven behavior of the existing crawler and keeps
the run working on a machine without the CA file. The single annotation carries a
justification, which is the only allowed use of a suppression.

**Alternatives considered**:

- Always disable verification, as the current script does. Rejected as the default.
  This is a blanket suppression and hides real risk. It stays only as a configurable
  fallback with a warning.
- Set an environment variable to a CA bundle globally. Rejected. A global change
  affects unrelated code. The per-context choice is contained and explicit.

## 5. Companion PDF selection when more than one PDF is named

**Decision**: `CompanionPdfResolver` extends `JvdPdfResolver`. It reads the root index
page first and the sibling `__toc.js` script second, which keeps the proven order. It
collects every `.pdf` reference. It selects by a fixed order (FR-010a): first, the PDF
whose file name best matches the document root slug; second, the first `.pdf`
reference in the same folder as the index page; third, the largest file. It returns
the chosen URL and the list of rejected candidates.

**Rationale**: The fixed order makes the choice reproducible and auditable. The
whole-document PDF is larger than a single-chapter PDF, so the size tiebreak favors
the complete document. The resolver records each rejected candidate for the manifest
(FR-010b).

**Alternatives considered**:

- Always take the first `.pdf` reference. Rejected. The first reference can be a
  single chapter, not the whole document.
- Download every candidate and keep the largest. Rejected. This wastes bandwidth and
  breaks the politeness goal. The name match plus a size probe is enough.

## 6. Slug classification and precedence

**Decision**: `SlugClassifier` matches the slug against a keyword map for the nine
categories: release notes, configuration guides, administration guides, installation
guides, CLI reference, API, security and compliance, migration, and design. When a
slug matches more than one category, the classifier applies a fixed precedence list
so the result is reproducible (FR-021). When no keyword matches, the classifier
returns `uncategorized`.

**Rationale**: A keyword map is simple, fast, and reproducible. A fixed precedence
list removes ambiguity when two keywords match. The `uncategorized` bucket feeds the
content sub-category step.

**Alternatives considered**:

- A machine-learning classifier on the slug. Rejected. The slug is short and the
  keyword rules are clear. A model adds cost and reduces reproducibility.

## 7. Content signal taxonomy, label, threshold, and fallback

**Decision**: `SignalScorer` scores the bounded sample against three signal groups.
The product-family group covers EX, QFX, SRX, MX, ACX, PTX, Mist, Apstra, Junos
Space, Paragon, and Contrail. The task-type group covers configuration, monitoring,
troubleshooting, hardware installation, licensing, and interoperability. The
technology-domain group covers routing, switching, security, wireless, automation,
and telemetry. Each group scores by keyword frequency in the sample. The scorer
builds a human-readable label from the highest-scoring signal in each group, for
example `srx__configuration__security`. The taxonomy is not a fixed list; the label
emerges from the signals (FR-022a). When no group reaches the confidence threshold,
or when the PDF yields no readable text, the scorer returns the fixed fallback label
`unclassified-content` and empty scores (FR-025, FR-025a).

**Rationale**: Three signal groups give a stable, reproducible, and readable label.
The frequency score is deterministic, so the same PDF yields the same label. The
confidence threshold prevents a wrong label on weak evidence. The fallback keeps the
run moving on a bad or image-only PDF.

**Alternatives considered**:

- A fixed sub-category list. Rejected. The spec forbids a closed list (FR-022a).
- A topic-model or embedding cluster. Rejected. The result is not reproducible across
  runs and adds a heavy dependency.

## 8. Politeness, fault tolerance, and resume

**Decision**: `HarvestRunner` waits at least the configured minimum delay between two
requests. The default delay is one second (FR-016). Every per-document step runs
inside a try and except block that records the failure against the document and
continues (FR-017). The timeout is generous for a large PDF. On start, the runner
reads the store and skips any document that is already at a final state, so it
re-downloads no completed file (FR-032, SC-003).

**Rationale**: The delay keeps the crawl polite and matches the existing
`DELAY_SECONDS` value. The per-document guard keeps one bad document from stopping the
whole run (SC-006). The state check gives a clean resume.

**Alternatives considered**:

- Parallel downloads. Rejected. Parallel requests break the politeness goal and add
  concurrency risk. A single paced stream is enough for an overnight run.

## 9. Windows-safe names and paths

**Decision**: A `PathSanitizer` step replaces every character that is invalid in a
Windows file name, trims trailing dots and spaces, and avoids reserved device names
such as CON and PRN. Every path uses `pathlib.Path` (FR-029, FR-030).

**Rationale**: The output must work on Windows and on Linux. Sanitizing the slug
before a write prevents a path error mid-run.

## 10. Manifest format and the DataExporter boundary

**Decision**: `ManifestWriter` renders the manifest from the SQLite store to
`manifest.json` and `manifest.csv`. The manifest maps each document to its source URL,
category, sub-category, file size, and status. It records the chosen companion PDF and
each rejected candidate. It lists each dropped release note with the reason (FR-028).
The manifest is an operational artifact, so it does not route through
`DataExporter.write_with_format_selection`.

**Rationale**: The manifest describes local files and run state, not collected Mist
API data. The constitution's multi-backend rule applies to API exports and collected
API data. The operational-store exception covers this internal artifact. JSON and CSV
give both a machine format and a spreadsheet format.

**Alternatives considered**:

- Route the manifest through `DataExporter`. Rejected. The manifest is not Mist API
  data, and `DataExporter` expects Mist endpoint semantics and primary-key strategies
  that do not apply here.

## 11. Quality gates

**Decision**: Meet every repository gate: ruff, black (line length 120), mypy,
pytest with coverage `fail_under = 90`, bandit, pydocstyle (google convention),
interrogate (`fail_under = 90`), radon with every function at complexity 10 or below,
vulture, and pylint at 9.5 or above. Unit tests mock all HTTP and use small recorded
fixtures.

**Rationale**: The gates are non-negotiable. The repository setting for coverage is
90, which is stricter than the 80 floor in the task and therefore satisfies it. Small
functions and clear classes keep radon complexity at 10 or below.

**Alternatives considered**:

- Target only the 80 percent floor. Rejected. The repository gate is 90, and CI
  enforces it.

## 12. The marketing sitemap source

**Decision**: Read a second source, the marketing sitemap at
`https://www.juniper.net/sitemaps/en_US.xml`. This sitemap is a flat list of asset
URLs. Keep every URL that ends in `.pdf`. The measured sitemap holds 2,130 entries
and 778 direct PDF files. Treat each marketing PDF as a direct PDF, so the run
downloads it with no companion-PDF resolution. Classify each asset by the path
segment after `assets`, such as `datasheets` in
`/content/dam/www/assets/datasheets/us/en/...`. Remove a marketing PDF that the
documentation sitemap already lists, so a shared file appears once. The measured
overlap is 2 files, so the two sitemaps together hold 1,410 unique direct PDF files.

**Rationale**: The user asked for the datasheets by name, and the marketing sitemap
is the only source that lists them. The measured breakdown holds 204 case studies,
139 solution briefs, 124 datasheets, 57 infographics, 52 white papers, 37 flyers, and
31 legal documents. The asset-type path segment is a reliable category signal, so a
marketing asset needs no content analysis. A flat direct-PDF read reuses the existing
downloader with no new resolution step.

**Alternatives considered**:

- Read the documentation sitemap only. Rejected. That source lists no datasheet, so
  the run would miss the assets the user asked for.
- Run content analysis on each marketing asset. Rejected. The asset-type path segment
  already names the category, so the content step adds cost with no gain.

## 13. The product landing family source

**Decision**: Read a third source, the product landing family under
`/documentation/product/`. This family holds 363 landing pages that cover 244
products. Each landing page links PDF files. Add each linked PDF to the inventory.

**Rationale**: The landing pages link PDF files that neither sitemap lists. A sample
of 10 landing pages found 25 PDF files that are absent from both known sources. The
sample includes a Mist GovCloud guide, hardware datasheets, letters of volatility,
and Junos XML references. So 25 is a measured lower bound, and the full scan of all
244 pages is pending. The source closes a real gap in the corpus.

**Alternatives considered**:

- Skip the landing pages. Rejected. The sample proves the pages hold unique PDF files
  that the operator needs.
- Crawl every page on the site to find the PDF files. Rejected. A full-site crawl is
  slow and impolite. The bounded landing family is a targeted source.

## 14. The release-note train key granularity

**Decision**: Key the release-note train by the product family, the major version,
the minor version, and the X-build number. Read the product family from the document
name, not from a fixed path segment. By default one train covers a major version and
a minor version, so 23.1, 23.2, 23.3, and 23.4 each keep their own newest note. The
`collapse_to_major` option collapses a train to the major version only. Give each
X-build its own train, so an X-build such as 23.4X100 never evicts the mainstream
23.4R2 note. Parse the D revision, so the newest D build wins inside an X-build train.

**Rationale**: The user wrote "23.x, 24.x", which is ambiguous, because Juniper ships
23.1 through 23.4 inside major 23. The user could not confirm the reading. The
failure modes are asymmetric. A few extra PDF files cost little disk space and little
time. A lost release note costs a multi-hour re-run of the whole corpus. So the
default keeps more history. The name-first product read keeps Junos OS apart from
Junos OS Evolved, because the two share the path segment `junos`. It also keeps a
locale segment such as `us` out of the product family, because a PDF tree can place a
locale segment where the product segment would otherwise sit.

**Alternatives considered**:

- Key by the major version only, as the default. Rejected. That reading can silently
  drop a release the operator wanted, such as 23.2, when 23.4 exists.
- Read the product family from a fixed path segment. Rejected. Junos OS and Junos OS
  Evolved collide on the `junos` segment, and a locale segment can shadow the product.
- Treat an X-build as a successor to the mainstream line. Rejected. An X-build is a
  special branch, so it evicts a mainstream R note when it shares the train.

## 15. The TLS mode recommendation and the auto-mode limitation

**Decision**: Recommend the `verify` mode for the production run. The `verify` mode
builds the SSL context from the repository root CA `zscaler-root-ca.crt` and requires
a valid certificate. Keep the three modes `auto`, `verify`, and `insecure`. Record
one known limitation of the `auto` mode and leave it unrepaired for now.

**Rationale**: On this machine all three modes reach the site. The connection is
intercepted, and the chain validates against both the system trust store and the
repository root CA. The `verify` mode requires a certificate with no downgrade path,
so it is the safe choice for the production run. The `auto` mode has a latent gap. It
falls back to the insecure context only when the CA file is absent, not when
verification fails. The name `auto` implies a fallback on any failure, so the current
behavior does not match the name. The gap is latent, because the CA file is present
and verification passes on this machine.

**Alternatives considered**:

- Recommend the `auto` mode for production. Rejected. The `auto` mode can fall back to
  an unverified context, so it has a downgrade path that `verify` does not.
- Repair the `auto` fallback now, so it also falls back on a verification failure.
  Rejected for this feature. The change widens the downgrade path, and the production
  run uses `verify`, so the repair is a separate, tracked follow-up.
