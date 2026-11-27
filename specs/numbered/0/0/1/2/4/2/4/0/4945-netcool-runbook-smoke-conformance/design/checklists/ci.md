# CI and Gate Requirements Quality Checklist: Netcool Runbook Smoke Package Conformance

**Purpose**: Check that the CI requirements and their gates are complete and testable.
**Created**: 2026-11-26
**Feature**: `spec.md` FR-011 to FR-019, `design/contracts/ci-steps.md`, and `design/research.md` decisions D-12 to D-15

## Gate Coverage

- [x] CHK201 Each of the seven gates names the package path. Evidence: `design/contracts/ci-steps.md`, section Gate jobs, and FR-014.
- [x] CHK202 The current gap is recorded with a row. Evidence: rows R18 to R22 show the five variables name no package path. Rows R27 to R29 show the three exclusions.
- [x] CHK203 The exclusions stay unchanged. Evidence: decision D-12 keeps `pyproject.toml` unchanged, and FR-014 requires only the path in CI.

## Count and Failure Rules

- [x] CHK204 Each gate prints its examined count. Evidence: FR-015 and the count step rule in `design/contracts/ci-steps.md`.
- [x] CHK205 A zero count fails the step. Evidence: FR-015 and the count step rule.
- [x] CHK206 The gate guard fails when a gate drops the package path or its count step. Evidence: FR-016 and TEST-06, TEST-07.

## Injected Violations and Job Count

- [x] CHK207 At least two steps fail on an injected violation. Evidence: FR-017, TEST-08, and TEST-09.
- [x] CHK208 The job count stays unchanged. Evidence: FR-018 and task T032.

## Coverage and Type Strictness

- [x] CHK209 The mypy rule forbids a relaxing override. Evidence: FR-019 and decision D-13.
- [x] CHK210 The package coverage has a measurable target and a measurement command. Evidence: FR-020, decision D-14, and quickstart Scenario 5.
- [x] CHK211 The explicit-path behavior of Ruff and Bandit has a check. Evidence: the count step rule and risk A-10 and A-11 in `analysis.md`.
