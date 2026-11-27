# Research: MSP Profile Lookup Failure

Each decision lists the chosen option, the alternatives, the reason, and the risk. Remote evidence comes from one `main` tree read at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The tree read is not truncated. File bodies come from `gh api` and decode in memory. Local SDK files are hashed without writing to Git.

## Decisions

### D-1 Valid profile contract

- **Decision**: A profile lookup is valid only when the status is 2xx, the body is a JSON object, and the body holds a `privileges` list. An empty list is valid.
- **Alternatives considered**:
  - Check the status only. Rejected. A 2xx body with a changed shape would pass with no grants.
  - Check the body only, for example for a `detail` key. Rejected. A proxy page with HTTP 503 and no error object would pass as no grants.
  - Treat an empty list as failed. Rejected. Organization-only accounts would fail closed on every menu 13 run.
- **Rationale**: The SDK sets `status_code` (RC-53) and keeps the JSON body in `data` (RC-54, RC-55). The OpenAPI 200 response is `admin`, which has a `privileges` property (RC-43, RC-46). The OpenAPI 403 body has a `detail` string (RC-44, RC-45).
- **Risk**: A future API change that omits `privileges` for valid accounts blocks menu 13. The warning names the cause, and the tests pin the rule.

### D-2 Lookup result and list view

- **Decision**: `lookup_msp_privileges` returns `MspPrivilegeLookup` with `succeeded` and `grants`. `detect_msp_privileges` keeps the list type. It returns the grants, or an empty list for a failed lookup.
- **Alternatives considered**:
  - Change `detect_msp_privileges` to return the lookup result. Rejected. Seven callers change, including `MistHelper.py` (RC-19 to RC-21) and the exporter (RC-14). Both have an owner in progress or a hot-file rule.
  - Raise an exception on failure. Rejected. The startup path (RC-20) would stop. Dispatch also needs a state, and an exception does not carry one into the grant list.
  - Add a module flag that the detector sets. Rejected. The detector removed its module globals in the refactor (RC-01 docstring).
- **Rationale**: The list view keeps every current caller unchanged (FR-014). The lookup result gives dispatch the distinction that FR-006 requires.
- **Risk**: A second public function can look like a wrapper, which Principle II forbids. The Complexity Tracking table in `plan.md` records the reason.

### D-3 Dispatch confirms absence with a live lookup

- **Decision**: When the grant list is empty, menu 13 makes one live lookup. It calls the single-organization callback only after a valid lookup with zero MSP grants.
- **Alternatives considered**:
  - Carry the lookup result through the `MainEntrypoint` context. Rejected. The change needs `MistHelper.py` (RC-19, RC-20) and `main_entrypoint.py` (RC-22). Both are protected paths, and the file hold is open.
  - Keep the grant list and print a warning before the single-organization callback. Rejected. The operator gets a partial inventory after a warning that the operator may skip. The issue requires that a failed lookup must not select that path.
  - Raise from the detector and catch the exception in dispatch. Rejected. Dispatch receives only the grant list, so the exception never reaches it.
- **Rationale**: The change stays in two source files. Dispatch reads the state at decision time. The facade already passes the session (RC-12).
- **Risk**: The empty-list branch makes one more API call. The branch runs only for organization-only accounts and for a failed startup lookup.

### D-4 Fail closed

- **Decision**: A failed live lookup prints `_LOOKUP_FAILED_MSG`, calls no callback, and returns. A valid live lookup with grants prints `_RESTART_FOR_GRANTS_MSG`, calls no callback, and returns.
- **Alternatives considered**:
  - Warn, then run the single-organization callback. Rejected. The issue requires that a failed lookup must not select that path. The output would look complete while it is partial.
  - Retry the live lookup in a loop. Rejected. A loop adds wait time and more API calls under a refusal.
  - Use the live grants in the same run. Rejected. The facade rebuilds the orchestrator from the context list on every call (RC-12, RC-13). The grants would be lost at the next callback.
- **Rationale**: The operator sees the cause and runs the operation again. The next run repeats the lookup.
- **Risk**: A transient outage blocks menu 13 for one run. The message tells the operator to run the operation again.

### D-5 Scope boundary

- **Decision**: Readers outside menu 13 keep their current behavior. These readers are startup, restore, login, the exporter, the firmware cache, and the org config exporter. Follow-up issues cover them (T011).
- **Alternatives considered**:
  - Fix every reader in this change. Rejected. The change would cross `MistHelper.py`, `main_entrypoint.py`, the exporter (issue #4762), and the firmware code. The issue asks for a file-scoped handoff.
  - Change only the detector warning and leave menu 13 unchanged. Rejected. Menu 13 would still select the single-organization callback after a failed lookup.
- **Rationale**: This is the smallest change that meets the issue. Each reader has its own owner or its own risk.
- **Risk**: Some operators still see "no MSP privileges" after a refused startup lookup. The detector warning and the operator guide paragraph name the cause.

### D-6 Tests model the SDK response

- **Decision**: Existing fixtures add `status_code=200`. New cases cover each status class and each body shape.
- **Alternatives considered**:
  - Keep the fixtures unchanged and mark the tests as skipped. Rejected. Skipping hides the contract.
  - Build real `APIResponse` objects. Rejected for this change. The module uses `SimpleNamespace` fakes (RC-26, RC-27), and real objects add setup without new coverage for this defect.
- **Rationale**: A fixture must describe a valid response. Otherwise the valid-path tests stop testing the contract (RC-27, RC-28).
- **Risk**: Low. The change updates five fixtures in one file.

## Linked Work

| Item | GitHub state, read 2026-11-26 | Effect on this change |
| - | - | - |
| #4713, this issue | OPEN. Last updated 2026-11-11. Two comments. | The scope. The comments name three holds: `MistHelper.py` (#4607), the orchestrator (#4708), and the exporter (#4762). |
| #4607 | MERGED on 2026-11-13. | Its `MistHelper.py` hold no longer applies. This change still leaves `MistHelper.py` unchanged. |
| PR #4358 | MERGED on 2026-11-13 at 19:33:49Z. Head branch `jmorrison-juniper-4142-test-package-deconfliction`. Its file list does not name `test_msp_privilege_detection.py`. | The rename target that the issue names is not in this PR. See Unverified item 6. |
| #4708 | OPEN. Labels `bug`, `tests`, and `in-progress`. | Owns `org_device_inventory_msp.py` and its test module. Gate T001. |
| #4762 | OPEN. Labels `bug`, `MistHelper.py`, and `in-progress`. | Owns `msp_inventory_exporter.py`. The site-lookup logging is out of scope. |
| #1794 | OPEN. Labels `refactor`, `web-portal`, and `in-progress`. | Owns the broad exception cleanup. Out of scope. |
| Record `4920-ex-hardware-inventory-csv` on `main` | Present (RC-79 to RC-84). | Its research R4 names #4713 and avoids the detector. This change does not alter that record. |
| Open pull requests | Seven open. Their file lists were scanned for MSP paths. PR #4208 touches `src/foundation/support/refactors/initialize_mist_session.py` only. | No overlap with the change map. |
| Commit `3964d21d03f9f5717cb8eafb7272ecff21f5362a` cited by the issue | An ancestor of `main`. The compare API reports `main` 88 commits ahead and 0 behind (RC-88). | The code path in the issue still exists on `main`. |

## Remote Verification

Method: one `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` call, filtered locally. Blob SHAs come from that tree. A file body came from the contents API when the file was under 1 MB. The OpenAPI file came from the Git blob API. The SDK rows use the local `.venv` path and the SHA from `git hash-object`. No file in the repository was written.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | `detect_msp_privileges` is the list entry point | `src/foundation/support/refactors/msp_privilege_detection.py` | main | 9b4ada4566ada1721a70a0a313a948bc2b05dfdd | present | 143 |
| RC-02 | The profile fetch calls `getSelf` | `src/foundation/support/refactors/msp_privilege_detection.py` | main | 9b4ada4566ada1721a70a0a313a948bc2b05dfdd | present | 131 |
| RC-03 | A falsy response returns None before any status check | `src/foundation/support/refactors/msp_privilege_detection.py` | main | 9b4ada4566ada1721a70a0a313a948bc2b05dfdd | present | 132 |
| RC-04 | A body that is a dict passes with no status check | `src/foundation/support/refactors/msp_privilege_detection.py` | main | 9b4ada4566ada1721a70a0a313a948bc2b05dfdd | present | 136 |
| RC-05 | The `privileges` value defaults to an empty list | `src/foundation/support/refactors/msp_privilege_detection.py` | main | 9b4ada4566ada1721a70a0a313a948bc2b05dfdd | present | 115 |
| RC-06 | A broad except writes through the root logger | `src/foundation/support/refactors/msp_privilege_detection.py` | main | 9b4ada4566ada1721a70a0a313a948bc2b05dfdd | present | 176 |
| RC-07 | Module global `msp_privileges` holds the grant list | `src/mist/resources/inventory/org_device_inventory_msp.py` | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 31 |
| RC-08 | Module global `apisession` holds the session | `src/mist/resources/inventory/org_device_inventory_msp.py` | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 28 |
| RC-09 | The configure function stores the grant list | `src/mist/resources/inventory/org_device_inventory_msp.py` | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 70 |
| RC-10 | Dispatch calls the single-organization callback on an empty grant list | `src/mist/resources/inventory/org_device_inventory_msp.py` | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 528 |
| RC-11 | The dispatch definition | `src/mist/resources/inventory/org_device_inventory_msp.py` | main | 36523c13a48d17580310ac4fc3d69efbe88a2dad | present | 524 |
| RC-12 | The facade passes the session and the grant list | `src/mist/resources/inventory/org_device_inventory_summary_facade.py` | main | 9f3549a47a941287968a9f9fff5cb163a62c75a9 | present | 55 |
| RC-13 | The facade dispatch delegates to the orchestrator | `src/mist/resources/inventory/org_device_inventory_summary_facade.py` | main | 9f3549a47a941287968a9f9fff5cb163a62c75a9 | present | 89 |
| RC-14 | The exporter detect call publishes the grants | `src/operations/exporting/export/msp_inventory_exporter.py` | main | 4b2aa3ab42ebac86ecdf43be224fa4df07385895 | present | 137 |
| RC-15 | The exporter site lookup logs failures at debug level | `src/operations/exporting/export/msp_inventory_exporter.py` | main | 4b2aa3ab42ebac86ecdf43be224fa4df07385895 | present | 361 |
| RC-16 | The login announce calls the injected detection callback | `src/mist/access/auth/interactive/login_orchestrator.py` | main | fd475be9467068e6c34a819697c3c46235801047 | present | 238 |
| RC-17 | The login summary prints the org-level message for an empty result | `src/mist/access/auth/interactive/login_orchestrator.py` | main | fd475be9467068e6c34a819697c3c46235801047 | present | 248 |
| RC-18 | The interactive initializer adapter calls the detector | `src/foundation/support/refactors/initialize_mist_session_interactive.py` | main | c0cea7c2cd4f88d60e7bc040f5dc90364911a45e | present | 44 |
| RC-19 | The restore path calls the detector | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2652 |
| RC-20 | The token session path publishes the grants | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7680 |
| RC-21 | `MistHelper.py` imports the detector | `MistHelper.py` | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 728 |
| RC-22 | The context field holds the grants | `src/foundation/support/refactors/main_entrypoint.py` | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 57 |
| RC-23 | The resolver maps the grants to the context | `src/foundation/runtime/config/source_dependency_resolver.py` | main | 18c0e2b88560614a4c987510032fea4946b0fc7c | present | 26 |
| RC-24 | The firmware cache holds the grants | `src/operations/execution/firmware/firmware_manager.py` | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | present | 43 |
| RC-25 | The org config exporter treats an empty grant list as no access | `src/operations/exporting/export/org_config_exporter.py` | main | 31de081c1be7f5a20362a8ccb23dc15fd853606c | present | 71 |
| RC-26 | The detector test helper stubs `getSelf` | `tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py` | main | 8a1c52109e565654f1e22a723ec056bd972ce374 | present | 134 |
| RC-27 | The profile body fixture has no status code | `tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py` | main | 8a1c52109e565654f1e22a723ec056bd972ce374 | present | 415 |
| RC-28 | The detector happy-path test | `tests/unit/config/standalone/foundation/support/registry/test_msp_privilege_detection.py` | main | 8a1c52109e565654f1e22a723ec056bd972ce374 | present | 452 |
| RC-29 | The dispatch test for an empty grant list | `tests/unit/inventory/test_org_device_inventory_msp.py` | main | 44475247c7b7182468ecad7cc69ab2fdd611a677 | present | 123 |
| RC-30 | The test helper configures the orchestrator | `tests/unit/inventory/test_org_device_inventory_msp.py` | main | 44475247c7b7182468ecad7cc69ab2fdd611a677 | present | 23 |
| RC-31 | The exporter test patches the detector | `tests/unit/export/test_msp_inventory_exporter.py` | main | 629799791fb9fd8755faa4f41329dcbf699e1266 | present | 436 |
| RC-32 | The exporter test asserts the no-grant message | `tests/unit/export/test_msp_inventory_exporter.py` | main | 629799791fb9fd8755faa4f41329dcbf699e1266 | present | 443 |
| RC-33 | The login test pins the legacy banner | `tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py` | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 604 |
| RC-34 | A guard test links an anchor in the operator guide | `tests/guardrails/test_hardware_shell_lock_docs.py` | main | 83926b3fbc870c5b69ba48dd5a0a2591ae183ed6 | present | 167 |
| RC-35 | The detection bullet in the MSP support page | `documentation/wiki/MSP-Support.md` | main | 350d19953fcee4790d7d01bca8715f22a813c4d2 | present | 116 |
| RC-36 | The no-grant paragraph in the operator guide | `documentation/operator-guide.md` | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 593 |
| RC-37 | The architecture table row names the orchestrator | `documentation/architecture.md` | main | b4cab54be36d223b7eba879ca99b838f508938ce | present | 285 |
| RC-38 | The menu API page maps `getSelf` to the detector | `documentation/menu-api/interactive.md` | main | ec5402f333e691cb9a490177932603df1b38bc7d | present | 461 |
| RC-39 | The endpoint catalog maps `getSelf` | `documentation/MIST_API_GET_ENDPOINTS.md` | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1045 |
| RC-40 | The bootstrap command for a new worktree | `documentation/development-setup.md` | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 32 |
| RC-41 | The test and debug containers section | `documentation/container-deployment.md` | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| RC-42 | The OpenAPI path `/api/v1/self` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25460 |
| RC-43 | The OpenAPI `getSelf` operation | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25490 |
| RC-44 | The OpenAPI `getSelf` maps status 403 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25498 |
| RC-45 | The OpenAPI 403 body has a `detail` string | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 94788 |
| RC-46 | The OpenAPI admin schema has a `privileges` property | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 67996 |
| RC-47 | The OpenAPI admin privileges list declares `minItems: 1` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68278 |
| RC-48 | The OpenAPI admin privilege has `msp_id` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68143 |
| RC-49 | The OpenAPI admin privilege has `msp_name` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68150 |
| RC-50 | The OpenAPI admin privilege has `role` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 68175 |
| RC-51 | The SDK `getSelf` definition | `.venv\Lib\site-packages\mistapi\api\v1\self\self.py` | local .venv | 9a1c323fb1045478d923ebcb30436655c851a6e2 | present | 17 |
| RC-52 | The SDK `getSelf` path and GET call | `.venv\Lib\site-packages\mistapi\api\v1\self\self.py` | local .venv | 9a1c323fb1045478d923ebcb30436655c851a6e2 | present | 32 |
| RC-53 | The SDK response sets the status code | `.venv\Lib\site-packages\mistapi\__api_response.py` | local .venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 48 |
| RC-54 | The SDK response data defaults to an empty dict | `.venv\Lib\site-packages\mistapi\__api_response.py` | local .venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 39 |
| RC-55 | The SDK response data comes from the JSON body | `.venv\Lib\site-packages\mistapi\__api_response.py` | local .venv | 2d878d79295fec79e6409f6243132c53280f15ab | present | 57 |
| RC-56 | The installed SDK version is 0.64.1 | `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` | local .venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |
| RC-57 | The writing style section of the shared rules | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-58 | The tests rule of the shared rules | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 133 |
| RC-59 | The secrets section of the shared rules | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 172 |
| RC-60 | The local gates table | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-61 | The numeric route rule | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 160 |
| RC-62 | Menu 13 belongs to the safe category | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 220 |
| RC-63 | The mistapi pin | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| RC-64 | The constitution secrets rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 134 |
| RC-65 | The constitution action logging rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| RC-66 | The constitution hot-file rule for `MistHelper.py` | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 506 |
| RC-67 | The spec template | `.specify/templates/spec-template.md` | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RC-68 | The plan template | `.specify/templates/plan-template.md` | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RC-69 | The tasks template | `.specify/templates/tasks-template.md` | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RC-70 | The checklist template | `.specify/templates/checklist-template.md` | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RC-71 | The route script default width is 8 | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-72 | The changelog naming rule | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| RC-73 | CI `MYPY_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-74 | CI `VULTURE_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-75 | CI `PYDOCSTYLE_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-76 | CI `INTERROGATE_PATHS` | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-77 | CI `VULTURE_CONFIDENCE` default is 70 | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 127 |
| RC-78 | CI `INTERROGATE_THRESHOLD` default is 90 | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 123 |
| RC-79 | Reference record `spec.md` | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| RC-80 | Reference record `plan.md` | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md` | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 0 |
| RC-81 | Reference record `tasks.md` | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/tasks.md` | main | 72bd85483706269fdf809322b2dca38a0e1d5698 | present | 0 |
| RC-82 | Reference record `analysis.md` | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/analysis.md` | main | b5db89b9d0d0a4f8e725ad8e0e746c34fa1a24e7 | present | 0 |
| RC-83 | Reference record `design/research.md` | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/research.md` | main | 2e4aaa714e56fff7f96a2af9e686e9f5c06224a7 | present | 0 |
| RC-84 | Reference record checklist `requirements.md` | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/checklists/requirements.md` | main | 4a53b89939bb523902efeaaffd1d7b12221c717b | present | 0 |
| RC-85 | The route folder for 4713 exists | `specs/numbered/0/0/1/2/2/3/2/3` | main | none | absent | 0 |
| RC-86 | No folder under `specs` holds 4713 | `specs` | main | none | absent | 0 |
| RC-87 | The `main` reference commit | `commits/main` | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| RC-88 | The commit cited by the issue is an ancestor of `main` | `commits/3964d21d03f9f5717cb8eafb7272ecff21f5362a` | main | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 0 |
| RC-89 | The changelog fragment guard test | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-90 | The login session test module that pins the detector callback | `tests/unit/marvis/mist/access/auth/test_interactive_session.py` | main | 2ac64f9a8d1621a86ef32a91e1816febb63e57f4 | present | 0 |
| RC-91 | The initializer test module that stubs the detector | `tests/unit/config/foundation/support/refactors/runtime/session/test_initialize_mist_session_interactive_wave9.py` | main | ec4069c071e61c31ef3afa2f59116deae0d80d22 | present | 0 |
| RC-92 | The menu wiki generator | `scripts/generate_menu_wiki.py` | main | f959225275536743e93bc95d37cb015865a73d53 | present | 0 |
| RC-93 | The menu API map package initializer | `scripts/menu_api_map/__init__.py` | main | 3e769f0de75ee0f9e1ef2d2b2961906a56a6941c | present | 0 |
| RC-94 | The menu API map package entry point | `scripts/menu_api_map/__main__.py` | main | 19f72aa767a1821f2ccf88680b8778b89012873d | present | 0 |
| RC-95 | The project configuration for mypy and bandit | `pyproject.toml` | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 0 |
| RC-96 | The test quality analyzer configuration | `.github/test-quality-config.toml` | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| RC-97 | The test quality baseline | `.github/test-quality-baseline.json` | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| RC-98 | The single-file form of the menu API map is absent, so the package form applies | `scripts/menu_api_map.py` | main | none | absent | 0 |

Remote checks: 98 rows. Each row matches one entry in `remote_checks` of the STATUS file.

## Sources

- Shared rules: `AGENTS.md` (RC-57 to RC-59). Repository rules: `.github/copilot-instructions.md` (RC-60 to RC-63). Constitution: `.specify/memory/constitution.md` (RC-64 to RC-66).
- Templates: `.specify/templates/` (RC-67 to RC-70). Route script: `.specify/scripts/powershell/spec-route.ps1` (RC-71). Changelog rule: `changelog.d/README.md` (RC-72). CI variables: `.github/workflows/ci.yml` (RC-73 to RC-78).
- Reference record: `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (RC-79 to RC-84). Its shape was copied. Its content was not copied.
- Mist API: `documentation/mist-api-openapi31yaml.yaml`, read through the Git blob API (RC-42 to RC-50). The file is over 1 MB, so the contents API does not return it.
- Mist SDK: `.venv\Lib\site-packages\mistapi\` (RC-51 to RC-56). The path is local and outside the repository. The pin is `mistapi>=0.64.0,<0.65` (RC-63).
- Operator and MSP pages: `documentation/wiki/MSP-Support.md`, `documentation/operator-guide.md`, `documentation/architecture.md`, `documentation/menu-api/interactive.md`, and `documentation/MIST_API_GET_ENDPOINTS.md` (RC-35 to RC-39).
- Gate paths: the changelog guard test, the two caller test modules, the menu scripts, `pyproject.toml`, and the test-quality files (RC-89 to RC-98).
- Upstream URLs: none fetched. The local OpenAPI file and the pinned SDK answered each question.

## Skills

No skill loaded. The issue asks no Podman question and no Juniper device question. The local OpenAPI file and the pinned SDK answer the Mist API questions.

## Route Check

The record route is `specs\numbered\0\0\1\2\2\3\2\3`. Base-5 digits of 4713 are 1, 2, 2, 3, 2, 3, which is `122323`. Padded to eight digits, the result is `00122323`, which matches the route. `spec-route.ps1` uses base 5 (line 17) and a default width of 8 (line 7, RC-71). The script was not run (rule 2 of the brief).

## Unverified

1. Live Mist API responses for `getSelf` with HTTP 403 and HTTP 503. A live run breaks rule 2 of the brief. The issue used synthetic responses.
2. The body text of a proxy HTTP 503 page. Nothing observed it. The contract treats every non-JSON body as a failed lookup.
3. The output of `scripts/generate_menu_wiki.py` and `scripts/menu_api_map` after the change. Rule 2 forbids running repository scripts.
4. The wording of `symbol-diff` for added names. The tool was not run.
5. The output of the safe sweep for menu 13. Rule 2 forbids running the sweep.
6. The rename target that the issue assigns to draft #4358. PR #4358 lists no detector test file (see Linked Work). No other remote source names a target.
7. Reproduction of the issue on `main` at `f03c6c9b`. Rule 2 forbids running tests. The code path is verified by RC-02 to RC-04 and RC-10.
8. Readers outside menu 13 (RC-14 to RC-25). They were traced by search only. Nothing ran.
9. Acceptance of the proposed commit and pull request titles by the title check. The check runs in CI only.
