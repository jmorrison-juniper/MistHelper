# junk

Retired files. Nothing here is read by shipped code, by a workflow, or by a test.

The folder exists so that a finished work product can leave the repository root
without losing its history. `git log --follow junk/<file>` still reaches the
original commits.

`.dockerignore` excludes `junk/`, so nothing here enters a container build
context. The wheel names its contents explicitly in `pyproject.toml`, so nothing
here can be packaged either.

## What belongs here

A file that is finished, generated, or was written once to answer a single
question. A stale report, a captured build log, a one-off diagnostic script, a
throwaway Dockerfile, a commit message draft.

## What does not belong here

Anything a gate reads, anything a test imports, and anything a reader needs in
order to understand current behavior. Delete dead code instead of retiring it;
history already holds it.

## Contents

| File | Origin |
| - | - |
| `.cm1802.txt` | A commit message draft for issue #1802. |
| `HANDOFF.md` | A run handoff note for the fiber and device catalog work. |
| `PHASE1_COMPLETION_REPORT.md` | A historical status report for issue #1823. Current facts live in `src/upgrade_portal/` and `specs/1823-upgrade-capture-portal/`. |
| `PHASE1_EXECUTION_REPORT.md` | A historical status report for the Plotly map templates. Current files are `src/maps/plotly_map_templates.py` and `tests/maps/test_plotly_map_templates.py`. |
| `refactor_candidates.md` | A generated analyzer report. `specs/1014-misthelper-refactor-hot-classes-with-src-callers/plan.md` records that this catalog is local-only and must not sit in the branch state. The generator now lives in the external devtools package. |
| `pip_audit_report.json` | Generated scanner output. The `pip-audit` gate regenerates it in CI. |
| `build-output.txt` | A captured 54-step container build log. |
| `diag_rbo.py` | A one-off diagnostic that printed audit delta internals for one network template. |
| `Dockerfile.diagnostic` | A throwaway image that only checked whether `snmpd` installs. |
| `Dockerfile.test` | A throwaway image with a bare shell entry point. |
| `test_input.txt` | Two lines of scratch menu input. |

`artifacts/` holds untracked local scratch, such as coverage logs and packet
captures. `.gitignore` excludes it.
