# Feature Specification: Triage the Test Quality Findings (#1772)

**Branch**: `test/1772-test-quality-triage`
**Created**: 2026-08-05
**Issue**: <https://github.com/jmorrison-juniper/MistHelper/issues/1772>
**Status**: Specified. Implementation not started.

## Problem / Goal

The test quality analyzer reports 1596 findings. None are triaged.

Spec `1019-test-quality-analyzer` is complete at 60/60 tasks. It delivered the
tool. It did not act on the output.

| Severity | Count |
| - | - |
| high | 35 |
| medium | 1561 |

### Goal

Turn 1596 raw findings into a small set of recorded decisions plus a short list
of real work.

### Non-goals

- Fixing 1596 findings one at a time. The dominant rules collapse into a few
  policy choices.
- Changing the analyzer itself. Scope and baseline defects are tracked
  separately.

## Findings

All 35 high findings are the single rule `untested_public_function`:

| Area | Count |
| - | - |
| `tests/unit` | 21 |
| `tests/integration` | 5 |
| `tests/conftest.py` | 3 |
| `tests/e2e` | 2 |
| `tests/fixtures` | 2 |
| other | 2 |

The five largest medium rules:

| Rule | Count |
| - | - |
| `weak_zero_assertions` | 698 |
| `weak_is_not_none` | 230 |
| `missing_ec_negative_value` | 119 |
| `missing_ec_zero_value` | 85 |
| `weak_bare_assert` | 73 |

Those five are 1205 of the 1561 medium findings, so four or five decisions cover
most of the set.

## Reading the findings

Six of the 35 high findings sit in `conftest.py` or `fixtures`. A fixture module
is support code, not a subject under test, so `untested_public_function` there is
likely rule noise rather than a coverage gap. Triage must therefore separate rule
tuning from real gaps before anyone writes a test.

`weak_zero_assertions` at 698 says a large share of the suite asserts that a
count equals zero rather than asserting the specific outcome. That is a real
weakness, because such an assertion passes when the code under test does nothing
at all. It still needs one policy decision rather than 698 edits.

## Constraints

- No test may be weakened to clear a finding.
- Any rule that is tuned must have the reason recorded, so a later reader does
  not simply re-enable it.

## Test Plan

1. Re-run the analyzer after each decision and record the finding count.
2. For every high finding marked as a real gap, add a test that fails before the
   fix and passes after.
3. Confirm the full unit suite still passes at each step.

## Dependencies

Two analyzer defects should settle first, because both change which findings
exist:

- Analyzer scope. The roots were widened from `tests` to include
  `mist-ops-platform/tests` on 2026-08-05, which moved the count from 1530 to
  1596.
- Baseline drift. Six baseline entries can never match again, so the gate
  compares against a drifted reference.

Re-recording the baseline before the root set settles would only need doing
twice.

## Open Questions

1. Are `conftest.py` and `fixtures` in scope for `untested_public_function`? Six
   of 35 high findings depend on the answer.
2. What replaces a `weak_zero_assertions` call site? A blanket rewrite risks
   asserting the wrong thing 698 times.
3. Is a finding count a gate, or a report? If it gates, the baseline must be
   correct first.

## Acceptance Criteria

- [ ] Every high finding is fixed, or recorded as intentional with a reason.
- [ ] A recorded decision on support-module scope.
- [ ] A recorded policy for `weak_zero_assertions`.
- [ ] The baseline reports 0 stale entries.

## Next Step

Run `speckit.clarify`. All three open questions are policy choices that a person
must make. Writing a plan before they are answered would guess at the shape of
the work.
