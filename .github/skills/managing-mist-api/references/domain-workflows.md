# Domain workflows

## Contents

1. [Identity, organizations, and inventory](#identity-organizations-and-inventory)
2. [Configuration and network services](#configuration-and-network-services)
3. [Monitoring and diagnostics](#monitoring-and-diagnostics)
4. [Location, files, and integrations](#location-files-and-integrations)
5. [Firmware and disruptive operations](#firmware-and-disruptive-operations)

Each procedure begins with the operation contract in the source-authority guide.
The endpoint catalog routes every primary category and every SDK-only entry.
These procedures do not grant approval to make a live request.

## Identity, organizations, and inventory

### Current identity and account administration

Sources: [Auth](../../../../documentation/Auth%20_%20API%20_%20Mist.html) and
[Self Account](../../../../documentation/api/INDEX.md#self-account).

Use `/self` to establish the current identity and privileges for an authorized live task.
Use the documented self audit logs and API usage operations when that task needs them.
Separate user-token operations from organization-token operations.

Account creation, password recovery, email verification, OAuth linking, MFA changes, and account deletion have security effects.
Do not invoke them during an inventory workflow.
Do not use a verification URL as a harmless connectivity check.

Before an access change, identify the affected account and its current privileges.
Show the intended role and scope changes without exposing credentials.
Keep an approved administrator access path during the change.
Verify the resulting privileges through the documented read operation.

Warning: deleting a user account can also delete an orphaned organization and its data.
Read [Leave](../../../../documentation/Auth%20_%20API%20_%20Mist.html#leave) before considering that request.

### Organizations, sites, and groups

Sources: [organization sites](../../../../documentation/Org%20_%20API%20_%20Mist.html#sites),
[site groups](../../../../documentation/Org%20_%20API%20_%20Mist.html#site-groups), and
[organization operations](../../../../documentation/api/INDEX.md#orgs).

1. Resolve the organization through authorized identity evidence.
2. List its sites with complete pagination.
3. Match the intended site by stable ID and approved identifying attributes.
4. Read the selected site and its group memberships.
5. Perform only the requested read or separately approved change.

For a new site, read the schema for name, timezone, country code, address, location, and template assignments.
Use the constants operations to validate country and state values when applicable.
Do not use a display name as a persistent database key.
Do not assume that a site-group relationship is one-to-one.

An organization clone is a change, not a backup read.
The [clone description](../../../../documentation/Org%20_%20API%20_%20Mist.html#clone-org) excludes sites and site groups.
Do not promise a full operational copy from that endpoint.
Reconcile each copied resource and assignment under the actual clone contract.

### MSP administration

Sources: [MSP guide](../../../../documentation/MSP%20_%20API%20_%20Mist.html) and
[MSP categories](../../../../documentation/api/INDEX.md#msps).

Resolve `msp_id` before selecting a customer organization.
Use MSP organization and organization-group operations only within the approved provider scope.
Keep provider administrators, organization administrators, and SSO roles distinct.
Do not treat a provider-level result as a site-level authorization grant.

For a cross-customer report, process each approved organization independently.
Record failures and unavailable organizations without replacing them with empty success results.
Preserve the provider and organization IDs in the output.

MSP license transfers and organization management can affect several tenants.
Obtain approval for both source and destination before a transfer.
Do not broaden an inventory lookup by MAC into unauthorized customer discovery.

### Inventory versus configuration versus observed state

Sources: [inventory](../../../../documentation/Org%20_%20API%20_%20Mist.html#inventory),
[site device configuration](../../../../documentation/api/sites/GET_sites_site_id_devices.md), and
[site device statistics](../../../../documentation/api/sites/GET_sites_site_id_stats_devices.md).

| Need | Preferred source family | Important distinction |
| - | - | - |
| Claimed devices and assignment | Organization inventory. | An unassigned device can have `site_id: null`. |
| Device configuration | Organization or site devices. | A configured value can differ from current device state. |
| Current connectivity and measurements | Device statistics. | Record the observation time and stale or missing values. |
| Historical device events | Device event search. | Use the correct time window and pagination. |
| Model capabilities | Device model constants. | A feature can depend on model and firmware. |

Specify `type=all` only on a listing that documents that value.
Otherwise, use the documented explicit device type.
Do not use access-point defaults for a switch or gateway audit.

Join records through stable identifiers and preserve their source.
Keep unassigned devices instead of dropping rows with a null site.
Treat name changes as updates to the same identity, not as new devices.

### Claim, assign, unassign, replace, and remove

Sources: [claim inventory](../../../../documentation/api/orgs/POST_orgs_org_id_inventory.md),
[assignment](../../../../documentation/api/orgs/PUT_orgs_org_id_inventory.md), and
[replacement](../../../../documentation/api/orgs/POST_orgs_org_id_inventory_replace.md).

1. Read the present inventory ownership and assignment.
2. Verify every MAC, serial, destination, and conditional request field.
3. Preview the approved targets and the exact assignment effects.
4. Submit the approved operation once.
5. Reconcile per-item results and verify the final assignment.

The inventory PUT multiplexes actions through `op`.
Its description includes `assign`, `unassign`, `delete`, `upgrade_to_mist`, and `downgrade_to_jsi`.
Do not classify this PUT as assignment-only from its SDK name.

For `assign`, validate the required target site and the permitted reassignment policy.
The current schema introduces `mist_configured` and marks `managed` and `disable_auto_config` as deprecated.
Do not send contradictory old and new flags.

Claim codes are credentials. Never log or export them as ordinary inventory attributes.
For asynchronous claims, distinguish the primary claim/status operations from the SDK-only `claims` helpers.
Do not invent the latter helpers' request bodies from their names.

### Licenses and support

Sources: [licenses](../../../../documentation/Org%20_%20API%20_%20Mist.html#license),
[organization licenses](../../../../documentation/api/INDEX.md#orgs-licenses), and
[tickets](../../../../documentation/api/INDEX.md#orgs-tickets).

Separate entitlements, consumption, active terms, and per-site requirements in a license report.
Preserve license type, start time, end time, quantity, and source scope.
Do not treat a quantity as proof that every enabled feature has a valid entitlement.

License movement, deletion, claims, and annotations are changes with separate contracts.
Verify both organizations and the remaining entitlement before an approved transfer.
Do not infer that a license transfer also moves devices.

Read support tickets when authorized. Treat ticket creation, comments, attachments, and support uploads as externally visible changes.
Remove secrets and unnecessary personal data before submission.
Do not upload full configuration or packet captures without explicit approval for that content.

## Configuration and network services

### Configuration ownership, templates, and variables

Sources: [device configuration generation](../../../../documentation/Org%20_%20API%20_%20Mist.html#device-config-generation),
[templates](../../../../documentation/Org%20_%20API%20_%20Mist.html#template), and
[derived WLANs](../../../../documentation/api/sites/GET_sites_site_id_wlans_derived.md).

1. Read the target resource and its template/profile assignments.
2. Read the related site and organization settings.
3. Inspect the documented derived view for the effective configuration.
4. Identify the object that owns the requested change.
5. Compare the intended change at that owner before seeking approval.

Do not assume a universal organization-to-site-to-device precedence for every field.
The source defines field-specific and resource-specific rules.
Do not write to a `/derived` route unless the exact source defines a write operation there.

Keep RF, network, AP, gateway, site, WLAN, alarm, and device-profile templates distinct.
An identifier named `template_id` does not automatically refer to every template class.
Read the appropriate assignment fields instead of copying a neighboring resource's schema.

For WLAN-derived reads, `resolve` controls `SITE_VARS` resolution.
It is not a generic instruction to expand every referenced object.
Preserve unresolved `{{...}}` values during template editing unless the task explicitly changes them.
Use the documented variable source and spelling.

Inspect `for_site`, `template_id`, and other provenance fields when the response supplies them.
Do not write a flattened derived response into the source template.
That action can copy generated defaults, site-specific values, and read-only state into a shared configuration.

After an approved change, read both the source object and its derived effect.
If the device applies configuration asynchronously, verify the operational result separately.

### WLANs, RF, guest access, and WXLAN

Sources: [WLAN definition](../../../../documentation/Site%20_%20API%20_%20Mist.html#wlan),
[RADIUS](../../../../documentation/Site%20_%20API%20_%20Mist.html#radius), and
[guest portal](../../../../documentation/Site%20_%20API%20_%20Mist.html#guest-portal).

For a WLAN audit, inspect the authentication mode, bands, VLAN behavior, access controls, and template ownership.
Check conditional fields for PSK, EAP, RADIUS, RadSec, and Mist NAC.
Do not enable an open network or weaken authentication as a diagnostic shortcut.

The primary schema deprecates `band` in favor of `bands`.
The documented band values include string values `24`, `5`, and `6`.
Do not convert them to frequency numbers or infer model support from their presence in a schema.
Use model and channel constants for capability and regulatory checks.

Preserve the order of authentication and accounting servers where the source gives the order meaning.
Check the interactions between broadcast filtering, Bonjour, isolation, and wireless bridging.
Do not modify all WLAN defaults when the user requests one field change.

For PSKs, distinguish site keys, organization keys, bulk key operations, and PSK portals.
Protect passphrases and preserve expiry, identity, and authorization scope.
Key revocation and guest unauthorization can interrupt access.

Portal templates and portal images use dedicated operations.
Do not assume that a WLAN GET includes the editable portal template.
Read `portal_template_url` and the documented portal-template route with the download security rules.
Preserve template placeholders such as `{{code}}` and `{{duration}}`.

WXLAN rules, tags, and tunnels are separate resources.
Read related tag IDs and tunnel IDs before changing a policy.
Do not confuse `wxtunnel_id` with `mxtunnel_ids` or a site Mist Edge tunnel name.

### Switches, ports, virtual chassis, and EVPN

Sources: [switch configuration](../../../../documentation/Site%20_%20API%20_%20Mist.html#switch-config),
[virtual chassis](../../../../documentation/api/INDEX.md#sites-devices---wired---virtual-chassis), and
[EVPN](../../../../documentation/api/INDEX.md#orgs-evpn-topologies).

Read device type, model, port identity, network template, device overrides, and current port statistics.
Preserve the actual interface identifier. Do not infer a port name from a display position.
Read the dedicated local-port configuration contract when a helpdesk override is involved.

Before a virtual-chassis change, resolve the managed chassis and all members.
Record member roles, serials, MACs, and the current virtual identity when available.
Do not treat FPC positions as globally stable identifiers across a conversion.

Virtual-MAC conversion, master switching, port-mode changes, and member removal can interrupt service.
Require typed confirmation and an operator-approved recovery procedure.
Verify both the chassis state and connectivity after the operation.

For EVPN, distinguish site and organization topologies.
Read the topology members, current ownership, and eligibility from the documented fields.
Do not assume that an unused switch can safely join a topology without a configuration preview.

### Gateways, WAN, SSR, SRX, and routing

Sources: [gateway template](../../../../documentation/Org%20_%20API%20_%20Mist.html#gateway-template),
[WAN utilities](../../../../documentation/api/INDEX.md#utilities-wan), and
[gateway insights](../../../../documentation/api/sites/GET_sites_site_id_insights_gateway_device_id_stats_metric.md).

Identify the gateway family and its supported operations before constructing a payload.
SSR, SRX, and switch command support differs. A common path prefix does not establish identical capability.

For a WAN diagnosis, correlate device status, ports, routes, BGP/OSPF peers, VPN paths, service events, and the incident time.
Distinguish configured networks and policies from observed forwarding state.
Use the correct routing instance, egress interface, and HA node when the command supports those fields.

A network, service, service policy, VPN, and gateway template are separate resources.
Verify their references before an approved change.
Do not create a permissive service policy to make a diagnostic request succeed.

For HA, inspect node state and cluster membership before any operation.
Do not assume that changing one logical gateway affects only one physical node.
Cluster creation, deletion, and role changes require explicit confirmation and recovery planning.

For WAN clients, preserve the documented singular `wan_client` count routes and plural `wan_clients` search routes.
Do not substitute one spelling for the other.

### Mist Edge

Sources: [Mist Edge categories](../../../../documentation/api/INDEX.md#orgs-mxedges),
[clusters](../../../../documentation/api/INDEX.md#orgs-mxclusters), and
[tunnels](../../../../documentation/api/INDEX.md#orgs-mxtunnels).

Separate the Mist Edge device, cluster, tunnel, service, and site assignment.
Read the selected scope's configuration and statistics before an active operation.
Do not assume that an organization Mist Edge and a site Mist Edge use interchangeable request paths.

Service control, data-port bounce, AP disconnection, preemption, restart, and unregister operations can interrupt tunnels.
Verify the attached APs and dependent sites before approval.
Use the dedicated version and upgrade operations for Mist Edge rather than AP firmware routes.

### NAC, security, certificates, and access policies

Sources: [NAC rules](../../../../documentation/api/INDEX.md#orgs-nac-rules),
[NAC tags](../../../../documentation/api/INDEX.md#orgs-nac-tags), and
[certificate operations](../../../../documentation/api/INDEX.md#orgs-cert).

Distinguish identity-provider credentials from intrusion-detection profiles despite similar `IDP` labels.
Read the category and schema before selecting an operation.
Keep NAC clients, rules, tags, portals, fingerprints, SCEP, and revocation lists separate.

For an authentication incident, correlate NAC events with client, site, and time evidence.
Do not revoke a certificate or issue Change of Authorization merely to test visibility.
An identity-provider validation request can send credentials to an external system.
Confirm the approved provider and test account before that diagnostic.

Certificate rotation, regeneration, revocation, CRL truncation, and SCEP disablement change trust.
Inventory the consumers and the recovery path before approval.
Never expose private keys or replace trust material with values copied from documentation examples.

Security profiles include advanced anti-malware, antivirus, intrusion detection, and security intelligence.
Do not disable protection to suppress an error.
Verify organization-level ownership and site-derived policies before changing a profile.

## Monitoring and diagnostics

### Statistics, events, clients, and SLEs

Sources: [site insights](../../../../documentation/api/INDEX.md#sites-insights),
[site SLEs](../../../../documentation/api/INDEX.md#sites-sles), and
[constant definitions](../../../../documentation/api/INDEX.md#constants-definitions).

Select the data family from the question, not from a familiar endpoint name.
Statistics describe observations. Configuration describes intent. Events describe recorded transitions.
Do not substitute one family for another without stating the limitation.

Use wired, wireless, WAN, NAC, SDK, or Marvis client routes according to the client type.
Correlate by documented identity and time. A MAC address alone can be insufficient across tenant or historical boundaries.

For Service Level Expectations (SLEs), discover valid metrics for the selected scope.
Then read supported classifiers, summaries, trends, histograms, and impacted resources as needed.
Do not reuse a classifier from one metric with another metric without evidence.
Preserve the returned interval, units, population, and time range.

A threshold update changes monitoring behavior. It is not part of a read-only SLE report.
An anomaly or Marvis result is evidence to inspect, not permission to apply an automatic correction.

### Alarms, audit logs, and reports

Sources: [organization alarms](../../../../documentation/api/INDEX.md#orgs-alarms),
[alarm templates](../../../../documentation/api/INDEX.md#orgs-alarm-templates), and
[audit logs](../../../../documentation/api/INDEX.md#orgs-logs).

Read alarm definitions and event definitions before interpreting an unfamiliar type.
Preserve alarm ID, affected scope, severity, time, and acknowledgement state when available.
Distinguish the event occurrence from its delivery or acknowledgement time.

Acknowledgement, unacknowledgement, suppression, and subscription changes modify state.
Do not acknowledge every alarm merely because an export succeeds.
Do not suppress an alarm to make an operational report appear healthy.

For audit reports, preserve actor, scope, timestamp, and the redacted before/after difference.
Do not export secrets from an audit payload even when the API returns them.
Premium Analytics and UI settings are separate categories. Do not infer report endpoints that the source does not define.

### Commands and active diagnostics

Sources: [common utilities](../../../../documentation/api/INDEX.md#utilities-common),
[LAN utilities](../../../../documentation/api/INDEX.md#utilities-lan), and
[ping](../../../../documentation/api/utilities/POST_sites_site_id_devices_device_id_ping.md).

Use an authorized show operation when a passive read answers the diagnostic question.
Use ping, traceroute, ARP, DNS, or a synthetic test only within approved target and load limits.
Validate destinations and do not concatenate untrusted input into a shell command.

A REST show command can return a session rather than the final output.
Apply the WebSocket correlation procedure from the request-lifecycle guide.
Do not parse the HTTP acknowledgement as the device's ARP, BGP, or forwarding table.

Port bounce, MAC-table clear, DHCP lease release, dot1x clear, radio reset, and client disconnection have active effects.
Do not include these operations in a read-only diagnostic batch.
Cable tests and forced polls also need target-specific impact assessment.

### Synthetic tests, spectrum, and RF diagnostics

Sources: [synthetic tests](../../../../documentation/api/INDEX.md#sites-synthetic-tests),
[spectrum analysis](../../../../documentation/api/INDEX.md#sites-spectrum-analysis), and
[RF recordings](../../../../documentation/api/INDEX.md#sites-rfdiags).

1. Read the supported test type and its required fields for the device family.
2. Confirm the destination, interface, routing context, and permitted traffic load.
3. Trigger only the approved bounded test.
4. Retrieve the documented status or results.
5. Match the result to the target, type, and request time before interpretation.

A stored historical success does not prove that the newly requested test succeeded.
A blocked ICMP response does not alone prove application failure.
Do not run a speed test or radio analysis without considering the production load.

RF recordings can require an explicit stop and a protected download.
Track the recording ID and apply the same ownership rules as packet captures.
Do not apply RRM optimization simply because a spectrum result looks unusual.

## Location, files, and integrations

### Maps, beacons, zones, and assets

Sources: [location services guide](../../../../documentation/location%20services%20guide.txt),
[maps](../../../../documentation/api/INDEX.md#sites-maps), and
[location](../../../../documentation/api/INDEX.md#sites-location).

Distinguish site coordinates, map coordinates, scale, orientation, and observed client location.
Read the selected field's units before converting or comparing values.
Do not assume that a map coordinate is latitude or longitude.

Physical beacons, virtual beacons, RSSI zones, ordinary zones, SDK clients, and discovered assets use different resources.
Select the correct schema and identity before joining data.
Preserve map ID, site ID, observation time, and source method in a location report.

For a map change, inspect the image, scale, AP placement, zones, and dependent assets first.
Import, replacement, automatic placement, automatic orientation, and confirmation are separate operations.
Do not treat a proposed automatic placement as an applied placement.
Do not erase manual placement while applying an unrelated map edit.

Machine-learning overwrite, reset, and clear operations change location behavior.
Do not invoke them during a coverage read.
Treat unconnected-client location and raw location events as sensitive data.

### Uploads, downloads, and imports

Read the exact request media type and part names for each file operation.
Some SDK-only helpers add a file parameter to an existing API route.
Verify the installed helper signature instead of treating its name as a new endpoint.

Validate the file type, size, permitted source location, and target scope.
Prevent archive extraction outside the approved destination.
Do not import unreviewed scripts or execute content from a downloaded file.

For a map, PSK, asset, device, certificate, or user-MAC import, preview the affected objects.
Check duplicate handling and replacement semantics before approval.
After submission, reconcile each reported result and inspect the final target state.
Do not assume that an import is atomic or reversible.

### Third-party integrations and provisioning

Sources: [organization settings](../../../../documentation/Org%20_%20API%20_%20Mist.html#org-setting),
[linked applications](../../../../documentation/api/INDEX.md#orgs-linked-applications), and
[JSI](../../../../documentation/api/INDEX.md#orgs-jsi).

Cradlepoint, JSE, Juniper accounts, SkyATP, Zscaler, and OAuth-linked applications have separate configuration contracts.
Distinguish connection status, setup, update, synchronization, testing, and deletion.
Do not infer that a status request also authorizes a synchronization or setup request.

Validate the destination account and tenant before account linking.
Protect third-party credentials and client secrets with the same controls as Mist tokens.
Do not send an SMS or external identity-provider request as an unapproved connectivity test.

A registration or outbound-SSH command can contain a credential.
Do not print, execute, or distribute that command without explicit provisioning authorization.
Retrieving such a command does not authorize adopting or reconfiguring the device.

### Installer workflow

Sources: [installer APIs](../../../../documentation/Org%20_%20API%20_%20Mist.html#installer-apis) and
[installer category](../../../../documentation/api/INDEX.md#installer).

1. Verify the installer privilege and its permitted organization.
2. Resolve the documented site name and recently claimed device identifiers.
3. Inspect required maps, profiles, and templates.
4. Apply only the approved provisioning steps.
5. Verify the resulting assignment and device state.

Several installer paths use `site_name` or `device_mac` rather than standard site/device UUIDs.
Use the actual path contract for each operation.
Do not substitute administrator routes to bypass installer restrictions.

The installer optimization GET triggers radio optimization after installation.
Confirm AP placement and readiness before an approved optimization.
Do not call it from a generic GET-endpoint test suite.

## Firmware and disruptive operations

### Firmware planning

Sources: [site upgrades](../../../../documentation/Site%20_%20API%20_%20Mist.html#device-upgrade),
[upgrade utilities](../../../../documentation/api/INDEX.md#utilities-upgrade), and
[SSR upgrade](../../../../documentation/api/utilities/POST_orgs_org_id_ssr_upgrade.md).

Warning: a firmware upgrade can interrupt network service. Require typed confirmation and an approved maintenance window before submission.

1. Resolve the approved device IDs, device families, models, sites, and cluster membership.
2. Read the observed running version from device statistics or another approved running-version source.
3. Read the applicable available-version operation and its model restrictions.
4. Define the target version, schedule, failure threshold, sequencing, and recovery procedure.
5. Preview the exact target set and obtain typed confirmation.

Do not select an upgrade from a stale configured `version` field.
In MistHelper, use `RunningFirmwareVersionResolver` and inspect `reading.is_running`.
If no running version is available, report the uncertainty instead of making a firmware decision.

Do not treat AP, switch, SSR, SRX, and Mist Edge upgrades as interchangeable.
BIOS and FPGA upgrades also have separate contracts and risks.
Read the selected route's schedule units, strategy, reboot behavior, and supported family.

The SSR schema distinguishes `start_time` from `reboot_at`.
It documents `-1` values that disable download or reboot for those fields.
Do not convert these sentinel values into ordinary timestamps or apply them to unrelated upgrade APIs.

### Upgrade execution and verification

1. Recheck the approved target set immediately before submission.
2. Submit the approved request once.
3. Store the returned upgrade ID and its scope.
4. Monitor the documented status and per-device target states within a bounded deadline.
5. Verify running versions, connectivity, and relevant service health after completion.

Keep download completion, reboot scheduling, firmware installation, and service recovery distinct.
Do not treat queued or downloading devices as upgraded devices.
Report every failed, pending, cancelled, and unknown target.

The SSR status route conflicts between the primary specification and the saved organization guide.
Resolve that conflict before selecting the live status call.
Do not rewrite or probe the route merely because `/cancel` looks incorrect.

Cancellation can leave completed device changes in place.
Obtain approval before cancelling another operator's upgrade or changing its schedule.
Do not claim a rollback unless the documented recovery operation actually restores the required state.

### Destructive-operation controls

Use these controls for deletion, zeroization, reboot, revocation, cluster changes, and other disruptive actions:

- Identify the exact resource IDs and all dependent services.
- State the specific service interruption, data loss, or access loss.
- Preserve a protected recovery record when recovery is possible.
- Obtain explicit typed confirmation for the final target set and payload.
- Use EOF-safe input handling that cancels safely when the session disconnects.
- Stop on a changed scope, missing authorization, or unresolved source conflict.
- Verify the result through documented reads.
- Record irreversible effects and incomplete targets honestly.

Do not interpret an instruction to automate as permission to remove these controls.
Do not enable unattended destructive operations through a broad test flag or automatic confirmation.
