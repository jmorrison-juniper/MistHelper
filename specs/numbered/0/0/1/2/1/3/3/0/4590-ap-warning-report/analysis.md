# AP warning report progress and validation

## Result

The independent report package and natural-key strategy are implemented.
The menu is not registered.
The user requires pull request #4208 to merge before the shared documentation changes.
The existing session automation checks that condition every 30 minutes.

## Artifact analysis

| ID | Severity | Finding | Resolution |
| --- | --- | --- | --- |
| I1 | Medium | The export contract described a Boolean return, but the callable returns a row count. | The contract now specifies the verified row count. |
| B1 | Blocked | Final menu registration and documentation require the README ownership restriction to end. | Tasks T017 through T020 remain unchecked. |

All twelve functional requirements have task coverage.
FR-001 remains deferred with menu integration.
The other requirements have isolated implementation and tests.
There are no unresolved code-meaning or connection-state questions.

## Verified behavior

The report includes connected and disconnected inventory APs with nonzero trouble codes.
It preserves unknown codes and observation times.
It does not equate historical trouble evidence with a current LED color.
Every required source read finishes before persistence.
Failures on later pages prevent partial reports.
The real CSV writer retains the report columns.
The real SQLite writer replaces repeated organization-and-MAC identities without duplicate AP rows.

## Local gate evidence

Commands ran from the feature worktree.
The paths below use the worktree virtual environment.

| Command | Result |
| --- | --- |
| `rtk proxy .venv\Scripts\python.exe -m pytest tests\unit\ap_warning_report tests\integration\ap_warning_report tests\integration\test_mistapi_sdk_compatibility.py tests\unit\refactors\test_sqlite_database_writer.py -q --cov=src.operations.exporting.ap_warning_report --cov-report=term-missing --cov-fail-under=90` | 160 passed. New report package coverage: 100 percent. |
| `rtk proxy .venv\Scripts\python.exe -m ruff check src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py tests\unit\ap_warning_report tests\integration\ap_warning_report` | All checks passed. |
| `rtk proxy .venv\Scripts\python.exe -m black --check src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py tests\unit\ap_warning_report tests\integration\ap_warning_report` | Twelve files need no format changes. |
| `rtk proxy .venv\Scripts\python.exe -m mypy src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py --config-file pyproject.toml` | Success. Six source files checked. |
| `rtk proxy .venv\Scripts\python.exe -m bandit -c pyproject.toml -r src\operations\exporting\ap_warning_report src\foundation\support\refactors\endpoint_primary_key_strategies.py -q` | No findings. |
| `rtk proxy .venv\Scripts\python.exe -m compileall -q src\operations\exporting\ap_warning_report` | No output. |
| `rtk proxy .venv\Scripts\radon.exe cc src\operations\exporting\ap_warning_report -j \| .venv\Scripts\complexity-gate.exe --max 10` | All functions within the threshold. |
| `rtk proxy .venv\Scripts\python.exe -m pylint src\operations\exporting\ap_warning_report --fail-under=9.5` | 9.73 out of 10. |
| `rtk proxy .venv\Scripts\python.exe -m pydocstyle src\operations\exporting\ap_warning_report` | No violations. |
| `rtk proxy .venv\Scripts\interrogate.exe src\operations\exporting\ap_warning_report --fail-under 90` | 100 percent documentation coverage. |
| `rtk proxy .venv\Scripts\python.exe -m vulture src\operations\exporting\ap_warning_report --min-confidence 70` | No findings. |
| `rtk proxy .venv\Scripts\symbol-diff.exe --base origin/main src\foundation\support\refactors\endpoint_primary_key_strategies.py` | No module-level name changed. |
| `rtk proxy .venv\Scripts\python.exe -m pytest tests\guardrails\test_nested_package_structure.py tests\guardrails\test_process_folder_structure.py tests\guardrails\test_changelog_fragment_policy.py -q -rs` | 37 passed. One pull-request-only diff check skipped outside a pull request event. |
| `rtk proxy .venv\Scripts\markdown-link-check.exe specs\numbered\0\0\1\2\1\3\3\0\4590-ap-warning-report changelog.d\issue-4590-ap-warning-report.md` | Ten tracked Markdown files scanned. Zero broken links. |
| `rtk proxy .venv\Scripts\python.exe -m py_compile src\foundation\support\refactors\endpoint_primary_key_strategies.py` | No output. |
| `rtk proxy .venv\Scripts\python.exe -m pydocstyle src\foundation\support\refactors\endpoint_primary_key_strategies.py` | No violations. |

The SDK compatibility tests passed with the targeted selection.
This result does not constitute full repository SDK verification.

The test run reported one Dash plugin deprecation warning and three existing SQLite fixture resource warnings.
The feature tests do not use production credentials.
No live cloud sweep, full-suite coverage run, portal browser run, or container deployment occurred.
Those checks do not replace the deferred menu integration checks.

## Environment notes

The standard bootstrap failed because locked dependency metadata did not match.
The separate bootstrap issue preserves the full failure output.
`uv sync --frozen --extra dev` installed the existing lock without dependency-file changes.
The first SQLite integration assertion used an unsanitized table name.
The test now uses the established SQLite table name normalization.
The first test-quality check found two missing SQLite failure cases.
The added cases reject empty bodies and malformed JSON before the SQLite writer runs.
Their first assertions expected the internal client message rather than the public report message.
The assertions now use the public error boundary, and both cases pass.
The test-quality baseline remains unchanged.

## Remaining work

Run the test-quality procedure after the local feature commit.
Record its result in a comment on issue #4590.
After pull request #4208 merges, recheck file ownership before tasks T017 through T020.
Determine the final unused menu number at that time rather than reserving a potentially stale number.
