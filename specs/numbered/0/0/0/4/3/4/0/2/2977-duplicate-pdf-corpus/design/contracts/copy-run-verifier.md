# Contract: Copy Run Verifier

**Issue**: #2977

**Module**: `src/mist/intelligence/juniper_docs/harvest/copy_verifier.py` (new, T008)

**Classes**: `CopyRunPreconditions`, `InventoryRow`, `CopyVerificationReport`, and `CorpusCopyVerifier`

## Owner Procedure Mapping

| Owner step (issue comment of 2026-10-30) | Method |
| - | - |
| Inventory relative paths, sizes, and SHA256 hashes before copying | `CorpusCopyVerifier.inventory(root)` |
| Refuse a run without the five recorded inputs | `CorpusCopyVerifier.check_preconditions(preconditions, source_rows)` |
| Compare every copied file with the source | `CorpusCopyVerifier.compare(source_rows, library_root, consolidator_unique, consolidator_duplicates)` |
| Compare the unique digest sets | `compare` (fields `source_unique` and `missing_digests`) |
| Confirm the source inventory did not change | `CorpusCopyVerifier.source_changed(before_rows, after_rows)` |

## CopyRunPreconditions

- Fields: `source_host: str`, `source_root: Path`, `copy_root: Path`, `output_root: Path`, `target_free_bytes: int`.
- The owner records each value (checklist `copy-run-preconditions.md`).

## check_preconditions

- Signature: `check_preconditions(preconditions: CopyRunPreconditions, source_rows: list[InventoryRow]) -> None`.
- Raises `ValueError` when `source_host` is blank.
- Raises `ValueError` when `copy_root` or `output_root` equals `source_root`, or lies inside it, or contains it.
- Raises `ValueError` when `target_free_bytes` is smaller than the sum of `size_bytes` in `source_rows`.
- Runs before any read of the copy root.

## inventory

- Signature: `inventory(root: Path) -> list[InventoryRow]`.
- Walks `*.pdf` files under `root`. Reads each file in blocks of one megabyte.
- Returns rows sorted by `relative_path`, a POSIX path relative to `root`.
- `InventoryRow` fields: `relative_path: str`, `size_bytes: int`, `sha256: str`.

## compare

- Signature: `compare(source_rows: list[InventoryRow], library_root: Path, consolidator_unique: int, consolidator_duplicates: int) -> CopyVerificationReport`.
- Builds the library inventory with `inventory(library_root)`.
- Computes the expected duplicate count as the source file count minus the source unique count.
- Sets `stats_match` when `consolidator_unique` equals the source unique count and `consolidator_duplicates` equals the expected duplicate count.
- Sets `passed` only when `missing_digests` is empty, `unmatched_library_files` is empty, and `stats_match` is true.

## CopyVerificationReport fields

- `source_files`, `source_unique`, `library_files`.
- `missing_digests`: digests in the source that the library lacks. Sorted.
- `unmatched_library_files`: relative paths in the library whose digest the source lacks. Sorted.
- `expected_duplicates`, `stats_match`, `passed`.

## source_changed

- Signature: `source_changed(before_rows: list[InventoryRow], after_rows: list[InventoryRow]) -> bool`.
- Returns true when the two lists differ in count, path, size, or digest.

## Logging

- Each method logs an info line before its reads and a debug line after them, with counts only (constitution Principle VII).
- Log text uses ASCII only (constitution Principle V).

## Tests That Pin the Contract

- `test_inventory_records_relative_path_size_and_digest` (T007).
- `test_compare_passes_when_library_matches_source_digests` (T007).
- `test_compare_fails_when_a_library_file_has_no_source_match` (T007).
- `test_source_changed_detects_a_modified_source_file` (T007).
- `test_preconditions_refuse_missing_or_overlapping_paths` (T007).
