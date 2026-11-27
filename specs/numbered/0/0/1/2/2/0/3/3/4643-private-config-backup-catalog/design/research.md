# Research: Private Configuration Backup and Verified Catalog

## Method and Truth Order

The drafting pass read GitHub `main` through `gh api` and `gh pr` reads only. The remote `main` commit is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, read with `gh api repos/jmorrison-juniper/MistHelper/commits/main`.

Each code, test, configuration, and document claim has one row in the remote verification table. A local file counts as evidence only when its Git blob hash equals the remote blob SHA. The local checkout was read for line numbers only after that hash check.

The installed `mistapi` package is outside the repository tree. Its rows name the local path and the Git blob hash that `git hash-object` computed. The `ref` column for those rows reads `local install 0.64.1`.

No test, linter, build, package install, container, or repository script ran in this pass.

## Gate Status

| Gate | Owner | Status at drafting | Blocks |
| --- | --- | --- | --- |
| G2 contract evidence | Issue 4634 (open) | Open. Method identity, signatures, and OpenAPI paths are verified. Payload, header, and failure evidence are absent. Issue 4634 comments record the open items. | T003 and T009. Persistence and catalog reads. |
| G3 shared-file ownership | Issue 4633 (closed) | Partly cleared. PR 4615 merged on 2026-11-13T06:20:12Z. No open PR touches `web_portal/services/output_scan.py` or `web_portal/services/data_browser.py`. PR 4208 (open) owns `web_portal/app.py`, which this change does not touch. | T013, the integration pull request. |
| G4 storage and durability | Issue 4633 and issue 4643 comment IC_kwDOQltU8c8AAAABkRDV7A | Storage policy approved on 2026-11-08. Implementation evidence is absent: restart, multiworker, and refusal tests. | Enablement (FR-026). |
| G5 operator and production | Issue 4633 | Not authorized. The owner authorized live testing only in the Mist portal NVMM lab, for named bounded tests. | Any production run. |
| State and identity | Issue 4636 (open) | Open. The coordinator denies cloud writes until an identity exists for each operator. Offline state types are authorized. | T008 to T011, and any catalog endpoint. |
| G1 source reuse and legal | Issue 4635 (open) | Open. This record reuses no external source or asset. | No task in this record. |

## Owner and Coordinator Decisions

- Owner comment IC_kwDOQltU8c8AAAABkRDV7A on issue 4643, dated 2026-11-08T23:37:41Z. It approves the local private storage policy. It sets the directory and the permission rules. It sets the path refusals, the output boundary, and the retention rule. It also sets the typed `CONFIRM` rule for deletion and the encryption caveat.
- Owner correction IC_kwDOQltU8c8AAAABkRD3aQ on issue 4643, dated 2026-11-08T23:38:30Z. File ownership alone does not release T023 or T024. Contract evidence from issue 4634 and state and identity evidence from issue 4636 are also required. The decision permits policy documentation and test design only.
- Coordinator decision on issue 4633, dated 2026-11-08T23:37:56Z. It authorizes offline implementation in `src/interfaces/portals/cisco_config_converter/` and its feature-owned tests. Each shared-file change goes in a separate integration pull request. It names the shared-file owners at that date.
- Coordinator decision on issue 4636, dated 2026-11-08T23:39:28Z. It denies cloud-write enablement until the portal proves an identity for each operator, authorization, and durable state. It requires one stable private portal secret across restarts and workers.
- Issue 4634 comments dated 2026-11-08T09:34:47Z, 2026-11-10T13:44:04Z, and 2026-11-10T13:47:17Z. They record the OpenAPI and SDK checks, the schema results, and the open items. One item is the absent `deleteOrgServicePolicy` scope.

## Remote Verification Table

The `blob_sha` column holds the Git object SHA. For folders, it holds the tree SHA. A value of `none` marks an absent path. The `line` column holds the line where the claim appears. A value of `0` marks a file-level or folder-level claim.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | Writing style rules and STE precedence | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R-02 | Local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-03 | Managed spec roots and fixed base-5 route | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R-04 | Principle III safety and secret rules | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R-05 | Principle VI inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-06 | Principle VII action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-07 | Operational store rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 315 |
| R-08 | Data directory rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 326 |
| R-09 | Principle I five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-10 | Converter package holds five direct children | src/interfaces/portals/cisco_config_converter | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| R-11 | Digest form uses sorted canonical JSON and SHA-256 | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 88 |
| R-12 | Portal application registers no converter blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| R-13 | Firmware backup directory constant | src/operations/execution/firmware_policy/recovery/backup.py | main | 8ff5ba1da19a407e2041b018ae8e7a1cd90039c7 | present | 70 |
| R-14 | Private-access checker class | src/operations/execution/firmware_policy/recovery/backup.py | main | 8ff5ba1da19a407e2041b018ae8e7a1cd90039c7 | present | 86 |
| R-15 | POSIX check refuses group and other bits only | src/operations/execution/firmware_policy/recovery/backup.py | main | 8ff5ba1da19a407e2041b018ae8e7a1cd90039c7 | present | 162 |
| R-16 | Existing root receives chmod 0700 | src/operations/execution/firmware_policy/recovery/backup.py | main | 8ff5ba1da19a407e2041b018ae8e7a1cd90039c7 | present | 211 |
| R-17 | Exclusive file creation with O_EXCL | src/operations/execution/firmware_policy/recovery/backup.py | main | 8ff5ba1da19a407e2041b018ae8e7a1cd90039c7 | present | 214 |
| R-18 | SDK diagnostic redaction guard class | src/operations/execution/firmware_policy/sdk.py | main | 7c10dfd32e50ae7841ff24af3f02c2096a7b9ed2 | present | 30 |
| R-19 | Shared admission class | src/operations/execution/firmware_policy/sdk.py | main | 7c10dfd32e50ae7841ff24af3f02c2096a7b9ed2 | present | 86 |
| R-20 | HTTP status check for each response | src/operations/execution/firmware_policy/sdk.py | main | 7c10dfd32e50ae7841ff24af3f02c2096a7b9ed2 | present | 189 |
| R-21 | List shape check | src/operations/execution/firmware_policy/sdk.py | main | 7c10dfd32e50ae7841ff24af3f02c2096a7b9ed2 | present | 212 |
| R-22 | Page collector that does not keep the reported total | src/operations/execution/firmware_policy/sdk.py | main | 7c10dfd32e50ae7841ff24af3f02c2096a7b9ed2 | present | 219 |
| R-23 | Output scan imports the firmware directory constant | web_portal/services/output_scan.py | main | bf97eb8f0e92a51ac2b13b2a5922359321b54bc5 | present | 43 |
| R-24 | Output scan excludes the firmware directory name | web_portal/services/output_scan.py | main | bf97eb8f0e92a51ac2b13b2a5922359321b54bc5 | present | 85 |
| R-25 | Data browser refuses paths under the firmware directory | web_portal/services/data_browser.py | main | 247d411105a7af1ed54458418630626182494ffe | present | 154 |
| R-26 | Output scan test module imports the exclusion tuple | tests/unit/web_portal/test_output_scan_runtime_files.py | main | a8e9d4c00bc92638d6f2809cbea33727c4a91181 | present | 31 |
| R-27 | Data browser path-guard test module exists | tests/unit/config/standalone/foundation/persistence/database/test_data_browser_path_guard.py | main | 79cafab3dabcbbada53b5e9486aa8cfae76edee9 | present | 0 |
| R-28 | Repository page limit is 1000 | src/foundation/runtime/config/runtime_settings.py | main | 4f47d44085d5bddef87f809cfd0ef5879052205f | present | 14 |
| R-29 | Data directory is git-ignored | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 95 |
| R-30 | Gunicorn runs one worker | container/scripts/start.sh | main | 3b138807883a8a8785bac7d8c9b7f9a79458ed0c | present | 225 |
| R-31 | Portal secret falls back to a random uuid4 value | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| R-32 | Portal has no user authentication | deploy/.env.example | main | 7137364423308485be734a391798d85c6a37eaf4 | present | 155 |
| R-33 | Container user has UID 1000 | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 114 |
| R-34 | Firmware backups live under data/.firmware-policy-backups/ | documentation/org-auto-upgrade-policy.md | main | fb9d134e47bdf8b56811a6948bef842df8aff2c9 | present | 105 |
| R-35 | Nested package guard sets MAX_CHILDREN to 5 | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| R-36 | Python version requirement is 3.15 or newer | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-37 | mistapi is pinned to 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R-38 | Type check scope | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-39 | Dead-code scope | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-40 | Docstring style scope | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-41 | Docstring coverage scope | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-42 | SDK compatibility guard module exists | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 0 |
| R-43 | Firmware recovery SDK contract test exists | tests/contract/firmware_policy/recovery/test_sdk.py | main | 2fd0be542a8b3428eeecc9dd246a54b55b879612 | present | 0 |
| R-44 | List operation for networks is in the GET endpoint map | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 730 |
| R-45 | GET path for organization networks | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15118 |
| R-46 | GET path for organization service policies | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18340 |
| R-47 | GET path for organization services | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18489 |
| R-48 | Limit parameter has minimum 0 and no maximum | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59742 |
| R-49 | Page parameter has minimum 1 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59923 |
| R-50 | X-Page-Total header is not documented in the OpenAPI file | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 0 |
| R-51 | Network schema has an id property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 88224 |
| R-52 | Network routed_for_networks holds network names | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 88248 |
| R-53 | Service policy services property holds strings | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 89351 |
| R-54 | Service policy tenants property holds strings | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 89357 |
| R-55 | Service schema has an id property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 99752 |
| R-56 | Installed listOrgNetworks signature has limit and page | .venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py | local install 0.64.1 | 13c142d7fd215700217c96559cdfedf068647d70 | present | 17 |
| R-57 | Installed listOrgServices signature has limit and page | .venv\Lib\site-packages\mistapi\api\v1\orgs\services.py | local install 0.64.1 | 20e034e490c137209f284fc69b95b43e6f33eb24 | present | 17 |
| R-58 | Installed listOrgServicePolicies signature has limit and page | .venv\Lib\site-packages\mistapi\api\v1\orgs\servicepolicies.py | local install 0.64.1 | b1c6ab1bc13c6925db80dfd30105f6b7166f1a74 | present | 17 |
| R-59 | Installed response class reads the X-Page-Total header | .venv\Lib\site-packages\mistapi\__api_response.py | local install 0.64.1 | 2d878d79295fec79e6409f6243132c53280f15ab | present | 76 |
| R-60 | Full-parity T023 scope names backup tests in a contract folder | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 88 |
| R-61 | Full-parity T024 scope names routes.py and models.py | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 89 |
| R-62 | Full-parity T023 depends on T003 and T006 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 147 |
| R-63 | C26 requires complete paginated private backups | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 110 |
| R-64 | List calls use explicit limit and page | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 20 |
| R-65 | A failed page makes recovery evidence invalid | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/data-model.md | main | afb08dab16578918a56d4a4cb95ddee998d99883 | present | 41 |
| R-66 | Parent record has no backup requirement | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md | main | 5e8b1bc162cbfe2e9a3d604420c42e670dd0cd97 | absent | 0 |
| R-67 | Portal folder holds six direct children | src/interfaces/portals | main | 7f5ac6778b6a7a78ad7268542bb8de2a9c550926 | present | 0 |
| R-68 | Contract test folder holds 17 direct children | tests/contract | main | 3e544ef7c55adf7c8a8010e6da3afc345b27d57e | present | 0 |
| R-69 | Portal unit test folder holds 52 direct children | tests/unit/web_portal | main | 091139596e93c865ebf1f7f93cd5b7feba2ba772 | present | 0 |
| R-70 | Documentation folder holds 73 direct children | documentation | main | 627d6382fd192c7ae294729a543c2532c2075b41 | present | 0 |
| R-71 | Converter integration test folder holds two direct children | tests/integration/web_portal/cisco_config_converter | main | 6538f20cdb454342a96e079a0e7678fb6baa7a42 | present | 0 |
| R-72 | Converter state package is absent on main | src/interfaces/portals/cisco_config_converter/state | main | none | absent | 0 |
| R-73 | Converter backup test package is absent on main | tests/integration/web_portal/cisco_config_converter/backup | main | none | absent | 0 |
| R-74 | Network tenants property uses the network_tenants schema and holds address mappings | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 88262 |
| R-75 | Service policy schema has an id property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 89324 |
| R-76 | Repository clamps the MIST_PAGE_LIMIT setting to the range 1 to 1000 | src/foundation/support/refactors/main_entrypoint.py | main | 1402beb8e9a901a5ef143c43cc32a8bcad6f8fb1 | present | 327 |
| R-77 | Service policy GET names operation listOrgServicePolicies and references ServicePoliciesArray | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18345 |
| R-78 | Service GET names operation listOrgServices and references ServicesArray | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18494 |
| R-79 | Network GET 200 response references NetworksArray | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15128 |
| R-80 | Windows reparse-point refusal runs before the ACL query | src/operations/execution/firmware_policy/recovery/backup.py | main | 8ff5ba1da19a407e2041b018ae8e7a1cd90039c7 | present | 159 |

Summary of the table: 80 rows. Of them, 75 rows have the result `present`, and 5 rows have the result `absent`: R-12, R-50, R-66, R-72, and R-73. The STATUS file and the summary repeat the row count.

## Findings Used in the Design

- The three list operations exist in the OpenAPI file and in the pinned SDK, with `limit` and `page` arguments (R-44 to R-49, R-56 to R-58).
- The OpenAPI file does not document `X-Page-Total` (R-50). The SDK reads the header in `_check_next` (R-59). Completeness therefore has no documented proof, and the design fails closed (D-3).
- The schema references are names, not IDs. `routed_for_networks` (R-52), `services` (R-53), and `tenants` (R-54) hold strings. Each object carries an `id` (R-51, R-55).
- The firmware collector drops the reported total (R-22). The firmware permission check accepts narrower modes (R-15), and the firmware writer changes an existing root (R-16).
- The output scan and the data browser exclude the firmware directory by name only (R-24, R-25). A converter directory stays visible until the integration pull request merges (E-08).

## Decisions

Each decision names the alternatives, the choice, the reason, and the risk. Decisions D-18 and D-19 are human decisions. The other decisions are recorded as decided.

### D-1 Backup directory location

- Alternatives: (a) `data/cisco_config_converter/state/backup/`, the kind directory in draft 4636. (b) `data/.cisco-config-converter-backups/`. (c) `data/.firmware-policy-backups/`.
- Chosen: (b).
- Reason: The owner sets this path in comment IC_kwDOQltU8c8AAAABkRDV7A. The same comment keeps the format separate from firmware bundles, which rules out (c).
- Risk: Draft 4636 defines another directory for the same records (E-03). Issue 4636 needs an amendment.
- Human decision: No.

### D-2 Private-access verification

- Alternatives: (a) a new verifier. (b) Reuse `BackupAccess.verify` (R-14) and add an exact-mode check. (c) Reuse the firmware writer as it stands, including the repair at R-16.
- Chosen: (b).
- Reason: `BackupAccess` already applies the owner's Windows rule through SID comparison and the owner rule on POSIX. The exact-mode check closes the gap in R-15, because the owner requires modes 0700 and 0600. Option (c) changes permissions, which the owner forbids.
- Risk: The converter depends on a firmware module. Follow-up R-04 adds exact-mode checks to the shared checker.
- Human decision: No.

### D-3 Pagination proof

- Alternatives: (a) Reuse `PolicyResponse.collect` (R-22), which follows the next link. (b) Use explicit `page` numbers and prove the count with `X-Page-Total`. (c) Read pages until one is empty.
- Chosen: (b).
- Reason: Option (a) discards the total, so a short page passes silently. Option (c) cannot prove completeness when the server caps results. The OpenAPI file gives no header contract (R-50), so the design refuses a capture without the header. Explicit pages match the contract (R-64).
- Risk: Every capture refuses if the header is absent live (U-01). The owner must accept that refusal until issue 4634 closes.
- Human decision: No.

### D-4 Request admission and redaction

- Alternatives: (a) Call the SDK directly. (b) Reuse `PolicyAdmission.request` (R-19), `PolicyResponse.request` (R-20), `PolicyResponse.rows` (R-21), and `SettingsRequestGuard` (R-18).
- Chosen: (b).
- Reason: Shared admission keeps one quota view across the portal workflows. The guard redacts SDK diagnostics for settings reads.
- Risk: The converter depends on firmware classes. The test `test_capture_calls_only_list_functions_with_explicit_arguments` pins the call pattern.
- Human decision: No.

### D-5 Object families

- Alternatives: (a) The three families named in T023 and T024 (R-60, R-61): `service-policy`, `service`, and `network`. (b) All six families in the draft 4636 enumeration.
- Chosen: (a).
- Reason: The full-parity task map and the C26 row name these three families (R-63).
- Risk: The other families need their own tasks.
- Human decision: No.

### D-6 Mist read calls

- Alternatives: (a) The three list functions. (b) The list functions plus get functions for single objects.
- Chosen: (a).
- Reason: The list functions cover the three families (R-44 to R-47, R-56 to R-58). The get functions for single objects appear in the missing endpoint map (`documentation/MIST_API_MISSING_ENDPOINTS.md`, line 704), so this design does not use them.
- Risk: The design assumes each list item holds the complete object (U-02).
- Human decision: No.

### D-7 Relationships by name

- Alternatives: (a) Record only ID-based relationships. (b) Record name-based relationships with the key type `name` and refuse any target that matches zero or several objects. (c) Omit relationships.
- Chosen: (b).
- Reason: The schemas reference networks, services, and tenants by name (R-52 to R-54). Option (a) would record none for these families. Option (c) breaks the owner requirement for relationships.
- Risk: Live names can collide (U-05). Restore in issue 4646 must resolve each relationship to an ID before any write.
- Human decision: No.

### D-8 Digests and seal

- Alternatives: (a) SHA-256 digests only. (b) HMAC-SHA256 seal keyed from the `PORTAL_SECRET_KEY` environment variable, as draft 4636 decisions D-4 and D-5 define. (c) A seal key read from the portal configuration value `secret_key`.
- Chosen: (b), with the environment variable only.
- Reason: The configuration value falls back to a random value at each start (R-31). A seal key from that value would break verification after a restart.
- Risk: A changed secret breaks verification (D-18).
- Human decision: No. D-18 covers the human part.

### D-9 File naming and content

- Alternatives: (a) Put the organization and the family in the file name. (b) Use an opaque identifier and put the metadata inside the sealed file.
- Chosen: (b).
- Reason: File names can reach listings and logs. The identifier rule matches draft 4636.
- Risk: Operators cannot find a file by its content from its name. The catalog returns metadata after verification.
- Human decision: No.

### D-10 Catalog exposure

- Alternatives: (a) Add a route now. (b) Use an in-process catalog only. (c) Add a route after issue 4636 approves identity.
- Chosen: (b). Option (c) follows later through a separate change.
- Reason: The owner blocks a catalog endpoint until issue 4636 approves the design. The portal has no user authentication (R-32).
- Risk: No operator view exists until the later change.
- Human decision: No.

### D-11 Module placement

- Alternatives: (a) A new `state/backup/` package, which adds a sixth child to `state/`. (b) Classes in `state/lifecycle/backup.py`, which keeps five top-level names. (c) A new package under `src/interfaces/portals/`, which adds a child to a folder that already holds six (R-67). (d) The firmware recovery package, which is outside the owner file scope and holds six children.
- Chosen: (b).
- Reason: Options (a), (c), and (d) each break the five-child rule or the owner scope.
- Risk: The module reaches five top-level names (E-13). A sixth name needs a structure decision.
- Human decision: No.

### D-12 Test placement

- Alternatives: (a) `tests/contract/cisco_config_converter/`, the T023 path. (b) `tests/integration/web_portal/cisco_config_converter/backup/`.
- Chosen: (b).
- Reason: The contract folder holds 17 children (R-68). The converter test root holds two (R-71). Draft 4636 decision D-2 uses the same placement.
- Risk: The tests sit in the integration tier, not the contract tier.
- Human decision: No.

### D-13 Shared-file exclusions

- Alternatives: (a) Change `output_scan.py` and `data_browser.py` in the feature pull request. (b) Change them in a separate integration pull request after the handover. (c) Rely on file permissions only.
- Chosen: (b).
- Reason: The coordinator decision on issue 4633 requires separate integration pull requests. At drafting time, no open PR touches either file, and PR 4615 merged on 2026-11-13. PR 4208 owns `web_portal/app.py`, which this change does not touch.
- Risk: Persistence waits until the integration pull request merges (FR-020).
- Human decision: No.

### D-14 Failed and retained files

- Alternatives: (a) Delete an unverified file after a failed read-back. (b) Keep the file and exclude it from the catalog.
- Chosen: (b).
- Reason: The owner forbids automatic deletion (comment IC_kwDOQltU8c8AAAABkRDV7A) and requires retention of recovery bundles.
- Risk: An unverified file holds settings until an operator removes it through a later approved workflow.
- Human decision: No.

### D-15 File size bound

- Alternatives: (a) No bound. (b) A bound of 134217728 bytes (128 MiB), checked before any parse.
- Chosen: (b).
- Reason: An unbounded read can exhaust memory on a damaged or hostile file.
- Risk: A valid large file is excluded (U-09).
- Human decision: No.

### D-16 Logging content

- Alternatives: (a) Log object IDs and bodies for triage. (b) Log the action, family, backup ID, counts, and refusal reason.
- Chosen: (b).
- Reason: Principle III forbids secret logging (R-04). The owner forbids backup content in logs (IC_kwDOQltU8c8AAAABkRDV7A).
- Risk: Triage needs a private read of the sealed file.
- Human decision: No.

### D-17 No production caller

- Alternatives: (a) Connect the writer to a route or a menu now. (b) Keep the classes unused in product code until the gates pass.
- Chosen: (b).
- Reason: The owner correction permits policy documentation and test design only.
- Risk: Unused classes can fail the dead-code gate. The local gate result records any failure.
- Human decision: No.

### D-18 Seal-key rotation and backup readability (human decision)

- Alternatives: (a) Re-seal each backup after rotation, with an operator workflow that verifies with the old key first. (b) Keep the old key for as long as any backup exists, because the retention rule has no expiry. (c) Use a separate backup seal key, held as its own secret, so portal rotation does not affect backups.
- Recommended: (c). It isolates backup readability from portal session rotation. It needs a new secret and an entry in `deploy/.env.example`.
- Reason: The owner must approve the credential policy. A rotated secret otherwise makes every sealed backup unverifiable.
- Risk: Each option adds an operational burden.
- Human decision: Yes. Credential policy.

### D-19 Encryption at rest (human decision)

- Alternatives: (a) Permission-only protection, as the owner decided on 2026-11-08. (b) Encrypt each backup file with a key that a key-management policy governs.
- Recommended: (a), only after the organization confirms that no separate rule requires encryption at rest. The owner comment says that persistence stops until a key-management policy exists when such a rule applies.
- Reason: The owner states that file permissions do not prove encryption. The organization must answer whether a rule applies.
- Risk: A rule that requires encryption blocks persistence until the key policy exists.
- Human decision: Yes. Credential and encryption policy.

## Mist Contract Notes

- The three list functions take a session, an organization ID, and optional `limit` and `page` keywords (R-56 to R-58). The SDK forwards those values as query parameters. No body is sent.
- The SDK sets `next` from a `next` key in a dictionary response or from `X-Page-Total`, `X-Page-Limit`, and `X-Page-Page` headers (R-59). Lists return arrays, so the header path applies.
- The design uses page limit 1000, the repository default page limit (R-28). The capture sends this value explicitly on each call.
- No write operation is part of this change. The payload evidence for writes stays in issue 4634.

## Sources

- Issue 4643 body and comments: `https://github.com/jmorrison-juniper/MistHelper/issues/4643`. Comment `https://github.com/jmorrison-juniper/MistHelper/issues/4643#issuecomment-6728766956` (owner decision) and `https://github.com/jmorrison-juniper/MistHelper/issues/4643#issuecomment-6728775529` (owner correction).
- Issue 4633 comments dated 2026-11-08T08:29:48Z, 2026-11-08T23:37:56Z, and 2026-11-08T23:38:04Z.
- Issue 4634 comments dated 2026-11-08T09:34:47Z, 2026-11-10T13:44:04Z, and 2026-11-10T13:47:17Z.
- Issue 4636 comments dated 2026-11-08T23:39:28Z, 2026-11-09T16:55:13Z, and 2026-11-09T17:07:13Z.
- PR 4596, merged 2026-11-13T09:41:52Z. Its ten changed files all sit under the full-parity folder.
- PR 4615, merged 2026-11-13T06:20:12Z. PR 4208, open.
- Draft record 4636, local path `C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-drafts\4636\` (its `design\data-model.md`, `plan.md`, `analysis.md`, and `spec.md`). The draft is not on `main`.
- Installed mistapi 0.64.1, local path `.venv\Lib\site-packages\mistapi`. Its rows are R-56 to R-59.
- Skill `container-storage`, file `03-filesystem-content/01-mounts-mappings-and-copy.md`, section "Mount, observation, and release interfaces". The skill states that the library supplies the container's UID and GID maps to the driver when it creates the mounted view. This supports U-08. The skill also states that Podman orchestration has a separate owner, so this record uses the skill only for the storage mapping principle.

## Unverified

Each item lists the reason that the claim is unverified and the owner of the next step.

- U-01: The `X-Page-Total` header appears on the three list operations live. The OpenAPI file does not document it (R-50). Owner: issue 4634.
- U-02: Each list item carries the complete object body. The schemas show object fields (R-51, R-55), but no live response was read. Owner: issue 4634.
- U-03: The service family reference fields. The `service` schema starts at line 99703 (R-55). This record read only the `id` property. Owner: issue 4634, task T003.
- U-04: Production sets `PORTAL_SECRET_KEY`. The repository cannot show the production environment. Owner: the owner (issue 4636, U-11).
- U-05: Live relationship names collide within one capture. The schema permits duplicates, and no live data was read. Owner: issue 4646 for restore.
- U-06: Live 429 and quota behavior on page reads. No live call was made in this pass. Owner: issue 4634 and the operator.
- U-07: The Windows access query result on the owner host. No query ran in this pass. Owner: implementer, the test `test_directory_checks_real_windows_acl` in `test_backup_directory.py`.
- U-08: The POSIX owner and mode of the mounted `data` directory inside the container, on Windows and macOS hosts. The skill states that the mapping shapes the view. No container was started. Owner: implementer, with the container steps in `design/quickstart.md`.
- U-09: The adequacy of the 128 MiB bound. No size evidence exists. Owner: owner, with G4 evidence.
- U-10: Whether these Markdown records join the STE gate. The local gates table lists specific files only. Owner: orchestrator (issue 4636, U-8).
- U-11: The legal basis for reuse of external material. This record reuses none. Owner: issue 4635.
- U-12: Whether the converter needs `deleteOrgServicePolicy`. Issue 4634 records this open question. Owner: issue 4634.
- U-13: Whether standard `logging` with key-value text satisfies the constitution's structured log rule. Issue 4636 records the same question (its U-2). Owner: owner.
- U-14: Whether the complete objects hold secret-bearing fields. The schemas must list each such field before enablement. No live object was read. Owner: owner, with the issue 4634 review.
