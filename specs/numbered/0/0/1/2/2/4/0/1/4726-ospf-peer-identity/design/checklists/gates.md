# Gate Applicability Checklist: OSPF Peer Identity Keys

**Purpose**: Record which row of the Local gates table applies to this change, and why

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

Each row names the gate, its command from `.github/copilot-instructions.md`, and the decision. Each decision is `applies` or `not applicable` with a reason.

## Gate Rows

- [x] Compile (`python -m py_compile MistHelper.py`): not applicable. `MistHelper.py` keeps its content. The menu wiring at RV-40 to RV-42 stays unchanged.
- [x] Lint (`python -m ruff check .`): applies to `src`, `tests`, and the new package.
- [x] Format (`python -m black --check .`): applies to the changed Python files.
- [x] Types (`python -m mypy` with the `MYPY_PATHS` value at RV-64): applies. The new package sits under `src/`.
- [x] Tests (`python -m pytest tests/<the changed file>`): applies to the three changed test files and the new test file.
- [x] Full tests (the two `pytest-chunks` commands): applies. The changed writers feed the unit and the integration trees.
- [x] Safe sweep (`python MistHelper.py --test`): applies. Menu 55 belongs to the `safe` category (RV-45). Without a credential, the Mist checks skip with a credential reason.
- [x] Coverage (`python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`): applies. The change adds source lines under `src`.
- [x] Test quality (the `test-quality-analyzer` procedure): applies to the new test file. Commit the tests first, then run the analyzer.
- [x] Complexity (`radon cc <package> -j | complexity-gate --max 10`): applies to `src/foundation/persistence/identity` and to the changed functions.
- [x] Security lint (`bandit -c pyproject.toml -r <package> -q`): applies to `src`. The change adds no `assert` and no suppression comment.
- [x] Dependency audit (`pip-audit -r requirements.txt`): not applicable. The change adds no dependency. Manifest files stay unchanged.
- [x] Code quality (`pylint src/ --fail-under=9.5`): applies.
- [x] Dead code (`vulture` with the `VULTURE_PATHS` value at RV-65): applies.
- [x] Docstrings (`pydocstyle` with RV-66, and `interrogate` with RV-67): applies. Each new module, class, and function needs a docstring.
- [x] Menu reference (`python scripts/generate_menu_wiki.py` and `python -m scripts.menu_api_map`): not applicable. The menu titles, categories, and table rows stay unchanged (RV-43 to RV-45).
- [x] Symbols (`symbol-diff --base origin/main <file>`): applies to the three existing modules that the change edits.
- [x] STE (`ste-linter` on the five instruction and README files): not applicable to the change itself, because none of those files changes. Task T009 runs the same linter on the operator guide and the changelog fragment.
- [x] Ops portal (npm commands in `ops-portal/`): not applicable. No file under `ops-portal/` changes.
- [x] Ops platform (`pytest` in `mist-ops-platform/`): not applicable. No file under `mist-ops-platform/` changes.

## Guardrails

- [x] Guardrails (`python -m pytest tests/guardrails`): applies. The new package changes the child count of `src/foundation/persistence/` from three to four (RV-89), and the nested source package guard reads that count.
- [x] Declared index contract (`python -m pytest tests/contract/test_arango_declared_indexes.py`): applies, because the strategy entries change (RV-97).
- [x] Endpoint catalog guardrail (`python -m pytest tests/guardrails/test_endpoint_catalog.py`): applies, because the strategy entries change (RV-98). The SLE checks in that file do not depend on the OSPF entries.
