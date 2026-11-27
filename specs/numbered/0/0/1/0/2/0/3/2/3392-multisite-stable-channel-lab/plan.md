# Implementation Plan: Multi-site stable word and router channel lab verification

**Branch**: `3392-multisite-stable-channel-lab` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this record

**Input**: Numeric specification from `/specs/numbered/0/0/1/0/2/0/3/2/3392-multisite-stable-channel-lab/spec.md`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The owner posts four lab answers. The answers select one branch for the access point stable word and one branch for each router channel value. Until the answers exist, the code keeps every refusal and every channel value. This plan fixes the branch rules, the evidence format, the file change map, and the verification commands. The agent writes no repository change in this record.

## Technical Context

- **Language and version**: Python 3.15 or newer (RC-03).
- **Primary dependencies**: mistapi 0.64.1 as the only Mist REST interface (RC-25, RC-120). No new dependency.
- **Storage**: no new storage. The lab answers live in issue #3392 comments, not in the `data/` directory.
- **Testing**: pytest contract, unit, and browser suites under `tests/contract/upgrade_portal`, `tests/unit/upgrade_portal`, `tests/unit/prod_readiness`, and `tests/e2e/upgrade_portal` (RC-84 to RC-97). Guardrail suites under `tests/guardrails` (RC-104 to RC-107).
- **Project type**: a Python package with a web upgrade portal under `src/interfaces/portals/upgrade_portal`.
- **Performance goals**: no change. The change does not add a request to the cloud.
- **Constraints**: a firmware write needs an explicit typed confirmation (RC-11, RC-52). Organization writes stay closed unless the write gate is open (RC-54, RC-55).
- **Scale and scope**: two classes and about ten repository files in each gated branch (see the file change map).

## Constitution Check

The check covers the constitution at `.specify/memory/constitution.md` (RC-10, RC-11, RC-12). Each rule shows a result and a reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass | The numbered route applies (RC-13 to RC-15, RC-112). Each digit level holds five children or fewer. The legacy record 3383 is existing debt (RC-26). |
| II. Class-based architecture | Pass | The gated changes remove a method and a guard. They add no wrapper function. The access point rule stays in the class OrgAdvancedRules (RC-41). |
| III. Safety first | Pass | Each lab write needs the owner, a target, and the phrase CONFIRM (D-2, D-3, D-18). The organization write gate stays closed by default (RC-54, RC-55). |
| IV. Full deployment pipeline | Pass (planned) | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in this order. The merge needs the orchestrator authorization. |
| V. Observability and logging | Pass (planned) | Changed code keeps its existing log lines. New log lines use ASCII text and `%s` formatting. The lab answer holds no secret. |
| VI. Inline comments | Pass (planned) | Each changed line in a gated branch carries an inline comment that gives its purpose. |
| VII. Action logging | Pass (planned) | A removed refusal also removes its own log lines. Each remaining action keeps its before and after log lines. |
| Technology: mistapi sole interface | Pass | All cloud calls use mistapi functions (RC-113 to RC-119). The constitution says 0.59 or newer, which is stale (RC-12). Item A-5 tracks it. |
| Technology: package manager | Pass | No dependency change. `requirements.txt` stays the pin (RC-25). |
| Technology: Podman runtime | Not applicable | This issue starts no container. A test container, if you need one, follows `documentation/container-deployment.md`. |
| Technology: file paths | Pass | The change adds no path code. |
| Technology: data directory | Pass | The change writes no product output. The lab answers stay out of `data/`. |
| Technology: output backends and operational store | Not applicable | The change adds no export and no coordination record. |
| Development workflow: new menu operations | Not applicable | The change adds no menu operation. |
| Documentation | Pass (planned) | The change adds one changelog fragment for each user-visible change (RC-09, RC-106, RC-110). README changes are not needed because no operation changes. |
| Audience standard | Pass (planned) | The warnings for operators stay in plain words. The change adds no jargon to the page. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/0/2/0/3/2/3392-multisite-stable-channel-lab/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      org-access-point-stable-request.md
      ssr-channel-request.md
      lab-answer-record.md
    checklists/
      requirements.md
      lab-evidence.md
      branch-rules.md
```

Each folder holds five children or fewer. The feature root holds four files and the `design` folder. The `design` folder holds five children.

### Source code (repository root)

The source tree changes only in the files of the change map below. No new source directory is added.

## Implementation Outline

The request path for the access point stable word:

```text
Multi-site save (org_upgrade.py:1287)
  -> OrgAdvancedRules.refuse_stable_access_points (org_advanced_options.py:143, :162)
Plan build (aggregate_upgrade_service.py:672)
  -> _ap_child (:674) -> _ap_body (:685) -> guard (:699, :700)
  -> OrgUpgradeBody.build (org_upgrade_body.py:182, :192)
Cloud call (mistapi upgradeOrgDevices, devices.py:840)
```

The request path for the router channel:

```text
Multi-site page control (org_options.html:535, :541)
Single-site page control (options.html:797)
CLI prompt (firmware_manager.py:2315)
Channel reader (options.py:1324) -> channel choices (upgrade_service.py:78)
Router body (upgrade_service.py:766) -> cloud call (mistapi upgradeOrgSsrs, orgs/ssr.py:114)
```

## Branch Rules

The lab answers select the branch. The agent runs one branch for each answer. The two access point branches are exclusive. Each channel value has its own branch.

| Lab check | Accepted branch | Refused branch |
| - | - | - |
| L-AP-STABLE | Remove both refusals. Offer the stable build on the multi-site page for access points. Update the tests and the parity row (T011, T016, T017). | Keep both refusals. Record the refused answer (T012). |
| L-SSR-STABLE | Keep the value (no change). | Remove the value from the channel choices and the controls (T013). |
| L-SSR-BETA | Keep the value (no change). | Remove the value from the channel choices and the controls (T014). |
| L-SSR-ALPHA | Keep the value (no change). | Remove the value from the channel choices and the controls (T015). |

A value that one lab router accepts and another refuses (EC-3) is treated as refused.

## File-by-File Change Map

| Path | Action | Condition | Requirement | Task |
| - | - | - | - | - |
| specs/numbered/0/0/1/0/2/0/3/2/3392-multisite-stable-channel-lab/ | Add | Always | FR-010, FR-011 | T001, T019 |
| changelog.d/issue-3392-multisite-stable-channel-lab.md | Add | A user-visible change is made | FR-012 | T018 |
| src/operations/execution/firmware/aggregate_upgrade_service.py | Modify: delete the guard at lines 699 and 700 | L-AP-STABLE accepted | FR-001, FR-005 | T011 |
| src/interfaces/portals/upgrade_portal/upgrade/org_advanced_options.py | Modify: delete the method refuse_stable_access_points at lines 143 to 163 | L-AP-STABLE accepted | FR-001, FR-005 | T011 |
| src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | Modify: delete the call at line 1287 | L-AP-STABLE accepted | FR-001, FR-005 | T011 |
| src/interfaces/portals/upgrade_portal/upgrade/options.py | Modify: the stable help text at lines 317 to 322 | L-AP-STABLE accepted | FR-005 | T011 |
| src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | Modify: add the access point type to the attribute at line 299 | L-AP-STABLE accepted | FR-005 | T011 |
| src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | Modify: remove a refused value from the list at lines 541 to 545, and update the warning at lines 547 to 551 | A channel value refused | FR-007 | T013, T014, T015 |
| src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/options.html | Modify: remove a refused value from the list at lines 797 to 801, and update the warning at line 807 | A channel value refused | FR-007 | T013, T014, T015 |
| src/operations/execution/firmware/upgrade_service.py | Modify: remove a refused value from SSR_CHANNEL_CHOICES at line 78 | A channel value refused | FR-007 | T013, T014, T015 |
| src/operations/execution/firmware/firmware_manager.py | Modify: remove a refused value from the CLI prompt at lines 2314 to 2326 | A channel value refused | FR-007 | T013, T014, T015 |
| tests/e2e/upgrade_portal/journeys/parity_matrix.json | Modify: rows C17 (lines 736 to 775) and C21 (lines 904 to 941) | Always | FR-009 | T017 |
| tests/contract/upgrade_portal/test_org_advanced_options.py | Modify: the refused case at line 133 and the refused list at lines 118 to 136. Add one test beside line 381 | L-AP-STABLE accepted | FR-001, FR-005 | T016 |
| tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_advanced_bodies.py | Modify: line 96 and the test at lines 158 to 161 | L-AP-STABLE accepted | FR-001, FR-005 | T016 |
| tests/e2e/upgrade_portal/test_org_advanced_options.py | Modify: the test at lines 231 to 241 | L-AP-STABLE accepted | FR-005 | T016 |
| tests/unit/upgrade_portal/test_upgrade_ssr_options.py | Modify: lines 158, 165, 195, and 349 to 350 | A channel value refused | FR-007 | T016 |
| tests/contract/upgrade_portal/test_upgrade_options.py | Modify: the loop at line 1358 | A channel value refused | FR-007 | T016 |
| design/research.md, analysis.md, tasks.md in this record | Modify with the posted answers | After each lab answer | FR-004, FR-006, FR-010 | T019 |

The change map names the exact lines of main (RC-27 to RC-57, RC-84 to RC-103). The lines move when a branch changes a file. Each task re-reads the line before it edits the file.

## Dependencies

- No package change. `requirements.txt` keeps `mistapi==0.64.1` (RC-25).
- The owner needs lab access and a credential outside the repository (D-18).
- The changelog fragment name depends on the pull request number. Before the pull request exists, use `issue-3392-multisite-stable-channel-lab.md`. After it exists, use `pr-` followed by the pull request number (RC-09, RC-110).

## Complexity Tracking

Each row names existing debt. The debt stays outside this issue unless a task names it.

| Debt | Evidence | Why it stays | Separate remediation |
| - | - | - | - |
| Legacy record 3383 sits at the specs root | RC-26 grandfathers the folder | This record uses the managed route, so it adds no direct child | Analysis item A-12 (owner decision on migration) |
| Issue #3392 cites paths that are absent on main | RC-58 | The owner edits the issue. The agent cannot write to GitHub | Analysis item A-1 |
| Parity rows C17 and C21 hold stale verdicts | RC-99, RC-101 | The fixture change is small and needs its own test run | T017 |
| Constitution text names an old mistapi version | RC-12 | The constitution changes only through its amendment procedure | Analysis item A-5 |

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| The owner gets an unclear error (EC-1) | The verdict is unknown, and the access point gap stays | The contract repeats the check once with the named field (D-13) |
| A lab run targets a production organization (EC-6) | Warning: a production device can change, and the service can stop | Decision D-18 limits targets to lab devices. The owner types CONFIRM |
| A lab router reboots (EC-5) | Caution: the lab site network can drop for a short time | Use lab devices only. The owner plans the run in a lab window |
| The cloud accepts the stable word but resolves to another build | The page could offer a build that differs from single-site | The job read must show the resolved build, which the answer records (contract) |
| The deprecated strategy field hides the answer | The answer could come from the field, not the word | Minimal bodies omit the deprecated field (D-13, RC-70) |
| The SDK call bypasses the portal gate (D-14) | Warning: a wrong target can change a device without the portal checks | D-18 and the contract limit targets. The owner runs only the listed calls |
| An operator sees a refused channel value | Caution: a failing router upgrade gives the operator no clear cause | Each refused value leaves the three controls in one branch (T013 to T015) |
| The parity test changes after the fixture change | A test fails for a reason outside the branch | T017 runs the parity page test first. Each change keeps the old row until the test passes |
| A posted comment exposes a secret (EC-7) | Warning: a secret in the issue history stays visible | Fixed fields (D-11) and the evidence checklist. The owner rotates a leaked token |

## Rollback Steps

1. For a merged code branch, open a new pull request that reverts the merge commit. Do not force-push to `main`.
2. For a parity change, revert the JSON edit in the same way.
3. For a lab job still in progress, cancel the job with the cancel operation of the same route before the device starts (RC-62, RC-66). Caution: a job that already changed a device stays changed. A cancel cannot undo that change.
4. For this record, delete the record folder in a new change. The record holds no code, so no runtime state needs a rollback.
