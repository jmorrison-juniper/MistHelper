# Quickstart: C0103 naming exceptions in MistHelper.py

Run each command from the repository root. Each command uses the repository `.venv` interpreter. Run `.venv\Scripts\Activate.ps1` first if a command name needs the activated environment.

## Step 1: Check web_portal/services/operation.py

```powershell
.venv\Scripts\python.exe -m pylint web_portal\services\operation.py --disable=all --enable=C0103 --reports=n --score=n --output-format=json
```

Expected result: `[]`. The file was fixed by PR #4662.

## Step 2: Check MistHelper.py

```powershell
.venv\Scripts\python.exe -m pylint MistHelper.py --disable=all --enable=C0103 --reports=n --score=n --output-format=json
```

Expected result before the change: 25 messages at the lines in `design/research.md`, Table 1. Expected result after the change: `[]`.

## Step 3: Run the guard test cases

```powershell
.venv\Scripts\python.exe -m pytest tests\guardrails\test_src_public_symbol_preservation.py -q
```

Expected result before the change: the three new cases fail. Expected result after the change: every case passes.

## Step 4: Run the symbol gate

```powershell
.venv\Scripts\symbol-diff.exe --base origin/main MistHelper.py
```

Expected result: `symbol_diff: no module-level name changed`, with exit code 0.

## Step 5: Run the targeted test modules

```powershell
.venv\Scripts\python.exe -m pytest tests\unit\config\foundation\support\refactors\runtime\entrypoint\test_main_entrypoint.py tests\unit\ssh\test_cli_shell_manager.py -q
```

Expected result: no failure.

## Step 6: Run the changelog policy guard

```powershell
.venv\Scripts\python.exe -m pytest tests\guardrails\test_changelog_fragment_policy.py -q
```

Expected result: no failure.

## Local gates for the changed files

These commands follow the Local gates table in `.github/copilot-instructions.md`.

```powershell
.venv\Scripts\python.exe -m py_compile MistHelper.py
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
.venv\Scripts\python.exe -m vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
.venv\Scripts\python.exe -m interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
.venv\Scripts\python.exe -m bandit -c pyproject.toml MistHelper.py -q
.venv\Scripts\python.exe MistHelper.py --test
```

Expected results: each command exits with code 0. `ruff check .` prints `All checks passed`. `black --check .` reports no file that needs a change. The `--test` sweep completes each safe operation. Without a Mist token, the Mist API checks skip with a credential reason.

Text gate for the Markdown files of this record and the changelog fragment:

```powershell
ste-linter --config .ste-linter.toml --min-score 80 changelog.d\issue-4130-c0103-invalid-names.md specs\numbered\0\0\1\1\3\0\1\0\4130-c0103-invalid-names\spec.md specs\numbered\0\0\1\1\3\0\1\0\4130-c0103-invalid-names\plan.md specs\numbered\0\0\1\1\3\0\1\0\4130-c0103-invalid-names\tasks.md specs\numbered\0\0\1\1\3\0\1\0\4130-c0103-invalid-names\analysis.md
```

Expected result: each file scores 80 or above.

Test quality check for the changed guardrail module:

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected result: `gate: 0 new findings vs baseline`.

## Full test shards (CI runs these as well)

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

Expected result: one summary line for each shard, with no failed chunk.

## Gates that do not apply

- Complexity: the change adds no executable line, so cyclomatic complexity does not change.
- Coverage and the `pylint src/` score gate: the change touches no file under `src/`.
- Dependency audit: the change adds no dependency.
- Menu reference: the change adds no menu operation.
- Docstrings with pydocstyle: `MistHelper.py` is not in `PYDOCSTYLE_PATHS` of `.github/workflows/ci.yml`.
