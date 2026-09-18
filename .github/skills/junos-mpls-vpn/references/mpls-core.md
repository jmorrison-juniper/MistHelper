# MPLS core

Use this reference for MPLS forwarding, LDP, RSVP, traffic engineering, fast
repair, and segment routing.

Source: Junos OS MPLS Applications User Guide, Junos 26.2.
Public URL: https://www.juniper.net/documentation/en_US/release-independent/downloads/juniper-PDFs-junos-262.zip
Staged corpus: `markdown2/extracted/juniper-PDFs-junos-262/juniper-PDFs-junos-262/mpls.md`.

## Contents

1. [MPLS forwarding model](#mpls-forwarding-model)
2. [Enable MPLS on an interface](#enable-mpls-on-an-interface)
3. [Use RSVP for an explicit LSP](#use-rsvp-for-an-explicit-lsp)
4. [Use LDP for label distribution](#use-ldp-for-label-distribution)
5. [Use traffic engineering](#use-traffic-engineering)
6. [Use fast repair](#use-fast-repair)
7. [Use segment routing](#use-segment-routing)
8. [Troubleshooting path](#troubleshooting-path)
9. [Command evidence](#command-evidence)

## MPLS forwarding model

MPLS forwards packets with labels instead of only the IP lookup. An ingress
router pushes a label. A transit router swaps a label. An egress router removes
the label or receives an already exposed packet.

A label stack supports nested services. For example, a transport label can carry
a VPN label. The PE uses the outer label to cross the provider core. The egress
PE uses the inner label to select the customer service.

Use `mpls.0` to verify label forwarding entries. Use `inet.3` to verify routes
that resolve over LSP next hops.

## Enable MPLS on an interface

### Task

Enable the interface family first. Then enable MPLS under `protocols mpls`.
Use an IGP with traffic engineering when RSVP or constraint-based routing uses
link attributes.

Warning: do not add MPLS to a customer access interface unless the design says
that interface carries labels. A wrong interface can accept labeled traffic from
an untrusted peer.

### Verified command

```text
set protocols mpls interface ge-0/0/5.0
```

### Verify

```text
show route table mpls.0
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
pages 88 and 480.

## Use RSVP for an explicit LSP

### Task

Use RSVP when the LSP needs an explicit path, bandwidth, constraint-based
routing, or link protection. RSVP signals a path and reserves resources.

Warning: a changed RSVP LSP can move traffic immediately after commit. Use a
change window and `commit confirmed 2` on a remote PE.

### Verified commands

```text
set protocols rsvp interface lo0.0
set protocols rsvp interface all
set protocols mpls label-switched-path lsp_to_pe2_ge1 to 127.1.1.3
set protocols mpls path via-p1 10.255.0.2 strict
set protocols mpls label-switched-path pe1-pe2 primary via-p1
set protocols mpls label-switched-path pe1-pe2 secondary path2 standby
set protocols mpls optimize-timer 120
```

### Verify

```text
show rsvp session
show rsvp interfaces
show mpls lsp ingress extensive
show mpls lsp extensive ingress
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
pages 88, 103, 309, 318, 488, and 490.

## Use LDP for label distribution

### Task

Use LDP when the core needs hop-by-hop label distribution without explicit RSVP
paths. Verify the neighbor and session before you depend on it for a service.

Warning: removing LDP from a core interface can remove the label path for VPN
traffic. Check dependent services before the change.

### Verified command

```text
set protocols ldp interface fe-1/2/1.0
```

### Verify

```text
show ldp neighbor
show ldp session detail
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
pages 134, 1407, and 1441.

## Use traffic engineering

### Task

Use traffic engineering when route resolution must prefer an LSP, or when an
IGP must advertise link attributes for path calculation.

Warning: a traffic engineering change can alter BGP next-hop resolution. Verify
`inet.3` and the affected VPN tables after commit.

### Verified commands

```text
set protocols ospf traffic-engineering
set protocols isis traffic-engineering l3-unicast-topology
set protocols mpls traffic-engineering bgp-igp
set protocols mpls traffic-engineering bgp-igp-both-ribs
```

### Verify

```text
show route table inet.3
show route table mpls.0
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
pages 88, 113, 157, 407, 937, and 480.

## Use fast repair

### Task

Use standby paths or link protection when traffic needs local repair after a
core fault. Confirm platform support and path diversity before the change.

Warning: link protection without a diverse repair path can give false safety.
A core fault can still drop the LSP.

### Verified commands

```text
set protocols mpls label-switched-path pe1-pe2 link-protection
set protocols rsvp interface ge-0/0/2.0 link-protection
set protocols rsvp interface ge-0/0/2.0 link-protection exclude-srlg
set routing-options forwarding-table ecmp-fast-reroute
```

### Verify

```text
show mpls lsp extensive ingress
show rsvp interfaces
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
pages 330, 331, 362, 488, and 978.

## Use segment routing

### Task

Use the segment routing content when the design uses source packet routing or
SPRING traffic engineering. The staged source covers static segment routing
paths and IS-IS segment advertisements.

Warning: a wrong segment list can force traffic through an unintended node. This
can overload a link or bypass a required inspection point.

### Verified commands

```text
set protocols source-packet-routing segment-list sl-15-primary hop-1 ip-address 10.10.13.3
set protocols source-packet-routing segment-list sl-15-primary hop-2 label 1000134
set protocols source-packet-routing source-routing-path lsp-15 to 192.168.146.181
set protocols source-packet-routing source-routing-path lsp-15 binding-sid 1000999
set protocols source-packet-routing source-routing-path lsp-15 primary sl-15-primary
set protocols isis interface all node-link-protection
set protocols isis source-packet-routing adjacency-segment hold-time 240000
set policy-options policy-statement prefix-sid term 1 then prefix-segment node-segment
```

### Verify

```text
show spring-traffic-engineering overview
show spring-traffic-engineering lsp name srlsp1 detail
show route 10.7.7.7 protocol spring-te active-path table inet.3
```

Citation: MPLS guide, Junos 26.2, public URL above, staged corpus `mpls.md`,
pages 884, 898, 899, 913, 928, 929, 933, and 936.

## Troubleshooting path

1. Verify that MPLS has a forwarding entry with `show route table mpls.0`.
2. Verify the route resolution table with `show route table inet.3`.
3. If RSVP carries the LSP, verify `show rsvp session`.
4. If LDP carries the label path, verify `show ldp neighbor`.
5. Verify the ingress LSP with `show mpls lsp ingress extensive`.
6. If segment routing carries traffic, verify the SPRING LSP detail.

Warning: do not repair an MPLS fault by deleting a protocol stanza first. A
delete can remove the remaining path and increase the outage.

## Command evidence

| Command | Page | Use |
| - | - | - |
| `set protocols mpls interface ge-0/0/5.0` | 88 | Enable MPLS on one interface. |
| `set protocols rsvp interface lo0.0` | 88 | Enable RSVP on loopback. |
| `set protocols rsvp interface all` | 167 | Enable RSVP on all interfaces in the sample. |
| `set protocols ldp interface fe-1/2/1.0` | 134 | Enable LDP on one interface. |
| `set protocols ospf traffic-engineering` | 88 | Advertise traffic engineering data in OSPF. |
| `set protocols isis traffic-engineering l3-unicast-topology` | 937 | Advertise IS-IS traffic engineering data. |
| `set protocols mpls traffic-engineering bgp-igp` | 113 | Resolve BGP through traffic engineered paths. |
| `set protocols mpls traffic-engineering bgp-igp-both-ribs` | 407 | Use both BGP and IGP routing tables. |
| `set protocols mpls label-switched-path lsp_to_pe2_ge1 to 127.1.1.3` | 88 | Define an RSVP LSP destination. |
| `set protocols mpls path via-p1 10.255.0.2 strict` | 309 | Define a strict explicit hop. |
| `set protocols mpls label-switched-path pe1-pe2 primary via-p1` | 309 | Attach a primary path. |
| `set protocols mpls label-switched-path pe1-pe2 secondary path2 standby` | 309 | Attach a standby secondary path. |
| `set protocols mpls label-switched-path pe1-pe2 link-protection` | 330 | Enable LSP link protection. |
| `set protocols rsvp interface ge-0/0/2.0 link-protection` | 331 | Enable RSVP link protection. |
| `set protocols rsvp interface ge-0/0/2.0 link-protection exclude-srlg` | 362 | Avoid shared-risk links in protection. |
| `set routing-options forwarding-table ecmp-fast-reroute` | 978 | Enable ECMP fast repair. |
| `set protocols source-packet-routing segment-list sl-15-primary hop-1 ip-address 10.10.13.3` | 898 | Define a segment routing first hop. |
| `set protocols source-packet-routing segment-list sl-15-primary hop-2 label 1000134` | 898 | Define a segment label. |
| `set protocols source-packet-routing source-routing-path lsp-15 to 192.168.146.181` | 898 | Define a segment routing LSP end point. |
| `set protocols source-packet-routing source-routing-path lsp-15 binding-sid 1000999` | 898 | Set a binding SID. |
| `set protocols source-packet-routing source-routing-path lsp-15 primary sl-15-primary` | 899 | Attach the primary segment list. |
| `set protocols isis interface all node-link-protection` | 928 | Enable node and link protection in IS-IS. |
| `set protocols isis source-packet-routing adjacency-segment hold-time 240000` | 929 | Set adjacency segment hold time. |
| `set policy-options policy-statement prefix-sid term 1 then prefix-segment node-segment` | 928 | Advertise a node segment. |
| `show route table mpls.0` | 480 | Read label forwarding entries. |
| `show route table inet.3` | 157 | Read LSP route resolution. |
| `show mpls lsp ingress extensive` | 318 | Read ingress LSP detail. |
| `show mpls lsp extensive ingress` | 488 | Read detailed ingress LSP state. |
| `show ldp neighbor` | 1441 | Read LDP neighbors. |
| `show ldp session detail` | 1407 | Read LDP session detail. |
| `show rsvp interfaces` | 490 | Read RSVP interface state. |
| `show rsvp session` | 103 | Read RSVP sessions. |
| `show spring-traffic-engineering overview` | 913 | Read SPRING overview. |
| `show spring-traffic-engineering lsp name srlsp1 detail` | 933 | Read one SPRING LSP. |
| `show route 10.7.7.7 protocol spring-te active-path table inet.3` | 884 | Read active SPRING route resolution. |
