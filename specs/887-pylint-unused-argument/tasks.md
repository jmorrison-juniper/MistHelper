# Tasks: Narrow the pylint W0613 unused-argument suppression

**Input**: Design documents from `specs/887-pylint-unused-argument/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/signature-changes.md](contracts/signature-changes.md), [contracts/pylint-gate.md](contracts/pylint-gate.md), [quickstart.md](quickstart.md)

**Tests**: The feature adds no test and removes no test. It updates 24 existing test call sites. Each update sits inside the source task that changes the signature. FR-026 requires that pairing.

**Organization**: The tasks below group by user story. Inside User Story 2, the tasks group by cascade thread, not by file. Section 3 of `research.md` explains the cascade rule.

**Source Issue**: #887, part 1 of 3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: The task can run in parallel. It touches a file that no other `[P]` task in the same group touches, and it holds no cascade relationship with those tasks.
- **[Story]**: The user story that owns the task. The values are `US1`, `US2`, and `US3`.
- Every task names the exact file paths that it touches.

## Path Conventions

The repository holds a single Python project. The package tree sits under `src/`. The test tree sits under `tests/`. Paths are relative to the repository root.

---

## Standing rules for every task

Read these rules once. They bind every task below.

1. **Use the virtual environment interpreter.** Run every Python command as `.venv\Scripts\python.exe -m <module>`. The global interpreter on the development machine is broken.
2. **Comment every changed line.** FR-030 and the project conventions require an inline comment that states why the line exists. Add the comment to each line that you touch and to each adjacent uncommented line in the same block.
3. **Change no runtime behavior.** FR-025 forbids a behavior change at any Outcome A site and at any Outcome B site. Remove no log call. Add no log call.
4. **Add no wrapper and no shim.** FR-032 forbids a wrapper function. FR-033 forbids a pass-through alias and a fallback path. Change the real call sites.
5. **Finish a cascade thread inside one task.** A partial removal moves the finding up one level and holds the count flat. Data model section 3 names that state "partly removed". No task may end in that state.
6. **Run the count command after every source task.**

   ```powershell
   .venv\Scripts\python.exe -m pylint src/ --disable=all --enable=W0613 --score=n
   ```

   Caution: The count must fall or hold. A rise means an unfinished cascade thread.

---

## Phase 1: Setup

**Purpose**: Confirm that the measuring tool matches the tool that produced the baseline.

- [ ] T001 Confirm the pylint version with `.venv\Scripts\python.exe -m pylint --version`. The baseline used pylint 4.0.6 and astroid 4.0.4 on Python 3.13.3. If the version differs, record the new version in `specs/887-pylint-unused-argument/research.md` section 1 before you continue. A version change can add a finding or remove a finding.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the two numbers that every later checkpoint compares against.

**Warning**: No source task may start until T002 confirms the finding count.

- [ ] T002 Re-measure the baseline (FR-003). Run `.venv\Scripts\python.exe -m pylint src/ --disable=all --enable=W0613 --score=n` from the repository root. Confirm 21 findings. Confirm that every file and every line matches the table in `specs/887-pylint-unused-argument/research.md` section 5. If the count differs, add each new finding to that table and assign an outcome before you continue.
- [ ] T003 [P] Record the test pass count before the work. Run `.venv\Scripts\python.exe -m pytest -q`. Write the pass count into the pull request draft. SC-005 compares the final count against this number.

**Checkpoint**: The baseline holds 21 findings. The triage record covers all 21. User story work can begin.

---

## Phase 3: User Story 1 - Record a decision for every finding (Priority: P1)

**Goal**: Prove that the triage record assigns one outcome to each of the 21 findings.

**Independent Test**: Read `specs/887-pylint-unused-argument/research.md` section 5. Confirm 21 rows. Confirm that every row names a file, a line, a function, a parameter, an outcome, and a justification. No code change is needed for this test.

- [ ] T004 [US1] Validate the triage record in `specs/887-pylint-unused-argument/research.md`. Confirm that section 5 holds 21 rows. Confirm that the outcome totals read 15 for Outcome A, 5 for Outcome B, and 1 for Outcome C. Confirm that no cell in the outcome column reads "To triage". Confirm that section 8 holds the exact suppression text for all six retained parameters. This satisfies SC-001.

**Checkpoint**: User Story 1 is complete. The record alone delivers value, because it separates a dead parameter from a contract-bound parameter.

---

## Phase 4: User Story 2 - Make the code match the triage (Priority: P2)

**Goal**: Apply the recorded outcome to every site. The finding count reaches zero.

**Independent Test**: Run `.venv\Scripts\python.exe -m pylint src/ --disable=all --enable=W0613 --score=n`. Confirm zero output. Run `.venv\Scripts\python.exe -m pytest`. Confirm that the suite passes.

### Phase 4a: Outcome A removals with no cascade

**Purpose**: Clear six findings. Each task changes one leaf function and its call sites. No caller inherits the parameter.

- [ ] T005 [P] [US2] Group 1. Remove the parameter `ap_macs` from `PacketCaptureManager._multi_ap_gather_params` in `src/capture/packet_capture.py`. The signature becomes `def _multi_ap_gather_params(self) -> dict[str, Any] | None:`. Update the single call site at `src/capture/packet_capture.py:1018` from `self._multi_ap_gather_params(ap_macs)` to `self._multi_ap_gather_params()`. Do not change the later call that passes `ap_macs` to `_multi_ap_confirm_and_launch`. No test changes.
- [ ] T006 [P] [US2] Group 3. Remove the parameter `msp_name` from `OrgLevelAPFirmwareUpgrader._display_org_list` in `src/firmware/org_ap_upgrader.py`. The signature becomes `def _display_org_list(self, orgs: list[Any]) -> None:`. Update the single call site at `src/firmware/org_ap_upgrader.py:617`. Do not change the calls that pass `msp_name` to `_collect_org_selection` or to the error log. No test changes.
- [ ] T007 [P] [US2] Group 5. Remove the final parameter `clone_payload` from `_MapsClone._confirm_clone` in `src/maps/_maps_clone.py`. Update the single call site at `src/maps/_maps_clone.py:352`. Caution: `src/gateway/template_config.py` holds a different method with the same name. Do not change that method and do not change `tests/unit/test_template_config.py`. No test changes.
- [ ] T008 [P] [US2] Group 6. Remove the first parameter `site_name` from `MapsManager._render_site_maps_table` in `src/maps/maps_manager.py`. The signature becomes `def _render_site_maps_table(maps: list) -> None:`. Update the single call site at `src/maps/maps_manager.py:559` in the same edit. Warning: `site_name` sits first of two. If you change the signature and leave the call site, the argument `maps` binds to the wrong slot. Do not change the `list_site_maps` code that prints and logs `site_name`. No test changes.
- [ ] T009 [P] [US2] Group 8. Remove both parameters `env_cmds` and `csv_cmds` from `AppRunner._prompt_for_commands` in `src/ssh/runtime/app_runner.py`. The signature becomes `def _prompt_for_commands() -> list[str]:`. Update the single call site at `src/ssh/runtime/app_runner.py:262`. Keep the `InputUtils.safe_input` call in the body unchanged. Do not change the `if` block in `_resolve_commands` that tests both lists. This task clears two findings. No test changes.
- [ ] T010 [US2] Checkpoint 4a. Run the count command. The count must read 15. A count above 15 means that a call site still passes a removed argument.

### Phase 4b: Outcome A removals with one production file plus tests

**Purpose**: Clear two more findings. Each task deletes a dead ruff suppression as well.

- [ ] T011 [P] [US2] Group 7. Remove the parameter `candidates` from `AddressResolver._combine` in `src/site/address_audit/address_resolver.py`. The signature becomes `def _combine(self, internal, osm, ui, query: str) -> ResolverResult:`. Update the single call site at `src/site/address_audit/address_resolver.py:83` from `self._combine(internal, osm, ui, candidates, query)` to `self._combine(internal, osm, ui, query)`. Warning: `candidates` sits fourth of five. The parameter `query` moves into the fourth slot. Change the signature and the call site in the same edit. No test changes.
- [ ] T012 [P] [US2] Group 9. Remove the parameter `results` from `_SsidTemplateCacheCluster._offer_resume` in `src/ssid_consolidation/_ssid_template_cache.py`. The signature becomes `def _offer_resume(self, phase: int) -> tuple[bool, list[dict[str, Any]]]:`. Delete the dead comment `# noqa: ARG002 - signature preserved for tests` in the same edit. Update the three call sites at `src/ssid_consolidation/_ssid_template_phase2.py:238`, `src/ssid_consolidation/_ssid_template_phase3.py:276`, and `src/ssid_consolidation/_ssid_template_phase45.py:610`. Each site passes a literal empty list today. Update the test call site at `tests/unit/test_ssid_template_consolidation.py:2027`. Do not change `tests/unit/test_ssid_template_consolidation.py` lines 3283 and 3339. Those two lines use `patch.object` by name, and a patch by name survives a signature change.
- [ ] T013 [US2] Checkpoint 4b. Run the count command. The count must read 13.

### Phase 4c: Cascade threads

**Purpose**: Clear seven more findings. Section 3 of `research.md` names four threads. Each thread is one task. The task changes the leaf and every cascade level in the same edit, so the count never rises.

- [ ] T014 [P] [US2] Group 2, the `mistapi` thread. In `src/firmware/bulk_ap_upgrader.py`, remove the final parameter `mistapi` from `BulkAPFirmwareUpgrader._upgrade_version_group` and from the cascade level `BulkAPFirmwareUpgrader._execute_multi_version_upgrade`. Update the call sites at `src/firmware/bulk_ap_upgrader.py:1479` and `src/firmware/bulk_ap_upgrader.py:1399`. Update the test call sites at `tests/unit/test_bulk_ap_upgrader.py:1724` and `tests/unit/test_bulk_ap_upgrader.py:1702`. Stop condition: `_execute_site_upgrade` keeps its `mistapi` parameter, because it also calls `_execute_single_version_upgrade`, which uses the value. Do not change `_invoke_upgrade_api`, which performs a lazy `import mistapi` of its own.
- [ ] T015 [P] [US2] Group 4, the `target_org_id` thread. In `src/inventory/inventory_summary/version_per_model_fetcher.py`, remove the first parameter `target_org_id` from `VersionPerModelFetcher._rows_for_model` and from the cascade level `VersionPerModelFetcher._expand_model_rows`. Update the call sites at `src/inventory/inventory_summary/version_per_model_fetcher.py:25` and `src/inventory/inventory_summary/version_per_model_fetcher.py:72`. Update the test call sites at `tests/unit/inventory/test_version_per_model_fetcher_wave3.py` lines 117, 123, 129, 136, 142, and 320. Warning: `target_org_id` sits first of four in both functions, and every call site passes it positionally. Change both signatures and all call sites in the same edit. Stop condition: `fetch` keeps `target_org_id` for `_prefetch_switches`, for `_prefetch_gateways`, for `_append_bulk_rows`, and for two log calls.
- [ ] T016 [US2] Group 10, the `sitegroup_lookup` thread. In `src/ssid_consolidation/_ssid_template_phase1.py`, remove the final parameter `sitegroup_lookup` from `_resolve_template` and from the cascade level `_resolve_site_wlan`. Delete the dead comment `# noqa: ARG001 - signature preserved for tests` in the same edit. Update the call sites at `src/ssid_consolidation/_ssid_template_phase1.py:289` and `src/ssid_consolidation/_ssid_template_phase1.py:351`. Update the test call sites at `tests/unit/test_ssid_template_consolidation.py` lines 423, 434, and 445. Stop condition: `_build_site_row` passes `lookups.sitegroup_lookup`, which is a dataclass field, and pylint does not report a field. Do not remove the `_SiteLookups.sitegroup_lookup` field. Do not remove `_build_sitegroup_lookup`. T024 files the issue that records that dead code. This task carries no `[P]` marker, because it edits `tests/unit/test_ssid_template_consolidation.py`, which T012 also edits.
- [ ] T017 [P] [US2] Group 12, the `source` thread. This is the widest thread. In `src/utils/address_utils.py`, remove the parameter `source` from all five methods of `NominatimValidator`: the three leaves `_make_api_request`, `_calculate_component_match`, and `_calculate_quality_boost`, and the two cascade levels `_calculate_confidence` and `_parse_geocode_response`. Update the call sites at `src/utils/address_utils.py` lines 1017, 1018, 1035, 1058, and 1061. Delete the three dead `# noqa: ARG002` comments that name future logging. Update the test call sites in `tests/unit/test_address_utils.py` at lines 728, 734, 740, 744, 751, 773, 778, 790, 798, 806, 813, 819, 827, and 844. Read the whole `NominatimValidator` test class before you edit, then run `tests/unit/test_address_utils.py` to catch a call that the search missed. Stop condition: `_geocode_address` keeps `source`, because it uses the value in two `logging.debug` calls in the exception path.
- [ ] T018 [US2] Group 11, the `debug` parameter. Remove the final parameter `debug` from `AddressUtils.apply_business_context_rules` in `src/utils/address_utils.py`. Delete the dead comment `# noqa: ARG004 - signature preserved for callers passing debug`. That comment states a claim that no call site supports. No production caller passes `debug`. The four tests already pass two arguments, so `tests/unit/test_address_utils.py` needs no change for this group. This task carries no `[P]` marker, because it edits `src/utils/address_utils.py`, which T017 also edits.
- [ ] T019 [US2] Checkpoint 4c. Run the count command. The count must read 6. Those six are the five Outcome B sites and the one Outcome C site. All 15 Outcome A findings are now clear.

### Phase 4d: Suppressions and companion issues

**Purpose**: Add six narrow suppressions with a specific reason. File three companion issues.

- [ ] T020 [P] [US2] Outcome B, row 7. Add a site-local suppression to `_build_probe_set` in `src/org/org_synthetic_probes_manager.py` at line 1619. Use the exact text from `research.md` section 8: `# pylint: disable=W0613 - back-compat contract with the caller. VLAN scope belongs on the tests[] row.` Place the comment on the parameter line or on the line directly above. Keep the parameter `vlan_ids`. Change no other line.
- [ ] T021 [P] [US2] Outcome B, rows 18 to 21. Add four site-local suppressions in `src/websocket/manager.py` at lines 318, 323, 336, and 343, on `WebSocketManager._on_open`, `_on_message`, `_on_error`, and `_on_close`. Use the four exact reason texts from `research.md` section 8. Each reason names the `websocket-client` library callback that passes the connection. Keep the parameter `websocket_connection` at all four sites.
- [ ] T022 [P] [US2] File the Outcome C companion issue with `gh issue create`. Title: "Phase 4 discards the operator deviation resolutions". Labels: `bug` and the scope label for `src/ssid_consolidation`. Body: the five-step chain from `research.md` section 6, which shows that `_resolve_deviations` records each operator answer in `resolutions`, that `_phase4_preflight` passes the map to `_build_all_template_configs`, that `_build_all_template_configs` passes it to `_build_template_config`, and that `_build_template_config` writes a `{{MISTHELPER_<PARAM>}}` placeholder instead. State that the parameter stays as the fix seam. Record the returned issue number. T025 needs that number.
- [ ] T023 [P] [US2] File the maps clone companion issue with `gh issue create`. Title: "The maps clone confirmation prints a static capability list". Labels: `bug` and the scope label for `src/maps`. Body: `_MapsClone._confirm_clone` in `src/maps/_maps_clone.py` prints the fixed text "Will copy: dimensions, orientation, location data, wayfinding, walls". The text does not describe the real payload that the operation sends, so the prompt can mislead the operator. State that the redesign of the confirmation text is out of scope for feature 887 and that this issue records the observation only.
- [ ] T024 [P] [US2] File the dead-code companion issue with `gh issue create`. Title: "Remove the unread sitegroup lookup after the W0613 narrowing". Labels: `chore` and the scope label for `src/ssid_consolidation`. Body: after T016, `_build_sitegroup_lookup` and the `_SiteLookups.sitegroup_lookup` field in `src/ssid_consolidation/_ssid_template_phase1.py` hold no reader. The module also re-exports `_build_sitegroup_lookup` for back-compat, so the removal changes a documented surface and needs its own specification.
- [ ] T025 [US2] Outcome C, row 13. Add a site-local suppression to `_build_template_config` in `src/ssid_consolidation/_ssid_template_phase45.py` at line 267. Warning: Do not remove the parameter `resolutions`. FR-015 forbids the removal, because the parameter is the seam that the future fix needs. Use the text from `research.md` section 8 and replace the placeholder with the number that T022 returned: `# pylint: disable=W0613 - kept as the seam for issue <N>. Phase 4 must apply this map.` The reason must name the defect and point at the companion issue. This task depends on T022.
- [ ] T026 [US2] Link the three issue numbers into the triage record at `specs/887-pylint-unused-argument/research.md`. Update section 6 with the Outcome C issue number. Update the three rows of section 7 with the matching issue numbers. Update the row 13 text in section 8 so that it holds the same number as the source comment. FR-017 requires this link.
- [ ] T027 [US2] Checkpoint 4d. Run the count command. The count must read 0. This satisfies FR-021 and SC-002. Do not start Phase 5 until this checkpoint reads zero.

### Phase 4e: Verification of the source tree

**Purpose**: Prove the source work before the gate changes. Run each gate exactly as the continuous integration job runs it.

- [ ] T028 [P] [US2] Scan the two ignored packages by hand (FR-004). Run `.venv\Scripts\python.exe -m pylint src/maps src/ssh --disable=all --enable=W0613 --score=n`. Expect no output. The gate cannot prove these files, because the `--ignore=maps,ssh,ui` flag hides them.
- [ ] T029 [P] [US2] Confirm that no suppression is too wide and that no dead ruff comment survives (FR-012, SC-006). Run `Get-ChildItem -Path src -Recurse -Filter *.py | Select-String -Pattern "pylint: disable=.*W0613"` and confirm exactly six matches. Five belong to Outcome B and one belongs to Outcome C. Read each reason and confirm that it names a library, a back-compat promise, or an issue number. Reject a generic phrase. Then run `Select-String -Path "src/ssid_consolidation/_ssid_template_cache.py","src/ssid_consolidation/_ssid_template_phase1.py","src/utils/address_utils.py" -Pattern "noqa: ARG00"` and confirm zero matches. All six dead ruff comments are gone.
- [ ] T030 [US2] Run the full gate suite from the repository root. Scope each command to the whole repository where the continuous integration job does. Every command must exit with code 0.

  ```powershell
  .venv\Scripts\python.exe -m ruff check .
  .venv\Scripts\python.exe -m black --check .
  .venv\Scripts\python.exe -m mypy src/ --config-file pyproject.toml
  .venv\Scripts\python.exe -m radon cc src/ -j | .venv\Scripts\python.exe -c "import json,sys; d=json.load(sys.stdin); bad=[(f,b['name'],b['complexity']) for f,bs in d.items() if isinstance(bs,list) for b in bs if b['complexity']>10]; print(bad or 'OK'); sys.exit(1 if bad else 0)"
  .venv\Scripts\python.exe -m pytest
  ```

  The radon command must report no block above complexity 10. Compare the pytest pass count against the number that T003 recorded. The counts must match, because the feature adds no test and removes no test. Caution: A radon failure points at an unrelated edit, because removing a parameter lowers the parameter count and does not raise complexity.

**Checkpoint**: User Story 2 is complete. The source tree holds zero unused arguments, and every gate passes.

---

## Phase 5: User Story 3 - Turn the gate back on (Priority: P3)

**Goal**: Remove the repository-wide suppression and prove the score on the Linux runner.

**Independent Test**: Read the continuous integration result for the branch. Confirm that the job named "Pylint (score gate)" passed. Confirm that `W0613` is absent from the `disable` list in `pyproject.toml`.

- [ ] T031 [US3] **This is the last source task.** Edit `pyproject.toml`. Remove the entry `"W0613"` from the `disable` list under `[tool.pylint."messages control"]`. The list becomes `disable = ["C0114", "C0115", "C0116", "W0718"]`. Keep every other entry in its position. Rewrite the comment block above the list so that it states three facts: `W0613` is enforced from this change onward, the audit record sits at `specs/887-pylint-unused-argument/research.md`, and six sites hold a site-local disable with a reason. Warning: Do not start this task until T027 reports zero findings. The moment the entry leaves the list, every open branch inherits the new gate, and a branch that still holds an unused argument fails. Do not change `"W0718"`. Do not change `"C0114"`, `"C0115"`, or `"C0116"`. Do not change `fail-under = 9.5`. Do not change the mypy `src.db` override. Do not change the `--ignore=maps,ssh,ui` flag in `.github/workflows/ci.yml`.
- [ ] T032 [US3] Reproduce the gate locally. Run `.venv\Scripts\python.exe -m pylint src/ --fail-under=9.5 --ignore=maps,ssh,ui` from the repository root. Expect exit code 0 and a score near 9.77. Warning: This local Windows result is an estimate only. It is not proof. T034 holds the proof.
- [ ] T033 [US3] Prove that the gate reports a new defect (SC-008). Add an unused parameter to any function under `src/`. Run the command from T032. Confirm that pylint reports a `W0613` message for the new parameter. Undo the temporary change. Run the command again and confirm that it passes. Do not commit the temporary change.
- [ ] T034 [US3] **Confirm the score on the real continuous integration run.** Push the branch. Open the run for the branch. Read the job named "Pylint (score gate)". Confirm that the job passed at the 9.5 threshold on `ubuntu-latest`. Record the reported score in the pull request body. Warning: A local Windows run is **not** acceptable proof. FR-023 forbids it. Issue #891 measured 9.71 on Windows and 9.41 on the `ubuntu-latest` runner for the same commit, and the Linux run failed the threshold. Warning: Do not add the `auto-merge` label until this job and CodeQL both pass. If the job fails, follow the rollback position in section 7 of `contracts/pylint-gate.md`:
  1. Read the runner log and list every message type with a count.
  2. Confirm that the drop comes from `W0613`. Compare the `W0613` count against zero.
  3. If any `W0613` message remains, fix that site. The audit missed it. This is the expected cause.
  4. If zero `W0613` messages remain, the drop comes from another message type on Linux. Record the message types and open a separate issue.
  5. Do not lower `fail-under`. FR-024 forbids it.
  6. Do not restore `"W0613"` to the `disable` list. FR-024 forbids it.
  7. If the score cannot reach 9.5 in this feature, revert the `pyproject.toml` commit only. Keep every source fix and keep the triage record. The gate change then waits for a follow-up branch, and the source work holds its value.

**Checkpoint**: All three user stories are complete. The gate reports any new unused argument on the first run.

---

## Phase 6: Polish and Cross-Cutting Concerns

- [ ] T035 [P] Update `CHANGELOG.md`. Add an entry under the `## [Unreleased]` heading. Follow the style of the entries above it: a level-three heading that names the change and the issue number, then bullets that lead with a bold label and a state word in parentheses. Suggested heading: `### Narrow the pylint W0613 unused-argument suppression (issue #887)`. Cover four points. Name the 21 triaged findings and the 15 parameters that the feature removed (Removed). Name the six site-local suppressions that replace the repository-wide entry (Changed). Name the six dead `noqa: ARG00x` comments that the feature deleted (Removed). Name the three companion issues (Recorded). State that no runtime behavior changed and that the test count held.
- [ ] T036 Run the Simplified Technical English linter at the 80 threshold on every Markdown file that the feature changes and on every document that the feature wrote. Every file must score 80 or higher.

  ```powershell
  .venv\Scripts\python.exe -m tools.ste_linter --min-score 80 CHANGELOG.md
  .venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/tasks.md
  .venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/research.md
  .venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/spec.md
  .venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/plan.md
  .venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/data-model.md
  .venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/quickstart.md
  .venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/contracts/signature-changes.md
  .venv\Scripts\python.exe -m tools.ste_linter --min-score 80 specs/887-pylint-unused-argument/contracts/pylint-gate.md
  ```

  Run the linter on the pull request body and on the three issue bodies as well. FR-031 covers all prose.
- [ ] T037 Walk `specs/887-pylint-unused-argument/quickstart.md` from Step 1 to Step 12 and confirm each expected result. Confirm Step 10: open the three issues, confirm that each holds a type label and a scope label, and confirm that the triage record and the source comment name the same Outcome C issue number. Write the pull request body. Link the spec issue, state `Closes #887` only when the whole of issue #887 is complete, and otherwise reference the issue without the closing keyword, because this feature covers part 1 of 3. Record the Linux pylint score from T034 in the body. Tick every conformance box in the pull request template.

---

## Dependencies and Execution Order

### Phase dependencies

| Phase | Depends on | Reason |
| - | - | - |
| Phase 1, Setup | Nothing | The version check reads the environment only. |
| Phase 2, Foundational | Phase 1 | A version change can move the baseline. |
| Phase 3, User Story 1 | Phase 2 | The record must cover the measured count. |
| Phase 4, User Story 2 | Phase 3 | The code follows the record. |
| Phase 5, User Story 3 | Phase 4e | FR-019 makes the `pyproject.toml` edit the final source change. |
| Phase 6, Polish | Phase 5 | The changelog states the delivered result. |

### Dependencies inside User Story 2

The sub-phases run in order. Each one ends with a checkpoint that reads a lower count.

| Sub-phase | Tasks | Ends with |
| - | - | - |
| 4a | T005 to T010 | 15 findings |
| 4b | T011 to T013 | 13 findings |
| 4c | T014 to T019 | 6 findings |
| 4d | T020 to T027 | 0 findings |
| 4e | T028 to T030 | A clean tree and green gates |

Task-level dependencies:

- T016 follows T012. Both edit `tests/unit/test_ssid_template_consolidation.py`.
- T018 follows T017. Both edit `src/utils/address_utils.py`.
- T025 follows T022. The suppression text needs the issue number.
- T026 follows T022, T023, and T024. The record needs all three numbers.
- T031 follows T027. The gate edit needs a zero count.
- T034 follows T031. The runner needs the pushed change.

### Cascade threads, one task each

The count never rises, because each task changes the leaf and every cascade level together.

| Thread | Task | Levels changed | Stops at |
| - | - | - | - |
| `mistapi` | T014 | `_upgrade_version_group`, `_execute_multi_version_upgrade` | `_execute_site_upgrade` |
| `target_org_id` | T015 | `_rows_for_model`, `_expand_model_rows` | `fetch` |
| `sitegroup_lookup` | T016 | `_resolve_template`, `_resolve_site_wlan` | `_build_site_row` |
| `source` | T017 | `_make_api_request`, `_calculate_component_match`, `_calculate_quality_boost`, `_calculate_confidence`, `_parse_geocode_response` | `_geocode_address` |

### Positional-shift tasks

These three tasks remove a parameter that is not last. Change the signature and every call site in the same edit.

| Task | Function | Position of the removed parameter |
| - | - | - |
| T008 | `MapsManager._render_site_maps_table` | First of two |
| T011 | `AddressResolver._combine` | Fourth of five |
| T015 | `_rows_for_model` and `_expand_model_rows` | First of four |

### The six dead ruff suppressions

`research.md` section 4 records that none of these reasons meets the FR-013 bar. Each comment is false after the parameter goes, so the task deletes it in the same edit.

| Comment | File | Task |
| - | - | - |
| `# noqa: ARG002 - signature preserved for tests` | `src/ssid_consolidation/_ssid_template_cache.py` | T012 |
| `# noqa: ARG001 - signature preserved for tests` | `src/ssid_consolidation/_ssid_template_phase1.py` | T016 |
| `# noqa: ARG002`, three sites, future logging reason | `src/utils/address_utils.py` | T017 |
| `# noqa: ARG004 - signature preserved for callers passing debug` | `src/utils/address_utils.py` | T018 |

T029 confirms that zero `noqa: ARG00` comments survive in those three files.

### Parallel opportunities

| Group | Tasks that can run together | Files |
| - | - | - |
| Phase 2 | T003 runs beside T002 | Both read only. |
| Phase 4a | T005, T006, T007, T008, T009 | Five different production files. No cascade between them. |
| Phase 4b | T011, T012 | `address_resolver.py` and the SSID template files. No shared file. |
| Phase 4c | T014, T015, T017 | `bulk_ap_upgrader.py`, `version_per_model_fetcher.py`, and `address_utils.py`, plus their own test files. |
| Phase 4d | T020, T021, T022, T023, T024 | Two different source files and three separate issue creations. |
| Phase 4e | T028, T029 | Two read-only scans. |
| Phase 6 | T035 runs beside the review of T034 | `CHANGELOG.md` only. |

T016, T018, T025, T026, T027, T030, and every Phase 5 task carry no `[P]` marker. Each one shares a file with an earlier task or depends on an earlier result.

---

## Implementation Strategy

### Minimum viable increment

User Story 1 alone delivers value. The triage record separates a dead parameter from a contract-bound parameter, and a reviewer can read it without a code change. T004 proves it.

### Incremental delivery

1. Complete Phase 1 and Phase 2. The baseline is confirmed.
2. Complete Phase 3. The record is proven. Stop here for a record-only increment.
3. Complete Phase 4. The source tree holds zero unused arguments. Stop here for a source-only increment. The gate change can wait for a follow-up branch. Section 7 of `contracts/pylint-gate.md` names this the safe stopping point.
4. Complete Phase 5. The gate is enforced.
5. Complete Phase 6. The changelog and the prose are current.

### Safe stopping point

If the Linux score falls below 9.5 and step 3 of the rollback finds no remaining `W0613` message, revert the `pyproject.toml` commit only. Keep every source fix and keep the triage record.

---

## Task summary

| Measure | Count |
| - | - |
| Total tasks | 37 |
| Setup and Foundational | 3 |
| User Story 1 | 1 |
| User Story 2 | 26 |
| User Story 3 | 4 |
| Polish | 3 |
| Tasks marked `[P]` | 19 |
| Source files changed | 16 |
| Test files changed | 4 |
| Configuration files changed | 1 |
| Companion issues filed | 3 |
