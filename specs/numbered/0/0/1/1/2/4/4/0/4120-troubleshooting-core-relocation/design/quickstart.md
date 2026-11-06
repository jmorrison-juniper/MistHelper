# Relocation verification

Activate the worktree environment before each command.

```sh
source .venv/bin/activate
python -m pytest tests/unit/troubleshooting tests/unit/marvis/actions tests/unit/refactors/test_run_interactive_test.py tests/unit/test_interactive_test_runner.py
python -m pytest tests/guardrails
python scripts/generate_menu_wiki.py
python -m scripts.menu_api_map
python -m ruff check .
python -m black --check .
```

The tests must preserve behavior and reject obsolete imports.
The package guard must report unchanged violation and excess counts.
Run both generators twice. The second run must produce no difference.
Do not invoke a live cloud operation to verify this source move.
