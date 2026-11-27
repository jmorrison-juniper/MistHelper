# Research: EX Transceiver Master Report

This record checks each claim against GitHub `main`, the local checkout, the pinned mistapi source, and the local OpenAPI file. Each table row names the path, the reference, the blob SHA, the result, and the line.

## Remote Verification

### Method

- The full tree of `main` came from `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1`. The response lists 11,404 entries and is not truncated.
- The blob SHA of each path matches the local checkout for every file except two. The two files are `.gitignore` and `.specify/scripts/powershell/spec-route.ps1`.
- Symbol lines come from the local file when its blob matches `main`. For the two differing files, the lines come from `gh api repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`, decoded from base64.
- Installed mistapi blobs come from `git hash-object --no-filters` on the local file. The mistapi package is not in the repository tree.
- The OpenAPI file blob on disk equals the blob on `main`, `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`.
- Commit lookups use `gh api repos/jmorrison-juniper/MistHelper/commits/<sha>`. The response HTTP 422 means that the commit is absent.
- No rate-limit response occurred during the checks.
- The table has 149 rows. The same 149 checks appear in the `remote_checks` array of `4773-STATUS.json`. Rows R119 to R149 record the insertion-point lines that `plan.md` and `tasks.md` cite.

### Table

| # | Claim | Path | Ref | Blob SHA | Result | Line |
|---|-------|------|-----|----------|--------|------|
| R01 | Menu 309 registration exists in the entry file | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4836 |
| R02 | Menu 310 registration is absent from the entry file | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 0 |
| R03 | Menu 309 registry entry exists | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 537 |
| R04 | Menu 310 registry entry is absent | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | absent | 0 |
| R05 | Expected menu entry count is 309 | tests/unit/test_menu_entry_metadata.py | main | d9b4d79ebb6f303e54ad52add9c741e87eb01e32 | present | 10 |
| R06 | Menu 309 identity entry sits in the endpoint catalog test | tests/guardrails/test_endpoint_catalog.py | main | e061f6624a69cbfc7947275c076523c3c8d85fcd | present | 546 |
| R07 | Agent instructions state 308 registered operations numbered 1 to 309 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 11 |
| R08 | Menu reference states 308 actionable menu entries | documentation/menu_reference.md | main | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 6 |
| R09 | Menu reference generator is present | scripts/generate_menu_wiki.py | main | f959225275536743e93bc95d37cb015865a73d53 | present | 0 |
| R10 | Operator guide states that menu 309 needs no setting | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 425 |
| R11 | README task table has its first data row | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 40 |
| R12 | Release-note fragment folder has a README | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 1 |
| R13 | Agent instructions define the writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R14 | Agent instructions require Simplified Technical English for prose | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 42 |
| R15 | Constitution defines the Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R16 | ExHardwareInventory primary key strategy exists | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | present | 3506 |
| R17 | ExTransceiverMaster primary key strategy is absent | src/foundation/support/refactors/endpoint_primary_key_strategies.py | main | 3547991028bdbe955e1ba6c8a6bf3082240f2af8 | absent | 0 |
| R18 | Public export entry point write_with_format_selection exists | src/operations/exporting/export/data_exporter.py | main | f45fc71f8fd6b891d92ce9f98fa3fc46dfd32411 | present | 153 |
| R19 | Menu 309 handler class ExHardwareInventoryReport exists, and RunCollector is at line 101 | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 221 |
| R20 | Confirmation step prints the one fixed XML command | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 87 |
| R21 | Batch request fixes the output format to xml | src/operations/exporting/ex_hardware_inventory/run/batch.py | main | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 176 |
| R22 | Run folder reader accepts only .xml files | src/operations/exporting/ex_hardware_inventory/run/watch.py | main | fc086a6ace02b49280dd184c4831bf15d1c0b154 | present | 141 |
| R23 | TargetResult stores the saved XML reply only | src/operations/exporting/ex_hardware_inventory/report/builder.py | main | e01cb664623c6e32c7393e65cb8239bcbd3b2b7b | present | 41 |
| R24 | FailureReasons.exact reads only the XML format entry | src/operations/exporting/ex_hardware_inventory/report/builder.py | main | e01cb664623c6e32c7393e65cb8239bcbd3b2b7b | present | 79 |
| R25 | CellGuard class is defined | src/operations/exporting/ex_hardware_inventory/report/columns.py | main | 5489ed5b4151f7cc8bf4c51216636a6362c5192d | present | 18 |
| R26 | ReportColumns class defines the fixed and preferred column orders | src/operations/exporting/ex_hardware_inventory/report/columns.py | main | 5489ed5b4151f7cc8bf4c51216636a6362c5192d | present | 39 |
| R27 | CsvVerifier class is defined | src/operations/exporting/ex_hardware_inventory/report/csv_file.py | main | aab90d618cfa5ead3427f366732b39ea3e9b2a93 | present | 64 |
| R28 | API name ExHardwareInventory is set for the natural-key strategy | src/operations/exporting/ex_hardware_inventory/report/export.py | main | 114c629ebc534e97aafed664654159d0ffcf2fad | present | 48 |
| R29 | Outcome reader accepts only .xml replies | src/operations/exporting/ex_hardware_inventory/run/publisher.py | main | 7f52f590982b0ce85449758434c3d7d6118f5873 | present | 88 |
| R30 | HardwareXmlFlattener.flatten parses one XML reply | src/operations/exporting/ex_hardware_inventory/report/flatten.py | main | 5c365422abee1d0aa1d483791b70f710d4ac5c97 | present | 164 |
| R31 | Resolver calls listMspOrgs for MSP organizations | src/operations/exporting/ex_hardware_inventory/scope/resolver.py | main | 866f7c701e574fa368c0203bfcc22062fd82cee1 | present | 118 |
| R32 | Profile read calls getSelf once | src/operations/exporting/ex_hardware_inventory/scope/profile.py | main | fb745bedeac7e0e955f80256f2affd43f72ef7c6 | present | 97 |
| R33 | New transceiver package path is absent from main | src/operations/exporting/ex_transceiver_master | main | not in tree at main | absent | 0 |
| R34 | Hardware preset defines REPORT_KINDS for the combined reports | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | main | bb018c99e0fc0ffe982a7f532064f1755a87865a | present | 318 |
| R35 | Hardware preset defines the fixed command formats | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | main | bb018c99e0fc0ffe982a7f532064f1755a87865a | present | 310 |
| R36 | Preset parse validates the exact request fields | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | main | bb018c99e0fc0ffe982a7f532064f1755a87865a | present | 342 |
| R37 | Target selector keeps only connected devices | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | main | bb018c99e0fc0ffe982a7f532064f1755a87865a | present | 135 |
| R38 | CSV report name is hardware/inventory.csv | src/mist/realtime/websocket_streams/web/services/operations/artifacts.py | main | 19249d12238025825c1a208696fff30b2e82c73a | present | 51 |
| R39 | Master XML report name is hardware/inventory.xml | src/mist/realtime/websocket_streams/web/services/operations/artifacts.py | main | 19249d12238025825c1a208696fff30b2e82c73a | present | 52 |
| R40 | Finish step publishes reports for known output formats | src/mist/realtime/websocket_streams/web/services/operations/artifacts.py | main | 19249d12238025825c1a208696fff30b2e82c73a | present | 260 |
| R41 | Publish method writes the reports of one batch | src/mist/realtime/websocket_streams/web/services/operations/artifacts.py | main | 19249d12238025825c1a208696fff30b2e82c73a | present | 687 |
| R42 | Report builders map csv and xml to file names and compilers | src/mist/realtime/websocket_streams/web/services/operations/artifacts.py | main | 19249d12238025825c1a208696fff30b2e82c73a | present | 706 |
| R43 | ReportDownload class is defined | src/mist/realtime/websocket_streams/web/services/operations/artifacts.py | main | 19249d12238025825c1a208696fff30b2e82c73a | present | 846 |
| R44 | CSV download object uses the combined CSV name | src/mist/realtime/websocket_streams/web/services/operations/artifacts.py | main | 19249d12238025825c1a208696fff30b2e82c73a | present | 792 |
| R45 | Download file name prefix ExHardwareInventory_ is set in ReportDownload | src/mist/realtime/websocket_streams/web/services/operations/artifacts.py | main | 19249d12238025825c1a208696fff30b2e82c73a | present | 871 |
| R46 | Preview record stores the output format | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | main | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 68 |
| R47 | Preview method exists in the batch service | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | main | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 891 |
| R48 | Preview values are bound to the hardware selection | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | main | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 902 |
| R49 | Summary payload reports the output format | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | main | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 629 |
| R50 | Device type comes from the family mapping | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | main | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 489 |
| R51 | Batch download outputs are zip, csv, and xml | src/mist/realtime/websocket_streams/web/blueprint/responses/download.py | main | 95e541579e3fcfe21c15148023d035d578dbb95e | present | 24 |
| R52 | Batch download error text lists the accepted formats | src/mist/realtime/websocket_streams/web/blueprint/responses/download.py | main | 95e541579e3fcfe21c15148023d035d578dbb95e | present | 51 |
| R53 | Batch ZIP download route is registered | src/mist/realtime/websocket_streams/web/blueprint/registry.py | main | d984a6fb5b3e63ec9778459969a07fc621d3ca80 | present | 149 |
| R54 | CSV preview route is registered | src/mist/realtime/websocket_streams/web/blueprint/registry.py | main | d984a6fb5b3e63ec9778459969a07fc621d3ca80 | present | 152 |
| R55 | Hardware checkbox is defined in the page | src/mist/realtime/websocket_streams/web/templates/websockets_page.html | main | cba30182879ba6788f78d36e963da1556006e03e | present | 177 |
| R56 | Format selector is defined in the page | src/mist/realtime/websocket_streams/web/templates/websockets_page.html | main | cba30182879ba6788f78d36e963da1556006e03e | present | 189 |
| R57 | CSV download link is defined in the page | src/mist/realtime/websocket_streams/web/templates/websockets_page.html | main | cba30182879ba6788f78d36e963da1556006e03e | present | 305 |
| R58 | REPORTS_OF_FORMAT maps each output format to its reports | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 110 |
| R59 | Batch preview request builder exists | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 648 |
| R60 | reportsOfFormat selects the reports of a run | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 960 |
| R61 | Hardware concurrency default is 3 in the environment read | src/mist/realtime/websocket_streams/live/sessions/settings.py | main | a93befc8b3ffab1ab63996366f0951ac458fd147 | present | 66 |
| R62 | Owned WebSocket stream path is fixed | src/mist/realtime/websocket_streams/live/transport/endpoint.py | main | 6a1c1a6296e81e50c702622a42b39edb07ee167e | present | 117 |
| R63 | Shell REST trigger builds the device shell path | src/mist/realtime/websocket_streams/live/runners/utility/triggers/table.py | main | 9a7b201ef99060dee0c6cc70611bff18f1dafcd6 | present | 103 |
| R64 | Switch device type maps to the ex family | src/mist/realtime/websocket_streams/intake/pickers/records.py | main | 9912ce21e7ac5bb813fc8daf853f720887accc18 | present | 170 |
| R65 | Device stats call is listSiteDevicesStats | src/mist/realtime/websocket_streams/intake/pickers/devices.py | main | 8e5cb175277d13372e5cd531e43326364f44fe72 | present | 43 |
| R66 | Organization site call is listOrgSites | src/mist/realtime/websocket_streams/intake/pickers/resources.py | main | 6b65137fea554d1da3ce67dd19463a0a14d0b969 | present | 77 |
| R67 | SFP transceiver processor class is defined | src/mist/intelligence/reports/sfp_transceiver_data_processor.py | main | b952a5a6be20ab527cc9e714c5a858541fca319c | present | 29 |
| R68 | Native acceptance test holds the chassis inventory JSON fixture | tests/unit/websocket_streams/web/test_hardware_native_acceptance.py | main | 176188efcafd1c9fe1f5193014995992aed7e9f0 | present | 43 |
| R69 | Page test selects XML only for combined CSV formats | tests/e2e/websockets_tab/test_websockets_page.py | main | 2d608a96bae724366566daed64531d4ed760f54c | present | 356 |
| R70 | Download error text is asserted exactly | tests/unit/websocket_streams/web/test_ws_hardware_csv.py | main | 61168abc17ce5db1d74161017d46aeb13c530f67 | present | 410 |
| R71 | Preview values are asserted exactly | tests/unit/websocket_streams/web/test_ws_web_services.py | main | d20a6c7b2f7e2f479f2d2db1e0df8265411e62ce | present | 662 |
| R72 | Batch test asserts the XML request with revision 0 | tests/unit/ex_hardware_inventory/run/test_hardware_batch.py | main | 3f9bf7b59f7f1a04169c7d2eff787c69c09bb2a7 | present | 86 |
| R73 | Synthetic reply builder names transceivers Xcvr | tests/unit/ex_hardware_inventory/support/hardware_replies.py | main | c5078dc2d09cc90efaa648d16866d82453f57237 | present | 185 |
| R74 | Synthetic builder places transceivers under chassis-sub-module PIC items | tests/unit/ex_hardware_inventory/support/hardware_replies.py | main | c5078dc2d09cc90efaa648d16866d82453f57237 | present | 167 |
| R75 | Primary key test module is present | tests/unit/export/test_pk_strategies.py | main | d3e45c6ff4621565545d12a7744398f0a07130b4 | present | 0 |
| R76 | Menu 309 operation test module is present | tests/unit/ex_hardware_inventory/test_hardware_operation.py | main | 98c4fab6e596b00d245652545bd832a59a4ced07 | present | 0 |
| R77 | Flatten test module is present | tests/unit/ex_hardware_inventory/report/test_hardware_flatten.py | main | 83adf8147aa79074dc756558f8c06a41180069c9 | present | 0 |
| R78 | Report builder test module is present | tests/unit/ex_hardware_inventory/report/test_hardware_report_builder.py | main | b911e840a626b87acaf0c2cf8db890537c360a65 | present | 0 |
| R79 | CSV file test module is present | tests/unit/ex_hardware_inventory/report/test_hardware_csv_file.py | main | c8c651d3d6fc7d32e23cec66822b70bea34ef21d | present | 0 |
| R80 | Export test module is present | tests/unit/ex_hardware_inventory/report/test_hardware_export.py | main | fe81a271f64a063caec37ae31117b680057aecb1 | present | 0 |
| R81 | CLI flow integration test module is present | tests/integration/ex_hardware_inventory/test_hardware_cli_flow.py | main | 45d5e244020455a9c8876841f807d28481482106 | present | 0 |
| R82 | Trigger parity contract test module is present | tests/contract/websocket_streams/test_ws_utility_trigger_parity.py | main | 2e0238f928a7b11dff594cbeaa0a1d67b39c4109 | present | 0 |
| R83 | Transport constitution guardrail test is present | tests/guardrails/test_websocket_transport_constitution.py | main | 447306b0a09400daabf79987e2b1a97f6430d951 | present | 0 |
| R84 | New transceiver test folder is absent | tests/unit/ex_transceiver_master | main | not in tree at main | absent | 0 |
| R85 | Data folder rule ignores data/ at line 95 | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 95 |
| R86 | Test artifacts rule ignores /test-artifacts/ at line 107 | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 107 |
| R87 | mistapi pin is version 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R88 | Spec route defines Get-SpecRadixSegments | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R89 | Spec route base is 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R90 | Spec route defines Resolve-SpecFeaturePath | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| R91 | CI workflow is present | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 0 |
| R92 | STE linter configuration is present | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| R93 | Project configuration is present | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 0 |
| R94 | CLAUDE.md is present | CLAUDE.md | main | 9821a79a4481e754bc34052ace0daffa0f8ec088 | present | 0 |
| R95 | Test-quality baseline is present | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 0 |
| R96 | Test-quality configuration is present | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| R97 | STE writing guide is present | documentation/ASD-STE100_writing-guide.md | main | b464165aae116a17bb3031d3cef9b84a95589c0a | present | 0 |
| R98 | Reference record for issue 4920 is present | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 0 |
| R99 | Portal app file is in the open draft pull request 4208 file list | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 0 |
| R100 | Portal base template is in the open draft pull request 4208 file list | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 0 |
| R101 | Mist OpenAPI file is present | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 0 |
| R102 | Mist self profile operation getSelf is defined | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25490 |
| R103 | Mist listMspOrgs operation is defined | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 4085 |
| R104 | Mist listOrgSites operation is defined | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20022 |
| R105 | Mist listSiteDevicesStats operation is defined | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 39555 |
| R106 | Mist createSiteDeviceShellSession operation is defined | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 30503 |
| R107 | Installed mistapi getSelf function is defined | .venv\Lib\site-packages\mistapi\api\v1\self\self.py | local-venv | 9a1c323fb1045478d923ebcb30436655c851a6e2 | present | 17 |
| R108 | Installed mistapi listMspOrgs function is defined | .venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py | local-venv | 869130830ed95d3a095daa9f7ff42bcd8de253b8 | present | 17 |
| R109 | Installed mistapi listOrgSites function is defined | .venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py | local-venv | b33331fbb12f81106e79799e9b5d0486c218b47c | present | 17 |
| R110 | Installed mistapi listSiteDevices function is defined | .venv\Lib\site-packages\mistapi\api\v1\sites\devices.py | local-venv | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 17 |
| R111 | Installed mistapi createSiteDeviceShellSession function is defined | .venv\Lib\site-packages\mistapi\api\v1\sites\devices.py | local-venv | fd3faa0988e688c1cac4e21f22ebe22693f77409 | present | 2775 |
| R112 | Installed mistapi listSiteDevicesStats function is defined | .venv\Lib\site-packages\mistapi\api\v1\sites\stats.py | local-venv | bce91c2c8ff2c793190c2afb3548ae83e15322c2 | present | 1051 |
| R113 | Installed mistapi distribution is version 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | local-venv | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 0 |
| R114 | Head commit of main is f03c6c9b | commits/main | main | not a blob: commit lookup returned HTTP 200 | present | 0 |
| R115 | Worktree commit 8140bb3 is present on GitHub | commits/8140bb3 | main | not a blob: commit lookup returned HTTP 422 | absent | 0 |
| R116 | Worktree commit 58ab484 is present on GitHub | commits/58ab484 | main | not a blob: commit lookup returned HTTP 422 | absent | 0 |
| R117 | Worktree commit 07cf3ee is present on GitHub | commits/07cf3ee | main | not a blob: commit lookup returned HTTP 422 | absent | 0 |
| R118 | Worktree commit edc12d5 is present on GitHub | commits/edc12d5 | main | not a blob: commit lookup returned HTTP 422 | absent | 0 |
| R119 | Mist device list call is listSiteDevices | src/mist/realtime/websocket_streams/intake/pickers/devices.py | main | 8e5cb175277d13372e5cd531e43326364f44fe72 | present | 102 |
| R120 | Helper DataProcessingUtils.flatten_dict joins nested keys and gives list items index keys | src/foundation/models/data/data_processing_utils.py | main | f0e53336717eefbbe0bf7b4136b3e0d4f11f3847 | present | 36 |
| R121 | CLI report calls write_with_format_selection | src/operations/exporting/ex_hardware_inventory/report/export.py | main | 114c629ebc534e97aafed664654159d0ffcf2fad | present | 81 |
| R122 | TargetResult class is defined | src/operations/exporting/ex_hardware_inventory/report/builder.py | main | e01cb664623c6e32c7393e65cb8239bcbd3b2b7b | present | 26 |
| R123 | RowFactory.classify returns the report status of one target | src/operations/exporting/ex_hardware_inventory/report/builder.py | main | e01cb664623c6e32c7393e65cb8239bcbd3b2b7b | present | 91 |
| R124 | RunFolder._result builds one target result | src/operations/exporting/ex_hardware_inventory/run/watch.py | main | fc086a6ace02b49280dd184c4831bf15d1c0b154 | present | 131 |
| R125 | RunFolder._xml reads the saved XML reply of one target | src/operations/exporting/ex_hardware_inventory/run/watch.py | main | fc086a6ace02b49280dd184c4831bf15d1c0b154 | present | 139 |
| R126 | OrganizationBatchRun class is defined | src/operations/exporting/ex_hardware_inventory/run/batch.py | main | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 173 |
| R127 | OrganizationBatchRun.preview finds the connected EX switches | src/operations/exporting/ex_hardware_inventory/run/batch.py | main | 5fe7b5061eda55bbd292a4cd9f6569e50c46e34d | present | 188 |
| R128 | OrganizationPlan.build is defined | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 70 |
| R129 | ExHardwareInventoryReport.run is the menu 309 entry point | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 225 |
| R130 | _confirmed asks for the typed phrase | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 287 |
| R131 | _collect runs each organization and writes the report | src/operations/exporting/ex_hardware_inventory/operation.py | main | d2a29f179e9e8d93721a8ee70591e8bcc2d9b858 | present | 296 |
| R132 | HardwareConsole class is defined | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 29 |
| R133 | HardwareConsole.confirm is defined | src/operations/exporting/ex_hardware_inventory/console.py | main | 4d7596f4e171a4d0aebbcada96c9f4b40f591a8d | present | 71 |
| R134 | Format group container exists in the page | src/mist/realtime/websocket_streams/web/templates/websockets_page.html | main | cba30182879ba6788f78d36e963da1556006e03e | present | 187 |
| R135 | Format select closing tag ends the format group | src/mist/realtime/websocket_streams/web/templates/websockets_page.html | main | cba30182879ba6788f78d36e963da1556006e03e | present | 197 |
| R136 | Format selector change listener is wired | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 183 |
| R137 | renderBatchPreview draws the preview summary | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 713 |
| R138 | Download link visibility follows the published reports | src/mist/realtime/websocket_streams/web/static/websockets.js | main | c0b4f439743280511cf82c00e9ca23a2e1c2a9d4 | present | 952 |
| R139 | Operator guide heading Run a Multi Site WebSocket operation exists | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 338 |
| R140 | Operator guide heading Collect EX chassis hardware as one CSV report or one XML file exists | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 398 |
| R141 | Copilot instructions resource_intensive table row lists menu 309 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 224 |
| R142 | HardwareXmlSelection class is defined | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | main | bb018c99e0fc0ffe982a7f532064f1755a87865a | present | 33 |
| R143 | Selection preview_values method is defined | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | main | bb018c99e0fc0ffe982a7f532064f1755a87865a | present | 64 |
| R144 | BatchPreviewRecord class is defined | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | main | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 50 |
| R145 | Second summary payload reports the output format | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | main | edcb8413d4bfb0dbc9a3d1471dce4558e9100a68 | present | 804 |
| R146 | _compile builds the report files of one batch | src/mist/realtime/websocket_streams/web/services/operations/artifacts.py | main | 19249d12238025825c1a208696fff30b2e82c73a | present | 702 |
| R147 | Menu 309 import of ExHardwareInventoryReport exists in the entry file | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 580 |
| R148 | Menu 309 entry closes at line 4843 | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 4843 |
| R149 | Expected menu list holds the menu 309 entry at line 45 | tests/unit/test_menu_entry_metadata.py | main | d9b4d79ebb6f303e54ad52add9c741e87eb01e32 | present | 45 |

## Remote State

- Main head is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The head commit date is 2026-11-26T07:15:01Z.
- Issue #4773 is open. Its labels are `feature`, `web-portal`, and `in-progress`. Its body states that the requester authorized read-only live testing in the configured lab organization.
- Issue #4920 is closed, closed at 2026-11-26T00:36:00Z. Its title is "[Spec]: Collect EX switch hardware inventory into one CSV for one organization or an MSP".
- Issue #4933 is closed, closed at 2026-11-26T00:36:21Z. Its title is "Feature: one combined master XML file for the EX hardware inventory, checked against the XML 1.0 standard".
- Issue #4931 is closed, closed at 2026-11-26T00:36:15Z. Its title is "Feature: preview the combined CSV report as a table in the WebSockets tab".
- Issue #4769 is closed, closed at 2026-11-12T07:35:11Z. Its title is "feat(web-portal): collect EX chassis hardware XML through WebSockets".
- Issue #4783 is open. Its title is "Test quality: native report tests miss failure-boundary checks".
- Issue #4939 is open. Its title is "Web portal: run the fixed EX hardware inventory command without unlocking the free-form remote shell".
- Pull request #4607 is merged, merged at 2026-11-13T07:14:03Z. Its title is "refactor(troubleshooting): relocate modules to cohesive packages".
- Pull request #4619 is merged, merged at 2026-11-13T08:54:28Z. Its title is "fix(wan-vpn): reject profiles from failed responses".
- Pull request #4208 is an open draft. Its title is "feat(web-portal): integrate WAN performance dashboards". Its files include `web_portal/app.py` and `web_portal/templates/base.html`.
- Pull request #4813 is an open draft. Its title is "fix(export): preserve carriage returns in CSV". Its files include `src/operations/exporting/export/data_exporter.py` and `tests/unit/export/test_data_exporter.py`.
- The other open pull requests, #4886 to #4890, list none of the paths that this plan changes.
- The worktree commits named in the issue comment, `8140bb3`, `58ab484`, `07cf3ee`, and `edc12d5`, return HTTP 422 on GitHub. Their content cannot be verified from this record.

## Decisions

### D-1. Menu number and CLI shape

- **Alternatives**: (a) A new menu 310 that runs the same collection. (b) An optional prompt inside menu 309. (c) A portal-only option.
- **Chosen**: (a). Menu 310 runs the same collection and writes only the transceiver master CSV.
- **Reason**: Menu 309 keeps its native files, its hardware CSV report, and its master XML (FR-029). Menu 310 is free on `main` (R02 and R04).
- **Risk**: One more resource-intensive menu entry. The typed phrase and the category limit the risk.

### D-2. Package location

- **Alternatives**: (a) A sibling package `src/operations/exporting/ex_transceiver_master/`. (b) A package inside `ex_hardware_inventory/`. (c) New modules inside `report/` or `run/`.
- **Chosen**: (a).
- **Reason**: `src/operations/exporting/` holds four directory children on `main`, so the new package makes five. `ex_hardware_inventory/` already holds five children, excluding `__init__.py`, so option (b) makes six. Option (c) adds to a full folder.
- **Risk**: The new package imports from `ex_hardware_inventory`. Imports run one way only, from the new package to the old one.

### D-3. Test placement

- **Alternatives**: (a) Append cases to existing test modules. (b) A new folder `tests/unit/ex_transceiver_master/`. (c) New test modules in existing folders.
- **Chosen**: (a).
- **Reason**: `tests/unit/` already holds more than five children. `tests/unit/ex_hardware_inventory/report/` holds six test modules. A new folder or module adds to a full parent.
- **Risk**: The existing test modules grow. Each new case stays short.

### D-4. Transceiver match rule

- **Alternatives**: (a) An item name that starts with `Xcvr`, followed by one space and an identifier. (b) An element type of `chassis-sub-sub-module` only. (c) A match on the description text.
- **Chosen**: (a).
- **Reason**: The synthetic builder names transceivers `Xcvr <n>` with element type `chassis-sub-sub-module`, under `chassis-sub-module` PIC items (R73 and R74). The live element type is unverified (U-1). The item name does not depend on vendor description text.
- **Risk**: A live switch may name its items differently. U-1 and task T034 check the live names.

### D-5. Module type

- **Alternatives**: (a) The description text, trimmed, with repeated spaces collapsed. (b) A lookup table from part numbers to readable names. (c) The CLEI code.
- **Chosen**: (a).
- **Reason**: A lookup table invents names, which FR-010 forbids. A CLEI code is not readable.
- **Risk**: Some descriptions are terse codes. The part number column keeps the exact identifier.

### D-6. Module location

- **Alternatives**: (a) The parent item path without the chassis root. (b) The full item path only. (c) A physical port number from another source.
- **Chosen**: (a).
- **Reason**: The reply already holds the path. The report adds no new source. The `item_path` column keeps the full value.
- **Risk**: A name that contains a slash can split the location text in an odd way. `item_path` still shows the full value.

### D-7. Source precedence

- **Alternatives**: (a) XML first, and JSON only when XML is absent for a completed target. (b) A JSON fallback after a failed XML reply. (c) XML only.
- **Chosen**: (a).
- **Reason**: A fallback hides an XML failure and mixes two sources. XML only breaks JSON-only runs, which FR-012 requires.
- **Risk**: In a both-format run, a failed XML reply gives an outcome row even when a valid JSON file exists. The outcome row names the failed format.

### D-8. Equivalence scope

- **Alternatives**: (a) Identity and transceiver columns only. (b) Full item equivalence, including attributes and the CLI banner. (c) Byte equality of the whole file.
- **Chosen**: (a).
- **Reason**: The JSON reply holds no CLI banner. The XML walker reads attributes that the JSON reader does not read. Byte equality would include the run time, which SC-001 excludes.
- **Risk**: A future column can break the equivalence. SC-001 guards the current columns.

### D-9. No-transceiver rows

- **Alternatives**: (a) One no-transceiver row for each collected switch without a transceiver item. (b) No row for such a switch.
- **Chosen**: (a).
- **Reason**: A missing row hides a collected switch (FR-013).
- **Risk**: A large organization with few transceivers gets more rows. Growth stays linear in the number of switches.

### D-10. CLI format prompt

- **Alternatives**: (a) A word prompt that accepts XML, JSON, or BOTH. Enter selects XML. Other answers cancel. (b) A numbered list. (c) A required choice without a default.
- **Chosen**: (a).
- **Reason**: Words avoid a wrong number. Enter matches the portal default. Other answers cancel, so the safe path stays the default.
- **Risk**: A misspelled word cancels the run. The summary line states that the run canceled.

### D-11. CLI CSV through DataExporter with a new key

- **Alternatives**: (a) A new key `ExTransceiverMaster` with a composite key. (b) The existing `ExHardwareInventory` key. (c) A private file writer.
- **Chosen**: (a).
- **Reason**: The rows have another shape. Database backends need their own key (FR-028). A private writer skips the shared export path.
- **Risk**: Database backends gain one table key. Operators see it only when they enable a database backend.

### D-12. Portal publication

- **Alternatives**: (a) Add the file to the existing publish step, and offer a download only. (b) Publish the file after the other reports. (c) Offer a table preview in the portal.
- **Chosen**: (a).
- **Reason**: One publish step prevents a partial set of reports. A table preview adds scope that the spec excludes.
- **Risk**: A compile error blocks the other reports. The compile step runs before the publish step writes any file.

### D-13. Preview binding

- **Alternatives**: (a) A boolean `transceiver_csv` in the preview values and the preview record. (b) A new preset value. (c) A separate preview route.
- **Chosen**: (a).
- **Reason**: The existing preset and binding code stay in place. The checkbox state joins the preview and invalidates it on change (FR-021).
- **Risk**: Two exact-value tests change, at `test_ws_web_services.py` line 662 and `test_ws_hardware_csv.py` line 410 (T018 and T021).

### D-14. Result sink for the collector

- **Alternatives**: (a) `RunCollector` takes a sink with `add`, `counts`, and `results`. (b) A copy of `RunCollector` for menu 310. (c) A subclass of `RunCollector`.
- **Chosen**: (a). `RunCollector` is at `operation.py` line 101 (R19).
- **Reason**: One collector loop keeps the rate limit and the cancel rules in one place.
- **Risk**: The refactor touches the menu 309 path. The existing tests and task T012 guard it.

### D-15. README row

- **Alternatives**: (a) One row in the README task table. (b) No README change. (c) An edited operation count.
- **Chosen**: (a).
- **Reason**: The README task table lists tasks, not counts. A search of the README found no 308 or 309 operation count (R11).
- **Risk**: One more row to maintain.

### D-16. Live check

- **Alternatives**: (a) An operator-run read-only check on the configured lab organization. (b) No live check. (c) Mock tests only.
- **Chosen**: (a).
- **Reason**: SC-007 needs evidence from a live switch. The issue body states that the requester authorized read-only live testing in the configured lab organization (issue body, line 11).
- **Risk**: The lab organization may hold no transceiver item. The run then shows zero rows, and the operator records that result.

### D-17. Worktree commits

- **Alternatives**: (a) Reimplement the feature on a new branch from `main`. (b) Cherry-pick the four commits named in the issue comment. (c) Use the local worktree as the branch.
- **Chosen**: (a).
- **Reason**: The four commits return HTTP 422 on GitHub (R115 to R118). Their content cannot be verified from this record, because worktree commands are outside the read-only rule.
- **Risk**: Some work repeats the local work. The local worktree stays unchanged as evidence for the owner.

### D-18. Mist access

- **Alternatives**: (a) Reuse the existing mistapi functions and the owned WebSocket transport. (b) A new REST call. (c) A change to the owned transport.
- **Chosen**: (a).
- **Reason**: The spec states that the feature adds no REST call. The mistapi functions exist in the pinned version (R107 to R112). The owned transport is approved and stays unchanged.
- **Risk**: No new risk. The transport contract tests stay in place (T028).

## Sources

### Repository files (read only)

- `AGENTS.md` lines 40 and 42 (writing style section and the STE rule).
- `.github/copilot-instructions.md` lines 11 and 224 (operation counts and the resource-intensive list).
- `.specify/memory/constitution.md` lines 38 and 40 (Five-Item Rule).
- `documentation/operator-guide.md` lines 425, 494, and 496 (menu 309 CLI guidance).
- `documentation/menu_reference.md` lines 6 to 8 (operation counts).
- `src/operations/exporting/ex_hardware_inventory/console.py` lines 43, 71, 81, 83, 87, and 91 (menu 309 steps, phrase, and fixed command).
- `src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py` lines 304 to 307 (fixed XML and JSON commands).
- `tests/unit/ex_hardware_inventory/support/hardware_replies.py` lines 34, 167, 183 to 189 (synthetic transceiver fixture).
- Issue #4773 body, line 11 (read-only live testing authorization).

### Mist API evidence (local OpenAPI file)

- `documentation/mist-api-openapi31yaml.yaml`, path `/api/v1/msps/{msp_id}/orgs` at line 4081 with operation `listMspOrgs` at line 4085.
- The same file, path `/api/v1/orgs/{org_id}/sites` at line 20018 with operation `listOrgSites` at line 20022.
- The same file, path `/api/v1/self` at line 25460 with operation `getSelf` at line 25490.
- The same file, path `/api/v1/sites/{site_id}/devices` at line 27872 with operation `listSiteDevices` at line 27877.
- The same file, path `/api/v1/sites/{site_id}/devices/{device_id}/shell` at line 30497 with operation `createSiteDeviceShellSession` at line 30503.
- The same file, operation `listSiteDevicesStats` at line 39555.
- The same file, schema `stat_device_status_filter` at lines 105419 to 105425, with enum values `all`, `connected`, and `disconnected`.

### Installed mistapi source (local, version 0.64.1)

- `.venv\Lib\site-packages\mistapi\api\v1\self\self.py` line 17 (`getSelf`).
- `.venv\Lib\site-packages\mistapi\api\v1\msps\orgs.py` line 17 (`listMspOrgs`).
- `.venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py` line 17 (`listOrgSites`).
- `.venv\Lib\site-packages\mistapi\api\v1\sites\devices.py` line 17 (`listSiteDevices`) and line 2775 (`createSiteDeviceShellSession`).
- `.venv\Lib\site-packages\mistapi\api\v1\sites\stats.py` line 1051 (`listSiteDevicesStats`).

### Juniper operational reference (skill)

- Skill `juniper-cliref-operational`, file `04-chassis-and-hardware/04-chassis-hardware-inventory.md`, section `### show chassis hardware` at line 5.
- Line 15 states that the `detail` option includes RAM and disk information, and that it was introduced in 24.4R1.
- Line 17 states that the `models` option displays model numbers and part numbers for orderable FRUs, and that it was introduced in 8.2.
- Line 20 states that the `member member-id` option applies to MX Series devices and EX Series switches.

## Unverified

- **U-1**: The live element type and item name of a transceiver. The fixtures are synthetic. Task T034 captures one live example.
- **U-2**: Whether a live transceiver item carries `model-number`. The fixed command uses `detail`. The skill line 17 describes `models`. Task T034 captures one live example.
- **U-3**: Whether every target software release accepts the `detail` option. The skill line 15 gives 24.4R1 as the introduction release. Task T034 records the lab release. An older release gives a failed outcome row.
- **U-4**: The JSON form of an empty leaf and the JSON element names in live output. The fixture uses `[{"data": "value"}]`, and the reader also accepts `[{}]`. The design assumes that JSON element names match the XML names. Task T034 captures one live example.
- **U-5**: The content of the four worktree commits named in the issue comment. They return HTTP 422 on GitHub (R115 to R118), and this record cannot read the local worktree.
- **U-6**: The collection counts in the owner comment on issue #4773. This record holds no lab run that reproduces them. Task T034 produces new counts.
