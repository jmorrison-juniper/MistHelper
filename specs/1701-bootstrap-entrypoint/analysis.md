# Analysis: Bootstrap entry point

## Acceptance Evidence

- **AC-001 (#1701)**: The import regression test patches startup APIs before a fresh `import MistHelper`. The event list is empty.
- **AC-002 (#1701)**: `rtk python -c "import MistHelper"` exits with code 0.
- **AC-003 (#1701)**: `MistHelper.py` no longer calls `logging.basicConfig` at module import. The bootstrap owns the call.
- **AC-004 (#1701)**: `rtk python MistHelper.py --help` prints argparse help before bootstrap work starts.
- **AC-005 (#1701)**: `rtk python -c "import wsgi"` imports the WSGI app through `ApplicationBootstrap(parse_cli=False)`.
- **AC-006 (#1706)**: `MistHelper.py` has zero `sys.argv` reads.
- **AC-007 (#1706)**: `src/refactors/main_entrypoint.py` reads `sys.argv` in one place.
- **AC-008 (#1706)**: The parse-count regression test proves `parse_args` runs one time.
- **AC-009 (#1706)**: The bad flag regression test proves `--test-interactive` exits through argparse with code 2.
- **AC-010 (#1701, #1706)**: The local quality gate section records the final command results.

## Counts

- Import-side-effect triage count before: 33 matches.
- Import-side-effect active count after: 0 watched startup side effects in the regression test.
- `sys.argv` scan count before: 14 matches.
- `sys.argv` read count after: 1 code read in `ApplicationBootstrap`.

## Local Quality Gates

- `rtk python -m py_compile MistHelper.py`: pass.
- `rtk python -m ruff check .`: pass.
- `rtk python -m black --check .`: pass.
- `rtk python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`: pass.
- `rtk python -m pytest tests/unit/refactors/test_reject_unsupported_flag_variants.py -q`: pass.
- `rtk python -m pytest tests/ -x -q`: started and passed the first 1 percent. The local Windows run was too slow to finish promptly. The pull request checks must finish the full suite before merge.
- `rtk python -m bandit -r MistHelper.py`: pass with zero findings and zero skipped lines.
- `rtk python -m tools.symbol_diff --base main MistHelper.py`: pass with no module-level name change.
- `rtk python -c "import MistHelper"`: pass.
- `rtk python MistHelper.py --help`: pass.
- `rtk python -c "import wsgi"`: pass.
- `rtk python -m radon cc MistHelper.py src/refactors/main_entrypoint.py wsgi.py -n C`: pass with no block above B.
