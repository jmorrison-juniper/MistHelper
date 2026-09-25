# Implementation Plan: Move the Starlink dashboard to its own repository

**Issue**: #3403 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Extract the history of the dashboard files into a new public repository. Add a
README, a license, two requirements files, and a CI workflow there. Then delete
the two files from MistHelper, and remove each gate setting and tool default
that names them.

## Technical context

- **Language**: Python 3.13.
- **Tools**: `git-filter-repo` through `uvx`, the GitHub CLI, pytest, and ruff.
- **Storage**: none changes.

## Constitution check

- **Safety**: no menu operation, container, or portal uses the dashboard. No
  cloud call and no firmware write change.
- **5-Item Rule**: the change adds no code to MistHelper.
- **STE**: every new text passes the STE linter at 80 or more.

## Files

| File | Change |
| - | - |
| `starlink_dashboard.py` | Delete. The file moved to the new repository. |
| `tests/unit/test_starlink_dashboard_startup_and_gps.py` | Delete. The test moved with the file. |
| `.github/workflows/ci.yml` | Remove the file from `RADON_PATHS`, `VULTURE_PATHS`, and `INTERROGATE_PATHS`. Update three comments. |
| `pyproject.toml` | Remove the mypy exclude, and record the removal in the comment. |
| `quality_gate_exclusions.json` | Remove the mypy entry for the file. |
| `.dockerignore` | Remove the three Starlink rules. |
| `.gitignore` | Remove the `starlink-api-reference/` rule. |
| `tools/compliance_analyzer/engine.py` | Remove the folder from `_DEFAULT_EXCLUDES`. |
| `tests/unit/test_compliance_analyzer.py` | Remove the folder sample from the exclusion test. |
| `tests/test_issue_433_src_g_no_regress.py` | Remove the file from `TARGET_PATHS`. |
| `changelog.d/issue-3403-starlink-split.md` | Add the release note. |

## Order of work

1. Merge pull request #3405 for issue #3320 first. This change edits `ci.yml`,
   so the ratchet runs the full gate.
2. Create the new repository, push the history, and verify the README steps in
   a new clone.
3. Delete the two files in MistHelper, and edit the settings.
4. Run every local gate. Rebase onto main, and then open the pull request.
5. After the merge, move the ignored `starlink-api-reference/` folder from the
   main checkout to a backup location. Do this step before the fast-forward.

## Risks

- **A gate names a missing path.** Vulture and interrogate fail on a missing
  path. The change removes the file from both lists in the same commit.
- **An untracked folder in the main checkout.** After the merge, the main
  checkout still holds the ignored clone. Step 5 moves the folder before the
  fast-forward, so no `git add` can commit it.
