# Specification Analysis Report

**Date**: 2026-11-05
**Scope**: Fresh planning for #4588, with non-closing context #4231 and #4278.
**Inputs**: [spec](spec.md), [plan](plan.md), [tasks](tasks.md), and all nested design contracts.

The analysis inspected these artifacts without changing product behavior or the constitution.
This document preserves the requested report.
Planning is complete when the recorded artifact checks pass.
Implementation remains blocked by the applicable decisions and future task acceptance.

## Findings and unresolved implementation gates

| ID | Category | Severity | Location | Finding and required action |
| --- | --- | --- | --- | --- |
| D1 | Access/privacy | HIGH gate | research decision register; FR-007/020; T002 | The source has no operator authorization model. Approve shared restricted scope or authenticated roles before live reads/writes. |
| D2 | Cloud contract | HIGH gate | API contract; FR-011/012/014/022; T003 | Schema and guide conflict on duration, writable name, and revoke. Obtain authoritative evidence or keep conflicting behavior unavailable. |
| D3 | Batch policy | HIGH gate | CSV contract; FR-018; T004 | Byte/row/field/request/time limits and duplicates lack approved values. Approve bounds and invalid-row policy before import implementation. |
| D4 | Audit/recovery | HIGH gate | data model; FR-024/025; T005/T030 | Durability, retention, actor evidence, and post-dispatch failure policy need approval. Verify existing-store support before writes. |
| D5 | Visual integration | MEDIUM gate | E2E difference acceptance; FR-027; T006/T034 | Approve source-magenta content or target-theme adaptation, comparator limits, and explicit differences. No target screenshots exist. |
| D6 | Notification | HIGH gate | API contract; FR-034; T006 | Source backend accepts an undeclared option. Keep it unavailable unless approved evidence supports a visible workflow. |
| D7 | Confirmation | HIGH gate | API confirmation contract; FR-021; T002/T018 | Approve exact action/batch words and actor/payload/scope/revision binding. No write may use an invented default. |

These are explicit future gates, not missing planning placeholders.
No source-rights permission gate remains.
No critical artifact inconsistency or unmapped functional requirement was found.
No duplicate requirement or dependency cycle was found.

## Coverage summary

The [35-row coverage table](tasks.md#requirement-coverage) maps every FR-001 through FR-035 to tasks and TEST-001 through TEST-035.
The [72-row inventory](design/contracts/parity.md) independently maps every measured source feature.
The [39-file register](design/contracts/source-files.md) covers the complete source tree, including seven PNG files and all workflows/tests.

| Success criterion | Has tasks? | Task IDs | Acceptance |
| --- | --- | --- | --- |
| SC-001 | Yes | T001,T037,T038 | TEST-030 accounts for all inventory rows and dispositions. |
| SC-002 | Yes | T002,T018,T024,T028,T033 | TEST-020/021/022 proves zero writes for invalid submissions. |
| SC-003 | Yes | T025,T026,T028 | TEST-016/018/019 accounts for every CSV row. |
| SC-004 | Yes | T006,T032,T034,T038 | TEST-027/028 requires approved screenshot differences. |
| SC-005 | Yes | T013,T024,T029,T030 | TEST-005/006/023/029 preserves unknown values and truthful outcomes. |
| SC-006 | Yes | T008,T031,T035 | TEST-025/026/035 preserves one application and existing stores. |
| SC-007 | Yes | T001,T035,T037 | TEST-030 maps remaining requirements before implementation. |

No task is without a requirement or acceptance purpose.
Setup and policy tasks establish the conditions required by their dependent stories.
Every task names a primary destination and explicit prerequisites.
All 40 tasks remain unchecked, not partly delivered.

## Measured metrics

| Measure | Result |
| --- | --- |
| Source tracked blobs | 39: 32 text files and seven PNG files |
| Source route handlers / SDK methods | 13 / 12 |
| Functional requirements / success criteria | 35 / 7 |
| Requirements with task coverage | 42 of 42, 100 percent |
| Inventory dispositions | 72: 1 Existing, 42 Missing, 15 Intentional deviation, 14 Decision required |
| Future implementation tasks | 40 unchecked, 0 checked, 0 malformed |
| Task prerequisites | 143 edges, zero cycles |
| Tasks by story | US1: 6, US2: 9, US3: 4, US4: 3, US5: 3 |
| Setup / final tasks | 9 / 6 |
| Acceptance families / paired visual families | 35 / 15 |
| Declared future paired viewport combinations | 45 family/viewport combinations, with additional state variants |
| Built-in spec-quality items | 16 satisfied planning criteria |
| Reviewer-owned migration-quality items | 36 unchecked |
| Current fresh source captures | 12 PNG files with SHA-256 manifest |
| Immutable file/range/asset references validated | 65 distinct references across 49 files |
| Explicit unresolved decision count | 7, all implementation-gated |
| Undefined placeholders / duplication / critical artifact issues | 0 / 0 / 0 |

The 14 Decision required rows share seven decision families. These are different units.
Existing infrastructure does not count as existing guest functionality.
Only P063 is Existing guest functionality.

## Constitution alignment

The feature root has five children. The design directory has five children.
Contracts has four files, and checklists has two files.
The new root uses the canonical eight-level base-5 numeric route.
No unmanaged direct record or shared selector changes.
The plan records existing folder debt and separate incremental remediation.
T007 gates future bounded destinations, touched existing violations, and shared-file handover.

All future functionality must use named classes, typed small methods, and direct defining-module imports.
The projection move must update every caller without a shim and record module/logger changes.
The safety contracts require validated inputs, exact scope, approved access, typed confirmation, durable intent, and no ambiguous retry.
Future CLI confirmation must use the repository safe-input pattern if a CLI surface is separately approved.
No new CLI/menu operation is currently proposed.

The current change contains no product code, enabled route, live session, schema, dependency, container, or workflow edit.
The user explicitly requested a planning-only PR and excluded implementation and merge.
Container build, deployment, live operation, and merge acceptance therefore remain future work, not claimed results.
The constitution and required status names remain unchanged.

## Executed evidence and limitations

Source rendering used actual Flask test-client HTML and source JavaScript with an in-memory connection.
Every browser request was fulfilled locally, including cached Bootstrap assets.
No server listened on port 9608 despite its synthetic browser URL.
No container, live Mist SDK construction, production credential, or cloud write occurred.
The manifest records 12 screenshots, no browser errors, and synthetic requests.
The screenshots cover dashboard, edit, blank/filled add, in-memory result, CSV dialog/preview, client search, statuses, empty search, tablet, and phone.
They are session evidence, not frozen-clock pixel baselines.

Target visual/browser/runtime migration acceptance is **UNVERIFIED**.
The target guest UI is absent.
Source screenshots and 39 mocked source tests do not prove target parity or live cloud semantics.
Only the existing 22 projection tests provide current guest product acceptance.

## Validation record

The commands below ran before the planning commit unless stated otherwise.
The PR records final rebased and post-commit results separately.

| Exact command | Actual result |
| --- | --- |
| `python3 scripts/bootstrap_worktree.py` | Passed using the inspected baseline script. Installed development tools and Chromium. Confirmed the expected GitHub account. |
| `SPECIFY_FEATURE_DIRECTORY=specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity test-artifacts/guest-parity-pwsh/pwsh -NoProfile -File .specify/scripts/powershell/setup-plan.ps1 -Json` | Passed. The plan template resolved into the explicit new feature directory. |
| `SPECIFY_FEATURE_DIRECTORY=specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity test-artifacts/guest-parity-pwsh/pwsh -NoProfile -File .specify/scripts/powershell/setup-tasks.ps1 -Json` | Passed. Resolved plan/spec and nested design inputs. |
| `SPECIFY_FEATURE_DIRECTORY=specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity test-artifacts/guest-parity-pwsh/pwsh -NoProfile -File .specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` | Passed. Required artifacts exist, and nested tasks/design inputs are discoverable. |
| `PATH="$PWD/test-artifacts/guest-parity-pwsh:$PATH" .venv/bin/python -m pytest -q tests/unit/web_portal/test_guest_authorization_read_model.py tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_nested_package_structure.py` | 82 passed. One existing Dash pytest deprecation warning. Initial execution without PowerShell failed routing tests. Verified official PowerShell restored the tool and the rerun passed. |
| `(cd test-artifacts/guest-parity-source && PYTHON_DOTENV_DISABLED=1 ../../.venv/bin/python -m unittest discover -s tests -v)` | 39 source tests passed with mocked responses. |
| `.venv/bin/python test-artifacts/guest-parity-render.py` | 12 source PNG captures, SHA-256 manifest, no browser errors or external browser requests. |
| `.venv/bin/python test-artifacts/guest-parity-validate.py` | 72 mapped rows, 35 functional requirements, 40 tasks, 35 test families, 15 visual families, 143 acyclic edges, 39 source files, 65 immutable references. Rejected dangling ID, dependency cycle, and out-of-range citation fixtures. |
| `.venv/bin/check-citations specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity` | Zero local `path:line` citations checked, zero unresolved. This does not validate remote anchors. The separate immutable-reference check does. |
| `.venv/bin/speckit-task-audit --root .` | Failed on unrelated historical records. Examined 870 feature records, 393 task files, and 10,783 task markers. No baseline or allow-list changed. |
| Targeted `SpecTaskAudit._finding_for` through the installed package | Passed: one Draft record, 40 unchecked, zero checked/malformed/citation errors/merge blockers. No allow-list exception. |
| `git diff --exit-code -- .specify/feature.json` | Passed. Shared selector unchanged. |
| `git diff --name-only 772fc927761b61dea8beb7f708fbbe78c2a38d86 origin/main -- src/interfaces/portals/guest_authorizations.py tests/unit/web_portal/test_guest_authorization_read_model.py web_portal/app.py web_portal/templates/base.html web_portal/services/config.py compose.yml requirements.txt documentation/mist-api-openapi31json.json AGENTS.md .github/copilot-instructions.md .specify/memory/constitution.md` | Only the repository instruction file changed. All eight target evidence files, generic instructions, and constitution remain identical. |

STE requires explicit Markdown file paths, not a directory argument.
An initial directory-only invocation examined zero files and failed.
The corrected explicit-file command passed all files inspected at that point, with scores from 92 through 98.
Final pre-commit checks produced these additional results:

| Exact command | Actual result |
| --- | --- |
| `find specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity -name '*.md' -print0 \| xargs -0 .venv/bin/ste-linter --config .ste-linter.toml --min-score 80 --quiet` | All 13 feature Markdown files passed, scores 91 through 98. |
| `.venv/bin/ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4588-guest-migration-parity-planning.md --quiet` | Passed, score 94. |
| `.venv/bin/markdown-link-check --root . specs/numbered/0/0/1/2/1/3/2/3/4588-guest-migration-parity changelog.d/issue-4588-guest-migration-parity-planning.md` | Examined 14 staged/tracked Markdown files, zero broken links. |
| `PATH="$PWD/test-artifacts/guest-parity-pwsh:$PATH" .venv/bin/python -m pytest -q tests/unit/web_portal/test_guest_authorization_read_model.py tests/guardrails/test_spec_route_contract.py tests/guardrails/test_process_folder_structure.py tests/guardrails/test_nested_package_structure.py tests/guardrails/test_changelog_fragment_policy.py` | 99 passed, one skipped, one existing warning. The skip requires a GitHub pull-request event, not a local run. |
| `PATH="$PWD/test-artifacts/guest-parity-pwsh:$PATH" .venv/bin/python -m pytest -q -rs tests/guardrails/test_changelog_fragment_policy.py` | 17 passed, one skipped. Exact reason: the changelog diff guard runs only during a pull request event. |
| `git diff --cached --check` | Passed. The manifest contains only 13 new planning files and one unique release-note fragment. |

Final rebased and post-commit test-quality results belong in the PR evidence.
Do not treat a zero-file result as an artifact pass.

The first rebase restored the environment with `uv sync --locked --extra dev`.
The same 99 tests passed, with the same one PR-event-only skip. Locked mistapi remained 0.64.1.
The post-commit guidance preflight passed one test and validated all four required inputs.
The committed-diff quality ratchet reported zero changed test files and zero new findings.
Zero selected test files is expected for this Markdown-only change, not proof of planning quality.

The first full quality scan found 35 additional findings in the downloaded original-source test snapshot.
These were not target repository tests.
The source snapshot moved into persistent session evidence, outside target test discovery.
No target file, analyzer configuration, threshold, or baseline changed to address this contamination.
The final clean full-scan result is recorded in the PR.

Main advanced again to `296b977e28be50cd9ddcca57c46b35bb029afe27` while validation ran.
That change affects the ops-platform token module, tests, and its existing specification.
All eight guest target evidence files remain unchanged.
The branch must rebase again before submission and repeat applicable checks.

## Workflow and approval handling

Specify, clarify, plan, tasks, checklist, and analyze skills were invoked in this worktree.
The mandatory git-feature hook skill was invoked, but its branch-creation script was not run.
The app already owns the branch. Its restrictions prohibit raw branch creation/switching and shared selector mutation.
Command-scoped feature selection resolved the logical numeric feature without renaming or switching Git.

Enabled optional git commit hooks were deferred to one coherent planning commit.
Disabled companion hooks stayed disabled.
No hook set the feature to ready-to-implement.
The active plan skill did not require a shared agent-context update.
No shared instruction or agent-context file changed.

The parent worktree and its old #4231 drafts remain untouched.
PR #4208 still owns shared portal files. This planning record does not overlap.
The planning PR must use non-closing links to #4588, #4231, and #4278.
Do not merge it automatically or treat it as approval for live guest operations.

## Next actions

Review the 36 reviewer-owned requirements-quality questions and applicable D1-D7 decisions.
Keep the implementation issue #4278 open.
Begin T001 only when the user separately requests implementation.
Before enabling behavior, satisfy each explicit access, contract, confirmation, audit, CSV, visual, and release gate.
Final migration approval requires T038 original-versus-target evidence, T039 recovery rehearsal, and T040 operator approval.
