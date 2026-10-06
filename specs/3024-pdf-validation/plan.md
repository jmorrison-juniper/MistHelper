# PDF corpus validation plan

## Design

Add one private validation helper to `downloader.py`. The helper checks the PDF
header and opens the bytes through `pdfplumber` using `io.BytesIO`. It reads the
page count so malformed objects fail during validation. It closes the parser
before the helper returns.

Run the helper against a same-URL stored file before returning `skipped`.
Read stored bytes through `Path.read_bytes`. If validation fails, continue with
the normal fetch path. Run the helper against fetched bytes before path
allocation and atomic storage.

Keep parser exceptions inside the validation boundary. Return a boolean to the
downloader and log the rejection with the URL or stored path. Do not add a new
dependency because `pdfplumber` is already pinned for the Juniper documentation
harvester.

## Test design

Extend the existing corpus downloader tests with offline byte fixtures:

- a minimal parser-usable PDF,
- the same PDF without `%%EOF`,
- truncated bytes,
- malformed object bytes,
- a malformed stored file followed by a valid fetched response,
- a valid stored file that avoids a fetch.

Keep the existing non-PDF and network failure tests.

## Scope

Change only `src/mist/intelligence/juniper_docs/acquire/downloader.py`,
`tests/unit/juniper_docs/test_corpus_downloader.py`, the issue-specific Spec Kit
artifacts, and one issue-specific changelog fragment.
