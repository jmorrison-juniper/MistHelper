# Research: Validate menu 309 with an MSP login

## 1. Method and truth source

- Remote truth: `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, tree `5f0c0ace8fbec6b46555f16d0b32b9d28907adf2`. Checked on 2026-11-26.
- Local `HEAD` equals `main`. Every local file cited below has a blob SHA equal to its remote blob SHA. Local line numbers therefore equal remote line numbers.
- One full-tree call gave the blob SHAs. File bodies came from the contents API, decoded from base64.
- No credential was used. No live request was made. No build, test, linter, or repository script ran.
- Line numbers follow the form `path:line`. Each row in section 4 is one check.

## 2. Issue and linked work

- Issue #4925 is open. It was created on 2026-11-25T03:29:57Z and updated on 2026-11-26T01:18:20Z. Labels: `chore`, `MistHelper.py`.
- Tasks 1 through 4 of issue #4925 are done on one test organization with an API token. Task 5 is open. Task 5 needs an MSP login.
- Owner comment of 2026-11-26T00:08:35Z lists the steps for the MSP sign-in with 2FA and the MSP run. Those steps are the basis of the live check.
- Owner comment of 2026-11-26T01:18:20Z records a post-merge check on `main` at commit `4e81b2a4a`. It reports 1079 tests passed and 8 skipped.
- Linked pull request #4924 is merged. It merged on 2026-11-26T00:30:01Z from `feat/4920-ex-hardware-inventory-csv`.
- Issue #4920 closed on 2026-11-26T00:36:00Z. Issues #4926 through #4929 closed between 2026-11-26T00:36:03Z and 2026-11-26T00:36:12Z. Issue #4936 is open. It tracks a browser sign-in for the operations portal.
- Legacy record search: no folder under `specs\` starts with `4925-`. Result: `existing_record.found` is false. Steps 3 and 4 of the brief apply to no record.
- Route check: base-5 digits of 4925 form `00124200`. The route `0\0\1\2\4\2\0\0` matches. The algorithm is `spec-route.ps1` lines 7 and 17 (R-66, R-67).

## 3. Decisions

### D-1 HUMAN-DECISION-REQUIRED: who runs the live check, and with which credential

- Alternatives: (a) the implementer runs the MSP check with a stored credential. (b) The owner runs the check in a terminal with the owner's own login (chosen). (c) The owner runs the check in a container.
- Reason: Issue #4925 assigns task 5 to the owner. The sign-in asks for a 2FA code. The operator guide section `Sign in for an MSP run` (heading row R-61) states that a container has no keyboard for that code.
- Risk: The check waits for the owner. Mitigation: the record gives exact steps and an evidence format.
- Recommended option: (b).

### D-2 Coverage rule: what "covers every organization" means

- Alternatives: (a) count organizations in the CSV report. (b) count organization elements in the master XML file. (c) count step 2 lines on the console (chosen).
- Reason: The run writes an outcome row or an XML element only for an organization that fails in step 2, or for an organization with a target (R-07, R-10). An organization with zero switches leaves no row and no element. Step 2 prints one line for each organization in scope (R-08, R-09, R-17).
- Risk: Step 2 lines exist only on the console. The owner copies the count into the evidence contract.
- Recommended option: (c).

### D-3 Pull request keyword

- Alternatives: (a) `Closes #4925`, as section 4 of the brief states. (b) `Refs #4925` (chosen).
- Reason: The issue body says the issue stays open until task 5 passes. A merged `Closes` line closes the issue early.
- Risk: This departs from the brief for this one issue. The orchestrator must record the exception.
- Recommended option: (b).

### D-4 Session lifetime sentence in the operator guide

- Alternatives: (a) keep the sentence that says Mist refuses the requests after the lifetime. (b) remove that sentence and keep the lifetime sentence (chosen). (c) verify the behavior first.
- Reason: The OpenAPI file states the lifetime in minutes for the admin (R-87). No code (R-33) and no OpenAPI text supports the refusal sentence (U-02).
- Risk: An operator loses a warning. Mitigation: the advice to use a token for a long run stays.
- Recommended option: (b).

### D-5 Wording mismatch in the 4920 contract

- Alternatives: (a) edit the 4920 contract in this change. (b) open a follow-up issue (chosen). (c) accept the mismatch.
- Reason: The 4920 record is merged history. The fix changes another record. The Issue first section of `AGENTS.md` asks for one issue for each concern (section 9).
- Risk: The contract stays wrong until the follow-up issue closes.
- Recommended option: (b).

### D-6 Scope of "one outcome row"

- Alternatives: (a) one row per organization for every failure. (b) one row per failed organization in step 2, and one skipped row per confirmed switch in step 4 (chosen).
- Reason: A step 2 failure gives one row (R-07). A step 4 failure gives skipped rows for each confirmed switch (R-13).
- Risk: The owner expects one row for each step 4 failure. The spec states the rule in its user stories.
- Recommended option: (b).

### D-7 Issue labels

- Alternatives: (a) no label change. (b) add `in-progress` only. (c) add `in-progress` and `needs-human-review` (chosen).
- Reason: The label list gives `in-progress` the description "Status: actively being worked on". It gives `needs-human-review` the description "Touches a destructive operation or a safety path" (section 9). The sign-in and secret handling form a safety path under constitution Principle III (R-68).
- Risk: A merge waits for a human review label.
- Recommended option: (c).

### D-8 Changelog fragment

- Alternatives: (a) no fragment. (b) one fragment named `changelog.d/issue-4925-menu-309-msp-validation.md` (chosen).
- Reason: The operator guide change is read by operators. The constitution, section Release notes, requires one fragment for each change (section 9). Only the issue number exists, so the name uses the issue form.
- Risk: None material.
- Recommended option: (b).

## 4. Remote verification table

Each row is one check. The row count is 93. The same count appears in `STATUS.json` and in `summary.md`. Result `absent` means the claim text is not on `main` at the listed path.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|---|---|---|---|---|---|---|
| R-01 | Menu 309 registry entry | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4836 |
| R-02 | Flag `--web-portal` exists | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7402 |
| R-03 | Flag `--login` exists | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7461 |
| R-04 | Menu 309 category is `resource_intensive` | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 538 |
| R-05 | Menu 309 handler is imported by the menu | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 580 |
| R-06 | Login branch on `args.login` | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7635 |
| R-07 | Unread organization gives one outcome row | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 130 |
| R-08 | Step 2 loops over each organization in scope | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 277 |
| R-09 | Step 2 prints one result for each organization | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 282 |
| R-10 | An organization without switches gets no run | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 132 |
| R-11 | No connected switch means no file | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 291 |
| R-12 | Step 4 header | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 298 |
| R-13 | A step 4 failure gives skipped rows for each confirmed switch | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 96 |
| R-14 | Step 1 credential line | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 44 |
| R-15 | Step 1 scope line | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 45 |
| R-16 | Step 1 organizations in scope line | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 46 |
| R-17 | Step 2 count line for each organization | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 62 |
| R-18 | Step 2 discovery failure sentence | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 35 |
| R-19 | Step 2 rate limit sentence | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 34 |
| R-20 | Step 3 read-only shell sentence | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 85 |
| R-21 | Confirmation phrase `RUN n TARGETS` | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 81 |
| R-22 | Confirmation prompt reads typed text | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 90 |
| R-23 | Cancel sentence after an empty answer | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 96 |
| R-24 | Run status line `complete` or `partial` | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 118 |
| R-25 | MSP organization list call | src/operations/exporting/ex_hardware_inventory/scope/resolver.py | main | 866f7c701e574fa368c0203bfcc22062fd82cee1 | present | 118 |
| R-26 | Every page of the MSP list is followed | src/operations/exporting/ex_hardware_inventory/scope/resolver.py | main | 866f7c701e574fa368c0203bfcc22062fd82cee1 | present | 127 |
| R-27 | HTTP 403 reason for the MSP list | src/operations/exporting/ex_hardware_inventory/scope/resolver.py | main | 866f7c701e574fa368c0203bfcc22062fd82cee1 | present | 134 |
| R-28 | Note tail `The run uses one organization.` | src/operations/exporting/ex_hardware_inventory/scope/resolver.py | main | 866f7c701e574fa368c0203bfcc22062fd82cee1 | present | 182 |
| R-29 | MSP scope needs at least one listed organization | src/operations/exporting/ex_hardware_inventory/scope/resolver.py | main | 866f7c701e574fa368c0203bfcc22062fd82cee1 | present | 190 |
| R-30 | Contract wording `The run continues with the organization of the credential` | src/operations/exporting/ex_hardware_inventory/scope/resolver.py | main | 866f7c701e574fa368c0203bfcc22062fd82cee1 | absent | 0 |
| R-31 | Profile read with `getSelf` | src/operations/exporting/ex_hardware_inventory/scope/profile.py | main | fb745bedeac7e0e955f80256f2affd43f72ef7c6 | present | 97 |
| R-32 | Read-only role rule | src/operations/exporting/ex_hardware_inventory/scope/profile.py | main | fb745bedeac7e0e955f80256f2affd43f72ef7c6 | present | 145 |
| R-33 | Code reads the profile field `session_expiry` | src/operations/exporting/ex_hardware_inventory/scope/profile.py | main | fb745bedeac7e0e955f80256f2affd43f72ef7c6 | absent | 0 |
| R-34 | Login success message `+ Login successful!` | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 230 |
| R-35 | MSP detection message `+ MSP access detected` | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 243 |
| R-36 | Two-factor replay call of `login_with_return` | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 199 |
| R-37 | Two-factor code is sent as `two_factor` | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 202 |
| R-38 | Two-factor abort clears the session | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 195 |
| R-39 | Email prompt method | src/mist/access/auth/interactive/credential_prompter.py | main | e1b5197a78e7ec5993faa7dd66eed9c8a553336c | present | 19 |
| R-40 | Password prompt text `  Password: ` | src/mist/access/auth/interactive/credential_prompter.py | main | e1b5197a78e7ec5993faa7dd66eed9c8a553336c | present | 38 |
| R-41 | Two-factor prompt text `  Enter 2FA code: ` | src/mist/access/auth/interactive/credential_prompter.py | main | e1b5197a78e7ec5993faa7dd66eed9c8a553336c | present | 57 |
| R-42 | Portal preview scope line starts `Scope: MSP,` | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 784 |
| R-43 | Portal preview scope line for one organization | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 785 |
| R-44 | Multi Site output choice `One combined CSV report (.csv)` | src/mist/realtime/websocket_streams/web/templates/websockets_page.html | main | cba30182879ba6788f78d36e963da1556006e03e | present | 194 |
| R-45 | Master XML organization element has a status attribute | src/operations/exporting/ex_hardware_inventory/run/master_xml.py | main | 49035cffcb1e94e5beb97dbc750d1cfd53b5d3c0 | present | 414 |
| R-46 | Master XML unread organization has no site | src/operations/exporting/ex_hardware_inventory/run/master_xml.py | main | 49035cffcb1e94e5beb97dbc750d1cfd53b5d3c0 | present | 416 |
| R-47 | Master XML tag prefix `mh:` | src/operations/exporting/ex_hardware_inventory/run/master_xml.py | main | 49035cffcb1e94e5beb97dbc750d1cfd53b5d3c0 | present | 384 |
| R-48 | Report discovery reason text | src/operations/exporting/ex_hardware_inventory/report/builder.py | main | e01cb664623c6e32c7393e65cb8239bcbd3b2b7b | present | 57 |
| R-49 | Fixed CSV column `collection_status` | src/operations/exporting/ex_hardware_inventory/report/columns.py | main | 5489ed5b4151f7cc8bf4c51216636a6362c5192d | present | 52 |
| R-50 | Test: MSP scope gives every organization once | tests/unit/ex_hardware_inventory/scope/test_hardware_resolver.py | main | 8132ee5c22ac5deb7c7c958babf80308718eba10 | present | 120 |
| R-51 | Test: password login with an MSP grant gives MSP scope | tests/unit/ex_hardware_inventory/scope/test_hardware_resolver.py | main | 8132ee5c22ac5deb7c7c958babf80308718eba10 | present | 135 |
| R-52 | Test: step 1 credential line | tests/unit/ex_hardware_inventory/test_hardware_operation.py | main | 98c4fab6e596b00d245652545bd832a59a4ced07 | present | 329 |
| R-53 | Test: password login sends cookies and no token header | tests/unit/websocket_streams/live/transport/test_ws_endpoint.py | main | ea6772ff714722c5396c26574a65e5658ddc96bf | present | 79 |
| R-54 | Test: two-factor prompt text and trimmed value | tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py | main | 49087357e58644c8f11147f542c688e5a9cd25c9 | present | 118 |
| R-55 | Test: two-factor replay with the code | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 463 |
| R-56 | Test: login success message | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 546 |
| R-57 | Test: unread organization is one CSV outcome row | tests/unit/ex_hardware_inventory/run/test_hardware_publisher.py | main | 12fbb5dedef027e0e2a76091b67800d345b428ec | present | 108 |
| R-58 | Test: unread organization is one XML element with no site | tests/unit/ex_hardware_inventory/run/test_hardware_master_xml.py | main | 1a4a77a73fb35c4ada0f343615ae6d0a278251af | present | 439 |
| R-59 | Test: MSP integration run lists each organization | tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py | main | dc4422ccd00aacc8228bc8893308dff32620a95e | present | 400 |
| R-60 | Guard reads the operator guide anchors | tests/guardrails/test_hardware_shell_lock_docs.py | main | 83926b3fbc870c5b69ba48dd5a0a2591ae183ed6 | present | 28 |
| R-61 | Operator guide heading `Sign in for an MSP run` | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 566 |
| R-62 | Operator guide lifetime Caution with `session_expiry` | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 621 |
| R-63 | Changelog fragment policy guard exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| R-64 | Process folder guard reads the baseline | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 15 |
| R-65 | Process folder baseline file exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R-66 | Route digit base is 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-67 | Route width is 8 digits | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| R-68 | Constitution secrets rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 134 |
| R-69 | STE configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| R-70 | Gates table STE row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-71 | Gates table Tests row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R-72 | Pinned mistapi version `mistapi>=0.64.0,<0.65` | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| R-73 | Tool runs on Windows 11, macOS, and Linux | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 15 |
| R-74 | STE gate applies to each Markdown file | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| R-75 | Safety statements start with `Warning` or `Caution` | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 52 |
| R-76 | No semicolon in prose | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 50 |
| R-77 | 4920 FR-039 rate limit rule | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 257 |
| R-78 | 4920 FR-040 one organization for live validation | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 258 |
| R-79 | 4920 FR-070 sign-in rule | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 250 |
| R-80 | 4920 FR-071 sign-in documentation rule | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 251 |
| R-81 | 4920 T095 sign-in review | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 199 |
| R-82 | 4920 T067 is still open | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 175 |
| R-83 | 4920 contract wording for the 403 note | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/cli-menu.md | main | e91b5f8642c06f1eb54d6b68ccc751b928d77798 | present | 79 |
| R-84 | OpenAPI two-factor login path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 3247 |
| R-85 | OpenAPI operation `listMspOrgs` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 4085 |
| R-86 | OpenAPI `getSelf` response uses the admin schema | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 60601 |
| R-87 | OpenAPI admin field `session_expiry` in minutes | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68000 |
| R-88 | OpenAPI admin scope values include `msp` | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68226 |
| R-89 | OpenAPI threshold of 5000 API calls per hour | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 62707 |
| R-90 | API reference 429 text for the API token | documentation/api/msps/DELETE_msps_msp_id.md | main | 62dc5cbda555e12a4931b6449ff0c8d171ad50ed | present | 43 |
| R-91 | 4920 CSV report contract exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/report-csv.md | main | 6812a74f208043bbd49a14d4064d0907e8639b1a | present | 0 |
| R-92 | 4920 master XML contract exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/report-xml.md | main | 78efb316eac40f20f359b55f946a9bdf747f0d83 | present | 0 |
| R-93 | A failed sign-in clears the session | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 224 |

## 5. Mist API evidence

- Login path: `POST /api/v1/login` at OpenAPI line 3089 and `POST /api/v1/login/two_factor` at line 3247 (R-84).
- MSP organization list: `GET /api/v1/msps/{msp_id}/orgs` with `operationId: listMspOrgs` at lines 4081 and 4085 (R-85).
- Profile: `GET /api/v1/self` with `operationId: getSelf` at lines 25460 and 25490. Its response uses the admin schema at line 60601 (R-86).
- Admin object: field `session_expiry` at line 68000 is "Session lifetime for the admin, in minutes" at line 68001 (R-87). The admin scope values include `msp` at line 68226 and `orggroup` at line 68228 (R-88).
- Rate limit: the OpenAPI text reads "5000 API Calls per hour threshold" at line 62707 (R-89). The API reference for the MSP delete path states the threshold for "the API Token used for the request" (R-90).
- The OpenAPI file has no text that states the behavior at session expiry. Section 8 lists this as U-02.

## 6. SDK evidence (installed `mistapi`, read-only)

The installed copy is under `.venv\Lib\site-packages\mistapi`. It is the pinned SDK named in `.github/copilot-instructions.md` (R-72).

- `listMspOrgs(mist_session, msp_id)` at `.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py:17`. The signature has no `limit` parameter.
- `getSelf(mist_session)` at `.venv\Lib\site-packages\mistapi\api\v1\self\self.py:17`.
- `get_next(mist_session, response)` at `.venv\Lib\site-packages\mistapi\__pagination.py:17`. It returns the next page or `None`.
- `login_with_return(self, apitoken, email, password, two_factor)` at `.venv\Lib\site-packages\mistapi\__api_session.py:804-809`.
- Coverage: `documentation/MIST_API_GET_ENDPOINTS.md` maps `listMspOrgs` to `mistapi.api.v1.msps.orgs` (line 331) and `getSelf` to `mistapi.api.v1.self.self` (line 1045). The document is local, and no claim depends on it. `documentation/MIST_API_MISSING_ENDPOINTS.md` also lists `listMspOrgs`. This record does not interpret that list.

## 7. Behavior derived from the code

- Scope: MSP scope needs at least one organization that the MSP list returns (R-29). Otherwise the run uses one organization and prints a note (R-28).
- Step 2: each organization in scope gets one console line (R-09, R-17). A failed organization prints a sentence instead of a count (R-18, R-19).
- Step 2 failure: one outcome row for the organization (R-07). The row has `record_type` `device_outcome`, `collection_status` `failed`, and empty site and device cells (R-48, R-49).
- Step 4 failure: a skipped row for each confirmed switch (R-13). The row carries the reason code.
- Zero switches: the organization has no run, no outcome row, and no XML element (R-10). Its step 2 line still prints (R-17).
- Cancel: an empty answer, end of input, or Ctrl+C prints the cancel sentence and opens no shell (R-23).
- Two-factor abort: an aborted 2FA prompt clears the session (R-38). A failed sign-in also clears the session (R-93).

## 8. Unverified

- U-01: "About three Mist requests for each site." Source: owner comment of 2026-11-26T00:08:35Z, step 6. A local search of the `ex_hardware_inventory` package found no request count. Impact: the spec uses the threshold in FR-007, not this estimate.
- U-02: "After that time, Mist refuses the requests of the session, and the organizations that remain do not finish." Source: operator guide lines 621 to 623 (R-62). No code (R-33) and no OpenAPI text (R-87) supports it. Action: task T009 removes the sentence.
- U-03: The threshold of 5000 calls per hour for a login session. The sources name only the API token (R-89, R-90). Login sessions are not named.
- U-04: The cloud choice prompt of the interactive login. The operator guide names it. The login files cited here do not hold that text. Not verified in this record.
- U-05: The portal session handoff from `--login` to `--web-portal`. Source: 4920 task T095 (R-81). This record does not re-read the handoff code.
- U-06: Whether the admin lifetime in minutes (R-87) applies to the session of a login. The schema describes the admin, not the session token.
- U-07: "No test names the MSP sign-in section." This is a local search of `tests` and `scripts`. It is not a remote proof, and the blob checks cover only the cited files.
- U-08: The owner account has an MSP grant and at least one organization. A credential is needed to check this. Human-only.

## 9. Sources

- Issue #4925 body and comments, read with `gh issue view` on 2026-11-26.
- Pull request #4924, read with `gh pr view` and `gh pr list` on 2026-11-26.
- Issues #4920, #4926, #4927, #4928, #4929, and #4936, read with `gh issue view` on 2026-11-26.
- Remote files on `main`, read with the contents API and checked by blob SHA (section 4).
- Installed SDK under `.venv\Lib\site-packages\mistapi` (section 6).
- No web source was used. No URL is cited.
- `AGENTS.md`, sections "Issue first" and "Writing style", read from `main` (blob `44a9afffb5bd6f774973a845d27343e4e528b6ad`).
- `.specify/memory/constitution.md`, section "Release notes", read from `main` (blob `4584997a264c5a7ade2ca7441246e1f067083aa1`).
- Repository label list, read with `gh label list` on 2026-11-26. The labels `in-progress` and `needs-human-review` carry the descriptions that decision D-7 quotes.
- Documents read in full or by section: `AGENTS.md`, `.github/copilot-instructions.md`, the constitution, the four templates, the 4920 reference record headings and contracts, and the operator guide section `Sign in for an MSP run`.
- Documents not read: `documentation/quality-gates.md`, `architecture.md`, `development-setup.md`, and `container-deployment.md`. This change adds no gate, no module, no setup step, and no container. The gate table in `copilot-instructions.md` covers the gates that apply.
- No skill was loaded. The issue asks no Podman question and no Juniper device question.

## 10. Reference record shape

The reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` has these children. The root holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design`. The `design` folder holds `research.md`, `data-model.md`, `quickstart.md`, `contracts`, and `checklists`. This record copies that shape. It copies no content.

## 11. Defects and gaps in the existing record

- The 4920 contract wording for the 403 note differs from the code (R-30, R-83). Decision D-5 covers it.
- The 4920 FR-040 limits live validation to one organization (R-78). Issue #4925 asks for an MSP run across every organization. Decision D-3 and the spec clarification cover the exception.
- The 4920 task T067 is still open on `main` after the merge (R-82).
- No automated guard names the MSP sign-in section (U-07).
