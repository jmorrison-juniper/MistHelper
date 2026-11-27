# Research: Browser sign-in with 2FA for the web portal

Each decision names the alternatives, the chosen option, the reason, and the risk. Remote facts come from GitHub `main` in `jmorrison-juniper/MistHelper`, checked on 2026-11-26. SDK facts come from the installed `mistapi` 0.64.1 source in `.venv`. Mist API facts come from the local OpenAPI file.

## Decision summary

| ID | Decision | Human decision | Recommended option |
| - | - | - | - |
| D-1 | Accept a Mist password in a browser form on the web portal | Yes | Accept it on every allowed address |
| D-2 | Build the sign-in in the web portal and reuse the capture code through one shared package | No | Shared package |
| D-3 | One process-wide Mist session replaced by the sign-in | Yes | Process-wide session |
| D-4 | Use two public SDK calls on one SDK session for the password and 2FA steps | No | Public SDK calls |
| D-5 | Take the session lifetime from `session_expiry` in the admin profile | No | `session_expiry` |
| D-6 | Keep no local wrong-code counter | No | Pending window and Mist 429 |
| D-7 | Map Mist 429 to one sentence and disable SDK retries on login calls | No | Retries disabled |
| D-8 | Use the existing CSRF protection | No | Existing CSRFProtect |
| D-9 | Use the same IP allowlist and add no setting | No | Same allowlist |
| D-10 | Use the paths `/auth/signin`, `/auth/twofactor`, and `/auth/signout` | No | Capture paths |
| D-11 | Place the code in `src/mist/access/auth/browser/` with its Flask blueprint | No | Mist package placement |
| D-12 | Keep the startup token bootstrap and serve the sign-in page when it fails | No | Keep bootstrap |
| D-13 | Import the digest and the email normalizer from the capture `identity` module | No | Import, record debt |
| D-14 | Take the organization from `MIST_ORG_ID`, then from the first organization privilege | No | Existing rule |
| D-15 | Keep the capture 2FA retry defect out of this change and file an issue | No | Separate issue |
| D-16 | Place new tests in a new unit folder and extend two existing modules | No | Unit folder |
| D-17 | Write session holders under one lock and refuse a change while an operation runs | No | Refuse during runs |

## D-1. Accept a Mist password in a browser form (HUMAN-DECISION-REQUIRED)

- **Alternatives**: (a) Accept the password and the 2FA code in the browser on every allowed address. (b) Accept the browser password only on loopback, and require an API token in a container. (c) Keep token-only sign-in and document a user API token from the Mist portal.
- **Decision**: (a). This option is the recommended option.
- **Reason**: The web portal has no user authentication (R-11). The allowlist is the only control. Any allowed visitor already runs the `safe` and `interactive_safe` operations with the process session (R-12, R-13). The form adds no new network reach. The password is not stored, logged, or echoed (FR-004). A token needs a manual step in the Mist portal. The operator guide states that a token never asks for a 2FA code (`documentation/operator-guide.md`, section "Sign in for an MSP run").
- **Risk**: An allowed visitor who knows a password can switch the process session to that account. Mitigations are the allowlist, the account name shown on each page, sign-out, and the logging rules.
- **Human action**: Confirm the credential policy for browser password entry before the pull request merges.

## D-2. Build the sign-in in the web portal and reuse the capture code

- **Alternatives**: (a) Copy the capture portal code into the web portal. (b) Import the capture route module from the web portal. (c) Move the pure logic into one shared package under `src/mist/access/auth/browser/` and import it from both portals.
- **Decision**: (c).
- **Reason**: The capture code already holds the cloud catalog (R-24), the pending store (R-23), the classifier (R-22), and the host check (R-24). The issue asks for reuse, not a copy. The capture route module also imports the capture `identity` registry and Flask routes (R-28), so importing that module would couple the two portals.
- **Risk**: The move changes the capture portal file. Mitigation: the capture contract tests (R-33) and the portal test gates in the local gates table (R-46).

## D-3. One process-wide Mist session replaced by the sign-in (HUMAN-DECISION-REQUIRED)

- **Alternatives**: (a) One process session, replaced by each successful sign-in. (b) One session per browser, as the issue proposal states. (c) One session per menu run.
- **Decision**: (a). This option is the recommended option.
- **Reason**: The menu operations read the shared session through `SourceDependencyResolver.apisession` (R-38), which reads the active `AppContext` (R-39, R-41). The `MistHelper.py` module declares `apisession` as an annotation and names `MainEntrypoint.context` as its owner (local line 2552, not fetched from `main`). Per-browser sessions would require each operation to accept a session argument. The web portal also keeps one `app.config` session (R-04).
- **Risk**: The last successful sign-in replaces the session for every browser. Mitigations are the refusal during runs (D-17), sign-out, and the account name shown on every page.
- **Human action**: Confirm the change from the issue proposal item 2, "one session for each browser", before implementation. This choice sets which Mist account every allowed visitor uses, so it is a credential policy.

## D-4. Use two public SDK calls on one SDK session

- **Alternatives**: (a) Call `mistapi.api.v1.login.login.login` and then `mistapi.api.v1.login.two_factor.twoFactor` on one SDK session, then call `getSelf`. (b) Call `APISession.login()`. (c) Replay `login_with_return(email, password, two_factor)` and keep the password for the pending window. (d) Keep the capture replay `login_with_return(two_factor=code)`. (e) Call the private `_two_factor_authentication` method.
- **Decision**: (a).
- **Reason**: `APISession.login()` prompts with `input()` for the login name (`__api_session.py:508`), with `getpass()` for the password (`__api_session.py:525`), and with `input()` for the 2FA code (`__api_session.py:1137`). A web request has no keyboard. Option (c) keeps the password in memory for 300 seconds, which FR-004 forbids. Option (d) fails because the SDK clears the password after a successful first login (`__api_session.py:744`), and `login_with_return` needs it (`__api_session.py:859`). The capture retry omits both fields (R-26). Issue #4755 fixed the same omission in the CLI path (R-30). Option (e) uses private API. The public functions post through `mist_post` (`__api_request.py:279-294`), which has no login guard. `getSelf` supplies the profile, and the scope code also uses `getSelf` (R-37).
- **Risk**: The SDK flag `_authenticated` stays unset (`__api_session.py:127`, and `_set_authenticated` at `__api_session.py:938`). Mitigation: the portal stores its own state, and the scope code reads `getSelf`, not the flag. The live behavior is unverified (U-1).

## D-5. Take the session lifetime from `session_expiry`

- **Alternatives**: (a) Read `session_expiry` from `getSelf` and accept 10 through 20160 minutes. (b) Use 1440 minutes for every account. (c) Set no local timer.
- **Decision**: (a).
- **Reason**: The admin schema defines `session_expiry` as the session lifetime for the admin, in minutes, with minimum 10 and maximum 20160 (R-60). The value 1440 is the default of the organization field, which is a different field (`documentation/mist-api-openapi31yaml.yaml`, organization schema near line 88873). The repository holds no admin default, so option (b) would invent a value. Option (c) breaks the issue requirement.
- **Risk**: The field can be absent (U-3). Rule: when the value is absent or outside the range, the portal sets no local timer and logs one warning. Mist refusal then ends the session.

## D-6. Keep no local wrong-code counter

- **Alternatives**: (a) Count wrong codes and stop after a fixed number. (b) Keep no counter. The pending window of 300 seconds and the Mist 429 response bound the attempts. (c) Drop the pending sign-in after one wrong code.
- **Decision**: (b).
- **Reason**: The repository holds no number for the Mist limit, so option (a) would invent a value (U-2). The capture portal keeps the pending record after a wrong code, so the operator can read a new code (`auth.py`, function `check_two_factor`, R-27). The pending window is 300 seconds (R-21).
- **Risk**: The operator can try several codes within one window. Mitigation: Mist counts the attempts and answers 429, and the window closes after 300 seconds.

## D-7. Map Mist 429 to one sentence and disable SDK retries on login calls

- **Alternatives**: (a) Keep the SDK default of 3 retries for HTTP 429 (`__api_request.py:59`). (b) Set the retry count to 0 on the login SDK session. (c) Add a portal-level retry loop.
- **Decision**: (b).
- **Reason**: A retry repeats a credential post. The capture portal already sets the count to 0 (R-25). Option (c) has no repository value to base a delay on.
- **Risk**: A short throttle fails the sign-in. Mitigation: the rate-limit sentence tells the operator to wait.

## D-8. Use the existing CSRF protection

- **Alternatives**: (a) Use the existing `CSRFProtect` with the `csrf-token` meta tag (R-08, R-16) and a hidden field from `csrf_token()`. (b) Add a second token.
- **Decision**: (a).
- **Reason**: The control already covers every browser form. A second token would duplicate it.
- **Risk**: Script callers must send the `X-CSRFToken` header. The existing CSRF error handler answers JSON for API callers (`web_portal/services/config.py`, function `_register_csrf_error_handler`).

## D-9. Use the same IP allowlist and add no setting

- **Alternatives**: (a) Use the existing `before_request` allowlist and fallback (R-09). (b) Add a separate allowlist for sign-in.
- **Decision**: (a).
- **Reason**: A second setting would drift from the first one. The operator guide already documents `PORTAL_ALLOWED_IPS` (R-56).
- **Risk**: None new. The sign-in pages inherit the same access rule.

## D-10. Use the paths `/auth/signin`, `/auth/twofactor`, and `/auth/signout`

- **Alternatives**: (a) Use the capture portal paths (R-20, R-54). (b) Use `/login` and `/login/2fa`.
- **Decision**: (a).
- **Reason**: One term names one concept. The capture portal and the web portal then share one vocabulary.
- **Risk**: The same paths exist on two ports. Each port runs in its own process, so the paths do not collide.

## D-11. Place the code in `src/mist/access/auth/browser/`

- **Alternatives**: (a) `src/mist/access/auth/browser/`, including the Flask blueprint. (b) `web_portal/routes/`. (c) `src/interfaces/portals/`. (d) The root of `web_portal/`.
- **Decision**: (a).
- **Reason**: The parent `src/mist/access/auth/` holds two children (R-78), so one new package fits the five-item rule. Options (b), (c), and (d) hold 9, 6, and 7 children (R-77). Flask blueprints already exist under `src/mist` (R-42).
- **Risk**: The `mist` package then holds one Flask blueprint, which is a layering cost. The cost is recorded in the plan under Complexity Tracking.

## D-12. Keep the startup token bootstrap

- **Alternatives**: (a) Keep the `wsgi.py` bootstrap (R-01, R-02) and serve the sign-in page when it fails. (b) Exit when no session exists. (c) Remove the bootstrap.
- **Decision**: (a).
- **Reason**: Option (b) stops the container, and the issue asks for a sign-in in the running portal. Option (c) removes the token path, which the operator guide documents. When the bootstrap fails, the existing `except` branch already catches the end-of-input error that the SDK raises in a container.
- **Risk**: The log line changes from "maps and execution disabled" to a line that names the sign-in page.

## D-13. Import the digest and the email normalizer from the capture `identity` module

- **Alternatives**: (a) Import `email_digest` and `normalize_email` from `identity.py` (R-28). (b) Move both functions to the shared package and update every call site. (c) Write a new digest in the shared package.
- **Decision**: (a). The import is a recorded debt.
- **Reason**: The two functions are pure and short. A local search finds 24 production call sites in nine files, and 30 test call sites in eight files. Option (b) would change all of them. Option (c) would create two digests, and log records from the two portals could no longer be joined.
- **Risk**: The shared package depends on one capture module. Mitigation: a remediation issue (T028 and analysis A-11).

## D-14. Take the organization from `MIST_ORG_ID`, then from the first organization privilege

- **Alternatives**: (a) Use the existing rule of `wsgi.py` (R-03). (b) Require `MIST_ORG_ID`. (c) Show an organization picker after sign-in.
- **Decision**: (a).
- **Reason**: The rule already exists. Option (b) fails for an MSP account with no environment value. Option (c) adds a page flow that the issue does not ask for.
- **Risk**: An account with no organization privilege has no organization. The portal shows the no-organization sentence (FR-013).

## D-15. Keep the capture 2FA retry defect out of this change

- **Alternatives**: (a) Fix the capture retry in this change by reusing the two-step function. (b) Keep the defect and file a separate issue. (c) Leave the defect undocumented.
- **Decision**: (b).
- **Reason**: The capture behavior would change in a change that targets the web portal. AGENTS.md asks for one concern for each pull request. Option (c) hides a known risk.
- **Risk**: The capture 2FA step stays broken until the issue closes. Mitigation: task T028 files the issue with the evidence in R-26 and R-33.

## D-16. Place new tests in a new unit folder and extend two existing modules

- **Alternatives**: (a) A new unit folder `tests/unit/marvis/mist/access/auth/browser/` with four modules and one `__init__.py`, plus two extended existing modules. (b) A new module under `tests/e2e/web_portal/`. (c) New modules under `tests/unit/web_portal/`.
- **Decision**: (a).
- **Reason**: The parent `tests/unit/marvis/mist/access/auth/` holds two children (R-78), so the new folder fits. The parents `tests/e2e/web_portal/` (32 children) and `tests/unit/web_portal/` (52 children) cannot take a new child (R-77).
- **Risk**: The layout differs from the web portal test folders. The plan records the reason.

## D-17. Write session holders under one lock and refuse a change while an operation runs

- **Alternatives**: (a) Refuse sign-in and sign-out while `get_active_runs()` returns runs, and write the holders under one lock. (b) Queue the change until the runs end. (c) Stop the running operations.
- **Decision**: (a).
- **Reason**: The executor already reports active runs (R-12, R-15). A change in the middle of a run could split one run across two accounts. Option (c) destroys operator work.
- **Risk**: An operator waits for a run to finish before a sign-in. The refusal sentence names that cause.

## Remote verification

Each row is one check that runs against `main` (ref `main`). The result column uses `present`, `absent`, `partial`, or `stale`. For an absent claim, `present` means the claim holds, and `absent` means the item is missing on `main`. The line column gives the first line of the range. The count of rows is 86, and the same 86 rows appear in `4936-STATUS.json`.

| ID | Claim | Path | Blob SHA | Result | Line |
| - | - | - | - | - | - |
| R-01 | Startup warning names the failed API auth and the disabled maps and execution | `wsgi.py` | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 59 |
| R-02 | Bootstrap calls the interactive `apisession.login()` on the env-file and environment paths | `wsgi.py` | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 49 |
| R-03 | Organization resolves from `MIST_ORG_ID`, then from `getSelf` privileges | `wsgi.py` | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 55 |
| R-04 | Session stored in `app.config["APISESSION"]` | `web_portal/app.py` | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 155 |
| R-05 | Security middleware with the allowlist applied in `create_app` | `web_portal/app.py` | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 178 |
| R-06 | Blueprint registration, the operations blueprint, and the context processor | `web_portal/app.py` | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 182 |
| R-07 | `PORTAL_ALLOWED_IPS` defaults to an empty value | `web_portal/services/config.py` | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 83 |
| R-08 | CSRF protection initialized through `CSRFProtect` in `_configure_csrf` | `web_portal/services/config.py` | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 297 |
| R-09 | Allowlist check registered as a `before_request` hook | `web_portal/services/config.py` | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 273 |
| R-10 | Session-expired sentence for CSRF failures | `web_portal/services/config.py` | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 33 |
| R-11 | Docstring states that the portal has no user authentication and cites issue #1933 | `web_portal/services/config.py` | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 12 |
| R-12 | Active runs listed through `executor.get_active_runs()` | `web_portal/routes/operations.py` | c7ef542129a0764a55ba18f2a1c9a2d6c5573754 | present | 173 |
| R-13 | Operation routes read `APISESSION`, and the executor caches its session | `web_portal/routes/operations.py` | c7ef542129a0764a55ba18f2a1c9a2d6c5573754 | present | 269 |
| R-14 | Executor stores `apisession`, and no other `_apisession` read exists in the file | `web_portal/services/operation.py` | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 928 |
| R-15 | `get_active_runs` is defined | `web_portal/services/operation.py` | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 997 |
| R-16 | CSRF token meta tag in the base template | `web_portal/templates/base.html` | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 6 |
| R-17 | No password input in the five web portal templates | `web_portal/templates/base.html` | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | 0 |
| R-18 | No password input in the WebSockets page | `src/mist/realtime/websocket_streams/web/templates/websockets_page.html` | cba30182879ba6788f78d36e963da1556006e03e | absent | 0 |
| R-19 | No file under `web_portal/` or `src/mist/realtime/` has a sign-in, login, or two-factor name | `web_portal/` and `src/mist/realtime/` | none | absent | 0 |
| R-20 | Sign-in and second-factor paths | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 68 |
| R-21 | Pending window of 300.0 seconds and a cap of 64 records | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 140 |
| R-22 | State constants, `failure_text`, `rate_limit_marked`, and `login_state` | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 128 |
| R-23 | Pending record class, store functions, and store lock | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 143 |
| R-24 | Cloud catalog, host check, and default cloud login | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 239 |
| R-25 | SDK token list cleared and 429 retries set to 0 before a login | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 331 |
| R-26 | Second-factor retry calls `login_with_return(two_factor=code)` without email or password | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 411 |
| R-27 | Run, finish, replay, check, and route functions of the capture sign-in | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 899 |
| R-28 | Shared helpers `email_digest`, `normalize_email`, `sign_in`, and `sign_out` | `src/interfaces/portals/upgrade_portal/runtime/identity.py` | 07098e4fb4510c295f385c037ef5230ec6509bf0 | present | 145 |
| R-29 | `CredentialMode` enumeration | `src/interfaces/portals/upgrade_portal/runtime/identity.py` | 07098e4fb4510c295f385c037ef5230ec6509bf0 | present | 355 |
| R-30 | CLI replay sends email and password (issue #4755 fix) | `src/mist/access/auth/interactive/login_orchestrator.py` | fd475be9467068e6c34a819697c3c46235801047 | present | 189 |
| R-31 | CLI prompt text `Enter 2FA code:` | `src/mist/access/auth/interactive/credential_prompter.py` | e1b5197a78e7ec5993faa7dd66eed9c8a553336c | present | 57 |
| R-32 | `MIST_CLOUDS` catalog | `src/mist/access/auth/interactive/clouds.py` | 15556189fd246e2f5aafef837feb804733ab45ee | present | 13 |
| R-33 | Recording fake `login_with_return` accepts `two_factor` only | `tests/contract/upgrade_portal/test_auth.py` | c864b183df3d67d9ad490b6004896c599d33828c | present | 82 |
| R-34 | `--web-portal` and `--login` flags | `MistHelper.py` | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7402 |
| R-35 | Terminal login branch runs before the portal starts | `MistHelper.py` | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6922 |
| R-36 | Scope and organization count lines of the hardware inventory | `src/operations/exporting/ex_hardware_inventory/console.py` | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 45 |
| R-37 | Scope profile supplied by `getSelf` | `src/operations/exporting/ex_hardware_inventory/scope/profile.py` | fb745bedeac7e0e955f80256f2affd43f72ef7c6 | present | 97 |
| R-38 | Menu reads the shared session through `SourceDependencyResolver.apisession` | `src/operations/exporting/ex_hardware_inventory/operation.py` | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 253 |
| R-39 | `apisession` maps to the active context | `src/foundation/runtime/config/source_dependency_resolver.py` | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 24 |
| R-40 | `AppContext` holds `apisession`, and `clear_session` drops it | `src/foundation/support/refactors/main_entrypoint.py` | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 55 |
| R-41 | `MainEntrypoint.context` is the live context, and `activate_context` sets it | `src/foundation/support/refactors/main_entrypoint.py` | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 367 |
| R-42 | Flask Blueprint already lives under `src/mist` | `src/mist/realtime/websocket_streams/web/blueprint/registry.py` | d984a6fb5b3e63ec9778459969a07fc621d3ca80 | present | 5 |
| R-43 | `mistapi` pinned to 0.64.1 | `requirements.txt` | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R-44 | Python 3.15 or newer | `pyproject.toml` | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-45 | Path variables for mypy, vulture, pydocstyle, and interrogate | `.github/workflows/ci.yml` | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-46 | Local gates table | `.github/copilot-instructions.md` | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-47 | Sign-in heading, start command, and no-form sentence in the web portal page | `documentation/wiki/Web-Portal.md` | e9dac116b73e6284b46cb6220ec0ca75228fe90c | present | 26 |
| R-48 | Issue #4936 tracking sentence in the web portal page | `documentation/wiki/Web-Portal.md` | e9dac116b73e6284b46cb6220ec0ca75228fe90c | present | 39 |
| R-49 | Sign-in section and two table rows in the operator guide | `documentation/operator-guide.md` | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 566 |
| R-50 | Issue #4936 tracking sentence in the operator guide | `documentation/operator-guide.md` | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 627 |
| R-51 | The `--web-portal` row says the page has no sign-in form | `documentation/cli-reference.md` | 2c171a635ea45241626110575e4b4fe9ed3e4f71 | present | 28 |
| R-52 | API page says MistHelper calls the login endpoint in two places | `documentation/api/admins/POST_login.md` | e3c382ede91b7e0587ffa84e4f7eaecafae044b8 | present | 122 |
| R-53 | API page says MistHelper completes the 2FA step in two places | `documentation/api/admins/POST_login_two_factor.md` | 98aeb3e81b08c956dc1137f04a833f33220a7bb2 | present | 91 |
| R-54 | Capture portal table gives the sign-in and second-factor paths | `documentation/upgrade_capture_portal.md` | 97fc51f98df43dff874b22330efb274e625054a8 | present | 34 |
| R-55 | MSP support page links to the operator guide sign-in anchor | `documentation/wiki/MSP-Support.md` | 350d19953fcee4790d7d01bca8715f22a813c4d2 | present | 34 |
| R-56 | `PORTAL_ALLOWED_IPS` example in the environment template | `deploy/.env.example` | 7137364423308485be734a391798d85c6a37eaf4 | present | 164 |
| R-57 | Architecture table names `src/mist/access/auth/` for authentication and session flows | `documentation/architecture.md` | b4cab54be36d223b7eba879ca99b838f508938ce | present | 271 |
| R-58 | Login and two-factor paths in the OpenAPI file | `documentation/mist-api-openapi31yaml.yaml` | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 3089 |
| R-59 | `getSelf` operation on `/api/v1/self` | `documentation/mist-api-openapi31yaml.yaml` | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25460 |
| R-60 | Admin schema `session_expiry` in minutes, minimum 10, maximum 20160 | `documentation/mist-api-openapi31yaml.yaml` | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68000 |
| R-61 | Two-factor required example for the login response | `documentation/mist-api-openapi31yaml.yaml` | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 51892 |
| R-62 | JSON twin of the OpenAPI file exists | `documentation/mist-api-openapi31json.json` | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 0 |
| R-63 | Allowlist unit test module exists | `tests/unit/web_portal/test_config_ip_allowlist.py` | 129ee6d8cb0341f3ade145ca38226a5d81661ce4 | present | 0 |
| R-64 | Portal smoke e2e module exists | `tests/e2e/web_portal/test_portal_smoke.py` | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 0 |
| R-65 | Shared e2e fixtures module exists | `tests/e2e/conftest.py` | e450e1855770d2e0ec587935a95233262b118ae1 | present | 0 |
| R-66 | CLI login tests exist | `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py` | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 0 |
| R-67 | Docs guard exists for the operator guide and the web portal page | `tests/guardrails/test_hardware_shell_lock_docs.py` | 83926b3fbc870c5b69ba48dd5a0a2591ae183ed6 | present | 0 |
| R-68 | Five-item guard baseline exists | `tests/guardrails/process_folder_baseline.json` | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R-69 | Constitution exists | `.specify/memory/constitution.md` | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| R-70 | Agent rules exist | `AGENTS.md` | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R-71 | Changelog fragment rule exists | `changelog.d/README.md` | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| R-72 | Reference record spec exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R-73 | Target route folder is absent | `specs/numbered/0/0/1/2/4/2/2/1/` | none | absent | 0 |
| R-74 | No legacy record for 4936 exists under `specs/` | `specs/` | none | absent | 0 |
| R-75 | New browser package and browser test folder are absent | `src/mist/access/auth/browser/` and `tests/unit/marvis/mist/access/auth/browser/` | none | absent | 0 |
| R-76 | Changelog fragment for 4936 is absent | `changelog.d/issue-4936*` | none | absent | 0 |
| R-77 | Parents above five children: `web_portal` 7, `web_portal/routes` 9, `web_portal/services` 9, `src/interfaces/portals` 6, `tests/unit/web_portal` 52, `tests/e2e/web_portal` 32 | directories listed | none | present | 0 |
| R-78 | Parents with room for one child: `src/mist/access` 4, `src/mist/access/auth` 2, `tests/unit/marvis/mist/access/auth` 2, `tests/unit/marvis/mist/access/auth/interactive` 4 | directories listed | none | present | 0 |
| R-79 | Parents at five children: `src` 5, `src/mist` 5, `src/mist/access/auth/interactive` 5, `web_portal/templates` 5, `tests/e2e` 5 | directories listed | none | present | 0 |
| R-80 | Issue #4936 is open with labels `feature` and `web-portal` and no comments | issue #4936 | none | present | 0 |
| R-81 | Issue #4755 is closed, and it records the CLI 2FA defect fix | issue #4755 | none | present | 0 |
| R-82 | Issue #4925 is open, and it covers live menu 309 and MSP validation | issue #4925 | none | present | 0 |
| R-83 | Issue #1933 is closed, and it covers the allowlist default | issue #1933 | none | present | 0 |
| R-84 | PR #4924 merged on 2026-11-26 and changed the web portal, operator guide, and API login pages | PR #4924 | none | present | 0 |
| R-85 | PR #4940 merged on 2026-11-26 and changed the web portal, operator guide, and shell-lock guard | PR #4940 | none | present | 0 |
| R-86 | PR #4208 is open and changes `web_portal/app.py` and `web_portal/templates/base.html` | PR #4208 | none | partial | 0 |

## Sources

- Installed SDK, read only, `.venv\Lib\site-packages\mistapi` (version 0.64.1, from `mistapi-0.64.1.dist-info`):
  - `__api_session.py`: `__init__` at line 55. Environment reads are at lines 360 to 370. The `set_email` input is at line 508. The `getpass` call is at line 525. `_process_login` is at line 713. The new SDK session is at line 730. The password is cleared at lines 744 and 753. `login_with_return` is at line 804. Its new session is at line 841. The check `elif self.email and self._password` is at line 859. The credentials-missing answer is at lines 895 and 896. The two-factor check is at line 901. `_two_factor_authentication` is at line 1080. Its URI is at line 1096. `_getself` is at line 1120. The two-factor check is at lines 1131 and 1132. The 2FA input is at line 1137. The retry input is at line 1185.
  - `__api_request.py`: `_MAX_429_RETRIES` is at line 59. `_request_with_retry` is at line 203. The retry loop is at line 209. The 429 retry is at line 229. `mist_post` is at line 279.
  - `api\v1\login\login.py`: `login` is at line 17. The URI is at line 37.
  - `api\v1\login\two_factor.py`: `twoFactor` is at line 17. The URI is at line 37.
  - `api\v1\self\self.py`: `getSelf` is at line 17. The URI is at line 32.
- Mist API, local OpenAPI `documentation\mist-api-openapi31yaml.yaml`. The remote lines match for R-58 to R-61. Path `/api/v1/login` is at line 3089. Path `/api/v1/login/two_factor` is at line 3247, with the 401 and 404 responses. Path `/api/v1/self` is at line 25460. `operationId: getSelf` is at line 25490. The `Admin` response is at line 60588. The admin schema is at line 67927. `session_expiry` is at lines 68000 to 68008. The organization `session_expiry` has a default of 1440 at lines 88873 to 88876. The `LoginSuccess2FArequired` example is at line 51892. `HTTP429Example` is at lines 51240 to 51243, and it describes the API token hourly threshold, not a login limit.
- Repository code, remote `main` (R-01 to R-46): see the table above.
- Repository documents, remote `main` (R-47 to R-57): see the table above.
- Local-only evidence, not fetched from `main`: `MistHelper.py` line 2552 declares `apisession` as an annotation and names `MainEntrypoint.context` as its owner (Unverified U-6). The call-site counts in D-13 come from a local search.
- Web fetch: not used. No URL is recorded.
- Skills: no local skill was loaded. The work changes Python portal code and Mist cloud login. It does not change Podman, container internals, or Juniper device behavior.

## Unverified

- **U-1**: The live behavior of the two public SDK calls with a 2FA account. No credential was used, and this step ran no live call. The fake SDK tests (T018) cover the code paths. The owner checks the live path in issue #4925.
- **U-2**: The numeric limit of login attempts and of 2FA attempts at Mist. The local OpenAPI describes a 429 response but gives no login-attempt number (R-58, R-61). `HTTP429Example` at lines 51240 to 51243 names the API token hourly threshold.
- **U-3**: Whether `GET /api/v1/self` returns `session_expiry` for every account type. The schema marks the field read only and gives bounds, but it does not state that the field always appears.
- **U-4**: Whether the Mist cloud keeps the password step state in the SDK cookie jar until the 2FA call. The OpenAPI describes the two steps (R-58) but not the cookie state.
- **U-5**: Whether the capture 2FA retry fails against the live cloud. The evidence is source only (R-26, `__api_session.py:744`, and `__api_session.py:859`). No run was made.
- **U-6**: Whether any menu code reads the `MistHelper` module attribute `apisession` that `wsgi.py` writes. The check used the local `MistHelper.py` (line 2552). The remote line was not fetched.
- **U-7**: The result of `symbol-diff` on `auth.py` after the move. The tool did not run during this step.
