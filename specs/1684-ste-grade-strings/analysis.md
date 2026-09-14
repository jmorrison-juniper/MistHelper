# Analysis: Grade Python user text in the STE linter

## Acceptance evidence

1. A Python file with a non-STE logging message is flagged at the correct line.
   - `tests/unit/ste_linter/test_cli.py::test_cli_enables_string_grading_flags` writes a logging call on line 2.
   - The JSON report contains a violation on line 2 when `--grade-logging-strings` is set.
2. A lazy logging format string grades only prose.
   - `test_python_cleans_lazy_logging_placeholder` proves that `"Fetched %s devices"` becomes `"Fetched devices"`.
3. Docstring and comment grading stays unchanged.
   - `test_python_extracts_docstring_and_comment` still sees `docstring` and `comment` spans with the default parser.
   - `test_python_skips_logging_string_by_default` proves that default parsing adds no logging spans.
4. The target call list is configurable.
   - `test_loads_string_grading_settings` proves that TOML can set the two switches and both call-name lists.
5. Edge cases are covered.
   - `test_python_string_edge_cases` covers an f-string, implicit concatenation, an empty string, non-ASCII prose, and an identifier-only string.
   - `test_python_extracts_prompt_keyword` covers a `safe_input` prompt keyword.

## Local gate evidence

- `rtk .\.venv\Scripts\python.exe -m pytest tests\unit\ste_linter\test_parsing.py tests\unit\ste_linter\test_config.py tests\unit\ste_linter\test_cli.py -q`: 36 passed.
- `rtk .\.venv\Scripts\python.exe -m ruff check .`: passed.
- `rtk .\.venv\Scripts\python.exe -m black --check .`: 1490 files unchanged.
- `rtk .\.venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`: success for 463 source files.
- `rtk .\.venv\Scripts\python.exe -m tools.ste_linter tools\ste_linter\README.md specs\1684-ste-grade-strings\spec.md specs\1684-ste-grade-strings\plan.md specs\1684-ste-grade-strings\research.md specs\1684-ste-grade-strings\data-model.md specs\1684-ste-grade-strings\tasks.md changelog.d\issue-1684-ste-grade-strings.md`: all files passed.

## STE linter self-run

Command:

```powershell
rtk .\.venv\Scripts\python.exe -m tools.ste_linter --grade-logging-strings --grade-user-facing-strings tools\ste_linter\parsing\python_source.py
```

Result summary:

```text
tools\ste_linter\parsing\python_source.py
  Score: 99/100  (words graded: 1083, dictionary: skipped)  PASS
  Violations (20): logging and user-facing spans were part of the graded word count.
```

This proves that the parser can grade its own logging strings when the opt-in flags are set.

## Full test suite

The full command was started locally and produced no failure before it was stopped for runtime. The pull request checks provide the full-suite result:

```powershell
rtk .\.venv\Scripts\python.exe -m pytest tests/ -x -q
```

The stopped run had reached `tests\\contract\\upgrade_portal\\test_errors.py` with no failure. The pull request must pass the full suite before merge.
