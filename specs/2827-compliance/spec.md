# Feature Specification: Compliance cleanup for org probes and AP profile migration

## User stories

1. As a reviewer, I need the compliance score and findings for both files before and after the refactor.
2. As an operator, I need menus 206, 207, and 208 to keep the same behavior.
3. As a maintainer, I need structural cleanup without suppressions.

## Baseline findings

- `src/org/org_synthetic_probes_manager.py`: score 54.0 F. Findings: 81 total. The analyzer reported 9 high length findings, 42 medium length findings, 30 low complexity or block findings, and one comment coverage finding.
- `src/device/ap_profile_migration_manager.py`: score 61.0 D-. Findings: 46 total. The analyzer reported 6 high length findings, 23 medium length findings, 17 low complexity or block findings, and one comment coverage finding.

## Previous pass result

Pull request #2780 changed `src/device/ap_profile_migration_manager.py`, but the score stayed at 61.0. The current analyzer no longer reports the prior parameter-count finding. The remaining measured debt is length, complexity, block count, and comment coverage, so the AP file did not move because the previous pass did not remove enough currently weighted findings to cross a score boundary.

## Refactor plan

- Extract summary, pacing, backup, and setting-update helpers.
- Keep existing module-level names that tests patch by string.
- Do not change exception handlers.
- Do not change destructive operation behavior.

## Behavior preservation proof

- Run focused unit tests before and after the refactor.
- Run the raw `input()` AST check before and after the refactor.
- Run string patch reference search and repair any broken test.
- Run `tools.symbol_diff` for each changed Python file.
