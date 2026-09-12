# Implementation Plan: ASD-STE100 Simplified Technical English Compliance Linter

**Branch**: `1026-ste-linter` | **Date**: 2026-07-26 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/1026-ste-linter/spec.md`

## Summary

Build a Python package `tools/ste_linter` that reads a Markdown or Python file,
extracts the prose, checks it against the Simplified Technical English rules in
`documentation/ASD-STE100_writing-guide.md`, and reports a compliance score from
0 to 100 percent with a per-section breakdown and a list of violations. The tool
runs from the command line, in continuous integration, and in a pre-commit hook.
Structural rules use the standard library. An optional spaCy backend improves the
grammar checks. Dictionary rules use a local, git-ignored dictionary file that a
separate tool generates from the licensed PDF.

## Technical Context

**Language/Version**: Python 3.13 or newer (repository standard).

**Primary Dependencies**: Standard library only for the core. `pypdf` for the
dictionary extraction tool (already used in this repository). Optional `spacy` for
the accurate grammar backend. Test tools: `pytest`, `pytest-cov`, `hypothesis`.

**Storage**: A local JSON dictionary file at `data/ste_dictionary.json`, ignored
by git. No database.

**Testing**: `pytest` with unit fixtures, golden-file tests, and Hypothesis
property tests.

**Target Platform**: Cross-platform command-line tool (Windows, Linux, macOS).

**Project Type**: Single project, command-line library under `tools/`.

**Performance Goals**: Grade a 300-line file in under five seconds with the
heuristic backend.

**Constraints**: The core runs with no third-party dependency. The tool never
crashes on malformed input. No copyrighted dictionary data is committed.

**Scale/Scope**: Around 20 rules across the nine writing-guide sections, two file
parsers, two analysis backends, a scoring model, two report formats, and a
dictionary extraction tool.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Structural discipline (5-item rule)**: The package groups modules into
  sub-packages (`parsing`, `analysis`, `rules`, `dictionary`) to keep each level
  small. The `rules` package holds one module per group of writing-guide sections
  for traceability. See Complexity Tracking for the one justified deviation.
- **Inline comments and action logging**: Every executable line gets an inline
  comment. The linter logs before and after each stage (parse, analyze, score,
  report) with the `logging` module, at info before and debug after.
- **Safety-first input handling**: The tool reads files and never runs untrusted
  input. It validates paths and handles read and parse errors without a crash.
- **Quality gates**: Ruff, Black, mypy, radon, and pytest with coverage at or above
  70 percent must pass. The linter code obeys the same STE guide it enforces.
- **Writing style**: All prose in the code, the help text, and the reports follows
  the STE writing guide.
- **No wrappers, class-based design**: Rules are classes with a common base. The
  backends are classes behind a protocol. No standalone pass-through functions.

## Project Structure

### Documentation (this feature)

```text
specs/1026-ste-linter/
├── plan.md              # This file
├── research.md          # Phase 0: rule detection methods and scoring model
├── data-model.md        # Phase 1: entities and their fields
├── quickstart.md        # Phase 1: how to install, run, and read the report
├── contracts/
│   └── cli.md           # Phase 1: command-line contract and JSON schema
└── tasks.md             # Phase 2: created by the tasks step
```

### Source Code (repository root)

```text
tools/ste_linter/
├── __init__.py          # Package marker and version
├── __main__.py          # Entry for "python -m tools.ste_linter"
├── cli.py               # Argument parsing, orchestration, exit codes
├── config.py            # Load config, rule weights, thresholds
├── models.py            # Severity, Violation, Score, ProseSpan, Document
├── scoring.py           # Deterministic scoring model
├── report.py            # Text reporter and JSON reporter
├── parsing/
│   ├── __init__.py
│   ├── markdown.py      # Extract prose spans from Markdown
│   ├── python_source.py # Extract docstrings and comments with ast and tokenize
│   ├── segmentation.py  # Split prose into sentences and paragraphs
│   └── wordcount.py     # Count words by the STE rules
├── analysis/
│   ├── __init__.py      # Backend factory
│   ├── backend.py       # Backend protocol and shared types
│   ├── heuristic.py     # Standard-library POS, tense, and passive heuristics
│   └── spacy_backend.py # Optional spaCy backend
├── rules/
│   ├── __init__.py      # Rule registry and loader
│   ├── base.py          # Rule base class and helpers
│   ├── sentences.py     # Length, tense, passive, -ing, contractions
│   ├── words.py         # Latin abbreviations, phrasal verbs, gendered pronouns
│   ├── structure.py     # Semicolons, noun clusters, paragraphs, warnings
│   └── dictionary.py    # Dictionary-based rules
└── dictionary/
    ├── __init__.py
    ├── loader.py        # Load and validate data/ste_dictionary.json
    └── extract.py       # Build the dictionary from the licensed PDF

tests/unit/ste_linter/   # One test module per rule group and component
tests/fixtures/ste_linter/
├── compliant.md         # Scores high
├── noncompliant.md      # Scores low, breaks many rules
└── sample_module.py     # Python docstrings and comments to grade
```

**Structure Decision**: Single-project layout under `tools/`, matching the existing
`tools/compliance_analyzer` and `tools/test_quality_analyzer` packages. The linter
is a self-contained package with a `__main__` entry and a `ste-linter` console
script.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| The `rules` package has six modules, which is above the five-item target | Rule modules mirror the nine writing-guide sections so a reader can trace each rule to the standard | One large rules module would exceed the 25-line function and single-responsibility limits and would be harder to test per rule |
| The package has more than five top-level members | A command-line tool needs a CLI, config, models, scoring, and report next to the sub-packages | Folding these into one module would create a large file that breaks the function-size and readability limits |
