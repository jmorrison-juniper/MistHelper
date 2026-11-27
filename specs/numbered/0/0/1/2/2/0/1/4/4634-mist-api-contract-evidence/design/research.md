# Research: Mist API Contract Evidence for the Cisco Converter

This file holds the decisions, the remote verification table, the unverified items, and the sources for issue 4634. The method uses local source first. Each remote check compares a repository path with GitHub `main`. The same 80 checks appear in `_meta\4634-STATUS.json` and in `_meta\4634-summary.md`.

## Method

1. Issue facts came from `gh issue view` with the JSON fields listed in the brief. The issue has five labels and three comments.
2. Linked PRs came from `gh pr list` with the search term 4634. The search returned PR 4596 only. PR 4596 merged on 2026-11-13.
3. No existing record folder starts with `4634-`. The search covered the local `specs` tree and the remote tree (zero matches).
4. The remote tree came from `gh api` with the recursive tree option. It held 11,404 entries and was not truncated. Local files equal the remote blobs for 75 checked paths. The check used `git hash-object` without `-w`.
5. Line numbers for files under 1 MB came from decoded remote contents. Line numbers for the two large Mist files came from local copies with equal blob SHAs.
6. The bundled OpenAPI JSON file has one line, so view ranges cannot split it. A JSON parser extracted the object locations, written as `paths[path].verb`. The YAML twin gives the `operationId` line.
7. The mistapi source is local only. It sits in the `.venv` folder, which the repository tree does not hold. Each SDK row names the local path.
8. No `web_fetch` call ran. No upstream URL was fetched. No live Mist request ran.

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. The chosen option is the recommended option.

### D-1 Offline evidence only

- Alternatives: (a) read-only live Mist calls through mistapi. (b) Offline evidence from the bundled OpenAPI file, the pinned SDK source, and synthetic fixtures. (c) Recorded fixtures from a lab tenant.
- Chosen: (b). This is the recommended option.
- Reason: The issue forbids cloud writes. The operator instruction forbids live calls. Offline evidence repeats in CI.
- Risk: The service can differ from the documents. Writes stay disabled, and gate G4 stays open.
- Human decision: No.

### D-2 Track each operation separately

- Alternatives: (a) One status for each family. (b) One status for each operation.
- Chosen: (b). This is the recommended option.
- Reason: The issue requires independent tracking. Missing evidence then blocks only one row.
- Risk: The record holds 40 contract rows. Family IDs map each row to record 4644 (FR-021).
- Human decision: No.

### D-3 Include the 18 read operations

- Alternatives: (a) Writes only. (b) Writes and reads. (c) Defer the reads to a later issue.
- Chosen: (b). This is the recommended option.
- Reason: Record 4645 asks this issue for reference reads (analysis F-04). Gate G2 covers reads and read-back (4645 plan line 130).
- Risk: The scope grows. Each read operation has an identity row and a role.
- Human decision: No.

### D-4 Exclude deleteOrgServicePolicy and keep it disabled

- Alternatives: (a) Add the operation to a family. (b) Exclude the operation and keep it disabled. (c) Defer the decision.
- Chosen: (b). This is the recommended option.
- Reason: No converter code names a service policy (converter scan, A-21). Record 4645 decision D-13 excludes the operation. The operation deletes production policy data.
- Risk: A later mapping may need the operation. A new issue must reopen the decision with owner approval.
- Human decision: Yes. HUMAN-DECISION-REQUIRED. The recommended option is to exclude the operation.

### D-5 Count SDK repeats of HTTP 429 as one attempt

- Alternatives: (a) Change the SDK retry count through a private attribute. (b) Accept the repeats and classify a final 429 as indeterminate. (c) Build a custom session.
- Chosen: (b). This is the recommended option.
- Reason: The retry loop sits inside the SDK (RV-64, lines 209 to 237). A private attribute is brittle. Record 4644 uses the same rule (its D-7).
- Risk: A create can repeat after HTTP 429. Create families stay disabled. The executor reads back before any retry.
- Human decision: No.

### D-6 Validate bodies with the bundled schema and a local allowlist

- Alternatives: (a) Schema validation only. (b) SDK validation only. (c) Schema validation plus an allowlist built from the schema properties.
- Chosen: (c). This is the recommended option.
- Reason: Most object schemas allow unknown fields (A-06). The SDK validates no body. Its wrapper signatures type the body as a dictionary or a list, and no wrapper validates it (RV-67 to RV-77).
- Risk: The allowlist can drift from the schema. The tests build the allowlist from the schema at run time.
- Human decision: No.

### D-7 Refuse list request bodies

- Alternatives: (a) Allow lists for each operation that accepts a dictionary or a list. (b) Refuse lists. (c) Allow lists after a service test.
- Chosen: (b). This is the recommended option.
- Reason: The OpenAPI file declares object bodies (A-22). The generic validator rejects a list (issue comment 2). Service support is unverified (U-09).
- Risk: A future family may need lists. A new decision must cite evidence.
- Human decision: No.

### D-8 Refuse a null site-template identifier as unassignment

- Alternatives: (a) Treat null as unassignment. (b) Refuse null. (c) Allow null after owner approval.
- Chosen: (b). This is the recommended option.
- Reason: The schema allows null but gives no meaning (A-10, U-08). Unassignment changes inheritance on live sites. Record 4645 decision D-3 asks the owner.
- Risk: The site-template path stays unavailable until the owner decides.
- Human decision: Yes. HUMAN-DECISION-REQUIRED. The recommended option is to refuse null.

### D-9 Place the tests under tests\contract\web_portal\cisco_config_converter

- Alternatives: (a) The converter integration folder, as records 4636 (D-2), 4644 (D-15), and 4645 (D-5) choose. (b) `tests\contract\cisco_config_converter`, as the parity tasks name. (c) `tests\contract\web_portal\cisco_config_converter`.
- Chosen: (c). This is the recommended option.
- Reason: The integration folder holds two children now (RV-32), and record 4649 projects five (A-14). `tests\contract` holds 17 children (RV-31). `tests\contract\web_portal` holds one child (RV-30).
- Risk: This choice differs from three sibling decisions. The owners of those records must accept the path.
- Human decision: No.

### D-10 Add no production code

- Alternatives: (a) Add a read-only evidence module under `src\mist`. (b) Add a write gate module. (c) Add tests and records only.
- Chosen: (c). This is the recommended option.
- Reason: The parent folders hold five or six children (RV-33 to RV-35). The write gate belongs to record 4644. The issue asks for evidence and tests.
- Risk: The evidence lives in tests and documents. Tests detect drift.
- Human decision: No.

### D-11 Use mistapi 0.64.1 as the evidence version

- Alternatives: (a) Version 0.64.0 from `.github\copilot-instructions.md` line 21 (RV-45). (b) Version 0.59 from the constitution line 279 (RV-44). (c) Version 0.64.1 from `requirements.txt` line 129 (RV-48).
- Chosen: (c). This is the recommended option.
- Reason: The exact pin names version 0.64.1. The installed package matches (RV-63).
- Risk: Five documents state three mistapi versions (A-11). A separate issue corrects the text.
- Human decision: No.

### D-12 Send only verified fields

- Alternatives: (a) Send every converter field. (b) Send the verified gateway template fields only. (c) Send fields after a service test.
- Chosen: (b). This is the recommended option.
- Reason: Record 4644 verifies three fields for families F-04 and F-05: `name`, `type`, and `dns_servers`. The converter model uses the same three fields (RV-11).
- Risk: Other families have no verified fields. Their rows stay partial.
- Human decision: No.

### D-13 Keep secret-bearing families disabled until redaction evidence exists

- Alternatives: (a) Change the SDK logger in product code. (b) Disable the SDK body log. (c) Keep the families disabled until redaction evidence exists.
- Chosen: (c). This is the recommended option.
- Reason: The SDK logs bodies at DEBUG (RV-65). A logger change needs product code, which D-10 excludes.
- Risk: An operator who enables DEBUG can expose a secret on an enabled family. This change enables no family.
- Human decision: No.

### D-14 Keep needs-human-review and add no auto-merge label

- Alternatives: (a) Add the auto-merge label after CI passes. (b) Add no auto-merge label and wait for review.
- Chosen: (b). This is the recommended option.
- Reason: Issue 4634 carries `needs-human-review`. The label says a human must review the change before merge.
- Risk: The merge waits for a person.
- Human decision: No.

### D-15 Add one changelog fragment

- Alternatives: (a) Add no fragment. (b) Add one fragment.
- Chosen: (b). This is the recommended option.
- Reason: The constitution requires one fragment for each change (Documentation section). Record 4920 added one for its spec change (RV-61).
- Risk: None known.
- Human decision: No.

### D-16 Use route 0/0/1/2/2/0/1/4 and slug mist-api-contract-evidence

- Alternatives: (a) A timestamp route under `specs\live`. (b) The numbered route for 4634.
- Chosen: (b). This is the recommended option.
- Reason: Issue 4634 equals 122014 in base 5. It pads to 00122014, which gives the route. The folder is free (RV-22).
- Risk: None known.
- Human decision: No.

### D-17 Labels

- Alternatives: (a) Add `in-progress` and keep the other labels. (b) Remove `needs-investigation` now. (c) Add a scope label.
- Chosen: (a). This is the recommended option.
- Reason: The claim needs `in-progress` (AGENTS Git flow). Label `needs-investigation` stays until the automated contract tests pass (tasks T005 to T015). The `web-portal` scope label already exists.
- Risk: The orchestrator applies the labels. This record changes no label.
- Human decision: No.

### D-18 Require name in service and service policy bodies

- Alternatives: (a) Rely on the schema, which requires no field. (b) Require `name` in the local rule. (c) Require a different field.
- Chosen: (b). This is the recommended option.
- Reason: The schema requires no field for `service` or `org_service_policy` (A-07). The parity contract says duplicate names need explicit conflict resolution (`mist.md`, Discovery and Approval).
- Risk: A service without a name cannot be created. Duplicate-name handling needs a separate review.
- Human decision: No.

## Remote Verification

Each row compares one claim with GitHub `main`, unless the ref column names another source. The result uses the words present, absent, partial, or stale. For a directory, the blob SHA column holds the tree SHA. For a local path, the blob SHA column holds `not-a-blob`. The line column holds the line number, or 0 when the row checks presence or a count.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| RV-01 | Parity contract file exists on main | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 45 |
| RV-02 | Parity contract lists 21 write rows (count check) | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 0 |
| RV-03 | Parity contract omits deleteOrgServicePolicy (count check) | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | absent | 0 |
| RV-04 | Parity task T003 defines the G2 evidence path | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 30 |
| RV-05 | Parity task rule: a family needs T003 evidence first | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 120 |
| RV-06 | Parity plan defines gate G2 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 126 |
| RV-07 | PR 4596 merged into main on 2026-11-13 | pull request 4596 | main | not-a-blob | present | 0 |
| RV-08 | Converter conversion module exists | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 11 |
| RV-09 | IOSDnsConverter.convert builds the offline proposal | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 15 |
| RV-10 | Conversion module names no Mist call (count check) | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | absent | 0 |
| RV-11 | GatewayTemplate declares name, type, and dns_servers | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 13 |
| RV-12 | Source type is limited to standalone and spoke | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 51 |
| RV-13 | Portal route /preview is registered for POST | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 62 |
| RV-14 | Portal route /export is registered for POST | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 64 |
| RV-15 | Portal URL prefix is /cisco-config-converter | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 54 |
| RV-16 | Routes module names no Mist call (count check) | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | absent | 0 |
| RV-17 | Integration route test class TestConverterRoutes exists | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 38 |
| RV-18 | Unit converter test class TestIOSDnsConverter exists | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 47 |
| RV-19 | Path cited by issue comment 1 exists | tests/unit/gateway/overrides | main | not-a-blob | absent | 0 |
| RV-20 | Overrides module reads one device through the SDK | src/mist/resources/gateway/overrides/device_data_fetcher.py | main | 391b7f1aaf3558190d8de6dd7136064de0c9d26b | present | 110 |
| RV-21 | SDK compatibility test names no target write function (count check) | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | absent | 0 |
| RV-22 | Route folder for this record is free | specs/numbered/0/0/1/2/2/0/1/4 | main | not-a-blob | absent | 0 |
| RV-23 | Sibling record 4636 folder is absent on main | specs/numbered/0/0/1/2/2/0/2/1 | main | not-a-blob | absent | 0 |
| RV-24 | Sibling record 4644 folder is absent on main | specs/numbered/0/0/1/2/2/0/3/4 | main | not-a-blob | absent | 0 |
| RV-25 | Sibling record 4645 folder is absent on main | specs/numbered/0/0/1/2/2/0/4/0 | main | not-a-blob | absent | 0 |
| RV-26 | Parent record 4224 spec exists | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md | main | 5e8b1bc162cbfe2e9a3d604420c42e670dd0cd97 | present | 1 |
| RV-27 | Parent record 4224 contract mist-apply.md exists | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/mist-apply.md | main | fbb549f8077f9d73773e7ca1ff8c5d3a3878615d | present | 0 |
| RV-28 | Reference record 4920 spec exists (shape source) | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RV-29 | Reference record 4920 design/contracts holds four files | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts | main | 90fed4d4cc3af19a3ecbe42ba2f6732680d60e77 | present | 0 |
| RV-30 | tests/contract/web_portal holds one child | tests/contract/web_portal | main | 61a998d782633bc325aefa574e18f8491e982dd1 | present | 0 |
| RV-31 | tests/contract holds 17 children | tests/contract | main | 3e544ef7c55adf7c8a8010e6da3afc345b27d57e | present | 0 |
| RV-32 | Converter integration folder holds two children | tests/integration/web_portal/cisco_config_converter | main | 6538f20cdb454342a96e079a0e7678fb6baa7a42 | present | 0 |
| RV-33 | Overrides unit folder holds five children | tests/unit/marvis/mist/resources/gateway/overrides | main | 7642b0de1d18f1cad5443a04b7b78c38bfc68db6 | present | 0 |
| RV-34 | Converter package folder holds five children | src/interfaces/portals/cisco_config_converter | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| RV-35 | Overrides source folder holds six children | src/mist/resources/gateway/overrides | main | f0d8ca266c8c8160d41c2bdf7551c2da31e127de | present | 0 |
| RV-36 | New contract test folder is free | tests/contract/web_portal/cisco_config_converter | main | not-a-blob | absent | 0 |
| RV-37 | OpenAPI JSON file exists on main | documentation/mist-api-openapi31json.json | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 1 |
| RV-38 | Issue-cited commit exists | commit 7b7d5406ca7b95a96edf42702ee0049e0c7c2d64 | 7b7d5406ca7b95a96edf42702ee0049e0c7c2d64 | not-a-blob | present | 0 |
| RV-39 | OpenAPI JSON blob is identical at the issue-cited commit | documentation/mist-api-openapi31json.json | 7b7d5406ca7b95a96edf42702ee0049e0c7c2d64 | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 1 |
| RV-40 | OpenAPI YAML exists with version 2609.1.0 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 54 |
| RV-41 | Record 4644 YAML line for createOrgSite matches the YAML file | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20047 |
| RV-42 | GET catalog lists listOrgNetworkTemplates | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 723 |
| RV-43 | MISSING catalog states its comparison basis | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | present | 3 |
| RV-44 | Constitution states mistapi 0.59 or newer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| RV-45 | Copilot instructions state mistapi 0.64.0 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| RV-46 | pyproject pins mistapi 0.64.1 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| RV-47 | pyproject declares jsonschema 4.26.0 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 47 |
| RV-48 | requirements pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RV-49 | requirements pins jsonschema 4.26.0 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 101 |
| RV-50 | Quality guide holds the writing gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| RV-51 | CI runs Bandit on the repository root | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 451 |
| RV-52 | CI mypy paths list no tests folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RV-53 | CI radon paths list one test file and not this folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 99 |
| RV-54 | CI vulture paths list no tests folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RV-55 | Spec route function Resolve-SpecFeaturePath exists | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| RV-56 | Spec template exists | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| RV-57 | Plan template exists | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| RV-58 | Tasks template exists | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| RV-59 | Checklist template exists | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| RV-60 | AGENTS.md exists with the writing rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| RV-61 | Changelog fragment example exists | changelog.d/issue-4920-ex-hardware-inventory-csv.md | main | 05befcb6b5e3f67c1554c1041d0d8d03d922abb7 | present | 0 |
| RV-62 | STE configuration exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RV-63 | mistapi 0.64.1 is installed locally | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local | not-a-blob | present | 0 |
| RV-64 | SDK request layer holds the retry constants and the retry loop | .venv\Lib\site-packages\mistapi\__api_request.py | local | not-a-blob | present | 59 |
| RV-65 | SDK request layer logs write request bodies at DEBUG | .venv\Lib\site-packages\mistapi\__api_request.py | local | not-a-blob | present | 296 |
| RV-66 | SDK REST write calls pass no timeout (count check) | .venv\Lib\site-packages\mistapi\__api_request.py | local | not-a-blob | absent | 298 |
| RV-67 | SDK orgs sites functions createOrgSite and listOrgSites | .venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py | local | not-a-blob | present | 58 |
| RV-68 | SDK sites functions updateSiteInfo and getSiteInfo | .venv\Lib\site-packages\mistapi\api\v1\sites\sites.py | local | not-a-blob | present | 67 |
| RV-69 | SDK setting functions updateSiteSettings and getSiteSetting | .venv\Lib\site-packages\mistapi\api\v1\sites\setting.py | local | not-a-blob | present | 42 |
| RV-70 | SDK device functions updateSiteDevice, getSiteDevice, and listSiteDevices | .venv\Lib\site-packages\mistapi\api\v1\sites\devices.py | local | not-a-blob | present | 1478 |
| RV-71 | SDK inventory functions updateOrgInventoryAssignment and getOrgInventory | .venv\Lib\site-packages\mistapi\api\v1\orgs\inventory.py | local | not-a-blob | present | 139 |
| RV-72 | SDK gateway template functions: create, update, delete, get, and list | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | local | not-a-blob | present | 58 |
| RV-73 | SDK device profile functions: create, delete, update, assign, unassign, get, and list | .venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py | local | not-a-blob | present | 63 |
| RV-74 | SDK network functions: create, delete, update, get, and list | .venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py | local | not-a-blob | present | 58 |
| RV-75 | SDK network template list function listOrgNetworkTemplates | .venv\Lib\site-packages\mistapi\api\v1\orgs\networktemplates.py | local | not-a-blob | present | 17 |
| RV-76 | SDK service functions: create, delete, update, get, and list | .venv\Lib\site-packages\mistapi\api\v1\orgs\services.py | local | not-a-blob | present | 58 |
| RV-77 | SDK service policy functions: create, delete, update, get, and list | .venv\Lib\site-packages\mistapi\api\v1\orgs\servicepolicies.py | local | not-a-blob | present | 58 |
| RV-78 | SDK constants function listDeviceModels | .venv\Lib\site-packages\mistapi\api\v1\const\device_models.py | local | not-a-blob | present | 17 |
| RV-79 | SDK names updateOrgSite and updateOrgInventory are absent | .venv\Lib\site-packages\mistapi\api\v1 | local | not-a-blob | absent | 0 |
| RV-80 | Development setup states mistapi 0.64.0, less than 0.65 | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 14 |

Line numbers for RV-01 to RV-28 and RV-30 to RV-35 came from decoded remote contents or from remote tree listings. Line numbers for RV-37 to RV-41 came from the local copies of the large Mist files. RV-40 and RV-41 read the YAML file at the same blob SHA.

## Sources

- S-01 `documentation\mist-api-openapi31json.json`. Blob `5f9f4ce94f812f0e818ee65f99f032118a28f56c`. One line. Object locations use `paths[path].verb` and `components.schemas`.
- S-02 `documentation\mist-api-openapi31yaml.yaml`. Blob `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`. Version line 54. The `operationId` lines match the record 4644 table (RV-41).
- S-03 `.venv\Lib\site-packages\mistapi\` (version 0.64.1, read-only).
- S-04 `.venv\Lib\site-packages\jsonschema-4.26.0.dist-info` (installed validator).
- S-05 Parity record files on main: `design\contracts\mist.md`, `tasks.md`, and `plan.md` (RV-01 to RV-06).
- S-06 Converter files on main: `conversion.py`, `models.py`, and `routes.py` (RV-08 to RV-16).
- S-07 Converter tests on main: `test_routes.py` and `test_cisco_config_converter.py` (RV-17 and RV-18).
- S-08 Overrides module on main: `device_data_fetcher.py` (RV-20).
- S-09 `documentation\MIST_API_GET_ENDPOINTS.md` and `documentation\MIST_API_MISSING_ENDPOINTS.md` (RV-42 and RV-43).
- S-10 Governance files: `AGENTS.md`, `.github\copilot-instructions.md`, `.specify\memory\constitution.md`, the four templates, and `.specify\scripts\powershell\spec-route.ps1`.
- S-11 `documentation\quality-gates.md` (writing gate, RV-50) and `documentation\development-setup.md` (pin statement, RV-80).
- S-12 `.github\workflows\ci.yml` (path variables and Bandit, RV-51 to RV-54).
- S-13 Sibling records in the local spec-drafts folder: 4636 (summary, STATUS, and files), 4644 (STATUS and `design\contracts\mist-write-families.md`), 4645 (summary, spec, analysis, and plan), and 4649 (analysis). None of them is on main. Rows RV-23 to RV-25 confirm this.
- S-14 GitHub issue 4634 and its comments. URL `https://github.com/jmorrison-juniper/MistHelper/issues/4634`. Comment IDs IC_kwDOQltU8c8AAAABkIkhQQ, IC_kwDOQltU8c8AAAABk3WdVw, and IC_kwDOQltU8c8AAAABk3awKg.
- S-15 GitHub PR 4596. URL `https://github.com/jmorrison-juniper/MistHelper/pull/4596`.
- S-16 Commit 7b7d5406ca7b95a96edf42702ee0049e0c7c2d64 (RV-38 and RV-39).

No `web_fetch` call ran. No upstream URL was fetched. The parity contract cites Context7 documentation. This record does not use it (U-11).

## Trace of the Affected Path

1. A browser sends `POST /cisco-config-converter/preview` (`routes.py` line 62).
2. `ConverterRoutes.preview` reads one upload through `ConverterInput.source`.
3. `SourceConfiguration.read` validates the upload and the template name and type (`models.py` lines 13 to 51).
4. `IOSDnsConverter.convert` builds the offline proposal (`conversion.py` line 15). The proposal holds one gateway template.
5. `ReviewState.publish` stores a digest in the session. The route returns the proposal as JSON.
6. `POST /cisco-config-converter/review` and `POST /cisco-config-converter/export` check the digest. Export returns the reviewed proposal as a download (`routes.py` line 64).

No step makes a Mist call (RV-10 and RV-16). The only Mist read in the overrides code is `getSiteDevice` (RV-20). No write path exists in this repository. The write path belongs to record 4644.

## Sibling Consistency

- Record 4644 cites YAML line numbers for its write families. This record reproduces those numbers (RV-41).
- Record 4645 asks this issue for reads. This record adds 18 reads (D-3).
- Record 4649 projects the converter integration folder at five children. This record places its tests elsewhere (D-9).
- Record 4636 summary states 60 remote checks. Its STATUS file states 24 (A-13).
- Records 4644 (F-01), 4645 (F-02), and 4649 (F-03) cite `tests/contract/cisco_config_converter` (A-14).

## Unverified

- U-01 Field meaning for write operations W-02 to W-21 beyond schema descriptions and property types. The repository holds no service evidence.
- U-02 Whether an update replaces or merges the object. The OpenAPI file does not say.
- U-03 Service response for HTTP 5xx. The OpenAPI file declares no 5xx response.
- U-04 Service handling of unknown request fields in objects that allow them. No test ran against the service.
- U-05 Hardware and model support for device and device profile subtypes. The parity contract lists this item as pending.
- U-06 Idempotency of POST create calls and PUT update calls. No service evidence exists.
- U-07 Presence of `id` in create responses. The schema does not require `id`.
- U-08 Meaning of a null `sitetemplate_id`. The schema allows null and gives no description.
- U-09 Array support for operations that the SDK annotates as accepting a dictionary or a list. The OpenAPI file declares objects.
- U-10 Role permissions for each write operation. The OpenAPI file does not describe them. Gate G4 owns this item.
- U-11 Context7 documentation for mistapi cited by the parity contract. It was not fetched.
- U-12 Upstream mistapi project documentation. It was not fetched. The local source answers the questions in this record.
- U-13 Results of the offline probes in issue comments 2 and 3. The probe is not in the repository.
- U-14 Whether the service retry window matches the SDK waits of 5, 10, and 20 seconds. No service evidence exists.
- U-15 MAC address format accepted by the service. The schema has no MAC pattern.
- U-16 Service effect of deleting an object that other objects reference. Record 4645 requires reference reads for this check.
- U-17 Effect of `updateSiteSettings` on inherited site settings. The OpenAPI file does not describe inheritance for this operation.
- U-18 Precedence between `dns_servers` in a gateway template and the DNS settings in device configuration. The description names the override. The precedence needs a service test.

## Skills

No skill was loaded. The task concerns the Mist API contract. It involves no Podman behavior and no Juniper device behavior.
