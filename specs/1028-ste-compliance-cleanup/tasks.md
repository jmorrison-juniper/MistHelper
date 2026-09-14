# Tasks: MistHelper.py STE Compliance Cleanup

**Feature**: 1028-ste-compliance-cleanup | **Input**: spec.md, plan.md, research.md, swap-map.md

## Conventions

- **[P]** marks tasks that can run in parallel because they touch different files.
- Every edit is to a comment or a docstring only. No edit changes code, an
  identifier, or a logging string.
- Every touched line keeps its inline comment per the project standard.

## Phase 0: Baseline

- [X] T001 Confirm no other open pull request modifies `MistHelper.py`. Record the (delivered: specs/1028-ste-compliance-cleanup/spec.md)
  baseline linter counts (structural and dictionary) for the before and after
  compare.
- [X] T002 Regenerate the local dictionary if needed so the dictionary rules run (delivered: tools/ste_linter/dictionary/extract.py)
  during the work.

## Phase A: Mechanical structural fixes (P1)

- [X] T003 [US1] Fix the 20 Latin abbreviations in comments ("e.g." to "for (delivered: MistHelper.py)
  example", "i.e." to "that is", "etc." to "and so on"). Confirm each is prose.
- [X] T004 [US1] Fix the 34 contractions in comments to their full forms. (delivered: MistHelper.py)
- [X] T005 [US1] Fix the 2 phrasal verbs in comments to a single precise verb. (delivered: MistHelper.py)
- [X] T006 [US1] Rewrite the 92 comment semicolons as two sentences each. Skip any (delivered: MistHelper.py)
  semicolon inside a code example.
- [X] T007 [US1] Split the 4 over-length comment sentences. Wrap lines so none pass (delivered: MistHelper.py)
  120 characters.
- [X] T008 [US1] Run the linter. Confirm STE-S9-LATIN, STE-S4-CONTRACTION, (delivered: specs/1028-ste-compliance-cleanup/spec.md)
  STE-S9-PHRASAL, STE-S8-SEMICOLON, and STE-S4-LEN all reach zero.

**Checkpoint**: The mechanical structural findings are gone. The continuous
integration STE gate can verify this phase.

## Phase B: Curated dictionary swaps (P2)

- [X] T009 [US2] Apply the swap map from swap-map.md to comment prose only. Work (delivered: specs/1028-ste-compliance-cleanup/swap-map.md)
  through the file in sections.
- [X] T010 [US2] Review each swap. Confirm no identifier, quoted string, URL, or (delivered: MistHelper.py)
  logging string changed.
- [X] T011 [US2] Run the linter. Confirm the mapped words dropped in the (delivered: specs/1028-ste-compliance-cleanup/spec.md)
  unapproved-word count.

**Checkpoint**: The curated swaps are applied. The prose is clearer.

## Phase C: Technical-noun allowlist (P3)

- [X] T012 [P] [US3] Add an allowlist option to the dictionary rules in (delivered: tools/ste_linter/rules/dictionary.py)
  `tools/ste_linter/rules/dictionary.py`. The linter skips a word in the allowlist.
- [X] T013 [P] [US3] Add the `[tool.ste_linter]` allowlist to `pyproject.toml`, (delivered: pyproject.toml)
  seeded with the common programming terms from the report.
- [X] T014 [US3] Add a unit test that a listed term is not flagged and an unlisted (delivered: tests/unit/ste_linter/test_rules.py)
  word still is.
- [X] T015 [US3] Run the linter with the allowlist. Confirm the listed terms are no (delivered: specs/1028-ste-compliance-cleanup/spec.md)
  longer flagged.

**Checkpoint**: The allowlist raises the signal for every future run.

## Phase D: Verify and gate

- [X] T016 Run `python -m py_compile MistHelper.py`. Confirm it passes. (delivered: MistHelper.py)
- [X] T017 Run the test suite. Confirm it passes, which proves no code behavior (delivered: specs/1028-ste-compliance-cleanup/spec.md)
  changed.
- [X] T018 Run ruff, black, mypy, radon, and the coverage gate. Fix any finding. (delivered: .github/workflows/ci.yml)
- [X] T019 Record the after counts. Confirm the structural findings dropped by at (delivered: specs/1028-ste-compliance-cleanup/spec.md)
  least 60 percent and the four errors reached zero.

## Dependencies

- Phase A is the core and comes first.
- Phase B depends on the swap map.
- Phase C is independent of A and B and can run in parallel.
- Phase D comes last.

## Parallel example

Phase C can run alongside Phase A or B because it touches the linter and the
configuration, not the comment prose:

```text
T012 allowlist option in the linter
T013 allowlist in pyproject.toml
T003 Latin abbreviations in MistHelper.py
```
