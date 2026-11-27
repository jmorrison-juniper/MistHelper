# Analysis: Browser sign-in with 2FA for the web portal

This review checks `spec.md`, `plan.md`, `tasks.md`, the design files, and the code and documents on GitHub `main` (checked on 2026-11-26). It records each defect in existing work, each conflict, and each unresolved item.

## Consistency review

| Check | Result | Evidence |
| - | - | - |
| Each FR has at least one task and one test | Pass after one fix. FR-019 had no test. T022 gains a second test for the startup case. | `tasks.md` T012 and T022 |
| Each SC has a verification path | Pass after one fix. SC-002 had no direct test. The holder test (T020) and the existing scope tests cover the path. T-LOCAL-GATES runs the scope tests. | `tasks.md` T020 and T-LOCAL-GATES |
| Each task names exact paths | Pass. Each path exists in the plan change map or in the remote tree. | `plan.md` change map, and R-01 to R-86 |
| Each task has a verification command | Pass. Each command names a test from the task or a gate from the local gates table (R-46). | `tasks.md` |
| Each decision names alternatives, a choice, a reason, and a risk | Pass. Each D-ID in `research.md` has all four parts. | `research.md` D-1 to D-17 |
| Decision IDs match across files | Pass. The plan and the tasks cite D-10, D-11, D-13, D-15, D-16, and D-17 with the same meaning. | `research.md` |
| Remote IDs match across files | Pass. Each R-ID cited in the plan or tasks exists in the 86-row table. | `research.md` |
| Five-item counts | Pass. Each new folder holds five children or fewer. The `state/` folder holds five children with `holder.py`. | `plan.md` Five-Item Rule Assessment |
| Test folder count | Pass. The new test folder holds `__init__.py` and four modules. | `tasks.md` T016 to T020 |
| Test count | Pass after the fix. The total is 37 tests (9, 9, 10, 6, 1, and 2). | `tasks.md` Counts |
| Terms | Pass. "Process session", "SDK session", "pending sign-in", and "2FA step" keep one meaning each. | `spec.md` Terms |
| Phrasal verbs and contractions | Pass after one fix. The sentence "could not sign you in" became "could not authenticate you". | `spec.md` failure table |
| Mist paths | Pass. The paths used in the SDK calls match the OpenAPI paths (R-58). | `design/contracts/sdk-calls.md` |

## Defects in existing work

- **A-1 (high): The capture portal 2FA retry omits the email and the password.** The retry at `src/interfaces/portals/upgrade_portal/app/routes/auth.py` line 411 calls `login_with_return(two_factor=code)` with no credentials (R-26). The SDK clears the password after a successful first login (`__api_session.py:744`). `login_with_return` then reads `self.email and self._password` (`__api_session.py:859`). That branch fails, and the SDK returns "credentials are missing" (`__api_session.py:895` and `:896`). The capture portal then shows the wrong-code sentence. Issue #4755 fixed the same omission in the CLI path (`login_orchestrator.py` lines 200 and 201, R-30). The capture contract fake accepts `two_factor` only (R-33), so the test suite cannot detect the defect. Evidence level: source only (U-5). Action: task T028 and RM-4. This change keeps the capture behavior (D-15).
- **A-2 (low): The startup warning hides the new path.** `wsgi.py` line 59 says "maps/execution disabled" and does not name the sign-in form (R-01). Action: task T012 extends the suffix and keeps the prefix that log searches use.
- **A-3 (medium): Two API pages say the login has two call sites.** `POST_login.md` line 122 and `POST_login_two_factor.md` line 91 say "in two places" (R-52, R-53). The browser sign-in makes it three. Action: task T026.
- **A-4 (medium): Three pages say the web portal has no sign-in form.** The wiki (R-47), the operator guide (R-49), and the CLI reference (R-51) state that the page has no form. Action: tasks T023, T024, and T025.
- **A-5 (medium): One guard reads the operator guide and the wiki.** `tests/guardrails/test_hardware_shell_lock_docs.py` reads both pages (R-67). An edit that removes the text it reads breaks the guard. Action: T-LOCAL-GATES runs the guard after each documentation edit, and the edits keep the shell-lock sentences.

## Conflicts and design risks

- **A-6 (medium): Two fields share the name `session_expiry`.** The admin field gives the lifetime in minutes (R-60). The organization field has a default of 1440 (`mist-api-openapi31yaml.yaml`, line 88873). The spec uses the admin field only (D-5). The code comment in `lifetime.py` names the field, so a reader does not confuse the two.
- **A-7 (medium): The Mist 429 example names a different limit.** The example at lines 51240 to 51243 describes the API token hourly threshold (R-58). The record does not claim a login-attempt number (U-2).
- **A-8 (high): Open pull request #4208 overlaps two planned edits.** PR #4208 changes `web_portal/app.py` and `web_portal/templates/base.html` (R-86). The tasks T010 and T011 carry status `partial`. Action: task T001 checks the state before the first edit. Task T-PR repeats the overlap check.
- **A-9 (high): The symbol gate reports moved names as lost.** The gate rule says that no module-level name changes (`copilot-instructions.md`, the symbols row, R-46). This change moves names out of `auth.py`. AGENTS.md forbids a compatibility shim. The conflict stays open until T-LOCAL-GATES runs. Resolution: the pull request lists each moved name and its new location. The reviewer checks each name (U-7).
- **A-10 (medium): Grandfathered folder debt stays.** Five parents already exceed five children (R-77). The plan adds no child to them. Remediation actions RM-1, RM-2, and RM-3 track the debt.
- **A-11 (medium): The shared package imports the capture identity module.** The import covers `email_digest` and `normalize_email` (D-13, R-28). Action: RM-2.
- **A-12 (low): A Flask blueprint sits in the `mist` package.** The reason is the five-item rule (D-11, R-77). Action: RM-1.

## Gaps closed during the analysis

- **FR-019 test.** The startup case had no test. Task T022 gains the test `test_startup_without_session_still_serves_sign_in_form`.
- **SC-002 test.** The hardware preview lines have no new test. The holder test (T020) proves that the menu session changes after sign-in. The existing scope tests under `tests/unit/ex_hardware_inventory/scope/` cover the lines (changed in PR #4924, R-84). T-LOCAL-GATES runs them.
- **Browser cookie.** The sign-in issues a random browser identifier cookie. The cookie is new code, so the shared package does not import any capture cookie helper. The cookie name is `misthelper_browser`.

## Unresolved items

- **H-1 (human): Browser password entry.** D-1 needs a credential-policy decision before the pull request merges.
- **H-2 (human): One process session.** D-3 departs from the issue proposal item 2. The human decides before implementation.
- **U-1 to U-7.** These items stay open. They cover the live 2FA path, the login-attempt limit, `session_expiry`, the cookie state, the capture failure, the attribute readers, and the symbol-gate output. `research.md` lists each item with its reason.
- **Open PR #4208.** The overlap stays until the pull request merges or rebases (A-8).

## Result

The plan and the tasks cover every requirement and every success criterion. Two gaps were closed in this review. Two human decisions remain open. The capture 2FA defect is recorded as a defect, and it gets a separate issue.
