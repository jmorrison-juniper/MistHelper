# Quality Gates

Every pull request runs these 13 checks in parallel through GitHub Actions. The
workflow is `.github/workflows/ci.yml`. A caller can override each threshold
through a `workflow_call` input. The table lists the default.

| Gate | Tool | Threshold |
|------|------|-----------|
| Lint | Ruff | Zero violations |
| Format | Black | Zero files need reformatting |
| Type check | mypy | Zero errors under the `pyproject.toml` settings |
| Tests | pytest with coverage | Coverage >= 80 percent |
| Security | Bandit | Zero findings at any severity |
| Dependencies | pip-audit | Zero known vulnerabilities |
| Code quality | Pylint | Score >= 9.5 |
| Complexity | Radon | No block above cyclomatic complexity 10 |
| Dead code | Vulture | Zero findings at confidence 70 |
| Docstring style | pydocstyle | Zero violations |
| Docstring coverage | interrogate | Coverage >= 90 percent |
| Diagram references | `scripts/lint_diagram_refs.py` | Every diagram reference resolves |
| Browser tests | Playwright | Every end-to-end test passes |

CodeQL runs in a separate workflow, `.github/workflows/codeql.yml`. A code pull
request must wait for CodeQL before it takes the `auto-merge` label.

A gate that fails on `main` opens an issue with the `quality-gate` label. The
same gate closes that issue when it passes again.

## Run a gate on your own machine

Each command below runs one gate. Run the gate that covers the file you changed.

```powershell
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m black --check .
.venv\Scripts\python.exe -m mypy src/ MistHelper.py wsgi.py --config-file pyproject.toml
.venv\Scripts\python.exe -m pytest -q
```

Read the type check scope from the `MYPY_PATHS` value in
`.github/workflows/ci.yml`. This page does not repeat that value, because a
repeated value drifts when the scope moves.

## The writing gate

The repository writes every document in Simplified Technical English. The linter
grades each Markdown file and each Python file at a threshold of 80.

```powershell
.venv\Scripts\python.exe -m tools.ste_linter --min-score 80 <file>
```

Read [the writing guide](ASD-STE100_writing-guide.md) for the rules.
