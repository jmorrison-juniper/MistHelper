# Contract: SDK calls of the browser sign-in

This contract lists each Mist call that the browser sign-in makes. It maps each HTTP answer to a state. It also lists the calls that the feature must never make. The line references identify lines in the installed `mistapi` 0.64.1 source in `.venv\Lib\site-packages\mistapi`. They also identify lines in the OpenAPI file.

## Calls in order

| Step | Call | Request | Answer and mapping |
| - | - | - | - |
| 1. Build | `mistapi.APISession(email=email, password=password, host=host, console_log_level=20, show_cli_notif=False)` | Constructor only, no REST call | Then clear the token list (`_apitoken = []`), reset the index (`_apitoken_index = -1`), and set `_MAX_429_RETRIES = 0`. The constructor reads `MIST_APITOKEN` and related variables (`__api_session.py` lines 360 to 370), so the clear step is required. `_MAX_429_RETRIES` defaults to 3 (`__api_request.py` line 59). |
| 2. Password step | `mistapi.api.v1.login.login.login(session, {"email": e, "password": p})` | POST `/api/v1/login` (`login.py` line 37, and OpenAPI line 3089) | 200: go to step 3. 400: `bad_credentials`. 429: `rate_limited`. Connection fault: `network_fault`. |
| 3. Profile check | `mistapi.api.v1.self.self.getSelf(session)` | GET `/api/v1/self` (`self.py` line 32, and OpenAPI line 25460) | 200 with `two_factor_required` true: open the 2FA step. 200 with the flag false: the sign-in is accepted. Other status: `bad_credentials`. |
| 4. 2FA step | `mistapi.api.v1.login.two_factor.twoFactor(session, {"two_factor": code})` | POST `/api/v1/login/two_factor` (`two_factor.py` line 37, and OpenAPI line 3247) | 200: go to step 3. 401: `bad_two_factor_code`. 404: the account has no 2FA, so go to step 3. 429: `rate_limited`. Connection fault: `network_fault`. |
| 5. Lifetime | Same `getSelf` answer | None | `session_expiry` as an integer from 10 to 20160 gives the lifetime. Any other value gives the unknown state. The OpenAPI field is at line 68000. |
| 6. Organization | Same `getSelf` answer | None | `MIST_ORG_ID` when set. Otherwise the first privilege that holds an `org_id`. The rule matches `wsgi.py` lines 55 and 64 to 75 (R-03). |

Each step writes one info record before its call and one debug record after it (`design/contracts/log-records.md`).

## Calls that must not happen in a browser request

| Call | Reason |
| - | - |
| `APISession.login()` | It prompts with `input()` for the login name (`__api_session.py` line 508) and `getpass()` for the password (line 525). It prompts with `input()` for the 2FA code (line 1137). |
| `APISession.login_with_return()` | Its retry needs the password that the SDK cleared after the first call (`__api_session.py` lines 744, 859, and 895 to 896). |
| `APISession._two_factor_authentication()` | Private method. |
| `APISession._process_login()` | It calls `set_password()`, which prompts with `getpass()` when the password is empty (line 733). |
| Any `input()` or `getpass()` call | A web request has no keyboard (FR-015). |

## Answers that the SDK does not return

The SDK does not return a 2FA state directly. The portal reads `two_factor_required` from the profile answer of step 3. The SDK applies the same test in `_getself` (`__api_session.py` lines 1131 and 1132) and in `login_with_return` (line 901).

## Flag of the SDK

The SDK sets `_authenticated` only in its own login methods (`__api_session.py` lines 745, 796, 851, and 938). The browser sign-in does not set this flag. Every code path that reads the session uses the profile answer or the REST calls, not the flag (research D-4).
