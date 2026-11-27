# Implementation Plan: Locked Bootstrap With a Configured Pip Index

**Branch**: `fix/4774-locked-bootstrap-pip-mirror` | **Date**: 2026-11-26 | **Spec**: `specs/numbered/0/0/1/2/3/0/4/4/4774-locked-bootstrap-pip-mirror/spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/3/0/4/4/4774-locked-bootstrap-pip-mirror/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Supporting artifacts sit under `design/`.

## Summary

The bootstrap maps the configured pip index into the uv primary index. The lock records only the public registry, so the locked sync reports a stale lock. The plan makes the locked sync use the registry that `uv.lock` records. The plan keeps `--locked`, leaves the lock unchanged, and logs a Caution when a configured index differs. The plan assumes option C for decision D-1.

## Technical Context

- **Language/Version**: Python 3.15 or newer (research.md, R45).
- **Primary Dependencies**: Python standard library. uv installs the locked environment (research.md, R09). The bootstrap calls no Mist API (research.md, R41).
- **Storage**: None. A source decision exists in memory for one run only.
- **Testing**: pytest unit tests under `tests/unit/`. Guard tests under `tests/guardrails/`.
- **Target Platform**: Windows 11 owner host. The change keeps the same code path on each platform.
- **Project Type**: Command-line script in `scripts/`.
- **Performance Goals**: None. The change adds no network request. The run keeps one locked sync.
- **Constraints**: No change to `uv.lock` or the dependency manifests (D-2). ASCII output (research.md, R19). Simplified Technical English text (research.md, R02).
- **Scale/Scope**: One script of 914 lines, three test files, one guide, and one changelog fragment.

## Constitution Check

Gate result: pass, with one recorded pre-existing violation and one recorded pre-existing drift. Each rule cites its research row.

| Rule | Result | Reason |
| - | - | - |
| Principle I, Five-Item Rule (R14) | Pass for the new record. Fail, pre-existing, for the module. | Record holds five or fewer children per level (R76). Module holds five classes and twelve functions (R40), and this change adds none. Remediation: D-11. |
| Principle II, Class-Based Architecture (R15) | Pass | Changes stay inside `WorktreeBootstrapper.InstallationPolicy`. No wrapper function is added. |
| Principle III, Safety-First (R17) | Pass | The change adds no input and no destructive action. The Caution text names no URL or credential (FR-004, FR-017). |
| Principle IV, Full Deployment Pipeline (R18) | Pass, planned | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE follow the pipeline. No task pushes to main. |
| Principle V, ASCII-only logs (R19) | Pass, planned | New log and message text uses ASCII characters only. |
| Principle VI, Inline comments (R20) | Pass, planned | Each changed executable line gets a comment on the same line. |
| Principle VII, Action logging (R21) | Pass, planned | The registry read and the Caution path write an info line before the action and a debug line after it. |
| Technology and compatibility (R22) | Pass | Python 3.15 (R45). uv performs the sync (R09). mistapi is not used (R41). No container starts, so Podman rules do not apply. |
| Security findings (R23) | Pass | The change adds no `# nosec`, `# noqa`, or `# type: ignore` comment. |
| Documentation (R24) | Pass, planned | The development guide and the module docstring change in the same pull request (D-7). |
| Complexity-driven SpecKit escalation (R25) | Pass | Three or more files need a specification. This record is that specification. |
| Multi-agent git workflow (R26) | Pass, planned | Issue #4774 exists. Label `in-progress` is set at claim time (D-13, R12). No open pull request changes a planned path (research.md, section 4). |
| Specs roots and route (R16, R10) | Pass | The record uses the managed root `specs/numbered/` and the route `0/0/1/2/3/0/4/4`. The route function gives this route for 4774 (R73, R74). |
| mistapi version rule (R27) | Fail, pre-existing drift | The constitution states 0.59 or newer. The pin states 0.64.1 (R47). This change does not alter either value. Remediation is D-11. |

## Architecture

Current flow at main (research.md, section 5):

1. The pip probe decision for the pip steps stays unchanged.
2. `InstallationPolicy.apply` clears the uv index variables and calls `_effective_sources` (R34).
3. `_effective_sources` sets `UV_INDEX_URL` to the configured primary index (R35).
4. `sync` runs `uv sync --locked --extra dev` (R36).
5. A failed sync reports an index mismatch when the configured index differs from the lock registry (R38).

New flow with option C:

1. The probe keeps its existing pip decision (unchanged).
2. `apply` keeps the removal of the uv index aliases. It no longer maps any configured index into uv.
3. `sync` reads the lock registry (R31). It fails closed when no registry exists. It sets `UV_INDEX_URL` to the registry. It logs one Caution line when the configured index differs.
4. A failed sync names lock drift only (R38 is removed).
5. `--public-lock-index` keeps its path and sets the public index (R33, R39).

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/0/4/4/4774-locked-bootstrap-pip-mirror/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      bootstrap-source-policy.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
scripts/
  bootstrap_worktree.py        (modified)
  bootstrap_worktree.ps1       (unchanged)
tests/unit/config/foundation/runtime/startup/bootstrap/dependency/
  test_uv_locked_sync.py       (modified)
tests/unit/scripts/
  test_bootstrap_worktree_uv.py (modified)
documentation/
  development-setup.md         (modified)
changelog.d/
  issue-4774-locked-bootstrap-pip-mirror.md (added)
```

**Structure Decision**: Keep the change inside the existing bootstrap script and its two test files. Add one changelog fragment. The record folder holds the design. No new source package is created.

## File-by-File Change Map

Line numbers refer to main commit f03c6c9b. The implementer rechecks each line before editing.

| Path | Action | Main lines | Change |
| - | - | - | - |
| `scripts/bootstrap_worktree.py` | Modify | 20 | Replace the docstring sentence about the stop on index mismatch (R28). |
| `scripts/bootstrap_worktree.py` | Delete | 136 | Remove `INDEX_MISMATCH_MESSAGE` (R30). |
| `scripts/bootstrap_worktree.py` | Modify | 325-334 | `read_lock_registry` returns the first registry line (R31). The caller fails closed when it returns None. |
| `scripts/bootstrap_worktree.py` | Delete | 342-347 | Remove `configured_index` (R32). The Caution check uses the pip sources directly. |
| `scripts/bootstrap_worktree.py` | Modify | 404-425 | `apply` keeps the alias removal (R92) and the `UV_NO_CONFIG` setting (R90). Remove the call at line 425 (R34). |
| `scripts/bootstrap_worktree.py` | Delete | 432-447 | Remove `_effective_sources` (R35). |
| `scripts/bootstrap_worktree.py` | Modify | 462-475 | `sync` sets `UV_INDEX_URL` to the lock registry, fails closed when no registry exists, logs the Caution line, then runs the locked sync (R36). |
| `scripts/bootstrap_worktree.py` | Modify | 477-493 | `diagnose_sync_failure` removes the index-mismatch branch (R38). It returns the lock drift message for a stale lock. |
| `scripts/bootstrap_worktree.py` | Modify | 679-683 | The `--public-lock-index` help text describes the default (R39). |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` | Modify | 203-219 | Rewrite TST-07 (R51). |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` | Modify | 220-241 | Rewrite TST-08 (R53). Remove the `UV_INDEX_URL` assertion at the apply level. Keep the pip and alias assertions. |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` | Modify | 131-163 | Rewrite TST-09 (R55). The second invocation receives the lock registry, not an absent setting. |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` | Delete | 336-357 | Remove the precedence test (R52). TST-01 replaces it. |
| `tests/unit/config/foundation/runtime/startup/bootstrap/dependency/test_uv_locked_sync.py` | Add | After 357 | Add TST-01 and TST-02. |
| `tests/unit/scripts/test_bootstrap_worktree_uv.py` | Modify | 25 | Remove the `INDEX_MISMATCH_MESSAGE` import (R56). |
| `tests/unit/scripts/test_bootstrap_worktree_uv.py` | Delete | 258-270 | Remove the mismatch test (R57). |
| `tests/unit/scripts/test_bootstrap_worktree_uv.py` | Add | End of file | Add TST-03, TST-04, TST-05, and TST-06. |
| `documentation/development-setup.md` | Modify | 61-66 | Replace the stop-on-mismatch paragraph and the opt-in text (R66). |
| `documentation/development-setup.md` | Modify | 95-106 | Rewrite the Package sources section (R67, R68). The mistapi row at line 14 (R89) stays unchanged for D-11. |
| `changelog.d/issue-4774-locked-bootstrap-pip-mirror.md` | Add | Not applicable | One fragment with one `###` heading and one bullet (R65). |
| `specs/numbered/0/0/1/2/3/0/4/4/4774-locked-bootstrap-pip-mirror/` | Add | Not applicable | This record. |
| `test-artifacts/issue4774/` | Add, not committed | Not applicable | Scratch output for the quickstart. Git ignores `/test-artifacts/` (R71). |
| `scripts/bootstrap_worktree.ps1` | No change | 68 | The wrapper passes the option through (R42). |
| `uv.lock`, `pyproject.toml`, `requirements.txt`, `requirements-dev.txt` | No change | Not applicable | D-2. |
| `.github/workflows/ci.yml`, `.github/workflows/container-build.yml` | No change | 648, 95 | The guards stay valid (R61, R63, R64). |
| `src/foundation/runtime/bootstrap/` | No change | Not applicable | No index mapping exists there (R93, D-8). |
| `.github/copilot-instructions.md` | No change | 36 | The statement about `uv sync --locked --extra dev` stays accurate (R09). |

Caution: after the edit, the module-level names `INDEX_MISMATCH_MESSAGE` and `configured_index` disappear. The symbol gate reports them. The pull request records the exception (D-9).

## Dependencies

- No new package. No change to a dependency manifest.
- Owner decision D-1 gates T011 through T015. The tests in T004 through T010 assume option C. Re-plan when the owner selects another option.

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
| - | - | - | - |
| Caution: public PyPI is blocked on the owner host. The locked sync fails with a network error. | Medium | High | The Caution line (FR-004) and the guide text (FR-013) explain the rule. The owner check (SC-002) confirms the host. |
| The owner selects option A, B, or P. | Medium | Medium | The plan stops at T011. The tests and the file map change before code starts. |
| Caution: a future lock names a second registry. | Low | High | TST-05 fails in the repository. `read_lock_registry` reads the first line only (R31). |
| The symbol gate reports the removed names. | High | Low | The pull request records the exception (D-9). |
| Caution: a test outside the planned set asserts the old mapping. | Medium | Low | T-LOCAL-GATES runs the full unit suite before the pull request. |
| Caution: uv behaves differently from the owner report. | Medium | Medium | The quickstart reproduces the child environment (Q3). SC-002 records the owner result. |
| Warning: a credential reaches a log through the Caution path. | Low | High | TST-02 and TST-03 check for redaction. FR-017 forbids any URL in the Caution text. |

## Rollback Steps

1. Revert the squash commit with a new pull request. Do not force push. Warning: a force push replaces remote history and cannot restore it.
2. Confirm that `scripts/bootstrap_worktree.py` has blob `e16515ffa789cca7d0bdd7e9789898588e5f1312` on main after the revert (R28 and R86).
3. Caution: a failed sync leaves an incomplete `.venv`. Run `uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py --recreate` in each affected worktree.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| `scripts/bootstrap_worktree.py` holds 17 top-level names (R40). | The file predates this change. The fix touches one class and its helpers. | Splitting the module in this change adds unrelated churn. D-11 tracks the split as a separate issue. |

## Contracts

The CLI and the child environment have a contract. The contract file is `design/contracts/bootstrap-source-policy.md`. The folder holds one file, which is within the limit of five.
