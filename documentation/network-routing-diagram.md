# Network Routing Diagram

Vertical 8-level topology: two datacenters (Dallas, Chicago) with Juniper SSR1300 hub pairs,
a branch site with Juniper SSR130 router pair, EX4400/EX4100 switching, and full-mesh WAN tunnels.

```mermaid
flowchart TD
    %% ===== Levels 1-2: TACACS and Nexus (LR subgraph for alignment) =====
    subgraph DCTop[" Datacenter Services "]
        direction LR
        subgraph DallasTop[" Dallas "]
            TACACS_D["TACACS / RADIUS (Vlan_All)"] -->|"L3"| NEX_D["Cisco Nexus L3<br/>Core Switch"]
        end
        subgraph ChicagoTop[" Chicago "]
            TACACS_C["TACACS / RADIUS (Vlan_All)"] -->|"L3"| NEX_C["Cisco Nexus L3<br/>Core Switch"]
        end
    end

    %% ===== Level 3: SSR1300 Hub Pairs (single LR subgraph) =====
    subgraph HubPairs[" SSR1300 Hub Router Pairs "]
        direction LR
        HUB_DA["Dallas<br/>Active"] <-->|"State<br/>Sync"| HUB_DI["Dallas<br/>Inactive"]
        HUB_DI ~~~ HUB_CA["Chicago<br/>Active"]
        HUB_CA <-->|"State<br/>Sync"| HUB_CI["Chicago<br/>Inactive"]
    end

    NEX_D --> LAN_BGP_D["LAN / BGP (VREDAL52_VLAN12/14)"] --> HubPairs
    NEX_C --> LAN_BGP_C["LAN / BGP (VRECHI52_VLAN4/6)"] --> HubPairs

    %% ===== Level 4: Internet WAN Cloud =====
    HubPairs -->|"Dedicated WAN"| INET(("Internet<br/>WAN Cloud"))

    %% ===== Level 5: SSR130 Branch Pair =====
    subgraph BranchPair[" SSR130 Branch Router Pair "]
        direction LR
        BR_A["Active"] <-->|"State Sync"| BR_P["Passive"]
    end

    INET -->|"ISP 1 / ISP 2"| BranchPair

    %% ===== Levels 6-8: Branch Stack =====
    BranchPair --> LAN_BGP_BR["LAN / BGP to IRB(FRE_LAN)"] --> EX4400["EX4400-24X VC<br/>Stacked Pair"]
    EX4400 -->|"L3 Trunk"| EX4100["EX4100 VC<br/>L2 Access"]
    EX4100 -->|"L2 Access Ports"| USERS["User Devices<br/>L3 Subnet"]

    %% ===== WAN Tunnels =====
    HubPairs -.->|"WAN Tunnels"| BranchPair

    %% ===== Styling =====
    style TACACS_D fill:#e74c3c,color:#fff,stroke:#c0392b
    style TACACS_C fill:#e74c3c,color:#fff,stroke:#c0392b
    style USERS fill:#e74c3c,color:#fff,stroke:#c0392b
    style LAN_BGP_D fill:#27ae60,color:#fff,stroke:#1e8449
    style LAN_BGP_C fill:#27ae60,color:#fff,stroke:#1e8449
    style LAN_BGP_BR fill:#27ae60,color:#fff,stroke:#1e8449
```

## Legend

| Line Style | Meaning |
| - | - |
| Solid arrow | Physical link (LAN, WAN, trunk) |
| Dotted arrow | Logical WAN tunnel overlay (through public internet) |
| Bidirectional | State sync or route exchange between peers |

## Hardware Summary

| Level | Role | Hardware |
| - | - | - |
| 1 | Authentication | TACACS / RADIUS servers (L3 subnet) |
| 2 | DC Core | Cisco Nexus L3 switches |
| 3 | DC Hub Routers | Juniper SSR1300 pairs (Active / Inactive) |
| 4 | WAN | Public Internet (dual dedicated + dual ISP) |
| 5 | Branch Routers | Juniper SSR130 pairs (Active / Passive) |
| 6 | Branch Distribution | Juniper EX4400-24X Virtual Chassis |
| 7 | Branch Access | Juniper EX4100 Virtual Chassis (L2 only) |
| 8 | Endpoints | User devices (L3 subnet) |
