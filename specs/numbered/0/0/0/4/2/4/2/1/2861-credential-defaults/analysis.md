# Analysis: Credential default audit

## Consistency Review

The spec, plan, tasks, research, and remote code were compared. Each item states the finding and the action.

| ID | Finding | Severity | Action |
| - | - | - | - |
| A-01 | Legacy `2861-required-token-resolution/tasks.md` leaves T019 unchecked after PR #4507 merged. | Low | Owner or orchestrator marks the legacy record closed. This record does not edit legacy records. |
| A-02 | Legacy `2861-required-token-resolution/plan.md` names Python 3.13. `pyproject.toml:23` requires 3.15. | Low | None in this record. The legacy file stays as history. |
| A-03 | Legacy spec FR-003 keeps the configured token as the final source. The owner analysis of 2026-10-06 lists that path as a wrong identity. | High | Decision D-6. |
| A-04 | Legacy spec status and plan name PR #4497 as the next merge position. Both are stale. | Low | None in this record. |
| A-05 | Both legacy quickstarts give POSIX commands only. The Windows target needs `.venv\Scripts\python.exe`. | Low | `design/quickstart.md` gives Windows commands. |
| A-06 | Owner line numbers are stale. Nine present lines moved (C-02, C-06, C-13, C-14, C-15, C-16, C-22, C-29, C-46). One partial line moved (C-36). | Medium | The research table replaces the owner line numbers. |
| A-07 | Candidate counts conflict: 31 in the issue body, 40 in the superseded first owner comment, and 64 in the second owner comment. The 31 count is unverified (U-5). | Medium | The baseline uses 64. |
| A-08 | The comment-proposed guard path adds a direct child to `tests/guardrails/`, which breaks constitution I. | Medium | Nested guard package (D-8). |
| A-09 | Mistapi pin text conflicts. The brief says `>=0.64.0,<0.65`. `pyproject.toml:29` says `>=0.64.1,<0.65`. `requirements.txt:129` pins `0.64.1`. `.github/copilot-instructions.md` line 21 says `>=0.64.0,<0.65`. The constitution technology section says 0.59 or later. | Low | Documentation correction in a separate docs change. This record uses the pins in `pyproject.toml` and `requirements.txt`. |
| A-10 | The brief asks each pull request body to use `Closes #2861`. Owner decision 5 keeps the issue open until every candidate is repaired. | Medium | D-15. Batch pull requests use `Refs #2861`. The final pull request uses `Closes #2861`. |
| A-11 | PR #3036 changed `src/db/__init__.py`, and PR #3096 changed `src/maps/_flask_viewer.py`. Main holds neither path (R-08, R-09). | Low | This record uses current paths only. |
| A-12 | PR #4507 merged with no submitted GitHub review (owner comment of 2026-11-09). | High | Owner confirms the review status. This record does not claim that a review occurred (U-4). |
| A-13 | The owner reported a missing connection-error case in `test_session_boundary.py` on 2026-11-10. | Low | D-13. No change in this record. |
| A-14 | Open PR #4208 changes `web_portal/app.py` (C-62). | Low | D-14. No batch changes that file. |
| A-15 | `maps_manager.py` line 2689 passes `token=`. The SDK constructor accepts `apitoken` only (R-58). The `except` clause exits with status 1. | Medium | D-12. Separate issue. |
| A-16 | Container literal credential defaults in `compose.yml` lines 223, 244, and 250 sit outside the Python scanner. | High | D-7. |
| A-17 | The SDK reads `MIST_APITOKEN` when `apitoken` is absent (R-59). Four product or script call sites depend on that channel. | Medium | D-11. Allowlist test (TST-16). |
| A-18 | The integration helper reads the legacy name first. The application reads the canonical name first (C-48, C-49, R-53). | Medium | D-4 and T011. |
| A-19 | Owner decision 3 is ambiguous. It keeps local defaults and rejects known credential values that match sample entries. This record reads local defaults as host and port defaults. The standalone tests expect empty credentials (R-14, R-15). | Medium | Owner confirms the reading. The implementer follows this record until then. |
| A-20 | The scanner did not run (rule 2). The count beyond the 64 lines is unverified (U-1). | Medium | T002 prints the count on the first run. The implementer reconciles that count with research.md. |
| A-21 | `ste-linter` did not run (rule 2). | Low | Manual style check. T-LOCAL-GATES runs `ste-linter` on changed Markdown. |
| A-22 | The `except` clause count of each changed file is not measured (U-13). | Low | T019 measures the counts before batch 1 edits. |

## Coverage Checks

- **FR coverage**: Each FR maps to at least one task. Each FR maps to at least one test. FR-009, FR-010, FR-012, and FR-016 use existing tests. FR-013 and FR-018 use blocked tests (TST-18 and TST-19).
- **Task paths**: Each task names repository paths or a verification command.
- **Layout**: The feature root holds five children (spec, plan, tasks, analysis, design). The design folder holds five children (research, data model, quickstart, contracts, checklists). Each contract and checklist folder holds at most five children.
- **Count agreement**: STATUS remote checks equal the research table rows (139). The summary repeats the candidate counts.

## Unresolved Items

| ID | Item | Owner or actor |
| - | - | - |
| HD-1 | D-5 legacy token variable window | Owner |
| HD-2 | D-6 configured-token fallback in `MistSessionFactory` | Owner |
| HD-3 | D-7 container literal credential defaults | Owner |
| UR-1 | Review status of PR #4507 (A-12) | Owner |
| UR-2 | Coordination for the analyzer candidate (A-13) | Owner and issue #4748 |
| UR-3 | Reading of owner decision 3 (A-19) | Owner |
| UR-4 | Scanner count beyond the 64 lines (A-20) | Implementer, batch 0 |
