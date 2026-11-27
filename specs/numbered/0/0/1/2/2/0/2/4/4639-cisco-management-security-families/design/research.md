# Research: Review management and security configuration families

## Evidence Boundary

- Remote `main` and local HEAD both point to commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.
- The OpenAPI YAML file and the converter module have the same blob SHA locally and on `main` (R42, R26). Line citations therefore match the remote files.
- Every repository, source, and SDK claim in this record has one row in the remote verification table below.
- This pass ran read-only operations only. No build, test, linter, package install, container, or GitHub write ran.

## Sources

- Repository `jmorrison-juniper/MistHelper` on `main`. Read with `gh api` contents and git tree calls.
- Issue 4639. Read with `gh issue view`. Title, body, labels (`feature`, `web-portal`), and state (open) were recorded. The issue has no comments.
- PR 4596, the full-parity task map. Merged on 2026-11-13. Read with `gh pr view` and from the remote `main` branch.
- Linked pull requests for `4639`. `gh pr list --search 4639` returned an empty list.
- Program issues 4224 and 4634 to 4649. Read with `gh issue list` (400 items fetched, 17 matched).
- Legacy record search. No folder beginning with `4639-` exists under local `specs\` or in the remote tree (R16).
- Local drafts for issues 4636 and 4649, not on `main`. These drafts are `spec-drafts\4636` and the `_meta` status and summary files. They set the pattern for decisions D-1 and D-2 (test folder and module placement) and for the owner decision in D-14.
- Source mapping document S4. Fetched with `gh api` from `https://api.github.com/repos/jmorrison-juniper/MistCiscoConfigConverter/contents/docs/CISCO_TO_MIST_MAPPING.md?ref=d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c`. Observation only. Issue 4635 decides any reuse.
- Installed SDK. `.venv\Lib\site-packages\mistapi`, version 0.64.1. Read with view and grep only.
- Mist API. `documentation\mist-api-openapi31yaml.yaml`, read in line ranges. The JSON twin is one line and gives no line citations (R25).
- Skill `juniper-flow-monitoring`, base directory `C:\Users\jmorrison\.copilot\skills\juniper-flow-monitoring`. Used for device-side context on flow export. No Mist mapping depends on it.
- Skill `juniper-high-availability`, base directory `C:\Users\jmorrison\.copilot\skills\juniper-high-availability`. Used for device-side context on redundancy. No Mist mapping depends on it.
- Endpoint inventories `documentation\MIST_API_GET_ENDPOINTS.md` and `documentation\MIST_API_MISSING_ENDPOINTS.md`. The site setting read is covered (R83). The missing list has no write entries for the paths in this issue (R84). The parent contract record holds the write inventory (R24 cites it).
- `documentation\container-deployment.md` and `documentation\development-setup.md`. This issue starts no test container and runs no bootstrap, so their rules do not change the plan.

## Family Dispositions

| ID | Family | Source row | Disposition | Evidence | Main reason |
| --- | --- | --- | --- | --- | --- |
| MGT-01 | Syslog | C13 | conditional | E-01, E-02, E-05 | Site settings hold remote syslog (R43). Gateway templates and gateway device profiles do not (R45, R46). |
| MGT-02 | SNMP | C13 | conditional | E-03, E-08 | Site settings hold location and contact (R48). Communities are secrets (R50). |
| MGT-03 | Management egress | C13 | display-only | E-05 | Host-out policies sit at organization scope and set path preference (R51, R52, R79). |
| MGT-04 | AAA | C14 | display-only | E-06 | Gateway templates have no AAA property (R46). RADIUS secrets are secrets (R53). |
| MGT-05 | TACACS | C14 | display-only | E-06, E-08 | TACACS sits in the switch management object (R54, R77). |
| MGT-06 | Local accounts | C14 | display-only | E-06, E-08 | Local account passwords sit in the switch configuration schema (R55). |
| MGT-07 | ACL | C15 | display-only | E-07 | No ACL property exists on the gateway template (R46). |
| MGT-08 | Class | C15 | display-only | E-07 | No class property exists on the gateway template (R46). |
| MGT-09 | Policy | C15 | display-only | E-07 | Service policies exist (R47), but no verified source pair exists. |
| MGT-10 | Zone | C15 | display-only | E-07 | No zone property exists on the gateway template (R46). |
| MGT-11 | Crypto | C15 | display-only | E-07, E-08 | The IPsec pre-shared key is a secret (R64). No verified source pair exists. |
| MGT-12 | Cellular | C16 | conditional | E-04, E-08 | The gateway port configuration holds the LTE APN (R56). The password is a secret (R57). |
| MGT-13 | Redundancy | C16 | display-only | E-07 | No HSRP property exists (R62). VRRP is a different protocol (R63). |
| MGT-14 | Flow export | C17 | display-only | E-07 | No flow export property exists (R61). The source states no native support (R80). |

## Decisions

### D-1 Management test folder

- Decision: Put the management tests in `tests/integration/web_portal/cisco_config_converter/management/test_management.py`.
- Alternatives: (a) `tests/contract/cisco_config_converter/`, as the parent task states. (b) `tests/unit/marvis/mist/resources/gateway/overrides/`, beside the DNS unit tests.
- Reason: `tests/contract/` already holds 17 direct children (R35). The constitution forbids a new child under a noncompliant parent (R07). The converter integration folder already holds the route tests (R33).
- Risk: Contract-style tests sit in the integration folder. The test names state the contract type.
- Human decision: No.

### D-2 Review code location

- Decision: Add two classes to `conversion.py`. Add no module under `src/interfaces/portals/cisco_config_converter/`.
- Alternatives: (a) A new module `management.py` in the package root. (b) A new nested package under the converter. (c) New logic in `models.py`.
- Reason: The package root already holds five children (R38). A new module makes six children, which breaks the five-item rule (R07). Issue 4636 replaces `models.py` (local draft), so new logic there conflicts with that work.
- Risk: `conversion.py` grows. The two classes stay small, and the complexity gate checks them.
- Human decision: No.

### D-3 Data contract only

- Decision: This issue delivers the review data contract. Issue 4637 displays it. Issue 4641 places it in the proposal.
- Alternatives: (a) Change `routes.py` and the presentation files now. (b) Add a key to `ConversionProposal` in `models.py`. (c) Add a new route.
- Reason: The route and presentation files belong to issues 4637 and 4641 (parent tasks T010 and T018). The issue body excludes navigation changes. A changed `ConversionProposal` would alter the shape that the DNS tests check (R31, R32).
- Risk: No management section appears in the portal until issue 4637 lands. The contract tests fix the shape that the display uses.
- Human decision: No.

### D-4 Secret omission with fixed labels

- Decision: Omit every secret value. Show the matched keyword phrase, the secret keyword, and a fixed marker.
- Alternatives: (a) Mask the characters with asterisks. (b) Show a digest of the value. (c) Decode a reversible value for review.
- Reason: Masks reveal length and pattern. A digest gives a guessing target for a weak secret. Decoding breaks the security rule (R02, R08). The DNS converter already omits unsupported values (R29).
- Risk: A reviewer cannot confirm a value from the review. The reviewer checks the source file.
- Human decision: No.

### D-5 Hashes and reversible values

- Decision: Treat one-way hashes and reversible type 7 values the same way. Never decode, reconstruct, or display them.
- Alternatives: (a) Decode type 7 because it is weak. (b) Show the scheme type and omit the hash text. (c) Compute a fingerprint for matching.
- Reason: The issue forbids decoded values and reconstructed hashes. Type 7 is a reversible encoding, so the record treats it as a secret. A scheme label gives an attacker a target.
- Risk: Two hashes cannot be compared in the review. The line number stays visible for the reviewer.
- Human decision: No.

### D-6 No device command

- Decision: Generate no device command. Never write `additional_config_cmds` or any raw command field (R59).
- Alternatives: (a) Generate Junos flow commands in the style of source line 708 (R81). (b) Write generated text to the raw command field. (c) Generate commands for display only.
- Reason: The issue forbids raw commands as a substitute for a verified mapping. No verified flow export field exists (R61). Display-only commands still form a copyable command set.
- Risk: Some flow export needs stay unmet. The family limit states that no command is generated.
- Human decision: No.

### D-7 Syslog placement

- Decision: Map `logging host` only to `site_setting.remote_syslog.servers[].host` for Branch and Standalone roles, after evidence E-01. Keep Hub syslog display-only.
- Alternatives: (a) Map Hub syslog to the gateway device profile, as source line 640 states (R75). (b) Map syslog to the gateway template. (c) Hold all syslog until the source claims agree.
- Reason: The OpenAPI gives remote syslog for gateways only in site settings (R43). The gateway device profile lacks the property (R45), and the gateway template lacks it too (R46). Source line 177 agrees with site settings only (R73). Source lines 623 and 640 do not (R74, R75). The OpenAPI decides, so Hub stays display-only.
- Risk: Hub sites receive no mapped syslog. The family limit states the gap. Review this decision when a Hub field appears in the schema.
- Human decision: No.

### D-8 Host-out is not a destination

- Decision: Never map `logging host` to host-out policies or to the per-policy syslog flag.
- Alternatives: (a) Map `logging host` to the organization host-out setting (R51). (b) Map it to the per-policy remote logging property (R60).
- Reason: The host-out setting controls path preference for gateway-originated traffic (R79). It sits at organization scope (R51), so one write changes every site. Its description applies remote logging per service policy (R60). This record does not map it to the gateway system log.
- Warning: A write to organization scope changes gateway traffic at every site. This issue writes nothing.
- Risk: None for this issue.
- Human decision: No.

### D-9 SNMP scope

- Decision: Map `snmp-server location` and `snmp-server contact` to `site_setting.snmp_config` after evidence E-03. Omit communities and SNMPv3 credentials. Keep trap targets display-only.
- Alternatives: (a) Map communities to the v2c configuration (R50). (b) Map trap targets now. (c) Skip SNMP.
- Reason: The OpenAPI has no top-level community property (R49). Source line 522 names one (R78), so the source conflicts with the OpenAPI. Communities are secrets (R50). Location and contact are identity data and stay out of logs. Trap targets lack verified field semantics.
- Risk: Trap targets stay unmapped. The family limit states it.
- Human decision: No.

### D-10 AAA, TACACS, and local accounts

- Decision: Keep AAA, TACACS, and local accounts display-only for gateways.
- Alternatives: (a) Map switch-scope TACACS fields to gateways. (b) Map the site RADIUS configuration to Cisco AAA. (c) Write local accounts to a gateway template.
- Reason: The gateway template has no such property (R46). TACACS sits in the switch management object (R54). Source line 514 names the same switch object (R77). Local account passwords sit in the switch configuration schema (R55). The site RADIUS secret (R53) needs a verified role mapping first.
- Risk: AAA stays unmapped. The family limit states the scope.
- Human decision: No.

### D-11 Cellular APN

- Decision: Map a cellular APN line to the `lte_apn` property of the selected LTE port in `gateway_template.port_config` after evidence E-04. The port must be an LTE port on a supported model. Omit the username and password.
- Alternatives: (a) Keep cellular display-only. (b) Map the username and password. (c) Map the authentication method and backup flag now.
- Reason: The OpenAPI has an APN property (R56) and an LTE WAN type (R58). The password is a secret (R57). The username is part of the credential pair, so it stays out. The authentication method and backup flag need confirmed Cisco forms (U-7).
- Risk: One cellular field maps. The family limit states the scope.
- Human decision: No.

### D-12 Display-only families

- Decision: Keep management egress, ACL, class, policy, zone, crypto, redundancy, and flow export display-only.
- Alternatives: (a) Map VRRP to HSRP. (b) Map the IPsec object to Cisco crypto. (c) Generate flow export commands, which D-6 rejects.
- Reason: The OpenAPI has no HSRP property (R62). VRRP sits in switch and site schemas (R63), and it uses a different protocol. The IPsec pre-shared key is a secret (R64). No ACL, class, or zone property exists on the gateway template (R46). No flow export field exists (R61). The skill `juniper-high-availability` describes VRRP and chassis mechanisms as separate features.
- Risk: Parity gaps stay visible. Issue 4649 must accept each one (D-14).
- Human decision: No.

### D-13 Unsupported models

- Decision: An unsupported model produces a model limit, not a mapping.
- Alternatives: (a) Infer the model from a hostname. (b) Block the review for unknown models. (c) Map every model.
- Reason: Hardware support belongs to issue 4638. A hostname is not verified source data. Blocking the review would stop DNS users.
- Risk: The reviewer sees a limit where a mapping could exist. The model table from issue 4638 can remove the limit.
- Human decision: No.

### D-14 Parity dispositions

- Decision: Owners approve the eleven display-only dispositions for MGT-03 to MGT-11, MGT-13, and MGT-14.
- Alternatives: (a) Require mapping evidence for every family before parity closes. (b) Accept the dispositions without review. (c) Defer the decision to issue 4649.
- Reason: Parity closure needs an owner decision for each unsupported row (parent task T033). The list is short. An owner, not an agent, accepts an unsupported disposition.
- Risk: The owner rejects a disposition. The family then needs new evidence and new work.
- Human decision: Yes. Recommended option: accept all eleven dispositions for issue 4649. MGT-01, MGT-02, and MGT-12 stay conditional and need no decision now.

### D-15 Changelog fragment

- Decision: Add one changelog fragment with this change set. Name it `issue-4639-management-security-families.md` until the pull request exists.
- Alternatives: (a) Add no fragment until the visible display ships in issue 4637. (b) Add a fragment only for user-visible changes.
- Reason: The constitution requires one fragment for each change (R82). Options (a) and (b) each limit the rule to some changes, and the constitution does not limit it.
- Risk: A reviewer may find a fragment for a specification unusual. The fragment text states that the change is a specification.
- Human decision: No.

### D-16 Serialize shared converter edits

- Decision: Finish issue 4640 task T014 before task T007 starts. Both tasks edit `conversion.py`.
- Alternatives: (a) Edit in parallel and rebase later. (b) Combine both tasks into one change.
- Reason: The parent rule forbids parallel edits to shared converter files (R20). The parent dependency row omits the edge (R19). A combined change would mix two issues.
- Risk: T007 waits for issue 4640. The schedule grows.
- Human decision: No.

## Mapping Evidence by Family

- Syslog. The site setting has a remote syslog object (R43). Its server item lists host, port, protocol, facility, severity, and source address (R44). Only the host maps in this issue. The other options stay display-only until E-01 records their enumerations.
- SNMP. The site setting holds an SNMP object (R48). Its location and contact properties are strings. Its v2c communities and SNMPv3 credentials are secrets (R50, R65 scan).
- Management egress. The host-out policy object appears only in the organization gateway management setting (R51). The gateway management object has no host-out property (R52).
- AAA and TACACS. The gateway template has no AAA property (R46). The site RADIUS secret (R53) and the switch management object (R54) do not give a gateway field.
- Local accounts. The local account password sits in the switch configuration schema (R55).
- Policy. The gateway template holds service policies (R47). The service policy syslog property applies remote logging per policy (R60). This record does not map it.
- Cellular. The gateway port configuration holds the LTE APN, authentication, backup, username, and password fields (R56). The LTE WAN type exists (R58). The password is a secret (R57).
- Redundancy. No HSRP property exists (R62). VRRP group settings sit in site settings (R63).
- Flow export. No flow export property exists (R61). The source states no native support (R80) and gives Junos commands (R81).
- Raw commands. The gateway template exposes a raw command property (R59). The converter never writes it.

## Secret Handling

- The secret keyword list and the field register are in `design/contracts/secret-redaction.md`.
- The Cisco keyword list includes `password`, `secret`, `key`, `key-string`, `community`, `passphrase`, `psk`, `auth`, and `priv`.
- A type 5, 7, 8, or 9 value follows the same omission rule as a plain value.
- The existing operator guide states that the portal redacts secrets before it saves results (R40).

## Unverified

- U-1. The JSON and YAML twins agree for each pointer. Reason: the JSON file is one line of 3.6 MB, so it gives no line comparison. Next step: task T001.
- U-2. LTE support for each model and the port identifiers. Reason: the model matrix belongs to issue 4638. Next step: task T008.
- U-3. Enumerations for syslog severity, facility, and protocol. Reason: this pass read the field names and the protocol and severity enumeration schemas only by name (remote syslog schemas near R42 and R44). Next step: task T001.
- U-4. The TACACS secret field name in the switch schema. Reason: source line 514 names a server secret, but the property scan did not isolate it. Next step: task T001.
- U-5. A length bound for SNMP location and contact text. Reason: the schema lines read this pass give a type and no maximum length. Next step: task T001.
- U-6. Live gateway behavior for the Hub schema absence. Reason: this pass made no live Mist request, per brief rule 1. The absence is schema evidence only.
- U-7. Cisco command forms in the fixtures. Reason: no Cisco command reference was fetched. Next step: task T003.
- U-8. Reuse rights for the source document. Reason: the source license decision belongs to issue 4635.
- U-9. Device-side statements from the Juniper skills. Reason: the statements give context only. No mapping depends on them.

## Remote Verification Table

Columns: ID, claim, path, reference, blob SHA, result, line. A line of 0 means a whole-file or whole-folder check. The blob SHA `absent` means the path is absent on the reference. The blob SHA `n/a-local` means an installed local file with no Git blob.

| ID | Claim | Path | Reference | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R01 | STE writing rules for prose | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R02 | Secret handling rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 172 |
| R03 | Five-children structure and function limits | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 77 |
| R04 | Local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R05 | STE gate command row | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R06 | Managed Spec Kit roots and numeric route rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| R07 | Five-item rule and noncompliant parent rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 43 |
| R08 | Secrets never appear in logs or outputs | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 134 |
| R09 | Secrets never logged | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 196 |
| R10 | Class-based architecture rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 91 |
| R11 | CI workflow source for gate path variables | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 0 |
| R12 | Spec headings template | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R13 | Plan headings template | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R14 | Tasks headings template | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R15 | Checklist headings template | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R16 | Target record route is free on main | specs/numbered/0/0/1/2/2/0/2/4 | main | absent | absent | 0 |
| R17 | Parent task T015 names the management test path | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 61 |
| R18 | Parent task T016 names the converter module | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 62 |
| R19 | Parent dependency row for T016 lists T012 and T015 only | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 140 |
| R20 | Parent rule forbids parallel edits to shared converter files | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 174 |
| R21 | FR-008 requires review of the management families | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 114 |
| R22 | Comparison row C13 covers syslog, SNMP, and management egress | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 97 |
| R23 | Research line 59 names a unit test path that is absent | tests/unit/gateway/overrides/test_cisco_config_converter.py | main | absent | stale | 59 |
| R24 | Mapping contract records inconsistent syslog placement statements | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 103 |
| R25 | JSON OpenAPI twin is one line and gives no line citations | documentation/mist-api-openapi31json.json | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | partial | 0 |
| R26 | IOSDnsConverter class handles the DNS subset | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 11 |
| R27 | Banner delimiter method in the DNS converter | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 67 |
| R28 | Generic label for unsupported source lines | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 83 |
| R29 | Known gap says unsupported values are omitted to protect credentials | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 28 |
| R30 | Source kind accepts only standalone and spoke | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 51 |
| R31 | DNS test asserts the unsupported item count and known gap count | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 64 |
| R32 | DNS test asserts one unsupported item for each rejected directive | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 83 |
| R33 | Route test file exists in a folder with two children | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 0 |
| R34 | Target management test path is absent | tests/contract/cisco_config_converter/test_management.py | main | absent | absent | 0 |
| R35 | tests/contract holds 17 direct children | tests/contract | main | 3e544ef7c55adf7c8a8010e6da3afc345b27d57e | present | 0 |
| R36 | Process folder guard test exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| R37 | Shared portal host file exists and stays unchanged | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 0 |
| R38 | Converter package root holds five children | src/interfaces/portals/cisco_config_converter | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| R39 | mistapi pin in requirements | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R40 | Operator guide states that the portal redacts secrets before it saves results | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 363 |
| R41 | Quality gates document has no converter gate | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | absent | 0 |
| R42 | Remote syslog schema lists enabled, servers, and console properties | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 92510 |
| R43 | Site settings hold a remote syslog property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 101532 |
| R44 | Remote syslog server item lists host, port, protocol, facility, severity, and source address | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 92672 |
| R45 | Gateway device profile has no remote syslog or SNMP property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 77247 |
| R46 | Gateway template has no syslog, SNMP, RADIUS, switch, ACL, zone, class, crypto, or redundancy property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 80654 |
| R47 | Gateway template holds a service policies property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80755 |
| R48 | Site settings SNMP object references the SNMP schema, which has a location property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 104026 |
| R49 | SNMP schema has no top-level community property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 103999 |
| R50 | SNMP v2c configuration holds a community name property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 104150 |
| R51 | The host-out policies property appears only in the organization gateway management setting | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 89924 |
| R52 | Gateway management schema has no host-out policy property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 79760 |
| R53 | RADIUS authentication server holds a secret property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 92282 |
| R54 | Site settings hold a switch management property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 101589 |
| R55 | Local account user schema holds a password property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 74305 |
| R56 | Gateway port configuration holds LTE APN, authentication, backup, and credential properties | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80141 |
| R57 | Gateway port configuration holds an LTE password property with password format | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80151 |
| R58 | WAN type property accepts the LTE value | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80280 |
| R59 | Gateway template holds a raw additional configuration commands property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 80657 |
| R60 | Service policy schema holds a syslog property for per-policy remote logging settings | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 100034 |
| R61 | No NetFlow, IPFIX, jFlow, or flow export property exists | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 0 |
| R62 | No HSRP property exists | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | 0 |
| R63 | Site settings hold a VRRP group property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 101668 |
| R64 | Pre-shared key schema holds a passphrase property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 91739 |
| R65 | Gateway management schema holds a root password property | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 79811 |
| R66 | Scan of secret-named properties returns 76 hits, including SNMP v3 user passwords | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 0 |
| R67 | Installed mistapi version is 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | mistapi==0.64.1 pin (R39) | n/a-local | present | 0 |
| R68 | updateSiteSettings takes the session, site identifier, and body | .venv\Lib\site-packages\mistapi\api\v1\sites\setting.py | mistapi==0.64.1 pin (R39) | n/a-local | present | 42 |
| R69 | updateSiteSettings sends a PUT to the site setting path | .venv\Lib\site-packages\mistapi\api\v1\sites\setting.py | mistapi==0.64.1 pin (R39) | n/a-local | present | 69 |
| R70 | updateOrgGatewayTemplate definition | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | mistapi==0.64.1 pin (R39) | n/a-local | present | 145 |
| R71 | updateOrgDeviceProfile definition | .venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py | mistapi==0.64.1 pin (R39) | n/a-local | present | 150 |
| R72 | Source table gives remote syslog NO for gateway template and device, and YES for site settings | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 174 |
| R73 | Source key finding says gateway logging is site settings only | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 177 |
| R74 | Source storage table gives the Hub device profile as syslog storage | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 623 |
| R75 | Source says the Hub device profile stores literal syslog values | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 640 |
| R76 | Source switch table gives remote syslog YES for the network template | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 202 |
| R77 | Source maps TACACS servers to the switch management object | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 514 |
| R78 | Source maps the SNMP community to snmp_config.community | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 522 |
| R79 | Source says host-out policies control gateway management path preference | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 349 |
| R80 | Source states no native flow export configuration support | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 699 |
| R81 | Source lists Junos flow export commands | jmorrison-juniper/MistCiscoConfigConverter:docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 708 |
| R82 | Constitution documentation section requires one changelog fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R83 | Endpoint inventory lists the site setting read as covered | documentation/MIST_API_GET_ENDPOINTS.md | main | 6281c11b46f22b9814a1948a96df9be4945fb8fd | present | 1456 |
| R84 | Missing endpoint list has no PUT site setting or gateway template entry | documentation/MIST_API_MISSING_ENDPOINTS.md | main | e4949ef2ab2ed1d86e6309bd919401d65b2c0ae0 | absent | 0 |
| R85 | Constitution principle IV requires the post-merge build and deployment steps | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 143 |
