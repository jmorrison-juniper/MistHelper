# Tasks: Local Test-Quality Loop

**Issue**: #3317 only.

**Input**: [spec.md](spec.md), [plan.md](plan.md), and [design/research.md](design/research.md).

**Prerequisites**: [data-model.md](design/data-model.md), [quickstart.md](design/quickstart.md), [validation-matrix.md](design/validation-matrix.md), and [contracts/](design/contracts/).

**Template**: `.specify/templates/tasks-template.md`, read directly.

**Tests**: The specification requires direct guard decisions and real offline analyzer observations.
No implementation task is complete at task generation.

**Organization**: Story phases retain specification order and priorities.
The dependency graph requires guard and analyzer proof before guide edits.
Execute ready tasks from the dependency table, not unchecked tasks by number alone.

## Format: `[ID] [P?] [Story] Description`

- Each task starts with an unchecked box and a unique sequential identifier.
- `[P]` permits parallel work only after the listed prerequisites pass.
- Story tasks use `[US1]`, `[US2]`, or `[US3]`.
- Every task names a concrete file.
- Mark a task complete only after its required checks pass.
- Add the template evidence note: `(delivered: path/to/file.py)`.
- Report validation commands and actual results in the implementation response.
- Do not create an evidence file, summary file, index, or tracking file.
- A skipped, uncollected, unsupported, or timed-out required case blocks completion.

## Path Conventions and Boundaries

Future implementation may change these three existing sections only:

| File | Section |
|------|---------|
| `.github/copilot-instructions.md` | `Validate locally, then push once` |
| `agents.md` | `Local Development Quick Reference` |
| `.github/instructions/git-flow-multi-agent.instructions.md` | `Part 3. GitHub Actions minutes` / `The local-first loop` |

The new package contains exactly these five source files:

```text
tests/guardrails/local_test_quality_loop/
|-- __init__.py
|-- guard.py
|-- fixtures.py
|-- test_guidance.py
`-- test_scope.py
```

Keep test support inside this package.
Do not add `conftest.py`, a command wrapper, a dependency, or a sixth source file.
Keep each new module and class within five children.
Keep methods within 25 lines, five parameters, and five logical blocks.
Use purpose comments on executable Python lines.
Use ASCII action logs before operations and measured result logs afterward.
Use RTK for commands and the repository STE guide for prose.

The plan records existing structural debt and the new guardrail-parent variance.
Do not restructure unrelated directories.

Do not change the installed analyzer, repository settings, baseline, workflows, requirements, hooks, or application behavior.
Do not change `README.md`, `CHANGELOG.md`, release fragments, or shared feature context.
Leave `tests/guardrails/test_quality_ratchet_files.py` unchanged.

## Phase 1: Setup

**Purpose**: Confirm the existing environment and create the package boundary.
Do not install packages or alter an environment to conceal missing capabilities.

- [X] T001 Verify the existing Python runtime and pinned tools against `pyproject.toml` and `requirements-dev.txt`. (delivered: pyproject.toml, read-only verification)
- [X] T002 Create the package marker in `tests/guardrails/local_test_quality_loop/__init__.py`. (delivered: tests/guardrails/local_test_quality_loop/__init__.py)

### Required results

- T001 confirms Python 3.13+, pytest, PyYAML, Git, RTK, and the installed analyzer.
- The required devtools version is `misthelper-devtools` 0.6.0.
- The required pin is `b140350ebc40e61b57a3a65731c0df520f143661`.
- Use installed metadata and CLI help, not an obsolete repository analyzer module.
- If a required capability is unavailable, report the limitation and stop affected checks.
- T002 adds no wrapper or automatic import with side effects.

**Checkpoint**: The package boundary exists and the required tools are available.

## Phase 2: Foundational

**Purpose**: Add shared input accounting and isolated analyzer support.
These prerequisites serve the guide preflight and both proof stories.

- [X] T003 Add failing input-accounting tests in `tests/guardrails/local_test_quality_loop/test_guidance.py`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py, 24 expected red failures)
- [X] T004 [P] Implement `InputLedger` and grouped progress records in `tests/guardrails/local_test_quality_loop/guard.py`. (delivered: tests/guardrails/local_test_quality_loop/guard.py, 24 accounting tests passed)
- [X] T005 [P] Implement isolated Git histories and installed analyzer execution in `tests/guardrails/local_test_quality_loop/fixtures.py`. (delivered: tests/guardrails/local_test_quality_loop/fixtures.py, two real offline observations)
- [X] T006 Implement measured observations and explicit expectation checks in `tests/guardrails/local_test_quality_loop/fixtures.py`. (delivered: tests/guardrails/local_test_quality_loop/fixtures.py, full and empty measurements)

### Input-accounting requirements

Use `TestInputLedger` for T003.
Prove its expected failure before T004.
After T004, run that class with pytest and require success.

The required input manifest contains:

1. `.github/copilot-instructions.md`
2. `agents.md`
3. `.github/instructions/git-flow-multi-agent.instructions.md`
4. `.github/workflows/ci.yml`
5. `.github/test-quality-config.toml`
6. `.github/test-quality-baseline.json`

Read each input once per invocation.
Attempt all independent reads even after one read fails.
Record attempted reads, completed UTF-8 reads, completed validations, guide reads, and completed guide decisions separately.
Validate available TOML and usable JSON baseline identities.
Accept readable empty TOML and fixture-local empty baseline lists.
Reject missing settings before any analyzer invocation.
Preserve named errors and successful independent checks.

### Fixture requirements

T005 creates repositories through `tmp_path`, not the real checkout.
Keep author values, refs, rename settings, and commits fixture-local.
Never fetch a remote or use network services.
Never change real or global Git settings.
Do not import product modules.

Run the active interpreter with this installed module:

```text
python -B -m misthelper_devtools.test_quality_analyzer
```

Use a fresh subprocess and a 30-second timeout for every analyzer observation.
Use fixture-local settings, baseline, report, and summary paths.
Use unique report paths with `--log-level DEBUG`, `--report`, and `--summary`.
Those diagnostic controls must not change selection.
Derive explicit trigger arguments from the live CI decoder completed in US2.
Do not fabricate output or copy the analyzer resolver.

T006 records revisions, argument vectors, exits, stdout, stderr, and report existence.
Decode discovered-file and filtered-finding counts from `gate_scope`.
Decode parsed-file counts from installed logging.
Read exact `analyzed_files` and finding identities from actual reports.
Use completed detector traces when an error prevents report generation.
Represent unavailable fields explicitly.
Assert that valid empty scope produces zero scope counts and no stale report.

Use these stable fixture witnesses:

| Path | Initial content | Expected role |
|------|-----------------|---------------|
| `tests/test_changed.py` | Strong assertion | Controlled changed path |
| `tests/test_witness.py` | `assert result is not None` | Unchanged full-suite witness |

The finding identity is `weak_is_not_none`.
Its settings control is `weak_assert_not_none`.
Do not interchange those identifiers.
An empty baseline accepts no findings.
Unless a case tests baseline triggering, create accepted fixture identities before the comparison base commit.
A full scan of both witnesses expects two analyzed paths and one new finding.
Define expected sets independently of the installed selection implementation.

**Checkpoint**: Input accounting passes and fixture support can collect real observations.
Fixture support alone does not prove the behavioral matrix.

## Phase 3: User Story 1 - Check a Local Commit Before Push (Priority: P1)

**Goal**: Give each named guide a complete, verified local procedure.

**Independent Test**: Check each guide's active procedure against live CI and the verified offline analyzer observations.
The direct live-guide preflight must report three checked guides and six validated inputs.

**Dependency condition**: Complete US2 before T007.
Complete US3 and the red live-guide proof before any guide edit.
This condition preserves the plan's evidence-first handoff.

### Tests for User Story 1

- [X] T007 [US1] Add the direct `TestLiveGuides` preflight in `tests/guardrails/local_test_quality_loop/test_guidance.py`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py)
- [X] T008 [US1] Prove live-guide rejection before edits with `tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py, one expected live failure with 6 reads and 3 validations)

Run T008 with:

```text
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Require a failure that names missing or incorrect active guide procedures.
Retain measured input and guide counts.
Do not use a bad commit, hook, workflow run, or artificial passing skip.

### Implementation for User Story 1

- [X] T009 [P] [US1] Update the local-loop section in `.github/copilot-instructions.md`. (delivered: .github/copilot-instructions.md)
- [X] T010 [P] [US1] Update the local quick reference in `agents.md`. (delivered: agents.md)
- [X] T011 [P] [US1] Update the Part 3 local-first section in `.github/instructions/git-flow-multi-agent.instructions.md`. (delivered: .github/instructions/git-flow-multi-agent.instructions.md)
- [X] T012 [US1] Validate all three guide procedures with `tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py, live green with six validations)

Apply the same complete procedure in each section.
Preserve existing checks and all text outside the named section.
Use the four exact active labels from [local-commands.md](design/contracts/local-commands.md).
Each label must introduce one supported executable fence.

Retain applicable checks before the local commit.
Explain the parent-owned commit of all intended tests and relevant inputs.
Require clean relevant working-tree content before the committed-candidate check.
Define `BASE_REF` as the intended base, not an assumed substitute.
Provide the matching fetch destination and commit-resolution command.
Require the direct input preflight before either analyzer command.

Each guide must contain these complete analyzer controls:

```text
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Recommend `rtk proxy` to preserve complete output.
Use correct PowerShell expansion and continuations in the Windows procedure.

Explain endpoint comparison against `HEAD`, not triple-dot or merge-base selection.
Explain staged, unstaged, and untracked-only path exclusion.
Explain that selected files use current working-tree content.
Explain recognized filenames, deletion behavior, and existing rename destinations.
Explain all four effective trigger paths and their explicit or automatic sources.
Explain full-suite scope for push and manual CI.

Explain discovered, parsed, analyzed, filtered-finding, and new-finding counts without combining their meanings.
Do not invent mode, reason, or changed-path fields on `gate_scope`.
Identify stderr selection messages and report `analyzed_files`.
Distinguish missing-settings guard rejection from analyzer defaults.
Require exit 0 and zero new findings.
Block the procedure on failure, unreadable inputs, unknown bases, or skipped checks.
Require repeated affected checks after candidate, content, or base changes.

For T012, inspect each complete procedure independently.
Repeat the T008 command and require success.
Expect the current counts: six inputs, three guides, two explicit paths, two automatic paths, and four effective paths.
Derive those counts from actual operations.
Do not execute real fetch, commit, or push commands for the walkthrough.

**Checkpoint**: All three guides independently satisfy the same verified command contract.

## Phase 4: User Story 2 - Detect Incomplete Local Guidance (Priority: P1)

**Goal**: Reject incomplete active procedures through a direct, measured guard.

**Independent Test**: Run valid local fixture inputs, then change one input or control at a time.
Require positive success and named negative decisions with exact partial counts.

### Tests for User Story 2

- [X] T013 [US2] Add positive semantic-normalization cases in `tests/guardrails/local_test_quality_loop/test_guidance.py`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py)
- [X] T014 [US2] Add per-guide active-command mutations for T16 in `tests/guardrails/local_test_quality_loop/test_guidance.py`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py)
- [X] T015 [US2] Add live-CI drift and decoding failures in `tests/guardrails/local_test_quality_loop/test_guidance.py`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py)
- [X] T016 [US2] Add six-input safety and partial-count cases for T15 in `tests/guardrails/local_test_quality_loop/test_guidance.py`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py)

Use at most five test classes, including `TestInputLedger` and the later `TestLiveGuides`.
Group normalization, guide decisions, and required-input cases into the remaining classes.
Prove positive tests fail before their missing implementation exists.
Negative tests must assert a guard result, not accept any exception as proof.

T013 covers option order, static quoting, `--option=value`, leading `./`, and identical singleton repeats.
Cover Bash continuations, PowerShell backticks, and token-preserving RTK prefixes.
Preserve variable expansion meaning.

T014 mutates each guide and each required control separately.
Cover missing labels, duplicate labels, absent commands, wrong executables, and obsolete module entry points.
Cover wrong settings, baseline, base expressions, fetch destinations, and commit-resolution references.
Cover omitted or incorrect explicit paths and duplicate explicit values.
Cover conflicting singleton values before and after correct values.
Cover extra roots, disabled rules, baseline writes, pruning, and unsupported shell constructs.
Reject `--include-mist-api` and unknown option controls.
Reject literal single-quoted base variables.
Reject changed-scope controls in the full-suite command.
Reject correct text located only in comments, another section, quotes, or unused examples.
Check the Part 3 parent heading and exact section boundaries.

T015 covers missing jobs, missing or duplicate named steps, malformed YAML, unsupported scripts, and incorrect event scope.
Add a third trigger to live fixture CI while all fixture guides retain the old command.
Expect failure with three decoded explicit paths and six required inputs.
Update all fixture guide commands to that live contract.
Expect success with three explicit, two automatic, and five effective paths.
Do not change the real workflow.

T016 removes each required input independently.
Replace each input with a directory to prove deterministic unreadability.
Include invalid UTF-8 and malformed workflow, TOML, and JSON cases.
Do not rely on permission-sensitive skips.
Assert attempted reads, successful reads, successful validations, guide reads, guide decisions, and decoded path counts.
Accept readable empty TOML and valid empty fixture baseline lists.
Reject missing settings before analyzer invocation.
Keep independent successful reads visible when CI cannot provide a contract.

### Implementation for User Story 2

- [X] T017 [US2] Implement exact-section and active-fence parsing with `SectionCommands` in `tests/guardrails/local_test_quality_loop/guard.py`. (delivered: tests/guardrails/local_test_quality_loop/guard.py)
- [X] T018 [US2] Implement semantic option validation with `CommandControls` in `tests/guardrails/local_test_quality_loop/guard.py`. (delivered: tests/guardrails/local_test_quality_loop/guard.py)
- [X] T019 [US2] Implement named live-step decoding with `CiGateContract` in `tests/guardrails/local_test_quality_loop/guard.py`. (delivered: tests/guardrails/local_test_quality_loop/guard.py)
- [X] T020 [US2] Implement complete comparisons and measured reports with `GuideGuard` in `tests/guardrails/local_test_quality_loop/guard.py`. (delivered: tests/guardrails/local_test_quality_loop/guard.py)
- [X] T021 [US2] Validate positive and negative guard decisions in `tests/guardrails/local_test_quality_loop/test_guidance.py`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py, 396 passed with only the live class excluded)

Keep `guard.py` limited to the five responsibility classes in the plan.
Do not add a cached command, cached trigger constant, shell evaluator, or wrapper.

T019 uses `yaml.safe_load`.
Locate job `test_quality_gate` and exactly one step named `Run test quality ratchet`.
Read the step's environment bindings and supported `scope=()` script.
Decode its pull-request scope and one analyzer invocation without execution.
Retain empty changed scope for push and manual events.
Derive explicit paths from live `--full-gate-path` controls.
Derive automatic paths from the validated settings and baseline arguments.

T020 checks all four active fences in each exact guide section.
Compare the executable, gate, settings, baseline, base relationship, and distinct live trigger controls.
Report every named failure and completed independent operation.
Print the ASCII summary defined in [guardrail.md](design/contracts/guardrail.md).
Count decoded path sets once, not once per guide.
If CI decoding fails, do not claim guide comparisons or decoded paths.
Never print input contents or credentials.

Run T021 with:

```text
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py -k "not TestLiveGuides"
```

Require all positive and mutation assertions to pass.
The excluded live class has its separate red and green checks in US1.
An omitted required mutation or skipped required case blocks completion.

**Checkpoint**: The guard passes valid fixtures and rejects every required input or control mutation.

## Phase 5: User Story 3 - Prove Scope Without Network Access (Priority: P2)

**Goal**: Prove all T01-T16 groups through real installed analyzer observations and direct guard decisions.

**Independent Test**: Run the controlled local matrix without network access.
Assert exact paths, independent counts, known findings, reports, and exits.

### Tests and implementation for User Story 3

- [X] T022 [US3] Add T01 filename inclusion and exclusion cases in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T023 [US3] Add T02 deletion and T03 rename cases in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T024 [US3] Add T04 empty scope and T09 full-suite cases in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T025 [US3] Add T10 alternate-base and divergent-history cases in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T026 [US3] Add T11 unresolved and invalid base cases in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T027 [US3] Add T12 staged-content cases before and after fixture commits in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T028 [US3] Add T13 unstaged and index-content contrasts in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T029 [US3] Add T14 untracked cases before and after fixture commits in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T030 [US3] Add T05 workflow and T06 requirements trigger cases in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T031 [US3] Add T07 automatic settings-trigger cases in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T032 [US3] Add T08 baseline-trigger and removal cases in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T033 [US3] Add T15 analyzer input and invalid-control cases in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T034 [US3] Add T16 behavioral pairs for semantic drift in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py)
- [X] T035 [P] [US3] Validate the complete installed-analyzer matrix in `tests/guardrails/local_test_quality_loop/test_scope.py`. (delivered: tests/guardrails/local_test_quality_loop/test_scope.py, 82 passed and 124 real analyzer runs)
- [X] T036 [P] [US3] Validate the T15/T16 direct guard decisions in `tests/guardrails/local_test_quality_loop/test_guidance.py`. (delivered: tests/guardrails/local_test_quality_loop/test_guidance.py, 396 passed without required-case exclusions)

### Explicit acceptance expectations

| Task | Required offline evidence |
|------|---------------------------|
| T022 | Add and modify `test_*.py` and `*_test.py` names. Reject `testlookalike.py` and `sample_tests.py`. Include weak and strong controls. |
| T023 | Delete recognized tests without nonexistent-file analysis. Cover test-to-test, test-to-non-test, and non-test-to-test renames. |
| T024 | Contrast valid empty scope with full-suite scope. Cover an empty baseline and an accepted-finding baseline. Require missing-baseline failure even at empty scope. |
| T025 | Create common A with weak `tests/test_shared.py`. Base B strengthens that test. Candidate H descends from A and changes only a document. |
| T026 | Contrast a resolving intended reference with unknown, empty, and option-like revisions. Assert exit 2 and unavailable evidence where appropriate. |
| T027 | Exclude staged-only added or modified tests before commit. Include them after fixture commit. Analyze current strong content on an already selected path. |
| T028 | Exclude unstaged-only changes before commit. On a selected path, stage strong content but retain weak working-tree content. Then change only current content to strong. |
| T029 | Exclude an untracked recognized test before commit. Include its known finding after fixture commit. |
| T030 | Cover addition, modification, deletion, and rename for both explicit triggers. Omit or replace each actual control under the same history. |
| T031 | Cover all four settings change forms. Prove defaults after deletion or rename. Contrast unrelated-only history and invalid settings failures. |
| T032 | Cover all four baseline change forms. Assert actual full-suite scanning before missing-baseline exit 2. Restore only the fixture working-tree baseline for paired observations. |
| T033 | Cover missing, empty, unreadable, and malformed settings. Cover invalid baselines at empty scope. Cover incompatible roots, baseline writes, and pruning controls. |
| T034 | Pair omitted explicit controls, disabled `weak_is_not_none`, and extra roots with guard rejection and actual analyzer results. |

Use [validation-matrix.md](design/validation-matrix.md) for every required variant.
Include group identifiers in parametrized case names and printed observation summaries.
Use at most five test classes.
Keep expected path sets explicit.
Never derive expectations from the analyzer resolver or the observation itself.

A selected weak test expects one discovered, parsed, and analyzed file.
It expects one new `weak_is_not_none` finding and exit 1.
A selected strong control expects zero findings and exit 0.
Valid empty scope expects zero scope counts, exit 0, and no report.
Full scope expects both witnesses and the unchanged weak finding.
An accepted fixture baseline changes new findings, not analyzed scope.

For T025, B-to-H must select `tests/test_shared.py` and return its weak finding.
A-to-H must produce valid empty scope.
These observations distinguish endpoint comparison from triple-dot selection.
Do not replace the installed resolver with a merge-base selector.

For T030-T032, every successful trigger observation includes the unchanged witness.
Assert the stderr trigger explanation, two discovered files, two parsed files, and both analyzed paths.
The ordinary empty baseline produces one new finding and exit 1.
Include an accepted-finding full-scan variant with exit 0.

For baseline deletion or rename, counts or reports can remain unavailable after scanning.
Assert actual parsed counts and completed detector traces when available.
The restored-input observation must produce both analyzed paths and the known finding.
Label that observation as controlled dirty fixture evidence, not a clean operator candidate.

For T033, missing or empty settings use installed defaults.
Unreadable or malformed settings fail with exit 2.
Missing, unreadable, malformed, or disabled baselines fail gate mode.
Include the disabled-baseline value `--baseline ""`.
Assert those baseline failures even when no test enters scope.
Do not claim that `ConfigLoader` rejects a missing settings file.
The separate direct guard must reject that missing file.

Run T035 and T036 after all matrix cases exist and T008 proves the live rejection:

```text
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_scope.py
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py -k "not TestLiveGuides"
```

Expected analyzer exits 1 or 2 can occur inside passing tests.
Each test must assert the specific exit and its actual evidence.
Require every applicable T01-T16 variant.
Do not count skips, timeouts, or unavailable capabilities as successful proof.

**Checkpoint**: All required offline groups pass explicit inclusion, exclusion, and failure assertions.
Guide edits can now use verified behavior.

## Phase 6: Polish and Cross-Cutting Concerns

**Purpose**: Verify the complete allowed implementation without delivery actions.

- [X] T037 Validate the new package with unchanged `tests/guardrails/test_quality_ratchet_files.py`. (delivered: tests/guardrails/local_test_quality_loop/, 542 passed including the existing 14 tests)
- [X] T038 Run syntax, Ruff, Black, and type checks for `tests/guardrails/local_test_quality_loop/guard.py` and its four package peers. (delivered: tests/guardrails/local_test_quality_loop/, global style gates and both type scopes passed)
- [X] T039 Check STE, links, and structure using `specs/3317-local-test-quality-loop/design/quickstart.md` and the eight implementation files. (delivered: specs/3317-local-test-quality-loop/design/quickstart.md, 13 Markdown files and 136 functions checked)
- [X] T040 Verify the allowed implementation and exclusions against `specs/3317-local-test-quality-loop/spec.md`. (delivered: specs/3317-local-test-quality-loop/spec.md, only the 18 authorized files changed)

### Local proof and remaining parent work

T001-T040 have local execution evidence.
The complete package contains 528 new cases.
All 542 combined cases passed without skips.
The final affected document and link guards passed 161 tests.
One existing pull-request-only changelog test skipped outside a pull-request event.

Preliminary checks compiled all five new Python files without bytecode output.
Ruff, Black, and explicit five-file mypy checks passed.
The measured method, parameter, class-child, and executable-comment checks passed.
The preliminary unchanged analyzer checked both new test files with zero findings and zero new findings.
Its explicit `--roots` scope does not prove configured committed CI scope.

T038-T040 passed the parent's final relevant validation and candidate review.
Global Ruff and Black passed.
The CI type scope passed for 608 source files.
The explicit package type scope passed for five files.
The installed STE check passed for all eight implementation files, with dictionary coverage unavailable.
The link check read 13 Markdown files and found no broken links.
Structural checks read five Python files and checked 136 functions.
The configured full-suite ratchet checked 949 files and found zero new findings.
The parent owns the clean local commit and the post-commit intended-base comparison.
The implementation agent made no real-repository delivery mutations.

The coordinator released `856e5065413d3026f9c0f6d5222d9d379ec79d8b` as the verified publication base.
The parent rebased without conflicts and repeated the 514 cases with incoming devtools 0.6.0.
The scoped ratchet checked two files and reported zero new findings.
The full-suite ratchet checked 994 files and reported zero new findings.
Current global style, types, links, writing structure, Bandit, and the 105-package hashed runtime audit pass.
The parent retains the one-push, protected-merge, and exact-main proof requirements.
The coordinator later authorized one necessary replacement push for the coupled CodeQL alert 236 correction.
The original failed head remains red evidence.
The new comment cases produce 18 failures before the correction and 31 passes afterward.
Fresh required checks must pass on the replacement head before the protected merge.

Before any push or pull request, the parent must receive a full verified stable `main` SHA.
Only coordinator `6d71fd26-57c2-48c0-abc8-607af98f75d0` supplies that delivery permission.
Do not replace that permission with a locally observed or shortened SHA.

Run T037 with:

```text
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop tests/guardrails/test_quality_ratchet_files.py
```

Retain the existing 14-test proof.
Report actual new collection, pass, failure, and skip counts.
Do not assume a fixed new parametrized test total.

For T038, parse all five Python files without bytecode output.
Run these scoped checks:

```text
rtk proxy python -m ruff check tests/guardrails/local_test_quality_loop
rtk proxy python -m black --check tests/guardrails/local_test_quality_loop
rtk proxy python -m mypy tests/guardrails/local_test_quality_loop --config-file pyproject.toml
```

For T039, give `ste-linter --min-score 80` explicit file arguments.
Include all three guides and all five Python files.
Check method limits, module and class children, ASCII logs, and purpose comments.
Verify issue-owned links after the research move.
Do not create a missing dictionary or change `.ste-linter.toml`.
If the dictionary remains unavailable, report partial vocabulary coverage.
Do not claim a complete dictionary-backed check.

For T040, compare committed, staged, unstaged, and feature-owned untracked changes.
Allow only the three named sections, five package files, and authorized issue-owned artifact adjustments.
Verify unchanged requirements, analyzer inputs, workflows, hooks, README, changelog, and release fragments.
Do not create a manifest file.
Retain commands and measured results in the implementation response.

The clean committed-candidate gate remains parent-owned.
It requires the direct preflight and installed scoped command after the parent's authorized local commit.
The full-suite command remains mandatory for its documented mode.
These constraints do not authorize an implementation agent to commit or deliver.

## Dependencies and Execution Order

### Phase and story dependencies

```text
Setup -> Foundation -> US2 guard decisions
                            |-> US1 live preflight -> required red proof --|
                            `-> US3 offline analyzer proof ---------------|-> US1 guide edits
                                                                         `-> US1 green proof
US1 green proof + US2 decisions + US3 proof -> final local validation
```

US1 has priority P1 but depends on verified behavior.
US2 has priority P1 and has no guide-edit dependency.
US3 has priority P2 and depends on shared fixtures and live CI decoding.
The story completion order is US2, US3, then US1.
The early US1 red proof can run during US3 work.

### Task prerequisites

| Task | Must complete first |
|------|---------------------|
| T001 | None |
| T002 | T001 |
| T003 | T002 |
| T004 | T003 |
| T005 | T003 |
| T006 | T004, T005 |
| T007 | T021 |
| T008 | T007 |
| T009, T010, T011 | T008, T035, T036 |
| T012 | T009, T010, T011 |
| T013 | T006 |
| T014 | T013 |
| T015 | T014 |
| T016 | T015 |
| T017 | T016 |
| T018 | T017 |
| T019 | T018 |
| T020 | T019 |
| T021 | T020 |
| T022 | T006, T021 |
| T023 | T022 |
| T024 | T023 |
| T025 | T024 |
| T026 | T025 |
| T027 | T026 |
| T028 | T027 |
| T029 | T028 |
| T030 | T029 |
| T031 | T030 |
| T032 | T031 |
| T033 | T032 |
| T034 | T033 |
| T035 | T034 |
| T036 | T008, T034 |
| T037 | T012, T035, T036 |
| T038 | T037 |
| T039 | T038 |
| T040 | T039 |

Same-file edits use explicit serial order.
Do not treat separate case groups in `test_scope.py` as independent file writes.

### Ready-task execution sequence

1. Complete T001-T003.
2. Complete T004 and T005, then T006.
3. Complete T013-T021.
4. Complete T007-T008 and T022-T034 on their separate files.
5. Complete T035 and T036.
6. Complete T009-T011, then T012.
7. Complete T037-T040.

## Parallel Examples

Parallel examples describe ready operations.
They do not authorize additional agents.

### User Story 1

After T008, T035, and T036 pass, these independent guide edits are ready:

```text
T009: .github/copilot-instructions.md
T010: agents.md
T011: .github/instructions/git-flow-multi-agent.instructions.md
```

Run T012 only after all three edits finish.

### User Story 2

Keep its tests and guard implementation serial.
The edits share `test_guidance.py` or `guard.py` and require test-first ordering.
After T021, the US1 red proof and US3 scope implementation use separate files.

### User Story 3

After T008 and T034, these independent local validation commands are ready:

```text
T035: pytest tests/guardrails/local_test_quality_loop/test_scope.py
T036: pytest tests/guardrails/local_test_quality_loop/test_guidance.py -k "not TestLiveGuides"
```

Use the complete RTK commands shown in Phase 5.
Keep fixture paths isolated between subprocesses.

The foundation also permits T004 and T005 on different files.

## Implementation Strategy

### MVP

The maintainer-facing MVP is US1's three complete guides.
It requires US2's preflight and US3's verified analyzer behavior.
A documentation-only increment cannot satisfy this specification.

### Incremental implementation

1. Confirm the environment and shared support.
2. Complete guard positive and negative decisions.
3. Demonstrate the unchanged guides' direct failure.
4. Complete real offline scope observations.
5. Add the three guide procedures.
6. Demonstrate direct success and complete local validation.

Stop at a checkpoint if its required evidence fails.
Repair only files within the implementation boundary.
Do not alter a baseline, analyzer, hook, or workflow to obtain success.

## Workflow Limitations and Delivery Constraints

Task generation uses the explicit feature directory:

```text
FEATURE_DIR=/Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-glowing-engine/specs/3317-local-test-quality-loop
TASKS_TEMPLATE=/Users/jmorrison/GitHub/copilot-worktrees/MistHelper/jmorrison-juniper-glowing-engine/.specify/templates/tasks-template.md
AVAILABLE_DOCS=spec.md, plan.md, design/research.md, design/data-model.md, design/quickstart.md, design/validation-matrix.md, design/contracts/
```

These values come from direct inspection, not successful setup JSON.
The checked-in `setup-tasks.ps1` exists.
Neither `pwsh` nor `powershell` is available.
The setup invocation failed because `pwsh` was absent.
No setup script ran and no shared feature context changed.

The issue-owned research moved from `research.md` to `design/research.md`.
The feature root and design directory each retain five direct children.
Task generation creates no summary, index, context record, or tracking file.

Optional Git hooks lack authorization.
The companion hook is registered, but its local command and scripts are absent.
The mandatory `speckit.companion.after-tasks` dispatch failed with `No such file or directory`.
No companion hook executed and no replacement context record exists.
Do not fabricate hook completion or a replacement `.spec-context.json`.
Existing branch and context reservations replace branch creation and shared context hooks.

The parent owns every real-repository commit and delivery action.
No task authorizes branch creation, branch changes, commits, pushes, pull requests, issues, agents, or workflows.
Coordinator `6d71fd26-57c2-48c0-abc8-607af98f75d0` must supply a full verified stable `main` SHA.
Before that verified SHA arrives, do not push or open a pull request.
Do not substitute the current branch revision or an abbreviated SHA.

The final parent-owned pull request must include the internal-only rationale.
This feature changes development guidance and direct proof only.
It changes no customer or application behavior.
It requires no README change or release fragment.
Keep that rationale as a delivery constraint, not an implementation checklist task.
