# Implementation Plan: Main workflow recovery

**Branch**: `docs/4763-post-merge-consumer` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs/numbered/0/0/1/2/3/0/2/3/`. The route is `0/0/1/2/3/0/2/3`, computed for issue 4763.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The recovery code for issue #4763 is on `main` (RC-01, RC-02, RC-47). This record verifies that state. It defines the open acceptance work and gates the issue closure. This change adds no runtime file.

## Technical Context

- **Language/Version**: Python 3.15 for the three guard test files. No Python file changes.
- **Primary Dependencies**: GitHub Actions. The shared workflows of `jmorrison-juniper/misthelper-devtools` at `d63a120487cecf750184cb178387cdc25c0a7635`. GitHub CLI for read-only evidence.
- **Storage**: Not applicable. No data store changes.
- **Testing**: The pytest guard files named in task T-LOCAL-GATES. The orchestrator runs them. The authoring agent ran no test.
- **Target Platform**: GitHub-hosted `ubuntu-latest` runners. Windows 11 for local gates.
- **Project Type**: CI configuration and a specification record.
- **Performance Goals**: An immediate merge gets recovery within about 100 seconds. A delayed merge that starts no closed run gets recovery within six hours.
- **Constraints**: No test-only merge. No manual start of a main workflow as evidence. A workflow file needs a manual merge.
- **Scale/Scope**: Four main workflows, one consumer workflow, one shared workflow pin, three guard test files, and one record folder.

## Constitution Check

Gate: checked before research and after design. Result: every rule passes. A recorded debt does not fail a rule. Each row gives the reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass, with recorded debt | The route holds one record folder before and after this change. The record folder holds five children. The guard module holds 18 top-level names (RC-12). This change adds no name to it. |
| II. Class-Based Architecture | Pass | This change adds no code. |
| III. Safety-First | Pass | This change adds no input handling. The dispatch job reads no operator input. |
| IV. Full Deployment Pipeline | Pass | The change is a Markdown record. The pipeline runs through T-PR, T-REMOTE-CI, and T-MERGE. |
| V. Observability and Logging | Pass | This change adds no log statement. The consumer log lines stay unchanged. |
| VI. Inline Comments | Pass | This change adds no code. |
| VII. Action Logging | Pass | This change adds no code. |
| Technology: mistapi | Not applicable | The feature calls no Mist REST endpoint. |
| Technology: Podman | Not applicable | No container runs in this change. |
| Technology: file paths | Not applicable | No path code changes. |
| Technology: output data directory | Not applicable | No product output changes. |
| Technology: container security | Not applicable | No container changes. |
| Technology: Zscaler | Not applicable | No local registry push. |
| Documentation | Pass | No behavior changes. The quality-gates document already names the dispatch check (RC-87). |
| Release notes | Pass | No user-visible change. The consumer fragment exists (RC-14). |
| SpecKit escalation | Pass | The change affects CI behavior and several records, so a record is required. |
| Multi-agent git | Pass | The branch starts from `main`. No open pull request touches the record route. Pull request #4886 touches `auto-merge.yml` only, and this change does not (RC-95). |
| Security findings | Pass | This change adds no finding and no suppression. |
| Governance | Pass | No constitution amendment. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      main-workflow-recovery.md
      evidence-record.md
    checklists/
      requirements.md
      acceptance.md
```

### Files read by the verification

```text
.github/workflows/auto-merge.yml
.github/workflows/ci.yml
.github/workflows/codeql.yml
.github/workflows/container-build.yml
.github/workflows/ste-lint.yml
.github/workflows/wiki-publish.yml
.github/workflows/close-linked-issues.yml
tests/guardrails/test_auto_merge_issue_close.py
tests/guardrails/test_spec_route_contract.py
tests/guardrails/test_process_folder_structure.py
changelog.d/issue-4763-post-merge-consumer.md
jmorrison-juniper/misthelper-devtools: .github/workflows/reusable-auto-merge.yml at d63a120
```

**Structure Decision**: Keep the managed numeric route. Change no runtime file in this change. Replace the legacy record files at the same route.

## File Change Map

| Exact path | Action | Reason |
| - | - | - |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/spec.md` | Modify | Replaces the legacy specification. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/plan.md` | Modify | Replaces the legacy plan. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/tasks.md` | Modify | Replaces the legacy tasks. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/analysis.md` | Modify | Replaces the legacy analysis. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/design/research.md` | Add | Decisions, evidence, and remote checks. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/design/data-model.md` | Add | Entities and state transitions. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/design/quickstart.md` | Add | Reproduction steps and evidence queries. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/design/contracts/main-workflow-recovery.md` | Add | Interface of the shared recovery workflow. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/design/contracts/evidence-record.md` | Add | Evidence row format. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/design/checklists/requirements.md` | Modify | Replaces the legacy checklist. |
| `specs/numbered/0/0/1/2/3/0/2/3/4763-post-merge-consumer/design/checklists/acceptance.md` | Add | Closure gate. |
| `.github/workflows/auto-merge.yml` | No change | Pin and list already verified (RC-01, RC-02). |
| `tests/guardrails/test_auto_merge_issue_close.py` | No change | Guard matches the consumer (RC-08 to RC-10). |
| `changelog.d/issue-4763-post-merge-consumer.md` | No change | Fragment exists (RC-14). |

## Dependencies

- GitHub CLI, for read-only evidence.
- The shared workflow pin `d63a120487cecf750184cb178387cdc25c0a7635` in `misthelper-devtools`. No new package.
- PowerShell (`pwsh`) for the route tests. `tests/guardrails/test_spec_route_contract.py` needs it (RC-79).

## Risks and Mitigations

| Risk | Mitigation |
| - | - |
| R-1: No organic pending request occurs, so delayed acceptance stays open. | Keep the issue open (D-6). Watch each labeled run. Do not force a pending request (AGENTS.md, RC-72). |
| R-2: A delayed merge starts no closed run. Recovery waits for the schedule. | Record the delay in SC-003. Keep the six-hour schedule (RC-05). |
| R-3: Pull request #4886 merges and moves the pin. The guard test fails. | Do not merge #4886 as is (D-8). A future bump changes the pin and the guard constant in one manual pull request. |
| R-4: The wiki lags after a token merge that changes `documentation/wiki/`. | Accept the lag (D-4). The daily schedule and a maintainer start cover it. |
| R-5: The record pull request closes the issue early. | Use `Refs #4763` (D-7). |
| R-6: A workflow-file change cannot merge by token. | Use one manual protected squash merge (D-10). |
| R-7: Duplicate runs start on one tip. | Keep the coverage check and the concurrency group (RC-32, RC-33). |
| R-8: Legacy files remain beside the new record. | Replace each legacy file at its path in T-PR (D-9). |

## Rollback

1. Revert the record squash commit with a new pull request. The record is documentation only.
2. If the consumer pin must return, restore pin `0fdcf610c87a281bd4e952486d6154b2bf45fec4` and the list `ci.yml codeql.yml container-build.yml`. Change the guard constant in the same pull request. Merge it by hand (RC-47 records the earlier values).

Caution: Reverting the consumer pin without the guard constant fails the guard test. Change both in one pull request.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| The guard module holds 18 top-level names (RC-12). | The module is an existing guard file. This fix does not change it. | Splitting the module changes a guard file that this record does not need to change. Remediation RM-1 tracks the split as a separate change. |

## Remediation (separate change)

- **RM-1**: Split `tests/guardrails/test_auto_merge_issue_close.py` into one module for each test class. This change does not start RM-1.

## Validation

The orchestrator runs the commands in `design/quickstart.md`, section 5. The authoring agent ran no build, test, linter, or script.
