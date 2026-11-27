# Implementation Plan: SSR optic and Mist cloud path lab tests

**Branch**: `docs/3960-ssr-lab-results` | **Date**: 2026-11-26 | **Spec**: spec.md

**Input**: Numeric record route `specs\numbered\0\0\1\1\1\3\2\0\3960-ssr-optic-cloud-lab-tests`. The route uses eight base-5 segments (research sources C-46 and C-47).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The change records six lab results in the SSR console health check runbook. It also adds one changelog fragment. The agent cannot run the lab tests. The owner runs them on lab SSR routers and returns sanitized outputs. The agent then applies the outputs, runs the local gates, and opens one pull request. The verification subsection already exists on main, so the change edits existing rows.

## Technical Context

- **Language/Version**: Not applicable. The change edits Markdown only.
- **Primary Dependencies**: ste-linter with `.ste-linter.toml` (C-50). markdown-link-check from the misthelper-devtools package (C-34). GitHub CLI for reads and the pull request.
- **Storage**: Git history only. The change adds no data file.
- **Testing**: TEST-01 to TEST-19 in design/quickstart.md. The changelog guard test runs without change (C-32).
- **Target Platform**: Engineers read the runbook on Windows 11, macOS, and Linux. Lab SSR routers run SSR software.
- **Project Type**: Documentation change with an owner-run lab procedure.
- **Performance Goals**: Not applicable. The change adds no runtime code.
- **Constraints**: The repository is public (C-39). Each change keeps one concern. No output may hold an address, serial number, or customer name.
- **Scale/Scope**: One runbook file, one changelog fragment, six lab tests, and two owner items (H-7 and H-8).

## Constitution Check

*Gate: passes before research and after design.*

| Principle or rule | Pass or fail | Reason |
|---|---|---|
| I. Five-item rule | Pass | The feature root holds five children. The design folder holds five children. Route parent 1/1/1 holds one child before this record (C-67), so the guard admits the new child. |
| II. Class-based architecture | Pass | The change adds no code. |
| III. Safety first | Pass | H-6 needs a typed confirmation (D-8). No credential is requested or stored (FR-002). Outputs are sanitized before commit (FR-004). |
| IV. Full deployment pipeline | Pass | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the gates, commit, push, pull request, CI, and squash merge. The container build does not run because no product file changes (C-38). |
| V. Observability and logging | Pass | The change adds no code and no log line. |
| VI. Inline comments | Pass | The change adds no code. |
| VII. Action logging | Pass | The change adds no code. |
| Mist Cloud transport | Pass | The feature makes no REST request. |
| Owned WebSocket transport | Pass | The feature owns no transport. |
| Technology constraints | Pass | The change touches no Python, PowerShell, container, or data file. |
| Test containers | Pass | The feature starts no container. The lab SSR is a device. |
| Adding menu operations | Pass | The feature adds no menu. |
| Testing | Pass | The change edits no test file. TEST-05 runs the existing guard. |
| Security findings | Pass | No tool finding is in scope. |
| Documentation | Pass | The runbook and its fragment change in one pull request. The README needs no update because no operation or product behavior changes. |
| Audience standard | Pass | The runbook text uses plain words for NOC engineers. STE applies. |
| Complexity-driven escalation | Pass | Documentation-only work runs directly. This record exists because owner-only steps need a handoff record. |
| Multi-agent git workflow | Pass | T002 covers the claim and the overlap check (C-41, C-44). T-PR covers the branch name, the body, and the labels (C-42, C-43). |

For repository structure and generated files:

- The commit subject and the pull request title use the Conventional Commit form.
- The change adds one fragment under `changelog.d/`. The orchestrator places this record folder in its own pull request.
- Folder debt: none. The change adds no child to a full folder. Route folder 1/1/1 gains one child (C-67).

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/1/3/2/0/3960-ssr-optic-cloud-lab-tests/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      lab-output-record.md
      verification-status-table.md
    checklists/
      requirements.md
      lab-safety.md
```

### Source change (repository root)

```text
documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md   (modify)
changelog.d/issue-3960-ssr-lab-results.md                (add)
```

## Architecture

The change runs in four stages:

1. The owner runs the lab tests and records sanitized outputs.
2. The agent applies the outputs to the runbook and adds one changelog fragment.
3. The agent runs the local gates and opens one pull request.
4. The orchestrator authorizes the merge. The auto-merge workflow squash merges after each required check passes.

## File-by-file change map

| Path | Action | Owner | Change |
|---|---|---|---|
| documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | Modify | Agent (T012, T013) | Record outputs at lines 104, 117, 141, 149, 166, and 240 to 246. Replace the Not run cells in rows 360 to 365. |
| changelog.d/issue-3960-ssr-lab-results.md | Add | Agent (T014) | One heading and one Changed bullet that names issue #3960. |
| scripts/verify_ssr_commands.py | No change | None | FR-008. |
| tests/unit/scripts/test_verify_ssr_commands.py | No change | None | FR-008. |
| Other files in documentation/noc-runbooks/ | No change | None | Out of scope. |
| CHANGELOG.md | No change | None | Out of scope. |
| specs/numbered/0/0/1/1/1/3/2/0/3960-ssr-optic-cloud-lab-tests/ | Add | Orchestrator | This record folder, in its own pull request. |

## Dependencies

- Merged and satisfied: pull request #3951 (commit 35177f4a, C-64), pull request #4114 (commit 400899f4, C-65), and pull request #3953 (merged 2026-10-06).
- Open and owner-only: lab SSR access (T003).
- Clear on 2026-11-26: no open pull request changes the runbook, the verifier files, or the planned fragment name. Seven pull requests were open.
- Tools: ste-linter and markdown-link-check run in the implementer's environment. This record did not run them.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| A customer name or an address enters the public repository. | Sanitize each output with contracts/lab-output-record.md. Run TEST-06. |
| H-6 stops Mist management of a lab router. | Require the typed confirmation (D-8). Remove the block rule and repeat H-5. |
| An output differs from a statement. | Change the statement to match the output. Keep the release string (FR-005). |
| The verifier reports a false pass. | Use the lab outputs as proof. The verifier is not a gate for this change (D-4). |
| Port names differ between the runbook and the device. | H-3 records the names that the device prints (T006). See U-2. |
| Old threads describe a stale state. | Use remote state. Record each difference in analysis.md (A1 and A2). |
| Main changes before the merge. | Rebase onto main. Repeat TEST-01 and TEST-02. |
| The issue closes too early. | Use `Refs #3960` until six outputs exist (FR-007, TEST-17). |

## Rollback Steps

1. If the merged change is wrong, open a new pull request that reverts it. Do not push to main.
2. If one recorded output is wrong, open a new pull request that corrects that statement. Keep its release string.
3. If H-6 leaves a lab router without Mist management, remove the block rule. Repeat H-5 and confirm that Connection reads up.
4. If the local branch of pull request #3951 is removed by mistake, recreate the branch from commit 35177f4a on main.

## Complexity Tracking

No constitution violation requires justification.
