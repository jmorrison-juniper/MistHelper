# PDF corpus validation

## Problem

The corpus downloader accepts any response that starts with `%PDF`. A damaged
response can enter the corpus and later receive the unclassified label.

## Requirements

- Validate PDF structure with the repository's existing `pdfplumber` dependency.
- Validate a new response before the downloader writes it.
- Validate a same-URL stored file before the downloader reuses it.
- Accept a valid PDF without a trailing `%%EOF` marker when the parser can read it.
- Reject truncated data and malformed PDF objects.
- Keep validation offline and use in-memory or temporary-file fixtures.
- Preserve the current outcome, path, size, and failure-reason contract.

## Scenarios

1. A parser-usable PDF downloads and stores successfully.
2. Truncated PDF bytes fail and do not create a stored file.
3. A PDF without `%%EOF` succeeds when `pdfplumber` reads it.
4. Malformed PDF objects fail and do not create a stored file.
5. A same-URL valid stored file is reused without a fetch.
6. A same-URL malformed stored file is not reused, and a valid replacement downloads.
