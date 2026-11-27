# Tasks: Convert Verified Network and Routing Settings

**Input**: `spec.md`, `plan.md`, and the supporting artifacts under `design\`.

**Parity mapping**: This list covers tasks T013 and T014 of the full-parity map in merged PR #4596. Tasks T001 through T003 check prerequisites. Tasks T004 through T007 write the failing tests for T013. Tasks T008 through T014 implement T014. Task T015 audits the result.

**Rules for this list**: Each task names exact repository paths and one verification command from the local gates table. Mark a task done only after its verification passes and its evidence exists.

## Format

- `[P]`: The task can run in parallel with other `[P]` tasks. It uses different files and has no shared dependency.
- `FR-###` and `SC-###`: The requirement and success criteria IDs in `spec.md`.
- `Depends on`: The tasks that must pass first.
- Status values are `open`, `verified-present`, `partial`, or `absent`.

## Phase 1: Prerequisites

- [ ] T001 [P] Verify the prerequisite evidence and merges.
  - Requirements: FR-013, FR-016
  - Depends on: None
  - Paths: `design\research.md` in this record, section Remote Verification, rows R07 and R08
  - Acceptance: Issue #4634 holds a row for each emitted key. Issues #4636 and #4638 merge before T008 starts.
  - Verification: `python -m pytest tests/guardrails/test_nested_package_structure.py`
  - Status: partial. Issue #4636 has a draft. Issues #4634 and #4638 have no record on main.

- [ ] T002 [P] Record the DNS baseline before any edit.
  - Requirements: FR-001
  - Depends on: None
  - Paths: `tests/integration/web_portal/cisco_config_converter/test_routes.py`, `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Acceptance: Both files pass on the unchanged tree. Record the counts in `analysis.md`.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Status: open.

- [ ] T003 Write the mapping register from the OpenAPI evidence.
  - Requirements: FR-013, SC-004
  - Depends on: T001
  - Paths: `design\contracts\mist-field-register.md` in this record
  - Acceptance: Each emitted key has one row with an OpenAPI line and a status. Each unverified key appears in the Unverified list.
  - Verification: `ste-linter --config .ste-linter.toml --min-score 80 design\contracts\mist-field-register.md`
  - Status: partial. The draft exists in this record.

## Phase 2: Tests First

- [ ] T004 [P] Write the interface test module before the interface code.
  - Requirements: FR-002, FR-003, FR-004, FR-005, FR-012, FR-014
  - Depends on: T001, T003
  - Paths: `tests/integration/web_portal/cisco_config_converter/conversion/__init__.py`, `tests/integration/web_portal/cisco_config_converter/conversion/test_network.py`
  - Acceptance: The module holds tests 1 to 17 from the test list in `analysis.md`. Each test fails before T010.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_network.py`
  - Status: open.

- [ ] T005 [P] Write the service test module before the DHCP and NTP code.
  - Requirements: FR-006, FR-010, FR-011
  - Depends on: T001, T003
  - Paths: `tests/integration/web_portal/cisco_config_converter/conversion/test_services.py`
  - Acceptance: The module holds tests 18 to 25. Each test fails before T011 and T013.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_services.py`
  - Status: open.

- [ ] T006 [P] Write the routing test module before the routing code.
  - Requirements: FR-007, FR-008, FR-009
  - Depends on: T001, T003
  - Paths: `tests/integration/web_portal/cisco_config_converter/conversion/test_routing.py`
  - Acceptance: The module holds tests 26 to 32. Each test fails before T012.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_routing.py`
  - Status: open.

- [ ] T007 [P] Write the compatibility and guard test module before the DNS change.
  - Requirements: FR-001, FR-013, FR-015
  - Depends on: T001, T002, T003
  - Paths: `tests/integration/web_portal/cisco_config_converter/conversion/test_compat.py`
  - Acceptance: The module holds tests 33 to 35. Test 33 expects the revised known-gap sentence and the domain key.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_compat.py`
  - Status: open.

## Phase 3: Package Move and Shared Types

- [ ] T008 Move the DNS converter and add the domain-name line.
  - Requirements: FR-001, FR-011, FR-017
  - Depends on: T004, T005, T006, T007, T001
  - Paths: add `src/interfaces/portals/cisco_config_converter/conversion/__init__.py`, `src/interfaces/portals/cisco_config_converter/conversion/common/__init__.py`, `src/interfaces/portals/cisco_config_converter/conversion/common/dns.py`. Delete `src/interfaces/portals/cisco_config_converter/conversion.py`. Modify `src/interfaces/portals/cisco_config_converter/routes.py` and `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`.
  - Acceptance: `IOSDnsConverter.convert` keeps its public method. Only the known-gap sentence and the domain key change. No shim remains.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
  - Status: open.

- [ ] T009 Add the shared types and the block reader.
  - Requirements: FR-014, FR-015, FR-016
  - Depends on: T008
  - Paths: add `src/interfaces/portals/cisco_config_converter/conversion/common/fragment.py` and `src/interfaces/portals/cisco_config_converter/conversion/common/syntax.py`
  - Acceptance: `PortAssignment`, `NetworkFragment`, `ConvertedNetwork`, the constant `UNRESOLVED_REASONS`, `SourceLine`, and `IOSBlockReader` exist. Each module holds five top-level names or fewer. The reader logs before and after parsing.
  - Verification: `python -m py_compile src/interfaces/portals/cisco_config_converter/conversion/common/fragment.py src/interfaces/portals/cisco_config_converter/conversion/common/syntax.py`
  - Status: open.

## Phase 4: Network Implementation

- [ ] T010 [P] Implement the interface rules.
  - Requirements: FR-002, FR-003, FR-004, FR-005, FR-012, FR-014
  - Depends on: T004, T009
  - Paths: add `src/interfaces/portals/cisco_config_converter/conversion/network/interfaces.py`
  - Acceptance: Tests 1 to 17 pass. Each class holds five members or fewer.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_network.py`
  - Status: open.

- [ ] T011 [P] Implement the DHCP pool rules.
  - Requirements: FR-006, FR-013, FR-014
  - Depends on: T005, T009
  - Paths: add `src/interfaces/portals/cisco_config_converter/conversion/network/dhcp.py`
  - Acceptance: Tests 18 to 21 pass. The range comes from leading and trailing exclusions only.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_services.py`
  - Status: open.

- [ ] T012 [P] Implement the static route, VRF, and BGP rules.
  - Requirements: FR-007, FR-008, FR-009, FR-014
  - Depends on: T006, T009
  - Paths: add `src/interfaces/portals/cisco_config_converter/conversion/network/routing.py`
  - Acceptance: Tests 26 to 32 pass. No credential or prefix appears in the output.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_routing.py`
  - Status: open.

- [ ] T013 [P] Implement the NTP server rules.
  - Requirements: FR-010, FR-014
  - Depends on: T005, T009
  - Paths: add `src/interfaces/portals/cisco_config_converter/conversion/network/ntp.py`
  - Acceptance: Tests 22 and 23 pass. Only IPv4 addresses without options appear in the output.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_services.py`
  - Status: open.

- [ ] T014 Wire the network entry point and extend the template type.
  - Requirements: FR-013, FR-017
  - Depends on: T010, T011, T012, T013, T001
  - Paths: add `src/interfaces/portals/cisco_config_converter/conversion/network/__init__.py`. Modify `src/interfaces/portals/cisco_config_converter/state/proposal.py` to add `NotRequired` keys to `GatewayTemplate`.
  - Acceptance: `IOSNetworkConverter.convert(source, assignments)` returns a `NetworkFragment`. The file `state/proposal.py` keeps four top-level names.
  - Verification: `python -m pytest tests/integration/web_portal/cisco_config_converter/conversion`
  - Status: open.

## Phase 5: Audit

- [ ] T015 Audit comments, logging, limits, and names.
  - Requirements: FR-016, SC-006
  - Depends on: T014
  - Paths: every file under `src/interfaces/portals/cisco_config_converter/conversion/` and `src/interfaces/portals/cisco_config_converter/state/proposal.py`
  - Acceptance: Each executable line has an inline comment. Each action has an info line before and a debug line after. Each method has five parameters or fewer.
  - Verification: `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
  - Status: open.

## Final Tasks

- [ ] T-LOCAL-GATES Run each applicable local gate on the changed files.
  - Requirements: FR-001 through FR-017, SC-001 through SC-006
  - Depends on: T015
  - Paths: every changed file from T008 through T015
  - Acceptance: Run each applicable gate below. Record each exact result in the pull request body.
  - Applicable gates, one per line:
    - Compile: `python -m py_compile` on each changed Python file.
    - Lint: `python -m ruff check .`
    - Format: `python -m black --check .`
    - Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`
    - Tests: `python -m pytest tests/integration/web_portal/cisco_config_converter` and `python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`
    - Full tests: the two `pytest-chunks` commands in `.github/copilot-instructions.md`
    - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
    - Test quality: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json`
    - Complexity: `radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10`
    - Security lint: `bandit -c pyproject.toml -r src/interfaces/portals/cisco_config_converter -q`
    - Code quality: `pylint src/ --fail-under=9.5`
    - Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`
    - Docstrings: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`
    - Symbols: `symbol-diff --base origin/main` for each new module. Document the removed `conversion.py` exception.
    - Guardrails: `python -m pytest tests/guardrails`
  - Not applicable, one reason per line:
    - Safe sweep and menu reference: no menu changed.
    - STE: no listed Markdown file changed.
    - Dependency audit: no dependency changed.
    - Ops portal and ops platform: no change in those trees.
  - Verification: Each applicable gate reports its expected result.
  - Status: open.

- [ ] T-PR Commit, rebase, push, and open the pull request.
  - Requirements: FR-001 through FR-017
  - Depends on: T-LOCAL-GATES
  - Paths: branch `feat/4640-convert-verified-network-routing`
  - Acceptance: The commit subject is `feat(web-portal): convert verified network and routing settings`. The pull request title uses the same form. The body contains `Closes #4640`, the symbol-gate exception, and each gate result.
  - Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body`
  - Status: open.

- [ ] T-REMOTE-CI Watch the remote checks until each one finishes.
  - Requirements: FR-001 through FR-017
  - Depends on: T-PR
  - Paths: the pull request from T-PR
  - Acceptance: Each required check reports success before the `auto-merge` label is added.
  - Verification: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`
  - Status: open.

- [ ] T-MERGE Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: FR-001 through FR-017
  - Depends on: T-REMOTE-CI and orchestrator authorization
  - Paths: the pull request from T-PR
  - Acceptance: Add the `auto-merge` label only after T-REMOTE-CI passes. Squash the merge. Remove the branch and worktree.
  - Verification: `gh pr view <number> -R jmorrison-juniper/MistHelper --json autoMergeRequest,state`
  - Status: open.

## Dependencies and Execution Order

| Task | Depends on | Parallel group |
| --- | --- | --- |
| T001 | None | A |
| T002 | None | A |
| T003 | T001 | None |
| T004 | T001, T003 | B |
| T005 | T001, T003 | B |
| T006 | T001, T003 | B |
| T007 | T001, T002, T003 | B |
| T008 | T004, T005, T006, T007, T001 | None |
| T009 | T008 | None |
| T010 | T004, T009 | C |
| T011 | T005, T009 | C |
| T012 | T006, T009 | C |
| T013 | T005, T009 | C |
| T014 | T010, T011, T012, T013, T001 | None |
| T015 | T014 | None |
| T-LOCAL-GATES | T015 | None |
| T-PR | T-LOCAL-GATES | None |
| T-REMOTE-CI | T-PR | None |
| T-MERGE | T-REMOTE-CI and orchestrator authorization | None |

Parallel group B holds four test modules. Each module is a different file. Parallel group C holds four implementation modules. Each module is a different file. No group shares a file. Task T014 owns `conversion/network/__init__.py`, so no parallel task edits that file.

## Test Plan Summary

The plan names 35 test functions. Each parametrized case counts once.

| Module | Functions | Requirements covered |
| --- | --- | --- |
| `test_network.py` | 17 (tests 1 to 17) | FR-002, FR-003, FR-004, FR-005, FR-012, FR-014 |
| `test_services.py` | 8 (tests 18 to 25) | FR-006, FR-010, FR-011, FR-014 |
| `test_routing.py` | 7 (tests 26 to 32) | FR-007, FR-008, FR-009, FR-014 |
| `test_compat.py` | 3 (tests 33 to 35) | FR-001, FR-013, FR-015 |

The existing tests in `test_routes.py` and in the unit test file cover FR-001 for the existing DNS behavior. Test 34 blocks sockets and file opens during the conversion path.
