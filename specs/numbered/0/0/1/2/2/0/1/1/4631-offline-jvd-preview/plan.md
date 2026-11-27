# Implementation Plan: Offline Dynamic JVD Labs Preview

**Branch**: `feat/4631-offline-jvd-preview` (planned) | **Date**: 2026-11-26 | **Spec**: `spec.md`

**Input**: Numeric record `specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/`. The route is the base-5 form of 4631, as `.specify/scripts/powershell/spec-route.ps1` computes it (R-54, R-55).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place supporting files under `design/`.

## Summary

Add an offline Labs page to the Flask web portal. The feature adds three routes: a page, a JSON capability response, and a POST plan route. The plan route validates one run name, calls a guarded planner, and projects the result through an allow-list. Registration waits for the shared-file handover.

## Technical Context

- **Language/Version**: Python 3.15 or newer (`pyproject.toml` line 23, R-69).
- **Primary Dependencies**: Flask 3.1.3 (`requirements.txt` line 49). Flask-WTF 1.3.0 (`requirements.txt` line 54, R-70). No new runtime dependency.
- **Test Dependencies**: The pytest stack in `requirements-dev.txt`. Playwright 1.65.2 (line 272, R-72). pytest-playwright 0.10.0 (line 333, R-73).
- **Storage**: None. The feature writes no file and no table. Browser evidence goes to `test-artifacts/labs-preview/`, which Git ignores.
- **Testing**: pytest. Route tests run through the real portal factory with a test harness (D-5).
- **Target Platform**: The web portal on port 8055 (`compose.yml` line 86, R-74). Paths use `pathlib`, never hard-coded separators.
- **Project Type**: Web portal feature with one Flask blueprint and one Jinja template.
- **Performance Goals**: None measured. The server example holds two devices and one link.
- **Constraints**: Offline only. No Mist call, provider call, or device action. Five children or fewer in each new directory. The shared portal files stay unchanged until the handover.
- **Scale/Scope**: Three routes, one page, one server example, 26 requirements, and 29 planned tests.

## Constitution Check

Each rule of `.specify/memory/constitution.md` (R-45 to R-50) and the repository rules has one result.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | Pass | `src/interfaces/labs` holds five children. `tests/integration/web_portal/labs` holds five children. No new child enters a noncompliant parent (R-22, R-25). |
| II. Class-Based Architecture | Pass | Routes, form, planner, and projector are classes. No standalone function wraps a method. |
| III. Safety-First | Pass | The form validates input first and returns at the first failure. CSRF covers each POST. No destructive operation exists, so no typed confirmation applies. |
| IV. Full Deployment Pipeline | Pass with steps | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover steps 1 to 11 (R-47). Step 12, the deployment, needs the orchestrator. |
| V. Observability and Logging | Pass with owner check | Logs use ASCII only (FR-022). Logs use stdlib key=value text, as `web_portal` does (R-17). The owner must confirm this against the structlog rule (R-46, U-8). |
| VI. Inline Comments | Pass by acceptance | Each task requires an inline comment on each executable line it adds. |
| VII. Action Logging | Pass by acceptance | Each task requires an info line before each action and a debug line after it. |
| Python 3.15 | Pass | `pyproject.toml` requires 3.15 or newer (R-69). |
| mistapi | Not applicable | The feature makes no Mist call (FR-020, D-22). |
| UV and requirements | Pass | No dependency changes. `requirements.txt` stays unchanged. |
| Podman and test containers | Not applicable | No container starts. The compose naming rules apply only when a container starts (R-43, D-22). |
| File paths | Pass | Code uses `pathlib` and `os.path` helpers only. |
| Output backends, operational store, export boundary, database keys | Not applicable | The feature exports no data, writes no coordination record, and writes no table. |
| Data directory | Not applicable | The feature writes no product output under `data/`. Browser screenshots go to `test-artifacts/`. |
| Container security and Zscaler | Not applicable | No image build or push occurs in this change. |
| Testing | Pass | Each requirement maps to a test (`analysis.md`, coverage matrix). |
| Security findings | Pass | No suppression comment is planned. Bandit runs on the new package. |
| Documentation | Pass | The changelog fragment is added (T012). The operator guide row follows registration (T015). `README.md` stays unchanged (R-80, D-21). |
| Audience standard | Pass | Page copy uses plain words (FR-026). |
| SpecKit escalation | Pass | The change touches more than three files and two classes, so the spec exists. |
| Multi-agent git workflow | Pass with handover | The branch starts from `main`. The issue carries `in-progress`. The overlap check found PR 4208 (R-11). No shared file changes before the handover. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/0/1/1/4631-offline-jvd-preview/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
    checklists/
```

### Source Code (repository root)

```text
src/interfaces/labs/
  __init__.py
  routes.py
  run_name_form.py
  planner.py
  presentation/
    labs_page.html

tests/integration/web_portal/labs/
  __init__.py
  harness.py
  test_labs_units.py
  test_labs_routes.py
  test_labs_browser.py

changelog.d/issue-4631-offline-jvd-preview.md
```

**Structure Decision**: New source code enters `src/interfaces/labs/`. New tests enter `tests/integration/web_portal/labs/`. Each package holds five children. Each parent stays at five children or fewer after the change (R-22, R-25, D-2, D-3).

## File Change Map

| Path | Action | Purpose | Blocked by |
| - | - | - | - |
| `src/interfaces/labs/__init__.py` | Add | Package marker and module docstring | None |
| `src/interfaces/labs/run_name_form.py` | Add | Run-name rule, form field rules, rejections | None |
| `src/interfaces/labs/planner.py` | Add | Planner gateway, plan result allow-list, fingerprint, server example | None |
| `src/interfaces/labs/presentation/labs_page.html` | Add | Labs page template with `data-testid` attributes | None |
| `src/interfaces/labs/routes.py` | Add | Blueprint factory and the three routes | Depends on the four files above |
| `tests/integration/web_portal/labs/__init__.py` | Add | Package marker | None |
| `tests/integration/web_portal/labs/harness.py` | Add | Synthetic fixtures and the test app builder | None |
| `tests/integration/web_portal/labs/test_labs_units.py` | Add | Unit tests for form, projector, fingerprint, gateway, and boundary | Harness |
| `tests/integration/web_portal/labs/test_labs_routes.py` | Add | Flask route tests with the real factory | Harness |
| `tests/integration/web_portal/labs/test_labs_browser.py` | Add | Browser journey, local only | Harness |
| `changelog.d/issue-4631-offline-jvd-preview.md` | Add | One changelog fragment | None |
| `web_portal/app.py` | Modify | Register the Labs blueprint after the precondition check | Shared-file handover |
| `web_portal/templates/base.html` | Modify | Add the `nav-labs` anchor after `nav-websockets` | Shared-file handover |
| `documentation/operator-guide.md` | Modify | Add one Labs row to the Open a portal table | Registration |

No file is deleted.

## Architecture

```text
GET  /labs/            -> LabsBlueprintFactory._page       -> PlannerGateway.status -> labs_page.html
GET  /labs/capability  -> LabsBlueprintFactory._capability -> PlannerGateway.status -> JSON body
POST /labs/plan        -> LabsBlueprintFactory._plan       -> RunNameForm.parse
                                                            -> PlannerGateway.plan
                                                            -> PlanResultProjector.project
                                                            -> labs_page.html
```

The CSRF check runs before each POST view (L-3). The blueprint factory checks the `csrf` extension at registration (D-7, L-2).

## Dependencies

- Internal: `WebPortalApp.create_app` (`web_portal/app.py` line 37, R-12). The factory calls `_apply_security` (R-12) and `_register_blueprints` (R-13).
- Internal: the shared CSRF protection in `web_portal/services/config.py` (R-15, R-16).
- External: Flask 3.1.3, Flask-WTF 1.3.0, and Jinja autoescape (L-6).
- Test only: pytest and Playwright (R-72, R-73).
- Optional private: the `vmm_topology` planner (U-1, D-16). Public CI runs without it.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| K-1 The shared-file handover does not arrive | The Labs page stays unreachable | Route tests prove the behavior through the harness. T013 and T014 stay separate tasks. |
| K-2 The planner API differs from the adapter call | The planner reports `failed` at run time | The adapter isolates the call. The owner confirms the API (U-1). |
| K-3 CI never runs the browser module | A UI regression can reach `main` | The browser gate runs on a developer machine (D-19). The route tests run in the CI root shard (R-34). |
| K-4 `tests/e2e` cannot take a new child | The browser module stays outside the E2E shard | RA-1 frees room in `tests/e2e`. |
| K-5 Logging differs from the structlog rule | Owner review delays the merge | The owner check is listed (U-8). D-18 records the convention. |
| K-6 The run-name rule rejects a valid operator name | An operator retries the form | TU-01 and TU-02 pin the rule. The owner may widen it in a later change. |
| K-7 Private fixtures enter the public change | A licensing breach | FR-018 limits fixtures to synthetic data. D-16 needs a human answer. The quickstart lists the changed files. |

## Rollback Steps

1. Remove the Labs registration line from `web_portal/app.py` and the `nav-labs` anchor from `web_portal/templates/base.html`. Use one commit.
2. Revert the squash commit of the Labs preview pull request.
3. Confirm that `GET /labs/` returns HTTP 404 after the revert.

Caution: The feature stores no data. A revert needs no data repair, but a revert of registration stops the page.

## Complexity Tracking

Existing folder debt that this change touches or relies on:

| Folder | Children | Treatment |
| - | - | - |
| `src/interfaces/portals` | 6 (R-23) | Not touched. Grandfathered. RA-2 reduces it. |
| `tests/e2e` | 5 (R-29) | Not touched. At the limit. RA-1 frees room. |
| `tests/e2e/web_portal` | 32 (R-30) | Not touched. Not used. RA-3 groups its children. |
| `tests/unit` | 50 (R-32) | Not touched. Not used. |
| `tests/unit/web_portal` | 52 (R-33) | Not touched. Not used. |
| `tests/integration` | 26 (R-27) | Only the `web_portal` child gains one folder. |
| `web_portal` | 7 (R-20) | Two existing files change after the handover. No child is added. |

Remediation actions, each a separate issue:

- RA-1: Reduce `tests/e2e` to four children. Then a compliant browser location joins the E2E shard.
- RA-2: Reduce `src/interfaces/portals` to five children. The portal owners decide the order.
- RA-3: Group the 32 children of `tests/e2e/web_portal` into compliant folders.

## Implementation Outline

- Phase A: Write the test modules first (T002 to T006). Confirm that the imports fail.
- Phase B: Write the source package (T007 to T011). Confirm that the tests pass.
- Phase C: Add the changelog fragment (T012).
- Phase D: Apply the shared-file changes after the handover (T013 to T015).
- Phase E: Run the gates and deliver the change (T-LOCAL-GATES, T-PR, T-REMOTE-CI, T-MERGE).
