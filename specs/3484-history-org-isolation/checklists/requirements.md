# Specification Quality Checklist: History Organization Isolation

**Purpose**: Validate specification completeness and quality before planning.

**Created**: 2026-09-30

**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs).
- [x] Focused on user value and business needs.
- [x] Written for non-technical stakeholders.
- [x] All mandatory sections completed.

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain.
- [x] Requirements are testable and unambiguous.
- [x] Success criteria are measurable.
- [x] Success criteria are technology-agnostic (no implementation details).
- [x] All acceptance scenarios are defined.
- [x] Edge cases are identified.
- [x] Scope is clearly bounded.
- [x] Dependencies and assumptions are identified.

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria.
- [x] User scenarios cover primary flows.
- [x] Feature meets measurable outcomes defined in Success Criteria.
- [x] No implementation details leak into specification.

## Notes

Items marked incomplete require specification updates before `/speckit.clarify` or `/speckit.plan`.
This checklist validates the specification only.
It does not report implementation completion or executed acceptance tests.

### Validation record

Validation iteration 1 found one audit coverage gap.
FR-014 stated, "A take after an unreleased take MUST retain the current inferred-expiry behavior".
It did not explicitly cover a prior unreleased takeover.
The existing audit reader treats both actions as opening actions.

The specification now includes that case in US4.4, FR-014, and the verification requirements.
Validation iteration 2 confirmed the correction.
All 16 checklist items pass.
No unresolved specification marker or blocking uncertainty remains.
The initial structural checks passed.
They counted four stories, 22 scenarios, 19 functional requirements, five outcomes, and 16 checklist items.
They found zero unresolved specification markers and no whitespace or sentence-length defects.
The second validation also checked table formatting and complete requirement traceability.
Protected metadata matched its baseline.
Only the two permitted artifacts appeared in the worktree changes.

The specification is ready for `/speckit.plan` with the explicit feature directory.
No planning or implementation phase ran.
No acceptance tests ran during this specification step.

| Criterion | Specification evidence |
| --- | --- |
| No implementation design | Existing request forms name current entry points only. No language, framework, new interface, or code structure is prescribed. |
| User value | User Stories 1 through 4 protect customer history, operator information, correct counts, and accurate audit events. |
| Stakeholder language | The specification defines the selected organization, authorized access, and foreign records before the scenarios. |
| Mandatory sections | User Scenarios & Testing, Requirements, Success Criteria, and Assumptions contain concrete content. |
| No unresolved clarification | The Assumptions section defines each necessary default without a clarification marker. |
| Testable requirements | FR-001 through FR-019 define refusals, exact scope, counts, audit inference, and preserved behavior. |
| Measurable outcomes | SC-001 through SC-005 specify zero foreign results, zero refused reads, exact totals, and complete journey success. |
| Outcome independence | Success criteria describe access, history results, task completion, and event accuracy without a technology choice. |
| Acceptance scenarios | All four request forms have invalid-selection coverage. Organization, site, operation, and audit scenarios define observable results. |
| Edge cases | Edge Cases covers malformed selection, changed privileges, missing attribution, page limits, interleaved actions, and unavailable sources. |
| Bounded scope | FR-018, FR-019, and Assumptions exclude unrelated behavior, data changes, and delivery actions in this step. |
| Dependencies and defaults | Assumptions identifies the current selection services, identity services, history readers, and audit attribution. |
| Requirement acceptance | The traceability table below maps every functional requirement to a scenario or explicit verification condition. |
| Primary journeys | The four stories cover organization history, early refusal, site history, and audit history. |
| Outcome coverage | The scenario and verification matrix can verify each measurable outcome with synthetic data. |
| No hidden design | The specification states scope and safety obligations without prescribing an implementation algorithm or new authentication policy. |

### Acceptance traceability

Scenario references use the story number and acceptance scenario number.
For example, US1.3 means User Story 1, Acceptance Scenario 3.

| Requirements | Acceptance evidence required |
| --- | --- |
| FR-001 | US2.6 retains the current sign-in refusal before any history read. |
| FR-002 | US2.1 proves refusal for absent or invalid selection and no first-organization fallback. |
| FR-003 | US2.2, US2.3, and US2.5 prove refusal for excluded, unknown, empty-privilege, and stale selections. |
| FR-004 | US2.4 preserves environment-token behavior. Assumptions retains the current authorization authorities. |
| FR-005, FR-006 | US1.1 and US3.2 prohibit foreign content even when both organizations are permitted. Complete-response inspection includes hidden values. |
| FR-007 | US1.4 and US3.1 prove scoped totals and page positions. SC-003 requires foreign-data independence. |
| FR-008, FR-009 | US3.1 through US3.4 prove organization-and-site intersection, successful empty foreign-site results, and preserved paging scope. |
| FR-010 | US1.3 proves that populated foreign history cannot fill an empty selected organization. |
| FR-011 | Verification requirements exercise the real capture and run adapters before counting or pagination. An injected approximation is insufficient. |
| FR-012 | US4.1 through US4.3 and US4.6 prove combined audit restrictions for bounded and unbounded results. |
| FR-013, FR-014 | US4.4 through US4.6 prove independent state, correct inferred attribution, release behavior, takeover behavior, and earlier context. |
| FR-015 | US4.1 preserves operator digests. Complete-response checks reject audit addresses, foreign operator content, and credentials. |
| FR-016 | US1.5 and US3.1 preserve operation scope and existing progress-link ownership. US2 applies before operation reads. |
| FR-017 | The unavailable-source edge case requires current availability behavior without an unrestricted retry or foreign-data fallback. |
| FR-018 | US3.1, US3.4, and SC-004 preserve fields, ordering, limits, and successful journeys. Scope limits prohibit unrelated changes. |
| FR-019 | US3.5 preserves lock-independent reads without a new lock check or confirmation. |

### Reviewed source context

- The live issue remains open and assigned to `jmorrison-juniper`.
  Its labels include `bug`, `security`, `web-portal`, `in-progress`, and `upgrade-portal`.
- The [audit comment](https://github.com/jmorrison-juniper/MistHelper/issues/3484#issuecomment-5854527294) explicitly includes the Audit log card.
- The [ownership comment](https://github.com/jmorrison-juniper/MistHelper/issues/3484#issuecomment-5919201863) records the exclusive owner and future file set.
- The active template resolver selected `.specify/templates/spec-template.md` from the core layer.
  The specification preserves its section order.
- The review read `.specify/memory/constitution.md`, version 1.5.0.
  This step introduces no code or operational-store write.
- All repository reads used the dedicated current worktree.
  The review did not inspect another worktree or the main checkout.
  Shell commands used RTK.
  Prose uses Simplified Technical English.

### Existing implementation constraints for later planning

These references record established dependencies and the user's scope limits.
They do not authorize implementation in this step.

- `review.store_capture_rows` and `review.store_run_rows` currently construct site-and-window queries without an organization.
  `CaptureQuery` and `RunQuery` already accept `org_id`.
  The store already applies organization filters before pagination and count queries.
  Acceptance evidence must prove that the real adapter supplies `org_id`.
- `review.call_lister` adapts older injected readers.
  That compatibility must not conceal a missing organization value on the real adapter path.
- `review.audit_history_rows` currently supplies only `site_id` to `compare.lock_audit.read_audit_rows`.
  Audit filtering must include organization and optional site on bounded and unbounded paths.
  Earlier events must still support correct per-site expiry inference.
- `runtime.identity.org_scope_refusal` and `runtime.identity.permitted_org_ids` remain the authorization authorities.
  `None` means unavailable privileges.
  A known empty set permits no organization.
  Preserve the current environment-token distinction.
- `app.routes.select.org_refusal` owns missing-selection and authorization refusal behavior.
  `SELECTED_ORG_KEY` and `resolve_org(None)` identify the signed selection.
  `read_chosen_org` reads the selection request body or form, not the saved history selection.
  Do not duplicate these rules.
- `OrgOperationHistory` already reads with `org_id`.
  It must share the early selection refusal and retain existing progress-link ownership rules.

The future claimed implementation files are:

1. `src/upgrade_portal/app/routes/review.py`
2. `src/upgrade_portal/compare/lock_audit.py`
3. `tests/contract/upgrade_portal/test_issue_3484_history_org_isolation.py`
4. `tests/unit/upgrade_portal/test_issue_3484_audit_org_isolation.py`
5. `changelog.d/issue-3484-history-org-isolation.md`, as the issue's Security fragment.

The coordinator must claim any additional directly coupled fixture before edits.
No shared instruction, bootstrap, dependency, firmware, unrelated interface, or workflow file is authorized for this step.
The user's forbidden edit list remains binding.

### Workflow boundary

- The specification directory is `specs/3484-history-org-isolation`.
  The current app-managed branch is `jmorrison-juniper-history-organization-isolation`.
- Only `spec.md` and `checklists/requirements.md` may change in this step.
  Do not write `.specify/feature.json` or any `.spec-context.json`.
  Use the explicit feature directory again for any later Spec Kit command.
- The explicit app-managed constraints exclude the branch-creation and context-writing hooks.
  The optional Git commit hook remains unexecuted.
- No plan, tasks, implementation, test execution, commit, push, pull request, merge, or deployment occurs in this step.
- Later delivery occupies queue position 7 after #3647, #3365, #3550, #3399, #3496, and #3398.
  External documentation PR #3613 precedes #3365.
- Coordinator session `6d71fd26-57c2-48c0-abc8-607af98f75d0` supplies the stable main SHA after local validation and local commit.
  No push or pull request may precede that message.
- Later delivery requires protected green checks, including CodeQL.
  The pull request must use the full template and include `Closes #3484`.
  Squash merge must obey protection.
  Validate the exact merged tree locally.
  Verify remote branch deletion separately.
  Do not use `--delete-branch` with `gh pr merge`.

### Specification uncertainty

There is no blocking uncertainty.
The specification states these reasonable defaults:

1. Reuse the existing missing-selection and unauthorized-selection refusals.
2. Return an empty scoped result for foreign or unknown sites.
3. Preserve the current policy for unavailable environment-token privileges.
4. Exclude records without matching organization attribution.
5. Keep expiry inference independent for each organization and site.
