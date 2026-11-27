# Implementation Plan: Bound host restore for the WLAN RADIUS fixture

**Branch**: `fix/4797-bound-host-restore` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/3/1/4/2/4797-bound-host-restore/spec.md`

**Input**: Numeric record route `0/0/1/2/3/1/4/2`. The route is the eight-digit base-5 form of issue 4797 (RC-42, RC-43, RC-44).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Keep research, data model, quickstart, and checklists under `design/`.

## Summary

The defect exists on main and on the candidate commit. The `fake_mh` fixture binds a fake host to the shared resolver and never restores the previous host. The fix exists in commit 1f4843c on open PR #4208. This change adds one parametrized restore test on main after PR #4208 closes. It changes no production code.

## Technical Context

- **Language/Version**: Python 3.15.2 in the repository virtual environment. The repository requires Python 3.15 or newer.
- **Primary Dependencies**: None added. pytest 9.2.0 is pinned in `requirements-dev.txt` (RC-55).
- **Storage**: Not applicable. The change writes no data.
- **Testing**: pytest with `unittest.mock`. Shard runs use `pytest-chunks`.
- **Target Platform**: Windows 11 for local runs. The issue reporter ran on Linux and macOS (issue #4797 body).
- **Project Type**: Test-only change.
- **Performance Goals**: Not applicable. The new tests use no network call.
- **Constraints**: ASCII output only. An inline comment on each new executable line. No suppression comment.
- **Scale/Scope**: One test module and one record folder.

## Constitution Check

*GATE: Must pass before implementation. Re-check before the pull request.*

Gate G-1 holds the file-overlap rule. Implementation starts only after PR #4208 closes.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule (constitution line 40) | Pass | The route parent holds one child, `1` (RC-50). Child `2` makes two. The feature root holds five children. |
| II. Class-based architecture | Pass | The change adds one parametrized fixture and one test class. No function wraps a method. |
| III. Safety-first | Pass | The change touches no input handling, destructive operation, or credential. |
| IV. Full deployment pipeline (constitution line 145) | Pass with condition | Steps 1 to 9 run in T-LOCAL-GATES through T-MERGE. Steps 10 to 12 follow the merge. Open item U-9. |
| V. Observability and logging | Pass | New log lines use `%s` templates and ASCII text. No secret reaches a log line. |
| VI. Inline comments | Pass | Each new executable line carries an inline comment that gives its reason. |
| VII. Action logging (constitution line 235) | Pass | The new fixture logs before and after its bind and its restore. Analysis item A-6 covers PR #4208. |
| Mist Cloud constraints | Not applicable | The change sends no REST request and calls no mistapi function. |
| Changelog fragment (constitution line 409) | Pass with decision D-5 | The changelog README exempts internal-only changes (RC-41). Analysis item A-7 records the conflict. |
| Process-folder rule | Pass | The record is one unique child of the managed numbered root (RC-53). No existing violation changes. |
| File overlap (constitution line 503 and AGENTS line 245) | Blocked until PR #4208 closes | Gate G-1 holds T005 through T008 until then. |
| PR checklist (constitution line 516) | Pass for T-PR | T-PR adds the closing reference, gate results, file summary, and deployment and rollback notes. |

## Architecture

The import path and the test path meet at the shared resolver. The sequence has six steps.

1. The import of MistHelper.py calls `MainEntrypoint.bind_host_module` (RC-18 at line 712, RC-17 at line 375). That call binds the real module as the bound host (RC-11 at line 131).
2. The conftest loads MistHelper.py into `sys.modules` before any test runs (RC-19 at line 170).
3. The `fake_mh` fixture binds a fake host (RC-08 at line 45). On main, no step restores the previous host.
4. The shared resolver compares `sys.modules` with its bound host (RC-14 at line 286). When the two differ, the resolver treats the `sys.modules` module as a test host.
5. A test host answers the `org_id` read before the patched active context (RC-15 at line 203, RC-16 at line 25). The admission module on PR #4208 reads `org_id` from the resolver (RC-22, RC-24). The read skips the patched context, and the admission raises (RC-23 at line 212).
6. PR #4208 restores the previous host with `patch.object` (RC-10 at line 46). The identity check then holds after teardown.

Main differs from the candidate. Main admission does not read the resolver (RC-21 at line 102). The defect therefore has no proven visible failure on main. Research item U-5 records this gap. The restore tests check the defect directly, so they do not depend on the admission layout.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/1/4/2/4797-bound-host-restore/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

The `contracts/` folder is omitted. The change adds no CLI, menu, API, or output contract.

### Source Code (repository root)

```text
tests/unit/refactors/
  test_wlanradius_timer_manager_paths.py   (follow-up change: one fixture and one test class)
```

No file under `src/` changes.

## File-by-File Change Map

| Path | Action | Requirements | Note |
| - | - | - | - |
| `tests/unit/refactors/test_wlanradius_timer_manager_paths.py` | Modify, after PR #4208 closes | FR-001, FR-007, FR-008, FR-009 | Add the `previous_host_guard` fixture and the `TestFakeHostRestore` class. |
| `specs/numbered/0/0/1/2/3/1/4/2/4797-bound-host-restore/` | Add | FR-006 | Add the record in the follow-up pull request. |
| `src/interfaces/wan_performance/collection/request_admission.py` | No change | FR-002 | The issue excludes production admission changes. |
| `src/foundation/runtime/config/source_dependency_resolver.py` | No change | FR-002 | The tests use the existing private attribute. No production change is needed. |
| `tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py` | No change | Not applicable | Main path. Verification uses it after the merge. |
| `tests/unit/wan_performance/test_request_admission.py` | No change | Not applicable | PR head path. Verification uses it before the merge. |
| `changelog.d/` | No change | Not applicable | Decision D-5. |
| `documentation/` | No change | Not applicable | The change alters no user-visible behavior. |
| `.github/test-quality-baseline.json` | No change | FR-009 | Never rewrite the baseline to hide a finding (RC-61). |

## Dependencies

- No dependency is added or changed.
- pytest 9.2.0 runs the tests (RC-55). The shard commands use `--test-timeout 120` (RC-71).
- The `unittest.mock` module from the standard library supplies the doubles.

## Implementation Outline

1. Confirm that PR #4208 is open or closed. Record the result for gate G-1.
2. After PR #4208 closes, branch from main as `fix/4797-bound-host-restore`.
3. Add the `previous_host_guard` fixture and the `TestFakeHostRestore` class to the fixture module.
4. Run the Tests row for the changed file.
5. Run the mutation check in a scratch worktree. Remove the restore and expect errors.
6. Add the record folder under the route.
7. Run the Lint, Format, Full tests, and Test quality rows.
8. Commit, push, open the pull request, watch the checks, and request authorization.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| PR #4208 merges late | The fix reaches main late. | Decision D-9 gives the merge timing to the owner. |
| PR #4208 moves the fixture path | Node IDs change. | Repeat the verification with the new IDs before the merge. |
| The fixture reads a private attribute | A rename breaks the fixture. | `patch.object` fails loudly on a missing attribute. The restore tests read the same attribute. |
| The teardown check depends on pytest order | A pytest change could reorder teardown. | pytest 9.2.0 runs teardown in reverse setup order (sources S-4). The mutation check proves the failure. |
| The local working tree differs from HEAD | A local run uses uncommitted code. | Run each check in a clean worktree at the commit under test (decision D-10). |
| The ratchet reads the fixture file | A new test adds a finding. | Run the ratchet on the committed change. Never rewrite the baseline (RC-61). |
| Shard 1 takes about 1179 seconds | The run is slow. | Run it once per commit under test (RC-71). |
| Principle IV steps 10 to 12 apply to a test-only change | A deployment runs for no runtime change. | Open item U-9 asks the orchestrator to confirm the action. |

## Rollback Steps

1. For the follow-up pull request, revert the squash commit on a new branch from main with `git revert`.
2. Open a new pull request for the revert. Never push to a merged branch.
3. For PR #4208, the orchestrator decides whether to revert the fixture commit. A revert restores the defect on main.
4. After a revert, the restore tests fail on main. Remove or repair them in the same pull request.

## Complexity Tracking

Not applicable. No constitution violation remains after decisions D-5 and D-6.
