# Tasks

## Measurement

- Record the commit and live finding count.
- Compare each live identity with the baseline.
- Save the red analyzer output outside the worktree.

## Test repair

- Repair the 36 available findings.
- Use response objects for Mist SDK status tests.
- Assert the exact failure signal.
- Repair false SDK coverage in a separate commit.

## Baseline and validation

- Prune 36 stale entries and retain the two measured deferred entries.
- Add one changelog fragment.
- Run targeted tests.
- Run compile, Ruff, Black, mypy, and symbol checks.
- Run the test-quality preflight.
- Run the changed-from analyzer.
- Rebase and repeat the measurement.

