# Remote State Checklist: Mixed WAN History Summaries

## Main Branch

- [x] RS-01 Main lacks `summary.py`. Evidence: remote check 37.
- [x] RS-02 Main lacks `calendar.py`. Evidence: remote check 38.
- [x] RS-03 Main lacks the WAN calendar test module. Evidence: remote check 39.
- [x] RS-04 Main lacks the WAN documentation. Evidence: remote check 40.
- [x] RS-05 The repair is not on main, so the defect cannot reproduce on main. Evidence: remote checks 37 to 40 and 41.

## Candidate Branch

- [x] RS-06 The candidate head contains repair commit d7a706d. Evidence: remote check 44.
- [x] RS-07 The candidate head keeps the presence check and the None check. Evidence: remote checks 52 and 53.
- [x] RS-08 Commit 15c69b11, which the issue cites, is absent. Evidence: remote check 46.
- [ ] RS-09 PR 4208 body names the closing keyword for issue 4794. Open until T-PR. Evidence: remote check 47 is partial.

## Record Route

- [x] RS-10 The record folder is absent and the route is free. Evidence: remote checks 35 and 36.
- [x] RS-11 The route parent holds five children, and the route reuses child 1. Evidence: remote checks 34 and 105.

## Version Drift

- [x] RS-12 The mistapi version wording differs across the repository. Evidence: remote checks 7, 23, and 25. Decision D-11 records the drift.

## Counts

- [x] RS-13 The remote table holds 106 rows. The STATUS file holds 106 entries. Evidence: `design/research.md` and the meta file `4794-STATUS.json`.
