# Implementation Plan: Site read refusal

**Branch**: `jmorrison-juniper-fix-org-upgrade-cloud-read` (merged) and `<type>/3393-site-read-refusal` for the follow-up work | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/0/2/0/3/3/3393-site-read-refusal/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

The repair for issue 3393 is on `main` (PR 4413). The save, the options page, and the confirmation page catch `RequestException` and answer 503. Source reading shows that the SDK does not raise that exception for these reads. The follow-up work adds one contract test that proves the production answer (T008). It also adds the inline comments that the constitution requires (T007). No behavior changes in this plan unless T008 proves a different answer.

## Technical Context

**Language/Version**: Python 3.15 or newer (`pyproject.toml` line 23, RC-58).

**Primary Dependencies**: Flask 3.1.3, requests 2.34.2, and mistapi 0.64.1 (`requirements.txt` lines 129 and 221, RC-59).

**Storage**: The durable run store and the signed browser session. No schema change.

**Testing**: pytest contract tests, unit tests, and Playwright browser tests. The browser stack is in `documentation/development-setup.md` section "Run the browser tests" (RC-62).

**Target Platform**: Windows 11, macOS, and Linux. The Podman container runs the same code.

**Project Type**: A Flask portal inside an existing repository.

**Performance Goals**: No new cloud request. The new handlers run only in the exception path.

**Constraints**: No firmware write. No change to the SDK, the credential handling, or the storage schema.

**Scale/Scope**: One save route, two page routes, one residual retry caller (out of scope).

## Constitution Check

The constitution is version 1.9.0 (RC-48). Each rule has a result and a reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass | The record folder holds five children or fewer at each level. The record sits under the numbered route, which holds one child (RC-45). The grandfathered debt in `org_upgrade.py` and the test and changelog folders is listed in Complexity Tracking. |
| II. Class-based architecture | Pass | The change adds comments and one test module case. It adds no wrapper function and no class. |
| III. Safety first | Pass | The refusal envelope holds no transport text (RC-37). Each handler logs the exception class only (`org_upgrade.py` lines 1148, 1228, and 1351). |
| IV. Full deployment pipeline | Open | The local gates, the pull request, the remote CI, and the merge are open tasks (T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE). The check rollup of PR 4413 reports no failure (analysis, remote state). |
| V. Observability and logging | Pass | Log messages use ASCII. No secret reaches a log line. |
| VI. Inline comments | Fail | Eleven added lines carry no inline comment (`org_upgrade.py` lines 230, 231, 1147 to 1149, 1227 to 1229, and 1350 to 1352). T007 fixes the lines. |
| VII. Action logging | Pass with note | Each handler logs an error with the exception class. The site list read logs before and after the call (`org_upgrade.py` lines 517 and 525). |
| Technology: Python | Pass | The project requires 3.15 or newer (RC-58). |
| Technology: mistapi | Pass | The reads call mistapi functions (RC-66 and RC-68). No direct HTTP call exists in the path. |
| Technology: Podman | Pass | No container starts in this record. |
| Technology: file paths | Pass | The change adds no path code. |
| Technology: outputs, store, keys, and data directory | Not applicable | The change adds no output, store, endpoint strategy, or data file. |
| Development workflow: menu operations | Not applicable | No menu operation changes. |
| Security findings | Pass | No security finding is open for this change. |
| Documentation: README | Pass with note | The README names no refusal (RC-34). Analysis A-9 records the decision. |
| Documentation: release notes | Pass | The fragment `changelog.d/issue-3393-site-read-refusal.md` exists (RC-44). |
| Audience standard | Pass | The refusal sentence uses plain English. |
| Complexity-driven escalation | Pass | This record is the specification. The change touches one code file and one test file. |
| Pull request title | Open | T-PR uses a Conventional Commits title. |

For repository structure and generated files:

- The commit subject and the pull request title use the Conventional Commits form.
- The record lands in its own documentation pull request. The code pull request carries no record file.
- The record counts existing folder debt in Complexity Tracking.
- Test output stays in `tmp_path`. Product output stays under `data/`.

For a feature that uses Juniper Mist Cloud:

- Every REST request uses a mistapi method (RC-66 and RC-68).
- No owned WebSocket transport exists in the path.
- The contract tests cover failure handling, safety, output, and redaction. T008 adds the production-path case.
- Treat the open T008 proof as a gate for any further code change.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/0/2/0/3/3/3393-site-read-refusal/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      refusal.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py   # the handlers and the 503 constants
src/interfaces/portals/upgrade_portal/app/routes/select.py        # the site list read (unchanged)
src/interfaces/portals/upgrade_portal/app/factory.py              # the 500 text (unchanged)
src/interfaces/portals/upgrade_portal/upgrade/org_site_records.py # the unread-site refusal (unchanged)
tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py  # contract cases
tests/e2e/upgrade_portal/test_org_upgrade_flow.py                    # browser case (unchanged)
changelog.d/issue-3393-site-read-refusal.md                          # release note (unchanged)
```

**Structure Decision**: Keep the repair at the route boundary (D-4). Keep the device rules and the reader unchanged. Put the new proof in the existing contract module, because that module owns the issue 3393 seam.

## File-by-File Change Map

| Path | Action | Task | Reason |
| - | - | - | - |
| `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | Modify (comments only) | T007 | Add inline comments to lines 230, 231, 1147 to 1149, 1227 to 1229, and 1350 to 1352 |
| `tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py` | Modify (add cases) | T008 | Add one parametrized test that raises `requests.exceptions.ConnectionError` below mistapi for the save, the options page, and the confirmation page |
| `specs/numbered/0/0/1/0/2/0/3/3/3393-site-read-refusal/` (nine legacy files) | Replace in the record pull request | Record landing | Replace the nine legacy files with the nine files of this record and add `design/checklists/security.md` |
| `src/interfaces/portals/upgrade_portal/app/routes/select.py` | No change | None | The reader is not the fault. D-4 keeps it unchanged. |
| `src/interfaces/portals/upgrade_portal/app/routes/org_controls.py` | No change | None | The retry caller is out of scope (D-6) |
| `src/interfaces/portals/upgrade_portal/upgrade/org_site_records.py` | No change | None | The unread-site text is out of scope until T008 (A-2) |
| `changelog.d/issue-3393-site-read-refusal.md` | No change | None | The fragment exists (RC-44) |
| Any file that a menu, a dependency, or a container uses | No change | None | Not affected |

## Gate Map for T-LOCAL-GATES

Each row names a gate of the local gates table in `.github/copilot-instructions.md` (RC-56). The paths in the mypy, vulture, pydocstyle, and interrogate rows come from `.github/workflows/ci.yml` (RC-57).

| Gate | Command | Expected result | Applies |
| - | - | - | - |
| Compile | `python -m py_compile src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | No output | Yes |
| Lint | `python -m ruff check .` | `All checks passed` | Yes |
| Format | `python -m black --check .` | No file needs a change | Yes |
| Types | `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml` | `Success` | Yes |
| Tests | `python -m pytest tests/contract/upgrade_portal/test_issue_3393_cloud_read_refusal.py` | All tests pass | Yes |
| Tests, regression | `python -m pytest tests/contract/upgrade_portal/test_org_site_records_routes.py tests/contract/upgrade_portal/test_org_upgrade_routes.py` | All tests pass | Yes |
| Tests, browser | `python -m pytest tests/e2e/upgrade_portal/test_org_upgrade_flow.py` | All tests pass | Yes |
| Full tests | The two `pytest-chunks` commands of the local gates table | One summary line for each shard | CI only |
| Test quality | The test quality ratchet procedure of `.github/copilot-instructions.md` | `gate: 0 new findings vs baseline` | Yes, for the test module |
| Complexity | `radon cc src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py -j \| complexity-gate --max 10` | No block above 10 | Yes |
| Security lint | `bandit -c pyproject.toml -r src -q` | No finding | Yes |
| Code quality | `pylint src/ --fail-under=9.5` | Score 9.5 or above | Yes |
| Dead code | `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70` | No finding | Yes |
| Docstrings | `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90` | No violation, coverage 90 or above | Yes |
| Symbols | `symbol-diff --base origin/main src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | `no module-level name changed`, exit code 0 | Yes |
| STE | `ste-linter --config .ste-linter.toml --min-score 80` followed by the changed Markdown files | Each file scores 80 or above | Yes, for the record files |
| Menu reference | `python scripts/generate_menu_wiki.py` | Not applicable | No |
| Safe sweep | `python MistHelper.py --test` | Not applicable | No |
| Dependency audit | `pip-audit -r requirements.txt` | Not applicable | No |
| Ops portal and ops platform | The npm and pytest commands of the local gates table | Not applicable | No |

Read each command output. Count the files that each gate examined. A gate that skips because of a missing input proves nothing.

## Risks and Mitigations

- R-1: A later mistapi release changes the retry wrapper. Mitigation: T008 pins the observed answer. A failure of T008 signals the change.
- R-2: The comment-only change conflicts with a later edit to `org_upgrade.py`. Mitigation: rebase before the push. No open PR changes the file on 2026-11-26 (analysis remote state).
- R-3: T008 shows an answer that differs from the prediction. Mitigation: record the observed answer in analysis.md and contracts/refusal.md, and revisit D-11.
- R-4: The record replaces the legacy folder and loses a legacy fact. Mitigation: each legacy claim has a result in analysis.md (L01 to L52).
- R-5: A reviewer reads the comment-only change as a behavior change. Mitigation: the pull request body names the comment-only scope, and the symbol gate proves that no name changed.

## Dependencies

- Python 3.15 (RC-58), mistapi 0.64.1 (RC-59, RC-76), requests 2.34.2 (`requirements.txt` line 221), and Flask 3.1.3 (`requirements.txt`).
- The browser test stack in `documentation/development-setup.md` (RC-62). No new dependency.

## Complexity Tracking

Existing debt. None of it is new.

| Item | Kind | Why it stays | Remediation |
| - | - | - | - |
| `org_upgrade.py` defines more than five top-level names, and some route functions exceed 25 lines (L24, L25) | Grandfathered | The change adds no name and no function | A separate issue splits the route module after human review. This record does not file it. |
| `tests/contract/upgrade_portal` holds 66 children (L26) | Grandfathered | The change adds one module case to an existing file | A separate issue owns the folder layout |
| `changelog.d` holds 335 children (L26) | Grandfathered | The release fragment is required by the repository rule | The release coordinator owns the folder |

No new class, module, or wrapper is added.

## Rollback Steps

1. For the T-PR code change, revert its squash commit. The change alters comments only, so runtime behavior does not change.
2. For the T008 cases, revert the commit that adds them. The contract module returns to its prior cases.
3. Do not revert PR 4413. Caution: a revert restores the 500 answer for an exception that reaches the route.
4. For the record landing, revert the documentation commit. The legacy record returns from the `main` history.
