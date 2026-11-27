# Specification Quality Checklist: Windows guardrail test failures

**Purpose**: Validate the specification before the task list is used

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Content Quality

- [x] Names only the files, tests, and workflows that issue #4917 names. The file names are requirements, not design choices.
- [x] Focuses on the results for a Windows maintainer and for the Ubuntu CI maintainer.
- [x] Uses plain words for a reader who did not write the tests.
- [x] Completes each mandatory section. Key Entities states that the change adds no entity.

## Requirement Completeness

- [x] Contains no placeholder text and no empty section.
- [x] Makes each requirement testable. `analysis.md` maps each FR to a task and a proving check.
- [x] Gives measurable success criteria. SC-001 gives predicted counts, and SC-002 gives a collection count.
- [x] Names each skip reason in SC-006, so a reviewer can compare the printed text.
- [x] Defines the acceptance scenarios for each user story.
- [x] Lists seven edge cases, including the privilege, PATH, and path-form cases.
- [x] Bounds the scope in Out of Scope, with the follow-up issues named.
- [x] Lists assumptions with the evidence that supports each one.

## Feature Readiness

- [x] Each FR has at least one task and one proving check (`analysis.md`, Coverage Summary).
- [x] The user stories cover the Windows run, the Ubuntu run, and the setup note.
- [x] The measurable outcomes match the success criteria.
- [x] Implementation detail stays at the level of file paths and line numbers from the remote checks.

## Notes

- Iteration 1: The predicted counts used the issue baseline and missed the new test. The corrected prediction is 1186 passed and 30 skipped, or 1187 passed and 29 skipped (SC-001).
- Iteration 2: The skip reasons name Ubuntu CI. SC-006 checks each reason in the Windows output.
- Iteration 3: Clarifications record six decisions with their references in `design/research.md`.
- The predicted counts need a Windows run before the pull request. The record marks them as predictions (U-8).
