# Research: Integrate Mist Cisco Config Converter

**Date**: 2026-11-26
**Feature**: [Spec](../spec.md)
**Issue**: #4224, "Integrate Mist Cisco config converter"
**Remote reference**: GitHub `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, committed 2026-11-26T07:15:01Z. The local checkout has the same HEAD.

## Method

- Issue facts came from `gh issue view 4224`. The issue has four comments, dated 2026-10-16, 2026-11-07, 2026-11-09, and 2026-11-13.
- Linked PRs came from `gh pr list --search 4224`. Each linked PR received one `gh pr view` read.
- A local search of `specs` for folders named `4224-*` found one folder, `specs\numbered\0\0\1\1\3\3\4\4\4224-cisco-config-converter`. Its nine files match the remote tree blob SHAs in R-01 to R-09. Reuse follows D-1 and D-2.
- The full `main` tree came from one call. The response listed 11,404 entries and was not truncated.
- Blob SHAs came from the contents API for each path. Line numbers came from decoded remote bodies.
- A local file counted as verified only when `git hash-object` returned the remote blob SHA.
- `web_fetch` failed for `github.com` and `raw.githubusercontent.com` with a blocked-address error. Every upstream read used `gh api`. The API URL is the recorded source for each upstream check.
- The pinned `mistapi` package was read from the local `.venv`. Its rows use the local path, and the blob column says so.
- No build, test, linter, package install, or repository script ran.

## Remote verification table

Each row is one check. Line 0 marks a path-only check. The table has 100 rows. The `remote_checks` array in `META_DIR\4224-STATUS.json` has the same 100 rows.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|---|---|---|---|---|---|---|
| R-01 | Legacy record: spec.md present | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md | main | 5e8b1bc162cbfe2e9a3d604420c42e670dd0cd97 | present | 0 |
| R-02 | Legacy record: plan.md present | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/plan.md | main | 9c3fdacc929850e1ed923b248f1dc6520aa01fdd | present | 0 |
| R-03 | Legacy record: tasks.md present | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/tasks.md | main | fcdff941b5dfd214ae882be77d26c17ec903e8d5 | present | 0 |
| R-04 | Legacy record: research.md present | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/research.md | main | 50bc18526b0c29d782566a32d8fc50fe7975c5a0 | present | 0 |
| R-05 | Legacy record: data-model.md present | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/data-model.md | main | 83c16de9a093db0e9526bafd08d0c8fc76ca6d48 | present | 0 |
| R-06 | Legacy record: quickstart.md present | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/quickstart.md | main | 47f2ab8233e4d5514b3fcc002db9414448299097 | present | 0 |
| R-07 | Legacy record: checklists/requirements.md present | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/checklists/requirements.md | main | 0ee7ecdabc9583ca8c3f4c40ec83b4da1d577a1f | present | 0 |
| R-08 | Legacy record: contracts/mist-apply.md present | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/mist-apply.md | main | fbb549f8077f9d73773e7ca1ff8c5d3a3878615d | present | 0 |
| R-09 | Legacy record: contracts/portal.md present | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/portal.md | main | 774b487ab32ae1417368ba79930e7eac0b3dad43 | present | 0 |
| R-10 | Legacy claim: converter package __init__.py present | src/interfaces/portals/cisco_config_converter/__init__.py | main | 5e34b005c2ae54d3f2a766dd8ab0be7ceab40a7e | present | 0 |
| R-11 | Legacy claim: conversion.py defines IOSDnsConverter | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 11 |
| R-12 | Legacy claim: models.py defines SourceConfiguration | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 38 |
| R-13 | Legacy claim: routes.py defines ConverterRoutes | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 45 |
| R-14 | Legacy claim: converter.html carries stable test IDs | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 4 |
| R-15 | Legacy claim: converter.js sends the CSRF header | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 56 |
| R-16 | Legacy claim: unit test at tests/unit/gateway/overrides (path absent, file moved) | tests/unit/gateway/overrides/test_cisco_config_converter.py | main | none at this path | stale | 0 |
| R-17 | Unit test present at the moved path | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 5 |
| R-18 | Legacy claim: integration test_routes.py present | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 12 |
| R-19 | Legacy claim: test_sdk_contract.py listed in the plan | tests/integration/web_portal/cisco_config_converter/test_sdk_contract.py | main | none | absent | 0 |
| R-20 | Legacy claim: isolated browser journey class present | tests/e2e/web_portal/test_portal_smoke.py | main | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 23 |
| R-21 | Legacy claim: PR fragment present | changelog.d/pr-4226.md | main | 031ec80e332a6c7af521244238baa00abacd2059 | present | 1 |
| R-22 | Legacy claim verified: portal factory lists no converter blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 182 |
| R-23 | Legacy claim verified: base template has no converter navigation entry | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 50 |
| R-24 | Legacy claim verified: OpenAPI JSON twin exists | documentation/mist-api-openapi31json.json | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 0 |
| R-25 | Legacy claim verified: 16 MiB upload limit | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 73 |
| R-26 | Legacy claim verified: 16 KiB multipart overhead bound | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 36 |
| R-27 | Legacy claim verified: request class and CSRF host check | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 105 |
| R-28 | Legacy claim verified: SDK signature createOrgGatewayTemplate(mist_session, org_id, body) | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | local-venv | none (local package file) | present | 58 |
| R-29 | Legacy claim verified: POST createOrgGatewayTemplate operation | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9764 |
| R-30 | Legacy claim verified: gateway_template requires name | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80782 |
| R-31 | Legacy claim verified: dns_servers is an array of strings | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 78038 |
| R-32 | Legacy claim stale: Python 3.13 project floor | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | stale | 23 |
| R-33 | Converter blueprint URL prefix is /cisco-config-converter | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 54 |
| R-34 | Converter registers POST routes for preview, review, and export | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 62 |
| R-35 | Converter responses set Cache-Control no-store | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 113 |
| R-36 | Converter route module imports no mistapi module | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | absent | 0 |
| R-37 | Template name rule allows 1 to 120 visible characters | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 49 |
| R-38 | Upload decodes strict UTF-8 and rejects null characters | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 76 |
| R-39 | Review digest uses SHA-256 | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 91 |
| R-40 | Conversion states that only global IPv4 name-server commands convert | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 26 |
| R-41 | Export control carries data-testid cisco-export | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 24 |
| R-42 | Converter routes define no apply route | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | absent | 0 |
| R-43 | Integration test enables real CSRFProtect and asserts HTTP 413 | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 153 |
| R-44 | Portal blueprint registration lists existing blueprints only | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 200 |
| R-45 | Portal assigns the Flask secret key from portal config | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 115 |
| R-46 | Portal config sets secret_key from PORTAL_SECRET_KEY or a random UUID | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| R-47 | Data browser excludes only the firmware BACKUP_DIRECTORY name | web_portal/services/data_browser.py | main | 247d411105a7af1ed54458418630626182494ffe | present | 154 |
| R-48 | AGENTS.md present with writing and git rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R-49 | copilot-instructions states mistapi pin >=0.64.0,<0.65 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| R-50 | copilot-instructions holds the local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-51 | copilot-instructions lists the STE gate command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-52 | copilot-instructions requires the eight-level base-5 route for numeric records | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 160 |
| R-53 | copilot-instructions requires five children or fewer per structural directory | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167 |
| R-54 | copilot-instructions places the web portal on port 8055 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 180 |
| R-55 | copilot-instructions names MIST_APITOKEN for safe sweeps | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 63 |
| R-56 | Constitution Principle I five-item rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-57 | Constitution Principle III requires typed confirmation for destructive operations | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 121 |
| R-58 | Constitution forbids secrets in logs, outputs, and errors | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 134 |
| R-59 | Constitution Principle V requires ASCII-only log output | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 184 |
| R-60 | Constitution Principle VI requires inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-61 | Constitution Principle VII requires action logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-62 | spec-route.ps1 default route width is 8 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| R-63 | spec-route.ps1 uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-64 | Container Rule 1 starts test containers inside the compose group | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 148 |
| R-65 | Container guide names misthelper-redis as the shared Redis service | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 26 |
| R-66 | quality-gates.md documents the STE writing gate command | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 283 |
| R-67 | development-setup.md requires Python 3.15 or newer | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 29 |
| R-68 | requirements.txt pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R-69 | pyproject.toml allows mistapi >=0.64.1,<0.65 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| R-70 | CI sets MYPY_PATHS for the type gate | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-71 | Process folder baseline file exists for the guard | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| R-72 | MIST_API_GET_ENDPOINTS lists listOrgGatewayTemplates | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 559 |
| R-73 | OpenAPI defines /api/v1/orgs/{org_id}/gatewaytemplates | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9727 |
| R-74 | OpenAPI defines operation deleteOrgServicePolicy | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18413 |
| R-75 | OpenAPI gateway_template type enum lists spoke and standalone only | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80789 |
| R-76 | OpenAPI gateway_template defines dns_servers | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80678 |
| R-77 | OpenAPI createOrgGatewayTemplate request body uses gateway_template | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9887 |
| R-78 | mistapi 0.64.1 is installed | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | none (local package file) | present | 3 |
| R-79 | mistapi retries HTTP 429 up to three times | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | none (local package file) | present | 59 |
| R-80 | mistapi gatewaytemplates module defines listOrgGatewayTemplates | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | local-venv | none (local package file) | present | 17 |
| R-81 | Source repository LICENSE declares CC BY-NC 4.0 | LICENSE in jmorrison-juniper/MistCiscoConfigConverter | main (upstream) | e9ae5eff92457c2372db3be30a3d99166aeee547 | present | 1 |
| R-82 | Source mapping reference has a features-requiring-workarounds section | docs/CISCO_TO_MIST_MAPPING.md in jmorrison-juniper/MistCiscoConfigConverter | main (upstream) | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 677 |
| R-83 | Source user guide documents an apply confirmation | docs/USER_GUIDE.md in jmorrison-juniper/MistCiscoConfigConverter | main (upstream) | 4badf004a01b37bf75b6ca0c3539f07be85a8bbf | present | 134 |
| R-84 | Source user guide documents upload through the web interface | docs/USER_GUIDE.md in jmorrison-juniper/MistCiscoConfigConverter | main (upstream) | 4badf004a01b37bf75b6ca0c3539f07be85a8bbf | present | 119 |
| R-85 | Parity record spec.md present | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 0 |
| R-86 | Parity record tasks.md present with tasks T001 to T033 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 0 |
| R-87 | Parity plan defines gate G1 Legal | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 125 |
| R-88 | Reference record 4920 design folder present (shape only) | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design | main | 88749b6e351e7be60666a0c27d08c348b9d0d83e | present | 0 |
| R-89 | Parity path tests/contract/cisco_config_converter is absent | tests/contract/cisco_config_converter | main | none | absent | 0 |
| R-90 | Parity path converter state package is absent | src/interfaces/portals/cisco_config_converter/state | main | none | absent | 0 |
| R-91 | Parity path tests/e2e/web_portal/test_cisco_parity.py is absent | tests/e2e/web_portal/test_cisco_parity.py | main | none | absent | 0 |
| R-92 | tests/contract has 17 direct children, above the limit of five | tests/contract | main | none (directory listing) | present | 0 |
| R-93 | tests/e2e/web_portal has 32 direct children, above the limit of five | tests/e2e/web_portal | main | none (directory listing) | present | 0 |
| R-94 | Converter package root has 5 direct children, at the limit | src/interfaces/portals/cisco_config_converter | main | none (directory listing) | present | 0 |
| R-95 | Spec template present | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R-96 | Tasks template present | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R-97 | Portal code uses the standard logger for info messages | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 97 |
| R-98 | Conversion states that unsupported values are omitted to protect credentials | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 28 |
| R-99 | Upload model rejects path forms before the suffix check | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 57 |
| R-100 | Parity spec FR-023 requires scoped service, network, and template deletion | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 129 |

Legacy summary: 29 verified (R-01 to R-15, R-17, R-18, R-20 to R-31), 2 stale (R-16, R-32), and 1 absent (R-19).

## Decisions

Each decision names its alternatives. Decisions D-15 to D-18 need a human choice. The other decisions are recorded here and carried into the spec and plan.

### D-1 Parent record role and folder

- Decision: Keep this record as the parent of child issues 4634 to 4649. Reuse the folder `4224-cisco-config-converter` at the route.
- Alternatives: (a) new folder `4224-mist-cisco-config-converter` at the same route. (b) reuse the legacy folder. (c) no parent record.
- Chosen: (b).
- Reason: One issue holds one record. The route already matches issue 4224 (R-01 to R-09).
- Risk: The DNS-only legacy text is replaced. Git history keeps it. Section "Legacy baseline" in the spec states what the replaced text said.

### D-2 Merged DNS slice stays unregistered

- Decision: Keep the merged DNS slice from PR #4226 in the repository. Keep its blueprint unregistered until D-17 and gate G3 close.
- Alternatives: (a) revert PR #4226. (b) register the blueprint now. (c) keep the code and leave it unregistered.
- Chosen: (c).
- Reason: A revert destroys verified tests. Registration needs gate G3 and the license decision. Shared registration is absent today (R-22, R-23).
- Risk: Unregistered code can drift from its tests. Task T005 records the baseline before other work.

### D-3 Cloud apply in scope, gated by write family

- Decision: Include cloud apply. Register each write family in a disabled state. Enable a family only after gates G2, G4, and G5 pass and a human approves enablement (D-15).
- Alternatives: (a) keep the legacy deferral of apply. (b) enable apply without gates. (c) gated families, disabled by default.
- Chosen: (c).
- Reason: The issue requires an apply path with typed confirmation. The legacy deferral conflicts with that requirement.
- Risk: A production change can follow an enabled family. Mitigation: D-15 and the gates in the plan.

### D-4 Credential use

- Decision: Preview and export need no Mist credential. Discovery and apply read the existing credential on the server only.
- Alternatives: (a) require a credential for preview. (b) store a credential in the browser. (c) read the existing server credential for cloud steps only.
- Chosen: (c).
- Reason: The issue forbids browser storage and requires preview without credentials. The existing credential names are MIST_APITOKEN and MIST_API_TOKEN (R-55).
- Risk: Low. Task T031 checks that preview reads no credential.

### D-5 Typed confirmation words

- Decision: EXPORT gates export. APPLY gates cloud apply. CONFIRM gates administration and restore.
- Alternatives: (a) one word for every operation. (b) one word for each risk class.
- Chosen: (b).
- Reason: The child records 4644 to 4647 use these words. Constitution Principle III requires a typed confirmation (R-57).
- Risk: Operators confuse the words. Mitigation: the interface shows the exact word and the organization name.

### D-6 Mist access through mistapi only

- Decision: Call mistapi methods only. Bound each write at 90 seconds and each run at 10 minutes. Do not retry a write in application code.
- Alternatives: (a) direct HTTP calls. (b) application retries for writes. (c) mistapi calls with no application retry for writes.
- Chosen: (c).
- Reason: Direct HTTP is prohibited when a mistapi method exists (plan constitution check). mistapi retries HTTP 429 three times (R-79). Another application retry would repeat a write.
- Risk: A long write can exceed its bound. Mitigation: the result reads indeterminate and no retry runs.

### D-7 Private state under data

- Decision: Store converter state as private files under `data/`. Use no new database and no new service.
- Alternatives: (a) new tables in the existing MistHelper database. (b) browser storage. (c) private files under `data/`.
- Chosen: (c).
- Reason: The child records 4636 and 4643 design this store. The issue forbids browser storage. The existing database is allowed, but the child designs were drafted around files.
- Risk: The data browser lists files under `data/` and excludes only the firmware backup name (R-47). Mitigation: an exclusion change lands before production retention.

### D-8 In-memory upload policy

- Decision: Process uploads in memory. Accept six text suffixes and files up to 16 MiB. Decode strict UTF-8. Reject path-like names.
- Alternatives: (a) store uploads in a configured input folder. (b) process uploads in memory.
- Chosen: (b).
- Reason: The operator never gives a path, so the traversal risk does not arise. The limit comes from the legacy contract and the request bound (R-25, R-26).
- Risk: Each request holds up to 16 MiB in memory. The request class bounds the body before form parsing (R-27).

### D-9 Test layout

- Decision: Put converter integration tests under `tests/integration/web_portal/cisco_config_converter/`. Add browser evidence to `tests/e2e/web_portal/test_portal_smoke.py`. Keep the unit test at its path on `main`.
- Alternatives: (a) `tests/contract/cisco_config_converter/`. (b) new files under `tests/e2e/web_portal/`. (c) the integration folder with grouped subfolders.
- Chosen: (c).
- Reason: `tests/contract` holds 17 children (R-92). `tests/e2e/web_portal` holds 32 children (R-93). Constitution Principle I limits each folder to five children (R-56).
- Risk: The child records name paths that need amendment. Analysis A-14 and A-15 list them.

### D-10 Package layout

- Decision: The converter root keeps five children: `__init__.py`, `routes.py`, `presentation/`, `conversion/`, and `state/`. The administration engine goes under `state/administration/`. The presentation folder keeps five children, with administration files in `presentation/administration/`.
- Alternatives: (a) a sixth root folder `engine/`. (b) keep single modules for conversion and models. (c) grouped packages under the existing root.
- Chosen: (c).
- Reason: The root already holds five children (R-94). Option (a) would add a sixth child.
- Risk: Imports change. The record forbids a compatibility shim, so each call site changes in the same change.

### D-11 Shared portal files wait for handover

- Decision: Do not edit `web_portal/app.py` or `web_portal/templates/base.html` before gate G3 closes. Use an isolated test host until then.
- Alternatives: (a) edit both files now. (b) isolated test host until handover. (c) skip browser tests until handover.
- Chosen: (b).
- Reason: PR #4208 is an open draft that lists both files. A conflicting edit can block that PR.
- Risk: Shared integration waits. Task T032 depends on G3.

### D-12 Logging style

- Decision: Use the standard `logging` module with key=value fields and ASCII text.
- Alternatives: (a) structlog, as named in constitution Principle V. (b) standard logging with structured fields.
- Chosen: (b).
- Reason: The portal already uses the standard logger (R-97). Principle V allows an equivalent for structured entries.
- Risk: A reviewer can reject the reading. Task T-PR asks the reviewer to confirm it.

### D-13 Task IDs

- Decision: Use parity task IDs T001 to T033. Retire legacy task IDs T001 to T030. Cite a legacy ID only as `L-T###`.
- Alternatives: (a) keep legacy IDs. (b) renumber the parity tasks. (c) use the parity IDs.
- Chosen: (c).
- Reason: Child records cite parity IDs. Legacy T017 and T018 collide with parity T017 and T018, as child 4641 reports.
- Risk: Legacy readers need the mapping in analysis A-09.

### D-14 Sequencing

- Decision: Follow the parity dependency table. Create the `conversion/` package (child 4640) before the hardware (child 4638) and management (child 4639) edits. Build administration after backup and before recovery.
- Alternatives: (a) run every child in parallel. (b) run tasks in number order. (c) run dependency waves.
- Chosen: (c).
- Reason: Several child records edit the same shared files (analysis A-18).
- Risk: Delivery takes longer.

### D-15 HUMAN-DECISION-REQUIRED: production write enablement and deletion scope

- Decision: Keep all eight write families disabled by default. Keep service-policy and device-profile deletion out of scope until the owner approves the scope.
- Alternatives: (a) enable each family after its gates pass. (b) read-only scope only. (c) keep each family disabled and exclude deletions.
- Recommended option: (c).
- Reason: A Mist production change can damage live configuration. This record cannot reverse that change.
- Sources: child 4634 D-4, child 4644 D-17, child 4645 D-2 and D-3, child 4646 D-20. Issue comment 2026-11-13 says the service-policy deletion scope remains unresolved.

### D-16 HUMAN-DECISION-REQUIRED: credential policy and identity

- Decision: Require a verified operator identity before each write. Require a configured `PORTAL_SECRET_KEY` in production.
- Alternatives: (a) keep the portal without an operator identity. (b) require a verified identity and a configured seal key. (c) keep the random fallback.
- Recommended option: (b).
- Reason: web_portal/app.py defines no login route (analysis A-12). The fallback creates a new random key at each start (R-46).
- Sources: child 4636 D-10 and D-15, child 4644 D-5 and D-18, child 4645 D-1, child 4646 D-14, child 4648 D-9, child 4649 D-10.

### D-17 HUMAN-DECISION-REQUIRED: license basis

- Decision: Keep original code only. Obtain a legal decision for the converter source and test files that PR #4226 merged before any registration or publication.
- Alternatives: (a) keep original code and obtain a legal review. (b) approve reuse of source text or assets under CC BY-NC 4.0. (c) remove the merged converter files in a separate change.
- Recommended option: (a).
- Reason: The source repository declares CC BY-NC 4.0 (R-81). The issue requires license compatibility before any copy.
- Sources: child 4635 D-1 to D-7 and child 4649 D-8. Child 4635 counts nine converter files. PR #4226 lists six source files and four test files (analysis A-01).

### D-18 HUMAN-DECISION-REQUIRED: product approval of mappings and dispositions

- Decision: Approve only verified mappings and dispositions. List every other item as unsupported, with its reason.
- Alternatives: (a) approve every row. (b) approve verified rows only. (c) approve no row.
- Recommended option: (b).
- Reason: The issue requires product-owner approval of the organization-template effect (issue comment 2026-10-16). Child 4639 D-14 and child 4649 D-7 need the same owner decision.
- Sources: issue #4224 comment 2026-10-16. Child 4639 D-14. Child 4649 D-7.

## Legacy baseline

The legacy record described an isolated DNS preview, review, and export slice. It deferred cloud apply. Its verified facts appear in R-01 to R-31. Its stale claims appear in R-16 and R-32. Its absent claim appears in R-19.

## Sources

- S-1: Issue #4224 through `gh issue view 4224 -R jmorrison-juniper/MistHelper`. The issue has labels feature, web-portal, frontend, needs-human-review, and feature-spec. It was created 2026-10-14 and updated 2026-11-13.
- S-2: PR #4226, title "feat(web-portal): add isolated offline Cisco DNS converter". The PR is MERGED at 2026-10-26T20:35:38Z with merge commit `14ac97942f1e575edd7dbf8c4bbfb517ef58fad3`. The commit exists through `gh api repos/jmorrison-juniper/MistHelper/commits/14ac97942f1e575edd7dbf8c4bbfb517ef58fad3`. The PR lists 20 files: 9 record files, 6 source files, 4 test files, and 1 changelog fragment.
- S-3: PR #4596, title "docs(spec): record Cisco converter parity readiness". The PR is MERGED at 2026-11-13T09:41:52Z with merge commit `4cb0553a55ef06ba7a157608886d4c9d64593d03`. The commit exists through `gh api`. The PR lists 10 files in the parity record.
- S-4: PR #4208, title "feat(web-portal): integrate WAN performance dashboards". The PR is OPEN and a draft, last updated 2026-11-22. Its file list includes `web_portal/app.py` and `web_portal/templates/base.html`.
- S-5: PR #4615, title "fix(web-portal): preview nested JSON results". The PR is MERGED at 2026-11-13T06:20:12Z. Its file list includes `web_portal/services/data_browser.py`.
- S-6: PR #2729 matched the search for 4224 by its test count text. Its body names issue 2644. The PR is not linked to issue 4224.
- S-7: Child issues. #4632 and #4633 are CLOSED. #4634 to #4649 are OPEN. The issue list came from `gh issue list`.
- S-8: Source repository `jmorrison-juniper/MistCiscoConfigConverter`. It is public, and its default branch is main. Reads used `gh api repos/jmorrison-juniper/MistCiscoConfigConverter/contents/<path>?ref=main`. The LICENSE blob and the docs blobs appear in the table.
- S-9: Local checkout. Its HEAD equals remote `main`. The legacy folder, source files, tests, OpenAPI files, and `.venv` package were read locally. Each local-only claim has a remote row or a local-package row.
- S-10: Child drafts under `spec-drafts\4634` to `spec-drafts\4649`, and their `_meta` STATUS and summary files. The drafts served as context. They are drafts, not proof.
- S-11: Reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. It gave the folder shape only. No content was copied.
- S-12: Constitution version 1.9.0 and the four templates. The spec and tasks templates appear in R-95 and R-96.
- S-13: The gates table in `.github/copilot-instructions.md`. Each task names one command from this table.
- S-14: Issue comments on child issues 4634 and 4642, read through `gh issue view --json comments`. The 2026-11-08 comment on 4634 and the 2026-11-09 comment on 4642 describe PR #4596 as open.
- Commit checks: `14ac97942f1e575edd7dbf8c4bbfb517ef58fad3` (2026-10-26T20:35:37Z), `4cb0553a55ef06ba7a157608886d4c9d64593d03` (2026-11-13T09:41:51Z), and `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (2026-11-26T07:15:01Z) all returned from the commits API.

## Unverified

- U-01: Cisco IOS syntax for `ip name-server`. The legacy spec cites a Cisco guidance URL. This session did not fetch it.
- U-02: The child claim that the SDK sets no timeout on writes (child 4634). This session did not verify it. The record sets its own bounds.
- U-03: The child claim that the SDK logs write bodies at DEBUG level (child 4634). This session did not verify it.
- U-04: The child claim that five files name three mistapi versions (child 4634). Three pin texts differ (R-49, R-68, R-69). The rest was not checked.
- U-05: Live Mist behavior. This record makes no live call.
- U-06: Legacy test results from 2026-10-18 (63 tests, 100 percent feature coverage). This record ran no test.
- U-07: The organization-template effect named in the issue comment. This is a product decision and is listed as D-18.
- U-08: Upload-policy verification named as a blocker in the issue comment of 2026-10-16. The 16 MiB limit is a feature policy. A keyword search of the source user guide and mapping reference for limit lines found no upload size statement.
- U-09: The child claim that `identity.current_session()` returns the operator session (child 4642). This session did not check it.
- U-10: The full mistapi method inventory. This session did not check it. Child 4634 reports 22 write rows, including `deleteOrgServicePolicy`, and 18 read rows. The parent names only the gatewaytemplates family (R-80).
- U-11: The check conclusions of PR #4226 (`statusCheckRollup`). This session did not evaluate them.
- U-12: Login routes in portal files other than `web_portal/app.py`. This session searched `app.py` only (analysis A-12).
