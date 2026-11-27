# Test and Guard Review Checklist: Check Every Operation Pair in the mistapi Spec Guard

**Purpose**: Review the guard change and its tests before the local gates run. These items apply to the implementation, not to the specification.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Failure Proof

- [ ] `test_wrong_first_pair_fails_the_guard` fails when `_source_fields` returns only its last pair (task T007).
- [ ] `test_operation_without_module_line_fails_the_guard` fails on the pre-change helper, which skips the orphan.
- [ ] `test_empty_spec_tree_fails_the_guard` fails on the pre-change helper, which passes with zero pairs.
- [ ] `test_declared_absence_fails_when_sdk_defines_operation` fails on the pre-change helper, which has no absence check.

## Test Strength

- [ ] No test asserts a bare truthy value, such as `assert result`.
- [ ] No test relies only on `is not None`.
- [ ] No test uses `pytest.raises(Exception)` or another broad exception type.
- [ ] Each fixture test asserts a message, a pair, or a count.
- [ ] Each fixture test uses monkeypatched roots and the fixed SDK map, so it does not scan the installed SDK.

## Code Rules

- [ ] Each changed executable line carries an inline comment that gives the purpose.
- [ ] `_source_fields` logs an `info` line before the file read and a `debug` line after it.
- [ ] Each changed or new helper keeps five parameters or fewer.
- [ ] Each changed or new helper keeps five logical blocks or fewer, and 25 lines or fewer.
- [ ] No module-level name is added. The declared absences live in the class attribute `ABSENT_SDK_OPERATIONS`.
- [ ] Each printed line and each log line uses ASCII text only.
- [ ] The stale comment on the old `return None` line is replaced.

## Analyzer Readiness

- [ ] The test quality analyzer reports zero new findings against the baseline.
- [ ] `.github/test-quality-baseline.json` has no edit in the commit.
- [ ] `.github/test-quality-config.toml` has no edit in the commit.
