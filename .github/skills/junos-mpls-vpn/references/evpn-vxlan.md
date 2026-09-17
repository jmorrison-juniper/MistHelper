# EVPN and VXLAN

Use this reference for EVPN over MPLS, EVPN over VXLAN, EVPN route types,
EVPN multihoming, VNI policy, and OVSDB VXLAN.

Primary source: Junos OS EVPN User Guide, Junos 26.2.
Public URL: https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip
Staged corpus: `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/evpn.md`.

Supplemental source: Junos OS EVPN User Guide, Junos 26.2 snapshot.
Public URL: https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip
Staged corpus: `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/evpn-vxlan.md`.

OVSDB source: Junos OS OVSDB and VXLAN User Guide, Junos 26.2.
Public URL: https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip
Staged corpus: `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/ovsdb-vxlan.md`.

## Contents

1. [EVPN control plane](#evpn-control-plane)
2. [EVPN over MPLS](#evpn-over-mpls)
3. [EVPN over VXLAN](#evpn-over-vxlan)
4. [VNI import and export](#vni-import-and-export)
5. [EVPN multihoming](#evpn-multihoming)
6. [OVSDB and VXLAN](#ovsdb-and-vxlan)
7. [Troubleshooting path](#troubleshooting-path)
8. [Command evidence](#command-evidence)

## EVPN control plane

EVPN uses BGP to advertise reachability for Ethernet services. EVPN route types
carry MAC addresses, IP bindings, Ethernet segment information, and inclusive
multicast state. The guides cover EVPN-VXLAN, EVPN-MPLS, EVPN-VPWS, and VPLS
migration cases.

Use the EVPN route table to check control plane state. Use the EVPN database or
MAC table to check learned endpoint state.

## EVPN over MPLS

### Task

Use EVPN over MPLS when the data plane uses MPLS labels and the control plane
uses EVPN routes. Verify the MPLS transport first, then verify `bgp.evpn.0`.

Warning: do not change EVPN over MPLS before you verify the RSVP or LDP path.
A control plane repair cannot fix a broken transport LSP.

### Verified commands

```text
set protocols rsvp interface all
set protocols mpls interface all
set protocols ldp interface ge-0/0/0.0
set protocols mpls label-switched-path pe1-rr to 10.0.255.3
set routing-instances routing-instance-name instance-type evpn
```

### Verify

```text
show route table bgp.evpn.0
show route table mpls.0
```

Citation: EVPN guide, Junos 26.2, public URL above, staged corpus `evpn.md`,
pages 28, 126, 133, 190, and 356.

## EVPN over VXLAN

### Task

Use EVPN over VXLAN when BGP EVPN supplies the control plane and VXLAN carries
bridged tenant traffic. Configure the VTEP source, VNI list, and route target.

Warning: a wrong VNI can bridge tenant traffic into the wrong segment. Verify
all VNI values against the change plan before commit.

### Verified commands

```text
set switch-options vtep-source-interface lo0.0
set switch-options route-distinguisher 10.2.3.1:1
set switch-options vrf-target target:1111:11
set protocols evpn encapsulation vxlan
set protocols evpn extended-vni-list all
set routing-instances EVPN-VXLAN-1 vtep-source-interface lo0.0
set routing-instances EVPN-VXLAN-1 vtep-source-interface lo0.81
```

### Verify

```text
show route table bgp.evpn.0
show evpn database
show evpn mac-table
```

Citation: EVPN guide, Junos 26.2, public URL above, staged corpus `evpn.md`,
pages 508, 509, 1794, and 1858. The `lo0.81` VTEP command comes from staged
corpus `evpn-vxlan.md`, page 1582.

## VNI import and export

### Task

Use per-VNI route targets when each tenant segment needs an explicit import or
export value. Use automatic route targets only when the design permits that
policy.

Warning: automatic route target values can affect many VNIs at once. Verify the
intended VNI list before commit.

### Verified commands

```text
set protocols evpn vni-options vni 101 vrf-target target:65000:101
set protocols evpn vni-options vni 102 vrf-target target:65000:102
set switch-options vrf-target auto import-as 207 vni-list all
set switch-options vrf-target auto export-as 207 vni-list all
set switch-options vrf-target auto as-num 209 vni-list all
```

Citation: EVPN guide, Junos 26.2, public URL above, staged corpus `evpn.md`,
pages 155, 156, and 844.

## EVPN multihoming

### Task

Use multihoming when a customer or server connects to more than one PE or leaf.
The Ethernet segment identifier lets EVPN advertise redundancy state.

Warning: a wrong ESI can join unrelated links into one Ethernet segment. This
can blackhole or duplicate traffic.

### Verified commands

```text
set interfaces ae0 esi 00:11:22:33:44:55:66:77:88:99
set interfaces ae0 esi single-active
set interfaces ae0 esi 00:11:11:11:11:11:11:11:11:11
set interfaces ae0 esi all-active
```

### Verify

```text
show route table bgp.evpn.0
show evpn instance extensive
```

Citation: EVPN guide, Junos 26.2, public URL above, staged corpus `evpn.md`,
pages 355, 424, and 190.

## OVSDB and VXLAN

### Task

Use OVSDB VXLAN references when a controller controls VXLAN state. The staged
set has one MX and EX9200 guide, one QFX NSX guide, and one QFX Contrail guide.

Warning: do not mix manual EVPN VXLAN commands with controller-owned state
unless the design allows it. The controller can replace local changes.

### Verify

```text
show evpn database
```

Citation: OVSDB and VXLAN guide, Junos 26.2, public URL above, staged corpus
`ovsdb-vxlan.md`, page 120. QFX NSX and QFX Contrail guide rows are in the
corpus index.

## Troubleshooting path

1. Verify the underlay route to each VTEP or PE loopback.
2. Verify MPLS transport if the service is EVPN over MPLS.
3. Verify BGP EVPN routes with `show route table bgp.evpn.0`.
4. Verify the EVPN database with `show evpn database`.
5. Verify learned MAC state with `show evpn mac-table`.
6. If multihoming fails, verify ESI values and active mode.
7. If a controller owns VXLAN state, verify controller state before local edit.

Warning: do not clear EVPN state before you preserve evidence. A clear can hide
the route or MAC state that identifies the fault.

## Command evidence

| Command | Page | Source | Use |
| - | - | - | - |
| `set protocols rsvp interface all` | 126 | `evpn.md` | Enable RSVP for EVPN MPLS sample. |
| `set protocols mpls interface all` | 126 | `evpn.md` | Enable MPLS for EVPN MPLS sample. |
| `set protocols ldp interface ge-0/0/0.0` | 356 | `evpn.md` | Enable LDP on one interface. |
| `set protocols mpls label-switched-path pe1-rr to 10.0.255.3` | 126 | `evpn.md` | Define an LSP to a route reflector. |
| `set routing-instances routing-instance-name instance-type evpn` | 28 | `evpn.md` | Create an EVPN instance. |
| `set switch-options vtep-source-interface lo0.0` | 508 | `evpn.md` | Set the VTEP source interface. |
| `set switch-options route-distinguisher 10.2.3.1:1` | 508 | `evpn.md` | Set switch EVPN RD. |
| `set switch-options vrf-target target:1111:11` | 508 | `evpn.md` | Set switch EVPN route target. |
| `set protocols evpn encapsulation vxlan` | 509 | `evpn.md` | Set VXLAN encapsulation. |
| `set protocols evpn extended-vni-list all` | 509 | `evpn.md` | Allow all extended VNIs. |
| `set protocols evpn vni-options vni 101 vrf-target target:65000:101` | 844 | `evpn.md` | Set a VNI route target. |
| `set protocols evpn vni-options vni 102 vrf-target target:65000:102` | 844 | `evpn.md` | Set another VNI route target. |
| `set switch-options vrf-target auto import-as 207 vni-list all` | 155 | `evpn.md` | Configure automatic import targets. |
| `set switch-options vrf-target auto export-as 207 vni-list all` | 155 | `evpn.md` | Configure automatic export targets. |
| `set switch-options vrf-target auto as-num 209 vni-list all` | 156 | `evpn.md` | Configure automatic route targets. |
| `set interfaces ae0 esi 00:11:22:33:44:55:66:77:88:99` | 355 | `evpn.md` | Set one ESI. |
| `set interfaces ae0 esi single-active` | 355 | `evpn.md` | Set single-active multihoming. |
| `set interfaces ae0 esi 00:11:11:11:11:11:11:11:11:11` | 424 | `evpn.md` | Set another ESI. |
| `set interfaces ae0 esi all-active` | 424 | `evpn.md` | Set all-active multihoming. |
| `set routing-instances EVPN-VXLAN-1 vtep-source-interface lo0.0` | 1858 | `evpn.md` | Set VTEP source in an instance. |
| `set routing-instances EVPN-VXLAN-1 vtep-source-interface lo0.81` | 1582 | `evpn-vxlan.md` | Set VTEP source in another instance. |
| `show route table bgp.evpn.0` | 190 | `evpn.md` | Read EVPN BGP routes. |
| `show route table mpls.0` | 133 | `evpn.md` | Read MPLS labels for EVPN. |
| `show evpn database` | 37 | `evpn.md` | Read the EVPN database. |
| `show evpn instance extensive` | 158 | `evpn-vxlan.md` | Read detailed EVPN instance state. |
| `show evpn mac-table` | 1794 | `evpn.md` | Read EVPN MAC state. |
