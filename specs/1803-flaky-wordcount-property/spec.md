# Feature Specification: Stop the Word-Counter Property Tests Flaking

**Issue**: #1803
**Status**: In progress

## Problem

`tests/unit/ste_linter/test_properties.py::test_count_matches_plain_word_count` failed once in a
full `pytest tests/unit` run, then passed on every attempt to reproduce it.

| Attempt | Result |
| - | - |
| Full suite | failed |
| Test alone | passed in 8.26s |
| Test alone, `-p no:randomly` | passed in 32.78s |
| Full suite, later run | passed, 9191 tests |

A test that fails roughly half the time for reasons unrelated to the change under test blocks
unrelated pull requests and trains reviewers to re-run until green. That habit hides real
regressions.

## Three candidate causes, all disproven

The fix below is deliberately narrow, because the obvious explanations do not survive
measurement. Recording them here so nobody spends the time again.

**Hypothesis constants injection.** The theory was that Hypothesis 6.161 injects string
constants harvested from the codebase into `from_regex`, producing a "word" holding a space.
A probe generated 3000 example lists and checked every word against `^[a-z]{1,10}$`, then checked
that `" ".join(words).split()` returns `len(words)`. Both counts were zero. The strategy does not
escape its alphabet.

**A counting defect in `WordCounter`.** Reading `tools/ste_linter/parsing/wordcount.py`, no path
can alter the tally for this input. `_QUOTED_SPAN` needs a quote character, `_merge_number_units`
fires only when `_NUMBER` matches and that pattern is `^[+-]?\d+(?:[.,]\d+)?%?$`, and `_is_word`
returns true for any token holding an alphanumeric character. The property holds by construction.

**State mutation by another test.** A search across `tests/` for anything touching `wordcount`,
`WordCounter`, `_UNITS`, `_NUMBER`, or `_QUOTED_SPAN` found only `test_parsing.py` and this file.
Neither patches module state.

## The remaining mechanism

Hypothesis reports a per-example deadline breach as a test failure, and the default deadline is
200 milliseconds. A full suite runs under memory and CPU pressure that an isolated run does not
have. That is the only mechanism found that is consistent with "fails in the full suite, never
alone."

This was not reproduced directly, because `WordCounter.count` completes well inside 1 millisecond
on this input. The fix is applied on the strength of the symptom matching, not a captured repro,
and this spec says so plainly.

## Requirements

- **FR-001**: Remove the per-example deadline from both property tests in the file.
- **FR-002**: Leave both assertions unchanged, so a real counting defect still fails the build.
- **FR-003**: Record the disproven theories where the next reader will find them.

## Non-goals

- **NG-001**: Do not weaken the strategies. The alphabet and sizes are correct.
- **NG-002**: Do not change `WordCounter`. It is not at fault.
- **NG-003**: Do not disable the tests or mark them `xfail`.

## Success criteria

- **SC-001**: Both properties still assert exactly what they asserted before.
- **SC-002**: The STE linter test directory passes.
- **SC-003**: The full unit suite passes.
- **SC-004**: ruff and black pass on the changed file.
