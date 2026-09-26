Slice H audits the agent instruction files and corrects factual claims only.

| File | Old claim | New claim | Evidence |
| - | - | - | - |
| `.github/copilot-instructions.md` | MistHelper provides 209 menu-driven operations. | MistHelper provides 269 menu-driven operations. | `README.md`; `python -c "from src.utils.operation_registry import OperationRegistry; print(len(OperationRegistry.registered_options()))"` returned `270`, and menu 0 is Exit. |
| `.github/copilot-instructions.md` | `mistapi` minimum is 0.59+. | `mistapi` is `>=0.64.0,<0.65`. | `requirements.txt`; `pyproject.toml`. |
| `.github/copilot-instructions.md` | `ENDPOINT_PRIMARY_KEY_STRATEGIES` is at line ~1672. | `ENDPOINT_PRIMARY_KEY_STRATEGIES` is in `src/refactors/endpoint_primary_key_strategies.py`. | `rg ENDPOINT_PRIMARY_KEY_STRATEGIES src/refactors/endpoint_primary_key_strategies.py`. |
| `.github/copilot-instructions.md` | `MistHelper.py` has 6,054 lines, and `src/` has 123,785 lines across 360 files. | Measured on 2026-09-25, `MistHelper.py` has 8,071 lines, and `src/` has 621 Python files with 223,491 lines. | `.venv\Scripts\python.exe -c "from pathlib import Path; ..."` returned those counts. |
| `.github/copilot-instructions.md` | `SSH_GUIDE.md` is at the repository root. | `documentation/SSH_GUIDE.md` is the SSH guide. | `Test-Path documentation\SSH_GUIDE.md` returned `True`; `Test-Path SSH_GUIDE.md` returned `False`. |
| `.github/copilot-instructions.md` | The CI workflow runs all tools as a parallel matrix. | `.github/workflows/ci.yml` runs the repository quality gates. | `.github/workflows/ci.yml`. |
| `.github/copilot-instructions.md` | The quality table listed a Hypothesis gate. | The quality table lists the current CI jobs, including test quality, CodeQL register, menu reference, ops portal, and ops platform jobs. | `.github/workflows/ci.yml` job IDs. |
| `.github/copilot-instructions.md` | The workflow defines 15 gate jobs and two issue-management jobs. | The workflow defines 24 quality jobs and two issue-management jobs. | `rg "^  [a-zA-Z0-9_-]+:" .github\workflows\ci.yml` showed 26 jobs, including the two issue-management jobs. |
| `.github/copilot-instructions.md` | The CI checklist included Hypothesis. | The CI checklist names the current CI areas and removes Hypothesis. | `.github/workflows/ci.yml`; `.github/workflows/codeql.yml`. |
| `agents.md` | `mistapi` minimum is 0.59+. | `mistapi` is `>=0.64.0,<0.65`. | `requirements.txt`; `pyproject.toml`. |
| `CLAUDE.md` | Active technology entries named `mistapi` 0.63.1+ or 0.63.3. | Active technology entries name `mistapi>=0.64.0,<0.65`. | `requirements.txt`; `pyproject.toml`. |
| `.github/PULL_REQUEST_TEMPLATE.md` | Format check uses Ruff. | Format check uses Black with `black --check --diff .`. | `.github/workflows/ci.yml` job `black`. |
| `.github/PULL_REQUEST_TEMPLATE.md` | mypy uses `mypy MistHelper.py`. | mypy uses `mypy $MYPY_PATHS --config-file pyproject.toml`. | `.github/workflows/ci.yml` job `mypy`. |
| `.github/PULL_REQUEST_TEMPLATE.md` | Bandit uses `bandit -r MistHelper.py -c pyproject.toml`. | Bandit uses `bandit -c pyproject.toml -r .`. | `.github/workflows/ci.yml` job `bandit`. |

## Open questions

- The requested `.github\skills\ste-writing\SKILL.md` file does not exist in this tree. I used `documentation/ASD-STE100_writing-guide.md`.
