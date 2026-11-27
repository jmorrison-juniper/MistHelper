# Implementation Plan: Browser sign-in with 2FA for the web portal

**Branch**: `feat/4936-web-portal-sign-in` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/4/2/2/1/4936-web-portal-sign-in/spec.md`.

`spec.md`, `plan.md`, `tasks.md`, and `analysis.md` stay at the feature root. Research, data model, quickstart, contracts, and checklists stay under `design/`.

## Summary

Add a browser sign-in to the web portal on port 8055. The browser flow asks for the work email, the password, and the cloud. When the account requires a 2FA code, a second page asks for the code. The flow calls two public `mistapi` functions on one SDK session, so the password is never kept between steps. A successful sign-in replaces the process session for every route and menu operation. The shared logic moves from the upgrade capture portal into one new package, `src/mist/access/auth/browser/`, and both portals import it. No environment variable is added. The token path and the terminal `--login` path keep working.

## Technical Context

**Language/Version**: Python 3.15 (`pyproject.toml` requires `>=3.15`, R-44).

**Primary Dependencies**: `mistapi` 0.64.1, pinned in `requirements.txt` (R-43). Flask and flask-wtf for the web portal, already in use (R-08). The capture `identity` module, imported for two pure helpers (D-13).

**Storage**: None. The pending sign-ins and the process session live in memory. The feature writes no file and no database row.

**Testing**: pytest with the Flask test client and fake SDK objects. The shared e2e fixtures live in `tests/e2e/conftest.py` (R-65).

**Target Platform**: Windows 11, macOS, Linux, and the Podman container. The container keeps the token path (D-12).

**Project Type**: A feature in an existing web portal, plus a shared package under `src/mist/access/auth/`.

**Performance Goals**: Each request reads the holder in constant time. The pending store holds at most 64 records (R-21).

**Constraints**: The five-item rule (constitution Principle I). Functions hold at most 25 lines, five parameters, and five logical blocks. Log output uses ASCII only. No secret appears in a log record. No new environment variable.

**Scale/Scope**: One operator at a time per web portal process. Three new routes, one new package, and one shared module used by two portals.

## Constitution Check

*Gate: passes before research. Re-checked after design: passes with the recorded exceptions in Complexity Tracking.*

| Principle or rule | Gate | Evidence in this plan |
| - | - | - |
| I. Five-item rule | No new child under a noncompliant parent. Each new directory holds five children or fewer. | The new package sits under `src/mist/access/auth/`, which holds two children (R-78). The new folders hold at most five children each (table below). No new child goes into `web_portal/`, `web_portal/routes/`, `src/interfaces/portals/`, `tests/unit/web_portal/`, or `tests/e2e/web_portal/`. |
| II. Class-based architecture | Behavior sits in named classes. No wrapper function. | Classes: `SignInBlueprint`, `TwoStepLogin`, `PendingSignInStore`, `ProcessSessionHolder`, `SessionLifetime`, `LoginClassifier`, `CloudCatalog`. `default_cloud_login` in the capture module is removed, and its call site uses `TwoStepLogin.build_session`. |
| III. Safety first | Safe input, early validation, no secret in output. | The email passes `normalize_email` before use (R-28). The cloud passes the catalog check (R-24) before the SDK call. No `input()` or `getpass()` runs in a request (FR-015). Redaction tests scan logs and bodies (T020). |
| IV. Full deployment pipeline | Gates, rebase, pull request, CI, merge, image revision. | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE. The agent does not merge without authorization. |
| V. Observability and logging | ASCII only, levels as stated, no secret. | The log contract is in `design/contracts/log-records.md`. |
| VI. Inline comments | Each executable line carries a comment. | Task acceptance criteria require it for each new and edited file. T-LOCAL-GATES reviews the changed lines. |
| VII. Action logging | An info record before each action and a debug record after it. | The log contract lists each SDK call and each holder write. |
| Mist Cloud: mistapi only | Every REST call uses a working `mistapi` function. | `login.login.login`, `login.two_factor.twoFactor`, and `self.self.getSelf` (R-58, R-59). No direct HTTP. No owned WebSocket transport. |
| Mist Cloud: SDK contract tests | Tests prove SDK insufficiency, authentication, endpoint parity, failure safety, and redaction. | T018 and T020 (spec section "Mist Cloud Transport Requirements"). |
| Output backends | Not applicable. The feature exports no data. | No `DataExporter` call. |
| Database keys | Not applicable. No endpoint strategy is added. | No entry in `ENDPOINT_PRIMARY_KEY_STRATEGIES`. |
| Data directory | Not applicable. The feature writes no product output. | No file write. |
| Container security | Not applicable. The container image is unchanged. | The container keeps its token path (D-12). |
| Zscaler and proxy | Not applicable. No container build or push changes. | None. |
| Adding menu operations | Not applicable. No menu operation changes. | `MistHelper.py` menu table unchanged. |
| Security findings | No suppression comment is added. | Bandit runs on the new package (T-LOCAL-GATES). |
| Multi-agent git | Issue first, claim, overlap check, one concern per pull request. | Task T001 records the overlap with PR #4208 (R-86). Task T-PR opens one pull request. |
| Required labels | Type label, scope label, and status label. | `feature` and `web-portal` already exist (R-80). `in-progress` is claimed in the status file. |

For repository structure and generated files:

- The commit subject and the pull request title use the Conventional Commits form.
- The change adds one record under `specs/numbered/0/0/1/2/4/2/2/1/` and one fragment under `changelog.d/`.
- Existing folder debt is recorded in Complexity Tracking, with separate remediation actions.
- Product output stays under `data/`. This feature writes none.

For a feature that uses Juniper Mist Cloud:

- REST requests use `mistapi.api.v1.login.login.login`, `mistapi.api.v1.login.two_factor.twoFactor`, and `mistapi.api.v1.self.self.getSelf`.
- The contract tests prove that the SDK login path prompts for input (`__api_session.py:508`, `__api_session.py:525`, and `__api_session.py:1137`). They also prove the token list and the retry count.
- The feature adds no owned transport. No SDK path loses output, so the owned-transport exception does not apply.

## Five-Item Rule Assessment

Counts come from the remote tree on `main` (R-77 to R-79). Counts after the change use the new children of this feature.

| Directory | Children on main | Children after the change | Result | Action |
| - | - | - | - | - |
| `src/mist/access/auth/` | 2 | 3 | Pass | Add `browser/` |
| `src/mist/access/auth/browser/` | 0 | 5 | Pass at five | New: `__init__.py`, `routes.py`, `state/`, `cloud/`, `templates/` |
| `src/mist/access/auth/browser/state/` | 0 | 5 | Pass at five | New: `__init__.py`, `holder.py`, `lifetime.py`, `outcome.py`, `pending.py` |
| `src/mist/access/auth/browser/cloud/` | 0 | 3 | Pass | New: `__init__.py`, `catalog.py`, `login.py` |
| `src/mist/access/auth/browser/templates/` | 0 | 2 | Pass | New: `sign_in.html`, `two_factor.html` |
| `web_portal/` | 7 | 7 | Debt, grandfathered | Narrow edit of `app.py` only |
| `web_portal/templates/` | 5 | 5 | Pass at five | Narrow edit of `base.html` only |
| `web_portal/routes/` | 9 | 9 | Debt, grandfathered | No change |
| `src/interfaces/portals/` | 6 | 6 | Debt, grandfathered | No change |
| `src/interfaces/portals/upgrade_portal/app/routes/` | 13 | 13 | Debt, grandfathered | Narrow edit of `auth.py` only |
| `tests/unit/marvis/mist/access/auth/` | 2 | 3 | Pass | Add `browser/` |
| `tests/unit/marvis/mist/access/auth/browser/` | 0 | 5 | Pass at five | New: `__init__.py` and four test modules |
| `tests/e2e/` | 5 | 5 | Pass at five | No new child |
| `tests/e2e/web_portal/` | 32 | 32 | Debt, grandfathered | Narrow edit of `test_portal_smoke.py` only |
| `tests/unit/web_portal/` | 52 | 52 | Debt, grandfathered | No change |
| `tests/contract/upgrade_portal/` | 66 | 66 | Debt, grandfathered | Narrow edit of `test_auth.py` only |
| `changelog.d/` | 335 | 336 | Allowed process folder | One unique fragment |
| `specs/numbered/0/0/1/2/4/2/2/1/` | 0 | 1 | Allowed process record | One record folder |

## Architecture

```text
Browser
  -> web_portal/app.py registers SignInBlueprint
       -> src/mist/access/auth/browser/routes.py  (SignInBlueprint)
            -> state/pending.py    PendingSignInStore, keyed by browser identifier
            -> cloud/catalog.py    CloudCatalog, host check against clouds.py
            -> cloud/login.py      TwoStepLogin: build_session, password step, 2FA step, getSelf
            -> state/outcome.py    LoginClassifier and the failure sentences
            -> state/lifetime.py   SessionLifetime from session_expiry
            -> state/holder.py     ProcessSessionHolder, one lock, writes the holders
                 -> app.config["APISESSION"], app.config["ORG_ID"]
                 -> MainEntrypoint.context.apisession (read by SourceDependencyResolver)

Upgrade capture portal (port 8056)
  -> src/interfaces/portals/upgrade_portal/app/routes/auth.py
       imports state/pending.py, state/outcome.py, cloud/catalog.py, cloud/login.py
       keeps its routes, its replay call, and its identity registry
```

Each sign-in step follows the same order. Validate the input first. Log an info record. Call the SDK. Log a debug record with the result. Classify the answer. Return one sentence on failure.

## File-by-File Change Map

### Add

| Path | Holds | Requirement IDs |
| - | - | - |
| `src/mist/access/auth/browser/__init__.py` | Package marker with one module note | FR-016 |
| `src/mist/access/auth/browser/routes.py` | `SignInBlueprint`: sign-in, 2FA, and sign-out routes, lifetime hook, active-run refusal, `Cache-Control` header | FR-001, FR-003, FR-007, FR-008, FR-014, FR-017 |
| `src/mist/access/auth/browser/state/__init__.py` | Package marker | FR-016 |
| `src/mist/access/auth/browser/state/pending.py` | `PendingSignIn` and `PendingSignInStore` (300 seconds, 64 records, lock) | FR-004, FR-010, FR-012 |
| `src/mist/access/auth/browser/state/lifetime.py` | `SessionLifetime` for `session_expiry` (10 to 20160) | FR-009 |
| `src/mist/access/auth/browser/state/outcome.py` | `LoginState`, `LoginOutcome`, `LoginClassifier`, and `SignInMessage` | FR-011, FR-013 |
| `src/mist/access/auth/browser/state/holder.py` | `ProcessSessionHolder`: one lock, writes app config and `MainEntrypoint.context` | FR-007, FR-018 |
| `src/mist/access/auth/browser/cloud/__init__.py` | Package marker | FR-016 |
| `src/mist/access/auth/browser/cloud/catalog.py` | `CloudCatalog` and the default host constants, moved from the capture module | FR-002, FR-016 |
| `src/mist/access/auth/browser/cloud/login.py` | `TwoStepLogin`: `build_session`, `password_step`, `two_factor_step`, `resolve_org_id` | FR-005, FR-006, FR-011, FR-015, FR-018 |
| `src/mist/access/auth/browser/templates/sign_in.html` | Sign-in form with `data-testid` attributes and the CSRF field | FR-001, FR-002, FR-014 |
| `src/mist/access/auth/browser/templates/two_factor.html` | 2FA form with `data-testid` attributes and the CSRF field | FR-003, FR-014 |
| `tests/unit/marvis/mist/access/auth/browser/__init__.py` | Package marker | Test layout, D-16 |
| `tests/unit/marvis/mist/access/auth/browser/test_sign_in_state.py` | Store, lifetime, classifier, and holder tests | FR-004, FR-009 to FR-013 |
| `tests/unit/marvis/mist/access/auth/browser/test_two_step_login.py` | SDK path tests, SDK insufficiency contract, retry and token contract | FR-005, FR-006, FR-011, FR-015 |
| `tests/unit/marvis/mist/access/auth/browser/test_sign_in_routes.py` | Flask client tests for the routes | FR-001 to FR-003, FR-007, FR-008, FR-014 |
| `tests/unit/marvis/mist/access/auth/browser/test_sign_in_contract.py` | Sentences, redaction, documentation text, digest use | FR-004, FR-013, FR-017, FR-020 |
| `changelog.d/issue-4936-web-portal-sign-in.md` | One `Added` entry that names issue 4936 | FR-020 |

The record folder `specs/numbered/0/0/1/2/4/2/2/1/4936-web-portal-sign-in/` receives the files from `DRAFT_DIR`. The orchestrator copies them, not this change.

### Modify

| Path | Change | Requirement IDs |
| - | - | - |
| `wsgi.py` | Replace the `_resolve_org_id` body (lines 64 to 75) with `TwoStepLogin.resolve_org_id`. Extend the warning text at line 59 to name the sign-in form. Keep the bootstrap calls at lines 48 to 53. | FR-018, FR-019 |
| `web_portal/app.py` | Register `SignInBlueprint.create()` in `_register_blueprints` (lines 182 to 202). Create `ProcessSessionHolder` in `_inject_dependencies`. Add `signed_in` and `signed_in_account` to the context processor (lines 249 to 253). | FR-001, FR-007, FR-008 |
| `web_portal/templates/base.html` | Add one navigation item that links to `/auth/signin` or `/auth/signout`, with a `data-testid`. | FR-001, FR-008 |
| `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | Remove the definitions that the shared package defines (see the removal list). Import them from the shared package. Replace `default_cloud_login` with `TwoStepLogin.build_session` at the seam in `run_login`. Update the call sites of the moved names. The routes, the replay call at line 411, and the identity registry keep their behavior. | FR-016, FR-021 |
| `tests/contract/upgrade_portal/test_auth.py` | Add one test that the capture portal reads the shared store and refuses a second factor with no pending sign-in. | FR-021, SC-005 |
| `tests/e2e/web_portal/test_portal_smoke.py` | Add one test that renders `/auth/signin` and checks the `data-testid` attributes. | FR-001, FR-014 |
| `documentation/wiki/Web-Portal.md` | Rewrite the "Sign in to Mist" section (lines 26 to 40). Remove the "Issue #4936 tracks" sentence and the "no sign-in form" sentence. | FR-020 |
| `documentation/operator-guide.md` | Update the table rows at lines 575 to 579 and the sentence at line 627. Add the browser sign-in row for the web portal. | FR-020 |
| `documentation/cli-reference.md` | Replace "The page has no sign-in form." at line 28 with the form path. | FR-020 |
| `documentation/api/admins/POST_login.md` | Replace "in two places" at line 122 with "in three places", and name the browser sign-in call site. | FR-020 |
| `documentation/api/admins/POST_login_two_factor.md` | Replace "in two places" at line 91 with "in three places", and name the browser 2FA call site. | FR-020 |

Files not changed: `web_portal/services/operation.py`, `web_portal/routes/operations.py`, `src/foundation/support/refactors/main_entrypoint.py`, `src/operations/exporting/ex_hardware_inventory/*`, `deploy/.env.example`, `requirements.txt`, and `.github/workflows/*`.

### Removal list in the capture module

Remove these definitions from `src/interfaces/portals/upgrade_portal/app/routes/auth.py`, after their call sites move to the shared package:

- Constants: `PENDING_SECONDS`, `PENDING_LIMIT`, `_PENDING_LOCK`, `_PENDING`, `STATE_OK`, `STATE_TWO_FACTOR`, `STATE_RATE_LIMITED`, `STATE_REFUSED`, `RATE_LIMIT_MARKERS`, `TWO_FACTOR_FIELD`, `AUTHENTICATED_FIELD`, `STATUS_CODE_FIELD`, `ERROR_FIELD`, `MESSAGE_FIELD`, `DEFAULT_CLOUD_HOST`, `DEFAULT_CLOUD_LABEL`, `CLOUDS_MODULE`, `CLOUDS_ATTRIBUTE`, `PROJECT_ROOT`.
- Classes: `PendingSignIn`, `LoginOutcome`.
- Functions: `cloud_catalog`, `resolve_host`, `failure_text`, `rate_limit_marked`, `two_factor_wanted`, `login_state`, `purge_pending`, `remember_pending`, `read_pending`, `drop_pending`, `default_cloud_login`.

Task T014 confirms each name with a search before removal. A name still used by the capture routes stays in the capture module.

## Dependencies

- No new package. `mistapi` stays at 0.64.1 (R-43).
- The browser package imports `src.interfaces.portals.upgrade_portal.runtime.identity` for `email_digest` and `normalize_email` (D-13). The import is a recorded debt.
- The browser package imports `src.mist.access.auth.interactive.clouds` for `MIST_CLOUDS` (R-32).
- The import order is one way. `auth.py` imports the browser package. The browser package does not import `auth.py`.

## Risks and Mitigations

| Risk | Likelihood | Mitigation |
| - | - | - |
| The capture portal regresses after the move. | Medium | Keep the routes and the replay unchanged. Run the contract tests, the unit tests for the capture auth, and the two `pytest-chunks` commands for the portal trees. |
| An open pull request conflicts on `web_portal/app.py` and `web_portal/templates/base.html` (PR #4208, R-86). | High | Task T001 checks the state of PR #4208 before the first edit. Rebase after that pull request merges. |
| A process session change breaks a running operation. | Low | `ProcessSessionHolder` writes under one lock. The routes refuse the change while `get_active_runs()` is not empty (D-17). |
| A menu reader keeps the old session. | Medium | Task T013 searches for readers of the legacy module attribute and of `ORG_ID` (U-6). Each reader found receives the new value. |
| The live 2FA path differs from the fake SDK. | Medium | The owner checks the live path in issue #4925 (U-1). The code follows the documented steps (R-58) and the SDK check of `two_factor_required` (`__api_session.py:1131` and `__api_session.py:1132`). |
| A secret appears in an exception message or a log record. | Low | Log the exception class name only, as the capture module does. Redaction tests scan the records (T020). |
| The Mist refusal text leaks to the page. | Low | The page shows only the failure sentence for the code. The Mist text stays in the debug record without the password. |
| A wrong `session_expiry` value ends the session early. | Low | The bounds check (10 to 20160) treats an out-of-range value as absent (FR-009). |
| The symbol gate reports the moved names as lost. | High | Task T-LOCAL-GATES records each moved name in the pull request body. The reviewer confirms that each name exists in the shared package (U-7). |
| The docs guard `tests/guardrails/test_hardware_shell_lock_docs.py` fails after the edits. | Medium | Task T-LOCAL-GATES runs the guard. The edits keep the sentences that the guard reads. |
| The five-item count grows in a noncompliant parent. | Low | The table above lists the parents. No task adds a child to a debt parent. |

## Rollback Steps

1. Revert the squash commit of the pull request on `main`. The change holds no stored data, so no data migration runs.
2. Restart the web portal. The process session returns to the startup token or to no session, as before the change.
3. Check that the capture portal starts and answers `/auth/signin` with its own page.
4. Confirm that `tests/contract/upgrade_portal/test_auth.py` passes on the reverted tree.

## Complexity Tracking

| Violation or debt | Why it is needed | Simpler alternative rejected because |
| - | - | - |
| A Flask blueprint sits in the `mist` package (`src/mist/access/auth/browser/routes.py`). | `web_portal/routes/` (9 children) and `src/interfaces/portals/` (6 children) cannot take a new child (R-77). | A new child in either parent breaks the five-item rule. |
| The browser package imports two pure functions from the capture `identity` module. | The functions have 24 production and 30 test call sites (D-13). | Moving them changes every call site in one change. |
| The new unit test folder sits under `tests/unit/marvis/mist/access/auth/`. | `tests/unit/web_portal/` (52 children) and `tests/e2e/web_portal/` (32 children) cannot take a child (R-77). | A new child in either parent breaks the five-item rule. |
| The capture 2FA retry defect stays in the capture module. | The defect is separate from the web portal scope (D-15). | Fixing it here mixes two concerns in one pull request. |

Separate remediation actions, each tracked in its own issue:

- **RM-1**: Move `SignInBlueprint` into `src/interfaces/portals/` after `web_portal/routes/` and `src/interfaces/portals/` are split into nested packages.
- **RM-2**: Move `email_digest` and `normalize_email` into a neutral module, and update the 24 production and 30 test call sites.
- **RM-3**: Split `web_portal/routes/` and `tests/unit/web_portal/` into nested packages. This removes the grandfathered debt in R-77.
- **RM-4**: Fix the capture 2FA retry. Task T028 files this issue with the evidence in R-26.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/4/2/2/1/4936-web-portal-sign-in/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      http-api.md
      sdk-calls.md
      log-records.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
src/mist/access/auth/browser/
  __init__.py
  routes.py
  state/
    __init__.py
    holder.py
    lifetime.py
    outcome.py
    pending.py
  cloud/
    __init__.py
    catalog.py
    login.py
  templates/
    sign_in.html
    two_factor.html

tests/unit/marvis/mist/access/auth/browser/
  __init__.py
  test_sign_in_contract.py
  test_sign_in_routes.py
  test_sign_in_state.py
  test_two_step_login.py
```

**Structure Decision**: The package sits under the compliant parent `src/mist/access/auth/`. The test folder sits under the compliant parent `tests/unit/marvis/mist/access/auth/`. Both follow the layout of the existing `interactive/` folders.
