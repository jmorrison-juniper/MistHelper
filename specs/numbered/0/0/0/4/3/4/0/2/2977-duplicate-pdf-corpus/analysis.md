# Specification Analysis Report: Duplicate PDF Corpus

**Issue**: #2977

**Scope**: Consistency across `spec.md`, `plan.md`, `tasks.md`, the remote code on `main` (`f03c6c9b36d612a48d7b9652998c2fd87dd777ca`), and the contracts. Defects in existing work are listed by identifier DF-1 to DF-12.

## Consistency Review

- **C1, requirements to tasks and tests**: Each FR from FR-001 to FR-013 maps to at least one task and at least one test. FR-001 maps to T001 and the test `test_same_bytes_under_different_names_keep_one_file`. FR-003 maps to T003. FR-007 and FR-008 map to T004 and T005. FR-009 maps to T006 and T011. FR-010 to FR-013 map to T007, T008, T010, T012, and T013.
- **C2, file map to tasks**: Each path in the `plan.md` file change map appears in one task. The source file `manual_sorter.py` appears in T005. The module `copy_verifier.py` appears in T008. The four test files appear in T003, T004, T006, and T007. The two changelog fragments appear in T009.
- **C3, test count**: The planned tests total 13. The count comes from one modified file (1 test) and three new files (3, 4, and 5 tests). `spec.md` SC-001, `plan.md`, `tasks.md`, and `2977-STATUS.json` agree on 13.
- **C4, task count**: `tasks.md` lists 17 tasks. `2977-STATUS.json` reports 17.
- **C5, decision identifiers**: Decisions D-1 to D-11 appear in `research.md`. `spec.md` cites D-3, D-5, D-6, D-9, D-10, and D-11. `plan.md` cites D-2, D-5, D-6, D-8, and D-11. Each citation matches the decision text.
- **C6, remote evidence count**: `research.md` lists 57 remote rows. `2977-STATUS.json` lists 57 `remote_checks`. `2977-summary.md` states 57.
- **C7, route and depth**: The record root holds five children. `design\` holds five children. `contracts\` holds three files. `checklists\` holds two files. The route folder `0\0\0\4\3\4\0\2` holds two children after this record.
- **C8, Closes conflict**: The brief requires `Closes #2977` in the pull request body. The owner comments keep the historical decision open. D-11 resolves the conflict with a successor issue. Until the owner confirms D-11, T-PR stays blocked.
- **C9, copy root under data**: The constitution requires product outputs under `data\`. The verifier checks blank fields, overlap, and capacity. It does not check the `data\` location. T010 makes the `data\` location an owner condition. This item stays open until the owner records the copy root.

## Defects in Existing Work

- **DF-1, manual sorter does not record moved paths**: `ManualDocumentSorter` moves files with `source.replace(target)` (R17, line 152). No `UPDATE` statement exists in the module (R18). `_read_rows` opens the database read-only (lines 120 to 131). Effect: each document row keeps the old path after a move. A second pass counts the row as missing (`_place_one`, line 133). Fixed by T005.
- **DF-2, reclassifier reads paths that DF-1 leaves stale**: The reclassifier selects `local_path` (lines 47 and 48) and opens that file (line 138) at HEAD. Its update path writes the new path (R15, line 210). A stale path from DF-1 makes the reclassifier open a missing file. Fixed by T005 for the manual sorter path. No change to the reclassifier.
- **DF-3, consolidator has no caller and no test**: No call to `LibraryConsolidator(` exists in `src`, `tests`, or `scripts` at HEAD (R08). Test file `test_library_consolidator.py` is absent (R10). The copy run in T011 uses code that no test covers. Fixed by T006.
- **DF-4, same-URL reuse drops a source without a byte check**: `_place_path` returns the same-URL owner without comparing bytes (R21, line 63). `_relocate` then calls `unlink` on the source (R13, line 434, and R14, line 196). A changed PDF at a known URL can be dropped. Deferred by D-5. Follow-up issue required before T-PR.
- **DF-5, crawler bypasses the content index**: `scripts/crawl_jvd.py` builds the base `JvdDownloader` (R22, line 80) for `OUT_DIR` (line 29, `jvd_pdfs`). The base class has no content index. Deferred by D-6. Follow-up issue required before T-PR.
- **DF-6, equal-size test gap and wrong comment**: Test `test_different_bytes_are_both_kept` (line 44) claims equal sizes in its docstring (line 45). Its payload at line 46 adds five bytes. Fixed by T003 (R07).
- **DF-7, stale issue references**: The claim comment of 2026-10-01 names `src/juniper_docs` and `acquire/content_index.py` (R02 holds the path `harvest/content_index.py`, and R43 shows no `src/juniper_docs`). The blocker comment of 2026-09-19 names issue #2738 as the harvester issue. GitHub item 2738 is a closed pull request titled `fix(tools): infer edge case applicability` (R56). The harvester shipped in pull request #3084 (R55). The branch and spec folder names carry 2738.
- **DF-8, stale label and blocker**: The issue carries the label `in-progress` (issue labels). No branch for this work exists on the remote (R44, R45). The blocker comment of 2026-09-19 is stale. Pull request #3084 merged on 2026-09-20 (R55).
- **DF-9, database counts disagree with the issue**: The state backup holds 5,352 rows with `local_path` and 2,892 distinct paths (L06). The issue reports 2,974 PDFs and 2,623 distinct documents. The backup holds no hash column (L05). The disagreement is recorded as unresolved (U2).
- **DF-10, pull request body count drift**: Pull request #4311 states "5 tests" (R51). The file holds seven tests after pull request #4823 added two (R06, R54). This drift has no effect on behavior.
- **DF-11, local-only commits**: Branch `356b65d402793c28c5eea9f6124489ecb230b8a1` holds two commits that main lacks (L10). The blob SHAs of the two changed files differ from main. The content diff is unverified (U5). The owner decides whether to delete the local branch.
- **DF-12, corpus root named by a guard**: The guard test names `C:\Users\jmorrison\Downloads\juniper-library-md` as the new corpus root (R26, line 12). Whether it is the source corpus is unverified (U7). This record did not open that path.

## Legacy Record Verification (`specs\numbered\0\0\0\4\3\4\0\2\2977-harvest-index-moves`)

The legacy record is a draft to verify (brief section 3, step 3). Ten claims are counted: FR-001 to FR-005, SC-001 to SC-004, and the Status line. The counting unit is one claim.

| Claim | Legacy text (short) | Result | Evidence |
| - | - | - | - |
| FR-001 | Find a stored PDF at its current path after reclassification moves it | verified | Test `test_index_finds_canonical_file_after_reclassification_move` (line 74) |
| FR-002 | Reuse a remaining file when the old path no longer exists | verified | Test `test_index_finds_remaining_duplicate_after_canonical_is_removed` (line 87) |
| FR-003 | Store a new PDF when no stored file matches | verified | Test `test_different_bytes_are_both_kept` (line 44) and the write path in `downloader.py` (lines 77 to 89, R04, R05) |
| FR-004 | Keep distinct PDFs separate when sizes match | absent | No equal-size test (R07). The test at line 44 uses different sizes (DF-6) |
| FR-005 | Leave files outside the output directory unchanged | verified | `content_index.py` contains no write call (R02 body). Test `test_index_reads_only_and_ignores_empty_and_missing` (line 54) |
| SC-001 | After a move, a repeated download creates zero extra PDF files | verified | Test `test_same_bytes_under_different_names_keep_one_file` (line 20) asserts one file |
| SC-002 | The repeated source record points to an existing file after the move | verified | Test `test_index_finds_canonical_file_after_reclassification_move` (line 74) asserts the moved path |
| SC-003 | Two different PDFs of the same size remain two files | absent | Same gap as FR-004 (R07, DF-6) |
| SC-004 | Tests use temporary files only | verified | All seven tests use `tmp_path` (lines 20, 31, 44, 54, 63, 74, 87) |
| Status | `Status: Draft` | stale | Pull request #4823 merged the record on 2026-11-19 (R54, R27) |

Totals: verified 7, absent 2, stale 1. `2977-STATUS.json` records these totals.

Assumption in the legacy record: the harvest already reuses files with identical content when their indexed paths remain valid. The allocator compared candidates in one target folder only (`pdf_paths.py` lines 57 to 66, R21). The assumption holds only inside one folder.

## Unresolved Items

- UR-1: Owner confirmation of D-11 (close #2977 with this pull request, and move the copy run to a successor issue).
- UR-2: Owner decision on D-9 (licensing text) and D-10 (deletion of redundant copies). Both are HUMAN-DECISION-REQUIRED.
- UR-3: Owner inputs for FR-012: source host, source path, copy root, output root, and target free bytes (T010).
- UR-4: Confirmation of the source corpus location (U7).
- UR-5: File the successor issue for the copy run. File the follow-up issues for D-5 and D-6. The filings occur before T-PR.
- UR-6: Measurement of the radon and pylint values for the touched files (plan, Complexity Tracking). The measurement occurs in T-LOCAL-GATES.
- UR-7: Reconciliation of the database counts with the issue figures (DF-9, U2).
- UR-8: The content diff of the two local-only commits (DF-11, U5).
