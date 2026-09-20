# Implementation Plan: Juniper Documentation Corpus Harvester

**Branch**: `2738-juniper-doc-corpus-harvester` | **Date**: 2026-09-16 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/2738-juniper-doc-corpus-harvester/spec.md`

## Summary

The harvester downloads the whole US and EN Juniper documentation corpus to local
disk. The run reads the sitemap index, builds a document inventory, and keeps every
document except a superseded release note. The run reads two more sources. The
marketing sitemap adds the datasheets and the other marketing assets. The product
landing family adds PDF files that neither sitemap lists. The run resolves one
companion PDF for each HTML document root, downloads each PDF, and sorts each file
into a slug category. For a document that matches no slug keyword, the run reads a
bounded PDF text sample in memory, derives a sub-category label from content signals,
and then discards the text. The run is polite, resumable, and fault tolerant. The run
writes a folder tree by category and a manifest.

The technical approach reuses four proven classes. The plan promotes
`JvdCatalogClient`, `JvdPdfResolver`, and `JvdDownloader` from `scripts/crawl_jvd.py`
into a new package `src/juniper_docs/`. The plan promotes `ReleaseNoteSelector` from
`scripts/jvd_doc_selector.py` into the same package. The new feature classes extend
these base classes rather than rewrite them. A dedicated SQLite store under
`data/juniper_corpus/` holds the durable, resumable per-document state and the
manifest source data. The content sub-category step uses `pdfplumber`, which the
repository already declares as a dependency.

## Technical Context

**Language/Version**: Python 3.13 or newer (constitution binding).

**Primary Dependencies**: Standard library `urllib`, `ssl`, `sqlite3`, `re`,
`pathlib`, `logging`, `dataclasses`. Third-party `pdfplumber` (already declared) for
the bounded PDF text sample. No new runtime dependency is required.

**Storage**: SQLite operational store at `data/juniper_corpus/harvest_state.db` for
the resumable per-document state and the manifest source rows. Downloaded PDFs live
under `data/juniper_corpus/<category>/[<sub-category>/]`. The manifest renders to
`data/juniper_corpus/manifest.json` and `manifest.csv`.

**Testing**: `pytest` with `pytest-cov`. Unit tests mock every HTTP read and use
recorded sitemap and PDF fixtures. No test performs a live network call. The
coverage gate is `fail_under = 90` (repository setting), which also meets the
80 percent floor stated in the task.

**Target Platform**: Windows 11 local development and Linux container. Every path
uses `pathlib.Path`. The output tree name is Windows-safe.

**Project Type**: Single-project command-line batch tool. One entry runner drives
the whole harvest. There is no web service and no external API surface.

**Performance Goals**: The run paces requests. The default minimum delay is about
one request per second, which matches the existing `DELAY_SECONDS` value. The
operator can change the delay. The run covers about 2,225 documents and 5 to 25 GB
over several hours.

**Constraints**:

- Class-based design. No wrapper function that only delegates to a class method.
- Five-Item Rule. Each function has at most 5 parameters, at most 5 logical blocks,
  at most 5 operations per block, and at most 25 lines.
- Each executable line carries an inline comment that explains the reason.
- `logging.info` before each action. `logging.debug` after each action with a result
  summary. Percent-style formatting. ASCII characters only.
- Simplified Technical English for all prose and all log text.
- Content text stays in memory only. The store holds the label, the detected signal
  names, and the numeric scores. The store holds no body text.
- TLS verification is on by default. The `verify` mode builds the SSL context from
  the repository root CA `zscaler-root-ca.crt` and requires a valid certificate.
  `verify` is the recommended mode for the production run, because it has no
  downgrade path. The `insecure` mode stays as a configurable fallback with a loud
  warning and one justified bandit annotation. The `auto` mode has a known
  limitation. It falls back to the insecure context only when the CA file is absent,
  not when verification fails. See research.md for the recommendation and the
  limitation.

**Scale/Scope**: About 75,774 sitemap URLs reduce to about 2,225 documents. About
1,591 are HTML roots and about 634 are direct PDF URLs. The marketing sitemap adds
778 direct PDF files, and the two sitemaps together hold 1,410 unique direct PDF
files. The product landing family holds 363 landing pages that cover 244 products,
and a sample of 10 pages found 25 more PDF files, so 25 is a measured lower bound
while the full 244-page scan is pending. About half of the documentation corpus
matches no slug keyword and needs the content sub-category step. The release-note
filter keeps 822 notes and drops 151 on the current corpus.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence in this plan |
|-----------|--------|-----------------------|
| I. Five-Item Rule | PASS with recorded debt | The new package `src/juniper_docs/` holds 5 real children. Each nested package holds 5 or fewer real children. Every function stays within the parameter, block, and line limits. The one new top-level child under the already-noncompliant `src/` parent is recorded in Complexity Tracking with a separate remediation action. |
| II. Class-Based Architecture (No Wrappers) | PASS | Every unit is a semantically named class. The entry script builds one runner and calls it. No standalone wrapper function delegates to a class method. Variable names use full words. |
| III. Safety-First | PASS | The tool runs without interactive prompts. The tool validates each URL, sanitizes each file name, and fails closed on a locked or damaged store. No credential is read or logged. |
| IV. Full Deployment Pipeline | DEFERRED to implement | The pipeline runs at implement time, not at plan time. The tasks phase adds the gate, commit, rebase, pull request, and container steps. |
| V. Observability and Logging | PASS | All log text is ASCII. Debug logs internal state. Info logs progress. Error logs exception context. |
| VI. Inline Comments | PASS by design | Every executable line carries an inline comment. The tasks phase enforces this per file. |
| VII. Action Logging | PASS by design | Info before each action. Debug after each action with a count, a status, or a size. Percent-style formatting. |
| Tech constraints (Python 3.13+, pathlib, `data/`) | PASS | The tool targets Python 3.13, builds paths with `pathlib`, and writes only under `data/`. |
| Operational Store rules | PASS | research.md defines fail-closed behavior, backup and recovery, retention, and the verified durable write. The tool does not report a document complete until the file and the state row are both durable. |
| Security: Fix over Suppress | PASS with justification | The plan prefers to keep TLS verification on with the corporate root CA in `zscaler-root-ca.crt`. The unverified context stays as a configurable fallback with one justified `# nosec B323` and a loud warning. |
| Output Backends (DataExporter) | PASS with justification | The manifest is an operational artifact, not collected Mist API data. The multi-backend export rule does not apply. The tool writes the manifest directly as JSON and CSV. |

No gate fails. No unresolved clarification remains. The three spec clarifications are
already recorded in the spec.

**Post-design re-evaluation (after Phase 1)**: The concrete package tree confirms the
gates. `src/juniper_docs/` holds 5 real children. `acquire/` holds 4, `discovery/`
and `harvest/` each hold 3, and `classify/` holds 4. Every planned class maps to one function
scope that stays within the 5-parameter, 5-block, 25-line limits. The content record
has no text field, so the privacy invariant holds by structure. The Constitution Check
result is unchanged: PASS, with the two recorded debt items in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/2738-juniper-doc-corpus-harvester/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── cli.md           # Command-line entry contract
│   ├── state-store.md   # SQLite schema and durability contract
│   ├── manifest.md      # Manifest field schema contract
│   └── classification.md# Category, signal, and privacy contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created here)
```

### Source Code (repository root)

The new feature package holds exactly 5 real children. Dunder files such as
`__init__.py` and `__pycache__` do not count toward the five, which matches the
established `src/db/` package pattern. Each nested package also holds 5 or fewer real
children.

```text
src/juniper_docs/                 # New feature package (one new child of src/)
├── __init__.py                   # Package marker (exempt from the count)
├── models.py                     # Shared dataclasses and the HarvestStage enum
├── discovery/                    # Inventory build and release-note filter
│   ├── __init__.py
│   ├── sitemap_reader.py         # SitemapReader: index and child sitemap parse
│   ├── inventory_builder.py      # InventoryBuilder: roots, direct PDFs, dedup
│   └── release_note_selector.py  # ReleaseNoteSelector (promoted) + CorpusReleaseNoteSelector
├── acquire/                      # HTTP client, PDF resolve, and download
│   ├── __init__.py
│   ├── http_config.py            # HttpConfig: base URL, headers, timeout, SSL context
│   ├── catalog_client.py         # JvdCatalogClient (promoted from scripts)
│   ├── pdf_resolver.py           # JvdPdfResolver (promoted) + CompanionPdfResolver
│   └── downloader.py             # JvdDownloader (promoted) + CorpusDownloader
├── classify/                     # Slug category, marketing asset, content sub-category
│   ├── __init__.py
│   ├── slug_classifier.py        # SlugClassifier: keyword match with precedence
│   ├── asset_classifier.py       # MarketingAssetClassifier: asset-type path segment
│   ├── content_sampler.py        # ContentSampler: bounded in-memory pdfplumber read
│   └── signal_scorer.py          # SignalScorer: three signal groups, label, fallback
└── harvest/                      # Durable state, manifest, orchestration
    ├── __init__.py
    ├── state_store.py            # HarvestStateStore: SQLite, fail-closed, verified write
    ├── manifest_writer.py        # ManifestWriter: JSON and CSV render from the store
    └── runner.py                 # HarvestRunner: end-to-end orchestration + progress

scripts/crawl_jvd.py              # Keeps JvdCatalogWalker and JvdCrawlRunner.
                                  # Imports the promoted base classes from src/juniper_docs/acquire.
scripts/jvd_doc_selector.py       # Thin: re-exports nothing; imports ReleaseNoteSelector
                                  # from src/juniper_docs/discovery for any legacy caller.

tests/unit/juniper_docs/          # Unit tests with mocked HTTP and PDF fixtures
├── test_sitemap_reader.py
├── test_inventory_builder.py
├── test_release_note_selector.py
├── test_companion_pdf_resolver.py
├── test_corpus_downloader.py
├── test_slug_classifier.py
├── test_signal_scorer.py
├── test_state_store.py
├── test_manifest_writer.py
└── test_runner.py
```

**Structure Decision**: The feature lives in one new package, `src/juniper_docs/`.
The package groups the work into five cohesive children: `models.py`, `discovery/`,
`acquire/`, `classify/`, and `harvest/`. The promoted base classes move into
`acquire/` and `discovery/`. `scripts/crawl_jvd.py` keeps only the validated-designs
classes (`JvdCatalogWalker`, `JvdCrawlRunner`) and imports the shared base classes
from the new package, so the JVD crawl keeps working with no duplicate code. This is
reuse by direct import, not a legacy shim. The move is recorded so a reviewer can
audit it.

The package also holds the extra corpus sources. The `SitemapReader` reads the
marketing sitemap as a flat list of direct PDF URLs. The `MarketingAssetClassifier`
in `classify/asset_classifier.py` sorts each marketing asset by its asset-type path
segment. The `HarvestRunner` `--source` option selects the documentation sitemap, the
marketing sitemap, or both. The product landing family is a planned third source.

## Complexity Tracking

The table separates grandfathered debt from new design, as the constitution requires.

| Violation | Type | Why Needed | Simpler Alternative Rejected Because | Remediation |
|-----------|------|------------|--------------------------------------|-------------|
| One new top-level child (`juniper_docs`) under `src/`, which already holds about 46 children | Grandfathered parent, new child | The feature needs a cohesive, discoverable home. The repository convention is one feature equals one top-level `src/` package, as with `upgrade_portal` and `ssid_consolidation`. | Nesting the package under an unrelated existing package such as `analytics/` or `inventory/` harms discoverability and cohesion. It also mixes Mist API code with documentation-crawl code. | A separate refactor groups the `src/` top-level packages into domain super-packages. This is tracked as its own incremental issue and is out of scope for this feature. |
| Move of shared classes out of `scripts/crawl_jvd.py` | Touched existing code | The spec requires reuse and extension of the proven classes (FR-008, FR-013, FR-018). The classes must live in the package so both the JVD crawl and the harvester share one copy. | Duplicating the classes in the package breaks the single-source rule and drifts over time. | The move is complete in this feature. `scripts/crawl_jvd.py` imports the base classes. No further remediation is needed. |
