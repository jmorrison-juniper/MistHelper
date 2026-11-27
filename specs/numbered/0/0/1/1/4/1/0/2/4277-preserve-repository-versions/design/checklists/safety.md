# Preservation Safety Checklist: Preserve Repository Versions and Update the Local Main Checkout

**Purpose**: Confirm that the preservation work keeps each owner item, and that it publishes nothing.
**Created**: 2026-11-26
**Feature**: `specs\numbered\0\0\1\1\4\1\0\2\4277-preserve-repository-versions\plan.md`

## Deletion and Rewrite

- [x] No branch, tag, stash, preserved ref, or worktree is deleted. Verification V-08 compares the counts.
- [x] The primary checkout does not change HEAD. Verification V-02 confirms the state.
- [x] No reset, clean, stash, or `git add -A` command runs in the primary checkout (AGENTS.md line 251).
- [x] The baseline worktree is detached. It creates no branch and no tag.

## Publication

- [x] No local-only ref is pushed. The repository is public (research R-23).
- [x] No backup, checkpoint object, or patch leaves the host.
- [x] The register and the patch stay under `test-artifacts\4277\`, which Git ignores (research R-41).

## Credentials and Data

- [x] No environment variable value is printed. Only names appear in the record.
- [x] No customer data is copied into the record.
- [x] The record copies no content from the owner backup.

## Recovery

- [x] Each uncommitted change has a preserved copy before any update (task T007).
- [x] Each recovery item names an owner and a close condition (recovery register).
- [x] The baseline worktree is removed after validation (task T014).
