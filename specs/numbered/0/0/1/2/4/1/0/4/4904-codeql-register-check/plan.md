# Implementation Plan: CodeQL register check fails on pull request 4888

**Branch**: `fix/4904-codeql-register-check` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification in `specs/numbered/0/0/1/2/4/1/0/4/4904-codeql-register-check/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, and quickstart stay under `design/`. The contracts folder is omitted, as explained below.

## Summary

Pull request #4888 raises the transitive pin `mando` from 0.7.1 to 0.8.2. Radon 6.0.1, pinned in the same file, requires `mando` below 0.8. Pip stops the `codeql_register_check` job at its install step, so the register check never runs. This plan keeps the pin at 0.7.1. It adds a Dependabot ignore entry for minor and major `mando` updates, adds a local guard for the radon ceiling, and documents the cause.

## Technical Context

**Language/Version**: Python, the version that the existing guard modules in `tests/guardrails/` use.

**Primary Dependencies**: pytest, `packaging`, and PyYAML, which the existing guard modules import. The standard library module `importlib.metadata` reads the installed radon requirement. No new dependency.

**Storage**: None. The change writes no data file.

**Testing**: pytest guard tests in `tests/guardrails/`. The pytest shards and the local gates run them.

**Target Platform**: Linux CI runners and Windows 11 developer machines.

**Project Type**: CI configuration and guard tests.

**Performance Goals**: The new guard reads one local requirement set and one installed metadata record. It makes no network call.

**Constraints**: `requirements-dev.txt`, `requirements.txt`, and `uv.lock` stay unchanged. The guard fails closed when radon metadata is absent.

**Scale/Scope**: One ignore entry, two guard tests, one class, one documentation note, and one changelog fragment.

## Constitution Check

*Gate: must pass before research. Re-checked after design.*

| Principle or rule | Result | Reason |
|-------------------|--------|--------|
| I. Five-item rule | Pass, with recorded debt | The change adds no child to `tests/guardrails/`, which holds 80 children in the local working tree. It adds one fragment to `changelog.d/`, which holds 335 children in the same working tree. Principle I allows that fragment as a unique process record. The remediation action is separate. The new record uses the numeric route, and each new directory holds one child. |
| II. Class-based architecture | Pass | The radon check logic lives in class `RadonRequirementCheck` with static methods. The test functions call that class and hold no logic. |
| III. Safety first | Pass | The new tests read local files and installed metadata only. They read no secret and make no network call. |
| IV. Full deployment pipeline | Pass, with the steps in `tasks.md` | The tasks run the local gates, commit explicit paths, rebase, push, open a pull request, wait for CI, and squash merge after authorization. `container-build.yml` does not run, because no changed path appears in its `paths` list (research RC-29). |
| V. Observability and logging | Pass | The new code logs in ASCII only, with `%s` values in each message. |
| VI. Inline comments | Pass, checked in tasks | Tasks T002 and T003 require an inline comment on each executable line. |
| VII. Action logging | Pass, checked in tasks | Task T003 requires an `info` line before and a `debug` line after each file or metadata read. |
| Mist Cloud constraints | Not applicable | No Mist REST or WebSocket call occurs. |
| Podman and containers | Not applicable | No container runs in this change. |
| UV and requirements | Pass | `requirements.txt`, `requirements-dev.txt`, and `uv.lock` stay unchanged. |
| File paths | Pass | The new Python code builds paths with `pathlib.Path`. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/1/0/4/4904-codeql-register-check/
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

### Source change map (repository paths)

| Path | Action | Purpose | Requirement |
|------|--------|---------|-------------|
| `.github/dependabot.yml` | Modify | Add the `mando` ignore entry to the pip stream. | FR-003 |
| `tests/guardrails/test_pr_title_workflow.py` | Modify | Add the same ignore entry to the pip snapshot. Add one policy test. | FR-003 |
| `tests/guardrails/test_dependency_lock_file.py` | Modify | Add class `RadonRequirementCheck` and two tests. | FR-001, FR-002, FR-005 |
| `documentation/quality-gates.md` | Modify | Add a note below the job table. | FR-007 |
| `changelog.d/issue-4904-codeql-register-check.md` | Add | Add one release-note fragment. | FR-006 |
| `requirements-dev.txt` | No change | Keeps `mando==0.7.1`. | FR-002 |
| `uv.lock` | No change | Keeps `mando` 0.7.1 and radon 6.0.1. | FR-002 |
| `.github/workflows/ci.yml` | No change | Keeps the gate job unchanged. | FR-004 |
| `tests/guardrails/test_codeql_register_gate.py` | No change | Keeps the gate guard unchanged. | FR-004 |

Process action, not a file: close pull request #4888 unmerged after the fix merges. The owner must authorize the close (SC-004).

### Contracts

The `design/contracts/` folder is omitted, because no interface contract applies. The ignore entry follows the `update-types` syntax that `.github/dependabot.yml` already uses in its npm stream (research RC-17).

## Gate Applicability

| Local gate | Applies | Reason |
|------------|---------|--------|
| Compile | Yes | Principle IV requires `py_compile MistHelper.py` before each commit. |
| Lint | Yes | Two Python test modules change. |
| Format | Yes | Two Python test modules change. |
| Types | No | No changed file is a type-checked source file. |
| Tests | Yes | Each changed test module runs. |
| Full tests | Yes | The changed guard tests belong to the `tests\guardrails` shard. |
| Safe sweep | No | No menu changes. |
| Coverage | No | No file under `src/` changes. |
| Test quality | Yes | Changed test modules pass the ratchet. |
| Complexity | No | No file in the radon path list changes. |
| Security lint | Yes | Bandit reads the changed test modules. |
| Dependency audit | No | No requirement file changes. |
| Code quality | No | No file under `src/` changes. |
| Dead code | No | No changed file lies in the vulture scope. |
| Docstrings | No | No changed file lies in the pydocstyle or interrogate scope. |
| Menu reference | No | No menu changes. |
| Symbols | No | No scripted sweep runs. |
| STE | Yes | `documentation/quality-gates.md` and the fragment are Markdown files. |
| Ops portal | No | No file under `ops-portal/` changes. |
| Ops platform | No | No file under `mist-ops-platform/` changes. |

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|-----------|------------|--------------------------------------|
| One new child in `changelog.d/`, which holds 335 children in the local listing | A release-note fragment is the required unique record for a user-visible fix. | Editing `CHANGELOG.md` on a feature branch conflicts on each rebase, so the rules forbid it. |

## Risks and Mitigations

| Risk | Effect | Mitigation |
|------|--------|------------|
| The ignore entry does not block a transitive pin in the export. | Dependabot proposes `mando` 0.8.x again. | Check SC-005 after the merge. The local guard still rejects a bad pin in CI. Unverified item U-1 tracks this risk. |
| A later radon release accepts `mando` 0.8. | The ignore entry blocks a valid upgrade. | The owner removes the ignore entry in the same change as the pin and the lock update. |
| Radon metadata is absent in an environment. | The guard fails. | The guard fails closed and names the missing package. |
| The policy snapshot does not match the new pip stream. | `test_complete_policy` fails. | Task T002 adds the same ignore list to the snapshot. |
| Pull request #4888 closes before the ignore entry merges. | Dependabot can propose the same bump again. | Task T-MERGE closes pull request #4888 after the merge. |

## Rollback Steps

1. Before the merge, close the fix pull request and delete branch `fix/4904-codeql-register-check`.
2. After the merge, open a new pull request that reverts the squash commit.
3. Reopen issue 4904 with a comment that names the revert pull request.

Caution: a revert restores the resolver conflict path. Keep pull request #4888 closed until the owner decides otherwise.

## Process Actions Outside the Change

- The orchestrator adds the `in-progress` label to issue 4904 before the branch exists.
- The orchestrator authorizes the merge and adds the `auto-merge` label after each check passes.
- The orchestrator authorizes the close of pull request #4888 after the merge.
