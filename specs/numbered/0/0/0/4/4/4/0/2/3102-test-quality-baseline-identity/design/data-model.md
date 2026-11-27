# Data model: Test-quality baseline identity

The data model defines the entities that the gate and prune commands read and write. The natural key of a baseline entry is its identity key. The identity key is `(category, rule_id, file_path, explanation, content_anchor)`.

## Entities

### Baseline entry

A stored JSON object in the baseline file. The schema is in `contracts/baseline-schema.md`.

- Natural key: the identity key.
- Lifecycle: the write run creates it. The gate matches it. The prune run or the write run removes it.
- Count: 733 entries on main (R-01). The migration sets the final count.

### Finding

A computed result from one analyzer run.

- Fields: entry fields without `content_anchor`, plus `content_anchor` after the pipeline assigns it. A detector sets the sentinel `file-level` for a file-level finding (R-45). The pipeline sets the digest for every other finding from its flagged line. `line_number` is at least 1 (`detection/types.py`, blob 89ad1fbc, R-43).

### Occurrence

One counted unit of an identity key. The gate builds two multisets of occurrences. One multiset holds the current findings. The other holds the baseline entries.

- New occurrences are current occurrences beyond the baseline count for a key.
- Removed occurrences are baseline occurrences beyond the current count for a key, in analyzed files.

### Content anchor

A derived value. It is the SHA-256 digest of the normalized flagged line, or the sentinel `file-level`.

- Invariant: the value is 64 lowercase hexadecimal characters, or exactly `file-level`.
- Invariant: the value is stable under line moves and under whitespace changes that the normalization removes.

### Gate result

A derived value for one gate run.

- Fields: exit code, files checked, findings checked, new occurrence list, removed occurrence count, and advisory stale paths.
- The output contract lists each printed field.

### Migration record

A derived value in the pull request body.

- Fields: entry count before and after, retained count, dropped count, and each dropped entry with its reason.
- Reasons are `file missing on main` and `no current finding matches`.

## State transitions

| From | Event | To | Effect |
| - | - | - | - |
| Baseline occurrence matched | Line number changes, anchor unchanged | Baseline occurrence matched | None. The gate exits 0. |
| Baseline occurrence matched | Flagged line text changes | Baseline occurrence unmatched, finding new | The gate exits 1 for the new finding. |
| Baseline occurrence matched | Finding disappears in an analyzed file | Baseline occurrence unmatched | The gate prints `gate_removed` and exits 0. |
| Baseline occurrence unmatched | Prune or write run | Removed | The baseline file drops the occurrence. |
| Baseline occurrence in unscanned, skipped, or parse-error file | Prune run | Retained or dropped by file rule | Parse-error and skipped files keep entries. Unscanned files lose entries. |
| Finding new | Write run after review | Baseline occurrence matched | The next gate run exits 0. |
| Finding new | Not reviewed | Gate fails | The pull request stays red. |

## Invariants

- The baseline file holds one entry for each occurrence of an identity key.
- Two entries with the same identity key are two occurrences, not a duplicate error.
- Each entry has a valid `content_anchor` value. A loader rejects any other value with exit code 2.
- Each entry has a `file_path` value that uses forward slashes.
