# Implementation Plan: Development setup installer text

**Branch**: `fix/4879-development-setup-installer` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Issue #4879 and the specification in this folder. The repository record folder is `specs\numbered\0\0\1\2\4\0\0\4\4879-development-setup-installer`.

Keep `spec.md`, `plan.md`, `tasks.md`, and `analysis.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

The guide describes a requirement-file install. The bootstrap runs one locked sync from `uv.lock`, and it runs no requirement-file install. This change edits the installer text of `documentation/development-setup.md` and adds one changelog fragment. It changes no script, test, workflow, or configuration file. Section 3 of `design/contracts/bootstrap-installer-flow.md` lists the settings that the guide must name.

## Technical Context

**Language/Version**: Markdown in Simplified Technical English. The bootstrap stays on Python 3.15 (`scripts/bootstrap_worktree.py` line 54).

**Primary Dependencies**: None added. The STE gate uses `ste-linter` from `misthelper-devtools`, pinned in `requirements-dev.txt` line 197.

**Storage**: None.

**Testing**: The local STE gate, the existing guard `tests/guardrails/test_container_policy_docs.py`, and the checks TST-001 to TST-010 in `design/quickstart.md`.

**Target Platform**: The guide is read on Windows 11, macOS, and Linux.

**Project Type**: A documentation correction in one existing file, plus one changelog fragment.

**Performance Goals**: Not applicable. The change alters no runtime path.

**Constraints**: Instructions hold 20 words or fewer. Descriptions hold 25 words or fewer. The text uses no semicolon, contraction, Latin abbreviation, or phrasal verb. The spelling is American. Each file scores 80 or above.

**Scale/Scope**: Four sections of one file, and one new fragment.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes.*

| Rule | Result | Reason |
|------|--------|--------|
| I. Five-item rule | Pass | The record root holds five children. The repository change adds no directory. |
| II. Class-based architecture | Not applicable | The change holds no code. |
| III. Safety first | Pass | The guide keeps its existing Warning and Caution statements. The change adds no destructive command. |
| IV. Full deployment pipeline | Pass with a note | Steps 1 to 9 apply. Steps 10 to 12 do not run, because `container-build.yml` triggers on product paths only (R-42). |
| V. Observability and logging | Not applicable | The change alters no log code. |
| VI. Inline comments | Not applicable | The change holds no executable code. |
| VII. Action logging | Not applicable | The change holds no executable code. |
| Technology: UV and pip | Pass | The guide keeps the pip export files and the manual pip path. |
| Technology: Podman | Pass | The container sections stay unchanged. |
| Technology: data directory | Pass | No product output changes. |
| Documentation: README | Not applicable | The change alters no operation and no behavior. |
| Release notes | Pass with the fragment | D-8 adds one fragment, as line 409 requires. |
| Complexity-driven escalation | Pass | A documentation-only change may run directly. This record is a spec by request. |
| Multi-agent git workflow | Pass | The branch name follows the MistHelper rule. No open pull request touches the three target files. The labels are `bug`, `in-progress`, and `docs`. |
| Mist Cloud transport | Not applicable | The change calls no Mist REST or WebSocket endpoint. |

For repository structure and generated files:

- The commit subject and the pull request title use the Conventional Commit form.
- The change adds the guide and one fragment only.
- The change records no existing folder debt, because it adds no direct child to a noncompliant parent.

## Architecture

The guide describes the flow of `scripts/bootstrap_worktree.py`. No code path changes. The flow below uses line numbers from `main` at commit `f03c6c9b`.

```text
Step 2 of documentation/development-setup.md
  scripts/bootstrap_worktree.py
    1. Create .venv when it is absent (line 549)
    2. Read pip configuration and probe the configured index (lines 179 and 86)
    3. Find uv: PATH, per-user folders, bootstrap module (lines 300 to 313)
    4. Install uv with pip when no uv executable exists (lines 455 to 457)
    5. Run uv sync --locked --extra dev in an installer child process (line 466)
    6. Run the health check, browser download, report, and account checks (lines 902 to 907)
```

## Project Structure

### Documentation (this feature)

```text
specs\numbered\0\0\1\2\4\0\0\4\4879-development-setup-installer\
  spec.md
  plan.md
  tasks.md
  analysis.md
  design\
    research.md
    data-model.md
    quickstart.md
    contracts\
      bootstrap-installer-flow.md
    checklists\
      requirements.md
```

### Source Code (repository root)

```text
documentation\development-setup.md                          # modify: Step 2, installer section, Package sources, Browser and account checks
changelog.d\issue-4879-development-setup-installer.md       # add: one fragment
```

**Structure Decision**: Two repository files change. The guide keeps its headings and its section order. The fragment name follows the rule for an open issue in `changelog.d/README.md` (line 27).

## File Change Map

The line numbers refer to `documentation/development-setup.md` on `main` (blob `1733975a7e0a0962fe5367e165a21f5831f8c3e5`). The target text must be applied as written, or with a change that keeps each rule of the spec.

| ID | Location (main lines) | Action | Target text | Requirement | Evidence |
|----|-----------------------|--------|-------------|-------------|----------|
| M-01 | Step 2, lines 28 and 29 | Modify | "The bootstrap script creates `.venv` when it is absent, then runs `uv sync --locked --extra dev`. The locked sync installs the versions that `uv.lock` records, with the `dev` extra from `pyproject.toml`. Use Python 3.15 or newer to run the script." | FR-001, FR-002 | R-03, R-11, R-15, R-39 |
| M-02 | Installer section, line 59 | Modify | "It installs `uv` with pip for this user only when no uv executable exists." | FR-003 | R-19 |
| M-03 | Installer section, after line 61 | Add | "The locked sync runs from the repository root with `uv sync --locked --extra dev`. The command stops when `uv.lock` needs an update." | FR-001 | R-11, R-15 |
| M-04 | Installer section, after line 64 | Add | "When `uv.lock` does not match `pyproject.toml`, the final message tells you to run `uv lock` on a branch." | FR-003 | R-25 |
| M-05 | Installer section, line 68 | Modify | "Each installer child process receives these settings:" | FR-005 | R-20, R-21 |
| M-06 | Settings table, lines 72 to 75 keep, rows added after line 75 | Add | Add eight rows for the settings that the table lacks: UV_HTTP_RETRIES, UV_HTTP_TIMEOUT, UV_INDEX_URL, UV_EXTRA_INDEX_URL, PIP_RETRIES, PIP_TIMEOUT, PIP_INDEX_URL, and PIP_CONFIG_FILE. The uv defaults are three retries and 30 seconds. The pip defaults are five retries and 15 seconds. | FR-005 | R-10, R-20, R-21, R-22, R-32, R-33 |
| M-07 | Lines 77 and 79, and after line 81 | Modify and add | Line 77: "The bootstrap removes `UV_CONFIG_FILE` from each installer child process." Line 79: "Each child process receives its own copy of the caller environment." Added: "When pip installs uv, the child process also removes `PYTHONNOUSERSITE`." | FR-005 | R-19, R-20 |
| M-08 | Report paragraph, lines 83 to 87 | Modify, delete, add | Keep "Actual duration depends on caches, storage, and network conditions." Delete the sentences on each attempted file, total installation time, and no requirement files. Add: "After a successful run, the report prints `Installed dependencies with uv sync --locked --extra dev.` and names the pip export files." Add: "Each command reports its elapsed time to one decimal place, including a failed command." Add: "The report names the interpreter and the activation command." | FR-002, FR-006 | R-06, R-07, R-08, R-16, R-17 |
| M-09 | After the report paragraph, after line 87 | Add | "The two pip export files, `requirements.txt` and `requirements-dev.txt`, serve manual pip installs. The bootstrap installs neither file." | FR-007 | R-17 |
| M-10 | Caution paragraph, line 91 | Modify | "It does not retry a failed uv command through pip." | FR-002 | R-19 |
| M-11 | Package sources, lines 103 and 104 | Delete and modify | Delete line 103 ("Extra-source order remains unchanged."). Line 104: "The bootstrap removes competing uv source aliases only from installer child processes." | FR-002, FR-005 | R-09, R-32 |
| M-12 | Package sources, lines 109 to 111 | Modify | Line 109 and line 110: "When the public index applies, each installer child process sets `PIP_CONFIG_FILE` to the platform null device. Pip then loads no configuration file, so a saved extra index cannot restore the failed mirror." Line 111: "`UV_NO_CONFIG=1` stops uv from reading saved configuration files, so a saved uv setting cannot restore the failed mirror." | FR-005 | R-20, R-22 |
| M-13 | Package sources, lines 115 to 117 | Delete and modify | Delete lines 115 and 116 (the table names these settings). Line 117: "These settings stay in each child process and do not change caller settings." | FR-005 | R-20, R-21 |
| M-14 | Browser and account checks, lines 122, 124, and 125 | Modify and delete | Line 122: "After dependency installation succeeds, the bootstrap runs the health check, the browser download, the report, and the account checks." Line 124: "The browser child process receives no uv setting and no `PIP_CONFIG_FILE` setting. It still receives `PIP_RETRIES` and `PIP_TIMEOUT`." Delete line 125. | FR-002, FR-005 | R-21, R-26, R-27, R-28 |
| M-15 | Browser and account checks, line 127 | Modify | "The bootstrap sets the repository credential username to `jmorrison-juniper`." | FR-002 | R-29 |
| M-16 | Installer section, lines 57, 58, 60, 63, 64, 65, and 66 | Keep | No change. These lines hold the uv discovery order, the install refusal, the lock message, and the public index option. | FR-003, FR-004 | R-18, R-19, R-23 |
| M-17 | Repository path `changelog.d\issue-4879-development-setup-installer.md` | Add | One heading that names the setup guide change, and one bullet: "- **Fixed**: The setup guide names `uv sync --locked --extra dev`, the install command that the bootstrap runs. Issue #4879." | FR-009 | R-41, R-44 |
| M-18 | Lines 17, 132 to 144, 264 and 265, and 355 | Keep | No change. The manual install path, the dev extra claim, and the browser package claim stay. | FR-001 (scope) | R-12, R-13, R-40 |

## Dependencies

- No package is added or changed.
- The STE gate requires `.venv\Scripts\ste-linter.exe` from the environment that `scripts/bootstrap_worktree.py` creates in the worktree.
- The guard test requires the same environment.

## Risks and Mitigations

| Risk | Effect | Mitigation |
|------|--------|------------|
| The current STE score of the guide is unknown (U-1). | The edited guide may score below 80. | Run TST-001, and repair each finding until each file scores 80 or above. |
| The settings table grows to twelve rows. | A junior engineer finds the table hard to scan. | Keep one row for each setting, and use plain words in each purpose. |
| The wording drifts from the script again. | The guide describes a flow that the script no longer runs. | Use `design/contracts/bootstrap-installer-flow.md` as the check list. Add a guard in a follow-up issue (D-6). |
| A reader confuses the manual path with the bootstrap. | A reader installs with pip and expects the lock. | Keep the heading "To build the environment by hand instead" (D-2). |
| The changelog name changes after the pull request opens. | The release coordinator sees a delete and an add (`changelog.d/README.md` line 32). | Keep the name `issue-4879-development-setup-installer.md` when the pull request opens. |

## Rollback

1. Before merge, close the pull request without merging, and delete the branch `fix/4879-development-setup-installer`.
2. After merge, revert the squash commit on `main` through a new pull request. The revert restores the previous guide text and removes the fragment.
3. No data, runtime state, or container image changes. No migration is needed.

## Complexity Tracking

Not applicable: the Constitution Check holds no violation. Decision D-8 resolves a conflict between the constitution (line 409) and the changelog README (line 58), and the research record states the reason.
