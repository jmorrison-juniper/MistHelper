# Quickstart: Versioned Proposal Review and Safe Export

Use this guide after issues #4636 and #4637 to #4640 merge. Each command below runs on Windows PowerShell from the repository worktree for `feat/4641-proposal-review-export`.

## Prerequisites

1. Confirm that `main` holds `src/interfaces/portals/cisco_config_converter/state/`. Issue #4636 creates it.
2. Confirm that issues #4637, #4638, #4639, and #4640 have merged.
3. Create a worktree for the branch. Do not switch branches in a checkout that another session uses.

```powershell
git worktree add ..\MistHelper-feat-4641 -b feat/4641-proposal-review-export main
```

4. Activate the environment from the worktree.

```powershell
.venv\Scripts\Activate.ps1
```

If `.venv` is absent, follow the bootstrap steps in `.github/copilot-instructions.md`, section "Language and environment."

## Reproduce the Gap

Run these commands after the test files exist and before the route code exists.

1. Run the version 2 preview test. It fails with HTTP 404 until task T007 completes.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_routes.py::test_v2_preview_returns_structured_proposal
```

2. Run the version 1 route tests. They pass before and after the change.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
```

## Verification Sequence

Run each command in this order. Stop at the first failure, correct it, and repeat from that command.

1. Compile each changed Python file. The command prints nothing on success.

```powershell
python -m py_compile src\interfaces\portals\cisco_config_converter\routes.py
```

Repeat the same command for `src\interfaces\portals\cisco_config_converter\conversion.py`, `src\interfaces\portals\cisco_config_converter\state\proposal.py`, `tests\integration\web_portal\cisco_config_converter\proposals\test_proposal_assembly.py`, and `tests\integration\web_portal\cisco_config_converter\proposals\test_proposal_routes.py`.

2. Run the lint gate. Expected result: `All checks passed`.

```powershell
python -m ruff check .
```

3. Run the format gate. Expected result: no file needs a change.

```powershell
python -m black --check .
```

4. Run the type gate. The scope matches the `MYPY_PATHS` value in `.github/workflows/ci.yml` (research row 45). Expected result: `Success`.

```powershell
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
```

5. Run the version 1 route tests. Expected result: every test passes without an edit.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
```

6. Run the assembly tests. Expected result: seven tests pass.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_assembly.py
```

7. Run the route tests. Expected result: thirteen tests pass.

```powershell
python -m pytest tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_routes.py
```

8. Run the browser test in strict mode. Set the variable on its own line first. Expected result: every test passes and none skips.

```powershell
$env:UPGRADE_PORTAL_E2E_STRICT = "1"
```

```powershell
python -m pytest tests/e2e/web_portal/test_portal_smoke.py
```

9. Run the structure guard. Expected result: pass.

```powershell
python -m pytest tests/guardrails/test_nested_package_structure.py
```

10. Run the changelog guard. Expected result: pass.

```powershell
python -m pytest tests/guardrails/test_changelog_fragment_policy.py
```

11. Run the complexity gate. Expected result: no block above cyclomatic complexity 10.

```powershell
radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10
```

12. Run the security lint. Expected result: no finding at any severity.

```powershell
bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q
```

13. Run the code quality gate. Expected result: score 9.5 or above.

```powershell
pylint src/ --fail-under=9.5
```

14. Run the dead code gate. Expected result: no finding.

```powershell
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
```

15. Run the docstring gates. Expected result: no violation, and coverage of 90 percent or above.

```powershell
pydocstyle src/ wsgi.py web_portal
```

```powershell
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90 -v
```

16. Run the symbol gate on each modified module. Expected result: `no module-level name changed`.

```powershell
symbol-diff --base origin/main src\interfaces\portals\cisco_config_converter\routes.py
```

Repeat the command for `src\interfaces\portals\cisco_config_converter\conversion.py` and `src\interfaces\portals\cisco_config_converter\state\proposal.py`.

17. Run the coverage gate. Expected result: the combined report shows 80 percent or above.

```powershell
python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=
```

18. Run the test quality gate. Expected result: `gate: 0 new findings vs baseline`.

```powershell
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

19. Run the two full-suite shard commands from `.github/copilot-instructions.md`. Expected result: one summary line for each shard.

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
```

```powershell
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

## Cleanup

No container starts in this change. The tests use memory and `tmp_path` only. No command removes a volume, a database, or a data file.
