# Research: Site Request Admission by Organization

**Issue**: #4921, Runtime: shared request admission rejects a site request when the ledger holds no organization.

**Record**: `specs\numbered\0\0\1\2\4\1\4\1\4921-site-request-admission`

**Truth source**: GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, read with `gh api` on 2026-11-26.

## 1. Scope and Method

1. The full `main` tree was fetched once. It holds 11404 entries, and the response was not truncated.
2. Each cited file body was decoded from base64. The line numbers in section 3 come from the decoded text.
3. The local clone sits at the same commit. A file that the five-file local diff does not name equals its `main` blob.
4. Five files differ between the local working copy and `HEAD`. Section 4 lists them. This design does not use them.
5. The Mist API claims cite the local OpenAPI file. Its remote blob matches row R57 to R63.
6. The SDK claims cite the installed `mistapi` 0.64.1 source. The installed version is in row R20 and section 5.
7. The git history checks used read-only commands only: `log -S`, `show --stat`, `rev-parse`, `hash-object` without `-w`, and `diff --name-only`.
8. Issue facts from `gh issue view 4921`: state open, created and updated 2026-11-25, author `jmorrison-juniper`, labels `bug` and `MistHelper.py`, no comments. The body names the ledger, the binding, and the three failing reads. It also links issue 4713.
9. Linked pull request: PR 4924, head `feat/4920-ex-hardware-inventory-csv`, merged at 2026-11-26T00:30:01Z, merge commit `4e81b2a4a` (R67). The pull request closes issue 4920 (R68). The commit adds `AdmissionBinding`. Its `git show --stat` output names no change to the four admission files.

## 2. Decisions

### D-1. Attribution order for a site request

- **Chosen**: Resolve the organization in this order. First, the site organization map. Second, the ledger organization. Third, the session organization. If none applies, fail closed.
- **Alternatives**:
  - (a) Use the session organization only.
  - (b) Use a per-thread organization scope with a context variable. This direction exists only in the local working copy (section 4).
  - (c) Look up each unknown site with `getSiteInfo` inside admission.
  - (d) Count unknown sites under the credential key only.
- **Reason**: Option (a) attributes wrongly when one process reads several organizations. Option (b) does not reach worker threads without a scope in each caller, and it is not on `main`. Option (c) adds a Mist request for each unknown site and re-enters admission. Option (d) removes the tenant attribution that the fail-closed test at R51 pins.
- **Risk**: Caution: a site that no listing returned falls back to the session organization. A wrong fallback counts the request against another organization quota key. The learned mapping runs first, and the fallback writes a debug record.

### D-2. Trigger for learning organization membership

- **Chosen**: Learn only from a successful (HTTP 200) GET response to `/api/v1/orgs/{org_id}/sites`, with exactly six path segments and a JSON list body.
- **Alternatives**:
  - (a) Learn from every organization-level response that carries a site identifier.
  - (b) Require each caller to register its sites.
- **Reason**: The listing schema is known (R57, R63). The record shapes of other endpoints are not verified. A caller registration is the workaround that this change removes.
- **Risk**: A site that appears only in other endpoints stays unknown until the session fallback applies.

### D-3. Map bound and eviction

- **Chosen**: Bound the map at 50,000 entries. Evict the oldest entry first.
- **Alternatives**: An unbounded map. An update of recency on each read.
- **Reason**: An unbounded map grows with each listed site in a long multi-organization run. A recency update on each read adds a lock write to each request and gives no quota benefit.
- **Risk**: An evicted site falls back to the session organization.

### D-4. Source of the session organization

- **Chosen**: Pass `ConfigUtils.get_cached_org_id` into the request ledger at connect time (R31).
- **Alternatives**:
  - (a) `ConfigUtils.get_cached_or_prompted_org_id`. This path can prompt and can exit the process.
  - (b) Read the `.env` file directly.
  - (c) Keep the per-run caller binding (`AdmissionBinding`).
- **Reason**: The cached getter returns without a prompt (R31). A prompt inside a transport thread is unsafe. A second resolver duplicates the precedence rules.
- **Risk**: In an MSP session, the cached organization is the home organization. The fallback can name the wrong organization for a site that no listing returned.

### D-5. Removal of `AdmissionBinding`

- **Chosen**: Delete the class, its import, and its two call sites. Keep `SdkErrorMute` in the same module (R35).
- **Alternatives**: Keep the class as a no-op. Keep the class and repair only the ledger.
- **Reason**: `AGENTS.md` forbids a compatibility shim. The class writes shared ledger state for each run. Two overlapping runs for different organizations can overwrite that state.
- **Risk**: The symbol gate reports one removal, and that removal is intended. The pull request body must record it.

### D-6. Refusal text

- **Chosen**: Keep the refusal text `Site API request admission requires a selected organization.` unchanged (R28).
- **Alternatives**: A new text that names the remedy.
- **Reason**: The existing test matches the word `organization` (R51). The operator text stays stable.
- **Risk**: The text does not name the remedy. The refusal now occurs only when no organization is known.

### D-7. Scope of affected readers

- **Chosen**: All site paths pass through the new rule. This includes the subscription-expiry virtual-chassis read (R48) and the dispatch status check (R42).
- **Alternatives**: Limit the change to the batch path of menu 309.
- **Reason**: The issue title and its failing list cover each site read. R48 is a site read that uses the same ledger.
- **Risk**: Site reads that now succeed count against the organization key. This result is intended.

### D-8. Learning failure behavior

- **Chosen**: Learning never raises. A response that is not HTTP 200, not JSON, or not a list gives no mapping, and it writes a debug record.
- **Alternatives**: Raise on a malformed listing.
- **Reason**: A successful Mist read must not fail because the admission side effect fails.
- **Risk**: A malformed listing gives no mapping, so the fallback applies.

### D-9. Mist requests and transport

- **Chosen**: Add no Mist request and no direct HTTP call. Learning observes the response of an existing mistapi call (R28 and R57).
- **Alternatives**: An explicit lookup request for each site.
- **Reason**: The constitution names mistapi as the sole interface to the Mist REST API (R06, line 279). A new request also adds load to a shared quota.
- **Risk**: None new.

### D-10. Concurrency primitive

- **Chosen**: One `threading.Lock` guards the ordered map for reads and writes.
- **Alternatives**: A lock-free dictionary. A concurrent collection from a third-party package.
- **Reason**: An ordered map needs one lock to evict safely. The standard library provides the lock, so no dependency change is needed.
- **Risk**: Reads wait for a writer. The writer holds the lock for one page of records only.

### Human decisions

None. Each decision above is technical. No decision concerns licensing, legal text, destruction of production data, credential policy, or product priority.

## 3. Remote Verification

Each row records one check against `main`. The table holds 72 rows. The `remote_checks` array in `4921-STATUS.json` holds the same 72 rows.

| Row | Claim | Path | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- |
| R01 | Writing style section of the generic rules | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R02 | Local gates table of the repository rules | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R03 | Symbols gate row, `symbol-diff --base <base> <file>` | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 73 |
| R04 | States mistapi floor `>=0.64.0`, which conflicts with R22 | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 21 |
| R05 | Technology and compatibility section | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |
| R06 | States mistapi `0.59+`, which conflicts with R22 | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 279 |
| R07 | Spec template exists | .specify/templates/spec-template.md | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R08 | Plan template exists | .specify/templates/plan-template.md | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R09 | Tasks template exists | .specify/templates/tasks-template.md | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R10 | Checklist template exists | .specify/templates/checklist-template.md | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R11 | Base-5 route function with base 5 | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R12 | Fragment names for pull request and issue | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| R13 | Managed root `numbered` in the process baseline | tests/guardrails/process_folder_baseline.json | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 7 |
| R14 | Process folder guard test exists | tests/guardrails/test_process_folder_structure.py | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| R15 | Changelog fragment policy test exists | tests/guardrails/test_changelog_fragment_policy.py | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| R16 | Mypy paths variable | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R17 | Vulture paths variable | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R18 | Pydocstyle paths variable | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R19 | Interrogate paths variable | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R20 | Requirements pin `mistapi==0.64.1` | requirements.txt | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R21 | Python requirement `>=3.15` | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R22 | Dependency floor `mistapi>=0.64.1,<0.65` | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| R23 | Class `RequestLedger` | src/interfaces/wan_performance/collection/request_admission.py | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 21 |
| R24 | `connect` takes an optional organization and no other input | src/interfaces/wan_performance/collection/request_admission.py | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 56 |
| R25 | `admit` resolves the organization through `_organization` | src/interfaces/wan_performance/collection/request_admission.py | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 83 |
| R26 | Fail-closed refusal for a site request with no organization | src/interfaces/wan_performance/collection/request_admission.py | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 108 |
| R27 | `AdmittedAdapter.send` admits each request before transport | src/interfaces/wan_performance/collection/request_admission.py | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 131 |
| R28 | `send` refuses HTTP 429 at line 139 and returns the response at line 142 | src/interfaces/wan_performance/collection/request_admission.py | a6064e8fadce930813f8404f85d6b0b830c68cb6 | present | 142 |
| R29 | Session setup connects the ledger without an organization | src/foundation/support/refactors/initialize_mist_session.py | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 74 |
| R30 | `_build_timeout_adapter` checks `RequestLedger.enabled` and builds the admission adapter | src/foundation/support/refactors/initialize_mist_session.py | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 72 |
| R31 | `get_cached_org_id` returns the cached organization without a prompt | src/foundation/runtime/config/config_utils.py | b63d83c1cfad322df7442a2241d8e614c1d6fdfa | present | 114 |
| R32 | Class `AdmissionBinding` | src/operations/exporting/ex_hardware_inventory/scope/session.py | 225a80511a3248a8c0138d67e002e8fe62eda62c | present | 25 |
| R33 | Binding writes the ledger organization on enter | src/operations/exporting/ex_hardware_inventory/scope/session.py | 225a80511a3248a8c0138d67e002e8fe62eda62c | present | 50 |
| R34 | Binding restores the earlier ledger organization on exit | src/operations/exporting/ex_hardware_inventory/scope/session.py | 225a80511a3248a8c0138d67e002e8fe62eda62c | present | 57 |
| R35 | Class `SdkErrorMute` in the same module | src/operations/exporting/ex_hardware_inventory/scope/session.py | 225a80511a3248a8c0138d67e002e8fe62eda62c | present | 77 |
| R36 | Module docstring names issue 4921 as the tracker | src/operations/exporting/ex_hardware_inventory/scope/session.py | 225a80511a3248a8c0138d67e002e8fe62eda62c | present | 7 |
| R37 | Batch module imports `AdmissionBinding` | src/operations/exporting/ex_hardware_inventory/run/batch.py | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 38 |
| R38 | Preview wraps its service call with `AdmissionBinding` | src/operations/exporting/ex_hardware_inventory/run/batch.py | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 199 |
| R39 | Run wraps the batch with `AdmissionBinding` | src/operations/exporting/ex_hardware_inventory/run/batch.py | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 223 |
| R40 | Stack receives the organization of each run | src/operations/exporting/ex_hardware_inventory/operation.py | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 72 |
| R41 | Site-scoped targets read the organization sites before any site resource | src/mist/realtime/websocket_streams/web/services/pickers/related.py | 934399eb302b2fdc007a9afc986cdced20f9bf83 | present | 160 |
| R42 | Dispatch status check reads device statuses without its own listing | src/mist/realtime/websocket_streams/web/services/pickers/related.py | 934399eb302b2fdc007a9afc986cdced20f9bf83 | present | 82 |
| R43 | Organization site list calls `listOrgSites` | src/mist/realtime/websocket_streams/intake/pickers/resources.py | 6b65137fea554d1da3ce67dd19463a0a14d0b969 | present | 77 |
| R44 | Device status calls `listSiteDevicesStats` | src/mist/realtime/websocket_streams/intake/pickers/devices.py | 8e5cb175277d13372e5cd531e43326364f44fe72 | present | 43 |
| R45 | Device list calls `listSiteDevices` | src/mist/realtime/websocket_streams/intake/pickers/devices.py | 8e5cb175277d13372e5cd531e43326364f44fe72 | present | 102 |
| R46 | Shell trigger path built per device | src/mist/realtime/websocket_streams/live/runners/utility/triggers/table.py | 9a7b201ef99060dee0c6cc70611bff18f1dafcd6 | present | 103 |
| R47 | Shell trigger posted through the session | src/mist/realtime/websocket_streams/live/runners/shell/lifecycle/opening.py | a5f80e0b1f28d0bad7b3767259864c0d3af43e08 | present | 57 |
| R48 | Virtual-chassis read calls `getSiteDeviceVirtualChassis` | src/mist/intelligence/reports/subscription_expiry/client.py | 980b332e7f8be83e4f495cf86913ba3c1b84ac5c | present | 507 |
| R49 | MSP profile calls `getSelf`, a path with no site or organization | src/operations/exporting/ex_hardware_inventory/scope/profile.py | fb745bedeac7e0e955f80256f2affd43f72ef7c6 | present | 97 |
| R50 | Class `TestRequestAdmission` | tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | 2aafadca588ab0a14385e9b3c53fb7fe68c31201 | present | 28 |
| R51 | Fail-closed test for an unscoped site request | tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | 2aafadca588ab0a14385e9b3c53fb7fe68c31201 | present | 95 |
| R52 | Adapter test patches `connect` with one keyword | tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | 2aafadca588ab0a14385e9b3c53fb7fe68c31201 | present | 120 |
| R53 | Hardware session test imports `AdmissionBinding` | tests/unit/ex_hardware_inventory/scope/test_hardware_session.py | 90cfbd8744f295db6731d550138b07eea30c3b04 | present | 15 |
| R54 | Class `TestAdmissionBinding` | tests/unit/ex_hardware_inventory/scope/test_hardware_session.py | 90cfbd8744f295db6731d550138b07eea30c3b04 | present | 28 |
| R55 | Class `TestSdkErrorMute` | tests/unit/ex_hardware_inventory/scope/test_hardware_session.py | 90cfbd8744f295db6731d550138b07eea30c3b04 | present | 88 |
| R56 | Hardware CLI flow integration test exists | tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py | 45d5e244020455a9c8876841f807d28481482106 | present | 0 |
| R57 | Operation `listOrgSites` for GET `/api/v1/orgs/{org_id}/sites` | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20022 |
| R58 | Operation `getSiteInfo` for GET `/api/v1/sites/{site_id}` | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25978 |
| R59 | Operation `listSiteDevices` | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 27877 |
| R60 | Operation `createSiteDeviceShellSession` for POST shell | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 30503 |
| R61 | Operation `listSiteDevicesStats` | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 39555 |
| R62 | Site schema property `org_id` | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 100566 |
| R63 | Sites schema is an array of site records | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 102626 |
| R64 | Reference record for issue 4920 exists | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R65 | Route folder for issue 4921 is absent | specs/numbered/0/0/1/2/4/1/4/1 | none | absent | 0 |
| R66 | No path with 4921 under specs | specs (tree search for 4921) | none | absent | 0 |
| R67 | Pull request 4924 merged, and merge commit 4e81b2a4a holds the workaround | pull request 4924 | none | present | 0 |
| R68 | Issue 4920 closed | issue 4920 | none | present | 0 |
| R69 | Issue 4713 open and related by subject | issue 4713 | none | present | 0 |
| R70 | Main commit used for this record | commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca | none | present | 0 |
| R71 | Subscription-expiry client test exists | tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py | fec6907fa47190960c5870f0d5093b301bec6566 | present | 0 |
| R72 | Hardware preview falls back to the picker sites reader, which calls listOrgSites | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 345 |

Result counts: 68 present, 2 stale (R04, R06), 2 absent (R65, R66), 0 partial.

## 4. Local-Only Evidence (Not on Main)

The local working copy differs from `HEAD` in five files. `git diff --name-only HEAD` names them. The stat line from `git diff --stat` gives the size of each change. None of these edits is on `main`, and this design does not depend on them.

| File | Local state | Note |
| --- | --- | --- |
| src/interfaces/wan_performance/collection/request_admission.py | Uncommitted | Adds a context-variable scope (`organization_scope`) and a credential helper. |
| src/mist/intelligence/reports/subscription_expiry/client.py | Uncommitted | Imports `organization_scope` and wraps the virtual-chassis read in it. |
| tests/unit/marvis/mist/intelligence/reports/audits/credentials/subscription_expiry/test_client.py | Uncommitted | Adds one virtual-chassis admission test. |
| tests/unit/wan_dashboard/wan_performance/collection/test_request_admission.py | Uncommitted | Adds scope tests and a frame-locals test. |
| src/foundation/support/utils/logger_utils.py | Uncommitted | Unrelated to this issue. |

The stat line for the five files reads 245 insertions and 13 deletions.

Git history checks:

- `git log -S organization_scope -- src/interfaces/wan_performance/collection/request_admission.py` returns no commit. The scope never reached that file on `main`.
- `git show --stat 4e81b2a4a` for the four admission files returns no change. PR 4924 did not touch them.
- The working-copy edits belong to another change. The implementation branch must start from `main`. Caution: staging the five files in the pull request mixes two changes and breaks review.

## 5. Sources

Local paths. Line numbers come from the same file body as the remote decode, or from the installed SDK.

- `AGENTS.md`: writing style, safety, and Git flow rules (R01).
- `.github/copilot-instructions.md`: local gates table (R02), symbols gate (R03), pin statement (R04), and container and port rules.
- `.specify/memory/constitution.md`: Principles I to VII, the technology constraints (R05), and the mistapi statement (R06).
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`: headings used for this record (R07 to R10).
- `.specify/scripts/powershell/spec-route.ps1`: base-5 route function (R11). Digits of 4921 in base 5 are 1, 2, 4, 1, 4, 1. Padded to eight levels, they match the route in the issue.
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`: reference record shape (R64). Its file list is `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design\`.
- `documentation\mist-api-openapi31yaml.yaml`: listed operations and schema lines (R57 to R63).
- `documentation\MIST_API_GET_ENDPOINTS.md` lines 867, 1078, 1199, and 1550: coverage rows for `listOrgSites`, `getSiteInfo`, `listSiteDevices`, and `listSiteDevicesStats`. The file equals its `main` blob.
- `documentation\MIST_API_MISSING_ENDPOINTS.md`: no row names the shell endpoint. The endpoint is covered by mistapi, so it is not missing.
- `documentation\architecture.md`, `documentation\operator-guide.md`, `documentation\development-setup.md`, `documentation\quality-gates.md`, and `documentation\container-deployment.md`: searched for admission, request ledger, and organization-scope terms. No match names the admission design. The files name Redis as a store only, and `container-deployment.md` names the Redis service at lines 26 and 37. The code docstrings are the design record.
- `documentation\cross-org-subscription-stock.md` line 81: the standalone flag disables Redis and shared API request admission.
- `.venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py`: `listOrgSites` at line 17, URI at line 48.
- `.venv\Lib\site-packages\mistapi\api\v1\sites\sites.py`: `getSiteInfo` at line 17, URI at line 36.
- `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py`: `listSiteDevices` at line 17, URI at line 54. `createSiteDeviceShellSession` at line 2775, URI at line 2802. `getSiteDeviceVirtualChassis` at line 3529, URI at line 3551.
- `.venv\Lib\site-packages\mistapi\api\v1\sites\stats.py`: `listSiteDevicesStats` at line 1051, URI at line 1088.
- `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` line 3: installed version 0.64.1.

## 6. Skills

No skill was loaded. The issue concerns the Mist request ledger and the mistapi session. It does not ask a Podman, Juniper device, or container question, so no listed skill matches.

## 7. Unverified

These claims have no verified source. The design does not rely on them, except where the note says so.

- U-1. Python thread context inheritance. The design does not depend on it, because the map is process-wide.
- U-2. Whether Mist moves a site to another organization. No local or remote source answers this question. The map keeps the first learned value until eviction or restart. This risk appears in `plan.md`.
- U-3. Whether every operator path sets the cached organization before a site read. Several menus call `get_cached_or_prompted_org_id`. The full set of paths was not traced.
- U-4. Live Mist responses. No token was used. The record uses the OpenAPI schema only.
- U-5. Quota behavior under load. The constants and the Redis script are unchanged, and no load test was run.
- U-6. The STE score of the new Markdown files. The repository linter was not run, because the brief forbids linter runs in this task.
- U-7. Whether the subscription-expiry client test (R71) passes after the change. The test was not run.
