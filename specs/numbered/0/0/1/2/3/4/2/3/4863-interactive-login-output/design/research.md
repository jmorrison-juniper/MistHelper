# Research: Interactive Login Output

Each decision lists the chosen option, the reason, the rejected options, and the risk. Each claim cites a remote row in the verification table or a local source. The decision IDs match the `decisions` array of the status file.

## D-1. Channel for banners, menus, success lines, and result lines

- **Decision**: Use the `echo` helper. It prints the text and writes one info record. The console handler drops that record through `ConsoleEchoFilter`, so the terminal shows the text once.
- **Rationale**: `echo` already exists for this purpose (RC-27, RC-28). The filter is attached to the console handler (RC-78), and it excludes the echo logger (RC-29). The same helper already prints the cloud choice (RC-18).
- **Alternatives considered**:
  - Keep `logger.warning`. Rejected, because the issue requires direct output for banners and prompts.
  - Write an info record only. Rejected, because the operator sees no banner or success line at the default threshold of 30.
  - Add a new print helper. Rejected, because `echo` already has the filter and the same contract.
- **Risk**: Each `echo` call also writes an info record to `data/script.log`. The file log gains a few info lines per login. Low.

## D-2. Progress lines write info records only, and duplicates are deleted

- **Decision**: Delete the five progress lines that duplicate an info record (RC-06, RC-07, RC-09, RC-11, RC-15). Change the progress line of the organization list to an info record (RC-23).
- **Rationale**: Each deleted line has an info record with the same meaning nearby (RC-05, RC-07, RC-09, RC-11, RC-15). Deleting the line keeps one record for each step. The issue requires progress in info and debug records.
- **Alternatives considered**:
  - Echo the progress lines. Rejected, because the issue requires progress to stay in info and debug records.
  - Keep the duplicates as info records. Rejected, because each step would write two records.
  - Use the debug level. Rejected, because the progress would then stay out of the info records of the default configuration.
- **Risk**: At threshold 30, operators see fewer progress lines. The file log keeps the info records. Accepted by the spec.

## D-3. Failure and validation lines keep warning or error records

- **Decision**: Keep the failure lines and validation lines as they are (RC-04, RC-17, RC-21, RC-26).
- **Rationale**: A failure line reports a real problem. The operator needs a label, and the file log needs a warning or error record. The issue does not ask to change failure lines.
- **Alternatives considered**:
  - Echo the failure lines. Rejected, because the file log then records the failure at INFO.
  - Raise every failure line to error. Rejected, because no reason supports a severity change.
- **Risk**: Operators still see warning labels on failures. This result is intended.

## D-4. SDK console level 30 for the interactive login

- **Decision**: Pass `console_log_level=30` to the `APISession` constructor (RC-08). The SDK then prints warning and error lines only (RC-66, RC-67, RC-68).
- **Rationale**: The SDK prints success with the INFO label through its own console object (RC-66 and RC-67). The console object is shared (RC-71), and the constructor sets its level (RC-68). A level of 30 removes the INFO success lines and keeps the SDK errors (RC-70 prints the label).
- **Alternatives considered**:
  - Keep 20. Rejected, because the SDK success lines stay visible.
  - Use 40. Rejected, because it hides SDK warnings with no benefit.
  - Edit or vendor the SDK. Rejected, because the SDK is a pinned third-party package in `.venv`, and the constitution gives no exception for this case.
  - Filter SDK records on the terminal. Deferred, because the SDK logger records already follow `CONSOLE_LOG_LEVEL` (RC-72, RC-77).
- **Risk**: Caution: the SDK console is process-wide, so SDK info lines stay hidden until another SDK session sets the level. Accepted, because the next session construction resets the level (RC-68).

## D-5. 2FA success line after Mist accepts the code

- **Decision**: After the replay login returns an `authenticated` flag of true, print `  + 2FA verification successful` as direct output (after RC-13).
- **Rationale**: The SDK returns the outcome as a dictionary with `authenticated` (RC-75). The 2FA success line should show only when the code passes, so the flag is the right test.
- **Alternatives considered**:
  - Rely on the SDK success line. Rejected, because D-4 hides it and it carries an INFO label.
  - Print before the call. Rejected, because the outcome is not known.
  - Print from the SDK. Rejected, because the SDK is third-party code.
- **Risk**: The success line depends on the SDK return shape. The test `test_accepted_2fa_code_prints_success_line` pins that shape.

## D-6. The MSP picker is in scope

- **Decision**: Convert the banner, the menus, the skip lines, and the selection results in `msp_org_selector.py` (RC-20, RC-22, RC-24, RC-25).
- **Rationale**: The picker runs in the switch flow. The switch flow calls the success handler (RC-31), which runs the picker for MSP grants. The same banner warnings appear in the same session.
- **Alternatives considered**:
  - Leave the picker unchanged. Rejected, because the same warning labels would remain in the same session.
  - Convert the failure lines too. Rejected under D-3.
- **Note**: The non-MSP organization picker in `MistHelper.py` already writes its first line through `echo` (RC-79). It needs no change.

## D-7. The switch cancel record is an info record

- **Decision**: Change the cancel record at line 2702 of `MistHelper.py` from `logger.warning` to `logger.info` (RC-02). The direct output line "Cancelled." stays (RC-01).
- **Rationale**: A cancel is a normal operator action. The direct output already reports it.
- **Alternatives considered**:
  - Keep the warning record. Rejected, because a normal action would show a warning label.
  - Echo the cancel record too. Rejected, because the text would appear twice.

## D-8. Test assertions move to direct output or to INFO level

- **Decision**: Convert the thirteen assertions that read warning caplog for converted lines (RC-35 to RC-40 and the menu assertions). Use `capsys` for direct output and INFO-level `caplog` for info records. Keep the failure assertions unchanged (RC-41).
- **Rationale**: An assertion that reads a warning record cannot pass after the line becomes direct output. A converted assertion keeps the same check on the new channel.
- **Alternatives considered**:
  - Keep the warning assertions. Rejected, because they would fail.
  - Delete the assertions. Rejected, because coverage of the text would drop.
  - Mock `echo`. Rejected, because it tests the mock and not the output.

## D-9. A new test module for the cloud menu

- **Decision**: Add `tests/unit/marvis/mist/access/auth/interactive/test_clouds.py`.
- **Rationale**: The folder keeps one test module for each class: `test_login_orchestrator.py`, `test_msp_org_selector.py`, and `test_credential_prompter.py`. No module tests `CloudSelector` today. The folder then holds five children, which the five-item rule allows.
- **Alternatives considered**:
  - Add the tests to `test_login_orchestrator.py`. Rejected, because the test would cover another class.

## D-10. No dependency and no SDK version change

- **Decision**: Keep `mistapi==0.64.1` (RC-45) and add no package.
- **Rationale**: The installed SDK is 0.64.1 (RC-73). The output behavior comes from the constructor argument and from MistHelper code. No upgrade is needed.
- **Alternatives considered**:
  - Upgrade the SDK. Rejected, because the upgrade is a separate concern and its output behavior is not verified.
  - Pin 0.64.0 as the guide states. Rejected, because the pin is 0.64.1 (RC-45 and RC-46). The guide statement is stale (RC-47). It is recorded in `analysis.md`.

## D-11. Out-of-scope items stay in place

- **Decision**: Leave the upgrade portal login (RC-33), the browser sign-in (issue #4936), SDK logger filtering, the bootstrap warning, and the token session path unchanged.
- **Rationale**: AGENTS.md asks for one concern for each change. Each item has its own owner or issue.
- **Alternatives considered**:
  - Fix all login output in one change. Rejected, because the portal login has its own console level and its own tests.
  - File new issues in this run. Not done. The repository owner decides on the issues.

## D-12. Branch, folder, and fragment names

- **Decision**: Branch `fix/4863-interactive-login-output`. Record folder `4863-interactive-login-output` under route `specs/numbered/0/0/1/2/3/4/2/3/`. Fragment `changelog.d/issue-4863-interactive-login-output.md`.
- **Rationale**: The branch pattern is in `.github/copilot-instructions.md`. The fragment rule for an issue without a pull request is in `changelog.d/README.md` (RC-53). The route formula is in `spec-route.ps1` (RC-52).
- **Alternatives considered**:
  - Use a shorter slug such as `login-output`. Rejected, because the slug should name the change.
  - Use a timestamp folder. Rejected, because the Spec Kit numeric route applies to this issue.

## D-13. Commit scope and labels

- **Decision**: Commit and pull request title `fix(login): route interactive login messages to direct output`. Keep the labels `bug`, `MistHelper.py`, `in-progress`, and `logging`.
- **Rationale**: The change touches the authentication package, so the scope names the login. The existing labels already give type, scope, and status.
- **Alternatives considered**:
  - Use the scope `MistHelper.py`. Rejected, because the change is not limited to the entry file.
  - Add the `docs` label. Rejected, because the type is `fix`.

## Remote verification

Method: the blob SHA of each repository file comes from the recursive git tree of `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The body of each file comes from the git blobs endpoint for that SHA. The contents endpoint returned HTTP 404 for every path during this run. Local SDK and stdlib files use `git hash-object --no-filters`, and their rows say `local`.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|----|-------|------|-----|----------|--------|------|
| RC-01 | Direct output line Cancelled precedes the cancel record | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2701 |
| RC-02 | Cancel record is a warning record | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2702 |
| RC-03 | Rollback failure record stays a warning record | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2654 |
| RC-04 | Import failure line stays a warning record | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 58 |
| RC-05 | Info record names host, account, and cloud | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 84 |
| RC-06 | Progress line duplicates the info record at line 84 | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 86 |
| RC-07 | Progress line duplicates the info record at line 137 | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 136 |
| RC-08 | SDK console level is 20 in the constructor call | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 142 |
| RC-09 | Progress line duplicates the info record at line 170 | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 169 |
| RC-10 | 2FA banner is a warning record | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 192 |
| RC-11 | Progress line duplicates the info record at line 198 | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 197 |
| RC-12 | Resubmitted login call carries the 2FA code | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 199 |
| RC-13 | Debug record of the 2FA result comes before the return | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 204 |
| RC-14 | Login success line is a warning record | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 230 |
| RC-15 | Progress line duplicates the info record at line 237 | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 236 |
| RC-16 | MSP summary line is a warning record | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 242 |
| RC-17 | Authentication failure line stays a warning record | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 222 |
| RC-18 | Cloud choice line already uses direct output | src/mist/access/auth/interactive/clouds.py | main | 15556189fd246e2f5aafef837feb804733ab45ee | present | 58 |
| RC-19 | Cloud banner is a warning record | src/mist/access/auth/interactive/clouds.py | main | 15556189fd246e2f5aafef837feb804733ab45ee | present | 66 |
| RC-20 | MSP banner is a warning record | src/mist/access/auth/interactive/msp_org_selector.py | main | d6c1bac798711076dfed1d31694ab2e9f1b01a9d | present | 45 |
| RC-21 | Invalid MSP input line stays a warning record | src/mist/access/auth/interactive/msp_org_selector.py | main | d6c1bac798711076dfed1d31694ab2e9f1b01a9d | present | 69 |
| RC-22 | Selected MSP line is a warning record | src/mist/access/auth/interactive/msp_org_selector.py | main | d6c1bac798711076dfed1d31694ab2e9f1b01a9d | present | 100 |
| RC-23 | Organization progress line is a warning record | src/mist/access/auth/interactive/msp_org_selector.py | main | d6c1bac798711076dfed1d31694ab2e9f1b01a9d | present | 101 |
| RC-24 | No-organization line is a warning record | src/mist/access/auth/interactive/msp_org_selector.py | main | d6c1bac798711076dfed1d31694ab2e9f1b01a9d | present | 133 |
| RC-25 | Selected organization line is a warning record | src/mist/access/auth/interactive/msp_org_selector.py | main | d6c1bac798711076dfed1d31694ab2e9f1b01a9d | present | 228 |
| RC-26 | 2FA validation line stays a warning record | src/mist/access/auth/interactive/credential_prompter.py | main | e1b5197a78e7ec5993faa7dd66eed9c8a553336c | present | 62 |
| RC-27 | echo prints the message and writes one info record | src/foundation/support/utils/console.py | main | 1192a295d6c2058ad966f1963426f2a0f28f058c | present | 51 |
| RC-28 | echo writes its info record | src/foundation/support/utils/console.py | main | 1192a295d6c2058ad966f1963426f2a0f28f058c | present | 74 |
| RC-29 | ConsoleEchoFilter class excludes the echo logger from the terminal | src/foundation/support/utils/console.py | main | 1192a295d6c2058ad966f1963426f2a0f28f058c | present | 43 |
| RC-30 | Console level defaults to INFO when CONSOLE_LOG_LEVEL is unset | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 197 |
| RC-31 | Switch flow calls the success handler, which runs the MSP picker | src/foundation/support/refactors/switch_to_interactive_login.py | main | 40704618ea70a52aeba73ad64022b4bd313e8bed | present | 102 |
| RC-32 | Startup login calls execute and does not call the MSP picker | src/foundation/support/refactors/initialize_mist_session_interactive.py | main | c0cea7c2cd4f88d60e7bc040f5dc90364911a45e | present | 53 |
| RC-33 | Portal console constant is 20 (out of scope) | src/interfaces/portals/upgrade_portal/app/routes/auth.py | main | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 98 |
| RC-34 | Constructor assertion pins console level 20 | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 380 |
| RC-35 | Progress assertion reads warning caplog | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 191 |
| RC-36 | 2FA banner assertion reads warning caplog | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 456 |
| RC-37 | MSP summary assertion reads warning caplog | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 594 |
| RC-38 | Selected organization assertion reads warning caplog | tests/unit/marvis/mist/access/auth/interactive/test_msp_org_selector.py | main | b57f5b445ab1f084ff0165557d8e01efb66ef241 | present | 83 |
| RC-39 | No-organization assertion reads warning caplog | tests/unit/marvis/mist/access/auth/interactive/test_msp_org_selector.py | main | b57f5b445ab1f084ff0165557d8e01efb66ef241 | present | 244 |
| RC-40 | Page hint assertion reads warning caplog | tests/unit/marvis/mist/access/auth/interactive/test_msp_org_selector.py | main | b57f5b445ab1f084ff0165557d8e01efb66ef241 | present | 348 |
| RC-41 | Validation assertion stays unchanged | tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py | main | 49087357e58644c8f11147f542c688e5a9cd25c9 | present | 134 |
| RC-42 | Module mocks the prompt function | tests/unit/config/foundation/support/refactors/runtime/session/test_switch_to_interactive_login.py | main | 563774cd7d0b5b15a53f557c5ef5d5e99f8e75f7 | present | 52 |
| RC-43 | Operator guide lists the login success output | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 591 |
| RC-44 | Sample console level is 20 | documentation/sample.env | main | 30981f0df54edb598b089a150757022946bf9c46 | present | 49 |
| RC-45 | Runtime pin is mistapi==0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-46 | Package range is mistapi>=0.64.1,<0.65 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RC-47 | Guide states mistapi>=0.64.0,<0.65, which disagrees with RC-46 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| RC-48 | MYPY_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-49 | VULTURE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-50 | PYDOCSTYLE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-51 | INTERROGATE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-52 | Route formula uses base 5 and width 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-53 | Name rule for a fragment of an issue without a pull request | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-54 | Heading and bullet format of a 2FA fragment | changelog.d/issue-4755-2fa-login.md | main | 7181f1567a7746f358b1f7e41d1917f4635b3c9d | present | 1 |
| RC-55 | Sentence limits of 20 and 25 words | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 48 |
| RC-56 | Principle V sets ASCII and secret rules | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| RC-57 | Principle VI sets the inline comment rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| RC-58 | Principle VII sets the action logging rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-59 | POST /api/v1/login path, with an optional two_factor field | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 3089 |
| RC-60 | POST /api/v1/login/two_factor path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 3247 |
| RC-61 | GET /api/v1/self path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25460 |
| RC-62 | getSelf row maps GET /api/v1/self, and no POST login row exists | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1045 |
| RC-63 | Only an OAuth login row exists, and no POST login row exists | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | present | 224 |
| RC-64 | STE command for Markdown files | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 283 |
| RC-65 | Bootstrap command for the Windows entry point | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 33 |
| RC-66 | SDK prints Authentication successful at INFO through its console | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 743 |
| RC-67 | SDK prints 2FA authentication succeeded at INFO through its console | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 1105 |
| RC-68 | APISession sets the shared console level on each construction | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 140 |
| RC-69 | Default console level of the constructor is 20 | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 67 |
| RC-70 | Console info method prints a label through print | .venv\Lib\site-packages\mistapi\__logger.py | local | f69c3669972dbfa2f9d0786a09adbd7c08a34d55 | present | 173 |
| RC-71 | One module-level console object serves the SDK | .venv\Lib\site-packages\mistapi\__logger.py | local | f69c3669972dbfa2f9d0786a09adbd7c08a34d55 | present | 217 |
| RC-72 | SDK logger is the mistapi logger | .venv\Lib\site-packages\mistapi\__logger.py | local | f69c3669972dbfa2f9d0786a09adbd7c08a34d55 | present | 218 |
| RC-73 | Installed SDK version is 0.64.1 | .venv\Lib\site-packages\mistapi\__version.py | local | cb8f30ff14092ff9d6ddfafaeef41dac5e425f38 | present | 1 |
| RC-74 | _process_login posts to /api/v1/login | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 740 |
| RC-75 | login_with_return is the public login method that returns authenticated | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 804 |
| RC-76 | login_with_return reads /api/v1/self on the password branch | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 892 |
| RC-77 | callHandlers applies each handler level along the parent chain | C:\Users\jmorrison\AppData\Local\Python\pythoncore-3.15-64\Lib\logging\__init__.py | local | 9b5550352203518e1a1f832f0c5857495766a28d | present | 1733 |
| RC-78 | ConsoleEchoFilter is attached to the console handler | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 201 |
| RC-79 | Non-MSP organization picker writes its first line through echo | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2757 |
| RC-80 | SDK prints Authentication failed at ERROR through its console | .venv\Lib\site-packages\mistapi\__api_session.py | local | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 751 |

## Sources

Local sources, read in this run:

- `.venv\Lib\site-packages\mistapi\__api_session.py`, `__logger.py`, and `__version.py` (installed SDK 0.64.1). Rows RC-66 to RC-76 and RC-73.
- `C:\Users\jmorrison\AppData\Local\Python\pythoncore-3.15-64\Lib\logging\__init__.py`, the stdlib of the Python home named in `.venv\pyvenv.cfg`. Row RC-77.
- `.env` in the operator checkout, a git-ignored file. Its `CONSOLE_LOG_LEVEL` line sets 30. Only that line was read. This value is local evidence and no repository claim depends on it.
- `documentation\operator-guide.md` section "Sign in for an MSP run", read at the remote blob. Row RC-43.
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`, the reference record. Its files gave the shape of this record.
- `documentation\api\admins\POST_login.md`, read for the statement that the interactive login calls the SDK login.
- `_meta\validate-drafts.ps1`, read to learn the draft checks. It was not run. See the method notes.

Remote sources, read through the GitHub API in this run:

- Issue #4863 (`gh issue view`), pull request search (`gh pr list`), open pull request files (`gh pr list --json files`), the issue timeline, and the matching-refs search for branches named with 4863.
- Issue #4755 and issue #4936 (state and title only).
- Remote files by blob SHA, listed in the verification table.

No web URL was fetched. No upstream claim is recorded.

Skills: no skill was loaded, because no Podman question and no Juniper device question is in scope. Documents not read in full: `documentation\container-deployment.md`, because no container file changes, and `documentation\architecture.md`, which was searched for login and console output rules with none found.

## Unverified

- The upstream mistapi 0.64.1 source was not compared with the installed copy. Reason: no upstream URL was fetched in this run. The installed copy is the only SDK source used.
- The login with a 2FA account was not run. Reason: a specification run uses no credential. The quickstart gives the manual check.
- The terminal output at threshold 20 was not observed. Reason: the tool was not run in this run.
- The `symbol-diff` result for the added `echo` import is unknown. Reason: the gate runs after the change.
- The contents endpoint of the GitHub API returned HTTP 404 for every path in this run, including paths listed in the tree. The blob endpoint returned the bodies. The cause of the 404 responses was not established.
- Other open pull requests were checked at the time of this record (seven open pull requests). A later pull request can still overlap. T-PR repeats the check.
- The validator `_meta\validate-drafts.ps1` was not run. Reason: rule 2 prohibits running scripts. Its checks were repeated with search tools.

## Linked work

- Issue #4863 is open. Labels: `bug`, `MistHelper.py`, `in-progress`, and `logging`. It has no comments. It was created on 2026-11-20 and last updated on 2026-11-20.
- No pull request is linked. A search for "4863" in all states returned no pull request.
- No branch with 4863 in its name exists on the remote. Searches covered the prefixes `fix/4863`, `feat/4863`, `chore/4863`, `docs/4863`, `refactor/4863`, and `4863`.
- Issue #4870 (open, backlog handoff) has a timeline cross-reference to #4863. Its body has no line that names #4863. It does not change the change.
- Issue #4755 is closed. It fixed the 2FA replay of the interactive login. The test `test_two_factor_login_resends_credentials_with_installed_sdk` cites it.
- Issue #4936 is open. It tracks a browser sign-in with 2FA for the operations portal. It is out of scope (D-11).
- Seven open pull requests exist. None changes a file in the change map of `plan.md`.
- The route folder `specs/numbered/0/0/1/2/3/4/2/3/` does not exist on `main`. No path that contains 4863 exists on `main`.
