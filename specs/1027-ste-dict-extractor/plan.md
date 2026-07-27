# Implementation Plan: Near-Flawless ASD-STE100 Dictionary Extractor

**Branch**: `1027-ste-dict-extractor` | **Date**: 2026-07-27 | **Spec**: [spec.md](./spec.md)

## Summary

Rewrite `tools/ste_linter/dictionary/extract.py` to read the ASD-STE100 PDF by word
position with pdfplumber. The tool reconstructs the two left columns of the
four-column dictionary table: the word column and the meaning-or-alternatives
column. It classifies approved status by letter case and extracts alternatives with
a pattern that matches an uppercase word followed by a part of speech. A golden set
and a quality harness measure accuracy, and the parser improves through repeated
measurement until it meets the targets.

## Technical Context

**Language/Version**: Python 3.13 or newer.

**Primary Dependencies**: pdfplumber for word-position extraction. pytest for tests.
The linter runtime does not change and keeps its zero-dependency default.

**Storage**: A local JSON dictionary at `data/ste_dictionary.json`, git-ignored.

**Testing**: pytest unit tests plus a golden-set quality harness.

**Target Platform**: Cross-platform command-line tool.

**Project Type**: Single project. The tool lives under `tools/ste_linter/dictionary`.

**Performance Goals**: Extract the whole dictionary in under 60 seconds.

**Constraints**: No copyrighted dictionary data in git. The tool never crashes on a
missing or unreadable PDF.

**Scale/Scope**: About 2149 entries across roughly 280 PDF pages.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Structural discipline**: The extractor splits into small helpers, each under the
  25-line limit, grouped by stage: page filtering, row building, column split, entry
  parsing, alternative parsing, and output.
- **Inline comments and action logging**: Every line gets a comment. The tool logs
  before and after each stage.
- **Safety-first input handling**: The tool validates the PDF path and the pdfplumber
  import, and it fails with a clear message.
- **Quality gates**: ruff, black, mypy, radon, and pytest with coverage must pass.
- **Writing style**: All prose follows the STE writing guide.
- **No wrappers, class-based design**: The parser is a class with clear methods. The
  harness is a class. No pass-through wrappers.

## Project Structure

### Documentation (this feature)

```text
specs/1027-ste-dict-extractor/
├── plan.md              # This file
├── research.md          # Phase 0: extraction method and column model
├── data-model.md        # Phase 1: entry and report fields
├── contracts/
│   └── cli.md           # Phase 1: extractor command contract
└── tasks.md             # Phase 2: task list
```

### Source Code (repository root)

```text
tools/ste_linter/dictionary/
├── extract.py           # Rewritten pdfplumber column-aware extractor
├── loader.py            # Unchanged dictionary loader
└── __init__.py          # Unchanged package marker

tests/unit/ste_linter/
├── test_dictionary_extract.py   # New: parser unit tests
└── test_dictionary.py           # Existing: loader tests

tests/fixtures/ste_linter/
└── dictionary_golden.json       # New: hand-verified expected entries

tools/ste_linter/dictionary/quality.py   # New: golden-set quality harness
```

**Structure Decision**: The rewrite stays inside the existing dictionary
sub-package. The harness lives next to the extractor so it can run without the full
PDF, using a saved sample when needed.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| - | - | - |
| A new dependency (pdfplumber) is added | The four-column table cannot be read from flattened text. Word positions are required for correct columns | The current flattened-text parser is the exact cause of the bad data this feature must fix |
