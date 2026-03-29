[<- Back to Diagram Index](../README.md)

# Network Protocols

Packet structure documentation for MistHelper's packet capture feature (Menu 9-10).

## Captured Packet Structure

Typical 802.11 frame structure captured by MistHelper's PacketCaptureManager.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
packet-beta
    title IEEE 802.11 Frame Structure
    0-1: "Frame Control (2B)"
    2-3: "Duration/ID (2B)"
    4-9: "Address 1 - Destination (6B)"
    10-15: "Address 2 - Source (6B)"
    16-21: "Address 3 - BSSID (6B)"
    22-23: "Seq Control (2B)"
    24-31: "Frame Body (variable)"
    32-35: "FCS (4B)"
```

> **PNG fallback**: If the packet-beta diagram does not render, see [network-protocols.png](network-protocols.png).

## Ethernet Frame (Switch Captures)

For switch port-specific captures using tcpdump filtering.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
packet-beta
    title Ethernet II Frame (Switch Port Capture)
    0-5: "Dest MAC (6B)"
    6-11: "Src MAC (6B)"
    12-13: "EtherType (2B)"
    14-17: "VLAN Tag 802.1Q (4B optional)"
    18-21: "IP Header Start (4B)"
    22-41: "IP Header (20B)"
    42-61: "TCP/UDP Header (20B)"
    62-63: "Payload Start"
```

## Capture Types Supported

| Capture Type | Menu | Target | Method |
|-------------|------|--------|--------|
| Wireless Client | 9, 10 | AP radio interface | Mist Cloud API |
| Wired Client | 9, 10 | Switch port | tcpdump filtering |
| Gateway | 9, 10 | Gateway interface | Mist Cloud API |
| Switch | 9, 10 | Switch port | Port-specific tcpdump |
| New Association | 9 | AP during client join | Mist Cloud API |
| Scan Radio | 9 | AP scanning radio | Mist Cloud API |

---

## Related Diagrams

- [Container Architecture](container-architecture.md) - Port mappings and access paths
- [Architecture Overview](../core/architecture-overview.md) - PacketCaptureManager in system context
- [Class Hierarchy: Managers](../class-hierarchy/managers.md) - PacketCaptureManager class detail
