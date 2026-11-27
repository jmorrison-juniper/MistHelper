# Data Model: Duplicate PDF Corpus

**Issue**: #2977

## Entities

### Stored PDF

- Location: a file with suffix `.pdf` under the output root `data\juniper_corpus` (R12).
- Natural key: the SHA256 digest of the file bytes (D-1).
- Attributes: the path, the byte size, and the URL that first stored the file.
- Empty files (zero bytes) are not stored PDFs. The index ignores them (`content_index.py`, R02).

### Document row

- Location: table `documents` in `harvest_state.db`, in the output root (R20).
- Natural key: `root_url`.
- Attributes used by this change: `stage`, `category`, `local_path`, `resolved_pdf_url`, and `updated_at`.
- Stage values seen in the code and the backup: `discovered`, `downloaded`, `classified`, `dropped`, `failed`, and `no_pdf` (state store and L06).
- This change writes `local_path` and `updated_at` only. It does not write `stage` or `category`.

### Canonical path map

- Location: memory, one instance of `CorpusContentIndex` for each downloader.
- Key: SHA256 digest. Value: the canonical path of the first file that holds the digest.
- The map resets on each run. The index rebuilds it from the file system.

### Inventory row

- Location: memory, produced by `CorpusCopyVerifier.inventory`.
- Natural key: `relative_path`, a POSIX path relative to the source root.
- Attributes: `size_bytes` and `sha256`.
- Rows sort by `relative_path`. Two inventories compare row for row.

### Library copy

- Location: a file under the library root, in the folder named after the source category.
- Natural key: the SHA256 digest of its bytes (one library copy for each digest).
- The consolidator names each copy with `_free_name`. A name clash adds the suffix `-2`, `-3`, and so on.

### Copy verification report

- Location: memory, returned by `CorpusCopyVerifier.compare`. The owner stores the report.
- Attributes: `source_files`, `source_unique`, `library_files`, `missing_digests`, `unmatched_library_files`, `expected_duplicates`, `stats_match`, and `passed`.

## Relationships

- One stored PDF has one digest. Many document rows can name the same stored path (`local_path`). The state backup shows this pattern (L06).
- One digest has one canonical path in the content index. Other paths with the same bytes are not written.
- One inventory row maps to one source file. One library copy maps to one digest.

## State Transitions

### Stored PDF

- Absent to present: the downloader writes the file and calls `register` (R05).
- Present to moved: the reclassifier or the manual sorter moves the file. The digest does not change. The path changes.
- Present to removed: the reclassifier or the runner calls `unlink` on a redundant source (R13, R14). The canonical file remains.
- Present to missing: a file removed by hand. The index drops the canonical path on the next lookup and searches the same size group (`content_index.py` lines 36 to 38).

### Document row

- `classified` with `local_path` set to the old path, to `classified` with `local_path` set to the new path. This change adds this transition for manual sorting.
- The reclassifier and the runner already write the new path (R15, R20).

### Library copy

- Absent to present: `shutil.copy2` writes the file under a free name (R09).
- Present to present: no change. The consolidator never overwrites a library copy.

### Copy run

- Preconditions recorded to inventory taken to library written to report compared.
- A report with `passed` false stops the run. The source stays unchanged.

## Natural Key Rules

- A digest is the identity of a document. A file name is not an identity.
- A `root_url` is the identity of a document row. A stored path is not an identity.
- A relative path is the identity of a source file within one inventory.
