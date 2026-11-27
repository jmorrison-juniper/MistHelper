# Tasks: Organization Invites Export Handles a Missing mistapi Function

**Input**: Record `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/`. Plan: `plan.md`. Requirements: `spec.md`. Research: `design/research.md`.

**Format**: `- [ ] ID [P?] [Story] Description. Files. Requirements. Acceptance. Verify. Status.`

**Status values**:

- `verified-present`: GitHub main already meets the task. The box is checked.
- `partial`: GitHub main meets part of the task.
- `absent`: GitHub main lacks the required element.
- `open`: A defect remains on GitHub main, or a process step has not run.

Each file path names the path on GitHub main at commit `f03c6c9`. Line numbers come from that commit.

## Phase 1: Shipped on GitHub main (pull request #4829)

- [X] T001 [US1] Guard the SDK lookup in `_invites`. Return when the function is missing. Files: `src/operations/exporting/export/org_export_utils.py` lines 726 to 732. Requirements: FR-001, FR-002, FR-003, FR-004, FR-005. Acceptance: `getattr` returns `None` for a missing name. One ERROR record names `listOrgInvites` and `OrgInvites.csv`. Verify: `python -m pytest tests/unit/export/test_org_export_utils.py`. Status: verified-present.
- [X] T002 [US2] Keep the shared export call with the same arguments. Files: `src/operations/exporting/export/org_export_utils.py` lines 733 to 735. Requirements: FR-001, FR-006. Acceptance: `api_call`, `data_type="invites"`, and `sort_key="email"` are passed. Verify: `python -m pytest tests/unit/export/test_org_export_utils.py`. Status: verified-present.
- [X] T003 [US1] Keep the absent-path test. Files: `tests/unit/export/test_org_export_utils.py` lines 976 to 986, method `test_invites_without_sdk_list_call_logs_error_and_skips`. Requirements: FR-002, FR-003. Acceptance: the test deletes the attribute and checks the ERROR text. Verify: `python -m pytest tests/unit/export/test_org_export_utils.py`. Status: verified-present.
- [X] T004 [US2] Keep the supported-path test. Files: `tests/unit/export/test_org_export_utils.py` lines 963 to 974, method `test_invites`. Requirements: FR-001, FR-006. Acceptance: the test checks the callable, `data_type`, and `sort_key`. Verify: `python -m pytest tests/unit/export/test_org_export_utils.py`. Status: verified-present.
- [X] T005 [US3] Keep the MistHelper Notes line that cites issue #4825. Files: `documentation/api/orgs/DELETE_orgs_org_id_invites_invite_id.md` line 73. Requirements: FR-010. Acceptance: the note states that MistHelper does not call the endpoint. Verify: `python -m pytest tests/guardrails/test_markdown_links.py`. Status: verified-present.
- [X] T006 [P] [US1] Keep the release-note fragment. Files: `changelog.d/issue-4825-org-invites.md` lines 1 to 3. Requirements: constitution release-note rule. Acceptance: one `###` heading and one `Fixed` bullet that names issue #4825. Verify: `python -m pytest tests/guardrails/test_markdown_links.py`. Status: verified-present.

## Phase 2: Tests

- [ ] T007 [US1] Make the absent-path test strict. Assert exactly one ERROR record. Assert that `OrgExportUtils.export_data` is not called. Files: `tests/unit/export/test_org_export_utils.py` lines 976 to 986. Requirements: FR-002, FR-004, FR-011. Acceptance: the test fails when `_invites` lines 726 to 732 are removed. Verify: `python -m pytest tests/unit/export/test_org_export_utils.py`. Status: partial (line 986 uses the `any` check, and no test checks the shared export).
- [ ] T008 [US4] Add a log-order test to class `TestSimpleDelegates`. Assert one INFO record before the shared export call and one DEBUG record after it. Files: `tests/unit/export/test_org_export_utils.py`. Requirements: FR-007. Acceptance: the test fails when the lines added by T011 are removed. Verify: `python -m pytest tests/unit/export/test_org_export_utils.py`. Status: absent.

## Phase 3: Implementation

- [ ] T009 [US4] Add the return type `-> None` to `_invites`. Files: `src/operations/exporting/export/org_export_utils.py` line 718. Requirements: FR-009. Acceptance: the `def` line declares `-> None`, and the behavior is unchanged. Verify: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`. Status: absent.
- [ ] T010 [US4] Add an inline comment that gives a reason to each adjacent uncommented line in `_invites`. Lines 727, 728, 729, 730, and 734 have none on GitHub main. Files: `src/operations/exporting/export/org_export_utils.py` lines 727 to 734. Requirements: FR-008. Acceptance: each commented line states why the line exists. Verify: `python -m ruff check .`. Status: partial (lines 726 and 732 have comments, and line 733 has only a suppression comment).
- [ ] T011 [US4] Add an INFO record before and a DEBUG record after the shared export call in `_invites`. Files: `src/operations/exporting/export/org_export_utils.py` lines 733 to 735. Requirements: FR-007. Acceptance: the INFO text names the organization invites export. The DEBUG text reports that the call returned. Both use `%s` values and no secret. Verify: `python -m pytest tests/unit/export/test_org_export_utils.py`. Status: absent.

## Phase 4: Documentation

- [ ] T012 [P] [US3] Remove the Related Endpoints entry on line 68. The entry is `- [GET_orgs_org_id_invites.md](POST_orgs_org_id_invites.md) — List invitations`. Files: `documentation/api/orgs/DELETE_orgs_org_id_invites_invite_id.md`. Requirements: FR-010. Acceptance: no line names `GET_orgs_org_id_invites.md`. Verify: `python -m pytest tests/guardrails/test_markdown_links.py`. Status: open.
- [ ] T013 [P] [US3] Remove the Related Endpoints entry on line 296. The entry is `- [GET_orgs_org_id_invites.md](POST_orgs_org_id_invites.md) — List invites`. Files: `documentation/api/orgs/POST_orgs_org_id_invites.md`. Requirements: FR-010. Acceptance: no line names `GET_orgs_org_id_invites.md`. Verify: `python -m pytest tests/guardrails/test_markdown_links.py`. Status: open.
- [ ] T014 [P] [US3] Remove the Related Endpoints entry on line 295. The entry is `- [GET_orgs_org_id_invites.md](POST_orgs_org_id_invites.md) — List invitations`. Files: `documentation/api/orgs/PUT_orgs_org_id_invites_invite_id.md`. Requirements: FR-010. Acceptance: no line names `GET_orgs_org_id_invites.md`. Verify: `python -m pytest tests/guardrails/test_markdown_links.py`. Status: open.

## Phase 5: Record and claim

- [ ] T015 [US1] Add the `in-progress` label to issue #4825 before the follow-up branch exists. Files: none. Requirements: constitution claim rule. Acceptance: the label appears on the issue, and the scope label stays `MistHelper.py`. Verify: `gh issue view 4825 -R jmorrison-juniper/MistHelper --json labels`. Status: open.
- [ ] T016 [US1] Replace the three legacy files with this record. Add `analysis.md` and the `design/` files. Files: `specs/numbered/0/0/1/2/3/3/0/0/4825-org-invites/`. Requirements: all. Acceptance: the folder holds this layout. It holds one `spec.md`, and that file is at the root. Verify: `python -m pytest tests/guardrails/test_process_folder_structure.py`. Status: open.

## Phase 6: Gates and publication

- [ ] T-LOCAL-GATES Run each local gate that applies to the changed files. Files: the files that T007 to T014 and T016 change. Requirements: all. Acceptance: each gate in the table prints its expected result. Verify: the commands in the table. Status: open.

| Gate | Command | Expected result |
| - | - | - |
| Compile | `python -m py_compile MistHelper.py` and `python -m py_compile src/operations/exporting/export/org_export_utils.py` | No output |
| Lint | `python -m ruff check .` | `All checks passed` |
| Format | `python -m black --check .` | No file needs a change |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` |
| Tests | `python -m pytest tests/unit/export/test_org_export_utils.py` | All tests pass |
| Guard tests | `python -m pytest tests/guardrails/test_markdown_links.py tests/guardrails/test_process_folder_structure.py` | All tests pass |
| Coverage | `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=` | Coverage 80 percent or above |
| Test quality | `test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt` | `gate: 0 new findings vs baseline` |
| Complexity | `radon cc src/operations/exporting/export/org_export_utils.py -j`, piped to `complexity-gate --max 10` | No block above complexity 10 |
| Security lint | `bandit -c pyproject.toml -r src -q` | No finding |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation, and coverage 90 percent or above |
| Symbols | `symbol-diff --base origin/main src/operations/exporting/export/org_export_utils.py` | `no module-level name changed`, exit code 0 |
| STE | `ste-linter --config .ste-linter.toml --min-score 80` with each changed Markdown file | Each file scores 80 or above |

Not applicable: the safe sweep, because no menu and no `MistHelper.py` line changes. Not applicable: the menu reference, because no menu changes. Not applicable: the dependency audit, because no requirements file changes. Not applicable: the ops portal and the ops platform, because those trees do not change. Not applicable: the container, because no container runs.

- [ ] T-PR Commit, push, and open the pull request. Files: the changed files in the file change map of `plan.md`. Requirements: process. Acceptance: the title is `fix(export): log org invites skip and correct invite API notes`. The branch is `fix/4825-org-invites-followup`. The body holds `Closes #4825`, the gate results, and the reason that no changelog fragment is needed. Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json title,body`. Status: open.
- [ ] T-REMOTE-CI Watch the CI run. Files: none. Requirements: constitution step 8. Acceptance: each required check reports SUCCESS on the latest commit. Verify: `gh pr checks <number> -R jmorrison-juniper/MistHelper --watch`. Status: open.
- [ ] T-MERGE Enable auto-merge only after T-REMOTE-CI passes and the orchestrator authorizes the merge. Files: none. Requirements: constitution steps 9 to 12. Acceptance: the squash commit is on main. The `container-build.yml` run on that commit finishes. Its image revision label equals the commit SHA. Verify: `gh pr view <number> -R jmorrison-juniper/MistHelper --json mergedAt,mergeCommit`. Status: open.
