# Implementation Plan: Locked Worktree Bootstrap

**Branch**: `fix/4591-locked-worktree-bootstrap` (planned) | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/1/3/3/1/4591-locked-worktree-bootstrap/spec.md` (planned record path)

**Input**: Numeric record under `specs/numbered/0/0/1/2/1/3/3/1/`. The route follows `.specify/scripts/powershell/spec-route.ps1` (base 5, width 8, line 17). Issue 4591 is 121331 in base 5. Padded to eight digits, it is 00121331, which gives the segments 0/0/1/2/1/3/3/1.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Name the index cause in the final message of the locked bootstrap. Name the active index variables without values. Stop the child environment from setting the deprecated `UV_NATIVE_TLS`. Correct the development setup document. The change edits one script, one test module, and one document. It adds one changelog fragment. It changes no dependency file.

## Technical Context

- **Language/Version**: Python 3.15 (`pyproject.toml:23`, `requires-python = ">=3.15"`).
- **Primary Dependencies**: None added. The bootstrap uses the standard library: `subprocess`, `logging`, `pathlib`, and `re`. uv is an external tool. This change documents uv 0.11.0 as the minimum.
- **Storage**: None. The bootstrap writes only the worktree `.venv` directory.
- **Testing**: pytest with `monkeypatch`, `tmp_path`, and the existing `ScriptedRun` helper in `tests/unit/scripts/test_bootstrap_worktree_uv.py`.
- **Target Platform**: Windows 11, macOS, and Linux.
- **Project Type**: Command-line bootstrap script.
- **Performance Goals**: Unchanged. The lock check timeout stays at 600 seconds (`scripts/bootstrap_worktree.py:129`).
- **Constraints**: ASCII-only output. No secret value in output. No shell string. No write to pip configuration.
- **Scale/Scope**: One script, one test module, one document, and one changelog fragment.

## Constitution Check

*GATE: Must pass before research. Re-check after design.*

| Rule | Result | Reason |
|---|---|---|
| I. Five-item rule, structure | Pass with recorded debt | `scripts/` holds 58 direct children (grandfathered). The change adds none. Each new route level holds five children or fewer. |
| I. Five-item rule, function limits | Pass | The new method and the changed functions keep at most five parameters, five blocks, and 25 lines. T-LOCAL-GATES checks the limits. |
| II. Class-based architecture | Pass with recorded debt | The new helper is a method of `InstallationPolicy`. Existing module-level helpers stay as they are (grandfathered). |
| III. Safety-first | Pass | The change adds no keyboard input and no destructive action. Index values never enter output (TC-02, TC-03). |
| IV. Full deployment pipeline | Pass | The tasks include T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. |
| V. Observability and logging | Pass | Output stays ASCII. The change adds no new service. |
| VI. Inline comments | Pass with review | Each changed line carries an inline comment. The review checks this rule. |
| VII. Action logging | Pass | The new info line runs before the locked sync. Its debug line reports the number of names. |
| Mist Cloud and mistapi | Not applicable | The change calls no Mist Cloud endpoint. |
| Container and Podman rules | Not applicable | The change starts no container. |
| Secrets and redaction | Pass | Output names variables only. TC-02 and TC-03 check it. |
| Dependency and lock rules | Pass | No dependency file changes (FR-010). |
| Security findings | Pass | No suppression comment is added. `bandit` runs on `scripts`. |
| SpecKit escalation | Pass | The cause spans the bootstrap, the lock, and uv. A record is required. |
| Multi-agent git | Pass with check | Issue 4591 exists. The branch name follows the pattern fix, issue number, and slug, as in `fix/4591-locked-worktree-bootstrap`. The overlap check runs before T-PR. |

For repository structure and generated files:

- The commit subject and the pull request title use `fix(scripts): name the index cause in the locked bootstrap`, which the title guard accepts.
- The change adds one unique changelog fragment. The constitution allows this in `changelog.d/`.
- The folder debt in `scripts/` is recorded above. A separate issue tracks the remediation after gate G-1.
- Product outputs stay under `data/`. The bootstrap produces no product output.

For a feature that uses Juniper Mist Cloud: not applicable.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/1/3/3/1/4591-locked-worktree-bootstrap/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      bootstrap-lock-cause.md
    checklists/
      requirements.md
      bootstrap-safety.md
```

### Source Code (repository root)

```text
scripts/bootstrap_worktree.py                    modify
scripts/bootstrap_worktree.ps1                   unchanged (passes -PublicLockIndex at line 68)
tests/unit/scripts/test_bootstrap_worktree_uv.py modify
documentation/development-setup.md               modify
changelog.d/issue-4591-locked-worktree-bootstrap.md add
```

**Structure Decision**: Edit existing files. Add one changelog fragment and the record. Add no module-level name to the bootstrap, so `symbol-diff` reports no module-level change. New helper code goes into a method of `InstallationPolicy`.

## Architecture

The locked bootstrap runs in this order. Each step names its location in `scripts/bootstrap_worktree.py` on `main`.

1. `main` (line 886) calls `WorktreeBootstrapper.sync_dependencies` (line 898).
2. `sync_dependencies` (line 565) reads the configured index through `PipIndexProbe.fallback_index`. The probe uses the public index for the run when the configured index does not answer.
3. `_install_environment` (line 636) copies the environment. `InstallationPolicy.apply` (line 404) clears the index variables and sets the child-only settings. `_effective_sources` (line 432) maps pip index settings into `UV_INDEX_URL` and `UV_EXTRA_INDEX_URL`.
4. `InstallationPolicy.sync` (line 462) runs `uv sync --locked --extra dev` (line 466).
5. On failure, `diagnose_sync_failure` (line 477) runs `lock_is_current` (line 495). The lock check runs `uv lock --check`. The stale phrase at line 153 decides the verdict.
6. The verdict compares the first registry source (`read_lock_registry`, line 325) with the primary configured index (`configured_index`, line 342). The result is index-mismatch, lock-drift, or the original error.
7. `main` prints the text `The bootstrap failed:` followed by the error (line 900), and it returns exit code 1.

## File-by-file Change Map

| Path | Action | Change | Requirement |
|---|---|---|---|
| `scripts/bootstrap_worktree.py` | modify | Remove the `UV_NATIVE_TLS` entry (line 417). Keep `UV_SYSTEM_CERTS` (line 418). Add a method on `InstallationPolicy` that lists the active index variable names. Use it in the index cause message (lines 136-139) and in an info log before the locked sync (lines 462-468). | FR-003, FR-004, FR-006 |
| `tests/unit/scripts/test_bootstrap_worktree_uv.py` | modify | Update the exact-text assertion for the index cause (lines 258-270). Add test cases TC-01 to TC-06. Keep TC-07 unchanged. | FR-003, FR-004, FR-006, FR-008 |
| `documentation/development-setup.md` | modify | Replace the requirements sentence at line 28. Update the option text at lines 65-66 with the two cause messages. Remove the `UV_NATIVE_TLS=1` row at line 73. Add the uv 0.11.0 minimum next to the table at lines 70-76. | FR-007 |
| `changelog.d/issue-4591-locked-worktree-bootstrap.md` | add | One `###` heading and one bullet under `Changed`. The bullet names issue 4591. | FR-009 |
| `specs/numbered/0/0/1/2/1/3/3/1/4591-locked-worktree-bootstrap/` | add | This record, committed with the change. | Process |

Not changed: `pyproject.toml`, `uv.lock`, `requirements.txt`, `requirements-dev.txt`, `scripts/bootstrap_worktree.ps1`, and `.github/workflows/*`.

## Test Cases

| ID | Case | Requirement | Before the change |
|---|---|---|---|
| TC-01 | The index cause message names the active index variable and keeps the stored message text. | FR-003, FR-004 | Fails |
| TC-02 | No index cause message contains `http`, a host name, or a credential-bearing value. | FR-003, SC-004 | Passes (guard) |
| TC-03 | An extra index variable appears by name only, with its value absent. | FR-004 | Fails |
| TC-04 | The child environment omits `UV_NATIVE_TLS` and keeps `UV_SYSTEM_CERTS` equal to `1`. | FR-006 | Fails |
| TC-05 | The active index variable names are logged before the locked sync starts. | FR-004 | Fails |
| TC-06 | The mapping of pip extra index settings into `UV_EXTRA_INDEX_URL` stays unchanged. | FR-003 | Passes (guard) |
| TC-07 | The public-lock-index option clears competing index variables (existing test). | FR-005 | Passes |

Regression checks: `tests/contract/packaging/test_bootstrap_compose_provider.py` (locked sync command), `tests/unit/scripts/test_browser_driver_bootstrap.py`, and `tests/unit/scripts/test_browser_download_certificates.py`.

Test design rules: use `ScriptedRun` and `monkeypatch`. Do not start uv or use the network. Do not read the real pip configuration. Use `tmp_path` for lock files.

## Dependencies

- No new package, tool, or file dependency.
- The change depends on gate G-1 (reporter data).
- The development setup document depends on the final cause message wording and the environment table.

## Risks and Mitigations

| ID | Risk | Mitigation |
|---|---|---|
| R-01 | A uv build older than 0.11.0 loses system certificate trust after `UV_NATIVE_TLS` is removed. | Document the minimum in `development-setup.md`. The project pin is uv 0.13.9. Record the residual risk in the pull request. |
| R-02 | The reporter data never arrives. | The change stays gated. The record stays complete, and the issue stays open. |
| R-03 | An index value reaches the output. | Add names only. TC-02 and TC-03 test the output. |
| R-04 | Extra-index-only failures keep the drift message. | The message names each active variable. Task T006 confirms the behavior. |
| R-05 | Another open pull request edits the bootstrap at the same time. | Run `gh pr list --json number,headRefName,files` before T-PR. Wait or coordinate when the bootstrap appears. |

## Rollback

1. Caution: do not delete a worktree `.venv` by hand. The deletion removes the installed packages. Run the bootstrap again to restore them.
2. Revert the squash commit with a new pull request. Do not force-push `main`.
3. The revert restores `UV_NATIVE_TLS`, the earlier message text, and the earlier documentation.
4. In a new worktree, run `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py` to confirm the restored behavior.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
|---|---|---|
| `scripts/` holds 58 direct children (grandfathered debt). | The bootstrap scripts already live here. | Moving them changes the documented entry points. A separate issue tracks the debt after gate G-1. |
| Module-level helpers in `scripts/bootstrap_worktree.py` (`read_lock_registry`, `configured_index`, `normalize_index`) are not class members (grandfathered debt). | Tests import these names. | Wrapping them in a class changes the test imports. The new helper is a class method. |
| `changelog.d/` holds 335 direct files (process folder). | One fragment is a required process record. | None. The constitution allows one unique fragment per change. |

## Verification

The applicable gates and their commands are listed in `design/quickstart.md`, section 4. The task `T-LOCAL-GATES` runs them.
