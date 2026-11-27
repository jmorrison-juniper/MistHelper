# Research: Converter Parity Evidence Gate

## Evidence Boundary

| Evidence | Value |
| --- | --- |
| MistHelper main commit | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, committed 2026-11-26T07:15:01Z |
| Remote tree | `git/trees/main?recursive=1` returned 11404 entries. `truncated` is false |
| Upstream source revision | `d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c` (MistCiscoConfigConverter) |
| Installed SDK | mistapi 0.64.1 in `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` |
| Parity record | PR #4596, merged 2026-11-13T09:41:52Z, at `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/` |
| Legacy record for issue 4649 | None. The route folder is absent on main (R53). Local search of `specs\` found no `4649-` folder |

Each remote check reads the file body from main with `contents/<path>?ref=main`, decodes the base64 text, and records the line. Blob SHAs come from the tree.

## GitHub State

These states come from read-only `gh` calls. They are not repository content, so they do not appear in the remote table.

| Item | State | Note |
| --- | --- | --- |
| Issue #4649 | OPEN | Created 2026-11-07T16:19:28Z. Labels: feature, web-portal |
| Issue #4224 | OPEN | Parent. Integrate Mist Cisco config converter |
| Issue #4632 | CLOSED | Reproduce the offline Cisco DNS converter baseline |
| Issue #4633 | CLOSED | Record implementation ownership and handover gates |
| Issue #4634 | OPEN | Verify Mist API contracts for Cisco converter mappings |
| Issue #4635 | OPEN | Resolve Cisco converter licensing and authorship decisions. Prerequisite |
| Issues #4636 to #4647 | OPEN | Program issues for the parity tasks (see decision D-12) |
| Issue #4648 | OPEN | Verify converter privacy and integrate with the shared portal. Prerequisite |
| PR #4596 | MERGED | docs(spec): record Cisco converter parity readiness. Source of the parity record |
| Issue #4649 links | None | `gh pr list --search 4649` returned no pull request |

## Remote Verification Table

Result values: `present` means the claim holds on main. `absent` means the claimed item is missing on main. `stale` means main contradicts the claim. The blob SHA for a folder, a commit, or a test directory is `not-a-blob`. The blob SHA for a third-party package is `not-in-repository`. Line 0 means that the check covers existence only.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | Parity spec status is Specified, and cloud use is not approved | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 7 |
| R02 | Parity spec lists requirement FR-032 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 138 |
| R03 | Parity tasks hold 33 unchecked tasks. T001 is at line 28 and T033 is at line 114 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 28 |
| R04 | Parity dependency row for T032 is at line 156. Row for T033 at line 157 depends on T002 and T032 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 156 |
| R05 | Parity research lists comparison rows C01 at line 85 and C40 at line 124 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md` | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 85 |
| R06 | Parity research states that the source has 24 observed route decorators | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md` | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 128 |
| R07 | Parity research holds eight unchecked readiness boxes, lines 186 to 193 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md` | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 186 |
| R08 | Parity plan gate table lists G1 to G5 at lines 125 to 129. Note on T004 is at line 136 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md` | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 125 |
| R09 | Parity analysis says all 33 future tasks remain unchecked (line 13). Validation section at line 90. deleteOrgServicePolicy stays undecided at line 227 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md` | main | a08601943e89b95af5ebe9530c0d8b9bb47459ab | present | 13 |
| R10 | Parity cloud contract lists 21 candidate write rows (lines 57 to 77). Payload and failure contracts are pending (line 11) | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md` | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 57 |
| R11 | Parity portal contract preserves converter routes (line 5), requires a T032 handover (line 26), and records no user authentication (line 28) | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md` | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 5 |
| R12 | Issue 4224 plan states Python 3.13 (line 15). Main requires Python 3.15 (R14) | `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/plan.md` | main | 9c3fdacc929850e1ed923b248f1dc6520aa01fdd | stale | 15 |
| R13 | Issue 4224 leaves T015 unchecked at line 51. T009, T018, and T027 are unchecked at lines 42, 66, and 85 | `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/tasks.md` | main | fcdff941b5dfd214ae882be77d26c17ec903e8d5 | present | 51 |
| R14 | Copilot instructions require Python 3.15 or newer | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| R15 | Copilot instructions hold the Local gates section (line 50), the Tests row (line 61), and the STE row (line 74) | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R16 | Copilot instructions require managed roots for new records (line 159) and five children or fewer (line 167) | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R17 | Copilot instructions require a fragment only for a change that a user sees (line 451) | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| R18 | Constitution requires five children or fewer (line 40) and managed roots for `specs/` records (line 57) | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| R19 | Constitution holds the deployment pipeline (line 143) and the rule that each change adds one fragment (line 409) | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
| R20 | AGENTS.md requires the STE gate for each Markdown file (line 340) and a specification for a change that touches three or more files (line 348) | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| R21 | `requirements.txt` pins `mistapi==0.64.1` | `requirements.txt` | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R22 | `spec-route.ps1` sets base 5 (line 17) and defines `Resolve-SpecFeaturePath` (line 34) | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R23 | Guard test `test_process_folder_structure.py` exists | `tests/guardrails/test_process_folder_structure.py` | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| R24 | Guard test `test_spec_route_contract.py` defines `test_radix_route_is_stable` at line 45 | `tests/guardrails/test_spec_route_contract.py` | main | b174399ad5f23f4844dc442954bf203be07342f3 | present | 45 |
| R25 | Converter package `__init__.py` holds the offline IOS DNS converter docstring | `src/interfaces/portals/cisco_config_converter/__init__.py` | main | 5e34b005c2ae54d3f2a766dd8ab0be7ceab40a7e | present | 1 |
| R26 | `conversion.py` defines `IOSDnsConverter` (line 11) and converts only global IPv4 name-server commands (line 26). No syslog, SNMP, NTP, DHCP, VLAN, BGP, or VRF text | `src/interfaces/portals/cisco_config_converter/conversion.py` | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 11 |
| R27 | `routes.py` defines the blueprint (line 49), page (68), preview (73), review (89), export (94), and CSRF registration check (103). No status, discovery, display, apply, backup, or administration route | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 49 |
| R28 | `models.py` holds five top-level classes at lines 13, 21, 29, 38, and 84. Source kind allows standalone and spoke only (line 51). UTF-8 decoding at line 76. Session digest at line 96 | `src/interfaces/portals/cisco_config_converter/models.py` | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 13 |
| R29 | `converter.html` holds the file input (line 11) and the role options standalone (line 16) and spoke (line 17). No Branch, Hub, SRX, or SSR text | `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 11 |
| R30 | `converter.html` holds the status region (line 21), the Review proposal button (line 23), and the Export reviewed JSON button (line 24) | `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 23 |
| R31 | `converter.js` posts to `/cisco-config-converter/preview` (line 32) and sends `X-CSRFToken` (line 56). No localStorage or sessionStorage text | `src/interfaces/portals/cisco_config_converter/presentation/converter.js` | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 32 |
| R32 | Integration `test_routes.py` defines `test_complete_offline_journey` (line 60) and the review rejection test (line 80). It holds ten test functions | `tests/integration/web_portal/cisco_config_converter/test_routes.py` | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 60 |
| R33 | Unit test file defines nine test functions and lists the hub template type as refused (line 39) | `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 39 |
| R34 | E2E smoke test defines `TestCiscoOfflinePreview` (line 23) and states that shared registration remains blocked (line 24) | `tests/e2e/web_portal/test_portal_smoke.py` | main | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 23 |
| R35 | Parity unit test path `tests/unit/gateway/overrides/test_cisco_config_converter.py` is absent on main | `tests/unit/gateway/overrides/test_cisco_config_converter.py` | main | not-a-blob | absent | 0 |
| R36 | Parity contract folder `tests/contract/cisco_config_converter/` is absent on main | `tests/contract/cisco_config_converter` | main | not-a-blob | absent | 0 |
| R37 | Parity browser test `tests/e2e/web_portal/test_cisco_parity.py` is absent on main | `tests/e2e/web_portal/test_cisco_parity.py` | main | not-a-blob | absent | 0 |
| R38 | Parity state package `src/interfaces/portals/cisco_config_converter/state/` is absent on main | `src/interfaces/portals/cisco_config_converter/state` | main | not-a-blob | absent | 0 |
| R39 | Feature test folder holds two children, `__init__.py` and `test_routes.py`. Parity file `test_parity.py` is absent | `tests/integration/web_portal/cisco_config_converter` | main | not-a-blob | present | 0 |
| R40 | Converter package root holds five children: `__init__.py`, `conversion.py`, `models.py`, `presentation`, and `routes.py` | `src/interfaces/portals/cisco_config_converter` | main | not-a-blob | present | 0 |
| R41 | `web_portal/app.py` holds zero cisco or converter matches. Registration function starts at line 182 and registers nine blueprints (lines 200 to 235) | `web_portal/app.py` | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 182 |
| R42 | `web_portal/templates/base.html` holds zero cisco or converter matches. Navbar at line 35. Theme stylesheet link at line 15 | `web_portal/templates/base.html` | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | 35 |
| R43 | `config.py` states that the portal has no user authentication (line 12) | `web_portal/services/config.py` | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 12 |
| R44 | `config.py` sets the secret from `PORTAL_SECRET_KEY` or a random `uuid4` fallback (line 113) | `web_portal/services/config.py` | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| R45 | `deploy/.env.example` warns that the portal has no user authentication (line 155) | `deploy/.env.example` | main | 7137364423308485be734a391798d85c6a37eaf4 | present | 155 |
| R46 | `compose.yml` checks readiness on `/ready` (line 169) | `compose.yml` | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 169 |
| R47 | `output_scan.py` skips the firmware `BACKUP_DIRECTORY` as private (line 85) | `web_portal/services/output_scan.py` | main | bf97eb8f0e92a51ac2b13b2a5922359321b54bc5 | present | 85 |
| R48 | `data_browser.py` refuses access to `BACKUP_DIRECTORY` (line 154) | `web_portal/services/data_browser.py` | main | 247d411105a7af1ed54458418630626182494ffe | present | 154 |
| R49 | Upstream LICENSE at `d9be92f9` declares Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0) at line 1 | `LICENSE` in MistCiscoConfigConverter | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | e9ae5eff92457c2372db3be30a3d99166aeee547 | present | 1 |
| R50 | Upstream commit `d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c` exists in MistCiscoConfigConverter | `commits/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c` in MistCiscoConfigConverter | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | not-a-blob | present | 0 |
| R51 | Upstream `app.py` at `d9be92f9` holds 24 route decorators, first at line 1118 and last at line 3703 | `app.py` in MistCiscoConfigConverter | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | 703d3b38f03de44a41f6e22f1eb2ea6da4814a5b | present | 1118 |
| R52 | Upstream `tests` directory at `d9be92f9` holds eight test files | `tests` in MistCiscoConfigConverter | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | not-a-blob | present | 0 |
| R53 | Route folder for issue 4649 (`specs/numbered/0/0/1/2/2/0/4/4`) is absent on main, so no legacy record exists | `specs/numbered/0/0/1/2/2/0/4/4` | main | not-a-blob | absent | 0 |
| R54 | Route folder for record 4636 (`specs/numbered/0/0/1/2/2/0/2/1`) is absent on main | `specs/numbered/0/0/1/2/2/0/2/1` | main | not-a-blob | absent | 0 |
| R55 | OpenAPI operation `createOrgSite` (POST `/api/v1/orgs/{org_id}/sites`) is at line 20047 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20047 |
| R56 | OpenAPI operation `updateSiteInfo` (PUT `/api/v1/sites/{site_id}`) is at line 26004 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 26004 |
| R57 | OpenAPI operation `updateOrgInventoryAssignment` (PUT `/api/v1/orgs/{org_id}/inventory`) is at line 10800 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10800 |
| R58 | OpenAPI operation `updateSiteDevice` (PUT `/api/v1/sites/{site_id}/devices/{device_id}`) is at line 29076 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 29076 |
| R59 | OpenAPI gateway template operations: create at line 9764, delete at line 9909, update at line 9951 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9764 |
| R60 | OpenAPI device profile operations: create at line 7988, delete at line 8144, update at line 8187, assign at line 8370, unassign at line 8405 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 7988 |
| R61 | OpenAPI operation `updateSiteSettings` (PUT `/api/v1/sites/{site_id}/setting`) is at line 37086 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 37086 |
| R62 | OpenAPI network operations: create at line 15161, delete at line 15279, update at line 15322 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15161 |
| R63 | OpenAPI service operations: create at line 18527, delete at line 18566, update at line 18611 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18527 |
| R64 | OpenAPI service policy operations: create at line 18378, delete (`deleteOrgServicePolicy`) at line 18413, update at line 18458 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18378 |
| R65 | OpenAPI operation `listDeviceModels` (GET `/api/v1/const/device_models`) is at line 1863 | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 1863 |
| R66 | Installed mistapi module `api/v1/orgs/sites.py` defines `createOrgSite` at line 58 | `.venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py` | mistapi 0.64.1 installed | not-in-repository | present | 58 |
| R67 | Installed mistapi module `api/v1/sites/sites.py` defines `updateSiteInfo` at line 67 | `.venv\Lib\site-packages\mistapi\api\v1\sites\sites.py` | mistapi 0.64.1 installed | not-in-repository | present | 67 |
| R68 | Installed mistapi module `api/v1/orgs/inventory.py` defines `updateOrgInventoryAssignment` at line 139 | `.venv\Lib\site-packages\mistapi\api\v1\orgs\inventory.py` | mistapi 0.64.1 installed | not-in-repository | present | 139 |
| R69 | Installed mistapi module `api/v1/sites/devices.py` defines `updateSiteDevice` at line 1478 | `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py` | mistapi 0.64.1 installed | not-in-repository | present | 1478 |
| R70 | Installed mistapi module `api/v1/orgs/gatewaytemplates.py` defines `createOrgGatewayTemplate` (58), `deleteOrgGatewayTemplate` (117), and `updateOrgGatewayTemplate` (145) | `.venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py` | mistapi 0.64.1 installed | not-in-repository | present | 58 |
| R71 | Installed mistapi module `api/v1/orgs/deviceprofiles.py` defines five device profile functions at lines 63, 122, 150, 182, and 214 | `.venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py` | mistapi 0.64.1 installed | not-in-repository | present | 63 |
| R72 | Installed mistapi module `api/v1/sites/setting.py` defines `updateSiteSettings` at line 42 | `.venv\Lib\site-packages\mistapi\api\v1\sites\setting.py` | mistapi 0.64.1 installed | not-in-repository | present | 42 |
| R73 | Installed mistapi module `api/v1/orgs/networks.py` defines `createOrgNetwork` (58), `deleteOrgNetwork` (117), and `updateOrgNetwork` (145) | `.venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py` | mistapi 0.64.1 installed | not-in-repository | present | 58 |
| R74 | Installed mistapi module `api/v1/orgs/services.py` defines `createOrgService` (58), `deleteOrgService` (117), and `updateOrgService` (145) | `.venv\Lib\site-packages\mistapi\api\v1\orgs\services.py` | mistapi 0.64.1 installed | not-in-repository | present | 58 |
| R75 | Installed mistapi module `api/v1/orgs/servicepolicies.py` defines `createOrgServicePolicy` (58), `deleteOrgServicePolicy` (117), and `updateOrgServicePolicy` (145) | `.venv\Lib\site-packages\mistapi\api\v1\orgs\servicepolicies.py` | mistapi 0.64.1 installed | not-in-repository | present | 58 |
| R76 | Installed mistapi module `api/v1/const/device_models.py` defines `listDeviceModels` at line 17 | `.venv\Lib\site-packages\mistapi\api\v1\const\device_models.py` | mistapi 0.64.1 installed | not-in-repository | present | 17 |
| R77 | Installed distribution folder is `mistapi-0.64.1.dist-info` | `.venv\Lib\site-packages\mistapi-0.64.1.dist-info` | mistapi 0.64.1 installed | not-in-repository | present | 0 |

## Parity Task Status

The status rule is decision D-17. `verified-present` needs a passing check. This record has no passing parity check, so no parity task is verified-present.

| Parity task | Status | Remote checks | Evidence summary |
| --- | --- | --- | --- |
| T001 | partial | R03, R07 | Offline scope came from closed issue #4633. The handover box at line 187 is unchecked (R07). |
| T002 | absent | R07 | The legal box at line 186 is unchecked. Issue #4635 is OPEN. |
| T003 | partial | R10, R55 to R77 | 22 operation IDs and SDK signatures exist. Payload evidence is pending (R10, line 11). |
| T004 | absent | R08 | Plan note at line 136 only. No child-count inventory and no replacement paths. |
| T005 | partial | R09 | Baseline results are recorded for earlier revisions (line 90). |
| T006 | partial | R28, R36, R38 | `models.py` holds five classes. Approval, operation, and backup types are absent. Test folder absent. |
| T007 | absent | R36 | `tests/contract/cisco_config_converter/test_input.py` is absent. |
| T008 | partial | R27, R29 | Transient upload exists (R29, line 11). Contained catalog and private prepopulation are absent (R27). |
| T009 | absent | R27, R36 | No parser review tests and no display route. |
| T010 | absent | R27, R29 | No display route. No sectioned review in `converter.html`. |
| T011 | absent | R36 | Hardware contract test file is absent. |
| T012 | partial | R26, R29 | Standalone and spoke selection exist (R29). No SRX, SSR, or port mapping (R26). |
| T013 | absent | R26, R36 | DNS-only conversion (R26). Conversion contract test file is absent. |
| T014 | partial | R26 | Global IPv4 DNS conversion only. |
| T015 | absent | R26, R36 | No syslog, SNMP, or management mapping. Contract test file is absent. |
| T016 | absent | R26 | No management mapping in `conversion.py`. |
| T017 | partial | R32, R39 | Export and review tests exist (R32). Proposal test file `test_proposals.py` is absent (R39). |
| T018 | partial | R27, R30 | Review binding and export exist. Structured and versioned operations are absent. |
| T019 | absent | R27, R36 | No status or discovery route and no discovery tests. |
| T020 | absent | R27 | No status, site, or gateway route. |
| T021 | absent | R27, R36 | No apply route and no apply tests. |
| T022 | absent | R27, R30 | No apply route. The review button exports only (R30). |
| T023 | absent | R36 | No backup tests. |
| T024 | absent | R27 | No backup route. |
| T025 | absent | R27, R36 | No administration route and no administration tests. |
| T026 | absent | R27 | No administration route. |
| T027 | absent | R36 | No recovery tests. |
| T028 | absent | R27 | No restore route. |
| T029 | absent | R37 | Browser test file is absent. |
| T030 | partial | R29, R31, R42 | Isolated presentation exists (R29, R31). No parity card or host theme mapping. Not registered in the portal (R42). |
| T031 | absent | R39 | Integration parity test file is absent. |
| T032 | absent | R41, R42 | No converter registration in `app.py` (R41). No converter navigation in `base.html` (R42). |
| T033 | partial | R05, R09 | Comparison and analysis exist from PR #4596. Refresh with row-level evidence is absent. |

Summary: 11 partial, 22 absent, 0 verified-present.

## Comparison Register Baseline

This table is the baseline for the register that parity T005 refreshes. Every row is open. Remaining tasks are parity tasks. Gate IDs come from the gate register below.

| Row | Current state on main | Remote checks | Required check | Disposition | Owner decision | Parity task | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | Missing. Upload only | R27, R29 | List only private contained supported files | open | none | T007, T008 | G4 |
| C02 | Partial. Transient upload exists | R27, R29 | Stored selection and drag and drop give the same validated input | open | none | T007, T008 | G1 |
| C03 | Missing. Proposal JSON only | R27, R30 | Show sectioned observations without conversion or cloud calls | open | none | T009, T010 | none |
| C04 | Partial. Standalone and spoke only | R28, R29 | Exercise three explicit roles with no inferred site creation | open | none | T011, T012 | G2 |
| C05 | Missing. No hardware controls | R29 | Exercise both families with each role | open | none | T011, T012 | G2 |
| C06 | Unsupported. DNS-only conversion | R26 | Verify model inventory and explicit valid port assignments | open | none | T011, T012 | G2 |
| C07 | Unsupported. No identity or location parser | R26 | Inspect identity and location without automatic cloud creation | open | none | T009, T010 | none |
| C08 | Unsupported. DNS-only conversion | R26 | Test ambiguity, missing ports, subinterfaces, speed, and VLAN ranges | open | none | T013, T014 | G2 |
| C09 | Unsupported. DNS-only conversion | R26 | Test valid ranges, overlaps, exclusions, and invalid masks | open | none | T013, T014 | G2 |
| C10 | Unsupported. DNS-only conversion | R26 | Preserve routing intent or show explicit unresolved items | open | none | T013, T014 | G2 |
| C11 | Implemented in the offline blueprint only | R25, R26 | Retain unique addresses and reject contextual or malformed directives | open | none | T005, T013 | G2 |
| C12 | Unsupported except C11 | R26 | Validate inheritance, variable resolution, and unresolved references | open | none | T013, T014 | G2 |
| C13 | Unsupported. DNS-only conversion | R26 | Verify destination object and avoid secret or location disclosure | open | none | T015, T016 | G2 |
| C14 | Unsupported. Values omitted | R26, R44 | Review identity intent with no decoded secrets or hash recovery | open | none | T015, T016 | G4 |
| C15 | Unsupported. Parser families are not proof of conversion | R26 | Review each family and separate display-only from verified conversion | open | none | T009, T015, T016 | G2 |
| C16 | Unsupported. Source families include cellular and HSRP parsing | R26 | Show observations and explicit hardware-specific limits | open | none | T009, T015, T016 | G2 |
| C17 | Unsupported. Source documents a conversion gap | R26 | Show display-only limits and generate no raw device commands | open | none | T015, T016 | G4 |
| C18 | Partial. Reviewed DNS JSON export exists | R27, R30 | Show structured changes, omissions, object identities, and exact export | open | none | T017, T018 | none |
| C19 | Implemented in the offline blueprint only | R31, R32 | Keep local inspection available and mark checks unavailable | open | none | T005, T019, T020 | none |
| C20 | Missing in the converter | R27 | Separate unavailable, denied, failed, pending, and verified states | open | none | T019, T020 | G2 |
| C21 | Missing in the converter | R27 | Use stable IDs and separate empty inventory from failed lookup | open | none | T019, T020 | G2 |
| C22 | Requires approval and contract evidence. No converter write path | R10, R27, R55 to R65 | Verify role and object contracts, inheritance, and preservation | open | none | T003, T021, T022 | G2, G4 |
| C23 | Missing. The review button exports only | R27, R30 | Exact APPLY, current scope, cancel reset, and zero refused writes | open | none | T021, T022 | G4, G5 |
| C24 | Requires approval and contract evidence. Route existence proves no safety | R10, R27 | Test duplicate submission, stale state, 429, timeout, and unknown results | open | none | T021, T022 | G2, G5 |
| C25 | Missing in the converter | R27 | Hidden by default and denied server-side without permission | open | none | T025, T026 | G4 |
| C26 | Missing in the converter | R27 | Complete paginated private backups with manifests and UTC timestamps | open | none | T023, T024 | G2, G4 |
| C27 | Missing in the converter | R27 | List only contained verified backups in the correct object family | open | none | T023, T024 | G4 |
| C28 | Requires approval and contract evidence. No recovery path | R10, R27 | Resolve name conflicts and verify each update or create result | open | none | T027, T028 | G2, G4 |
| C29 | Requires approval and contract evidence. No converter path | R10, R62, R63, R64 | Exact reviewed object scope, backup, two confirmations, and refusal tests | open | none | T025, T026 | G4 |
| C30 | Requires approval and contract evidence. No converter path | R10, R60 | Preserve unrelated references and require fresh scope approval | open | none | T025, T026 | G4 |
| C31 | Missing. Source gives no atomic rollback guarantee | R27 | Reconcile each result and restore only approved recorded changes | open | none | T027, T028 | G2, G4 |
| C32 | Partial. Theme link exists. No converter card | R29, R42 | Independently author a centered card in the real portal shell | open | none | T029, T030 | G1, GV |
| C33 | Partial. Preformatted proposal and two buttons | R30 | Distinct input review, change review, confirmation, and cancel states | open | none | T017, T018, T029, T030 | G1 |
| C34 | Partial. Host theme configuration exists | R42 | Map pink, red, neon, and green intentions to approved host themes | open | none | T029, T030 | GV |
| C35 | Partial. Status text in the isolated page | R29 | Test focus, contrast, narrow screens, stale responses, and recovery | open | none | T029, T030 | GV |
| C36 | Partial. Shared health route not verified. Converter not registered | R41, R46 | Preserve existing health and service ownership without another stack | open | none | T031, T032 | G3 |
| C37 | Partial. Upload validation exists | R28, R29 | Test exact bounds, symlinks, invalid text, malformed masks, and banners | open | none | T007, T009, T031 | none |
| C38 | Partial. Session stores digests | R28, R44 | Prove no secrets in richer review, backups, browser state, or logs | open | none | T006, T015, T031 | none |
| C39 | Partial. Unit, route, and isolated browser tests exist | R32, R33, R34 | Cover each observed category with original fixtures and negative tests | open | none | T031, T032 | G1 |
| C40 | Requires approval. Observation only | R49, R50 | Obtain legal review before reuse and audit independent authorship | open | none | T001, T002, T033 | G1 |

## Gate Register

Gate status values are `open` and `passed`. A gate passes only with a decision ID and a UTC date. No gate passes in this record. Gate G5 applies to each cloud write at run time. The register records G5 as passed only when its typed-confirmation and permission controls exist with tests.

| Gate | Scope | Status | Owner | Decision ID | Evidence | Blocked work |
| --- | --- | --- | --- | --- | --- | --- |
| G1 Legal | Reuse, independent authorship, and distribution | open | Legal and repository owners | none | R07 (line 186), R49 | Source reuse and release |
| G2 API | Field, schema, role, model, signature, response, and failure fixtures | open | API owners | none | R10, R55 to R77 | Each unverified mapping and each write |
| G3 Integration owner | Handover for `web_portal/app.py` and `web_portal/templates/base.html` | open | Integration owner | none | R07 (line 187), R41, R42 | Portal and shared-service changes |
| G4 Cloud owner | Operation families, scope, retention, recovery, identity design, and private storage | open | Cloud owner | none | R07 (lines 188, 189, 191), R10, R43, R44 | Apply, restore, delete, unassign, and private storage |
| G5 Operator | Current scope, permission, typed word, and backup | open | Operator | none | R07 (line 192) | Each cloud write |
| GV Visual owner | Visual journeys and unsupported states | open | Visual owner | none | R07 (line 193), R29 | Visual acceptance |

Note: the parity plan lists G1 to G5 only. The storage box (line 191) maps to G4, and the visual box (line 193) maps to GV. See finding F-08.

## Decisions

Human decisions carry the marker HUMAN-DECISION-REQUIRED. All other decisions are made by this record.

| ID | Decision | Alternatives | Chosen option and reason | Risk | Human flag |
| --- | --- | --- | --- | --- | --- |
| D-1 | This record defines the closure method for parity T033 only. Implementation for T001 to T032 stays out of scope | (a) Implement the audit now. (b) Combine with parity T032 | Method only. The issue names T033 alone, and T032 needs an integration handover | The closure method may drift before T033 runs | No |
| D-2 | The register lives in the parity `design/research.md` table | (a) A new register file in this record. (b) A JSON file under `data/` | The parity file, because parity T033 names it. One source avoids a second table | Table edits can break the audit. The audit test guards the layout | No |
| D-3 | Dispositions are `accepted`, `unsupported-approved`, and `open` | (a) Binary accepted or open. (b) Five values including blocked and deferred | Three values. Blocked and deferred describe a reason, so the reason belongs in the remaining-task column | A reader may expect more states. The contract defines each value | No |
| D-4 | Evidence identity is repository path, blob SHA on main, and line from the decoded main file | (a) Local worktree. (b) Branch name | Main content. The brief truth order and the issue constraint on unlanded work require it | Remote evidence needs a refresh after each main commit | No |
| D-5 | The audit lives in `tests/integration/web_portal/cisco_config_converter/evidence/` | (a) `tests/guardrails/`, whose parent holds many children. (b) `tests/contract/cisco_config_converter/`, which overflows (F-03) | `evidence/`, a feature-owned nested package under constitution Principle I | Parity T017 and T031 can overflow the parent (F-04) | No |
| D-6 | The completion claim needs every row accepted or unsupported-approved, every gate passed, and every parity task verified-present | (a) Close on T033 execution alone. (b) Partial credit per row | The strict rule. The issue forbids inference from issue closure | The claim may stay refused for a long time | No |
| D-7 | Owners approve each unsupported row and each visual journey. The record names the GV gate for visual acceptance | (a) The agent proposes and records approval. (b) One batch approval for all rows | Per-row approval by an owner, with the limit text. Product priority belongs to the owner | Owner time limits the pace of closure. Recommended option: per-row approval with limit text | HUMAN-DECISION-REQUIRED |
| D-8 | Gate G1 blocks source reuse until a recorded legal decision exists. Authorship stays independent | (a) Allow reuse under CC BY-NC 4.0 with attribution. (b) License-compatible path chosen by the owner | No reuse without a recorded decision. R49 declares CC BY-NC 4.0. Recommended option: independent authorship and a legal decision | The converter schedule slips while legal review runs | HUMAN-DECISION-REQUIRED |
| D-9 | The converter guide waits for documentation ownership approval and gate G1 | (a) Write the guide now from observation. (b) Write the guide after implementation | Gated guide. The issue states the guide needs documentation approval. Recommended option: defer | Operators have no guide until approval | HUMAN-DECISION-REQUIRED |
| D-10 | Credential policy. The owner approves operator identity, server-side authorization, and whether `PORTAL_SECRET_KEY` is required | (a) Use the IP allowlist as authorization. (b) Identity provider chosen by the agent | The owner decides. R43 states that the portal has no user authentication. R44 shows a random fallback secret. Recommended option: authenticated operator identity before any write, and a required stable secret for production | Cloud apply stays blocked until the owner decides | HUMAN-DECISION-REQUIRED |
| D-11 | The pull request body uses `Closes #4649`, as the brief requires. A Caution line states that parity T033 stays partial | (a) `Refs #4649`, which keeps the issue open | `Closes`, because the brief requires the closing keyword for this record | Readers may read closure as parity completion. The Caution line and the summary mitigate this risk | No |
| D-12 | `depends_on_issues` lists the open program issues #4634 to #4648 | (a) Only #4635 and #4648, as the issue text names | The full open set. Parity T033 depends on T002 and T032 (R04). T032 depends on T001, T022, T028, T030, and T031 (line 156) | The list grows or shrinks as issues close | No |
| D-13 | Labels to add are `feature-spec` and `needs-human-review` | (a) Only `needs-human-review`, as record 4636 did | Both labels. Spec issues #4632 to #4635 carry `feature-spec`, and this record holds human decisions | None known | No |
| D-14 | No changelog fragment for this record | (a) Add `changelog.d/issue-4649-converter-parity-evidence.md`. (b) Add a fragment at completion | No fragment now. The change alters no user-visible behavior, as in PR #4596. Copilot instructions (R17) limit fragments to user-visible change | Constitution line 409 (R19) says each change adds a fragment (F-09) | No |
| D-15 | SDK baseline is mistapi 0.64.1 | (a) Accept any 0.64.x. (b) Pin a newer release | The 0.64.1 pin in `requirements.txt` (R21) and the installed distribution (R77) | A pin change invalidates R66 to R77 | No |
| D-16 | Size is M | (a) S for one file. (b) L for multi-file implementation | M. One register, one nested package, six gates, 13 tests, and 16 tasks | The implementation grows to L after gates pass | No |
| D-17 | Status rule. `partial` means a named deliverable exists in part. `absent` means none exists. `verified-present` needs a passing check | (a) Binary present or absent | Four values. The issue separates route presence from completion | Reviewers may disagree on `partial` | No |

## Sources

Local files read (paths relative to the repository `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`):

- `AGENTS.md` (full)
- `.github\copilot-instructions.md` (full, read in ranges)
- `.specify\memory\constitution.md` (full, read in ranges)
- `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`
- `documentation\quality-gates.md` (line 283, the STE command)
- `documentation\architecture.md` and `documentation\container-deployment.md` (search only). Both mention parity in the Docker and menu sense, not the converter
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` (section headings of `spec.md` and `tasks.md`)
- `specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter` (tasks and plan lines)
- `specs\live\0\0\0\1\2\1\3\3\2\1\4\2\1\4\1\3\0\20261105-170040-cisco-converter-full-parity` (spec, plan, tasks, analysis, research, contracts, data model, quickstart, checklist)
- `C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-drafts\4636` (tasks, `spec.md`, and the meta files `4636-STATUS.json` and `4636-summary.md`). This is the only related record in the draft folder
- `.venv\Lib\site-packages\mistapi` (read-only signature search) and `mistapi-0.64.1.dist-info`
- `documentation\mist-api-openapi31yaml.yaml` (local search. The remote blob has the same size, 4317370 bytes, and the same line numbers)
- `src\interfaces\portals\cisco_config_converter` (folder listing)

GitHub reads (read-only):

- `gh issue view` for #4224, #4632 to #4649
- `gh pr list --search 4649` and `gh pr view 4596`
- `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`
- `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`
- `gh api repos/jmorrison-juniper/MistHelper/git/blobs/b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`
- `gh api repos/jmorrison-juniper/MistHelper/commits/main`
- `gh api repos/jmorrison-juniper/MistCiscoConfigConverter/commits/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c`
- `gh api repos/jmorrison-juniper/MistCiscoConfigConverter/contents/LICENSE`, `app.py`, and `tests` at ref `d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c`

Web fetches: none. Skills: none loaded. This record makes no Juniper device behavior claim and no container behavior claim.

## Unverified

| ID | Claim | Reason it is unverified |
| --- | --- | --- |
| U1 | Parity row C36 states that the host `/health` route exists | This pass did not find `/health` text in `web_portal/app.py`. The route location was not searched elsewhere |
| U2 | PR #4226 merged the DNS component with the file set that the parity analysis lists | Recorded in the parity analysis. Not checked on GitHub in this pass |
| U3 | Parity row C32 names a magenta theme | The theme stylesheet link is verified (R42). The color is not verified |
| U4 | Source route-to-function mapping and parser family identifiers (parity S5 and S6) | The source route count is verified (R51). The contents are not compared |
| U5 | Source test bodies and fixtures (parity S7) | The file count is verified (R52). The bodies are not read, by design, because copied tests are prohibited |
| U6 | Legal effect of CC BY-NC 4.0 on reuse | Not a repository fact. Decision D-8 assigns it to a human owner |
| U7 | Documentation ownership approval for a converter guide | No approval record exists in the repository or in issue #4649 |
| U8 | Syslog placement statements in parity source document S4 conflict | Source document S4 was not read in this pass |
| U9 | Function-level counts for source test categories and route functions | Only the route count and the file count are verified |
| U10 | Recorded test counts (43, 20, and 74 passed) in the parity analysis | Not re-run. Brief rule 2 forbids test runs. Recorded as stale in finding F-07 |
