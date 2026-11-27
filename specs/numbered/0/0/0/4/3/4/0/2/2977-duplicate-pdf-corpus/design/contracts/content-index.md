# Contract: Content Index

**Issue**: #2977

**Module**: `src/mist/intelligence/juniper_docs/harvest/content_index.py`

**Class**: `CorpusContentIndex` (R02, line 21)

## Constructor

- `CorpusContentIndex(root: Path)`. The root is the output root. The index reads the root and never changes it.

## Method: find

- Signature: `find(payload: bytes) -> Path | None`.
- Returns the canonical path of a stored PDF with identical bytes. Returns `None` when no stored PDF matches.
- Hashes the payload with SHA256 and looks up the digest.
- Groups stored PDFs by byte size. Hashes only the candidates whose size equals the payload size, and hashes each file once.
- Drops a canonical path that no longer exists. Refreshes the size group before the second lookup.
- Logs an info line before the first index build and before each size refresh. Logs a debug line after each build and refresh.

## Method: register

- Signature: `register(path: Path, payload: bytes) -> None`.
- Records `path` as the canonical path for the SHA256 digest of `payload`.
- Keeps the first registered path for each digest. A later registration for the same digest changes nothing.
- Adds `path` to the size group for `len(payload)`.

## Invariants

- The index never writes, renames, or deletes a file (FR-004).
- A zero-byte file is not a stored PDF.
- A digest maps to one canonical path at a time (D-1, D-2).
- The first sorted path wins for prevention (D-2).

## Tests That Pin the Contract

- `test_same_bytes_under_different_names_keep_one_file` (line 20).
- `test_existing_file_from_earlier_run_is_canonical` (line 31).
- `test_different_bytes_are_both_kept` (line 44).
- `test_index_reads_only_and_ignores_empty_and_missing` (line 54).
- `test_index_drops_canonical_path_that_was_removed` (line 63).
- `test_index_finds_canonical_file_after_reclassification_move` (line 74).
- `test_index_finds_remaining_duplicate_after_canonical_is_removed` (line 87).
- `test_same_size_different_bytes_are_both_kept` (new, T003).
