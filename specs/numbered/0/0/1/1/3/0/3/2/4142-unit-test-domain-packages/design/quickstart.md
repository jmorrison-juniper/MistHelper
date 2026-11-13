# Quickstart: Unit Test Domain Packages

## Prerequisites

- Use the repository Python environment.
- Read [the package grouping map](../plan.md#package-grouping-map).
- Refresh open pull request file lists before each move batch.

## Verify the fresh-main candidate

1. Confirm the candidate uses the requested base, `31b752f060d4d10cbe87b5880b071b6570d0b3c9`.
2. Confirm that the map lists 360 unclaimed moves and ten required package markers.
3. Keep 23 site address-audit and rogue-DHCP paths at source because their target groups would exceed five children.
4. Keep four `output_defaults` files at source because `test_session.py` uses relative package imports.
5. Keep eight Juniper RMA JSON replies beside their shared fixture loader.
6. Keep all 22 claimed paths unchanged, including the issue #4721 test.
7. Confirm that the pip-index test deleted on main stays absent.
8. Confirm that the #4607 relocation guard and both #4404 org migration tests stay at their canonical paths.
9. Collect the unit tests and compare normalized node IDs with the fresh-main baseline.
10. Run the affected tests, relocation guards, configuration checks, and test-quality gate.
11. Record the exact command and result for each check in `design/research.md`.

This candidate is partial. It does not claim that `tests/unit/` meets the five-child limit. Issue #4142 stays open.

## Validate full hierarchy acceptance

1. Count direct children in `tests/unit/`. The final entries must be `__init__.py`, `config`, `marvis`, `maps`, and `prod_readiness`. Confirm that no direct child was added.
2. Count direct children in each new grouping directory. Each count must not exceed five.
3. Compare each moved path with the open pull request file lists. No active owner path may move.
4. Search imports, test selectors, lint rules, workflows, and documents for each old path.
5. Collect the unit tests with the repository pytest command. The collected test set must match the baseline set.
6. Run the focused tests for each moved package.
7. Run the applicable lint, format, type, and guardrail checks for the changed files.
8. Complete the local and release pipeline steps that Constitution IV requires.

## Expected result for full acceptance

The four existing root containers hold source-aligned domain groups. The tree meets the five-child limit, every baseline unit test remains discoverable, and all references use current paths.
