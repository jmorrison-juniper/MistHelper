# VPN, management, and flow

Use this reference for IPsec VPN, Security Director, Policy Enforcer, the session table, flow state, and packet path checks.

Sources: Junos OS VPN Feature Guide for Security Devices, SRX document set, modified 2017-08-14. Security Director User Guide, release 22.3, published 2023-03-09. Security Director Policy Enforcer User Guide, release 22.2, published 2022-11-23. Junos OS Flow-Based and Packet-Based Processing Feature Guide for Security Devices, SRX document set, modified 2017-09-15.

Warning: a VPN, policy publish, or flow change can interrupt production traffic. Use `commit confirmed` for a remote SRX change.

## 1. IPsec route-based VPN

A route-based VPN uses IKE phase 1, IPsec phase 2, a gateway, an IPsec VPN, and a secure tunnel interface.

### Task: configure the secure tunnel interface

```text
set interfaces st0 unit 0 family inet address 10.11.11.10/24
set routing-options static route 192.168.168.0/24 next-hop st0.0
set security zones security-zone vpn-chicago interfaces st0.0
show interfaces terse st0.0
show security zones security-zone vpn-chicago
```

The VPN guide confirms the `st0.0` address, static route, and zone binding in a route-based VPN example.

### Task: configure the phase 1 proposal

```text
set security ike proposal ike-phase1-proposal authentication-method pre-shared-keys
set security ike proposal ike-phase1-proposal dh-group group2
set security ike proposal ike-phase1-proposal authentication-algorithm sha1
set security ike proposal ike-phase1-proposal encryption-algorithm aes-128-cbc
set security ike proposal ike-phase1-proposal lifetime-seconds 28800
show configuration security ike proposal ike-phase1-proposal
```

The source confirms the IKE proposal hierarchy and a pre-shared key example. Use the stronger algorithms that your release and peer support.

### Task: configure the phase 1 policy and gateway

```text
set security ike policy ike-phase1-policy mode main
set security ike policy ike-phase1-policy proposals ike-phase1-proposal
set security ike policy ike-phase1-policy pre-shared-key ascii-text REPLACE_WITH_SECRET
set security ike gateway gw-chicago ike-policy ike-phase1-policy
set security ike gateway gw-chicago address 198.51.100.10
set security ike gateway gw-chicago external-interface ge-0/0/3.0
show configuration security ike policy ike-phase1-policy
show configuration security ike gateway gw-chicago
```

Warning: never paste a real pre-shared key into an example or a log. A leaked key can let an attacker impersonate the VPN peer.

### Task: configure the phase 2 proposal and VPN

```text
set security ipsec proposal ipsec-phase2-proposal protocol esp
set security ipsec proposal ipsec-phase2-proposal authentication-algorithm hmac-sha1-96
set security ipsec proposal ipsec-phase2-proposal encryption-algorithm aes-128-cbc
set security ipsec proposal ipsec-phase2-proposal lifetime-seconds 3600
set security ipsec policy ipsec-phase2-policy proposals ipsec-phase2-proposal
set security ipsec vpn ike-vpn-chicago bind-interface st0.0
set security ipsec vpn ike-vpn-chicago ike gateway gw-chicago
set security ipsec vpn ike-vpn-chicago ike ipsec-policy ipsec-phase2-policy
show configuration security ipsec vpn ike-vpn-chicago
```

The VPN guide confirms `bind-interface st0.0` for the IPsec VPN.

### Task: verify the tunnel

```text
show security ike security-associations detail
show security ipsec security-associations
show security ipsec statistics
show security ipsec tunnel-events-statistics
show route 192.168.168.0/24
show security flow session
```

Read both IKE and IPsec security associations. A route-based VPN also needs the route that sends protected traffic to `st0.0`.

## 2. Policy-based VPN check

A policy-based VPN binds IPsec to a security policy action instead of a tunnel interface. Use a route-based VPN when the design needs routing protocols or many subnets.

### Task: verify a policy-based VPN

```text
show configuration security policies | display set | match ipsec
show security ipsec security-associations
show security flow session
```

If the policy does not match, the VPN cannot protect the traffic.

## 3. Security Director policy at scale

Security Director manages SRX policy across devices. A change is not live until the operator publishes or updates it to the device.

### Task: change a policy in Security Director

1. Open the policy in Security Director.
2. Make the smallest policy change.
3. Review the device assignment.
4. Click `Publish` when the staged policy is ready.
5. Click `Update` to send the change to devices.
6. Verify the SRX with `show security policies`.

The Security Director guide confirms the publish and update steps in the policy workflow.

Warning: publishing the wrong shared policy can affect many SRX devices. Review the device list before you update devices.

### Task: verify a Security Director change on the SRX

```text
show security policies
show configuration security policies | display set
show log messages | match UI_CMDLINE
```

Use the SRX read as the final proof. A management platform status alone is not a complete device check.

## 4. Policy Enforcer update

Policy Enforcer applies user intent and threat prevention policy to enforcement groups.

### Task: apply a Policy Enforcer change

1. Create or edit the policy.
2. Select the policy enforcement group.
3. Review pending policy changes on the analysis page.
4. Choose `Update now` when the change is approved.
5. Verify the SRX policy and flow logs.

The Policy Enforcer guide confirms that the operator must apply a new or edited policy configuration before the policy goes live.

Warning: a policy enforcement group can include many devices. Confirm the group membership before you update now.

## 5. Session table and flow state

The session table shows traffic that passed enough checks to create a flow. Read it after routes, NAT, and policy look correct.

### Task: read all sessions

```text
show security flow session
show security flow session extensive
show security flow status
show interfaces flow-statistics
```

The flow guide confirms these operational commands.

### Task: read application-aware sessions

```text
show security flow session application-firewall dynamic-application junos:FTP
show security flow session application-firewall dynamic-application junos:UNKNOWN extensive
show security flow session application-traffic-control extensive
```

Use these commands when application identification or application firewall is in the policy path.

## 6. Packet path through the SRX

A flow-based packet commonly passes these checks.

1. The ingress interface maps to a source zone.
2. Screen checks run on the ingress zone.
3. Destination NAT can change the destination.
4. Route lookup selects the egress interface.
5. Policy lookup uses the source zone and destination zone.
6. Source NAT or static NAT can change addresses.
7. ALG, UTM, IDP, or application identification can inspect the session.
8. The SRX installs or updates the session.

### Task: isolate a packet path failure

```text
show interfaces terse
show security zones
show configuration security nat | display set
show security policies
show security flow session
show log messages | match RT_FLOW
```

If the packet targets the SRX itself, check host inbound traffic before transit policy. Host inbound traffic controls traffic to the device.

## 7. Sources

| ID | Source | Release | Use |
| - | - | - | - |
| VMF-1 | Junos OS VPN Feature Guide for Security Devices | SRX document set, modified 2017-08-14 | IKE, IPsec, gateway, VPN, and `st0.0`. |
| VMF-2 | Security Director User Guide | 22.3, published 2023-03-09 | Publish and update workflow. |
| VMF-3 | Security Director Policy Enforcer User Guide | 22.2, published 2022-11-23 | Policy enforcement groups and update workflow. |
| VMF-4 | Junos OS Flow-Based and Packet-Based Processing Feature Guide for Security Devices | SRX document set, modified 2017-09-15 | Session table, flow status, and packet path checks. |
