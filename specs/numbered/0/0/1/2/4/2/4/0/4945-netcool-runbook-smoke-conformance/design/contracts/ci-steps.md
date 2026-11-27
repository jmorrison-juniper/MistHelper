# Contract: CI Gate Steps

This contract lists the CI changes for the package. Each gate names the package path, and each gate prints the count of files that it examined (FR-014, FR-015). The job count stays unchanged (FR-018).

## Gate jobs

| Gate | Job id | Job line on `main` | Gate command on `main` | Variable or step | Change |
| - | - | - | - | - | - |
| Ruff | `ruff` | 140 | `ruff check .` (line 165) | Explicit step after line 165 | Add `ruff check scripts/netcool_runbook_smoke`, then a count step. |
| Black | `black` | 167 | `black --check --diff .` (line 196) | None | No change. The package already passes this gate because `[tool.black]` names no exclusion (`pyproject.toml` line 558). |
| Mypy | `mypy` | 201 | `mypy ${{ env.MYPY_PATHS }} --config-file pyproject.toml` (line 237) | `MYPY_PATHS` (line 93) | Add `scripts/netcool_runbook_smoke/__init__.py`, then a count step. |
| Bandit | `bandit` | 413 | `bandit -c pyproject.toml -r .` (line 451) | Explicit step after line 451 | Add `bandit -c pyproject.toml -r scripts/netcool_runbook_smoke -q`, then a count step. |
| Radon | `radon` | 531 | `radon cc ${{ env.RADON_PATHS }} -a -nb` (line 548) and `complexity-gate --max 10` (line 549) | `RADON_PATHS` (line 99) | Add the package path, then a count step. |
| Vulture | `vulture` | 551 | `vulture ${{ env.VULTURE_PATHS }} --min-confidence ${{ env.VULTURE_CONFIDENCE }}` (line 565) | `VULTURE_PATHS` (line 101) | Add the package path, then a count step. |
| Pydocstyle | `pydocstyle` | 570 | `pydocstyle ${{ env.PYDOCSTYLE_PATHS }}` (line 584) | `PYDOCSTYLE_PATHS` (line 104) | Add the package path, then a count step. |
| Interrogate | `interrogate` | 586 | `interrogate ${{ env.INTERROGATE_PATHS }} --fail-under ${{ env.INTERROGATE_THRESHOLD }} -v` (line 600) | `INTERROGATE_PATHS` (line 107) | Add the package path, then a count step. |

The line numbers come from the decoded `ci.yml` on `main`, blob `d51efbc1`.

## Count step rule

1. The count step runs after the gate step in the same job.
2. The count step counts the Python files under `scripts/netcool_runbook_smoke`. On Windows, it uses `Get-ChildItem -Recurse -Filter '*.py' -LiteralPath scripts/netcool_runbook_smoke`. On Linux, it uses `find scripts/netcool_runbook_smoke -name '*.py'`.
3. The count step prints the number. The text reads `netcool examined files: <count>`.
4. The count step fails when the number is zero.

## Gate guard rule

1. The gate guard in `tests/guardrails/test_ci_gate_triggers.py` reads `ci.yml` through `_parse` (line 58) and `CI_WORKFLOW` (line 35).
2. The guard fails when any of the seven gates lacks the package path in its variable or in its step.
3. The guard fails when any of the seven gates lacks a count step.
4. The guard prints the number of gates and steps that it examined.

## Injected-violation rule

1. TEST-08 writes one file with a known Ruff violation into a temporary copy of the package. It runs the explicit Ruff step. The step must fail.
2. TEST-09 writes one function that Vulture reports. It runs the Vulture step. The step must fail.
3. Each test runs in a temporary directory outside the repository. No test file is written into the repository.
