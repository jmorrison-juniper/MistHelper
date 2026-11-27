# Tasks: Browser sign-in with 2FA for the web portal

**Input**: Numeric record `specs/numbered/0/0/1/2/4/2/2/1/4936-web-portal-sign-in/`. Required: `plan.md` and `spec.md`. Supporting: `design/research.md`, `design/data-model.md`, and `design/contracts/`.

**Organization**: Tasks are grouped in phases. Each task names its requirement IDs, its exact paths, its acceptance statement, its verification command, and its status.

## Format

- **[P]**: The task can be done in parallel. It touches a different file, and it has no dependency on an open task.
- **Requirements**: The FR and SC IDs that the task covers. A process task names the process.
- **Files**: Exact repository paths. Each path is relative to the repository root.
- **Acceptance**: The result that the task must show before its status changes.
- **Verify**: One command from the local gates table, or the test names that the task creates.
- **Status**: `open`, `verified-present`, `partial`, or `absent`. `absent` means the target is missing on `main` (R-73 to R-76). `verified-present` means the anchor exists on `main`. `partial` means an open pull request overlaps the target (R-86).

Every new Python line carries an inline comment on the same line. Every new Markdown file passes the STE gate.

## Phase 1: Coordination

- [ ] **T001** Check the state of open pull request #4208 before any edit to `web_portal/app.py` or `web_portal/templates/base.html`.
  - Requirements: process (this task is a prerequisite for FR-014 and FR-020).
  - Files: none changed. Records the result in `analysis.md`.
  - Acceptance: The pull request is open with overlap on both files (R-86). Either it merged first, or the branch rebases after it merges. Also check for overlap with open pull requests again at T-PR.
  - Verify: `gh pr view 4208 -R jmorrison-juniper/MistHelper --json state,mergedAt,files`
  - Status: partial

## Phase 2: Shared package (state and cloud)

- [ ] **T002** [P] Create the package markers of the shared package.
  - Requirements: FR-016.
  - Files: `src/mist/access/auth/browser/__init__.py`, `src/mist/access/auth/browser/state/__init__.py`, `src/mist/access/auth/browser/cloud/__init__.py`.
  - Acceptance: Each file holds one module note and no code. The parent `src/mist/access/auth/` holds three children after the change (R-78).
  - Verify: `python -m py_compile src/mist/access/auth/browser/__init__.py src/mist/access/auth/browser/state/__init__.py src/mist/access/auth/browser/cloud/__init__.py`
  - Status: absent

- [ ] **T003** [P] Implement `PendingSignIn` and `PendingSignInStore` in the pending module.
  - Requirements: FR-004, FR-010, FR-012.
  - Files: `src/mist/access/auth/browser/state/pending.py`. The source logic is in `src/interfaces/portals/upgrade_portal/app/routes/auth.py` lines 140 to 141, 143 to 186, and 498 to 566 (R-21, R-23).
  - Acceptance: The store keys records by browser identifier. A record ends after 300 seconds. The store holds at most 64 records. `PendingSignIn` holds no password, no code, and no token. Its `__repr__` names only the digest and the host.
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_state.py -k pending -q`
  - Status: absent

- [ ] **T004** [P] Implement `LoginState`, `LoginOutcome`, `LoginClassifier`, and `SignInMessage` in the outcome module.
  - Requirements: FR-011, FR-013.
  - Files: `src/mist/access/auth/browser/state/outcome.py`. The source logic is in `auth.py` lines 128 to 134, 188 to 215, 415 to 497 (R-22).
  - Acceptance: The classifier reads the success flag, `two_factor_required`, HTTP 429, and throttle text. `SignInMessage` holds the eight sentences of the spec table, each one sentence with no semicolon.
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_state.py -k classifier -q`
  - Status: absent

- [ ] **T005** [P] Implement `SessionLifetime` in the lifetime module.
  - Requirements: FR-009.
  - Files: `src/mist/access/auth/browser/state/lifetime.py`.
  - Acceptance: The class reads `session_expiry` from the profile and accepts 10 to 20160 minutes (R-60). Any other value gives the unknown state. The unknown state sets no timer, and the caller logs one warning.
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_state.py -k lifetime -q`
  - Status: absent

- [ ] **T006** [P] Implement `CloudCatalog` in the catalog module.
  - Requirements: FR-002, FR-016.
  - Files: `src/mist/access/auth/browser/cloud/catalog.py`. Reads `MIST_CLOUDS` from `src/mist/access/auth/interactive/clouds.py` (R-32). The source logic is in `auth.py` lines 239 to 283 and the constants at lines 103 and 104 (R-24).
  - Acceptance: The class returns the label and host pairs. The host check accepts only a host from the catalog. An unknown host returns the default host and logs one warning.
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_routes.py -k unknown_cloud -q`
  - Status: absent

- [ ] **T007** Implement `TwoStepLogin` in the login module, with `build_session`, `password_step`, `two_factor_step`, and `resolve_org_id`.
  - Requirements: FR-005, FR-006, FR-011, FR-015, FR-018.
  - Files: `src/mist/access/auth/browser/cloud/login.py`. The builder logic comes from `default_cloud_login` in `auth.py` lines 304 to 336 (R-24, R-25). The organization rule comes from `wsgi.py` lines 55 and 64 to 75 (R-03).
  - Acceptance: `build_session` clears the token list, sets `_MAX_429_RETRIES` to 0, and passes `console_log_level=20` and `show_cli_notif=False`. `password_step` calls `mistapi.api.v1.login.login.login` on one session. `two_factor_step` calls `mistapi.api.v1.login.two_factor.twoFactor` on the same session. Both steps call `getSelf` and accept only when `two_factor_required` is false. No method calls `input()`, `getpass()`, `APISession.login()`, or `login_with_return()`.
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_two_step_login.py -q`
  - Status: absent

- [ ] **T008** [P] Write the two templates of the sign-in pages.
  - Requirements: FR-001, FR-002, FR-003, FR-014.
  - Files: `src/mist/access/auth/browser/templates/sign_in.html`, `src/mist/access/auth/browser/templates/two_factor.html`.
  - Acceptance: Each page extends `base.html`. Each form holds the `csrf_token()` field and posts to its route. Each input has a `data-testid` attribute: `sign-in-email`, `sign-in-password`, `sign-in-cloud`, `sign-in-submit`, `two-factor-code`, and `two-factor-submit`. The password input has `autocomplete="current-password"`. Each page shows the failure sentence in a region with `data-testid="sign-in-error"`.
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_routes.py -k get_sign_in_form -q`
  - Status: absent

## Phase 3: Routes and wiring

- [ ] **T009** Implement `SignInBlueprint` in the routes module.
  - Requirements: FR-001, FR-003, FR-007, FR-008, FR-014, FR-017.
  - Files: `src/mist/access/auth/browser/routes.py`.
  - Acceptance: The blueprint serves `GET` and `POST` at `/auth/signin`, `GET` and `POST` at `/auth/twofactor`, and `POST` at `/auth/signout` (D-10). Each response carries `Cache-Control: no-store`. A browser form post gets a 303 redirect. A script call gets the JSON body that `design/contracts/http-api.md` defines. A `before_app_request` hook ends an expired session. The routes issue the browser identifier cookie `misthelper_browser`, a random token with HttpOnly and SameSite Lax. The `run_active` refusal uses `get_active_runs()` (R-12, R-15). Each route logs an info record before its SDK call and a debug record after it.
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_routes.py -q`
  - Status: absent

- [ ] **T010** Register the blueprint and the holder in the web portal factory.
  - Requirements: FR-001, FR-007, FR-008.
  - Files: `web_portal/app.py`. The anchors are `app.config["APISESSION"]` at line 155, and the middleware call at line 178. Further anchors are `_register_blueprints` at line 182 (operations registration at line 202), and `_register_context_processor` at line 249 (R-04, R-05, R-06).
  - Acceptance: `_register_blueprints` registers `SignInBlueprint.create()` before the webhook registration. `_inject_dependencies` creates one `ProcessSessionHolder` and stores it under `app.config["PROCESS_SESSION"]`. The context processor adds `signed_in` and `signed_in_account`. No new function sits outside the class.
  - Verify: `python -m pytest tests/unit/web_portal -k "allowlist or csrf" -q`
  - Status: partial (R-86)

- [ ] **T011** Add the sign-in navigation item to the base template.
  - Requirements: FR-001, FR-008.
  - Files: `web_portal/templates/base.html`. The anchor is the `csrf-token` meta tag at line 6 (R-16).
  - Acceptance: The navigation shows "Sign in" with a link to `/auth/signin` when `signed_in` is false. It shows the account name and a sign-out form that posts to `/auth/signout` when `signed_in` is true. The sign-out form carries the CSRF field. The elements have `data-testid` attributes.
  - Verify: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -k sign_in -q`
  - Status: partial (R-86)

- [ ] **T012** Update the startup bootstrap in `wsgi.py`.
  - Requirements: FR-018, FR-019.
  - Files: `wsgi.py`. The anchors are the warning at line 59 (R-01), the bootstrap at lines 48 to 53 (R-02), and `_resolve_org_id` at lines 64 to 75 (R-03).
  - Acceptance: The warning keeps the prefix `WSGI: API auth failed (%s)` and names the sign-in form in its suffix. `_resolve_org_id` is removed, and the call uses `TwoStepLogin.resolve_org_id`. The bootstrap keeps the environment and token path. The portal starts with no session when the bootstrap fails (FR-019).
  - Verify: `python -m py_compile wsgi.py`
  - Status: verified-present

- [ ] **T013** Implement `ProcessSessionHolder` and audit the legacy readers.
  - Requirements: FR-007, FR-017, FR-018.
  - Files: `src/mist/access/auth/browser/state/holder.py`. The read-only audit covers `MistHelper.py` and `src/`. It uses the anchors `src/foundation/support/refactors/main_entrypoint.py` lines 55 and 64 and 367 to 381. It also uses `src/foundation/runtime/config/source_dependency_resolver.py` line 24 (R-39, R-40, R-41).
  - Acceptance: `replace` writes `app.config["APISESSION"]`, `app.config["ORG_ID"]`, and `MainEntrypoint.context.apisession` under one lock. `clear` writes `None` to the same holders. The audit records each reader of the module attribute `apisession` and of the environment variable `ORG_ID`. Each reader found receives the new value in the same write, or the record names the reason that it does not.
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_contract.py -k holders_share -q`
  - Status: verified-present

- [ ] **T014** Move the shared capture logic out of the capture module.
  - Requirements: FR-016, FR-021.
  - Files: `src/interfaces/portals/upgrade_portal/app/routes/auth.py`. The moved names are listed in `plan.md` under "Removal list in the capture module". The anchors are lines 68 and 69 (paths), 140 and 141 (pending constants), and 239 to 283 (catalog and host). Further anchors are line 304 (default login), lines 331 and 333 (token and retries), and line 411 (replay call). The last anchors are line 899 (run function) and lines 1100 to 1243 (replay and routes) (R-20 to R-27).
  - Acceptance: Each moved name is defined once, in the shared package. `run_login` uses `TwoStepLogin.build_session` as its builder when no seam is injected. The replay at line 411 and the routes keep their behavior. Each name still used by the capture routes stays in the capture module. Run the removal search before each deletion, and record the results in the pull request.
  - Verify: `python -m pytest tests/contract/upgrade_portal/test_auth.py tests/unit/upgrade_portal/test_auth.py tests/unit/upgrade_portal/test_identity.py -q`
  - Status: verified-present

- [ ] **T015** Import the two identity helpers in the shared package and verify the import graph.
  - Requirements: FR-017.
  - Files: `src/mist/access/auth/browser/routes.py` and `src/mist/access/auth/browser/cloud/login.py`. The helpers are `email_digest` (R-28, line 145) and `normalize_email` (R-28, line 186).
  - Acceptance: Both modules import the helpers from `src.interfaces.portals.upgrade_portal.runtime.identity`. The import of the new package does not import `auth.py`. No cycle forms.
  - Verify: `python -c "import src.mist.access.auth.browser.routes"`
  - Status: absent

## Phase 4: Tests

- [ ] **T016** [P] Create the package marker of the new test folder.
  - Requirements: D-16.
  - Files: `tests/unit/marvis/mist/access/auth/browser/__init__.py`.
  - Acceptance: The file holds one module note. The folder then holds five children, which is the limit.
  - Verify: `python -m py_compile tests/unit/marvis/mist/access/auth/browser/__init__.py`
  - Status: absent

- [ ] **T017** [P] Write the state tests.
  - Requirements: FR-004, FR-009, FR-010, FR-011, FR-012, FR-013.
  - Files: `tests/unit/marvis/mist/access/auth/browser/test_sign_in_state.py`.
  - Tests (9): `test_pending_store_expires_after_300_seconds`, `test_pending_store_drops_oldest_record_at_cap_64`, `test_pending_store_replaces_record_for_same_browser`, `test_pending_store_drop_removes_record`, `test_pending_record_repr_holds_no_secret`, `test_classifier_reads_success_flag_as_ok`, `test_classifier_reads_two_factor_required_as_two_factor`, `test_classifier_reads_429_and_throttle_text_as_rate_limited`, and `test_lifetime_reads_session_expiry_and_rejects_out_of_range_values`.
  - Acceptance: Each test uses a fake clock or a fake answer and checks one behavior. Each test fails on the behavior it names when the behavior is removed.
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_state.py -q`
  - Status: absent

- [ ] **T018** [P] Write the SDK path tests.
  - Requirements: FR-005, FR-006, FR-011, FR-015, FR-018.
  - Files: `tests/unit/marvis/mist/access/auth/browser/test_two_step_login.py`.
  - Tests (9): `test_build_session_clears_token_list_and_sets_retries_to_zero`, `test_password_step_calls_login_function_on_one_session`, `test_two_factor_step_calls_two_factor_function_on_same_session`, `test_accepts_session_only_when_two_factor_required_is_false`, `test_sdk_login_path_prompts_for_input_contract`, `test_http_400_on_password_step_is_refused`, `test_http_401_on_two_factor_step_is_wrong_code`, `test_http_429_maps_to_rate_limited_and_connection_fault_maps_to_network_fault`, and `test_resolve_org_id_prefers_environment_then_first_privilege`.
  - Acceptance: The fake HTTP layer records each URI. The SDK contract test patches `builtins.input` and proves that `APISession.login()` asks for input when the account requires a code (`__api_session.py:1137`). No test uses a production credential (AGENTS.md, tests section).
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_two_step_login.py -q`
  - Status: absent

- [ ] **T019** [P] Write the route tests.
  - Requirements: FR-001, FR-002, FR-003, FR-007, FR-008, FR-014, SC-001.
  - Files: `tests/unit/marvis/mist/access/auth/browser/test_sign_in_routes.py`.
  - Tests (10): `test_get_sign_in_form_renders_fields_and_no_store_header`, `test_post_sign_in_with_wrong_password_shows_bad_credentials_sentence`, `test_post_sign_in_requiring_2fa_opens_two_factor_page_without_session`, `test_post_two_factor_code_sets_process_session_and_redirects`, `test_post_wrong_code_keeps_pending_sign_in_open`, `test_post_code_without_pending_sign_in_shows_two_factor_expired`, `test_sign_out_clears_process_session_and_pending_sign_in`, `test_sign_in_refused_while_operation_runs`, `test_post_without_csrf_token_is_refused`, and `test_unknown_cloud_host_uses_default_and_logs_one_warning`.
  - Acceptance: The tests use the Flask test client and a fake SDK. Each test checks the status code, the redirect or JSON body, and the sentence. The two-factor code test follows the journey to the dashboard (SC-001).
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_routes.py -q`
  - Status: absent

- [ ] **T020** [P] Write the contract tests.
  - Requirements: FR-004, FR-013, FR-017, FR-020, SC-003, SC-004, SC-006.
  - Files: `tests/unit/marvis/mist/access/auth/browser/test_sign_in_contract.py`.
  - Tests (6): `test_each_failure_sentence_is_one_plain_sentence`, `test_logs_and_bodies_never_hold_password_or_code`, `test_logs_use_email_digest_not_address`, `test_holders_share_one_value_after_sign_in`, `test_docs_no_longer_say_no_sign_in_form_or_track_4936`, and `test_missing_session_expiry_logs_one_warning_and_sets_no_timer`.
  - Acceptance: The redaction test reads the captured log records and each response body. The documentation test reads the four changed pages and the changelog fragment. Each test prints the count of records or files that it examined (AGENTS.md, guard rule).
  - Verify: `python -m pytest tests/unit/marvis/mist/access/auth/browser/test_sign_in_contract.py -q`
  - Status: absent

- [ ] **T021** Extend the capture contract test module with one test.
  - Requirements: FR-016, FR-021, SC-005.
  - Files: `tests/contract/upgrade_portal/test_auth.py`. The fake `login_with_return` is at line 82 (R-33).
  - Tests (1): `test_capture_portal_reads_shared_pending_store_and_refuses_code_without_pending`.
  - Acceptance: The test asserts that the capture portal reads the shared store and refuses a second factor with no pending sign-in. The count of passed tests in the module equals the count before the change, plus one.
  - Verify: `python -m pytest tests/contract/upgrade_portal/test_auth.py -q`
  - Status: verified-present

- [ ] **T022** Extend the portal smoke module with two tests.
  - Requirements: FR-001, FR-014, FR-019.
  - Files: `tests/e2e/web_portal/test_portal_smoke.py` (R-64).
  - Tests (2): `test_sign_in_form_renders_with_test_ids_and_allowlist_refuses_blocked_address` and `test_startup_without_session_still_serves_sign_in_form`.
  - Acceptance: The first test renders `/auth/signin` with the Flask client from `tests/e2e/conftest.py` (R-65). It checks each `data-testid` value. It checks that a blocked address gets 403. The second test builds the app with no session and checks that `/auth/signin` answers 200 and that the portal logs the bootstrap warning.
  - Verify: `python -m pytest tests/e2e/web_portal/test_portal_smoke.py -q`
  - Status: verified-present

## Phase 5: Documents and changelog

- [ ] **T023** [P] Update the web portal page.
  - Requirements: FR-020, SC-006.
  - Files: `documentation/wiki/Web-Portal.md`. The anchors are the heading at line 26, the "no sign-in form" sentence at line 28, and the start command at line 33. The tracking sentence is at line 39 (R-47, R-48).
  - Acceptance: The section names the sign-in form, the 2FA step, the session lifetime, the sign-out form, and all eight failure sentences. The section keeps the start command of the terminal path. The tracking sentence is removed.
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/wiki/Web-Portal.md`
  - Status: verified-present

- [ ] **T024** [P] Update the operator guide.
  - Requirements: FR-020, SC-006.
  - Files: `documentation/operator-guide.md`. The anchors are the section at line 566, the table rows at lines 575 to 579, and the tracking sentence at line 627 (R-49, R-50).
  - Acceptance: The table row for the web portal with a login names the browser sign-in. The row for the container names the browser sign-in and the token. The tracking sentence is removed. The text keeps the caution about the session lifetime.
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/operator-guide.md`
  - Status: verified-present

- [ ] **T025** [P] Update the CLI reference row.
  - Requirements: FR-020.
  - Files: `documentation/cli-reference.md` (R-51, line 28).
  - Acceptance: The row names the sign-in form path `/auth/signin`, and it no longer says that the page has no sign-in form.
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/cli-reference.md`
  - Status: verified-present

- [ ] **T026** [P] Update the two API login pages.
  - Requirements: FR-020.
  - Files: `documentation/api/admins/POST_login.md` (R-52, line 122) and `documentation/api/admins/POST_login_two_factor.md` (R-53, line 91).
  - Acceptance: Each page says "in three places" and names the browser call site of the web portal.
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80 documentation/api/admins/POST_login.md documentation/api/admins/POST_login_two_factor.md`
  - Status: verified-present

- [ ] **T027** [P] Write the changelog fragment.
  - Requirements: FR-020.
  - Files: `changelog.d/issue-4936-web-portal-sign-in.md`.
  - Acceptance: One `###` heading, one `Added` bullet that names issue 4936. The fragment follows `changelog.d/README.md` (R-71).
  - Verify: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4936-web-portal-sign-in.md`
  - Status: absent

- [ ] **T028** [P] File the issue for the capture 2FA retry defect.
  - Requirements: D-15, RM-4.
  - Files: none. The issue cites `src/interfaces/portals/upgrade_portal/app/routes/auth.py` line 411 (R-26), the fake at `tests/contract/upgrade_portal/test_auth.py` line 82 (R-33), and `__api_session.py` lines 744 and 859.
  - Acceptance: The issue has the labels `bug` and `web-portal`. It names the evidence and the fix path. It does not change this pull request.
  - Verify: `gh issue list -R jmorrison-juniper/MistHelper --label web-portal --search "2FA retry" --json number,title,labels`
  - Status: absent

## Phase 6: Delivery

- [ ] **T-LOCAL-GATES** Run each local gate that applies to the changed files.
  - Requirements: FR-001 to FR-021, SC-001 to SC-006.
  - Files: all changed files.
  - Gates that apply (R-45, R-46):
    - Compile: `python -m py_compile` on each changed Python file.
    - Lint: `python -m ruff check .`
    - Format: `python -m black --check .`
    - Types: `python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml`
    - Tests: `python -m pytest` on each changed test file, and `python -m pytest tests/unit/ex_hardware_inventory/scope -q` for SC-002.
    - Full tests: the two `pytest-chunks` commands for the portal trees, because `auth.py` changes.
    - Coverage: `python -m pytest tests --ignore=tests/e2e --cov=src --cov-report=`, with 80 percent or above.
    - Test quality: `test-quality-analyzer --gate` with the committed config and baseline.
    - Complexity: `radon cc src/mist/access/auth/browser -j | complexity-gate --max 10`.
    - Security lint: `bandit -c pyproject.toml -r src/mist/access/auth/browser -q` and `bandit -c pyproject.toml -r web_portal -q`.
    - Code quality: `pylint src/ --fail-under=9.5`.
    - Dead code: `vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70`.
    - Docstrings: `pydocstyle src/ wsgi.py web_portal` and `interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90`.
    - Symbols: `symbol-diff --base origin/main` on each changed Python file, with the moved names recorded.
    - STE: `ste-linter --config .ste-linter.toml --min-score 80` on each changed Markdown file.
  - Gates that do not apply, with the reason:
    - Menu reference: no menu change.
    - Safe sweep `python MistHelper.py --test`: no menu operation changes.
    - Dependency audit `pip-audit -r requirements.txt`: no dependency change.
    - Ops portal and ops platform gates: no change under `ops-portal/` or `mist-ops-platform/`.
  - Move-a-module gates for the moved names of `auth.py`:
    - Guardrails: `python -m pytest tests/guardrails`.
    - Nested source package guard: `python -m pytest tests/guardrails/test_move_module_guidance.py`.
    - Five-item guard: `python -m pytest tests/guardrails/test_process_folder_structure.py`.
    - Import smoke: `python -c "import src.mist.access.auth.browser.routes"`.
    - Old-path search: `git grep -n "PendingSignIn\|cloud_catalog\|resolve_host"` in tracked text files. Explain each hit.
  - Acceptance: Each gate prints its result. Each failed gate is repaired or recorded with its cause. The symbol gate output lists each moved name, and the pull request names the new location of each name (U-7).
  - Verify: the commands above, in the order of the local gates table.
  - Status: open

- [ ] **T-PR** Commit, push, and open the pull request.
  - Requirements: process (FR-020 and the Conventional Commits rule).
  - Files: the changed files, added by explicit path. The record folder is added only when the orchestrator copies it into `specs/numbered/0/0/1/2/4/2/2/1/`.
  - Steps: Create the worktree with `git worktree add ../MistHelper-feat-4936 -b feat/4936-web-portal-sign-in origin/main`. Run the overlap check with `gh pr list --json number,headRefName,files` again. Add the changed files by explicit path. Commit with the subject `feat(web-portal): add browser sign-in with 2FA`, the body line `Closes #4936`, and the Co-authored-by trailer. Push the branch with `git push -u origin feat/4936-web-portal-sign-in`. Open the pull request into `main` with the title `feat(web-portal): add browser sign-in with 2FA`. The body names the changed files, the local gate results, the moved names, the rollback steps, and `Closes #4936`. After the pull request exists, rename the fragment to `pr-` plus the pull request number, with `.md`.
  - Acceptance: The pull request targets `main`, carries `Closes #4936`, and passes the title check. The label `in-progress` is on the issue.
  - Verify: `gh pr view feat/4936-web-portal-sign-in -R jmorrison-juniper/MistHelper --json number,title,body,baseRefName`
  - Status: open

- [ ] **T-REMOTE-CI** Watch the remote checks.
  - Requirements: process (constitution Principle IV, step 8).
  - Files: none.
  - Steps: Run `gh pr checks feat/4936-web-portal-sign-in --watch`. Wait for CodeQL, which takes two to three minutes after the other gates (copilot-instructions.md, git section). Read each failed job. Repair each failure in a new commit on the same branch, and rerun the local gate of that failure.
  - Acceptance: Every required check passes on the latest commit, and CodeQL reports no new finding.
  - Verify: `gh pr checks feat/4936-web-portal-sign-in -R jmorrison-juniper/MistHelper`
  - Status: open

- [ ] **T-MERGE** Enable auto-merge after the orchestrator authorizes the merge.
  - Requirements: process (constitution Principle IV, steps 9 to 12).
  - Files: none.
  - Steps: Add the `auto-merge` label only after every check is green and the orchestrator authorizes the merge (copilot-instructions.md, git section). After the squash merge, wait for `container-build.yml` on the merged revision. Verify that the image revision label equals the merged commit SHA. The deploy and the health check run only after the orchestrator approves them.
  - Acceptance: The merged commit appears on `main`. The container build for that commit passes. The revision label matches the merged SHA. The branch and the worktree are removed.
  - Verify: `gh pr view feat/4936-web-portal-sign-in -R jmorrison-juniper/MistHelper --json state,mergedAt,mergeCommit`
  - Status: open

## Dependencies

- T001 precedes T010 and T011.
- T002 precedes T003, T004, T005, T006, T007, and T008.
- T003, T005, and T006 precede T007.
- T004 and T007 precede T009.
- T009 precedes T010, T013, T015, and T019.
- T007 precedes T012 and T018.
- T003, T004, T006, and T007 precede T014.
- T016 precedes T017 to T020.
- T017 needs T003, T004, and T005.
- T019 needs T009, T010, and T013.
- T020 needs T009, T013, and T023 to T026.
- T021 needs T014.
- T022 needs T008, T010, and T011.
- T023 to T028 can be done in parallel after their dependencies.
- T-LOCAL-GATES needs T002 to T028 complete.
- T-PR needs T-LOCAL-GATES complete.
- T-REMOTE-CI needs T-PR complete.
- T-MERGE needs T-REMOTE-CI complete and the orchestrator authorization.

## Counts

- Tasks: 32 (T001 to T028, T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE).
- Tests planned: 37 (T017 with 9, T018 with 9, T019 with 10, T020 with 6, T021 with 1, and T022 with 2).
