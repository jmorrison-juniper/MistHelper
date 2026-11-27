# Tasks: Virtual Chassis Menu Guidance

**Input**: Numeric record `specs/numbered/0/0/1/2/2/4/4/2/4747-virtual-chassis-menu-options/`. Read `plan.md` and `spec.md` first.

**Prerequisites**: `plan.md` (required), `spec.md` (required), `design/research.md`, `design/quickstart.md`, and `design/contracts/vc-menu-guidance.md`.

**Tests**: Required by FR-007 and FR-008. Four tests are written first. They must fail before the text change.

**Warning**: Do not start menu 161 or menu 162 in any task. A conversion changes the Mist cloud and can need a factory reset to revert.

## Format

- `[P]` marks a task that can run in parallel. It edits a file that no other open task edits.
- Each task lists its status, requirements, files, acceptance statement, and one verification command from the local gates table.
- Status values are `open`, `verified-present`, `partial`, and `absent`.

## Dependencies

- T001 has no prerequisite.
- T002 depends on T001.
- T003 depends on T002.
- T004 depends on T003, because both edit `virtual_chassis.py`.
- T005 is `[P]` after T002. It edits a different file.
- T006 is `[P]` after T001.
- T-LOCAL-GATES depends on T003, T004, T005, and T006.
- T-PR depends on T-LOCAL-GATES.
- T-REMOTE-CI depends on T-PR.
- T-MERGE depends on T-REMOTE-CI.

## Phase 1: Preflight

### T001 Confirm the anchors and the file overlap before editing

- **Status**: verified-present. Research rows RC-01 to RC-105 hold the remote evidence.
- **Requirements**: FR-007, FR-012, A-1, A-4
- **Files**: none
- **Acceptance**: The remote anchors in RC-04 to RC-27 still match `main`. The open pull request scan finds no target path. Issue #4747 carries the `in-progress` label. The branch `fix/4747-virtual-chassis-menu-options` exists.
- **Verification**: `python -m pytest tests/guardrails/test_operation_registry_menu_coverage.py`

## Phase 2: Tests first

### T002 Add four offline tests and confirm that they fail

- **Status**: open
- **Requirements**: FR-001, FR-002, FR-003, FR-004, FR-006, FR-007, FR-008, SC-005
- **Files**: `tests/unit/test_virtual_chassis.py`
  - Add `import re` and `from pathlib import Path` to the import block.
  - Add `test_status_usage_notes_name_conversion_menus`, `test_named_menus_match_registered_operations`, and `test_virtual_chassis_sources_name_no_stale_menus` to `TestCheckStatus` (RC-39).
  - Add `test_success_guidance_names_status_menu` to `TestHandleConversionResponse` (RC-40).
- **Acceptance**: `TestCheckStatus` holds five methods. `TestHandleConversionResponse` holds four methods. Each new test has 25 lines or fewer and five parameters or fewer. Each executable line has a WHY comment. All four new tests fail on the unchanged source. The existing tests in the file still pass.
- **Verification**: `python -m pytest tests/unit/test_virtual_chassis.py`

Test expectations for T002:

- `test_status_usage_notes_name_conversion_menus` calls `VirtualChassisManager._print_status_usage_notes()`. It asserts that `re.findall(r"[Mm]enu (\d+)", output)` equals `["161", "162"]`. It asserts both exact note strings.
- `test_named_menus_match_registered_operations` calls `_print_status_usage_notes()` and `_print_conversion_success(MagicMock(data={}), "dev-1", "site-1")`. It imports `MistHelper` and `OperationRegistry` inside the method. It asserts that the named set equals `{"161", "162", "14"}`. It asserts each category and that each registered title contains `virtual chassis`.
- `test_virtual_chassis_sources_name_no_stale_menus` reads `virtual_chassis.py` and `tests/test_virtual_chassis.py` with `pathlib`. It asserts that the pattern `(?:[Mm]enus?|[Oo]ptions?)\b[^\n]{0,20}?\b(?:92|93|94)\b` never matches. It asserts that `menu 161` appears in both files.
- `test_success_guidance_names_status_menu` calls `_handle_conversion_response(MagicMock(status_code=200, data={}), "dev-1", "site-1", "Site A", "switch-1")`. It asserts that the named menus equal `["14"]`.

## Phase 3: Text changes

### T003 Replace the three printed menu numbers

- **Status**: open
- **Requirements**: FR-001, FR-002, FR-003, FR-004, SC-001, SC-002
- **Files**: `src/mist/resources/device/virtual_chassis.py` lines 420, 421, and 540
- **Acceptance**: Line 420 prints `   !? Use menu 161 to convert individual switches`. Line 421 prints `   !? Use menu 162 for bulk conversion by site list`. Line 540 prints `   Use menu 14 to verify conversion status after the device reboots.`. The WHY comments on lines 420 and 421 name menus 161 and 162. The file keeps its line count.
- **Verification**: `python -m pytest tests/unit/test_virtual_chassis.py`

### T004 Replace the stale comment and docstring menu numbers

- **Status**: open
- **Requirements**: FR-004, FR-005, SC-004
- **Files**: `src/mist/resources/device/virtual_chassis.py` lines 7, 81, 82, 83, 84, 96, 111, 116, 135, 153, 182, 206, and 231
- **Acceptance**: Line 7 reads `Menu operations: 161 (single convert), 162 (bulk by site list), 14 (status check).`. Lines 81 and 82 name menu 161 and its dependency roles. Lines 83 and 84 name menu 14 for the export. Lines 96, 111, 116, 135, 153, 182, 206, and 231 name menus 161, 162, or 14. The static test passes for the module. The diff replaces each line, so added and deleted line counts are equal.
- **Verification**: `symbol-diff --base origin/main src/mist/resources/device/virtual_chassis.py`

### T005 [P] Replace the stale root test text

- **Status**: open
- **Requirements**: FR-006, SC-004
- **Files**: `tests/test_virtual_chassis.py` lines 1 and 9
- **Acceptance**: Line 1 reads `"""Tests for VirtualChassisManager.convert_single menu 161 behavior."""`. Line 9 reads `import MistHelper  # Use the public menu surface that menu 161 exposes.`. The static test passes for this file.
- **Verification**: `python -m pytest tests/test_virtual_chassis.py`

### T006 [P] Add the changelog fragment

- **Status**: open
- **Requirements**: FR-011
- **Files**: `changelog.d/issue-4747-virtual-chassis-menu-options.md`
- **Acceptance**: The file has one `###` heading and one `- **Fixed**:` bullet. The bullet names issue #4747, the old menu numbers 92, 93, and 94, and the new numbers 161, 162, and 14. The file passes the STE gate. The changelog policy guard `tests/guardrails/test_changelog_fragment_policy.py` passes.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4747-virtual-chassis-menu-options.md`

## Phase 4: Gates and delivery

### T-LOCAL-GATES Run each applicable local gate

- **Status**: open
- **Requirements**: FR-008, FR-009, FR-010, FR-012, SC-006
- **Files**: the three modified files and the new changelog fragment
- **Acceptance**: Each gate below reports its expected result. Each gate that does not apply states its reason.
  - Compile: `python -m py_compile MistHelper.py` prints no output.
  - Lint: `python -m ruff check .` prints `All checks passed`.
  - Format: `python -m black --check .` reports no file that needs a change.
  - Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` prints `Success` (scope from `ci.yml`, RC-90).
  - Tests: `python -m pytest tests/unit/test_virtual_chassis.py`, `python -m pytest tests/test_virtual_chassis.py`, and `python -m pytest tests/guardrails/test_operation_registry_menu_coverage.py tests/guardrails/test_destructive_menu_docs.py` all pass.
  - Test quality: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` reports `gate: 0 new findings vs baseline` (RC-95).
  - Complexity: `radon cc src/mist/resources/device -j | complexity-gate --max 10` reports no block above 10.
  - Security lint: `bandit -c pyproject.toml -r src/mist/resources/device -q` reports no finding.
  - Code quality: `pylint src/ --fail-under=9.5` scores 9.5 or above.
  - Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` reports no finding (RC-91).
  - Docstrings: `pydocstyle src/ wsgi.py web_portal` reports no violation, and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` reports 90 percent or above (RC-92 and RC-93).
  - Menu reference: `python scripts/generate_menu_wiki.py` followed by `python -m scripts.menu_api_map` leaves no changed file. A changed file means the change needs a regenerated page (D-9).
  - Symbols: `symbol-diff --base origin/main src/mist/resources/device/virtual_chassis.py` and `symbol-diff --base origin/main tests/unit/test_virtual_chassis.py` report no module-level name change.
  - STE: the STE command for the changelog fragment (T006) passes at 80 or above.
  - Not applicable: the safe sweep. The `--test` run covers only the `safe` category (RC-98). Menus 161 and 162 are destructive, and menu 14 is resource intensive (RC-34 to RC-36).
  - Not applicable: the ops portal and ops platform gates, because no file changes in those folders.
  - Left to CI: the full test shards and the coverage run. The targeted tests above cover the change.
- **Verification**: `python -m pytest tests/unit/test_virtual_chassis.py`

### T-PR Commit, rebase, push, and open the pull request

- **Status**: open
- **Requirements**: FR-011, FR-012, SC-006
- **Files**: the three modified files and the new changelog fragment
- **Acceptance**: The orchestrator authorizes publication first. The issue does not authorize publication. The commit subject is `fix(virtual-chassis): name registered menus in guidance`. The commit body contains `Closes #4747` and the Co-authored-by trailer. The branch rebases onto `origin/main` and reruns the affected gates. The pull request title uses the same Conventional Commits form. The pull request body contains `Closes #4747`, the changed-file summary, the local gate results, and the rollback steps from `plan.md`. The fragment name stays `issue-4747-virtual-chassis-menu-options.md` after the pull request opens (RC-58).
- **Verification**: `python -m pytest tests/unit/test_virtual_chassis.py`

### T-REMOTE-CI Watch the remote checks

- **Status**: open
- **Requirements**: SC-007, FR-010
- **Files**: none
- **Acceptance**: `gh pr checks <number> --watch` reports each required check as passed on the latest commit. The `test_quality_gate` job (RC-95) and the `menu_reference_drift` and `pytest_coverage_shards` jobs pass. A failed job gets an issue with its full error output before any fix.
- **Verification**: `python -m pytest tests/unit/test_virtual_chassis.py`

### T-MERGE Authorize, review, and confirm after merge

- **Status**: open
- **Requirements**: FR-012, SC-007, A-6
- **Files**: none
- **Acceptance**: The orchestrator authorizes the merge. A human reviews the pull request, because the issue carries `needs-human-review`. The `auto-merge` label stays off (D-11). After the squash merge, `.github/workflows/container-build.yml` runs on `main`. The image revision label equals the merged commit. Deployment and the health check run only after a separate orchestrator authorization.
- **Verification**: `python -m pytest tests/unit/test_virtual_chassis.py` on the merged `main` commit
