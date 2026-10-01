# Tasks: Remove Unused Output Defaults

**Input**: [spec.md](spec.md) and [plan.md](plan.md).

**Template**: [The repository task template](../../.specify/templates/tasks-template.md).

**Feature directory**: `/Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-glowing-potato/specs/3314-unused-output-defaults`.

**Branch**: `jmorrison-juniper-unused-output-defaults` is app-managed.

**Owner**: Session `694ad69e-4090-4f3e-91bd-4bc197e768be` claimed issue #3314.

**Initial base**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
This reference does not grant publication permission.

**Current phase**: Write only `specs/3314-unused-output-defaults/tasks.md`.
All tasks below describe later authorized work.
Task generation does not complete an implementation task.
Do not stage or commit during task generation.

**Implementation delegation**: The user now authorizes implementation and focused proof only.
The parent retains T041-T054 and all publication actions.
Changed-test format and lint checks do not complete the full-scope T041 gate.

## Prerequisites and Execution Rules

Ownership, specification, and planning are complete.
Do not repeat feature discovery, numbering, branch creation, or ownership publication.
The plan contains the research, design, and validation guide.
Do not create their optional companion documents.

The actual missing-pytest failure already occurred.
Recovery is restoring this worktree's own `.venv`.
Wait for that recovery before tests.
Do not start a second bootstrap process while the first process runs.
Do not use another worktree's environment.

The user reports successful Podman information with Linux arm64.
This result is not an image-build result.
Verify the local connection and ownership before a build.

Use Python 3.13 or newer and the existing dependency pins.
Use semantic classes for substantive test helpers.
Add no production wrapper or shared test fixture module.
Keep comments rare and explain non-obvious reasons.
Apply the narrow structural exceptions already recorded in `plan.md`.

Use only synthetic values and owned temporary paths.
Tests must make no network calls.
Do not load a real environment file or start the production application.
Do not authenticate, change firmware, access production stores, or perform migrations.

Keep test commands and execution evidence in `specs/3314-unused-output-defaults/validation.md`.
Use one writer for that file.
Record commands, scope, exit status, counts, results, and capability gaps.
Keep temporary configurations, coverage data, caches, and output outside the repository.
Use an owned temporary directory for these outputs.
Do not create another tracked manifest, log, checklist, or report.

All tasks start unchecked.
Check a task only after verification.
Add the template evidence annotation when a delivered file exists.
Use the form `(delivered: path/to/file)`.
Keep blocked execution tasks unchecked and explain the missing condition.
Never convert a missing capability, skip, or empty report into a pass.

## Exact Reservation and Artifact Producers

The reservation contains these 15 files.
It does not authorize changes during this phase except to `tasks.md`.

| Reserved path | Producer |
| --- | --- |
| `container/scripts/misthelper-session.sh` | T022 removes one declaration. |
| `Dockerfile` | T023 removes one declaration. |
| `Containerfile` | T024 removes one declaration. |
| `documentation/wiki/Data-Model.md` | T029 corrects one instruction. |
| `tests/unit/container/output_defaults/__init__.py` | T004 creates the package marker. |
| `tests/unit/container/output_defaults/contract.py` | T005 creates the contract helpers. |
| `tests/unit/container/output_defaults/session.py` | T006 creates the session helpers. |
| `tests/unit/container/output_defaults/test_contract.py` | T007 through T010 create the contract and compatibility tests. |
| `tests/unit/container/output_defaults/test_session.py` | T011 through T015 create the actual Bash tests. |
| `specs/3314-unused-output-defaults/spec.md` | The specification phase already produced this file. |
| `specs/3314-unused-output-defaults/plan.md` | The planning phase already produced this file. |
| `specs/3314-unused-output-defaults/tasks.md` | This phase produces the task list. Later authorized work records verified task status here. |
| `specs/3314-unused-output-defaults/analysis.md` | T051 produces the analysis. T054 checks its final evidence. |
| `specs/3314-unused-output-defaults/validation.md` | T001 creates the evidence record. Later execution tasks supply their own results. |
| `changelog.d/issue-3314-unused-output-defaults.md` | T030 produces the release fragment. |

Keep the new test package at five files.
Keep the feature directory at five direct files.
No existing test module needs an edit.
Existing container, environment, export, and readiness tests remain read-only.

Keep `compose.yml` and `web_portal/routes/dashboard.py` byte-identical to the initial base.
Keep `MistHelper.py`, `src/`, entrypoints, and `container/scripts/write-session-env.sh` unchanged.
Do not change `README.md`, `CHANGELOG.md`, agent instructions, deployment environments, dependencies, or SDK pins.
Do not change schemas, primary keys, baselines, suppressions, exclusions, or thresholds.
Do not write shared `.specify` state, `.spec-context.json`, or agent context.
Do not run Git hooks or Git extensions.
Issue #3313 remains separate.

## Phase 1: Setup

**Goal**: Complete the existing environment recovery and establish one local evidence record.

- [X] T001 Create `specs/3314-unused-output-defaults/validation.md` for later implementation evidence. Record the actual missing-pytest failure and current recovery status. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T002 Verify recovery of this worktree's `.venv` through `scripts/bootstrap_worktree.py`. Record the supported interpreter and pytest availability in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T003 Record immutable base bytes and hashes in `specs/3314-unused-output-defaults/validation.md`. Verify the six contract inputs against the initial base. (delivered: specs/3314-unused-output-defaults/validation.md)

T001 must distinguish supplied history from newly executed results.
Do not invent the missing-pytest command or its exit status.
If the original details are unavailable, state that limitation.
T002 must wait for the existing recovery.
If recovery fails, use the existing bootstrap without changing dependency files.
Record the original failure before any recovery attempt.

T003 records the exact reservation and protected-file hashes.
Store temporary base copies only under the owned temporary directory.
Verify that each dead declaration occurs exactly once.
Verify the original false instruction and complete image-file equality.
Do not fetch another base.

**Checkpoint**: The supported worktree environment is ready.
The original inputs remain unchanged.

## Phase 2: Foundational Guards and Tests

**Goal**: Prove the shared safety contract before any configuration or documentation edit.

The guards protect all four stories.
Their failure evidence is a prerequisite for every product edit.
Tests are required by the specification.

### Shared Helpers

- [X] T004 Create `tests/unit/container/output_defaults/__init__.py` as a passive package marker. Add no import-time operation. (delivered: tests/unit/container/output_defaults/__init__.py)
- [X] T005 [P] Implement semantic contract helpers in `tests/unit/container/output_defaults/contract.py`. Read all six inputs and report exact decisions and counts. (delivered: tests/unit/container/output_defaults/contract.py)
- [X] T006 [P] Implement semantic session helpers in `tests/unit/container/output_defaults/session.py`. Use the existing Bash capability helper and bounded synthetic application execution. (delivered: tests/unit/container/output_defaults/session.py)

T005 must read these six inputs without executing them:

| Input | Required decision |
| --- | --- |
| `container/scripts/misthelper-session.sh` | No active `OUTPUT_FORMAT` assignment remains. |
| `Dockerfile` | No active image declaration assigns `OUTPUT_FORMAT`. |
| `Containerfile` | No active image declaration assigns `OUTPUT_FORMAT`. |
| `documentation/wiki/Data-Model.md` | The SQLite instruction requires the explicit flag and rejects environment-only selection. |
| `compose.yml` | The existing `OUTPUT_FORMAT=polyglot` declaration remains. |
| `web_portal/routes/dashboard.py` | The reader, normalization, SQLite default, selected checks, and readiness responses remain. |

Report `expected`, `checked`, `rejected`, failing paths, and exact reasons.
Read every input after an earlier rejection.
Count only successful reads as checked.
Count each rejected input once.
Do not substitute empty text for unreadable input.
Success requires six expected inputs, six checked inputs, and zero rejected inputs.

Recognize active shell assignment and export forms.
Recognize image declarations with legacy syntax, multiple assignments, quotes, whitespace, and continuation lines.
Reject other assigned values, including `polyglot`.
Ignore comment-only declarations.
Check the actual SQLite instruction, not a flag in an unrelated example.
Use standard-library text processing and AST inspection where appropriate.

T006 reuses `tests/unit/container/bash_support.py` without editing it.
Use its capability result, not executable presence alone.
Place the synthetic application, session file, logs, markers, and recorder output under `tmp_path`.
Set every existing application, session, log, runtime-log, and Python-command override.
Use a controlled session file to replace the operational database path.
Allow only a synthetic environment, controlled `PATH`, `HOME`, and temporary paths.
Exclude real tokens, `BASH_ENV`, cloud settings, and production database settings.
Keep every new session subprocess and session test within 30 seconds.
Terminate only specifically owned child processes and wait for cleanup.

### Contract and Compatibility Tests

- [X] T007 [P] Add the live contract and 14 required mutation cases to `tests/unit/container/output_defaults/test_contract.py`. Use repaired temporary copies. (delivered: tests/unit/container/output_defaults/test_contract.py)
- [X] T008 Add valid comment cases and active-declaration variants to `tests/unit/container/output_defaults/test_contract.py`. Add separate compose and readiness corruption cases. (delivered: tests/unit/container/output_defaults/test_contract.py)
- [X] T009 Add the 15 actual parser and export cases to `tests/unit/container/output_defaults/test_contract.py`. Reject the unsupported explicit selection separately. (delivered: tests/unit/container/output_defaults/test_contract.py)
- [X] T010 Add six healthy readiness cases and 17 single-failure cases to `tests/unit/container/output_defaults/test_contract.py`. Keep the real route and reader. (delivered: tests/unit/container/output_defaults/test_contract.py)

T007 must cover these required negative cases:

| Mutation | Count | Exact decision |
| --- | --- | --- |
| Restore each original dead declaration separately. | 3 | Reject the altered input after six successful reads. |
| Inject an active `OUTPUT_FORMAT=polyglot` assignment into each repair source separately. | 3 | Reject the altered input and name its path. |
| Restore the false instruction or remove the required flag. | 2 | Reject the page in each separate case. |
| Make each required input unreadable separately. | 6 | Report six expected inputs, five checked inputs, and one rejected input. |

Use a missing file or a directory for reliable unreadable-input cases.
Do not rely only on permission bits.
Test a narrow `PermissionError` decision separately when coverage requires it.
Report additional cases separately from the required count of 14.
Prove both outcomes of each critical guard decision.
Do not add passing skips, weaker assertions, or expected-failure markers to hide the live defect.

T009 uses this complete matrix:

| Environment `OUTPUT_FORMAT` | No format flag | Explicit `csv` | Explicit `sqlite` |
| --- | --- | --- | --- |
| Unset | CSV | CSV | SQLite |
| `csv` | CSV | CSV | SQLite |
| `sqlite` | CSV | CSV | SQLite |
| `polyglot` | CSV | CSV | SQLite |
| `synthetic-unsupported` | CSV | CSV | SQLite |

Set the clean environment and temporary working directory before passive imports.
Use `MistHelper._build_argument_parser().parse_args()` and the actual `_configure_runtime_options()`.
Use an isolated `AppContext`.
Do not invoke `MainEntrypoint.run()` or either bootstrap startup path.
Replace only telemetry and harmless deferred dependencies needed by the isolated call.
Keep the parser decision real.

Call the real `DataExporter.write_with_format_selection()` without a format override.
Use two flat synthetic records, `listOrgSites`, and a safe bare destination name.
Set `MISTHELPER_STANDALONE=true`.
Place all database and export paths under `tmp_path`.
Keep local writers, processing helpers, schema helpers, and existing key treatment real.
Make unexpected authentication, host probes, router construction, and network access fail.
Restore context, resolver bindings, environment, and exporter caches after each case.

Assert the parsed format, runtime format, exporter success, and both stored records.
Read CSV with `csv.DictReader`.
Read SQLite with explicit standard-library row queries.
A CSV case must create no SQLite result.
A SQLite case must create no CSV result.
The explicit `polyglot` case must return `SystemExit.code == 2` and produce no export.
Its environment also contains `polyglot`.

T010 replaces all five resource checks before the Flask test client requests `/ready`.
Replace `_check_data_dir_writable`, `_check_mist_api_session`, `_check_sqlite_database`, `_check_arangodb`, and `_check_redis`.
Unexpected resource access must fail.
Do not open a port.

| Environment | Exact active checks |
| --- | --- |
| Unset, `sqlite`, or `standalone` | `data_directory_writable`, `mist_api_session`, `sqlite_database` |
| ` PolyGloT ` | `data_directory_writable`, `mist_api_session`, `arangodb`, `redis` |
| `csv` or `synthetic-unsupported` | `data_directory_writable`, `mist_api_session` |

Assert the normalized format, exact check names, and exact calls.
Each healthy case returns 200 with `status == "ready"` and no failed checks.
Fail each selected check separately.
Each failure returns 503 with `status == "not ready"` and its exact single failure name.
Polyglot must not select SQLite.
The unset format must retain the readiness SQLite default.

### Actual Bash Tests

- [X] T011 [P] Add actual Bash syntax tests to `tests/unit/container/output_defaults/test_session.py`. Require the malformed temporary script to fail with status 2. (delivered: tests/unit/container/output_defaults/test_session.py)
- [X] T012 Add clean-exit and inherited-format tests to `tests/unit/container/output_defaults/test_session.py`. Verify one launch and the exact original arguments. (delivered: tests/unit/container/output_defaults/test_session.py)
- [X] T013 Add four token-transfer cases and missing-token refusal to `tests/unit/container/output_defaults/test_session.py`. Assert that output and logs contain no token values. (delivered: tests/unit/container/output_defaults/test_session.py)
- [X] T014 Add two-session isolation and cleanup tests to `tests/unit/container/output_defaults/test_session.py`. Compare normal, INT, and TERM outcomes with the original script. (delivered: tests/unit/container/output_defaults/test_session.py)
- [X] T015 Add restart-limit, delay, cap, reset, and default checks to `tests/unit/container/output_defaults/test_session.py`. Use only existing short-run overrides. (delivered: tests/unit/container/output_defaults/test_session.py)

T011 must parse the actual repository script.
Its invalid copy must produce a syntax diagnostic that names the owned temporary script.
Syntax success does not replace actual session execution.

T012 covers unset, `csv`, `sqlite`, `polyglot`, and `synthetic-unsupported` format values.
The repaired script must preserve each supplied value and leave the unset value unset.
The application arguments remain exactly `["MistHelper.py"]`.
The script adds no format flag.
A clean application exit returns 0 after one launch.

T013 covers both token aliases from the controlled session file and the supplied environment.
These are four transfer cases.
Missing credentials return 1 before any application launch.
Use internal exact comparisons or fingerprints without recording token values.
Check captured output and every owned log for token disclosure.

T014 uses two distinct synthetic `SSH_CONNECTION` values and normalized session identifiers.
Each session removes only its own pre-created marker.
Preserve the existing PID-file treatment.
Measure exact original signal outcomes before the product edit.
Do not invent new signal exit codes.

T015 verifies exact attempt counts and reported delay sequences.
Prove doubling, the cap, and count and delay reset after a controlled healthy run.
Preserve defaults of five attempts, 30 healthy seconds, two initial seconds, and a 60-second cap.

### Required Original Failure Evidence

- [X] T016 Verify test isolation and the supported Bash capability in `specs/3314-unused-output-defaults/validation.md`. Record the owned temporary locations and timeout controls. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T017 Record the original live contract failure in `specs/3314-unused-output-defaults/validation.md`. Require six expected inputs, six checked inputs, and four rejected inputs. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T018 Record all 14 invalid-input guard results in `specs/3314-unused-output-defaults/validation.md`. Record additional valid and invalid cases separately. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T019 Record original session and compatibility results in `specs/3314-unused-output-defaults/validation.md`. Capture inherited-format failures and exact signal, credential, and restart baselines. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T020 Verify the pre-edit evidence barrier in `specs/3314-unused-output-defaults/validation.md`. Authorize product edits only after the required guards and tests exist. (delivered: specs/3314-unused-output-defaults/validation.md)

T017 names the session script, both image files, and the data-model page.
Record the contract revision or hash and the exact runner result.
Do not repair a live input before this red result.

T018 records failing contract decisions separately from passing negative-case test assertions.
Each invalid input must cause a guard failure.
Each unreadable case must identify the exact path and correct read count.

T019 records actual parser, exporter, readiness, and unchanged session-control evidence.
Separate expected original format failures from unresolved test defects.
Keep all original results for later comparison.

T020 requires the original four-rejection result and all required invalid-input proofs.
Require accurate counts and complete baseline controls.
Required capabilities must not silently skip.
Freeze the contract before the product edits.
If later guard logic changes, repeat its original and invalid proofs using immutable base copies.
Retain the first live red evidence.

**Checkpoint**: All five test files exist.
The unchanged live sources still produce the original false contract.
No product or release file changed before this checkpoint.

## Phase 3: User Story 1 - Keep the Existing CSV Default

**Priority**: P1.

**Goal**: Remove exactly three dead declarations without changing the CSV default or session invocation.

**Independent test**: All three repaired source decisions pass.
The five no-flag selection cases produce actual CSV with both records.
Actual Bash preserves inherited settings and the original application arguments.
The full contract can still reject the unchanged page until US2 completes.

### Tests Before Configuration Edits

- [X] T021 [US1] Verify the completed guard barrier and frozen contract in `specs/3314-unused-output-defaults/validation.md`. Preserve all original failure evidence. (delivered: specs/3314-unused-output-defaults/validation.md)

### Configuration Edits

- [X] T022 [P] [US1] Delete only `export OUTPUT_FORMAT=sqlite` from `container/scripts/misthelper-session.sh`. Preserve every other byte. (delivered: container/scripts/misthelper-session.sh)
- [X] T023 [P] [US1] Delete only `ENV OUTPUT_FORMAT=sqlite` from `Dockerfile`. Preserve every other byte. (delivered: Dockerfile)
- [X] T024 [P] [US1] Delete only `ENV OUTPUT_FORMAT=sqlite` from `Containerfile`. Preserve every other byte. (delivered: Containerfile)

### Independent Validation

- [X] T025 [US1] Verify the three exact line deletions in `specs/3314-unused-output-defaults/validation.md`. Confirm complete image-file equality and all protected bytes. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T026 [US1] Record actual CSV-default and inherited-session results in `specs/3314-unused-output-defaults/validation.md`. Verify two records and no added format argument. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T027 [US1] Run the unchanged session and image-equivalence tests. Record their results in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)

T025 compares each repaired file with its immutable base bytes minus its one original line.
Do not add an environment default, an `unset`, or new logging.
Do not change restart logic, traps, credential handling, arguments, or log text.

T027 includes `tests/unit/container/test_misthelper_session_script.py` and `tests/unit/container/test_build_files_match.py`.
Do not edit these modules.

**Checkpoint**: US1 provides an internal CSV-preservation checkpoint.
It does not complete the documentation repair or authorize publication.

## Phase 4: User Story 2 - Select SQLite Explicitly

**Priority**: P1.

**Goal**: Correct the SQLite instruction while retaining actual explicit-format behavior.

**Independent test**: The page requires the SQLite flag and offers no environment-only alternative.
Ten explicit-format cases preserve both records and their selected writer.
The unsupported explicit `polyglot` case fails without output.

### Tests Before the Documentation Edit

- [X] T028 [US2] Record the ten explicit-format export cases and unsupported selection in `specs/3314-unused-output-defaults/validation.md`. Keep parser and writer decisions real. (delivered: specs/3314-unused-output-defaults/validation.md)

### Documentation and Release Fragment

- [X] T029 [US2] Replace only the false SQLite instruction in `documentation/wiki/Data-Model.md`. Write: Use `--output-format sqlite` to select SQLite output. (delivered: documentation/wiki/Data-Model.md)
- [X] T030 [P] [US2] Create `changelog.d/issue-3314-unused-output-defaults.md` with the existing fragment structure. Describe only the three removals and corrected instruction. (delivered: changelog.d/issue-3314-unused-output-defaults.md)
- [X] T031 [P] [US2] Verify the exact page replacement and unchanged contract in `specs/3314-unused-output-defaults/validation.md`. Require six checked inputs and zero rejected inputs. (delivered: specs/3314-unused-output-defaults/validation.md)

T030 uses one descriptive heading and applicable change-type bullets.
Name issue #3314 without adding a version stamp.
State that the CSV default and explicit SQLite selection remain unchanged.
Do not claim a new output default or repair for issue #3313.

T031 also records the explicit-format tests after the correction.
Keep every other page byte unchanged.
Use the same contract that produced T017.

**Checkpoint**: The combined configuration and documentation repair now satisfies all six source decisions.

## Phase 5: User Story 3 - Preserve Readiness and Session Controls

**Priority**: P1.

**Goal**: Prove that real readiness and session behavior remain unchanged.
This phase adds no production change.

**Independent test**: Six healthy readiness cases and 17 single failures produce exact responses.
Actual Bash preserves credentials, identifiers, cleanup, PID treatment, restart controls, and defaults.

- [X] T032 [US3] Verify protected compose and dashboard bytes in `specs/3314-unused-output-defaults/validation.md`. Retain polyglot configuration and the readiness SQLite default. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T033 [US3] Record all 23 isolated readiness outcomes in `specs/3314-unused-output-defaults/validation.md`. Assert exact formats, checks, calls, statuses, and failures. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T034 [US3] Record actual Bash syntax and clean-session outcomes in `specs/3314-unused-output-defaults/validation.md`. Include the malformed-copy failure and inherited-format cases. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T035 [US3] Record credential transfer and refusal outcomes in `specs/3314-unused-output-defaults/validation.md`. Require four transfer cases, zero missing-token launches, and no disclosure. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T036 [US3] Record two-session isolation and signal cleanup in `specs/3314-unused-output-defaults/validation.md`. Compare exact marker, PID, and exit results with T019. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T037 [US3] Record restart counts, delay sequences, cap, reset, and defaults in `specs/3314-unused-output-defaults/validation.md`. Compare these results with T019. (delivered: specs/3314-unused-output-defaults/validation.md)

Use only the actual script and synthetic application.
Do not replace the loop, trap, parser, or writer with duplicate production logic.
No session test or new session subprocess may exceed 30 seconds.

**Checkpoint**: Readiness and all required session controls match the original behavior.
No real resource check ran.

## Phase 6: User Story 4 - Verify the Repair Without Publication

**Priority**: P2.

**Goal**: Complete truthful local validation within the reservation and publication boundary.

**Independent test**: The original contract is red and the repaired contract is green.
All required invalid inputs fail with accurate counts.
Focused tests and nonempty guard coverage pass.
The local changed-file review contains no path outside the reservation.

### Contract, Focused Tests, and Coverage

- [X] T038 [US4] Audit counted contract evidence in `specs/3314-unused-output-defaults/validation.md`. Require original red, repaired green, all 14 negative cases, and separate additional counts. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T039 [US4] Run the new package and every listed existing focused test without edits. Record complete counts in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T040 [US4] Measure branch coverage for both new helper modules. Record measured files, lines, branches, missing arcs, and thresholds in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)

T039 includes exactly these focused paths:

- `tests/unit/container/output_defaults`
- `tests/unit/container/test_misthelper_session_script.py`
- `tests/unit/container/test_write_session_env_script.py`
- `tests/unit/container/test_build_files_match.py`
- `tests/unit/web_portal/test_dashboard_readiness.py`
- `tests/unit/export/test_data_exporter.py`
- `tests/unit/test_exports.py`
- `tests/test_exports.py`

Use the focused command defined in `plan.md`.
Record its complete invocation only in `validation.md`.
Disable bytecode writes and pytest cache writes.
Use an owned temporary test root and the 30-second pytest limit.
Record collected, executed, passed, failed, and skipped counts.
Required cases must have zero skips and zero unresolved failures.
A missing Bash capability blocks required evidence.
Do not run the production application's test mode.

T040 produces a supplemental coverage configuration under the owned temporary directory.
Measure `tests/unit/container/output_defaults/contract.py` and `tests/unit/container/output_defaults/session.py`.
Do not include assertion modules in the guard denominator.
Enable branch coverage and require a nonzero denominator.
Prove both outcomes of every critical guard decision.
Apply the unchanged direct-report floor of 90 percent.
Keep any applicable whole-source report separate.
Its combined CI floor remains 80 percent.
Focused helper coverage does not prove that combined source gate.
Do not change shared omissions or thresholds.

### Configured Quality Gates

- [X] T041 [US4] Run the complete configured Ruff and Black scopes from `pyproject.toml`. Record both commands and results in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T042 [US4] Read exact CI `MYPY_PATHS` from `.github/workflows/ci.yml`. Record the configured mypy command and result in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T043 [US4] Run the CI Bandit separator check and full configured scan. Record samples, scope, and results in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T044 [US4] Run the unchanged test-quality ratchet with full local scope. Record analyzed tests and `gate_scope` in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T045 [US4] Check local Markdown targets and anchors without network access. Record checked counts and unverified external links in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T046 [US4] Apply configured STE checks and review the writing guide. Record PowerShell, linter, and dictionary limitations in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)

T041 must use complete configured scope, not only changed files.
Use check-only Black with its diff report.
T042 must use the current workflow value and `pyproject.toml` configuration.
At the initial base, that value contains these five paths:

- `src/`
- `MistHelper.py`
- `wsgi.py`
- `scripts/mist_ideas_analyzer_pkg/__init__.py`
- `scripts/mist_ideas_distiller_v2_pkg/__init__.py`

Do not reduce that scope.
State that the configured mypy scope excludes tests.
Do not claim that this run types the new test package.

T043 keeps all configured severity levels and exclusions.
Use both CI samples: `./src/utils/zen_city_metadata.py` and `.\src\utils\zen_city_metadata.py`.
Do not add severity filters or suppressions.

T044 uses `.github/test-quality-config.toml` and `.github/test-quality-baseline.json` unchanged.
Confirm that both new test modules appear while they are untracked.
Record checked test counts.
Preserve the full-scope triggers for configuration, baseline, workflow, and development-requirement changes.
Push and manual CI scopes remain full.
T054 later verifies the CI changed-scope rule against the local comparison base.
Do not fetch or invoke a workflow for this evidence.

T045 includes the corrected page and all existing feature-owned Markdown.
Use an offline-capable pinned tool only after confirming its behavior.
Otherwise, check local targets and anchors directly.
Do not use a network-enabled replacement.

T046 uses `.ste-linter.toml` and its score floor of 80 when the executable is available.
Apply `documentation/ASD-STE100_writing-guide.md` manually when necessary.
The configured dictionary is `data/ste_dictionary.json`.
Manual review does not establish a dictionary-backed score.
Do not download or reconstruct a licensed dictionary.
Do not change pins, exclusions, or dependencies to obtain a pass.
PowerShell absence must not appear as successful PowerShell validation.

### Owned Local Image Evidence

- [X] T047 [US4] Verify an explicit owned local Podman connection before building `Dockerfile` or `Containerfile`. Record ownership, reachability, and architecture in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T048 [US4] Build both image files through the verified local connection. Record commands, results, tags, and image identifiers in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T049 [US4] Inspect both owned images without starting containers. Record absent output declarations and exact cleanup in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)

T047 checks connection and local machine metadata.
The previously successful information result reports Linux arm64.
Verify that the connection belongs to the session's operator.
Do not use an unverified default or remote engine.
Check that the build context contains no real credentials.
Do not start or reconfigure a runtime to bypass a capability gap.

T048 uses the two local build commands in `plan.md`.
Retain the Docker-compatible image format.
Use `localhost/misthelper-tmp-issue3314-dockerfile` and `localhost/misthelper-tmp-issue3314-containerfile`.
Do not overwrite a production tag or another owner's tag.

T049 checks image environment metadata for an `OUTPUT_FORMAT` declaration.
Keep image identifiers and architecture in the evidence record.
Remove only exact owned image tags or artifacts after inspection.
Do not remove shared images or use prune.

If ownership or build capability is unavailable, record that result.
Keep the affected build or inspection task unchecked.
Do not claim a pass.
An information command alone does not satisfy T048 or T049.

No task requires a test or debug container start.
A build alone is not a container start.
Do not invoke a registry workflow just for a build.
If a later start becomes necessary, use the existing compose group or profile.
Use owned `misthelper-tmp-issue3314-*` names and `127.0.0.1` ports from 9600 through 9699.
Keep `compose.yml` unchanged.
Record the exact temporary configuration producer and exact named cleanup in `validation.md`.
Remove only owned containers, volumes, and networks.
Never use bare `podman run`, production ports, prune, or `down -v`.

**Checkpoint**: Every applicable runnable local gate has a result.
Required tests and guard coverage pass.
Any permitted capability gap remains explicit and is not a successful gate.
No publication or deployment occurred.

## Phase 7: Polish and Local Completion

**Goal**: Complete final analysis and one scoped local commit after later implementation authorization.

- [X] T050 Audit the complete 15-file reservation and structural limits. Record all changed-file states and protected bytes in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T051 Analyze the specification, plan, task list, and final owned changes. Write findings and requirement coverage only to `specs/3314-unused-output-defaults/analysis.md`. (delivered: specs/3314-unused-output-defaults/analysis.md)
- [X] T052 Repeat offline links and STE review for the final owned Markdown. Record analysis-file coverage and limitations in `specs/3314-unused-output-defaults/validation.md`. (delivered: specs/3314-unused-output-defaults/validation.md)
- [X] T053 Prepare the verified local completion record in `specs/3314-unused-output-defaults/validation.md`. Keep future publication and exact-main proof explicitly deferred. (delivered: specs/3314-unused-output-defaults/validation.md)
- [ ] T054 Create one scoped local Conventional Commit containing only the reservation. Verify final evidence and a clean worktree through `specs/3314-unused-output-defaults/validation.md`, then stop. The verified post-commit receipt belongs in the session artifact directory.

T050 reviews committed, staged, unstaged, and owned untracked changes.
Reject every changed path outside the reservation.
Confirm that existing tests, protected files, quality settings, and shared state remain unchanged.
Confirm that no sixth test file or extra feature artifact exists.
Review class names, parameter counts, logical blocks, and function lengths.
Do not repair inherited structural debt here.

T051 checks all functional requirements and success criteria.
Check original red evidence, invalid-input decisions, real exports, actual Bash, readiness, scope, and publication boundaries.
Resolve owned implementation findings and repeat affected gates.
Do not rewrite the specification or plan to hide a discrepancy.
Stop and report any finding that requires an out-of-scope change.
Do not run discovery, state hooks, Git hooks, or publication during analysis.

T053 records all completed results and remaining limitations.
Keep blocked execution tasks unchecked.
Required tests, guard proofs, and nonempty coverage must actually pass before the local commit.
Record permitted availability limits without changing a missing result into a pass.

T054 runs only in the later authorized implementation phase.
Stage explicit reserved paths, not the repository as a whole.
Disable hooks for authorized Git writes without changing repository configuration.
Use a scoped Conventional Commit such as `fix(container): remove unused output defaults`.
Include `Closes #3314` in the local message.
Include `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.

Before the local commit, stage the complete reservation and finish the full-scope ratchet.
Retain both full-gate paths: `.github/workflows/ci.yml` and `requirements-dev.txt`.
Record the full-scope command and result in `validation.md`.
Keep the earlier full-scope evidence.
Check the final analysis against these results.
Stage the final owned evidence and verified task status.
Retain the required trailer.
Create the local commit without an amendment.
Verify the final manifest and clean worktree.
Then run the ratchet's CI changed-scope rule against the local comparison base.
That selector compares the base with `HEAD`, not with staged files.
Persist its result outside the checkout and include it in the handoff.
Do not amend the commit to add this result.
Do not perform a push, PR operation, workflow run, merge, or deployment.

## Dependencies and Execution Order

The specification, plan, and ownership precede T001 and are already complete.
Their delivery does not complete any later implementation task.

### Task Prerequisites

| Task | Required prerequisite |
| --- | --- |
| T001 | Existing specification, plan, and ownership are complete. |
| T002 | T001 records the actual failure and recovery status. |
| T003 | T001 and T002 are complete. |
| T004 | T003 is complete. |
| T005, T006 | T004 is complete. The two files have separate writers. |
| T007, T011 | T005 and T006 are complete. The two test files have separate writers. |
| T008 | T007 is complete. |
| T009 | T008 is complete. |
| T010 | T009 is complete. |
| T012 | T011 is complete. |
| T013 | T012 is complete. |
| T014 | T013 is complete. |
| T015 | T014 is complete. |
| T016 | T010 and T015 are complete. |
| T017 | T016 is complete. |
| T018 | T017 is complete. |
| T019 | T018 is complete. |
| T020 | T017, T018, and T019 have verified evidence. |
| T021 | T020 is complete. |
| T022, T023, T024 | T021 is complete. The three files have separate writers. |
| T025 | T022, T023, and T024 are complete. |
| T026 | T025 is complete. |
| T027 | T026 is complete. |
| T028 | T020 is complete. |
| T029 | T028 is complete. |
| T030, T031 | T022, T023, T024, and T029 are complete. The outputs have separate writers. |
| T032 | T025 is complete. |
| T033 | T032 is complete. |
| T034 | T033 is complete. |
| T035 | T034 is complete. |
| T036 | T035 is complete. |
| T037 | T036 is complete. |
| T038 | T027, T030, T031, and T037 are complete. |
| T039 | T038 is complete. |
| T040 | T039 is complete. |
| T041 through T046 | T039 and T040 are complete. Ledger writes remain serial. |
| T047 | T041 through T046 have their required results or explicitly permitted capability reports. |
| T048 | T047 proves an available owned local build connection. Otherwise, the build remains blocked. |
| T049 | T048 produced both owned images. Otherwise, inspection remains blocked. |
| T050 | T038 through T049 have verified results or permitted capability reports. Blocked execution stays unchecked. |
| T051 | T050 is complete. |
| T052 | T051 is complete. |
| T053 | T051 and T052 are complete. All required runnable gates pass. |
| T054 | T053 is complete and the later local-commit phase is authorized. |

### Story Completion Graph

```text
Completed ownership + specification + plan
    -> Worktree recovery and immutable inputs: T001-T003
    -> Shared helpers and both test tracks: T004-T015
    -> Original red, invalid proofs, and control baselines: T016-T020
    -> US1 configuration repair: T021-T027
    -> US2 documentation and combined source green: T028-T031
    -> US3 unchanged readiness and session proof: T032-T037
    -> US4 focused tests, coverage, gates, and image evidence: T038-T049
    -> Final manifest, analyze, and scoped local commit: T050-T054
    -> STOP
```

This graph shows the default serial delivery order.
The prerequisite table identifies allowed parallel work.
US2 tests and its page edit need the shared barrier, not US1 completion.
US2 combined source green and its release fragment wait for all four product edits.
US3 compares the repaired session with the original baseline.
US4 guard creation and invalid proofs occur in the shared foundation, before any product edit.
Its later phase audits those proofs and completes local validation.

No product edit can bypass T020.
One writer owns `validation.md`, even when tasks have independent prerequisites.

## Parallel Execution Examples

### Shared Foundation

After T004, T005 and T006 can run together.
They write `contract.py` and `session.py`.
After both helpers exist, T007 and T011 can run together.
Continue T008 through T010 with the contract-test writer.
Continue T012 through T015 with the session-test writer.
Do not assign two writers to either test file.

### User Story 1

After T021, execute T022, T023, and T024 together.
Each task deletes one declaration from a different file.
Wait for all three before T025 verifies exact bytes and image equality.

### User Story 2

After all four product edits, T030 and T031 can run together.
T030 writes the release fragment.
T031 writes only the validation record.
Its six-input contract does not depend on the fragment.

### User Story 3

T036 can exercise two owned Bash sessions concurrently inside its isolation test.
Use separate identifiers, markers, recorder outputs, and logs.
Coordinate only specifically owned processes.
Execute the ledger-writing tasks serially.

### User Story 4

Execute T038 through T049 serially with one validation writer.
Do not mark shared-ledger tasks as parallel writers.
Keep each gate's temporary output isolated.
No image build needs a concurrent container start.

Nine tasks carry `[P]`.
They form four safe groups: two helpers, two test modules, three configuration edits, and two US2 outputs.

## Implementation Strategy

### Internal MVP

Complete setup and the entire shared guard barrier first.
Complete US1 and validate actual CSV selection and session inheritance.
This is an internal checkpoint only.
US1 alone does not satisfy the required documentation repair.
Complete US2 for the minimum complete four-file product repair.
US3 safety proof and US4 local evidence remain required before the final commit.

### Incremental Local Delivery

Keep each story independently testable through its named criteria.
Retain the original failure evidence throughout implementation.
After any guard change, repeat its original and invalid-input proofs.
After any affected test change, repeat focused tests and coverage.
After any product change, repeat the relevant invariants and configured gates.
Do not change an out-of-scope file to resolve a gate failure.

Complete the final analysis before the final local commit.
Stop with a clean worktree after the scoped commit.
Do not deploy an increment or publish an intermediate branch.

## Deferred Publication Boundary

Publication position is 18, after issue #3300.
Parent PR #3687 owns the current publication window.
These facts do not grant permission.

Future push, PR creation or editing, merge, deployment, and exact-main proof remain deferred.
They are not completed tasks and are not authorized by this list.
Resume only after an explicit parent grant names a verified current base.
The initial SHA, an observed `main`, and sibling reports are not grants.
Any later authorized base change requires the affected local gates again.
