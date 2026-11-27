# Tasks: Other-Device Event Export Fails Closed on Failed Pages

**Input**: Numeric record `specs\numbered\0\0\1\2\2\3\1\4\4709-other-device-events-page-failures\`. Available documents: `plan.md`, `spec.md`, `design/research.md`, `design/data-model.md`, `design/contracts/`, and `design/checklists/`.

**Format**: `[ ]` means not done. Mark a task only after the delivered file passes its verification command. Add the evidence in this form: `(delivered: path)`.

**Parallel marker**: No task carries `[P]`. Tasks T001 to T007 change one source file and one test file, so they run in sequence.

## Implementation Tasks

### T001 - Confirm the handoff and the base file [FR-021, FR-018]

- [ ] T001 Confirm the #1794 handoff and the base file blob.
- **Files**: `src/operations/exporting/export/site_other_device_events_exporter.py`, `tests/unit/export/test_site_other_device_events_exporter.py`.
- **Acceptance**: A handoff comment from the #1794 owner names both files. The branch copy of the exporter has blob `60f1ac7fdd966ef4cd7b38b4e3f6cd314d1fbf3a`, which matches `main` (RC-01).
- **Verification**: `symbol-diff --base origin/main src/operations/exporting/export/site_other_device_events_exporter.py`. Expected result: `no module-level name changed`, exit code 0.
- **Status**: absent. The handoff is not posted.

### T002 - Write the failing tests first [FR-001 to FR-014, FR-016, FR-017]

- [ ] T002 Add the 16 test cases of plan.md before any source edit. Test 7 holds two cases.
- **Files**: `tests/unit/export/test_site_other_device_events_exporter.py`.
- **Acceptance**: The file holds the 16 test cases. Every new case fails on the current exporter, except Test 12, which guards the unchanged success path. The five retained tests pass. The menu test patches the SDK response and no longer patches `mistapi.get_all`.
- **Verification**: `python -m pytest tests/unit/export/test_site_other_device_events_exporter.py`. Expected result before T003: the new failure cases fail, and the retained tests pass.
- **Status**: absent.
- **Depends on**: T001.

### T003 - Add first-page status and body validation [FR-001, FR-003, FR-004, FR-009, FR-010, FR-011]

- [ ] T003 Add `_validate_page` with status and body checks, and log each rejected page.
- **Files**: `src/operations/exporting/export/site_other_device_events_exporter.py`.
- **Acceptance**: `_validate_page` rejects a missing status, a status outside 200 through 299, a body without a list `results`, and a non-object row. It logs one ERROR line and raises `RuntimeError`. Its messages hold no body text. Tests 1 to 6 pass.
- **Verification**: `python -m pytest tests/unit/export/test_site_other_device_events_exporter.py`.
- **Status**: absent.
- **Depends on**: T002.

### T004 - Add the next-page loop and the cursor guard [FR-002, FR-005, FR-006, FR-010, FR-015]

- [ ] T004 Add `_next_page` and `_collect_all_pages` with the `mistapi.get_next` call and the repeated-cursor check.
- **Files**: `src/operations/exporting/export/site_other_device_events_exporter.py`.
- **Acceptance**: Each later page passes through `_validate_page` before its rows are kept. The loop calls `mistapi.get_next(mist_session=session, response=page)`. A repeated `next` value raises `RuntimeError`. Tests 7 to 9 and Test 13 pass.
- **Verification**: `python -m pytest tests/unit/export/test_site_other_device_events_exporter.py`.
- **Status**: absent.
- **Depends on**: T003.

### T005 - Add the total and header checks [FR-007, FR-008, FR-009]

- [ ] T005 Add `_check_total` for the body `total` and the `X-Page-*` headers.
- **Files**: `src/operations/exporting/export/site_other_device_events_exporter.py`.
- **Acceptance**: A row count that differs from `total` raises `RuntimeError`. A non-integer `total` or `X-Page-*` header raises `RuntimeError`. A read without any total passes. Tests 10 and 11 pass.
- **Verification**: `python -m pytest tests/unit/export/test_site_other_device_events_exporter.py`.
- **Status**: absent.
- **Depends on**: T004.

### T006 - Route the menu operation through the collector [FR-012, FR-013, FR-014, FR-016, FR-017, FR-018]

- [ ] T006 Route `other_device_events` through `_collect_all_pages`, and keep `_persist_events` and the outer guard.
- **Files**: `src/operations/exporting/export/site_other_device_events_exporter.py`, `tests/unit/export/test_site_other_device_events_exporter.py`.
- **Acceptance**: A complete empty read prints the no-data message. A complete read with rows calls the writer once. A failure returns to the loop without an exception. `_persist_events` keeps its signature. The module adds no module-level name. Tests 6 and 12 pass, and the five retained tests pass.
- **Verification**: `python -m pytest tests/unit/export/test_site_other_device_events_exporter.py`.
- **Status**: absent.
- **Depends on**: T005.

### T007 - Add inline comments, action logs, and size checks [FR-019, FR-011]

- [ ] T007 Add an inline comment to each changed line, and action logs around each request.
- **Files**: `src/operations/exporting/export/site_other_device_events_exporter.py`, `tests/unit/export/test_site_other_device_events_exporter.py`.
- **Acceptance**: Each changed executable line has an inline comment. Each request has an INFO line before it and a DEBUG line after it. Each function holds 25 lines or fewer, five parameters or fewer, and five logical blocks or fewer. Test 15 passes.
- **Verification**: `radon cc src/operations/exporting/export/site_other_device_events_exporter.py -j | complexity-gate --max 10`. Expected result: no block above complexity 10.
- **Status**: absent.
- **Depends on**: T006.

### T008 - Add the changelog fragment [FR-020]

- [ ] T008 Add the changelog fragment for issue #4709.
- **Files**: `changelog.d/issue-4709-other-device-events-page-failures.md`.
- **Acceptance**: The fragment holds one `###` heading and one `Fixed` bullet that names issue #4709. `CHANGELOG.md` stays unchanged.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4709-other-device-events-page-failures.md`. Expected result: a score of 80 or above.
- **Status**: absent.
- **Depends on**: T007.

## Final Tasks

### T-LOCAL-GATES - Run every applicable local gate [FR-001 to FR-022, SC-004, SC-005]

- [ ] T-LOCAL-GATES Run each applicable gate and record its result.
- **Files**: `src/operations/exporting/export/site_other_device_events_exporter.py`, `tests/unit/export/test_site_other_device_events_exporter.py`, `changelog.d/issue-4709-other-device-events-page-failures.md`, and the Markdown files of this record.
- **Acceptance**: Each gate in the list below reports its expected result. The pull request body records each command and result. A gate that does not apply names its reason.
- **Verification**: The gates of the local gates table in `.github/copilot-instructions.md` (line 50, RC-35), run as listed below.
  - Compile: `python -m py_compile MistHelper.py`. Expected result: no output. This gate applies to every commit (constitution Development Workflow section).
  - Lint: `python -m ruff check .`. Expected result: `All checks passed`.
  - Format: `python -m black --check .`. Expected result: no file needs a change.
  - Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. The path list comes from `MYPY_PATHS` (RC-26). Expected result: `Success`.
  - Tests: `python -m pytest tests/unit/export/test_site_other_device_events_exporter.py`, then `python -m pytest tests/unit/export`. Expected result: all tests pass. The second run covers FR-022.
  - SDK compatibility: `python -m pytest tests/integration/test_mistapi_sdk_compatibility.py` (RC-48). Expected result: all tests pass.
  - Full tests: run these two commands, one for each shard. Each prints one summary line, and the run stops at the first failed chunk.
    - `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal`
    - `pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal`
    Expected result: one summary line for each shard, with no failure.
  - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`. Expected result: coverage of 80 percent or above.
  - Test quality: `python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides` (RC-49), then `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main`. Expected result: `gate: 0 new findings vs baseline`.
  - Complexity: `radon cc src/operations/exporting/export/site_other_device_events_exporter.py -j | complexity-gate --max 10`. Expected result: no block above complexity 10.
  - Security lint: `bandit -c pyproject.toml -r src/operations/exporting/export/site_other_device_events_exporter.py -q`. Expected result: no finding.
  - Code quality: `pylint src/ --fail-under=9.5` (RC-30). Expected result: score 9.5 or above.
  - Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` (RC-27). Expected result: no finding.
  - Docstrings: `pydocstyle src/ wsgi.py web_portal` (RC-28) and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` (RC-29). Expected result: no violation, and coverage of 90 percent or above.
  - Symbols: `symbol-diff --base origin/main src/operations/exporting/export/site_other_device_events_exporter.py`. Expected result: `no module-level name changed`, exit code 0.
  - STE: `ste-linter --config .ste-linter.toml --min-score 80 AGENTS.md .github/copilot-instructions.md README.md CLAUDE.md documentation/ASD-STE100_writing-guide.md changelog.d/issue-4709-other-device-events-page-failures.md specs/numbered/0/0/1/2/2/3/1/4/4709-other-device-events-page-failures/spec.md specs/numbered/0/0/1/2/2/3/1/4/4709-other-device-events-page-failures/plan.md specs/numbered/0/0/1/2/2/3/1/4/4709-other-device-events-page-failures/tasks.md`. Expected result: each file scores 80 or above. Add the other record Markdown files to the same command.
  - Not applicable, with reasons: Safe sweep (menu 258 is in the `interactive_safe` category, and `--test` skips it). Menu reference (no title or registry change). Dependency audit (no dependency file changes). Ops portal and ops platform (no change to those trees).
- **Status**: open.
- **Depends on**: T008.

### T-PR - Commit, push, and open the pull request [FR-020, FR-021, D-13]

- [ ] T-PR Commit the change on a new branch, and open the pull request after authorization.
- **Files**: the three changed files and the record folder.
- **Acceptance**: The branch is `fix/4709-other-device-events-page-failures`, created from `main` in its own worktree. The commit subject is `fix(export): fail other-device event export on failed pages`. The pull request title uses the same form. The body holds `Closes #4709`, the references `Refs #1794`, `Refs #4707`, and `Refs #4710`, the gate results, and the changelog fragment name. The orchestrator authorizes the push and the pull request before either happens.
- **Verification**: `python -m pytest tests/unit/export/test_site_other_device_events_exporter.py` on the committed tree. Expected result: all tests pass.
- **Status**: open.
- **Depends on**: T-LOCAL-GATES.

Caution: a closing keyword for #1794, #4707, or #4710 closes that issue on merge. Use `Refs` for each of them.

### T-REMOTE-CI - Watch the CI run [SC-006]

- [ ] T-REMOTE-CI Watch the CI run on the pull request and confirm each required check.
- **Files**: `.github/test-quality-config.toml` and `.github/test-quality-baseline.json`. The gate reads both files.
- **Acceptance**: `gh pr checks <number> --watch` shows every required check green on the latest commit. No check is skipped or canceled. The test quality job reports zero new findings.
- **Verification**: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`. Expected result: `gate: 0 new findings vs baseline`.
- **Status**: open.
- **Depends on**: T-PR.

### T-MERGE - Merge after the checks and authorization [D-13, SC-005]

- [ ] T-MERGE Squash merge the pull request after authorization, and verify the main build.
- **Files**: `src/operations/exporting/export/site_other_device_events_exporter.py`.
- **Acceptance**: After the orchestrator authorizes, add the `auto-merge` label only when every check is green. Squash merge the pull request. Delete the branch and its worktree. The `container-build.yml` run on the merged commit succeeds. The image revision label equals the merged commit (`documentation/container-deployment.md`, section "Check the revision of the running container", line 268).
- **Verification**: `symbol-diff --base origin/main src/operations/exporting/export/site_other_device_events_exporter.py`. Expected result: `no module-level name changed`, exit code 0.
- **Status**: open.
- **Depends on**: T-REMOTE-CI.

Warning: a commit pushed to the branch after the squash merge leaves the pull request orphaned. Create a new issue and a new branch from `main` instead.
