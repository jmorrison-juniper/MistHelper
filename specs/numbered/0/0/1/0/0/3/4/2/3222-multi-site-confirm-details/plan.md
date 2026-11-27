# Implementation Plan: Multi-Site Confirm Page Plan Detail

**Branch**: `fix/3222-multi-site-confirm-details` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric record `specs\numbered\0\0\1\0\0\3\4\2\3222-multi-site-confirm-details\spec.md`. The route digits are the eight-digit base-5 form of 3222 (research R-13).

## Summary

Add one pure view class that reads the stored plan record. The confirm page renders its rows and its missing-detail list. The submit route refuses a plan that lacks a detail. The change makes no cloud call and adds no file or directory to the source tree.

## Technical Context

- **Language/Version**: Python 3.15 or newer. The repository instructions require it (`.github/copilot-instructions.md`, "Language and environment").
- **Primary Dependencies**: Flask 3.1.3 with Jinja2 (`.venv\Lib\site-packages\flask-3.1.3.dist-info`). mistapi 0.64.1 meets the pin `mistapi>=0.64.0,<0.65` (`.venv\Lib\site-packages\mistapi-0.64.1.dist-info`). Playwright runs the browser tests.
- **Storage**: The existing durable aggregate record. The change adds no field and no key.
- **Testing**: pytest unit and contract tests, and Playwright browser tests under `tests/`.
- **Target Platform**: Windows 11, macOS, and Linux. The Podman container image does not change.
- **Project Type**: Flask web portal. The upgrade portal serves port 8056 through `wsgi_capture.py`.
- **Performance Goals**: The confirm GET keeps its existing site reads, three in total (research R-55). Rendering adds no cloud call. The issue sets no latency target.
- **Constraints**: The five-item rule. Typed `CONFIRM` stays required. Writing follows Simplified Technical English. Each executable line carries an inline comment. Each action carries a log line.
- **Scale/Scope**: One plan holds the planned devices of its selected sites. The page shows each planned device as one row.

## Constitution Check

| Rule | Result | Reason |
| - | - | - |
| Five-item rule, children of a directory (Principle I) | Pass | The change adds no file and no directory. The new class goes into an existing module, `org_child_controls.py`. |
| Five-item rule, top-level names of a module (Principle I) | Pass with recorded debt | `org_child_controls.py` already defines six top-level names (research R-68). The change adds one class. Remediation action RA-1 tracks the split. |
| Five-item rule, members of a class (Principle I) | Pass | `OrgConfirmPlanView` has five members. They are `build` and four private helpers. |
| Function limits (Principle I) | Pass | Each method takes at most four parameters. Each method fits in 25 lines and holds at most five logical blocks. |
| Existing structure debt (Principle I) | Pass with recorded debt | `upgrade/` and the three portal test folders hold more than five children (research R-69, R-70, R-71). The change adds none. RA-2 tracks the reduction. |
| Managed specs route (Principle I) | Pass | The record uses `specs/numbered/` and the eight-digit base-5 route. Each folder of the record holds five children or fewer. |
| Class-based architecture (Principle II) | Pass | The view logic lives in one class. No wrapper function is added. |
| Safety-first (Principle III) | Pass | The typed `CONFIRM` check stays. The server refuses an incomplete plan before any write. |
| Secrets (Principle III) | Pass | The change reads no credential, prints no credential, and stores no credential. |
| Full deployment pipeline (Principle IV) | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE follow the pipeline. No task pushes to `main`. |
| Observability (Principle V) | Pass | The new log lines use ASCII only. They log counts and never a MAC address. |
| Mist cloud transport | Pass | The change adds no mistapi call and no direct REST request (research R-56 to R-58). |
| Test rules (AGENTS) | Pass | Each new test fails before the implementation (tasks T002 to T005). The tests use stand-in services and no production credential. |
| STE writing (AGENTS) | Pass by manual review | The prose follows the STE rules of this record. The ste-linter score is not measured in this session (research U-3). |
| Changelog fragment (`changelog.d/README.md`) | Pass | The issue exists and no pull request exists when the commit is made. The fragment name is `issue-3222-multi-site-confirm-details.md`. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/0/0/3/4/2/3222-multi-site-confirm-details/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      confirm-page.md
      confirm-plan-view.md
      submit-refusal.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
src/interfaces/portals/upgrade_portal/upgrade/org_child_controls.py                    modify: add OrgConfirmPlanView
src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py                        modify: pass confirm_plan, refuse an incomplete plan
src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html   modify: render the new sections
tests/unit/upgrade_portal/test_org_child_controls.py                                   modify: builder tests U1 to U8
tests/contract/upgrade_portal/test_org_upgrade_routes.py                               modify: route tests C1 to C6
tests/contract/upgrade_portal/test_issue_3390_confirm_strategy_wording.py              modify: render helper passes confirm_plan
tests/e2e/upgrade_portal/test_org_upgrade_flow.py                                      modify: browser rows E1
tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py                       modify: journey J1 without the expected failure
tests/e2e/upgrade_portal/journeys/parity_matrix.json                                   modify only after J1 passes
specs/3200-upgrade-portal-journeys/parity-matrix.md                                    modify only after J1 passes
documentation/upgrade_capture_portal.md                                                modify: describe the confirm sections
changelog.d/issue-3222-multi-site-confirm-details.md                                   add: release note
```

**Structure Decision**: Add no file to the source tree and no directory. Put the view class in an existing module. Put every test in an existing module. The only new repository file is the release note, which the changelog rule allows.

## Architecture

```text
GET /upgrade/org/confirm
  -> confirm_page()                          org_upgrade.py, confirm route
       -> selected_rows()                    unchanged: three cloud reads through build_site_rows
       -> _owned_operation()                 unchanged: the stored plan record
       -> OrgConfirmPlanView.build(plan)     new: a pure function of the stored plan
       -> render_page(confirm_plan=view)      org_confirm.html renders the new sections

POST /api/org-upgrades
  -> submit_upgrade()                        org_upgrade.py, submit route
       -> _owned_operation()                 unchanged
       -> OrgConfirmPlanView.build(plan)     new: refuse when complete is false
       -> pre-check gate, site locks, submit unchanged
```

## Design

### OrgConfirmPlanView (new class)

- Location: `src/interfaces/portals/upgrade_portal/upgrade/org_child_controls.py`, after `OrgScheduleView`.
- Members: `build` (public class method), `_site_rows`, `_route_rows`, `_device_rows`, and `_missing_details` (private static methods). The class has five members, which is the limit.
- Input: the stored plan record, or `None` for an AP-only request.
- Output: a dictionary with the keys `complete`, `missing`, `cloud_call_count`, `sites`, `routes`, `devices`, and `phases`. The data model defines each key.
- Labels and wording: none in Python. The template maps each family token to its label and renders each text. The existing `strategy_names` and `device_group_names` maps use the same pattern.
- Logging: one info line before `build` and one debug line after it. The debug line reports counts only.

### Route changes (org_upgrade.py)

- Add `OrgConfirmPlanView` to the import block from `org_child_controls` that starts at line 101.
- Add the constants `PLAN_INCOMPLETE_CODE = "org_upgrade_plan_incomplete"` and `PLAN_INCOMPLETE_MESSAGE`. Place them beside the other confirmation messages at lines 191 and 192.
- In `confirm_page()`, add `confirm_plan=OrgConfirmPlanView.build(operation)` after `prechecks=prechecks` at line 1375.
- In `submit_upgrade()`, add the completeness refusal after the owned plan read at line 2163. The refusal runs before the pre-check gate. It runs before any lock, record change, or submit call.

### Template changes (org_confirm.html)

- Replace the family expression at line 54 with a mapping from the `family` values of `confirm_plan.routes`. The labels are AP, switch, gateway, and session smart router.
- Insert the sections for selected sites, child routes, planned devices, and phases after the advanced summary block that ends at line 71. Insert them before the scope warning at line 106.
- Insert the cloud call count and the missing-detail list. Render the list only when `confirm_plan.complete` is false.
- Change the disabled condition at line 189 so that it also requires `confirm_plan.complete`.
- Keep the scope warning, the write-disabled caution, the pre-check table, and the start button unchanged.

### Parity matrix (conditional)

- Update row C25 in `tests/e2e/upgrade_portal/journeys/parity_matrix.json` and in `specs/3200-upgrade-portal-journeys/parity-matrix.md` only after the journey test J1 passes. The two files must match.

## File-by-File Change Map

| Path | Action | Requirements | Reason |
| - | - | - | - |
| `src/interfaces/portals/upgrade_portal/upgrade/org_child_controls.py` | Modify | FR-001 to FR-005, FR-007, FR-008, FR-012, FR-014 | Add the pure view class. |
| `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | Modify | FR-008, FR-009, FR-012, FR-013 | Pass the view and refuse an incomplete plan. |
| `src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html` | Modify | FR-001 to FR-008, FR-010, FR-011, FR-014 | Render the rows, the labels, and the missing list. |
| `tests/unit/upgrade_portal/test_org_child_controls.py` | Modify | FR-001 to FR-005, FR-007, FR-008, FR-012 | Builder tests U1 to U8. |
| `tests/contract/upgrade_portal/test_org_upgrade_routes.py` | Modify | FR-001 to FR-006, FR-008, FR-009, FR-011 to FR-014 | Route and refusal tests C1 to C6. |
| `tests/contract/upgrade_portal/test_issue_3390_confirm_strategy_wording.py` | Modify | FR-010 | Pass `confirm_plan` to the strict render helper. |
| `tests/e2e/upgrade_portal/test_org_upgrade_flow.py` | Modify | FR-003, FR-008, FR-014 | Browser row checks E1. |
| `tests/e2e/upgrade_portal/journeys/test_upj_multisite_journeys.py` | Modify | FR-001 to FR-004, SC-006 | Remove the expected failure and assert the rows J1. |
| `tests/e2e/upgrade_portal/journeys/parity_matrix.json` | Modify, conditional | FR-016 | Update C25 after J1 passes. |
| `specs/3200-upgrade-portal-journeys/parity-matrix.md` | Modify, conditional | FR-016 | Match the JSON row C25. |
| `documentation/upgrade_capture_portal.md` | Modify | FR-016 | Describe the new confirm sections. |
| `changelog.d/issue-3222-multi-site-confirm-details.md` | Add | FR-016 | Release note. |
| `specs/numbered/0/0/1/0/0/3/4/2/3222-multi-site-confirm-details/` | Add | FR-015 | This record, copied from the draft folder. |

No file in this list changes the mistapi pin, `requirements.txt`, `pyproject.toml`, or any firmware write module.

## Dependencies

No package is added or updated. The change needs no change to `requirements.txt`, `pyproject.toml`, or the mistapi pin. The `pip-audit` gate therefore does not apply.

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| The route file changes while another pull request is open. | Run the overlap check as part of T-PR. Keep the route change to three small edits. Rebase before the merge, as AGENTS requires. |
| A stored plan from before this change lacks a field and is refused. | The refusal applies only to plans that hold child routes. A plan with no child route keeps the AP-only path (FR-012). Test C5 covers it. |
| The page grows long. | Each table uses plain labels and stable identifiers. The page keeps the order of the existing summary. |
| The stable build shows a typed version that the cloud does not send. | FR-007 requires the stable text. Test U6 covers it. |
| A device name holds markup. | Jinja autoescape stays on. FR-011 requires escaping. Test C4 covers it. |
| The preserved branch or the local commits leak into the new branch. | Decision D-10 forbids reuse. Task T001 starts from `origin/main`. T-PR names the new branch only. |
| The journey fails for a reason other than the defect. | Task T004 selects the canary strategy and asserts one detail for each row. |
| The parity matrix drifts from its readable copy. | Task T012 changes both files in one commit and runs the parity contract test. |
| Caution: repeated pushes spend account minutes on remote CI. | Push one commit after the local gates pass. Do not push to read a log, as AGENTS requires. |
| The safety review is not complete when the merge is ready. | T-MERGE waits for the human review that the `needs-human-review` label names (decision D-11). |

## Rollback Steps

1. Revert the squash commit of the pull request on `main` through a new pull request. Do not force-push `main`.
2. Confirm that `org_confirm.html` and `org_upgrade.py` return to their previous content.
3. Keep the write gate closed until the revert merges and the confirm page shows the previous content.
   - Leave `ORG_UPGRADE_WRITES_ENABLED` unset during that time.
4. No data migration exists. The stored plan shape does not change, so no record needs repair.

## Complexity Tracking

| Existing condition | Decision | Remediation |
| - | - | - |
| `org_child_controls.py` defines six top-level names before the change. | Add one class. Add no constant. | RA-1 splits the module. |
| `upgrade/` holds more than five direct children. | Add no child. Put the view class in an existing module. | RA-2 reduces the direct children. |
| The three portal test folders hold more than five direct children. | Add no test module. Add tests to existing modules. | RA-2 covers the test folders. |
| `org_upgrade.py` defines far more than five top-level names, for example at lines 146 and 2714. | Add three small edits and one import. | RA-3 moves the confirm builders out of the route file. |

## Remediation Actions

- **RA-1**: Split `org_child_controls.py` so that each module defines five top-level names or fewer. Owner: the orchestrator files a follow-up issue. Trigger: the next change to this module.
- **RA-2**: Reduce the direct children of `upgrade/` and of the three portal test folders. Owner: the orchestrator files a follow-up issue.
- **RA-3**: Move the confirm builders out of `org_upgrade.py`. Owner: the orchestrator files a follow-up issue. Trigger: the next change to the route file.

## Local Gates for This Change

Run each gate from the local gates table that applies to the changed files:

- Compile: `python -m py_compile` on each changed Python module.
- Lint: `python -m ruff check .`
- Format: `python -m black --check .`
- Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`
- Tests: `python -m pytest` on each changed test file.
- Full tests: the two `pytest-chunks` commands in `.github/copilot-instructions.md`.
- Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`
- Test quality: the `test-quality-analyzer` procedure in `.github/copilot-instructions.md`.
- Complexity: `radon cc src/interfaces/portals/upgrade_portal -j` piped to `complexity-gate --max 10`.
- Security lint: `bandit -c pyproject.toml -r src/interfaces/portals/upgrade_portal -q`
- Code quality: `pylint src/ --fail-under=9.5`
- Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`
- Docstrings: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`
- Symbols: `symbol-diff --base origin/main` on `org_upgrade.py` and on `org_child_controls.py`.
- STE: `ste-linter --config .ste-linter.toml --min-score 80` on each changed Markdown file.

The gates for the menu reference, the safe sweep, the dependency audit, the ops portal, and the ops platform do not apply. The change touches no menu, no dependency, and no ops code.
