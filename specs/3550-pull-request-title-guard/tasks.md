# Tasks: Pull request title guard

**Input**: Design documents from `specs/3550-pull-request-title-guard/`.

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md), and [contracts/](contracts/).

**Template**: `.specify/templates/tasks-template.md`.

**Issue**: [MistHelper #3550](https://github.com/jmorrison-juniper/MistHelper/issues/3550).

**Branch**: `jmorrison-juniper-pull-request-title-guard`.

**Owner**: Parent session `dc0c00d5-a429-416a-9549-ccfa49bb688c`.

**Merge coordinator**: Parent session `6d71fd26-57c2-48c0-abc8-607af98f75d0`.

**Tests**: FR-018 and FR-019 require offline behavior tests and policy contracts.

**Organization**: Each user story has its own phase and independent test criteria.
Parent validation and parent delivery have separate task lists.
All 42 tasks start unchecked.

## Format: `[ID] [P?] [Story] Description`

- `[P]` identifies tasks that can run together after their listed prerequisites finish.
- `[US1]` through `[US4]` identify the corresponding user stories in `spec.md`.
- Each task names its exact file paths.
- Mark a task complete only after its evidence proves the stated result.
- Add an evidence note in this form: `(delivered: path/to/file.py)`.
- If a task needs a live system or an owner decision, retain its unchecked state until that condition resolves.

## Path Conventions

All paths are relative to this worktree's repository root.
Use `SPECIFY_FEATURE_DIRECTORY=specs/3550-pull-request-title-guard` for every SpecKit step.
The repository template and feature-owned context replace the unavailable PowerShell and companion commands.
Skip optional commit hooks.

This tasks step writes only these files:

- `specs/3550-pull-request-title-guard/tasks.md`
- `specs/3550-pull-request-title-guard/.spec-context.json`

The tasks below describe later work.
Do not implement code, install packages, create issues or branches, commit, push, or open a pull request during task generation.
Do not invoke another agent during this tasks step.
Do not access the main checkout.

### Later implementation ownership

The issue ownership comment permits only these implementation paths:

- `.github/workflows/pull-request-title.yml`
- `scripts/pr_title_guard/__init__.py`
- `scripts/pr_title_guard/__main__.py`
- `tests/unit/scripts/test_pr_title_guard.py`
- `tests/guardrails/test_pr_title_workflow.py`
- `.github/dependabot.yml`
- `.github/instructions/git-flow-multi-agent.instructions.md`, Part 6 only
- `changelog.d/issue-3550-pull-request-title-guard.md`
- `specs/3550-pull-request-title-guard/**`

Keep `CHANGELOG.md`, other fragments, `ci.yml`, `quality-gates.md`, and all test ratchet files unchanged.
Keep `.specify/feature.json`, the constitution, and other shared agent files unchanged.
Change no runtime, menu, database, portal, container, repository setting, protection rule, or required status.
Separate owner approval is necessary before anyone makes the new check required.
Keep strict up-to-date protection, existing required checks, CodeQL, and `squash_merge_commit_title=PR_TITLE`.

### Existing local preparation

The parent reports an isolated Python 3.13 environment with pinned `requirements.txt` and `requirements-dev.txt` dependencies.
The environment exists because a chosen pytest command first proved that the worktree environment was absent.
No bootstrap or installation task is necessary.
The parent also reports 12 passing tests in `tests/guardrails/test_ci_gate_triggers.py`.
That baseline does not prove the new guard.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the existing worktree, explicit feature directory, ownership, and installed local tools.

- [X] T001 Confirm the branch and ownership recorded in `specs/3550-pull-request-title-guard/.spec-context.json`. Use the explicit feature-directory override. Reuse issue #3550.
- [X] T002 Verify the existing `.venv/bin/python` and pinned tools against `requirements.txt` and `requirements-dev.txt`. Use Python 3.13. Install nothing.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the package boundary and fixed policy evidence before story work.

No user story starts before both foundational tasks finish.
The data model needs no model class, database, persistent record, or migration.

- [X] T003 [P] Create the package boundary in `scripts/pr_title_guard/__init__.py` and `scripts/pr_title_guard/__main__.py`. Reserve one compiled pattern and four class methods. Add no wrapper or application import.
- [X] T004 [P] Establish fixed policy evidence in `tests/guardrails/test_pr_title_workflow.py`. Store the complete pre-change Dependabot mapping. Import the existing YAML parser directly.

Use `PullRequestTitleGuard` with `is_valid_title`, `read_title`, `check`, and `main`.
Keep the class within five members.
Keep each method within 25 lines, five parameters, five logical blocks, and five operations per block.
Keep each test class within five members.
Use the narrow location exceptions already recorded in `plan.md`.
Do not restructure existing parent directories.

The guardrail module uses `TestWorkflowPolicy`, `TestDependabotPolicy`, and `TestPartSixPolicy`.
Store its fixed snapshots inside this module, not in another file.
Do not derive an expected snapshot from the changed file under test.
A missing YAML parser must fail instead of producing a successful skip.
Verify instruction preservation outside Part 6 once with git during implementation.
Record that proof in the feature-owned context.
Do not freeze unrelated instruction text with permanent hashes or snapshots.

**Checkpoint**: The package imports, policy evidence is fixed, and the story tests can prove failures before implementation.

---

## Phase 3: User Story 1 - Correct a pull request title (Priority: P1)

**Goal**: Return the exact title decision and useful correction guidance without changing the supplied title.

**Independent Test**: Run `TestTitleGrammar` and `TestTitleOutput` offline.
The two requested titles must produce opposite exit results, exact title representations, and count one.

### Tests for User Story 1

Write each behavior test before its corresponding implementation.
Confirm that an incomplete behavior fails.
Do not mock the decision or compiled pattern.

- [X] T005 [US1] Add valid grammar cases to `tests/unit/scripts/test_pr_title_guard.py` under `TestTitleGrammar`. Cover all nine types and four accepted forms.
- [X] T006 [US1] Add invalid grammar and non-string decisions to `tests/unit/scripts/test_pr_title_guard.py`. Cover unsupported types, uppercase types, scopes, separators, markers, leading spaces, and blank descriptions.
- [X] T007 [US1] Add character and size cases to `tests/unit/scripts/test_pr_title_guard.py`. Cover Unicode, every forbidden character, separators, punctuation, and large valid and invalid titles.
- [X] T008 [P] [US1] Add exact result and action-log assertions to `tests/unit/scripts/test_pr_title_guard.py` under `TestTitleOutput`. Prove reversible ASCII titles, correction guidance, exit codes, and count one.

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement the compiled full-match rule and `is_valid_title` in `scripts/pr_title_guard/__init__.py`. Preserve the exact input. Log the real decision before and after.
- [X] T010 [US1] Implement `check` in `scripts/pr_title_guard/__init__.py` against `specs/3550-pull-request-title-guard/contracts/title-check.md`. Print exact contracted stdout. Return zero only for valid titles.
- [X] T011 [US1] Run the grammar and result tests in `tests/unit/scripts/test_pr_title_guard.py`. Prove `wip: model prompts` fails and `fix(web-portal): model prompts` passes offline.

The accepted types are exactly `fix`, `feat`, `chore`, `refactor`, `test`, `docs`, `ci`, `style`, and `perf`.
Only the type has a lowercase requirement.
The accepted forms are `type: description`, `type(scope): description`, `type!: description`, and `type(scope)!: description`.

A present scope contains a non-whitespace character and no parentheses.
The separator is a colon followed by an ASCII space.
The description contains a non-whitespace character and occupies one line.
Additional description spaces and Unicode text are valid.
Do not trim, normalize, rewrite, truncate, or impose a title-length limit.

Reject every character in U+0000 through U+001F and U+007F through U+009F.
Also reject U+2028 and U+2029.
Treat quotes, backslashes, and shell punctuation as data.
Use `json.dumps(title, ensure_ascii=True)` for every available title.
Every readable title prints `Checked 1 pull request title`.
An empty or whitespace-only string remains a title decision with count one.
A non-string direct `is_valid_title` argument returns false and logs count zero.

**Checkpoint**: Direct title decisions work without event input, credentials, or a workflow service.
This phase is the functional MVP, not permission to merge.

---

## Phase 4: User Story 2 - Trust the result and its measurement (Priority: P1)

**Goal**: Distinguish title failures from input failures and never report success without a readable title.

**Independent Test**: Run `TestEventInput` and `TestTitleCli` offline with temporary event files.
Input failures must exit one, omit the title line, and report count zero.

### Tests for User Story 2

- [X] T012 [US2] Add event-input cases to `tests/unit/scripts/test_pr_title_guard.py` under `TestEventInput`. Cover every contracted input problem and exact count-zero output.
- [X] T013 [P] [US2] Add process and `main` cases to `tests/unit/scripts/test_pr_title_guard.py` under `TestTitleCli`. Assert complete stdout, ASCII stderr, logging order, counts, and exit codes.

### Implementation for User Story 2

- [X] T014 [P] [US2] Implement `read_title` in `scripts/pr_title_guard/__init__.py`. Read only `GITHUB_EVENT_PATH` as UTF-8 JSON. Validate each object and the exact title type.
- [X] T015 [US2] Complete `main` in `scripts/pr_title_guard/__init__.py` and the direct exit in `scripts/pr_title_guard/__main__.py`. Report explicit input failures. Sanitize exception diagnostics.
- [X] T016 [US2] Run all four unit classes in `tests/unit/scripts/test_pr_title_guard.py`. Prove input-failure behavior and preserve User Story 1 results.

Input cases include an absent or empty environment value and a missing, unreadable, directory, or unusable path.
They also include bad UTF-8, malformed or empty JSON, wrong roots, wrong records, and missing or non-string titles.
Use a real temporary file where possible.
Use only a narrow file-capability stand-in when permissions cannot fail reliably on the host.
Readable blank strings report count one, not count zero.

Match the fixed reasons in `contracts/title-check.md`.
An input failure prints `Checked 0 pull request titles` and exits with one.
Do not print raw paths, event payloads, decoder bytes, credentials, or raw exception text.
Log event reading before and after both success and failure.
An input failure starts no title decision.
Use escaped exception categories and complete stack-frame text on stderr.
Use `%s` logging arguments.

CLI tests invoke `python -m scripts.pr_title_guard` through argument lists with temporary JSON fixtures.
Do not interpolate titles into executable shell text.
The checker imports no MistHelper runtime and needs no network or installed runtime dependency.

**Checkpoint**: The module CLI proves success, title failure, and input failure with measured counts.

---

## Phase 5: User Story 3 - Keep dependency updates active (Priority: P2)

**Goal**: Apply one decision to all authors while preserving every existing dependency update stream.

**Independent Test**: Run the bot cases and `TestDependabotPolicy` offline.
Reverse only the two approved prefixes, then compare the complete parsed policy with the fixed snapshot.

### Tests for User Story 3

- [X] T017 [US3] Add author and bot cases in `tests/unit/scripts/test_pr_title_guard.py` and policy contracts in `tests/guardrails/test_pr_title_workflow.py`. Prove identical decisions and complete policy preservation.

### Implementation for User Story 3

- [X] T018 [US3] Replace only pip `deps` with `chore` and npm `deps(ops-portal)` with `chore(ops-portal)` in `.github/dependabot.yml`.
- [X] T019 [US3] Run the bot and Dependabot tests in `tests/unit/scripts/test_pr_title_guard.py` and `tests/guardrails/test_pr_title_workflow.py`. Confirm the prefix-only `.github/dependabot.yml` diff.

Keep github-actions `ci`.
Keep `version: 2`, the three streams, their order, and their directories.
Keep weekly schedules, limits of five, labels, groups, ignores, comments, and every other key.
Keep the npm React group and its four patterns.
Keep the TypeScript major-version ignore.

Include contributor, bot, draft, and fork event fixtures.
Actor, author, draft, and changed-file data must not change the decision.
Existing `deps` and `deps(ops-portal)` titles fail.
A maintainer renames them and permits the `edited` event to repeat the check.
Do not rename existing PRs automatically, close updates, disable streams, or add exemptions.

**Checkpoint**: New bot prefixes pass without changing the dependency update policy.

---

## Phase 6: User Story 4 - Use a current check without changing enforcement (Priority: P2)

**Goal**: Run one safe check after every approved event and document correction without changing merge enforcement.

**Independent Test**: Run `TestWorkflowPolicy` and `TestPartSixPolicy` offline.
Parsed contracts must reject unsafe settings and verify the exact job name and owner approval boundary.

### Tests for User Story 4

- [X] T020 [US4] Add parsed workflow contracts to `tests/guardrails/test_pr_title_workflow.py` under `TestWorkflowPolicy`. Prove valid policy and rejected in-memory policy mutations.
- [X] T021 [US4] Add Part 6 contracts to `tests/guardrails/test_pr_title_workflow.py` under `TestPartSixPolicy`. Assert names, grammar, correction, bot policy, and approval.

### Implementation for User Story 4

- [X] T022 [P] [US4] Create `.github/workflows/pull-request-title.yml` against `specs/3550-pull-request-title-guard/contracts/workflow-policy.md`. Use one read-only job and the safe JSON reader.
- [X] T023 [P] [US4] Update only Part 6 in `.github/instructions/git-flow-multi-agent.instructions.md`. Name `Conventional Commits PR title`. Document title correction, bot prefixes, and separate owner approval.
- [X] T024 [US4] Run workflow and documentation contracts in `tests/guardrails/test_pr_title_workflow.py`. Confirm that the complete owned behavior and policy selection passes offline.

Use `Pull request title` as the workflow name.
Use `Conventional Commits PR title` as the exact job and check name.
Declare only `pull_request` with this exact activity set:

```text
opened
edited
reopened
synchronize
ready_for_review
```

Add no branch or path filter, ignore filter, other trigger, or author condition.
Do not declare `push`, `schedule`, or `pull_request_target`.
Use these exact concurrency settings:

```text
group: ${{ github.workflow }}-${{ github.head_ref || github.ref }}
cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}
```

A replacement run cancels an older same-group run outside `main`.
A different head branch retains its independent run.
The reference provides the fallback.

Grant only `contents: read`.
Use a standard Linux runner, `actions/checkout@v7`, and `actions/setup-python@v7`.
Accept newer major versions of these same actions in the policy tests.
Keep every other workflow setting fixed.
Prove that normal Actions updates pass and that downgrades and different action names fail.
Set `persist-credentials: false`, Python `3.13`, and `timeout-minutes: 5`.
Run exactly `python -m scripts.pr_title_guard`.
Use the runner-provided `GITHUB_EVENT_PATH`.
Add no package-install step, secrets, title interpolation, network lookup, privileged event, or write permission.
Do not suppress failures or use `continue-on-error`.

Negative contracts cover omitted events, extra triggers, filters, altered concurrency, permissions, credentials, unsafe interpolation, and author exemptions.
They also cover unrelated Dependabot changes and missing documentation requirements.
Account for the YAML parser's Boolean form of an unquoted `on` key.
Use mutated in-memory inputs, not a temporary bad remote commit.
Each failure proof must exercise a real assertion or decision.
Do not accept an empty measurement or environmental skip as a pass.

Part 6 retains Conventional Commits and the existing squash-merge rules.
It names both the workflow and the exact check.
It describes all four forms, nine types, nonblank scope and description, controls, Unicode, and title-edit reruns.
It states that the new check is not required without separate owner approval.
The durable tests check Part 6 semantics only.
The one-time git proof checks this issue's unchanged text outside Part 6.
Future changes to another Part must not fail these tests.

**Checkpoint**: All four user stories work and the existing enforcement remains unchanged.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Finish the owned release note, review conformance, and perform the required post-implementation analysis.

- [X] T025 Add the user-visible release note in `changelog.d/issue-3550-pull-request-title-guard.md`. Use one allowed change heading and an issue-linked bullet.
- [X] T026 Review owned source, tests, and Part 6 against `specs/3550-pull-request-title-guard/plan.md`. Verify structural limits, logging, comments, types, correction steps, and protected-file preservation.
- [x] T027 Run required `speckit.analyze` after implementation against `specs/3550-pull-request-title-guard/spec.md`, `plan.md`, and `tasks.md`. Use the explicit override. Resolve owned findings before parent delivery. (delivered: `plan.md` records full requirement coverage, the corrected reader block, and the coordinator-confirmed scope.)

The analysis covers the specification, plan, tasks, and delivered implementation.
It does not authorize shared-file edits or another issue.
If an unresolved finding needs another owner, record the blocker in the feature-owned context.
Do not report completed implementation while a relevant finding remains open.

---

## Parent Validation (Not Implementation)

The parent owns final local evidence after T027.
These tasks do not run during task generation.
Use the existing isolated environment.
Record each exact command, result, measured scope, and revision.
Do not replace a missing capability with a passing skip.

- [x] T028 Run targeted compile command V1 for `MistHelper.py`, `scripts/pr_title_guard/__init__.py`, `scripts/pr_title_guard/__main__.py`, and both owned test files. (delivered: Five files compile.)
- [x] T029 Run targeted Ruff command V2 for `scripts/pr_title_guard/__init__.py`, `scripts/pr_title_guard/__main__.py`, and both owned test files. (delivered: The targeted check and `ruff check .` pass.)
- [x] T030 Run targeted Black command V3 for `scripts/pr_title_guard/__init__.py`, `scripts/pr_title_guard/__main__.py`, and both owned test files. (delivered: The targeted check passes. The full check reports 1,879 unchanged files.)
- [x] T031 Run targeted mypy command V4 for `scripts/pr_title_guard/__init__.py` and `scripts/pr_title_guard/__main__.py`. Verify that both files receive analysis. (delivered: Two source files pass.)
- [x] T032 Run targeted Bandit command V5 for `scripts/pr_title_guard/__init__.py` and `scripts/pr_title_guard/__main__.py`. Require a nonzero measured source scope. (delivered: 87 source lines, zero findings, and zero skipped files.)
- [x] T033 Run pytest and coverage command V6 for both owned tests and `tests/guardrails/test_ci_gate_triggers.py`. Require positive collection and no successful environmental skip. (delivered: 853 passed, zero skipped, and 96.67 percent package coverage.)
- [x] T034 Run test quality command V7 on the new tests in `tests/unit/scripts/` and `tests/guardrails/`. Keep `.github/test-quality-config.toml` and `.github/test-quality-baseline.json` unchanged. (delivered: 42 files checked, including both new modules, with zero new findings.)

### Exact local commands

Run commands from the worktree root.
The table identifies each command and its expected result.

| Command | Expected result |
| --- | --- |
| V1 | All five named Python files compile. |
| V2 | All four changed Python files pass Ruff. |
| V3 | All four changed Python files pass Black. |
| V4 | Both checker files pass strict mypy. |
| V5 | Both checker files receive Bandit analysis with no finding. |
| V6 | Selected tests pass and package coverage reaches at least 90 percent. |
| V7 | Both new test modules receive measurement with zero new quality findings. |

V1:

```bash
rtk proxy .venv/bin/python -m py_compile MistHelper.py scripts/pr_title_guard/__init__.py scripts/pr_title_guard/__main__.py tests/unit/scripts/test_pr_title_guard.py tests/guardrails/test_pr_title_workflow.py
```

V2:

```bash
rtk proxy .venv/bin/python -m ruff check scripts/pr_title_guard/__init__.py scripts/pr_title_guard/__main__.py tests/unit/scripts/test_pr_title_guard.py tests/guardrails/test_pr_title_workflow.py
```

V3:

```bash
rtk proxy .venv/bin/python -m black --check scripts/pr_title_guard/__init__.py scripts/pr_title_guard/__main__.py tests/unit/scripts/test_pr_title_guard.py tests/guardrails/test_pr_title_workflow.py
```

V4:

```bash
rtk proxy .venv/bin/python -m mypy --config-file pyproject.toml scripts/pr_title_guard/__init__.py scripts/pr_title_guard/__main__.py
```

V5:

```bash
rtk proxy .venv/bin/python -m bandit scripts/pr_title_guard/__init__.py scripts/pr_title_guard/__main__.py
```

V6:

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/scripts/test_pr_title_guard.py tests/guardrails/test_pr_title_workflow.py tests/guardrails/test_ci_gate_triggers.py -q --timeout=120 --cov=scripts.pr_title_guard --cov-report=term-missing --cov-fail-under=90
```

V7:

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --roots tests/unit/scripts tests/guardrails
```

The mypy command names files because the repository excludes `scripts` during directory discovery.
The Bandit command uses explicit files and all default checks.
It omits `-c pyproject.toml` because that configuration excludes `scripts` from analysis.
This targeted command changes no exclusion and suppresses no finding.
The coverage command retains the repository's current 90 percent threshold.
The test quality command uses explicit roots so it measures new, untracked tests.
Do not write or prune the baseline, disable rules, add exclusions, or add suppressions.

Use the story checkpoints for earlier targeted pytest selections.
The final combined run must prove both exact example titles, all failure categories, and all policy contracts.
If a rebase changes the tree, repeat the affected gates before the single push.
No production container deployment is necessary for this metadata-only change.

---

## Parent Delivery (Not Implementation)

The parent owns all tasks in this section.
Implementation completion does not mean delivery completion.
The PR template must retain its headings, comments, checklists, and ordering.
After merge, record evidence in the PR or parent session rather than pushing another commit to the merged branch.

- [x] T035 Record final local results and the owned manifest in `specs/3550-pull-request-title-guard/.spec-context.json`. Include analysis, failure proofs, gate counts, and revision evidence. (delivered: The context records the parent validation and the confirmed publication boundary.)
- [ ] T036 Commit only the explicit owned manifest, including `specs/3550-pull-request-title-guard/tasks.md`. Use Conventional Commits and the required Copilot co-author trailer.
- [ ] T037 Verify strict up-to-date protection for the branch that contains `scripts/pr_title_guard/__init__.py`. If the branch needs an update, rebase onto `origin/main`. Repeat affected local gates without main-checkout access.
- [ ] T038 Push the validated app branch containing `specs/3550-pull-request-title-guard/tasks.md` once. Do not push to `main` or dispatch an unnecessary workflow.
- [ ] T039 Create the template-preserving PR for `.github/workflows/pull-request-title.yml` and the owned manifest. Include `Closes #3550` and `chore`, `ci`, and `in-progress` labels.
- [ ] T040 Wait for every required check, CodeQL, and `Conventional Commits PR title` from `.github/workflows/pull-request-title.yml`. Treat skipped required checks as unknown. Preserve existing protection.
- [ ] T041 Coordinate the squash merge of `.github/workflows/pull-request-title.yml` and the owned manifest with parent `6d71fd26-57c2-48c0-abc8-607af98f75d0`. Require current passing checks.
- [ ] T042 Verify the exact squash SHA in the parent's isolated checkout using both owned test files and `tests/guardrails/test_ci_gate_triggers.py`. Repeat V1 through V7. Record SHA-specific results.

Use this trailer at the end of the Conventional Commits message:

```text
Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>
```

Use a compliant PR title.
Include exact local commands and their results in the preserved PR template.
Do not claim unperformed checks, production deployment, or a new required title status.
Wait for CodeQL before any permitted auto-merge label.
Confirm strict up-to-date protection again before the coordinated merge.
If a title edit occurs, confirm that its new event file produces the current result.
Use the offline concurrency proof unless overlapping runs occur naturally.
Do not push another commit only to demonstrate cancellation.
Do not substitute the feature tip for the exact squash SHA.

---

## Dependencies & Execution Order

### Phase Dependencies

| Phase or owner stage | Prerequisite | Completion boundary |
| --- | --- | --- |
| Setup | None | Existing context and tools are confirmed. |
| Foundational | T002 | T003 and T004 finish. |
| US1 | Both foundational tasks | T011 proves the direct MVP. |
| US2 | US1 | T016 proves event and CLI behavior. |
| US3 | US2 | T019 proves bot and policy behavior. |
| US4 | US3 | T024 proves workflow and documentation contracts. |
| Polish | All stories | T027 analysis has no unresolved owned finding. |
| Parent validation | Polish | V1 through V7 pass on the final local tree. |
| Parent delivery | Parent validation | T042 proves the exact merged tree. |

### User Story Dependencies

US1 needs only the foundation.
US2 uses US1's decision and result methods.
US3 uses that common decision and the event tests.
US4 uses US2's safe reader and US3's bot policy.

Unit tests share `tests/unit/scripts/test_pr_title_guard.py`.
Policy tests share `tests/guardrails/test_pr_title_workflow.py`.
Complete the earlier story's edits before the next story edits either shared file.
Independent story tests require no remote service or credentials.
File ownership prevents unrestricted parallel story editing.

### Task Dependencies

Each row lists direct prerequisites.
The sequence preserves the stories' priority and shared-file ownership.

| Task | Direct prerequisites |
| --- | --- |
| T001 | None |
| T002 | T001 |
| T003, T004 | T002 |
| T005 | T003, T004 |
| T006 | T005 |
| T007 | T006 |
| T008, T009 | T007 |
| T010 | T008, T009 |
| T011 | T010 |
| T012 | T011 |
| T013, T014 | T012 |
| T015 | T013, T014 |
| T016 | T015 |
| T017 | T016 |
| T018 | T017 |
| T019 | T018 |
| T020 | T019 |
| T021 | T020 |
| T022, T023 | T021 |
| T024 | T022, T023 |
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
| T036 | T035 |
| T037 | T036 |
| T038 | T037 and repeated affected gates after any rebase |
| T039 | T038 |
| T040 | T039 |
| T041 | T040 |
| T042 | T041 |

### Completion Graph

```text
T001 -> T002 -> (T003 + T004)
  -> US1: T005 -> T006 -> T007 -> (T008 + T009) -> T010 -> T011
  -> US2: T012 -> (T013 + T014) -> T015 -> T016
  -> US3: T017 -> T018 -> T019
  -> US4: T020 -> T021 -> (T022 + T023) -> T024
  -> Polish: T025 -> T026 -> T027
  -> Parent validation: T028 -> T029 -> T030 -> T031 -> T032 -> T033 -> T034
  -> Parent delivery: T035 -> T036 -> T037 -> T038 -> T039 -> T040 -> T041 -> T042
```

### Parallel Opportunities

There are eight `[P]` tasks in four safe pairs.
Each pair edits different files after its prerequisites finish.
Use no nested agents during this tasks step.
Later parallel work requires separate file ownership.

| Stage | Ready condition | Independent tasks |
| --- | --- | --- |
| Foundation | T002 finishes. | T003 edits the checker package while T004 prepares the guardrail snapshot. |
| US1 | T007 finishes. | T008 edits result tests while T009 implements the tested grammar. |
| US2 | T012 finishes. | T013 edits CLI tests while T014 implements the tested event reader. |
| US4 | T021 finishes. | T022 edits the workflow while T023 edits Part 6. |

---

## Parallel Example: User Story 1

After T007, complete T008 and T009 together under separate file ownership.
The result tests stay in `tests/unit/scripts/test_pr_title_guard.py`.
The grammar implementation stays in `scripts/pr_title_guard/__init__.py`.
T010 waits for both tasks.

## Parallel Example: User Story 2

After T012, complete T013 and T014 together under separate file ownership.
The CLI tests stay in `tests/unit/scripts/test_pr_title_guard.py`.
The event reader stays in `scripts/pr_title_guard/__init__.py`.
T015 waits for both tasks.

## Parallel Example: User Story 3

This story has no safe same-story edit pair.
T017 establishes tests before T018 changes the single Dependabot file.
T019 then proves the policy and common decision.
Do not divide the pip and npm edits between owners of the same file.

## Parallel Example: User Story 4

After T021, complete T022 and T023 together under separate file ownership.
The workflow stays in `.github/workflows/pull-request-title.yml`.
The documentation stays inside Part 6 of `.github/instructions/git-flow-multi-agent.instructions.md`.
T024 waits for both tasks.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational tasks.
2. Complete US1's grammar and exact-result behavior.
3. Prove the two requested direct decisions offline.

The MVP contains T001 through T011.
It proves the core rule but does not satisfy event, bot, workflow, or delivery acceptance.
Do not merge the MVP alone.

### Incremental Delivery

1. Complete US2's safe event input and module CLI.
2. Complete US3's common bot decision and two prefix changes.
3. Complete US4's workflow and Part 6 contracts.
4. Complete the release note and required post-implementation analysis.
5. Transfer final validation and delivery to the parent.

### Parallel Team Strategy

Use only the four documented pairs after their prerequisites finish.
Keep the shared test modules under one editor at a time.
Keep all delivery actions with the parent.
Do not create issues, branches, commits, or pushes for individual tasks.

## Notes

The task total is 42.
US1 has seven tasks, US2 has five, US3 has three, and US4 has five.
Setup has two tasks and Foundation has two tasks.
Polish has three tasks, parent validation has seven, and parent delivery has eight.
All tasks use the required checkbox, sequential ID, applicable labels, and exact paths.
The feature has no unresolved planning blocker.
