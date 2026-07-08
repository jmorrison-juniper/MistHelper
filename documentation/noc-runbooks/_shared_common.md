# NOC Alarm Runbook — Shared Appendix

This document holds the conventions, cross-cutting guidance, and shared reference material used by every alarm-specific runbook in this library. Each per-alarm document links back to sections here rather than duplicating content.

## 1. Runbook field standard

Every alarm runbook must include the following fields. Fields that don't apply to a given alarm should be marked `n/a` rather than omitted, so the layout stays scannable.

| Field | Purpose |
|---|---|
| **Alert Name** | Human-readable name used on dashboards and in ticket titles. |
| **Mist alarm key** | Lowercase, API-safe key. This is what you filter/search on via the Mist API and webhooks (e.g. `sw_alarm_chassis_mgmt_link_down`). |
| **Platform** | Device family/model this runbook targets (EX4400, SSR1300, etc.). If a Mist alarm applies to multiple platforms with different CLIs, produce one runbook per platform. |
| **Mist native severity** | The severity Mist ships the alarm at (`info` / `warn` / `critical`). |
| **NOC severity** | The severity we page on. When it differs from Mist native, this is an intentional **override** and must be documented in the runbook body. |
| **Group** | Mist alarm group: `infrastructure`, `marvis`, `security`, or `certificate_expiry`. |
| **Clear event key** | Paired `_clear` / `_up` event that closes the alarm, when one exists. Used for auto-resolution automation. |
| **Correlated alarms** | Other Mist alarm keys that commonly co-fire. Used for dedup rules and root-cause triage. |
| **Prerequisites** | Any configuration state required for the alarm to actually fire (e.g. port marked as "critical" in port profile). |
| **Description** | One-paragraph, operator-facing summary of what the alarm means. |
| **Impact / Required Information / Validation / Resolution / Closure Criteria** | Per the existing template. |

## 2. Severity override policy

Mist assigns each alarm a native severity based on its own operational model. Our NOC dashboard may need to raise or lower that severity to fit our on-call model.

- Any runbook whose **NOC severity** differs from **Mist native severity** must explain the override in the Description or a dedicated "Severity rationale" note.
- Overrides are set in the alarm template in Mist (**Organization → Alarm Templates**). They are not implicit — someone has to configure them.
- If two teams need different severities for the same alarm, split alarm templates by site group rather than by teaching operators to reinterpret severities.

## 3. Closure criteria and auto-resolution

Every runbook's Closure Criteria section must reference the paired `_clear` or `_up` event key when one exists. This gives us an unambiguous, machine-verifiable close signal and enables webhook-driven ticket auto-resolution.

- Manual close: operator confirms condition resolved (root cause documented).
- Automated close: our webhook consumer resolves the ticket on receipt of the paired clear event, provided no duplicate alarm has re-fired within a debounce window.
- Alarms without a paired clear event must document a manual verification step (usually a CLI check).

## 4. Correlated alarms and dedup

Many failures cascade. A physical uplink failure will typically fire:

`sw_critical_port_down` → `sw_alarm_chassis_mgmt_link_down` *(if mgmt rode that path)* → `switch_down` → `gw_bgp_neighbor_down` *(if BGP peered over that link)*

The runbook for each alarm should list its usual co-fires under **Correlated Alarms**. Triage rule of thumb: **the lowest-layer alarm is usually root cause**; higher-layer alarms are symptoms. Suppress the symptoms in the ticketing layer once the root-cause alarm is acknowledged, not in Mist.

## 5. Peer / port classification

For alarms whose severity depends on *which* port or *which* peer went down, the runbook must require the operator to classify the object before escalating:

- **Ports**: `access` / `uplink` / `IDF-MDF` / `server-edge` / `AP` / `VCP` / `LAG-member`
- **BGP peers**: `underlay-ISP` / `internal-RR` / `overlay-CE`
- **VPN peer paths**: `hub` / `spoke` / `mesh`

This classification determines blast radius and whether an alarm should escalate beyond the NOC.

## 6. Standard Mist GUI navigation

Paths as of the current Mist UI. If you find a path is stale, update the shared appendix — do not fork it into individual runbooks.

| Task | Navigation |
|---|---|
| Active alarms (org-wide) | Monitor → Alerts (Alarms) |
| Alarm templates (severity/routing) | Organization → Alarm Templates |
| Site alarm history | Monitor → Alerts → filter by site |
| Device health (switch) | Switches → *device* → Health / Insights |
| Device health (WAN edge / SSR / SRX) | WAN Edges → *device* → Health / Insights |
| Port state | Switches → *device* → Front Panel / Port Config |
| Client / connected device | Clients → Connected Devices |
| SVR peer paths | WAN Assurance → Peer Path Insights |
| WAN link health | WAN Assurance → WAN Links |
| Events (raw) | Monitor → Events |
| Audit logs | Organization → Audit Logs |

**Legacy path note:** older docs may reference `Routers → …` for SSR devices. Current UI unifies all gateways under `WAN Edges → …`.

## 7. Standard information to capture on every ticket

Independent of alarm type, capture on ticket creation:

- Site name, site ID
- Device hostname, serial number, MAC, Mist device ID
- Software version (Junos / SSR firmware)
- Alarm timestamp (UTC) and Mist alarm ID
- Whether the device is currently reachable in Mist (`connected` / `disconnected`)
- Any correlated alarms active in the last 15 minutes on the same device or site

## 8. Common Junos (EX / SRX) commands

Applicable to any Junos-based device (EX switches, SRX gateways). Use these as building blocks in per-alarm runbooks.

| Purpose | Command |
|---|---|
| System / model / uptime | `show system information` |
| Software version | `show version` |
| Chassis hardware / FRUs | `show chassis hardware` |
| Chassis alarms | `show chassis alarms` |
| Environment (temp / power / fans) | `show chassis environment` |
| Virtual Chassis state | `show virtual-chassis` |
| Virtual Chassis ports | `show virtual-chassis vc-port` |
| Interface summary | `show interfaces terse` |
| Interface detail | `show interfaces <interface> extensive` |
| Interface config | `show configuration interfaces <interface>` |
| Live interface counters | `monitor interface <interface>` |
| Optics DDM | `show interfaces diagnostics optics <interface>` |
| LLDP neighbors | `show lldp neighbors` |
| LACP status | `show lacp interfaces` |
| LACP stats | `show lacp statistics interfaces <interface>` |
| MAC table (per interface) | `show ethernet-switching table interface <interface>` |
| Routing table | `show route` |
| Log messages (interface-scoped) | `show log messages \| match <interface>` |
| Config diff (recent changes) | `show system commit` then `show configuration \| compare rollback N` |

## 9. Common SSR (Session Smart Router) PCLI commands

Applicable to SSR gateways. SSR PCLI differs from Junos — do not mix.

| Purpose | Command |
|---|---|
| System / model / uptime | `show system` |
| Conductor / cloud connectivity | `show system connected` |
| Device interfaces (physical) | `show device-interface` |
| Network interfaces (logical) | `show network-interface` |
| Routing table | `show route` |
| BGP summary | `show bgp summary` |
| BGP peer detail | `show bgp neighbor <peer-ip>` |
| BGP received prefixes | `show bgp neighbor <peer-ip> received-routes` |
| BGP advertised prefixes | `show bgp neighbor <peer-ip> advertised-routes` |
| SVR peer paths (overlay) | `show peers` |
| Active session count | `show sessions summary` |
| Events (scoped) | `show events filter type <type>` |
| Alarms | `show alarms` |
| Reachability (correct source) | `ping <target> source <local-transport-ip>` |
| Traceroute | `traceroute <target>` |

## 10. Standard escalation ladder

Applies to every runbook unless a specific runbook overrides.

1. **Tier 1 NOC** — validate alarm, run validation commands, classify port/peer, apply resolution steps.
2. **Tier 2 / Network Engineering** — hardware replacement, config restore, routing policy adjustments.
3. **Vendor (Juniper TAC / Mist Support)** — reproducible defects, RMA, licensing/entitlement issues.
4. **Change Advisory Board** — when resolution requires an out-of-window change.

Every runbook should note at which step (if earlier than Tier 2) the alarm can be self-cleared.

## 11. Cross-references from per-alarm runbooks

Per-alarm runbooks should reference this appendix by section number, not by copying content. Example:

> Severity override policy: see Shared Appendix §2.
> Commands: see Shared Appendix §8 (Junos) or §9 (SSR).
