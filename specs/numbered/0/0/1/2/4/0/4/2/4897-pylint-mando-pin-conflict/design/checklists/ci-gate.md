# CI Gate Checklist: Pylint gate failure from the mando 0.8.2 pin

**Purpose**: Confirm the evidence for the failed check and the path to a passing check.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Failed check evidence

- [x] The failed check name matches the job name `Pylint (score gate)` at `.github/workflows/ci.yml` line 504. (RC-02)
- [x] The failed step is `Install dependencies`, step 4 of job 137338442217. (RC-29)
- [x] The skipped step is `Run Pylint`, step 5 of job 137338442217. The pylint score never ran. (RC-29)
- [x] The failed rule is the pip resolution error, with its log lines 932 to 945. (RC-30)
- [x] The conflicting pins are `mando==0.8.2` at `requirements-dev.txt` line 179 and `radon==6.0.1` at line 365. (RC-12, RC-09)

## Scope and recurrence evidence

- [x] The same resolution error appears once in 26 of the 28 failed jobs. (RC-31)
- [x] The two Windows checks log the same error. (RC-32)
- [x] The two aggregate jobs fail on an upstream result. (RC-31)
- [x] The Dependabot pip stream has no ignore entry, and it runs weekly. (RC-18, RC-19)

## Main branch and commit evidence

- [x] Main run 45774119357 passed the Pylint job. (RC-33)
- [x] Main run 45774119357 passed the dependency lock job. (RC-34)
- [x] The issue commit `5bb4b385` is the test merge, and the run head is `e86098cd`. (RC-27, RC-28)
- [x] The requirements file has the same blob on base commit `00d9a16e` and on main. (RC-11)

## Remaining proof on the fix branch

- [ ] The new test fails on the pull request #4888 pin. Pending: task T006.
- [ ] The Pylint (score gate) check reaches step `Run Pylint` and passes on the fix branch. Pending: task T-REMOTE-CI.
- [ ] No install step logs `ResolutionImpossible` on the fix branch. Pending: task T-REMOTE-CI.
- [ ] The next scheduled Dependabot run raises no mando version of 0.8 or later. Pending: User Story 3, after the merge.

## Notes

- Each checked item cites its remote row in `design\research.md`.
- Each unchecked item names the task that closes it.
