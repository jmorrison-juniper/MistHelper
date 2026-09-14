# Tasks: ASD-STE100 Simplified Technical English Compliance Linter

**Feature**: 1026-ste-linter | **Input**: spec.md, plan.md, research.md, data-model.md, contracts/cli.md

**Tests**: Unit, golden-file, and property tests are required by the spec success
criteria. Test tasks are included and precede or accompany each implementation task.

## Conventions

- **[P]** marks tasks that can run in parallel because they touch different files.
- Each task names the exact file it creates or changes.
- Every source file follows the STE writing guide, the inline-comment rule, and the
  action-logging rule from the repository standard.

## Phase 1: Setup

- [X] T001 Create the package skeleton: `tools/ste_linter/__init__.py` (version (delivered: tools/ste_linter/__main__.py)
  string) and `tools/ste_linter/__main__.py` (calls `cli.main`). Add empty
  `__init__.py` files for the `parsing`, `analysis`, `rules`, and `dictionary`
  sub-packages.
- [X] T002 Add the `data/ste_dictionary.json` path and any linter cache to (delivered: .gitignore)
  `.gitignore`. Confirm the licensed PDF is already ignored.
- [X] T003 [P] Add `[tool.ste_linter]` defaults and the `ste-linter` console script (delivered: pyproject.toml)
  to `pyproject.toml`. Confirm the mypy and ruff scopes include `tools/ste_linter`.
- [X] T004 [P] Create the test fixtures folder `tests/fixtures/ste_linter/` with a (delivered: tests/fixtures/ste_linter/compliant.md)
  compliant Markdown file, a noncompliant Markdown file, and a sample Python module.

## Phase 2: Foundational (blocks all rules)

- [X] T005 Implement `tools/ste_linter/models.py`: the `Severity` enum and the (delivered: tools/ste_linter/models.py)
  `ProseSpan`, `Sentence`, `Document`, `Violation`, `SectionScore`, and `Score`
  dataclasses from data-model.md.
- [X] T006 [P] Implement `tools/ste_linter/parsing/wordcount.py`: the STE word (delivered: tests/unit/ste_linter/test_parsing.py)
  counter from research.md Decision 3. Unit test `tests/unit/ste_linter/test_wordcount.py`.
- [X] T007 [P] Implement `tools/ste_linter/parsing/segmentation.py`: split prose (delivered: tests/unit/ste_linter/test_parsing.py)
  into sentences and paragraphs with abbreviation guards. Unit test
  `tests/unit/ste_linter/test_segmentation.py`.
- [X] T008 [P] Implement `tools/ste_linter/parsing/markdown.py`: extract prose (delivered: tests/unit/ste_linter/test_parsing.py)
  spans and skip code, links, tables, and HTML, keeping line numbers. Unit test
  `tests/unit/ste_linter/test_markdown.py`.
- [X] T009 [P] Implement `tools/ste_linter/parsing/python_source.py`: extract (delivered: tests/unit/ste_linter/test_parsing.py)
  docstrings with `ast` and comments with `tokenize`. Unit test
  `tests/unit/ste_linter/test_python_source.py`.
- [X] T010 Implement `tools/ste_linter/analysis/backend.py` (the `Backend` protocol) (delivered: tests/unit/ste_linter/test_analysis.py)
  and `tools/ste_linter/analysis/heuristic.py` (the standard-library backend). Unit
  test `tests/unit/ste_linter/test_heuristic_backend.py`.
- [X] T011 Implement `tools/ste_linter/analysis/spacy_backend.py` and the factory in (delivered: tools/ste_linter/analysis/__init__.py)
  `tools/ste_linter/analysis/__init__.py` that picks spaCy when it imports. Skip the
  spaCy test when spaCy is absent.
- [X] T012 Implement `tools/ste_linter/rules/base.py`: the `Rule` base class, the (delivered: tools/ste_linter/rules/base.py)
  `scope` and `eligible_units` helpers, and the registry hook.
- [X] T013 Build the `Document` builder that runs the parsers and fills the (delivered: tools/ste_linter/parsing/__init__.py)
  sentences and paragraphs. Put it in `tools/ste_linter/parsing/__init__.py`. Unit
  test `tests/unit/ste_linter/test_document.py`.

## Phase 3: User Story 1 - Grade a file from the command line (P1)

**Goal**: A working command that grades a `.md` or `.py` file and prints a score
and a violation report.

**Independent test**: Run the tool on the fixtures and confirm a numeric score and
a violation list.

- [X] T014 [P] [US1] Implement the sentence rules in (delivered: tests/unit/ste_linter/test_rules.py)
  `tools/ste_linter/rules/sentences.py`: length, passive voice, complex tense,
  progressive "-ing", and contractions. Unit test
  `tests/unit/ste_linter/test_rules_sentences.py`.
- [X] T015 [P] [US1] Implement the word rules in `tools/ste_linter/rules/words.py`: (delivered: tests/unit/ste_linter/test_rules.py)
  Latin abbreviations, phrasal verbs, and gendered pronouns. Unit test
  `tests/unit/ste_linter/test_rules_words.py`.
- [X] T016 [P] [US1] Implement the structure rules in (delivered: tests/unit/ste_linter/test_rules.py)
  `tools/ste_linter/rules/structure.py`: semicolons, noun clusters, paragraph
  length, and warnings. Unit test `tests/unit/ste_linter/test_rules_structure.py`.
- [X] T017 [US1] Implement `tools/ste_linter/rules/__init__.py`: the registry that (delivered: tools/ste_linter/rules/__init__.py)
  loads every rule and lets `--select` and `--ignore` filter them.
- [X] T018 [US1] Implement `tools/ste_linter/scoring.py`: the deterministic scoring (delivered: tests/unit/ste_linter/test_scoring.py)
  model from research.md Decision 4. Unit test
  `tests/unit/ste_linter/test_scoring.py`, including a determinism test.
- [X] T019 [US1] Implement `tools/ste_linter/report.py`: the text reporter. Unit (delivered: tests/unit/ste_linter/test_report.py)
  test `tests/unit/ste_linter/test_report_text.py`.
- [X] T020 [US1] Implement `tools/ste_linter/config.py`: load defaults and the (delivered: tests/unit/ste_linter/test_config.py)
  `[tool.ste_linter]` settings, weights, and thresholds.
- [X] T021 [US1] Implement `tools/ste_linter/cli.py` and wire `__main__.py`: parse (delivered: tests/unit/ste_linter/test_cli.py)
  arguments, grade each file, print the text report, and set the exit code.
- [X] T022 [US1] Add the golden test `tests/unit/ste_linter/test_golden.py`: the (delivered: tests/unit/ste_linter/test_golden.py)
  guide scores 90 or higher and the noncompliant fixture scores below 60.

**Checkpoint**: User Story 1 works end to end from the command line.

## Phase 4: User Story 2 - Enforce a threshold in continuous integration (P2)

**Goal**: A JSON output mode and a threshold exit code for a continuous integration
gate.

**Independent test**: Run with `--format json --min-score` on a low file and
confirm valid JSON and a nonzero exit code.

- [X] T023 [US2] Add the JSON reporter to `tools/ste_linter/report.py`. Unit test (delivered: tests/unit/ste_linter/test_report.py)
  `tests/unit/ste_linter/test_report_json.py` that checks the schema in
  contracts/cli.md.
- [X] T024 [US2] Add `--format`, `--min-score`, `--quiet`, and `--version` handling (delivered: tests/unit/ste_linter/test_cli.py)
  and the exit-code contract to `tools/ste_linter/cli.py`. Unit test
  `tests/unit/ste_linter/test_cli.py`.
- [X] T025 [P] [US2] Add the continuous integration job `ste-linter` to (delivered: .github/workflows/ste-lint.yml)
  `.github/workflows/ci.yml` that grades the changed docs with a threshold.

**Checkpoint**: The continuous integration gate fails a low-scoring file.

## Phase 5: User Story 3 - Check writing before a commit (P3)

**Goal**: A pre-commit hook that grades staged files.

**Independent test**: Stage a low file and confirm the hook blocks the commit.

- [X] T026 [US3] Add the `ste-linter` hook to `.pre-commit-config.yaml` for `.md` (delivered: .pre-commit-config.yaml)
  and `.py` files.
- [X] T027 [US3] Confirm the command form the hook uses matches the CLI contract and (delivered: specs/1026-ste-linter/quickstart.md)
  document it in `specs/1026-ste-linter/quickstart.md` if it changed.

**Checkpoint**: The hook blocks a low-scoring staged file.

## Phase 6: User Story 4 - Full dictionary checks (P4)

**Goal**: Dictionary rules that work from a local, git-ignored dictionary file, and
a tool that builds the file from the licensed PDF.

**Independent test**: With a small test dictionary, confirm the linter flags an
unapproved word. With no dictionary, confirm the checks are skipped.

- [X] T028 [P] [US4] Implement `tools/ste_linter/dictionary/loader.py`: load and (delivered: tools/ste_linter/dictionary/loader.py)
  validate `data/ste_dictionary.json` into the `Dictionary` type. Unit test
  `tests/unit/ste_linter/test_dictionary_loader.py` with a small test file.
- [X] T029 [US4] Implement `tools/ste_linter/rules/dictionary.py`: the unapproved (delivered: tools/ste_linter/rules/dictionary.py)
  word and wrong part-of-speech rules. Unit test
  `tests/unit/ste_linter/test_rules_dictionary.py`.
- [X] T030 [US4] Wire the dictionary into the registry and the score. Set (delivered: tools/ste_linter/rules/__init__.py)
  `dictionary_used` and show the skipped note when the file is absent.
- [X] T031 [US4] Implement `tools/ste_linter/dictionary/extract.py`: read the (delivered: tools/ste_linter/dictionary/extract.py)
  licensed PDF with `pypdf` and write `data/ste_dictionary.json`. Guard against a
  missing PDF. Do not commit any output.

**Checkpoint**: Dictionary checks run when the file is present and skip when absent.

## Phase 7: Polish and cross-cutting

- [X] T032 [P] Add the Hypothesis property test (delivered: tests/unit/ste_linter/test_properties.py)
  `tests/unit/ste_linter/test_wordcount_properties.py` for the word counter
  invariants.
- [X] T033 [P] Add a `README.md` for the tool at `tools/ste_linter/README.md` that (delivered: tools/ste_linter/README.md)
  points to the quickstart.
- [X] T034 Run the full gate set: ruff, Black, mypy, radon, and pytest with (delivered: .github/workflows/ste-lint.yml)
  coverage. Fix every finding at the root.
- [X] T035 Grade the new source and docs with the linter itself and raise any file (delivered: tools/ste_linter/README.md)
  below the threshold.

## Dependencies

- Phase 2 blocks Phase 3 through Phase 6.
- User Story 1 (Phase 3) is the core and comes first.
- User Story 2 and User Story 3 depend on the CLI from User Story 1.
- User Story 4 depends on the registry and score from User Story 1.
- Phase 7 comes last.

## Parallel example

After Phase 2, these can run together because they touch different files:

```text
T014 sentence rules
T015 word rules
T016 structure rules
T028 dictionary loader
```
