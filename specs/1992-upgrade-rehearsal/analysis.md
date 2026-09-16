# Analysis of the upgrade rehearsal harness

Run 2026-09-16 by the closure pass for issue #1992, against current `main`.

## What changed since the first analysis

Pull request #2274 merged the rehearsal harness and corrected the circular stop assertion that the first analysis found. Pull request #2737 added `firmware_operator_page`, so the browser suite now reaches the start route with a write-approved stand-in operator. Pull request #2714 corrected terminal-state reconciliation, and pull request #2720 carried the reboot delay through the multi-site route. Pull request #2729 is open, so this pass does not depend on it.

## Option chosen

This closure chooses option 1: a seeded stand-in site and recorded fixtures run in continuous integration with no credentials. A live run stays outside automation because it writes firmware and can reboot production hardware. The skip and limit text states that the automated path does not measure real cloud acceptance or real hardware reboot.

## Coverage result

The unit rehearsal suite drives the shipped driver, event reader, statistics reader, settle gate, and stop control. The suite proves the cascade order, the settle waits, the post-check, the stop lists, the stop message, the organization-scope router cancel, and the three defect drills.

The browser suite now covers the three operator journeys that issue #1992 names.

1. The upgrade start journey uses `firmware_operator_page`. It saves options, verifies a pre-check, types `CONFIRM`, reaches `/api/runs/<run_id>/start`, and sees `upgrade_submitting`.
2. The stop journey opens the run page, types `STOP`, intercepts the stop call with a fixed outcome, and paints the cancelled, writing, and no-cancel lists.
3. The comparison journey opens the picker, chooses the stored pre and post captures of the stand-in site, reads the statistics, filters the tables, and downloads the exports.

## What the proof does not measure

The proof sends no live Mist request. It does not prove that the Mist cloud accepts an upgrade call or a cancel call. It does not prove that hardware reboots or returns with new firmware. The live checklist keeps those facts as a human change-window decision.

## Local evidence

- `mistapi.__version__`: 0.64.0.
- Collection: 16613 tests collected, with zero collection errors.
- Rehearsal suite: 51 passed in 2.95 seconds.
- Browser focus run for upgrade start, stop, and comparison: 32 passed in 30.86 seconds.
- STE scores for the edited feature documents and release fragment: 95 or higher.

## Conclusion

The feature is ready for a pull request. The automated proof closes issue #1992, and the live hardware checklist stays available for the later human run.
