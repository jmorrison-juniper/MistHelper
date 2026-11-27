# Research: Convert Verified Network and Routing Settings

## Evidence Boundary

| Evidence | Revision or state |
| --- | --- |
| GitHub `main` | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, commit dated 2026-11-26T07:15:01Z |
| Local `HEAD` | `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, same as `main` |
| Issue #4640 | OPEN. Created 2026-11-07. Labels `feature` and `web-portal`. No comments. |
| Linked pull requests | None. `gh pr list --search 4640` returned an empty list. |
| Merged full-parity task map | PR #4596, merged 2026-11-13T09:41:52Z, "docs(spec): record Cisco converter parity readiness" |
| Parent and program issues | #4224 OPEN. #4634 to #4639 OPEN. #4641 to #4649 OPEN. |
| Sibling draft for #4636 | Present in `spec-drafts\4636`. Its branch is not on `main`. |
| Installed SDK | `mistapi` 0.64.1. The distribution folder `mistapi-0.64.1.dist-info` exists in `.venv`. |

## Procedure Record

- Step 1, issue facts: The issue body requires T013 and T014. It names the families, the synthetic tests, the no-secret rule, and the parent and prerequisite issues. It has no comments.
- Step 2, linked work: No pull request names issue #4640. Merged PR #4596 supplies the full task map. Its files are the live record under `specs\live\0\0\0\1\2\1\3\3\2\1\4\2\1\4\1\3\0\20261105-170040-cisco-converter-full-parity`.
- Step 3, existing record: No folder under `specs\` starts with `4640-`. The route folder `specs\numbered\0\0\1\2\2\0\3\0` is absent on `main`. The draft folder was created in this pass.
- Step 4, remote verification: One recursive tree fetch returned 11,404 entries with no truncation. Twelve code, test, and spec files were read through the contents endpoint. The OpenAPI file is 4,317,370 bytes. The contents endpoint does not return bodies above 1 MB, so the git blob endpoint was used for that file. The local OpenAPI file has the same blob SHA as `main`.
- Step 5, research: The code, its tests, the live record, the sibling record for #4636, the OpenAPI document, and the mistapi source were read. No web page was fetched. No skill was loaded. The Mist claims rest on the OpenAPI document. The converter claims rest on repository files.
- Step 6, decide: The decisions appear in the next section.
- Step 7, write: The record files appear under `DRAFT_DIR`.

## Decisions

### D-1 Replace conversion.py with a conversion package

- Alternatives: (A) Keep `conversion.py` and add the network logic there. (B) Add a `network/` child directly under the converter root. (C) Place the logic in the `state/` package. (D) Replace `conversion.py` with a `conversion/` package.
- Chosen: D.
- Reason: Option A breaks the five-name limit for modules and the five-member limit for classes. The current DNS class already has five methods (`conversion.py` lines 15 to 78). Option B makes the converter root six children, which the constitution forbids. Option C mixes conversion behavior with state records.
- Risk: The live T014 path changes. The symbol gate reports the removed module, which the pull request must record. Issue #4636 D-1 keeps `conversion.py` for import lines only. This record supersedes that part after issue #4636 merges.

### D-2 Place the tests under the integration folder

- Alternatives: (A) `tests/contract/cisco_config_converter/` as the live T013 path. (B) `tests/integration/web_portal/cisco_config_converter/conversion/`. (C) The unit folder that holds the DNS unit test.
- Chosen: B.
- Reason: `tests/contract/` holds 17 children (R04). A new direct child breaks the constitution. Option C places new tests beside an unrelated legacy path (analysis E-8). Option B matches issue #4636 D-2 for the state tests.
- Risk: The test folder differs from the live record. The test quality ratchet reads each committed test file, so the placement does not hide a finding.

### D-3 Reserve two package slots

- Alternatives: (A) Use all five slots of `conversion/` now. (B) Reserve `hardware/` for issue #4638 and `management/` for issue #4639. (C) Put management code inside `network/`.
- Chosen: B.
- Reason: Issues #4638 and #4639 each need one child directory under `conversion/`. Reserved names keep the count at five after both issues merge. Option C fills `network/` with unrelated families.
- Risk: The reserved names stay empty if the owners choose a different layout. Issues #4638 and #4639 must confirm the names before they start.

### D-4 Take WAN and LAN roles from the explicit assignment

- Alternatives: (A) Infer roles from a hostname, `ip address dhcp`, `switchport`, or a default route. (B) Take the role from one `PortAssignment` value that issue #4638 produces. (C) Set all unassigned ports to LAN.
- Chosen: B. The type `PortAssignment` appears in `conversion/common/fragment.py`. Issue #4638 produces values of that type.
- Reason: The live FR-005 forbids role inference from a hostname. The OpenAPI port `usage` enum allows only `ha_control`, `ha_data`, `lan`, and `wan` (80464 to 80470). Source hints conflict in real configurations, and an explicit role is auditable.
- Risk: Each physical port needs an assignment before the converter maps it. Each missing assignment produces an unresolved item, so the gap stays visible.

### D-5 Derive DHCP ranges from leading and trailing exclusions

- Alternatives: (A) Split one pool into several ranges. (B) Emit no pool when any exclusion exists. (C) Derive the range from leading and trailing exclusions. Treat middle exclusions, overlaps, and gateway conflicts as unresolved. (D) Ignore exclusions.
- Chosen: C.
- Reason: The OpenAPI pool object has one `ip_start` and one `ip_end` per network (77700 and 77706). Their descriptions give the starting and ending addresses of the lease pool. The inclusive reading comes from that text. Option A has no schema support. Option D is unsafe because a pool could cover a gateway address.
- Risk: The inclusive reading is schema text, not a live check. It stays on the Unverified list (UV-2). Gateway conflicts stay unresolved until issue #4634 confirms the semantics.

### D-6 Emit static routes with IPv4 next hops only

- Alternatives: (A) Emit interface next hops by interface name. (B) Emit an IPv4 next hop only. Treat distance, name, tag, VRF, and interface forms as unresolved. (C) Emit distance and name as extra fields.
- Chosen: B.
- Reason: The OpenAPI route object defines one property, `via`, with IPv4 format (79609 to 79617, `via` at 79613). The schema describes no other route field.
- Risk: Routes with a distance become unresolved. Each unresolved item names the reason, so an operator can review it.

### D-7 Map VRF members and omit route distinguishers

- Alternatives: (A) Emit route distinguishers in `vrf_config`. (B) Map VRF members to instances. Omit `vrf_config.enabled`, route distinguishers, and VRF routes. (C) Skip VRFs entirely.
- Chosen: B.
- Reason: The gateway VRF instance holds only `networks` (80821 to 80832). The only `vrf_config` property is `enabled` (118048). The schema owner of the VRF extra routes is `switch_vrf_instance` (header at 113368, reference at 113395), which is not a gateway object.
- Risk: The converter omits `vrf_config.enabled` until issue #4638 confirms support per model (UV-7).

### D-8 Derive BGP fields and omit prefixes and credentials

- Alternatives: (A) Emit advertised prefixes in `bgp_config` networks. (B) Emit each neighbor with its remote AS. Derive the type and the transport. Omit prefixes and credentials. Treat other commands as unresolved. (C) Map the Cisco password to `auth_key`.
- Chosen: B.
- Reason: The schema describes `bgp_config.networks` as network names for neighbor connections (71798 and 71870), not as prefixes. The `type` enum has `external` and `internal` (71876 to 71884). `local_as` has a minimum of 1 (71893 to 71898). A password mapping needs the owner decision in D-18.
- Risk: A session without a derivable transport becomes unresolved. The transport comes from a converted subnet, so a neighbor outside every subnet stays unresolved.

### D-9 Emit IPv4 NTP servers without options

- Alternatives: (A) Emit hostnames and IPv6 addresses as strings. (B) Emit IPv4 addresses only and treat options as unresolved. (C) Emit options as extra fields.
- Chosen: B.
- Reason: The `ntp_servers` schema is an array of strings with no format rule (88742 to 88746). Hostname resolution and IPv6 behavior are not verified. No option field is verified.
- Risk: A template that uses hostnames gets unresolved items. The reason text names the hostname form.

### D-10 Add the DNS suffix and revise the known-gap sentence

- Alternatives: (A) Leave `ip domain name` unsupported. (B) Add `ip domain name` to `dns_suffix` and revise the first known-gap sentence. (C) Make the sentence depend on the input.
- Chosen: B.
- Reason: Live row C12 names DNS suffixes as a required family. The first sentence at `conversion.py` line 26 says only `ip name-server` converts. That sentence becomes false after the addition. A conditional sentence adds a code path that the evidence does not need.
- Risk: The DNS output text changes for every input. Test 33 pins the change. The DNS values, the unsupported item rules, the review rules, and the export rules stay the same.

### D-11 Keep variable tokens only in allowed fields

- Alternatives: (A) Resolve variables from a site store. (B) Keep `{{name}}` tokens in allowed fields and list each required name. Treat other tokens as unresolved. (C) Reject every token.
- Chosen: B.
- Reason: The OpenAPI descriptions allow variables in six fields. Those fields are the port key (80742), IP (80312), netmask (80326), gateway (80299), VLAN ID (80472), and extra route key (79627). The site variable store is not verified (UV-9).
- Risk: Operators must supply values before apply. The required list makes that work visible.

### D-12 Name generated networks from the VLAN ID

- Alternatives: (A) Use the VLAN names from the source. (B) Name each network `VLAN` followed by the VLAN ID. (C) Name each network after its SVI interface.
- Chosen: B.
- Reason: Source VLAN names are optional and not emitted (D-14). An SVI name such as `Vlan10` repeats the ID, so the form in B gives one name for one ID. The `network` schema requires only `name` (88200 to 88283), so VLAN-only networks are schema-valid.
- Risk: The Mist name rules are unverified (UV-6). Generated names use ASCII letters and digits only.

### D-13 Emit only verified keys

- Alternatives: (A) Emit every key from the schema without a register row. (B) Emit only keys with a register row and an OpenAPI line. (C) Wait for issue #4634 before implementing anything.
- Chosen: B.
- Reason: The issue requires implementation of verified field mappings only. The register makes that rule testable, and test 35 enforces it.
- Risk: A register row can drift from the code. Test 35 reads the register and fails when a key lacks a row.

### D-14 Keep output offline and free of secrets

- Alternatives: (A) Emit interface descriptions and credential values. (B) Omit descriptions and credential values. Label each command without its values.
- Chosen: B.
- Reason: The issue requires no secret in logs or exports. Descriptions can contain customer data. The existing DNS label method omits values, as `conversion.py` line 78 shows.
- Risk: The review loses some description text. Each unresolved item keeps its source line number so the reviewer can check the source.

### D-15 Sequence this record after its prerequisites

- Alternatives: (A) Compose the DNS output and the network fragment here. (B) Leave composition to issue #4641. (C) Start before issue #4638 merges.
- Chosen: B, with the sequence in `plan.md`, section Multi-Agent Sequencing.
- Reason: Composition changes the route and the presentation, which belong to issue #4641. Starting before issue #4638 would overlap on the same converter files.
- Risk: The preview shows only the DNS path until issue #4641 merges. The record states that limit.

### D-16 Add no changelog fragment and no documentation change

- Alternatives: (A) Add a changelog fragment. (B) Add operator documentation. (C) Add no changelog fragment and no operator documentation.
- Chosen: C.
- Reason: The converter is not registered in the shared portal. A search of `web_portal/` finds no `cisco` match. The repository rule for user-visible changes does not apply yet.
- Risk: A later registration needs a fragment. Issue #4641 or the registration issue must add it.

### D-17 Keep the role values from issue #4638

- Alternatives: (A) Map `spoke` to `Branch`. (B) Keep `standalone` and `spoke` until issue #4638 changes the contract. (C) Add Hub support to this record.
- Chosen: B.
- Reason: The gateway template type enum names only `spoke` and `standalone` (80768). Issue #4636 D-11 keeps those values. A Hub maps to a device profile, which issue #4638 owns.
- Risk: The naming differs until issue #4638 merges. Issue #4638 owns the mapping.

### D-18 Decide the credential policy for BGP secrets (HUMAN-DECISION-REQUIRED)

- Alternatives: (A) Convert a Cisco password into a Mist `auth_key`. (B) Map a reference to a credential store after the owner approves a secret-handling design. (C) Omit every credential value and list the line as unresolved.
- Chosen: C until the owner decides. Recommended option: keep C until the owner approves a secret-handling design.
- Reason: The credential policy belongs to the owner. The issue requires omission. Cisco password forms can be reversible or hashed, so a decoding step is unsafe.
- Risk: A BGP session without its password can fail at apply. A later issue must provide a secure path for the operator to supply the value.

## Remote Verification

Each row names one claim. Rows R01 to R33 read files on GitHub `main` through the tree endpoint or the contents endpoint. Row R34 decodes the OpenAPI blob on GitHub `main`. Rows R35 to R50 cite lines of the local copy, whose blob SHA equals the blob on `main` (R34). Rows R51 and R52 read the local installed package in `.venv`. The column `Blob or tree SHA` holds a git object SHA or a tree SHA. It holds `none` for an absent object and `not-a-git-object` for an installed package.

| ID | Claim | Path | Ref | Blob or tree SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | Converter root holds five direct children | src/interfaces/portals/cisco_config_converter | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| R02 | Portal folder holds six direct children | src/interfaces/portals | main | 7f5ac6778b6a7a78ad7268542bb8de2a9c550926 | present | 0 |
| R03 | Converter integration folder holds two children | tests/integration/web_portal/cisco_config_converter | main | 6538f20cdb454342a96e079a0e7678fb6baa7a42 | present | 0 |
| R04 | Contract test folder holds 17 direct children | tests/contract | main | 3e544ef7c55adf7c8a8010e6da3afc345b27d57e | present | 0 |
| R05 | Gateway overrides folder holds five children | tests/unit/marvis/mist/resources/gateway/overrides | main | 7642b0de1d18f1cad5443a04b7b78c38bfc68db6 | present | 0 |
| R06 | Parent record folder exists | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter | main | 2324c91a3e3067c6e0912b76807755fce992e8c1 | present | 0 |
| R07 | Route folder for 4640 is absent | specs/numbered/0/0/1/2/2/0/3/0 | main | none | absent | 0 |
| R08 | Route folder for 4636 is absent | specs/numbered/0/0/1/2/2/0/2/1 | main | none | absent | 0 |
| R09 | conversion.py declares IOSDnsConverter | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 11 |
| R10 | conversion.py imports from models | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 6 |
| R11 | conversion.py defines the convert method | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 15 |
| R12 | routes.py imports IOSDnsConverter from conversion | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 11 |
| R13 | routes.py preview calls IOSDnsConverter.convert | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 80 |
| R14 | models.py declares GatewayTemplate as its first class | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 13 |
| R15 | models.py limits the source kind to standalone and spoke | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 51 |
| R16 | Integration test defines test_complete_offline_journey | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 60 |
| R17 | Unit test defines test_supported_dns_and_unknown_commands | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 50 |
| R18 | Unit test asserts three known gaps | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 65 |
| R19 | CI sets MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R20 | CI sets VULTURE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R21 | CI sets PYDOCSTYLE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R22 | CI sets INTERROGATE_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R23 | Nested package guard sets the child limit to five | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| R24 | Nested package guard counts modules and child directories | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 117 |
| R25 | Route script uses base five | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R26 | Route script checks a parent with five children | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 92 |
| R27 | Live T013 names tests under tests/contract | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 59 |
| R28 | Live T014 names conversion.py | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 60 |
| R29 | Live comparison row C08 covers interface addressing and VLANs | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 92 |
| R30 | Live comparison row C12 covers DNS suffixes, NTP, and variables | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 96 |
| R31 | Live FR-005 requires an explicit role | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 111 |
| R32 | Live FR-007 requires WAN and LAN intent without silent assumptions | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 113 |
| R33 | Live mist.md lists addresses and routing as evidence needed | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 91 |
| R34 | OpenAPI blob on main equals the local file, and the gateway template header is at line 80654 | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80654 |
| R35 | Gateway template type enum names spoke and standalone | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80768 |
| R36 | Gateway extra route next hop is an IPv4 address | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 79613 |
| R37 | DHCP pool property ip_start is the starting address of the lease pool | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 77706 |
| R38 | DHCP pool schema has no exclusion field | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 0 |
| R39 | Gateway port usage enum lists ha_control, ha_data, lan, and wan | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80464 |
| R40 | Gateway port config has an aggregated flag | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80103 |
| R41 | Gateway template port key accepts an aggregated member list | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80742 |
| R42 | VLAN ID for a gateway port accepts 1 to 4094 or a variable | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80472 |
| R43 | Gateway VRF instance holds a networks list only | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80821 |
| R44 | Switch VRF instance owns the extra routes reference | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 113395 |
| R45 | BGP session via property is required | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 71820 |
| R46 | BGP via enum lists lan, tunnel, vpn, and wan | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 71884 |
| R47 | Network vlan_id property accepts a VLAN ID or a variable | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 88265 |
| R48 | NTP servers are an array of strings | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 88742 |
| R49 | DNS suffixes are an array of strings | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 78044 |
| R50 | Gateway IP configuration netmask accepts a prefix length example | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 79671 |
| R51 | createOrgGatewayTemplate takes body as dict or list | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | local-install | not-a-git-object | present | 58 |
| R52 | The pinned mistapi 0.64.1 distribution is installed | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local-install | not-a-git-object | present | 0 |

The count of rows in this table is 52. The STATUS file and the summary state the same count.

## Mist Evidence Summary

The register in `design\contracts\mist-field-register.md` holds one row for each emitted key. The main facts are these.

- The gateway template `type` accepts `spoke` and `standalone` only. The OpenAPI line is 80768.
- The port `usage` accepts `lan` or `wan` for the converter. The enum is at lines 80464 to 80470.
- The port key form accepts `ge-0/0/0`, a range, an aggregated list, or a variable. The description is at lines 80742 to 80744.
- The port IP configuration holds `ip` and `netmask`. The netmask example is a prefix such as `/24`. The IP property is at line 80312, and the netmask property is at line 80326.
- The network object holds `name`, `subnet`, `gateway`, and `vlan_id`. Only `name` is required (88200 to 88283).
- The DHCP pool object holds `type`, `ip_start`, `ip_end`, `gateway`, `dns_servers`, `dns_suffix`, and `lease_time`. The lease default is 86400, and the range is 3600 to 604800 (77579 to 77770).
- The gateway template extra routes object is keyed by destination. Its value holds `via` (79609 to 79627).
- The gateway template BGP object is keyed by session name. It requires `via`. Its `type` enum is `external` or `internal` (71719 to 71900).

## Sources

- `AGENTS.md`, lines 1 to the end. The generic rules for writing, structure, tests, and git flow.
- `.github/copilot-instructions.md`, lines 1 to 640. The local gates table, the Five-Item Rule for the converter, and the STE gate command.
- `.specify/memory/constitution.md`, lines 1 to 180. Principles I to IV.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. The headings used by this record.
- `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/` (remote R06). The parent record. Used for context only.
- `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`. The full-parity record from PR #4596. The rows that this record cites appear in `tasks.md` lines 58 to 60, `design/research.md` lines 92 to 96, `design/contracts/mist.md` lines 89 to 91, and `spec.md` lines 111 and 113.
- `src/interfaces/portals/cisco_config_converter/conversion.py`, lines 6, 8, 11, 15, 17, 25 to 28, 56, and 78.
- `src/interfaces/portals/cisco_config_converter/models.py`, lines 13, 21, 29, 38, 51, and 84.
- `src/interfaces/portals/cisco_config_converter/routes.py`, lines 11, 12, 73, and 80.
- `tests/integration/web_portal/cisco_config_converter/test_routes.py`, lines 60, 80, and 171. The test patches sockets and file opens during the offline journey.
- `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`, lines 50, 65, 78, and 85.
- `documentation/mist-api-openapi31yaml.yaml`, the line numbers cited in the remote verification table. The blob SHA matches `main`.
- `.venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py`, lines 58 to 60.
- `spec-drafts\4636\plan.md`, `tasks.md`, `analysis.md`, and `_meta\4636-STATUS.json`. The sibling decisions D-1, D-2, D-11, and the sibling defects.
- `.specify\scripts\powershell\spec-route.ps1`, lines 17, 18, 26, and 92. The base-5 route rule. The route for 4640 is `0/0/1/2/2/0/3/0`.

No web page was fetched. No URL is listed because no page was used.

## Unverified

- UV-1: The Cisco IOS command forms in the fixtures. No Cisco reference was fetched in this pass. No local grammar source exists. The reason is that the source parser may not be reused.
- UV-2: The interaction of `ip_start` and `ip_end` with the gateway address. The schema text gives the first and last address of the pool. The converter lists each gateway conflict as unresolved. Issue #4634 must confirm the interaction.
- UV-3: The `disabled` property. The property name and its description point in opposite directions (lines 80118 and 80120). No `shutdown` value is emitted.
- UV-4: The representation of `ae_idx`. The schema type is `string` or `null`, and the description states an integer from 0 to 127 (lines 80089 to 80094).
- UV-5: The representation of `neighbor_as`. The referenced schema `bgp_as` starts at line 71709, and its content was not reviewed.
- UV-6: The naming rules for Mist networks. The schema gives no length or character rule.
- UV-7: VRF support per SRX and SSR model. The `vrf_config.enabled` description says "when supported on the device" (line 118048). The converter does not emit the key until issue #4638 confirms support.
- UV-8: The meaning of `bgp_config.networks` as names or prefixes. The schema text says networks for neighbor connections (line 71798).
- UV-9: The site variable store and its schema for `{{name}}` values. The `vars` schema at line 117442 describes WLAN variables. The example in that schema holds a credential-like value, which this record does not copy.
- UV-10: The `networks` property of `deviceprofile_gateway`, which carries the Hub target. The property names at lines 77255 to 77363 were read, but `networks` was not checked.
- UV-11: Port name grammar beyond the examples `ge-0/0/0`, ranges, and aggregated lists. The converter validates the form `ge-<fpc>/<pic>/<port>` as its own rule.
- UV-12: Speed and duplex values. The schema gives format examples only.
- UV-13: The content of the `strings` schema at line 111562, which the VRF networks list references. The record assumes an array of strings.
- UV-14: The mistapi signature of the future write method is cited but not executed.
- UV-15: The composed proposal and the second known-gap sentence. Issue #4641 owns them.
