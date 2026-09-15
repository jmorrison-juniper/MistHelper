# Implementation Plan: Pytest Coverage Gate Headroom

**Branch**: `chore/2650-coverage-gate` | **Date**: 2026-09-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/2650-coverage-gate/spec.md`

## Summary

Issue #2650 shows that the serial root coverage gate leaves too little time margin. Recent runs took 7.9 to 11.9 minutes against a 15 minute limit. The chosen design splits the root pytest suite into four matrix shards, uploads one coverage file from each shard, and keeps a final job named `pytest (coverage gate)` to combine coverage and enforce the unchanged threshold.

## Technical Context

**Language/Version**: Python 3.13 and GitHub Actions YAML.

**Primary Dependencies**: pytest, pytest-cov, coverage, PyYAML, and existing GitHub artifact actions.

**Storage**: GitHub Actions artifacts hold temporary `.coverage.<shard>` files for one workflow run.

**Testing**: pytest contract tests that parse `.github/workflows/ci.yml`.

**Target Platform**: GitHub-hosted Ubuntu runners for CI and Windows for local validation.

**Project Type**: Single Python CLI repository with workflow guardrails.

**Performance Goals**: Keep each root coverage shard below the existing 15 minute shard limit and keep the final combine job below 8 minutes.

**Constraints**: Do not change the coverage threshold. Do not add `paths-ignore`. Do not change `MistHelper.py`. Preserve the required check name.

**Scale/Scope**: The CI-equivalent local collection found 16,554 non-E2E tests. The workflow split uses four path-based shards.

## Constitution Check

| Principle | Gate evaluation |
| - | - |
| Five-Item Rule | PASS. One workflow split and one small contract test file answer this issue. |
| Class-Based Architecture | PASS. New Python test behavior lives in the `CoverageGateWorkflow` class. |
| Safety-First | PASS. The change does not touch destructive operations or live Mist API calls. |
| Full Deployment Pipeline | PASS. The plan includes local gates, a release-note fragment, a pull request, and CI observation. |
| Observability and Logging | PASS. The new Python test logs before and after workflow reads. |

## Project Structure

### Documentation (this feature)

```text
specs/2650-coverage-gate/
├── spec.md
├── plan.md
└── tasks.md
```

### Source Code (repository root)

```text
.github/workflows/ci.yml
tests/contract/test_pytest_coverage_gate.py
changelog.d/issue-2650-coverage-gate.md
```

**Structure Decision**: The workflow remains in `.github/workflows/ci.yml`. The contract test goes under `tests/contract/` because it verifies CI behavior.

## Design

The workflow adds a new `pytest_coverage_shards` matrix job. Each shard installs the same dependencies as the old job, runs a path group with `--cov=${{ env.SRC_PATH }}`, writes a unique `.coverage.<shard>` file, and uploads that file as an artifact.

The workflow keeps the existing `pytest` job identifier and `pytest (coverage gate)` job name for branch protection. That final job downloads all coverage artifacts, fails if the shard job result is not `success`, combines coverage data, and applies `--fail-under=${{ env.COVERAGE_THRESHOLD }}`.

## Files Changed

- `.github/workflows/ci.yml`: split root coverage execution into shards and keep a final coverage gate.
- `tests/contract/test_pytest_coverage_gate.py`: add a workflow contract test for the split.
- `specs/2650-coverage-gate/spec.md`: record the feature contract.
- `specs/2650-coverage-gate/plan.md`: record the implementation design.
- `specs/2650-coverage-gate/tasks.md`: record the dependency-ordered tasks.
- `changelog.d/issue-2650-coverage-gate.md`: add the release-note fragment.

## Complexity Tracking

No constitution violation is needed.
