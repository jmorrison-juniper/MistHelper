# Quickstart: Restore -LiteralPath in the setup scripts

Run each command from the root of the worktree for branch `fix/4910-routed-literal-path`. Use a worktree of its own, and do not change a checkout that another session uses (AGENTS.md, Branch, RC-70).

## Prerequisites

- Windows 11 or Linux, with `pwsh` 7 on `PATH`. The behavior tests start `pwsh` (RC-65).
- The repository virtual environment, active in the shell.
- The branch `fix/4910-routed-literal-path` checked out, with the tests of T001 and T002 committed first.

## Scenario 1: Reproduce the bare probes

Command:

```text
python -m pytest tests/guardrails/test_routed_core_port.py -q
```

Expected before the fix: the test `test_scoped_scripts_use_literal_probes` fails. The message reports 10 bare lines among 26 examined lines (RC-60).

## Scenario 2: Reproduce the bracket symptom

Command:

```text
python -m pytest tests/guardrails/test_spec_route_contract.py -k bracket -q
```

Expected before the fix: the two listing cases fail. The message shows that `design/research.md` is missing from `AVAILABLE_DOCS`. The two empty-folder cases pass, because the empty folder holds no optional document.

## Scenario 3: Apply the fix and rerun

Run the commands of Scenarios 1 and 2 again.

Expected after the fix: every case passes. The guard reports 0 bare lines among 26 examined lines.

## Scenario 4: Generator and route regression

Command:

```text
python -m pytest tests/guardrails/test_spec_route_contract.py -q
```

Expected: every test passes, as on the untouched `main`. Run the same command on `main` first and record the count.

## Scenario 5: Changelog policy

Command:

```text
python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q
```

Expected: every test passes. The fragment `changelog.d/issue-4910-routed-literal-path.md` uses the issue name form that RC-31 defines.

## Scenario 6: Full guardrails folder

Command:

```text
python -m pytest tests/guardrails -q
```

Run the command on the untouched `main` first, and record the counts of passed, failed, and skipped tests. Run it again after the change. A new failure blocks the pull request.

## Scenario 7: Lint and format

Commands:

```text
python -m ruff check .
python -m black --check .
```

Expected: `All checks passed` for the first command. The second command reports that no file needs a change.

## Scenario 8: Symbols, security, and complexity

Commands:

```text
symbol-diff --base origin/main tests/guardrails/test_routed_core_port.py
symbol-diff --base origin/main tests/guardrails/test_spec_route_contract.py
bandit -c pyproject.toml -r .
radon cc tests/guardrails/test_routed_core_port.py tests/guardrails/test_spec_route_contract.py -j | complexity-gate --max 10
```

Expected: each `symbol-diff` run exits with code 0 and removes no module-level name. `bandit` runs the same form that CI runs (RC-52) and reports no finding. The complexity gate reports no block above 10.

## Scenario 9: Test quality ratchet

Follow the procedure in `.github/copilot-instructions.md`, section Test quality ratchet (RC-97). Commit the tests before the run. Stop if a staged, unstaged, or untracked change remains.

Commands, in order:

```text
python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Expected: the preflight passes. The changed-file gate and the full-suite gate print `gate: 0 new findings vs baseline`. Do not edit `.github/test-quality-baseline.json` to hide a finding.

## Scenario 10: Markdown checks

Command:

```text
ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/4/1/2/0/4910-routed-literal-path/spec.md specs/numbered/0/0/1/2/4/1/2/0/4910-routed-literal-path/plan.md specs/numbered/0/0/1/2/4/1/2/0/4910-routed-literal-path/tasks.md specs/numbered/0/0/1/2/4/1/2/0/4910-routed-literal-path/analysis.md changelog.d/issue-4910-routed-literal-path.md
```

Expected: each file scores 80 or above. Run the same command for the files under `design/` as well.

## Scenario 11: Change map check

Command:

```text
git status --short
```

Expected: only the paths of the change map in `plan.md` appear. The record folder appears after T-PR copies it into `specs/numbered/0/0/1/2/4/1/2/0/4910-routed-literal-path/`.

## Scenario 12: Cleanup

No container starts in this change, and no port is published. The behavior tests write to `tmp_path` only. Do not run a `system prune` or a `volume prune` command (AGENTS.md, Safety).

## Gates That Do Not Apply

Each gate below comes from the local gates table of `.github/copilot-instructions.md` (RC-80). The reason states why the gate does not apply to this change.

- Compile (`python -m py_compile MistHelper.py`): `MistHelper.py` does not change.
- Coverage (`--cov=src`): no file under `src/` changes.
- Types (`mypy`): the test modules lie outside `MYPY_PATHS` (RC-66).
- Safe sweep and menu reference: the change adds no menu operation.
- Code quality (`pylint src/`) and dependency audit (`pip-audit`): no file under `src/` changes, and no requirement file changes.
- Dead code (`vulture`), docstrings (`pydocstyle`, `interrogate`): their path lists exclude the test modules (RC-66).
- Ops portal and ops platform: the change touches neither `ops-portal/` nor `mist-ops-platform/`.

