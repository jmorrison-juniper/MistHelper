# Bootstrap pip security validation

1. Run `.venv/bin/python -m pytest -q tests/unit/bootstrap/test_pip_index_probe.py`.
2. Run `python3 scripts/bootstrap_worktree.py`.
3. Run `.venv/bin/python -m pip --version`.
4. Run `.venv/bin/python -m pip_audit --local`.
5. Run `.venv/bin/python -m pip_audit -r requirements.txt`.

The command-contract test must reject the old command for both installers.
The installed pip must be 26.2.2 or newer without a pip advisory finding.
Report the requirements audit separately if its temporary environment fails.
The local audit cannot examine the Git-only `misthelper-devtools` package.
