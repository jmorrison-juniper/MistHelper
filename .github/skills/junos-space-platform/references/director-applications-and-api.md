# Director applications and API

This reference covers Network Director, Connectivity Services Director, and the
REST API surfaces that the staged corpus confirms.

Use the newest selected application sources first:

- Junos Space Network Director Network Director User Guide, Release 4.0.
- Junos Space Network Director API, Release 5.3.
- Junos Space Connectivity Services Director User Guide, Release 5.3.
- Junos Space Connectivity Services Director API Reference, Release 5.3.

## Use Network Director topology view

Use this procedure when the user needs a topology map, physical connectivity, or
a map-based device view.

Source: Junos Space Network Director Network Director User Guide, Release 4.0,
pages 218 through 223.

Before you use topology view, confirm these conditions:

1. Confirm that Network Director and the client system have Internet access.
2. Discover and manage the devices in Network Director.
3. Specify SNMP parameters during discovery or in the Refresh Topology task.
4. Enable LLDP, STP, or RSTP on devices so Network Director can find neighbors.
5. Create physical location nodes such as sites, buildings, floors, closets, aisles, or racks.
6. Assign devices to their physical locations.

Set up topology view:

1. Enter Build mode.
2. Select Location view or Topology view from the view selector.
3. Use Location tasks to create sites, buildings, floors, closets, aisles, or racks.
4. Select `Topology` from the Network View Selector.
5. Refresh the topology.
6. Use the Topology tasks pane for connectivity, discovery, location, or alarm tasks.

Use topology tasks:

1. Select a device or location node in the topology map.
2. Use `View Device Connectivity` to see neighbor details.
3. Use `Refresh Topology` to refresh discovered devices and connectivity.
4. Use `View Topology Discovery Job` to see discovery jobs.
5. Use alarm tasks to show alarms by severity for selected topology objects.
6. Upload a floor plan or outdoor map when the site needs a visual map.

Caution: topology view depends on SNMP and neighbor protocols. Missing SNMP or
LLDP data can make the topology incomplete.

## Use Network Director fault and monitor views

Use these procedures when the user needs faults, alarms, or performance data.

Sources:

- Junos Space Network Director Network Director User Guide, Release 4.0, pages 115 and 1422 through 1427.
- Junos Space Network Director Network Director User Guide, Release 4.0, pages 1243 through 1248.

Use Fault mode:

1. Select Fault mode in Network Director.
2. Review active alarms by severity, category, and state.
3. Use `Search Alarms` to filter alarms by condition, time, or annotation.
4. Acknowledge an alarm only after you identify the owner and next action.
5. Clear an alarm only after the device condition is resolved.
6. Configure alarm notifications in the Fault tab of System Preferences.
7. Configure threshold alarms in the Fault tab of System Preferences.

Fault mode receives SNMP notifications from managed devices. Network Director
correlates related traps into one alarm. Severity levels are Critical, Major,
Minor, and Info.

Use Monitor mode:

1. Select Monitor mode in Network Director.
2. Select the scope in the View pane.
3. Open the Summary tab for the high-level dashboard.
4. Open Traffic, Client, RF, Equipment, Fabric Analysis, or VC Equipment Summary as needed.
5. Click a monitor details icon to view detailed records.
6. Change polling intervals in Preferences only when the data rate requires it.
7. Refresh the monitor display after the next polling interval finishes.

Monitor mode collects data from managed devices at polling intervals. Refreshing
the display does not force Network Director to poll devices immediately. In a
fabric, Network Director balances polling across fabric nodes.

## Use Network Director deploy mode

Use this procedure when Network Director has pending configuration changes or
software image tasks.

Source: Junos Space Network Director Network Director User Guide, Release 4.0,
pages 1147 through 1151 and 1170 through 1171.

1. Enter Deploy mode.
2. Review devices with pending configuration changes.
3. Preview the pending configuration changes.
4. Validate the pending changes.
5. If manual approval is enabled, create or review the change request.
6. Deploy approved changes now or schedule them.
7. Track the deployment job.
8. Open the Deploy Configuration window.
9. Review each device deployment status.
10. Open the configuration or result details when a device reports a warning or failure.

Warning: Network Director deploys all pending configuration changes for a device.
Do not deploy until you review the complete pending configuration.

Warning: Network Director does not deploy to an out-of-sync device or to a
device with uncommitted candidate changes. Resync or clear the device state
before you deploy.

Network Director locks a scheduled deployment job and its assigned profiles and
devices until the job runs or is canceled. Cancel the scheduled job and create a
new one when properties must change.

## Use Connectivity Services Director

Use this section when the user manages services, service orders, service faults,
or provider edge devices through Connectivity Services Director.

Sources:

- Junos Space Connectivity Services Director User Guide, Release 5.3, pages 56 through 59.
- Junos Space Connectivity Services Director User Guide, Release 5.3, pages 842 through 906.
- Junos Space Connectivity Services Director User Guide, Release 5.3, pages 901 through 904.

Select the view:

1. Use Service View for service orders and service lifecycle tasks.
2. Use Device View for devices grouped by model.
3. Use Custom Group View for operator-defined groups.
4. Use Topology View for a graphical view of devices, links, and zones.
5. Use the Tasks pane to start the task that matches the selected view.
6. Use the Alarms bar to enter Fault mode for active alarms.

Deploy device configuration in Connectivity Services Director:

1. Enter Deploy mode.
2. Open the Devices with recent configuration changes page.
3. Review the pending configuration changes.
4. If manual approval is required, create a change request.
5. Enter the change request number and title.
6. Add comments for the configuration changes when useful.
7. Submit the change request.
8. The approver opens `Approve Change Requests`.
9. The approver reviews details, views the pending configuration, and approves or rejects the request.
10. After approval, deploy now or schedule deployment.
11. Open the Deploy Configuration window and review each device result.

Warning: a service or device configuration deployment can affect many customer
services. Review the service order, pending configuration, and device list before
you deploy.

Enable SNMP traps in Connectivity Services Director:

1. Enter Deploy mode.
2. Select `Set SNMP Trap Configuration` in the Tasks pane.
3. Select devices that are up and in the same device family.
4. Click `Deploy Trap Configuration`.
5. Enter a deployment job name or keep the default.
6. Select individual traps or all traps.
7. Click `OK`.
8. Review the Deploy Configuration window.
9. After deployment, enable alarms and set alarm retention in Preferences.

Connectivity Services Director uses protocol port 10162 for traps from devices.
Down devices cannot receive trap forwarding configuration.

## Use service orders in Connectivity Services Director

Use this procedure when the user asks how CSD turns a service design into a
service order.

Source: Junos Space Connectivity Services Director User Guide, Release 5.3,
pages 901 through 955.

1. Enter Service View.
2. Select the service provisioning task for the service type.
3. Select a published service definition.
4. Enter the service order general settings.
5. Select provider edge devices or nodes.
6. Enter endpoint or UNI settings.
7. Select LSPs when the service requires explicit LSP selection.
8. Review the service order.
9. Click `Finish` to create the order.
10. Deploy the new service.
11. Monitor the service order until it reaches the expected state.
12. Audit the service when the task needs proof that the device configuration matches the service.

Warning: service orders can create, change, or delete customer connectivity.
Confirm the service definition, endpoints, VLAN values, and route targets before
approval.

The CSD source covers E-Line, E-LAN, IP, LSP, OAM, performance management,
functional audit, and configuration audit workflows.

## Use REST APIs

Use this section when the user needs API workflow guidance for Junos Space,
Network Director, or Connectivity Services Director.

Sources:

- Junos Space Connectivity Services Director API Reference, Release 5.3, pages 40 through 42.
- Junos Space Network Director API, Release 5.3, pages 4 through 6.
- Junos Space Network Management Platform Workspaces User Guide, Release 21.1, pages 961 and 962.
- Junos Space Network Management Platform Complete Software Guide, Release 21.1, pages 1351 and 1352.

Follow the shared REST workflow:

1. Confirm the product and release.
2. Confirm that the installed application exposes the needed API.
3. Confirm that the account has the required role.
4. For `exec-rpc`, confirm that the user has an API access profile.
5. Choose the HTTP method that matches the operation.
6. Use `GET` to retrieve a resource or query data.
7. Use `POST` to update a resource on the server.
8. Use `PUT` to create resource state on the server.
9. Use `DELETE` to remove resource state on the server.
10. Set `Accept` for APIs that return XML or JSON.
11. Set `Content-Type` for APIs that send a request payload.
12. Send the request from a REST client.
13. Read the response body and status.
14. For long running jobs, poll the progress or detail link until the state is done.

Warning: an API can change services or devices at scale. Test the request in a
lab and confirm the target resource list before a production request.

Connectivity Services Director exposes RESTful web services under
`/api/juniper/space`. The API reference lists resource families for customers,
provider edge devices, prestage devices, resource pools, service definitions,
service orders, service operations, service templates, audits, performance
statistics, LSP services, OAM services, benchmarking, and timing services.

Network Director API exposes REST APIs for network management functions. The
source states that only `Super Administrator` and `Monitor Admin` can access the
Network Director APIs. It also states that a REST HTTP client is required.

Junos Space Network Management Platform has REST API settings for long running
job results. The setting controls whether a final progress response includes
detailed data or a detail link for supported jobs such as script management and
configlet management jobs.
