# Analysis: API Fetch Failures

## Consistency Review

| Check | Result | Evidence |
| - | - | - |
| Spec to plan | Pass | Each of FR-001 to FR-016 appears in the change map or the plan text. |
| Plan to tasks | Pass | The ten implementation tasks match the ten change-map paths. Seven are source files, one is the unit test module, one is the integration test module, and one is the release note. |
| Tasks to requirements | Pass | `tasks.md` maps each requirement to a task and to at least one test case. FR-013 has no pytest case. The Symbols gate covers it (SC-005). |
| Tests to requirements | Pass | The 24 planned cases are U-1 to U-11 and I-1 to I-13. |
| Research to record counts | Pass | `design/research.md` has 126 remote rows. `STATUS.json` lists the same 126 rows. `summary.md` states 126. |
| Reserved paths to change map | Pass with one change | The issue comments reserve six source paths and one test path. The change map covers all six source paths. The test path moves to `tests/integration/export/` (D-10). |
| Ownership of the core helper file | Pass | No issue comment reserves `src/mist/access/api/api_core_fetch_utils.py`. No open pull request touches it (A-004). |
| Five-item rule | Pass | The new test module goes to a folder with two children (R126). The helper class has five members. |
| Symbols gate approach | Pass | The nested class adds no module-level name (D-1, R102 to R105). |
| Test quality rule | Pass | The integration module has HTTP 403 and HTTP 503 cases (I-1). The unit module has HTTP 403 and HTTP 503 cases (U-5). Row R113 states the rule. |
| Writing style | Pass | Style review is manual (Step 8). No command checks it. The record uses no semicolon, no contraction, and no Latin abbreviation. |

## Defects in the Unpublished Candidate

The candidate lives only in issue comments. No commit on `main` contains it (row R07). Each finding below comes from the issue comments. The plan repairs each finding by design, not by reusing the candidate.

| Finding | Source | Handling in this plan |
| - | - | - |
| The candidate read `status`. `mistapi` exposes `status_code`. | Comment 2 | Use `status_code` (rows R98 to R100). |
| Tests mocked `get_next` and the status field. They hid HTTP handling. | Comments 2 and 3 | Use real `mistapi.APIResponse` objects and a fake session (U-1 to U-11). |
| A missing status reported as `HTTP None`. | Comment 7 | Report `no HTTP status` as the cause (contract). |
| The error did not subclass `RuntimeError`, so the prompt cache fallback aborted. | Comment 4 | Subclass `RuntimeError` (D-1, row R31). |
| The MSP site lookup logged the failure at debug level. | Comment 5 | Raise the level to warning (D-9, row R28). |
| Optional enrichment raised instead of warning. | Comment 8 | Catch `APIFetchError` in each optional lookup (D-7). |
| The AP model and inventory exporters stopped on a site failure. | Comment 12 | The site read is optional. The inventory read propagates (D-6, D-7). |
| The patch omitted the integration test and the release note. The patch was not a valid Git patch. | Comments 17, 21, and 23 | No patch is reused. Each file is written from this record. |
| The integration test had Ruff line-length errors and a Black reformat. | Comment 18 | Task T-LOCAL-GATES runs the Lint and Format gates. |
| Gateway tests fabricated the enriched row. | Comments 17, 19, and 20 | Test I-6 uses the real enrichment method. |
| Fast-path tests read the runtime cache CSV files. | Comments 19, 20, and 23 | Each integration test uses `tmp_path` and a patched `FilePathUtils.get_csv_path`. |
| `symbol-diff` reported an exit code of 1 because of the added `APIFetchError` name. | Comments 16 and 17 | The class is nested (D-1). The comparator counts imports and classes (rows R103 to R105). |
| The test-quality gate blocker was tracked in issue 4765. | Comment 22 | Issue 4765 is closed on `main`. Its owner comment predates the closure (item U-H). The gate reruns in T-LOCAL-GATES. |
| The reserved test path is a direct child of a noncompliant folder. | Rows R125 and R126 | The path moves to `tests/integration/export/` (D-10). |

## Root Cause on `main`

1. `mistapi.get_all` never reads `status_code`. A 403 or 503 response with a JSON error body has a dictionary payload with no `results` key. The function returns an empty list (rows R95 and R98 to R100). The defect is in the SDK call pattern, and this repository calls it unchanged.
2. The list branch of `get_all` extends the list with `response.data` from a later page. If that later page holds a dictionary, `list += dict` adds the dictionary keys, not rows (row R95).
3. `get_all` stops without an error when `get_next` returns no page (row R96). The result is a partial list.
4. Both fetch helpers return the `get_all` result without a status check (rows R03 and R06).
5. Other direct readers call `mistapi.get_all` with the same pattern, for example rows R29 and R39. They keep the defect. D-5 sends them to a follow-up issue.

## Unresolved Items

- U-A: Direct readers that call `mistapi.get_all` (rows R29 and R39) keep the defect. A separate issue must cover them. This agent cannot file an issue, so the orchestrator or the owner must file it.
- U-B: A required-read failure ends a direct-mode session with exit code 1 (D-13). The owner should review the policy after the merge. Container mode is unchanged.
- U-C: The offline report uses `Unknown Site` (row R15). The gateway export uses `Unknown` (rows R25 and R26). Both fallbacks exist before this change. This plan keeps both. A later issue can unify them.
- U-D: Session 79a9bb52 owns `tests/unit/export/test_site_device_exporter.py`. T-LOCAL-GATES runs that module. A failure there means the owner must review the result. No edit is planned.
- U-E: The two exporter files carry a file-only handoff from the owners of issue 1794. Issue 1794 must rebase after this change merges.
- U-F: Issue 4762 was closed by pull request 4853 and reopened on 2026-11-22. Row R107 confirms the body text of pull request 4853. Its state is OPEN now (issue state read on 2026-11-26).
- U-G: The hook provenance, the candidate hashes, and the owner's gate results from the issue comments cannot be reproduced here. The record lists them in `design/research.md` under Unverified.
- U-H: The owner placed publication and hook holds in the issue comments. The orchestrator decides when T-MERGE runs.

## Verdict

The record is internally consistent. No blocking defect remains in the record. The implementation tasks start after the orchestrator accepts this record.
