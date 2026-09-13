# Mist Ops Platform — A-Z Gap Matrix (Brand-Agnostic)

**Purpose**: Documents all operator-grade capabilities that competitors commonly provide but are NOT natively available inside the Juniper Mist AI Cloud portal UI. This matrix informed the functional requirements (FR-001 through FR-037) in the feature specification.

**Scope rule**: "Missing in Mist" means not a first-class feature inside the Mist AI Cloud portal. Some functions may exist elsewhere in the broader Juniper portfolio (e.g., Security Director for SRX policy) or via third-party tools, but they are not part of the Mist portal itself.

**Source**: Compiled from public vendor documentation, analyst reviews, and competitive research (session 2026-03-05).

---

## A) Historical "Time-Travel" Views for Devices/Clients/Paths

**How it works**: Lets operators rewind the network to a given timestamp to see correlated health, topology, and KPIs. UI provides 360-style pages, historical charts, and hop-by-hop context (e.g., "what did that access switch port look like yesterday at 14:05?").

**Operator value**: Faster root cause — reconstructs incidents precisely when they occurred; fewer blind spots than static logs; better post-mortems.

**Mist status**: Mist has historical SLEs/insights, but no Assurance-style timeline-playback UX to step through a past event at the port/device/path level within the Mist UI.

**Maps to**: FR-013 (Historical time-travel query interface), US-1

---

## B) Scheduled Policy/Config Deployments (Delayed Commits)

**How it works**: UI offers one-time or recurring schedules to deploy policies/updates/backups during maintenance windows; shows history and preview before deployment. Admins time policy updates, database/VDB updates, backups, and other jobs for specific windows.

**Operator value**: Enforces change windows, reduces after-hours toil, and creates repeatable runbooks for compliance.

**Mist status**: Mist UI does not provide a native "deploy at 02:00" scheduler for configuration changes.

**Maps to**: FR-005 (Scheduling deployments), US-3

---

## C) Configuration Versioning, Diff & Rollback

**How it works**: Stores every config/policy revision; shows who changed what; supports compare two versions, view install logs, and revert to a known-good snapshot. Built-in revision repository with detailed diff and full revert capability.

**Operator value**: Provides instant safety net; speeds blame-free rollback when a change misbehaves; simplifies audits.

**Mist status**: Mist UI does not expose a general "compare & revert" repository for device/policy configs.

**Maps to**: FR-002, FR-003, FR-004 (Revision storage, diff, install-from-revision), US-2

---

## D) Auto-Rollback on Connectivity Loss (Safety Nets)

**How it works**: After a config push, if the device loses controller connectivity, it reverts to the last known good config. The system disables auto-commit until an operator reviews.

**Operator value**: Saves remote hands, prevents site outages from persisting; promotes safer day-2 operations.

**Mist status**: Not built into the Mist UI push workflow.

**Maps to**: FR-007 (Auto-revert on post-check failure), US-3

---

## E) Change Audit Trail with Old-to-New Field Values

**How it works**: A single change log page lists every config action across the estate with timestamp, actor, scope, and explicit old/new values; filterable and exportable.

**Operator value**: Speeds forensics ("what exactly changed?"), supports peer accountability, and simplifies audit evidence for SOX/PCI/SOC2.

**Mist status**: Mist surfaces histories/alerts, but doesn't provide a unified old-to-new diff log across all settings.

**Maps to**: FR-008, FR-009 (Audit trail with field-level diffs, exportable reports), US-4

---

## F) Firmware Orchestration (Schedule, Reschedule, Cancel, Rollback)

**How it works**: Centralized page to select networks/devices, pin target versions, schedule upgrades, reschedule/cancel, and roll back to prior version within a safe window.

**Operator value**: Reduces risk of mass upgrades, provides quick exit if a regression appears, and standardizes fleet hygiene.

**Mist status**: Mist UI lacks this end-to-end scheduling + rollback workflow depth.

**Maps to**: FR-005, FR-010 (Scheduling, phased rollouts), US-5

---

## G) Install from Historical Build (Targeted Rollback)

**How it works**: From installation history, select a prior successful build and redeploy that exact version to specific gateways — without restoring the entire manager database. Enables surgical rollback at the edge while preserving ongoing work in the manager.

**Operator value**: Limits blast radius of a bad change; ideal for controlled reversion under pressure.

**Mist status**: Not natively present in Mist UI.

**Maps to**: FR-004 (Install from revision), US-2

---

## H) Pre-/Post-Change Validation & Health Gates

**How it works**: When scheduling an OS or policy rollout, the system automatically performs pre-checks (image compatibility, dependency validation) and post-checks (verifying services return healthy), blocking or rolling back on failure.

**Operator value**: Reduces change-failure rate; turns upgrades into safe, repeatable runbooks for CAB.

**Mist status**: Not a first-class Mist UI pattern for wired/wireless upgrades with automated gates.

**Maps to**: FR-006, FR-007, FR-023 (Pre-checks, post-checks, risk assessment), US-3

---

## I) Policy Lifecycle Management (Recertification & Expiry)

**How it works**: Change platform tracks policy rules with owners, expiry dates, and recertification workflows. Stale exceptions are auto-flagged and can be set to auto-expire unless renewed.

**Operator value**: Shrinks policy sprawl, enforces least-privilege, and improves audit posture with provable review cadence.

**Mist status**: Not native to Mist UI.

**Maps to**: FR-024 (Policy lifecycle tracking), US-6

---

## J) Administrative Domains (Per-Tenant / Per-Region Isolation)

**How it works**: Creates isolated domains for device groups, policies, and change histories. Teams operate in their domain without impacting others; central admins can still govern globally.

**Operator value**: Enables federated ops at scale (MSP, global enterprise) with blast-radius reduction for changes.

**Mist status**: Mist UI doesn't expose domain-style segmentation for policy/config repositories.

**Maps to**: FR-025 (Access control scoped to MSP/org/site/device-group)

---

## K) End-to-End Path Analysis & "What-If" Simulation

**How it works**: Before approving a change, the system computes intended traffic paths, shows devices in the way, predicts policy impacts, and simulates risk violations — all pre-deploy. During investigation, operators view past path state correlated to the incident time window.

**Operator value**: Prevents outages by surfacing route/policy conflicts early; accelerates approvals with evidence.

**Mist status**: Not built into Mist UI; requires external design/simulation tooling.

**Maps to**: FR-026 (Network path tracing)

---

## L) Change Windows, Blackouts & Governance Hooks

**How it works**: Native schedulers run jobs only in defined windows; deployment tasks keep history/preview records for audit. Admins couple with backups and definition updates on timers.

**Operator value**: Enforces CAB mandates; reduces after-hours toil; creates a paper trail that satisfies auditors.

**Mist status**: No built-in Mist UI scheduler/governance to this depth.

**Maps to**: FR-005 (Scheduling), US-3

---

## M) Application-Centric Change Modeling

**How it works**: Changes are authored at the application level (app components, flows, dependencies), with the platform translating intent into device-level policies and validating the post-change state.

**Operator value**: Aligns network/security changes with business services; reduces ambiguity and accelerates approvals.

**Mist status**: Not native in Mist UI.

**Maps to**: FR-027 (Application-centric change modeling)

---

## N) Continuous Compliance & Drift Control

**How it works**: The platform continuously compares intended state vs. actual, flags config drift or policy violations, and offers auto-remediation steps or one-click fixes via workflows.

**Operator value**: Turns audits into ongoing hygiene, preventing last-minute findings; reduces MTTR for misconfigurations.

**Mist status**: Not delivered as a built-in Mist UI capability.

**Maps to**: FR-011, FR-012 (Drift detection and remediation), US-6

---

## O) Per-Change Impact Preview & Targeted Deploy (Transactional Edits)

**How it works**: Before pushing, operators see a diff of what will change (rules/objects), which devices are affected, and can limit deployment to a safe subset. Multi-device transactions either commit to all targets or roll back entirely.

**Operator value**: Prevents surprises; narrows blast radius; provides clear approval artifacts.

**Mist status**: Mist UI doesn't provide a rich pre-deploy diff + selective target preview pane.

**Maps to**: FR-028 (Atomic multi-device transactions)

---

## P) Two-Stage Commit (Build, Review, Commit)

**How it works**: With auto-commit disabled, admins stage configs in cloud, review diffs and impact, then commit to devices later. The system supports an auto-commit toggle per group or site scope.

**Operator value**: Enables peer review and reduces accidents; aligns with change control processes.

**Mist status**: Not a native Mist UI pattern.

**Maps to**: FR-033 (Maker-checker approval workflows)

---

## Q) Transactional Device Editing with Checkpoint Timer

**How it works**: Operator creates a checkpoint, applies changes, and must confirm before a timer elapses. If not confirmed, the device auto-reverts to the checkpoint — eliminating "dead-box" risk.

**Operator value**: Enables confident remote work in dark closets/branches with no smart hands.

**Mist status**: Not a Mist UI feature.

**Maps to**: FR-007 (Auto-revert mechanisms)

---

## R) Image Governance & Golden-Image Compliance

**How it works**: A controller maintains authoritative golden software images for device families, runs pre-checks for compatibility, manages staged downloads, and performs intent-based image compliance (detects drift from the approved image set and queues remediation). Records pre/post checks and upgrade outcomes for audit.

**Operator value**: Reduces upgrade failure risk, enforces standardization across large fleets, and gives CABs a repeatable audit trail for image hygiene.

**Mist status**: Not a native Mist UI workflow for fleet-wide golden-image governance with embedded pre/post validation gates.

**Maps to**: FR-029 (Golden image repository with approval workflows)

---

## S) Application Discovery & Flow Mapping

**How it works**: The platform discovers business applications, maps their network connectivity (sources, destinations, services), and ties policy changes to app context so approvals and validations are expressed in application terms — not just IP/port. Post-change, verifies that the application's declared flows are still reachable.

**Operator value**: Speeds approvals ("this is for Order-Processing app, flow X->Y over TCP/443"), avoids guesswork, and lowers the chance of breaking upstream/downstream dependencies.

**Mist status**: Not provided in Mist UI as application-centric modeling and validation.

**Maps to**: FR-030 (Application discovery and inventory)

---

## T) Pre-Approved Change Templates with Guardrails

**How it works**: Teams build standard change templates (e.g., "branch exception," "decom object"), each with workflow steps, required evidence, risk checks, and approvers. Operators submit against templates; the system auto-populates design details, runs policy/risk validations, and either auto-implements or routes for approval.

**Operator value**: Shrinks mean time to implement without bypassing governance; reduces variability and human error by codifying best practice.

**Mist status**: Not a Mist UI construct — no native template-driven, guardrailed workflows for network/security changes.

**Maps to**: FR-031 (Reusable parameterized change templates)

---

## U) Auto-Generated Audit Packs & Installer Evidence

**How it works**: For each change or policy install, the manager compiles a change report (who/what/when), diffs, install logs, and relevant artifacts (success/fail, targets, timestamps) and makes them exportable for auditors or ticket closure.

**Operator value**: Turns audit prep into a one-click export, proving due diligence and accelerating SOX/PCI/SOC2 responses.

**Mist status**: Mist exposes histories/telemetry but does not provide a dedicated, packaged audit dossier per change with installer logs and formalized reports.

**Maps to**: FR-032 (Compliance audit evidence packages)

---

## V) Segregation of Duties & Role-Constrained Approvals

**How it works**: Workflow engines enforce role separation (e.g., designer != approver != implementer), multi-stage approvals, and risk-based escalation before deployment. Scheduled tasks honor admin roles and histories.

**Operator value**: Meets compliance mandates and reduces insider risk while keeping velocity via structured paths and automation.

**Mist status**: Mist UI doesn't include an opinionated SoD workflow with role-based approval chains tied to deployment.

**Maps to**: FR-033 (Maker-checker workflows)

---

## W) Auto-Backup & Back-Out Hooks Tied to Change Windows

**How it works**: Prior to a scheduled deployment, the platform triggers automatic backups (manager and/or device configs), deploys within the approved window, and registers an explicit back-out plan (e.g., restore from backup or install a prior revision) if health gates fail.

**Operator value**: Provides rapid escape hatches during maintenance, shortens MTTR, and satisfies CAB expectations for documented back-out steps.

**Mist status**: No native Mist scheduler that couples backup + deployment + back-out linkage within a single, governed workflow.

**Maps to**: FR-034 (Automated backup on schedule and before changes)

---

## X) Phased / Ring-Based Rollouts (Canary, Waves)

**How it works**: Rollouts are organized into rings/waves (pilot -> regional -> global). Admins schedule or queue batches of networks/devices per wave and promote only after health checks pass. Reschedule/cancel controls are built in, and rollback is available to the previous version within a window.

**Operator value**: Limits blast radius, creates predictable progressions, and gives a structured path to pause or roll back between waves.

**Mist status**: Mist UI lacks a first-class ring/wave orchestration for changes/upgrades with built-in wave promotion logic.

**Maps to**: FR-010 (Multi-wave phased rollouts), US-5

---

## Y) Change-Impact Correlation (Issues <-> Changes)

**How it works**: The assurance plane correlates user/device issues on a timeline with recent configuration/policy changes and old-to-new diffs, so operators can quickly test the hypothesis that "the change caused the problem."

**Operator value**: Cuts investigation time by linking symptoms directly to probable change events, improving post-incident analysis and accountability.

**Mist status**: Mist does not offer a single pane that fuses assurance time-travel with field-level change diffs across the org.

**Maps to**: FR-035 (Incident-change correlation)

---

## Z) "Dry-Run" Verification & Post-Implementation Validation

**How it works**: Before implementing, the system runs a dry-run to validate the change against policy, topology, and risk rules. After implementing, it verifies that the requested access or behavior is now in effect and flags unauthorized requests or mismatches.

**Operator value**: Prevents policy violations pre-deploy and proves success post-deploy (closing the loop), reducing rework and audit findings.

**Mist status**: Mist UI does not provide a built-in dry-run engine with automatic post-change verification against the original request intent.

**Maps to**: FR-036 (Dry-run mode for configuration pushes), FR-023 (Risk assessment)

---

## Operator Narratives (How These Features Work Together)

1. **Reconstructing an outage**: An engineer rewinds the assurance timeline to 14:05 yesterday and sees the client path degraded on an access port, with historical KPIs proving a brownout; they attach the screenshot/history to the incident record. *(Categories A, Y)*

2. **Safer after-hours change**: A firewall policy change is scheduled for 01:30, with a pre-deploy preview and automatic backup. If metrics spike, the team installs from the last good revision on only the affected branch to stabilize quickly. *(Categories B, G, H, W)*

3. **Remote closet edits without fear**: An engineer enables checkpoint with a 10-minute confirm window on a distant switch. If they lose SSH, the switch reverts automatically. *(Categories D, Q)*

4. **Audit response in minutes**: Compliance asks "who changed guest VLAN ACLs last quarter?" The team flips to the org change log, filters by label, exports the old-to-new records, and closes the audit. *(Categories E, U)*

5. **Pre-change risk check**: A new exception is requested. The change tool simulates path impact and flags a conflict with segmentation policy. The designer adjusts the rule before any outage can occur. *(Categories H, K, Z)*

---

## Competitive Landscape (Vendors Evaluated)

The following competitive categories were evaluated when building this gap matrix. Vendor names are listed for traceability; the capabilities above are described brand-agnostically.

### Enterprise WLAN + Cloud-Managed Networking
- Cisco Meraki (cloud-managed full stack)
- HPE Aruba / Aruba Central (wireless, analytics, cloud management)
- Ruckus Wireless / CommScope (hardware-driven performance)
- Extreme Networks (AI/ML, cloud-managed edge)
- Huawei WLAN (enterprise WLAN)
- Arista Cognitive Campus (switches + campus WLAN)

### AI-Driven Network Automation & AIOps
- NetBrain (AI automation, troubleshooting, observability)
- LogicMonitor (observability, network monitoring, device configs)
- Auvik (cloud network monitoring, automated mapping)
- Datadog (full-stack monitoring, network visibility)
- Darktrace (AI detection, network behavioral analytics)

### Location & Indoor Visibility
- Cisco Spaces (indoor location, occupancy analytics)
- Sewio RTLS (UWB-based real-time location tracking)
- Zebra MotionWorks (enterprise asset tracking)
- Ubisense Dimension4 (enterprise RTLS, spatial intelligence)

### SD-WAN / WAN Edge
- Cisco Catalyst SD-WAN (Viptela / DNA SD-WAN)
- Cato Networks (secure cloud-native SD-WAN / SASE)
- VMware / Broadcom SD-WAN (VeloCloud)
- Zscaler (SASE, overlaps with WAN Assurance)
- Fortinet FortiGate / FortiSASE / FortiAP / FortiSwitch

### On-Prem Campus Management / SD-x
- Cisco DNA Center / Catalyst Center (on-prem appliance for campus fabric/assurance)
- Aruba AirWave (on-prem WLAN/LAN management)
- Aruba SD-Branch / EdgeConnect (unified wired/wireless/WAN)
- Extreme Networks (ExtremeCloud IQ + Site Engine on-prem)

### Firewall Management (Vendor-Native)
- Palo Alto Networks Panorama (centralized NGFW management)
- Fortinet FortiManager + FortiAnalyzer (policy orchestration, analytics)
- Cisco Secure Firewall Management Center (FMC) (central console for FTD)
- Check Point SmartConsole / Security Management (unified policy/threat mgmt)
- Juniper Security Director (SRX policy management — separate from Mist)
- SonicWall Global Management System (GMS) / NSM
- Barracuda CloudGen Firewall Control Center
- Sophos Central (cloud-based unified security management)
- WatchGuard WSM (centralized Firebox management)

### Multi-Vendor Firewall Policy Orchestration
- Tufin Orchestration Suite (multi-vendor automation/compliance)
- AlgoSec (connectivity mapping, risk analysis, automated optimization)
- FireMon (real-time policy analysis, change control, compliance)
- Skybox Security (firewall assurance, vulnerability exposure analysis)
- ManageEngine Firewall Analyzer (multi-vendor reporting, logs, compliance)

### Enterprise Wired LAN
- Cisco Catalyst Switching
- HPE Aruba CX Switches
- Fortinet FortiSwitch
- Huawei Campus LAN

---

## Net New Value Summary

These capabilities collectively provide, over Mist's portal:

1. **Fewer war-rooms** via timeline playback and app telemetry correlation (investigation speedup)
2. **Change safety** through auto-rollback, checkpoint timers, staged commit, and targeted install-from-revision (fewer lockouts, faster reversions)
3. **Operational discipline** with in-product scheduling, previews, and change logs with old-to-new values (clean CAB approvals and audits)
4. **Throughput + compliance** via workflowed, simulated, zero-touch changes (more changes, less risk)
5. **Fleet standardization** via golden image governance, policy lifecycle, and drift detection (continuous compliance)
