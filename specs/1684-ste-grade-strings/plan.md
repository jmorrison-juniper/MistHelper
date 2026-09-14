# Implementation Plan: Grade Python user text in the STE linter

**Branch**: `feat/1684-ste-grade-strings` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/1684-ste-grade-strings/spec.md`

## Summary

This feature adds opt-in extraction of Python string literals that operators read. The parser keeps the existing docstring and comment spans. It adds logging spans and user-facing spans when configuration or command-line flags enable them.

The implementation uses the standard-library `ast` parser. A small extractor class walks call nodes, matches configured call names, cleans placeholders and code tokens, and returns `ProseSpan` objects.

## Technical Context

**Language/Version**: Python 3.13.

**Primary Dependencies**: Standard-library `ast`, `re`, and the shipped STE linter package.

**Storage**: None.

**Testing**: pytest. Tests live in `tests/unit/ste_linter/test_parsing.py`.

**Target Platform**: Windows 11 for local work, and Linux for continuous integration.

**Project Type**: A Python command-line tool in the `tools` package.

**Performance Goals**: The parser walks the Python AST once. A file parse stays linear in the source size.

**Constraints**: The change must not edit `MistHelper.py`. The parser must not grade identifiers, format placeholders, or quoted code tokens.

**Scale/Scope**: One parser, one configuration model, one command-line surface, and one test module.

## Constitution Check

*GATE: This gate passed before Phase 0. It passed again after Phase 1.*

| Principle | How this plan meets it |
| - | - |
| I. Five-Item Rule | New methods keep no more than five parameters and 25 lines. |
| II. Class-Based Architecture | `PythonStringSpanExtractor` owns the new extraction behavior. |
| III. Safety-First | The feature reads source text only and writes no external state. |
| IV. Full Deployment Pipeline | The implementation phase runs the required local gates before the commit. |
| V. Observability and Logging | The parser logs each extraction stage with ASCII text and lazy formatting. |
| VI. Inline Comments | Each new executable line carries an inline comment that states the reason. |
| VII. Action Logging | Each meaningful parser action has an `info` log before and a `debug` log after. |

## Project Structure

### Documentation (this feature)

```text
specs/1684-ste-grade-strings/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── tasks.md
└── analysis.md
```

### Source Code (repository root)

```text
tools/ste_linter/
├── cli.py                    # Adds opt-in flags.
├── config.py                 # Adds category switches and call-name lists.
├── models.py                 # Documents new span kinds.
└── parsing/
    ├── __init__.py           # Passes the configuration into the Python parser.
    └── python_source.py      # Extracts the configured Python string literals.

tests/unit/ste_linter/
└── test_parsing.py           # Covers all requested parser cases.

changelog.d/
└── issue-1684-ste-grade-strings.md
```

**Structure Decision**: The parser already owns Python source extraction, so the new extractor stays in `python_source.py`. The configuration stays in `config.py`, and the CLI switches stay in `cli.py`.

## Design Decision 1: default behavior

The new categories default off. This choice keeps the repository score stable. A repository-wide run with string grading would report many old messages that this issue does not repair.

An operator can enable the categories in `[tool.ste_linter]` with `grade_logging_strings` and `grade_user_facing_strings`. The operator can also use `--grade-logging-strings` and `--grade-user-facing-strings` for one run.

## Design Decision 2: call matching

Logging calls match the configured dotted names. The default list includes `logging.debug`, `logging.info`, `logging.warning`, `logging.error`, `logging.critical`, and `logging.exception`.

User-facing calls match the configured names. The default list includes `print` and `safe_input`. `print` grades each literal positional argument. `safe_input` grades the first positional literal or the `prompt` keyword.

## Design Decision 3: text cleaning

The extractor removes `%` placeholders, brace placeholders, f-string expressions, and quoted code tokens. It skips a span when the cleaned text is empty or only an identifier.

This implements the STE rule that an identifier and a quoted string must not change.
