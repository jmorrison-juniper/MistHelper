# Implementation Plan: Add independently authored converter visual journeys

**Branch**: `feat/4647-converter-visual-journeys` (planned) | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/2/0/4/2/4647-converter-visual-journeys/spec.md`.

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, contracts, and checklists under `design/`.

## Summary

Replace the converter presentation with an independently authored page. Add the browser journeys to the shared smoke module, which already holds the converter smoke class. The journeys run in a test host built from the real portal factory. Server routes and JSON shapes stay unchanged. Implementation waits for issues #4636, #4641, and #4642.

## Technical Context

**Language/Version**: Python, the version that the repository test environment uses.

**Primary Dependencies**: Flask and Jinja2 for the portal host. Playwright 1.65.2 and pytest-playwright 0.10.0 for browser tests (RC-58, RC-59).

**Storage**: No new storage. The portal host writes one browser key, `misthelper-theme` (RC-32).

**Testing**: pytest with the `page` fixture from pytest-playwright and the E2E fixtures in `tests/e2e/conftest.py` (RC-44 to RC-46).

**Target Platform**: A Windows developer host and the Linux CI runner of the `playwright_shards` job (RC-50).

**Project Type**: Feature inside the existing converter package and the existing web portal test module.

**Performance Goals**: The `web_portal` browser shard finishes within 20 minutes (RC-54).

**Constraints**: No reuse of source assets (D-14). No new direct child under a noncompliant directory (RC-48). No change to shared portal files (RC-30, RC-31, RC-72).

**Scale/Scope**: One converter page, four shipped themes (RC-34), two viewports (RC-40), and 20 planned test cases.

## Constitution Check

*Gate: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The check uses constitution version 1.9.0 (`.specify/memory/constitution.md`, blob 4584997a264c5a7ade2ca7441246e1f067083aa1, RC-78).

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, directory limits | Pass | No direct child is added to `tests/e2e/` or `tests/e2e/web_portal/` (RC-47, RC-48). The presentation folder grows from two files to three (RC-02). Debt is in the Complexity Tracking table below. |
| I. Five-item rule, function limits | Pass (planned) | Test helpers keep at most five parameters, five blocks, and 25 lines. Review checks each helper. |
| II. Class-based architecture | Pass | Tests and helpers live in classes. No wrapper function delegates to a method. |
| III. Safety and typed confirmation | Pass | Export needs the typed word `EXPORT` (D-2). The change adds no destructive operation. No secret is read (D-13). |
| IV. Full deployment pipeline | Pass (planned) | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE follow the pipeline. No task pushes to `main`. |
| V. ASCII logging | Pass | Python log text uses ASCII only. The browser script writes no log line (see U-2). |
| VI. Inline comments | Pass (planned) | Each changed Python line gets an inline comment. Changed browser script blocks get comments. Scope question in U-2. |
| VII. Action logging | Pass (planned) | The test host logs before and after server start and stop. The browser script adds no server action (see U-2). |
| Python version and dependencies | Pass | No dependency change. The pins stay at RC-57 to RC-59. |
| mistapi and Mist REST rules | Not applicable | The converter sends no Mist request (RC-07). The mistapi pin stays unchanged (RC-57). |
| Owned WebSocket transport | Not applicable | No WebSocket transport is added. |
| Container runtime and test containers | Not applicable | Tests run on the host with Chromium. No container starts. |
| File paths | Pass | Python tests use `pathlib`. No path string joins separators by hand. |
| Data directory | Pass | Test evidence goes to `test-artifacts/`, which Git ignores (RC-60). No write goes to `data/`. |
| Container security and Zscaler | Not applicable | No container build or push is part of this change. |
| Documentation | Pass | A local search of five operator and API documents found no converter reference (U-7). This change edits no document. |
| Release notes | Pass | One fragment covers the user-visible presentation change (D-16). |
| Specification before implementation | Pass | The change touches five files in two packages, so this record exists first. |
| Multi-agent git workflow | Pass | Open PR #4208 touches `base.html` and `app.py` (RC-72). This change touches neither file. |
| Security findings | Pass | No suppression comment is added. Safe text uses DOM text APIs (RC-15). |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/0/4/2/4647-converter-visual-journeys/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      portal-journey.md
      http-routes.md
      test-host.md
    checklists/
      requirements.md
      security.md
      accessibility.md
      provenance.md
```

### Source changes (repository root)

| Action | Path | Purpose |
| - | - | - |
| Add | `src/interfaces/portals/cisco_config_converter/presentation/converter.css` | Host-token styles, focus outline, and text wrapping (T004) |
| Modify | `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | Independent markup and test IDs (T003) |
| Modify | `src/interfaces/portals/cisco_config_converter/presentation/converter.js` | DOM rendering, typed gate, cancel, and reset (T005) |
| Modify | `tests/e2e/web_portal/test_portal_smoke.py` | Replace the isolated class with the journeys (T002, T006 to T014) |
| Add | `changelog.d/issue-4647-converter-visual-journeys.md` | Release note for the user-visible change (T-PR) |

These files stay unchanged: `src/interfaces/portals/cisco_config_converter/routes.py`, `models.py`, `conversion.py`, and `__init__.py` (RC-01). Also unchanged are `web_portal/app.py` (RC-30), `web_portal/templates/base.html` (RC-31), `web_portal/static/js/portal.js` (RC-32), the theme files, `responsive.css`, `tests/integration/web_portal/cisco_config_converter/test_routes.py`, `tests/e2e/conftest.py`, `.github/workflows/ci.yml`, and the requirements files.

## Design Summary

1. **Test placement**: The journeys replace the isolated class in `tests/e2e/web_portal/test_portal_smoke.py`. No file or directory is added under `tests/e2e/`. See D-1.
2. **Test host**: A test class builds the real portal app and mounts the converter blueprint before the first request. Production registration stays unchanged. See D-3 and `contracts/test-host.md`.
3. **Presentation**: The converter page and script are rewritten with DOM APIs and host tokens. A stylesheet is added. The server stays unchanged. See D-5 and D-6.
4. **Typed confirmation**: The operator types `EXPORT`. The page enables export only after review and the exact word. See D-2 and `contracts/portal-journey.md`.
5. **Stale responses**: The existing generation token stays. A held route proves that an older response is ignored. See D-7 and D-10.
6. **Themes and viewports**: The tests reuse `SHIPPED_THEMES`, `PHONE`, and `DESKTOP` from existing modules. See D-8.
7. **Failure evidence**: The CI pytest options keep traces and screenshots on failure. See D-9.
8. **Cloud guard**: A route handler aborts every non-loopback request, and the test counts those requests. See D-11.

## Complexity Tracking

The constitution requires this table to separate grandfathered debt from new design (RC-84). Grandfathered debt does not permit another violation.

| Structure | Grandfathered debt or new design | Status in this change | Action |
| - | - | - | - |
| `tests/e2e/web_portal/` holds 32 direct children (RC-48) | Grandfathered debt | No child is added | Remediation action R-1 |
| `tests/e2e/` holds exactly five entries (RC-47) | Compliant at the limit | No child is added | None |
| `src/interfaces/portals/cisco_config_converter/` holds five children (RC-01) | Compliant at the limit | No child is added | None |
| `src/interfaces/portals/cisco_config_converter/presentation/` holds two files (RC-02) | New design within the limit | One file is added, so three remain | None |

Remediation action R-1: Open a separate issue that moves the shared portal tests out of `tests/e2e/web_portal/` into a compliant package. The orchestrator opens that issue. This record makes no GitHub change.

## Dependencies

- Issue #4636 defines converter state and must merge first (open).
- Issue #4641 defines versioned proposal review and safe export. It may change the JSON shapes (open).
- Issue #4642 defines read-only Mist discovery. It is a stated prerequisite (open).
- Issue #4648 owns shared portal integration. It is out of scope here.
- Issue #4635 owns the legal decision on source reuse. It is out of scope here.
- PR #4208 is open and touches `web_portal/templates/base.html` and `web_portal/app.py` (RC-72).

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| The browser shard exceeds 20 minutes | CI fails | Keep the eight theme cases. Measure in T-REMOTE-CI. Do not raise the budget (RC-54). |
| The host renames its storage key | Storage test fails | Keep the key in one constant in the test module. Update it with the host (D-4). |
| Held routes make the stale test flaky | False failure | Use explicit route handling and `expect` waits. Do not use fixed sleeps (D-10). |
| Test host state leaks between classes | False pass | Use a fresh browser context for each test. Stop the host after its class (RC-45). |
| Issue #4641 changes the proposal shape | Structured review breaks | Update the contract and the renderer after #4641 merges (U-4). |
| PR #4208 conflicts with the shared files | Rebase effort | This change does not touch `base.html` or `app.py`. Rebase when #4208 merges first. |
| CSP allows inline scripts | Safe text relies on code discipline | Use DOM text APIs only. Test that no element is injected (D-5, RC-42). |
| Three themes lack the focus token | Focus outline is hard to see | Use `currentColor` as the fallback for the focus outline. Test each theme (RC-35 to RC-38). |
| The test module grows | Review cost rises | Use small classes. Record the debt. Open R-1 (D-15). |

## Rollback Steps

1. Revert the squash commit of the pull request with a new pull request.
2. Confirm that `tests/e2e/web_portal/test_portal_smoke.py` again holds the converter smoke class.
3. Restore `converter.html` and `converter.js` from the reverted commit.
4. Delete `converter.css` in the same revert.
5. Run `python -m pytest tests/e2e/web_portal/test_portal_smoke.py` to confirm the previous state.

Caution: a revert changes `main`. Use a pull request, and do not force-push `main`. The history stays recoverable.

## Contracts

The contracts folder applies. The browser journey, the HTTP shapes, and the test host are interfaces. The three files are `contracts/portal-journey.md`, `contracts/http-routes.md`, and `contracts/test-host.md`.
