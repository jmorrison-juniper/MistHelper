# Security Checklist: SQLite schema context errors

**Purpose**: Check the security aspects of the failure path before implementation.

**Created**: 2026-11-26

## Failure Handling

- [x] A failed detection never selects a strategy (FR-002 and FR-005).
- [x] The exporter boundary stops the write and returns `False` (FR-005).
- [x] No broad handler ignores its caught exception (FR-011, research row 17).

## Logging

- [x] The error line holds the table name, the output format, and the exception text only (research row 11).
- [x] The new text adds no secret, token, or password. Constitution Principle III forbids them in logs.
- [x] The new messages use ASCII text (constitution Principle V).

## Network and Data

- [x] The tests open no network connection. TST-3 asserts zero database connections.
- [x] No table, key, or existing data changes. The plan warns against deleting or rewriting `data/mist_data.db`.
- [x] No dependency changes (plan, Dependencies).

## Remaining Risks

- [x] An unnamed SQLite write stops during a local failure. The README and operator guide describe this behavior (risk R-1).
