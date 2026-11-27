# Contract: Mist evidence rows for management families

Status: Specified. Every row starts as pending or as the status stated below. Issue 4634 records the verified rows in its own contract file. Task T001 checks each row before task T008.

## Rules for Each Row

- The pointer names the OpenAPI schema path in `documentation/mist-api-openapi31yaml.yaml`.
- The SDK signature names the installed mistapi function and its definition line.
- The positive fixture is a synthetic input with a simulated response. The negative fixture is a synthetic input that the mapping must reject.
- A row becomes verified-present only when the pointer, the SDK signature, and both fixtures pass.
- A row becomes absent when a read-only check finds no property. An absent row keeps its family display-only.
- A row becomes stale when a later pointer check fails. A stale row removes its mapping entry from the registry.

## Evidence Rows

| ID | Question | Repository rows | Status in this record | Owner | Required fixtures |
| --- | --- | --- | --- | --- | --- |
| E-01 | Does site settings remote syslog accept a server host, and which server fields exist? | R42, R43, R44 | pending. The enumerations for severity, facility, and protocol are open (research U-3). | Issue 4634 | Positive host fixture for an IPv4 address and a DNS name. Negative fixture for an invalid host. Negative fixture for an unmapped option. |
| E-02 | Does a gateway device profile accept a syslog destination? | R45, R75 | absent. The gateway device profile lacks the property. Source line 640 disagrees, and the OpenAPI decides. | Issue 4634 | Negative fixture: a Hub role gives display-only status. |
| E-03 | Do site settings SNMP location and contact accept text? | R48, R49, R50, R66 | pending for location and contact. The length bound is open (research U-5). The community is absent as a top-level field and is a secret. | Issue 4634 | Positive fixture for location and contact. Negative fixture: a community line is secret-omitted. |
| E-04 | Does gateway port configuration accept an LTE APN for a supported model? | R56, R57, R58 | pending. The model table belongs to issue 4638 (research U-2). The password is a secret. | Issues 4634 and 4638 | Positive APN fixture for a supported LTE model. Negative fixture for an unsupported model. |
| E-05 | Does the host-out setting or the service policy syslog property receive a logging host? | R51, R52, R60, R79 | absent for system log destinations. Host-out is organization scope and sets path preference. The service policy setting applies per policy. | Issue 4634 | Negative fixture: a logging host line never maps to a host-out or service policy field. |
| E-06 | Do AAA, TACACS, and local account fields apply to gateways? | R46, R53, R54, R55, R77 | absent for the gateway template. Site settings and switch objects hold the fields. | Issue 4634 | Negative fixture: an AAA or TACACS line gives display-only status for a gateway. |
| E-07 | Do ACL, class, policy, zone, crypto, redundancy, and flow export have verified gateway fields? | R46, R47, R61, R62, R63, R64 | absent for ACL, class, zone, redundancy, and flow export. Pending for policy and crypto. | Issue 4634 | Negative fixture for each absent family. Policy and crypto fixtures wait for the review of R47 and R64. |
| E-08 | Which fields hold secret values? | R50, R53, R55, R57, R64, R65, R66, R77 | verified-present for the names in R50, R53, R55, R57, R64, and R65. The TACACS field name is pending (research U-4). | Issue 4634 | Secret omission fixture for each verified name. |

## Candidate Mistapi Functions

| Target | Function | Installed definition | Repository row |
| --- | --- | --- | --- |
| Site settings for E-01 and E-03 | `mistapi.api.v1.sites.setting.updateSiteSettings` | `updateSiteSettings(mist_session, site_id, body)`, PUT at line 69 | R68, R69 |
| Gateway port configuration for E-04 | `mistapi.api.v1.orgs.gatewaytemplates.updateOrgGatewayTemplate` | Definition at line 145. Task T001 records the arguments. | R70 |
| Gateway device profile for E-02 | `mistapi.api.v1.orgs.deviceprofiles.updateOrgDeviceProfile` | Definition at line 150. Used only for the negative check. | R71 |

The installed signatures accept a generic `body` dictionary. The OpenAPI pointer is the field contract. A call that forwards arbitrary arguments is prohibited.

## Mapping Entry Requirements

Each mapping entry in the registry holds these fields.

1. Keyword phrase from the allow-list.
2. Family ID.
3. Field path.
4. OpenAPI pointer.
5. Evidence ID with status verified-present.
6. Mistapi function name and definition line.
7. Roles that may use the entry.
8. Models that may use the entry.
9. Value rule.
10. Positive fixture ID.
11. Negative fixture ID.

## Unmapped Candidates

The following candidates stay unmapped in this issue. Each one has a recorded reason.

- Syslog severity, facility, and protocol. Reason: enumerations are open (research U-3).
- Syslog source network. Reason: the source address semantics are not verified.
- SNMP trap targets. Reason: the trap group semantics are not verified.
- LTE authentication method and backup flag. Reason: the Cisco forms need confirmation (research U-7).
- The LTE username. Reason: it belongs to the credential pair.
- Organization gateway management settings. Reason: organization scope changes every site.
- Switch management settings. Reason: switch scope does not apply to gateways.
