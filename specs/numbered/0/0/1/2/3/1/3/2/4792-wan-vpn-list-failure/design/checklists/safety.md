# Safety Requirements Checklist: Stop VPN Creation When the VPN Inventory Is Unverified

**Purpose**: Test whether the safety requirements of the VPN creation path are complete and consistent.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

**Note**: `[x]` means that the specification meets the criterion. `[ ]` means that a task or the owner completes the item later. Each open item states the task that completes it.

## Fail-Closed Behavior

- [x] CHK001 Each failure class has a named stop rule. [Completeness, Spec §FR-001 to FR-009]
- [x] CHK002 The empty result needs a verified read. [Clarity, Spec §FR-010]
- [x] CHK003 A later page failure discards the earlier pages. [Coverage, Spec §User Story 1 scenario 4]
- [x] CHK004 Missing pagination headers stop the read. [Coverage, Spec §FR-005]

## Operator Confirmation

- [x] CHK005 The typed word `CREATE` stays unchanged. [Consistency, Spec §FR-015]
- [x] CHK006 The stop happens before every prompt. [Clarity, Spec §FR-012]
- [x] CHK007 The change adds no prompt. [Consistency, Plan §Constitution Check]

## Data and Secrets

- [x] CHK008 Log lines name the exception type and never a token. [Clarity, Spec §FR-017]
- [x] CHK009 The tests use mocks and no production credential. [Coverage, Spec §User Story 3]
- [x] CHK010 The live integration test stays out of the change. [Scope, Spec §Dependencies]

## Owner Review

- [x] CHK011 The pull request carries no `auto-merge` label. [Consistency, Tasks T-MERGE and decision D-13]
- [ ] CHK012 The owner records the pagination header check before merge. Explained: task T-HEADER-CHECK runs after the pull request opens. This item stays open until the owner records the result.
- [ ] CHK013 The menu reference generators change only the expected pages. Explained: task T005 checks this during implementation.
