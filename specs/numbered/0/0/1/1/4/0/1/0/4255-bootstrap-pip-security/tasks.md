# Tasks: Bootstrap pip security

## Phase 1: Setup

- [x] T001 Inspect the current `scripts/bootstrap_worktree.py`, issue evidence, and file ownership.

## Phase 2: Foundational

- [x] T002 Reproduce the seeded pip advisories and independent audit failure with `scripts/bootstrap_worktree.py`.

## Phase 3: Safe development environment (US1)

**Goal**: A successful bootstrap installs a safe pip release through either selected installer.
**Independent test**: The command test rejects the previous source, then an actual bootstrap produces a clean installed-pip audit.

- [x] T003 [US1] Require the safe pip argument in `tests/unit/bootstrap/test_pip_index_probe.py` and confirm failure before the repair.
- [x] T004 [US1] Add the minimum pip requirement to `scripts/bootstrap_worktree.py` without another subprocess.
- [x] T005 [US1] Run the focused bootstrap tests, source gates, and actual bootstrap audit for `scripts/bootstrap_worktree.py`.

## Phase 4: Evidence and documentation

- [x] T006 [P] Add `changelog.d/issue-4255-bootstrap-pip-security.md`.
- [x] T007 Check consistency across `spec.md`, `plan.md`, and `tasks.md`, then record exact results on issue #4255.

## Dependencies

T001 precedes T002. T002 precedes T003. T003 precedes T004. T004 precedes T005.
T007 requires T005 and T006.
T006 can run independently of the test and source changes.

## Implementation Strategy

Deliver the single user story in one coherent repair.
Keep the runtime requirements and shared instruction files unchanged.
Optional task-generation commit hooks remain deferred until the coherent repair is ready.

## Results

The regression rejected the old source for both installers.
The final focused run passed 182 tests.
New and existing environments installed pip 26.2.2 and passed the installed-environment audit.
The actual pip fallback also installed pip 26.2.2.
The independent requirements audit still aborts during temporary-environment `ensurepip`.
The specification review found coverage for all five requirements across seven tasks.
Both issue records remain open.
See the [validation evidence](https://github.com/jmorrison-juniper/MistHelper/issues/4255#issuecomment-6426679621).
