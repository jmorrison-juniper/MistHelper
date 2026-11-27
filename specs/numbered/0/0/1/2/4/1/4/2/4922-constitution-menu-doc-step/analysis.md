# Analysis: Menu step names the generated pages

## Scope of Review

This review checks `spec.md`, `plan.md`, `tasks.md`, and `design/research.md`. It also checks the 28 remote checks, RC-01 to RC-28, that `design/research.md` records.

## Consistency Checks

| Check | Result |
| --- | --- |
| Each requirement maps to a task | Pass. FR-001 to FR-006 map to T002 to T005. FR-007 and FR-010 map to the guard run in T-LOCAL-GATES. FR-008 maps to T007. FR-009 maps to T006 and T-LOCAL-GATES. |
| Each changed file appears in a task | Pass. The four changed files map to T002, T003, T004, T005, T006, and T007. |
| Each guard case maps to a requirement | Pass. `menu-step` covers FR-001 and FR-002. `readme-bullet` covers FR-003. `rule-file-step` covers FR-004. `footer-version` covers FR-005. `sync-report` covers FR-006. |
| Counts agree | Pass. The spec lists 10 requirements. The tasks list 11 tasks. The guard lists 5 cases. The remote table, `STATUS.json`, and `summary.md` each list 28 checks. |
| Issue premise against remote code | Fail on `main`. The issue says the rule file already states that the README keeps no menu number. RC-07 is absent, and RC-06 shows the stale step. Decision D-2 corrects the rule file. |
| Local files against remote blobs | Pass. Ten local files match their remote blob SHAs. |
| Test placement under the Five-Item Rule | Pass with existing debt. `tests/guardrails` holds 79 children (RC-28). The change adds no child there. |

## Defects in Existing Work

| ID | Defect | Evidence | Handling |
| --- | --- | --- | --- |
| A-1 | Constitution step 5 names the README menu table. | RC-01 | Fixed by T003. |
| A-2 | The constitution README bullet requires a README change for each operation. | RC-02 | Fixed by T004 (D-1). |
| A-3 | Rule file step 1 names the README menu table. The issue premise says the opposite. | RC-06 and RC-07 | Fixed by T006 (D-2). |
| A-4 | Constitution step 6 requires one fragment for each change. Rule 4 of `changelog.d/README.md` exempts an internal-only change. | RC-18 and constitution step 6 | Not changed. D-6 follows the constitution. A follow-up issue should align the two texts. |
| A-5 | The STE CI list omits the constitution. `AGENTS.md` requires each Markdown file to score 80 or above. | RC-22 and the Writing style section of `AGENTS.md` | Not changed. D-9 measures the score. A follow-up issue should decide the CI list. |
| A-6 | Five historical spec records quote the old step. | Code search result U-1 | Not changed. D-8 applies. |
| A-7 | The pull request template holds a generic README checkbox. | RC-21 | Not changed. D-11 applies. |
| A-8 | The operator guide states a stale operation count. | Issue #4915, OPEN | Out of scope. Issue #4915 tracks it. |
| A-9 | The reference plan of issue #4920 says step 5 does not apply. | RC-23 | Consistent with the new step. The historical record keeps its text. |

## Unresolved Items

- The STE score of the constitution. T-LOCAL-GATES measures it (U-2).
- Whether a reviewer accepts the PATCH class (D-5). The reviewer decides in the pull request.
- Follow-up issues for A-4 and A-5. The orchestrator files them. This record creates no issue.
- The `tests/guardrails` debt (RC-28). Complexity Tracking in `plan.md` records it.

## Convergence After Implementation

- Before the change, the five guard cases fail. Quickstart step 2 shows the failures.
- After T003 to T007, the five cases pass.
- The changelog guard accepts the new fragment name and format.
- The record folder adds no direct child under `specs/` beyond the route folders.

## Metrics

- Requirements: 10.
- Tasks: 11.
- Guard cases: 5.
- Remote checks: 28.
- Decisions: 12. Human decisions: 0.
