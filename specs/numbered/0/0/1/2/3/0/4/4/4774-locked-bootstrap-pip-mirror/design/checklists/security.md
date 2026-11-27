# Security Checklist: Locked Bootstrap With a Configured Pip Index

**Purpose**: Confirm that the change keeps credentials, private hosts, and the lock out of reach of logs, tests, and the repository.
**Created**: 2026-11-26
**Feature**: `spec.md` in the parent folder of this checklist

## Credential and Index Handling

- [x] SEC001 The Caution text names no URL, host, or credential. Evidence: design/contracts/bootstrap-source-policy.md, Messages, and spec.md FR-004 and FR-017.
- [x] SEC002 Log output never shows a configured index value. Evidence: TST-02 and TST-03 in tasks.md, T004 and T005.
- [x] SEC003 The bootstrap writes no pip or uv configuration file. Evidence: spec.md FR-007, and KT-02 (research.md, R54) asserts that the saved configuration files keep their content.
- [x] SEC004 The parent process environment stays unchanged. Evidence: spec.md FR-008, and KT-02.
- [x] SEC005 The old public-only fallback keeps its protection against a dead index. Evidence: spec.md FR-009, and TST-08 (research.md, R53).

## Test Isolation

- [x] SEC006 New tests open no connection to any host except loopback. Evidence: TST-02 stubs the probe and fails on any socket connection (T004).
- [x] SEC007 Reproduction uses a loopback listener on 127.0.0.1 only. Evidence: quickstart.md, Step 3.
- [x] SEC008 The private mirror receives no request during the work. Evidence: research.md, D-4, and comment 6807911629.

## Lock and Manifest Integrity

- [x] SEC009 The change keeps `--locked` and adds no `--frozen`. Evidence: spec.md FR-006, and the locked command at research.md, R36.
- [x] SEC010 The change leaves `uv.lock` and every dependency manifest unchanged. Evidence: spec.md FR-005, and plan.md file map.
- [x] SEC011 The guard test reads the lock and fails on a second registry. Evidence: TST-05 (tasks.md, T007).

## Code and Output Hygiene

- [x] SEC012 The change adds no suppression comment such as `# nosec`, `# noqa`, or `# type: ignore`. Evidence: constitution security findings rule (research.md, R23).
- [x] SEC013 New log and message text uses ASCII characters only. Evidence: constitution ASCII rule (research.md, R19).
- [x] SEC014 Scratch output stays under the git-ignored folder `test-artifacts`. Evidence: research.md, R71, and quickstart.md, Cleanup.
- [x] SEC015 The owner check records no index value and no host name. Evidence: quickstart.md, Step 5.

## Notes

- A failed check in this list blocks T-PR. The implementer records each failed check and its fix in the pull request.
