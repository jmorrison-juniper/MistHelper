# Research: Report a Mist transport fault as an unavailable Mist API

This record states each decision with its alternatives, reason, and risk. Decisions D-1 to D-11 in the STATUS file appear as sections R2 to R12. It also lists the remote and local evidence. Remote evidence comes from the `main` tree of `jmorrison-juniper/MistHelper`. Local SDK evidence comes from the installed mistapi 0.64.1 and requests packages in `.venv`. Each row in the remote verification table has one counterpart in the STATUS file.

## R1. Root cause and mechanism

The login path validates a token inside the `mistapi.APISession` constructor. Four defects follow from that design. Each defect is verified by reading source. No code was run.

- **F-01, read timeout dropped.** `_get_api_token_data` sends GET `/api/v1/self` with `timeout=30` (`.venv\Lib\site-packages\mistapi\__api_session.py` L575-576). Its broad handler catches every exception except proxy and connection errors, then returns `(None, None)` (L595-603). `requests.exceptions.ReadTimeout` subclasses `Timeout`, not `ConnectionError` (`requests\exceptions.py` L98). The token is dropped, the session has no Authorization header (`set_api_token` else branch, L563-564), and the privilege lookup returns HTTP 401. `_handle_self_failure` maps that to empty privileges (`mist-ops-platform/src/shared/services/auth.py` L133-135). The login route answers HTTP 401 (`health.py` L212-213).
- **F-02, rejected token becomes 503.** A rejected token returns HTTP 401 from the SDK check. `_get_api_token_data` raises `ValueError` outside its try block (`__api_session.py` L605-616). No try block exists in `_check_api_tokens` (L649-712, SDK-13), `set_api_token` (L529-564), or the constructor (L55 onward). `_fetch_self` catches every exception and raises `MistApiUnavailableError` (`auth.py` L116-119). The login route answers HTTP 503 (`health.py` L237-241). The existing tests patch the SDK class, so they never reach this path (F-09 in analysis).
- **F-03, another token answers for a login.** The constructor calls `_load_env` (L141). That method reads `MIST_HOST` first (L360-361) and then `MIST_APITOKEN` (L363-364). If both variables are set and the environment token validates, `_apitoken` holds the environment token. A later supplied-token check that drops the token (F-01 path) leaves the environment token in the header (L563-564). The privilege lookup then answers for the environment token. The session store keeps the supplied token, so the stored privileges and the stored token disagree.
- **F-04, every login fails with 503.** With `MIST_HOST` set and an invalid `MIST_APITOKEN`, the constructor raises `ValueError` at L363-364 through the path in F-02. `_fetch_self` maps it to HTTP 503 for every login.

Conditions for F-03 and F-04: the operator must set both `MIST_HOST` and `MIST_APITOKEN` in the process environment. The example file names `MIST_API_TOKEN` and not the SDK name (RC-45). The example file names no `MIST_HOST` key. Whether a deployment sets these names is unverified (open item U-6 in analysis).

## R2. Decision D-1: validation session that ignores the process environment

- **Decision**: Add `TokenValidationSession(mistapi.APISession)` in `auth.py`. Override `_load_env` as a no-op. Pass `host="api.mist.com"` and no `apitoken`. Then call `set_api_token(token, validate=False)`. Read `/self` through `getSelf` (D-2).
- **Alternatives considered**:
  1. Keep the constructor call with an `apitoken` argument. Rejected, because the constructor validates the environment token and the supplied token (F-02, F-03, F-04).
  2. Remove the environment variables from `os.environ` around the call. Rejected, because `validate_token` runs in worker threads and `os.environ` is process-wide.
  3. Call `requests` directly for `/api/v1/self`. Rejected, because the constitution prohibits direct HTTP to a Mist REST endpoint when a mistapi method exists.
  4. Build the session without a token and overwrite the token later. Rejected, because the constructor still validates the environment token and still reads `MIST_HOST`.
  5. Wait for a mistapi fix. Rejected, because the pin is `mistapi==0.64.1` and no fix exists in that release.
- **Reason**: The subclass removes every process-environment read and every constructor request. It needs no change to the SDK.
- **Risk**: The override depends on the private method `_load_env` (L341). Test N6 detects a change. Caution in the plan covers the risk.

## R3. Decision D-2: single-object shape for the registry entry `self_identity`

- **Decision**: Add the boolean field `single_object` (default False) to `MistEndpoint` (`mist-ops-platform/src/shared/mist/types.py` L12-13). Set it to True on `self_identity` (L188-195). When the flag is True and the status is success, `list_all_entities` returns the identity object as one row. `ApiResult.success` returns False for a None status (`endpoints.py` L52-54).
- **Alternatives considered**:
  1. Call `getSelf` directly from `auth.py`. Rejected, because it bypasses the registry. The consumer test `test_consumer_registry_usage.py` L34 and L74 expects the registry call.
  2. Keep list extraction and read the body in `auth.py`. Not possible: `_extract_list` drops a dict body before `auth.py` sees it (L312-316, RC-11).
  3. Make `_extract_list` keep dict bodies for every entity. Rejected, because every list entity would change its contract.
- **Reason**: The change is limited to one entity. The registry architecture stays. The same change resolves the `/self` part of issue #4749 (D-8).
- **Risk**: A list entity that returns a dict body by mistake now reaches callers only when its flag is set. Tests N13 to N15 check the rule.

## R4. Decision D-3: status classification

- **Decision**:
  - No HTTP status (timeout, connection error, proxy error, or a dropped exception): unavailable, HTTP 503.
  - HTTP 429 after the SDK and endpoint retries: unavailable, HTTP 503.
  - HTTP 1xx, 3xx, and 5xx: unavailable, HTTP 503.
  - HTTP 2xx without an identity object (empty body, empty list, or a non-object body): unavailable, HTTP 503.
  - HTTP 401, 403, and other 4xx except 429: empty privileges, which the login route maps to HTTP 401.
  - HTTP 2xx with an identity object: parse as today.
- **Alternatives considered**:
  1. Keep HTTP 429 as an invalid token (current code, F-05). Rejected, because a throttle is the same defect class as F-01.
  2. Map a 2xx without identity to an invalid token (current code). Rejected, because Mist answered with success.
  3. Add a new client status for a throttle. Rejected, because the contract would grow for one case.
  4. Split HTTP 429 into a separate issue. Not chosen. The same branch and the same tests fix it. A reviewer may split the issue if the policy requires one subject per issue (AGENTS, Issue-First rule).
- **Risk**: A login during a throttle returns HTTP 503. The operator sees the try-again message. This result is the intended outcome.

## R5. Decision D-4: token shape check before any request

- **Decision**: Accept only ASCII code points 33 to 126. Reject an empty token, a space, a comma, a control character, and a non-ASCII character. A rejected token returns empty privileges without a request.
- **Alternatives considered**:
  1. Pass the token to the SDK. Rejected, because the SDK splits the text on commas (`__api_session.py` L542). A comma can select a different token. A non-ASCII character can raise an error in the header encoding and then report HTTP 503 by accident.
  2. Accept any non-empty string. Rejected for the same reasons.
- **Reason**: The check validates input before use, as the constitution requires.

## R6. Decision D-5: 30-second bound through a mounted adapter

- **Decision**: Mount `_BoundedTimeoutAdapter(HTTPAdapter)` on the `https://` prefix of the session. The adapter sets `timeout=30` when the caller passes none. The class constant `TIMEOUT_SECONDS = 30` sets the value.
- **Mechanism verified**: `Session.get` passes its keyword arguments to `Session.request` (`.venv\Lib\site-packages\requests\sessions.py` L671). `Session.request` puts `timeout` in `send_kwargs` (L647). `Session.send` calls `adapter.send(request, **kwargs)` (L784). `HTTPAdapter.send` accepts the keyword (`requests\adapters.py` L634).
- **Why needed**: The SDK method `mist_get` sends the request with no timeout (`__api_request.py` L277). The old validation request had `timeout=30` (`__api_session.py` L575-576). Removing that request without a replacement removes the bound (F-06).
- **Alternatives considered**:
  1. Override `mist_get` in the subclass. Rejected, because it copies the SDK retry logic.
  2. Patch the `requests` module globally. Rejected, because every caller would change.
  3. Accept no timeout. Rejected, because a stalled Mist connection would block a login thread.
- **Risk**: The adapter uses the private attribute `_session` of the SDK object. Test N12 checks that the timeout reaches `HTTPAdapter.send`.

## R7. Decision D-6: logs and results carry types and status codes only

- **Decision**: Log the exception class name and the HTTP status code. Do not log the token, the Authorization header, the response body, or the text of an SDK exception.
- **Alternatives considered**: Log `str(error)`. Rejected, because SDK exception texts can include request details.
- **Reason**: The constitution requires redaction at the logging boundary. Test N9 checks the log records.

## R8. Decision D-7: test placement and patch targets

- **Decision**: Add the new tests to `tests/unit/api/test_auth.py` and `tests/unit/mist/test_list_status.py`. Update the patch targets in `tests/unit/api/test_session_security.py` at L338 and L369. Create no new module under `tests/unit/api/`.
- **Reason**: `tests/unit/api/` holds 11 tracked children (listed in the test directory). A new module adds a child to a noncompliant parent, which the constitution forbids. `test_auth.py` is reserved by this issue (issue #4748 comment), so the change owns it.
- **Alternatives considered**: A new test module. Rejected for the reason above.

## R9. Decision D-8: one pull request for issues #4748 and #4749

- **Decision**: One pull request closes both issues. It owns `auth.py`, `endpoints.py`, `types.py`, `test_auth.py`, `test_session_security.py`, and `test_list_status.py`.
- **Reason**: The issue comments name one owner and one pull request for the shared files. The `/self` part of #4749 is resolved by D-2. The separate #4749 candidate that changed only `endpoints.py` is superseded for `/self`.
- **Alternatives considered**: Two pull requests. Rejected, because both would edit the same classes and the same tests.

## R10. Decision D-9: worker session path is out of scope

- **Decision**: `mist-ops-platform/src/shared/mist/session.py` L51-53 builds `mistapi.APISession(apitoken=token)` for worker sessions. This record does not change that path. A separate issue must track it.
- **Reason**: The worker path reads Vault tokens. It serves a different caller. Changing it in this pull request would breach the one-subject rule.
- **Alternatives considered**: Include the worker path. Rejected for the reason above.

## R11. Decision D-10: five-item debt in `auth.py` and `AuthService`

- **Decision**: Record the existing violations and the increase. Remediation R-A is in the plan.
- **Reason**: The constitution allows a touched violation only when it is recorded with a remediation action.

## R12. Decision D-11: login route and middleware mapping

- **Decision**: `health.py` (L212-213, L237-241) and `middleware/auth.py` (L279-283) keep their mapping. No new client status appears.
- **Reason**: The clients already handle HTTP 401 and HTTP 503. The contract stays stable (see `design/contracts/login-status.md`).

## R13. Open pull requests and remote branches

- Seven pull requests are open. None changes `auth.py`, `endpoints.py`, `types.py`, `health.py`, `middleware/auth.py`, `test_auth.py`, `test_session_security.py`, `test_consumer_registry_usage.py`, or `test_list_status.py`.
- The remote has 598 branches. None name issue 4748, issue 4749, or the phrases `mist-auth` and `token-timeout`.
- Pull request 973 is merged and not linked. Its body mentions "4748" only as a test count ("4748 passed").
- The issue comments say that no pull request is open for this repair. The remote state confirms that statement.

## R14. Route and record placement

- The route is the base-5 encoding of 4748 in eight segments. Each division by 5 gives the digits 1, 2, 2, 4, 4, 3. The padded value is `00122443`. The route `0\0\1\2\2\4\4\3` matches (`.specify/scripts/powershell/spec-route.ps1` L17-18 set base 5 and the width).
- The reference record uses the same derivation. The number 4920 gives `00124140`, which matches `0\0\1\2\4\1\4\0`.
- The route folder `specs/numbered/0/0/1/2/2/4/4/3` does not exist on `main` (RC-56). The record folder is `4748-mist-token-timeout-unavailable`.

## R15. Applicable local gates

From the `Local gates` section of `.github/copilot-instructions.md` (L50) and the ops platform jobs in `ci.yml`:

- Applies: compile, ops Ruff correctness, ops pytest with coverage (threshold 56, minimum 390 tests), and Bandit on `mist-ops-platform/src`.
- Applies: symbol diff, STE for changed Markdown, and the test-quality analyzer when it scans ops tests.
- Applies with a caveat: Black on changed Python files. The root Black configuration was not read (open item U-9).
- Does not apply: `pip-audit` (no dependency change), menu reference (no menu change), and safe sweep `--test` (no menu change).
- Does not apply: ops portal gates (no portal change) and root coverage (root `src` only).
- The root Ruff settings exclude `mist-ops-platform` (RC-44). The ops platform Ruff job is the applicable lint gate.
- Each task runs the targeted form of one gate. T-LOCAL-GATES runs each applicable gate in full.

## Remote and local verification table

Each row records one claim. The table holds 80 rows: RC-01 to RC-56 for `main` and SDK-01 to SDK-24 for the local installed packages. Result values follow the schema: present, absent, partial, or stale. The ref column reads `main` for the repository tree and `local-venv` for installed packages. The blob column for an absent item reads `none-found`.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Issue commit 0d881744 exists on main | repos/jmorrison-juniper/MistHelper/commits/0d881744310dc2c1b1be8b47b5b5402504029062 | main | 0d881744310dc2c1b1be8b47b5b5402504029062 | present | 0 |
| RC-02 | Issue commit is behind main | repos/jmorrison-juniper/MistHelper/compare/0d881744310dc2c1b1be8b47b5b5402504029062 with head main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | stale | 0 |
| RC-03 | auth.py exists | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 0 |
| RC-04 | _fetch_self builds mistapi.APISession with apitoken | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 107 |
| RC-05 | _fetch_self maps constructor and list failures to MistApiUnavailableError | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 116 |
| RC-06 | _handle_self_failure maps every status below 500 to empty privileges | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 133 |
| RC-07 | auth.py has an HTTP 429 branch | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | absent | 0 |
| RC-08 | An empty success list becomes an empty identity | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 123 |
| RC-09 | validate_token writes the cache after the privilege lookup | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 100 |
| RC-10 | ApiResult.success has no None check | mist-ops-platform/src/shared/mist/endpoints.py | main | 36c20d9085047a551070007fd058a1f69c2c9065 | present | 54 |
| RC-11 | _extract_list drops a dict body | mist-ops-platform/src/shared/mist/endpoints.py | main | 36c20d9085047a551070007fd058a1f69c2c9065 | present | 316 |
| RC-12 | _list_result returns the failure without rows | mist-ops-platform/src/shared/mist/endpoints.py | main | 36c20d9085047a551070007fd058a1f69c2c9065 | present | 152 |
| RC-13 | MistEndpoint is a frozen slots dataclass | mist-ops-platform/src/shared/mist/types.py | main | 4eb6024159ff5694ddf10acf56109be25ef91059 | present | 12 |
| RC-14 | self_identity uses module self.self and method getSelf | mist-ops-platform/src/shared/mist/types.py | main | 4eb6024159ff5694ddf10acf56109be25ef91059 | present | 188 |
| RC-15 | login maps an empty identity to HTTP 401 | mist-ops-platform/src/api/routes/health.py | main | bbed1e29374572b5daf8cec392243b6b1ed64a15 | present | 212 |
| RC-16 | login maps MistApiUnavailableError to HTTP 503 | mist-ops-platform/src/api/routes/health.py | main | bbed1e29374572b5daf8cec392243b6b1ed64a15 | present | 237 |
| RC-17 | middleware maps MistApiUnavailableError to HTTP 503 | mist-ops-platform/src/api/middleware/auth.py | main | e65950a3ebad6306baa9ce31b105be79923624e8 | present | 279 |
| RC-18 | worker session factory builds APISession with apitoken | mist-ops-platform/src/shared/mist/session.py | main | c591516dcfe68e8e884d584811858b556f962600 | present | 51 |
| RC-19 | test_auth patches mistapi.APISession in the _fetch_self tests | mist-ops-platform/tests/unit/api/test_auth.py | main | 10bcefdf45cac5117a61899371800e1621b7d306 | present | 213 |
| RC-20 | test_session_security patches mistapi.APISession | mist-ops-platform/tests/unit/api/test_session_security.py | main | f2d951679c3b64ed2022b8879b14052025a40b8f | present | 338 |
| RC-21 | test_consumer_registry_usage asserts the self_identity list call | mist-ops-platform/tests/unit/mist/test_consumer_registry_usage.py | main | 77eb53208ea4108f60530283d852380d0d1fb070 | present | 74 |
| RC-22 | test_list_status.py exists | mist-ops-platform/tests/unit/mist/test_list_status.py | main | 39a6cd7f9dba204d1deb6394065b745591e72b34 | present | 0 |
| RC-23 | CI sets the ops coverage threshold to 56 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 116 |
| RC-24 | CI sets the ops minimum test count to 390 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 121 |
| RC-25 | CI runs the ops Ruff correctness command | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1272 |
| RC-26 | CI runs pytest with coverage in the ops platform | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1188 |
| RC-27 | CI sets Python 3.15 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 77 |
| RC-28 | copilot-instructions lists the ops platform gate | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 76 |
| RC-29 | copilot-instructions requires Python 3.15 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| RC-30 | AGENTS.md has the Writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-31 | Constitution has the Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-32 | Constitution has Safety-First | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| RC-33 | Constitution has the Technology and Compatibility Constraints | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |
| RC-34 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-35 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-36 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-37 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-38 | ROUTE uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-39 | quality-gates lists the ops platform pytest job | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 70 |
| RC-40 | Ops requirements pin mistapi==0.64.1 | mist-ops-platform/requirements.txt | main | 8daf95a15558f8dffbf4f892f8eaf9f1acb30e07 | present | 99 |
| RC-41 | Ops pyproject requires mistapi>=0.64.1 | mist-ops-platform/pyproject.toml | main | 64162dd141653bfe00c0962a3137569352ee8f8b | present | 37 |
| RC-42 | Ops pyproject requires Python >=3.15 | mist-ops-platform/pyproject.toml | main | 64162dd141653bfe00c0962a3137569352ee8f8b | present | 13 |
| RC-43 | Root requirements pin mistapi==0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-44 | Root Ruff settings exclude mist-ops-platform | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 206 |
| RC-45 | Ops example names MIST_API_TOKEN | mist-ops-platform/.env.example | main | 21e036f1554d352ccfdcf72d1c029513da3b2d72 | present | 5 |
| RC-46 | Operations guide has a section on intermittent 401 | mist-ops-platform/docs/operations.md | main | 285a72af0a0047fdf2780f28c52ebbe1400c309b | present | 112 |
| RC-47 | Reference record has spec.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-48 | Reference record has design/research.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| RC-49 | Changelog README exists | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| RC-50 | OpenAPI YAML matches the local file | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 0 |
| RC-51 | OpenAPI defines GET /api/v1/self | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25460 |
| RC-52 | OpenAPI getSelf returns Admin on 200 and HTTP429 on 429 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25490 |
| RC-53 | OpenAPI defines the Admin response component | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 60588 |
| RC-54 | MIST_API_GET_ENDPOINTS maps getSelf to mistapi.api.v1.self.self | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1045 |
| RC-55 | No spec record for issue 4748 exists under specs | specs | main | none-found | absent | 0 |
| RC-56 | Route folder specs/numbered/0/0/1/2/2/4/4/3 is absent | specs/numbered/0/0/1/2/2/4/4/3 | main | none-found | absent | 0 |
| SDK-01 | _load_env reads MIST_APITOKEN | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 363 |
| SDK-02 | _load_env reads MIST_HOST first | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 360 |
| SDK-03 | The constructor calls _load_env before the host branch | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 141 |
| SDK-04 | The constructor sets the cloud from host after _load_env | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 159 |
| SDK-05 | The constructor validates a constructor apitoken through set_api_token | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 182 |
| SDK-06 | set_api_token validates by default | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 551 |
| SDK-07 | set_api_token assigns the token list without validation when validate is false | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 553 |
| SDK-08 | set_api_token keeps the earlier token when no token validates | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 563 |
| SDK-09 | set_api_token splits the token text on commas | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 542 |
| SDK-10 | _get_api_token_data calls /api/v1/self with timeout 30 | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 575 |
| SDK-11 | _get_api_token_data returns (None, None) for other exceptions | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 595 |
| SDK-12 | _get_api_token_data raises ValueError for HTTP 401 outside its try block | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 605 |
| SDK-13 | _check_api_tokens starts before _process_login and has no try block between them | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 649 |
| SDK-14 | CLOUDS includes api.mist.com | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 42 |
| SDK-15 | mist_get sends the request without a timeout | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 277 |
| SDK-16 | _request_with_retry returns a response with no status after a generic exception | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 250 |
| SDK-17 | APIResponse status_code defaults to None | .venv\Lib\site-packages\mistapi\__api_response.py | local-venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 43 |
| SDK-18 | getSelf sends GET /api/v1/self | .venv\Lib\site-packages\mistapi\api\v1\self\self.py | local-venv | 9a1c323fb1045478d923ebcb30436655c851a6e2 | present | 32 |
| SDK-19 | ReadTimeout is not a ConnectionError | .venv\Lib\site-packages\requests\exceptions.py | local-venv | cb5e9510e3b1cf4804ac6091fd7fdb55e9f2745b | present | 98 |
| SDK-20 | ConnectTimeout is a ConnectionError | .venv\Lib\site-packages\requests\exceptions.py | local-venv | cb5e9510e3b1cf4804ac6091fd7fdb55e9f2745b | present | 91 |
| SDK-21 | Session.get passes the timeout keyword to the adapter | .venv\Lib\site-packages\requests\sessions.py | local-venv | feaf34053a911d4b9051069aeb57e595b4d00165 | present | 784 |
| SDK-22 | HTTPAdapter.send accepts a timeout keyword | .venv\Lib\site-packages\requests\adapters.py | local-venv | 40fe8a6d5a6168ba7303b91477af925db0aa3914 | present | 634 |
| SDK-23 | The SDK retries HTTP 429 up to 3 times with a 5 second default delay | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 59 |
| SDK-24 | The installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |

Remote row count: 80. Remote checks in the STATUS file: 80. Summary count: 80.

## Method notes

- Remote bodies came from the Contents API with the path in braces. Each decoded body was hashed with the Git blob formula. The recomputed hash equals the tree SHA for every decoded file.
- The OpenAPI YAML is larger than 1 MB. Its local file matches the remote blob SHA (RC-50). Local line numbers therefore hold for `main`.
- Local SDK blob IDs come from `git hash-object --no-filters`. This command reads a file and writes nothing.
- The remote tree was fetched once with `git/trees/main?recursive=1`. The tree is not truncated, and it lists 11404 entries.
- Commands in this record were read-only. No checkout, fetch, pull, add, commit, or push ran.

## Sources

- Repository files verified on `main` through the Contents API: `AGENTS.md`, `.github/copilot-instructions.md`, and `.github/workflows/ci.yml`.
- Also verified on `main`: `.specify/memory/constitution.md`, `.specify/templates/*.md`, and `.specify/scripts/powershell/spec-route.ps1`.
- Also verified on `main`: `documentation/quality-gates.md`, `documentation/mist-api-openapi31yaml.yaml`, and `documentation/MIST_API_GET_ENDPOINTS.md`.
- Also verified on `main`: `mist-ops-platform/src/**`, `mist-ops-platform/tests/unit/**`, `mist-ops-platform/docs/operations.md`, and the requirements and pyproject files.
- Installed packages read locally (read-only): `.venv\Lib\site-packages\mistapi\` (version 0.64.1), `.venv\Lib\site-packages\requests\`.
- Issue data read through `gh issue view`: #4748 with six comments, #4749 with four comments, and #1858 with its comments.
- Issue #1884 read for its title and state.
- Pull request data read through `gh pr list` and `gh pr view 973`.
- No `web_fetch` call was made. Every claim above cites a local path or a remote path.
- Local skills: none loaded. The visible skill list has no skill for Mist REST authentication. The hidden entries were not searched.

## Unverified

1. Runtime behavior of mistapi 0.64.1 under a real timeout or a real HTTP 401. The findings come from reading source. No test or live request ran. Tests N10 and N11 must confirm them.
2. Whether a deployment sets `MIST_HOST` and `MIST_APITOKEN`. The example file does not name them. Repository code search returns hits for these names, but the hits do not show runtime use.
3. Whether the `requests` default proxy settings from the environment (`trust_env`) change the validation session. The change keeps that behavior.
4. The text of the `docs/operations.md` section at L112 beyond its heading. Task T013 reads it.
5. The remote lines for `AuthService()` construction in `health.py` and the middleware. The local reads show no Redis argument. The remote lines were not decoded.
6. The exact output of `symbol-diff` for an added name. The installed `misthelper_devtools` package did not contain the phrase `no module-level name changed` in its `*.py` files at the package root.
7. Whether the root test-quality analyzer scans `mist-ops-platform/tests`.
8. Whether the root Black configuration covers `mist-ops-platform`. The root `pyproject.toml` Black section was not read.
9. The duration of a throttled login. The SDK retry constants (SDK-23) are verified. The total delay was not measured.
10. Whether the held analyzer finding about constructor coverage accepts a transport-level test. The reviewer must confirm (open item U-1).
