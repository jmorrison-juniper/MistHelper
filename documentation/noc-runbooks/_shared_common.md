# NOC Alarm Runbook — Shared Appendix

This document holds the conventions, cross-cutting guidance, and shared reference material used by every alarm-specific runbook in this library. Each per-alarm document links back to sections here rather than duplicating content.

## 0. Target topology (retail branch)

Every runbook in this library assumes the **retail branch reference topology**:

| Layer | Hardware | Notes |
|---|---|---|
| WAN gateway | **1 × Juniper SSR130** | Single node — no local HA peer. BGP + SVR overlay to the DC hub SSR1300 pair (Dallas / Chicago). A total gateway failure isolates the branch. |
| Access switching | **2 × Juniper EX4100** in a Virtual Chassis | 2-member VC (master + backup). No dedicated distribution layer at the branch. |
| Downstream | Mist APs, POS terminals, IP phones, back-office endpoints | PoE from EX4100. |
| WAN transport | Dual ISP (typically) | Underlay to the ISPs is normally static-routed; BGP is the *overlay* to hub. |

Implications that shape the runbooks:

- **Single SSR130.** No gateway HA at the branch — any gateway-side outage is site-impacting. Overlay BGP peers point at the DC hub SSR1300 pair; there is no branch-local BGP peer.
- **2-member EX4100 VC.** Only master + backup roles (no linecards). Losing the sole VCP path splits the VC into two isolated single-member fragments — split risk is immediate, not gradual.
- **No dedicated OOB in most branches.** If your branch has no separate OOB management network, treat `sw_alarm_chassis_mgmt_link_down` as `warn` rather than the library-default `critical` (see §2).
- **DC hub SSR1300 pair is out of scope** for this library — a separate hub-side runbook set covers Dallas/Chicago SSR1300 alarms.

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

Mist assigns each alarm a native severity in the alarm definitions catalog (`GET /api/v1/const/alarm_defs`). This severity is **fixed per alarm key** and is **not configurable** — Mist alarm templates (`POST/PUT /orgs/{org_id}/alarmtemplates`) only control per-alarm `enabled` state and email `delivery`. There is no `severity` field on an alarm-template rule.

Where severity overrides actually live:

- **Downstream paging / ticketing layer** (webhook consumer, PagerDuty, ServiceNow, etc.) — this is where we translate a Mist-native `warn` into a NOC-paged `critical`, or suppress an `info` alarm entirely.
- Overrides are keyed off the alarm-payload `type` (Mist alarm key), optionally combined with `group`, site tags, or device role.

Rules for this runbook library:

- Any runbook whose **NOC severity** differs from **Mist native severity** must explain the override in the Description or a dedicated "Severity rationale" note.
- The override lives in the paging/ticketing layer, not in Mist. Document *which* layer owns the mapping so operators know where to change it.
- If two teams need different severities for the same alarm, split the mapping by site tag or device role in the downstream layer — do not teach operators to reinterpret severities.

## 3. Closure criteria and auto-resolution

Every runbook's Closure Criteria section must reference the paired `_clear` or `_up` event key when one exists. This gives us an unambiguous, machine-verifiable close signal and enables webhook-driven ticket auto-resolution.

- Manual close: operator confirms condition resolved (root cause documented).
- Automated close: our webhook consumer resolves the ticket on receipt of the paired clear event, provided no duplicate alarm has re-fired within a debounce window.
- Alarms without a paired clear event must document a manual verification step (usually a CLI check).

## 4. Correlated alarms and dedup

Many failures cascade. A typical retail-branch example — the EX4100 VC uplink to the SSR130 fails:

`sw_critical_port_down` (EX4100 uplink) → `sw_alarm_chassis_mgmt_link_down` *(if branch mgmt rode that path)* → `switch_down` *(if the affected member also loses its keepalive)* → `gw_bgp_neighbor_down` *(if the SSR130's LAN-side BGP peer sat behind that uplink)*

The runbook for each alarm should list its usual co-fires under **Correlated Alarms**. Triage rule of thumb: **the lowest-layer alarm is usually root cause**; higher-layer alarms are symptoms. Suppress the symptoms in the ticketing layer once the root-cause alarm is acknowledged, not in Mist.

## 5. Standard information to capture on every ticket

Independent of alarm type, capture on ticket creation:

- Site name, site ID
- Device hostname, serial number, MAC, Mist device ID
- Software version (Junos / SSR firmware)
- Alarm timestamp (UTC) and Mist alarm ID
- Whether the device is currently reachable in Mist (`connected` / `disconnected`)
- Any correlated alarms active in the last 15 minutes on the same device or site

## 6. Common Junos (EX / SRX) commands

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

## 7. Common SSR (Session Smart Router) PCLI commands

Applicable to SSR gateways. SSR PCLI differs from Junos — do not mix.

Every command below is verified against the Session Smart Networking command line
reference at <https://docs.128technology.com/docs/cli_reference>.

Run `python scripts/fetch_ssr_docs.py` to build a local copy under
`documentation/references/ssr/`. That directory is not committed, because it holds
verbatim vendor text.

For the reason to run each command, the healthy output, and the failure signature,
see [SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md).

| Purpose | Command |
|---|---|
| System state, role, version, uptime, alarm count | `show system` |
| Mist cloud link | `show mist` |
| Link between the nodes of one router | `show system connectivity` |
| Process state | `show system processes` |
| Device interfaces (physical) | `show device-interface` |
| Network interfaces (logical) | `show network-interface` |
| Address resolution table | `show arp` |
| Routes that the router learned | `show rib` |
| Forwarding decision for a prefix | `show fib <ip-prefix>` |
| BGP summary | `show bgp summary` |
| BGP peer detail | `show bgp neighbors <peer-ip>` |
| BGP received prefixes | `show bgp neighbors <peer-ip> received-routes` |
| BGP advertised prefixes | `show bgp neighbors <peer-ip> advertised-routes` |
| SVR peer paths (overlay) | `show peers` |
| SVR peer path quality | `show peers detail` |
| Service paths for applications | `show service-path` |
| Active sessions (always limit the rows) | `show sessions rows 20` |
| Largest sessions by bandwidth | `show sessions top bandwidth` |
| Events (scoped by type) | `show events type <type>` |
| Events (scoped by time) | `show events from 1d` |
| Alarms | `show alarms` |
| Reachability over a chosen path | `ping egress-interface <network-interface> <target>` |
| Reachability as a user (policy plane) | `service-ping service-name <service> tenant <tenant> source-ip <address> <target>` |
| Traceroute | `traceroute <target>` |
| Support archive | `save tech-support-info` |

Warning: six commands in the earlier version of this table do not exist in any SSR
release. Do not reintroduce them. `show system connected`, `show route`,
`show bgp neighbor` in the singular form, `show sessions summary`,
`show events filter type`, and `ping <target> source <ip>` all fail at the prompt.
[SSR_CONSOLE_HEALTH_CHECK.md](SSR_CONSOLE_HEALTH_CHECK.md) § 11 states the working
replacement for each one.

Warning: `ping` bypasses the policy plane, and `service-ping` does not. A
successful `ping` proves the transport only. Run both commands before you report
that a gateway is healthy.

## 8. Standard escalation ladder

Applies to every runbook unless a specific runbook overrides.

1. **Tier 1 NOC** — validate alarm, run validation commands, classify port/peer, apply resolution steps.
2. **Tier 2 / Network Engineering** — hardware replacement, config restore, routing policy adjustments.
3. **Vendor (Juniper TAC / Mist Support)** — reproducible defects, RMA, licensing/entitlement issues.
4. **Change Advisory Board** — when resolution requires an out-of-window change.

Every runbook should note at which step (if earlier than Tier 2) the alarm can be self-cleared.

## 9. Cross-references from per-alarm runbooks

Per-alarm runbooks should reference this appendix by section number, not by copying content. Example:

> Severity override policy: see Shared Appendix §2.
> Commands: see Shared Appendix §6 (Junos) or §7 (SSR).
