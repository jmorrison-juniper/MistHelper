# Retry scope verification

## Conformance

The implementation satisfies FR-001 through FR-007 and SC-001 through SC-004 in [the specification](spec.md).
The issue holds the separate read-only Spec Kit consistency report.

The saved retry parent now uses approved site rows that have aggregate targets.
Confirmation and submission intersect the active selection with the owned durable retry scope.
The existing ordered-site and nonce comparisons still reject a changed effective context.
The operator selection remains unchanged.

No authentication, typed confirmation, audit, token lock, child request, claim, or transaction implementation changed.
No live firmware operation ran. The focused contract module blocks external socket connections.

## Evidence

| Check | Result |
|---|---|
| Existing contract baseline | 44 passed |
| Regression before repair | 3 failed, 4 passed, 42 deselected. Each failure retained site A in the parent. |
| Focused contract after repair | 52 passed |
| Related contracts, units, guards, and SDK checks | 386 passed, 1 skipped |
| Skip cause | The changelog diff guard runs only during a pull request event. |
| Changed route coverage | 91.32 percent, above the 90 percent command threshold |
| New scope methods | Every executable line covered |
| Ruff, entire repository | All checks passed |
| Black, entire repository | 2502 files would remain unchanged |
| Compile, entry point and changed route | Passed |
| Full configured mypy target | Success, 864 source files |
| Changed-route Bandit | No finding |
| Changed-route pydocstyle | No violation |
| Changed-route interrogate | 100 percent |
| Route complexity | Every function within threshold 10 |
| Full configured Vulture target | No finding |
| Repository Pylint | 9.92 out of 10 |
| Test-quality input preflight | Passed, four required inputs read and validated |
| Committed-difference test quality | One file checked, zero findings, zero new findings against the baseline |
| Full-suite test quality | 1211 files checked, 594 existing findings, zero new findings against the baseline |
| Symbol comparison | Zero lost names. One intentional addition: `OrgRetrySiteScope`. The tool returns 1 for an addition. |
| STE, nine initial Markdown files | Each file passed threshold 80 |
| Markdown links | Nine specification files checked, zero broken local links |

The initial smaller coverage selection reached 89.79 percent.
Adding the remaining related organization contracts raised coverage without lowering the threshold.

## Environment limits and advisory results

`pip-audit -r requirements.txt` could not create its temporary environment.
The temporary interpreter aborted with SIGABRT while running `ensurepip --upgrade --default-pip`.
The alternative `pip-audit --local --progress-spinner off` found no known vulnerabilities.
It could not audit the Git-sourced `misthelper-devtools` package because PyPI does not list that package.
No dependency declaration changed.

The repository-wide `speckit-task-audit --root .` advisory found existing historical record debt.
It examined 863 feature records, 386 task files, and 10585 task markers before final completion updates.
The CI job treats that report as advisory.
Do not edit other feature records to remove those findings.

The task uses the existing rendered confirmation controls and adds no interactive element.
The bounded request permits only the existing contract test file.
Browser tests, full-suite tests, live menu sweeps, container builds, and deployment did not run.

## Delivery

The branch started from verified `origin/main` commit `0b04cda81c8ef75096f3bedae0885038c775d665`.
The required managed numeric route passed both PowerShell route checks.
The app-managed branch hook ran through branch rename. Optional commit hooks remain deferred to the tested commits.
The draft pull request must retain `needs-human-review`, with auto-merge disabled.
