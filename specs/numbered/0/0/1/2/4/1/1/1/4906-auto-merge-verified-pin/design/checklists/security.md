# Security Checklist: Pin the verified auto-merge commit

**Purpose**: Review the supply-chain effect of moving the reusable workflow pin.
**Created**: 2026-11-26
**Feature**: `spec.md` and `plan.md` in this record

## Pin Integrity

- [x] SEC001 The pin and the verified commit are full 40-character commit SHAs. Evidence: `FULL_COMMIT` at line 45 of the guard file requires 40 hexadecimal characters, and the new value has that length.
- [x] SEC002 The reusable workflow blob SHA is the same at both commits. Evidence: rows R-14 and R-15 in `design/research.md` name `08870fcd7ab89dc5f9c5abe61f5d407d3721bfb8` for both.
- [x] SEC003 The upstream compare changes no reusable workflow file. Evidence: row R-16 in `design/research.md`.
- [x] SEC004 The reusable workflow runs no external script in the keyword scan. Evidence: unverified item U-7 in `design/research.md` records the limit of the scan.

## Permissions and Secrets

- [x] SEC005 The job permissions do not change. Evidence: the change edits line 61 of the workflow only. Guard test `test_the_job_grants_each_scope_of_the_shared_jobs` checks the scopes.
- [x] SEC006 The change adds no secret, token, or credential to any file. Evidence: the diff adds one commit SHA, comments, and the record folder. Each new line holds plain text only.

## Change Control

- [x] SEC007 The Dependabot branch receives no push. Evidence: decision D-3 in `design/research.md`.
- [x] SEC008 The merge waits for the orchestrator authorization and for passing remote checks. Explained: task T-MERGE in `tasks.md` requires both conditions, and the orchestrator controls the merge.
- [x] SEC009 The guard limit is recorded. Explained: analysis item A-4 in `analysis.md` states that the guard checks equality only, and the blob check stays a manual review.
