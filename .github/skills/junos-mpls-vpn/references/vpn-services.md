# VPN services

Use this reference for L3VPN, L2VPN, VPLS, and layer 2 circuit tasks.

Source: Junos OS MPLS Applications User Guide, Junos 26.2.
Public URL: https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip
Staged corpus: `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/mpls.md`.

## Contents

1. [Service roles](#service-roles)
2. [Build a layer 3 VPN](#build-a-layer-3-vpn)
3. [Control route import and export](#control-route-import-and-export)
4. [Build a layer 2 VPN](#build-a-layer-2-vpn)
5. [Build a VPLS instance](#build-a-vpls-instance)
6. [Build a layer 2 circuit](#build-a-layer-2-circuit)
7. [Troubleshooting path](#troubleshooting-path)
8. [Command evidence](#command-evidence)

## Service roles

A PE router connects the provider core to one or more customer edge routers. A
P router forwards labeled traffic in the core. A CE router exchanges customer
routes or customer frames with the PE.

A layer 3 VPN uses a VRF on each PE. The route distinguisher makes customer
routes unique. Route targets control import and export. The PE to CE protocol
moves customer routes into the VRF.

A layer 2 VPN or VPLS carries customer layer 2 traffic. A layer 2 circuit maps
one local attachment circuit to one remote circuit.

Warning: a wrong route target can import another customer route into the VRF.
This can leak traffic between customers.

## Build a layer 3 VPN

### Task

Create the VRF, add a route distinguisher, set route targets, and attach the
customer interface. Then configure the PE to CE route exchange.

### Verified commands

```text
set routing-instances MPLS-over-UDP-PE1 instance-type vrf
set routing-instances MPLS-over-UDP-PE1 route-distinguisher 10.127.0.2:1
set routing-instances MPLS-over-UDP-PE1 vrf-target target:600:1
set routing-instances VPN1 instance-type vrf
set routing-instances VPN1 route-distinguisher 100:100
set routing-instances VPN1 vrf-target target:100:1
set protocols bgp group toCE1 type external
set protocols bgp group toCE1 peer-as 65001
set protocols bgp group toCE1 neighbor ::10.1.1.1
```

### Verify

Use these checks from the MPLS guide and the BGP routing context:

```text
show route table inet.3
show route table mpls.0
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
pages 134, 149, 168, 157, and 480.

## Control route import and export

### Task

Use a `vrf-import` policy when route targets alone do not give the required
route selection. Use a `vrf-export` policy when exported routes need a policy.

Warning: a broad import policy can install unexpected customer routes. Verify
matched routes before you commit the policy.

### Verified commands

```text
set routing-instances vpn2CE1 vrf-import vpnimport
set routing-instances vpn2CE1 vrf-export vpnexport
set routing-instances vpn vrf-export vpn-exp
```

### Verify

```text
show route table inet.3
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
pages 413, 456, and 157.

## Build a layer 2 VPN

### Task

Create an L2VPN instance, select an encapsulation, identify the site, and bind
the local attachment circuit to the remote site.

Warning: a wrong remote site identifier can connect the local customer circuit
to the wrong remote site. This can send frames to the wrong customer.

### Verified commands

```text
set routing-instances foo instance-type l2vpn
set routing-instances foo protocols l2vpn encapsulation-type ethernet-vlan
set routing-instances foo protocols l2vpn site foo site-identifier 1
set routing-instances foo protocols l2vpn site foo site-preference primary
set routing-instances foo protocols l2vpn site foo interface ge-2/0/2.0 remote-site-id 2
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
page 432.

## Build a VPLS instance

### Task

Use VPLS when several sites must share a bridged service. The sample creates a
VPLS routing instance and a VPLS site.

Warning: deleting `protocols vpls` can cause traffic loss. The EVPN guide states
that VPLS decommissioning can cause loss of traffic.

### Verified commands

```text
set routing-instances vpls1 instance-type vpls
set routing-instances vpls1 protocols vpls no-tunnel-services
set routing-instances vpls1 protocols vpls site vpls-pe site-identifier 3
set routing-instances vpls1 protocols vpls site vpls-pe best-site
```

Citation: EVPN guide, Junos 26.2, public URL above, staged corpus `evpn.md`,
pages 114, 490, and 491.

## Build a layer 2 circuit

### Task

Use a layer 2 circuit when one local circuit maps to one remote PE neighbor and
one virtual circuit identifier.

Warning: a wrong virtual circuit identifier can bind two different services.
This can break or cross-connect customer traffic.

### Verified command

```text
set protocols l2circuit neighbor 40.1.1.1 interface ge-0/1/1.0 virtual-circuit-id 1
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
page 1905.

## Troubleshooting path

1. Identify the service type and PE role.
2. Verify the MPLS transport with `show route table mpls.0`.
3. Verify LSP resolution with `show route table inet.3`.
4. Check the VRF route target and policy names in configuration.
5. For a layer 2 circuit, check the neighbor address and circuit identifier.
6. For VPLS, check the site identifier and service membership.

Warning: do not change both route import and export in one remote commit. A
single wrong policy can hide the route leak cause.

## Command evidence

| Command | Page | Use |
| - | - | - |
| `set routing-instances MPLS-over-UDP-PE1 instance-type vrf` | 149 | Create a VRF. |
| `set routing-instances MPLS-over-UDP-PE1 route-distinguisher 10.127.0.2:1` | 149 | Set an RD. |
| `set routing-instances MPLS-over-UDP-PE1 vrf-target target:600:1` | 149 | Set a route target. |
| `set routing-instances VPN1 instance-type vrf` | 168 | Create another VRF sample. |
| `set routing-instances VPN1 route-distinguisher 100:100` | 168 | Set another RD sample. |
| `set routing-instances VPN1 vrf-target target:100:1` | 168 | Set another route target sample. |
| `set protocols bgp group toCE1 type external` | 134 | Configure an external CE group. |
| `set protocols bgp group toCE1 peer-as 65001` | 134 | Set the CE AS. |
| `set protocols bgp group toCE1 neighbor ::10.1.1.1` | 134 | Set the CE neighbor. |
| `set routing-instances vpn2CE1 vrf-import vpnimport` | 413 | Apply a VRF import policy. |
| `set routing-instances vpn2CE1 vrf-export vpnexport` | 413 | Apply a VRF export policy. |
| `set routing-instances vpn vrf-export vpn-exp` | 456 | Apply another export sample. |
| `set routing-instances foo instance-type l2vpn` | 432 | Create an L2VPN instance. |
| `set routing-instances foo protocols l2vpn encapsulation-type ethernet-vlan` | 432 | Set L2VPN encapsulation. |
| `set routing-instances foo protocols l2vpn site foo site-identifier 1` | 432 | Set the local L2VPN site. |
| `set routing-instances foo protocols l2vpn site foo site-preference primary` | 432 | Set site preference. |
| `set routing-instances foo protocols l2vpn site foo interface ge-2/0/2.0 remote-site-id 2` | 432 | Bind an attachment circuit. |
| `set protocols l2circuit neighbor 40.1.1.1 interface ge-0/1/1.0 virtual-circuit-id 1` | 1905 | Bind a layer 2 circuit. |
| `set routing-instances vpls1 instance-type vpls` | 490 | Create a VPLS instance. |
| `set routing-instances vpls1 protocols vpls no-tunnel-services` | 491 | Configure VPLS without tunnel services. |
| `set routing-instances vpls1 protocols vpls site vpls-pe site-identifier 3` | 491 | Set the VPLS site identifier. |
| `set routing-instances vpls1 protocols vpls site vpls-pe best-site` | 491 | Prefer the VPLS site. |
| `show route table inet.3` | 157 | Read LSP route resolution. |
| `show route table mpls.0` | 480 | Read label forwarding entries. |
