# Research: Issue 4389, Marvis resolve HTTP 403

## Summary

Menu 270 mode 3 sent one resolve request. Mist answered HTTP 403, and the Marvis Action stayed open. The client treats every non-2xx answer as refused. The repository does not show a client defect. The repository does not show the cause of the refusal either. This research proposes a masked refusal text, a stop rule for HTTP 401 and HTTP 403, tests, and documents. The cause stays unverified until a human collects the evidence listed in `quickstart.md`.

## Issue facts

Source: `gh issue view 4389` on `jmorrison-juniper/MistHelper`, read on 2026-11-26.

- Title: "Runtime: HTTP 403 in MarvisActionsClient.resolve_action". State: OPEN. Created 2026-10-21. Updated 2026-11-08.
- Labels: `bug`, `MistHelper.py`, `needs-human-review`.
- Reported result: one approved resolve request returned HTTP 403. A read-only query showed the action still open. The log excerpt holds `HTTP 403`, `outcome=error`, `verified_status=<empty>`, and `follow-up status=open`.
- Steps: list actions with a read-only request, select one open `vpn_path_down` action, run menu 270, choose the resolve flow, select `suggested`, type `RESOLVE 1`, and record the result. Do not acknowledge the alarm.
- Owner comment, 2026-10-23, URL `https://github.com/jmorrison-juniper/MistHelper/issues/4389#issuecomment-6373877196`: the owner confirms that the client treats only 2xx as success. The owner says the existing unit tests cover HTTP 400, 503, and 429. The owner asks for a sanitized body and a read-only comparison of the caller permission with the Mist UI. The owner says not to repeat a resolve against production.
- The response body is omitted from the issue, because it was not reviewed for sensitive content.

## Linked work and related issues

- Linked pull requests for "4389": none. The search returned an empty list.
- Issue #3299, closed 2026-09-24: "[Spec]: Menu 270 -- export Marvis Actions and bulk resolve them by topic". It introduced menu 270.
- Issue #3341, open, created 2026-09-24: "test: menu 270 mode 3 never sent a live resolve PUT, because the lab organization holds no open Marvis Action". It tracks the live resolve gap, and it stays open.
- Issue #4008, open: "Refactor: isolate Marvis alarm handling modules". It may touch nearby modules.
- Seven open pull requests exist. None changes a path under `marvis`, `operation_registry.py`, `web_portal/services/operation.py`, `MistHelper.py`, or `menu_registry.py`.

## Existing record check

- The search for a folder that starts with `4389-` under `specs\` found nothing.
- The remote tree holds no path that contains `4389` (RC-45).
- A legacy record exists for issue 3299 at `specs\3299-marvis-actions-bulk-resolve`. It is not a record for 4389. Its spec holds a planned HTTP 403 scenario (RC-42). Its quickstart requires a role that can write Marvis (RC-43).
- No legacy record is reused. Steps 3 and 4 of the brief apply only to a record for 4389.

## Route check

- Issue 4389 in base 5 is 1 2 0 0 2 4 (1 × 5^5 + 2 × 5^4 + 2 × 5 + 4 = 4389).
- Padded to eight digits, the route is 0 0 1 2 0 0 2 4. It equals the route from the brief.
- The reference record `4920-ex-hardware-inventory-csv` uses the same rule. 4920 is 1 2 4 1 4 0 in base 5. Padded, it is 0 0 1 2 4 1 4 0, which matches its folder path (RC-44).

## Code path from menu to request

1. Menu 270 maps to `MarvisActionsOperation.run` (`MistHelper.py` line 4472, RC-23). The portal entry is `registry["270"]` (`web_portal/services/operation.py` line 645, RC-24).
2. `MarvisActionsOperation.run` reads mode 3 and sends it to `MarvisResolveWorkflow.resolve_open_actions` (`operation.py` line 385 for the method, line 400 for the resolver call, RC-15).
3. The workflow asks the resolution code, the comment, and the typed confirmation `RESOLVE <count>` (`selection.py` line 504, RC-19). The default code is `suggested` (`model.py` line 126, RC-20).
4. `MarvisBulkResolver.resolve` sends one request for each target. The loop stops only for the stop signal (`operation.py` line 244, RC-10).
5. `MarvisBulkResolver._send` calls `resolve_action` (`operation.py` line 285). A refusal sets outcome `error` (line 288, RC-11). A warning line follows (line 289).
6. `MarvisActionsClient.resolve_action` sends the request through `mist_put` (`client.py` line 184, RC-06). Only status 200 through 299 counts as accepted (line 187, RC-07). Any other status returns the status and the error text (line 189).
7. `_error_text` writes the status and the JSON body, and it caps the text at 300 characters (`client.py` lines 305 to 310, RC-08, RC-09).
8. The verify read runs only when a row holds `OUTCOME_SENT` (`operation.py` line 484, RC-12). The acknowledgement step runs only for resolved rows with an alarm ID (line 497, RC-14). An empty list returns before any prompt (`acknowledgement.py` line 67, RC-17).

The request path is `/api/v1/labs/orgs/{org_id}/suggestions` (`client.py` line 33, RC-05). The body holds `row_key`, `status` set to `resolved`, `label` as the code, `comment`, and `resolve_time` (`selection.py` lines 412 and 413, RC-18).

## Hypotheses for the HTTP 403

Each hypothesis is open. The repository cannot choose between them.

- H-1, role or permission: the token role lacks the permission `canUpdateMarvisActionsStatus`. The repository report says the Mist UI gives the permission to the admin, write, and helpdesk roles (RC-31). The report says the research used admin tokens only (RC-32). The legacy quickstart requires a write role (RC-43). The 2026-10-21 read query worked, so the token authenticated. A role that reads but cannot write fits the evidence. Status: open.
- H-2, endpoint rule: the labs endpoint refuses the request for a reason other than the role. The labs path is absent from the public OpenAPI (RC-34), and the pinned SDK has no method for it (RC-48). The report says no live resolve ran before 2026-10-21 (RC-30). Status: open.
- H-3, action rule: a rule for the action state refuses a manual resolve. No repository evidence exists for this rule. Status: open and unsupported.

The public OpenAPI describes the generic HTTP 403 as a permission error (RC-35). The described labs path is absent, so the generic description does not prove H-1.

## Decisions

### D-1. Keep the resolve request contract

- Alternatives: (a) change the path or body to another shape, (b) keep the path, method, body, and the 2xx rule.
- Chosen: (b).
- Reason: The owner confirms that the client sends the recorded request and treats only 2xx as success. No evidence shows a client defect (RC-06, RC-07).
- Risk: The cause stays open until the evidence arrives.
- Human decision: false.

### D-2. Mask identifiers in the refused error text

- Alternatives: (a) keep the raw body, which is the base behavior, (b) store the status only, (c) store the status and the body with masks for UUIDs, token values, and email addresses, capped at 300 characters.
- Chosen: (c).
- Reason: The raw body reaches the results file (RC-08, RC-11) and the WARNING log without review. Option (b) removes the reason needed to separate H-1 from H-2. Option (c) keeps the reason and removes identifiers.
- Risk: A useful identifier can be masked. A cut UUID fragment can remain at the 300-character limit.
- Human decision: false.

### D-3. Stop mode 3 after HTTP 401 or HTTP 403

- Alternatives: (a) keep the base loop, which sends every request, (b) stop after any non-2xx status, (c) stop after HTTP 401 or HTTP 403 only, (d) stop after HTTP 429 as well.
- Chosen: (c).
- Reason: A token refusal repeats for each request, so later requests add refused writes (RC-10). A 400 or a 500 can depend on one action. Mistapi already retries HTTP 429 (RC-47), so option (d) duplicates that retry.
- Risk: One action-specific refusal stops the run. The results file marks each unsent row, and the next run continues the work.
- Human decision: false.

### D-4. Keep the menu 270 category and file a separate issue

- Alternatives: (a) move mode 3 to `destructive`, (b) keep `interactive_safe` and record the conflict, (c) keep it silently.
- Chosen: (b).
- Reason: A category change changes the sweeps, the portal guards, and the destructive list in several documents. It is a separate concern (RC-22, RC-39, RC-40). The typed confirmation already exists (RC-19).
- Risk: The conflict stays until the separate issue closes it.
- Human decision: false.

### D-5. Add no pre-flight role check in this change

- Alternatives: (a) read the caller role before the first PUT, (b) add no role read in this change.
- Chosen: (b).
- Reason: The role names are stated in the repository report (RC-31), which the record does not verify against the Mist API. The role read adds a call before each run. The record does not check the role field of the self response.
- Risk: The operator must read the role by hand until a later issue adds the check.
- Human decision: false.

### D-6. Use mock sessions in every test

- Alternatives: (a) add a live resolve test in CI, (b) use the fake session in `conftest.py` (RC-28).
- Chosen: (b).
- Reason: The constitution forbids production credentials in tests and requires mocked external responses. A live resolve changes Mist data.
- Risk: The fake session does not prove the live contract. The operator evidence in `quickstart.md` covers that gap.
- Human decision: false.

### D-7. Decide the credential policy for mode 3 runs

- Alternatives: (a) grant the existing token a role that holds `canUpdateMarvisActionsStatus`, (b) use a separate token with an admin, write, or helpdesk role for mode 3, (c) keep the existing token and block mode 3 until the role check passes.
- Recommended: (c) now. Choose (b) if the role check confirms H-1. Option (a) widens write access for every run.
- Reason: A token role changes access for every MistHelper user. A human owns the credential policy.
- Risk: Option (c) blocks the bulk resolve workflow until the check completes.
- Human decision: true. HUMAN-DECISION-REQUIRED.

### D-8. State the HTTP 403 cause as unverified in the documents

- Alternatives: (a) state the cause as a role problem, (b) state the cause as unknown and list the evidence needed.
- Chosen: (b).
- Reason: No source confirms H-1 or H-2. The endpoint report states that no live resolve ran (RC-30). The documents must match the evidence.
- Risk: A reader can read the section as incomplete. The steps in `quickstart.md` give the next action.
- Human decision: false.

## Remote verification

The remote tree is `git/trees/main?recursive=1` (11,404 entries, not truncated). Blob SHAs are read from the tree. Line numbers were read from the decoded blob bodies returned by `git/blobs`. The local files for the cited governing documents, the endpoint report, the operator guide, `client.py`, `operation.py`, `ci.yml`, and the OpenAPI file have a git blob hash that equals the remote blob. Local bytes and remote bytes are identical for these files.

The local mistapi rows use the Git blob formula on the installed bytes. The installed package is `mistapi-0.64.1.dist-info`. The path is local and is not a repository path.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Owner comment cites commit 9991d30a as current main | commits/9991d30a | main | 9991d30a187e5d215462eefac60a09a57e5f99e5 | present | 0 |
| RC-02 | Record base is remote main | commits/main | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-03 | Class MarvisActionsClient is defined | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 60 |
| RC-04 | Method resolve_action is defined | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 175 |
| RC-05 | Resolve path is the labs suggestions path | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 33 |
| RC-06 | Resolve sends the body through mist_put | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 184 |
| RC-07 | Only HTTP 2xx counts as accepted | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 187 |
| RC-08 | Error text includes the Mist body through json.dumps | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 309 |
| RC-09 | Error text cap constant is 300 characters | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 37 |
| RC-10 | Resolve loop stops only for the stop signal | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 244 |
| RC-11 | Error row keeps the reason and the error outcome | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 288 |
| RC-12 | Verify runs only when a row holds OUTCOME_SENT | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 484 |
| RC-13 | Verified status is set in the verify step | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 298 |
| RC-14 | Acknowledgement is limited to resolved rows with an alarm ID | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 497 |
| RC-15 | Mode 3 workflow calls the resolver after the prompts | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 400 |
| RC-16 | Results file name is OrgMarvisActionsResolveResults.csv | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 89 |
| RC-17 | Empty acknowledgement list returns before any prompt | src/mist/intelligence/marvis/actions/acknowledgement.py | main | 765c01070ebdf0d79580af464441f9f44e3c34fb | present | 67 |
| RC-18 | Request body fields are row_key, status, label, comment, and resolve_time | src/mist/intelligence/marvis/actions/selection.py | main | b0c5e5b834f636b521abd1056f0c3cf20ecf1f68 | present | 412 |
| RC-19 | Typed confirmation expects RESOLVE followed by the count | src/mist/intelligence/marvis/actions/selection.py | main | b0c5e5b834f636b521abd1056f0c3cf20ecf1f68 | present | 504 |
| RC-20 | Resolution code suggested is the first code | src/mist/intelligence/marvis/actions/model.py | main | 8d81f971c2b2e12c3f942572315e298851ad428e | present | 126 |
| RC-21 | Topic gateway vpn_path_down is in the topic table | src/mist/intelligence/marvis/actions/model.py | main | 8d81f971c2b2e12c3f942572315e298851ad428e | present | 74 |
| RC-22 | Menu 270 is interactive_safe with a note for issue 3299 | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 347 |
| RC-23 | Menu 270 handler is MarvisActionsOperation.run | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4472 |
| RC-24 | Portal mode 3 label says the mode changes Mist | web_portal/services/operation.py | main | 39f9446da8648fb245022c63dc382ff38ccece76 | present | 654 |
| RC-25 | Unit test covers resolve HTTP 400 | tests/unit/marvis/actions/test_client.py | main | 19b8ca17116d2f098c639623efef496670dfece1 | present | 381 |
| RC-26 | No resolve unit test covers HTTP 403 | tests/unit/marvis/actions/test_client.py | main | 19b8ca17116d2f098c639623efef496670dfece1 | absent | 0 |
| RC-27 | No run unit test sends a refused PUT with HTTP 403 | tests/unit/marvis/actions/test_operation.py | main | be88636e3f63030d2dd73c8f10663e6fcacd7199 | absent | 0 |
| RC-28 | Fake session queues PUT statuses | tests/unit/marvis/actions/conftest.py | main | 4ecef3a5dbdcce1c5184b83795420c6e627834b9 | present | 164 |
| RC-29 | Endpoint report lists the labs PUT | documentation/marvis-actions-api-endpoints.md | main | 0e96ef07104c0d610c6d75dd558a0fd331499451 | present | 30 |
| RC-30 | Endpoint report states that no live resolve ran | documentation/marvis-actions-api-endpoints.md | main | 0e96ef07104c0d610c6d75dd558a0fd331499451 | present | 582 |
| RC-31 | Endpoint report names the permission and the roles admin, write, and helpdesk | documentation/marvis-actions-api-endpoints.md | main | 0e96ef07104c0d610c6d75dd558a0fd331499451 | present | 637 |
| RC-32 | Endpoint report states that the research used admin tokens only | documentation/marvis-actions-api-endpoints.md | main | 0e96ef07104c0d610c6d75dd558a0fd331499451 | present | 640 |
| RC-33 | Operator guide describes mode 3 as changing records and needing RESOLVE | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 33 |
| RC-34 | Public OpenAPI document has no labs path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 0 |
| RC-35 | Public OpenAPI defines a generic HTTP 403 permission error response | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94784 |
| RC-36 | CI sets MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-37 | CI sets VULTURE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-38 | CI sets INTERROGATE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-39 | Repository defines a destructive operation as one that changes the Mist cloud | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 311 |
| RC-40 | Constitution destructive list includes other changes to the Mist cloud | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 120 |
| RC-41 | Changelog rule names an issue fragment issue-number-slug | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| RC-42 | Legacy issue 3299 spec planned an HTTP 403 scenario | specs/3299-marvis-actions-bulk-resolve/spec.md | main | acfec4208241383afd2802a665b2b3da852b2ace | present | 174 |
| RC-43 | Legacy issue 3299 quickstart requires an organization role that can write Marvis | specs/3299-marvis-actions-bulk-resolve/quickstart.md | main | 78e8eb0d0ccd355d5c42c2e874d54c91c625ac65 | present | 12 |
| RC-44 | Reference record exists for the record shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-45 | No record exists for issue 4389 under the route | specs/numbered/0/0/1/2/0/0/2/4/ | main | none (0 entries) | absent | 0 |
| RC-46 | Local SDK defines session method mist_put | .venv\Lib\site-packages\mistapi\__api_request.py | mistapi 0.64.1 installed | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 303 |
| RC-47 | Local SDK retries only HTTP 429 and returns other HTTP errors as a response | .venv\Lib\site-packages\mistapi\__api_request.py | mistapi 0.64.1 installed | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 229 |
| RC-48 | Local SDK has no endpoint method for the labs suggestions path | .venv\Lib\site-packages\mistapi | mistapi 0.64.1 installed | none (directory search) | absent | 0 |
| RC-49 | Guard test for changelog fragments exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-50 | Guard test for the Marvis portal exposure exists | tests/guardrails/test_marvis_actions_portal_exposure.py | main | 369ff646c36b180ed9af032905bb38745962584a | present | 0 |
| RC-51 | Repository defines data/script.log as the runtime log | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 337 |
| RC-52 | Test class TestResolveRequest exists | tests/unit/marvis/actions/test_client.py | main | 19b8ca17116d2f098c639623efef496670dfece1 | present | 358 |
| RC-53 | Test class TestResolve exists | tests/unit/marvis/actions/test_operation.py | main | be88636e3f63030d2dd73c8f10663e6fcacd7199 | present | 416 |
| RC-54 | The Marvis actions folder holds seven direct children | src/mist/intelligence/marvis/actions/ | main | none (folder listing, seven blob children) | present | 0 |

Totals: 54 checks. 49 present. 5 absent (RC-26, RC-27, RC-34, RC-45, RC-48).

## Sources

Local paths and remote URLs read for this record:

- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and the four templates under `.specify/templates/`.
- `documentation/quality-gates.md`. It states that STE grades Markdown and Python files, and it lists the CI job IDs.
- `documentation/architecture.md`. It states that new features go in `src/`. The change follows that rule.
- `documentation/development-setup.md`, Step 2. It states that a new worktree needs the bootstrap before tests run.
- `documentation/container-deployment.md`. Its section "Test and debug containers" applies only when a container starts. This record starts no container.
- `documentation/marvis-actions-api-endpoints.md`, `documentation/operator-guide.md`, and `documentation/mist-api-openapi31yaml.yaml`.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Its spec starts with the clarifications after the header, followed by user stories with acceptance scenarios. This record copies that order.
- The unit tests `tests/unit/marvis/actions/test_client.py`, `test_operation.py`, and `conftest.py`.
- The installed SDK `.venv\Lib\site-packages\mistapi\__api_request.py` and `__pagination.py`.
- Issue 4389: `https://github.com/jmorrison-juniper/MistHelper/issues/4389`.
- The owner comment: `https://github.com/jmorrison-juniper/MistHelper/issues/4389#issuecomment-6373877196`.

No web source was fetched. The labs contract stays unverified, because no public or local source describes it.

## Unverified

- U-1: The meaning of HTTP 403 for `/api/v1/labs/orgs/{org_id}/suggestions`. Reason: the labs path is absent from the public OpenAPI (RC-34) and from the SDK (RC-48).
- U-2: The role names and the permission in the live product. Reason: the repository report states them (RC-31), and the research used admin tokens only (RC-32).
- U-3: The body of a live HTTP 403 response for the labs path. Reason: no live response is on record (RC-30).
- U-4: The role that the 2026-10-21 token held. Reason: the repository does not record it.
- U-5: An action-state rule that refuses a manual resolve. Reason: no repository evidence exists.
- U-6: The content of the mistapi ERROR log line for an HTTP error. Reason: the record does not check that log text. The SDK code path is in RC-47.
- U-7: Whether masking covers every identifier format in a Mist error body. Reason: no sample body from the labs path exists.

## Skills and tools

- No skill was loaded. The issue concerns the Mist cloud API client. It does not concern Podman or a Juniper device.
- No container was started. No build, test, package install, or repository script ran.
- The repository was read only. Git reads used no checkout, fetch, or write command.
