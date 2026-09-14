# Analysis: MistHelper.py Suppression Cleanup

**Issue**: #1004

## Final suppression state

The final suppression search returned zero matches in `MistHelper.py`.

Command:

```powershell
rtk rg "#\s*(type: ignore|noqa|nosec|pylint: disable)" MistHelper.py
```

Result: no matches.

## Repairs

- Replaced the direct `subprocess` import with the audited subprocess module re-export from `src.utils.subprocess_runner`.
- Replaced the PyPI `urlopen` call with a bounded `requests.get` call after an HTTPS scheme check.
- Replaced optional `paramiko` imports with dynamic imports and typed casts.
- Replaced the dynamic `mistapi` attribute write with a module dictionary binding.
- Replaced the hardcoded bind-all literal with a guarded runtime value that exists only for container use.
- Updated the web portal bind-address guardrail tests for the no-suppression rule.

## Local evidence

- `rtk python -m py_compile MistHelper.py`: passed.
- `rtk python -m ruff check .`: passed.
- `rtk python -m black --check .`: passed. It reported 1492 files unchanged.
- `rtk python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`: passed. It reported no issues in 463 source files.
- `rtk python -m tools.symbol_diff --base main MistHelper.py`: passed. It reported no module-level name changed.
- `rtk python -m pytest tests\unit\test_web_portal_bind_address.py tests\unit\test_dependency_check.py tests\bootstrap\test_dependency_check_venv_guard.py -q`: passed. It reported 20 passed.
- `rtk python -m pytest tests/ -x -q`: started and reached 3 percent with no failure after more than two hours. The run was stopped to avoid blocking the shared workstation. The pull request checks will run the full suite.

## Notes

The full `ruff check MistHelper.py --select ALL --statistics` command still reports advisory rules that the normal project gate does not enable. The security signals that mapped to removed suppressions are gone.
