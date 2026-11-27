# Research: Weak zero-assertion triage

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk.

### D-1. Gate authority

- Alternatives: the 0.6.3 reports in the issue comments. The pinned analyzer at commit `2239e7bd`. The upstream main branch of `misthelper-devtools`.
- Chosen: the pinned analyzer at commit `2239e7bd`, version 0.6.4.
- Reason: CI runs this pin. The full gate passed on `main` at `f03c6c9` in run 45774119357.
- Risk: A local install that predates the pin reports false new findings. T001 stops the work when the commit differs.

### D-2. Removal of stale entries

- Alternatives: edit the JSON by hand. Keep the stale entries. Run the analyzer write command.
- Chosen: the analyzer write command with the full-suite scope, in one serial pull request (T004).
- Reason: The analyzer owns the key format. Hand edits can drift from it.
- Risk: The write command rewrites every rule. The pull request restores each entry outside `weak_zero_assertions`.

### D-3. Detector-gap handling

- Alternatives: rewrite each test to match the detector. Add a configuration exclusion or a fixture marker. Route the gap upstream and keep the entries.
- Chosen: route upstream and keep the entries (T005).
- Reason: The assertions are real. A rewrite weakens the test. An exclusion hides the finding.
- Risk: The 129 entries stay until the devtools pin changes.

### D-4. Repair of zero-construct tests

- Alternatives: delete each test. Add `assert True`. Add behavior checks.
- Chosen: add behavior checks (T006 to T015).
- Reason: The checks keep coverage and add evidence. The other options lower the gate.
- Risk: A repaired test can share state with another test. Each changed file runs alone and in order.

### D-5. Helper-based cases

- Alternatives: trust the helper name. Read the helper body.
- Chosen: read the helper body before classification (T003).
- Reason: Comments 110 and 155 show that a helper name does not prove an assertion, and a call can hide one.
- Risk: The reading costs time for 20 entries.

### D-6. Slice shape and merge order

- Alternatives: one large pull request. One pull request per test file. Ten domain slices merged serially.
- Chosen: ten domain slices. Each slice merges alone. A slice splits when its diff exceeds 400 changed lines.
- Reason: `AGENTS.md` requires one change per pull request. Parallel slices conflict on the shared baseline.
- Risk: Ten merges take more time than one.

### D-7. Closing keywords

- Alternatives: `Closes #2711` in each slice. `Part of #2711` in each slice. `Closes #2711` in the final pull request only.
- Chosen: `Part of #2711` in each slice. `Closes #2711` appears in the final pull request only.
- Reason: The umbrella issue closed automatically three times (comments 30, 48, and 57).
- Risk: The final pull request waits for SC-003.

### D-8. Test paths

- Alternatives: follow the paths in the comments. Follow the paths on `main`.
- Chosen: the paths on `main`.
- Reason: Pull request #4358 moved files into domain folders. The comments still cite the old paths.
- Risk: Readers who use the comments reach a missing file. The mapping appears in `analysis.md` section 1.

### D-9. Preserved branches

- Alternatives: integrate each preserved commit. Re-derive each assertion from `main`. Wait for an owner handoff for each file.
- Chosen: re-derive from `main`, unless the owner gives a file handoff.
- Reason: Comments 159 through 166 record holds on several files.
- Risk: Some preserved work repeats.

### D-10. Acceptance command

- Alternatives: `python -m tools.test_quality_analyzer`. `test-quality-analyzer`.
- Chosen: `test-quality-analyzer`.
- Reason: The `tools` module is absent on `main`. The tree check returns zero paths.
- Risk: None known.

Human decisions: none. Each decision falls inside engineering authority.

## Remote verification

Each row is one remote check. The `blob_sha` column holds a blob SHA for a file. For a commit row, it holds the commit SHA. For an absent row, it holds `absent`. The `Line` column gives the first matching line, or zero when the check has no line.

The table has 37 rows. The `remote_checks` array in `2711-STATUS.json` has 37 rows.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| -: | - | - | - | - | - | -: |
| 1 | The baseline holds 557 `weak_zero_assertions` entries | `.github/test-quality-baseline.json` | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 76 |
| 2 | The analyzer config holds the rules table | `.github/test-quality-config.toml` | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 16 |
| 3 | CI runs the full analyzer gate | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 632 |
| 4 | The devtools pin is commit `2239e7bd` | `requirements-dev.txt` | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 197 |
| 5 | The quality guide documents the prune command | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 33 |
| 6 | The preflight guard class exists | `tests/guardrails/local_test_quality_loop/test_guidance.py` | main | 1f49b5fe3deea64d8e3bf3f5a49635f457d0819b | present | 771 |
| 7 | `TestSecretMasker` derives from `unittest.TestCase` | `tests/test_upgrade_portal_audit.py` | main | 4d36aa4faf0d366b2ebadb70900344e6d37037c2 | present | 20 |
| 8 | The first flagged function starts at line 31 | `tests/test_upgrade_portal_audit.py` | main | 4d36aa4faf0d366b2ebadb70900344e6d37037c2 | present | 31 |
| 9 | The last flagged function starts at line 371 | `tests/test_upgrade_portal_audit.py` | main | 4d36aa4faf0d366b2ebadb70900344e6d37037c2 | present | 371 |
| 10 | The first SSH flagged function starts at line 66 | `tests/unit/test_ssh_host_key_tofu.py` | main | 57e66775417591efd0456a0cbfdebc1c938accd6 | present | 66 |
| 11 | The second SSH flagged function starts at line 83 | `tests/unit/test_ssh_host_key_tofu.py` | main | 57e66775417591efd0456a0cbfdebc1c938accd6 | present | 83 |
| 12 | The remaining template finding starts at line 76 | `tests/unit/export/test_org_template_exporter.py` | main | 7d1002d8b1a007826f3a3dbd525099234c517aa2 | present | 76 |
| 13 | The relocated favicon test starts at line 67 | `tests/unit/maps/standalone/interfaces/portals/test_favicon.py` | main | 737c8382e41cca30c6e4998b486433531e5d0a96 | present | 67 |
| 14 | Comment 155 cites `tests/unit/test_favicon.py` as live | `tests/unit/test_favicon.py` | main | absent | stale | 0 |
| 15 | The sequential-path test starts at line 95 | `tests/unit/export/test_gateway_test_exporter.py` | main | 7b98a926156b37158064c7ce35babec3208637c5 | present | 95 |
| 16 | The no-site test starts at line 137 | `tests/unit/export/test_site_search_exporter.py` | main | 6c810aa688f906e374eae376cefc3bfe562daaa5 | present | 137 |
| 17 | The synthetic probe test starts at line 991 | `tests/unit/org/test_org_synthetic_probes_manager.py` | main | 3e9652d978cb5e2c90b912d39f39e80c95052977 | present | 991 |
| 18 | The compatibility entry test starts at line 14 | `tests/integration/test_next5_compatibility_paths.py` | main | 4131d2c646fa4b211912086c91edc8f7a92a54fa | present | 14 |
| 19 | The compatibility helper module defines functions | `tests/integration/helpers/compatibility_assertions.py` | main | 80fb6d5d2ac4cf89668fd011d3c5bc78e72ae8c2 | present | 8 |
| 20 | The healthy-connection test starts at line 284 | `tests/unit/utils/test_zscaler_probe_transport.py` | main | c028e21d33d189046b4f91b154f244da2dcd698c | present | 284 |
| 21 | The first Playwright `expect` call is at line 286 | `tests/e2e/upgrade_portal/test_site_selection.py` | main | 4a60b15fb7c0b9798c18321111c7e28f3d792456 | present | 286 |
| 22 | The route function `Resolve-SpecFeaturePath` is defined | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| 23 | The reference record task file exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md` | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 1 |
| 24 | The baseline cites `tests/unit/test_bulk_switch_upgrader.py` as live | `tests/unit/test_bulk_switch_upgrader.py` | main | absent | stale | 0 |
| 25 | The issue acceptance command module `tools/test_quality_analyzer` exists | `tools/test_quality_analyzer` | main | absent | stale | 0 |
| 26 | A 2711 route folder exists on `main` | `specs/numbered/0/0/0/4/1/3/2/1` | main | absent | absent | 0 |
| 27 | A `2711-` record exists under `specs` on `main` | `specs/**/2711-*` | main | absent | absent | 0 |
| 28 | Commit `db5f6263` exists for the webhook repair | `tests/unit/config/standalone/foundation/persistence/redis/test_webhook_ingestion.py` | main | db5f62639868255c5926f27eece0947d005886f2 | present | 0 |
| 29 | Commit `73bdbbfd` exists for the firmware status repair | `tests/unit/firmware/test_firmware_upgrade_status_checker.py` | main | 73bdbbfd873a565fb023ee27b28790982343df72 | present | 0 |
| 30 | Commit `57df4aa4` exists for the capture payload repair | `tests/integration/test_packet_capture_org_compatibility.py` | main | 57df4aa45fa7025bce4ea80be5bc398604561697 | present | 0 |
| 31 | Commit `d233eb31` exists for the parameter collector repair | `tests/unit/ui/test_parameter_collector.py` | main | d233eb31c7e92d8f3f77fc5095b5e77d42ecd7c0 | present | 0 |
| 32 | Commit `3964d21d` exists as the cited main snapshot | `.github/test-quality-baseline.json` | main | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 0 |
| 33 | Commit `1868b0d8` exists as the PR 4819 head | `tests/integration/test_site_capture_loop_compatibility.py` | main | 1868b0d8853e73f19a8c3a7693c6d2fdbccb0e33 | present | 0 |
| 34 | The devtools pin reports version 0.6.4 | misthelper-devtools `pyproject.toml` | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 0f52f10c8308a883314489e20970883c62d0943d | present | 3 |
| 35 | The devtools strong-mock set starts at line 40 | misthelper-devtools `src/misthelper_devtools/test_quality_analyzer/detection/weak_assertion.py` | 2239e7bd468fd27e40c43f2b87fcd35a2e49672b | 954ff75110492c221efba929f200225ac6415f54 | present | 40 |
| 36 | The local install records the pinned commit | `.venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info\direct_url.json` | local | 25f69f79362e354467dfa92cc1f1e4a183b883b4 | present | 1 |
| 37 | The main `Quality Gates` run passed the test-quality job | `.github/workflows/ci.yml` (run 45774119357) | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |

Method notes:

- Rows 1 to 27 use the contents API and one recursive tree call on `main`. The tree held 8,821 blobs, and it was not truncated.
- Rows 28 to 33 use the commits API. A 200 response counts as present.
- Row 34 and row 35 use the contents API at commit `2239e7bd`.
- Row 36 uses a local blob hash. The file is metadata of the local install.
- Row 37 uses `gh run view` and the jobs API for the `Quality Gates` run.
- Remote blob SHAs equal the local blob SHAs for 120 of the 121 baseline files. The remaining file is absent on `main`.
- The 37 rows reflect every remote check used in this record. Other claims cite only local source or documentation.

## Sources

### Local repository files

- Read-only classification output for this record: `files/spec-drafts/_meta/2711-triage-run5.txt`. The script that produced it is `files/spec-drafts/_meta/2711-triage-scan.ps1`. Earlier outputs used a body parser that ended early on multi-line signatures. Those outputs are superseded.

- `AGENTS.md` (repository root). Read in full. Sections used: Writing style, Tests, Git flow, Pull request, Parallel agents and shared state, Specifications.
- `.github/copilot-instructions.md`. Read in full. Sections used: Local gates table, Test quality ratchet, Known pitfalls, Serial validation and merge queues, Pull request titles.
- `.specify/memory/constitution.md`. Read in full, version 1.9.0. Sections used: Core Principles I to VII, Technology and Compatibility Constraints, Complexity-Driven SpecKit Escalation.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`. Read in full. Headings followed in this record.
- `.specify/scripts/powershell/spec-route.ps1` lines 4 and 34. The route calculation uses base-5 digits padded to eight segments.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (14 files). Read the headings to copy the shape only.
- `documentation/quality-gates.md` lines 17 to 46. Commands for the prune and write procedures.
- `.github/test-quality-baseline.json` lines 1 to 45 (schema) and line 76 (first weak-zero entry).
- `.github/test-quality-config.toml` lines 1 to 16 (rules table begins at line 16).
- `requirements-dev.txt` line 197 (pin).
- `.github/workflows/ci.yml` line 632 (gate command).
- `tests/guardrails/local_test_quality_loop/test_guidance.py` line 771 (preflight class).
- `tests/test_upgrade_portal_audit.py` lines 20 and 31 (class and first flagged function). Full file read in part.
- `tests/unit/test_ssh_host_key_tofu.py` lines 55 to 92 (three flagged functions).

### Installed analyzer and SDK

- `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\detection\weak_assertion.py`:
  - Lines 1 to 20: rule description.
  - Lines 40 to 53: `_STRONG_MOCK_ASSERT_METHODS`. This set holds `assert_called_once_with` at line 43. It lacks `assert_called_once` and `assert_awaited`.
  - Lines 55 to 57: `_UNITTEST_ASSERT_METHODS`.
  - Lines 109 to 160: `_unittest_receivers`. This method maps TestCase methods to their receiver name.
  - Lines 161 to 240: `_analyze_function`. Line 180 counts an `ast.Assert`. Line 195 counts a unittest receiver call. Line 197 counts a strong mock call.
  - Lines 241 to 251: zero-assertion rule. Line 245 sets `rule_id`. Line 249 sets the explanation.
- `.venv\Lib\site-packages\misthelper_devtools\test_quality_analyzer\baseline.py`:
  - Line 6: the key is `(category, rule_id, file_path, line_number, explanation)`.
  - Lines 55, 194, and 214: the line number is part of the stored and compared entry.
- `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`. Present. No claim depends on it, so no row checks it.
- `.venv\Lib\site-packages\misthelper_devtools-0.6.4.dist-info\direct_url.json` line 1. Records commit `2239e7bd`.

### Remote sources fetched through `gh`

- `https://api.github.com/repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The tree call. Read once in each scan run.
- `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/contents/pyproject.toml?ref=2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/contents/src/misthelper_devtools/test_quality_analyzer/detection/weak_assertion.py?ref=2239e7bd468fd27e40c43f2b87fcd35a2e49672b`.
- `https://api.github.com/repos/jmorrison-juniper/misthelper-devtools/compare/79a5e45970e876f1656d69520d9635cea1aa25ef...2239e7bd468fd27e40c43f2b87fcd35a2e49672b`. Five commits ahead, zero behind. The release-to-pin diff changes no `weak_assertion.py` file.
- `https://api.github.com/repos/jmorrison-juniper/MistHelper/compare/0788b975e...main`. Three commits ahead. None of the six watched paths changed.
- `https://api.github.com/repos/jmorrison-juniper/MistHelper/actions/runs/45774119357/jobs`. Job `Test quality ratchet (gate)` at success.
- Issue `#2711`, pull requests, and comments 0 to 167, read through `gh issue view` and `gh pr list` / `gh pr view`. The 43 linked pull requests are merged. None is open.
- Open quality-gate issues: 18, numbered 4891 to 4908. Issue 4902 reports the `test_quality_gate` failure on pull request 4888. That pull request is open.

No `web_fetch` call ran. No skill loaded. No Podman, container, or Juniper device question applies.

## Unverified

- U-1: The 18-finding result in comment 167 is not reproduced. Running the analyzer is forbidden for this authoring task. The source reading and the passing run 45774119357 support the explanation in `analysis.md` A-4. T001 and T002 confirm it.
- U-2: The count of 244 findings under the pin is a prediction from source classification. T002 confirms it.
- U-3: The bodies of the 20 helper-assertion entries are not read. T003 reads them.
- U-4: The cause of the `test_quality_gate` failure on pull request 4888 is not inspected.
- U-5: The closing text in pull requests 4506 and 4527 is not found. A pattern search of the bodies found none. The closure comments 30 and 57 are the only evidence.
- U-6: The reason that pull request 4821 merged on 2026-11-19 is not in the issue. Comment 166 said the pull request was a draft.
- U-7: The 0.6.3 counts (875, 486, and 459) come from comments. They are not re-run.
- U-8: The detector behavior for Playwright `expect` and for helper calls is inferred from the absence of those names in the pinned source. It is not executed.
