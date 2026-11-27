# Research: Menu 270 Live Resolve Acceptance Evidence

Each decision gives the options, the chosen option, the reason, and the risk. Facts come from the issue record, from the pinned SDK, and from repository files. Each code claim cites a row of the remote verification table.

## Decisions

### D-1 HUMAN-DECISION-REQUIRED: Who runs the live check and under which access

- **Decision**: The repository owner runs the live check after written approval. The agent does not run it. The agent does not request a lab credential.
- **Options**: (a) The agent runs the check with a lab credential. (b) The owner runs the check with the owner's own access after written approval. (c) Close issue #3341 without live evidence.
- **Chosen**: (b). This is the recommended option.
- **Reason**: The brief forbids the agent from requesting or using a credential. The connected Mist tools do not expose the beta actions list (issue comment IC_kwDOQltU8c8AAAABkIBgGQ). Closing without evidence leaves the acceptance criteria open.
- **Risk**: Acceptance waits for the owner. Mitigation: `design\quickstart.md` and the evidence record format in `design\contracts\live-evidence-record.md`.
- **Human decision**: Credential policy. The owner confirms who holds lab access and approves the live run.

### D-2 Retry after the HTTP 403 response

- **Decision**: No retry occurs until issue #4389 names a cause or the owner approves a new run in writing.
- **Options**: (a) Retry now with the same body. (b) Wait for the cause or for written approval. (c) Change the body and retry.
- **Chosen**: (b). This is the recommended option.
- **Reason**: Issue comment IC_kwDOQltU8c8AAAABkIBgGQ says "Do not retry the resolve." The cause is unknown. The body matches the test set in `tasks.md`, and no record shows a body defect.
- **Risk**: Acceptance can wait for a long time. Mitigation: the owner approves a new run when the cause is known.

### D-3 Endpoint report now or after the live run

- **Decision**: Correct the two stale statements now, add the 2026-10-21 attempt, and add the accepted date after a live HTTP 2xx result.
- **Options**: (a) Wait for the live run. (b) Correct now, then add the accepted date later. (c) Remove the live section.
- **Chosen**: (b). This is the recommended option.
- **Reason**: Row 26 says that no live request was sent. The issue record contradicts that statement. Option (c) removes evidence. Option (a) leaves a false statement in place.
- **Risk**: A second edit follows acceptance (task T006).

### D-4 Test scope

- **Decision**: Run the 22 existing tests of the test set. Add no new test.
- **Options**: (a) Add a test for HTTP 403. (b) Run the existing tests and add none. (c) Rewrite the offline tests.
- **Chosen**: (b). This is the recommended option.
- **Reason**: The non-2xx branch in `resolve_action` (rows 6 and 7) treats HTTP 403 like HTTP 400, 429, and 503. The test set covers those statuses (tests 4, 5, and 7 of the test set, and research row 21). The branch does not depend on the status value. No behavior changes, so a new test would repeat a covered branch.
- **tests_planned**: 22 existing test functions.
- **Risk**: The exact text of an HTTP 403 response is not tested. The risk is low, because the branch returns the same result for every non-2xx status.

### D-5 HUMAN-DECISION-REQUIRED: Category of menu 270 mode 3

- **Decision**: Keep `interactive_safe` for this change, with the typed gate and the stated reason.
- **Options**: (a) Keep `interactive_safe`. (b) Move mode 3 to `destructive` and remove the portal row. (c) Move mode 3 to a new destructive menu number.
- **Chosen**: (a). This is the recommended option for this change.
- **Reason**: The registry comment (row 4) states that the operations portal needs the row. The typed gate (row 17) meets the typed-confirmation rule of constitution Principle III. The written rules conflict with the registry. The copilot instructions define destructive as a change to the Mist cloud or a production device (row 28). The constitution lists other changes to the Mist cloud as destructive (row 33). Mode 3 changes Mist cloud state (row 14). Option (b) changes product behavior. Option (c) needs a larger change.
- **Risk**: A Mist-changing action stays in the portal. Mitigations: the typed count gate, the preview, and the default mode 1.
- **Human decision**: Product priority and safety class. The owner decides before the pull request merges, because the issue carries `needs-human-review`.

### D-6 Mist transport for the resolve request

- **Decision**: Use `APISession.mist_put` from the pinned mistapi package with the labs path.
- **Options**: (a) `APISession.mist_put` from mistapi. (b) A raw HTTP client. (c) An owned WebSocket transport.
- **Chosen**: (a). This is the recommended option.
- **Reason**: mistapi 0.64.1 holds no method for the labs paths (row 50). `mist_put` is a method of the mistapi session (row 43), so the call stays inside the SDK session. A raw HTTP client breaks the rule in constitution section "Technology & Compatibility Constraints" (row 34). An owned WebSocket transport covers no flow in this feature.
- **Risk**: The labs path is beta. A future mistapi release may add a method. Mitigation: test 1 of the test set fails when the path changes.

### D-7 Pull request keyword

- **Decision**: The pull request body uses `Refs #3341` until the owner evidence record shows acceptance.
- **Options**: (a) `Closes #3341`. (b) `Refs #3341` until acceptance. (c) No issue link.
- **Chosen**: (b). This is the recommended option.
- **Reason**: The acceptance criteria in the issue body stay open. A squash merge reads the pull request body (`AGENTS.md`, commit and merge rules). The brief names `Closes`. This decision departs from the brief for this issue only, because a closure before acceptance would hide the open evidence gap.
- **Risk**: Issue #3341 stays open after the merge. This is intended until task T005.

## Method

- One tree call on `main` returned 11,404 entries. The tree was not truncated.
- Each cited line came from a decoded file body on `main`, or from a local file whose `git hash-object` equals the `main` blob SHA. The local check covered `MistHelper.py`, `operation_registry.py`, `client.py`, `operation.py`, `selection.py`, `test_client.py`, `test_operation.py`, `test_selection.py`, `endpoint_primary_key_strategies.py`, `marvis-actions-api-endpoints.md`, `copilot-instructions.md`, `constitution.md`, `AGENTS.md`, the OpenAPI document, and the 3299 research file.
- No `gh` call returned HTTP 403 or 429. No retry was needed.
- Rows 43 to 51 cite the pinned SDK in `.venv\Lib\site-packages\mistapi`. Third-party packages are not in the repository tree, so their rows carry the local path and the ref `local-venv`.

## Remote Verification

Rows: 52. The `remote_checks` array in `META\3341-STATUS.json` and the summary use the same count.

| Row | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| 1 | Menu 270 row binds `MarvisActionsOperation.run` | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4470 |
| 2 | Menu 270 imports `MarvisActionsOperation` | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 778 |
| 3 | Menu 270 row has category `interactive_safe` | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 346 |
| 4 | Registry comment gives the reason for mode 3 classification | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 340 |
| 5 | `RESOLVE_PATH` is the labs suggestions path | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 33 |
| 6 | `resolve_action` sends a status change for one action | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 175 |
| 7 | `resolve_action` calls `mist_put` once with `RESOLVE_PATH` | src/mist/intelligence/marvis/actions/client.py | main | a7577ff0167e7462fb73adc39adc81036247cbdf | present | 184 |
| 8 | Results file name is `OrgMarvisActionsResolveResults.csv` | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 89 |
| 9 | `OUTCOME_SENT` is the interim outcome `sent` | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 96 |
| 10 | `OUTCOMES` lists resolved, sent_unverified, error, not_sent, and skipped | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 102 |
| 11 | `MarvisResolveResult` is the results row with 26 columns | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 108 |
| 12 | `_verdict` marks a row resolved only for a closed status | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 303 |
| 13 | `_write_results` writes the results file through the shared exporter | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 514 |
| 14 | Mode 3 branch resolves open actions | src/mist/intelligence/marvis/actions/operation.py | main | 4934903c7a2e81d225e75195779a7ba00bd634c9 | present | 618 |
| 15 | `MarvisResolveRequest` holds the code, the comment, and the run time | src/mist/intelligence/marvis/actions/selection.py | main | b0c5e5b834f636b521abd1056f0c3cf20ecf1f68 | present | 388 |
| 16 | Request body sets `status` to `resolved` | src/mist/intelligence/marvis/actions/selection.py | main | b0c5e5b834f636b521abd1056f0c3cf20ecf1f68 | present | 412 |
| 17 | Typed confirmation text is `RESOLVE` followed by the count | src/mist/intelligence/marvis/actions/selection.py | main | b0c5e5b834f636b521abd1056f0c3cf20ecf1f68 | present | 504 |
| 18 | `OPEN_STATUSES` holds open, inprogress, and reoccured | src/mist/intelligence/marvis/actions/model.py | main | 8d81f971c2b2e12c3f942572315e298851ad428e | present | 27 |
| 19 | `STATUS_NAMES` lists the status keys | src/mist/intelligence/marvis/actions/model.py | main | 8d81f971c2b2e12c3f942572315e298851ad428e | present | 29 |
| 20 | Client tests name the labs path, the body, and the refusal outcomes | tests/unit/marvis/actions/test_client.py | main | 19b8ca17116d2f098c639623efef496670dfece1 | present | 358 |
| 21 | Operation test asserts an error row for a refused request | tests/unit/marvis/actions/test_operation.py | main | be88636e3f63030d2dd73c8f10663e6fcacd7199 | present | 594 |
| 22 | Selection tests assert the five body fields and no suggestion ID | tests/unit/marvis/actions/test_selection.py | main | e11821c188e553e17ec5798ffe0c67d034a4ec92 | present | 543 |
| 23 | Portal contract lists seven controls in prompt order | tests/unit/marvis/actions/test_portal_contract.py | main | c0f3ba395ea5d93079c2f3af556761509b78e5eb | present | 50 |
| 24 | `resolveOrgMarvisActions` has a primary key strategy | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 249 |
| 25 | Endpoint report names mistapi 0.64.0 | documentation/marvis-actions-api-endpoints.md | main | 0e96ef07104c0d610c6d75dd558a0fd331499451 | present | 13 |
| 26 | Endpoint report says no live resolve request was sent | documentation/marvis-actions-api-endpoints.md | main | 0e96ef07104c0d610c6d75dd558a0fd331499451 | present | 582 |
| 27 | Category table lists menu 270 as `interactive_safe` | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 219 |
| 28 | Destructive means a change to the Mist cloud or a production device | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 311 |
| 29 | Local gates section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| 30 | Architecture section names the menu entry point | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 153 |
| 31 | Bootstrap and activation commands | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 29 |
| 32 | Language and environment section names Python 3.15, the mistapi pin, and the devtools commands | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 18 |
| 33 | Principle III covers other changes to the Mist cloud as destructive | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 120 |
| 34 | Constitution sets the mistapi direct HTTP rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 280 |
| 35 | `AGENTS.md` defines the writing style | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| 36 | Route script sets the width to 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| 37 | Route script sets the base to 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 38 | Reference record title, the shape source | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| 39 | Route folder for 3341 is absent | specs/numbered/0/0/1/0/1/3/3/1 | main | none | absent | 0 |
| 40 | No record folder for 3341 exists | specs (folders named 3341-) | main | none | absent | 0 |
| 41 | PR 3316 retired path `marvis/actions/client.py` is absent | retired `marvis/actions/client.py` | main | none | absent | 0 |
| 42 | OpenAPI document holds no labs path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 0 |
| 43 | mistapi `mist_put` method | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | none | present | 303 |
| 44 | mistapi `mist_get` method | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | none | present | 260 |
| 45 | mistapi `get_all` helper | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | none | present | 39 |
| 46 | mistapi `get_next` helper | .venv\Lib\site-packages\mistapi\__pagination.py | local-venv | none | present | 17 |
| 47 | mistapi `ackOrgMultipleAlarms` function | .venv\Lib\site-packages\mistapi\api\v1\orgs\alarms.py | local-venv | none | present | 17 |
| 48 | mistapi `searchOrgAlarms` function | .venv\Lib\site-packages\mistapi\api\v1\orgs\alarms.py | local-venv | none | present | 135 |
| 49 | mistapi `listOrgSites` function | .venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py | local-venv | none | present | 17 |
| 50 | mistapi holds no labs or org suggestion method, checked in 288 Python files | .venv\Lib\site-packages\mistapi | local-venv | none | absent | 0 |
| 51 | Installed mistapi distribution is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local-venv | none | present | 0 |
| 52 | Safety section places each product output under `data/` | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 309 |

## Sources

- Issue #3341, read with `gh issue view 3341 -R jmorrison-juniper/MistHelper`. State open. Labels: chore, tests, api, src, needs-human-review. Updated 2026-11-08T08:31:57Z. Comments: IC_kwDOQltU8c8AAAABWysfYQ (2026-09-25), IC_kwDOQltU8c8AAAABY__A4g (2026-10-03), IC_kwDOQltU8c8AAAABaCWRGA (2026-10-07), IC_kwDOQltU8c8AAAABeBNT3g (2026-10-21), IC_kwDOQltU8c8AAAABeBmFAQ (2026-10-21), and IC_kwDOQltU8c8AAAABkIBgGQ (2026-11-08).
- Pull request #3316, read with `gh pr view 3316`. State merged. Head branch `feat/3299-marvis-actions-bulk-resolve`. Its body says `Closes #3299` and `Closes #3308`. Its file list names paths that row 41 shows as absent.
- Issue #4389, read with `gh issue view 4389`. State open. Title "Runtime: HTTP 403 in MarvisActionsClient.resolve_action". Updated 2026-11-08T17:42:36Z.
- Issue #3339 is named in the 2026-09-25 comment. It was not fetched.
- `gh pr list --search "3341"` returned no pull request. The issue body names PR #3316, so that pull request is included by reference.
- Local tree at `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`, read only. Git commands used: `git hash-object` without a write flag, and `git rev-parse HEAD`.
- Pinned SDK at `.venv\Lib\site-packages\mistapi`, distribution 0.64.1 (row 51).
- Mist OpenAPI document at `documentation\mist-api-openapi31yaml.yaml`, 4,317,370 bytes. It was searched with grep. It was not read in full, because the file exceeds 20 KB.
- Local skills: none loaded. The issue concerns the Mist cloud API. It does not concern Podman or Juniper device behavior.
- Web: no `web_fetch` call. No upstream URL is cited.
- Credentials: GitHub reads used the account identity that brief rule 5 names. The account variable was checked for presence by name only. No Mist, lab, or other credential was requested or used.
- Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. Its shape was used. No content was copied.

## Unverified

- **U-1 The cause of the HTTP 403 response.** Issue #4389 is open. Its body was not read. The lab organization is not reachable from this session.
- **U-2 The current state of the lab organization.** The last read in the issue record is the 2026-11-08 comment, which sent no list request. The count of open actions now is unknown.
- **U-3 Whether Mist accepts the labs resolve body.** The only live result in the issue record is the 2026-10-21 refusal. No accepted result exists.
- **U-4 The default file log level for `data\script.log`.** The log handler setup in `MistHelper.py` was searched. The default level was not traced.
- **U-5 The Mist UI bundle named in the issue body** (`admin2.21.1765-hotfix`, chunk 490). It was not fetched. The issue text is the only source.
- **U-6 The browser extension file named in the issue body** (`quick_links_audit.yaml`). It was not fetched.
- **U-7 mistapi 0.64.0, the lower bound of the pin.** Only 0.64.1 is installed, and only 0.64.1 was inspected.
- **U-8 Whether the labs endpoints changed after 2026-10-21.** No new test was run.
- **U-9 The meaning of the HTTP 403 status for this endpoint.** Account privilege and beta gating both remain possible. No test separates them.
