# Tasks: Organization and site identifier defaults

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](design/research.md), and [quickstart.md](design/quickstart.md).

**Format**: `[ID] [P?] [Requirements] Title`. `[P]` marks a task that is safe in parallel. Each task names its exact paths, its acceptance statement, one verification command from the local gates table, and its status.

**Status values**: `open`, `verified-present`, `partial`, or `absent`. Each code task is `absent` on main revision `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

**Test count**: Sixteen test functions are planned. Ten belong to batch 1, three to batch 2, one to batch 3, and two to batch 4.

## Phase 1: Batch B1, tenant boundary refusal (claimed slice)

- [ ] T001 [FR-001, FR-002, FR-004, FR-005, FR-006] Add failing refusal tests.
  - Files: `tests/unit/api/test_tenant_identifier_validation.py` (add).
  - Tests: `test_required_identifier_refused_before_sdk`, `test_optional_site_invalid_refused_before_org_sdk`, `test_refusal_names_field_without_value`, `test_refusal_logs_field_only`.
  - Acceptance: Each test fails on current main code. Each failing case records its SDK call count.
  - Verify: `python -m pytest tests/unit/api/test_tenant_identifier_validation.py`
  - Status: absent

- [ ] T002 [FR-001, FR-002, FR-004, FR-005, FR-006] Add the validator and route the six SDK boundaries. Depends on T001.
  - Files: `src/mist/access/api/tenant_fetch.py` (modify).
  - Acceptance: `TenantIdentifierValidator` and `TenantNameCollector` exist. `_add_valid_name` and `_add_valid_names` are removed. Each SDK call keeps its arguments. Each existing exception handler keeps its types and return values. Tests from T001 pass.
  - Verify: `python -m pytest tests/unit/api/test_tenant_identifier_validation.py`
  - Status: absent

- [ ] T003 [FR-003, FR-007, FR-008] Add valid-path tests. Depends on T002.
  - Files: `tests/unit/api/test_tenant_identifier_validation.py` (modify).
  - Tests: `test_none_site_keeps_organization_only`, `test_valid_opaque_identifiers_reach_sdk_unchanged`, `test_union_results_stay_sorted_and_unique`.
  - Acceptance: `None` makes one organization SDK call and zero site SDK calls. The value `org-1` reaches the SDK unchanged. The union stays sorted and unique.
  - Verify: `python -m pytest tests/unit/api/test_tenant_identifier_validation.py`
  - Status: absent

- [ ] T004 [FR-009, FR-010] Add failure-contract tests. Depends on T002.
  - Files: `tests/unit/api/test_tenant_identifier_validation.py` (modify).
  - Tests: `test_cloud_failures_keep_empty_contract`, `test_resolver_runtime_error_propagates`.
  - Acceptance: HTTP 4xx and 5xx, parse failure, and transport error keep the empty result. A resolver `RuntimeError` propagates unchanged.
  - Verify: `python -m pytest tests/unit/marvis/standalone/mist/access/api/test_api_tenant_fetch.py` (existing file, unchanged)
  - Status: absent

- [ ] T005 [FR-011] Add the service ping surfacing test. Depends on T002.
  - Files: `tests/unit/api/test_tenant_identifier_validation.py` (modify).
  - Test: `test_discovery_surfaces_refusal_as_error`.
  - Acceptance: The mixin in `src/mist/realtime/websocket/service_ping_discovery.py:51-87` raises `ValueError`. The manager prints `Error during Service Ping operation` (`service_ping_manager.py:467-468`). No "No tenants found" line appears.
  - Verify: `python -m pytest tests/unit/api/test_tenant_identifier_validation.py`
  - Status: absent

- [ ] T006 [P] [FR-013] Add the changelog fragment. Runs in parallel with T002 to T005.
  - Files: `changelog.d/issue-2863-tenant-identifier-validation.md` (add).
  - Acceptance: One `### Fixed` heading. One bullet that names issue #2863 and states the refusal.
  - Verify: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py`
  - Status: absent

## Phase 2: Batch B2, masking-default ratchet (blocked by decision D-14)

- [ ] T007 [FR-014, FR-015] Add the ratchet guard tests. Blocked until a compliant folder exists.
  - Files: `tests/guardrails/org_site_identifier_default/test_ratchet.py` (add).
  - Tests: `test_guard_fails_on_new_masking_default`, `test_guard_rejects_zero_file_and_zero_parse_scope`.
  - Acceptance: The guard fails on a fixture with one new default. It fails on a zero-file scope. It prints one proof line with scanned, parsed, finding, and baseline totals.
  - Verify: `python -m pytest tests/guardrails/org_site_identifier_default/test_ratchet.py`
  - Status: absent

- [ ] T008 [FR-015] Add the baseline validation test. Blocked until a compliant folder exists. Depends on T007.
  - Files: `tests/guardrails/org_site_identifier_default/baseline.json` (add) and `tests/guardrails/org_site_identifier_default/test_ratchet.py` (modify).
  - Test: `test_guard_rejects_malformed_or_wrong_baseline`.
  - Acceptance: The guard rejects duplicate keys, invalid paths, invalid counts, malformed JSON, a wrong schema version, a wrong rule identifier, and a wrong scope.
  - Verify: `python -m pytest tests/guardrails/org_site_identifier_default/test_ratchet.py`
  - Status: absent

## Phase 3: Batch B3, SSID site-variable writes (menu 145, interactive)

- [ ] T009 [FR-016] Refuse an empty site identifier before the SSID site write. Starts after B1 merges.
  - Files: `src/operations/execution/ssid_consolidation/_ssid_template_phase2.py` (modify lines 72, 132, 187, and 267 to 274) and `tests/unit/prod_readiness/standalone/operations/execution/ssid/test_ssid_template_consolidation.py` (modify).
  - Test: `test_ssid_empty_site_refused_before_write`.
  - Acceptance: No `_write_single_site_vars` call runs for a row with an empty site identifier. The phase summary shows the refusal and names `site_id`.
  - Verify: `python -m pytest tests/unit/prod_readiness/standalone/operations/execution/ssid/test_ssid_template_consolidation.py`
  - Status: absent

## Phase 4: Batch B4, destructive paths (human review before merge)

- [ ] T010 [FR-016] Refuse an empty site identifier before the chassis convert call. Starts after B1 merges and after human review of the batch plan.
  - Files: `src/mist/resources/device/virtual_chassis.py` (modify lines 579 and 820) and `tests/unit/test_virtual_chassis.py` (modify).
  - Test: `test_chassis_convert_missing_site_refused_before_sdk`.
  - Acceptance: `_call_convert_api` (line 575) makes no `convertSiteVirtualChassisToVirtualMac` call for an empty site identifier. The existing return value `False` and the printed message remain.
  - Verify: `python -m pytest tests/unit/test_virtual_chassis.py`
  - Status: absent

- [ ] T011 [FR-016] Refuse an empty site identifier before the gateway reboot call. Starts after B1 merges and after human review of the batch plan.
  - Files: `src/mist/resources/device/device_reboot_manager.py` (modify line 367) and `tests/unit/device/test_device_reboot_manager.py` (modify).
  - Test: `test_reboot_missing_site_refused_before_sdk`.
  - Acceptance: `_reboot_one_device` (line 364) makes no restart call for an empty site identifier. The returned text `ERROR: missing site_id` remains.
  - Verify: `python -m pytest tests/unit/device/test_device_reboot_manager.py`
  - Status: absent

## Phase 5: Final tasks for batch B1 (repeat for each later batch)

- [ ] T-LOCAL-GATES [FR-001 to FR-016] Run each local gate that applies to the changed files.
  - Files: `src/mist/access/api/tenant_fetch.py`, `tests/unit/api/test_tenant_identifier_validation.py`, `changelog.d/issue-2863-tenant-identifier-validation.md`, and this record.
  - Commands, in order:
    1. Compile: `python -m py_compile MistHelper.py`
    2. Compile changed modules: `python -m py_compile src/mist/access/api/tenant_fetch.py tests/unit/api/test_tenant_identifier_validation.py`
    3. Lint: `python -m ruff check .`
    4. Format: `python -m black --check .`
    5. Types: `python -m mypy $MYPY_PATHS --config-file pyproject.toml` with `MYPY_PATHS` from `.github/workflows/ci.yml:93`.
    6. Tests: `python -m pytest tests/unit/api/test_tenant_identifier_validation.py`
    7. Coverage: `python -m pytest tests/unit/api/test_tenant_identifier_validation.py --cov=src.mist.access.api.tenant_fetch --cov-branch --cov-report=term-missing --cov-fail-under=90`
    8. Complexity: `radon cc src/mist/access/api/tenant_fetch.py -j | complexity-gate --max 10`
    9. Security lint: `bandit -c pyproject.toml -r src/mist/access/api -q`
    10. Code quality: `pylint src/ --fail-under=9.5`
    11. Dead code: `vulture $VULTURE_PATHS --min-confidence 70` with `VULTURE_PATHS` from `.github/workflows/ci.yml:101`.
    12. Docstrings: `pydocstyle $PYDOCSTYLE_PATHS` and `interrogate $INTERROGATE_PATHS --fail-under 90`.
    13. Symbols: `symbol-diff --base origin/main src/mist/access/api/tenant_fetch.py`
    14. Structure (FR-012): `git diff --name-status origin/main -- src/mist/access/api tests/guardrails` shows no `A` line.
    15. STE: `ste-linter --config .ste-linter.toml --min-score 80` for each changed Markdown file, with the full dictionary.
  - Acceptance: Each command exits 0 and matches the expected result in the Local gates table (`.github/copilot-instructions.md:50-76`).
  - Verify: The list above. Each command is from the Local gates table.
  - Status: open

- [ ] T-PR [FR-013] Open the pull request after the parent grant.
  - Files: the paths of T002 to T006, listed in the Change Map of `plan.md`.
  - Actions:
    1. Create branch `fix/2863-tenant-identifier-validation` from `main`.
    2. Commit with the title `fix(tenant): refuse missing organization and site identifiers`.
    3. Add the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>` to the commit message.
    4. Write the body with `Part of #2863`. Do not write `Closes #2863` in this batch.
    5. Rename the fragment to `pr-<number>.md` after the pull request number exists (`.github/copilot-instructions.md:451-453`).
    6. Do not add the `auto-merge` label.
  - Acceptance: The body lists each local gate and its result. The parent grant is recorded on issue #2863 before the push.
  - Verify: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` shows `gate: 0 new findings vs baseline`.
  - Status: open

- [ ] T-REMOTE-CI [FR-001 to FR-016] Watch the remote checks. Depends on T-PR.
  - Files: the same paths as T-PR.
  - Action: Run `gh pr checks <number> --watch` for the pull request.
  - Acceptance: Each required check passes. The CodeQL check passes.
  - Verify: Full tests. Run the two `pytest-chunks` commands in the Full tests section of `.github/copilot-instructions.md`.
  - Status: open

- [ ] T-MERGE [FR-001 to FR-016] Squash merge after authorization. Depends on T-REMOTE-CI.
  - Files: the same paths as T-PR.
  - Actions:
    1. The parent authorizes the merge.
    2. A human reviews the change and removes `needs-human-review`.
    3. Add the `auto-merge` label only after each check is green (`AGENTS.md:230-231`).
  - Acceptance: One squash commit lands on `main`. The branch and its worktree are removed.
  - Verify: `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json` shows `gate: 0 new findings vs baseline` on the merge candidate.
  - Status: open

## Dependencies and Execution Order

- T001 comes first. T002 depends on T001. T003, T004, and T005 depend on T002 and run in order, because they share one test file.
- T006 runs in parallel with T002 to T005.
- T-LOCAL-GATES depends on T002 to T006.
- T-PR depends on T-LOCAL-GATES and on the parent grant.
- T-REMOTE-CI depends on T-PR. T-MERGE depends on T-REMOTE-CI.
- T007 and T008 depend on B1 merged and on the structural remediation. They run in order.
- T009 depends on B1 merged. T010 and T011 depend on B1 merged and on human review. They run in parallel.

Caution: keep each task inside its own batch. A task from batch 4 must not start while its human review is open.
