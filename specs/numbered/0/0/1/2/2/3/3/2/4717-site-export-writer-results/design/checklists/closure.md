# Closure Checklist: Site export write results

**Purpose**: Define the conditions that must hold before issue #4717 closes.

**Created**: 2026-11-26

**Feature**: [Site export write results](../../spec.md)

## Work Items

- [ ] Each task from T001 to T012 has status `verified-present` or a recorded result. Explained: tasks T007 to T012 are open or partial.
- [ ] The T-LOCAL-GATES output is in the pull request body. Explained: the task has not run.
- [ ] The pull request body contains `Closes #4717`. Explained: the pull request does not exist yet.

## Remote Conditions

- [ ] T-REMOTE-CI reports SUCCESS on the head commit. Explained: the pull request does not exist yet.
- [ ] The route check (T011) passed before the merge. Explained: the check has not run.

## Authorization

- [ ] The orchestrator authorizes the merge, and the authorization is recorded. Explained: decision R-8 gates T-MERGE on this authorization.

## Closing

- [ ] Issue #4717 closes through the merge, not by hand. Explained: decision R-9 names the merge as the closing event.
- [ ] The orchestrator removes the `in-progress` label after closure. Explained: the orchestrator performs this step.

## Notes

- This record does not close the issue. The merge closes it.
- A revert of PR #4847 is out of scope. Caution: a revert restores the defect in both persistence methods.
