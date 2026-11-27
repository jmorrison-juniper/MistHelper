# Research: Mist Identity Object Sign-In

This file records the decisions, the remote verification, the local gate plan, the sources, and the claims that remain unverified. Remote rows use the branch `main` of `jmorrison-juniper/MistHelper` unless the row says `local`.

## Route Check

The numeric route of issue 4749 is `0/0/1/2/2/4/4/4`. The base-5 digits of 4749 are 1, 2, 2, 4, 4, and 4. Their weighted sum equals 4749. The digits `122444` pad to eight places as `00122444`. The reference record `4920-ex-hardware-inventory-csv` (rows 70 to 74) uses the same method. Its digits `124140` pad to `00124140`, which equals 4920. The route script `.specify/scripts/powershell/spec-route.ps1` sets the width to eight (row 58). The route script was not run.

## Call Path

The trace below runs from the entry points to the SDK call. The rows name the evidence.

1. Sign-in: the route `POST /auth/login` (row 14) calls the validation service `AuthService.validate_token` (row 10). It rejects empty privileges with HTTP 401 (row 15). It caches the token for workers (row 16) and stores the session record (row 17).
2. Request authentication: the middleware `get_current_user` rejects empty privileges (row 11). It stores privileges on the session record (row 12). It reuses them for 300 seconds while they are fresh (row 13).
3. Validation: `validate_token` calls `_fetch_self` (rows 6 and 7). The SDK session uses the environment and the supplied token (rows 81 to 85). `list_all_entities` reads `self_identity` (row 2), paginates (row 3), and drops dictionary bodies (row 1). The SDK call is `getSelf` (row 80), which sends `GET /api/v1/self` (rows 32 and 33).
4. Worker path: the worker sync reads list endpoints through `list_all_entities` (row 18). The list rule of row 1 applies there, so the change keeps it.
5. Test path: existing tests pin the dictionary drop (row 19) and the registry call (row 20). They also pin the 4xx and 5xx outcomes (rows 21 to 23).

## Decisions

### D-1 Read the identity object through a registry flag

- **Decision**: Add the field `object_response` to `MistEndpoint` (types.py line 21, row 5). Set it to true on the `self_identity` entry (types.py line 188, row 4). `list_all_entities` branches on the flag (endpoints.py line 127, row 2). `_extract_list` stays unchanged (row 1).
- **Alternatives**: (a) `AuthService` calls a single-object read method for `/self`. (b) `_extract_list` accepts dictionary bodies for every endpoint. (c) The list layer hard-codes the entity name `self_identity`.
- **Rationale**: The flag keeps the consumer contract (rows 6 and 20). It keeps the list rule of issue #1884 (row 19). Option (a) changes `AuthService` and its call assertions. Option (b) restores the defect that issue #1884 closed for error bodies. Option (c) couples the list layer to one name.
- **Risk**: A future object endpoint must set the flag. The contract tests cover the rule.

### D-2 Make one call for an object endpoint

- **Decision**: The object branch makes one protected call through `_invoke_with_protection`. The branch never calls `_paginate`.
- **Alternatives**: Reuse `_paginate` for object endpoints.
- **Rationale**: The SDK method `getSelf` takes only the session (row 80). `APIResponse` sets `next` from a body key or from pagination headers (row 86). A pagination loop could call `getSelf` with a cursor argument that the method does not accept.
- **Risk**: Low. An object endpoint that paginates needs a new decision.

### D-3 Create a record only from a 2xx object body

- **Decision**: `_extract_object` returns no record unless the status is 2xx. A non-empty dictionary becomes one record. A list body keeps its records.
- **Alternatives**: Accept any object body and let the status check decide later.
- **Rationale**: The status check keeps the rule of issue #1884 that a Mist error body never becomes a data record (row 1).
- **Risk**: Low.

### D-4 Check the active token after the success check

- **Decision**: After the success check (auth.py line 120, row 8), `_identity_from_success` verifies that the active SDK token is one of the supplied tokens. A mismatch returns empty privileges. The check reads the attributes `_apitoken` and `_apitoken_index`, which the SDK contract test pins (row 31).
- **Alternatives**: (a) Check before the SDK call. (b) Build an SDK session without environment reads by overriding the private method `_load_env`. (c) Accept the path and rely on the dictionary drop.
- **Rationale**: (a) fails the existing 4xx and 5xx tests, because they use an `object()` session and assert one call (row 23). (b) overrides a private SDK method and changes how the session reads the environment. (c) leaves the path open once the drop is fixed. The post-call check keeps the existing tests unchanged.
- **Risk**: One environment-token call remains when both `MIST_HOST` and `MIST_APITOKEN` are set (analysis A-05).

### D-5 Ship the identity fix and the token check together

- **Decision**: The endpoint change, the token check, the tests, and the changelog fragment land in one pull request.
- **Alternatives**: Ship the identity fix first and the token check in a later pull request.
- **Rationale**: Warning: the identity fix alone lets a rejected token return the identity of the active SDK token (analysis A-02). The dictionary drop hides that result today. A split release would open the path between the two steps.
- **Risk**: The pull request edits a reserved file (analysis A-06).

### D-6 Sequence after the #4748 repair

- **Decision**: If the local repair for issue #4748 lands first, rebase this branch on `main` before the auth.py task. If that repair is abandoned, this change proceeds alone.
- **Alternatives**: One pull request for both issues, as the issue body proposes.
- **Rationale**: The project rules require one change for each pull request (AGENTS, row 89). The two defects have separate causes. Issue #4748 maps a timeout to a 503 response. Issue #4749 restores an identity object.
- **Risk**: A rebase conflict in `_fetch_self`.

### D-7 Place the new tests in `tests/contract` and change no existing test module

- **Decision**: Add two modules to `mist-ops-platform/tests/contract/` (rows 24 and 25). Change no existing test module.
- **Alternatives**: (a) Add cases to `test_list_status.py`, which the issue comments reserve. (b) Put the tests in a folder whose subject is token resolution, which is not the list layer.
- **Rationale**: The reserved test modules stay unchanged (issue comment IC_kwDOQltU8c8AAAABk_UEwg). The contract folder holds two tracked children and stays at four after the change (row 25). The folder `tests/unit/mist` holds 17 children (row 29), so it cannot take a new file.
- **Risk**: The contract folder covers more than one subject. It already holds API contract tests (row 24).

### D-8 Leave environment isolation and negative caching to follow-up issues

- **Decision**: This change does not isolate environment reads in the SDK session. It does not change the caching of empty privileges. Two follow-up issues own those items.
- **Alternatives**: Include both items in this change.
- **Rationale**: Each issue holds one subject, as AGENTS requires (row 88). Both items change more code and more tests. The active-token check blocks the exposure that isolation would remove.
- **Risk**: Caution: a residual environment-token call remains (analysis A-05), and empty results persist for 300 seconds (analysis A-03).

### D-9 Use a neutral changelog bullet

- **Decision**: The `Fixed` bullet states the sign-in behavior. The bullet names neither the defect class nor the environment path.
- **Alternatives**: A `Security` bullet that names the defect class.
- **Rationale**: Changelog text reaches release readers. A neutral bullet avoids a detailed security description before review. The changelog README defines the fragment name for an issue without a pull request (row 66).
- **Risk**: Reviewers may ask for more detail. The security checklist records the reason.

### D-10 Run the gates for the changed files

- **Decision**: Run the Ops platform gate (row 46) and the changed-file gates. The changed-file gates are lint, format, symbols, test quality, complexity, security lint, and STE. Skip the root full suites, the safe sweep, and the menu gate. Skip the Ops portal gates, the root types gate, the dead code gate, the docstring gates, and the dependency audit.
- **Alternatives**: Run the root full shards and the safe sweep.
- **Rationale**: The change edits no root source file and no root test file. The CI scope variables name root paths for the types, dead code, docstring, and code quality gates (rows 37 to 41). The Ops platform job covers the changed code (row 43).
- **Risk**: A remote gate may read a path that the local run skips. The remote check T-REMOTE-CI covers that case.

## Local Gate Plan

Each row names the gate, its applicability, the command, the expected result, and the evidence row.

| Gate | Applies | Command | Expected result | Evidence |
|------|---------|---------|-----------------|----------|
| Compile | Yes | `python -m py_compile` for each changed Python file | No output | Row 45 |
| Lint | Yes | `python -m ruff check .` at the repository root, and at `mist-ops-platform` | `All checks passed` at the root and zero findings in the sub-project | Rows 44 and 45 |
| Format | Yes | `python -m black --check .` at the repository root | No file needs a change | Row 45 |
| Types | No | Not applicable | The types gate reads root paths | Row 37 |
| Tests | Yes | The new modules and the four existing modules, from `mist-ops-platform` | All selected tests pass | Row 45 |
| Full tests | No | Not applicable | The change edits no root test or root source file | Decision D-10 |
| Safe sweep | No | Not applicable | The root CLI is unchanged | Decision D-10 |
| Coverage | Yes, for the Ops platform | `python -m pytest --cov=src --cov-fail-under=56` from `mist-ops-platform` | At least 390 collected tests and coverage of at least 56 percent | Rows 43 and 46 |
| Test quality | Yes | The procedure of the Test quality ratchet, with `--changed-from origin/main` | `gate: 0 new findings vs baseline` | Row 49 |
| Complexity | Yes | `radon cc mist-ops-platform/src/shared -j \| complexity-gate --max 10` | No block above cyclomatic complexity 10 | Row 45 |
| Security lint | Yes | `bandit -c pyproject.toml -r mist-ops-platform/src -q` | No finding at any severity | Rows 42 and 45 |
| Dependency audit | No | Not applicable | No dependency change | Decision D-10 |
| Code quality | No | Not applicable | The pylint scope is the root `src/` path, and the changed files lie outside it | Row 38 |
| Dead code | No | Not applicable | VULTURE_PATHS names root paths only | Row 39 |
| Docstrings | No | Not applicable | PYDOCSTYLE_PATHS and INTERROGATE_PATHS name root paths only | Rows 40 and 41 |
| Menu reference | No | Not applicable | No menu change | Decision D-10 |
| Symbols | Yes | `symbol-diff --base origin/main <file>` for each changed Python file | `no module-level name changed`, exit code 0 | Row 47 |
| STE | Yes, for Markdown | `ste-linter --config .ste-linter.toml --min-score 80 <file>` for each Markdown file of this record and the changelog fragment | Each file scores 80 or above | Row 48 |
| Ops portal | No | Not applicable | No file under `ops-portal` changes | Decision D-10 |
| Ops platform | Yes | `python -m pytest --cov=src --cov-fail-under=56` from `mist-ops-platform` | At least 390 collected tests and coverage of at least 56 percent | Rows 43 and 46 |

## Remote Verification

Each row is one check. The table holds 91 rows. The STATUS file and the summary report the same count.

| # | Claim | Path | Ref | Blob or tree SHA | Result | Line |
|---|-------|------|-----|------------------|--------|------|
| 1 | Extract list drops a non-list body and returns no record | mist-ops-platform/src/shared/mist/endpoints.py | main | 36c20d9085047a551070007fd058a1f69c2c9065 | present | 316 |
| 2 | List all entities defines the list read path | mist-ops-platform/src/shared/mist/endpoints.py | main | 36c20d9085047a551070007fd058a1f69c2c9065 | present | 127 |
| 3 | Paginate follows the next cursor in a loop | mist-ops-platform/src/shared/mist/endpoints.py | main | 36c20d9085047a551070007fd058a1f69c2c9065 | present | 217 |
| 4 | The self identity registry entry is list only | mist-ops-platform/src/shared/mist/types.py | main | 4eb6024159ff5694ddf10acf56109be25ef91059 | present | 188 |
| 5 | The endpoint dataclass ends with the list method field | mist-ops-platform/src/shared/mist/types.py | main | 4eb6024159ff5694ddf10acf56109be25ef91059 | present | 21 |
| 6 | Fetch self calls list all entities with the self identity type | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 112 |
| 7 | Fetch self builds the SDK session from the supplied token | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 109 |
| 8 | Fetch self checks success before it reads the identity | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 120 |
| 9 | Fetch self reads the first list row as the identity | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 123 |
| 10 | Validate token returns the privileges type | mist-ops-platform/src/shared/services/auth.py | main | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 87 |
| 11 | The middleware rejects privileges that hold no email and no org id | mist-ops-platform/src/api/middleware/auth.py | main | e65950a3ebad6306baa9ce31b105be79923624e8 | present | 115 |
| 12 | The middleware stores returned privileges on the session record | mist-ops-platform/src/api/middleware/auth.py | main | e65950a3ebad6306baa9ce31b105be79923624e8 | present | 254 |
| 13 | Session freshness compares against the 300 second constant | mist-ops-platform/src/shared/services/session_store.py | main | a60333b602275db4aad3eefc077da08ae14680e0 | present | 58 |
| 14 | The login route is POST /auth/login | mist-ops-platform/src/api/routes/health.py | main | bbed1e29374572b5daf8cec392243b6b1ed64a15 | present | 199 |
| 15 | The login rejects empty privileges with HTTP 401 | mist-ops-platform/src/api/routes/health.py | main | bbed1e29374572b5daf8cec392243b6b1ed64a15 | present | 212 |
| 16 | The login caches the supplied token for worker reuse | mist-ops-platform/src/api/routes/health.py | main | bbed1e29374572b5daf8cec392243b6b1ed64a15 | present | 216 |
| 17 | The login stores the supplied token and privileges as a session record | mist-ops-platform/src/api/routes/health.py | main | bbed1e29374572b5daf8cec392243b6b1ed64a15 | present | 308 |
| 18 | The worker sync reads inventory through list all entities | mist-ops-platform/src/worker/sync/inventory.py | main | 6c94e486c89e5a69fc29fa317f31b4201c7450f6 | present | 73 |
| 19 | An existing test pins the dictionary drop in the extract list function | mist-ops-platform/tests/unit/mist/test_list_status.py | main | 39a6cd7f9dba204d1deb6394065b745591e72b34 | present | 106 |
| 20 | An existing test pins the self identity call from the auth service | mist-ops-platform/tests/unit/mist/test_consumer_registry_usage.py | main | 77eb53208ea4108f60530283d852380d0d1fb070 | present | 74 |
| 21 | An existing 401 test expects empty privileges | mist-ops-platform/tests/unit/api/test_auth.py | main | 10bcefdf45cac5117a61899371800e1621b7d306 | present | 215 |
| 22 | An existing 503 test expects MistApiUnavailableError | mist-ops-platform/tests/unit/api/test_auth.py | main | 10bcefdf45cac5117a61899371800e1621b7d306 | present | 241 |
| 23 | An existing real service 4xx test patches getSelf | mist-ops-platform/tests/unit/api/test_session_security.py | main | f2d951679c3b64ed2022b8879b14052025a40b8f | present | 342 |
| 24 | The contract folder docstring names the contract tests | mist-ops-platform/tests/contract/test_api_contracts.py | main | a19de742436d648ac71a35db900acf1b47f5bdaf | present | 1 |
| 25 | The contract folder holds two tracked children | mist-ops-platform/tests/contract | main | 3e41d9631ea6e15483a5dd0db1e2e741f43f4db2 | present | 0 |
| 26 | The shared mist folder holds five tracked children | mist-ops-platform/src/shared/mist | main | 9c0a6d23ceddbb0a5392eb10ef96d974f7b73f2d | present | 0 |
| 27 | The shared services folder holds seven tracked children | mist-ops-platform/src/shared/services | main | bc8840be7d6fd38d2feb7683cf10914c884e8018 | present | 0 |
| 28 | The changelog folder holds 335 tracked children | changelog.d | main | ece56396f47d31dfed7bebe6c69f6dda39f53d83 | present | 0 |
| 29 | The unit mist test folder holds 17 tracked children | mist-ops-platform/tests/unit/mist | main | f12e1af4cfc537cbc5807b2aa48522a364071b72 | present | 0 |
| 30 | The unit api test folder holds 11 tracked children | mist-ops-platform/tests/unit/api | main | 14218744faeb48e871d15abd653d0ea9bcf2905f | present | 0 |
| 31 | The SDK contract test pins four private SDK attributes | tests/contract/websocket_streams/test_ws_sdk_contract.py | main | 7696410b9e1260de64a807216e60e7bee7870db4 | present | 65 |
| 32 | The OpenAPI file defines the path /api/v1/self | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25460 |
| 33 | The getSelf GET operation returns HTTP 200 with the Admin response | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25493 |
| 34 | The Admin response refers to the admin schema | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 60595 |
| 35 | The admin schema declares the privileges property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 67996 |
| 36 | The JSON twin holds the getSelf operation at character offset 739872 on a single line | documentation/mist-api-openapi31json.json | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 1 |
| 37 | The CI MYPY_PATHS variable names root paths only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 38 | The CI SRC_PATH variable defaults to src | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 78 |
| 39 | The CI VULTURE_PATHS variable names root paths only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 40 | The CI PYDOCSTYLE_PATHS variable names root paths only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| 41 | The CI INTERROGATE_PATHS variable names root paths only | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| 42 | The CI bandit job scans the repository root | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| 43 | The CI job ops platform pytest runs the Ops platform suite | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1122 |
| 44 | The CI job ops platform ruff runs ruff in the Ops platform | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 1198 |
| 45 | The local gates section starts the gate table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| 46 | The Ops platform gate row sets 56 percent coverage and 390 tests | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 76 |
| 47 | The symbols gate row runs symbol-diff | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| 48 | The STE gate row runs ste-linter with a score of 80 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| 49 | The test quality ratchet procedure starts | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 95 |
| 50 | Principle I is the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| 51 | Principle II is class-based architecture without wrappers | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| 52 | Principle III is safety first with secret redaction | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| 53 | Principle IV is the full deployment pipeline | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| 54 | Principle V is observability and logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| 55 | Principle VI is inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| 56 | Principle VII is action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| 57 | The mistapi bullet states version 0.59 or later | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| 58 | The spec route width is eight base-5 digits | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| 59 | The spec template has the Mist Cloud transport section | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 102 |
| 60 | The plan template has the Mist Cloud constitution gate | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 62 |
| 61 | The tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| 62 | The checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| 63 | The agent rules define the writing style | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| 64 | The agent rules define the secrets handling | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 172 |
| 65 | The agent rules require a specification for a change to three or more files | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 348 |
| 66 | The changelog README names the fragment for an issue without a pull request | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| 67 | The quality gates document has the Ops platform pytest row | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 70 |
| 68 | The development setup document warns about the global interpreter | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 40 |
| 69 | The container guide has the test and debug containers section | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| 70 | The reference record has spec.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| 71 | The reference record has plan.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 0 |
| 72 | The reference record has tasks.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| 73 | The reference record has analysis.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/analysis.md | main | b5db89b9d0d0a4f8e725ad8e0e746c34fa1a24e7 | present | 0 |
| 74 | The reference record has design/research.md | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| 75 | No record folder exists at the route on main | specs/numbered/0/0/1/2/2/4/4/4 | main | none on main | absent | 0 |
| 76 | No folder under specs starts with 4749 on main | specs | main | none on main | absent | 0 |
| 77 | The commit cited by the issue is an ancestor of main | commit 0d881744310dc2c1b1be8b47b5b5402504029062 | main | not a blob (commit) | present | 0 |
| 78 | The merge commit of pull request 1896 is an ancestor of main | commit 82169f66c2efe4ad6a006ed14bab504df86e51ac | main | not a blob (commit) | present | 0 |
| 79 | The merge commit of pull request 1871 is an ancestor of main | commit 76ddebbbf2af2e6d74f5eca176fb98cab3717e3b | main | not a blob (commit) | present | 0 |
| 80 | The SDK getSelf function takes only the session at line 17 and sends GET to /api/v1/self at line 32 | .venv\Lib\site-packages\mistapi\api\v1\self\self.py | local | 9a1c323fb1045478d923ebcb30436655c851a6e2 | present | 17 |
| 81 | The SDK constructor loads the environment before the supplied token | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 141 |
| 82 | The SDK constructor applies the supplied token through set_api_token | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 182 |
| 83 | The SDK set_api_token replaces the token list after validation | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 555 |
| 84 | The SDK reads MIST_APITOKEN from the process environment | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 363 |
| 85 | The SDK validates each token with its own Authorization header | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 572 |
| 86 | The SDK response object sets next from the body key | .venv\Lib\site-packages\mistapi\__api_response.py | local | 2d878d79295fec79e6409f6243132c53280f15ab | present | 73 |
| 87 | The installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |
| 88 | The agent rules hold one subject for each issue | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 185 |
| 89 | The agent rules hold one change for each pull request | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 223 |
| 90 | The GET endpoint catalog maps getSelf to the SDK module mistapi.api.v1.self.self | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1045 |
| 91 | The missing endpoints document lists getSelf as a missing MistHelper.py mapping | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | present | 990 |

Method notes:

- Repository rows use the blob SHA from the recursive tree of `main` (one call, 11404 entries, not truncated). Directory rows use the tree SHA.
- Line numbers come from the decoded remote body of each file. The OpenAPI YAML and JSON twin exceed the contents API limit, so they were decoded from the blob SHA `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14` and `5f9f4ce94f812f0e818ee65f99f032118a28f56c`.
- Local file hashes (`git hash-object`, no write) equal the remote blob SHAs for all 20 repository files that were hashed. The local checkout is at commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca on branch `main`.
- Rows 80 to 87 cover the SDK, which is not in the repository tree. Their SHA is the Git hash of the local file.

## Sources

Local paths and remote paths:

- Brief: `files\spec-brief.md`, read in full before any other step.
- Repository tree and bodies: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`, `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`, and `gh api repos/jmorrison-juniper/MistHelper/git/blobs/<sha>`.
- Commit ancestry: the compare endpoint with each commit as the base and `main` as the head, using `--jq .status`. Each of the three commits returned `ahead`.
- Issue facts: `gh issue view 4749 -R jmorrison-juniper/MistHelper --json number,title,body,state,labels,comments,createdAt,updatedAt,author`. Related issues 4748, 1858, and 1884 came from `gh issue view` with `closedByPullRequestsReferences`.
- Linked pull requests: `gh pr list --state all --search 4749` returned no pull request. A scan of the 1000 most recent pull requests for the terms 4749, 4748, 1858, and 1884 found no match. Pull requests 1896 and 1871 came from `gh pr view`.
- Local SDK source: `.venv\Lib\site-packages\mistapi\api\v1\self\self.py`, `.venv\Lib\site-packages\mistapi\__api_session.py`, `.venv\Lib\site-packages\mistapi\__api_response.py`, and `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA`, read with read-only views.
- Existing record: a glob and a recursive PowerShell search of `specs` found no folder that starts with 4749-. Rows 75 and 76 confirm the absence on main.
- Coverage documents: row 90 shows that the GET catalog maps `getSelf` to the SDK module. Row 91 shows that the missing-endpoints document lists the CLI mapping as missing. The ops platform calls the SDK through the registry, so the CLI gap does not block this change.
- Web: no `web_fetch` call was made. Every behavior claim cites a local source.

## Unverified

Each item below is a claim that this record does not prove. Each item states the reason.

1. Runtime behavior when the SDK validates a token with an empty base URL. The reason: the source reading only, and no test runs in this record.
2. Runtime behavior when a rejected supplied token leaves the environment token active. The reason: the mechanism follows rows 81 to 85. The record did not run it.
3. Whether the production deployment sets both `MIST_HOST` and `MIST_APITOKEN`. The reason: no deployment file was read for that purpose.
4. The offline control in issue comment IC_kwDOQltU8c8AAAABk_ehTA. The reason: the record did not repeat the control, and the mechanism differs.
5. Test outcomes for the new and existing modules. The reason: the brief forbids running tests in this task.
6. The current collected test count and coverage of the Ops platform. The reason: task T002 measures them.
7. The live shape of `GET /api/v1/self`. The reason: the record uses the OpenAPI contract only, and it makes no live call.
8. Whether `APIResponse.next` can be set for a `/self` body. The reason: the record read the admin schema in part only. Row 86 shows the rule.
9. Whether the production SDK version equals 0.64.1. The reason: only the local `.venv` was inspected.
10. Whether the local repair for issue #4748 lands before this change. The reason: the outcome is outside the repository.
11. The diff of pull request #1896. The reason: the record read only its file list (research rows 78 and 19). The record does not claim which lines the pull request changed.

## Skills

No skill was loaded. The brief limits skill use to Podman questions and Juniper device questions. This issue concerns neither.
