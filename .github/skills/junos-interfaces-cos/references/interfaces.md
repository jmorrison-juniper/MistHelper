# Interfaces

## Contents

1. [Source scope](#source-scope)
2. [Interface names](#interface-names)
3. [Physical interface tasks](#physical-interface-tasks)
4. [Logical unit tasks](#logical-unit-tasks)
5. [Optics and transceivers](#optics-and-transceivers)
6. [Aggregated Ethernet and load balance](#aggregated-ethernet-and-load-balance)
7. [Read commands](#read-commands)

## Source scope

Use this reference for Junos interface work on routers, switches, security
devices, and Junos Evolved devices. The staged source train is Junos 26.2.

Primary sources:

- `interfaces-fundamentals`: Junos OS Interfaces Fundamentals for Junos OS,
  Junos 26.2.
- `interfaces-fundamentals-evo`: Junos OS Evolved Interfaces Fundamentals,
  Junos 26.2.
- `interfaces-ethernet`: Junos OS Ethernet Interfaces User Guide for Routing
  Devices, Junos 26.2.
- `interfaces-ethernet-switches`: Interfaces User Guide for Switches,
  Junos 26.2.
- `interfaces-security-devices`: Junos OS Interfaces User Guide for Security
  Devices, Junos 26.2.

Warning: an interface change on a live device can drop traffic. Verify the peer
state and the rollback plan before you commit the change.

## Interface names

Use this pattern for most physical interfaces:

```text
type-fpc/pic/port.unit
```

The `type` part names the media type. Common examples include `ge`, `xe`, and
`et`. The `fpc` part names the FPC slot. The `pic` part names the PIC location.
The `port` part names the port on that PIC. The `unit` part names the logical
unit, such as `.0`.

Example:

```text
ge-0/0/0.0
```

This example is a Gigabit Ethernet interface on FPC 0, PIC 0, port 0, and
logical unit 0.

Source: Junos OS Interfaces Fundamentals for Junos OS, Junos 26.2, pages 17 to
18. The Junos Evolved source states the same structure on pages 11 to 13.

## Physical interface tasks

### Add a description

Use the description to state the circuit, peer, or purpose.

```text
set interfaces ge-0/0/0 description "to R2 ge-0/0/0"
```

Verify the result:

```text
show configuration interfaces
```

Source: Junos OS Adaptive Services Interfaces User Guide for Routing Devices,
Junos 26.2, page 810.

### Disable an interface

Warning: disabling an interface drops all traffic on that interface. Confirm an
out-of-band recovery path before you commit the change.

Enter the interface hierarchy. Then set the `disable` statement.

```text
edit interfaces et-0/3/2
set disable
```

Verify the result:

```text
show configuration interfaces
```

Source: Junos OS Interfaces Fundamentals for Junos OS, Junos 26.2, pages 43 to
44. Junos Evolved gives the same task on page 39.

### Set MTU

Warning: an MTU mismatch can drop large packets. Verify the peer MTU before you
commit the change.

```text
set interfaces xe-7/0/2 mtu 9192
```

Verify the result:

```text
show interfaces terse
```

Source: Next Gen Services Interfaces User Guide for Routing Devices, Junos
26.2, page 391. The adaptive services guide also shows this command on page
1277.

### Set speed and duplex

Warning: a speed or duplex mismatch can drop traffic. Verify the peer setting
before you commit the change.

Disable autonegotiation only when the peer also uses a fixed setting.

```text
set interfaces ge-0/0/0 ether-options no-auto-negotiation
set interfaces ge-0/0/0 speed 100m
set interfaces ge-0/0/0 link-mode full-duplex
```

Some switch examples set half duplex on a test interface:

```text
set interfaces ge-0/0/3 link-mode half-duplex
```

For selected high-speed Ethernet ports, set the speed from the interface
hierarchy:

```text
edit interfaces et-1/0/3
set speed 100g
```

Verify the result:

```text
show interfaces ge-0/0/0 extensive
```

Sources:

- Interfaces User Guide for Switches, Junos 26.2, pages 16 and 28.
- Junos OS Interfaces User Guide for Security Devices, Junos 26.2, page 83.
- Junos OS Ethernet Interfaces User Guide for Routing Devices, Junos 26.2,
  page 192.

## Logical unit tasks

### Add an IPv4 address

```text
set interfaces ge-0/0/0 unit 0 family inet address 10.1.12.2/30
```

Verify the result:

```text
show interfaces terse ge*
```

Source: Junos OS Adaptive Services Interfaces User Guide for Routing Devices,
Junos 26.2, page 810.

### Configure VLAN tagging

```text
set interfaces ge-0/0/0 vlan-tagging
set interfaces ge-0/0/0.0 vlan-id 101
```

Verify the result:

```text
show configuration interfaces
```

Source: Junos OS Interfaces Fundamentals for Junos OS, Junos 26.2, page 70.

### Apply an input filter

Warning: a wrong input filter can block management traffic. Verify the accepted
sources before you commit the change.

```text
set interfaces ge-0/0/0 unit 0 family ethernet-switching filter input voip_class
```

Verify the result:

```text
show configuration interfaces
```

Source: Junos OS for EX Series Ethernet Switches Class of Service User Guide,
Junos 26.2, page 24.

### Apply an output filter

Warning: a wrong output filter can drop user traffic. Verify the match terms
before you commit the change.

```text
set interfaces ge-2/0/8 unit 0 family inet filter output mf-classifier
```

Verify the result:

```text
show configuration interfaces
```

Source: Junos OS Class of Service User Guide for Routers, Junos 26.2, page 219.

## Optics and transceivers

Use hardware inventory and optics diagnostics together. Inventory confirms the
module. Diagnostics confirm light levels, voltage, and temperature.

```text
show chassis hardware
show interfaces diagnostics optics et-0/0/10
```

Verify the interface state:

```text
show interfaces terse et*
```

Sources:

- Next Gen Services Interfaces User Guide for Routing Devices, Junos 26.2,
  page 119.
- Junos OS Ethernet Interfaces User Guide for Routing Devices, Junos 26.2,
  page 333.

## Aggregated Ethernet and load balance

### Create an aggregated Ethernet bundle

Warning: a bundle change can drop traffic on all member links. Verify both ends
of the bundle before you commit the change.

Set the number of aggregated Ethernet devices. Then add member links.

```text
set chassis aggregated-devices ethernet device-count 10
set interfaces xe-0/0/2 ether-options 802.3ad ae0
set interfaces ae0 aggregated-ether-options lacp active
set interfaces ae0 unit 0 family inet address 120.168.104.1/30
```

Verify the result:

```text
show interfaces terse
```

Sources:

- Junos OS Class of Service User Guide for Routers, Junos 26.2, page 1073.
- Interfaces User Guide for Switches, Junos 26.2, page 46.
- Junos OS Ethernet Interfaces User Guide for Routing Devices, Junos 26.2,
  page 90.

### Set the aggregated Ethernet link speed

```text
set interfaces ae0 aggregated-ether-options link-speed 1g
```

For mixed member speeds on supported platforms, use the interface hierarchy.

```text
edit interfaces ae0 aggregated-ether-options
set link-speed mixed
```

Verify the result:

```text
show configuration interfaces
```

Sources:

- Junos OS Ethernet Interfaces User Guide for Routing Devices, Junos 26.2,
  page 90.
- Junos OS Interfaces Fundamentals for Junos OS, Junos 26.2, page 62.

### Configure dynamic load balancing

Warning: a load balance change can reorder packets. Verify the application risk
before you commit the change.

```text
set forwarding-options enhanced-hash-key ecmp-dlb per-packet
```

Verify the result:

```text
show forwarding-options enhanced-hash-key
```

To inspect a configured hash key on a router, read the configuration.

```text
show configuration forwarding-options hash-key
```

Sources:

- Interfaces User Guide for Switches, Junos 26.2, pages 111 and 121.
- Junos OS Ethernet Interfaces User Guide for Routing Devices, Junos 26.2,
  page 77.

## Read commands

Use these commands before and after a change.

| Task | Command | Source |
| - | - | - |
| List configured and operational interfaces. | `show interfaces terse` | Interfaces Fundamentals, Junos 26.2, page 17. |
| List Gigabit Ethernet interfaces. | `show interfaces terse ge*` | Ethernet Interfaces, Junos 26.2, page 438. |
| Check a physical interface. | `show interfaces ge-0/0/0 extensive` | Class of Service for Routers, Junos 26.2, page 57. |
| Read transceiver diagnostics. | `show interfaces diagnostics optics et-0/0/10` | Ethernet Interfaces, Junos 26.2, page 333. |
| Read hardware inventory. | `show chassis hardware` | Next Gen Services Interfaces, Junos 26.2, page 119. |
