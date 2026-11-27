# Specification Analysis: Batch target site snapshot

This review checks `spec.md`, `plan.md`, `tasks.md`, and the remote code on `main`. It lists each defect in existing work and each open item.

## Findings

| ID | Severity | Finding | Evidence | Action |
| - | - | - | - | - |
| A-1 | MEDIUM | The mistapi pin in the repository guide differs from the pin in the code. The guide says `>=0.64.0,<0.65`. | `.github/copilot-instructions.md`, line 21 (row 32). `pyproject.toml`, line 29, says `>=0.64.1,<0.65` (row 30). `requirements.txt`, line 129, pins `==0.64.1` (row 31). | Open a separate documentation issue. D-14 records the decision. This change edits no pin text. |
| A-2 | MEDIUM | The constitution technology section states `mistapi: 0.59+`. The value is older than the pin in code. | `.specify/memory/constitution.md`, section "Technology & Compatibility Constraints" (row 49). | Include this value in the separate documentation issue of A-1. |
| A-3 | LOW | The integration test docstring describes the later site checks as expected reads. The change makes that statement wrong. | `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py`, line 558 (row 41). | Task T003 updates the docstring and the assertion. |
| A-4 | MEDIUM | `related.py` has six top-level names: `logger` and five classes. This is one name more than the five-item rule allows. | `related.py`, line 20 (`logger`), lines 23, 49, 107, 178, and 233 (classes). The blob matches `main` (row 1). | Grandfathered debt. The change adds no name. Open a separate remediation issue. |
| A-5 | MEDIUM | A site snapshot can keep a removed site for up to 300 seconds. | D-2 in `design/research.md`. The spec Caution appears in the edge cases. | Accepted risk. Each discovery replaces the snapshot. A failed read clears it. |
| A-6 | LOW | The Mist documentation states the 5000-call threshold for an API token. The issue states it for a credential. | `documentation/api/admins/POST_register.md`, line 213 (row 27). | No action. The substance matches. The threshold applies to the token. |
| A-7 | LOW | PR #4924 states 177 requests for 15 switches. No measurement in this record confirms that figure. | PR #4924 body, linked in `design/research.md`. | Unverified item U-2. |
| A-8 | INFO | Issue #4921 is open. It covers the shared request admission rule. | `gh issue view 4921`, state OPEN. | Not a dependency. The change does not alter admission. |
| A-9 | INFO | PR #4924 is merged. It cites issue #4923 as the source of the read count and does not close it. | PR #4924 body, merged at 2026-11-26T00:30:01Z. | Consistent with this record. Issue #4923 remains open. |

## Coverage Summary

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T002, T003, T004, T006, T007 | Seven unit tests, the integration test, and the routing test. |
| FR-002 | T006 | `test_discovery_refreshes_the_snapshot_for_later_checks` |
| FR-003 | T005, T007 | `test_site_checks_share_one_organization_read`, `test_empty_organization_snapshot_is_reused` |
| FR-004 | T005 | `test_snapshot_older_than_the_lifetime_is_read_again` |
| FR-005 | T005 | `test_concurrent_site_checks_share_one_read` |
| FR-006 | T005 | `test_failed_refresh_clears_the_snapshot_and_raises` |
| FR-007 | T007 | Existing test `test_batch_target_picker_filters_families_and_rejects_foreign_sites` |
| FR-008 | T006 | Existing foreign-site test, which asserts `rows` and `excluded` |
| FR-009 | T008 | `tests/guardrails/test_changelog_fragment_policy.py` |
| FR-010 | T005 | `test_refresh_logs_start_and_finish_without_identifiers`. Inline comments are reviewed in T-PR. |
| FR-011 | T005, T006, T007 | `tests/guardrails/test_move_module_guidance.py` and `test_ws_feature_structure.py` in T-LOCAL-GATES |
| FR-012 | T006 | The existing site picker test at `test_ws_web_services.py`, line 326 |

## Constitution Alignment

- Principle I: The change adds one module to a compliant folder. It adds no top-level name to `related.py`. The existing debt is recorded (A-4).
- Principle II: The change adds a class and no wrapper function.
- Principle III: The membership check fails closed. The change adds no input path.
- Principle IV: The four final tasks cover the pipeline. Deployment needs orchestrator approval.
- Principles V to VII: The logs use ASCII event names. Each new read logs before and after. Each new line gets an inline comment during review.

## Unmapped Tasks

None. Each task maps to at least one requirement. The final tasks cover every requirement. T-REMOTE-CI and T-MERGE check remote state. The local gates table has no command for them. Their commands come from AGENTS.md (`gh pr checks`, `gh run list`).

## Metrics

- Requirements: 12 (FR-001 to FR-012).
- Tasks: 13 (nine implementation and verification tasks, and four final tasks).
- Planned tests: 9 (seven new and two updated).
- Decisions: 14. None requires a human decision.
- Remote checks: 59. Fifty-six are present. Three are absent as expected for new paths.
- Existing record: none. No folder under `specs\` starts with `4923-`.

## Unresolved Items

- U-1: Live Mist behavior is not checked. The change needs one live read-only run after merge. The orchestrator decides that run.
- U-2: The request count in PR #4924 is not measured here.
- U-3: The container start script is not read. The worker count checked is `wsgi.py`, line 4.

## Convergence After Implementation

Pending. After T-LOCAL-GATES, confirm these points.

1. Each new test fails before the code tasks, and passes after them.
2. The integration read list equals `[ORG_A, ORG_B, ORG_C]`.
3. The routing test counts one read for organization B.
4. Each FR maps to a diff hunk that a reviewer can name.
