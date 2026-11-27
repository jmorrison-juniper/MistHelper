# Research: Interactive login request timeout

**Issue**: #4827, "Runtime: missing session timeout module in LoginOrchestrator"
**Repository**: `jmorrison-juniper/MistHelper`
**Remote reference**: `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (RC-03)

## 1. Scope and current state

Issue #4827 reports a deferred import of `src.mist.access.auth.session_timeout`. The module does not exist on `main`.

PR #4830 merged on 2026-11-19 at commit `0c89de53d39caeae359b981b371d70b794a9b312` (RC-01). It removed the import, the dead helper, and its call in `_finalize_session`. Its body says "Refs #4827" and "This pull request keeps #4827 open." It states that "Interactive login still has no timeout contract."

This record covers the open contract. The open contract is a request timeout for interactive login. Interactive login sends requests with no time limit today.

### Issue facts from `gh issue view 4827`

- **State and dates**: OPEN. Created 2026-11-17T23:32:43Z. Last updated 2026-11-17T23:34:40Z. Author `jmorrison-juniper`.
- **Labels**: `bug` and `MistHelper.py`. The label `in-progress` is absent.
- **Comments**: None. The comments array is empty.
- **Base commit in the report**: `b7a18b7ead7b1de5882bcd288203c015b1eef792` (RC-02).
- **Reproduction step 1**: Use the locked development environment at the base commit.
- **Reproduction step 2**: Run `.venv/bin/pylint src/mist/access/auth/interactive/login_orchestrator.py --fail-under=9.5`. The report gives exit code 30 and a score of 9.14/10.
- **Reproduction step 3**: Run `git ls-files '*session_timeout*'`. The report gives no tracked path.
- **Error text in the report**: `login_orchestrator.py:240:12: E0401: Unable to import 'src.mist.access.auth.session_timeout' (import-error)`. The same line also has E0611 (`no-name-in-module`) and C0415 (`import-outside-toplevel`).
- **Expected result in the report**: Interactive login uses an available timeout configuration contract.
- **Actual result in the report**: The deferred import fails. The handler catches the error and skips timeout configuration.
- **Instruction in the report**: "Defer the repair to a separate change. Verify the supported timeout contract and add a real import-resolution regression without production credentials."
- **Assessment note in the report**: No production login or Mist request ran during the assessment.

## 2. Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. No decision needs a human decision under section 6 of the brief.

### D-1: Keep the removed import removed

- **Alternatives**: (a) Add `src/mist/access/auth/session_timeout.py` as a compatibility module. (b) Keep the import inside a `try` block. (c) Keep the removal.
- **Chosen**: (c).
- **Reason**: AGENTS.md forbids compatibility shims and fallback paths (RC-72). The five-item rule blocks a new file in `src/mist/access/auth/interactive/`, which already holds five children (RC-46). The timeout contract is the SDK transport hook and the environment variable `API_REQUEST_TIMEOUT` (RC-15, RC-19).
- **Risk**: A reader can expect the removed module. Mitigation: the corrected CONTRIBUTING row (RC-22) and this record.
- **Human decision**: no.

### D-2: Apply the request timeout through a wrapped SDK transport factory

- **Alternatives**: (a) Reuse `MistSessionConfigurator.configure_once` unchanged. (b) Mount the adapter after login in `_finalize_session`, where the removed helper stood. (c) Wrap the SDK transport factory `_new_session` before the first login and mount a timeout adapter on every transport it returns. (d) Defer the timeout to a new issue.
- **Chosen**: (c).
- **Reason for (c)**: The SDK builds a new transport at each login call (RC-55, RC-56). Option (b) leaves the login requests without a limit, including the first POST to `/api/v1/login` (RC-57). Option (a) adds read retries for GET and HEAD requests (`initialize_mist_session.py` lines 65 to 135, RC-87). It also adds the Redis admission adapter when Redis is enabled (same lines). It couples the login to a context flag. Option (d) leaves the documented intent unmet. The comment in `MistHelper.py` says the timeout "prevents indefinite hangs" (RC-16).
- **Risk**: The design uses the private SDK hook `_new_session`. Mitigation: a pin test in `tests/integration/test_mistapi_sdk_compatibility.py` (task T006 in `tasks.md`), the pin `mistapi>=0.64.1,<0.65` (RC-32), and a fail-closed rule (D-5).
- **Human decision**: no.

### D-3: Read the request timeout from `MistHelper.API_REQUEST_TIMEOUT`

- **Alternatives**: (a) Pass `_MH.API_REQUEST_TIMEOUT` into `LoginOrchestrator` as a constructor argument. (b) Add `API_REQUEST_TIMEOUT` to `runtime_settings.py`. (c) Read the environment inside the orchestrator.
- **Chosen**: (a).
- **Reason**: One source of truth already exists. The startup code publishes the value before any menu runs (RC-19, RC-20). The default 120 seconds appears in `MistHelper.py` (RC-15). `runtime_settings.py` holds the retry settings only (RC-21), so option (b) adds a second source. Option (c) repeats the default in a second module.
- **Risk**: The constructor gains a required argument. Mitigation: the three test call sites and the wave-9 wiring test (RC-50, RC-51, RC-52).
- **Human decision**: no.

### D-4: Raise `ValueError` for a non-positive request timeout

- **Alternatives**: (a) No check, as the token path does. (b) Clamp the value to 120 and log a warning. (c) Raise `ValueError` before the first request.
- **Chosen**: (c).
- **Reason**: AGENTS.md requires validation before use. urllib3 raises `ValueError` for a timeout of zero or less (RC-90), so each request fails at once, and a clamp can hide that fault. The existing `ValueError` handler reports the message (`login_orchestrator.py` line 258, RC-04 file).
- **Risk**: An operator who expects 0 to mean "no limit" gets a failed login. Mitigation: the operator guide sentence (RC-27) and the caution in `tasks.md`.
- **Human decision**: no.

### D-5: Fail closed when the SDK lacks the transport factory

- **Alternatives**: (a) Log a warning and continue without a timeout, as the token path does (`initialize_mist_session.py` line 57). (b) Raise `RuntimeError` before the first request.
- **Chosen**: (b).
- **Reason**: An unbounded login is the defect in this issue. Without the hook, the timeout cannot apply. The pin test catches the same drift in CI first.
- **Risk**: A future SDK that removes the hook blocks interactive login until the code changes. The failure is visible at once.
- **Human decision**: no.

### D-6: Keep the seam inside `login_orchestrator.py`

- **Alternatives**: (a) Add the adapter and the hook to `initialize_mist_session.py`, which holds `MistSessionConfigurator`. (b) Add them to `login_orchestrator.py`.
- **Chosen**: (b).
- **Reason**: Open PR #4208 changes `src/foundation/support/refactors/initialize_mist_session.py` (RC-85). AGENTS.md forbids two open pull requests on one file. The overlap check in section 5 finds no open PR on `login_orchestrator.py`.
- **Risk**: The new adapter repeats the token path adapter (RC-87). Mitigation: unify both adapters after PR #4208 merges (analysis.md, item U-2).
- **Human decision**: no.

### D-7: Verify with mocks and one loopback socket test

- **Alternatives**: (a) Mocks only. (b) One loopback socket test on `127.0.0.1` with an ephemeral port, plus mocks. (c) A live Mist login.
- **Chosen**: (b).
- **Reason**: AGENTS.md forbids a production credential in a test (RC-72). The loopback test proves the bound at the socket level. The pattern exists in `tests/unit/refactors/test_issue_3732_read_retry.py` (RC-48).
- **Risk**: The loopback test adds about one second. Mitigation: the server waits on an event with a 5 second cap.
- **Human decision**: no.

### D-8: Document in three files and defer `deploy/.env.example`

- **Alternatives**: (a) Add the variable to `deploy/.env.example` now. (b) Document in `README.md`, `documentation/operator-guide.md`, and `documentation/CONTRIBUTING-MistHelper.md`. (c) Skip the documentation.
- **Chosen**: (b). Option (a) is deferred.
- **Reason for (a) deferral**: Open PR #4208 changes `deploy/.env.example` (RC-86). AGENTS.md forbids two open pull requests on one file. The constitution requires a README update for each behavior change (RC-68 file, Documentation section). Option (c) fails that rule.
- **Risk**: The environment template lacks the variable until the follow-up merges (analysis.md, item U-1). The operator guide covers the variable meanwhile.
- **Human decision**: no.

### D-9: Add one changelog fragment with a Fixed bullet

- **Alternatives**: (a) No fragment, as PR #4830 chose for an internal change. (b) Add `changelog.d/issue-4827-interactive-login-timeout.md` with a Fixed bullet.
- **Chosen**: (b).
- **Reason**: Operators see the new bounded wait. The rule in `changelog.d/README.md` exempts only an internal-only change (RC-28).
- **Risk**: None known.
- **Human decision**: no.

### D-10: Use a new branch and the slug `interactive-login-timeout`

- **Alternatives**: (a) Reuse the merged branch `fix/4827-login-session-timeout`. (b) Create `fix/4827-interactive-login-timeout` from `main`. (c) Use a Spec Kit branch `4827-interactive-login-timeout`.
- **Chosen**: (b).
- **Reason**: AGENTS.md forbids a push to a branch after its squash merge. The branch name uses the type prefix `fix`. The changelog fragment name and the record folder use the same slug.
- **Risk**: None known.
- **Human decision**: no.

### D-11: Keep issue #4827 open until this change merges

- **Alternatives**: (a) Close the issue now. (b) Keep the issue open and let the pull request close it with `Closes #4827`.
- **Chosen**: (b).
- **Reason**: PR #4830 states that the issue stays open because the timeout contract is missing (RC-01 pull request body).
- **Risk**: None known.
- **Human decision**: no.

## 3. Remote verification

### Method

1. One call fetched the full tree of `main` with `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The tree held 11,404 entries and was not truncated.
2. For each repository file, the blob SHA on `main` was compared with the local blob SHA from `git hash-object`. Every compared file matched. Therefore each local line number equals the line number on `main`.
3. For commit and reference rows, the Blob or commit SHA column holds the commit SHA.
4. For local SDK and `requests` files, `git hash-object --no-filters` produced the blob SHA of the installed file. The ref column names `local-venv`. These rows never cite a repository path under `src/`.
5. A row with result `absent` names the path or the symbol that the tree or file does not contain. Its line is 0.
6. No `gh` call returned HTTP 403 or 429. No retry was needed.

### Table

The table holds 90 rows. The STATUS file holds the same 90 rows.

| ID | Claim | Path | Ref | Blob or commit SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | PR #4830 merge commit exists on main | commit: fix(auth): remove stale session timeout import (#4830) | main | 0c89de53d39caeae359b981b371d70b794a9b312 | present | 0 |
| RC-02 | Base commit named in the issue exists | commit: ci: enforce dependency lock and export checks (#4820) | main | b7a18b7ead7b1de5882bcd288203c015b1eef792 | present | 0 |
| RC-03 | Main head at verification time | ref: heads/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-04 | Interactive orchestrator defines LoginOrchestrator | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 15 |
| RC-05 | Login pipeline calls the create-session helper | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 105 |
| RC-06 | Create-session helper is defined | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 129 |
| RC-07 | Removed module path is absent | src/mist/access/auth/session_timeout.py | main | none (absent from tree) | absent | 0 |
| RC-08 | Orchestrator has no import of the removed module | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | absent | 0 |
| RC-09 | Import-resolution test class exists | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 570 |
| RC-10 | Import-resolution test method exists | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 573 |
| RC-11 | Token session configurator class exists | src/foundation/support/refactors/initialize_mist_session.py | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 35 |
| RC-12 | Token path calls configure_once | src/foundation/support/refactors/initialize_mist_session.py | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 179 |
| RC-13 | Interactive initializer does not call the configurator | src/foundation/support/refactors/initialize_mist_session_interactive.py | main | c0cea7c2cd4f88d60e7bc040f5dc90364911a45e | absent | 0 |
| RC-14 | Interactive initializer constructs LoginOrchestrator | src/foundation/support/refactors/initialize_mist_session_interactive.py | main | c0cea7c2cd4f88d60e7bc040f5dc90364911a45e | present | 48 |
| RC-15 | Default request timeout constant is 120 | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2520 |
| RC-16 | Timeout comment states the hang purpose | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2518 |
| RC-17 | Legacy configure_session_timeout entry point exists | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3357 |
| RC-18 | Public name list includes API_REQUEST_TIMEOUT | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 195 |
| RC-19 | Startup reads API_REQUEST_TIMEOUT from the environment | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 286 |
| RC-20 | Startup publishes runtime configuration before login | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 181 |
| RC-21 | Runtime settings module has no timeout setting | src/foundation/runtime/config/runtime_settings.py | main | 4f47d44085d5bddef87f809cfd0ef5879052205f | absent | 0 |
| RC-22 | CONTRIBUTING row for configure_session_timeout exists | documentation/CONTRIBUTING-MistHelper.md | main | 0859587507a8ee27b8f41320c57fb52be93f9a7b | present | 46 |
| RC-23 | Environment template has no API_REQUEST_TIMEOUT line | deploy/.env.example | main | 7137364423308485be734a391798d85c6a37eaf4 | absent | 0 |
| RC-24 | Environment template optional section anchor | deploy/.env.example | main | 7137364423308485be734a391798d85c6a37eaf4 | present | 29 |
| RC-25 | README sentence about --login exists | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 26 |
| RC-26 | Operator guide heading for MSP sign-in exists | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 566 |
| RC-27 | Operator guide login prompt paragraph ends at line 589 | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 589 |
| RC-28 | Changelog naming rule for issue fragments | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 19 |
| RC-29 | Planned changelog fragment does not exist yet | changelog.d/issue-4827-interactive-login-timeout.md | main | none (absent from tree) | absent | 0 |
| RC-30 | CI pylint gate command | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 529 |
| RC-31 | CI mypy path list | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-32 | mistapi pin in pyproject.toml | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-33 | mistapi pin in requirements.txt | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-34 | requests pin in requirements.txt | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 221 |
| RC-35 | STE command for changed Markdown files | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 283 |
| RC-36 | STE configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-37 | Test configuration preloads MistHelper | tests/conftest.py | main | f55885cafab8f4c346ee7d7a813835bab300e45d | present | 165 |
| RC-38 | Development guide notes the shadow-copy check before pytest | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 370 |
| RC-39 | Architecture guide has no interactive login section | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | absent | 0 |
| RC-40 | GET coverage guide lists no POST login request | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | absent | 0 |
| RC-41 | Local OpenAPI defines POST /api/v1/login | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 3090 |
| RC-42 | Local OpenAPI defines POST /api/v1/login/two_factor | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 3248 |
| RC-43 | Local OpenAPI defines GET /api/v1/self | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25487 |
| RC-44 | Source layout guardrail exists | tests/guardrails/test_src_domain_structure.py | main | 8c1567e3b78c57a9a7a40578106d4a34659a977a | present | 0 |
| RC-45 | Changelog fragment guardrail exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-46 | Interactive package holds five children | src/mist/access/auth/interactive | main | fd574364e2c0c4f5aa4aa6e46599c377cdd4f90a | present | 0 |
| RC-47 | SDK compatibility test module exists | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 1 |
| RC-48 | Loopback retry test helper exists | tests/unit/refactors/test_issue_3732_read_retry.py | main | 997b4e97504ee9b8a7e5bbc4187581cbf4304e41 | present | 71 |
| RC-49 | Token path test patches configure_once | tests/unit/refactors/test_initialize_mist_session.py | main | e5c3a34b490ec082e0d4fc5aeacab99778d8ffbe | present | 130 |
| RC-50 | Interactive session test constructs LoginOrchestrator | tests/unit/marvis/mist/access/auth/test_interactive_session.py | main | 2ac64f9a8d1621a86ef32a91e1816febb63e57f4 | present | 27 |
| RC-51 | Wave-9 test asserts constructor keyword arguments | tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py | main | ec4069c071e61c31ef3afa2f59116deae0d80d22 | present | 139 |
| RC-52 | Orchestrator test helper constructs LoginOrchestrator | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 44 |
| RC-53 | Pipeline test fake session uses spec=object | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 295 |
| RC-54 | Installed SDK defines the transport factory _new_session | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 193 |
| RC-55 | Installed SDK login path replaces the transport | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 730 |
| RC-56 | Installed SDK login_with_return replaces the transport | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 841 |
| RC-57 | Installed SDK login path URI is /api/v1/login | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 738 |
| RC-58 | Installed SDK two-factor URI is /api/v1/login/two_factor | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 1096 |
| RC-59 | Installed SDK has one explicit request timeout, on one direct call | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 576 |
| RC-60 | Installed SDK constructor has no timeout parameter | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | absent | 55 |
| RC-61 | Installed SDK request wrapper sends no timeout | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | absent | 203 |
| RC-62 | Installed SDK request wrapper stops on a connection error | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 225 |
| RC-63 | Installed SDK request wrapper stops on any exception | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 250 |
| RC-64 | Installed SDK package version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |
| RC-65 | Installed SDK exports APISession | .venv\Lib\site-packages\mistapi\__init__.py | local-venv | f6fca30f4088d763e76f3072d02a3095d46852b9 | present | 14 |
| RC-66 | Installed requests adapter defines send | .venv\Lib\site-packages\requests\adapters.py | local-venv | 40fe8a6d5a6168ba7303b91477af925db0aa3914 | present | 634 |
| RC-67 | Installed requests session passes keyword arguments to the adapter | .venv\Lib\site-packages\requests\sessions.py | local-venv | feaf34053a911d4b9051069aeb57e595b4d00165 | present | 784 |
| RC-68 | Constitution defines the five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-69 | Constitution states the mistapi version as 0.59 or later | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| RC-70 | Repository instructions state the mistapi pin as 0.64.0 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| RC-71 | Repository instructions contain the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-72 | AGENTS.md exists with the writing and code rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RC-73 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-74 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-75 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-76 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-77 | Reference record spec.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-78 | Reference record plan.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 0 |
| RC-79 | Reference record tasks.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| RC-80 | Reference record analysis.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/analysis.md | main | b5db89b9d0d0a4f8e725ad8e0e746c34fa1a24e7 | present | 0 |
| RC-81 | Reference record design/research.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| RC-82 | Reference record design/checklists/requirements.md exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/checklists/requirements.md | main | 4a53b89939bb523902efeaaffd1d7b12221c717b | present | 0 |
| RC-83 | Record route leaf for issue 4827 is absent | specs/numbered/0/0/1/2/3/3/0/2 | main | none (absent from tree) | absent | 0 |
| RC-84 | No specs path contains 4827 | specs/ | main | none (0 matching paths) | absent | 0 |
| RC-85 | Open PR #4208 changes the token configurator file | src/foundation/support/refactors/initialize_mist_session.py | PR #4208 (open) | none (PR file list) | present | 0 |
| RC-86 | Open PR #4208 changes the environment template | deploy/.env.example | PR #4208 (open) | none (PR file list) | present | 0 |
| RC-87 | Token timeout adapter builder defines the admission and retry branches | src/foundation/support/refactors/initialize_mist_session.py | main | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 65 |
| RC-88 | Installed SDK self URI is /api/v1/self, read through the SDK helper | .venv\Lib\site-packages\mistapi\__api_session.py | local-venv | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 853 |
| RC-89 | Installed SDK GET helper mist_get is defined | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 260 |
| RC-90 | Installed urllib3 raises ValueError for a timeout of zero or less | .venv\Lib\site-packages\urllib3\util\timeout.py | local-venv | 4bb1be11d9cb06900dd82ecebd06aa6a7c5de916 | present | 158 |

Result counts: present 78, absent 12. Two PR rows (RC-85, RC-86) record a file list, so their result is `present` for the PR file.

## 4. Local SDK evidence

- The pinned SDK is `mistapi` 0.64.1 (RC-64). The installed source is in `.venv\Lib\site-packages\mistapi`.
- `APISession.login_with_return` calls `self._new_session()` at line 841 (RC-56). `APISession._process_login` calls it at line 730 (RC-55). Each login therefore replaces `self._session`.
- Pinned SDK request calls pass no timeout. The only explicit timeout is `timeout=30` at line 576 (RC-59).
- The request wrapper stops at a connection error (RC-62) and at any other exception (RC-63). It never repeats a timed-out request. One timeout therefore waits one bound, not several.
- `requests` 2.34.2 passes keyword arguments from `Session.request` to `HTTPAdapter.send` (RC-66, RC-67). A timeout adapter therefore receives `timeout` as a keyword.

## 5. Open pull request overlap check

The command `gh pr list --state open --json number,headRefName,files` returned seven open pull requests. Pull requests #4886 through #4890 touch only dependency manifests, a workflow, or the npm frontend. PR #4813 touches export and data files. PR #4208 touches these files that this change also needs:

- `src/foundation/support/refactors/initialize_mist_session.py` (RC-85). This change does not edit it (D-6).
- `deploy/.env.example` (RC-86). This change does not edit it (D-8).

No open pull request touches `login_orchestrator.py`, the interactive initializer, the listed tests, `README.md`, `documentation/operator-guide.md`, `documentation/CONTRIBUTING-MistHelper.md`, or `changelog.d/`.

## 6. Sources

Remote sources (GitHub):

- `gh issue view 4827` for the body, labels, and state. The issue has no comments.
- `gh issue view 4758` and `gh issue view 1712` for related issue state.
- `gh pr view 4830` for the body, files, state, merge commit, and status checks. Every listed check reports success or skipped.
- `gh pr list --search 4827` for linked pull requests. It returned only PR #4830.
- `gh api repos/jmorrison-juniper/MistHelper/commits/<sha>` for the commit rows RC-01 and RC-02. The ref row RC-03 comes from `gh api repos/jmorrison-juniper/MistHelper/git/ref/heads/main`.
- `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` for every blob SHA in the table.

Local sources (read-only):

- Governance: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four `.specify/templates/` files.
- Code and tests: the files cited in the table.
- Installed SDK and `requests`: `.venv\Lib\site-packages\mistapi\` and `.venv\Lib\site-packages\requests\`.
- Documents: `documentation\operator-guide.md`, `documentation\CONTRIBUTING-MistHelper.md`, `documentation\quality-gates.md`, `documentation\development-setup.md`, `documentation\architecture.md`, `documentation\MIST_API_GET_ENDPOINTS.md`, and `documentation\mist-api-openapi31yaml.yaml`.
- Reference record: `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, read for shape only.

No URL was fetched. The `web_fetch` tool was not needed because the local SDK source answers each SDK question.

## 7. Unverified

- **U-1, live login**: A live interactive login against Mist cloud was not run. Reason: the brief forbids production credentials and the test rules forbid them in tests.
- **U-2, later SDK releases**: Later `mistapi` 0.64.x releases were not checked. Reason: no upstream URL was fetched, and the local pin is 0.64.1 (RC-64).
- **U-3, gate results**: The coverage percentage, the pylint score, the `symbol-diff` result, and the STE scores of the future change are not known. Reason: the brief forbids running gates during the spec phase.
- **U-4, other login calls on token sessions**: Other call sites of `login()` on a token session were not traced. Reason: they lie outside the token configurator seam. The seam calls `configure_once` after the strategy returns (RC-12).
- **U-5, pull request CI**: The CI result of the future pull request is not known. Reason: the pull request does not exist yet.
- **U-6, new import in the symbol gate**: The `symbol-diff` gate may report the new `requests.adapters` import as an added name. Reason: the gate has not run.
- **U-7, new pylint messages**: The pylint score for the nested adapter class is not known. Reason: the gate has not run.

## 8. Skills

No skill was loaded. The change involves no Podman operation and no Juniper device behavior.
