# Feature Specification: Netcool Runbook Smoke Package Conformance

**Feature Branch**: `chore/4945-netcool-runbook-smoke-conformance`

**Created**: 2026-11-26

**Status**: Draft

**Input**: GitHub issue #4945, "Refactor: conform the netcool runbook smoke package to the constitution and the CI gates". The issue is OPEN and carries the labels `refactor`, `tests`, and `in-progress`. The owner delegated the decisions on 2026-11-26.

## Clarifications

### Session 2026-11-26

- Q: Which repair does the owner choose? A: Restructure the package into sub-packages. Each sub-package holds five children or fewer. Public names change their import path. No alias and no compatibility shim exist. Rewrite the weak comments. Add steps to the existing CI gates for the package path. Add no CI job.
- Q: Does this change amend the constitution? A: No. Issue #4937 closed with the written Complexity Tracking exception. Issue #4944 tracks the folder debt of `scripts/` and `tests/unit/scripts/`.
- Q: How does the structure guard count a code line? A: A code line is a non-blank line. It is not a comment-only line and not a docstring line. The limit is 25 code lines per function. Research decision D-1 records the reason.
- Q: How does the structure guard count a block? A: Each block holds five statements or fewer. A docstring is not a statement. Research decision D-2 records the reason.
- Q: Where do the new guards live? A: Existing guard files are extended. No file joins `tests/guardrails/`, which holds 79 children. Research decisions D-9 and D-10 record the reason.
- Q: Does the change need a changelog fragment? A: Yes. The constitution requires one fragment for each change. Research decision D-16 records the reason.
- Q: Does CI measure the package coverage? A: No. CI measures `src` only. The package coverage is measured locally and recorded in the pull request body. Research decision D-14 records the reason.
- Q: Does the change add tests to new test files? A: No. The test folder already holds five children. New tests go into the existing modules. Research decision D-11 records the reason.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Maintainer Runs the Structure Guard (Priority: P1)

A maintainer runs the structure guard on the package. The guard reports zero violations of the function, class, module, and directory limits.

**Why this priority**: Principle I of the constitution forbids the fourteen function-level violations. New code cannot enter the full modules until the restructure completes.

**Independent Test**: Run `python -m pytest tests/guardrails/test_nested_package_structure.py -q`. The guard prints the count of examined functions, classes, modules, and directories. The guard passes with zero violations.

**Acceptance Scenarios**:

1. **Given** the restructured package, **When** the guard runs, **Then** it reports zero violations and prints each examined count.
2. **Given** a function with six statements in one block, **When** the guard runs, **Then** it fails and names the file, the function, and the limit.

---

### User Story 2 - Reviewer Sees the CI Gates Examine the Package (Priority: P1)

A reviewer opens a pull request. The Ruff, mypy, Bandit, radon, Vulture, pydocstyle, and Interrogate steps name the package path. Each step prints the count of files it examined. A step fails when that count is zero.

**Why this priority**: The current gates skip the package. A defect can merge with no red gate.

**Independent Test**: Run the gate guard and the injected-violation tests. At least two new steps fail on an injected violation.

**Acceptance Scenarios**:

1. **Given** the changed `ci.yml`, **When** the gate guard runs, **Then** it confirms the package path in each of the seven gates.
2. **Given** an injected Ruff violation in the package, **When** the Ruff step runs, **Then** the step fails.

---

### User Story 3 - Junior Engineer Reads Useful Comments (Priority: P2)

An engineer reads any executable line of the package. The comment states the cause and the purpose of the line. A seeded sample of 40 comment lines passes the rule for at least 36 lines.

**Why this priority**: Junior NOC engineers maintain the package. Principle VI makes each comment a required quality gate.

**Independent Test**: Run the seeded sample procedure in `design/quickstart.md`. Count the lines that pass.

**Acceptance Scenarios**:

1. **Given** the rewritten package, **When** the comment check runs, **Then** each first physical line of a statement carries an inline comment.
2. **Given** the seeded sample, **When** the reviewer grades 40 lines, **Then** at least 36 lines state a cause and a purpose.

---

### User Story 4 - Operator Runs the Smoke Test and Sees the Same Result (Priority: P1)

An operator runs `python -m scripts.netcool_runbook_smoke` with the same options as before. The console lines and the evidence keys keep the same content. The runbook command path needs no text change.

**Why this priority**: The restructure must not change operator-visible behavior.

**Independent Test**: Run the fixed fake-session command test. Compare the console lines and the evidence keys with the baseline that T002 records.

**Acceptance Scenarios**:

1. **Given** the same fake session and options, **When** the command runs before and after the change, **Then** the console lines and the evidence keys match.
2. **Given** the runbook command path, **When** the operator runs it, **Then** the command starts the package without an error.

### Edge Cases

- A tool skips an explicit path. Ruff and Bandit can skip a path that the configuration excludes. The count step fails at zero, so the gate cannot pass in silence.
- A new import creates a cycle. The dependency direction in `plan.md` blocks the cycle. An import smoke test imports every new module.
- A logger name changes after a move. The log setup applies to the package loggers by prefix. A test proves the prefix rule.
- A test module reaches the limit of five children. New tests go into the existing modules, so the folder keeps five children.
- A mypy error exists in the current package. The change repairs the error and adds no suppression comment.
- The package coverage falls under 95 percent. The change adds tests before the merge.
- A helper needs a sixth method in a full class. The helper moves to a new class in the same sub-package.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each function of the package MUST hold 25 code lines or fewer. Docstring lines, comment-only lines, and blank lines are not code lines.
- **FR-002**: Each function of the package MUST hold five parameters or fewer. The parameters `self` and `cls` are not counted.
- **FR-003**: Each function body MUST hold five logical blocks or fewer. Each block MUST hold five statements or fewer.
- **FR-004**: Each class of the package MUST hold five methods or fewer.
- **FR-005**: Each module of the package MUST hold five top-level names or fewer. The count includes the module logger.
- **FR-006**: Each directory of the package MUST hold five children or fewer. A child is a module, excluding `__init__.py`, or a sub-package directory.
- **FR-007**: The fourteen functions that the issue names MUST meet FR-001 to FR-003. The change MUST also repair every other function that breaks a limit.
- **FR-008**: The package MUST restructure into the sub-packages that `plan.md` names. Each `__init__.py` MUST hold no re-export, no alias, and no compatibility shim.
- **FR-009**: Each public name that moves MUST change its import path in every call site and every test in the same change. The old module files MUST be deleted.
- **FR-010**: The entry point MUST remain `scripts/netcool_runbook_smoke/__main__.py`. The command `python -m scripts.netcool_runbook_smoke` MUST keep working.
- **FR-011**: Each executable statement MUST carry an inline comment on its first physical line. The comment MUST state the cause and the purpose of the statement.
- **FR-012**: A random sample of 40 comment lines, drawn with seed 4945, MUST contain at least 36 lines that state a cause and a purpose.
- **FR-013**: Each action in new or touched code MUST log an info message before the action and a debug message after it. An exception MUST log its full context.
- **FR-014**: Ruff, mypy in strict mode, Bandit, radon, Vulture, pydocstyle, and Interrogate MUST each name the package path in `ci.yml`.
- **FR-015**: Each new or extended gate step MUST print the count of files that it examined. The step MUST fail when the count is zero.
- **FR-016**: The gate guard MUST fail when a gate drops the package path or drops its count step.
- **FR-017**: At least two new gate steps MUST fail on an injected violation. A test MUST prove each failure.
- **FR-018**: The change MUST add no CI job. The job count stays at the value that `.github/copilot-instructions.md` records.
- **FR-019**: The package MUST pass mypy in strict mode. No suppression comment and no relaxing override MUST be added to pass a gate.
- **FR-020**: The package coverage MUST be 95 percent or above. The command in `design/quickstart.md` measures it.
- **FR-021**: The unit tests MUST pass. The collected count before the change MUST equal the collected count after the change.
- **FR-022**: The console lines and the evidence keys MUST match the baseline for the fixed fake-session run.
- **FR-023**: The package MUST call the Mist REST API through mistapi methods only. Evidence MUST stay under `test-artifacts/`. No product output MUST go to `data/`.
- **FR-024**: The change MUST add one changelog fragment named `changelog.d/issue-4945-netcool-runbook-smoke-conformance.md`.
- **FR-025**: The pull request body MUST contain `Closes #4945`, the local gate results, the package coverage value, and the symbol-diff result for each changed file. It MUST also state the count of removed lines that are not comments.

### Mist Cloud Transport Requirements *(include if feature uses Mist Cloud)*

- The package uses one mistapi REST method, `APISession.mist_get`. The method is defined at `.venv\Lib\site-packages\mistapi\__api_request.py` line 260. The package calls it at `scripts/netcool_runbook_smoke/client.py` line 496.
- The package builds its session with `mistapi.APISession`. The default is set at `scripts/netcool_runbook_smoke/__main__.py` line 587.
- The package owns no WebSocket transport. The constitution exception for an owned transport does not apply.
- The package imports `urllib.parse` for link parsing only, at `scripts/netcool_runbook_smoke/client.py` line 25. No direct HTTP request exists.
- The installed SDK is `mistapi` 0.64.1. The pin `mistapi>=0.64.0,<0.65` allows this version.

### Key Entities *(include if feature involves data)*

- **Function Limit Measure**: The count of code lines, parameters, body blocks, and statements in each block of one function. It is defined in `research.md` decisions D-1 and D-2.
- **Sub-Package**: A directory of the package that holds an `__init__.py` file and five modules or fewer.
- **Module Name Set**: The top-level names of one module. The set holds classes, functions, constants, and the module logger.
- **CI Gate Step**: One step in `ci.yml` that runs a gate on the package path and prints the examined count.
- **Structure Guard**: The pytest test that measures FR-001 to FR-006 and prints the examined counts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The structure guard reports zero violations for the package. The guard covers FR-001 to FR-006.
- **SC-002**: The gate guard and the injected-violation tests pass. The tests cover FR-014 to FR-017.
- **SC-003**: The seven gates print a file count above zero for the package in the remote CI run.
- **SC-004**: The seeded comment sample passes at least 36 of 40 lines.
- **SC-005**: The collected test count before and after the change is equal, and all collected tests pass.
- **SC-006**: The package coverage is 95 percent or above.
- **SC-007**: The console lines and the evidence keys match the baseline for the fixed fake-session run.
- **SC-008**: The CI job count is unchanged.

## Assumptions

- The owner decisions in the issue body apply without change. The owner delegated them on 2026-11-26.
- The local `.venv` uses Python 3.15 and the `mistapi` 0.64.1 package. The pin `mistapi>=0.64.0,<0.65` allows this version.
- The Windows development host runs the local gates. The remote CI run runs the same gates on Ubuntu.
- The runbook file `documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md` keeps its command text.
- The OpenAPI JSON file `documentation/mist-api-openapi31json.json` stays available at the default path.
- No Mist endpoint, request parameter, or response field changes in this change.

## Out of Scope

- The runbook text. Only a module path change in a command could require a text change, and this plan avoids that change.
- A constitution amendment. Issue #4937 closed with the written exception.
- The folder debt of `scripts/` and `tests/unit/scripts/`. Issue #4944 tracks that debt.
- A new CI job, or a package coverage gate in CI.
- Changes to the other scripts under `scripts/`.
- Changes to the Mist API behavior, the operations, or the menu of MistHelper.
