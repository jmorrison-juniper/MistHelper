# Implementation Plan: Correct interactive two-factor login notes

**Branch**: `docs/4759-two-factor-login-note` | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric record at `specs\numbered\0\0\1\2\3\0\1\4\4759-two-factor-login-note`. The route uses the base-5 digits of 4759, which are 0 0 1 2 3 0 1 4. The route rule is in `.github/copilot-instructions.md` lines 159 to 161 (RC-46).

## Summary

The corrected two-factor note is already on `main`. The release-note fragment is missing. This plan adds one fragment, keeps both verified notes, and holds publication until the owner gives a new instruction.

## Technical Context

**Language/Version**: Markdown. The Python 3.15 test runner does not change.

**Primary Dependencies**: None added. The gates use `ste-linter` from `misthelper-devtools` and `pytest`.

**Storage**: Not applicable.

**Testing**: The STE gate and `tests/guardrails/test_changelog_fragment_policy.py`, which holds 18 test functions (RC-36).

**Target Platform**: Repository content, read on Windows, macOS, and Linux.

**Project Type**: Documentation change with one release-note fragment.

**Performance Goals**: Not applicable.

**Constraints**: STE score of 80 or above (RC-48). The fragment naming rule (RC-37). The owner hold (RC-56).

**Scale/Scope**: One fragment file added. Two notes verified. No other file changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Gate results, from `.specify/memory/constitution.md` (RC-50, RC-51):

- **Principle I, Five-Item Rule**: Pass with recorded debt. `changelog.d/` holds 335 entries on `main` (RC-59). The principle permits unique process records in that folder. This change adds one record. Remediation is a separate issue.
- **Principle II, Class-Based Architecture**: Not applicable. The change adds no code.
- **Principle III, Safety-First**: Not applicable. The change adds no input handling.
- **Principle IV, Full Deployment Pipeline**: Pass with mapping. Steps 1 to 12 map to T-LOCAL-GATES (step 1), T-PR (steps 2 to 7), T-REMOTE-CI (step 8), and T-MERGE (steps 9 to 12).
- **Principle V, Observability and Logging**: Not applicable. The change adds no log output.
- **Principle VI, Inline Comments**: Not applicable. The change adds no code.

Repository structure and generated files:

- The commit subject and pull request title use `docs(api): correct two-factor login note`. This form matches the Conventional Commit rule in Principle IV, step 4, and the title rule (RC-62).
- The change adds only its own unique fragment, as Principle I and the release-note rule require (RC-64).
- The record folder sits under the managed route `specs/numbered/` (RC-46, RC-47).
- Product outputs under `data/`: not applicable.

Mist Cloud contract checks:

- The change adds no REST request. The SDK evidence appears in RC-04 to RC-09.
- The wrong SDK path on the two-factor page is a finding in `analysis.md`. This change does not repair it.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/3/0/1/4/4759-two-factor-login-note/
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

The `design/contracts/` folder is omitted. No interface contract applies to a prose change.

### Source Code (repository root)

```text
documentation/api/admins/POST_login_two_factor.md   verified present, no change in this branch
documentation/api/admins/POST_login.md              verified present, no change in this branch
changelog.d/issue-4759-two-factor-login-note.md     new
```

**Structure Decision**: One new fragment and one record folder. The two notes stay as they are on `main`, pending the owner review in `analysis.md`.

## File Change Map

| Path | Action | Task | Reason |
| - | - | - | - |
| `documentation/api/admins/POST_login_two_factor.md` | Keep, verified present | T001 | Corrected note at blob `98aeb3e8`, line 91 (RC-02) |
| `documentation/api/admins/POST_login.md` | Keep, verified present | T002 | Note changed by pull request #4924, line 122 (RC-34) |
| `changelog.d/issue-4759-two-factor-login-note.md` | Add | T003 | Release-note fragment (FR-005) |
| `specs\numbered\0\0\1\2\3\0\1\4\4759-two-factor-login-note\` | Add | Record | This record, committed with T-PR |
| `README.md` | No change | T004 | FR-006 |
| `CHANGELOG.md` | No change | T004 | FR-006 |

## Dependencies

No new dependency. The gates use `ste-linter` and `pytest` from the project environment. The `gh` command reads pull request state. Installed `mistapi` stays at 0.64.1 (RC-05).

## Gate Applicability

Each gate name comes from the Local gates table in `.github/copilot-instructions.md` (lines 50 to 74).

| Gate | Applies | Reason |
| - | - | - |
| Compile, Lint, Format, Types | No | No Python file changes |
| Tests | Yes | The changelog guard test runs in CI (RC-41) |
| Full tests, Coverage, Test quality | No | No code or test file changes |
| Safe sweep, Menu reference | No | No menu or operation change |
| Complexity, Security lint, Dependency audit, Code quality, Dead code, Docstrings, Symbols | No | No Python file changes |
| STE | Yes | The changed files are Markdown (RC-49) |
| Ops portal, Ops platform | No | No npm or ops file change |

## Risks

| Risk | Effect | Mitigation |
| - | - | - |
| The owner hold stays active | Caution: publication lacks owner authority | T-PR, T-REMOTE-CI, and T-MERGE wait for a new owner instruction (D-7) |
| A stale branch restores the old note | Caution: the false statement returns to main | Rebase onto `main` before the commit. Check line 91 after the rebase (RC-02) |
| The fragment name changes after the pull request opens | Caution: a reviewer reads the change as a conflict | Keep the name chosen in T003 (D-3) |
| The STE score drops below 80 | The gate fails | Repair the prose and run the gate again (RC-48) |
| Pull request #4924 stays unlinked | Caution: ownership stays unclear | Link pull request #4924 in the T-PR body. The owner reviews it (`analysis.md` A-2) |
| A push uses another account | Caution: the push lands under another identity | Clear `GH_TOKEN` and `GITHUB_TOKEN`, then run `gh auth switch --user jmorrison-juniper` (RC-67) |
| The candidate fragment cannot be found | Caution: the earlier text is lost | Write the fragment from `spec.md` (T003) |

Warning: a squash merge to `main` cannot be undone without a new pull request. Merge only after the owner authorizes it.

## Rollback

1. Before T-PR, delete the local branch and the fragment file. `main` stays unchanged.
2. After T-PR and before the merge, close the pull request and delete its branch. Do not force-push `main`.
3. After the merge, open a new pull request that edits the fragment text.

Caution: a revert of the note restores the false statement on `main`. Do not revert the note unless the owner decides so (D-1).

## Constitution Re-check After Design

Pass. The design adds no code, no REST request, and no log output. The Principle IV mapping remains complete.
