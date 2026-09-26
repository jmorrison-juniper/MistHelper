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

Warning: the browser gate can report a false pass. Each browser test module
calls `pytest.importorskip`, so a missing Playwright package turns the whole
suite into a skip, and pytest reports a skip as a pass. Issue #2241 recorded 11
test files that covered nothing while this gate stayed green.

Two changes close that hole, and both must stay.

- The workflow downloads the browser with `playwright install --with-deps
  chromium`, because the package ships no browser.
- The workflow sets `UPGRADE_PORTAL_E2E_STRICT=1`, which turns a missing package
  into a collection failure instead of a skip.

Warning: do not remove either step. The gate then passes over an empty suite,
and no signal reports the loss.

CodeQL runs in a separate workflow, `.github/workflows/codeql.yml`. A code pull
request must wait for CodeQL before it takes the `auto-merge` label.

A gate that fails on `main` opens an issue with the `quality-gate` label. The
same gate closes that issue when it passes again.

## Exclusion drift report

The file `quality_gate_exclusions.json` records each documented Ruff, mypy,
Bandit, and Pylint exclusion with its recorded finding count.

The `Quality exclusion drift (advisory)` job runs
`scripts/check_exclusion_drift.py`. It compares each current count with the
recorded count and uploads a JSON report. It reports growth and zero counts in
the job log. It never blocks a pull request.

## Ruff S rule decision

Issue #1780 measured the Ruff `S` rule family on 2026-09-13. The repository
does not select `S` in Ruff. Bandit stays the only security syntax linter.

The measurement used these commands.

```powershell
.\.venv\Scripts\python.exe -m bandit -c pyproject.toml -r .
.\.venv\Scripts\python.exe -m ruff check --select S .
```

The Bandit command matches the `bandit` job in `.github/workflows/ci.yml`. The
Ruff command was a trial only, so `pyproject.toml` keeps `S` absent.

| Measurement | Count | Rule count |
| - | - | - |
| Bandit findings from the CI command | 0 | None |
| Ruff trial findings | 21,807 | S101 21,551, S102 1, S104 7, S105 107, S106 53, S107 1, S108 25, S110 10, S112 1, S113 2, S310 4, S311 1, S603 30, S605 2, S606 1, S607 8, S608 3 |
| Active findings that both tools report | 0 | None |
| Active findings that only Bandit reports | 0 | None |
| Active findings that only Ruff reports | 21,807 | Same as the Ruff trial |

The active Bandit count is zero because the current `# nosec` comments hide the
accepted findings. A second measurement used `--ignore-nosec` to compare those
accepted findings with the Ruff trial.

| Suppression set | Count | Rule count |
| - | - | - |
| Same line and mapped rule in both tools | 83 findings on 81 lines | B101/S101 29, B104/S104 4, B105/S105 19, B110/S110 8, B112/S112 1, B310/S310 2, B311/S311 1, B603/S603 11, B605/S605 2, B606/S606 1, B607/S607 2, B608/S608 3 |
| Only Bandit reported it | 32 | B104 3, B105 7, B107 1, B404 10, B603 3, B608 8 |
| Only Ruff reported it | 21,724 | S101 21,522, S102 1, S104 3, S105 88, S106 53, S107 1, S108 25, S110 2, S113 2, S310 2, S603 19, S607 6 |

If both tools ran, 81 existing lines would need both `# nosec` and `# noqa`
comments. Dropping Bandit would lose measured findings and scopes. Bandit
reported B404, B107, and B608 findings that the Ruff trial did not report on the
same line. Bandit also scans `web_portal`, `mist-ops-platform`, and `src/maps`,
which the gate for Ruff at the root excludes.

The decision is option 2 from issue #1780. Do not select `S` in Ruff. Do not
drop Bandit. Use `# nosec` with a Bandit rule and a reason when a false positive
needs a suppression.

## Branch protection on main

Branch protection names 14 required checks. They are the 13 gates above plus
CodeQL.

Branch protection also sets `strict` to true, which GitHub calls "Require
branches to be up to date before merging". Rebase your branch onto `main` before
you merge. GitHub then re-runs the gates against the new tip.

Warning: do not turn that flag off. A gate run measures the branch against the
base that existed when the run started, and it never re-runs when `main` moves.
Without the flag, a green pull request that sits far behind can break `main`, and
the next author pays for a defect that another branch introduced. Issue #1978
records the case, and issue #1754 records the choice of the 14 checks.

Read the current setting with one command.

```powershell
gh api repos/jmorrison-juniper/MistHelper/branches/main/protection/required_status_checks
```

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
.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80 <file>
```

Read [the writing guide](ASD-STE100_writing-guide.md) for the rules.
