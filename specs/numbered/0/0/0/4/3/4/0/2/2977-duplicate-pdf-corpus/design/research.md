# Research: Duplicate PDF Corpus

**Issue**: #2977 (Corpus harvest: 351 duplicate PDF files fill 11.8 percent of the corpus)

**Remote reference**: branch `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, read on 2026-11-26.

## Method

- Read the issue with `gh issue view`. The issue holds 8 comments, from 2026-09-19 to 2026-11-17.
- Listed linked pull requests with `gh pr list --search "2977"`. Read each linked pull request with `gh pr view`. Pull request 160 matched the search text through a link to a pygments issue with the same number. Its body does not name issue 2977, so it is not linked.
- Issue labels read with the issue: chore, tests, in-progress, data-quality, performance, src, priority:P3, and severity:low. The issue is open.
- Read the legacy record `specs\numbered\0\0\0\4\3\4\0\2\2977-harvest-index-moves` in full. It holds one file.
- Read remote bodies through the contents endpoint and decoded the base64 text. The blob endpoint served the body when the contents call returned no body.
- Checked each commit, branch, and tag with the GitHub API. Checked ancestry with the compare endpoint.
- Read the local checkout with read-only commands only. No test, build, lint, container, or corpus file ran or opened.
- Early contents calls failed because PowerShell read `$path?ref` as one variable name. Later calls used string concatenation. The failed calls did not change any result.
- No skill loaded. The issue makes no Podman or Juniper device claim.

## Decisions

### D-1. The identity key is the SHA256 digest of the stored bytes

- Alternatives: file name, file name with size, file size, or SHA256 digest.
- Chosen: SHA256 digest.
- Reason: Names fail across categories. Size alone cannot prove equal bytes, as the legacy record FR-004 states.
- Risk: The first lookup hashes equal-size candidates. Size grouping limits this work (`content_index.py` lines 83 to 93 on `main`, R02).
- Human: false.

### D-2. Each rule keeps one canonical file, and the copy run uses a second rule

- Alternatives: one canonical rule for both paths, the first sorted path, the newest file, or the most specific category.
- Chosen: prevention keeps the first sorted path (`content_index.py` line 81 and line 88 on `main`, R02). The copy run keeps the most specific category (`LibraryConsolidator._best_copy`, `consolidator.py` lines 84 to 86, R08).
- Reason: Prevention must not move a stored file. The library is a read copy, and readers need the most specific folder.
- Risk: Two rules exist. The plan and the contracts name both rules, and tests cover each rule.
- Human: false.

### D-3. This issue does not change the historical corpus in place

- Alternatives: delete duplicates in place, move files in place, run the consolidator on a verified copy, or leave the corpus unchanged.
- Chosen: run the consolidator on a verified copy into an empty library root. Do not change the source.
- Reason: The owner decided this on 2026-10-21. The owner required source preservation and a verified copy on 2026-10-30.
- Risk: The copy uses disk space close to the library size. Mitigation: the owner records target capacity first (FR-012).
- Human: false.

### D-4. Fix the manual sorter so it updates `documents.local_path` in this issue

- Alternatives: open a separate issue, or document the stale path as a known limit.
- Chosen: fix in this issue. The sorter writes the new path after each move, in one transaction.
- Reason: The claim comment of 2026-10-01 requires alias references to stay valid after manual sorting. The defect sits in the deduplication path (R18).
- Risk: The file moves before the database update. A failed update leaves a stale path. Mitigation: the sorter logs both paths, counts the failure, and keeps the file in place (contract `manual-sort-update.md`).
- Human: false.

### D-5. Keep the same-URL reuse rule, and file a follow-up issue for byte checks

- Alternatives: add a byte comparison now, remove the `unlink` calls, or keep the rule and file a follow-up issue.
- Chosen: keep the rule and file a follow-up issue before the pull request opens.
- Reason: A byte check changes the resume contract that `test_existing_file_from_earlier_run_is_canonical` covers. The change needs its own review. AGENTS.md requires one concern for each issue.
- Risk: A changed PDF at a known URL can drop a new version. The reclassifier logs each drop at info level (R14, `reclassifier.py` line 196).
- Human: false.

### D-6. Keep the legacy crawler out of this issue, and file a follow-up issue

- Alternatives: route `scripts/crawl_jvd.py` through the content index now, remove the crawler, or keep the crawler and file a follow-up issue.
- Chosen: keep the crawler and file a follow-up issue.
- Reason: The crawler writes to `jvd_pdfs` (R22, `crawl_jvd.py` line 29). That folder sits outside the output root `data/juniper_corpus` (R12). The crawler usage outside the repository is unknown (see Unverified U4).
- Risk: The crawler can write duplicate files into `jvd_pdfs`. This issue makes no claim about that folder.
- Human: false.

### D-7. Add 13 focused tests in four files

- Alternatives: no new tests, or integration tests that use real PDFs.
- Chosen: one test in the existing `test_content_dedup.py`, and three new test files. Each new file uses temporary files and synthetic bytes.
- Reason: FR-003, FR-007, FR-008, FR-009, FR-010, FR-011, and FR-012 have no test on `main` (R07, R10, R18, R19). Real PDFs would slow the run and add data risk.
- Risk: Synthetic bytes do not prove PDF parsing. The parsing path has its own tests on `main`.
- Human: false.

### D-8. Add `CorpusCopyVerifier` for the owner verification procedure

- Alternatives: PowerShell one-liners, consolidator statistics only, or a new verifier module.
- Chosen: a new verifier module under `harvest/`.
- Reason: The owner procedure needs an inventory before the copy, a comparison after it, and a source-unchanged proof (issue comment of 2026-10-30). Statistics alone prove no source change. One-liners cannot run in the test suite.
- Risk: The module adds maintenance. Mitigation: five tests cover its public methods.
- Human: false.

### D-9. Write no licensing or legal text in this issue

- HUMAN-DECISION-REQUIRED: decide whether a free-corpus licensing document exists, and who writes its text.
- Alternatives: create `documentation/free-juniper-corpus.md` now, or skip the document.
- Chosen: skip the document. The reserved path stays absent (R40).
- Recommended: a human owner writes any licensing text. The agent writes none.
- Human: true.

### D-10. Deleting redundant copies from the historical corpus needs human approval

- HUMAN-DECISION-REQUIRED: decide whether the 351 redundant copies in the source corpus are deleted. Warning: deletion removes production data and cannot be undone.
- Alternatives: delete all redundant copies in place, delete each copy after the copy-run report passes, or keep every copy.
- Recommended: keep every copy until the copy-run report passes. Then decide per copy. Do not delete without a recorded approval in the successor issue.
- Human: true.

### D-11. Split the copy run into a successor issue, and close #2977 with this pull request

- Alternatives: keep #2977 open until the copy run ends, or close #2977 and move the copy run to a successor issue.
- Chosen: close #2977 with this pull request. File the copy run as a successor issue before the pull request opens.
- Reason: AGENTS.md requires one concern for each issue. The brief requires `Closes #2977` in the pull request body. The owner keeps the historical decision open, so the successor issue carries it.
- Risk: The owner may want #2977 to stay open. Mitigation: the orchestrator confirms D-11 before T-PR.
- Human: false.

## Remote verification

Each row is one check against `main` or against the GitHub object named in the row. The blob column holds the blob SHA for a file row and the object SHA for a commit row. The column reads `none` when no object applies.

| ID | Claim | Path | Result | Blob or object SHA | Line |
| - | - | - | - | - | - |
| R01 | Remote main head is the reference | (branch) main | present | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | 0 |
| R02 | Content index class exists | src/mist/intelligence/juniper_docs/harvest/content_index.py | present | bf1e1fb669efd7b13a821c5b1766e32d4f9753bf | 21 |
| R03 | Downloader builds the content index | src/mist/intelligence/juniper_docs/acquire/downloader.py | present | cb3242a24988f39e317d490eaa4bd70444740471 | 60 |
| R04 | Downloader reuses the canonical file | src/mist/intelligence/juniper_docs/acquire/downloader.py | present | cb3242a24988f39e317d490eaa4bd70444740471 | 77 |
| R05 | Downloader registers each written file | src/mist/intelligence/juniper_docs/acquire/downloader.py | present | cb3242a24988f39e317d490eaa4bd70444740471 | 89 |
| R06 | Dedup test module has seven tests, and the first test starts here | tests/unit/juniper_docs/test_content_dedup.py | present | 5aa083f7177ccc92b3208029f79c10c4f44c1db5 | 20 |
| R07 | An equal-size, distinct-bytes test exists | tests/unit/juniper_docs/test_content_dedup.py | absent | 5aa083f7177ccc92b3208029f79c10c4f44c1db5 | 0 |
| R08 | Consolidator class exists | src/mist/intelligence/juniper_docs/harvest/consolidator.py | present | 081343043b3ea52407a26a1df6463f316f2e909f | 43 |
| R09 | Consolidator copies with copy2 and calls no unlink or remove | src/mist/intelligence/juniper_docs/harvest/consolidator.py | present | 081343043b3ea52407a26a1df6463f316f2e909f | 94 |
| R10 | Consolidator test file exists | tests/unit/juniper_docs/test_library_consolidator.py | absent | none | 0 |
| R11 | Runner constructs CorpusDownloader with the output root | src/mist/intelligence/juniper_docs/harvest/runner.py | present | 988ad34b755492816819f01bce81ac7a12293f94 | 171 |
| R12 | Runner default output root is data/juniper_corpus | src/mist/intelligence/juniper_docs/harvest/runner.py | present | 988ad34b755492816819f01bce81ac7a12293f94 | 52 |
| R13 | Runner unlinks a redundant download | src/mist/intelligence/juniper_docs/harvest/runner.py | present | 988ad34b755492816819f01bce81ac7a12293f94 | 434 |
| R14 | Reclassifier unlinks a redundant download | src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py | present | f5c09b6090214e33a0bd6e5681826ad6a3922553 | 196 |
| R15 | Reclassifier updates documents.local_path | src/mist/intelligence/juniper_docs/classify/reprocessing/reclassifier.py | present | f5c09b6090214e33a0bd6e5681826ad6a3922553 | 210 |
| R16 | Manual sorter class ManualDocumentSorter exists | src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py | present | 8e42448017efd55e3ac487ee076b6a1b9e0841e4 | 88 |
| R17 | Manual sorter moves files with replace | src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py | present | 8e42448017efd55e3ac487ee076b6a1b9e0841e4 | 152 |
| R18 | Manual sorter updates documents.local_path | src/mist/intelligence/juniper_docs/classify/reprocessing/manual_sorter.py | absent | 8e42448017efd55e3ac487ee076b6a1b9e0841e4 | 0 |
| R19 | Manual sorter test file exists | tests/unit/juniper_docs/test_manual_sorter.py | absent | none | 0 |
| R20 | State store writes local_path on download | src/mist/intelligence/juniper_docs/harvest/state_store.py | present | 64416e5178ce44a609c6b31fd86d32dfd2381767 | 191 |
| R21 | Same-URL owner reuse returns without a byte check | src/mist/intelligence/juniper_docs/acquire/pdf_paths.py | present | b4beef67211ee39e01912d22a8d6b17c944843a5 | 63 |
| R22 | Crawler uses the base downloader with no content index | scripts/crawl_jvd.py | present | 855bd6005bccf8fbecc3576485e7c9aa6491b1f9 | 80 |
| R23 | CI type-check scope is MYPY_PATHS | .github/workflows/ci.yml | present | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | 93 |
| R24 | CI dead-code, docstring, and docstring-coverage scopes | .github/workflows/ci.yml | present | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | 101 |
| R25 | CI code-quality threshold is 9.5 | .github/workflows/ci.yml | present | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | 122 |
| R26 | Corpus path guard names the new corpus root | tests/guardrails/test_juniper_corpus_paths.py | present | 081ea0bac4d75d80e1134e7fc0715344dde4a3c1 | 12 |
| R27 | Legacy record spec.md exists with its title | specs/numbered/0/0/0/4/3/4/0/2/2977-harvest-index-moves/spec.md | present | 803982a1fd96f8e426ba0404fd13cc6153ab30fc | 1 |
| R28 | Legacy record folder holds spec.md only | specs/numbered/0/0/0/4/3/4/0/2/2977-harvest-index-moves | present | bb4d0b7e3e561c9c4aeaeb9f587f35795e0d649d | 0 |
| R29 | Changelog fragment for content dedup exists | changelog.d/issue-2977-content-dedup.md | present | 089a5d60b5a9aae75aa9558b5ddcf0ec07f11277 | 0 |
| R30 | Changelog fragment for index moves exists | changelog.d/issue-2977-harvest-index-moves.md | present | f1b62abb5238f0d69c5b911f1596bdd281be804d | 0 |
| R31 | Generic agent rules exist | AGENTS.md | present | 44a9afffb5bd6f774973a845d27343e4e528b6ad | 0 |
| R32 | Repository rules hold the Local gates section | .github/copilot-instructions.md | present | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | 50 |
| R33 | Project constitution exists | .specify/memory/constitution.md | present | 4584997a264c5a7ade2ca7441246e1f067083aa1 | 0 |
| R34 | Spec template exists | .specify/templates/spec-template.md | present | 083ef123c7a2e56e21f3062173fb003258f927e2 | 0 |
| R35 | Plan template exists | .specify/templates/plan-template.md | present | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | 0 |
| R36 | Tasks template exists | .specify/templates/tasks-template.md | present | 7e5170324d41a6736c498d6b9fc83651f31d0778 | 0 |
| R37 | Checklist template exists | .specify/templates/checklist-template.md | present | 806657da09d1058823923e346a323b633114971a | 0 |
| R38 | Quality gates document exists | documentation/quality-gates.md | present | 6776d334cca5d9b43273473a06da367a65605c6d | 0 |
| R39 | Reference record spec exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | present | 83b950279e45704943ad6942d23c8fc99cced492 | 0 |
| R40 | Reserved free-corpus document exists | documentation/free-juniper-corpus.md | absent | none | 0 |
| R41 | Hash inventory file exists at the repository root | corpus_hashes.json | absent | none | 0 |
| R42 | Source corpus folder is in the tree | data/juniper_corpus | absent | none | 0 |
| R43 | Old source package path exists | src/juniper_docs | absent | none | 0 |
| R44 | Recovery branch exists on the remote | fix/2977-recovered-content-dedup | absent | none | 0 |
| R45 | Merged pull request branch exists on the remote | jmorrison-juniper-2977-pdf-dedup-prevention | absent | none | 0 |
| R46 | Recovery tag exists on the remote | recovery/4822/pdf-dedup | absent | none | 0 |
| R47 | Commit cited by the recovery comment exists | 591b6b86697b | absent | none | 0 |
| R48 | Commit cited by the preservation comment exists | 356b65d402793c28c5eea9f6124489ecb230b8a1 | present | 356b65d402793c28c5eea9f6124489ecb230b8a1 | 0 |
| R49 | Initial main commit cited by the claim comment exists | b7ce8eecea305c20b498e12b3f3446ae662663ea | present | b7ce8eecea305c20b498e12b3f3446ae662663ea | 0 |
| R50 | Main commit cited by the preservation comment is in main history | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | 0 |
| R51 | Pull request 4311 merge commit exists | e34553278301ea0715902fa905be3975b3cc8c13 | present | e34553278301ea0715902fa905be3975b3cc8c13 | 0 |
| R52 | Pull request 4823 merge commit exists | b6347ec7374c2a3c1c8ba1f2482aed52cbc81fe6 | present | b6347ec7374c2a3c1c8ba1f2482aed52cbc81fe6 | 0 |
| R53 | Pull request 4311 is merged | pull request 4311 | present | none | 0 |
| R54 | Pull request 4823 is merged | pull request 4823 | present | none | 0 |
| R55 | Pull request 3084 is the merged harvester | pull request 3084 | present | none | 0 |
| R56 | Issue 2738 is the harvester issue, as the comments state | issue or pull request 2738 | stale | none | 0 |
| R57 | Recovery issue 4822 is open | issue 4822 | present | none | 0 |

Row count: 57. The count matches `remote_checks` in `2977-STATUS.json` and the count in `2977-summary.md`.

R56 is stale. Item 2738 is a closed pull request titled `fix(tools): infer edge case applicability`. The harvester shipped in pull request 3084 (R55). The branch `feat/2738-juniper-doc-corpus-harvester` and the folder `specs/2738-juniper-doc-corpus-harvester` carry the number, but GitHub item 2738 is unrelated.

## Local evidence (read-only, not part of the remote table)

- L01: `data\juniper_corpus` does not exist in this worktree. `Test-Path` returned false.
- L02: The recursive name count of `*.pdf` under `data\` is 0. No file content was read.
- L03: `data\` holds 452 top-level entries: 17 directories and 435 files. None is `juniper_corpus`.
- L04: Git tracks two files under `data\`: `data/mib_generator/allowlist.json` and `data/mib_generator/oid_assignments.json`. `.gitignore` line 97 (`DATA/`) matches `data/harvest_state.db.bak-presort`.
- L05: `data\harvest_state.db.bak-presort` (9,416,704 bytes) holds tables `documents`, `pdf_candidates`, `content_scores`, `dropped_release_notes`, and `run_meta`. Table `documents` has no hash column. The database opened read-only with `immutable=1`.
- L06: Table `documents` holds 15,767 rows. 5,352 rows have a `local_path`. 2,892 distinct `local_path` values exist. Stage counts: classified 5,350, discovered 5,488, dropped 225, failed 406, no_pdf 4,298.
- L07: The `harvest_run*.log` files in `data\` have no line that matches `duplicate`, `redundant`, `sha256`, or `dedup`.
- L08: Local branch `main` and `origin/main` both name `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- L09: `git hash-object` returned the same blob SHA as the remote tree for 17 files. The files are AGENTS.md, copilot-instructions.md, constitution.md, four templates, quality-gates.md, architecture.md, development-setup.md, operator-guide.md, container-deployment.md, the legacy spec.md, the reference spec.md, content_index.py, downloader.py, and test_content_dedup.py. Local reads therefore match remote text.
- L10: Two local-only commits on `356b65d402793c28c5eea9f6124489ecb230b8a1` are not in main. They are `356b65d40` (move content index to harvest package, 2026-10-19) and `4ff2d2387` (keep one canonical PDF per SHA256 content, 2026-10-19). Their blob SHAs differ from main: content_index.py `36b21943fd7bbc13d8511352e642d8adf3d1aab0`, downloader.py `a911358c413f2ec8814b02e5f9db07ddd2fff191`.
- L11: `documentation\architecture.md` line 223 lists `juniper_docs/` as a tree entry. No document describes deduplication. `README.md` names no harvester.
- L12: The reference record holds `analysis.md`, `plan.md`, `spec.md`, `tasks.md`, and `design\`. `design\` holds `checklists\` (3 files), `contracts\` (4 files), `data-model.md`, `quickstart.md`, and `research.md`.

## Sources

- Local, read: `AGENTS.md`, and `.github\copilot-instructions.md` (sections Local gates, Spec Kit layout, Safety, Containers, and Git and GitHub).
- Local, read: `.specify\memory\constitution.md` (Principles I to VII and governance), and the four files in `.specify\templates\`.
- Local, read: `documentation\quality-gates.md`, `documentation\architecture.md` line 223, the reference record, and the legacy record `specs\numbered\0\0\0\4\3\4\0\2\2977-harvest-index-moves\spec.md`.
- Local code and tests, read and matched to remote blobs: `src\mist\intelligence\juniper_docs\harvest\content_index.py`, `acquire\downloader.py`, `acquire\pdf_paths.py`, `harvest\consolidator.py`, `harvest\runner.py`, `harvest\state_store.py`, `classify\reprocessing\manual_sorter.py`, `classify\reprocessing\reclassifier.py`, `tests\unit\juniper_docs\test_content_dedup.py`.
- GitHub API, read only: the issue 2977 record, pull requests 160, 3084, 4311, and 4823, and issues 2738 and 4822.
- GitHub API, read only: the recursive tree of main, and the contents endpoint with ref main.
- GitHub API, read only: the blob endpoint for one blob SHA, and the commits endpoint for one commit SHA.
- GitHub API, read only: the compare endpoint for one base commit and main, the branches endpoint, and the matching-refs endpoint for the recovery tag.
- Not used: web_fetch. No external source answers a repository question.
- Not used: the Mist OpenAPI file and the mistapi SDK. No Mist API claim is in scope.
- Not used: the skill tool. No Podman or Juniper device claim is in scope.

## Unverified

- U1: The 351 redundant copies, 2,974 source files, 2,623 distinct documents, 1.32 GB redundant bytes, and 7.73 GB total. Reason: no source corpus exists in this worktree (L01 to L03). No hash inventory exists (L05). The owner withheld corpus access until the source host and path are recorded (issue comment of 2026-10-30).
- U2: The database counts in L06 (5,352 rows and 2,892 distinct paths). Reason: the counts differ from the issue, the database holds no hashes, and the backup time is unknown.
- U3: The 85-minute conversion time for the 100 MB, 33,072-page PDF. Reason: the figure appears only in the issue text. No conversion ran.
- U4: Whether `scripts/crawl_jvd.py` still runs outside the repository. Reason: this record checked the repository only.
- U5: Whether the two local-only commits in L10 hold content that main lacks. Reason: the blob SHAs differ, and no content diff was examined.
- U6: Test results on main `f03c6c9b`. Reason: the PR check results (R53 and R54) cover the pull request heads. No main check run was fetched. No test ran locally.
- U7: The source corpus location. Reason: the corpus path guard names `C:\Users\jmorrison\Downloads\juniper-library-md` as the new corpus root (R26). The owner must confirm that path. This record did not open it.
- U8: Licensing status of the corpus documents. Reason: legal text is outside this record (D-9).
- U9: Whether the process-folder guard accepts the record path. Reason: `tests/guardrails/process_folder_baseline.json` was not read. The record path sits under the fixed route, and the route folder holds two children after this record.
