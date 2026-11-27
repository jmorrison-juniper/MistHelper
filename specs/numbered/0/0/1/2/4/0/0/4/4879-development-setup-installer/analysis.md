# Specification Analysis Report: Development setup installer text

**Date**: 2026-11-26

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/research.md`, `design/contracts/bootstrap-installer-flow.md`, `design/quickstart.md`, and the constitution (version 1.9.0).

**Method**: A read-only pass compared the issue body, the guide on `main`, the script on `main`, and the governing documents. Each finding cites a line of `main` at commit `f03c6c9b`, or a remote row of `design/research.md`.

## Findings

| ID | Category | Severity | Location | Summary | Resolution |
|----|----------|----------|----------|---------|------------|
| A-01 | Inconsistency | HIGH | Guide lines 28 and 29 | Step 2 says the bootstrap installs the two requirement files. The script never installs them. It runs the locked sync at line 466 (R-03, R-15). | Fixed by T002. |
| A-02 | Stale issue text | MEDIUM | Issue #4879 body | The body quotes two statements that `main` no longer holds (R-04, R-05). PR #4880 changed the uv paragraphs of the guide (10 additions and 10 deletions). The defects that remain are A-01, A-03, A-05, and A-07. | The spec uses `main` as the source of truth (Clarifications). |
| A-03 | Inconsistency | MEDIUM | Guide lines 83 to 86 | The report paragraph describes a report per file, a total time, and an invocation with no requirement files (R-06 to R-08). The script logs elapsed time per command (line 533) and prints one report (lines 692 to 699). | Fixed by T004. |
| A-04 | Inaccuracy | MEDIUM | Guide line 103 | "Extra-source order remains unchanged." The parser keeps one value for each source key (R-32), so the claim has no support. | Fixed by T009 (D-4). The limit is recorded as U-6 and in follow-up F-2. |
| A-05 | Gap | MEDIUM | Guide lines 68 to 75 | The table names four settings. The script also sets UV_HTTP_RETRIES, UV_HTTP_TIMEOUT, PIP_RETRIES, PIP_TIMEOUT, UV_INDEX_URL, UV_EXTRA_INDEX_URL, PIP_INDEX_URL, and PIP_CONFIG_FILE (R-10, R-20 to R-22, R-33). | Fixed by T007 (D-3). |
| A-06 | Gap | LOW | Issue #4879 body | The body says the script runs only the locked sync. The script also runs `pip config list` (line 179). It installs uv with pip when uv is missing (line 457). It runs `uv lock --check` after a failed sync (line 497). It runs the health check (line 623), the browser download (line 593), the Git credential setting (line 820), and the account check (line 848). | The contract lists each command (section 2). The guide names the install-relevant commands. |
| A-07 | Terminology | LOW | Guide lines 59, 77, 79, 91, and 104 | "uv installation" names two concepts: the uv program and the uv-based install. "Each file receives" names child processes, not files. | Fixed by T002, T006, T008, and T009. The terms appear in `spec.md`. |
| A-08 | Gap | MEDIUM | `.github/workflows/ste-lint.yml` line 44 | CI grades five named files and not the guide (R-35). The issue acceptance needs a local score only. | D-7. Follow-up F-4. |
| A-09 | Gap | LOW | Repository | No CI check compares the guide with the script. No local gate table entry does either. | D-6. Follow-up F-5. |
| A-10 | Scope note | LOW | `scripts/bootstrap_worktree.py` lines 706 to 800, and line 895 | The source sweep runs before setup. It removes cache-only orphan directories under `src`. The guide does not describe it. | D-5. Follow-up F-1. This agent did not file it, under rule 4 of the brief. |
| A-11 | Deprecated names | LOW | `scripts/bootstrap_worktree.py` lines 352, 354, and 446 | The script sets UV_INDEX_URL and UV_EXTRA_INDEX_URL, which the uv reference marks as deprecated. It also sets UV_NATIVE_TLS, which the reference marks as deprecated in favor of UV_SYSTEM_CERTS. | Out of scope. The guide names the names that the script sets. Follow-up F-3. |
| A-12 | Conflict | MEDIUM | Constitution line 409 and `changelog.d/README.md` line 58 | The constitution requires one fragment for each change. The changelog README exempts an internal-only change. The constitution takes precedence (line 529, R-45). | D-8. The plan adds one fragment. |
| A-13 | Pipeline | LOW | Constitution lines 166 to 170, and `.github/workflows/container-build.yml` lines 5 to 19 | Steps 10 to 12 expect an image build. The build triggers on product paths only, and this change touches none of them (R-42). | Recorded in the Constitution Check of `plan.md`. No action. |
| A-14 | Brief gap | LOW | Brief section 3, step 8 (b) | The brief asks for one verification command from the local gates table for each task. No gate in the table compares the guide with the script, and none checks the changed-file scope. T013 and T016 use `git grep` and `git diff`. | Recorded. Each task names its check. |
| A-15 | Unverified claim | LOW | Guide lines 17 and 144 | "requirements.txt and pyproject.toml hold the full dependency list" and "reviewed, immutable commit" are not fully verified (U-2, U-3). The immutable pin is verified (R-40). | Both sentences stay unchanged. The record lists them as unverified. |
| A-16 | Editorial | LOW | Guide line 125 | "The browser repair guidance below remains unchanged." describes the document, not the bootstrap. | Deleted by T011 (plan M-14). |
| A-17 | Legacy record | LOW | `specs\numbered\0\0\1\2\4\0\0\4` | No record for issue 4879 exists on `main` or locally (R-46, R-53). This record is new. | No legacy record is reused. Steps 3 and 4 of the brief found none. |
| A-18 | Overlap | LOW | Open pull requests | None of the seven open pull requests touches the guide, the script, or the guard test. | The branch claim is safe. Recheck the list before T-PR. |
| A-19 | Guard coupling | LOW | `tests/guardrails/test_container_policy_docs.py` lines 59 to 67 | The guard reads the guide's code blocks. It fails on a destructive volume command or a production volume removal. | The edits add no code block with such a command. TST-010 proves it. |
| A-20 | Drift between guides | LOW | Guide line 32 and `.github/copilot-instructions.md` line 29 | The guide runs `python scripts/bootstrap_worktree.py`. The agent guide runs `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py`. Both run the same script. | Out of scope. Follow-up F-6. |

## Coverage Summary

| Requirement | Tasks | Checks | Status of the work |
|-------------|-------|--------|--------------------|
| FR-001 | T002, T003, T013 | TST-003 | Absent on `main` (R-11). |
| FR-002 | T002, T004, T006, T008, T009, T011, T013 | TST-002 | Stale text present on `main` (R-03, R-06 to R-09). |
| FR-003 | T003, T010, T013 | TST-004 | Discovery text present (R-18). Lock messages absent from the guide. |
| FR-004 | T010, T013 | TST-008 | Present on `main` (R-23). Kept. |
| FR-005 | T007, T008, T009, T011, T013 | TST-005 | Four of twelve names present (R-10). |
| FR-006 | T004, T013 | TST-006 | Absent from the guide. The script line is present (R-16). |
| FR-007 | T005, T013 | TST-007 | Absent from the guide. The script line is present (R-17). |
| FR-008 | T014, T-LOCAL-GATES | TST-001 | Unknown on `main` (U-1). |
| FR-009 | T012, T015, T016, T-PR | TST-009, TST-010 | The fragment is absent on `main` (R-53). |

Success criteria map to the same checks. SC-001 maps to TST-003. SC-002 maps to TST-002. SC-003 maps to TST-005. SC-004 maps to TST-001 and T-LOCAL-GATES. SC-005 maps to TST-009.

## Open Items and Follow-Up Issues

Each follow-up needs its own issue. This agent did not file any issue, under rule 4 of the brief.

- F-1: Document the source sweep in a separate issue (A-10, D-5).
- F-2: Preserve multi-value pip extra index lists in the parser (A-04, U-6).
- F-3: Replace the deprecated uv names in the script (A-11, U-7).
- F-4: Add the guide to the STE CI file list after the local score is known (A-08, D-7).
- F-5: Add a guard that compares the guide with the script (A-09, D-6).
- F-6: Align the bootstrap command in the guide and the agent guide (A-20).
- U-1: The STE score of the guide and the fragment is unknown until T014 runs.
- The record folder reaches the repository only through the orchestrator. This agent wrote the draft folder and the meta files only.
