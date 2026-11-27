# Preservation Gate Checklist: Stranded Branch Preservation

**Purpose**: Check each preservation batch before a pull request opens

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

**Note**: An unchecked item stays open until its task runs. Each open item names that task.

## Hold and Scope

- [ ] An owner release comment exists on issue #4719, and its time precedes the batch. Open: runs in task T010.
- [ ] The batch list matches the `batch` values in `design/data-model.md`. Open: runs in task T011.
- [ ] The four overlap branches stay out of batch 1. Open: runs in task T011.
- [ ] No row for `recovery/2977-handoff-20261004` lists a path name or a commit subject. Open: runs in task T013.

## Pull Request Content

- [ ] Each draft body names the branch, the full head SHA, and issue #4719. Open: runs in task T011.
- [ ] Each preservation pull request is a draft. Open: runs in tasks T011 to T013.
- [ ] No pull request body quotes source content from a branch. Open: runs in tasks T011 to T013.

## Safety

- [ ] No branch head changed during the batch. Open: runs in tasks T011 and T012.
- [ ] No branch was deleted, renamed, rebased, or force-pushed. Open: runs in tasks T011 to T014.
- [ ] No token value appears in a pull request body, a comment, or a log. Open: runs in tasks T011 to T013.
