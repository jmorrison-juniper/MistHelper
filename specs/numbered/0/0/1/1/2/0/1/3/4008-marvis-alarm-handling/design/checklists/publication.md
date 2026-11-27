# Publication Checklist: Isolate Marvis Alarm Handling Modules

**Purpose**: Confirm that publication waits for the held guard file, and that each naming and body rule holds before the pull request opens.
**Created**: 2026-11-26
**Feature**: `tasks.md` tasks T001, T002, T-PR, T-REMOTE-CI, and T-MERGE

## Hold and Ownership

- [x] CHK001 The held file is `tests/guardrails/test_src_public_symbol_preservation.py`, held by open PR #4208 (research R44).
- [x] CHK002 The open pull request scan covered seven open pull requests, and only PR #4208 overlaps the candidate file set (research R77).
- [x] CHK003 The serial pull request slot belongs to the coordinator. The orchestrator authorizes the merge (tasks T-PR and T-MERGE).
- [x] CHK004 The shared checkout holds five unrelated edits. Work starts in a new worktree (tasks T001, research E-2).

## Naming and Body Rules

- [x] CHK005 The branch name `chore/4008-marvis-alarm-handling` uses a type from the list that AGENTS allows (research R93 and D-8).
- [x] CHK006 The commit subject `refactor(marvis): isolate alarm handling modules` follows the Conventional Commits form (research D-8).
- [x] CHK007 The pull request body names `Closes #4008`, which AGENTS requires (research R94, tasks T-PR).
- [x] CHK008 The changelog fragment name `issue-4008-marvis-alarm-handling.md` follows the issue form in the changelog README (research R34 and R62).
- [x] CHK009 The rebase onto main happens before the merge, and the affected gates rerun after the rebase (tasks T-PR, constitution Principle IV, research R80).
- [x] CHK010 The auto-merge label is added only after every required check passes (tasks T-REMOTE-CI and T-MERGE).
