# Quickstart: Offline validation for issue #3399

This guide applies to separately authorized implementation.
No command in this guide ran during task generation.
Use the [installation contract](contracts/bootstrap-installation.md) for expected behavior.
Use the [data model](data-model.md) for run ownership and failure transitions.

## Prerequisites

1. Wait for the parent to confirm completion of the separate dependency restoration.
2. Keep branch `jmorrison-juniper-unclaimed-issue-repairs`.
3. Use the completed worktree `.venv` with Python 3.13 or newer.
4. Confirm that its existing pytest, coverage, and quality tools are available.
5. Keep all installer, connection, browser, and GitHub actions under test substitutes.

Caution: concurrent environment work can change packages while tests read them.
Do not start these commands before the parent confirms completion.
Do not install dependencies, recreate `.venv`, or use `uv run` for validation.

Python 3.13 is installed.
Use the completed worktree interpreter, not a different global interpreter.
Its existence does not confirm that dependency restoration finished.
This feature does not change the interpreter that creates `.venv`.
If the completed environment is unsupported, stop and report that prerequisite to the parent.

## 1. Select the completed interpreter

Run commands from the existing repository root.
Do not create or switch a branch.

On macOS or Linux:

```bash
.venv/bin/python --version
```

On Windows:

```powershell
.\.venv\Scripts\python.exe --version
```

Expected result: Python 3.13 or newer.
Do not use the default macOS interpreter as a substitute.

## 2. Run focused offline tests

Run this four-file baseline before the first implementation edit.
Repeat it after each story and during final validation.
Record the command, exit status, executed-case count, and failed or skipped cases.

These commands exclude repository-wide `tests/conftest.py`.
That file imports `MistHelper.py` and applies unrelated environment checks.
The focused tests import only the bootstrap script and existing test dependencies.

Automatic plugin discovery is disabled.
The tests must replace every real package installer and connection.
They must also replace environment creation, browser downloads, Git operations, and GitHub requests.

On macOS or Linux:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest \
  --confcutdir=tests/unit -o addopts= -p no:cacheprovider \
  tests/unit/bootstrap/test_pip_index_probe.py \
  tests/unit/bootstrap/test_github_account_checker.py \
  tests/unit/scripts/test_browser_download_certificates.py \
  tests/unit/scripts/test_browser_driver_bootstrap.py -q
```

On Windows:

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"
.\.venv\Scripts\python.exe -m pytest `
  --confcutdir=tests/unit -o addopts= -p no:cacheprovider `
  tests/unit/bootstrap/test_pip_index_probe.py `
  tests/unit/bootstrap/test_github_account_checker.py `
  tests/unit/scripts/test_browser_download_certificates.py `
  tests/unit/scripts/test_browser_driver_bootstrap.py -q
```

Expected result: All selected tests pass without network access or real installer starts.
No required case is skipped.
The existing browser and GitHub account assertions remain valid.

### Story red and green commands

The new group is `TestInstallEnvironment.TestUvBootstrap`.
Its four nested groups are `TestCommands`, `TestIndexes`, `TestIsolation`, and `TestFailures`.
[tasks.md](tasks.md) assigns the test names below.

For US1, US2, and US3, write the tests first.
Run the corresponding command before its source edit.
Record the expected assertion failures as red evidence.
Repeat that exact command after the source edit for green evidence.
An environment error, collection error, or unexpected external call is not valid red evidence.
Existing compatibility cases can remain green.
Do not change correct source behavior to force a test failure.

US1:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest \
  --confcutdir=tests/unit -o addopts= -p no:cacheprovider \
  tests/unit/bootstrap/test_pip_index_probe.py \
  -k 'TestUvBootstrap and (test_installer_commands or test_uv_child_settings or test_separate_environments or test_success_reports)' -q
```

US2:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest \
  --confcutdir=tests/unit -o addopts= -p no:cacheprovider \
  tests/unit/bootstrap/test_pip_index_probe.py \
  -k 'TestUvBootstrap and (TestIndexes or test_fresh_invocations)' --tb=no -q
```

US3:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest \
  --confcutdir=tests/unit -o addopts= -p no:cacheprovider \
  tests/unit/bootstrap/test_pip_index_probe.py \
  -k 'TestUvBootstrap and TestFailures' --tb=no -q
```

US4 new compatibility cases:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest \
  --confcutdir=tests/unit -o addopts= -p no:cacheprovider \
  tests/unit/bootstrap/test_pip_index_probe.py \
  -k 'TestUvBootstrap and (test_platform_paths or test_missing_files or test_environment_options or test_successful_main or test_browser_isolation or test_nonblocking_checks)' -q
```

US4 unchanged regression files:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest \
  --confcutdir=tests/unit -o addopts= -p no:cacheprovider \
  tests/unit/bootstrap/test_github_account_checker.py \
  tests/unit/scripts/test_browser_driver_bootstrap.py -q
```

Each story selection must execute at least one required case.
Zero selected cases or a required skip fails the evidence requirement.
The full focused command also checks the existing browser-certificate assertions.
The source and failure selections use `--tb=no` to keep fake credentials out of failed-test console reports.
Failed-case names and result counts remain visible.

## 3. Check the required scenarios

Review the [offline test matrix](contracts/bootstrap-installation.md#offline-test-contract).
Confirm evidence for each row.

| Scenario group | Required result |
| --- | --- |
| Installer commands | Both files use one discovery result and the correct explicit target. |
| File and platform cases | Missing files are skipped. Windows and non-Windows paths remain complete arguments. |
| Working sources | Environment and configuration sources retain their effective primary and extra choices. |
| Public override | Competing aliases and inherited extras cannot restore the dead mirror. Saved files remain unchanged. |
| Isolation | Caller settings, another child dictionary, browser settings, and later invocations remain independent. |
| Failed installation | A nonzero result or launch error raises. `main()` returns `1` without later actions. |
| Reports and compatibility | Timing uses one decimal place. Logs contain no secrets. Successful setup order remains unchanged. |

The substitutes must record commands, call order, dictionary identity, durations, and return codes.
Assertions must verify these observations, not only that a method returned.

## 4. Measure coverage

Use existing pytest-cov.
Load it explicitly because automatic plugin discovery remains disabled.
Keep the configured report threshold of 90%.
Also confirm at least 80% coverage of changed behavior.

On macOS or Linux:

```bash
mkdir -p data/uv-bootstrap-3399
COVERAGE_FILE=data/uv-bootstrap-3399/.coverage \
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest \
  --confcutdir=tests/unit -o addopts= -p no:cacheprovider -p pytest_cov \
  tests/unit/bootstrap/test_pip_index_probe.py \
  tests/unit/bootstrap/test_github_account_checker.py \
  tests/unit/scripts/test_browser_download_certificates.py \
  tests/unit/scripts/test_browser_driver_bootstrap.py \
  --cov=scripts.bootstrap_worktree --cov-config=pyproject.toml --cov-branch --cov-fail-under=90 \
  --cov-report=term-missing \
  --cov-report=json:data/uv-bootstrap-3399/coverage.json
```

On Windows:

```powershell
New-Item -ItemType Directory -Force data/uv-bootstrap-3399
$env:COVERAGE_FILE = "data/uv-bootstrap-3399/.coverage"
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"
.\.venv\Scripts\python.exe -m pytest `
  --confcutdir=tests/unit -o addopts= -p no:cacheprovider -p pytest_cov `
  tests/unit/bootstrap/test_pip_index_probe.py `
  tests/unit/bootstrap/test_github_account_checker.py `
  tests/unit/scripts/test_browser_download_certificates.py `
  tests/unit/scripts/test_browser_driver_bootstrap.py `
  --cov=scripts.bootstrap_worktree --cov-config=pyproject.toml --cov-branch --cov-fail-under=90 `
  --cov-report=term-missing `
  --cov-report=json:data/uv-bootstrap-3399/coverage.json
```

Compare changed statements and branches with the JSON report.
Each required command, override, failure, and isolation branch needs executed assertions.
If coverage fails, add meaningful offline cases within the planned test structure.
Do not lower thresholds, add exclusions, or claim a skipped gate passed.

## 5. Review the implementation boundary

Review only the [exact implementation files](tasks.md#exact-implementation-files).
Confirm unchanged requirement files, package pins, PowerShell entry point, and protected setup methods.
Confirm that `CHANGELOG.md` remains unchanged.
Compare the protected snapshots and hashes recorded before implementation.

The task-generation request reduces the plan's documentation scope.
Update only `documentation/development-setup.md`.
Keep the existing README reference and add only the directly related installer summary.
Add only `changelog.d/issue-3399-uv-bootstrap.md` during authorized implementation.

Issue #3398 remains a separate, later dependency concern.
Do not add `podman-compose` or edit requirement declarations.

## 6. Run exact local quality checks

Run these commands only after the parent releases the environment.
Use the existing project configuration and installed tools.
Do not install a missing tool.
Do not use `--fix` or a baseline-update option.

Syntax:

```bash
.venv/bin/python -m py_compile \
  scripts/bootstrap_worktree.py \
  tests/unit/bootstrap/test_pip_index_probe.py \
  tests/unit/scripts/test_browser_download_certificates.py
```

Lint:

```bash
.venv/bin/python -m ruff check --config pyproject.toml \
  scripts/bootstrap_worktree.py \
  tests/unit/bootstrap/test_pip_index_probe.py \
  tests/unit/scripts/test_browser_download_certificates.py
```

Format:

```bash
.venv/bin/python -m black --check --config pyproject.toml \
  scripts/bootstrap_worktree.py \
  tests/unit/bootstrap/test_pip_index_probe.py \
  tests/unit/scripts/test_browser_download_certificates.py
```

Types:

```bash
.venv/bin/python -m mypy --config-file pyproject.toml scripts/bootstrap_worktree.py
```

The broad Ruff and mypy scans exclude `scripts/`.
These commands name the source file explicitly.
Confirm that the tool checks that file.
Do not report an excluded file or empty scan as a pass.
Keep the configured exclusions unchanged.

Test quality:

```bash
mkdir -p data/uv-bootstrap-3399
.venv/bin/python -m misthelper_devtools.test_quality_analyzer \
  --gate \
  --roots tests/unit/bootstrap tests/unit/scripts \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --report data/uv-bootstrap-3399/test-quality.json \
  --summary data/uv-bootstrap-3399/test-quality.md
```

This static scan includes neighboring existing tests in the two named directories.
It starts no test, package installer, or network operation.
Assert that both changed test files appear in the scanned evidence.
Record the scanned-file count, parse errors, skipped files, new findings, and exit status.
Require zero new findings against the repository baseline.
Keep `.github/test-quality-config.toml` and `.github/test-quality-baseline.json` unchanged.
Do not use `--write-baseline`, `--prune-baseline`, or `--disable-rule`.
Do not omit either repository path and accept the installed package's defaults.

For STE, use the installed entry point through the completed interpreter:

```bash
.venv/bin/python .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 \
  scripts/bootstrap_worktree.py \
  tests/unit/bootstrap/test_pip_index_probe.py \
  tests/unit/scripts/test_browser_download_certificates.py \
  documentation/development-setup.md \
  changelog.d/issue-3399-uv-bootstrap.md
```

Keep the production browser, health, account, and environment-creation methods unchanged.
If an existing finding blocks a command, report it without unrelated edits or new issues.
Record each check in `specs/3399-uv-bootstrap/.spec-context.json`.

## Expected evidence

The later implementation report must name:

1. The completed interpreter version and selected test files.
2. The number of executed cases and their results.
3. Red and green assertion evidence, coverage, and configured quality-gate results.
4. The command, environment, failure, and compatibility observations.
5. Any failed or unavailable validation capability.

Offline tests do not prove real download speed, OneDrive behavior, or live certificate trust.
Do not invent a speed percentage.
This task does not require a live package install, browser download, or GitHub account request.
