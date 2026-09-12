# Tasks: Stop the Word-Counter Property Tests Flaking

**Spec**: `specs/1803-flaky-wordcount-property/spec.md`
**Issue**: #1803

## Phase 1: Root cause

- [X] T001 Probe whether the `from_regex` strategy escapes `[a-z]{1,10}`. It does not.
- [X] T002 Probe whether the space-join splits back to `len(words)`. It does.
- [X] T003 Read `WordCounter.count` and confirm no path alters the tally. Confirmed.
- [X] T004 Search the test tree for anything mutating the wordcount module. Nothing found.
- [X] T005 Identify the remaining mechanism: the Hypothesis per-example deadline.

## Phase 2: Fix

- [X] T006 Add a shared `settings(deadline=None)` and apply it to both properties.
- [X] T007 Comment the reason inline, naming the issue.

## Phase 3: Verification

- [X] T008 Confirm both assertions are unchanged.
- [X] T009 Run the STE linter test directory.
- [X] T010 Run ruff and black on the changed file.
- [X] T011 Run the full unit suite.
