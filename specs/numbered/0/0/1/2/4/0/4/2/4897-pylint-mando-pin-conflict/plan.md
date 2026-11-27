# Implementation Plan: Pylint gate failure from the mando 0.8.2 pin

**Branch**: `fix/4897-pylint-mando-pin` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/0/4/2/4897-pylint-mando-pin-conflict/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, and checklists stay under `design/`. No contract applies to this change, so the plan omits `design/contracts/`.

## Summary

Hold `mando` at 0.7.1, and stop Dependabot from raising version 0.8. Pull request #4888 pins `mando==0.8.2`, but radon 6.0.1 requires `mando` below 0.8. pip stops at that conflict, so the Pylint (score gate) job never reaches its score step. The fix edits four files, adds one fragment, and adds one test function. It leaves the pins, the lock, and the gate threshold unchanged.

## Technical Context

- **Language and version**: Python 3.15, as `.github/copilot-instructions.md` requires in section Language and environment.
- **Primary dependencies**: pytest and packaging for the guard tests, and `importlib.metadata` from the standard library. The change adds no new dependency.
- **Pinned packages**: radon 6.0.1 as a development pin, and mando 0.7.1 as its transitive pin.
- **Storage**: None.
- **Testing**: pytest guard tests in `tests\guardrails`, the Quality Gates workflow in `.github/workflows/ci.yml`, and `uv lock --check`.
- **Target platform**: GitHub Actions runner `ubuntu-latest`, and Windows 11 for local runs.
- **Project type**: CI and dependency configuration change in an existing repository.
- **Performance goals**: None. The new test reads two small text files and one installed metadata record.
- **Constraints**: The five-item rule applies to each new file and folder. STE applies to each prose line and comment. Each new line needs an inline comment and action logging. The change does not edit `requirements-dev.txt`, `uv.lock`, or `pyproject.toml`.
- **Scale and scope**: Four edited files, one added fragment, and one new test function.

## Constitution Check

*Gate: passes before research and again after design.*

| Rule | Gate | Result | Reason |
| - | - | - | - |
| I. Five-item rule | No new direct child under a noncompliant parent. | Pass | The change adds no file to `tests\guardrails`. It edits two existing guard modules. The fragment is one unique process record in `changelog.d\`, which the constitution allows. Existing debt appears in Complexity Tracking. |
| II. Class-based architecture | No standalone wrapper. | Pass | The new test calls the existing class method `DependencyLock.read_requirements`. It delegates to no other function. |
| III. Safety first | No input, secret, or destructive step. | Pass | The change reads repository files and installed metadata only. No credential enters code, logs, or output. |
| IV. Full deployment pipeline | Each gate runs before the pull request passes CI. | Pass by plan | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run the pipeline. |
| V. Observability | ASCII log text and no secret in logs. | Pass by plan | The new log lines use ASCII text and `%s` values only. |
| VI. Inline comments | Each new executable line has an inline comment. | Pass by plan | Task T005 requires a comment on each new line. |
| VII. Action logging | An info line before and a debug line after each action. | Pass by plan | Task T005 requires log lines around the metadata read and the pin read. |
| Mist Cloud REST | Each REST call uses a working mistapi method. | Not applicable | The change makes no Mist REST call. |
| Owned WebSocket transport | Names a mistapi path and a failed contract. | Not applicable | The change owns no WebSocket transport. |
| UV and pip inputs | `requirements.txt` and `requirements-dev.txt` stay current. | Pass | Both export files and `uv.lock` stay unchanged. |
| Test containers | Each container joins the compose group. | Not applicable | The change starts no container. |
| Data directory and backends | Product output goes to `data\` and to the configured backends. | Not applicable | The change writes no product output. |
| Database keys | A natural key exists before a new operation. | Not applicable | The change adds no operation. |
| Security findings | Fix over suppress. | Pass | The change adds no suppression comment. |
| Release notes | One unique fragment for each change. | Pass | Task T008 adds `changelog.d\issue-4897-pylint-mando-pin.md`. Decision D-6 resolves the README exemption. |
| Documentation | The same change updates the affected documents. | Pass | Task T007 adds the Known pitfalls entry. |

For repository structure and generated files:

- The commit subject and the pull request title use a Conventional Commit form.
- The change adds only its own fragment and its own record folder.
- The plan records existing folder debt. Complexity Tracking names a separate remediation action for it.
- Product output stays under `data\`. The change writes none.

For a feature that uses Juniper Mist Cloud: not applicable. The change makes no Mist call.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/0/4/2/4897-pylint-mando-pin-conflict/
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
      ci-gate.md
```

### File-by-file change map

| Path | Action | Change |
| - | - | - |
| `.github/dependabot.yml` | Modify | Add an `ignore` list to the pip stream, lines 3 to 11. The entry names `mando` and `versions: [">= 0.8"]`. |
| `tests/guardrails/test_pr_title_workflow.py` | Modify | Add the same `ignore` list to the pip item of `POLICY_SNAPSHOTS["dependabot"]`, after line 29. |
| `tests/guardrails/test_dependency_lock_file.py` | Modify | Add `import importlib.metadata` before line 9. Append one test function, `test_pinned_mando_satisfies_radon_requirement`, after the last function. |
| `.github/copilot-instructions.md` | Modify | Add one bullet to Known pitfalls after line 574, before `## Key files` at line 576. |
| `changelog.d/issue-4897-pylint-mando-pin.md` | Add | One `###` heading and one `Fixed` bullet that names issue #4897. |
| `requirements-dev.txt` | No change | Stays at `mando==0.7.1` on line 179. |
| `requirements.txt` | No change | Pins no mando or radon. |
| `uv.lock` | No change | Stays at mando 0.7.1 on line 1301. |
| `pyproject.toml` | No change | Keeps `radon==6.0.1` on line 118. |
| `.github/workflows/ci.yml` | No change | Keeps the Pylint job, the install step, and the threshold. |
| `src\` and `MistHelper.py` | No change | Product code stays unchanged. |

### Dependencies

- The change adds or changes no dependency.
- radon 6.0.1 and mando 0.7.1 stay pinned.
- The new test uses `packaging`, which the module already imports, and `importlib.metadata` from the standard library.

### Architecture

```text
pyproject.toml (radon==6.0.1, dev extra)
        |
uv.lock (mando 0.7.1, radon 6.0.1)
        |
requirements-dev.txt (uv export, mando==0.7.1) -- guarded by test_dependency_export.py
        |
pip install in each Quality Gates job

.github/dependabot.yml (pip stream, ignore mando 0.8 and later)
        |
Dependabot pull requests -- policy snapshot in test_pr_title_workflow.py

Installed radon 6.0.1 metadata --> test_pinned_mando_satisfies_radon_requirement
```

## Implementation Outline

1. Confirm the root cause with the reproduction commands. This record does that in T001 and T002.
2. Add the Dependabot ignore entry and update the policy snapshot to match (T003, T004).
3. Add the mando pin test and prove its red state on the pull request #4888 pin (T005, T006).
4. Add the Known pitfalls entry and the changelog fragment (T007, T008).
5. Keep the pins, the lock, and the gate unchanged, and confirm lock parity (T009).
6. Run every local gate that applies (T-LOCAL-GATES).
7. Open the pull request, watch CI, and merge after authorization (T-PR, T-REMOTE-CI, T-MERGE).

## Complexity Tracking

Existing debt that the change touches. None of it is new debt.

| Item | Kind | Why it stays | Remediation |
| - | - | - | - |
| `tests\guardrails` holds 79 direct children on main. | Grandfathered | The change edits two existing modules and adds no child. | A separate issue moves the dependency guards into a nested package. |
| `tests\guardrails\test_dependency_lock_file.py` holds eight top-level names. | Grandfathered | The change adds one function, which makes the ninth. | The same separate issue splits the module. |
| `changelog.d` holds 335 direct children on main. | Grandfathered process folder | The constitution allows one unique record for each change. | A separate issue archives released fragments by release. |

New design that needs a reason.

| Item | Why it is needed | Simpler alternative rejected because |
| - | - | - |
| The new test reads the range of radon with `importlib.metadata`. | The rule lives in the installed radon metadata, and the lock does not store it. | `uv.lock` names mando under radon without a version range, so a lock parse cannot see the rule. |

## Risks and Mitigations

- **Dependabot may not honor the `versions` key.** Mitigation: the implementer checks the next scheduled run in User Story 3. The implementer closes any repeated mando pull request and records the result. The main branch stays green.
- **The policy snapshot freezes the whole Dependabot file.** Mitigation: T003 and T004 change the file and the snapshot in one commit.
- **A future radon release may accept mando 0.8.** Mitigation: the new test passes with the old ignore still present. The Known pitfalls entry tells the maintainer to remove the ignore and raise both packages in one pull request.
- **A security fix may exist only in mando 0.8.** Mitigation: pip-audit scans `requirements.txt` only, and mando is a development-only package. This record accepts the gap for development tooling. `design\research.md` records the gap.
- **The Windows checks use the same install step.** Mitigation: T-REMOTE-CI confirms that each Windows check passes on the fix pull request.
- **Main moves before the fix merges.** Mitigation: update the branch from main, then rerun every required check.
- **The guard module already exceeds the five-item limit.** Mitigation: Complexity Tracking records the debt and names the remediation issue.

## Rollback Steps

1. Before the merge, close the fix pull request. Keep the issue open.
2. Warning: deleting a remote branch can remove the only copy of its commits. Record the commit SHA before you delete the branch.
3. After the merge, create a new issue and a new branch from main. Revert the squash commit on that branch. Do not push to main.
4. The revert removes the ignore entry, the snapshot change, the test function, the Known pitfalls entry, and the fragment together.
5. Caution: after a revert, the next scheduled Dependabot run can raise mando 0.8.2 again. The Pylint job then fails again until the ignore entry returns.
