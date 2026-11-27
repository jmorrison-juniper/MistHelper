# Specification Analysis Report: Webhook config test isolation

## Findings

| ID | Type | Finding | Evidence | Action |
| - | - | - | - | - |
| A-1 | Defect in existing work | Issue #4730 stayed open after the repair merged. PR #4843 uses `Refs #4730` because the issue has no acceptance criteria section. | R-10. PR #4843 body, read through `gh pr view`. | T009 closes the issue after step A passes. |
| A-2 | Defect in existing work | The merged repair adds a precondition line with no inline comment. The touched function has no comments on any code line. Principle VI is non-negotiable. | R-02, R-04, R-25, and `AGENTS.md` line 97. | T010 adds the comments in a follow-up. |
| A-3 | Provenance | Issue #4730 comment 2 reports that commit `5e55cca` ran with `core.hooksPath` set to `/dev/null` and `commit.gpgsign` set to `false`. Commit `5e55cca` is not on `main` (R-06). The merged blob matches the repaired blob (R-01, R-08). | Issue comment 2. Remote checks R-06 and R-08. | Record only. D-5 keeps normal hooks in the follow-up. |
| A-4 | Stale claim | Issue #4730 comments 1 to 4 describe a local, unpublished commit and a main tip of `3964d21d`. Main now holds squash commit `15da34506`. The pull request head is `3ea78a3`. | R-06, R-07, R-08. | Record the claims as stale. |
| A-5 | Governance conflict | `.specify/memory/constitution.md` line 409 says each change adds one fragment. `changelog.d/README.md` rule 4 (line 58) exempts internal-only changes. The changelog guard requires no fragment per change (R-29). The constitution supersedes practice documents (line 529). | R-26, R-27, R-28, R-29. | D-4 decides for this record. The owner decides any constitution amendment. |
| A-6 | Out-of-scope observation | The route reads only the `X-Mist-Signature` header (`web_portal/routes/webhooks.py`). The local OpenAPI file names `X-Mist-Signature-v2` for webhook deliveries (lines 43937, 43998, and 44070). | Local OpenAPI file, read as a grep result. | D-11. Open a separate issue if the owner wants this change. |
| A-7 | Same defect class | The titles of issues #4728, #4731, #4797, and #4492 describe ambient global state in tests. The bodies are not read. | Issue titles from `gh issue list`. | D-6. Open separate issues after the bodies are read. |
| A-8 | Unverified link | Issue #4730 says "Related evidence is recorded in #2711". The body of #2711 does not name #4730. | Issue #2711 body, read through `gh issue view`. | Keep #2711 as related only. |
| A-9 | Stale claim | Issue #4730 comment 4 says that the independent clone requires explicit authorization. | Issue comment 4. | D-5 decides that no clone is created. |
| A-10 | Process gap | Principle IV steps 11 and 12 are not run by this record. | `.specify/memory/constitution.md` lines 143 to 180. | Complexity item CT-1. |
| A-11 | Evidence | Quality Gates run 45774119357 on `f03c6c9` concluded success. Its 33 jobs include the root unit shard, Ruff, Black, mypy, Bandit, and the test quality ratchet. | Run 45774119357, read through `gh run view`. | Evidence for SC-001 and SC-004. |
| A-12 | Evidence | No open pull request changes a path that contains `webhook`. Seven open pull requests were scanned. | Open pull request scan (R-37). | None. |
| A-13 | Excluded link | Pull request #4228 mentions the number 4730 as a test count ("upgrade units 4730 passed"). It is not linked to this issue. | PR #4228 body, read through `gh pr view`. | None. |

## Coverage Summary (requirements to tasks and checks)

| Requirement | Tasks | Checks | Status |
| - | - | - | - |
| FR-001 | T001, T002, T003 | TC-001, TC-002 | verified-present (merged). Local run open. |
| FR-002 | T001 | TC-001 | verified-present (merged). Local run open. |
| FR-003 | T-LOCAL-GATES step A | TC-002 | open |
| FR-004 | T-LOCAL-GATES step A | TC-003 | open |
| FR-005 | T004, T006 | TC-005 | verified-present |
| FR-006 | T002 | TC-007 | verified-present |
| FR-007 | T-LOCAL-GATES step A | TC-004 | open |
| FR-008 | T008, T010 | TC-008 | open |
| FR-009 | T010, T011 | TC-005, TC-006, TC-009, TC-014 | open |
| FR-010 | T-LOCAL-GATES step A | TC-010 | open |
| FR-011 | T007, T009 | TC-011 | partial and open |
| FR-012 | T-PR | TC-012 | open |
| FR-013 | T-PR | TC-013 | open |

Each requirement maps to at least one task and at least one check.

## Unmapped Tasks

None. T-REMOTE-CI maps to SC-004. T-MERGE maps to SC-001 and FR-011.

## Constitution Alignment

The plan records two FAIL rows: Principle IV (CT-1) and Principle VI (CT-2). The follow-up task T010 closes the Principle VI row. Principle IV has no fix in this record.

## Metrics

- Requirements: 13 (FR-001 to FR-013).
- Success criteria: 5 (SC-001 to SC-005).
- Tasks: 15 (T001 to T011 and four final tasks).
- Verification checks: 14 (TC-001 to TC-014).
- Remote checks: 38 (R-01 to R-38).
- Decisions: 11 (D-1 to D-11). Human decisions: 0.
- Analysis findings: 13 (A-1 to A-13).

## Unresolved Items

- U-1: Constitution wording on release-note fragments (A-5). The owner decides any amendment.
- U-2: Principle IV steps 11 and 12 (A-10 and CT-1). The orchestrator decides whether a deploy runs.
- U-3: The `X-Mist-Signature-v2` header (A-6). Out of scope for issue #4730.
- U-4: Sibling isolation issues (A-7). The bodies are not read.
- U-5: The link between issue #4730 and issue #2711 (A-8).

## Convergence

After T010 and T011, the touched function meets Principle VI. After T009, the issue state matches `main`. Principle IV remains open until the orchestrator decides on the deploy (U-2).
