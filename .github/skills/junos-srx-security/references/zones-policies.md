# Zones and policies

Use this reference for zones, interface bindings, host inbound traffic, security policy, policy order, global policy, and unified policy.

Sources: Junos OS Security Basics Guide for Security Devices, SRX document set, modified 2017-07-18. Junos OS AppSecure Services Feature Guide for Security Devices, SRX document set, modified 2017-09-10.

Warning: a zone, host inbound traffic, or policy change can drop production traffic or expose a service. Use `commit confirmed` for a remote change.

## 1. Security zones

A security zone groups logical interfaces that share a trust level. Traffic between two zones needs a security policy unless the traffic goes to the SRX itself.

### Task: bind an interface to a zone

```text
set security zones security-zone trust interfaces ge-0/0/0.0
show security zones security-zone trust
show configuration security zones security-zone trust
```

The corpus confirms this hierarchy with examples that bind `ge-0/0/1.0` to a zone and then read the zone with `show security zones security-zone ABC`.

### Task: bind a tunnel interface to a VPN zone

```text
set security zones security-zone vpn interfaces st0.0
show security zones security-zone vpn
show configuration security zones security-zone vpn
```

The VPN guide confirms the tunnel binding with an example that adds `st0.0` to the `vpn-chicago` zone.

### Task: confirm all zone bindings

```text
show security zones
show configuration security zones
show interfaces terse
```

A zone read proves where Junos evaluates the from-zone and to-zone policy context.

## 2. Host inbound traffic

Host inbound traffic controls traffic that terminates on the SRX. It does not permit transit traffic through the SRX.

### Task: permit SSH to the SRX on one interface

```text
set security zones security-zone trust interfaces ge-0/0/0.0 host-inbound-traffic system-services ssh
show configuration security zones security-zone trust interfaces ge-0/0/0.0
show security zones security-zone trust
```

Warning: do not set `system-services all` on an untrusted interface. That change can expose management services to an untrusted network.

### Task: permit one routing protocol to the SRX

```text
set security zones security-zone trust interfaces ge-0/0/0.0 host-inbound-traffic protocols ospf
show configuration security zones security-zone trust interfaces ge-0/0/0.0
show security zones security-zone trust
```

The source confirms protocol entries under the interface host inbound traffic hierarchy.

## 3. Security policy match and action

A security policy matches a source zone, a destination zone, addresses, applications, and optional services. The action permits, denies, or rejects the matched traffic.

### Task: permit a specific application from trust to untrust

```text
set security policies from-zone trust to-zone untrust policy permit-web match source-address any
set security policies from-zone trust to-zone untrust policy permit-web match destination-address web-server
set security policies from-zone trust to-zone untrust policy permit-web match application junos-http
set security policies from-zone trust to-zone untrust policy permit-web then permit
show security policies from-zone trust to-zone untrust
show configuration security policies from-zone trust to-zone untrust policy permit-web
```

The source confirms the `from-zone`, `to-zone`, `match source-address`, `match destination-address`, `match application`, and `then permit` policy hierarchy.

### Task: deny traffic from untrust to trust

```text
set security policies from-zone untrust to-zone trust policy deny-all match source-address any
set security policies from-zone untrust to-zone trust policy deny-all match destination-address any
set security policies from-zone untrust to-zone trust policy deny-all match application any
set security policies from-zone untrust to-zone trust policy deny-all then deny
show security policies from-zone untrust to-zone trust
show configuration security policies from-zone untrust to-zone trust policy deny-all
```

A deny action silently drops traffic. Use `then reject` only when the design requires a response to the sender.

### Task: attach UTM or IDP to a permitted policy

```text
set security policies from-zone trust to-zone untrust policy permit-web then permit application-services utm-policy utmp1
set security policies from-zone trust to-zone untrust policy permit-web then permit application-services idp-policy idp1
show security policies from-zone trust to-zone untrust
show configuration security policies from-zone trust to-zone untrust policy permit-web
```

The UTM and IDP guides confirm the `application-services` attachment under a permitted policy.

## 4. Policy order

Junos evaluates policies in order within a zone pair. A match is terminal, so no later policy can change the result.

### Task: move a specific policy before a broad policy

```text
insert security policies from-zone trust to-zone untrust policy permit-mail before policy permit-all
show security policies from-zone trust to-zone untrust
show configuration security policies from-zone trust to-zone untrust | display set
```

Warning: a broad permit policy above a specific deny policy can expose a service. Move the specific policy above the broad policy before you commit.

## 5. Global policy

A global policy can match traffic across multiple zones. Use it only when one rule must apply across many zone pairs.

### Task: configure a global permit policy

```text
set security policies global policy gp1 match source-address server1
set security policies global policy gp1 match destination-address server2
set security policies global policy gp1 match application any
set security policies global policy gp1 then permit
show security policies global
show configuration security policies global policy gp1
```

### Task: configure a global deny policy

```text
set security policies global policy gp2 match source-address server2
set security policies global policy gp2 match destination-address server1
set security policies global policy gp2 match application junos-ftp
set security policies global policy gp2 then deny
show security policies global policy-name gp2
show configuration security policies global policy gp2
```

Warning: a missing final deny in a global design can let later zone policies handle traffic differently than expected. Read both global and zone policy lists.

### Task: match multiple zones in one global policy

```text
set security policies global policy Pa match source-address any
set security policies global policy Pa match destination-address any
set security policies global policy Pa match application any
set security policies global policy Pa match from-zone zone1
set security policies global policy Pa match from-zone zone2
set security policies global policy Pa match to-zone zone3
set security policies global policy Pa match to-zone zone4
set security policies global policy Pa then permit
show security policies global policy-name Pa
```

The Security Basics guide confirms these commands in the global policy examples.

## 6. Unified policy and application identifier

A unified policy can use the application identifier through dynamic application matching. Use it when Layer 3 and Layer 4 data is not enough.

### Task: match a dynamic application in a policy service

```text
set security application-firewall rule-sets social-network rule google-rule match dynamic-application junos:GOOGLETALK
set security application-firewall rule-sets social-network rule denied-sites match dynamic-application-groups junos:social-networking
set security policies from-zone trust to-zone untrust policy permit-app then permit application-services application-firewall rule-set social-network
show security policies from-zone trust to-zone untrust
show security flow session application-firewall dynamic-application junos:FTP
```

The AppSecure guide confirms `dynamic-application`, `dynamic-application-group`, and the policy attachment through `application-services application-firewall`.

### Task: verify application classification

```text
show security flow session application-firewall dynamic-application junos:FTP
show security flow session application-firewall dynamic-application junos:UNKNOWN extensive
show security flow session application-firewall dynamic-application-group junos:WEB
```

If the application is `junos:UNKNOWN`, update the application package and test again before you change the policy.

## 7. Troubleshooting checklist

Use this order when traffic does not match the expected policy.

1. Run `show interfaces terse` and verify that both logical interfaces are up.
2. Run `show security zones` and verify the from-zone and to-zone.
3. Run `show configuration security zones | display set` and verify host inbound traffic when the traffic targets the SRX.
4. Run `show security policies from-zone <source-zone> to-zone <destination-zone>` and verify policy order.
5. Run `show security flow session` and verify the session direction.
6. Run `show log messages | match RT_FLOW` when logging is enabled.

## 8. Sources

| ID | Source | Release | Use |
| - | - | - | - |
| ZP-1 | Junos OS Security Basics Guide for Security Devices | SRX document set, modified 2017-07-18 | Zones, host inbound traffic, security policy, global policy, and policy order. |
| ZP-2 | Junos OS AppSecure Services Feature Guide for Security Devices | SRX document set, modified 2017-09-10 | Dynamic application and application firewall policy attachment. |
| ZP-3 | Junos OS VPN Feature Guide for Security Devices | SRX document set, modified 2017-08-14 | `st0.0` zone binding for route-based VPN. |
