# Quickstart: Juniper Documentation Corpus Harvester

This guide shows how to run the harvester and how to prove that it works. It is a
validation guide, not an implementation guide. See `data-model.md` and the `contracts/`
folder for the field-level detail. The code lives in `src/juniper_docs/`.

## Prerequisites

- Python 3.13 or newer.
- The repository virtual environment with the development dependencies installed.
  `pdfplumber` is already declared, so no extra install is needed.
- About 5 to 25 GB of free disk space for a full run.
- Optional: `zscaler-root-ca.crt` in the repository root for verified TLS behind the
  corporate proxy.

## Run a cold harvest

```powershell
# Run the whole US and EN harvest with safe defaults
python -m src.juniper_docs.harvest.runner
```

Expected outcome:

- The tool reads the sitemap index and the 16 US and EN child sitemaps.
- The tool records the full inventory in `data/juniper_corpus/harvest_state.db` before
  any download (SC-001).
- The tool downloads each companion PDF, sorts it into a category folder, and writes
  `manifest.json` and `manifest.csv`.

## Run a fast subset for a test

```powershell
# Point the tool at a recorded sitemap subset to validate quickly
python -m src.juniper_docs.harvest.runner --sitemap-source tests/unit/juniper_docs/fixtures/sitemap_subset.xml
```

Expected outcome: the tool builds the inventory and applies the release-note filter on
the subset, then resolves and downloads each companion PDF from the fixture host.

## Validate the acceptance scenarios

| Check | How to run | Expected result |
|-------|------------|-----------------|
| Inventory before download (SC-001) | Start a cold run and stop it after the log line `Inventory recorded`. | The `documents` table holds about 2,225 rows and no file is downloaded yet. |
| Release-note filter (SC-002) | Query `dropped_release_notes` after the filter. | Each product and major train keeps one note. Every non-release-note is kept. |
| Companion PDF order (FR-010a) | Inspect `pdf_candidates` for a multi-PDF document. | Exactly one row has `chosen = 1`. The reason shows the applied rule. |
| Resume with no re-download (SC-003) | Stop a run, then start it again. | The tool re-downloads zero completed documents. |
| Per-document failure (SC-006) | Inject a 404 and a timeout on single documents. | The run continues and records each failure. The exit code is 0. |
| Non-PDF body (FR-014) | Serve an HTML error page with a 200 status. | The tool rejects the file and marks the document failed. |
| Politeness (SC-008) | Measure the time between two requests in the log. | The delay is at least the configured minimum. |

## Validate the content sub-category

```powershell
# Run only the classify stage on already-downloaded uncategorized PDFs
python -m src.juniper_docs.harvest.runner --retry-failed
```

Expected outcome:

- Each uncategorized document gets a sub-category label, detected signal names, and
  numeric scores in the store (SC-007).
- The output tree gains a folder for each sub-category under `uncategorized/`.

## Prove the privacy invariant (SC-005)

```powershell
# Search the output tree and the store for any stored body text
Select-String -Path "data/juniper_corpus/manifest.json","data/juniper_corpus/manifest.csv" -Pattern "body_text|extracted_text"
sqlite3 data/juniper_corpus/harvest_state.db ".schema content_scores"
```

Expected outcome:

- The search finds no body-text field.
- The `content_scores` schema has columns for the signal group, the signal name, and
  the score only. There is no text column.

## Read the final summary

At the end of a run, the tool prints a summary. The summary shows the count for each
category and sub-category. It shows the downloaded, skipped, failed, and dropped
counts and the total bytes (FR-036, SC-009).

## Find the consolidated library

A full run writes to `data/juniper_corpus/` by default. After the 2026 harvest, the
operator consolidated every harvested PDF, the earlier `jvd_pdfs/` output, and the
locally scavenged PDF files into one root:

```text
data/juniper_pdf_library/
```

That root holds one folder for each category and one `library_index.csv` file. The
index lists the category, the file name, the relative path, and the size in bytes of
every PDF. The preserved state database sits at
`data/juniper_pdf_library/_harvest_record/harvest_state.db`.

Point a downstream tool, such as a PDF-to-Markdown converter, at that one root. Every
file in the root is unique by SHA-256 content hash, so the tool reads no duplicate.

Warning: do not delete `_harvest_record/harvest_state.db`. That file is the only
record of the terminal failures and the resolved URL of each document. A delete
forces a full re-harvest of more than 15,000 documents.

```powershell
# Count the files and confirm that every content hash is unique
Get-ChildItem data/juniper_pdf_library -Recurse -File -Filter *.pdf | Measure-Object
```

## Run the quality gates

```powershell
# Run the gates the repository enforces on the new package
ruff check src/juniper_docs
black --check src/juniper_docs
mypy src/juniper_docs
pytest tests/unit/juniper_docs --cov=src/juniper_docs --cov-report=term-missing
bandit -r src/juniper_docs
pydocstyle src/juniper_docs
interrogate src/juniper_docs
radon cc src/juniper_docs -nc
vulture src/juniper_docs
```

Expected outcome: every gate passes. Coverage is 90 percent or higher. Every function
is at radon complexity 10 or below. The one `# nosec B323` on the insecure TLS
fallback carries a justification.
