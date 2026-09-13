# Tasks: Near-Flawless ASD-STE100 Dictionary Extractor

**Feature**: 1027-ste-dict-extractor | **Input**: spec.md, plan.md, research.md, data-model.md, contracts/cli.md

## Conventions

- **[P]** marks tasks that can run in parallel because they touch different files.
- Every source file follows the STE writing guide, the inline-comment rule, and the
  action-logging rule.

## Phase 1: Setup

- [ ] T001 Add pdfplumber to the `ste-linter` optional dependency extra in
  `pyproject.toml`. Confirm `data/ste_dictionary.json` stays git-ignored.
- [ ] T002 [P] Create the golden set at
  `tests/fixtures/ste_linter/dictionary_golden.json` with about 35 hand-verified
  entries (keyword, part of speech, approved flag, alternatives).

## Phase 2: Foundational

- [ ] T003 Define the parser data types in `tools/ste_linter/dictionary/extract.py`:
  `PositionedWord`, `RawEntry`, and the record builder, from data-model.md.
- [ ] T004 Implement page filtering: skip pages before the start page, and skip
  header, footer, and blank rows by known text.

## Phase 3: User Story 1 - Build an accurate dictionary (P1)

- [ ] T005 [US1] Implement row building: group words by top coordinate and split into
  the word column and the meaning column by left coordinate.
- [ ] T006 [US1] Implement entry detection: match a word plus a part of speech in the
  word column to start an entry, and join continuation rows into column 2.
- [ ] T007 [US1] Implement approved classification by letter case and part-of-speech
  capture from the word column.
- [ ] T008 [US1] Implement alternative extraction by the part-of-speech suffix rule
  from research.md Decision 4. Record the approved meaning for an approved word.
- [ ] T009 [US1] Implement keyword validation: reject a keyword longer than four
  words. Normalize the keyword and alternatives to lower case.
- [ ] T010 [US1] Implement the output writer and the command-line entry with the
  `--output` and `--start-page` options. Write the git-ignored JSON.

## Phase 4: User Story 2 - Measure quality (P2)

- [ ] T011 [US2] Implement the quality harness in
  `tools/ste_linter/dictionary/quality.py`: load the dictionary and the golden set,
  compare each field, and compute the per-field accuracy.
- [ ] T012 [US2] Add the harness command-line entry and the mismatch report from
  contracts/cli.md. Set the exit code from the accuracy target.

## Phase 5: Iterate to the target

- [ ] T013 Run the extractor on the licensed PDF. Run the harness. Read the
  mismatches and the entry count.
- [ ] T014 Fix the parser for the biggest failure group. Re-run. Repeat until the
  field accuracy is 95 percent or higher and the entry count is in range.

## Phase 6: Tests and gates

- [ ] T015 [P] Write `tests/unit/ste_linter/test_dictionary_extract.py`: unit tests
  for row building, entry detection, approved classification, alternative extraction,
  and keyword validation, using small synthetic word lists (no PDF needed).
- [ ] T016 [P] Write a harness unit test: a known dictionary and golden set produce
  the expected accuracy and mismatch list.
- [ ] T017 Run the full gate set: ruff, black, mypy, radon, and pytest with coverage.
  Fix every finding at the root.

## Dependencies

- Phase 2 blocks Phase 3.
- The harness (Phase 4) depends on the extractor output shape.
- Phase 5 depends on the extractor and the harness.
- Phase 6 comes last.

## Parallel example

After Phase 2, these can run together because they touch different files:

```text
T002 golden set
T015 extractor unit tests
T016 harness unit test
```
