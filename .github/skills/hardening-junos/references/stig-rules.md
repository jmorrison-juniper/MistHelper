# DISA STIG rules for Juniper EX switches

## Platform scope

These rules come from the EX switch STIG bundle, `U_Juniper_EX_Switches_Y26M07_STIG`.
The bundle includes Layer 2 Switch V2R5, Network Device Management V2R5, and Router V2R1.
The Network Device Management set covers device management. Many controls can inform another
Junos platform. The Layer 2 Switch set covers layer 2 switching. An MX router or an SRX firewall
can use those functions differently.

If your device is an MX router or an SRX firewall, get the STIG for that platform. This corpus
does not hold it. When the platform does not match, use this file only as a pointer for questions.
Verify the rule in the platform STIG before you act.

## How to use this file

DISA names a Security Technical Implementation Guide, or STIG, as a hardening standard.
DISA requires a STIG for many Department of Defense systems.
A NOC engineer uses a STIG to compare a Junos configuration with required controls.
Use each row as a quick check, not as the full authority.

This condensed file stays inside the skill budget.
This file does not copy the full DISA description, check text, or fix text.
Open the XCCDF file in the staged DISA corpus for the complete check and fix text.
The paths below are relative to the staged corpus root, not to this repository.

## Source files

| Rule set | Rules | XCCDF file |
| - | -: | - |
| Layer 2 Switch, V2R5 | 24 | `U_Juniper_EX_Switches_Y26M07_STIG\U_Juniper_EX_Switches_L2S_V2R5_Manual_STIG\U_Juniper_EX_Switches_L2S_STIG_V2R5_Manual-xccdf.xml` |
| Network Device Management, V2R5 | 55 | `U_Juniper_EX_Switches_Y26M07_STIG\U_Juniper_EX_Switches_NDM_V2R5_Manual_STIG\U_Juniper_EX_Switches_NDM_STIG_V2R5_Manual-xccdf.xml` |
| Router, V2R1 | 102 | `U_Juniper_EX_Switches_Y26M07_STIG\U_Juniper_EX_Switches_RTR_V2R1_Manual_STIG\U_Juniper_EX_Switches_RTR_STIG_V2R1_Manual-xccdf.xml` |

## Severity spread

| Rule set | High | Medium | Low | Total |
| - | -: | -: | -: | -: |
| Layer 2 Switch, V2R5 | 2 | 18 | 4 | 24 |
| Network Device Management, V2R5 | 13 | 41 | 1 | 55 |
| Router, V2R1 | 10 | 63 | 29 | 102 |
| **Total** | **25** | **122** | **34** | **181** |

## Condensed rule table

The table gives one statement for Junos when the fix procedure names it.
Some procedures need more statements than this table shows.
Open the XCCDF file before you change a production device.

### Layer 2 Switch, V2R5

Rule count: 24. Severity spread: high 2, medium 18, low 4.

| STIG ID | Severity | Requirement | Junos statement |
| - | - | - | - |
| JUEX-L2-000010 | high | Disable non-essential capabilities | `delete system services finger` |
| JUEX-L2-000020 | high | Uniquely identify all network-connected endpoint devices before establishing any connection | `set access radius-server <RADIUS IPv4 or IPv6 address> secret "<PSK>"` |
| JUEX-L2-000030 | medium | Disable all dynamic VLAN registration protocols | `delete protocols mvrp` |
| JUEX-L2-000040 | medium | Manage excess bandwidth to limit the effects of packet flooding types of denial-of-service (DoS) attacks | `set class-of-service classifiers dscp <classifier name> import default` |
| JUEX-L2-000050 | medium | Permit authorized users to select a user session to capture | `set forwarding-options analyzer <analyzer name> input ingress interface <input interface>.<logical unit>` |
| JUEX-L2-000060 | medium | Permit authorized users to remotely view, in real time, all content related to an established user session from a component separate from the layer 2 switch | `set vlans <destination VLAN name> vlan-id <VLAN ID>` |
| JUEX-L2-000070 | medium | Authenticate all network-connected endpoint devices before establishing any connection | `set access radius-server <RADIUS IPv4 or IPv6 address (global)> secret "<PSK>"` |
| JUEX-L2-000080 | low | Enable Root Protection on STP switch ports connecting to access layer switches | `set protocols mstp interface <interface name> no-root-port` |
| JUEX-L2-000090 | medium | Enable BPDU Protection on all user-facing or untrusted access switch ports | `set protocols mstp bpdu-block-on-edge` |
| JUEX-L2-000100 | medium | Enable STP Loop Protection on all non-designated STP switch ports | `set protocols rstp interface <interface name> bpdu-timeout-action block` |
| JUEX-L2-000120 | medium | Enable DHCP snooping for all user VLANs with active access interfaces to validate DHCP messages from untrusted sources | `set vlans <untrusted VLAN name> vlan-id <untrusted VLAN ID>` |
| JUEX-L2-000130 | medium | Enable IP Source Guard on all user-facing or untrusted access VLANs with active access interfaces | `set vlans <untrusted VLAN name> vlan-id <untrusted VLAN ID>` |
| JUEX-L2-000140 | medium | Enable Dynamic Address Resolution Protocol (ARP) Inspection (DAI) on all user VLANs with active access interfaces | `set vlans <untrusted VLAN name> vlan-id <untrusted VLAN ID>` |
| JUEX-L2-000150 | low | Enable Storm Control on all host-facing access interfaces | `set forwarding-options storm-control-profiles profile-percent all bandwidth-percentage (1..100)` |
| JUEX-L2-000160 | low | Enable IGMP or MLD Snooping on all VLANs | `set protocols igmp-snooping vlan all immediate-leave` |
| JUEX-L2-000170 | medium | If STP is used, implement Rapid STP, or Multiple STP, where VLANs span multiple switches with redundant links | `set protocols rstp bridge-priority (0..61440 in 4k increments)` |
| JUEX-L2-000180 | medium | Verify two-way connectivity on all interswitch trunked interfaces | `set protocols oam ethernet link-fault-management interface <interface name> LAG` |
| JUEX-L2-000190 | medium | Assign all explicitly disabled access interfaces to an unused VLAN | `set vlans vlan_disabled vlan-id <VLAN ID>` |
| JUEX-L2-000200 | medium | Do not be configured with VLANs used for L2 control traffic assigned to any host-facing access interface | `set interfaces interface-range name member <interface name>` |
| JUEX-L2-000210 | medium | Prune the default VLAN from all trunked interfaces that do not require it | `delete interfaces <trunked interface name> unit 0 family ethernet-switching vlan members <default \| other unnecessary VLAN name>` |
| JUEX-L2-000220 | medium | Do not use the default VLAN for management traffic | `set interfaces <interface name> unit 0 family ethernet-switching interface-mode access` |
| JUEX-L2-000230 | medium | Set all enabled user-facing or untrusted ports as access interfaces | `delete interfaces <interface name> unit 0 family ethernet-switching interface-mode` |
| JUEX-L2-000240 | medium | Do not have a native VLAN ID assigned, or have a unique native VLAN ID, for all 802.1q trunk links | `delete interfaces <interface name> native-vlan-id` |
| JUEX-L2-000250 | low | Do not have any access interfaces assigned to a VLAN configured as native for any trunked interface | `set interfaces <interface name> unit 0 family ethernet-switching interface-mode access` |

### Network Device Management, V2R5

Rule count: 55. Severity spread: high 13, medium 41, low 1.

| STIG ID | Severity | Requirement | Junos statement |
| - | - | - | - |
| JUEX-NM-000010 | medium | Limit the number of concurrent management sessions to 1 or an organization-defined value | `set system services ssh connection-limit 1` |
| JUEX-NM-000020 | medium | Automatically audit account creation | `set system syslog host <IPv4 or IPv6 syslog address> change-log info` |
| JUEX-NM-000060 | high | Assign appropriate user roles or access levels to authenticated users | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000070 | medium | Enforce approved authorizations for controlling the flow of management information within the network device based on information flow control policies | `set policy-options prefix-list ipv4-management <IPv4 MGT subnet/mask>` |
| JUEX-NM-000080 | medium | Enforce the limit of three consecutive invalid logon attempts for any given user, after which time it must block any login attempt for that user for 15 minutes | `set system login retry-options tries-before-disconnect 3` |
| JUEX-NM-000090 | medium | Display the Standard Mandatory DOD Notice and Consent Banner before granting access to the device | No direct Junos statement in the fix text. |
| JUEX-NM-000120 | medium | Produce audit log records containing sufficient information to establish what type of event occurred | `set system syslog host <syslog IPv4 or IPv6 address> any info` |
| JUEX-NM-000130 | medium | Produce audit records containing information to establish when (date and time) the events occurred | `set system syslog host <syslog IPv4 or IPv6 address> any info` |
| JUEX-NM-000140 | medium | Produce audit records containing information to establish where the events occurred | `set system syslog host <syslog IPv4 or IPv6 address> any info` |
| JUEX-NM-000150 | medium | Produce audit log records containing information to establish the source of events | `set system syslog host <syslog IPv4 or IPv6 address> any info` |
| JUEX-NM-000160 | medium | Produce audit records that contain information to establish the outcome of the event | `set system syslog host <syslog IPv4 or IPv6 address> any info` |
| JUEX-NM-000170 | medium | Generate audit records containing information that establishes the identity of any individual or process associated with the event | `set system syslog host <syslog IPv4 or IPv6 address> any info` |
| JUEX-NM-000190 | medium | Protect audit information from unauthorized modification | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000200 | medium | Protect audit information from unauthorized deletion | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000210 | medium | Protect audit tools from unauthorized access | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000220 | medium | Limit privileges to change the software resident within software libraries | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000230 | high | Prohibit the use of all unnecessary and/or nonsecure functions, ports, protocols, and/or services | `delete system services ftp` |
| JUEX-NM-000240 | medium | Use only one local account to be used as the account of last resort in the event the authentication server is unavailable | `set system login user <account of last resort username> authentication plain-text-password` |
| JUEX-NM-000260 | medium | Implement replay-resistant authentication mechanisms for network access to privileged accounts | `set system services ssh protocol-version v2` |
| JUEX-NM-000270 | medium | Enforce a minimum 15-character password length | `set system login password minimum-length 15` |
| JUEX-NM-000280 | medium | Enforce password complexity by requiring that at least one uppercase character be used | `set system login password minimum-upper-cases 1` |
| JUEX-NM-000290 | medium | Enforce password complexity by requiring that at least one lowercase character be used | `set system login password minimum-lower-cases 1` |
| JUEX-NM-000300 | medium | Enforce password complexity by requiring that at least one numeric character be used | `set system login password minimum-numerics 1` |
| JUEX-NM-000310 | medium | Enforce password complexity by requiring that at least one punctuation (special) character be used | `set system login password minimum-punctuations 1` |
| JUEX-NM-000320 | medium | Require that when a password is changed, the characters are changed in at least eight of the positions within the password | `set system login password minimum-character-changes 8` |
| JUEX-NM-000330 | high | Only store cryptographic representations of passwords | `set system login password format <sha-256\|sha-512>` |
| JUEX-NM-000340 | high | Use FIPS 140-2/140-3-validated algorithms for authentication to a cryptographic module | `set system login password format <sha256\|sha512>` |
| JUEX-NM-000360 | high | End all network connections associated with a device management session at the end of the session, or the session must be terminated after five minutes of inactivity except to fulfill mission requirements | `set system login idle-timeout 5` |
| JUEX-NM-000370 | high | Only allow authorized administrators to view or change the device configuration, system files, and other files stored either in the device or on removable media (such as a flash drive) | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000390 | medium | Enforce organization-defined role-based access control policies over defined subjects and objects | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000410 | medium | Allocate audit record storage capacity in accordance with organization-defined audit record storage requirements | `set system syslog host <address 1> any info` |
| JUEX-NM-000420 | medium | Generate an immediate real-time alert of all audit failure events requiring real-time alerts | `set chassis disk-partition /var level full free-space <0..100>` |
| JUEX-NM-000430 | medium | Synchronize internal information system clocks using redundant authoritative time sources | `set system ntp authentication-key 1 type sha256` |
| JUEX-NM-000440 | medium | Record time stamps for audit records that can be mapped to Coordinated Universal Time (UTC) or Greenwich Mean Time (GMT) | `set system time-zone UTC` |
| JUEX-NM-000450 | medium | Prohibit installation of software without explicit privileged status | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000460 | medium | Enforce access restrictions associated with changes to device configuration | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000480 | high | Authenticate SNMP messages using a FIPS-validated Keyed-Hash Message Authentication Code (HMAC) | `set snmp v3 usm local-engine user <SNMPv3 username> authentication-sha authentication-password "PSK"` |
| JUEX-NM-000490 | low | Use an an NTP service that is hosted by a trusted source or a DOD-compliant enterprise or local NTP server | `set system ntp authentication-key 1 type sha256` |
| JUEX-NM-000510 | high | Use FIPS-validated Keyed-Hash Message Authentication Code (HMAC) to protect the integrity of nonlocal maintenance and diagnostic communications | `set snmp v3 usm local-engine user <SNMPv3 user> authentication-sha authentication-password "PSK"` |
| JUEX-NM-000520 | high | Implement cryptographic mechanisms using a FIPS 140-2/140-3 approved algorithm to protect the confidentiality of remote maintenance sessions | `set snmp v3 usm local-engine user <SNMPv3 user> authentication-sha authentication-password "PSK"` |
| JUEX-NM-000530 | medium | Protect against known types of denial-of-service (DoS) attacks by employing organization-defined security safeguards | `set system services ssh connection-limit <1..250>` |
| JUEX-NM-000560 | medium | Generate audit records when successful/unsuccessful logon attempts occur | `set system syslog file <file name> any info` |
| JUEX-NM-000570 | medium | Generate audit records for privileged activities or other system-level access | `set system syslog host <syslog address> any info` |
| JUEX-NM-000580 | medium | Generate audit records showing starting and ending time for administrator access to the system | `set system syslog file <file name> any info` |
| JUEX-NM-000590 | medium | Generate audit records when concurrent logons from different workstations occur | `set system syslog file <file name> any info` |
| JUEX-NM-000600 | medium | Off-load audit records onto a different system than the system being audited | `set system syslog host <external syslog host IPv4 or IPv6 address> any info` |
| JUEX-NM-000620 | medium | Generate log records for a locally developed list of auditable events | `set system syslog file <file name> messages any info` |
| JUEX-NM-000630 | medium | Enforce access restrictions associated with changes to the system components | `set system login class <name> permissions <permission sets or 'all'>` |
| JUEX-NM-000640 | high | Use an authentication server for the purpose of authenticating users prior to granting administrative access | `set system radius-server <RADIUS-1 address> secret "<PSK>"` |
| JUEX-NM-000650 | medium | Conduct backups of system level information contained in the information system when changes occur | `set system services netconf ssh` |
| JUEX-NM-000660 | medium | Obtain its public key certificates from an appropriate certificate policy through an approved service provider | No direct Junos statement in the fix text. |
| JUEX-NM-000670 | high | Send log data to at least two central log servers for the purpose of forwarding alerts to the administrators and the information system security officer (ISSO) | `set system syslog host <external syslog host1 IPv4 or IPv6 address> any info` |
| JUEX-NM-000680 | high | Use an operating system release that is currently supported by the vendor | No direct Junos statement in the fix text. |
| JUEX-NM-000910 | medium | Change credentials for account of last resort when administrators who know the credential leave the organization | `set system login user <account of last resort name> authentication plain-text-password` |
| JUEX-NM-000930 | high | Prevent nonprivileged users from executing privileged functions to include disabling, circumventing, or altering implemented security safeguards/countermeasures | `set system login class <name> permissions <permission sets or 'all'>` |

### Router, V2R1

Rule count: 102. Severity spread: high 10, medium 63, low 29.

| STIG ID | Severity | Requirement | Junos statement |
| - | - | - | - |
| JUEX-RT-000010 | medium | Enforce approved authorizations for controlling the flow of information within the network based on organization-defined information flow control policies | `set policy-options prefix-list inside-addresses-ipv4 <inside IPv4 subnet>` |
| JUEX-RT-000020 | medium | Reject inbound route advertisements for any Bogon prefixes | `set policy-options route-filter-list bogon 0.0.0.0/8 orlonger` |
| JUEX-RT-000030 | medium | Reject inbound route advertisements for any prefixes belonging to the local autonomous system (AS) | `set policy-options route-filter-list local-routes 192.0.2.0/24 orlonger` |
| JUEX-RT-000040 | medium | Reject inbound route advertisements from a customer edge (CE) router for prefixes that are not allocated to that customer | `set policy-options route-filter-list customer1-routes <customer route 1/mask> orlonger` |
| JUEX-RT-000050 | medium | Reject outbound route advertisements for any prefixes that do not belong to any customers or the local autonomous system (AS) | `set policy-options route-filter-list customer1-routes <customer route 1/mask> exact` |
| JUEX-RT-000060 | low | Reject route advertisements from BGP peers that do not list their autonomous system (AS) number as the first AS in the AS_PATH attribute | `set protocols bgp group eBGP enforce-first-as` |
| JUEX-RT-000070 | low | Filter received source-active multicast advertisements for any undesirable multicast groups and sources | `set protocols msdp peer <address> import source-active-filter` |
| JUEX-RT-000080 | low | Filter source-active multicast advertisements to external MSDP peers to avoid global visibility of local-only multicast sources and groups | `set protocols msdp peer <address> export source-active-filter` |
| JUEX-RT-000090 | low | Limit the amount of source-active messages it accepts on per-peer basis | `set protocols msdp active-source-limit maximum <1..1000000>` |
| JUEX-RT-000100 | low | Reject route advertisements from CE routers with an originating AS in the AS_PATH attribute that does not belong to that customer | `set policy-options policy-statement bgp_originate_65535 term 1 from as-path orig_65535` |
| JUEX-RT-000110 | low | Disable the auxiliary port unless it is connected to a secured modem providing encryption and authentication | `set system ports auxiliary disable` |
| JUEX-RT-000120 | medium | Enforce approved authorizations for controlling the flow of information between interconnected networks in accordance with applicable policy | `set interfaces <interface name> unit <logical unit> family inet rpf-check` |
| JUEX-RT-000130 | medium | Disable Protocol Independent Multicast (PIM) on all interfaces that are not required to support multicast routing | `delete protocols pim` |
| JUEX-RT-000140 | medium | Bind a Protocol Independent Multicast (PIM) neighbor filter to interfaces that have PIM enabled | `set policy-options prefix-list PIM-NEIGHBOR-1 <PIM neighbor address>/32` |
| JUEX-RT-000150 | low | Establish boundaries for administratively scoped multicast traffic | `set routing-options multicast scope <IPv4 scope name> prefix 239.0.0.0/8` |
| JUEX-RT-000160 | low | Have all inactive interfaces disabled | `delete interfaces <interface name>` |
| JUEX-RT-000170 | high | Protect an enclave connected to an alternate gateway by using an inbound filter that only permits packets with destination addresses within the site's address space | `set policy-options prefix-list inside_addresses-ipv4 <IPv4 subnet / mask>` |
| JUEX-RT-000180 | high | Do not be a Border Gateway Protocol (BGP) peer to an alternate gateway service provider | `delete protocols bgp group <name> neighbor <peer AS belonging to alternate gateway service provider>` |
| JUEX-RT-000190 | low | Do not redistribute static routes to an alternate gateway service provider into BGP or an IGP peering with the NIPRNet or to other autonomous systems | `set policy-options policy-statement <policy name> term 1 from protocol static` |
| JUEX-RT-000200 | medium | Have separate IGP instances for the managed network and management network | `set protocols ospf area <number> interface <interface name>.<logical unit>` |
| JUEX-RT-000210 | medium | Do not redistribute routes between the management network routing domain and the managed network routing domain | `set policy-options policy-statement deny-managed-routes term 1 from route-filter <IPv4 subnet>/<mask> orlonger` |
| JUEX-RT-000220 | low | Filter Protocol Independent Multicast (PIM) Register messages received from the Designated Router (DR) for any undesirable multicast groups and sources | `set policy-options policy-statement <name> term filter_groups from route-filter <multicast address>/<mask> <match criterion>` |
| JUEX-RT-000230 | low | Filter Protocol Independent Multicast (PIM) Join messages received from the Designated Router (DR) for any undesirable multicast groups | `set policy-options policy-statement <name> term filter_groups from route-filter <multicast address>/<mask> <match criterion>` |
| JUEX-RT-000240 | medium | Produce audit records containing information to establish where the events occurred | `set firewall family inet filter <filter name> term 1 from <match conditions>` |
| JUEX-RT-000250 | medium | Produce audit records containing information to establish the source of the events | `set firewall family inet filter <filter name> term 1 from <match conditions>` |
| JUEX-RT-000260 | low | Log all packets that have been dropped | `set firewall family inet filter <filter name> term <name> then log` |
| JUEX-RT-000270 | low | Have all nonessential capabilities disabled | `delete system services finger` |
| JUEX-RT-000280 | medium | Do not have any feature enabled that calls home to the vendor | `delete system phone-home` |
| JUEX-RT-000290 | medium | Use encryption for routing protocol authentication | `set protocols ospf area <area number> interface <interface name>.<logical unit> authentication md5 <key ID> key "<PSK>"` |
| JUEX-RT-000300 | medium | Authenticate all routing protocol messages using NIST-validated FIPS 198-1 message authentication code algorithm | `set security ipsec security-association <SA name> mode transport` |
| JUEX-RT-000310 | medium | Limit the number of MAC addresses it can learn for each Virtual Private LAN Services (VPLS) bridge domain | `set routing-instance <name> protocols vpls interface-mac-limit <value>` |
| JUEX-RT-000320 | low | Enable refresh reduction features | `set protocols rsvp interface <interface name>.<logical unit> aggregate` |
| JUEX-RT-000330 | medium | Have traffic storm control thresholds on CE-facing interfaces | `set firewall policer <policer name> if-exceeding bandwidth-limit <value> burst-size-limit <value>` |
| JUEX-RT-000340 | medium | Enforce a Quality-of-Service (QoS) policy to limit the effects of packet flooding denial-of-service (DoS) attacks | `set class-of-service classifiers dscp <classifier name> forwarding-class NC loss-priority low code-points 110000` |
| JUEX-RT-000350 | low | Enforce a Quality-of-Service (QoS) policy in accordance with the QoS DODIN Technical Profile | `set class-of-service classifiers dscp <classifier name> forwarding-class NC loss-priority low code-points 110000` |
| JUEX-RT-000360 | low | Enforce a Quality-of-Service (QoS) policy in accordance with the QoS GIG Technical Profile | `set class-of-service classifiers dscp <classifier name> forwarding-class NC loss-priority low code-points 110000` |
| JUEX-RT-000370 | high | Deny network traffic by default and allow network traffic by exception | `set firewall family inet filter permitted_inbound_traffic_ipv4 term 1 from destination-prefix-list INSIDE_ADDRESSES` |
| JUEX-RT-000380 | high | Restrict traffic destined to itself | `set prefix-list auth_mgt_networks-ipv4 <IPv4 subnet / mask>` |
| JUEX-RT-000390 | medium | Drop all fragmented Internet Control Message Protocol (ICMP) packets destined to itself | `set policy-options prefix-list router-addresses-ipv4 <interface IPv4 address>/32` |
| JUEX-RT-000400 | medium | Filter traffic destined to the enclave in accordance with the guidelines contained in DoD Instruction 8551.1 | `set policy-options prefix-list inside-addresses-ipv4 <IPv4 subnet>/<mask> <additional subnets as required>` |
| JUEX-RT-000410 | medium | Filter ingress traffic at the external interface on an inbound direction | `set interfaces <external interface name> unit <number> family inet filter input inbound-ipv4` |
| JUEX-RT-000420 | medium | Filter egress traffic at the internal interface on an inbound direction | `set interfaces <internal interface name> unit <number> family inet filter input outbound-ipv4` |
| JUEX-RT-000430 | medium | Reject outbound route advertisements for any prefixes belonging to the IP core | `set policy-options prefix-list ip-core-ipv4 192.0.2.0/24` |
| JUEX-RT-000440 | high | Block any traffic that is destined to IP core infrastructure | `set policy-options prefix-list ipv4-core 192.0.2.0/24` |
| JUEX-RT-000450 | medium | Use Unicast Reverse Path Forwarding (uRPF) loose mode, or a firewall filter, enabled on all CE-facing interfaces | `set interfaces ge-0/0/0 unit 0 family inet rpf-check mode loose` |
| JUEX-RT-000460 | medium | Transport management traffic to the Network Operations Center (NOC) via dedicated circuit, MPLS/VPN service, or IPsec tunnel | `set interfaces <exterior interface> unit <number> family inet address <IPv4 address>/<mask>` |
| JUEX-RT-000470 | medium | Forward only authorized management traffic to the Network Operations Center (NOC) | `set policy-options prefix-list NOC-ipv4 <IPv4 network>/<mask>` |
| JUEX-RT-000480 | medium | Block any traffic destined to itself that is not sourced from the OOBM network or the NOC | `set policy-options prefix-list OOBM-ipv4 <IPv4 address>/<mask>` |
| JUEX-RT-000490 | medium | Only permit management traffic that ingresses and egresses the OOBM interface | `set policy-options prefix-list OOBM-ipv4 192.0.2.0/24` |
| JUEX-RT-000500 | high | Restrict it from accepting outbound IP packets that contain an illegitimate address in the source address field via egress filter or by enabling Unicast Reverse Path Forwarding (uRPF) | `set interfaces <internal interface name> unit <number> family inet rpf-check` |
| JUEX-RT-000510 | medium | Block all packets with any IP options | `set firewall family inet filter <filter name> term 1 from ip-options any` |
| JUEX-RT-000520 | medium | Ignore or block all packets with any IP options | `set firewall family inet filter <filter name> term 1 from ip-options any` |
| JUEX-RT-000530 | medium | Implement message authentication for all control plane protocols | `set security ipsec security-association <sa name> manual direction bidirectional protocol esp` |
| JUEX-RT-000540 | medium | Use a unique key for each autonomous system (AS) that it peers with | `set security ipsec security-association <sa name> manual direction bidirectional protocol esp` |
| JUEX-RT-000550 | medium | Use keys with a duration not exceeding 180 days for authenticating routing protocol messages | `set security authentication-key-chains key-chain <name> key <number-1> secret <key value>` |
| JUEX-RT-000560 | medium | Authenticate targeted LDP sessions used to exchange VC information using a FIPS-approved message authentication code algorithm | `set protocols ldp interface <interface 1 name>.<logical unit>` |
| JUEX-RT-000570 | medium | Authenticate all received MSDP packets | `set protocols msdp active-source-limit maximum <1..1000000>` |
| JUEX-RT-000580 | medium | Do not have any zero-touch deployment feature enabled when connected to an operational network | `delete system auto-configuration` |
| JUEX-RT-000590 | medium | Protect against or limit the effects of denial-of-service (DoS) attacks by employing control plane protection | `set firewall family inet filter <name> term accept-tcp-initial from source-prefix-list management-networks-ipv4` |
| JUEX-RT-000600 | medium | Have Gratuitous ARP disabled on all external interfaces | `set interfaces <external interface> no-gratuitous-arp-reply` |
| JUEX-RT-000610 | low | Have IP directed broadcast disabled on all interfaces | `delete interfaces <L3 interface> unit <number> family inet targeted-broadcast` |
| JUEX-RT-000620 | medium | Have Internet Control Message Protocol (ICMP) unreachable notifications disabled on all external interfaces | `set policy-options prefix-list router-addresses-ipv4 <external interface address>/32` |
| JUEX-RT-000630 | medium | Have Internet Control Message Protocol (ICMP) mask replies disabled on all external interfaces | `set policy-options prefix-list router-addresses-ipv4 <external interface address>/32` |
| JUEX-RT-000640 | medium | Have Internet Control Message Protocol (ICMP) redirects disabled on all external interfaces | `set system no-redirects` |
| JUEX-RT-000650 | medium | Use the prefix limit feature to protect against route table flooding and prefix deaggregation attacks | `set protocols bgp group <group name> type external` |
| JUEX-RT-000660 | low | Limit the prefix size on any inbound route advertisement to /24 or the least significant prefixes issued to the customer | `set policy-options policy-statement <statement name> term 1 from route-filter 0.0.0.0/0 prefix-length-range /25-/32` |
| JUEX-RT-000670 | low | Implement Internet Group Management Protocol (IGMP) or Multicast Listener Discovery (MLD) snooping for each Virtual Private LAN Services (VPLS) bridge domain | `set routing-instances <name> protocols igmp-snooping vlan <vlan ID>` |
| JUEX-RT-000680 | low | Limit the multicast forwarding cache so that its resources are not saturated by managing an overwhelming number of PIM and MSDP source-active entries | `set routing-options multicast forwarding-cache threshold suppress <1..200000>` |
| JUEX-RT-000690 | medium | Rate limit the number of Protocol Independent Multicast (PIM) Register messages | `set protocols pim rp register-limit maximum <1..65535>` |
| JUEX-RT-000700 | medium | Limit the number of mroute states resulting from Internet Group Management Protocol (IGMP) and Multicast Listener Discovery (MLD) Host Membership Reports | `set protocols igmp interface <name>.<logical unit> group-limit <1..32767>` |
| JUEX-RT-000710 | medium | Increase the shortest-path tree (SPT) threshold or set it to infinity to minimalize source-group (S, G) state within the multicast topology where Any Source Multicast (ASM) is deployed | `set it to infinity to minimalize (S, G) state within` |
| JUEX-RT-000720 | low | Enable the Generalized TTL Security Mechanism (GTSM) | `set firewall family inet filter gtsm term 1 from protocol tcp` |
| JUEX-RT-000730 | medium | Only allow incoming communications from authorized sources to be routed to authorized destinations | `set policy-options prefix-list inside-addresses-ipv4 192.0.2.0/25` |
| JUEX-RT-000740 | medium | Block inbound packets with source Bogon IP address prefixes | `set policy-options prefix-list bogon-ipv4 0.0.0.0/8` |
| JUEX-RT-000750 | low | Have Link Layer Discovery Protocols (LLDPs) disabled on all external interfaces | `set protocols lldp interface all disable` |
| JUEX-RT-000760 | medium | Have Proxy ARP disabled on all external interfaces | `delete interfaces <external interface> unit 0 proxy-arp` |
| JUEX-RT-000770 | medium | Block all outbound management traffic | `set firewall family inet filter <name> term block-UDP-MGT-SRC from protocol udp` |
| JUEX-RT-000780 | low | Filter the IGMP and MLD Report messages to allow hosts to join only multicast groups that have been approved by the organization | `set policy-options policy-statement <name> term unauth-groups from route-filter 224.0.1.2/32 exact` |
| JUEX-RT-000790 | medium | Filter the IGMP and MLD Report messages to allow hosts to join a multicast group only from sources that have been approved by the organization | `set policy-options policy-statement <name> term unauth-sources from source-address-filter <IPv4 address>/<mask> orlonger` |
| JUEX-RT-000800 | medium | Only accept MSDP packets from known MSDP peers | `set firewall family inet filter <name> term 1 from source-prefix-list msdp-peers` |
| JUEX-RT-000810 | medium | Drop fragmented IPv6 packets where the first fragment does not include the entire IPv6 header chain | `set firewall family inet6 filter <name> term <name> from next-header fragment` |
| JUEX-RT-000820 | medium | Be configured drop IPv6 packets with a Routing Header type 0, 1, or 3255 | `set firewall family inet6 filter <name> term 1 from next-header routing` |
| JUEX-RT-000830 | medium | Drop IPv6 packets containing a Hop-by-Hop header with invalid option type values | `set firewall family inet6 filter <name> term 1 from next-header hop-by-hop` |
| JUEX-RT-000840 | medium | Drop IPv6 packets containing a Destination Option header with invalid option type values | `set firewall family inet6 filter <name> term 1 from next-header hop-by-hop` |
| JUEX-RT-000850 | medium | Drop IPv6 packets containing an extension header with the Endpoint Identification option | `set firewall family inet6 filter <name> term 1 from next-header hop-by-hop` |
| JUEX-RT-000860 | medium | Drop IPv6 packets containing the NSAP address option within Destination Option header | `set firewall family inet6 filter <name> term 1 from next-header dstopts` |
| JUEX-RT-000870 | medium | Drop IPv6 packets containing a Hop-by-Hop or Destination Option extension header with an undefined option type | `set firewall family inet6 filter <name> term 1 from next-header hop-by-hop` |
| JUEX-RT-000880 | low | Use its loopback address as the source address for iBGP peering sessions | `set protocols bgp group <group name> type internal` |
| JUEX-RT-000890 | low | Use its loopback address as the source address for LDP peering sessions | `set interfaces lo0 unit 0 family inet <IPv4 address>/32` |
| JUEX-RT-000900 | low | Synchronize IGP and LDP to minimize packet loss when an IGP adjacency is established prior to LDP peers completing label exchange | `set protocols ospf area <number> interface <name>.<logical unit> authentication md5 <key number> <PSK>` |
| JUEX-RT-000910 | medium | Have TTL Propagation disabled | `set protocols mpls no-propagate-ttl` |
| JUEX-RT-000920 | high | Have each Virtual Routing and Forwarding (VRF) instance bound to the appropriate physical or logical interfaces to maintain traffic separation between all MPLS L3VPNs | `set interfaces <ce facing interface> description <"appropriate description">` |
| JUEX-RT-000930 | high | Have each Virtual Routing and Forwarding (VRF) instance with the appropriate Route Target (RT) | `set routing-instances <name> description <"appropriate description">` |
| JUEX-RT-000940 | medium | Have each VRF with the appropriate Route Distinguisher (RD) | `set routing-instances <name> description <"appropriate description">` |
| JUEX-RT-000950 | high | Have the appropriate virtual circuit identification (VC ID) for each attachment circuit | `set interfaces <interface name> unit <number> encapsulation vlan-ccc` |
| JUEX-RT-000960 | high | Have all attachment circuits defined to the virtual forwarding instance (VFI) with the globally unique VPN ID assigned for each customer VLAN | `set routing-instances <instance name> protocols vpls vpls-id <VPLS ID> neighbor <neighbor address>` |
| JUEX-RT-000970 | low | Enforce the split-horizon rule for all pseudowires within a Virtual Private LAN Services (VPLS) bridge domain | `delete routing-instances <name> protocols vpls mesh-group <name> local-switching` |
| JUEX-RT-000980 | low | Use its loopback address as the source address when originating MSDP traffic | `set protocols msdp active-source-limit maximum <1..1000000>` |
| JUEX-RT-000990 | low | Advertise a hop limit of at least 32 in Router Advertisement messages for IPv6 stateless auto-configuration deployments | `set protocols router-advertisement interface <internal interface> current-hop-limit <32 or greater>` |
| JUEX-RT-001000 | medium | Do not use IPv6 Site Local Unicast addresses | `delete interfaces <interface name> unit <logical unit number> family inet6 address <unauth address>/<prefix>` |
| JUEX-RT-001010 | medium | Suppress Router Advertisements on all external IPv6-enabled interfaces | `deactivate router advertisements on external interfaces. [delete\|deactivate] protocols router-advertisement interface <external interface>` |
| JUEX-RT-001020 | medium | Be configured in accordance with the security configuration settings based on DoD security configuration or implementation guidance, including STIGs, NSA configuration guides, CTOs, and DTMs | No direct Junos statement in the fix text. |
