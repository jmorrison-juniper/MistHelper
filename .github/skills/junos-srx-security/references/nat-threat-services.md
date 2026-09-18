# NAT and threat services

Use this reference for NAT, proxy ARP, screens, ALG, application identification, UTM, intrusion prevention, and security intelligence feeds.

Sources: Junos OS Network Address Translation Feature Guide for Security Devices, SRX document set, modified 2017-08-03. Junos OS Attack Detection and Prevention Feature Guide for Security Devices, SRX document set, modified 2017-08-08. Junos OS Application Layer Gateways Feature Guide for Security Devices, SRX document set, modified 2017-07-31. Junos OS AppSecure Services Feature Guide for Security Devices, SRX document set, modified 2017-09-10. Junos OS UTM Feature Guide for Security Devices, SRX document set, modified 2017-09-11. Junos OS Intrusion Detection and Prevention Feature Guide for Security Devices, SRX document set, modified 2017-06-14. Juniper SecIntel Administration Guide, release 22.3, published 2023-03-09.

Warning: a NAT or threat service change can drop valid traffic or expose an internal host. Use `commit confirmed` for a remote change.

## 1. Source NAT

Source NAT changes the source address of traffic that leaves the SRX. Use it for outbound client traffic or overlapping inside addresses.

### Task: translate clients to the egress interface address

```text
set security nat source rule-set rs1 from zone trust
set security nat source rule-set rs1 to zone untrust
set security nat source rule-set rs1 rule r1 match source-address 0.0.0.0/0
set security nat source rule-set rs1 rule r1 match destination-address 0.0.0.0/0
set security nat source rule-set rs1 rule r1 then source-nat interface
show configuration security nat source rule-set rs1
show security nat source rule all
```

The NAT guide confirms this `source rule-set` hierarchy and the interface source NAT action.

### Task: verify source NAT use

```text
show security nat source rule all
show security nat source pool all
show security flow session
```

Read the session table after traffic starts. Confirm that the post-NAT source address matches the design.

## 2. Destination NAT

Destination NAT changes the destination address before policy lookup completes. The security policy must permit the translated destination.

### Task: send a public address to an inside server

```text
set security nat destination rule-set dst-web from zone untrust
set security nat destination rule-set dst-web rule web1 match destination-address 203.0.113.10/32
set security nat destination rule-set dst-web rule web1 then destination-nat pool web-pool
set security nat destination pool web-pool address 192.0.2.10/32
show configuration security nat destination
show security nat destination rule all
```

Warning: a wrong destination NAT address can expose the wrong host to the network. Verify the inside address before you commit.

### Task: permit the translated service

```text
set security policies from-zone untrust to-zone trust policy permit-web match source-address any
set security policies from-zone untrust to-zone trust policy permit-web match destination-address web-server
set security policies from-zone untrust to-zone trust policy permit-web match application junos-http
set security policies from-zone untrust to-zone trust policy permit-web then permit
show security policies from-zone untrust to-zone trust
```

## 3. Static NAT and proxy ARP

Static NAT maps one address to another address. Add proxy ARP when the SRX must answer ARP for the mapped address on an Ethernet segment.

### Task: configure static NAT

```text
set security nat static rule-set static-web from zone untrust
set security nat static rule-set static-web rule web1 match destination-address 203.0.113.10/32
set security nat static rule-set static-web rule web1 then static-nat prefix 192.0.2.10/32
show configuration security nat static
show security nat static rule all
```

### Task: configure proxy ARP for a NAT address

```text
set security nat proxy-arp interface ge-0/0/1.0 address 203.0.113.10/32
show configuration security nat proxy-arp
show arp no-resolve | match 203.0.113.10
```

The NAT guide confirms the `proxy-arp` statement under the security NAT hierarchy.

## 4. Screen protection

A screen detects simple floods, scans, and malformed packets before a session fully forms.

### Task: build one screen profile

```text
set security screen ids-option screen-config icmp ip-sweep threshold 1000
set security screen ids-option screen-config icmp flood threshold 200
set security screen ids-option screen-config icmp ping-death
set security screen ids-option screen-config ip bad-option
set security screen ids-option screen-config ip tear-drop
set security screen ids-option screen-config tcp syn-fin
set security screen ids-option screen-config tcp tcp-no-flag
set security screen ids-option screen-config tcp port-scan threshold 1000
set security screen ids-option screen-config tcp syn-flood alarm-threshold 500
set security screen ids-option screen-config tcp syn-flood attack-threshold 500
set security screen ids-option screen-config tcp syn-flood source-threshold 50
set security screen ids-option screen-config tcp syn-flood destination-threshold 1000
set security screen ids-option screen-config tcp syn-flood timeout 10
set security screen ids-option screen-config tcp land
set security screen ids-option screen-config udp flood threshold 500
show security screen ids-option screen-config
show security screen status
```

The attack detection guide confirms each listed screen option in one example.

### Task: apply a screen to a zone

```text
set security zones security-zone untrust screen screen-config
show security zones security-zone untrust
show configuration security zones security-zone untrust
```

Warning: an aggressive screen threshold can drop valid traffic during a burst. Test the threshold with expected traffic before you commit.

## 5. Application layer gateways

An application layer gateway helps a protocol that opens related sessions or embeds address data in the payload.

### Task: enable IKE ESP NAT ALG

```text
set security alg ike-esp-nat enable
set security alg ike-esp-nat esp-gate-timeout 20
set security alg ike-esp-nat esp-session-timeout 2400
set security alg ike-esp-nat state-timeout 360
show configuration security alg ike-esp-nat
clear security alg ike-esp-nat
```

### Task: adjust an ALG safety setting

```text
set security alg ftp ftps-extension
set security alg sip maximum-call-duration 600
set security alg sip inactive-media-timeout 90
show configuration security alg
```

Warning: an ALG change can alter related session creation. Confirm the affected application before you commit.

## 6. Application identification

Application identification classifies traffic by application. Application firewall, application traffic control, and some policy matches use it.

### Task: download and install the application package

```text
request services application-identification download
request services application-identification download status
request services application-identification install
request services application-identification install status
show security policies
```

### Task: define a custom application signature

```text
set services application-identification application mycustom-http over HTTP signature sig1
set services application-identification application MY-ICMP icmp-mapping type 100
set services application-identification application MY-ICMP icmp-mapping code 1
show configuration services application-identification
```

The AppSecure guide confirms these custom application command families.

## 7. Unified threat management

UTM attaches anti-spam, anti-virus, content filtering, or web filtering profiles to a security policy.

### Task: create a UTM policy and attach it

```text
set security utm feature-profile anti-spam sbl profile sblprofile1 sbl-default-server
set security utm utm-policy spampolicy1 anti-spam smtp-profile sblprofile1
set security policies from-zone trust to-zone untrust policy permit-mail then permit application-services utm-policy spampolicy1
show security utm status
show security utm session
show configuration security utm
```

Warning: a UTM profile can block valid mail, web, or file traffic. Test the policy with a nonproduction source before you commit.

## 8. Intrusion prevention

IDP uses a security package, an IDP policy, and an active policy. A security policy can attach IDP services to matching traffic.

### Task: configure and activate an IDP policy

```text
set security idp security-package url <package-url>
set security idp security-package automatic enable
set security idp idp-policy policy1 rulebase-ips rule r1 match from-zone any
set security idp idp-policy policy1 rulebase-ips rule r1 match source-address any
set security idp idp-policy policy1 rulebase-ips rule r1 match to-zone any
set security idp idp-policy policy1 rulebase-ips rule r1 match destination-address any
set security idp idp-policy policy1 rulebase-ips rule r1 match application default
set security idp active-policy policy1
show security idp security-package-version
show security idp predefined-attacks
show configuration security idp
```

Warning: an IDP signature action can drop valid sessions. Start with monitor or a limited source when the change is new.

## 9. Security intelligence feed

Security Intelligence uses feeds and policies through Security Director and Policy Enforcer. Use the management platform when the design spans many SRX devices.

### Task: prepare a feed-backed policy

1. In Policy Enforcer, create or select the feed profile.
2. Select the command and control, infected host, malware, or GeoIP profile.
3. Assign the policy enforcement group.
4. Apply the policy update when the review is complete.
5. On the SRX, verify the policy and the flow logs.

The SecIntel guide states that the policy needs a profile and a policy enforcement group before you apply it.

### Task: verify a feed-backed block

```text
show security policies
show security flow session
show log messages | match RT_FLOW
```

If the SRX does not show the expected match, verify that Policy Enforcer updated the device group.

## 10. Sources

| ID | Source | Release | Use |
| - | - | - | - |
| NT-1 | Junos OS Network Address Translation Feature Guide for Security Devices | SRX document set, modified 2017-08-03 | Source NAT, destination NAT, static NAT, and proxy ARP. |
| NT-2 | Junos OS Attack Detection and Prevention Feature Guide for Security Devices | SRX document set, modified 2017-08-08 | Screen options for floods, scans, and malformed packets. |
| NT-3 | Junos OS Application Layer Gateways Feature Guide for Security Devices | SRX document set, modified 2017-07-31 | ALG commands and verification. |
| NT-4 | Junos OS AppSecure Services Feature Guide for Security Devices | SRX document set, modified 2017-09-10 | Application identification and application firewall. |
| NT-5 | Junos OS UTM Feature Guide for Security Devices | SRX document set, modified 2017-09-11 | UTM profiles and policy attachment. |
| NT-6 | Junos OS Intrusion Detection and Prevention Feature Guide for Security Devices | SRX document set, modified 2017-06-14 | IDP package, policy, and active policy. |
| NT-7 | Juniper SecIntel Administration Guide | 22.3, published 2023-03-09 | Feed-backed policy workflow. |
