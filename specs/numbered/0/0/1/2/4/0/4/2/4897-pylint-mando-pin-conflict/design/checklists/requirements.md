# Specification Quality Checklist: Pylint gate failure from the mando 0.8.2 pin

**Purpose**: Validate the specification and the record before the implementation.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Content Quality

- [x] The user stories need no implementation detail beyond the named files and commands.
- [x] Each user story states the value to a maintainer.
- [x] Each user story names the reader and the result.
- [x] All mandatory sections contain content.

## Requirement Completeness

- [x] No clarification marker remains. The clarifications section records each answer with its evidence.
- [x] Each requirement is testable. FR-001 uses the reproduction commands. FR-002 uses the CI job.
- [x] Each success criterion is measurable with a CI result, a test result, or a count.
- [x] Each user story defines its acceptance scenarios.
- [x] The spec lists edge cases, including radon release, Dependabot syntax, main movement, and a missing radon.
- [x] The Out of Scope section bounds the scope.
- [x] The spec lists dependencies and assumptions. It names the unverified Dependabot syntax as an assumption.

## Feature Readiness

- [x] Each functional requirement maps to a task in `analysis.md`.
- [x] User scenarios cover the failed check, the fix, and the repeated bump.
- [x] The success criteria match the measurable outcomes in the spec.
- [x] No Mist API behavior or mistapi behavior leaks into the specification, because the change makes no Mist call.

## Notes

- The issue title names `pylint`. The clarification corrects the failed step to `Install dependencies`, because the score step did not run.
- Main passed the Pylint job and the dependency lock job on commit f03c6c9. The clarification records that result.
- The constitution requires one fragment for each change, while the README exempts internal-only changes. The constitution controls the conflict. FR-012 records the requirement.
- No source verifies the Dependabot `versions` key. The assumption and the unverified list in `design\research.md` name the check that closes it.
