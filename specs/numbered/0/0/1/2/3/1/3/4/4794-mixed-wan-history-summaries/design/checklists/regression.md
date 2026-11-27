# Regression Test Quality Checklist: Mixed WAN History Summaries

## Fail-Before Evidence

- [ ] RG-01 The mixed-hour test fails on parent commit 07b7751 with KeyError for flap_count. Open until T002. Code reading predicts the failure (remote checks 48 and 49).
- [ ] RG-02 The missing-evidence test fails on parent commit 07b7751. Open until T002. Code reading predicts zero totals (remote check 49).
- [ ] RG-03 The known-zero test fails on parent commit 07b7751. Open until T002. Code reading predicts zero minutes (remote check 49).

## Coverage

- [ ] RG-04 The mixed-hour test asserts all six summaries. Open until T004 (remote check 62 shows the daily-only assertion).
- [x] RG-05 The snapshot-only guard fails if `_has_events` returns true for snapshot hours. Evidence: remote check 54. Test added by T005.
- [x] RG-06 The e2e test asserts the four Unknown strings. Evidence: remote check 65.

## Review Items

- [ ] RG-07 Each changed or touched executable line has a same-line inline comment. Open until T003 and T006 (FR-011, Principle VI).
- [ ] RG-08 `LinkEventSummaries.build` logs an info line before the period build and a debug line after it. Open until T003 (FR-011, Principle VII).
- [ ] RG-09 Each new log line uses ASCII text and `%s` formatting. Open until T003 (Principle V).
