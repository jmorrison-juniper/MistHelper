# Feature Specification: Bandit Severity Gate Hardening

**Feature Branch**: `security/889-bandit-ll`

**GitHub Issue**: [#889](https://github.com/jmorrison-juniper/MistHelper/issues/889) — "security: drop the bandit -ll severity suppression in ci.yml"

**Created**: 2026-07-28

**Status**: Draft

**Input**: Remove the `-ll` severity suppression from the bandit step in `.github/workflows/ci.yml`. Triage every finding that the removal makes visible. Apply the project rule of fix over suppress.

---

## Background

The CI security gate runs the following command.

```bash
bandit -c pyproject.toml -r . -ll
```

The `-ll` flag hides every finding below MEDIUM severity. The flag removes the finding from the report and from the exit code. A LOW severity finding therefore cannot fail the build. The gate reports success while real defects stay hidden.

The configuration drift part of issue #889 is already closed. The command already reads `-c pyproject.toml` and already scans `-r .`. Issue [#881](https://github.com/jmorrison-juniper/MistHelper/issues/881) delivered that part. This specification covers the `-ll` flag only.

### Measured baseline

A maintainer ran `bandit -c pyproject.toml -r . -f json` with no severity flag. The maintainer then compared every result against `git ls-files`.

| Measurement | Count |
| - | - |
| Findings on a local Windows checkout | 105 |
| Findings in files that git tracks | 96 |
| Findings that CI sees | 54 |
| Findings above LOW severity in tracked code | 0 |

Two sources of local noise exist. Both stay outside the scope of this work.

1. The scan reports 42 findings under `tools/test_quality_analyzer/fixtures/`. The `[tool.bandit]` table already lists that path in `exclude_dirs`. CI runs on Linux and applies the exclusion. A Windows run does not apply the exclusion, because the configured path uses a forward slash and a Windows scan reports a backslash.
2. The scan reports 9 findings in files that git does not track. One of them is the only MEDIUM finding in the whole run. It sits at `mist-ops-platform/src/shared/config/settings.py:41`. Line 244 of `.gitignore` ignores that file through the `config/` pattern. The line carries a ruff annotation of `# noqa: S104`, which bandit does not read.

### The 54 findings in scope, by rule

| Rule | Name | Count |
| - | - | - |
| B101 | assert_used | 18 |
| B105 | hardcoded_password_string | 11 |
| B603 | subprocess_without_shell_equals_true | 9 |
| B110 | try_except_pass | 7 |
| B404 | blacklist (subprocess import) | 4 |
| B607 | start_process_with_partial_path | 3 |
| B107 | hardcoded_password_default | 1 |
| B606 | start_process_with_no_shell | 1 |

### The 54 findings in scope, by file

| File | Count |
| - | - |
| starlink_dashboard.py | 10 |
| src/export/data_exporter.py | 5 |
| src/firmware/firmware_manager.py | 5 |
| src/maps/plotly_map_templates.py | 5 |
| src/firmware/site_auto_upgrade.py | 3 |
| src/maps/plotly_map_figure_builder.py | 3 |
| src/utils/zscaler_probe.py | 3 |
| tools/compliance_analyzer/engine.py | 3 |
| mist-ops-platform/src/api/routes/health.py | 2 |
| src/gateway/wan_probe_device_override_manager.py | 2 |
| src/site/address_audit/ui_geocoder.py | 2 |
| src/wan_vpn_builder.py | 2 |
| mist-ops-platform/src/shared/mist/session.py | 1 |
| mist-ops-platform/src/shared/services/notification.py | 1 |
| src/auth/interactive/login_orchestrator.py | 1 |
| src/db/redis_writer.py | 1 |
| src/export/site_insights/device_metric_operation.py | 1 |
| src/gateway/_wan2_variable_device.py | 1 |
| src/maps/_flask_viewer.py | 1 |
| src/utils/logger_utils.py | 1 |
| tools/ste_linter/parsing/wordcount.py | 1 |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clear every LOW severity finding from the tracked code (Priority: P1)

A security reviewer wants the tracked code to hold zero bandit findings at any severity. The reviewer runs the scan with no severity flag. The reviewer reads a clean report. Each former finding now carries either a code fix or a suppression comment that states a verified reason.

**Why this priority**: This story removes the defects. The gate change in User Story 2 fails the build until this story is complete. This story delivers value on its own, because a fixed `assert` still protects the user under `python -O`, even before CI enforces the state.

**Independent Test**: A reviewer runs `bandit -c pyproject.toml -r .` on a Linux checkout of the branch. The command exits with code 0. The report lists zero findings.

**Acceptance Scenarios**:

1. **Given** the branch holds the completed triage, **When** a reviewer runs `bandit -c pyproject.toml -r .` with no severity flag on Linux, **Then** the command exits with code 0 and reports zero findings.
2. **Given** a module that used an `assert` to guard runtime behavior, **When** a reviewer runs that module under `python -O`, **Then** the guard still rejects the invalid input and raises a clear error.
3. **Given** a finding that the team accepts as safe, **When** a reviewer reads the source line, **Then** the reviewer finds a suppression comment that names the rule and states the reason.
4. **Given** the full quality gate suite, **When** CI runs the suite on the branch, **Then** every gate stays green and the unit test suite keeps its pass count.

---

### User Story 2 - Fail the build on any bandit finding (Priority: P2)

A maintainer wants CI to stop a pull request that adds a security finding at any severity. The maintainer removes the `-ll` flag from the bandit step. The gate then treats a LOW finding as a failure.

**Why this priority**: This story locks in the clean state that User Story 1 creates. The story cannot merge before User Story 1 completes, because the gate would fail on the existing findings.

**Independent Test**: A reviewer reads the bandit step in `.github/workflows/ci.yml` and finds no severity flag. A reviewer then adds a temporary LOW severity finding to a tracked file and confirms that the job fails.

**Acceptance Scenarios**:

1. **Given** the updated workflow file, **When** a reviewer searches the bandit step for `-ll`, **Then** the search returns no match.
2. **Given** the updated workflow file, **When** CI runs the bandit job on the clean branch, **Then** the job succeeds inside the existing 5 minute timeout.
3. **Given** a pull request that adds a LOW severity finding to a tracked file, **When** CI runs the bandit job, **Then** the job fails and the log names the rule and the file.
4. **Given** the updated workflow file, **When** a reviewer reads the step comment, **Then** the comment states that the gate fails on any severity.

---

### User Story 3 - Understand each accepted finding without asking the author (Priority: P3)

A future maintainer reads a suppression comment. The maintainer learns the rule identifier and the reason the team accepted the finding. The maintainer does not need to contact the original author.

**Why this priority**: This story protects the value of the first two stories over time. An unexplained suppression turns into a hidden defect after the author leaves the project.

**Independent Test**: A reviewer lists every suppression comment that this work adds. Each comment names a rule identifier and states a reason in one sentence.

**Acceptance Scenarios**:

1. **Given** a suppression comment that this work adds, **When** a reviewer reads the line, **Then** the comment names the bandit rule identifier.
2. **Given** a suppression comment that this work adds, **When** a reviewer reads the line, **Then** the comment states why the finding is safe in this specific call site.
3. **Given** a suppression comment that this work adds, **When** a reviewer applies the Simplified Technical English rules, **Then** the comment passes the rules.

---

### Edge Cases

- A developer runs the scan on Windows. The scan reports 105 findings, because the Windows path separator defeats the `exclude_dirs` entry for the analyzer fixtures. The developer must compare the result against the CI baseline of 54 findings and must ignore the fixture findings.
- A developer runs the scan on a working tree that holds untracked files. The scan reports findings that CI never sees. The developer must compare each finding against `git ls-files`.
- A bandit release adds a new rule after this work merges. The gate then fails on the next run. The team must triage the new finding. The team must not restore a severity filter.
- A B110 fix overlaps issue [#1709](https://github.com/jmorrison-juniper/MistHelper/issues/1709), which asks the same question about the broad `except` blocks in `MistHelper.py`. The two efforts must not change the same lines at the same time.
- A hardcoded password finding names a real secret. The team must move the value to the environment and must rotate the secret. The team must not add a suppression comment.
- A reviewer disagrees with a proposed suppression. The pull request must hold the fix instead of the suppression, because the project rule prefers a fix.

---

## Requirements *(mandatory)*

### Gate requirements

- **FR-001**: The CI security gate MUST fail when the bandit scan reports one or more findings at any severity.
- **FR-002**: The bandit command in `.github/workflows/ci.yml` MUST NOT contain the `-ll` flag.
- **FR-003**: The bandit command MUST NOT contain any other severity filter or confidence filter.
- **FR-004**: The bandit command MUST keep the existing configuration source `-c pyproject.toml` and the existing scan root `-r .`.
- **FR-005**: The comment above the bandit step MUST state that the gate fails on any severity.

### Triage requirements

- **FR-006**: Each of the 54 findings in scope MUST receive one recorded decision. The decision MUST be a code fix, a refactor that removes the pattern, or a suppression comment.
- **FR-007**: A suppression comment MUST name the bandit rule identifier and MUST state the reason the finding is safe at that call site. A bare suppression is forbidden.
- **FR-008**: The team MUST select the decision in this order. First, fix the root cause. Second, refactor to remove the pattern. Third, add a suppression comment for a verified false positive.
- **FR-009**: An `assert` statement that guards runtime behavior MUST become an explicit check that raises an error. The reason is that the Python interpreter removes an `assert` under the `-O` flag.
- **FR-010**: An `assert` statement that only narrows a type for the type checker MAY keep a suppression comment. The comment MUST state that the statement carries no runtime duty.
- **FR-011**: A `try`/`except`/`pass` block MUST narrow the exception type and MUST log the event, or MUST keep a suppression comment that states why silence is correct.
- **FR-012**: A subprocess call MUST pass a list of arguments and MUST NOT request a shell.
- **FR-013**: A subprocess call MUST name an absolute path or a resolved executable path, or MUST keep a suppression comment that states why the partial path is safe.
- **FR-014**: A hardcoded password finding MUST show that the value is not a secret, or the value MUST move to the environment.
- **FR-015**: An `import subprocess` finding MUST follow the model in `MistHelper.py` at line 47, which states the dependency injection seam and names the runner class.
- **FR-016**: The team MUST coordinate the B110 decisions with issue #1709 to prevent a duplicate change or a conflicting change.

### Quality requirements

- **FR-017**: Every changed Python line MUST carry an inline comment that explains why the line exists.
- **FR-018**: Every meaningful action that this work adds MUST log before the action and after the action.
- **FR-019**: All prose, all code comments, and all commit text MUST follow the Simplified Technical English guide at `documentation/ASD-STE100_writing-guide.md`.
- **FR-020**: The change MUST NOT alter the behavior that the test suite covers. Every existing quality gate MUST stay green.

### Key Entities

- **Bandit finding**: One report entry. It holds a rule identifier, a severity, a confidence, a file path, and a line number.
- **Triage decision**: The recorded outcome for one finding. The value is a fix, a refactor, or a suppression.
- **Suppression comment**: A source comment that hides one finding. It MUST name the rule identifier and MUST state the reason.

---

## Per-rule triage policy

The table states the default decision for each rule. A reviewer may choose a different decision for one finding. The reviewer must then record the reason in the pull request.

| Rule | Count | Default decision | Escalate when |
| - | - | - | - |
| B101 assert_used | 18 | Replace the `assert` with an explicit check that raises `RuntimeError` or `ValueError`. `MistHelper.py` already applies this pattern. | The `assert` only narrows a type for the type checker. Then add a suppression comment that states the absence of a runtime duty. |
| B105 hardcoded_password_string | 11 | Confirm that the value is a field name, a sentinel, or a placeholder. Add a suppression comment that names the value and states the role. `src/ssh/config/env_loader.py` line 67 shows the model. | The value is a real credential. Then move the value to the environment and rotate the credential. |
| B603 subprocess_without_shell_equals_true | 9 | Confirm that the call passes a list of arguments and that no user input reaches the list without validation. Add a suppression comment that states the source of each argument. | Any argument comes from user input without validation. Then validate the input first. |
| B110 try_except_pass | 7 | Narrow the exception type and log the event at debug level. | The silence is correct, such as a best effort cleanup. Then add a suppression comment that states the reason. Coordinate with issue #1709. |
| B404 blacklist (subprocess import) | 4 | Add a suppression comment in the style of `MistHelper.py` line 47. State the seam and name the runner class. | The module calls `subprocess` directly. Then route the call through the shared runner first. |
| B607 start_process_with_partial_path | 3 | Resolve the executable with `shutil.which` and pass the resolved path. | The tool must stay on the caller path. Then add a suppression comment that states the reason. |
| B107 hardcoded_password_default | 1 | Replace the default value with `None` and read the value from the environment. | The default is a documented placeholder. Then add a suppression comment. |
| B606 start_process_with_no_shell | 1 | Confirm that the call passes a list of arguments. Add a suppression comment that states the source of each argument. | Any argument comes from user input without validation. Then validate the input first. |

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A bandit scan of the branch on Linux, with the project configuration and with no severity flag, reports zero findings and exits with code 0.
- **SC-002**: A text search of the bandit step in `.github/workflows/ci.yml` returns zero matches for `-ll`.
- **SC-003**: A pull request that adds one LOW severity finding to a tracked file fails the security gate. The gate reports the failure inside the existing 5 minute job timeout.
- **SC-004**: The count of findings without a recorded decision is zero. All 54 findings in scope hold a decision.
- **SC-005**: The count of bare suppression comments that this work adds is zero. Every added suppression names a rule identifier and states a reason.
- **SC-006**: The count of `assert` statements that guard runtime behavior in the files in scope is zero. Every affected module keeps the same guard behavior under the `python -O` flag.
- **SC-007**: Every existing quality gate stays green. The unit test suite keeps its pass count and adds no new failure.
- **SC-008**: A reviewer who did not write the change reads any added suppression comment and states the reason in under one minute, without help from the author.
- **SC-009**: The change touches zero findings in files that git does not track and zero findings under `tools/test_quality_analyzer/fixtures/`.

---

## Non-Goals

- Do not change the `targets` list or the `exclude_dirs` list in the `[tool.bandit]` table. Issue #881 covered that scope and the team closed it.
- Do not replace bandit with another static analysis tool.
- Do not fix the 9 findings in files that git does not track. This includes the MEDIUM finding at `mist-ops-platform/src/shared/config/settings.py:41`.
- Do not fix the 42 findings under `tools/test_quality_analyzer/fixtures/`. The analyzer needs that code to stay unsafe.
- Do not repeat the configuration drift fix. The command already uses `-c pyproject.toml -r .`.
- Do not add a confidence filter as a replacement for the severity filter.
- Do not resolve issue #1709 in full. Change only the B110 findings that this scope lists.
- Do not change the Windows path behavior of `exclude_dirs`. Track that separately if a developer needs a clean local run.

---

## Assumptions

- The CI runner uses Linux. The forward slash in the `exclude_dirs` entry therefore matches, and CI sees 54 findings.
- The baseline of 54 findings reflects the current `main` branch. New commits may change the count. The implementer must measure the count again before the first fix.
- The pinned bandit version stays the same during this work. A version change may add or remove a rule and may change the count.
- A LOW severity finding carries real signal for this project. The team accepts the cost of a stricter gate.
- The 11 B105 findings and the 1 B107 finding name field names, sentinels, or placeholders. The implementer must confirm each value before the implementer adds a suppression comment.
- The existing 79 suppression comments in 38 files stay valid. This work does not review them.
- The team resolves issue #1709 after this work or in coordination with it.

---

## Dependencies

- Issue #1709 overlaps this work on the 7 B110 findings. The two efforts must not edit the same lines at the same time.
- The Simplified Technical English guide at `documentation/ASD-STE100_writing-guide.md` governs all prose in this work.
- The suppression comment style follows the existing model in `MistHelper.py` at line 47 and at line 904.
