# Slice Gate Checklist: Nested Source Package Child Counts

**Purpose**: Confirm each wave 1 slice before its pull request merges.

**Created**: 2026-11-26

**Scope**: One slice at a time, under hold H-2.

## Before the Change

- [ ] Hold check: the pull request list shows no open pull request that changes a path in the slice. Holds H-1 to H-7 are clear for the slice.
- [ ] Measure check: the guard prints the totals of the previous step in `plan.md`.
- [ ] Destination check: each destination path is absent, or it holds fewer than five counted children.
- [ ] Consumer check: `git grep` lists each consumer of each old path.

## During the Change

- [ ] Each moved module uses `git mv`.
- [ ] Each new package holds an `__init__.py` file with a docstring that gives its purpose.
- [ ] Each new package holds five or fewer counted children.
- [ ] Each consumer uses the new path.
- [ ] Each old path is removed. No alias, re-export, or fallback import remains.
- [ ] Each changed logger name and class `__module__` value is recorded in the pull request.

## Guard Files

- [ ] The baseline removes the entry for the directory when it holds five or fewer children.
- [ ] The expected totals in `tests/guardrails/test_nested_package_structure.py` match the ratchet sequence in `plan.md`.
- [ ] The symbol map in `tests/guardrails/test_src_public_symbol_preservation.py` names each old and new path.
- [ ] The import-path test `tests/unit/structure/test_nested_slice_w1_NN.py` proves the new path imports and the old path fails.

## Gates

- [ ] `python -m py_compile MistHelper.py` runs only when `MistHelper.py` changes.
- [ ] `python -m ruff check .` reports `All checks passed`.
- [ ] `python -m black --check .` reports no file that needs a change.
- [ ] `python -m mypy $MYPY_PATHS --config-file pyproject.toml` reports success.
- [ ] `python -m pytest tests/guardrails` passes.
- [ ] `python -m pytest tests/<changed test file>` passes for each changed test file.
- [ ] `radon cc <changed package> -j | complexity-gate --max 10` reports no block above 10.
- [ ] `bandit -c pyproject.toml -r <changed package> -q` reports no finding.
- [ ] `pylint src/ --fail-under=9.5` scores 9.5 or above.
- [ ] `symbol-diff --base origin/main <file>` reports no lost module-level name for each changed file.
- [ ] `ste-linter --config .ste-linter.toml --min-score 80` scores each changed Markdown file 80 or above.
- [ ] `python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map` change no file, when the slice moves a menu-registered module.

## Process

- [ ] The changelog fragment `changelog.d/issue-3824-<slug>.md` exists.
- [ ] The pull request body uses `Refs #3824`, not `Closes #3824`.
- [ ] Remote checks pass on the exact pull request head.
- [ ] The orchestrator authorizes the merge before auto-merge starts.
