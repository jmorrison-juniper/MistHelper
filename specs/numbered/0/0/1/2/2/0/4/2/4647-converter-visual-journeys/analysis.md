# Specification Analysis Report: Add independently authored converter visual journeys

## Scope and inputs

- Issue #4647, its body and two comments, and the parent #4224 task map.
- The merged full-parity record on `main` (PR #4596), which names T029 and T030.
- The sibling draft #4636, read for consistent decisions.
- The remote verification table in `design/research.md` (101 rows, of which 95 check `main`, 1 checks an open pull request, and 5 check installed packages).

## Consistency review

| Check | Result | Note |
| - | - | - |
| Spec to plan | Consistent | Each file in the plan change map appears in a spec requirement. FR-017 and FR-018 match plan D-1. |
| Plan to tasks | Consistent | Each changed file has a task. The changelog fragment has T-PR. |
| Contracts to tasks | Consistent | T003 uses the IDs in `portal-journey.md`. T005 uses the status strings. T014 uses the production route check in `test-host.md`. |
| Research to STATUS | Consistent | Row count and order match (101 rows). The self-review rechecked the count. |
| Summary to STATUS | Consistent | The summary repeats the counts from STATUS. |
| Decisions to #4636 | Consistent | #4636 D-2 places state tests in the converter integration folder. This record places browser journeys in the E2E smoke module. The placements do not overlap. |
| Decisions to #4636 D-13 and D-15 | Consistent | D-3 and D-6 keep route registration and shared files out of this change, as #4636 D-13 requires. D-13 defers the secret policy to #4636 D-15. |
| Decisions to #4224 | Consistent | Presentation keeps the current `data-testid` values (RC-70) and avoids shared portal changes (RC-69). |
| Terms | Consistent | One term per concept: proposal, review, typed confirmation, export, cancel, reset, status, shipped theme, portal host, test host. |
| Human decisions | None | The four section 6 categories do not apply. D-1 to D-17 each record a reason. |

## Requirement coverage

| FR | Tasks | Tests |
| - | - | - |
| FR-001 | T002, T006 | `test_structured_review_and_typed_export` |
| FR-002 | T003, T005, T006 | `test_structured_review_and_typed_export` |
| FR-003 | T005, T007 | `test_typed_word_gates_export_and_cancel_clears_it` |
| FR-004 | T003, T005, T007 | `test_typed_word_gates_export_and_cancel_clears_it`, `test_reset_and_input_change_clear_state` |
| FR-005 | T005, T008 | `test_stale_preview_response_is_ignored` |
| FR-006 | T005, T009 | `test_server_failures_show_text_status` (2 cases) |
| FR-007 | T003, T004, T011 | `test_keyboard_only_journey_shows_focus` |
| FR-008 | T012 | `test_shipped_theme_at_viewport` (4 themes) |
| FR-009 | T004, T012 | `test_shipped_theme_at_viewport` (phone and desktop) |
| FR-010 | T005, T010 | `test_markup_renders_as_text` |
| FR-011 | T013 | `test_cloud_guard_blocks_external_request` |
| FR-012 | T006 | `test_structured_review_and_typed_export` (synthetic input) |
| FR-013 | T009, T015, T-REMOTE-CI | `test_server_failures_show_text_status` (failure path) and the CI options (RC-52) |
| FR-014 | T003, T006 | Each journey uses the IDs in the contract |
| FR-015 | T004, T014 | `test_presentation_uses_host_theme_tokens` |
| FR-016 | T004, T014 | `test_presentation_adds_no_image_font_or_animation` |
| FR-017 | T001, T-MERGE | `tests/guardrails/test_e2e_package_structure.py` (existing) |
| FR-018 | T002, T006 | `test_structured_review_and_typed_export` replaces the isolated class |
| FR-019 | T016 | Existing smoke classes in the same module |
| FR-020 | T014 | `test_production_host_serves_no_converter_route` |

The 20 planned cases are grouped as follows. Eight are theme and viewport cases. Two are server failure cases. The other ten each cover one journey, state, guard, or static check.

## Defects in existing work

| ID | Severity | Evidence | Effect | Handling |
| - | - | - | - | - |
| DF-1 | High | The isolated test asserts zero browser storage (RC-27). The host writes `misthelper-theme` on each load (RC-33). | The isolated assertion fails in the host. | D-4. T006 and T007 apply the corrected rule. |
| DF-2 | High | The planned T029 file `test_cisco_parity.py` is absent (RC-49). `tests/e2e/web_portal/` holds 32 children (RC-48). The constitution forbids a new child under a noncompliant parent (RC-79). | A new file would add debt. | D-1. Remediation action R-1 is separate. |
| DF-3 | Medium | The current page lacks typed confirmation, cancel, reset, and focus control (RC-11). The current script shows JSON only, not a structured review (RC-12). | The journeys in T029 cannot pass on the current presentation. | T003 and T005 add the controls. |
| DF-4 | Medium | Parent task T013 marks the presentation delivered (RC-68). | The parent status overstates the delivered scope. | Recorded only. This record does not edit the parent. |
| DF-5 | Medium | The content security policy allows inline script and inline style (RC-42). | A missing text rule would not be blocked by CSP. | D-5 and T010 use DOM text APIs. The security checklist records the residual risk. |
| DF-6 | Medium | The isolated integration client mounts a bare Flask app (RC-28). The production host registers no converter (RC-30). | The current smoke test proves no host integration. | D-3 and T002 build the test host. T014 proves the production route is absent. |
| DF-7 | Low | Only the magenta theme defines the focus ring token (RC-35). Three themes define none (RC-36 to RC-38). | The focus outline may be invisible in three themes. | The stylesheet falls back to `currentColor`. T011 checks each theme. |
| DF-8 | Medium | The session secret falls back to a random value (RC-41). A restart clears review state, so the server returns 409 (RC-17). | Reviews fail after a restart. | Outside this change. #4636 D-5 and D-15 own the policy. |
| DF-9 | Low | The live task map cites PR #4596 as open (issue comment, 2026-11-09). PR #4596 is merged (2026-11-13). | Citation drift. | This record cites the merged paths on `main` (RC-62 to RC-67). |
| DF-10 | Medium | PR #4208 is open and touches `base.html` and `app.py` (RC-72). | Merge conflict risk. | This change touches neither file. The plan says to rebase after #4208 merges. |
| DF-11 | Low | The provenance of the current presentation files is not checked (U-6). | Unknown origin of current markup. | The provenance checklist requires review. D-14 forbids reuse. |

## Unresolved items

| ID | Owner | Question | Blocks |
| - | - | - | - |
| U-1 | Implementer | Playwright route behavior with a held response needs an executed run. | T008 |
| U-2 | Owner | Whether Principles VI and VII cover browser script (RC-82, RC-83). | Logging scope in review |
| U-3 | Implementer | Duration of the browser shard after this change. | T-REMOTE-CI |
| U-4 | Issue #4641 owner | Whether the proposal JSON shape changes. | T005 and T006 |
| U-5 | Issue #4636 owner | Whether state refusal without `PORTAL_SECRET_KEY` changes the test host. | T002 |
| U-6 | Reviewer | Origin of the current presentation files. | Provenance review |
| U-7 | Implementer | Whether other documents name the converter page. Five documents were searched. | Documentation gate |
| U-8 | Implementer | Exact Flask setup-guard text. Only the first-request flag was checked (RC-73). | Harness comments |
| U-9 | Implementer | Chromium on a Windows developer host. | Local run |

## Metrics

- Functional requirements: 20.
- Tasks: 20 (16 implementation, 4 delivery).
- Planned test cases: 20.
- Decisions: 17. Human decisions: 0.
- Remote checks: 101.
- Open prerequisites: 3 (#4636, #4641, #4642).

## Not run

This drafting pass ran no tests, linters, builds, formatters, package installs, or containers. Each remote check was read from GitHub or from a read-only local command.
