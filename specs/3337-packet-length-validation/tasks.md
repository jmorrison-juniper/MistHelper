# Tasks: Packet Length Validation

**Issue**: [#3337](https://github.com/jmorrison-juniper/MistHelper/issues/3337)

**Branch**: `jmorrison-juniper-packet-length-validation`

**Feature directory**: `SPECIFY_FEATURE_DIRECTORY=specs/3337-packet-length-validation`

**Input**: [spec.md](spec.md), [plan.md](plan.md), and the existing documents under [design/](design/).

**Prerequisites**: [design/research.md](design/research.md), [design/data-model.md](design/data-model.md), [design/contracts/prompt-limits.md](design/contracts/prompt-limits.md), and [design/quickstart.md](design/quickstart.md).

**Tests**: The specification requires offline behavior tests and measured guard coverage.

**Organization**: Tasks use the three user stories from `spec.md`.
US1 owns the shared test matrix because all stories use two functions in one existing test file.
US2 and US3 reuse that matrix without another test file or helper.

## Current Documentation Boundary

This phase updates existing documents under `specs/3337-packet-length-validation/` only.
The parent owns source, tests, release notes, gate execution, and final gate counts.
Implementation is in progress.
The parent supplied verified final local results for T001 through T029.
Checked tasks record that supplied evidence, not gate execution by the documentation owner.
Cross-artifact analysis and T030 are complete.
The verified local implementation commit is `e74a996777d9fffb163c1be904f497132cbb7081`.
T031 through T038 remain blocked.
The normal requirements audit failed before scanning.
The documented local audit alternative completed without known vulnerabilities in the audited packages.

Do not change the branch or shared `.specify` configuration.
Do not read source or tests during documentation alignment.
Do not edit source, tests, dependencies, configuration, or release notes.
Do not execute tests or gates.
Do not commit, push, create a pull request, start another agent, or contact Mist cloud.

The optional Git commit hooks remain skipped.
`pwsh` and the companion command are unavailable.
Do not repeat their failed command attempts.
Update implementation progress directly in the feature's `.spec-context.json`.
Record verified local validation with the documented audit alternative.
Keep implementation in progress, record the local implementation commit, and keep delivery blocked.
Do not claim that the companion command executed.

## Format: `[ID] [P?] [Story] Description`

- `[P]` identifies independent file changes after their stated prerequisites.
- `[US1]`, `[US2]`, and `[US3]` identify the corresponding user story.
- Every task names an exact file or report path.
- Check a task only after verification.
- Include an evidence note in this form: `(delivered: path/to/file.py)`.
- Keep blocked tasks unchecked.

## Approved Final Manifest

| Owner | Permitted change |
| --- | --- |
| `src/capture/_packet_capture_prompts.py` | Change three existing `2048` literals to `1536` in `PacketCapturePrompts.prompt_max_packet_length`. |
| `src/refactors/serial_cc/start_site_client_capture_wireless.py` | Change three existing `2048` literals to `1536` in `_MAX_PKT_LEN_SPEC`. |
| `tests/unit/capture/test_multi_ap_scan_workflow.py` | Append `test_packet_length_prompt_limits` and `test_packet_length_prompt_defaults`. Permit necessary imports and the module docstring only. |
| `specs/3337-packet-length-validation/` | Commit the existing issue-owned documents and maintain accurate task and completion evidence. |
| `changelog.d/issue-3337-packet-length-validation.md` | Add one `Fixed` bullet with a link to issue #3337. |

The final test manifest supersedes both earlier test locations.
Restore `tests/unit/test_packet_capture.py` exactly to base `9148155c95e1f502abb0a09fd69f5a928b3bf22f`.
`tests/unit/serial_cc/test_start_site_client_capture_wireless.py` is a read-only regression target.
Do not create `tests/unit/capture/test_packet_capture_prompt_limits.py`.
No other test file belongs to the edit manifest.
The final file has three definitions and zero quality findings before the additions.
Two appended functions keep five definitions and add no directory child.
Preserve its existing tests apart from necessary imports and the module docstring.
Do not add a class, fixture, helper, wrapper, module, or production declaration.
Do not change `InputUtils`, `_prompt_bounded_int`, or `_collect_bounded_ints`.
Preserve existing comments, logging, signatures, defaults, and structural debt.
Supplied live open-pull-request checks show no overlap.
The parent notified the coordinator and refined the ownership comment.

The completed sender review found no required edit.
`multi_ap_scan_workflow` and `start_site_scan_capture` send 1300.
`packet_capture` uses compliant fixed lengths of 1300 and 1500.
`org_capture_workflow` reaches the shared prompt and stops on `None`.
Do not edit these senders or the bundled OpenAPI artifact.
Issue #3338 is not a prerequisite.

Future gate artifacts belong under `data/issue-3337/`.
They are not additional planning documents or commit-manifest entries.
Use only the existing Python 3.13.13 `.venv`.
The environment already exists after the recorded missing-dependency evidence.
Do not run bootstrap, install dependencies, edit baselines, add suppressions, or weaken gates.

## Phase 1: Setup

**Purpose**: Confirm the bounded manifest and existing local environment.

- [X] T001 Confirm the final manifest in `specs/3337-packet-length-validation/plan.md`. Preserve the existing branch and all excluded files. (delivered: specs/3337-packet-length-validation/plan.md)
- [X] T002 [P] Verify Python 3.13.13 and the required tools in `.venv/bin/`. Record any missing capability as a blocker without installation. (delivered: specs/3337-packet-length-validation/.spec-context.json)

**Checkpoint**: The implementation owner knows the permitted files and local capabilities.
No branch creation, setup-script execution, dependency change, or new project structure is necessary.

## Phase 2: Foundational Prerequisites

**Purpose**: Prepare the final existing test location without a new abstraction.

- [X] T003 Prepare necessary imports and path-specific parameter IDs in `tests/unit/capture/test_multi_ap_scan_workflow.py`. Use the real prompt classes and `InputUtils`. (delivered: tests/unit/capture/test_multi_ap_scan_workflow.py)

T003 permits imports for pytest, existing mock utilities, and the real classes only.
Keep new behavior inside `test_packet_length_prompt_limits` and `test_packet_length_prompt_defaults`.
Append both functions after the existing tests.
Use `shared` and `wireless` parameter IDs.
Use descriptive IDs for defaults, whitespace, padded input, EOF, and interruption.
These IDs support independent story selections.

Use `pytest.CaptureFixture[str]`, `pytest.LogCaptureFixture`, and `-> None` where applicable.
Keep each function within five parameters, five logical blocks, and 25 lines.
Group raw input, expected length, and exact diagnostic in the limits-case parameter.
Do not create another fixture, class, helper, or module-level test-data declaration.

**Checkpoint**: All story tasks use the two final functions and real input handling.

## Phase 3: User Story 1 - Shared Prompt Limits (Priority: P1)

**Goal**: Accept 64 through 1536 bytes and reject unsupported lengths through the real shared prompt.

**Independent test**: Run the `shared` cases in both final functions.
Each case asserts the returned value and exact prompt argument.
Invalid cases also assert the actual printed diagnostic.
The numeric evidence includes 1473 accepted and 513 required rejected integers.

### Tests for User Story 1 and the Shared Matrix

Write the complete cross-story matrix before either production file changes.
Substitute only `builtins.input`.
Do not replace `_get_input_utils`, `safe_input`, validator results, or the wireless collector.
Call `PacketCapturePrompts.prompt_max_packet_length` directly.
Call `SiteWirelessClientCaptureService._collect_bounded_ints(InputUtils)` for wireless cases.
Do not construct a capture session or start a capture.

- [X] T004 [US1] Add accepted and padded cases to `tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_limits`. Cover all integers from 64 through 1536 for both paths. (delivered: tests/unit/capture/test_multi_ap_scan_workflow.py)
- [X] T005 [US1] Add lower invalid cases to `tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_limits`. Reject 63, 0, and -1 through both real paths. (delivered: tests/unit/capture/test_multi_ap_scan_workflow.py)
- [X] T006 [US1] Add upper invalid cases to `tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_limits`. Reject 1537 through 2048, 2049, and 9999 through both paths. (delivered: tests/unit/capture/test_multi_ap_scan_workflow.py)
- [X] T007 [US1] Add conversion and interruption cases to `tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_limits`. Cover `text`, `64.0`, `1e3`, and `KeyboardInterrupt` through both paths. (delivered: tests/unit/capture/test_multi_ap_scan_workflow.py)
- [X] T008 [US1] Add `tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_defaults`. Cover blank input, spaces, tabs, defaults, packet-length EOF, and complete wireless default sequences. (delivered: tests/unit/capture/test_multi_ap_scan_workflow.py)
- [X] T009 [US1] Record the focused red run against unchanged production source in `data/issue-3337/red-pytest.xml`. Require failures from the old maximum or actual messages. (delivered: data/issue-3337/red-pytest.xml)

### Shared Matrix and Observable Results

| Function and case group | Required inputs and results |
| --- | --- |
| `test_packet_length_prompt_limits`: accepted | Execute every integer from 64 through 1536 for each path. Include padded 64 and 1536. Assert the unchanged integer or complete wireless tuple and exact prompt argument. |
| `test_packet_length_prompt_limits`: lower invalid | Reject 63, 0, and -1 with `None` and the exact range diagnostic. |
| `test_packet_length_prompt_limits`: upper invalid | Reject every integer from 1537 through 2048, plus 2049 and 9999. Assert `None` and the exact range diagnostic. |
| `test_packet_length_prompt_limits`: conversion and interruption | Reject `text`, `64.0`, and `1e3` with the actual trimmed conversion diagnostic. An interruption returns `None` with the cancellation notice and conversion error. |
| `test_packet_length_prompt_defaults` | Cover blank input, spaces-only input, and tabs-only input. Preserve shared defaults 128 and caller default 1300. Preserve wireless packet-length default 1300. Packet-length EOF returns the applicable default. Complete wireless blank or EOF sequences return `(60, 1024, 1300)`. Assert actual safety notices. |

Use wireless inputs `120` and `7` before a selected packet length.
Assert `(120, 7, selected_integer)` for each valid selection.
Assert `None`, not a partial tuple, for each invalid selection.
Use blank inputs across the complete sequence for the all-default case.
Use EOF across the complete sequence for the EOF default case.

Inspect the recorded `builtins.input` prompt arguments.
The input substitute does not print the prompt.
Do not use prompt-call assertions without returned-value assertions.
Use `capsys` for shared printed errors.
Use `caplog` for wireless warnings and input-safety notices.
Assert the exact text and diagnostic channel from `design/contracts/prompt-limits.md`.
Preserve leading newlines and prompt trailing spaces.

The supplied final matrix executed 4010 pytest items, with 2005 per path.
Each path executed 1473 supported integers, 513 required rejected integers, and 19 additional cases.
Each parameterized item executes one real path.
T009 depends on completion of both functions through T004 through T008.
Both production files must still match the original source when it runs.
Record the source SHA, command, exit code, and collected, executed, passed, failed, and skipped counts.
The recorded source base is `9148155c95e1f502abb0a09fd69f5a928b3bf22f`.
It is not delivery authorization.
Values 1537 and 2048 must expose the old acceptance error.
Import errors, missing tools, and collection failures do not satisfy T009.
The supplied final red run executed 4010 cases and recorded 4010 failures, zero errors, and zero skips.
Both production files matched the source base exactly.
Shared input 1537 returned `1537`.
Wireless input 1537 returned `(120, 7, 1537)`.
Both results violate the required maximum.

### Implementation for User Story 1

- [X] T010 [P] [US1] Replace exactly three `2048` literals in `src/capture/_packet_capture_prompts.py::PacketCapturePrompts.prompt_max_packet_length`. Change the prompt, inclusive upper guard, and range-error maximum to `1536`. (delivered: src/capture/_packet_capture_prompts.py)
- [X] T011 [US1] Record the `shared` cases from both final functions in `tests/unit/capture/test_multi_ap_scan_workflow.py`. Use the final green report and require correct values and messages. (delivered: data/issue-3337/green-pytest.xml)

Preserve minimum 64, default 128, valid caller default 1300, integer conversion, EOF handling, and cancellation.
Do not add a shared constant or change the method body beyond those literals.

**Checkpoint**: US1 works independently through its real prompt.
The complete cross-story red evidence exists before any production edit.

## Phase 4: User Story 2 - Wireless Client Capture Limits (Priority: P1)

**Goal**: Apply the same maximum through the real wireless collection sequence.
Retain duration and packet count for valid length.
Return no settings for invalid length.

**Independent test**: Run the `wireless` cases in both final functions.
Require 1473 accepted integers and 513 required rejected integers.
Assert complete tuples, exact packet-length prompts, and actual WARNING diagnostics.

### Tests for User Story 2

- [X] T012 [US2] Verify wireless failures and executed-case counts in `data/issue-3337/red-pytest.xml`. Reuse both final functions in `tests/unit/capture/test_multi_ap_scan_workflow.py` without another function. (delivered: data/issue-3337/red-pytest.xml)

The matrix already covers both wireless limits and real collection behavior.
T012 verifies that the original red run measured wireless behavior.
It does not substitute a later run against modified source for the original evidence.

### Implementation for User Story 2

- [X] T013 [P] [US2] Replace exactly three `2048` literals in `_MAX_PKT_LEN_SPEC` in `src/refactors/serial_cc/start_site_client_capture_wireless.py`. Change `prompt`, `high`, and `range_lines` to use `1536`. (delivered: src/refactors/serial_cc/start_site_client_capture_wireless.py)
- [X] T014 [US2] Record the `wireless` cases from both final functions in `tests/unit/capture/test_multi_ap_scan_workflow.py`. Use the final green report and require complete settings or `None`. (delivered: data/issue-3337/green-pytest.xml)

Preserve all other specification fields, minimum 64, default `"1300"`, and existing duration and packet-count behavior.
Do not edit `_prompt_bounded_int`, `_collect_bounded_ints`, or later capture actions.

**Checkpoint**: US2 works independently through real `InputUtils` and the real collector.

## Phase 5: User Story 3 - Defaults and Input Safety (Priority: P2)

**Goal**: Preserve defaults, whitespace conversion, EOF notices, cancellation, and compliant fixed lengths.

**Independent test**: Run the default, whitespace, padded, EOF, and interruption cases in the two final functions.
Blank or EOF wireless sequences return `(60, 1024, 1300)`.
Shared caller default 1300 remains unchanged.
An interruption returns `None` with the existing notice.

### Tests and Preservation for User Story 3

- [X] T015 [US3] Record default, whitespace, and padded-input results from both final functions in `tests/unit/capture/test_multi_ap_scan_workflow.py`. Use the final green report and assert real values and prompts. (delivered: data/issue-3337/green-pytest.xml)
- [X] T016 [US3] Record EOF and interruption results from both final functions in `tests/unit/capture/test_multi_ap_scan_workflow.py`. Use the final green report and assert defaults, complete tuples, and safety notices. (delivered: data/issue-3337/green-pytest.xml)
- [X] T017 [US3] Verify the unchanged sender-file state against `specs/3337-packet-length-validation/design/research.md`. Confirm no sender or bundled OpenAPI edit without repeating the completed acceptance review. (delivered: specs/3337-packet-length-validation/design/research.md)

The input helper already supplies these behaviors.
US3 needs no production edit.
Only the two final parameterized functions add test behavior.
The three existing definitions remain unchanged apart from necessary imports and the module docstring.

**Checkpoint**: US3 preserves the existing input-safety behavior without another production abstraction.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Record complete local evidence and the bounded future delivery sequence.

### Local Gates and Release Note

- [X] T018 Record both final function nodes from `tests/unit/capture/test_multi_ap_scan_workflow.py` in `data/issue-3337/green-pytest.xml`. Use the existing coverage API to export branch evidence to `data/issue-3337/coverage.json`. (delivered: data/issue-3337/green-pytest.xml)
- [X] T019 Measure the two guard regions and real collector from `data/issue-3337/coverage.json`. Require at least 80% statement coverage in each region. (delivered: data/issue-3337/coverage.json)
- [X] T020 Record adjacent capture pytest results in `data/issue-3337/adjacent-pytest.xml`. Run all five existing capture targets listed below without network contact. (delivered: data/issue-3337/adjacent-pytest.xml)
- [X] T021 Compile both prompt files, `tests/unit/capture/test_multi_ap_scan_workflow.py`, and `MistHelper.py`. Use the unchanged repository syntax command listed below. (delivered: specs/3337-packet-length-validation/.spec-context.json)
- [X] T022 Run repository-scope Ruff and Black. Require clean results without unrelated edits. Black checked 1882 files without changes. (delivered: specs/3337-packet-length-validation/.spec-context.json)
- [X] T023 Run configured mypy using `MYPY_PATHS` from `.github/workflows/ci.yml` and `pyproject.toml`. Use the existing inline command in `specs/3337-packet-length-validation/design/quickstart.md`. (delivered: specs/3337-packet-length-validation/.spec-context.json)
- [X] T024 Run repository-configured Bandit with `pyproject.toml`. Record its complete result under `data/issue-3337/` without new exclusions or suppressions. (delivered: data/issue-3337/bandit.json)
- [X] T025 Run pip-audit against `requirements.txt`. Record the macOS failure before scanning and the documented local audit alternative. Keep the Git pin explicitly unaudited. (delivered: specs/3337-packet-length-validation/.spec-context.json)
- [X] T026 Rerun the configured test-quality ratchet for the final `tests/unit/capture/test_multi_ap_scan_workflow.py` edit and current test tree. Preserve `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`. (delivered: specs/3337-packet-length-validation/.spec-context.json)
- [X] T027 [P] Add one `### Fixed` heading and one bullet to `changelog.d/issue-3337-packet-length-validation.md`. Link issue #3337 in that bullet. (delivered: changelog.d/issue-3337-packet-length-validation.md)
- [X] T028 Record exact local commands, results, counts, and blockers in `specs/3337-packet-length-validation/tasks.md` and `.spec-context.json`. Do not mark unmeasured work complete. (delivered: specs/3337-packet-length-validation/tasks.md)
- [X] T029 Verify the complete bounded manifest against `specs/3337-packet-length-validation/plan.md`. Require six production literal changes, two appended test functions, and exact restoration of the large test file. (delivered: specs/3337-packet-length-validation/plan.md)
- [X] T030 After cross-artifact analysis, commit only the approved manifest. Commit `e74a996777d9fffb163c1be904f497132cbb7081` contains the repair and the required Copilot trailer. (delivered: e74a996777d9fffb163c1be904f497132cbb7081)

T019 measures these existing regions separately:

| File | Region | Supplied final evidence |
| --- | --- | --- |
| `src/capture/_packet_capture_prompts.py` | `prompt_max_packet_length` | 11/11 statements, 100%, pass. |
| `src/refactors/serial_cc/start_site_client_capture_wireless.py` | `_prompt_bounded_int` | 12/12 statements, 100%, pass. |
| `src/refactors/serial_cc/start_site_client_capture_wireless.py` | `_collect_bounded_ints` | 8/8 statements, 100%, pass. |

Use the existing AST-based inline measurement in `design/quickstart.md`.
Do not add a coverage helper or guard file.
Missing reports, unreadable input, absent source regions, and zero measured statements must fail the measurement.
Preserve the branch report.
Coverage does not replace actual boundary and message assertions.
Use coverage's existing run and JSON APIs, not pytest-cov's whole-module threshold for the focused suite.
Do not set `--cov-fail-under=0`, change configuration, or add a coverage helper file.
The global repository coverage threshold remains unchanged and required in CI.

Report 1473 accepted and 513 required rejected integers for each real path.
The required rejected set contains 63 and all 512 integers from 1537 through 2048.
Report additional invalid, default, whitespace, EOF, and interruption cases separately.
Do not confuse path execution counts with pytest item counts.
Every pytest result includes collected, executed, passed, failed, and skipped counts.
A skipped test is not passing evidence.

T025 must distinguish requirements resolution from the installed-environment audit.
Record the normal audit error before the local alternative.
The supplied macOS error occurs during ensurepip with SIGABRT and a copy error, before the audit starts.
Use `rtk proxy .venv/bin/python -m pip_audit --local --skip-editable` as the documented local alternative.
A passing local audit does not prove that the requirements-resolution audit passed.
The Git-pinned `misthelper-devtools` version `0.5.2` is absent from PyPI and remains explicitly unaudited.
Keep the normal requirements audit as a delivery check.
Do not change dependencies or suppress a vulnerability.

T026 uses `rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`.
Include `--report data/issue-3337/test-quality-report.json` and `--summary data/issue-3337/test-quality-summary.md`.
Run against the current tree, including uncommitted test edits.
Do not use `--changed-from` before commit.
Do not use `--write-baseline`, `--prune-baseline`, or rule exclusions.
Record the checked scope, checked counts, findings, and gate result.
The rejected large-file manifest passed 4010 focused and 4369 adjacent cases.
Its region measurements were shared 11/11, wireless bounded 12/12, and collector 8/8, each at 100%.
The ratchet reported 23 new line-sensitive `weak_zero_assertions` findings after existing assertions moved.
That file still had exactly 24 findings, with zero semantic new findings.
These results explain the manifest correction.
Those earlier results did not satisfy final-manifest verification.
Restore the file exactly instead of changing the baseline, adding suppressions, or repairing unrelated tests.

The parent supplied final evidence on 2026-09-30 at 19:06:28.648-05:00.
The documentation owner recorded these results without executing or rechecking a gate.

| Final check | Supplied result |
| --- | --- |
| Focused red | 4010 executed, 4010 failures, zero errors, zero skips. Source matched the base exactly. |
| Focused green | 4010 passed, zero failures, zero errors, zero skips. |
| Each prompt path | 2005 executed: 1473 supported integers, 513 required rejected integers, and 19 additional cases. |
| Adjacent tests | 4373 passed, zero failures, zero skips. |
| Quality ratchet | 944 files checked, 728 existing findings checked, zero new findings, 42 configured skips, zero parse errors. |
| Compile | All four required files passed. |
| Ruff | Repository-scope `rtk proxy .venv/bin/python -m ruff check .` passed. |
| Black | Repository-scope `rtk proxy .venv/bin/python -m black --check --diff .` passed. All 1882 files remain unchanged. |
| mypy | The exact configured CI scope passed across 608 source files. |
| Bandit | Zero findings across 206617 checked lines. Report: `data/issue-3337/bandit.json`. |
| Normal requirements audit | Failed during macOS ensurepip with SIGABRT before scanning. This audit did not pass. |
| Local audit alternative | No known vulnerabilities in audited installed packages. `misthelper-devtools` version `0.5.2` remained explicitly unaudited because PyPI does not contain it. |

The source diff contains exactly three replaced lines in each approved source file.
The final test file contains five functions.
`test_packet_length_prompt_limits` has 23 lines and four parameters.
`test_packet_length_prompt_defaults` has 21 lines and three parameters.
The large packet-capture test file matches the base exactly.
No other production declaration, wrapper, or class was added.
All named senders, OpenAPI artifacts, dependencies, README, shared configuration, and baselines remain unchanged.
Cross-artifact analysis and T030 are complete.
The verified local implementation commit is `e74a996777d9fffb163c1be904f497132cbb7081`.

T029 includes committed branch changes, staged changes, unstaged changes, and feature-owned untracked files.
Verify the two appended functions, five total definitions, permitted imports and docstring, and unchanged production declarations.
Require `tests/unit/test_packet_capture.py` to match the base exactly.
Require zero sender, OpenAPI, dependency, README, shared configuration, baseline, and suppression changes.
Do not stage `data/` reports or unrelated files.
Do not use a repository-wide staging command.
A failed or unavailable required local gate blocks T030.
The documented macOS audit alternative can satisfy its local check.
The normal requirements audit remains a separate delivery condition.
Do not report a blocker as a passing gate.

Use this future commit message:

```text
fix(capture): limit packet length to 1536 bytes

Closes #3337

Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>
```

The authoritative Git workflow requires this Conventional Commit format.
The current request excludes README changes and production deployment.
The fragment and terminal contract document the changed range.
Do not add unrequested deployment or production health checks to these delivery tasks.
Protected merge, all applicable checks, and offline exact-main tests remain required.

### Coordinator-Authorized Delivery

The coordinator released publication on `bceba98ff1177ab32ed65ef90279baccba85a47f`.
The prerequisite protected merge and 919 exact-main cases passed.
The preserved local tip rebased cleanly onto that exact revision.
The isolated environment now matches the current manifests and contains 160 compatible packages.
Both exhaustive prompt tests and all adjacent capture tests passed after the rebase.
The repeated ratchet checked 947 files and 725 existing findings with zero new findings.
The complete hashed runtime audit checked 105 packages with zero vulnerabilities or skips.
No remote check or protection requirement is waived.
The initial source-base SHA remains red-test evidence, not publication authorization.

- [X] T031 Record the coordinator-authorized main SHA `bceba98ff1177ab32ed65ef90279baccba85a47f`. (delivered: specs/3337-packet-length-validation/.spec-context.json)
- [X] T032 Rebase the preserved local tip onto that exact authorized main revision. (delivered: 4dbe3a7fa374459f406309c4c11faf6c93639bb3)
- [X] T033 Refresh the isolated environment and repeat all scoped tests, coverage, quality checks, and the runtime audit. (delivered: specs/3337-packet-length-validation/.spec-context.json)
- [ ] T034 Push only the verified issue branch after confirming the authorized main revision still matches.
- [ ] T035 Create the complete-template pull request with `Closes #3337`, exact evidence, and required labels.
- [ ] T036 Verify every CI, title, CodeQL, and normal requirements-audit result.
- [ ] T037 Complete the protected, up-to-date, exact-head squash merge. Omit `--delete-branch`.
- [ ] T038 Test the exact merged main revision locally without any capture request or Mist cloud contact.

Record publication and post-merge evidence in the issue, pull request, and session artifacts.
Do not create an orphan commit after the squash merge merely to update these delivery checkboxes.

Before T032 and T034, confirm that remote `main` still matches the coordinator's authorized full SHA.
If it differs, retain the block until the coordinator supplies a new verified stable SHA.
Do not use the source-base SHA as a substitute.
Do not switch a checkout, rename a branch, or access the shared `main` checkout.
Do not force-push `main` or another owner's branch.
If the existing issue branch needs a rewritten push, use only `--force-with-lease`.

T035 must preserve every template heading, comment, checklist item, and ordering.
Use a Conventional Commit title.
Include each local command with its actual result.
Do not check a conformance item without evidence.
Apply a type label, a scope label, and `in-progress` while work remains active.

T036 requires all applicable repository checks, including the title check and CodeQL.
Treat skipped or missing checks as unknown, not passed.
Do not remove a gate or edit a baseline.
Do not enable auto-merge before every applicable check passes.

T037 requires the branch to remain up to date and protection to approve the merge.
If `main` advances, repeat authorization, rebase, affected local gates, and CI before the merge.
Do not bypass protection or push directly to `main`.

T038 uses an isolated checkout of the exact merged commit.
Do not substitute the feature-branch result or a later `main` revision.
Use local offline prompt tests without Mist credentials, API calls, captures, or production deployment.
Do not declare final delivery complete until this evidence exists.

**Checkpoint**: Local evidence proves the bounded correction.
Remote delivery remains incomplete while any delivery condition lacks evidence.

## Local Command Reference

These commands describe the final local-validation procedure.
Do not rerun them for this documentation update.
After authorization, repeat the required commands under T033.
Use the existing worktree as the repository root.
Use `rtk proxy` for Python and environment commands.
Use `rtk git` for Git commands.
Do not execute these commands during documentation alignment.

Create `data/issue-3337/` before the first report-producing run.
The focused red command must retain its nonzero exit result.

```bash
rtk proxy mkdir -p data/issue-3337
rtk proxy env -u MIST_APITOKEN -u MIST_API_TOKEN .venv/bin/python -m pytest \
  tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_limits \
  tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_defaults \
  -q --tb=short --junitxml=data/issue-3337/red-pytest.xml
```

Use the same two function nodes after the six-literal correction:

```bash
rtk proxy env -u MIST_APITOKEN -u MIST_API_TOKEN COVERAGE_FILE=data/issue-3337/.coverage \
  .venv/bin/python -m coverage run --branch \
  --source=src.capture._packet_capture_prompts,src.refactors.serial_cc.start_site_client_capture_wireless \
  -m pytest \
  tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_limits \
  tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_defaults \
  -q --junitxml=data/issue-3337/green-pytest.xml
```

T011, T014, T015, and T016 reuse the supplied final green report.
Do not require separate report files or another gate run to record this evidence.
For a later authorized rerun, use `-k shared` or `-k wireless` with both function nodes.
Alternatively, select the final test file with `-k packet_length_prompt`.
Each selection must execute at least one relevant case.
A zero-case selection fails its verification task.

```bash
rtk proxy env -u MIST_APITOKEN -u MIST_API_TOKEN .venv/bin/python -m pytest \
  tests/unit/test_packet_capture.py \
  tests/unit/capture \
  tests/unit/serial_cc/test_start_site_client_capture_wireless.py \
  tests/unit/serial_cc/test_start_site_scan_capture.py \
  tests/integration/test_packet_capture_org_compatibility.py \
  -q --tb=short --junitxml=data/issue-3337/adjacent-pytest.xml
rtk proxy .venv/bin/python -m py_compile MistHelper.py \
  src/capture/_packet_capture_prompts.py \
  src/refactors/serial_cc/start_site_client_capture_wireless.py \
  tests/unit/capture/test_multi_ap_scan_workflow.py
rtk proxy .venv/bin/python -m ruff check .
rtk proxy .venv/bin/python -m black --check --diff .
rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r . \
  -f json -o data/issue-3337/bandit.json
rtk proxy .venv/bin/python -m pip_audit -r requirements.txt
rtk proxy .venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --report data/issue-3337/test-quality-report.json \
  --summary data/issue-3337/test-quality-summary.md
```

Use the exact coverage JSON export, AST region check, and mypy commands from `design/quickstart.md`.
They read the existing CI scope and current source regions without another helper file.
The dependency audit may contact advisory services.
It must not contact Mist cloud or make capture requests.
All pytest evidence remains offline.

## Dependencies and Execution Order

| Tasks | Prerequisites |
| --- | --- |
| T001, T002 | None. Both are read-only capability and manifest checks. |
| T003 | T001 and T002. |
| T004 through T008 | T003. One owner edits the two final functions in the same file sequentially. |
| T009 | T004 through T008, with both production files unchanged. |
| T010 | T009. |
| T011 | T010. |
| T012 | T009. |
| T013 | T012. |
| T014 | T013. |
| T015, T016 | T010 and T013. |
| T017 | T001. |
| T018 | T011, T014, T015, and T016. |
| T019 | T018. |
| T020 through T026 | T018. |
| T027 | T018. |
| T028 | T017 and T019 through T027. |
| T029 | T028. |
| T030 | T029, clear local gate results with the documented audit alternative, and the parent's completed cross-artifact analysis. |
| T031 | The coordinator's full verified stable `main` SHA. |
| T032 | T030 and T031. |
| T033 | T032. |
| T034 | T033 and current authorization. |
| T035 | T034. |
| T036 | T035. |
| T037 | T036, protection approval, and an up-to-date branch. |
| T038 | T037 and the exact merged SHA. |

The user-story completion graph is:

```text
Setup -> Foundation -> Complete shared test matrix -> Original-source red run
                                                     |
                       +-----------------------------+------------------+
                       |                                                |
                 US1 shared literals                             US2 wireless literals
                       |                                                |
                 US1 shared green                                US2 wireless green
                       +-----------------------------+------------------+
                                                     |
                                    US3 defaults and safety evidence
                                                     |
                       Local gates -> Cross-artifact analysis -> Manifest-only commit
                                                     |
                       BLOCKED: coordinator's verified stable main SHA
                                                     |
                          Rebase -> Repeated gates -> Authorized push
                                                     |
                           Template-preserving PR -> CI/title/CodeQL
                                                     |
                              Protected, up-to-date squash merge
                                                     |
                                  Exact merged-main offline tests
```

US2 does not depend on the shared literal edit.
Its test-matrix dependency prevents a second owner from changing the same test file.
US3 adds no production edit and reuses both real paths.
No implementation task depends on issue #3338.

## Parallel Execution Examples

### User Story 1

After T009 and T012, T010 can run beside T013.
The owners edit different production files.
Do not edit the two test functions during those changes.
Run T011 after T010.

### User Story 2

After T009 and T012, T013 can run beside T010.
Run T014 after T013.
Do not create a separate wireless test file or helper.

### User Story 3

The shared test file requires one owner.
T015 and T016 are read-only selections of the completed matrix.
After T010 and T013, those selections can run beside the read-only sender-state check T017.
No parallel test-file edit is available.

T001 and T002 can run together.
T027 can run beside the local gates after T018.
Parallel examples do not authorize nested agents.

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational tasks.
2. Author the full cross-story matrix in the two permitted functions.
3. Prove the original-source failure before any production change.
4. Complete US1 and its independent shared green selection.

US1 is the local MVP.
It is not the complete feature or permission for remote delivery.

### Incremental Completion

1. Complete US2 and its independent wireless green selection.
2. Complete US3 preservation evidence.
3. Complete every local gate and the release-note fragment.
4. Commit the approved manifest only.
5. Retain the remote-delivery block until the coordinator supplies the authorized SHA.
6. Complete the protected delivery sequence and exact merged-main local tests.

## Task Summary

| Area | Count |
| --- | --- |
| Setup | 2 |
| Foundational | 1 |
| US1 | 8 |
| US2 | 3 |
| US3 | 3 |
| Polish and cross-cutting concerns | 21 |
| **Total** | **38** |

Four tasks carry `[P]`: T002, T010, T013, and T027.
Five delivery tasks, T034 through T038, remain incomplete.
All 38 tasks retain their sequential IDs and exact file paths.
T001 through T029 are complete from the supplied verified local evidence.
T030 is complete in local implementation commit `e74a996777d9fffb163c1be904f497132cbb7081`.
T031 through T033 are complete after coordinator authorization and repeated verification.
There are 33 completed tasks and five remaining tasks.
The normal requirements audit remains failed before scanning.
The documented local audit alternative does not audit the Git-pinned package.
Story tasks also carry their required label.
No task, gate result, or delivery action is complete merely because this file exists.
