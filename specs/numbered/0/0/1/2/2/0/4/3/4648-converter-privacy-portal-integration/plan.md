# Implementation Plan: Converter Privacy and Shared Portal Integration

**Branch**: `feat/4648-converter-portal-integration` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record `specs/numbered/0/0/1/2/2/0/4/3/4648-converter-privacy-portal-integration/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

The plan has two phases. Phase A adds offline cross-cutting tests through a composition harness. Phase A edits no shared portal file. Phase B registers the converter in the shared portal files. It adds one navigation entry and one browser module. It also runs the regression suites and updates the docs. Neither phase adds a route, a cloud write, or infrastructure.

## Technical Context

**Language/Version**: Python 3.15. Source: `pyproject.toml` line 23.

**Primary Dependencies**: Flask 3.1.3 (`requirements.txt` line 49). Flask-WTF 1.3.0 provides CSRF (line 54). Pytest 9.2.0 (`requirements-dev.txt` line 325), pytest-timeout 2.4.0 (line 335), pytest-playwright 0.10.0 (line 333), and Playwright 1.65.2 (line 272). This plan changes no dependency.

**Storage**: None added. The converter stores a SHA-256 proposal digest in the signed session under `cisco_proposal`. Source: `src/interfaces/portals/cisco_config_converter/models.py` line 96.

**Testing**: Pytest in `tests/integration/web_portal/cisco_config_converter/`. Guard tests in `tests/guardrails/`. Browser tests use the `page` fixture from `pytest-playwright` (R-45).

**Target Platform**: Windows 11, macOS, and Linux. The Podman container runs one Gunicorn worker. Source: `wsgi.py` line 4.

**Project Type**: Integration of a Flask blueprint into an existing portal application.

**Performance Goals**: The health reply reads no disk and opens no network connection. Source: `web_portal/routes/dashboard.py` lines 49 to 53. This plan adds no call to that path.

**Constraints**: The converter file limit is 16 MiB, with a 16 KiB form allowance. Source: `routes.py` line 36. No shared-file edit happens before the G3 handover. Each new directory holds five children or fewer.

**Scale/Scope**: One portal process. One converter entry. Forty comparison rows. Each row links to a test or a remaining task.

## Constitution Check

*Gate: passes before the design. Re-checked after the design: passes.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | The converter root keeps five children (R-01). The converter test folder holds two children and gains two modules (R-15). `tests/e2e` holds five and gains none (R-25). No new direct child enters `tests/e2e/web_portal` (R-26). |
| II. Class-Based Architecture | Pass | New test code uses test classes and fixtures. The two lines in `web_portal/app.py` extend an existing method. |
| III. Safety-First | Pass | No operation writes to the cloud. The converter reads one upload and writes no file. |
| IV. Full Deployment Pipeline | Pass | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover the pipeline. |
| V. Observability and Logging | Pass | Test strings and log messages use ASCII. The existing standard-library logger stays. |
| VI. Inline Comments | Pass | Each executable line in a new or changed file gets an inline comment. Each task acceptance states this rule. |
| VII. Action Logging | Pass | The registration edit logs before and after the change. |
| Mist SDK rule | Pass | The integration adds no Mist call. Remote check R-07 shows no SDK import in the converter package. |
| Owned WebSocket transport | Not applicable | The feature owns no WebSocket transport. |
| Test containers | Not applicable | No container starts. No Compose service changes (R-42). |
| File paths | Pass | Tests use `pathlib`. No path separator is hard-coded. |
| Data directory | Pass | Test evidence goes to `test-artifacts/`, which Git ignores (R-48). No product output is written. |
| Security findings | Pass | No suppression comment is added. Bandit runs on `web_portal` after T009. |
| Documentation | Pass | Task T013 updates the operator guide and adds a changelog fragment. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/0/4/3/4648-converter-privacy-portal-integration/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      portal-registration.md
      health-and-services.md
      csrf-negotiation.md
      privacy-and-logs.md
      browser-journey.md
    checklists/
      requirements.md
      privacy.md
      handover.md
      regression.md
```

### Source Code (repository root)

Changed or added paths:

| Path | Change | Task | When |
| - | - | - | - |
| `tests/integration/web_portal/cisco_config_converter/test_parity.py` | Add | T002 to T008, T014 | Phase A |
| `tests/integration/web_portal/cisco_config_converter/test_portal_browser.py` | Add | T011 | Phase B |
| `web_portal/app.py` | Modify two places in `create_app` and `_register_blueprints` | T009 | Phase B, after G3 |
| `web_portal/templates/base.html` | Modify one navigation entry after line 79 | T010 | Phase B, after G3 |
| `documentation/operator-guide.md` | Modify the web portal row near line 215 | T013 | Phase B |
| `changelog.d/pr-<number>.md` | Add one fragment | T-PR | Phase B |

Paths that stay unchanged:

- `src/interfaces/portals/cisco_config_converter/`. The package root already holds five children (R-01).
- `web_portal/services/config.py`. The secret policy belongs to issue #4636 (decision D-9).
- `web_portal/services/output_scan.py` and `web_portal/services/data_browser.py`. Storage exposure belongs to the storage issues (decision D-10).
- `tests/e2e/`. The folder already holds five children (R-25).
- `compose.yml`, `requirements.txt`, and `requirements-dev.txt`.

## Architecture

The converter joins the portal at one seam. The factory applies CSRF before it registers blueprints. The converter requires that order.

```text
Browser
  -> WebPortalApp.create_app                       web_portal/app.py line 37
       -> _apply_security (CSRFProtect)            web_portal/app.py line 52
            -> SecurityMiddleware._configure_csrf  web_portal/services/config.py lines 297 to 304
       -> app.request_class = ConverterRequest     web_portal/app.py, before line 53 (T009)
       -> _register_blueprints                     web_portal/app.py line 182
            -> ConverterRoutes.blueprint           src/interfaces/portals/cisco_config_converter/routes.py lines 49 to 66
                 -> ConverterInput.verify_host     routes.py lines 103 to 108
                 -> page, preview, review, export  routes.py lines 68 to 96
```

The composition harness runs the same steps in a test fixture. It sets the request class and registers the blueprint on a real app. It edits no shared file. After T009, the fixture reads the registered app instead.

## Phases and Dependencies

Phase A has no shared-file dependency. It needs no decision except the handover check (T001).

Phase B waits for these items:

- The G3 handover, recorded by a comment on issue #4648 (decision D-3).
- PR #4208 closes or merges. It was OPEN on 2026-11-26.
- Issue #4636 closes. It defines the state model. Source: draft record `spec-drafts/4636`.
- Issue #4644 closes. It defines gated apply. Source: issue body, "Prerequisites" in issue #4648.
- Issue #4646 closes. It defines reviewed recovery.
- Issue #4647 closes. It defines visual journeys.

Issue #4633 is closed. Its decision authorizes offline work and names the coordinator as owner.

## Risks and Mitigations

- **RISK-1**: PR #4208 changes the shared files before T009 starts. Mitigation: re-check its state, and rebase on `main`, before the edit.
- **RISK-2**: Caution: an edit to a shared file before the handover can conflict with PR #4208. Mitigation: T009 waits for the handover checklist to read `recorded`.
- **RISK-3**: The blueprint guard raises `ValueError` when the request class or CSRF is missing (routes.py lines 105 to 108). Mitigation: set the request class before `_register_blueprints` (`app.py` line 53).
- **RISK-4**: The request class applies to the whole portal. Mitigation: the `ConverterRequest` path check (routes.py lines 22 to 42) limits the change to the converter prefix. Test `test_other_upload_routes_keep_flask_limits` checks a non-converter route.
- **RISK-5**: Browser waits can stall. Mitigation: the browser module sets a timeout mark of 120 seconds, the same budget as `tests/e2e/conftest.py` line 33. It uses `make_server` on port 0.
- **RISK-6**: Random per-process secrets break CSRF across processes (`services/config.py` line 113). Mitigation: tests set one synthetic key. Production policy stays with decision D-9.
- **RISK-7**: The harness can diverge from the real registration. Mitigation: test `test_handover_state_matches_shared_files` changes its expectation at T009, and the same tests then run on the real factory.
- **RISK-8**: Issue #4647 may place browser tests in an overfull folder. Mitigation: decision D-4 and defect E-02 in `analysis.md`.

Warning: a cloud write changes production state, and this integration cannot undo it. Mitigation: no write route exists (test `test_route_allowlist_has_no_cloud_write_route`), and this plan adds no apply code.

## Rollback Steps

1. Revert the integration commit with a new pull request. Close the pull request instead when it has not merged.
2. Remove the two registration lines in `web_portal/app.py`.
3. Remove the navigation entry in `web_portal/templates/base.html`.
4. Remove the operator guide row and the changelog fragment.
5. Remove `test_portal_browser.py`. Keep `test_parity.py` only when the harness still runs.
6. Run `test_health_reply_keeps_exact_shape` and `test_ready_reply_unchanged_with_converter` to confirm the health baseline.
7. Confirm that `data/` holds no converter file. The converter writes no file.

Caution: revert only the integration change. The converter package under `src/` stays in place.

## Complexity Tracking

Existing debt. This plan adds no new debt.

| Item | Kind | Why it stays | Remediation |
| - | - | - | - |
| `tests/e2e/web_portal` holds 32 children (R-26) | Grandfathered | This plan adds no child there. | A separate issue reduces the count. |
| `tests/integration` holds 26 children | Grandfathered | This plan adds no child there. | A separate issue reduces the count. |
| `web_portal` holds seven children (R-75) | Grandfathered | This plan adds no child there. | A separate issue reduces the count. |
| `src/interfaces/portals` holds six children (R-76) | Grandfathered | This plan adds no child there. | Issue #4636 defect R-1 tracks the count. |

New design that needs a reason: none. The browser module uses the feature folder, which is a compliant location, as decision D-4 explains.
