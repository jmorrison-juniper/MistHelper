# Implementation Plan: Zone Summary Validation

**Branch**: `jmorrison-juniper-zone-summary-validation` | **Date**: 2026-10-28 | **Spec**: [Specification](spec.md)

## Summary

Replace one empty-default read in `ZoneConfigurationAnalyzer._display_zone_section` with a dictionary check.
Log and raise `ValueError` before the zone header when the required statistics dictionary is absent or invalid.
Keep the empty-analysis return and accepted dictionaries unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: Standard logging and existing pytest fixtures.

**Storage**: None.

**Testing**: Existing analyzer tests, one parameterized addition, direct output comparison, and focused static gates.

**Target Platform**: Windows, macOS, and Linux.

**Project Type**: Internal report display in the existing command-line tool.

**Performance Goals**: One type check per nonempty zone section.

**Constraints**: Exactly one production validation repair. No cloud requests or export changes.

**Scale/Scope**: One source method, one new test method, preserved test assertions, one release note, and this bounded record.

## Constitution Check

- The source and test modules exceed five top-level names. This narrow edit adds no module-level name.
- `TestDisplayResults` has four methods. The added parameterized method becomes its fifth child.
- The source method remains below 25 lines and has fewer than five parameters.
- The established `changelog.d/` folder exceeds five children. The process-record exception permits one uniquely named fragment.
- Incremental remediation remains separate: reduce existing module and process-folder debt during the repository structure campaign.
- No compatibility wrapper, dependency, transport, configuration, schema, shared pointer, or baseline changes are needed.
- The feature root has four children. Its `design/` directory has four children.
- Failure diagnostics name the field and boundary, not the rejected data.
- The existing app-managed branch replaces the branch-creation hook. The required route helper ran with `-DryRun -Number 2753`.
- Optional Git commit hooks remain disabled in the extension configuration.
- Post-design check: the same constraints hold. No unresolved decision remains within this slice.

## Project Structure

### Documentation

The feature record contains `spec.md`, `plan.md`, `tasks.md`, and `design/`.
Supporting files are `design/research.md`, `design/data-model.md`, `design/quickstart.md`, and `design/checklists/requirements.md`.
No external interface contract is needed because the method is internal.

### Owned Changes

- `src/mist/intelligence/analytics/zone_analyzer.py`: the single display validation boundary.
- `tests/unit/test_zone_analyzer.py`: one addition under `TestDisplayResults`.
- `changelog.d/issue-2753-zone-summary-validation.md`: the operator-visible refusal.

## Ownership and Evidence

The base is `origin/main` at `2cc8bdab4e10a8eafab9384d2f2e2d3ddb634b8f`.
The source matches that revision.
All comments on issues #2753, #2861, and #2863 were read.
The artifact list returned HTTP 200 and an empty array.
Six open pull requests contain no overlap with either Python file.
Pull request #4358 contains no analyzer test relocation.

The prior specification owner released the non-overlapping addition under `TestDisplayResults`.
Their 27-line test change remains preserved on branch `jmorrison-juniper-code-defaults-specification` at `482c5d64c`.
The committed test-quality gate initially reported six existing weak tests after the new method changed their line numbers.
The prior owner and coordinator then released the exact preserved test change for this repair.
Its stable patch identifier matches: `eb360d7ba9aca0796ea1d557bbfa4ea5819d663b`.
The transfer adds the existing assertions without removing or changing their source branch.

## Validation Strategy

First prove that missing statistics currently print zero scanned sites.
Add missing and invalid input cases for both direct and combined display entry points.
Run the new cases before the repair to prove they fail.
After the repair, run the complete analyzer test module.
Compare valid, explicitly empty, and empty-analysis output against the original implementation.

Run applicable compile, Ruff, Black, mypy, complexity, Bandit, docstring, symbol, Markdown, process-folder, changelog, and test-quality gates.
Run the test-quality comparison only after the intended tests are committed.
Use `Refs #2753` in the pull request because this change does not complete the campaign.
Do not merge until the exact acceptance and every required check pass.

## Local Results

- The 16 new refusal cases failed before repair. The final focused run passes all 140 tests.
- Analyzer coverage is 99.08 percent. Three accepted-output comparisons match the original exactly.
- The analyzer has 77 empty `.get` defaults, compared with 78 before this repair.
- Ruff and Black pass for the repository. Mypy passes for all 864 documented source files.
- The source complexity and Bandit gates pass. Pylint reports 9.92 out of 10.
- Vulture and pydocstyle pass for their documented scopes. Interrogate reports 99.7 percent.
- Symbol comparison reports no lost or added module-level names.
- Eight committed Markdown files have no broken local link. All eight pass the STE threshold.
- Process and changelog guards report 28 passed and one expected skip because this is not a pull request event.
- The test-quality preflight reads and validates all four required inputs.
- Both committed test-quality scopes report zero new findings without a baseline change.

The standard `pip-audit -r requirements.txt` command hit the macOS temporary-environment failure recorded in issue #4359.
A complete UV resolution followed by the supported strict, no-dependency-resolution audit reports no known vulnerabilities.
No dependency manifest or interpreter configuration changed.
