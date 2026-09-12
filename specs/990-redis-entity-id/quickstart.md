# Quickstart: Validate the Entity Identifier Fallback

**Feature**: `990-redis-entity-id` | **Date**: 2026-07-29

This guide validates the feature end to end. It holds no implementation code. For
the rule itself, read [contracts/entity-id-resolution.md](contracts/entity-id-resolution.md).
For the field definitions, read [data-model.md](data-model.md).

---

## Prerequisites

- The branch `feat/990-redis-entity-id` is checked out.
- The project interpreter is `.venv\Scripts\python.exe`. Warning: the global
  `python` on this host is broken. A command that calls `python` directly fails
  to import `requests` and `mistapi`.
- No Redis server is required. Every test mocks the Redis client.

Run every command from the repository root.

---

## Step 1 - Record the baseline before the change

Capture the current test result and the current complexity score. Compare against
these numbers after the change.

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_redis_writer.py -q
.venv\Scripts\python.exe -m radon cc src/db/redis_writer.py -s -n A | Select-Object -First 5
```

**Expected**: Every test passes. The highest block score is 5.

---

## Step 2 - Validate User Story 1, the fallback path

A record omits the strategy field and carries a common identifier.

**Scenario**: Build two records. Neither record carries the strategy field. One
record carries `device_id` with the value `dev-1`. The other record carries
`device_id` with the value `dev-2`. Both records carry one numeric field.

**Expected result**:

- The writer creates two distinct time-series keys.
- Neither key holds the text `unknown`.
- The identifier part of each key equals the `device_id` value.

**Covers**: Acceptance Scenarios 1, 2, and 3 of User Story 1. Success Criterion
SC-001.

---

## Step 3 - Validate User Story 2, the no-change guarantee

Every record carries the strategy field.

**Scenario**: Build one record that carries both the strategy field and a
`device_id` field. Give the two fields different values.

**Expected result**:

- The identifier part of the key equals the strategy field value.
- The writer ignores the `device_id` value.

**Covers**: Acceptance Scenarios 1 and 2 of User Story 2. Success Criterion
SC-002. Invariant INV-3.

Then run the full existing writer suite. It acts as the regression guard.

```powershell
.venv\Scripts\python.exe -m pytest tests/unit/test_redis_writer.py -q
```

**Expected**: Every test passes. Only one existing test changes, and the change
is the mock return value in `test_over_1000_records_uses_thread_pool`. No
expected key changes.

**Covers**: Acceptance Scenario 3 of User Story 2.

---

## Step 4 - Validate User Story 3, the sentinel path

A record carries no identifier at all.

**Scenario**: Build one record that carries only a numeric field. Then build one
empty record.

**Expected result**:

- The identifier part of the key is the text `unknown`.
- The write completes and raises no error.

**Covers**: Acceptance Scenarios 1 and 2 of User Story 3.

---

## Step 5 - Validate the edge cases

Confirm each row of the decision table in
[data-model.md](data-model.md).

| Case | Expected identifier | Expected source |
| - | - | - |
| The strategy field holds `None` | The fallback value | `fallback` |
| The strategy field holds `""` | The fallback value | `fallback` |
| The strategy field holds `"   "` | The fallback value | `fallback` |
| The strategy field holds `0` | The text `0` | `strategy` |
| The record holds `site_id` and `org_id` | The `site_id` value | `fallback` |
| The record holds an empty `device_id` and a real `site_id` | The `site_id` value | `fallback` |
| The strategy field name is `device_id` and it holds a usable value | The `device_id` value | `strategy` |

---

## Step 6 - Validate the logging rules

**Scenario**: Extract a set of 10000 records with the debug level enabled.

**Expected result**:

- The writer emits exactly one resolution summary event.
- The event reports three counts.
- The three counts sum to 10000.
- The writer emits no log line for a single record.

**Covers**: Functional Requirements FR-007 and FR-008. Success Criterion SC-007.

---

## Step 7 - Run the quality gates

Run the gates exactly as the continuous integration workflow runs them. Warning:
a gate that runs only against the changed path can pass while the workflow gate
fails.

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check --diff .
.venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml
.venv\Scripts\python.exe -m radon cc src/ -a -nb
.venv\Scripts\python.exe -m pytest --cov=src/ --cov-fail-under=80 -q
.venv\Scripts\python.exe -m bandit -c pyproject.toml -r .
```

**Expected**: Every command exits with the code 0. The radon step prints no block
above the score 10.

**Covers**: Success Criterion SC-006.

---

## Step 8 - Grade the prose

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 CHANGELOG.md
```

**Expected**: The score is 80 or above.

**Covers**: Functional Requirement FR-012. Success Criterion SC-008.

---

## Step 9 - Confirm the changelog entry

Open `CHANGELOG.md` and confirm one new entry under the `## [Unreleased]`
heading. The entry names the defect, the fallback order, and the issue number
990.

**Covers**: Functional Requirement FR-010.

---

## Definition of done

| Check | Source |
| - | - |
| The three resolution branches each have a test | FR-009, SC-003 |
| No record with a common identifier lands in the `unknown` bucket | SC-001 |
| Every key for a record with the strategy field is byte-identical | SC-002, FR-005 |
| Every key holds three colon-separated parts | SC-004 |
| One summary line per extraction call and no per-record line | SC-007 |
| Every quality gate passes | SC-006 |
| The STE linter reports 80 or above | SC-008 |
| Every changed line carries an inline comment | FR-011 |
| The changelog holds a new entry | FR-010 |
