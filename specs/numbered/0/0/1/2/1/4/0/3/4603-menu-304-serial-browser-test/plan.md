# Implementation Plan: Menu 304 serial number browser test

**Branch**: `fix/4603-menu-304-serial-browser-test` | **Date**: 2026-11-26 | **Spec**: `spec.md` in this folder

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/1/4/0/3/4603-menu-304-serial-browser-test/spec.md`.

This record uses the numeric route. The feature root holds five children or fewer: `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/`. The route folders hold one child each.

## Summary

The menu 304 browser test failed once in CI at head `1b8c06a8`. The failing assertion checks the serial number control, which never appeared. The helper `select_menu` waits on a loading predicate that already passes before any request starts. This plan first makes the helper prove each selection. It then measures the failure across four environment combinations. A production repair starts only when the matrix proves a cause.

## Technical Context

- **Language/Version**: Python 3.15.2 in CI. The default is `'3.15'` (`.github/workflows/ci.yml` line 77). The floor is `requires-python = ">=3.15"` (`pyproject.toml` line 23). The failing run used Python 3.13.18.
- **Primary Dependencies**: pytest 9.2.0 (CI log), pytest-playwright 0.10.0 (`requirements-dev.txt` line 333), Playwright 1.65.2 (`requirements-dev.txt` line 272), Dash 4.5.1 (`requirements-dev.txt` line 76). Dash loads a pytest plugin in every run, and the product map code uses Dash.
- **Storage**: Not applicable to the test. The test writes to a pytest temporary folder and sets `MISTHELPER_STANDALONE=true` in the module fixture `juniper_workspace`.
- **Testing**: pytest with the `page` fixture from pytest-playwright. Chromium comes from `python -m playwright install --with-deps chromium` (`ci.yml` line 887).
- **Target Platform**: Windows 11 for local runs. Linux for CI (the CI log path starts with `/home/runner`).
- **Project Type**: CLI tool with a Flask web portal.
- **Performance Goals**: Each E2E test ends within 180 seconds (`ci.yml` line 909). The parameter response wait ends within 15 seconds (`READY_TIMEOUT_MS`, test module line 45).
- **Constraints**: No call reaches Juniper or Mist. The double answers each call. No write reaches `data/`.
- **Scale/Scope**: One test module with 18 tests. This plan changes one helper, adds one test, and adds one changelog fragment.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule | Pass | No new directory child. Each new function stays at 25 lines or fewer. Existing debt is recorded in Complexity Tracking. |
| II. Class-based architecture | Pass | Changes sit in the existing test class and the existing helper. No wrapper function is added. |
| III. Safety first | Pass | The change reads no operator input. The test uses synthetic data and writes only to a temporary folder. |
| IV. Full deployment pipeline | Pass with steps | Local gates run in T-LOCAL-GATES. The pull request opens in T-PR. CI is watched in T-REMOTE-CI. Merge follows in T-MERGE. The container build does not change, because the change touches no product code unless T007 starts. |
| V. Observability and logging | Pass | The helper adds an `info` line before each wait and a `debug` line after it. Messages use ASCII. No secret reaches a log. |
| VI. Inline comments | Pass with plan | Each changed line carries an inline comment (FR-009). |
| VII. Action logging | Pass with plan | Each click and each wait carries a log line before and after it (FR-009). |
| Technology: mistapi | Not applicable | The menu 304 path makes no mistapi call (RV-23). |
| Technology: Podman | Not applicable | The change starts no container. |
| Technology: file paths | Pass | The test uses `Path` objects and the module fixtures. |
| Technology: data directory | Pass | Output goes to the module workspace under a temporary folder. No write reaches `data/`. |
| Technology: output backends, operational store, database keys, container security, proxy | Not applicable | The change alters no export, store, key, container, or proxy path. |
| Development: menu operations | Not applicable | The change adds no menu. |
| Development: testing | Pass | TC-2 proves that the helper can fail. TC-1 covers the success path. |
| Development: security findings | Not applicable | No security tool reports a finding for this change. |
| Development: release notes | Pass with decision D-5 | The constitution requires one fragment for each change. `changelog.d/README.md` line 58 excludes internal-only changes. The constitution governs (D-5). |
| Multi-agent: issue first | Pass | Issue #4603 exists. The `in-progress` label is added before the branch is created (T-PR). |
| Multi-agent: branch name | Pass | `fix/4603-menu-304-serial-browser-test` follows the constitution pattern. |
| Multi-agent: labels | Pass | The issue carries `bug`, `tests`, and `web-portal`. |
| Multi-agent: file overlap | Pass | PR #4888 changes `requirements-dev.txt`, and this plan does not. No open PR changes the browser test module. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/1/4/0/3/4603-menu-304-serial-browser-test/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      parameter-request-response.md
      selection-failure-message.md
    checklists/
      requirements.md
```

### Source Code (repository root)

```text
tests/e2e/web_portal/test_juniper_menus_browser.py        (modify)
changelog.d/issue-4603-menu-304-serial-browser-test.md    (add)
web_portal/static/js/operations.js                        (modify only if T007 starts)
```

**Structure Decision**: The change touches tests only, unless T007 starts. The record follows the layout of the reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`.

## File-by-File Change Map

| Path | Action | Requirements | Change |
| - | - | - | - |
| `tests/e2e/web_portal/test_juniper_menus_browser.py` | Modify | FR-002 to FR-010, FR-014, FR-015 | Replace the loading wait (line 186) and the fixed sleep (line 187) in `select_menu` with a response wait and a title wait. Capture page and console errors. Add the negative test after the menu 300 tests. |
| `changelog.d/issue-4603-menu-304-serial-browser-test.md` | Add | FR-012 | One `###` heading and one `Fixed` bullet that names issue 4603. |
| `web_portal/static/js/operations.js` | Modify, conditional | FR-013 | Changes only if T007 starts under decision D-7. |
| `specs/numbered/0/0/1/2/1/4/0/3/4603-menu-304-serial-browser-test/` | Add | FR-001, FR-011 | This Spec Kit record, committed with the pull request. |

No file is deleted.

## Architecture

The selection flow after the change:

```text
open_portal
  -> open_juniper_group
  -> register page error and console listeners
  -> register the parameter response wait (path of menu 304, HTTP 200 required)
  -> click the row for menu 304
  -> receive the parameter response
  -> wait until #selectedOpTitle reads "Menu 304"
  -> wait until #parameterLoading is hidden
  -> return to the test
```

On any failed wait, the helper raises an `AssertionError` that follows the contract in `design/contracts/selection-failure-message.md`.

## Dependencies

- `pytest-playwright==0.10.0` (`requirements-dev.txt` line 333).
- `playwright==1.65.2` (`requirements-dev.txt` line 272).
- `dash==4.5.1` (`requirements-dev.txt` line 76). It loads a pytest plugin in every run.
- `pytest-timeout` (required by `tests/e2e/conftest.py` line 209).
- Chromium, from `python -m playwright install --with-deps chromium`.

No dependency changes are part of this plan (decision D-4).

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| The response wait registers after the click and misses the response. | False failure. | Register the wait before the click (T002 acceptance). TC-1 covers the path. |
| A slow runner exceeds the 15 second response timeout. | False failure. | The timeout equals the module constant. The matrix records slow runs. |
| Dash 4.5.1 changes behavior in a later release. | Failure returns. | Run the matrix when Dash changes. The E2E job runs on each dependency update. |
| The root cause stays unknown. | The issue stays open. | Stop rules in T006 and T007. Close with the matrix evidence when combination A passes 20 of 20. |
| `select_menu` exceeds 25 lines. | Constitution violation. | Use a nested function. Count the lines before the push. |
| A module-level name changes. | The Symbols gate fails. | No module-level change (decision D-6). |
| A Windows local run differs from the Linux CI run. | A local pass can hide a CI failure. | The CI result is the authority. T-REMOTE-CI checks it. |

## Rollback Steps

1. Revert the squash commit of the pull request on main. The test returns to its current form.
2. If T007 started, revert the commit that changed `web_portal/static/js/operations.js` first.
3. No data migration exists. The test writes only to a temporary folder, so no cleanup is required.

## Complexity Tracking

Existing folder debt. The constitution requires a separate remediation action for each debt item.

| Existing violation | Why it stays | Simpler alternative rejected because | Remediation action |
| - | - | - | - |
| `tests/e2e/web_portal/` holds 33 direct children. The limit is five. | The folder predates this change. | Moving tests changes the E2E shard path and the shard guard. | A separate issue splits the folder by domain. This change does not include it. |
| `tests/e2e/` holds 6 direct children. The limit is five. | The folder predates this change. | Moving files changes the shard partition guard. | The same separate issue covers this folder. |

This change adds no direct child to either folder.
