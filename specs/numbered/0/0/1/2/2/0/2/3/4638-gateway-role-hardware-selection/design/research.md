# Research: Add explicit gateway role and hardware selection

This record reads GitHub `main` through `gh api`. It reads local files only after their git blob SHA matched the remote blob SHA. The local SHA check used `git hash-object` on 20 files, and every hash matched. Line numbers for OpenAPI, guidance, and code files are taken from the remote content or from the matched local copy.

## Decisions

### D-1 Role vocabulary

- Alternatives: (A) keep `standalone` and `spoke`, which issue 4636 decision D-11 keeps for now. (B) add Branch, Hub, and Standalone beside the old values. (C) replace the old values with `branch`, `hub`, and `standalone`.
- Chosen: C. The role `standalone` keeps its value. The input `spoke` leaves the vocabulary.
- Reason: Full-parity FR-005 names Branch, Hub, and Standalone (spec line 111). Issue 4636 decision D-11 defers the contract change to tasks T011 and T012.
- Risk: A caller that sends `spoke` as the role receives HTTP 400.

### D-2 Retire the `type` form field

- Alternatives: (A) accept `type` beside `role`. (B) ignore `type` without a message. (C) return HTTP 400 that names the role field.
- Chosen: C.
- Reason: Full-parity portal contract line 16 says do not silently reinterpret existing names or types. Option A keeps two inputs for one concept.
- Risk: A script that posts `type` fails until it posts `role`.

### D-3 Branch stays blocked

- Alternatives: (A) map Branch to the `spoke` deployment type and report it verified. (B) withhold the deployment type and block review. (C) remove Branch from the form.
- Chosen: B. The page shows Branch. The proposal omits `gateway_template.type`. Blocker `role_unverified` stops review.
- Reason: No local text names Branch. The Mist API page that the pinned SDK cites is blocked for this agent (see Sources). Option A would certify an unverified mapping. Option C removes a role that full-parity FR-005 requires.
- Risk: Branch cannot reach review until issue 4634 records mapping evidence.

### D-4 Hub stays blocked

- Alternatives: (A) map Hub to `standalone` plus a VPN hub role. (B) map Hub to the `deviceprofile_gateway` object (OpenAPI line 77247). (C) withhold the deployment type and block review.
- Chosen: C. Blocker `role_without_deployment_type` stops review.
- Reason: The gateway deployment type enum names only `spoke` and `standalone` (OpenAPI lines 80788 to 80790). The VPN path role `hub` (line 80518) belongs to VPN configuration, which this issue excludes. The device profile networks field is not verified (UV-03).
- Risk: Hub stays unusable. Issue 4641 or a later record owns any Hub support.

### D-5 Eligibility rule

- Alternatives: (A) any cabling text that names a model. (B) an inventory sample plus complete, explicit WAN and LAN names. (C) SDK evidence only.
- Chosen: B.
- Reason: Full-parity mist contract line 90 requires current model inventory. The pinned SDK holds no SRX or SSR model enumeration (remote check R62). Option A admits models that appear only in cabling headings, such as SRX340 and SRX4100.
- Risk: Six models stay blocked until issue 4634 supplies inventory samples.

### D-6 HA and OOB ports excluded

- Alternatives: (A) allow every named port. (B) exclude each port with an HA, fxp0, or OOB role in local evidence. (C) exclude only the ports that the device model defaults list as HA.
- Chosen: B.
- Reason: A port with two roles creates a conflicting assignment. The standalone release uses no HA port. Cabling line 29726 states that `ge-0/0/0` becomes OOB after cluster enablement.
- Risk: `ge-0/0/0` cannot be a WAN port for SRX300 or SRX320 in this release.

### D-7 Named ports and closed ranges only

- Alternatives: (A) expand the open-ended range `ge-0/0/3-` to higher ports, using the SRX300 skill count of eight. (B) expand closed ranges and named ports only. (C) accept free-text port names.
- Chosen: B.
- Reason: The skill confirms the count of eight ports (skill sources below). It does not name ports 4 to 6. Free text cannot meet the verified-mapping rule.
- Risk: Some physical ports cannot be selected.

### D-8 SRX1500 blocked for conflicting evidence

- Alternatives: (A) select the node 0 names that both sections share. (B) block the model.
- Chosen: B. Blocker `model_evidence_conflict` stops review.
- Reason: Lines 29758 and 29784 name different cluster members for the same model. The record does not choose between them.
- Risk: SRX1500 stays unavailable until issue 4634 resolves the conflict.

### D-9 SSR blocked

- Alternatives: (A) reuse SRX port roles for SSR. (B) accept free-text SSR ports. (C) block every SSR row.
- Chosen: C. Blocker `port_evidence_absent` stops review for SSR120.
- Reason: No local line names SSR WAN or LAN roles. Option A assumes a mapping. Option B breaks the verified-mapping rule.
- Risk: No SSR gateway can reach review in this release.

### D-10 Stale rule by revision string

- Alternatives: (A) expire rows by date. (B) compare each row revision with `CURRENT_REVISION`. (C) fetch the live Mist catalog at run time.
- Chosen: B.
- Reason: The converter runs offline. Tests stay deterministic. A pin change forces a revision update.
- Risk: A pin change needs a manual revision update and a new review of each row.

### D-11 Review and export refuse blocked proposals

- Alternatives: (A) allow review with a warning. (B) refuse review with HTTP 409. (C) refuse preview.
- Chosen: B. Preview still shows every blocker.
- Reason: Issue 4638 says unresolved mappings cannot authorize a write. Option C hides the explanation.
- Risk: A blocked selection cannot produce an export.

### D-12 Test placement

- Alternatives: (A) `tests/contract/cisco_config_converter/test_hardware.py` as task T011 names. (B) `tests/integration/web_portal/cisco_config_converter/test_hardware.py`. (C) a new hardware test folder inside the integration folder.
- Chosen: B.
- Reason: `tests/contract/` already holds 17 children (remote check R18). Constitution Principle I forbids a new direct child there. Option C adds a folder without a gain in count.
- Risk: The integration folder reaches five children after issue 4640. Issue 4642 must not add a sixth child (analysis F-13).

### D-13 Offline operation and no apply path

- Alternatives: (A) call `listDeviceModels` during preview. (B) add an apply stub. (C) use local evidence, and add no apply path.
- Chosen: C.
- Reason: Full-parity spec line 147 says an available method does not prove a mapping. Issue 4634 says no live writes and no live discovery. Option A adds a network call to preview.
- Risk: The register can go stale until a person updates it.

### D-14 Code placement

- Alternatives: (A) add hardware classes to `conversion.py`. (B) add a root package named `hardware/`. (C) add `state/hardware.py`. (D) add `conversion/hardware/` after the `conversion/` package move.
- Chosen: D.
- Reason: Option A breaks the five-name and five-member limits (issue 4640 analysis E-1). Option B makes the converter root hold six children. Option C makes `state/` hold six children after issue 4636. Option D matches issue 4640 decisions D-1 and D-3.
- Risk: This record executes the move that issue 4640 decision D-1 plans. Issue 4640 must drop its own DNS move.

### D-15 Port value names

- Alternatives: (A) call the WAN or LAN value `role`, as issue 4640 text does. (B) call it `usage`, the term in the OpenAPI enum `gateway_port_usage` (line 80464). (C) call it `direction`.
- Chosen: B. The assignment keys are `mist_port`, `usage`, and `source_interface`.
- Reason: The word role names the gateway role in this issue. The OpenAPI uses the word usage for ports.
- Risk: Issue 4640 must use `usage` in its `PortAssignment` text. Issue 4640 also lists family in each assignment. This record keeps family on the selection (analysis F-10).

### D-16 The page lists blocked rows

- Alternatives: (A) hide blocked rows. (B) show each row with its blocker.
- Chosen: B.
- Reason: Full-parity SC-002 requires a verified proposal or an explicit unsupported decision for each combination.
- Risk: The model list is longer.

### D-17 VRF support is unsupported

- Alternatives: (A) set VRF support per row from the device model example. (B) leave VRF unsupported in every row. (C) defer the answer to issue 4640.
- Chosen: B.
- Reason: The device model example carries no VRF field. Issue 4640 open item U-7 asks for this answer. This record answers it for this release.
- Risk: VRF configuration stays unavailable.

### D-18 Human decisions

- Alternatives: (A) mark the Branch mapping as a human decision. (B) mark the Hub object as a human decision. (C) mark no decision.
- Chosen: C.
- Reason: The open items are evidence gaps. They are not licensing, legal text, data destruction, credential policy, or product priority. Issue 4634 closes them with evidence.
- Risk: None for this record.

## Remote Verification

Ref `main` applies to rows R01 to R57. Ref `local` applies to rows R58 to R62, which are third-party files outside the repository. Each row matches one entry in `_meta/4638-STATUS.json`.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | models.py limits source kind to standalone and spoke | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 51 |
| R02 | models.py holds the ReviewState digest binding | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 84 |
| R03 | conversion.py copies the source kind into the template type | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 19 |
| R04 | conversion.py known gap states that hardware mappings remain unsupported | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 27 |
| R05 | conversion.py IOSDnsConverter declares five methods | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 11 |
| R06 | routes.py reads the form field named type | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 126 |
| R07 | routes.py verifies review state before export | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 137 |
| R08 | converter.html limits the template type select to standalone and spoke | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 15 |
| R09 | converter.html has no role, family, model, or port control | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | absent | 0 |
| R10 | converter.js resets the proposal on input | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 12 |
| R11 | converter package root holds five direct children | src/interfaces/portals/cisco_config_converter | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| R12 | state package is absent on main | src/interfaces/portals/cisco_config_converter/state | main | none | absent | 0 |
| R13 | unit test expects hub to be refused | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 39 |
| R14 | unit test passes standalone as the kind argument | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 16 |
| R15 | integration preview helper posts the type field spoke | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 55 |
| R16 | integration test folder holds two direct children | tests/integration/web_portal/cisco_config_converter | main | 6538f20cdb454342a96e079a0e7678fb6baa7a42 | present | 0 |
| R17 | converter contract test folder is absent | tests/contract/cisco_config_converter | main | none | absent | 0 |
| R18 | tests/contract holds 17 direct children | tests/contract | main | 3e544ef7c55adf7c8a8010e6da3afc345b27d57e | present | 0 |
| R19 | tests/e2e holds five direct children | tests/e2e | main | 828f24a6106147d9263b550da13acfaa4866b3bf | present | 0 |
| R20 | tests/e2e/web_portal holds 32 direct children | tests/e2e/web_portal | main | 3d492d6e0bec7e4a76925d345c095dfa44bb813e | present | 0 |
| R21 | test_portal_smoke.py exists under tests/e2e/web_portal | tests/e2e/web_portal/test_portal_smoke.py | main | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 0 |
| R22 | nested package guard sets MAX_CHILDREN to five | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| R23 | nested package guard scans the src root only | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 16 |
| R24 | web_portal/app.py registers no converter blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 182 |
| R25 | ci.yml sets MYPY_PATHS with src/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R26 | ci.yml sets VULTURE_PATHS with src/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R27 | ci.yml sets PYDOCSTYLE_PATHS with src/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R28 | ci.yml sets INTERROGATE_PATHS with src/ | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R29 | copilot-instructions defines the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R30 | copilot-instructions requires web UI tests under tests/e2e | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 303 |
| R31 | copilot-instructions states the five-child rule for structural directories | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167 |
| R32 | constitution Principle I bars a direct child in a noncompliant parent | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 42 |
| R33 | constitution names mistapi as the sole Mist interface | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 279 |
| R34 | AGENTS.md requires an inline comment on each executable line | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| R35 | AGENTS.md requires a specification for changes that touch three or more files | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 347 |
| R36 | full-parity FR-005 names Branch, Hub, and Standalone | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 111 |
| R37 | full-parity FR-006 requires SRX or SSR with an explicit mapping | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 112 |
| R38 | full-parity T011 names tests/contract/cisco_config_converter/test_hardware.py | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 57 |
| R39 | full-parity T012 names converter.html, converter.js, and conversion.py | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 58 |
| R40 | full-parity portal contract states current types are spoke and standalone | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 7 |
| R41 | full-parity mist contract names Hub profile type as a role target | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 89 |
| R42 | parent 4224 record folder exists on main | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter | main | 2324c91a3e3067c6e0912b76807755fce992e8c1 | present | 0 |
| R43 | OpenAPI defines listDeviceModels at /api/v1/const/device_models | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 1859 |
| R44 | OpenAPI const_device_model discriminator maps gateway and switch schemas in reverse | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 75113 |
| R45 | OpenAPI defines gateway port default keys by interface role | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 75083 |
| R46 | OpenAPI SRX320 device model example lists WAN and LAN defaults | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 47223 |
| R47 | OpenAPI gateway_template_type enum lists spoke and standalone only | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80788 |
| R48 | OpenAPI gateway_port_usage enum lists wan and lan | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80464 |
| R49 | OpenAPI VPN path role enum lists hub | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80518 |
| R50 | OpenAPI inventory schema defines a model field | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 82192 |
| R51 | OpenAPI getOrgInventory operation exists | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 10660 |
| R52 | OpenAPI SRX300 device example reports model SRX300 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 48412 |
| R53 | OpenAPI SRX300 cabling names default WAN ports | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 29725 |
| R54 | OpenAPI SRX1500 cabling sections name different cluster members | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 29758 |
| R55 | OpenAPI SRX340, SRX345, and SRX380 cabling heading exists | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 29744 |
| R56 | OpenAPI SSR120 device search example reports model SSR120 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 50625 |
| R57 | OpenAPI deviceprofile_gateway schema exists as a Hub candidate | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 77247 |
| R58 | SDK getOrgInventory accepts a model parameter | .venv\Lib\site-packages\mistapi\api\v1\orgs\inventory.py | local | not-in-repository | present | 21 |
| R59 | SDK listOrgGatewayTemplates exists | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | local | not-in-repository | present | 17 |
| R60 | SDK listDeviceModels exists | .venv\Lib\site-packages\mistapi\api\v1\const\device_models.py | local | not-in-repository | present | 17 |
| R61 | SDK package mistapi 0.64.1 is installed | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local | not-in-repository | present | 0 |
| R62 | SDK contains no SRX or SSR model enumeration | .venv\Lib\site-packages\mistapi | local | not-in-repository | absent | 0 |

Row count: 62. Result counts: present 57, absent 5, partial 0, stale 0. Rows R09, R12, R17, R24, and R62 check a missing item, so their absent result is the expected finding.

## Sources

- Local guidance: `AGENTS.md` (blob `44a9afff`), `.github/copilot-instructions.md` (blob `f1ec2a46`), `.specify/memory/constitution.md` (blob `4584997a`), and the four templates under `.specify/templates/`.
- Local reference record: `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`, read for shape only. Spec headings include Clarifications, User Scenarios, Requirements, Mist Cloud Transport Requirements, Key Entities, Success Criteria, and Assumptions.
- Repository code and tests on `main` (remote rows R01 to R24).
- OpenAPI file `documentation/mist-api-openapi31yaml.yaml`, blob `b7fc2bfb`, read through the git blob API.
- Installed mistapi 0.64.1 at `.venv\Lib\site-packages\mistapi`. This path is local and outside the repository.
- Juniper skill `juniper-hw-srx300`, file `C:\Users\jmorrison\.copilot\skills\juniper-hw-srx300\01-platform-and-ports.md`. It states eight 1GbE network ports: six copper and two SFP. It states that `ge-0/0/0` is the WAN default used by first setup.
- Juniper Mist API page for listing gateway templates, cited by mistapi `gatewaytemplates.py` line 24: `https://www.juniper.net/documentation/us/en/software/mist/api/http/api/orgs/gateway-templates/list-org-gateway-templates`. The fetch failed. The tool reported a blocked address for the resolved host, so the page content is unavailable to this record.
- Legacy record search: `specs\` in the repository has no folder named `4638-*`. The PowerShell recursive search and the glob search both found none, so no legacy record was reused.
- Linked work: `gh pr list --search 4638` returned no pull request. Pull request 4596 appears only in the issue body.
- GitHub issues read with `gh issue view`: states for 4224 and 4632 to 4637, and bodies for 4634, 4637, and 4638.
- Drafts 4643, 4645, and 4648 were not read in full. This record does not use their decisions.
- Merged pull request 4596 with the full-parity task map (`mergedAt` 2026-11-13). Its record lives at `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`.
- Open pull requests read with `gh pr list`: 4890, 4889, 4888, 4887, 4886, 4813, and 4208. None touches the converter files. Pull request 4208 touches `web_portal/app.py` and `base.html`. This record does not touch those files.
- Sibling drafts under `spec-drafts`, local and not on `main`: 4636, 4640, 4641, 4642, 4644, 4646, and 4647.
- Draft 4636 files read: plan, spec, research, data model, and STATUS. Draft 4640 files read: plan, spec, analysis, research, and tasks.
- Drafts 4641, 4642, 4644, 4646, and 4647 were read in part, for the sections that name this issue.
- Changelog precedent: `changelog.d/pr-4226.md`, heading line 1.

## Unverified

Each item below stays unverified. The reason follows each item.

- UV-01 Branch maps to the `spoke` deployment type. No local text names Branch. The Mist page cited by the SDK is blocked for this agent.
- UV-02 Hub profile is a Mist object type. The only local text is the service policy description at OpenAPI line 901. No enum names it. The full-parity contract at line 89 asserts it.
- UV-03 The `networks` field of `deviceprofile_gateway` at line 77247 carries Hub topology. This record did not read the property semantics.
- UV-04 The `defaults` keys at OpenAPI lines 75083 to 75089 name port roles. The schema describes keys with examples only. Issue 4634 confirms the semantics.
- UV-05 The `ge-0/0/3-` range on SRX300 names higher LAN ports. The range is open-ended and this record does not expand it (D-7).
- UV-06 The SRX300 chassis has two SFP ports at `ge-0/0/6` and `ge-0/0/7`. The skill confirms two SFP ports and does not name them. Line 29725 names `ge-0/0/7` as SFP.
- UV-07 SRX300 and SRX320 appear as live inventory items. The examples at lines 48412 and 47236 are documentation examples. The offline rule forbids a live read.
- UV-08 Cabling-only models (SRX340, SRX345, SRX380, SRX550, SRX1600, and SRX4100) exist in live inventory. The cabling headings name them, and no inventory sample does.
- UV-09 SSR120 has WAN or LAN port roles. No local line names them.
- UV-10 VRF support exists for any model. No local line states it. Issue 4640 open item U-7 asks for it (D-17).
- UV-11 The name grammar covers every physical port name. The register uses `ge` and `xe` names only. `cl`, `vme`, and `irb` names are outside this release.
- UV-12 The discriminator mapping at OpenAPI lines 75113 to 75116 has an intended meaning. The text reverses the gateway and switch schemas. The record does not use the mapping and reports the defect (analysis F-05).
- UV-13 `cl-1/0/0` is a WAN candidate on SRX320. Line 47222 names it as LTE. The LTE port is out of scope.
- UV-14 The live Mist catalog matches the OpenAPI example for SRX320 port defaults. The example is a documentation example, and issue 4634 must confirm the match.
