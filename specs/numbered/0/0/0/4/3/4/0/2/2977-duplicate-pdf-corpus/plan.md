# Implementation Plan: Duplicate PDF Corpus

**Branch**: `fix/2977-duplicate-pdf-corpus` | **Date**: 2026-11-26 | **Spec**: `specs\numbered\0\0\0\4\3\4\0\2\2977-duplicate-pdf-corpus\spec.md`

**Input**: Numeric specification under `specs/numbered/` on the eight-level route `0\0\0\4\3\4\0\2`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Keep research, data model, quickstart, contracts, and checklists under `design\`.

## Summary

The prevention code for issue #2977 is on `main` (R02 to R06). Two gaps remain in the code. The manual sorter leaves stale document paths (R18). No test covers equal-size distinct bytes (R07), and no test covers the consolidator (R10). The historical copy run needs owner inputs.

This plan closes the code gaps with three focused changes and 13 tests. It adds a verifier for the owner copy procedure. It does not change the historical corpus.

## Technical Context

**Language/Version**: Python 3.15 or newer (`copilot-instructions.md`, section Language and environment).

**Primary Dependencies**: None added. The change uses the standard library: `hashlib`, `sqlite3`, `shutil`, `pathlib`, `dataclasses`, and `logging`.

**Storage**: Stored PDFs under the output root `data/juniper_corpus` (R12). The state database `harvest_state.db` in the same folder (R20).

**Testing**: pytest. The test files live under `tests/unit/juniper_docs/`. The local gates table in `copilot-instructions.md` lists the commands.

**Target Platform**: Windows 11 for development. The code also runs on macOS and Linux (`copilot-instructions.md`, section What this repository is).

**Project Type**: Internal package under `src/mist/intelligence/juniper_docs/`, driven by the harvest and classification passes.

**Performance Goals**: The first content lookup hashes equal-size candidates only. The copy run reads the historical corpus twice: once for the inventory and once for the verification. The issue reports 7.73 GB (unverified, U1).

**Constraints**: No corpus access before the owner records the inputs (FR-012). No deletion in this issue (FR-013). Logs use ASCII only (constitution Principle V).

**Scale/Scope**: About 2,974 PDFs according to the issue (unverified U1). Three source changes, one changelog pair, and four test files.

## Constitution Check

*Gate applied before Phase 0 and again after Phase 1 design.*

- **Principle I, Five-Item Rule**: Pass. The record root holds five children. `design\` holds five children. `contracts\` holds three files. `checklists\` holds two files. The new functions hold at most five parameters, five blocks, and 25 lines. Existing violations in the touched files are not measured yet. Action: the T-LOCAL-GATES radon and pylint runs measure them before T-PR (conditional pass).
- **Principle II, Class-Based Architecture**: Pass. New logic lives in `ManualDocumentSorter` and `CorpusCopyVerifier`. The plan adds no wrapper function.
- **Principle III, Safety-First**: Pass. The manual sorter keeps dry-run as the default. The verifier refuses partial preconditions. No code path deletes a file. Deletion needs D-10.
- **Principle IV, Full Deployment Pipeline**: Pass by plan. Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the pipeline steps.
- **Principle V, Observability and Logging**: Pass by plan. Every new message uses ASCII. Each action has an info line before it and a debug line after it.
- **Principle VI, Inline Comments**: Pass by plan. Every new executable line carries an inline comment that explains intent.
- **Principle VII, Action Logging**: Pass by plan. Every file move, database write, file read for hashing, and copy has an info line before it and a debug line after it.
- **Technology: Python version**: Pass. Python 3.15 or newer.
- **Technology: mistapi**: Not applicable. No Mist REST call is in scope.
- **Technology: Podman and test containers**: Not applicable. No container starts for this change.
- **Technology: File paths**: Pass. Each path uses `pathlib.Path`.
- **Technology: Data directory**: Pass with a condition. The constitution requires product outputs under `data\`. The owner records the copy root under `data\` in T010. The verifier checks overlap with the source root and blank fields (test `test_preconditions_refuse_missing_or_overlapping_paths`).
- **Development workflow: README**: Not applicable. `README.md` names no harvester or sorter (L11). The change alters no menu operation.
- **Documentation: Release notes**: Pass by plan. Two fragments under `changelog.d\` (T009).
- **Security: Findings**: Pass by plan. Bandit runs on the touched package (T-LOCAL-GATES). No `# nosec` annotation is added.
- **Specification escalation**: Pass. The change touches more than three files, so a specification is required. This record satisfies the rule.
- **Multi-agent git**: Pass by plan. Issue #2977 exists and carries `in-progress`. The branch `fix/2977-duplicate-pdf-corpus` starts from `main`. T-PR checks open pull requests for file overlap before it opens. Labels follow the repository rule.

## Architecture

- **Prevention path (unchanged)**: The harvest runner builds `CorpusDownloader` (R11). The downloader fetches bytes and asks `CorpusContentIndex.find` for a canonical path (R03, R04). When the index holds no match, the downloader writes the file and calls `register` (R05).
- **Move paths**: The reclassifier, the runner, and the manual sorter move files. The reclassifier and the runner update `documents.local_path` (R15, R20). The manual sorter does not (R18). This plan adds that update.
- **Copy run path (new verifier)**: The verifier validates the preconditions. It builds the source inventory. The consolidator copies one file for each digest into the library root (R08, R09). The verifier compares the library with the inventory and checks that the source did not change.
- **Class names**: `CorpusContentIndex`, `CorpusDownloader`, `ManualDocumentSorter`, `LibraryConsolidator`, and the new `CorpusCopyVerifier` and `CopyRunPreconditions`.

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\0\4\3\4\0\2\2977-duplicate-pdf-corpus\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      content-index.md
      manual-sort-update.md
      copy-run-verifier.md
    checklists\
      requirements.md
      copy-run-preconditions.md
```

### File Change Map (repository paths)

| Path | Action | Purpose | Requirements |
| - | - | - | - |
| `src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py` | Modify | Record each applied move in `documents.local_path`. Count unrecorded moves. | FR-007, FR-008 |
| `src/mist/intelligence/juniper_docs/harvest/copy_verifier.py` | Add | Preconditions, inventory, comparison, and source-change check for the copy run | FR-010, FR-011, FR-012, FR-013 |
| `tests/unit/juniper_docs/test_content_dedup.py` | Modify | Add `test_same_size_different_bytes_are_both_kept` | FR-003 |
| `tests/unit/juniper_docs/test_manual_sorter.py` | Add | Three sorter tests | FR-007, FR-008 |
| `tests/unit/juniper_docs/test_library_consolidator.py` | Add | Four consolidator tests | FR-009, FR-013 |
| `tests/unit/juniper_docs/test_copy_verifier.py` | Add | Five verifier tests | FR-010, FR-011, FR-012, FR-013 |
| `changelog.d/issue-2977-manual-sort-paths.md` | Add | Release note for the sorter fix | FR-007 |
| `changelog.d/issue-2977-copy-run-verifier.md` | Add | Release note for the verifier | FR-010 |
| `specs/numbered/0/0/0/4/3/4/0/2/2977-duplicate-pdf-corpus/` | Add | This record, copied from the draft folder | All |

Files that stay unchanged: `content_index.py` (R02), `downloader.py` (R03 to R05), and `consolidator.py` (R08 and R09).

Also unchanged: `runner.py` (R11 to R13), `reclassifier.py` (R14 and R15), `state_store.py` (R20), `pdf_paths.py` (R21), `scripts/crawl_jvd.py` (R22), and the legacy record (R27).

## Design Details

### Manual sorter (FR-007, FR-008)

- `ManualDocumentSorter.run(database)` keeps `_read_rows` read-only.
- `_place_one` receives the database path. After `_move` returns the final path in apply mode, `_place_one` calls a new method `_record_new_path`.
- `_move` returns the final path. It returns nothing in dry-run mode.
- `_record_new_path` runs `UPDATE documents SET local_path = ?, updated_at = ? WHERE root_url = ?` in one transaction. It logs before and after the write. On `sqlite3.Error`, it logs both paths at error level and increments `unrecorded`.
- `SortStats` gains the field `unrecorded`. The contract `manual-sort-update.md` lists each field.

### Copy verifier (FR-010 to FR-013)

- `CopyRunPreconditions` holds five fields: `source_host`, `source_root`, `copy_root`, `output_root`, and `target_free_bytes`.
- `check_preconditions` refuses a blank text field, a path that equals or contains another path, and free space below the total source size. It runs before any read.
- `inventory` returns rows sorted by relative POSIX path. Each row holds the size and the SHA256 digest. Reads use blocks of one megabyte.
- `compare` builds the library inventory. It reports the source file count and the unique digest count. It lists the missing digests and the unmatched library files. It reports the expected duplicate count and whether the consolidator statistics match. It reports a pass only when every check passes.
- `source_changed` compares two inventories row for row.

## Dependencies

- No package is added or updated. `requirements.txt` and `requirements-dev.txt` stay unchanged. The T-LOCAL-GATES dependency audit row therefore does not apply.
- The change depends on merged work: the harvester (PR #3084, R55) and the prevention code (PR #4311, R51, and PR #4823, R52 and R54).

## Risks and Mitigations

| ID | Risk | Mitigation |
| - | - | - |
| RK-1 | A database write fails after a file moves, which leaves a stale path. | The sorter logs both paths at error level and counts the failure. The file stays in place. The rollback restores the database from a backup. |
| RK-2 | A changed PDF at a known URL drops the new version. | D-5 files a follow-up issue. The reclassifier logs each drop. |
| RK-3 | The crawler writes duplicates into `jvd_pdfs`. | D-6 files a follow-up issue. This record makes no claim about `jvd_pdfs`. |
| RK-4 | The copy run exhausts disk space. | FR-012 requires the owner to record the target capacity. The verifier refuses a run without enough free space. |
| RK-5 | The harvest writes into the source during the copy run. | The owner stops every harvest before the run. The source-change check fails the run if a file changes. |
| RK-6 | The consolidator runs untested. | T006 writes its tests before any copy run. |
| RK-7 | The first content lookup hashes many equal-size files. | The index groups files by size first. It hashes only the equal-size candidates, and it hashes each file once. |
| RK-8 | `Closes #2977` closes the issue before the copy run ends. | D-11 moves the copy run to a successor issue before T-PR. |
| RK-9 | Two canonical rules confuse a reader. | The contracts name both rules. The library folder keeps the most specific category (D-2). |

## Rollback Steps

1. Revert the squash commit on `main` with a new pull request. Do not force-push `main`.
2. Restore `data\juniper_corpus\harvest_state.db` from the backup taken before the sorter run. The runner stores the database at `output_dir / "harvest_state.db"` (runner line 140).
3. Move each file back to its logged source path. The sorter logs each source and target path at info level.
4. Remove the copy-run library root only after the verification report is saved. The source stays unchanged.

Caution: Step 4 removes only the library copy. The removal cannot be undone without a new copy run.

## Complexity Tracking

| Existing item | Why it stays | Remediation |
| - | - | - |
| Radon and pylint results for `manual_sorter.py` and `consolidator.py` are not measured in this record | The measurement needs a local run, which this record does not perform | T-LOCAL-GATES records the measured values in the pull request body |
| `scripts/crawl_jvd.py` bypasses the content index | D-6 keeps the crawler out of this issue | Follow-up issue filed before T-PR |
| The same-URL reuse rule skips a byte check | D-5 keeps the resume contract | Follow-up issue filed before T-PR |
