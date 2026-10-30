# Quickstart: Unit Test Domain Packages

## Prerequisites

- Use the repository Python environment.
- Read [the package grouping map](../plan.md#package-grouping-map).
- Refresh open pull request file lists before each move batch.

## Validate the final tree

1. Count direct children in `tests/unit/`. The final entries must be `__init__.py`, `config`, `marvis`, `maps`, and `prod_readiness`. Confirm that no direct child was added.
2. Count direct children in each new grouping directory. Each count must not exceed five.
3. Compare each moved path with the open pull request file lists. No active owner path may move.
4. Search imports, test selectors, lint rules, workflows, and documents for each old path.
5. Collect the unit tests with the repository pytest command. The collected test set must match the baseline set.
6. Run the focused tests for each moved package.
7. Run the applicable lint, format, type, and guardrail checks for the changed files.
8. Complete the local and release pipeline steps that Constitution IV requires.

## Expected result

The four existing root containers hold source-aligned domain groups. The tree meets the five-child limit, every baseline unit test remains discoverable, and all references use current paths.
