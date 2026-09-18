# DCB, storage, and Contrail

Use this reference for data center bridging, storage traffic, FCoE, FIP snooping,
Fibre Channel gateway tasks, and Contrail networking.

Sources:

- Traffic Management on the QFX Series, QFX archive 2014-2015.
- Storage on the QFX Series, QFX archive 2014-2015.
- Contrail Feature Guide, Contrail 5.0.3.
- Contrail Networking Fabric Lifecycle Management Guide, Contrail 2011.
- Contrail Networking Monitoring and Troubleshooting Guide, Contrail 19.

## 1. DCB terms

| Term | Meaning in this skill | Source |
| - | - | - |
| PFC | Priority flow control. It pauses one priority without pausing the full link. | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| ETS | Enhanced transmission selection. It groups classes and assigns bandwidth. | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| DCBX | Data Center Bridging Capability Exchange. It advertises DCB settings to a peer. | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| Congestion notification profile | Junos object that enables PFC for selected IEEE 802.1 code points. | Traffic Management on the QFX Series, QFX archive 2014-2015. |
| FCoE | Fibre Channel over Ethernet. It carries storage traffic on Ethernet. | Storage on the QFX Series, QFX archive 2014-2015. |
| FIP snooping | A control that tracks FCoE Initialization Protocol state on a transit switch. | Storage on the QFX Series, QFX archive 2014-2015. |

Warning: do not change PFC, ETS, DCBX, or FCoE on a storage path without a tested
rollback. A wrong value can pause storage traffic or drop Fibre Channel sessions.

## 2. PFC and congestion notification workflow

Use this workflow for PFC:

1. Identify the lossless traffic class and IEEE 802.1 code point.
2. Read the current interface CoS configuration.
3. Read DCBX neighbor state.
4. Confirm the peer DCB configuration.
5. Apply the classifier and congestion notification profile together.
6. Verify the profile and DCBX state.

| Goal | Command | Source and release | Result |
| - | - | - | - |
| Classify FCoE with IEEE 802.1 code point 011. | At `[edit class-of-service]`, use `set classifiers ieee-802.1 fcoe-classifier forwarding-class fcoe loss-priority low code-points 011` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Maps FCoE frames to the lossless class. |
| Enable PFC for the FCoE code point. | `set class-of-service congestion-notification-profile fcoe-cnp input ieee-802.1 code-point 011 pfc` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Enables PFC on the selected priority. |
| Apply the classifier to an interface unit. | At `[edit class-of-service]`, use `set interfaces xe-0/0/31 unit 0 classifiers ieee-802.1 fcoe-classifier` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Classifies ingress FCoE traffic. |
| Apply the congestion notification profile. | At `[edit class-of-service]`, use `set interfaces xe-0/0/31 congestion-notification-profile fcoe-cnp` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Applies PFC behavior to the interface. |
| Read all congestion profiles. | `show class-of-service congestion-notification` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Shows the configured profile state. |
| Read one congestion profile. | `show class-of-service congestion-notification fcoe-cnp` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Shows one profile. |
| Read DCBX neighbor state. | `show dcbx neighbors` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Shows peer DCBX information. |

## 3. ETS and scheduler workflow

Use this workflow for ETS:

1. Define forwarding classes and class sets.
2. Define schedulers and scheduler maps.
3. Define traffic control profiles.
4. Attach class sets and profiles to the interfaces.
5. Verify class-of-service state before and after the change.

| Goal | Command | Source and release | Result |
| - | - | - | - |
| Create an FCoE scheduler. | At `[edit class-of-service]`, use `set schedulers fcoe-sched priority low transmit-rate 3g` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Sets the minimum transmit rate. |
| Set scheduler shaping. | At `[edit class-of-service]`, use `set schedulers fcoe-sched shaping-rate percent 100` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Allows the scheduler to use the shaped rate. |
| Map FCoE to a scheduler. | At `[edit class-of-service]`, use `set scheduler-maps fcoe-map forwarding-class fcoe scheduler fcoe-sched` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Links a forwarding class to a scheduler. |
| Create an FCoE forwarding class set. | At `[edit class-of-service]`, use `set forwarding-class-sets fcoe-pg class fcoe` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Groups the FCoE forwarding class. |
| Create a traffic control profile. | At `[edit class-of-service]`, use `set traffic-control-profiles fcoe-tcp scheduler-map fcoe-map guaranteed-rate 3g` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Sets the guaranteed bandwidth. |
| Attach the FCoE class set to an interface. | At `[edit class-of-service]`, use `set interfaces xe-0/0/31 forwarding-class-set fcoe-pg output-traffic-control-profile fcoe-tcp` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Applies ETS behavior to the output path. |
| Disable PFC autonegotiation on DCBX. | `set protocols dcbx interface interface-name priority-flow-control no-auto-negotiation` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Forces the local PFC state. |
| Disable ETS autonegotiation on DCBX. | `set protocols dcbx interface interface-name enhanced-transmission-selection no-auto-negotiation` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Prevents peer-driven ETS negotiation. |
| Disable the ETS recommendation TLV. | At `[edit protocols dcbx interface interface-name]`, use `set enhanced-transmission-selection no-recommendation-tlv` | Traffic Management on the QFX Series, QFX archive 2014-2015. | Sends only the ETS configuration TLV. |

## 4. FCoE and Fibre Channel workflow

Use this workflow for FCoE or native Fibre Channel:

1. Identify the FCoE VLAN and FIP mode.
2. Identify whether the switch is a transit switch or an FCoE-FC gateway.
3. Verify Fibre Channel interfaces and fabrics.
4. Verify FIP snooping state.
5. Change one storage path at a time.
6. Verify FLOGI, proxy, and FIP counters after the change.

| Goal | Command | Source and release | Result |
| - | - | - | - |
| Configure a VLAN unit as an F port. | `set interfaces vlan unit 100 family fibre-channel port-mode f-port` | Storage on the QFX Series, QFX archive 2014-2015. | Sets the FCoE VLAN to F-port mode. |
| Configure a Fibre Channel port range. | `set chassis fpc 0 pic 0 fibre-channel port-range 0 5` | Storage on the QFX Series, QFX archive 2014-2015. | Enables native Fibre Channel ports in the range. |
| Configure an NP port. | `set interfaces fc-0/0/0 unit 0 family fibre-channel port-mode np-port` | Storage on the QFX Series, QFX archive 2014-2015. | Sets a native Fibre Channel interface as an NP port. |
| Read Fibre Channel interfaces. | `show fibre-channel interfaces` | Storage on the QFX Series, QFX archive 2014-2015. | Lists native Fibre Channel interfaces and FCoE VLAN interfaces. |
| Read Fibre Channel fabrics. | `show fibre-channel fabric` | Storage on the QFX Series, QFX archive 2014-2015. | Lists interfaces that belong to each fabric. |
| Read proxy NP ports. | `show fibre-channel proxy np-port` | Storage on the QFX Series, QFX archive 2014-2015. | Shows proxy NP port state. |
| Read proxy NP port detail. | `show fibre-channel proxy np-port detail` | Storage on the QFX Series, QFX archive 2014-2015. | Shows sessions and max-login state. |
| Read proxy statistics. | `show fibre-channel proxy statistics` | Storage on the QFX Series, QFX archive 2014-2015. | Shows FLOGI, FDISC, and LOGO counters. |
| Read FIP snooping state. | `show fip snooping` | Storage on the QFX Series, QFX archive 2014-2015. | Shows FIP snooping VLAN state. |
| Read FIP snooping detail. | `show fip snooping detail` | Storage on the QFX Series, QFX archive 2014-2015. | Shows detailed FIP snooping sessions. |
| Read FIP snooping statistics. | `show fip snooping statistics` | Storage on the QFX Series, QFX archive 2014-2015. | Shows FIP counters. |
| Rebalance proxy load in dry-run mode. | `request fibre-channel proxy load-rebalance dry-run` | Storage on the QFX Series, QFX archive 2014-2015. | Shows the planned rebalance without applying it. |

Warning: do not change `port-mode`, FIP snooping, or Fibre Channel proxy state on
a production storage path without a storage rollback. The change can drop Fibre
Channel logins.

## 5. Contrail fabric and virtual network workflow

Contrail joins the physical IP fabric to virtual networks. The Contrail Feature
Guide states that Contrail creates and orchestrates virtual networks. The fabric
lifecycle guide describes underlay management and data center fabric automation.

Use this workflow for Contrail design questions:

1. Identify the Contrail release and orchestration mode.
2. Identify the physical fabric role, such as leaf, spine, or border leaf.
3. Identify the underlay AS pool and fabric subnet pool.
4. Identify the overlay AS pool and virtual network design.
5. Confirm whether routing occurs centrally or at the leaf.
6. Use Contrail UI or API documentation for the exact workflow action.
7. Verify the generated device configuration before deployment.

| Concept | What to verify | Source and release |
| - | - | - |
| Virtual network | Tenant subnet, routing mode, and policy attachment. | Contrail Feature Guide, Contrail 5.0.3. |
| vRouter | Compute host interface, vhost0 state, and virtual network attachment. | Contrail Feature Guide, Contrail 5.0.3. |
| Controller | Configuration, control, analytics, and database node health. | Contrail Monitoring and Troubleshooting Guide, Contrail 19. |
| Fabric object | Management subnet, fabric subnet, loopback subnet, underlay ASNs, and overlay ASN. | Contrail Fabric Lifecycle Management Guide, Contrail 2011. |
| Brownfield import | Current device configuration and generated plan difference. | Contrail Fabric Lifecycle Management Guide, Contrail 2011. |

The staged Contrail Fabric Lifecycle Management Guide describes UI workflows for
fabric creation, ZTP, device discovery, role assignment, and virtual network
creation. It does not provide a single Junos `set` command for those actions.
Use the product workflow or API guide for the exact release.

Warning: do not run a Contrail brownfield import until you save the current device
configuration. A wrong generated plan can replace a working fabric configuration.

## 6. Storage troubleshooting order

Use this read-only order:

1. Run `show interfaces terse` on each storage-facing Ethernet or Fibre Channel port.
2. Run `show class-of-service congestion-notification` for PFC state.
3. Run `show dcbx neighbors` for peer DCB state.
4. Run `show fip snooping detail` for transit FCoE state.
5. Run `show fibre-channel proxy np-port detail` for gateway state.
6. Run `show fibre-channel proxy statistics` for FLOGI or FDISC counters.
7. Run `show class-of-service shared-buffer` if lossless traffic drops.

Do not clear counters until the incident owner approves the data loss. Counter
clears remove evidence that helps find the failing segment.
