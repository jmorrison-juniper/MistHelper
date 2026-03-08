# Feature Specification: Mist Ops Platform

**Feature Branch**: `001-mist-ops-platform`  
**Created**: 2026-03-05  
**Status**: Draft  
**Input**: User description: "Build a 3-layer containerized microservice platform that implements operator-grade features missing from Juniper Mist (A-Z gap matrix), using free/OSS Kubernetes-ready components (PostgreSQL, Redis, MinIO, FastAPI, Celery, KEDA, etc.), integrated with the Mist API. The platform provides time-travel assurance, config versioning/diff/rollback, scheduled changes, auto-rollback safety nets, change audit with old-to-new diffs, firmware orchestration, install-from-revision, multi-vendor change workflows with risk simulation, pre/post-change validation gates, policy lifecycle management, continuous compliance/drift detection, phased rollouts, and application-centric change modeling."

## Clarifications

### Session 2026-03-05

- Q: Will this platform serve a single Mist organization, or must it support multiple Mist organizations simultaneously? → A: Must support the Mist MSP (Managed Service Provider) level, which controls many organizations. Hierarchy: MSP → Organizations → Sites → Devices.
- Q: Should the MVP include all 26 A-Z gap categories, or limit to the current 6 user stories and defer the rest? → A: Expand MVP to include all 26 categories (full scope).
- Q: How should the platform deliver operational notifications and alerts (deployment failures, drift detection, post-check failures, approval requests)? → A: Both email (SMTP) and webhooks (Slack, Teams, PagerDuty, generic HTTP), operator-configurable per alert type.
- Q: What is the baseline scale the platform must handle (number of orgs, sites, devices)? → A: 100 organizations, 1,000 sites per org, 10 devices per site = 1,000,000 devices baseline. With 5x headroom (SC-008) = 5,000,000 devices.
- Q: Where should user identity and permissions originate for RBAC and maker-checker workflows? → A: Use API tokens, interactive login (email/password + 2FA), or Mist SSO integration to authenticate. Retrieve permissions and roles directly from the Mist API (GET /api/v1/self privileges). No separate RBAC layer — the platform inherits the user's Mist-assigned roles and scopes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Historical State Investigation ("Time-Travel") (Priority: P1)

A NOC engineer receives a complaint that a branch office experienced intermittent connectivity yesterday afternoon. They open the platform's investigation view, select the site/device, and rewind to a specific timestamp. The platform displays the device's configuration state, port up/down status, connected clients, and relevant health metrics at that exact point in time. The engineer compares the historical snapshot against the current state and identifies that a port flapped during the outage window without any corresponding change record — confirming a hardware issue rather than a misconfiguration.

**Why this priority**: Investigation and root-cause analysis are the most frequently requested operator capabilities and the #1 gap identified versus competitor assurance platforms. Without this, every other feature (rollback, audit) loses context.

**Independent Test**: Can be fully tested by ingesting historical snapshots from the Mist API, storing them, then querying a past timestamp and verifying the returned state matches what was captured. Delivers immediate value as a standalone "network forensics" tool.

**Acceptance Scenarios**:

1. **Given** the platform has been syncing device/port/client state from the Mist API for at least 24 hours, **When** an operator selects a device and a past timestamp, **Then** the platform returns the device's configuration, port states, connected clients, and health metrics as they were at that moment.
2. **Given** a device experienced a port flap at 14:05 yesterday, **When** the operator rewinds to 14:04 and then to 14:06, **Then** the platform shows the port as "up" at 14:04 and "down" at 14:06, with the transition event logged.
3. **Given** the operator queries a timestamp older than the configured retention window, **When** the query executes, **Then** the platform returns a clear message indicating the data has been aged out, along with the oldest available timestamp.

---

### User Story 2 — Configuration Versioning, Diff & Rollback (Priority: P1)

A network administrator pushes a WLAN policy change via the Mist portal. The platform automatically captures the device/site/org configuration before and after the change. Later, a user reports degraded Wi-Fi. The administrator opens the platform, views the configuration revision history for the affected site, selects two revisions, and sees a field-level diff (old value → new value). Confirming the recent change caused the issue, the administrator selects "Install from Revision" to redeploy the prior known-good configuration snapshot to selected devices via the Mist API.

**Why this priority**: Config versioning and rollback are the second-most-cited missing capability across competitor platforms. This directly enables the "install from revision" and "targeted rollback" features from the gap matrix.

**Independent Test**: Can be tested by making a configuration change via the Mist API, verifying the platform captures both the before and after states, displaying a correct diff, and then restoring the prior state via API push. Value: instant "undo button" for any Mist change.

**Acceptance Scenarios**:

1. **Given** the platform is syncing org/site/device configurations, **When** a configuration change occurs in Mist, **Then** the platform stores a new revision with a timestamp, the actor (if available from audit logs), and a hash for dedup.
2. **Given** at least two configuration revisions exist for a site, **When** the operator selects two revisions to compare, **Then** the platform displays a field-level diff showing exactly which settings changed, with old and new values.
3. **Given** the operator selects a prior revision and clicks "Install from Revision," **When** the operation executes, **Then** the platform pushes the historical configuration to the selected devices via the Mist API and records the restore as a new revision entry.
4. **Given** the "Install from Revision" push fails (e.g., API error), **When** the failure occurs, **Then** the platform logs the error, notifies the operator, and does not mark the revision as "installed."

---

### User Story 3 — Scheduled Changes & Maintenance Windows (Priority: P2)

A change manager needs to deploy a firewall policy update during a 2 AM maintenance window. They author the change in the platform during business hours, specify the target devices and the deployment time, and submit it. At 2 AM, the platform automatically pushes the change via the Mist API, runs pre-checks (connectivity, version compatibility) before deploying and post-checks (service health, reachability) afterward. If post-checks fail, the platform auto-reverts to the pre-change state and alerts the on-call engineer.

**Why this priority**: Scheduled deployments with automated safety gates are a core operational workflow for regulated and large enterprises. This directly addresses the "scheduled tasks," "pre/post-change validation gates," and "auto-rollback on failure" gaps.

**Independent Test**: Can be tested by scheduling a future configuration change, verifying the platform executes it at the correct time, runs pre/post checks, and (in a failure simulation) rolls back. Value: eliminates after-hours manual toil and reduces change failure rate.

**Acceptance Scenarios**:

1. **Given** the operator authors a configuration change and sets a deployment time in the future, **When** the scheduled time arrives, **Then** the platform executes the change automatically.
2. **Given** a scheduled change has pre-checks configured, **When** the deployment time arrives but a pre-check fails (e.g., target device unreachable), **Then** the platform aborts the deployment, logs the failure reason, and notifies the operator.
3. **Given** a scheduled change deploys successfully but a post-check fails (e.g., client connectivity drops below threshold), **When** the failure is detected, **Then** the platform automatically reverts to the pre-change configuration and sends an alert.
4. **Given** the operator wants to cancel or reschedule a pending change, **When** they modify the schedule before the deployment time, **Then** the platform updates the job accordingly.

---

### User Story 4 — Change Audit Trail with Field-Level Diffs (Priority: P2)

An auditor requests evidence of all configuration changes made to WLAN policies in the last quarter. The operator opens the platform's audit view, filters by entity type ("WLAN"), date range, and optionally by actor. The platform displays a chronological list of changes, each showing timestamp, actor, scope, and explicit old → new field values. The operator exports this as a report for the auditor.

**Why this priority**: Field-level change audit trails with old/new values are table-stakes for SOX/PCI/SOC2 compliance and were identified as missing in the Mist portal. This capability underpins accountability and audit readiness.

**Independent Test**: Can be tested by making several configuration changes, then querying the audit view and verifying every change is captured with correct old/new values and timestamps. Value: standalone compliance evidence tool.

**Acceptance Scenarios**:

1. **Given** the platform has been tracking configuration changes, **When** an operator filters the audit log by entity type, date range, and actor, **Then** the platform returns matching change records with timestamp, actor, scope, and old → new field diffs.
2. **Given** the operator selects an export format (CSV or structured report), **When** they export the filtered audit log, **Then** the platform generates a downloadable file containing the selected records with all diff details.
3. **Given** a change was made by an unknown actor (e.g., API key without attribution), **When** the audit log displays it, **Then** the actor field shows the API token identifier rather than leaving it blank.

---

### User Story 5 — Phased / Ring-Based Rollouts (Priority: P3)

A firmware upgrade needs to be deployed to 200 branch APs across 40 sites. The operator creates a rollout plan with three waves: Wave 1 (5 pilot sites), Wave 2 (15 regional sites), Wave 3 (remaining 20 sites). The platform executes Wave 1, waits for health checks to pass, and only promotes to Wave 2 after operator approval (or automatic approval if all health gates are green). If Wave 2 shows degraded client experience, the operator pauses the rollout and rolls back Wave 2 devices to the prior firmware version.

**Why this priority**: Phased rollouts limit blast radius and are a key differentiator in competitor firmware orchestration. This is P3 because it builds on top of the scheduling (P2) and versioning (P1) capabilities.

**Independent Test**: Can be tested by creating a multi-wave rollout plan, executing the first wave, verifying promotion logic (manual or automatic), and simulating a failure to confirm rollback and pause behavior. Value: safe, controlled fleet-wide upgrades.

**Acceptance Scenarios**:

1. **Given** the operator defines a multi-wave rollout with device/site assignments per wave, **When** Wave 1 completes and health checks pass, **Then** the platform either auto-promotes to Wave 2 (if configured) or waits for operator approval.
2. **Given** a wave is in progress and health metrics degrade beyond a threshold, **When** the degradation is detected, **Then** the platform pauses the rollout and notifies the operator.
3. **Given** the operator initiates a rollback for a specific wave, **When** the rollback executes, **Then** the platform restores the prior firmware/config on all devices in that wave and logs the rollback.

---

### User Story 6 — Continuous Compliance & Drift Detection (Priority: P3)

The platform continuously compares the intended ("golden") configuration state against the actual state synced from Mist. When drift is detected (e.g., someone manually changed a VLAN on a switch outside the platform), the system flags the deviation, shows the diff, and offers one-click remediation to push the intended state back to the device.

**Why this priority**: Continuous compliance and drift detection close the loop on configuration governance. This is P3 because it depends on the config versioning infrastructure (P1) and the scheduling/push mechanisms (P2).

**Independent Test**: Can be tested by defining an intended state, manually introducing a drift via the Mist API, and verifying the platform detects and flags it with a correct diff. Value: prevents silent configuration rot.

**Acceptance Scenarios**:

1. **Given** an intended configuration baseline is defined for a site/device group, **When** the platform's periodic sync detects a deviation from the baseline, **Then** the platform flags the drift with a field-level diff and timestamp.
2. **Given** the operator views a flagged drift, **When** they click "Remediate," **Then** the platform pushes the intended configuration back to the affected device(s) via the Mist API.
3. **Given** the operator determines the drift is intentional, **When** they click "Accept as New Baseline," **Then** the platform updates the intended state to match the current actual state.

---

### Edge Cases

- What happens when the Mist API is unreachable during a scheduled deployment? The platform retries with exponential backoff up to a configurable limit, then marks the job as "failed — API unreachable" and alerts the operator.
- What happens when two operators schedule conflicting changes for the same device and maintenance window? The platform detects the conflict at submission time and requires the second operator to acknowledge or reschedule.
- What happens when a configuration snapshot is too large to store efficiently? The platform stores incremental diffs after the initial full snapshot, with periodic full snapshots for integrity.
- What happens when the platform itself fails mid-deployment? The platform uses idempotent operations and records progress checkpoints so that on restart, it resumes from the last completed step rather than re-executing completed actions.
- What happens when the Mist API rate limit is exceeded during a bulk sync? The platform uses adaptive rate limiting with backoff, and queues remaining work for retry after the rate window resets.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST continuously sync device inventory, configuration, and status from the Mist API at a configurable interval (default: every 5 minutes) across all organizations under the configured MSP(s).
- **FR-002**: System MUST store every observed configuration state as an immutable, timestamped revision with a content hash to prevent duplicate entries.
- **FR-003**: System MUST provide a field-level diff view between any two configuration revisions for the same entity (device, site, WLAN, policy).
- **FR-004**: System MUST allow operators to "Install from Revision" — pushing a prior configuration snapshot back to target devices via the Mist API.
- **FR-005**: System MUST support scheduling configuration or firmware deployments for a future date/time, with the ability to cancel or reschedule before execution.
- **FR-006**: System MUST execute automated pre-checks (device reachability, version compatibility) before a scheduled deployment and abort if pre-checks fail.
- **FR-007**: System MUST execute automated post-checks (service health, client connectivity) after a deployment and auto-revert if post-checks fail beyond a configurable threshold.
- **FR-008**: System MUST record every configuration change in an audit trail that includes timestamp, actor identity, entity scope, and old → new field values.
- **FR-009**: System MUST support exporting audit trail records as downloadable reports (CSV or structured format) with filters for date range, entity type, and actor.
- **FR-010**: System MUST support multi-wave (phased) rollout plans where each wave requires health-gate approval before promoting to the next wave.
- **FR-011**: System MUST detect configuration drift between the defined intended state (baseline) and the actual state observed from the Mist API, and flag deviations with a field-level diff.
- **FR-012**: System MUST allow operators to remediate drift (push intended state) or accept drift as the new baseline with a single action.
- **FR-013**: System MUST provide a historical "time-travel" query interface — given a device and a timestamp, return the configuration, port states, and health metrics as they were at that moment.
- **FR-014**: System MUST handle Mist API rate limits gracefully using adaptive backoff and queuing, without losing or duplicating work.
- **FR-015**: System MUST use idempotent operations and progress checkpoints so that interrupted jobs resume safely on restart.
- **FR-016**: System MUST expose health and readiness endpoints for container orchestration (liveness/readiness probes).
- **FR-017**: System MUST export operational metrics (sync latency, job durations, error rates, queue depths) for external monitoring.
- **FR-018**: System MUST support three authentication methods: (1) API tokens (org-scoped), (2) interactive login (email/password with optional 2FA, required for MSP-level access), and (3) Mist SSO integration. After authentication, the platform MUST retrieve the user's permissions and roles from the Mist API (`GET /api/v1/self` privileges) and enforce them for all operations. No separate user database or RBAC layer is maintained — the Mist API is the single source of truth for identity and authorization.
- **FR-019**: System MUST log all actions (syncs, deploys, rollbacks, schedule changes) with structured, machine-parseable entries and never log secrets or credentials.
- **FR-020**: System MUST support running on-premises in a corporate datacenter or in any cloud environment without vendor lock-in.
- **FR-021**: System MUST be composed of free, open-source components with permissive or copyleft licenses.
- **FR-022**: System MUST be deployable as horizontally scalable containers orchestrated by a container platform, with each of the three layers (frontend, application, backend) scaling independently.

#### Extended A-Z Gap Coverage (Full Scope)

- **FR-023** *(Category H — Risk Simulation)*: System MUST provide a dry-run / risk-score assessment before any configuration or firmware change is applied, estimating blast radius (number of affected devices, sites, clients) and flagging high-risk changes for additional approval.
- **FR-024** *(Category I — Policy Lifecycle)*: System MUST track the full lifecycle of network policies (WLAN, firewall, NAC rules) including creation, modification, expiry, and retirement with version history and dependency analysis.
- **FR-025** *(Category J — Administrative Domains / RBAC)*: System MUST enforce access control scoped to MSP, organization, site, or device-group level based on the user's Mist API privileges (retrieved via `GET /api/v1/self`). Operators can only view and modify resources within their Mist-assigned scope. API token users are limited to their token's org scope; interactive/SSO users inherit their full Mist privilege set including MSP-level access.
- **FR-026** *(Category K — Path Analysis)*: System MUST provide network path tracing between any two points (client-to-gateway, site-to-site) using topology and routing data synced from Mist, showing each hop, latency, and potential failure points.
- **FR-027** *(Category M — Application-Centric Change Modeling)*: System MUST allow operators to model changes in terms of applications and services (e.g., "move Teams traffic to DSCP EF") rather than raw device configs, translating intent into device-level configuration.
- **FR-028** *(Category O — Transactional / Atomic Edits)*: System MUST support atomic multi-device configuration transactions that either commit to all target devices or roll back entirely, preventing partial-apply states.
- **FR-029** *(Category P/R — Golden Image Governance)*: System MUST maintain a golden image repository for firmware and configuration templates, with approval workflows for promoting images to "approved" status and preventing deployment of unapproved versions.
- **FR-030** *(Category S — Application Discovery)*: System MUST discover and inventory applications traversing the network using Mist's application visibility data, correlating traffic flows with configured policies.
- **FR-031** *(Category T — Change Templates)*: System MUST provide reusable, parameterized change templates (e.g., "Add VLAN to site," "Enable 802.1X on port range") that operators can instantiate with site-specific values to reduce errors.
- **FR-032** *(Category U — Compliance Audit Packs)*: System MUST generate compliance-ready audit evidence packages (SOX, PCI-DSS, SOC2) bundling change records, approval chains, before/after diffs, and health check results into a single exportable artifact.
- **FR-033** *(Category V — Segregation of Duties)*: System MUST enforce maker-checker workflows for high-impact changes, requiring a different operator to approve a change than the one who authored it.
- **FR-034** *(Category W — Automated Backup)*: System MUST automatically back up all device and site configurations on a configurable schedule (default: daily) and before every planned change, storing backups in the revision store with retention policies.
- **FR-035** *(Category Y — Incident-Change Correlation)*: System MUST correlate configuration changes with incident timelines (alarms, SLE degradations, client drops synced from Mist), enabling operators to identify which change caused a specific incident.
- **FR-036** *(Category Z — Dry-Run Verification)*: System MUST support a "dry-run" mode for any configuration push that validates the payload against target device constraints, API schema, and policy rules without actually applying the change.
- **FR-037** *(Notifications)*: System MUST deliver operational alerts (deployment failures, drift detection, post-check failures, approval requests, rollback events) via operator-configurable notification channels supporting both email (SMTP) and webhooks (Slack, Teams, PagerDuty, generic HTTP). Each alert type MUST be independently routable to one or more channels.

### Deferred Requirements

The following requirements are included for completeness but are **deferred from initial implementation**. They require Mist API capabilities and/or design patterns that need further research before tasking:

- **FR-026** *(Category K — Path Analysis)*: Deferred. Requires topology and routing data from Mist that may not be available via current API endpoints. Research needed: identify available topology APIs (`/api/v1/sites/{site_id}/stats/maps`, PCap/BLE data, gateway route tables) and determine feasibility.
- **FR-027** *(Category M — Application-Centric Change Modeling)*: Deferred. Requires an intent-to-config translation engine that maps application-level abstractions to device-specific configuration. Research needed: define the application taxonomy, identify Mist config primitives that map to application intents (DSCP, QoS policies, firewall rules).
- **FR-030** *(Category S — Application Discovery)*: Deferred. Depends on Mist application visibility APIs. Research needed: verify `mistapi.api.v1.sites.insights` or similar endpoints provide the required traffic flow and application classification data.

### Key Entities

- **MSP (Managed Service Provider)**: The top-level tenant representing a Juniper Mist MSP account that controls one or more Organizations. Key attributes: MSP ID, name, Mist cloud host (API base URL), authentication session, sync status. Discovered via `GET /api/v1/self` privileges and enumerated via `mistapi.api.v1.msps.*` endpoints. Requires session-based (email/password) authentication — API tokens are org-scoped and cannot access MSP-level APIs.
- **Organization**: A Mist organization managed under an MSP. Key attributes: org ID, MSP reference, name, API base URL, sync status. Enumerated via `mistapi.api.v1.msps.orgs.listMspOrgs(msp_id)`.
- **Site**: A logical grouping of devices within an organization. Key attributes: site ID, org reference, name, location metadata.
- **Device**: A physical AP, switch, or gateway managed by Mist. Key attributes: device ID, site reference, serial number, model, role, firmware version, operational status.
- **Configuration Revision**: An immutable snapshot of a device/site/org configuration at a point in time. Key attributes: revision ID, entity reference, captured timestamp, content hash, configuration payload, actor (if known).
- **Scheduled Job**: A planned deployment or change to be executed at a future time. Key attributes: job ID, target entities, change payload, scheduled time, status (pending/running/completed/failed/cancelled), pre-check and post-check definitions.
- **Audit Record**: A log entry capturing a single configuration change event. Key attributes: record ID, timestamp, actor, entity scope, change type, old values, new values.
- **Rollout Plan**: A multi-wave deployment plan. Key attributes: plan ID, waves (ordered list), devices per wave, health gate criteria, promotion mode (manual/automatic), overall status.
- **Baseline (Intended State)**: The "golden" configuration defined as the correct state for a device group. Key attributes: baseline ID, entity scope, configuration payload, last updated timestamp.
- **Drift Alert**: A flagged deviation between intended and actual configuration. Key attributes: alert ID, baseline reference, device reference, detected timestamp, diff payload, status (open/remediated/accepted).
- **Change Template**: A reusable, parameterized recipe for common change operations. Key attributes: template ID, name, category (VLAN, ACL, WLAN, firmware), parameter schema, target entity type, author, approval status.
- **Golden Image**: An approved firmware or configuration artifact in the golden image repository. Key attributes: image ID, type (firmware/config), version, approval status (draft/approved/retired), approver, hash, upload timestamp.
- **Compliance Audit Pack**: A bundled evidence artifact for regulatory compliance. Key attributes: pack ID, compliance framework (SOX/PCI/SOC2), date range, included records (changes, approvals, diffs, health checks), export timestamp, format.
- **Network Policy**: A tracked policy lifecycle entity (WLAN, firewall rule, NAC rule). Key attributes: policy ID, type, org/site scope, version, lifecycle state (active/expired/retired), dependencies, effective dates.
- **Incident-Change Correlation**: A linkage between a detected incident and causally related configuration changes. Key attributes: correlation ID, incident reference (alarm/SLE event), change reference (revision/job), confidence score, detection method.
- **Notification Channel**: A configured delivery endpoint for operational alerts. Key attributes: channel ID, type (email/webhook), destination (SMTP address or webhook URL), alert type subscriptions, enabled flag, authentication credentials (for webhooks).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operators can retrieve historical device state for any timestamp within the retention window in under 5 seconds.
- **SC-002**: Configuration changes are captured and available in the revision history within 10 minutes of occurring in Mist.
- **SC-003**: Field-level diffs between any two revisions render in under 3 seconds for configurations up to 50 KB.
- **SC-004**: Scheduled deployments execute within 60 seconds of their target time, with pre-check and post-check gates completing within 2 minutes each.
- **SC-005**: Auto-rollback on post-check failure initiates within 90 seconds of detecting the threshold breach.
- **SC-006**: Audit trail queries filtered by date range, entity, and actor return results in under 5 seconds for datasets covering 12 months of changes.
- **SC-007**: The platform runs entirely on free, open-source software with no paid license dependencies.
- **SC-008**: Each layer (frontend, application, backend) scales horizontally to handle at least 5x the baseline load (baseline: 100 orgs, 100,000 sites, 1,000,000 devices; 5x target: 500 orgs, 500,000 sites, 5,000,000 devices) without architecture changes.
- **SC-009**: Multi-wave rollouts support at least 10 waves with 500+ devices per wave without manual intervention between waves (when auto-promotion is enabled and health gates pass).
- **SC-010**: Drift detection identifies configuration deviations within two sync cycles (default: 10 minutes) of the drift occurring.
- **SC-011**: 90% of operators can complete a "rewind and inspect" investigation within 5 minutes on their first attempt using the platform.
- **SC-012**: Audit evidence export (12 months of changes) completes in under 30 seconds and produces a valid, parseable file.
- **SC-013**: Dry-run validation for a configuration change returns a risk assessment and validation result within 10 seconds.
- **SC-014**: Change templates can be instantiated and applied to a target site in under 3 user actions (select template, fill parameters, confirm).
- **SC-015**: Maker-checker approval workflow completes within the platform without requiring external tooling.
- **SC-016**: Incident-change correlation identifies the causal change for an alarm/SLE degradation within 2 minutes of the incident being synced.
- **SC-017**: Golden image promotion workflow supports at least draft → approved → retired lifecycle with approval audit trail.
- **SC-018**: Automated backups capture all org/site/device configs daily with zero operator intervention after initial configuration.

## Assumptions

- The Mist API provides sufficient endpoints to read device inventory, configuration, status, firmware versions, and event/audit logs programmatically. Operations that "push" configuration back to Mist rely on existing Mist API write endpoints. MSP-level endpoints (`/api/v1/msps/*`) provide organization enumeration and cross-org access.
- The Mist API exposes enough change context (timestamps, actor metadata) in its audit/event logs to attribute changes; where attribution is unavailable, the platform records the API token identifier.
- Retention windows for historical data are configurable by the operator (default assumption: 90 days for full snapshots, 1 year for audit trail records).
- The platform does not replace the Mist portal UI for day-to-day WLAN/LAN/WAN configuration — it augments Mist with the operator-grade features (time-travel, versioning, scheduling, audit) that the portal does not natively provide.
- Pre-checks and post-checks are defined as pluggable health probes (e.g., "device responds to ICMP," "client count above threshold") and can be extended over time.
- The platform is operated by NOC engineers with network operations experience; it does not need to provide a general-purpose network design tool.
- User identity and authorization are inherited from the Mist API. The platform does not maintain its own user database or RBAC rules. Authentication supports API tokens (org-scoped, limited to single-org operations), interactive login (email/password + 2FA, enables MSP-level access), and Mist SSO integration. Permissions are retrieved via `GET /api/v1/self` and cached with a configurable TTL (default: 5 minutes). This is consistent with MistHelper's existing `detect_msp_privileges()` and `initialize_mist_session_interactive()` patterns.
- Corporate environments may use Zscaler or similar SSL-inspecting proxies; the platform's container build/push workflows use CI/CD infrastructure to bypass proxy restrictions (consistent with MistHelper's existing Zscaler workaround pattern).
- All components selected must be free and open-source, deployable on-premises or in any cloud, and orchestrated via container platforms without vendor lock-in.
- Baseline scale target: 100 Mist organizations under one or more MSPs, 1,000 sites per organization, 10 devices per site (1,000,000 total devices). Database partitioning (by org/time), async worker concurrency, and per-org API rate-limit budgeting must be designed for this scale from the start. Configuration snapshots at this scale will generate significant storage volume; incremental diff storage (FR-002) and configurable retention are critical.
