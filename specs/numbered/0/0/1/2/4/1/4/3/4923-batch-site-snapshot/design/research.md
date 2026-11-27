# Research: Batch target site snapshot

## 1. Method and truth order

- Truth order: GitHub `main`, read with `gh api`, outranks any local file. The table in section 3 cites the remote blob SHA for each path.
- The remote tree call read 11,404 entries from `main`. The tree was not truncated. Contents and blob calls read the line numbers.
- Nine files compared equal between the local `HEAD` blob and the remote blob: `related.py`, `resources.py`, `devices.py`, `routing.py`, `sessions.py`, `websockets.js`, `test_ws_web_services.py`, the OpenAPI file, and `spec-route.ps1`. Every local line number used in this record comes from one of these nine files or from a remote decode.
- The mistapi source is local only. The `.venv` folder is not tracked, so SDK claims cite the installed package.
- No GitHub call returned HTTP 403 or 429. No retry was needed.
- No container, build, test run, or package install ran during this research.

## 2. Issue facts and linked work

- Issue #4923 is open. It was created and last updated at 2026-11-25T01:41:27Z. Its labels are `refactor` and `web-portal`. It has no comments.
- The body has three parts. "Problem" names `BatchTargetResolver._site_rows` and `sites()`, and states N + 1 reads of the full site list. "Evidence" cites an integration test with three organizations and the 5000-request hourly limit. "Expected result" asks for one read for each preview, or a few seconds of caching, and a check of each site against that list.
- The issue has no error text. Its only reproduction detail is the three-organization integration test described in "Evidence".
- PR #4924 is merged. Its head is `feat/4920-ex-hardware-inventory-csv`, and it merged at 2026-11-26T00:30:01Z. Its body cites issue #4923 as the source of 177 requests for 15 switches. It does not close issue #4923. Its relation is "reports the defect".
- Issue #4920 is closed (2026-11-26T00:36:00Z). It is the specification for the EX hardware inventory feature. The Multi Site hardware action of that feature exposed the defect.
- Issue #4921 is open. Its title is "Runtime: shared request admission rejects a site request when the ledger holds no organization". It is not a dependency.
- Overlap check: 7 open pull requests exist. None of them changes a planned file (AGENTS.md, Parallel agents rule).
- Existing record: no folder under `specs\` starts with `4923-`. The remote path `specs/numbered/0/0/1/2/4/1/4/3/` has no entry (row 59).


## 3. Remote verification table

Ref is `main` for every row. Result values are `present`, `absent`, `partial`, or `stale`. A line of 0 means that the path alone is the evidence.

| No. | Claim | Path | Blob SHA | Result | Line |
| - | - | - | - | - | - |
| 1 | `BatchTargetPickerService` class exists | `src/mist/realtime/websocket_streams/web/services/pickers/related.py` | 934399eb302b2fdc007a9afc986cdced20f9bf83 | present | 49 |
| 2 | `targets()` builds a `BatchTargetResolver` for each call | same as row 1 | 934399eb302b2fdc007a9afc986cdced20f9bf83 | present | 63 |
| 3 | `hardware_targets()` method exists | same as row 1 | 934399eb302b2fdc007a9afc986cdced20f9bf83 | present | 67 |
| 4 | `sites()` reads the picker sites | same as row 1 | 934399eb302b2fdc007a9afc986cdced20f9bf83 | present | 100 |
| 5 | `BatchTargetResolver` class exists | same as row 1 | 934399eb302b2fdc007a9afc986cdced20f9bf83 | present | 107 |
| 6 | `_site_rows()` reads the picker sites for each call | same as row 1 | 934399eb302b2fdc007a9afc986cdced20f9bf83 | present | 160 |
| 7 | `build()` returns `rows`, `total_count`, `complete`, `reason`, `excluded`, and `scope` | same as row 1 | 934399eb302b2fdc007a9afc986cdced20f9bf83 | present | 269 |
| 8 | `ResourcePicker.sites()` calls `listOrgSites` | `src/mist/realtime/websocket_streams/intake/pickers/resources.py` | 6b65137fea554d1da3ce67dd19463a0a14d0b969 | present | 77 |
| 9 | The page reader loops over every page | `src/mist/realtime/websocket_streams/intake/pickers/records.py` | 9912ce21e7ac5bb813fc8daf853f720887accc18 | present | 32 |
| 10 | `mistapi.get_next` fetches the next page | same as row 9 | 9912ce21e7ac5bb813fc8daf853f720887accc18 | present | 50 |
| 11 | `StreamPickerService` inherits `ResourcePicker` | `src/mist/realtime/websocket_streams/intake/pickers/service.py` | ebab6beda7e7fc91bb8f6df53e95ee075b5e43b7 | present | 21 |
| 12 | The device cache lifetime is 30 seconds | `src/mist/realtime/websocket_streams/intake/pickers/devices.py` | 8e5cb175277d13372e5cd531e43326364f44fe72 | present | 91 |
| 13 | `ScopeRouter.TTL_SECONDS` is 300.0 | `src/operations/exporting/ex_hardware_inventory/run/routing.py` | aeeb69cd62fbb923c2a986fc61770c9509cc3e8a | present | 37 |
| 14 | `Discovery.sites` calls each organization service once | same as row 13 | aeeb69cd62fbb923c2a986fc61770c9509cc3e8a | present | 62 |
| 15 | `ScopeAwareTargets.hardware_targets` routes to the owner service | same as row 13 | aeeb69cd62fbb923c2a986fc61770c9509cc3e8a | present | 192 |
| 16 | The CLI batch builds `BatchTargetPickerService` | `src/operations/exporting/ex_hardware_inventory/run/batch.py` | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 156 |
| 17 | The CLI preview calls `service.preview` | same as row 16 | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 200 |
| 18 | The server preview runs a loop over sites | `src/mist/realtime/websocket_streams/web/services/operations/sessions.py` | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 288 |
| 19 | The preview selects `hardware_targets` for the hardware preset | same as row 18 | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 302 |
| 20 | The preview site discovery uses `hardware_sites` or `sites` | same as row 18 | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 345 |
| 21 | `WebSocketBatchService.preview` resolves targets | same as row 18 | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 903 |
| 22 | The browser groups site requests in fives | `src/mist/realtime/websocket_streams/web/static/websockets.js` | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 520 |
| 23 | The route for one site calls `batch.targets()` | `src/mist/realtime/websocket_streams/web/blueprint/routes/pickers.py` | 0967488421bfa681623f343b084d59106883ad1f | present | 113 |
| 24 | `DEFAULT_API_PAGE_LIMIT` is 1000 | `src/foundation/runtime/config/runtime_settings.py` | 4f47d44085d5bddef87f809cfd0ef5879052205f | present | 14 |
| 25 | Path `/api/v1/orgs/{org_id}/sites` has `operationId` `listOrgSites` | `documentation/mist-api-openapi31yaml.yaml` | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20018 |
| 26 | The `limit` parameter has default 100 and no maximum | same as row 25 | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59742 |
| 27 | The Mist documentation states 5000 API calls each hour for an API token | `documentation/api/admins/POST_register.md` | e809322db926f4b7d504926c7a5448b05b348f1f | present | 213 |
| 28 | The operator guide states that the preview loads all pages | `documentation/operator-guide.md` | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 344 |
| 29 | The fragment naming rule for an issue | `changelog.d/README.md` | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 27 |
| 30 | The mistapi pin is `>=0.64.1,<0.65` | `pyproject.toml` | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| 31 | The mistapi pin is `==0.64.1` | `requirements.txt` | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| 32 | The repository guide states `>=0.64.0,<0.65` (drift from row 30) | `.github/copilot-instructions.md` | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| 33 | `MYPY_PATHS` value | `.github/workflows/ci.yml` | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 34 | `VULTURE_PATHS`, `PYDOCSTYLE_PATHS`, and `INTERROGATE_PATHS` values (lines 101, 104, 107) | same as row 33 | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 35 | The foreign-site batch target test exists | `tests/unit/websocket_streams/web/test_ws_web_services.py` | d20a6c7b2f7e2f479f2d2db1e0df8265411e62ce | present | 389 |
| 36 | The existing site picker test calls `service.pickers.site.sites()` | same as row 35 | d20a6c7b2f7e2f479f2d2db1e0df8265411e62ce | present | 326 |
| 37 | The MSP routing test reads each organization once | `tests/unit/ex_hardware_inventory/run/test_hardware_routing.py` | 640689ce86b7f991ad6ba58facabdb8e20200b48 | present | 125 |
| 38 | The target and status routing test exists | same as row 37 | 640689ce86b7f991ad6ba58facabdb8e20200b48 | present | 137 |
| 39 | `FakeOrganization` patches `listOrgSites` | `tests/unit/ex_hardware_inventory/support/hardware_shells.py` | c907e585708491af46af06766c6cad0350909fca | present | 132 |
| 40 | The read-order integration test exists | `tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py` | dc4422ccd00aacc8228bc8893308dff32620a95e | present | 557 |
| 41 | The integration docstring names later site checks | same as row 40 | dc4422ccd00aacc8228bc8893308dff32620a95e | present | 558 |
| 42 | The symbol preservation guard exists | `tests/guardrails/test_src_public_symbol_preservation.py` | 08f978e755abdf643e7a6d826811401f710883f8 | present | 0 |
| 43 | The changelog fragment guard exists | `tests/guardrails/test_changelog_fragment_policy.py` | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| 44 | The WebSocket structure guard exists | `tests/unit/websocket_streams/live/transport/runtime/test_ws_feature_structure.py` | d2a3569288f6443e3d06b19819f0daa0eaa4478b | present | 0 |
| 45 | The nested package guard exists | `tests/guardrails/test_move_module_guidance.py` | ae163b792b330285dba7a8c32cc957a78c3838d4 | present | 0 |
| 46 | The SDK compatibility guard exists and stays unchanged | `tests/integration/test_mistapi_sdk_compatibility.py` | cab2d602113012729f6c392dff43197d05913a38 | present | 0 |
| 47 | The STE configuration exists | `.ste-linter.toml` | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| 48 | The STE writing guide exists | `documentation/ASD-STE100_writing-guide.md` | b464165aae116a17bb3031d3cef9b84a95589c0a | present | 0 |
| 49 | The constitution exists | `.specify/memory/constitution.md` | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 0 |
| 50 | The agent rules exist | `AGENTS.md` | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| 51 | The quality gate document exists | `documentation/quality-gates.md` | 6776d334cca5d9b43273473a06da367a65605c6d | present | 0 |
| 52 | The reference record specification exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| 53 | The route script exists | `.specify/scripts/powershell/spec-route.ps1` | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 0 |
| 54 | The factory exists and stays unchanged | `src/mist/realtime/websocket_streams/web/services/assembly/factory.py` | 2e35ee8b777a6ac419f606e9de7cb0099adcb28a | present | 0 |
| 55 | The structured logger `emit` method | `src/mist/realtime/websocket_streams/live/transport/runtime/logging/structured_logger.py` | 612da4028e4a1bf5ede34cc1e6fe146c04f408cb | present | 29 |
| 56 | The Gunicorn thread setting is `--threads 4` | `wsgi.py` | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 4 |
| 57 | The new module does not exist yet | `src/mist/realtime/websocket_streams/web/services/pickers/site_snapshot.py` | none | absent | 0 |
| 58 | The new fragment does not exist yet | `changelog.d/issue-4923-batch-site-snapshot.md` | none | absent | 0 |
| 59 | The record folder does not exist yet | `specs/numbered/0/0/1/2/4/1/4/3/4923-batch-site-snapshot` | none | absent | 0 |

Counts: 59 rows. 56 are present. 3 are absent. 0 are partial or stale.

## 4. Code path trace

Browser path for a site-scoped batch target:

1. `websockets.js`, line 455: `loadBatchTargets` starts the discovery.
2. `websockets.js`, line 517 and line 520: `readBatchDiscoveryPages` sends groups of five site requests.
3. `websockets.js`, line 514: the URL is `/api/websockets/batches/sites/<site_id>/targets?kind=<kind>&key=<key>`.
4. `routes/pickers.py`, line 113: `BatchTargetPickerRoutes.site_targets` calls `services.pickers.batch.targets`.
5. `related.py`, line 58 and line 63: `targets()` creates `BatchTargetResolver`, then calls `discover`.
6. `related.py`, line 160: `_site_rows` calls `self._picker.sites()["rows"]`. This is the full read that repeats for each site.
7. `resources.py`, line 71 and line 77: `ResourcePicker.sites` calls `listOrgSites`.
8. OpenAPI, line 20018: the request reaches `GET /api/v1/orgs/{org_id}/sites`.

Server preview path (hardware preset, and also the CLI batch):

1. `sessions.py`, line 891: `WebSocketBatchService.preview` starts the preview.
2. `sessions.py`, line 903: `self._targets.resolve(values)` resolves all targets.
3. `sessions.py`, line 345: the site discovery reads once through `hardware_sites` or `sites`.
4. `sessions.py`, lines 287 and 288: `Targets._discover` runs `_site_targets` for each selected site.
5. `sessions.py`, line 302: `hardware_targets` is selected for the hardware preset.
6. `related.py`, line 160: each site check reads the organization again. The total is N + 1 reads.

`start` (`sessions.py`, lines 916 to 968) contains no call to `resolve` or `_discover`. The start step reuses the preview record, so the start adds no organization read.

MSP path:

1. `routing.py`, line 180: `hardware_sites` starts the discovery across organizations.
2. `routing.py`, line 46 and line 62: `Discovery.sites` calls each organization service once.
3. `routing.py`, line 186 and line 192: `hardware_targets` routes each site check to the owner service of that site.

## 5. Local source evidence

- mistapi `listOrgSites`: `.venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py`, lines 17 and 18 for the signature, line 48 for the URI, and lines 50 and 51 for the `limit` query parameter.
- mistapi `get_next`: `.venv\Lib\site-packages\mistapi\__pagination.py`, line 17. The package exports it from `.venv\Lib\site-packages\mistapi\__init__.py`, line 16.
- Installed mistapi version: `.venv\Lib\site-packages\mistapi-0.64.1.dist-info`.
- OpenAPI: path at line 20018, `operationId` at line 20022, `limit` component at lines 59742 to 59749. The component sets `default: 100` and `minimum: 0`, and it sets no maximum.
- Endpoint coverage: `documentation\MIST_API_GET_ENDPOINTS.md`, line 867 lists `listOrgSites`. `documentation\MIST_API_MISSING_ENDPOINTS.md` lists `listOrgSiteStats` at line 882 and does not list `listOrgSites`.
- Rate limit wording: `documentation\api\admins\POST_register.md`, line 213.
- Operator behavior: `documentation\operator-guide.md`, lines 344 to 347.

## 6. Decisions

Each decision lists the options, the chosen option, the reason, and the risk. No decision needs a human decision. Each one is recorded in `4923-STATUS.json` with `human_decision_required` set to false.

### D-1 Owner of the site snapshot

- Options: (a) add a 30-second cache to `StreamPickerService.sites()`. (b) pass a preview token through each route. (c) keep one snapshot in the batch target service of each organization.
- Chosen: (c).
- Reason: Option (a) changes every caller of `sites()`, including the picker dropdown. Option (b) changes the route contract and the browser code. Option (c) changes only the batch target service, and both the browser path and the server path use it.
- Risk: The snapshot lives as long as the service object. A restart clears it.

### D-2 Lifetime of the site snapshot

- Options: (a) 5 seconds, from the issue text "a few seconds". (b) 30 seconds, the device cache lifetime. (c) 300 seconds, the scope lifetime. (d) no time limit until the next discovery.
- Chosen: (c), 300 seconds. The constant is `SITE_SNAPSHOT_LIFETIME_SECONDS`, and it equals `ScopeRouter.TTL_SECONDS` (row 13).
- Reason: A preview of many sites runs for minutes. Option (a) covers only a few site checks. Option (d) can keep a removed site for an unlimited time.
- Risk: Caution: a site removed in Mist can pass the site check for up to 300 seconds. Each device read then fails with the Mist error.

### D-3 Discovery reads the organization again

- Options: (a) discovery reads the snapshot when it is fresh. (b) discovery always reads.
- Chosen: (b).
- Reason: A new preview then includes sites that Mist added after the last read. The cost is one read for each discovery.
- Risk: A browser page that loads the site list again starts one read. The read count stays bounded.

### D-4 Single-flight lock

- Options: (a) no lock. (b) a `threading.Lock` held during the read. (c) a shared future that other threads await.
- Chosen: (b).
- Reason: The web UI runs four threads (row 56), and the browser sends five requests at once (row 22). Option (a) lets each request read the organization. Option (c) adds code without a benefit in one process.
- Risk: Other site checks wait while one read runs. The wait equals the read time.

### D-5 Fail closed on a failed read

- Options: (a) reuse the old snapshot after a failed read. (b) clear the snapshot and raise the picker error.
- Chosen: (b).
- Reason: A membership check must not use data that a failed read cannot confirm. A rate-limit response then stops the preview with a clear error.
- Risk: A short Mist outage stops the preview. The operator runs the preview again.

### D-6 Module placement

- Options: (a) add the class to `related.py`. (b) add a module to `intake/pickers/`. (c) add a module to `web/services/pickers/`.
- Chosen: (c).
- Reason: `related.py` has six top-level names (row 5 and the analysis item A-4). The constitution forbids a new direct child of a noncompliant module. `intake/pickers/` has five tracked children. `web/services/pickers/` has three tracked children, so it can take one more.
- Risk: The new module name must describe its subject. The name `site_snapshot.py` does that.

### D-7 No change outside the batch target service

- Options: (a) move the site map into `ScopeRouter`. (b) change the route to accept the snapshot. (c) change only the batch target service.
- Chosen: (c).
- Reason: `Discovery.sites` already calls each organization service once for each discovery (row 14). The organization services are cached by organization (`routing.py`, lines 136 to 146). The discovery priming covers the MSP path.
- Risk: `ScopeAwareTargets` keeps its own service object. Its snapshot is not primed when no discovery ran in the process. The first site check then reads once.

### D-8 Test location

- Options: (a) a new test file for the snapshot. (b) tests in the existing test files.
- Chosen: (b). The seven new tests go in `test_ws_web_services.py`, where the batch target tests already exist (row 35).
- Reason: The repository prefers existing files for tests of existing behavior. The batch target behavior already has tests in that file.
- Risk: The file grows by seven test functions.

### D-9 Changelog fragment

- Options: (a) no fragment, because the change is internal. (b) one fragment.
- Chosen: (b).
- Reason: The change alters how many Mist calls an operator's preview makes. Rule 4 in `changelog.d/README.md` (section "Obey these five rules", line 53) excludes only internal-only changes. This change is visible to the operator, so it gets a fragment.
- Risk: None material.

### D-10 Operator guide unchanged

- Options: (a) add a sentence about the read count. (b) make no edit.
- Chosen: (b).
- Reason: Lines 344 to 347 stay true. The portal loads all pages and does not start partial work. The operator sees the same result.
- Risk: None.

### D-11 Exact read list in the integration test

- Options: (a) keep the loose assertion `calls[:3]` and the set equality. (b) assert the exact list `[ORG_A, ORG_B, ORG_C]`.
- Chosen: (b).
- Reason: The start step does not run discovery (section 4). The exact list proves one read for each organization across the preview and the start.
- Risk: A later change that adds discovery to the start fails this test. That failure reports a new read, which is the intent of the test.

### D-12 Branch and commit type

- Options: (a) branch `refactor/4923-batch-site-snapshot` with commit type `refactor`. (b) branch `fix/4923-batch-site-snapshot` with commit type `perf` and scope `web-portal`.
- Chosen: (b).
- Reason: AGENTS.md allows the branch type `fix`. The constitution lists `perf` as a commit type. The issue title starts with "Perf:".
- Risk: None. AGENTS.md allows a more precise commit type than the branch type.

### D-13 Labels

- Options: (a) keep the labels unchanged. (b) add `in-progress`. (c) change the type label.
- Chosen: (b). The labels `refactor` and `web-portal` stay.
- Reason: AGENTS.md requires the `in-progress` label before a branch. The existing type label and scope label match the repository lists in `.github/copilot-instructions.md`.
- Risk: The orchestrator applies the labels. This record does not change them.

### D-14 Pin drift

- Options: (a) correct the pin text in `.github/copilot-instructions.md` in this change. (b) open a separate documentation issue.
- Chosen: (b). This change edits no pin text.
- Reason: AGENTS.md states that one issue holds one subject. The pin text does not affect the behavior of this change.
- Risk: Readers can use the wrong pin until the separate issue lands. The pin in code is `>=0.64.1,<0.65` (row 30).

## 7. Documents read

- `AGENTS.md`: read in full.
- `.github/copilot-instructions.md`: read in full, 600 lines. The local gates table (section "Local gates") and the labels table were used.
- `.specify/memory/constitution.md`: read in full, 562 lines.
- `.specify/templates/`: spec, plan, tasks, and checklist templates read in full.
- Reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`: headings and the structure of `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design/` read. Content was not copied.
- `documentation\quality-gates.md`: headings read.
- `documentation\operator-guide.md`: lines 336 to 362 read. The keyword search covered the rest of the file.
- `documentation\architecture.md` and `documentation\development-setup.md`: keyword search only. No picker or batch behavior appears in either file.
- `documentation\container-deployment.md`: not read. No container change applies to this issue.
- `changelog.d\README.md`: read in full.
- Mist API files: OpenAPI lines 20018 to 20060 and 59742 to 59750, read from the local copy and from the remote blob. `MIST_API_GET_ENDPOINTS.md` line 867 and `MIST_API_MISSING_ENDPOINTS.md` checked.

## 8. Sources

- Local paths: the paths in sections 3 to 5, in the repository working tree `Code\MistHelper`.
- Remote sources: GitHub `main` through `gh api`. The tree, the contents, and the blob endpoints were read.
- Web URLs: none fetched. The SDK docstring names a Juniper documentation page for `listOrgSites`. The page was not fetched, because the local SDK and OpenAPI files answer the questions.

## 9. Skills

No skill was loaded. The brief lists skills for Podman questions and Juniper device behavior. This issue asks about a Mist cloud read and a Python class, and no listed skill applies.

## 10. Unverified

- U-1: Live Mist behavior. This research made no live call. The page limit of 1000 and the 5000-call threshold are not checked against a live credential.
- U-2: The request count in PR #4924 (177 requests for 15 switches) is not measured here. The figure appears only in the PR body.
- U-3: The container start script is not read. It is named in `deploy/misthelper.container`, line 28. The worker count checked is `wsgi.py`, line 4.
- U-4: The mistapi source is local only. The `.venv` folder is not tracked, so no remote blob exists for it. The installed version is 0.64.1.
- U-5: The 5000-call threshold is documented for an API token (row 27). The issue states it for a credential. This record treats the two wordings as the same limit.
- U-6: The internals of `StructuredTransportLogger` beyond `emit` (row 55) are not read.
- U-7: The single table row for `listOrgSites` in `MIST_API_GET_ENDPOINTS.md` is checked. The rest of that document is not read.
- U-8: The full STE writing guide (row 48) is not read. This record applies the writing rules of AGENTS.md and brief rule 8.
