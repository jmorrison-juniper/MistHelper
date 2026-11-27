# Research: Multi-site stable word and router channel lab verification

Issue: #3392. Audit date: 2026-11-26. Reference: `main` of jmorrison-juniper/MistHelper.

Each claim below cites a remote check row (RC-nn). Local files were read to search only. The remote row decides the claim.

## Summary

Issue #3392 asks for four lab answers. The answers decide two code paths. The organization access point route refuses the stable word in two layers. The router channel has three values in the schema, the portal, the SDK, and the CLI. Two parity rows and one issue path are stale. The owner runs every lab check. The agent makes no cloud call.

## Issue and linked work

Read with `gh` only. The record holds no token value.

- Issue #3392 is OPEN. Created 2026-09-25T16:14:32Z. Updated 2026-11-06T08:40:47Z. Labels: chore, web-portal, upgrade-portal, firmware, priority:P3, needs-human-review.
- Comment IC_kwDOQltU8c8AAAABaCJ2iA (2026-10-07) reassesses origin/main at commit e0dc054d74e0a53c074c8b08158f105eb7c08fc0. It states that no lab run occurred.
- Comment IC_kwDOQltU8c8AAAABeA-lUg (2026-10-21, owner) authorizes checks only on identified lab devices. It requires exact targets and a one-time typed confirmation. No firmware request is authorized.
- `gh pr list --search "3392"` with state all returned no pull request. A search for "#3392" also returned none.
- PR #3391 is MERGED (2026-09-25T16:08:28Z). Its head is feat/3383-multisite-advanced-controls. It closes #3383. Its changed-file list names src/firmware and src/upgrade_portal paths. Both are absent on main (RC-58, RC-59).
- Issue #3383 is CLOSED (2026-09-25T16:08:29Z). Issues #3388, #3389, and #3390 are CLOSED. The body of PR #3391 names each issue.
- `gh api repos/jmorrison-juniper/MistHelper/commits/e0dc054d74e0a53c074c8b08158f105eb7c08fc0` returns the commit. Its committer date is 2026-10-07T09:11:26Z.

## Existing record check

- A search of `specs` for folders named `3392-*` returned no folder. No legacy record exists. Existing record found: false.
- The folder `specs/3383-multisite-advanced-controls` exists at the specs root. The baseline grandfathers it (RC-26). It supplies Decisions 2 and 3 (RC-17, RC-18). It is not reused as the record for 3392.
- The route folder `specs/numbered/0/0/1/0/2/0/3/2/` is absent on main (RC-112).

## Remote verification

Method:

- One tree call: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The response holds 11404 entries and is not truncated.
- Content checks decode the base64 body from the `contents` endpoint with `ref=main`. The OpenAPI YAML exceeds the contents size limit. For that file the blobs endpoint returned the body.
- Local SDK rows read the installed package under `.venv`. An installed package is not a repository blob. The row records a SHA-256 value instead.
- Result: 114 present, 3 absent, 3 stale. Total 120 rows.

Columns: ID, Claim, Path, Ref, Blob SHA, Result, Line. A line value of 0 marks a file or folder check.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | AGENTS.md writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-02 | AGENTS.md bans semicolons, contractions, and Latin abbreviations | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 50 |
| RC-03 | Python 3.15 or newer | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| RC-04 | Instructions pin mistapi as a range from 0.64.0 to below 0.65 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| RC-05 | Local gates section | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| RC-06 | STE gate row names a fixed list of Markdown files | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-07 | Managed roots and fixed route for numbered records | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| RC-08 | Typed word UPGRADE for destructive CLI operations | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 327 |
| RC-09 | Changelog fragment naming rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 452 |
| RC-10 | Five-children rule for each hierarchy level | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| RC-11 | Principle III requires typed confirmation for firmware upgrades | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 119 |
| RC-12 | Constitution states mistapi 0.59 or newer, which conflicts with the pin | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 279 |
| RC-13 | Route width default is eight digits | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| RC-14 | Route base is five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| RC-15 | Numbered records join under the numbered root | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 51 |
| RC-16 | Reference record title | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| RC-17 | Decision 2 refuses the stable build for access points | specs/3383-multisite-advanced-controls/research.md | main | 598db49e3ee3331dc94aeb3f893f11a5549d4266 | present | 28 |
| RC-18 | Decision 3 names the router channel need | specs/3383-multisite-advanced-controls/research.md | main | 598db49e3ee3331dc94aeb3f893f11a5549d4266 | present | 46 |
| RC-19 | Citation lint command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 66 |
| RC-20 | MYPY_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-21 | VULTURE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| RC-22 | PYDOCSTYLE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| RC-23 | INTERROGATE_PATHS value | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| RC-24 | speckit-task-audit step is advisory with a true fallback | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 750 |
| RC-25 | Exact pin mistapi==0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| RC-26 | Legacy record 3383 is grandfathered in the baseline | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 247 |
| RC-27 | Builds the access point child body through _ap_body | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 672 |
| RC-28 | Access point child uses the organization access point route | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 674 |
| RC-29 | Defines the access point body method _ap_body | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 685 |
| RC-30 | Body method refuses the vendor stable build | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 699 |
| RC-31 | Refusal message for the vendor stable build | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 700 |
| RC-32 | Adds the shared access point fields to the body | src/operations/execution/firmware/aggregate_upgrade_service.py | main | 496b269d8dc0ed5d006609f21a0e910ff7e5ffc3 | present | 740 |
| RC-33 | Organization body requires exactly one versions record | src/operations/execution/firmware/org_upgrade_body.py | main | 5e19d030ca1b150adf8e889751ac637635a5d4b8 | present | 182 |
| RC-34 | Organization body requires the firmware_type ap value | src/operations/execution/firmware/org_upgrade_body.py | main | 5e19d030ca1b150adf8e889751ac637635a5d4b8 | present | 192 |
| RC-35 | Router endpoint name upgradeOrgSsrs | src/operations/execution/firmware/upgrade_service.py | main | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 49 |
| RC-36 | VERSION_STABLE holds the word stable | src/operations/execution/firmware/upgrade_service.py | main | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 58 |
| RC-37 | SSR_CHANNEL_CHOICES holds alpha, beta, and stable | src/operations/execution/firmware/upgrade_service.py | main | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 78 |
| RC-38 | Router body copies the channel when the operator picks one | src/operations/execution/firmware/upgrade_service.py | main | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 766 |
| RC-39 | Stable choice replaces the typed version for each body | src/operations/execution/firmware/upgrade_service.py | main | 24825d192e4988ce408b92e9a3be6f5fb10b6d90 | present | 925 |
| RC-40 | ADVANCED_FIELDS includes channel | src/interfaces/portals/upgrade_portal/upgrade/org_advanced_options.py | main | fab86177b1c617f028ae39f338db195946b8203b | present | 39 |
| RC-41 | Defines the refusal refuse_stable_access_points | src/interfaces/portals/upgrade_portal/upgrade/org_advanced_options.py | main | fab86177b1c617f028ae39f338db195946b8203b | present | 143 |
| RC-42 | Raises BadOptionError when the stable word meets an access point | src/interfaces/portals/upgrade_portal/upgrade/org_advanced_options.py | main | fab86177b1c617f028ae39f338db195946b8203b | present | 162 |
| RC-43 | Save calls the access point stable refusal | src/interfaces/portals/upgrade_portal/app/routes/org_upgrade.py | main | 11c839db760b07291b51a3804546dc53e8ba8a85 | present | 1287 |
| RC-44 | Stable group shows only for switch and gateway types | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | main | 2675897ed0a835538b084673b8c1f628dbaff612 | present | 299 |
| RC-45 | Router channel select has the id org-upgrade-ssr-channel | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | main | 2675897ed0a835538b084673b8c1f628dbaff612 | present | 535 |
| RC-46 | Router channel options list stable, beta, and alpha | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | main | 2675897ed0a835538b084673b8c1f628dbaff612 | present | 541 |
| RC-47 | Warning text for alpha and beta builds | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_options.html | main | 2675897ed0a835538b084673b8c1f628dbaff612 | present | 548 |
| RC-48 | Stable help text names the organization access point limit | src/interfaces/portals/upgrade_portal/upgrade/options.py | main | 6a1446c99a1f03b6c2110df3030bd860c3c9ca3a | present | 321 |
| RC-49 | Router channel reader accepts only the channel choices | src/interfaces/portals/upgrade_portal/upgrade/options.py | main | 6a1446c99a1f03b6c2110df3030bd860c3c9ca3a | present | 1324 |
| RC-50 | Single-site page offers the stable build for every device | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/options.html | main | 3adbec813ea894ef7513b143b8e6e63c596370f3 | present | 575 |
| RC-51 | Single-site router channel list | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/options.html | main | 3adbec813ea894ef7513b143b8e6e63c596370f3 | present | 797 |
| RC-52 | Confirm word is CONFIRM | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 2 |
| RC-53 | Organization writes disabled caution text | src/interfaces/portals/upgrade_portal/app/assets/templates/upgrade/org_confirm.html | main | bb388fd2845aa235c5d802fe58bbd7e981f10015 | present | 112 |
| RC-54 | Write gate variable ORG_UPGRADE_WRITES_ENABLED | src/interfaces/portals/upgrade_portal/app/config.py | main | adfa7ba9b59ea1ab89bbcb8a20a18cfc28b4ff6e | present | 55 |
| RC-55 | Blank value keeps organization writes closed | src/interfaces/portals/upgrade_portal/app/config.py | main | adfa7ba9b59ea1ab89bbcb8a20a18cfc28b4ff6e | present | 501 |
| RC-56 | CLI channel prompt offers stable, beta, and alpha | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | present | 2315 |
| RC-57 | CLI alpha warning text | src/operations/execution/firmware/firmware_manager.py | main | f1c1c6d1ccc5b1fe16e5a34d86e57a2b55f6c00f | present | 2324 |
| RC-58 | Path cited by issue #3392 is absent | src/firmware/aggregate_upgrade_service.py | main | absent | absent | 0 |
| RC-59 | Path cited by PR #3391 is absent | src/upgrade_portal/upgrade/org_advanced_options.py | main | absent | absent | 0 |
| RC-60 | Organization device upgrade path for the POST operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9232 |
| RC-61 | Organization device upgrade job path for the GET operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9282 |
| RC-62 | Organization device upgrade cancel path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9306 |
| RC-63 | Organization router upgrade path for the list GET and the POST | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20956 |
| RC-64 | Router job list description names the release channel | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20958 |
| RC-65 | Operation identifier listOrgSsrUpgrades | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20960 |
| RC-66 | Organization router cancel path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 21013 |
| RC-67 | Site device upgrade path for the POST operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 28825 |
| RC-68 | Organization device upgrade body has a versions property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 116073 |
| RC-69 | Deprecated version field names suggested and alpha, not stable | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 116070 |
| RC-70 | Deprecated strategy field of the organization device upgrade body | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 116066 |
| RC-71 | Organization version entry holds a free string version | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 116191 |
| RC-72 | Site device upgrade version allows the stable word | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 116310 |
| RC-73 | Single-device router upgrade defaults version to stable | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 105317 |
| RC-74 | Router channel enum alpha, beta, and stable | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 105326 |
| RC-75 | Multi-device router upgrade request body | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 105332 |
| RC-76 | Multi-device router channel description | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 105337 |
| RC-77 | Multi-device router strategy enum big_bang and serial | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 105359 |
| RC-78 | Job status enum words | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 115749 |
| RC-79 | JSON twin holds the organization device upgrade key at character offset 3333602 | documentation/mist-api-openapi31json.json | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 0 |
| RC-80 | Router API note names the channel enum alpha, beta, and stable | documentation/api/utilities/POST_orgs_org_id_ssr_upgrade.md | main | 1df713fd4515a21bcdd00249f1eea1a24c1c0a27 | present | 35 |
| RC-81 | Router API note describes reboot_at with minus one to disable reboot | documentation/api/utilities/POST_orgs_org_id_ssr_upgrade.md | main | 1df713fd4515a21bcdd00249f1eea1a24c1c0a27 | present | 47 |
| RC-82 | Router API note strategy enum big_bang and serial | documentation/api/utilities/POST_orgs_org_id_ssr_upgrade.md | main | 1df713fd4515a21bcdd00249f1eea1a24c1c0a27 | present | 57 |
| RC-83 | Site API note allows the stable word in version | documentation/api/utilities/POST_sites_site_id_devices_upgrade.md | main | a76a7d2c5032f787cccb67b6e2c1dd1f51c2ce49 | present | 197 |
| RC-84 | Contract case refuses stable with an access point plan | tests/contract/upgrade_portal/test_org_advanced_options.py | main | c6015b6c849d9aca280b9bdcada039e9825d8814 | present | 133 |
| RC-85 | Contract test: stable reaches each switch body | tests/contract/upgrade_portal/test_org_advanced_options.py | main | c6015b6c849d9aca280b9bdcada039e9825d8814 | present | 381 |
| RC-86 | Contract test: router channel reaches only the router body | tests/contract/upgrade_portal/test_org_advanced_options.py | main | c6015b6c849d9aca280b9bdcada039e9825d8814 | present | 394 |
| RC-87 | Contract test: channel control shows only for a router | tests/contract/upgrade_portal/test_org_advanced_options.py | main | c6015b6c849d9aca280b9bdcada039e9825d8814 | present | 405 |
| RC-88 | Unit test: stable build needs a body that names it | tests/unit/upgrade_portal/test_org_advanced_summary.py | main | 4e3ce5cf57abd654c6349c61690cd274f1e74440 | present | 150 |
| RC-89 | Unit test: stable choice replaces each picked version | tests/unit/upgrade_portal/test_upgrade_advanced_options.py | main | 436532d55274604851f56a2dd91b81c24817d098 | present | 365 |
| RC-90 | Unit test: SSR channel stable value | tests/unit/upgrade_portal/test_upgrade_ssr_options.py | main | 3d10a681011490583195f1720bc188da39f9fe97 | present | 158 |
| RC-91 | Prod test refused request holds stable_version true | tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_advanced_bodies.py | main | cda412a8a3e55c337b7bf0edaa0375b69e316708 | present | 96 |
| RC-92 | Prod test refuses the stable build for the access point child | tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_advanced_bodies.py | main | cda412a8a3e55c337b7bf0edaa0375b69e316708 | present | 158 |
| RC-93 | E2E test: router channel control count is zero without a router | tests/e2e/upgrade_portal/test_org_advanced_options.py | main | 1923a2a41906710ac675bbcbf894821cf2808366 | present | 227 |
| RC-94 | E2E test: stable build with an access point names the control | tests/e2e/upgrade_portal/test_org_advanced_options.py | main | 1923a2a41906710ac675bbcbf894821cf2808366 | present | 231 |
| RC-95 | Single-site contract case: stable yes option | tests/contract/upgrade_portal/test_upgrade_options.py | main | 4eaf0d36a54ab66195eaf870903567039f81d2dc | present | 128 |
| RC-96 | Single-site contract loop over alpha, beta, and stable | tests/contract/upgrade_portal/test_upgrade_options.py | main | 4eaf0d36a54ab66195eaf870903567039f81d2dc | present | 1358 |
| RC-97 | Contract test requires the exact confirmation word | tests/contract/upgrade_portal/test_org_upgrade_routes.py | main | d026c23ca2c0abe647fc8106bea5ce8a88442bcf | present | 633 |
| RC-98 | Parity row C17 lists the access point family | tests/e2e/upgrade_portal/journeys/parity_matrix.json | main | 8d67df755c596c5b56925c8ecac688f357ebbd60 | present | 743 |
| RC-99 | Parity row C17 verdict is parity, which conflicts with the refusal | tests/e2e/upgrade_portal/journeys/parity_matrix.json | main | 8d67df755c596c5b56925c8ecac688f357ebbd60 | stale | 756 |
| RC-100 | Parity row C17 multi-site evidence path is org_options.html line 35 | tests/e2e/upgrade_portal/journeys/parity_matrix.json | main | 8d67df755c596c5b56925c8ecac688f357ebbd60 | present | 770 |
| RC-101 | Parity row C21 verdict is parity, which conflicts with the evidence path | tests/e2e/upgrade_portal/journeys/parity_matrix.json | main | 8d67df755c596c5b56925c8ecac688f357ebbd60 | stale | 922 |
| RC-102 | Parity row C21 multi-site evidence path is org_options.html line 35 | tests/e2e/upgrade_portal/journeys/parity_matrix.json | main | 8d67df755c596c5b56925c8ecac688f357ebbd60 | present | 936 |
| RC-103 | Parity row C17 names test_parity_pages.py as its multi-site journey | tests/e2e/upgrade_portal/journeys/parity_matrix.json | main | 8d67df755c596c5b56925c8ecac688f357ebbd60 | present | 753 |
| RC-104 | Spec route contract guard file exists | tests/guardrails/test_spec_route_contract.py | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 0 |
| RC-105 | Five-child guard file exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| RC-106 | Changelog fragment policy guard file exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| RC-107 | SDK compatibility guard file exists | tests/integration/test_mistapi_sdk_compatibility.py | main | cab2d602113012729f6c392dff43197d05913a38 | present | 0 |
| RC-108 | STE linter configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-109 | Pull request template exists | .github/PULL_REQUEST_TEMPLATE.md | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 0 |
| RC-110 | Changelog fragment README exists | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 0 |
| RC-111 | Parity page test file exists | tests/e2e/upgrade_portal/journeys/test_parity_pages.py | main | afd90f6c0e22cdc9d385d3c8f7db6ae8561cbf27 | present | 0 |
| RC-112 | Route folder for issue #3392 is absent before this record | specs/numbered/0/0/1/0/2/0/3/2/ | main | absent | absent | 0 |
| RC-113 | The installed SDK defines upgradeOrgDevices | .venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py | local install | sha256:1bce5cc173e5e24f0702cace9b9cbef9fce034992fddd05d099372254ae95683 | present | 840 |
| RC-114 | The installed SDK defines getOrgDeviceUpgrade | .venv\Lib\site-packages\mistapi\api\v1\orgs\devices.py | local install | sha256:1bce5cc173e5e24f0702cace9b9cbef9fce034992fddd05d099372254ae95683 | present | 871 |
| RC-115 | The installed SDK defines listOrgSsrUpgrades | .venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py | local install | sha256:312eeada911529f97998f239feef84a24ceac4877e3f6d5502630de45694a12b | present | 89 |
| RC-116 | The installed SDK defines upgradeOrgSsrs | .venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py | local install | sha256:312eeada911529f97998f239feef84a24ceac4877e3f6d5502630de45694a12b | present | 114 |
| RC-117 | getOrgSsrUpgrade requests the cancel path with a GET call | .venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py | local install | sha256:312eeada911529f97998f239feef84a24ceac4877e3f6d5502630de45694a12b | present | 167 |
| RC-118 | listOrgAvailableSsrVersions channel enum alpha, beta, and stable | .venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py | local install | sha256:312eeada911529f97998f239feef84a24ceac4877e3f6d5502630de45694a12b | present | 221 |
| RC-119 | The installed SDK defines upgradeSiteDevices | .venv\Lib\site-packages\mistapi\api\v1\sites\devices.py | local install | sha256:ea6a683dbc2d7bb516b039115eae8d0b4d1dc6b18e8e2fe668d9e18de5c87291 | present | 1230 |
| RC-120 | Installed mistapi package version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local install | sha256:3eb4404e7676444f00932d85e933d755475d0371fadb018d597f3e009556c9cb | present | 3 |

## Decisions

Each decision names the alternatives, the choice, the reason, and the risk. D-18 is the only decision that needs a human.

### D-1 Keep both access point refusals until an accepted lab answer exists

- Alternatives: (a) Remove both refusals now and send the stable word. (b) Keep both refusals. (c) Show the stable control and let the cloud refuse the write.
- Chosen: (b).
- Reason: The organization version entry is a free string and names no stable word (RC-71). The deprecated version field names suggested and alpha, not stable (RC-69). Warning: a firmware write can change production devices (RC-11).
- Risk: The access point parity gap stays until the owner posts an accepted answer. Mitigation: T006, T011, and T012.

### D-2 The owner runs every lab check, and the agent makes no cloud call

- Alternatives: (a) The agent runs the checks with a token. (b) The owner runs the checks. (c) Close the issue without the checks.
- Chosen: (b).
- Reason: The owner comment of 2026-10-21 authorizes owner runs only. The agent has no lab access. The brief forbids the agent from writes and credential use.
- Risk: The issue waits for the owner. Mitigation: owner steps T005 to T010 with fixed contracts.

### D-3 The typed phrase for each lab write is CONFIRM

- Alternatives: (a) UPGRADE, the CLI word (RC-08). (b) CONFIRM, the portal word (RC-52). (c) A phrase chosen for each run.
- Chosen: (b).
- Reason: The portal already requires CONFIRM for organization writes (RC-52). One word keeps one convention for operators and owners.
- Risk: The constitution example names UPGRADE (RC-11). The two words differ by surface. Mitigation: analysis item A-7.

### D-4 Keep all three channel values until each router lab answer exists

- Alternatives: (a) Remove beta and alpha now. (b) Keep all three values. (c) Keep all three values and add an unverified note.
- Chosen: (b).
- Reason: The schema enum names all three values (RC-74). The SDK channel filter documents the same enum (RC-118). The portal, the CLI, and the tests use all three values (RC-46, RC-56, RC-96).
- Risk: A refused value stays visible until its answer exists. Mitigation: T007 to T009 and T013 to T015.

### D-5 Cite the current main paths, not the stale paths of issue #3392

- Alternatives: (a) Cite the paths named by issue #3392 under src/firmware. (b) Edit the issue text. (c) Cite the current main paths.
- Chosen: (c).
- Reason: The issue path is absent on main (RC-58). The current paths hold the code (RC-27, RC-40). The agent cannot write to GitHub.
- Risk: The issue text stays stale until the owner edits it. Mitigation: analysis item A-1 names the owner action.

### D-6 Place the record at ROUTE\3392-multisite-stable-channel-lab

- Alternatives: (a) A flat folder under specs. (b) A timestamp record under specs\live. (c) The numbered route.
- Chosen: (c).
- Reason: The constitution requires managed roots and the numbered route for numeric records (RC-07, RC-10). The route digits for 3392 are 0, 0, 1, 0, 2, 0, 3, 2. Hand calculation with base five and eight digits gives that result from RC-13, RC-14, and RC-15.
- Risk: The route folder is new. Mitigation: T001, TST-15, and TST-16.

### D-7 Use the local OpenAPI file as the Mist contract

- Alternatives: (a) Fetch upstream Juniper documentation. (b) Use mistapi docstrings only. (c) Use the local OpenAPI file and its JSON twin.
- Chosen: (c).
- Reason: The local file answers each schema question in this record (RC-60 to RC-78). The brief requires local sources before web sources.
- Risk: The local file can lag the cloud. Mitigation: the lab answers decide each undocumented word.

### D-8 Gate each code branch on its posted lab answer

- Alternatives: (a) Implement both branches behind a flag. (b) Implement neither branch and file a new issue. (c) Gate each branch on its lab answer.
- Chosen: (c).
- Reason: A flag keeps unused code for an unknown answer. A new issue delays the rules that the answers need.
- Risk: The access point parity waits for the owner. Mitigation: D-15 corrects the parity rows now.

### D-9 Treat requirements.txt as the executable pin and record the constitution text as stale

- Alternatives: (a) Amend the constitution now. (b) Change the pin to a range. (c) Keep the exact pin and record the stale text.
- Chosen: (c).
- Reason: requirements.txt pins 0.64.1 exactly (RC-25). The installed package is 0.64.1 (RC-120). The instructions name a range (RC-04). The constitution says 0.59 or newer (RC-12).
- Risk: The three documents disagree. Mitigation: analysis item A-5 for the owner.

### D-10 Read access point jobs with getOrgDeviceUpgrade and router jobs with listOrgSsrUpgrades

- Alternatives: (a) Use getOrgSsrUpgrade for router jobs. (b) Use listOrgSsrUpgrades for router jobs. (c) Read no job state.
- Chosen: (b) for router jobs and getOrgDeviceUpgrade for access point jobs.
- Reason: getOrgSsrUpgrade requests the cancel path with a GET call (RC-117). The list operation names the release channel in its description (RC-64, RC-65). The access point job path is documented (RC-61, RC-114).
- Risk: The list returns every router job. Mitigation: the owner reads the job created by the lab check only.

### D-11 Post each lab answer in the fixed contract format

- Alternatives: (a) Paste raw cloud responses. (b) Write a free text summary. (c) Use fixed fields.
- Chosen: (c).
- Reason: Raw bodies can hold identifiers and tokens. Fixed fields let the four answers compare.
- Risk: The owner must fill each field. Mitigation: checklist lab-evidence.md.

### D-12 Run the STE gate on changed Markdown files and on the fixed list

- Alternatives: (a) The fixed list only (RC-06). (b) Changed files only. (c) Both.
- Chosen: (c).
- Reason: The fixed list omits specs records (RC-06). AGENTS.md requires STE prose (RC-01).
- Risk: Record prose can score below 80. Mitigation: the self-review of the brief rule 8.

### D-13 Send minimal lab bodies and repeat once on a field error

- Alternatives: (a) Send the full portal body. (b) Send minimal bodies. (c) Send bodies with documented defaults.
- Chosen: (b).
- Reason: The organization body in code sends the deprecated strategy field (RC-70). The single-device router schema defaults version to stable (RC-73). Minimal bodies isolate the checked word.
- Risk: The cloud can refuse a body for a missing field. Mitigation: contract rule EC-1 repeats the check once with the named field.

### D-14 Make the access point lab call through the SDK, not the portal

- Alternatives: (a) Use the multi-site page. (b) Use one SDK call. (c) Change the page first.
- Chosen: (b).
- Reason: The save refuses the stable word for access points (RC-41, RC-42, RC-43). The page cannot send the checked word.
- Risk: Warning: an SDK call bypasses the portal write gate. A wrong target can change a production device. Mitigation: D-18 limits targets to lab devices.

### D-15 Correct parity rows C17 and C21 in the first code change, before any lab answer

- Alternatives: (a) Wait for the lab answers. (b) Correct the rows now.
- Chosen: (b).
- Reason: Row C17 claims access point parity while the save refuses the stable word (RC-42, RC-98, RC-99). Row C21 cites an absent multi-site path while the control exists (RC-45, RC-101, RC-102).
- Risk: The fixture test expectations change. Mitigation: T017 runs the parity page test.

### D-16 Keep the needs-human-review label and add in-progress at claim time

- Alternatives: (a) Remove needs-human-review. (b) Keep needs-human-review and add in-progress.
- Chosen: (b).
- Reason: The issue label marks a review for a destructive operation (gh label data). The issue claims firmware writes.
- Risk: None significant. The orchestrator applies the label change.

### D-17 Size the work M

- Alternatives: (a) S for documentation only. (b) L for both branches with live work. (c) M.
- Chosen: (c).
- Reason: Each gated branch changes about ten repository files in two classes (plan change map). The lab work stays outside the repository.
- Risk: The size changes after the lab answers. Mitigation: T011 to T015 select one branch each.

### D-18 HUMAN-DECISION-REQUIRED: select the lab organization, the lab devices, and the credential source

- Alternatives: (a) The owner uses a personal account token in the owner session. (b) The owner uses a token scoped to the lab organization in the owner session only. (c) The agent requests a token.
- Chosen: (b). Recommended option: (b).
- Reason: Credential policy and the lab target decide whether a write reaches a production device. Section 6 of the brief reserves these choices for a human.
- Risk: The lab checks wait for the owner. Mitigation: T005 names the choice and the recommendation.

## Sources

1. Repository rules: AGENTS.md (RC-01, RC-02), .github/copilot-instructions.md (RC-03 to RC-09), .specify/memory/constitution.md (RC-10 to RC-12).
2. Spec Kit templates read in full: spec-template.md, plan-template.md, tasks-template.md, checklist-template.md under .specify/templates. They set the heading shape of this record.
3. Route calculation: .specify/scripts/powershell/spec-route.ps1 (RC-13 to RC-15). The script was read, not run.
4. Reference record shape: specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv (RC-16). Its layout was copied. Its content was not copied.
5. Legacy research: specs/3383-multisite-advanced-controls/research.md (RC-17, RC-18).
6. GitHub reads: issue #3392, PR #3391, issue #3383, issues #3388 to #3390, and commit e0dc054d74e0a53c074c8b08158f105eb7c08fc0. Each read used the gh command only.
7. Mist contract: documentation/mist-api-openapi31yaml.yaml (RC-60 to RC-78), documentation/mist-api-openapi31json.json (RC-79), and documentation/api/utilities (RC-80 to RC-83).
8. SDK: installed mistapi 0.64.1 under .venv (RC-113 to RC-120). The record uses local paths and no src/mistapi path.
9. Skills loaded: juniper-hw-ssr400, which routes SSR software upgrades to juniper-ssr-wan-edge. Its answer rules hold no channel rule. Skill juniper-ssr-wan-edge covers SSR design. Its file 06-release-market-architecture/01-ssr-60-upgrade-changes-caveats.md holds no channel, stable, beta, or alpha text.
10. The agent fetched no web source. The record holds no upstream URL.

## Unverified

1. The cloud answer for the stable word and for each channel value. Reason: only the owner can run these lab checks.
2. The field name that a job read uses for the resolved build. Reason: the response schemas of the job reads were not read in this run.
3. Absence of ORG_UPGRADE_WRITES_ENABLED from documentation/operator-guide.md. Reason: the search ran on the local copy only, not on main.
4. The test quality ratchet files .github/test-quality-config.toml and .github/test-quality-baseline.json. Reason: they are not needed for this record. T-LOCAL-GATES reads them.
5. Whether CLAUDE.md exists. Reason: the STE row in RC-06 names it. The existence check was not run.
6. Live status of the single-site stable build for access points. Reason: PR #3391 states that no live run covered the multi-site route. The single-site live status was not verified.
7. The upstream Juniper API pages that mistapi docstrings name. Reason: the agent fetched no web source.
