# Research: Upgrade Portal Session Recovery

**Issue**: #3714. **Base**: remote `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (RC-52).

## Method

- Remote `main` is the authority. Blob SHAs come from the remote tree listing (11404 entries, not truncated). Line anchors come from decoding remote file contents.
- A local file was read only when its `git hash-object` value equaled the remote blob SHA. Matching local files: `identity.py`, `auth.py`, `factory.py`, `config.py`, `mist_client.py`, `wsgi_capture.py`, `start.sh`, `compose.yml`. Also matching: `test_identity.py`, `test_no_credential_leak.py`, `test_auth.py`, `.gitignore`, `requirements.txt`, `deploy/.env.example`, `routes/upgrade.py`, `driver.py`, `spec-route.ps1`, the OpenAPI file, and the governing documents.
- The local file `src/foundation/support/utils/logger_utils.py` differs from main. Its local blob is `b47036046770f9a36aaecaff1e2821f165ed66df`. Its remote blob is `6cb99dc0e3e0a4808391e6953560071b69e36683`. This spec cites remote lines only for that file (analysis.md item A-11).
- The SDK and cryptography files are not in the repository tree. They come from the local `.venv`. Their rows use the local path and a `git hash-object` value.
- No build, test, linter, install, or container command ran. No GitHub write ran. No environment variable value appeared in any output.

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. A decision marked HUMAN-DECISION-REQUIRED names the recommended option. The human must approve it before implementation.

### D-1 HUMAN-DECISION-REQUIRED: Credential persistence scope

- **Alternatives**: (a) Persist no credential material. Recover only the environment token mode from the process environment. (b) Store browser token material, encrypted. (c) Store provider authentication state, encrypted.
- **Recommended**: (a).
- **Reason**: The issue body states that it does not authorize persistent token storage. The operator guide states that the portal does not store the token (RC-69, line 192). The pinned SDK keeps provider state in private attributes (RC-55, lines 124 to 129). The public SDK methods include `set_api_token`, `login`, `logout`, and `get_authentication_status` (`__api_session.py` lines 529, 778, 912, 1007). None of the public methods exports session state.
- **Risk**: Caution: Browser token and provider login operators authenticate again after each worker replacement.

### D-2 HUMAN-DECISION-REQUIRED: Redis password before the store activates

- **Alternatives**: (a) Refuse container startup with the compose default `REDIS_PASSWORD` when the store is enabled. (b) Log a warning and continue. (c) Keep the default.
- **Recommended**: (a).
- **Reason**: `compose.yml:149` defines a literal default, and `compose.yml:244` applies it as `requirepass`. The credential choice belongs to the owner (brief section 6). The rule matches the existing `CAPTURE_SECRET_KEY` refusal (RC-06, `config.py:429`).
- **Risk**: An operator who keeps the default cannot start the container after the change. The operator must set a value first.

### D-3 Shared store: Redis with a dedicated prefix

- **Alternatives**: ArangoDB (a run store, not suited to short records). A JSON file under `data/` (not shared across containers, and `data/` holds product output). In-process storage only (the current behavior).
- **Chosen**: Redis with the prefix `misthelper:capture:session:`.
- **Reason**: Redis already holds site locks (`lock.py:1071`, `config.py:156`) and supports key expiry. The service exists in compose (`compose.yml:231`).
- **Risk**: A client with the Redis password can write keys under the prefix. D-5 prevents a valid forged record.

### D-4 Store record holds non-credential fields, and only for the environment token mode

- **Alternatives**: Store the full `OperatorSession` (rejected: it holds the cloud session object). Store the owner key only (rejected: it cannot rebuild the mode or the identity). Store browser token material (see D-1).
- **Chosen**: Store the fields in `design/contracts/store-record.md`. Write records only for `environment_token` sign-ins.
- **Reason**: Recovery needs the mode, the token name, the browser digest, the host, and two deadlines. `OperatorSession` already states that it holds no password and no API token (`identity.py:470` to `477`). The token name is safe. The code comment calls it "the safe token name that the cloud returns" (`identity.py:375`).
- **Risk**: The token name remains in the store. D-5 protects it.

### D-5 Encrypt each record with MultiFernet, using a key separate from the signing key

- **Alternatives**: Plaintext JSON with a Redis password only (rejected: a writer can change the mode or the identity, and the portal would trust the change). AES-GCM with low-level primitives (more code, and nonce handling is needed). Reuse of `CAPTURE_SECRET_KEY` (rejected: signing and encryption keys must differ).
- **Chosen**: `cryptography.fernet.MultiFernet` with `CAPTURE_SESSION_ENCRYPTION_KEY` and an optional previous key. The key comes from the environment only.
- **Reason**: `Fernet.encrypt` authenticates each token (`fernet.py:57`). `Fernet.decrypt` accepts a time-to-live (`fernet.py:86`). `MultiFernet` supports rotation (`fernet.py:172`, `rotate` at line 187). The package is pinned (`requirements.txt:37`).
- **Risk**: Caution: A lost key makes every record unreadable (R-4 in plan.md).

### D-6 Lifetimes: absolute 28800 seconds, idle 1800 seconds

- **Alternatives**: An absolute lifetime of 4 hours (a long upgrade session would end sooner). No idle limit (rejected: an unattended workstation keeps access). An idle limit of 60 minutes (a longer replay window).
- **Chosen**: 28800 seconds absolute and 1800 seconds idle, each configurable and validated (`design/contracts/settings.md`).
- **Reason**: A firmware upgrade run can last several hours. The idle limit reduces replay time at an unattended workstation.
- **Risk**: A session can outlive a short task by up to 8 hours.

### D-7 Binding: owner identity, browser digest, mode, and host. No address binding.

- **Alternatives**: Bind to the client address (rejected: NAT and roaming networks break the binding). Store the organization in the record (rejected: a second write path on each organization pick).
- **Chosen**: Bind the record to the identity, the browser digest, the mode, and the host. The organization stays in the signed session (`select.py:621` for the store function, `select.py:1875` for the call).
- **Reason**: The guard already compares the browser identifier (`identity.py:780`). The organization pick is signed, and the signature survives a worker replacement.
- **Risk**: The cloud access can change after sign-in. The existing organization checks still apply to each request.

### D-8 Registry first, store read only on a registry miss

- **Alternatives**: Read the store on each request (rejected: a Redis outage would block pages that need no Redis). Use a short local cache (rejected: a sign-out in one worker would not reach another worker's cache).
- **Chosen**: A registry hit uses the local record. A registry miss reads the store.
- **Reason**: The current read path needs no Redis, and the lock comment says viewing must not need Redis (`lock.py:217`).
- **Risk**: With several workers, a sign-out in one worker leaves the record in another registry until its deadline. D-11 prevents that state.

### D-9 Failure responses and fail-closed rules

- **Alternatives**: Map an outage to 401 (rejected: operators would authenticate again for an outage). Continue with a local session (rejected: the session is unverified). Keep the record after a validation failure (rejected: a revoked token could recover again and again).
- **Chosen**: Unrecoverable sessions return 401 `not_authenticated`. A store outage returns 503 `session_store_unavailable`. Each validation failure deletes the record. No local fallback exists.
- **Reason**: The constitution requires fail-closed behavior for the operational store (Technology constraints, `.specify/memory/constitution.md:274`).
- **Risk**: A transient cloud error forces a sign-in (R-3 in plan.md).

### D-10 Sign-out deletes the record once and reports a failed delete

- **Alternatives**: Retry in a loop (adds latency). Fail the sign-out (rejected: operators cannot leave a shared workstation).
- **Chosen**: One delete attempt. A failed delete logs an error. In every case, the browser session clears.
- **Reason**: A cleared cookie removes the owner key from the browser. The record cannot restore a session without the old signed cookie.
- **Risk**: The record remains until its deadline (R-6 in plan.md).

### D-11 Keep one Gunicorn worker

- **Alternatives**: Raise the worker count (rejected: revocation across workers and the registry semantics are not designed).
- **Chosen**: Keep `--workers 1` (`container/scripts/start.sh:324`, RC-10).
- **Reason**: The defect needs survival across replacement, not concurrency. One worker avoids an untested second behavior.
- **Risk**: Caution: The driver thread still stops when a worker is replaced (D-12).

### D-12 Run driver threads are out of scope

- **Alternatives**: Include driver recovery now (rejected: a separate subsystem with a larger effect, and it needs its own approval).
- **Chosen**: Keep the driver out of scope. File a separate issue.
- **Reason**: The driver keeps its thread in a class dictionary and starts a daemon thread (RC-17, `driver.py:1386` and `driver.py:1432`). The issue names session persistence as its subject.
- **Risk**: Runs can stop after a replacement. The capture guide states that run rows can disappear at a restart without a database run store (`documentation/upgrade_capture_portal.md:984` to `987`).

### D-13 Keep SensitiveFilter, add value-based tests, and do not edit logger_utils.py

- **Alternatives**: Rewrite the filter (rejected: scope). Add value-based redaction inside the store module (rejected: it spreads logging logic).
- **Chosen**: Keep the filter (`logger_utils.py:189`). Add test TP-22 with synthetic values. Do not edit `logger_utils.py`.
- **Reason**: The filter states that unlabeled secrets are outside its pattern contract (RC-16, `logger_utils.py:216` to `217`). The local checkout has an uncommitted change in this file (analysis.md item A-11).
- **Risk**: An unlabeled new secret can still reach a log.

### D-14 Place the new module in `persistence/`

- **Alternatives**: `runtime/` (10 children, RC-20). Adding a child breaks Principle I. `auth/` (2 children, RC-22). It holds the unrelated JWT module (RC-19). A new package (adds a child to a noncompliant parent).
- **Chosen**: `src/interfaces/portals/upgrade_portal/persistence/session_store.py`. The folder has 3 children (RC-21), so it holds 4 after the change.
- **Reason**: Principle I allows new code only in a compliant nested package.
- **Risk**: The folder grows to 4 children. Another change there must respect the five-child limit.

### D-15 Edit existing test files only, and leave test_no_credential_leak.py untouched

- **Alternatives**: New test files under `tests/unit/upgrade_portal/` (168 children, RC-75) or `tests/contract/upgrade_portal/` (66 children, RC-76). Both add a child to a noncompliant parent.
- **Chosen**: Add tests to `test_identity.py`, `test_config.py`, `test_auth.py`, and `test_security.py`. Leave `test_no_credential_leak.py` untouched until issue #2708 completes the handoff of the file (RC-32).
- **Reason**: Principle I and the reservation rule.
- **Risk**: The edited test files grow. `test_identity.py` already holds 1958 lines on main (RC-30).

### D-16 Update the operator guide and leave the README unchanged

- **Alternatives**: Change the README (rejected: it holds no sign-in behavior text, RC-70). Leave the guide unchanged (rejected: the guide's environment table lacks the new variables).
- **Chosen**: Update `documentation/upgrade_capture_portal.md` (RC-69, lines 132 and 181 to 192).
- **Reason**: The documentation rule requires one change that updates behavior and its documents (`AGENTS.md:336`, `constitution.md:398`).
- **Risk**: The guide text needs STE review (task T016).

### D-17 Record the existing five-item debt and file a remediation issue

- **Alternatives**: Split the noncompliant parents in this change (rejected: broad, unrelated churn).
- **Chosen**: Record the counts (RC-20 to RC-22 and RC-72 to RC-78). File a separate remediation issue. Add no child to a noncompliant parent.
- **Reason**: The constitution treats existing violations as grandfathered technical debt that needs a separate action (`constitution.md:38`).
- **Risk**: The debt remains until the remediation issue lands.

### D-18 Replace the legacy seven batches with three groups and no route edits

- **Alternatives**: Keep the legacy route batches (rejected: 51 route edits add no behavior, because one guard covers every route).
- **Chosen**: Group A (store and settings), Group B (identity and sign-in), Group C (tests and documents). No file under `app/routes/` changes except `auth.py`.
- **Reason**: All 51 handlers use one decorator (RC-23 to RC-29), and the guard at `identity.py:886` performs the check.
- **Risk**: A future route that omits the decorator skips recovery. Test TP-23 counts the decorators.

### D-19 Accept one planned sign-in at the deployment that adds the store

- **Alternatives**: A drain before deployment (rejected: the old process cannot write records). A dual-write migration (rejected: the old code cannot change).
- **Chosen**: One planned sign-in for each operator. The guide states the rule (T016).
- **Reason**: The old process holds each session in memory (`identity.py:516`). A new process cannot read those sessions.
- **Risk**: Operators lose their session once. Deploy when no run is active.

### D-20 Public mistapi calls only

- **Alternatives**: Copy private attributes (`_apitoken`, `_session`, `_csrftoken`) to rebuild state (rejected: private attributes, RC-55). Serialize the session (rejected: no public export exists, see D-1).
- **Chosen**: Rebuild with the same builders used at sign-in (`auth.py:337` to `365`, RC-07). Call `login` to fill the privilege list. Call `getSelf` to read the token name (`auth.py:385`, RC-56).
- **Reason**: The public constructor and methods suffice. `set_api_token` (line 529) exists, but the builders already set the token through the constructor.
- **Risk**: A future SDK pin could change `login`. The pin `mistapi==0.64.1` stays (RC-14).

### Legacy owner decisions mapped to this record

| Legacy decision (PR 4018 spec.md) | Result in this record |
| - | - |
| Shared store is Redis with a dedicated prefix and ACL | D-3 keeps Redis and the prefix. The ACL is out of scope (U-5). |
| Store only the minimum encrypted record | D-4 and D-5 |
| Encryption with one active and one previous key | D-5 |
| Eight-hour absolute and 30-minute idle lifetimes | D-6 |
| Renewal only after successful validation | FR-013 (refresh at most once each 60 seconds) |
| Bind to browser and organization, not address | D-7 |
| Fail closed when the store is unavailable | D-9 |
| Preserve live sessions through staged migration | D-19 replaces this target because the old process cannot write records |
| Keep Gunicorn workers during the migration | D-11 |
| Route changes for 51 handlers | D-18 replaces this target with one guard |

## Remote Verification Table

Each row is one check. Results are `present` or `absent`. The table has 78 rows. The `design` and `STATUS` counts match this table.

| ID | Claim | Path | Ref | Blob or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Process-local registry dictionary and record methods (dict 516 get 542 drop 559) | `src/interfaces/portals/upgrade_portal/runtime/identity.py` | `main` | `07098e4fb4510c295f385c037ef5230ec6509bf0` | present | 516 |
| RC-02 | Sign-in register, browser check, and sign-out drop (register 725 browser check 780 sign-out drop 826) | `src/interfaces/portals/upgrade_portal/runtime/identity.py` | `main` | `07098e4fb4510c295f385c037ef5230ec6509bf0` | present | 725 |
| RC-03 | Guard, refusal envelope, environment names, mode enum, environment refusal (names 70 mode enum 355 refusal 753 envelope 843 guard 886) | `src/interfaces/portals/upgrade_portal/runtime/identity.py` | `main` | `07098e4fb4510c295f385c037ef5230ec6509bf0` | present | 886 |
| RC-04 | Flask signing key and session cookie flags (SECRET_KEY 964 HttpOnly 995 SameSite 996) | `src/interfaces/portals/upgrade_portal/app/factory.py` | `main` | `5729127f3b4a0d25f45a33e8ef79a4e460d8be92` | present | 964 |
| RC-05 | Portal log filters and lock store client (RunContextFilter and SensitiveFilter 274 connect_lock_store 681) | `src/interfaces/portals/upgrade_portal/app/factory.py` | `main` | `5729127f3b4a0d25f45a33e8ef79a4e460d8be92` | present | 274 |
| RC-06 | Signing key variable and container refusal (CAPTURE_SECRET_KEY 49 refusal 429) | `src/interfaces/portals/upgrade_portal/app/config.py` | `main` | `adfa7ba9b59ea1ab89bbcb8a20a18cfc28b4ff6e` | present | 49 |
| RC-07 | Mode builders call mistapi APISession (provider 324 environment token 357 browser token 371) | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | `main` | `5c496f5465a7f940896080958efafb40b000b0a7` | present | 357 |
| RC-08 | Token identity getSelf provider registration and mode dispatch (getSelf 385 identity sign_in 969 dispatch 1197) | `src/interfaces/portals/upgrade_portal/app/routes/auth.py` | `main` | `5c496f5465a7f940896080958efafb40b000b0a7` | present | 1197 |
| RC-09 | Dotenv load before create_app (load_dotenv 33 create_app 48) | `wsgi_capture.py` | `main` | `bb62567576fe80c07982533acdc63f66fdb9ba3a` | present | 48 |
| RC-10 | Capture Gunicorn one worker and no max-requests (workers 324 no max-requests 321) | `container/scripts/start.sh` | `main` | `3b138807883a8a8785bac7d8c9b7f9a79458ed0c` | present | 324 |
| RC-11 | CAPTURE_SECRET_KEY required in compose and restart policy (required 109 restart 163) | `compose.yml` | `main` | `b3944fc9f994ca149974072b1a9c8f13797d7924` | present | 109 |
| RC-12 | Redis password literal default and Redis requirepass (default 149 requirepass 244) | `compose.yml` | `main` | `b3944fc9f994ca149974072b1a9c8f13797d7924` | present | 149 |
| RC-13 | Ignore rule for dotenv files (line 5) | `.gitignore` | `main` | `17eadfadb35a59e191a61c78877569ad747ddcc7` | present | 5 |
| RC-14 | Pins for cryptography 50.0.2 at 37 mistapi 0.64.1 at 129 redis 8.1.0 at 215 | `requirements.txt` | `main` | `50fe63d4cf5e6071612c62c288e965190c60b969` | present | 37 |
| RC-15 | Transport exception text logged through str(error) (74 and 97) | `src/interfaces/portals/upgrade_portal/api/mist_client.py` | `main` | `69408709fc059bda8aff360a29a0891e85054722` | present | 74 |
| RC-16 | SensitiveFilter is pattern based and excludes unlabeled secrets (class 189 limit 217) | `src/foundation/support/utils/logger_utils.py` | `main` | `6cb99dc0e3e0a4808391e6953560071b69e36683` | present | 217 |
| RC-17 | Run driver threads in a class dictionary and daemon threads (dictionary 1386 daemon 1432) | `src/interfaces/portals/upgrade_portal/upgrade/driver.py` | `main` | `0279d399396fed1253d46cf525d65f15ff61a6c1` | present | 1432 |
| RC-18 | connect_lock_store opens the shared Redis handle (line 1071) | `src/interfaces/portals/upgrade_portal/runtime/lock.py` | `main` | `1b9a4a2916ab3ffe3a5835c69db7220902c5e8c7` | present | 1071 |
| RC-19 | JWTSessionManager is defined and the sign-in path does not import it (class 27) | `src/interfaces/portals/upgrade_portal/auth/session.py` | `main` | `cdc8753d0eb65404fb6f0b32a41edda950a7ca4f` | present | 27 |
| RC-20 | runtime directory holds ten direct children | `src/interfaces/portals/upgrade_portal/runtime` | `main` | `6603e5cd07604509e51b07689609de824a4c2d91` | present | 0 |
| RC-21 | persistence directory holds three direct children | `src/interfaces/portals/upgrade_portal/persistence` | `main` | `f8c18f609adb2c35d0b773a07e939af2b90f3349` | present | 0 |
| RC-22 | auth directory holds two direct children | `src/interfaces/portals/upgrade_portal/auth` | `main` | `f75b53668448352c25596da6ed88dd8bd25c71b8` | present | 0 |
| RC-23 | capture.py holds six protected handlers (first at 1155) | `src/interfaces/portals/upgrade_portal/app/routes/capture.py` | `main` | `fdebed5e2fd073b04009c97efd82c81d10200955` | present | 1155 |
| RC-24 | org_controls.py holds four protected handlers (first at 153) | `src/interfaces/portals/upgrade_portal/app/routes/org_controls.py` | `main` | `315ac60d079b07475d08cd223d77eaf869b66416` | present | 153 |
| RC-25 | org_precheck.py holds one protected handler (line 101) | `src/interfaces/portals/upgrade_portal/app/routes/org_precheck.py` | `main` | `2437eb5b7ceb86890f67ba05319987fddae80797` | present | 101 |
| RC-26 | org_upgrade.py holds seven protected handlers (first at 1138) | `src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py` | `main` | `11c839db760b07291b51a3804546dc53e8ba8a85` | present | 1138 |
| RC-27 | review.py holds six protected handlers (first at 1970) | `src/interfaces/portals/upgrade_portal/app/routes/review.py` | `main` | `b26716b474e1ac6f7fa69257e08258eab254021a` | present | 1970 |
| RC-28 | select.py holds twelve protected handlers (first at 1814) and store_chosen_org at 621 and 1875 | `src/interfaces/portals/upgrade_portal/app/routes/select.py` | `main` | `604f8a5e1b6f72b6df860cf1ae03d0ffbc01055c` | present | 1814 |
| RC-29 | upgrade.py holds fifteen protected handlers (first at 1168) | `src/interfaces/portals/upgrade_portal/app/routes/upgrade.py` | `main` | `ac87e5dda78b77a7856d410668185f1f9df788c1` | present | 1168 |
| RC-30 | Defect-asserting restart test (lines 1505 to 1520) | `tests/unit/upgrade_portal/test_identity.py` | `main` | `947a0fbf4d101a4e75cfdf9a272a4ed1eb799379` | present | 1505 |
| RC-31 | Sign-out restart assertion (line 1647) | `tests/unit/upgrade_portal/test_identity.py` | `main` | `947a0fbf4d101a4e75cfdf9a272a4ed1eb799379` | present | 1647 |
| RC-32 | Contract credential test reserved by issue 2708 | `tests/contract/upgrade_portal/test_no_credential_leak.py` | `main` | `ac90c47c89d7e0114bfb8d74817c914cbc7e3432` | present | 1 |
| RC-33 | Contract auth test module | `tests/contract/upgrade_portal/test_auth.py` | `main` | `c864b183df3d67d9ad490b6004896c599d33828c` | present | 1 |
| RC-34 | Contract security test module (edit target) | `tests/contract/upgrade_portal/test_security.py` | `main` | `dc0b8b044623b48994333975a0c1bd401b5d6c93` | present | 1 |
| RC-35 | Changelog fragment policy guard | `tests/guardrails/test_changelog_fragment_policy.py` | `main` | `dbd5e8776797f12536b3bc2bd613143b85f3fc4a` | present | 1 |
| RC-36 | Container policy docs guard | `tests/guardrails/test_container_policy_docs.py` | `main` | `1b842c302e52bcb43a95e4a2aed2366a93d94909` | present | 1 |
| RC-37 | Configuration unit test module | `tests/unit/upgrade_portal/test_config.py` | `main` | `c516f3a3e5b98a2b1930b84a006349d226514cc7` | present | 1 |
| RC-38 | Restart test file cited by the issue body | `tests/contract/upgrade_portal/session_signing/test_restart.py` | `main` | `none` | absent | 0 |
| RC-39 | Source path cited by the issue body without the interfaces prefix | `src/upgrade_portal/runtime/identity.py` | `main` | `none` | absent | 0 |
| RC-40 | Planned shared session store module | `src/interfaces/portals/upgrade_portal/persistence/session_store.py` | `main` | `none` | absent | 0 |
| RC-41 | Legacy record folder for issue 3714 on main | `specs/numbered/0/0/1/0/4/3/2/4/3714-session-persistence` | `main` | `none` | absent | 0 |
| RC-42 | Legacy changelog fragment on main | `changelog.d/issue-3714-session-persistence.md` | `main` | `none` | absent | 0 |
| RC-43 | Planned changelog fragment | `changelog.d/issue-3714-portal-session-recovery.md` | `main` | `none` | absent | 0 |
| RC-44 | Legacy spec.md on the closed PR 4018 head | `specs/numbered/0/0/1/0/4/3/2/4/3714-session-persistence/spec.md` | `379f2719cbf85bdbff08da41c389209d439c4a67` | `848fd8f3f530959a75d4b19569057ff39156693a` | present | 1 |
| RC-45 | Legacy plan.md on the closed PR 4018 head | `specs/numbered/0/0/1/0/4/3/2/4/3714-session-persistence/plan.md` | `379f2719cbf85bdbff08da41c389209d439c4a67` | `aae2784eccba7ba8c7fe59bdd6dab5ea330074af` | present | 1 |
| RC-46 | Legacy tasks.md on the closed PR 4018 head | `specs/numbered/0/0/1/0/4/3/2/4/3714-session-persistence/tasks.md` | `379f2719cbf85bdbff08da41c389209d439c4a67` | `8806698afb3b6fc99352ace6b65c63652ccec47e` | present | 1 |
| RC-47 | Legacy changelog fragment on the closed PR 4018 head | `changelog.d/issue-3714-session-persistence.md` | `379f2719cbf85bdbff08da41c389209d439c4a67` | `6296e07cd342f0f45ec43cea081a8380282b2eb9` | present | 1 |
| RC-48 | Legacy head branch jmorrison-juniper-3714-session-persistence | `branch jmorrison-juniper-3714-session-persistence` | `jmorrison-juniper-3714-session-persistence` | `none` | absent | 0 |
| RC-49 | Measured base commit cited by issue comment 2 | `commit efd082892584f54099973449a5953cd1b8d9a181` | `main` | `efd082892584f54099973449a5953cd1b8d9a181` | present | 0 |
| RC-50 | Assessment and legacy base commit d82f715 | `commit d82f715436f295711ed5ac01ab9242118c03fee0` | `main` | `d82f715436f295711ed5ac01ab9242118c03fee0` | present | 0 |
| RC-51 | Legacy plan base commit f1505203 | `commit f1505203d1d5ec845c94cb54f55118d613cf4e49` | `main` | `f1505203d1d5ec845c94cb54f55118d613cf4e49` | present | 0 |
| RC-52 | Current main head commit f03c6c9 | `commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | `main` | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` | present | 0 |
| RC-53 | Mist OpenAPI defines self and login paths (self 25460 login 3089) | `documentation/mist-api-openapi31yaml.yaml` | `main` | `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14` | present | 25460 |
| RC-54 | Endpoint map links getSelf to the mistapi self module (line 1045) | `documentation/MIST_API_GET_ENDPOINTS.md` | `main` | `6281c11b46f22b9814a1948a96df9be4945fb8fd` | present | 1045 |
| RC-55 | mistapi APISession class private state and public login (class 52 state 121 to 129 login 778) | `.venv\Lib\site-packages\mistapi\__api_session.py` | `local-venv` | `491530cb6e6397ec6fd3b1b34803192f4f68afa3` | present | 52 |
| RC-56 | mistapi getSelf function (line 17) | `.venv\Lib\site-packages\mistapi\api\v1\self\self.py` | `local-venv` | `9a1c323fb1045478d923ebcb30436655c851a6e2` | present | 17 |
| RC-57 | cryptography MultiFernet class and Fernet decrypt ttl (MultiFernet 172 decrypt 86) | `.venv\Lib\site-packages\cryptography\fernet.py` | `local-venv` | `582e594ae4d983b446699894c2b610c6770161ba` | present | 172 |
| RC-58 | Constitution Principles I and III (38 and 113) | `.specify/memory/constitution.md` | `main` | `4584997a264c5a7ade2ca7441246e1f067083aa1` | present | 38 |
| RC-59 | Copilot instructions Local gates and Spec Kit roots (50 and 159) | `.github/copilot-instructions.md` | `main` | `f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179` | present | 50 |
| RC-60 | AGENTS writing style section (line 40) | `AGENTS.md` | `main` | `44a9afffb5bd6f774973a845d27343e4e528b6ad` | present | 40 |
| RC-61 | Spec template layout | `.specify/templates/spec-template.md` | `main` | `083ef123c7a2e56e21f3062173fb003258f927e2` | present | 1 |
| RC-62 | Plan template layout | `.specify/templates/plan-template.md` | `main` | `1a54553bd85cbef2178aa55efbeeb0c1942ffdde` | present | 1 |
| RC-63 | Tasks template layout | `.specify/templates/tasks-template.md` | `main` | `7e5170324d41a6736c498d6b9fc83651f31d0778` | present | 1 |
| RC-64 | Checklist template layout | `.specify/templates/checklist-template.md` | `main` | `806657da09d1058823923e346a323b633114971a` | present | 1 |
| RC-65 | Spec route base five and width eight (lines 7 and 17) | `.specify/scripts/powershell/spec-route.ps1` | `main` | `37293a255f9b5de20ccb2b3ef0ad15717bab2826` | present | 17 |
| RC-66 | CI path variables for mypy vulture pydocstyle and interrogate (lines 93 101 104 107) | `.github/workflows/ci.yml` | `main` | `d51efbc13c0f0a2076680030ed8be7ef7cf64523` | present | 93 |
| RC-67 | Quality gates job table | `documentation/quality-gates.md` | `main` | `6776d334cca5d9b43273473a06da367a65605c6d` | present | 1 |
| RC-68 | Reference record spec shape (line 11 Clarifications) | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | `main` | `83b950279e45704943ad6942d23c8fc99cced492` | present | 11 |
| RC-69 | Operator guide env table and credential mode statement (lines 132 and 192) | `documentation/upgrade_capture_portal.md` | `main` | `97fc51f98df43dff874b22330efb274e625054a8` | present | 132 |
| RC-70 | README link to the capture portal guide (line 42) | `README.md` | `main` | `331a4567f72156fe2a3e3ee91005d2cbbcaed6d0` | present | 42 |
| RC-71 | Environment template file | `deploy/.env.example` | `main` | `7137364423308485be734a391798d85c6a37eaf4` | present | 1 |
| RC-72 | upgrade_portal directory holds twelve direct children | `src/interfaces/portals/upgrade_portal` | `main` | `9f69e75110e889343b9a81f62c774f60fd1ebe33` | present | 0 |
| RC-73 | app directory holds ten direct children | `src/interfaces/portals/upgrade_portal/app` | `main` | `5050b006f776a8b4031cbc64293c4c52ddc646fa` | present | 0 |
| RC-74 | upgrade directory holds twenty-two direct children | `src/interfaces/portals/upgrade_portal/upgrade` | `main` | `4523cb1c518d4a6c85b719a956478a40384c076e` | present | 0 |
| RC-75 | tests unit upgrade_portal directory holds 168 direct children | `tests/unit/upgrade_portal` | `main` | `4a51282e64576c2deb09060a34997275fcc4603a` | present | 0 |
| RC-76 | tests contract upgrade_portal directory holds 66 direct children | `tests/contract/upgrade_portal` | `main` | `0d329a2d3c0e8e6b3811fab73b0a62f28fa1f6b7` | present | 0 |
| RC-77 | fakeredis is absent from requirements-dev.txt | `requirements-dev.txt` | `main` | `9a528bfe03a10f7bc903f5768ef26de765bbff43` | absent | 0 |
| RC-78 | routes directory holds thirteen direct children | `src/interfaces/portals/upgrade_portal/app/routes` | `main` | `6c14ca92440a688b6e56687c4e8648b7e439b886` | present | 0 |

Result counts: 70 present and 8 absent. The absent rows are RC-38 to RC-43, RC-48, and RC-77. RC-77 records the absence of a package, so its path exists and its claim is the absence.

## Legacy Draft Verification

The closed PR 4018 holds a draft. Its branch no longer exists on the remote (RC-48). Its head commit is `379f2719cbf85bdbff08da41c389209d439c4a67`. The draft is a draft to verify, not proof. Each claim receives one verdict:

- **verified**: the claim is true on remote main at `f03c6c9`.
- **stale**: the claim held at an older revision, or it never held.
- **absent**: the named path is absent on remote main.

| ID | Legacy claim (file) | Verdict | Evidence |
| - | - | - | - |
| LC-01 | Sessions live in a process-local dictionary, and a restart returns 401 (spec.md) | verified | RC-01, RC-03 |
| LC-02 | The signed cookie keeps only the owner key (spec.md) | verified | RC-02 |
| LC-03 | The measured revision is d82f715 (spec.md) | stale | RC-50 present, superseded by RC-52 |
| LC-04 | 51 protected handlers (spec.md, plan.md, issue comment 5) | verified | RC-23 to RC-29 sum to 51 |
| LC-05 | 51 handlers across 13 route files (spec.md, plan.md) | stale | RC-23 to RC-29 show 7 files. RC-78 shows 13 entries in the folder, including `__init__.py`. |
| LC-06 | Decorator line numbers in the handler groups (spec.md) | stale | RC-23 starts at 1155. The draft lists 1133 for the same handler family. |
| LC-07 | The issue body path `src/upgrade_portal/` is stale (spec.md) | verified | RC-39 absent. RC-01 present under the interfaces prefix. |
| LC-08 | The defect check at `test_identity.py` lines 1505 to 1520 (spec.md) | verified | RC-30 |
| LC-09 | The base revision is f1505203 (plan.md) | stale | RC-51 present, superseded by RC-52 |
| LC-10 | Redis holds site locks, not sessions (plan.md) | verified | RC-18, RC-12 |
| LC-11 | Batch 1 paths exist except the new module (plan.md) | verified | RC-04, RC-06, RC-11, RC-71. RC-40 is absent as expected. |
| LC-12 | Five-item rule PASS for `runtime/session_store.py` (plan.md) | stale | RC-20 shows ten children in `runtime/` |
| LC-13 | Task T001 expects origin/main to resolve to f1505203 (tasks.md) | stale | RC-52 |
| LC-14 | Task T002 expects `specs/numbered/` to exist (tasks.md) | verified | RC-68 path exists under `specs/numbered/` |
| LC-15 | Comment 6026814949 is the source for the 51 count (tasks.md) | verified | The comment exists and states 51. It also states 13 files, which LC-05 corrects. |
| LC-16 | Batches 3 to 6 need 51 route edits (tasks.md) | stale | RC-23 to RC-29 and the guard at `identity.py:886` cover every route |
| LC-17 | The pull request changes only specification and changelog files (PR body) | verified | The PR lists four paths, all under `specs/` or `changelog.d/` |
| LC-18 | The branch `jmorrison-juniper-3714-session-persistence` exists | absent | RC-48 |
| LC-19 | The legacy record folder exists on main | absent | RC-41 |

Verdict counts: 10 verified, 7 stale, and 2 absent. These counts appear in STATUS.json as `existing_record`.

## Sources

- Remote issue data: `gh issue view 3714` (body and metadata), and the seven comments with IDs 6024956847, 6025165101, 6025956300, 6026736792, 6026814949, 6027182355, and 6759344378. The cited comment is `https://github.com/jmorrison-juniper/MistHelper/issues/3714#issuecomment-6026814949`.
- Remote pull request data: `gh pr list` and `gh pr view 4018` (state, body, files, and head SHA).
- Remote related issues: `gh issue view` for #2051, #2708, #3213, #3503, and #3959.
- Remote tree and contents: `gh api git/trees/main` and `gh api contents` decoded from base64.
- Local governing documents (read only, hash matched): `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `.specify/templates/*`, `.specify/scripts/powershell/spec-route.ps1`, `documentation/quality-gates.md`, `documentation/container-deployment.md`, `documentation/operator-guide.md`, `documentation/architecture.md`, `documentation/development-setup.md`.
- Remote documentation read through contents: `documentation/upgrade_capture_portal.md` (lines 128 to 134, 181 to 193, and 982 to 990).
- Local SDK sources (read only): `.venv\Lib\site-packages\mistapi\__api_session.py` (lines 52 to 130, 406 to 1198), `.venv\Lib\site-packages\mistapi\api\v1\self\self.py` (line 17), `.venv\Lib\site-packages\cryptography\fernet.py` (lines 32, 57, 86, 172, 187).
- Local OpenAPI file (read only): `documentation\mist-api-openapi31yaml.yaml` (lines 3089, 25460, 25910).
- No URL was fetched with `web_fetch`. The spec relies on local and GitHub sources only.

## Unverified

- **U-1**: The issue states that the restart test returns "3 passed in 0.57 seconds". The named test file is absent (RC-38), and the brief forbids test runs. The result is unverified.
- **U-2**: The legacy draft states STE scores, a changelog policy test result, a markdown link check result, and a `git diff --check` result. These were not repeated, because the brief forbids gate runs.
- **U-3**: The legacy plan states that `upgrade.py` is a hot file owned by another worker. No repository evidence confirms this ownership.
- **U-4**: The issue states that five targeted searches found no separate issue. The searches were not repeated. This record checked the related issues listed in Sources.
- **U-5**: Redis ACL support in the image `docker.io/redis/redis-stack:latest` (`compose.yml:232`) is unverified. The design uses `requirepass` only (`compose.yml:244`).
- **U-6**: Mist cloud token validity and login refusal rules are unverified. The record treats any failed login during recovery as a failed validation.
- **U-7**: Whether `cryptography` is a direct requirement is unverified. `requirements.txt:37` pins it. The "via" comment block below the pin was not read in full.
- **U-8**: Redis read-after-write and TTL behavior in a live store are unverified. Tests use an in-memory fake.
- **U-9**: The live deployment state is unverified, including running workers, active runs, and operator counts. The brief forbids live checks.

## Skills

No skill was loaded. The design needs no Podman storage, network, or runtime behavior, because the compose change adds environment variables only. No listed skill covers Flask session state or the mistapi session object. The repository documents answer the remaining questions.
