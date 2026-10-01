# Tasks: Prefer uv for worktree setup

**Issue**: #3399
**Branch**: `jmorrison-juniper-unclaimed-issue-repairs`
**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), and [data-model.md](data-model.md)
**Contract**: [bootstrap-installation.md](contracts/bootstrap-installation.md)
**Validation**: [quickstart.md](quickstart.md)
**Context**: `.spec-context.json`

Tests are required by the request and FR-020.
The parent authorized implementation and recovered the agent's partial edits.
All local implementation tasks below are complete. Protected remote delivery remains pending.

## Scope and execution rules

Keep the existing app-managed branch and the parent's issue ownership.
Do not create or switch branches.
Do not create issues, install dependencies, commit, push, or deploy.
Do not run the bootstrap command against the real worktree during validation.

Caution: the parent dependency restoration can change packages while tests read them.
Wait for the parent's release before you use `.venv/bin/python`.
Python 3.13 is installed.
That fact does not confirm that dependency restoration finished.
Do not inspect or repair the environment during task generation.

### Exact implementation files

| File | Permitted later change |
| --- | --- |
| `scripts/bootstrap_worktree.py` | Change dependency selection, source capture, child environments, and installation reports. |
| `tests/unit/bootstrap/test_pip_index_probe.py` | Add offline cases within the existing class structure. |
| `tests/unit/scripts/test_browser_download_certificates.py` | Make the existing pip case simulate absent uv. Keep its assertions. |
| `documentation/development-setup.md` | Explain the complete bootstrap behavior on one setup page. |
| `README.md` | Name the installer behavior beside the existing setup-page reference. |
| `changelog.d/issue-3399-uv-bootstrap.md` | Add one issue-owned release fragment after implementation. |

The README already links to the setup page.
After its Maps ownership reservation ended, the parent added one behavior sentence beside that reference.
Keep detailed setup instructions on the single setup page.
The final implementation scope contains six files, including this directly related README sentence.

Issue #3398 is a separate, later dependency concern.
Do not add `podman-compose`.
Do not change `requirements.txt`, `requirements-dev.txt`, package pins, or `pyproject.toml`.
Do not change `scripts/bootstrap_worktree.ps1`, shared guidance, or `CHANGELOG.md`.
Do not change production browser, environment-creation, health-check, or GitHub-account methods.

Use the existing standard library and test dependencies.
Do not introduce a source module, installer framework, lockfile, or automatic uv installation.
The caller-authorized correction in `plan.md` permits one nested installation-policy class and one test type alias.
All changed functions retain the existing size and parameter limits.
Keep new and changed functions within the constitution limits.
Add inline reasons and before-and-after action logs to touched code blocks.
Use ASCII and STE.
Never print credentials, source URLs with credentials, or environment dictionaries.

## Task format

Each task uses a checkbox, sequential ID, optional `[P]`, and an exact file path.
Story tasks also use `[US1]`, `[US2]`, `[US3]`, or `[US4]`.
`[P]` permits concurrent work only in different files after the stated prerequisites.

Check a task only after its delivery and required evidence exist.
Add `(delivered: path/to/file)` to the completed task.
Keep a blocked task open and record the reason in `.spec-context.json`.

## Phase 1: Setup

**Goal**: Confirm permission and the completed validation environment without changing shared state.
**Prerequisite**: Separate implementation authorization and the parent's environment-release confirmation.

- [X] T001 Record implementation permission, parent release, and interpreter version in `specs/3399-uv-bootstrap/.spec-context.json`. (delivered: specs/3399-uv-bootstrap/.spec-context.json)
- [X] T002 Record the focused baseline and protected file hashes in `specs/3399-uv-bootstrap/.spec-context.json`. (delivered: specs/3399-uv-bootstrap/.spec-context.json)

For T002, record the four-file baseline before any source or test edit.
Record the current branch and HEAD.
Record requirement-file hashes and the existing README reference.
Also preserve source snapshots for the protected methods.
Compare those method blocks again in T033.
If a baseline fails, record the failure without environment repair or unrelated edits.

## Phase 2: Foundational

**Goal**: Provide deterministic test substitutes for all four stories.
**Prerequisite**: Phase 1.

- [X] T003 Add the shared offline fixture under `TestInstallEnvironment.TestUvBootstrap` in `tests/unit/bootstrap/test_pip_index_probe.py`. Reject unexpected external actions. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)

Add `TestUvBootstrap` as the fifth child of `TestInstallEnvironment`.
Give it four nested groups and one shared fixture.
Use `TestCommands`, `TestIndexes`, `TestIsolation`, and `TestFailures`.
Keep each group at five direct children or fewer.
Do not add a top-level class, constant, test module, or package.

The fixture must substitute `subprocess.run`, executable discovery, sockets, and monotonic clocks.
Use temporary requirement files and `subprocess.CompletedProcess` results.
Substitute environment creation, deletion, browser downloads, Git operations, and GitHub requests when a case reaches them.
Record full argument lists, subprocess options, original environment objects, snapshots, and action order.
Retain each original dictionary so identity checks cannot pass through object-ID reuse.

Do not replace the installation methods under test with mocked results.
Exercise actual source parsing, environment mapping, installation dispatch, and `main()` decisions.
A pip configuration read is permitted when uv is selected.
A pip installation retry is not permitted.
Fail the test if any unplanned process or connection starts.

**Checkpoint**: All external actions have local substitutes.
No user-story source edit starts before this checkpoint.

## Phase 3: User Story 1 - Select the available installer (Priority: P1)

**Goal**: Select uv once, use pip only when uv is absent, and report completed installation times.

**Independent test**: Simulate uv presence and absence with both files.
Assert exact commands, one discovery, file order, worktree targeting, child settings, and controlled reports.
Start no real installer.

### Tests first

- [X] T004 [P] [US1] Add `test_installer_commands` in `tests/unit/bootstrap/test_pip_index_probe.py`. Assert exact uv and pip commands for both files. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T005 [P] [US1] Mock absent uv in `test_the_pip_install_gets_no_node_option` in `tests/unit/scripts/test_browser_download_certificates.py`. Keep both existing assertions. (delivered: tests/unit/scripts/test_browser_download_certificates.py)
- [X] T006 [US1] Add `test_uv_child_settings` and `test_separate_environments` in `tests/unit/bootstrap/test_pip_index_probe.py`. Assert child overrides and caller isolation. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T007 [US1] Add `test_success_reports` in `tests/unit/bootstrap/test_pip_index_probe.py`. Assert installer identity and one-decimal file and total durations. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T008 [US1] Record the US1 red run in `specs/3399-uv-bootstrap/.spec-context.json`. Use the exact US1 command in `quickstart.md`. (delivered: specs/3399-uv-bootstrap/.spec-context.json)

T004 and T005 can run together after T003.
Complete T004 before T006 and T007 because they edit the same file.
Complete all US1 tests before T008.

Put command and successful timing cases in `TestCommands`.
Put child-setting and dictionary cases in `TestIsolation`.
Use a resolved uv path with spaces.
Assert `shutil.which("uv")` runs once and its exact result serves both files.
Assert `requirements.txt` precedes `requirements-dev.txt`.
Assert one installation per present file and the ordered returned names.

Assert `check=False`, separate arguments, no shell, and visible installer output.
Assert no upgrade option, version probe, or automatic uv installation.
For pip, assert `PIP_RETRIES=1` and `PIP_TIMEOUT=15`.
For uv, assert `UV_LINK_MODE=copy`, `UV_NATIVE_TLS=1`, and `UV_SYSTEM_CERTS=1`.
Also assert child-only `UV_HTTP_RETRIES=1` and `UV_HTTP_TIMEOUT=15`.
Start with conflicting caller settings.
Preserve unrelated proxy, certificate, Node, and fake token values.
Change one child dictionary and verify that the other child and caller remain unchanged.
Control the clocks and assert ASCII reports without secret values.

### Implementation and integration

- [X] T009 [US1] Select uv once in `WorktreeBootstrapper.install_requirements()` in `scripts/bootstrap_worktree.py`. Pass the local selection to the installation policy. (delivered: scripts/bootstrap_worktree.py)
- [X] T010 [US1] Add installer-specific arguments and fresh child settings in `scripts/bootstrap_worktree.py`. Preserve zero-argument `_install_environment()` behavior. (delivered: scripts/bootstrap_worktree.py)
- [X] T011 [US1] Report installer choice and successful durations in `scripts/bootstrap_worktree.py`. State uv absence when selecting pip. (delivered: scripts/bootstrap_worktree.py)
- [X] T012 [US1] Record the US1 green run and focused regression results in `specs/3399-uv-bootstrap/.spec-context.json`. Repeat the recorded red command. (delivered: specs/3399-uv-bootstrap/.spec-context.json)

Use the command lists in the contract without string splitting.
Keep the selected installer local to one invocation.
Keep the existing pip configuration read before installation.
Use existing class members without adding a bootstrapper method.
Preserve the current nonzero-result stop behavior while adding uv dispatch.
The browser caller must not receive newly forced uv settings.

**Checkpoint**: US1 passes offline and the existing certificate tests retain their assertions.

## Phase 4: User Story 2 - Keep index decisions local to one run (Priority: P1)

**Goal**: Preserve working pip sources and make the public fallback exclusive and local to one run.

**Independent test**: Simulate source configuration and connection results for both installers.
Assert working mirrors, source precedence, exclusive fallback, probe counts, and fresh later invocations.
Use the same bootstrapper for repeated-run cases.

### Tests first

- [X] T013 [US2] Add working-source and configuration-snapshot cases in `tests/unit/bootstrap/test_pip_index_probe.py`. Assert primary and extra-source precedence for both installers. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T014 [US2] Add `test_public_override` in `tests/unit/bootstrap/test_pip_index_probe.py`. Assert exclusive public selection despite conflicting aliases and saved extras. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T015 [US2] Add `test_probe_outcomes` and `test_fresh_invocations` in `tests/unit/bootstrap/test_pip_index_probe.py`. Cover probe boundaries and successful or failed earlier runs. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T016 [US2] Record the US2 red run in `specs/3399-uv-bootstrap/.spec-context.json`. Use the exact US2 command in `quickstart.md`. (delivered: specs/3399-uv-bootstrap/.spec-context.json)

Use `test_working_sources` and `test_configuration_snapshot` in `TestIndexes`.
Put fresh-invocation cases in `TestIsolation`.
Test nonempty caller `PIP_*` values before `install.*`, then `global.*`.
Test primary and extra sources independently, including multiple ordered extra sources and quoted or empty settings.
Capture all four settings even when extras follow the first primary line.
Keep the parser's existing first-primary result for the probe.
Assert ordinary pip source and configuration behavior remains unchanged.

For public fallback, test both installers with conflicting `PIP_INDEX_URL`, `PIP_EXTRA_INDEX_URL`, and all four uv aliases.
The aliases are `UV_INDEX`, `UV_DEFAULT_INDEX`, `UV_INDEX_URL`, and `UV_EXTRA_INDEX_URL`.
Assert public-only mapping, removed extras, and child-only configuration controls.
For pip fallback, assert `PIP_CONFIG_FILE=os.devnull`, including Windows `nul`.
For uv, assert `UV_NO_CONFIG=1` and removed child `UV_CONFIG_FILE`.
Use saved-configuration sentinel files and verify their contents stay unchanged.

Test absent, empty, public, unreadable, and unusable configuration.
Simulate `OSError` and `subprocess.SubprocessError` during the configuration read.
Assert one configuration read and at most one three-second connection per invocation.
Do not add a per-file probe.
Change uv availability and dead-then-reachable outcomes between invocations.
Include a failed first invocation.
Assert the next invocation has no stale installer, source snapshot, or public override.
Verify earlier child dictionaries remain unchanged.
Use fake index credentials and assert that bootstrap reports do not disclose them.

### Implementation and integration

- [X] T017 [US2] Capture four source settings during the existing `PipIndexProbe` read in `scripts/bootstrap_worktree.py`. Keep probe decisions and safe reports. (delivered: scripts/bootstrap_worktree.py)
- [X] T018 [US2] Map effective sources and exclusive public overrides in `_install_environment()` in `scripts/bootstrap_worktree.py`. Suppress configuration only in installation children. (delivered: scripts/bootstrap_worktree.py)
- [X] T019 [US2] Reset prior overrides and create fresh probe state in `install_requirements()` in `scripts/bootstrap_worktree.py`. Preserve earlier child dictionaries. (delivered: scripts/bootstrap_worktree.py)
- [X] T020 [US2] Record the US2 green run and focused regression results in `specs/3399-uv-bootstrap/.spec-context.json`. Repeat the recorded red command. (delivered: specs/3399-uv-bootstrap/.spec-context.json)

Use the existing `PipIndexProbe` constructor and parser.
Do not add a configuration subprocess, connection rule, or method.
Normalize uv aliases before mapping authoritative pip sources.
Keep uv's default source-resolution policy.
Preserve ordinary pip configuration and zero-argument browser-helper behavior.
Never write pip or uv configuration.
Never force a public override when the existing probe does not select it.

**Checkpoint**: Working mirrors stay selected.
Public fallback cannot restore a failed mirror through an inherited or saved extra source.

## Phase 5: User Story 3 - Stop when an install fails (Priority: P1)

**Goal**: Report failure and stop without pip retry or later setup actions.

**Independent test**: Simulate nonzero results for either file with either installer.
Also simulate a discovered uv executable that raises `OSError`.
Exercise the real installation path and `main()` failure boundary.

### Tests first

- [X] T021 [US3] Add `test_nonzero_results` and `test_main_failure` in `tests/unit/bootstrap/test_pip_index_probe.py`. Parameterize both files and both installers. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T022 [US3] Add uv launch-error and failed-report cases in `tests/unit/bootstrap/test_pip_index_probe.py`. Assert failure context, duration, and no retry. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T023 [US3] Record the US3 red run in `specs/3399-uv-bootstrap/.spec-context.json`. Use the exact US3 command in `quickstart.md`. (delivered: specs/3399-uv-bootstrap/.spec-context.json)

Put these cases in `TestFailures`.
Use `test_uv_launch_failure` and `test_failed_reports` for T022.
Use controlled return codes and clocks.
Distinguish the one permitted pip configuration read from a forbidden pip installation.
After a first-file failure, assert no second-file installation.
After either-file failure, assert `main()` returns `1`.
Assert no health check, browser download, readiness report, Git credential configuration, or account request.
Do not mock `install_requirements()` or the policy installation method to force the failure.
Assert installer, failed file, and return code when available.
Assert duration after nonzero results and launch errors.
Assert no successful total or ready report after failure.

### Implementation and integration

- [X] T024 [US3] Add safe failure context and guaranteed attempt-duration reports in `InstallationPolicy.install()` in `scripts/bootstrap_worktree.py`. Raise without installer retry. (delivered: scripts/bootstrap_worktree.py)
- [X] T025 [US3] Record the US3 green run and focused regression results in `specs/3399-uv-bootstrap/.spec-context.json`. Repeat the recorded red command. (delivered: specs/3399-uv-bootstrap/.spec-context.json)

Keep the existing `main()` exception boundary.
Convert installer launch errors into contextual installation failures.
Use a `finally` path for attempt duration.
Do not change installers after discovery.
Append a successful file name only after a zero result.
Do not add later setup actions to an exception path.

**Checkpoint**: Every simulated installation failure produces exit status `1` and zero later setup actions.

## Phase 6: User Story 4 - Preserve existing setup compatibility (Priority: P2)

**Goal**: Preserve paths, file handling, setup options, browser trust, and account behavior.

**Independent test**: Simulate Windows, Linux, and macOS paths and every requirement-file presence combination.
Run successful setup and nonblocking browser-failure cases with external substitutes.
Run the existing browser and account regression files unchanged.

### Tests and integration

- [X] T026 [US4] Add `test_platform_paths` in `tests/unit/bootstrap/test_pip_index_probe.py`. Assert complete Windows and non-Windows interpreter arguments for both installers. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T027 [US4] Add missing-file and environment-option cases in `tests/unit/bootstrap/test_pip_index_probe.py`. Preserve returned names, empty-run duration, and `--recreate`. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T028 [US4] Add successful-main and browser-isolation cases in `tests/unit/bootstrap/test_pip_index_probe.py`. Preserve setup order, Node options, and account behavior. (delivered: tests/unit/bootstrap/test_pip_index_probe.py)
- [X] T029 [US4] Record compatibility and unchanged regression results in `specs/3399-uv-bootstrap/.spec-context.json`. Use both US4 commands in `quickstart.md`. (delivered: specs/3399-uv-bootstrap/.spec-context.json)

Put `test_platform_paths`, `test_missing_files`, and `test_environment_options` in `TestCommands`.
Use `test_successful_main` and `test_browser_isolation` in `TestIsolation`.
Use paths with spaces.
Assert `.venv/Scripts/python.exe` on Windows and `.venv/bin/python` elsewhere.
Use `PureWindowsPath` for literal Windows argument checks without accessing a Windows filesystem on macOS.
Simulate the Windows null configuration path for public pip fallback.

Parameterize both files, runtime-only, development-only, and neither with both installers.
Assert each present file runs once and each absent file is skipped.
Assert an empty run returns `[]`, starts no package install, and reports a total duration.
Test the existing parser, reuse path, and `--recreate` path through local creation and deletion substitutes.
Assert `venv.EnvBuilder(with_pip=True, upgrade_deps=False)` remains unchanged.
Verify requirement-file hashes against T002 without changing their contents.

After successful installation, assert this order:

```text
create_environment
install_requirements
check_environment_health
install_browser_driver
report_result
configure_git_username
warn_on_mismatch
```

Exercise browser success and nonblocking browser failure.
Assert the readiness report receives the correct browser result.
Preserve caller `NODE_OPTIONS` and add `--use-system-ca` once.
Assert pip and browser children receive no newly forced uv copy, TLS, or configuration settings.
If the caller supplied uv settings, preserve those original values in the browser child.
Assert installation-only `PIP_CONFIG_FILE=os.devnull` does not reach that child.
Preserve the browser command and repair guidance.

Assert the expected account remains `jmorrison-juniper`.
Exercise credential-variable warnings and repository username commands through local subprocess substitutes.
Start no real Git or GitHub operation.
Keep these regression files unchanged:

- `tests/unit/bootstrap/test_github_account_checker.py`
- `tests/unit/scripts/test_browser_driver_bootstrap.py`

Existing compatibility assertions can remain green before and after the feature edits.
Do not change correct production behavior to force a test failure.
New feature-dependent assertions must retain the earlier red evidence.

**Checkpoint**: All four stories pass without network calls or real setup actions.

## Phase 7: Polish and cross-cutting concerns

**Goal**: Complete the single setup page, release note, quality evidence, and final scope check.
**Prerequisite**: All four story checkpoints.

- [X] T030 [P] Update bootstrap behavior in `documentation/development-setup.md`. Explain optional uv, local sources, child settings, timing, and failure without retry. (delivered: documentation/development-setup.md)
- [X] T031 [P] Add one release fragment in `changelog.d/issue-3399-uv-bootstrap.md`. Use one heading, typed bullets, and issue #3399. (delivered: changelog.d/issue-3399-uv-bootstrap.md)
- [X] T032 Run the exact validation commands in `specs/3399-uv-bootstrap/quickstart.md`. Record results in `specs/3399-uv-bootstrap/.spec-context.json`. (delivered: specs/3399-uv-bootstrap/.spec-context.json)
- [X] T033 Audit protected files and the six-file implementation scope in `specs/3399-uv-bootstrap/.spec-context.json`. Report failures without unrelated changes. (delivered: specs/3399-uv-bootstrap/.spec-context.json)

T030 and T031 can run together.
Keep the current entry points and Python 3.13 requirement in the setup page.
Explain copy mode, system certificate trust, exclusive public fallback, and preserved working mirrors.
State that only absent uv selects pip.
State that a failed uv install stops setup without pip retry.
Preserve the browser repair and account guidance.
Do not claim a fixed speed improvement.
Keep the existing README reference and its one-sentence installer summary.

The release fragment has no version stamp.
Do not add another fragment or edit `CHANGELOG.md`.
T032 must use `.venv/bin/python`, the repository test-quality configuration, and the repository baseline.
Require at least 80% coverage of changed behavior and retain the configured 90% report threshold.
Do not lower thresholds, change exclusions, disable quality rules, or update the baseline.
Record each required command's exit status and checked-file or executed-case count.
An unavailable tool, skipped case, empty scan, or unrelated baseline failure is not a pass.
Do not install a missing tool.

## Dependencies and completion order

### Actual prerequisites

| Work | Prerequisite |
| --- | --- |
| T001 | Implementation permission and the parent's environment release. |
| T002 | T001. |
| T003 | T002. |
| US1 | T003, then tests before source edits, then green evidence. |
| US2 and US3 | US1 installer dispatch. Keep their edits serial because they share files. |
| US4 | Completed US1, US2, and US3 behavior. |
| T030 and T031 | US4 checkpoint. |
| T032 | T030 and T031. |
| T033 | T032 results and the T002 protected snapshots. |

```text
Permission and parent release -> Setup -> Foundation -> US1
                                                       |-> US2
                                                       |-> US3
                                                US2 + US3 -> US4 -> Polish

Write order: US1 -> US2 -> US3 -> US4
```

US2 and US3 do not require each other's logic.
They share `scripts/bootstrap_worktree.py` and the bootstrap test file.
The write order prevents conflicting edits.
Each story has its own test selection and acceptance observations.
Do not treat independent test selections as permission for concurrent writes to the same file.

### Within each story

Write the tests before the related source changes.
Record a real assertion failure for new behavior.
An interpreter error, missing package, or accidental external call is not red evidence.
Repeat the same command after implementation.
Run the complete focused suite after every story.
Keep all compatibility assertions intact.

## Parallel examples

### US1

```text
Worker A: T004, tests/unit/bootstrap/test_pip_index_probe.py
Worker B: T005, tests/unit/scripts/test_browser_download_certificates.py
Wait for both workers before T006 through T008.
Do not start T009 before the red evidence exists.
```

### US2

```text
Write sequence: T013 -> T014 -> T015 -> T016 -> T017 -> T018 -> T019 -> T020
Concurrent write tasks: none.
Both source and test changes use shared files.
```

### US3

```text
Write sequence: T021 -> T022 -> T023 -> T024 -> T025
Concurrent write tasks: none.
Failure evidence precedes the source edit.
```

### US4

```text
Write sequence: T026 -> T027 -> T028
After those writes, run the US4 new-case and unchanged-regression commands in separate processes.
Neither command starts an installer or writes source.
One worker records both results in T029.
```

The other write pair is T030 with T031.
No other task carries `[P]`.
Do not run concurrent tests while dependency restoration is active.

## Requirement coverage

| Story | Requirements | Task evidence |
| --- | --- | --- |
| US1 | FR-001 through FR-006, FR-011, FR-014, FR-015, FR-020 | T004 through T012. |
| US2 | FR-006 through FR-010, FR-015, FR-020 | T013 through T020. |
| US3 | FR-012 through FR-015, FR-020 | T021 through T025. |
| US4 | FR-004, FR-006, FR-014, FR-016 through FR-020 | T026 through T029. |
| Shared validation | FR-015, FR-016, FR-020 | T002, T003, T030 through T033. |

The run, requirement-file, index-decision, and child-environment entities remain local values.
No entity needs a new production model or persistent record.
The command and subprocess contracts map to the story phases above.

## Implementation strategy

### Minimum viable product

Complete Setup, Foundation, and US1.
Use the US1 test selection as the first offline demonstration.
US1 alone is not a complete issue #3399 delivery.
The remaining P1 source-safety and failure stories must also pass.
US4 must pass before the final completion claim.
No deployment or release operation belongs to these tasks.

### Incremental delivery

Add installer selection first.
Add source preservation and exclusive fallback next.
Add complete failure reports next.
Verify compatibility last.
After each increment, retain the earlier tests and run the focused suite.
Complete documentation and the unique fragment only within separately authorized implementation.

### Summary

| Phase | Task count |
| --- | --- |
| Setup | 2 |
| Foundation | 1 |
| US1 | 9 |
| US2 | 8 |
| US3 | 5 |
| US4 | 4 |
| Polish | 4 |
| **Total** | **33** |

Four tasks carry `[P]`.
They form two safe write pairs.
All 33 tasks remain unchecked until authorized implementation supplies their evidence.
