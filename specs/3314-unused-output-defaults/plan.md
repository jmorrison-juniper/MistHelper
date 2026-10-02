# Implementation Plan: Remove Unused Output Defaults

**Branch**: `jmorrison-juniper-unused-output-defaults` is app-managed.

**Date**: 2026-10-01

**Input**: [The existing specification](spec.md) for [issue #3314](https://github.com/jmorrison-juniper/MistHelper/issues/3314).

**Claim owner**: Session `694ad69e-4090-4f3e-91bd-4bc197e768be`.

**Initial base**: `ff3cc1bea8ab58026210a968ff1465f61c9fec78`.
The observed checkout matches this base.
This reference does not grant publication permission.

**Current phase**: Write only `specs/3314-unused-output-defaults/plan.md`.
Do not stage or commit this plan.
Do not implement the repair during this phase.

## Summary

Use the selected option 2.
Remove the unused SQLite declaration from the session script and both image files.
Correct the SQLite selection instruction in `documentation/wiki/Data-Model.md`.
Keep the CSV default and explicit SQLite selection unchanged.

Create the counted contract before later production edits.
Capture its failure against the original files.
Prove its rejection decisions with owned temporary inputs.
Use actual Bash execution, the actual CLI parser, and actual local exporters.
Replace readiness resource checks with synthetic results.

This named artifact workflow replaces feature discovery and numbering.
Use the [repository plan template](../../.specify/templates/plan-template.md) without creating its additional artifact files.
Keep the research, design, and validation guide inside this plan.
Do not run setup scripts, agent-context scripts, Git hooks, or companion state hooks.
Do not write shared `.specify` state or `.spec-context.json`.

## Technical Context

**Language/Version**: Python 3.13 or newer for tests.
Use the existing Bash session script and OCI image syntax.

**Primary Dependencies**: Existing pytest, pytest-timeout, pytest-cov, coverage, and Flask.
Use standard-library file, subprocess, argument, CSV, SQLite, text, and AST facilities.
Add no runtime or development dependency.
Keep all dependency pins unchanged.

**Storage**: Synthetic CSV and SQLite outputs under `tmp_path`.
Keep remote database writes inactive.
Introduce no production entity, schema, primary key, or migration.

**Testing**: A six-input source contract, 14 required negative cases, and 15 valid selection cases.
Add actual session tests and isolated readiness tests.
Reuse `tests/unit/container/bash_support.py` for actual Bash capability.
Keep existing tests and helpers read-only.

**Target Platform**: Linux container scripts with local macOS validation.
Do not assume that a Bash executable can open the selected test paths.
Use the capability result from the existing helper.

**Project Type**: A configuration and documentation repair for an SSH CLI application.
The existing Flask readiness interface remains unchanged.

**Performance Goals**: Add no production processing or startup delay.
Limit every session test and session subprocess to 30 seconds.
Use existing restart overrides for short test runs.

**Constraints**: Use synthetic credentials and a clean environment.
Use no Mist cloud, remote database, production port, or production store.
Keep all test writes under `tmp_path`.
Use clear exact assertions and rare comments that explain a non-obvious reason.

**Scale/Scope**: Four product paths, five reserved test files, five phase records, and one reserved release fragment.
The complete future reservation has 15 paths.
Only this plan is writable now.

## Constitution Check

Use the [constitution](../../.specify/memory/constitution.md), version 1.5.0.
The design passes the scope and safety review with the explicit exceptions below.
These exceptions do not amend repository rules.

| Principle | Design decision |
| --- | --- |
| I. Structural discipline | Keep the new test package at five files. Keep the feature directory at five direct files. Record existing parent debt and the fixed reservation exceptions below. |
| II. Class-based architecture | Put substantive test helpers in named classes. Add no production wrapper, entry point, or compatibility layer. |
| III. Safety-first | Use only synthetic inputs. Replace resource checks before execution. Keep paths, logs, markers, and exports under `tmp_path`. Never print a token. |
| IV. Deployment pipeline | Run later local gates directly. Later authorized implementation stops at a clean local commit. Publication and deployment remain blocked by the parent boundary. |
| V. Observability | Give contract results exact counts, paths, and reasons. Keep diagnostics ASCII. Report missing capabilities as missing, not passed. |
| VI. Comments | The request requires rare, meaningful comments. Do not add comment sweeps to unchanged production blocks. Record this narrow rule exception below. |
| VII. Action logging | Preserve production logging. Give test operations useful counted diagnostics without credential values. Do not add production format logging. |

Use Python 3.13 or newer and the existing dependency set.
Keep `DataExporter.write_with_format_selection()` as the actual export entry point.
Do not change database strategy mappings.
Use Podman only for an owned local build when that capability is available.
No container must start for this repair.

**Before research**: The selected repair, file ownership, and safety boundary are fixed.
**After design**: The same boundary holds.
The design has no unresolved clarification.
Execution gates remain pending for later phases.

## Project Structure

### Documentation for this feature

```text
specs/3314-unused-output-defaults/
    spec.md
    plan.md
    tasks.md
    analysis.md
    validation.md
```

The specification already exists.
This phase creates only `plan.md`.
Later phases own `tasks.md`, implementation evidence in `validation.md`, and `analysis.md`.
Do not create `research.md`, `data-model.md`, `quickstart.md`, `contracts/`, checklists, or a separate manifest file.

### Reserved tests

```text
tests/unit/container/output_defaults/
    __init__.py
    contract.py
    session.py
    test_contract.py
    test_session.py
```

| File | Later responsibility |
| --- | --- |
| `__init__.py` | Mark the test package. Perform no import-time operation. |
| `contract.py` | Own input reading, source decisions, and counted contract results. Contain test helpers only. |
| `session.py` | Own temporary session fixtures, synthetic application recording, and bounded actual Bash execution. Contain test helpers only. |
| `test_contract.py` | Test live and temporary source contracts, CLI selection, real exports, and readiness decisions. |
| `test_session.py` | Test Bash syntax, environment behavior, credentials, isolation, cleanup, and restart controls. |

Use small helper methods and parameterized cases.
Keep new functions within the constitution's parameter, block, and length limits.
Keep new module and class structures within their child limits.
Do not add a sixth package file or a shared `conftest.py`.

### Product paths for later implementation

| Path | Allowed change |
| --- | --- |
| `container/scripts/misthelper-session.sh` | Delete only `export OUTPUT_FORMAT=sqlite`. |
| `Dockerfile` | Delete only `ENV OUTPUT_FORMAT=sqlite`. |
| `Containerfile` | Delete only `ENV OUTPUT_FORMAT=sqlite`. |
| `documentation/wiki/Data-Model.md` | Replace the false selection instruction with `Use --output-format sqlite to select SQLite output.` Keep the flag in Markdown code notation. |

The later release fragment is `changelog.d/issue-3314-unused-output-defaults.md`.
It is reserved, not writable during planning.

Keep `compose.yml` and `web_portal/routes/dashboard.py` byte-identical to the initial base.
Keep `MistHelper.py`, `src/`, and `container/scripts/write-session-env.sh` unchanged.
Keep `README.md`, `CHANGELOG.md`, instructions, other specifications, dependency pins, schemas, and primary keys unchanged.
Keep baselines, suppressions, exclusions, and thresholds unchanged.
Issue #3313 and its password allowlist repair are outside this scope.

## Phase 0: Research Decisions

The source review confirms three unused declarations and one false documentation instruction.
All six contract inputs match the initial base.
`Dockerfile` and `Containerfile` are byte-identical.

| Decision | Rationale | Alternatives considered |
| --- | --- | --- |
| Remove declarations without adding an environment default. | `MistHelper._add_output_format_arguments()` uses `default="csv"` and choices `csv` and `sqlite`. The user selected this compatibility repair. | Reading `OUTPUT_FORMAT` in the CLI would change behavior and exceed option 2. |
| Keep readiness configuration separate from CLI selection. | `dashboard._configured_output_format()` reads the environment, applies `strip().lower()`, and defaults to SQLite. Compose supplies `polyglot`. | Removing this reader or its backend checks would remove active behavior. |
| Execute actual Bash with existing path overrides. | The script already exposes application, log, session, environment-file, and Python-command overrides. | A rewritten loop or text-only session test would not prove actual session behavior. |
| Call the actual parser, runtime selection function, and exporters without full startup. | Passive import and isolated test seams permit local selection and export evidence. Full startup can load credentials or authenticate. | A duplicate parser, a production wrapper, or mocked local writes would weaken the compatibility proof. |
| Measure guards separately from repository source coverage. | `pyproject.toml` omits `tests/*`. A normal report can omit every new helper line. | Changing shared omissions or lowering a threshold would hide missing evidence. |

Read-only prior art provides these reuse points:

- `tests/unit/container/bash_support.py` provides `BashHarness`, `BASH_PATH`, and `BASH_SKIP_REASON`.
- Existing session tests provide synthetic applications, restart cases, token aliases, and log assertions.
  Their subprocess timeout is 60 seconds.
  New session subprocesses must use 30 seconds.
- Existing environment-writer tests provide a minimal environment and isolated shell round trips.
  Do not copy the complete ambient environment.
- Existing readiness tests provide a Flask test client and resource replacements.
- Existing export tests provide real CSV and SQLite output checks under a temporary working directory.
  They do not prove the complete environment and CLI selection matrix.

Tool availability affects later evidence, not the selected design.
The planning review found Python 3.9.6 on `python3` and no worktree `.venv`.
It found Podman, but did not verify runtime reachability or ownership.
It found no `pwsh`, `ste-linter`, or `test-quality-analyzer` on `PATH`.
The configured `data/ste_dictionary.json` is absent.
Do not treat these observations as executed gates.

## Phase 1: Design and Compatibility Contracts

### Test-only data model

No production data model changes.
Use a contract input set with six explicit paths and their source kinds.
Use a contract result with `expected`, `checked`, `rejected`, and path-specific failures.
Keep session observations limited to arguments, selected safe environment fields, launch counts, exit status, and owned paths.
Use credential fingerprints or exact synthetic-value comparisons inside the recorder.
Do not put token values in recorder output or logs.

Use two flat synthetic records for each export case.
Use the existing `listOrgSites` strategy and a safe bare destination name.
Preserve existing business keys and record values.
Do not add schema definitions or a new export strategy.

### Six-input source contract

| Required input | Required decision |
| --- | --- |
| `container/scripts/misthelper-session.sh` | No active `OUTPUT_FORMAT` assignment remains. |
| `Dockerfile` | No active `ENV` declaration assigns `OUTPUT_FORMAT`. |
| `Containerfile` | No active `ENV` declaration assigns `OUTPUT_FORMAT`. |
| `documentation/wiki/Data-Model.md` | The SQLite selection instruction requires `--output-format sqlite` and offers no environment-only alternative. |
| `compose.yml` | The existing `OUTPUT_FORMAT=polyglot` declaration remains. |
| `web_portal/routes/dashboard.py` | The reader, normalization, SQLite default, backend selection, and readiness responses remain. |

Read every required input, even when an earlier input fails.
Count an input as checked only after a successful read.
Count each rejected input once, including a read failure.
Report all failing paths and exact reasons.
Success requires `expected == 6`, `checked == 6`, and `rejected == 0`.
Do not replace an unreadable input with empty text.
Do not skip a required input.

Check active declarations, not the substring `OUTPUT_FORMAT=sqlite` alone.
Reject assignments with another value, including `polyglot`.
Handle whitespace, quoting, shell export forms, and image `ENV` declaration forms.
Ignore comment-only declarations.
Use standard-library text processing and AST inspection where appropriate.
Do not execute an input to inspect its declarations.
Check the actual SQLite instruction, not a flag in an unrelated example.
Use separate behavior tests for the protected readiness decisions.

Create repaired copies of all six inputs under `tmp_path`.
Apply repairs only to those copies while constructing test fixtures.
Use those copies for these 14 required negative cases:

| Mutation | Case count | Required result |
| --- | --- | --- |
| Restore each original dead assignment separately. | 3 | Failure, six checked inputs, and the altered source in the failure list. |
| Add an active `OUTPUT_FORMAT=polyglot` assignment to each repair source separately. | 3 | Failure with the altered source named. |
| Restore the false instruction, then remove the required flag in a separate case. | 2 | Failure with the page named. |
| Make each required input unreadable separately. | 6 | Failure with six expected inputs, five checked inputs, one rejected input, and the exact unreadable path. |

Use a missing file or a directory in place of the owned file for reliable read failures.
Do not depend only on permission bits, which can behave differently under privileged accounts.
Add a narrow `PermissionError` test if that error decision needs separate coverage.
Add valid comment cases and invalid compose and readiness cases.
Record these additional case counts separately.
Prove both outcomes of every critical guard decision.

Retain the measured SHA-256 values for all six original inputs.
Restore only the three removed declarations and the replaced sentence in temporary copies.
Require each restored copy to match its measured original hash.
This proof preserves the exact original bytes without Git history.
Shallow continuous integration checkouts need no old commit object.
Reject altered bytes instead of applying a history-dependent fallback.

### CLI selection and actual export contract

Execute these 15 valid cases with two records each:

| Environment `OUTPUT_FORMAT` | No format flag | Explicit `csv` | Explicit `sqlite` |
| --- | --- | --- | --- |
| Unset | CSV | CSV | SQLite |
| `csv` | CSV | CSV | SQLite |
| `sqlite` | CSV | CSV | SQLite |
| `polyglot` | CSV | CSV | SQLite |
| `synthetic-unsupported` | CSV | CSV | SQLite |

Set a clean synthetic environment and change the working directory to `tmp_path` before imports.
Import the actual CLI module without invoking `MainEntrypoint.run()` or either bootstrap startup path.
Call `MistHelper._build_argument_parser().parse_args()` with the case arguments.
Use an isolated `AppContext` and the actual `_configure_runtime_options()` selection.
Replace only telemetry and harmless deferred dependencies that this isolated call needs.
Do not replace the parser's format decision.
Restore context, resolver bindings, environment, and exporter caches after each case.

Call the real `DataExporter.write_with_format_selection()` without a format override.
Keep the CSV writer, SQLite writer, processing helpers, and schema helpers real.
Set `MISTHELPER_STANDALONE=true` and route all database paths under `tmp_path`.
Make any unexpected authentication, host probe, router construction, or network access fail the test.

Assert the exact parsed format and exact runtime format.
Assert exporter success and both stored records.
Read CSV with `csv.DictReader`.
Read SQLite with the standard-library connection and explicit row queries.
Check the existing key treatment without changing it.
A CSV case must create no SQLite result.
A SQLite case must create no CSV result.

Also parse `--output-format polyglot` with environment value `polyglot`.
Assert `SystemExit.code == 2` and zero export output.
This readiness value must not become a CLI choice.
Real local export evidence is feasible with the existing writers.
If missing capabilities block it, report the block.
Do not substitute mocked writes and report success.

### Actual Bash and session contract

Use the actual repository script with the capability-checked Bash executable.
Run `bash -n` against that script.
Also run it against a malformed owned temporary copy.
Assert status 2 and a syntax diagnostic that names the temporary script.
Do not use syntax success as a substitute for actual session execution.

Put the synthetic `MistHelper.py`, session environment file, logs, markers, and recorder data under `tmp_path`.
Set all existing application, session, log, runtime-log, and Python-command overrides explicitly.
Use a controlled session file to keep any operational database path under `tmp_path`.
Supply `HOME`, temporary paths, and a controlled `PATH`.
Do not inherit real tokens, `BASH_ENV`, cloud settings, or database settings.
Do not launch the production application or SSH daemon.

Cover these outcomes with exact assertions:

- A clean exit returns 0 after one launch.
  The application arguments remain exactly `["MistHelper.py"]`.
  No format flag appears.
  Unset `OUTPUT_FORMAT` stays unset.
  Supplied format values remain inherited.
  Do not add an `unset` operation.
- Both token aliases work from an owned session file and from an explicit synthetic environment.
  These are four transfer cases.
  No credentials cause status 1 and zero launches.
  Captured output and all logs contain none of the supplied synthetic token values.
- Two distinct synthetic `SSH_CONNECTION` values produce separate normalized session identifiers.
  Each session removes only its own pre-created marker.
  Verify cleanup on normal exit, `INT`, and `TERM`.
  Preserve the existing PID-file treatment.
  Compare signal outcomes with the original script before production edits.
- Consecutive failures stop at the configured attempt limit with status 1.
  Verify exact launch counts and exact reported delay sequences.
  Use short existing overrides to prove doubling and the cap.
  Use a controlled healthy run to prove count and delay reset.
- Preserve defaults of five attempts, 30 healthy seconds, two initial seconds, and a 60-second cap.
  Enforce every session timeout at 30 seconds.
  Terminate only specifically owned child processes and wait for their cleanup.

Removing one export must leave every other script byte unchanged.
Do not alter restart logic, traps, arguments, credential handling, or log text.

### Unchanged readiness contract

Use a Flask test client without opening a port.
Replace all five resource checks before requesting `/ready`:
`_check_data_dir_writable`, `_check_mist_api_session`, `_check_sqlite_database`, `_check_arangodb`, and `_check_redis`.
Keep the route, format reader, check selection, and response construction real.
Unexpected resource access must fail.

| Environment | Exact active check names |
| --- | --- |
| Unset, `sqlite`, or `standalone` | `data_directory_writable`, `mist_api_session`, `sqlite_database` |
| ` PolyGloT ` | `data_directory_writable`, `mist_api_session`, `arangodb`, `redis` |
| `csv` or `synthetic-unsupported` | `data_directory_writable`, `mist_api_session` |

Assert the normalized `output_format`, exact check names, and recorded check calls.
For each of these six environment cases, healthy results return 200 with `status == "ready"` and no failed checks.
Fail each selected check separately.
Assert 503, `status == "not ready"`, and the exact single failure name.
This gives six healthy cases and 17 single-failure cases.
A polyglot case must never select SQLite.
An unset format must retain the readiness SQLite default.

## Phase 2: Later Work Order and Validation Guide

This section defines later work.
It does not create tasks or implementation evidence now.

1. Create the five reserved test files after implementation authorization.
   Build the six-input contract and repaired temporary fixtures first.
   Record the unchanged base bytes before any product edit.
2. Run the success contract against the original live sources.
   Capture a red result with six expected inputs, six checked inputs, and four rejected inputs.
   Name the script, both images, and the page.
   Capture relevant session red results and baseline signal outcomes.
   Record commands, exit codes, counts, and contract revision in `validation.md`.
3. Remove only the three declarations and correct only the one documentation instruction.
   Require exactly one occurrence of each original line before deletion.
   Compare repaired bytes with the base bytes minus that line.
   Compare the page with the base page plus only its instruction replacement.
   Keep both image files byte-identical.
4. Run the unchanged contract, negative cases, compatibility tests, and applicable local gates.
   Record commands, checked counts, results, missing capabilities, and coverage details in `validation.md`.
   Add the reserved release fragment only in its later authorized phase.
   Do not weaken tests or quality settings.
5. Review the complete owned manifest and later analysis.
   Include committed, staged, unstaged, and owned untracked files in the review.
   Reject any path outside the reservation.
   After later commit authorization, commit locally without Git hooks and stop with a clean worktree.
   This planning phase performs none of those Git actions.

### Focused local tests

Use the existing pinned Python 3.13 development environment.
Run commands from the repository root.
Run tests with an allowlisted synthetic environment.
Do not load a real `.env` file.
Disable bytecode writes and pytest cache writes.
Put coverage data, temporary roots, and test output under an owned temporary directory.
Here, `OWNED_TMP` names that directory and `python` names the supported interpreter.

```bash
python -m pytest -p no:cacheprovider --basetemp "$OWNED_TMP/pytest" --timeout=30 \
  tests/unit/container/output_defaults \
  tests/unit/container/test_misthelper_session_script.py \
  tests/unit/container/test_write_session_env_script.py \
  tests/unit/container/test_build_files_match.py \
  tests/unit/web_portal/test_dashboard_readiness.py \
  tests/unit/export/test_data_exporter.py \
  tests/unit/test_exports.py tests/test_exports.py
```

Record collected, executed, passed, failed, and skipped counts.
Required cases must have zero skips and zero unresolved failures.
A missing Bash capability must block required session evidence, not produce a successful skip.
Do not run the production `MistHelper.py --test` command for this repair.

### Guard branch coverage

Measure `contract.py` and `session.py` separately because shared coverage settings omit tests.
Use an owned temporary coverage configuration for this supplemental measurement.
Enable branch coverage and include the two helper files in the report.
Do not count test assertion files as the guard denominator.
Do not change repository coverage omissions or thresholds.

Record measured files, line counts, branch counts, missing lines, and missing branch arcs.
Require a nonzero denominator and both outcomes of every critical guard decision.
Apply the configured direct-report floor of 90 to the supplemental report.
Keep any applicable whole-source report separate.
The current combined CI source gate uses an 80 percent floor.
Do not claim that focused helper coverage proves the combined source gate.
Do not treat an empty report as passed.

### Configured local gates

| Gate | Required command or check |
| --- | --- |
| Ruff | `python -m ruff check .` with the complete configured scope. |
| Black | `python -m black --check --diff .` with the complete configured scope. |
| mypy | Read `MYPY_PATHS` from `.github/workflows/ci.yml`. Run `python -m mypy` with exactly those paths and `--config-file pyproject.toml`. |
| Bandit | Run the configured separator check, then `python -m bandit -c pyproject.toml -r .`. Keep all severity levels and existing exclusions. |
| Test-quality ratchet | Run `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`. Keep both files unchanged. |
| Markdown links | Check local targets and anchors in the owned Markdown and the corrected wiki page without network access. Record checked counts and unverified external links. |
| STE | Run `ste-linter --config .ste-linter.toml --min-score 80` on owned text when available. Apply the writing guide and report dictionary limits. |
| Source and image invariants | Compare protected files with the initial base. Compare both full image files. Verify the single-line image and session deletions. |

At the reviewed base, the exact mypy command is:

```bash
python -m mypy src/ MistHelper.py wsgi.py \
  scripts/mist_ideas_analyzer_pkg/__init__.py \
  scripts/mist_ideas_distiller_v2_pkg/__init__.py \
  --config-file pyproject.toml
```

Read the workflow again before validation.
Use its current exact value if the authorized base changes.
Do not reduce mypy to the changed files.
Tests are excluded by the configured mypy scope.
Do not claim that this command types the new tests.
Record any non-applicability reason or missing tool explicitly.

Run the Bandit separator check with the two CI samples:
`./src/utils/zen_city_metadata.py` and `.\src\utils\zen_city_metadata.py`.
Do not add severity filters or suppressions.

For the ratchet, first use full local scope while the new tests are untracked.
Verify that both new test files appear in the analyzed set.
Record `gate_scope` and checked test counts.
After an authorized local commit, also use the CI changed-scope rule against the local comparison base.
Retain `--full-gate-path .github/workflows/ci.yml` and `--full-gate-path requirements-dev.txt`.
Baseline or configuration changes require full scope.
Changes to either full-gate path also require full scope.
Push and manual CI events always use full scope.
Do not fetch, change baselines, or invoke a workflow to obtain this local evidence.

Run link and STE tools directly, not through Git hooks.
Do not inherit hook exclusions that omit the feature directory or wiki page.
Confirm offline behavior from the pinned link tool before use.
If it lacks that mode, check local targets and anchors without a network-enabled replacement.
Apply the [writing guide](../../documentation/ASD-STE100_writing-guide.md) manually when the STE executable is unavailable.
Manual review does not establish a dictionary-backed score.
Do not download or reconstruct a licensed dictionary.
Missing tools, dictionaries, or measurements remain explicit capability gaps.
Do not add dependencies, update pins, or change exclusions to obtain a passing result.

### Owned local image builds

No container must start.
Before a build, inspect Podman connection metadata and local machine metadata.
Confirm that the selected runtime belongs to this session's operator.
Confirm that it is local and reachable with an explicit connection.
Do not use an unverified default or remote engine.
Do not start or reconfigure a runtime to bypass a missing capability.

If the owned local runtime is reachable, build both image files:
Set `LOCAL_PODMAN_CONNECTION` to the verified connection name.

```bash
podman --connection "$LOCAL_PODMAN_CONNECTION" build --format docker \
  -f Dockerfile -t localhost/misthelper-tmp-issue3314-dockerfile .
podman --connection "$LOCAL_PODMAN_CONNECTION" build --format docker \
  -f Containerfile -t localhost/misthelper-tmp-issue3314-containerfile .
```

Record connection ownership, both commands, both results, and image identifiers.
Keep issue-specific local tags separate from production tags.
Remove only owned build artifacts when their evidence is complete.
If the executable, ownership proof, or connection is unavailable, record the build as unavailable.
Do not report it as passed.
Do not push images, run containers, deploy services, use production stores, or invoke an image workflow.
Never use bare `podman run`.

## Complexity Tracking

Counts below refer to tracked direct children at the initial base.
They exclude caches and Git metadata.
The current named feature directory already contains the specification.
This phase adds only its second direct file.

| Existing debt or narrow exception | Treatment for #3314 | Separate incremental action |
| --- | --- | --- |
| Repository root has 48 direct children. | Edit only existing image files in the later repair. Add no root file. | Review grouped root content in independent structural work. |
| `specs/` has 746 direct children. | Use the already claimed feature directory. Keep that directory at five direct files. | Review archival groups in independent specification maintenance. |
| `documentation/wiki/` has 25 direct children. | Correct one instruction in an existing page. Add no page. | Review wiki groups with the documentation owner separately. |
| `tests/unit/container/` has seven direct children. The fixed reservation adds an eighth child. | This is an explicit reservation exception. Put all new tests inside the five-file package. Do not move or edit prior tests. | Group existing container tests in a separate repair after coordination. |
| `changelog.d/` has 44 direct children. The reserved fragment adds one later. | The unique fragment avoids shared changelog edits. Do not add it now or reorganize fragments. | Review grouped fragments with the release tooling owner separately. |
| Broad comment and logging rules conflict with the requested narrow repair. | Use rare reason comments in new test helpers. Preserve all other production bytes and existing logging. | Resolve the rule difference only in separately requested governance work. |
| Automatic setup, hooks, publication, and deployment exceed this phase. | Write one named plan. Later work stops at the authorized local commit. Allow only verified local image builds. | Resume later delivery only under the parent's explicit verified-base grant. |

Do not refactor unrelated parents or inherited source structure for this issue.
These records do not authorize another file change.

## Local-Only Completion Boundary

Publication position is 18, after issue #3300.
Parent PR #3687 currently holds publication.
Neither planning nor later local validation grants permission to publish.

Stop this phase after writing and checking only `plan.md`.
Keep the original specification and all other workspace files unchanged.
Do not change Git branches, commits, issues, pull requests, or shared feature state.
Do not run Git hooks.

Later implementation stops at a clean local commit until the parent grants publication against a verified current base.
The initial SHA, an observed `main`, and sibling reports are not grants.
Any authorized base change requires the relevant local gates again.
This plan claims no implementation, test, coverage, STE score, or image-build result.

## Authorized delivery on 2026-10-02

The parent explicitly granted sole position-18 publication and delivery.
The granted main is `7a4435bdf8ceff7e1dd527e4d2fd854e79542f37`.
The grant supersedes the historical local-only pause.
It changes no product requirement or file reservation.

Rebase only this worktree onto the granted main.
Recheck the live claim and every open pull request's complete file list.
Repeat the six-input red and green decisions and all 342 current focused cases.
Repeat the current configured local gates and the six-input, three-guide preflight.
Build both current image files with owned local tags and remove only owned resources.
Commit the final evidence before the required clean-commit ratchet.
Fetch, resolve, and compare the intended `origin/main` base consistently.
Push once after the complete local proof.

Use the complete current pull request template with accurate commands and results.
Post one public ownership comment.
Require fresh quality, title, applicable STE, CodeQL analysis, and separate required CodeQL results.
Require all 15 current strict contexts and the exact granted base.
Stop if an unrelated change advances main.

Use a protected full-head-match squash merge without `--admin`, `--auto`, or `--delete-branch`.
Verify the actual resulting main SHA and tree.
Run local proof with this worktree at that exact main commit.
Persist the final receipt in the pull request and session artifacts.
Do not change the production stack, stores, ports, or named volumes.
Pause after the handoff.
The parent alone releases the next issue.
