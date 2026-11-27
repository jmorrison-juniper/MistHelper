# Coordination Checklist: Statistics Export Processed Count After Failed Fetch

**Purpose**: Confirm the publication conditions before the pull request opens.
**Created**: 2026-11-26
**Feature**: `spec.md` and `plan.md` in the parent folder

Caution: An edit to a reserved file can conflict with the owner's local branch. Both changes then need rework. Clear each item before T-PR starts.

## Reservations

- [ ] The #1794 owner records a release of `src\operations\exporting\export\org_device_stats_exporter.py` in the issue thread.
- [ ] The #2711 owner confirms that this change does not edit `tests\unit\export\test_org_device_stats_exporter.py`.
- [ ] The branch of commit `57c99870` is not rebased, moved, or deleted by this work.
- [ ] The older local branch named in the issue is not changed by this work.

## Repository State

- [ ] `gh pr list` shows no open pull request that touches the planned files. Read the list on the day of publication.
- [ ] The issue carries the `in-progress` label before the branch starts.
- [ ] The branch starts from `main`. A worktree holds the branch.
- [ ] The commit contains only the files in the Source Code table of `plan.md`.

## Serial Publication Hold

- [ ] One pull request for this change is open for merge at a time.
- [ ] The branch is current with `main` before the merge. The required checks pass on the latest commit.
- [ ] The orchestrator authorizes the merge before the auto-merge label is added.
