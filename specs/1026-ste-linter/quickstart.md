# Quickstart: STE Linter

**Feature**: 1026-ste-linter | **Phase**: 1

## Install

The linter ships with the repository. No extra install is needed for the core.

Optional, for higher grammar accuracy:

```powershell
uv pip install spacy
python -m spacy download en_core_web_sm
```

## Grade a file

```powershell
python -m tools.ste_linter documentation/ASD-STE100_writing-guide.md
```

The tool prints a score from 0 to 100 and a list of violations. Each violation
shows the line, the rule, the problem, and a suggested fix.

## Use in continuous integration

```powershell
python -m tools.ste_linter --format json --min-score 80 docs/**/*.md
```

The exit code is nonzero when a file scores below 80. The JSON output holds the
score, the per-section breakdown, and the violations for the job log.

## Use as a pre-commit hook

Add the hook to `.pre-commit-config.yaml`:

```yaml
  - repo: local
    hooks:
      - id: ste-linter
        name: STE writing linter
        entry: python -m tools.ste_linter --min-score 80
        language: system
        files: \.(md|py)$
```

## Turn on the dictionary checks

The dictionary is not in the repository because it is copyrighted. Build it once
from your licensed PDF:

```powershell
python -m tools.ste_linter.dictionary.extract documentation/ASD-STE100_ISSUE9.pdf
```

The tool writes `data/ste_dictionary.json`, which git ignores. After that, the
linter runs the dictionary checks on every file. Without the file, the linter runs
the structural checks only and says the dictionary checks were skipped.

## Read the score

- 90 to 100: The text follows the STE rules well.
- 70 to 89: The text is mostly clear. Fix the listed violations to improve it.
- Below 70: The text needs work. Start with the errors, then the warnings.

## Tune the rules

Add a section to `pyproject.toml`:

```toml
[tool.ste_linter]
min_score = 80
dictionary = "data/ste_dictionary.json"

[tool.ste_linter.weights]
STE-S1-LEN = 3
STE-S3-PASSIVE = 2
```

Set a weight to zero to turn a rule off.
