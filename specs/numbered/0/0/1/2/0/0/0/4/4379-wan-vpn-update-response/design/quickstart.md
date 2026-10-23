# Quickstart: WAN VPN Update Response

## Prerequisites

Build the worktree environment with `python3 scripts/bootstrap_worktree.py`, then activate `.venv`.

## Validate the response handling

Run:

```sh
python -m pytest tests/unit/test_wan_hub_group_manager.py
```

The tests use mocked SDK responses. A rejected or missing status must produce a failure log and no success log. A 2xx status must preserve the changed path count and success log.

Do not provide Mist credentials. Do not run a live WAN VPN update for this check.

## Validation Results

Run on 2026-10-23:

- `.venv/bin/python -m pytest tests/unit/test_wan_hub_group_manager.py -q`: 59 passed.
- `.venv/bin/python -m pytest tests/guardrails/test_process_folder_structure.py tests/guardrails/test_changelog_fragment_policy.py -q -rs`: 28 passed, 1 skipped because the changelog diff guard requires a pull request event.
- `.venv/bin/ruff check src/operations/wan/wan_hub_group_manager.py tests/unit/test_wan_hub_group_manager.py`: passed.
- `.venv/bin/black --check src/operations/wan/wan_hub_group_manager.py tests/unit/test_wan_hub_group_manager.py`: 2 files unchanged.
- `.venv/bin/python -m py_compile src/operations/wan/wan_hub_group_manager.py tests/unit/test_wan_hub_group_manager.py`: passed.
- `.venv/bin/mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`: no issues in 860 source files.
- `.venv/bin/radon cc src/operations/wan/wan_hub_group_manager.py -j | .venv/bin/complexity-gate --max 10`: all functions passed.
- `.venv/bin/bandit -c pyproject.toml -r src/operations/wan/wan_hub_group_manager.py -q`: passed with no findings.
- The STE gate passed for all nine new Markdown files. Scores ranged from 93 to 99.
- The combined spec-route guard command reported 36 failed, 32 passed, and 1 skipped. Each failure required `pwsh`, which this host does not provide. The issue route was checked against the repository's base-five resolver.
