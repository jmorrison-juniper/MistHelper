# Zone Summary Validation Guide

## Prerequisites

Run `python3 scripts/bootstrap_worktree.py` if the worktree has no environment.
Activate `.venv` before each validation command.
No live Mist credential or service is required.

## Failure Evidence

Run `python -m pytest tests/unit/test_zone_analyzer.py -k zone_statistics_contract -q`.
Before the repair, the missing-input cases must fail.
After the repair, all cases must pass.

## Valid Behavior

Run `python -m pytest tests/unit/test_zone_analyzer.py -q`.
The existing complete-report and empty-report tests must pass.
Compare original and repaired display output for complete statistics, explicit empty statistics, and an empty analysis.
Each output must match exactly.

## Scope Check

Run `git diff -- src/mist/intelligence/analytics/zone_analyzer.py`.
Only `_display_zone_section` may change.
Issue #2753 must remain open after publication.
