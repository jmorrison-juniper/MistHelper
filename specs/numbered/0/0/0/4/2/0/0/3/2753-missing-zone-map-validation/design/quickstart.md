# Quickstart: Missing Zone Map Validation

## Prerequisites

Create the repository environment with `python3 scripts/bootstrap_worktree.py`, then activate `.venv`.

## Focused Validation

Run:

```text
python -m pytest tests/unit/test_zone_analyzer.py
```

The tests must prove that missing, null, and wrong-type maps fail before reassurance. They must also prove that explicit empty and valid nonempty maps retain their output.

## Regression Mutation

Temporarily restore the empty-map fallback in `_display_missing_zones` and run the focused validation. The invalid-input tests must fail. Restore the required validation before the final test run.
