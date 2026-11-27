# Research: Webhook response status

## Method

The truth order of the brief applies. Remote evidence from GitHub `main` outranks local search. Each repository path in this record matched its `main` blob SHA. The local copy equals `main` for each of the 44 cited repository paths. The check used `git hash-object` without a write. The SDK files come from the local `.venv`, which is not in git. Their line numbers come from read-only views. Narrative line references in the spec, plan, and tasks match the decoded content of `main`, which has the same blob SHA as the local copy.

## Decisions

### D-1 The web portal selector stays outside issue #4718

- Alternatives: (a) add `web_portal/routes/settings.py` to this repair. (b) open a separate issue for the portal path.
- Chosen: (b). Recommended.
- Reason: The owner comments of 2026-11-09 name only the exporter, its reserved test, and the stable-selection test. AGENTS.md asks for one concern per issue. The portal path has its own browser test (R22, R23) and its own log wording.
- Evidence: R24 and R25 (lines 46 and 47 of `web_portal/routes/settings.py`).
- Risk: Menu 256 in the browser shows an empty choice list for a missing HTTP status until the separate issue merges.
- Human decision: no.

### D-2 Accept only integer HTTP statuses from 200 through 299

- Alternatives: (a) accept any integer below 400, which permits 1xx and 3xx. (b) accept 200 through 299 only. (c) reject only the documented error codes.
- Chosen: (b). Recommended.
- Reason: FR-003 requires the 200 to 299 range. The OpenAPI lists 200 as the only success code for both operations (OpenAPI lines 23871 to 23883 and 24106 to 24118). The list operation documents 403, 404, and 429, but not 500 or 503. Option (c) would miss the undocumented HTTP 503 in the issue.
- Evidence: R03 (range line 22), R02 (reader line 28), R30 (`org_inventory_search_exporter.py` line 89 uses the same range).
- Risk: A future SDK that returns a 2xx status outside 200 to 299 would fail the gate. The SDK pin and the contract tests reduce this risk.
- Human decision: no.

### D-3 Keep the private HTTP status reader in the exporter

- Alternatives: (a) reuse `http_response_status.http_failure`. (b) move a reader into a shared module. (c) keep `_response_status_code` in the exporter.
- Chosen: (c). Recommended.
- Reason: `http_failure` returns False when the status is not an integer (R29, line 17 and the lines after it). That result treats a missing status as success, which FR-004 forbids. Option (b) edits a shared module outside the reserved files.
- Evidence: R29, R02.
- Risk: Two status readers exist in the code base. RM-6 covers the duplicates.
- Human decision: no.

### D-4 Log the HTTP status inside the reader

- Alternatives: (a) add one debug line at each call site. (b) add a logging method to the class. (c) log inside `_response_status_code`, with the call name as an operation parameter.
- Chosen: (c). Recommended.
- Reason: The class holds five static methods (R08 context). A logging method adds a sixth method, which breaks the five-item rule. Option (a) adds lines to `_select_webhook_id`, which already holds 25 lines, and to `deliveries()`, which already holds 32 lines. Option (c) changes only the helper. The module keeps its names, because a new module constant would add a child to a module that already exceeds five children (R14).
- Evidence: R01 (span of `_select_webhook_id`), R08 (span of `deliveries()`), R14 (module children).
- Risk: The helper gains a parameter. T009 requires a search for other callers (RK-5).
- Human decision: no.

### D-5 Add one parametrized test to an existing class

- Alternatives: (a) add a new class. (b) add a new test module. (c) add one parametrized method to `TestWebhookInitialResponse`.
- Chosen: (c). Recommended.
- Reason: The class holds four methods (R10 to R13). Option (c) gives five methods, which is the limit. A new class adds a top-level child to a module that already exceeds five (R14). A new module spreads one repair across a second file.
- Evidence: R09, R14.
- Risk: The parametrized test covers two calls in one method, so a failure names the case by parameter.
- Human decision: no.

### D-6 Reuse the legacy record folder and slug

- Alternatives: (a) create `4718-webhook-response-failures`. (b) reuse `4718-webhook-response-status`.
- Chosen: (b). Recommended.
- Reason: One issue keeps one record. The route folder holds one child now (`route children: 1`, which is the legacy folder). Option (a) adds a second child and leaves two records for one issue. The legacy folder is verified on `main` (R60 to R67). Its stale claims appear in `analysis.md`.
- Risk: The orchestrator replaces the legacy files. The eight legacy files have matching names, so no legacy file survives unchanged.
- Human decision: no.

### D-7 Repair branch and pull request

- Alternatives: (a) push to `fix/4718-webhook-response-failures`. (b) open a new issue first, which the repository post-merge rule suggests. (c) create `fix/4718-webhook-log-comments` from `main` under issue #4718.
- Chosen: (c). Recommended.
- Reason: Issue #4718 stays open, and its Principle VI and VII requirements are unmet. A branch from `main` avoids the merged branch. Option (a) pushes to a squash-merged branch, which the repository rules forbid. If the orchestrator prefers option (b), the branch name changes, and the pull request body names the new issue.
- Risk: The post-merge rule and this choice differ. The orchestrator records the choice on the issue.
- Human decision: no.

### D-8 Add no changelog fragment for the repair

- Alternatives: (a) add a fragment named for the pull request. (b) add no fragment and state the reason in the pull request body.
- Chosen: (b). Recommended.
- Reason: The repair adds comments and debug lines only. The changelog rule excludes internal-only changes (R84). The existing fragment covers the user-visible fix (R20).
- Risk: None known.
- Human decision: no.

### D-9 Keep the labels until the repair merges

- Alternatives: (a) remove `in-progress` now. (b) keep the labels until the repair merges.
- Chosen: (b). Recommended.
- Reason: The repair remains open. The issue carries `bug`, `MistHelper.py`, and `in-progress`. The orchestrator removes `in-progress` when it closes the issue.
- Labels to add: none. Labels to remove: none.
- Human decision: no.

### D-10 Treat issue #4715 as delivered

- Alternatives: (a) treat #4715 as an open dependency. (b) treat #4715 as delivered.
- Chosen: (b). Recommended.
- Reason: Issue #4715 closed on 2026-11-19. PR #4849 merged as commit a3e8a2e7 (R75). The writer behavior that this issue keeps is on `main`.
- Risk: None known.
- Human decision: no.

### D-11 Sibling exporters and menu 45 stay outside issue #4718

- Alternatives: (a) repair every exporter that defaults a missing status to 200 in one issue. (b) repair this issue only and open separate issues for the siblings.
- Chosen: (b). Recommended.
- Reason: AGENTS.md asks for one concern per issue. The sibling files keep their own helpers and tests. Menu 45 uses a generic export path (R28), which the review did not trace (U-2).
- Evidence: R31, R32, U-3.
- Risk: The same defect remains in other exporters until their issues merge.
- Human decision: no.

### D-12 Record Principle I debt and do not refactor it here

- Alternatives: (a) split `deliveries()` and the test module in this repair. (b) record each violation in `plan.md` and open a remediation issue.
- Chosen: (b). Recommended.
- Reason: Principle I requires the plan to record each touched violation and a separate remediation action. A split widens the diff beyond FR-006 and FR-008.
- Evidence: R08, R14, R19.
- Risk: Principle I stays violated until the remediation merges.
- Human decision: no.

## Remote Verification Table

Columns: ID, claim, path, ref, blob SHA, result, line. For commit rows, the blob SHA column holds the commit SHA. For the local SDK rows, the blob SHA is the git hash of the local file.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R01 | List call gate precedes pagination | src/operations/exporting/export/org_webhook_deliveries_exporter.py | main | 1dbd5f42cc5ff7c0292e4e37d367763c7666ca81 | present | 76 |
| R02 | HTTP status reader rejects Booleans and non-integers | src/operations/exporting/export/org_webhook_deliveries_exporter.py | main | 1dbd5f42cc5ff7c0292e4e37d367763c7666ca81 | present | 28 |
| R03 | Accepted HTTP status range starts at 200 and ends below 300 | src/operations/exporting/export/org_webhook_deliveries_exporter.py | main | 1dbd5f42cc5ff7c0292e4e37d367763c7666ca81 | present | 22 |
| R04 | Delivery call gate precedes pagination | src/operations/exporting/export/org_webhook_deliveries_exporter.py | main | 1dbd5f42cc5ff7c0292e4e37d367763c7666ca81 | present | 138 |
| R05 | Inline comment on the list gate line (Principle VI) | src/operations/exporting/export/org_webhook_deliveries_exporter.py | main | 1dbd5f42cc5ff7c0292e4e37d367763c7666ca81 | absent | 76 |
| R06 | Debug line after the list SDK call (Principle VII) | src/operations/exporting/export/org_webhook_deliveries_exporter.py | main | 1dbd5f42cc5ff7c0292e4e37d367763c7666ca81 | absent | 74 |
| R07 | Debug line after the delivery SDK call (Principle VII) | src/operations/exporting/export/org_webhook_deliveries_exporter.py | main | 1dbd5f42cc5ff7c0292e4e37d367763c7666ca81 | absent | 137 |
| R08 | `deliveries()` holds 25 lines or fewer (32 lines, 119 to 150) | src/operations/exporting/export/org_webhook_deliveries_exporter.py | main | 1dbd5f42cc5ff7c0292e4e37d367763c7666ca81 | absent | 119 |
| R09 | Class `TestWebhookInitialResponse` exists | tests/unit/export/test_org_webhook_deliveries_exporter.py | main | be22af8ff449dec526ef20a2aa4adcab319afe97 | present | 298 |
| R10 | Rejection test covers 23 HTTP status values for both calls | tests/unit/export/test_org_webhook_deliveries_exporter.py | main | be22af8ff449dec526ef20a2aa4adcab319afe97 | present | 329 |
| R11 | Valid-empty test covers statuses 200, 201, 204, and 299 | tests/unit/export/test_org_webhook_deliveries_exporter.py | main | be22af8ff449dec526ef20a2aa4adcab319afe97 | present | 355 |
| R12 | Absent-status test rejects a response without the attribute | tests/unit/export/test_org_webhook_deliveries_exporter.py | main | be22af8ff449dec526ef20a2aa4adcab319afe97 | present | 379 |
| R13 | Native selection and delivery test keeps the writer result | tests/unit/export/test_org_webhook_deliveries_exporter.py | main | be22af8ff449dec526ef20a2aa4adcab319afe97 | present | 393 |
| R14 | Test module holds five top-level children or fewer | tests/unit/export/test_org_webhook_deliveries_exporter.py | main | be22af8ff449dec526ef20a2aa4adcab319afe97 | absent | 51 |
| R15 | Native HTTP 403 refusal test exists | tests/integration/export/test_org_webhook_native_refusals.py | main | cfa6b9ee3fe8c39e94e7500ae6f4cb2f5f16d120 | present | 21 |
| R16 | Native HTTP 503 refusal test exists | tests/integration/export/test_org_webhook_native_refusals.py | main | cfa6b9ee3fe8c39e94e7500ae6f4cb2f5f16d120 | present | 69 |
| R17 | Status-200 list double in the stable-selection module | tests/unit/export/test_issue_3188_webhook_id_selection.py | main | e229ad21d0cfde2850e85e91dca8b58d591a9a61 | present | 79 |
| R18 | Stable-selection test exists | tests/unit/export/test_issue_3188_webhook_id_selection.py | main | e229ad21d0cfde2850e85e91dca8b58d591a9a61 | present | 115 |
| R19 | Class `TestStableWebhookResolver` holds five methods or fewer | tests/unit/export/test_issue_3188_webhook_id_selection.py | main | e229ad21d0cfde2850e85e91dca8b58d591a9a61 | absent | 30 |
| R20 | Release-note fragment has one Fixed bullet that names issue 4718 | changelog.d/issue-4718-webhook-response-status.md | main | d325ad73afd4c6a3243c84f468a1a6f35d035efe | present | 3 |
| R21 | Changelog rule keeps the first file name after the pull request opens | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 32 |
| R22 | Browser double returns HTTP status 200 | tests/e2e/web_portal/test_issue_3188_webhook_control.py | main | 523c0d8de6d2e02b8265fbe45dd3bc0f23fc9ed7 | present | 38 |
| R23 | Browser stable-identifier test exists | tests/e2e/web_portal/test_issue_3188_webhook_control.py | main | 523c0d8de6d2e02b8265fbe45dd3bc0f23fc9ed7 | present | 104 |
| R24 | Portal treats a missing HTTP status as 200 | web_portal/routes/settings.py | main | 3d1e7c419ea292b393a1623a6bdac6cce1055cbe | present | 46 |
| R25 | Portal rejects only HTTP status 400 and above | web_portal/routes/settings.py | main | 3d1e7c419ea292b393a1623a6bdac6cce1055cbe | present | 47 |
| R26 | Menu 256 handler binds to `deliveries()` | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4982 |
| R27 | Primary key strategy for `searchOrgWebhooksDeliveries` | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 1612 |
| R28 | Menu 45 passes `listOrgWebhooks` to the generic export path | src/operations/exporting/export/org_config_exporter.py | main | 31de081c1be7f5a20362a8ccb23dc15fd853606c | present | 48 |
| R29 | Shared helper treats a missing HTTP status as success | src/operations/exporting/export/http_response_status.py | main | 7d511edd6de3a909093e685deed1a9d0b3b7e648 | present | 17 |
| R30 | Precedent validator rejects statuses outside 200 to 299 | src/operations/exporting/export/org_inventory_search_exporter.py | main | 49afaf076e37868a476ec6a3e3a9cc40df1442bf | present | 89 |
| R31 | Sibling exporter defaults a missing HTTP status to 200 | src/operations/exporting/export/site_webhook_deliveries_exporter.py | main | 25d4fc1e3e07f4d0399ed8f85aa853d8bad83aad | present | 40 |
| R32 | Sibling helper defaults a missing HTTP status to 200 | src/operations/exporting/export/org_export_utils.py | main | cfe85d09447ec3be6271f2a4cb8e5ea2dac5fb81 | present | 35 |
| R33 | AGENTS.md defines the inline comment rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| R34 | Repository states Python 3.15 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 18 |
| R35 | Repository holds the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R36 | Repository holds the pull request title rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 501 |
| R37 | Constitution Principle I (five-item rule) | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R38 | Constitution Principle VI (inline comments) | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R39 | Constitution Principle VII (action logging) | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R40 | CI sets `MYPY_PATHS` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R41 | CI sets `VULTURE_PATHS` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R42 | CI sets `PYDOCSTYLE_PATHS` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R43 | CI sets `INTERROGATE_PATHS` | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R44 | Spec route width is eight segments by default | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| R45 | Numeric route uses the default width | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 49 |
| R46 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R47 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R48 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R49 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R50 | Architecture page holds the directory layout section | documentation/architecture.md | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 160 |
| R51 | Development setup page exists | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 0 |
| R52 | Container page holds the test and debug container section | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| R53 | Operator guide holds no webhook behavior text | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| R54 | README holds no webhook behavior text | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| R55 | Coverage page lists `searchOrgWebhooksDeliveries` | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1002 |
| R56 | Missing-endpoint page lists `listOrgWebhooks` as missing | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | stale | 947 |
| R57 | OpenAPI defines the `listOrgWebhooks` path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 23864 |
| R58 | OpenAPI defines the `searchOrgWebhooksDeliveries` path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 24059 |
| R59 | Quality gates page lists the test quality gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 63 |
| R60 | Legacy record `spec.md` exists | specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/spec.md | main | e3703c2976733d6f848c61dabff8cef7bc0a43f6 | present | 0 |
| R61 | Legacy record `plan.md` exists | specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/plan.md | main | 9b9bf7f6034dfd366c1c9b87e1afce9bd0bc0e31 | present | 0 |
| R62 | Legacy record `tasks.md` exists | specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/tasks.md | main | fa09ecf5d35a6f8e7c0d724afef068fa18786700 | present | 0 |
| R63 | Legacy record `analysis.md` exists | specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/analysis.md | main | e89d17d1794f8c5c4911b430029cfa4e9269e610 | present | 0 |
| R64 | Legacy record `design/research.md` exists | specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/design/research.md | main | 81831456fc34356f11c25447c54ed796f6d7d47a | present | 0 |
| R65 | Legacy record `design/data-model.md` exists | specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/design/data-model.md | main | a812a1f90384bab4ef79d73b9c0c1292900912a1 | present | 0 |
| R66 | Legacy record `design/quickstart.md` exists | specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/design/quickstart.md | main | a4a002289b20743e18d63e7e5f39ddcf9e727e7d | present | 0 |
| R67 | Legacy record `design/checklists/requirements.md` exists | specs/numbered/0/0/1/2/2/3/3/3/4718-webhook-response-status/design/checklists/requirements.md | main | 2b92339e347a79530b21c255abc933de96659ea7 | present | 0 |
| R68 | Related record for issue 4715 exists | specs/numbered/0/0/1/2/2/3/3/0/4715-webhook-write-status/spec.md | main | 390443b970d0d5cd8bc273f00b89c8c5a9eed749 | present | 0 |
| R69 | Reference record 4920 `spec.md` exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R70 | Reference record 4920 `tasks.md` exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| R71 | Commit 3964d21d is an ancestor of `main` | commit 3964d21d03f9f5717cb8eafb7272ecff21f5362a | main | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 0 |
| R72 | Commit 520da641 is not an ancestor of `main` | commit 520da64195d90c54d5160bae0b7c0422d1dc9cf3 | main | 520da64195d90c54d5160bae0b7c0422d1dc9cf3 | partial | 0 |
| R73 | Commit 9662426f is not an ancestor of `main` | commit 9662426f1da95939badabc5222a660655ad6d4b4 | main | 9662426f1da95939badabc5222a660655ad6d4b4 | partial | 0 |
| R74 | Commit b1307510 is on `main`, and its 38 check runs succeeded | commit b1307510ca81d2889d660dfd1714b167d7791c59 | main | b1307510ca81d2889d660dfd1714b167d7791c59 | present | 0 |
| R75 | Commit a3e8a2e7 is on `main` (PR #4849 merge) | commit a3e8a2e7267f9de51fdcffe852bc672cb023ed83 | main | a3e8a2e7267f9de51fdcffe852bc672cb023ed83 | present | 0 |
| R76 | SDK defines `listOrgWebhooks` | .venv\Lib\site-packages\mistapi\api\v1\orgs\webhooks.py | local .venv | c31e78181aceb9d722e4ddf76cf9330fb670cd2b | present | 17 |
| R77 | SDK defines `searchOrgWebhooksDeliveries` | .venv\Lib\site-packages\mistapi\api\v1\orgs\webhooks.py | local .venv | c31e78181aceb9d722e4ddf76cf9330fb670cd2b | present | 255 |
| R78 | `APIResponse.data` defaults to an empty dictionary | .venv\Lib\site-packages\mistapi\__api_response.py | local .venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 39 |
| R79 | `APIResponse.status_code` is None until a response exists | .venv\Lib\site-packages\mistapi\__api_response.py | local .venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 43 |
| R80 | SDK defines `get_all` | .venv\Lib\site-packages\mistapi\__pagination.py | local .venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 39 |
| R81 | `get_all` returns the empty list for a dictionary without results | .venv\Lib\site-packages\mistapi\__pagination.py | local .venv | 795dd0400f9db69d1ee67aa96e3ddfca405e6f1a | present | 74 |
| R82 | Installed SDK version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local .venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |
| R83 | Changelog guard test exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| R84 | Changelog five-rule list excludes internal-only changes (rule 4) | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 53 |
| R85 | Exporter reads the stable webhook identifier from the `id` field | src/operations/exporting/export/org_webhook_deliveries_exporter.py | main | 1dbd5f42cc5ff7c0292e4e37d367763c7666ca81 | present | 38 |
| R86 | Autouse fixture `block_network` blocks socket, DNS, and SQLite connect calls | tests/unit/export/test_org_webhook_deliveries_exporter.py | main | be22af8ff449dec526ef20a2aa4adcab319afe97 | present | 28 |
| R87 | Repository overview names Windows 11, macOS, and Linux as the platforms | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 8 |

Totals: 87 rows. Present 76. Absent 8. Partial 2. Stale 1.

## Local Verification

- The 44 repository paths in the table have local copies equal to their `main` blob SHAs. The check ran with `git hash-object` and no write.
- The guard test (R83) exists on `main` only. The record does not cite a local line for it.
- The SDK files are present under `.venv`. Their git hashes are in rows R76 to R82.
- The check for the legacy session files found no repository path that matches `issue4718`, `export_candidate`, or `offline_checks`.

## Sources

- Issue #4718, read with `gh issue view`: https://github.com/jmorrison-juniper/MistHelper/issues/4718. The body, three owner comments, and labels were read.
- PR #4852 with `gh pr view` and `gh pr diff`: https://github.com/jmorrison-juniper/MistHelper/pull/4852. The state, merge commit, file list, body, check rollup, and exporter diff were read.
- PR #4849 with `gh pr view`: https://github.com/jmorrison-juniper/MistHelper/pull/4849.
- Issues #4715, #3745, and #3188, read with `gh issue view`. Each is closed.
- GitHub trees and contents for `main`, read with `gh api`.
- Local repository files named in the table, read as views and searches.
- Pinned SDK `mistapi` 0.64.1 under `.venv\Lib\site-packages\mistapi`, read as views.
- Mist REST contract: `documentation\mist-api-openapi31yaml.yaml`, read at the listed lines.
- URL fetches: none. The local and remote sources answered each question.
- Skills: none loaded. The behavior comes from the Mist REST contract and the SDK source. The listed skills cover Podman and Juniper device behavior, which this issue does not involve.

## Unverified

- U-1: Local gate results, including ruff, black, mypy, pylint, vulture, pydocstyle, interrogate, bandit, radon, symbol-diff, and the test-quality ratchet. Reason: rule 2 of the brief forbids running them. T-LOCAL-GATES runs them.
- U-2: The menu 45 generic export path that receives `listOrgWebhooks` (R28). Reason: the review did not trace the generic handler.
- U-3: A full census of exporters that default a missing HTTP status to 200. Reason: a local search found at least 13 modules with the pattern, but its output stopped at 40 matching lines. Remote evidence covers R31 and R32 only.
- U-4: The image revision label that CI publishes for the merge commit. Reason: the image registry was not queried. Principle IV steps 10 to 12 depend on it.
- U-5: Legacy claim that the test-quality analyzer, the coverage run, and the full test run passed (legacy `analysis.md`, Verification). Reason: no local run exists in this session.
- U-6: Legacy claim that the local interpreter is Python 3.14 (legacy `plan.md`, Technical Context). Reason: the environment was not inspected.
- U-7: Local gate claims in the PR #4852 body. The CI rollup is verified (R74). The local claims are not.
