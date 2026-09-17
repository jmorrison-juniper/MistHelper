# Fleet operations

This reference covers discovery, adoption, status checks, resync, configuration
templates, bulk configuration deployment, image import, image staging, checksum
validation, and device image deployment.

Use the newest selected fleet sources first:

- Junos Space Network Management Platform Complete Software Guide, Release 21.1.
- Junos Space Network Management Platform Workspaces User Guide, Release 21.1.

## Discover devices

Use this procedure to create and run a device discovery profile.

Sources:

- Junos Space Network Management Platform Complete Software Guide, Release 21.1, pages 78 through 80.
- Junos Space Network Management Platform Workspaces User Guide, Release 21.1, pages 85 through 97.

Before discovery, confirm these conditions:

1. Confirm that the device has a management IP address that Junos Space can reach.
2. Confirm that a device user with Junos Space administrator privileges exists.
3. If you use ping as a probe, confirm that the device answers ping.
4. If you use SNMP as a probe, confirm that SNMP has read-only v1, v2c, or v3 credentials.
5. Confirm that SSHv2 is enabled on the device.
6. Confirm that firewalls allow Junos Space to reach TCP port 22 on the device.
7. Confirm that the device can reach UDP port 162 on Junos Space for traps.
8. For an SRX cluster, discover each node by its own management IP address.
9. For a device with dual Routing Engines, use the current primary Routing Engine IP address.

Create the profile:

1. In the Junos Space UI, select `Devices > Device Discovery > Device Discovery Profiles`.
2. Click the `Create Device Discovery Profile` icon.
3. Enter the discovery profile name.
4. Choose manual targets or upload a CSV file.
5. Enter IP addresses, hostnames, IP ranges, or subnets.
6. Select the probes.
7. Select the authentication method.
8. Enter credentials or select existing credentials.
9. Optionally, enter SSH fingerprints.
10. Set the discovery schedule.
11. Save the profile.

Run the profile:

1. Select `Devices > Device Discovery > Device Discovery Profiles`.
2. Select the profile check box.
3. Click the `Run Now` icon.
4. Watch the Discovery Status report.
5. Open the Job Management page.
6. Double-click the discovery job ID.
7. Read the Description column for each target.
8. If discovery succeeds, open the Device Management page.
9. Confirm that the device appears in the inventory.

Warning: discovery can push `set system services netconf ssh` to a Junos OS
device. Confirm that the change is allowed before you run discovery.

Junos Space uses DMI over SSHv2 for managed Junos OS devices. It can add itself
as an SNMP trap destination during discovery unless the application setting is
disabled.

## Check status and resync a device

Use this procedure when an operator asks whether Junos Space adopted a device or
whether the database matches the device.

Sources:

- Junos Space Network Management Platform Complete Software Guide, Release 21.1, pages 79 through 82.
- Junos Space Network Management Platform Workspaces User Guide, Release 21.1, pages 306 and 307.

Check status:

1. Open `Network Management Platform > Devices > Device Management`.
2. Find the device.
3. Confirm that `Connection Status` shows `Up`.
4. Confirm that managed status shows `In Sync`.
5. If the device is absent, open the discovery job details.
6. If the status is down, check reachability, SSH, credentials, and SNMP.

Resync the device:

1. Confirm that the network is the system of record.
2. Open `Devices > Device Management`.
3. Select the device or devices to resynchronize.
4. From the Actions menu, select `Device Operations > Resynchronize with Network`.
5. In the Resynchronize Devices window, click `Confirm`.
6. Open Job Management.
7. Double-click the resynchronization job ID.
8. Read the Description column for the result or failure reason.

Warning: if Junos Space is the system of record, do not use a normal resync to
accept device changes. Review the out-of-band changes first, because a reject
can remove configuration from the device.

Junos Space delays a scheduled resync when another resync job already runs on
the same device. The default damper interval is 20 seconds.

## Deploy configuration with templates

Use this procedure when the user needs one configuration change on many devices.

Sources:

- Junos Space Network Management Platform Complete Software Guide, Release 21.1, pages 82 through 84.
- Junos Space Network Management Platform Workspaces User Guide, Release 21.1, pages 321 through 357.

Choose the template type:

1. Use a template definition when the change must be scoped to a device family and Junos OS version.
2. Use a quick template when the operator needs a CLI-based or form-based template without a definition.
3. Use variables when each device needs a different value.
4. Use CSV values when many device-specific values must be loaded at once.

Create a quick template:

1. Select `Device Templates > Templates`.
2. Click the `Create Template` icon.
3. Select `Create Quick Template`.
4. Enter a unique quick template name.
5. Select the device family.
6. Select the Junos OS version.
7. Choose the CLI-based template editor or the form-based editor.
8. Enter the configuration.
9. Configure variable settings if the template uses variables.
10. Preview the configuration.
11. Click `Save` to save only.
12. Click `Save and Assign/Deploy` to continue to deployment.

Assign a device template:

1. Select `Device Templates > Templates`.
2. Select the configuration template or quick template.
3. Select `Assign to Device` from the Actions menu.
4. Select the template version.
5. Find compatible devices manually, by tag, by device property, or by CSV.
6. Select the devices.
7. Open the XML or CLI tab to review the generated configuration.
8. Click `Validate on Device`.
9. If validation fails, correct the template parameters.
10. Click `Assign` only after validation succeeds.

Deploy or assign a template:

1. Select `Device Templates > Templates`.
2. Select the device template.
3. Select `Assign/Deploy Template` from the Actions menu.
4. Select the template version.
5. Select target devices manually, by device property, by tag, or by CSV.
6. Click `Next`.
7. Resolve device-specific variables.
8. Review the generated configuration.
9. Validate the configuration on devices.
10. Deploy now, schedule deployment, or publish for later review.
11. Open the job ID and verify each device result.

Warning: template deployment can change many devices. Review the generated CLI
or XML and the selected devices before you deploy.

Warning: a quick template can erase configuration when `SET` commands are
replaced with `DELETE` commands. Check each delete command before deployment.

If a template was already assigned to a device, do not use the Deploy workflow
for the same template and device. The source states that Junos Space can show
managed status as `SpaceChanged` in that case.

## Review and deploy device configuration

Use this procedure when a device has pending configuration changes.

Source: Junos Space Network Management Platform Workspaces User Guide, Release
21.1, pages 147 through 159.

1. Open the Review/Deploy Configuration page from the Devices workspace.
2. Select the device with pending changes.
3. Review the configuration in the available formats.
4. Exclude any change that must not deploy.
5. Validate the pending configuration.
6. If validation fails, repair the source configuration.
7. If validation succeeds, deploy now or schedule deployment.
8. Open Job Management.
9. Confirm that each device reports success.

Warning: never deploy a pending configuration that you did not review. The job
can apply all pending changes for the device, not only the change you expected.

## Stage and deploy device images

Use this procedure when the user needs a device image upgrade at scale.

Sources:

- Junos Space Network Management Platform Complete Software Guide, Release 21.1, page 81.
- Junos Space Network Management Platform Workspaces User Guide, Release 21.1, pages 471 through 504.

Import the image:

1. Download the device image from the Juniper support site.
2. Select `Images and Scripts > Images`.
3. Click the `Import Image` icon.
4. Click `Browse`.
5. Select the image file.
6. Click `Upload`.
7. Open the job ID or `Jobs > Job Management`.
8. Verify that the image appears on the Images page.

Stage the image:

1. Select `Images and Scripts > Images`.
2. Select the device image.
3. From the Actions menu, select `Stage Image on Device`.
4. Review the device family, platform, software version, staged status, and checksum status.
5. Select devices manually, by tags, or by CSV.
6. Stage the image.
7. Verify the staging job.
8. Select `Verify Image on Devices`.
9. Confirm that `Checksum Status` is `Valid`.

Deploy the image:

1. Select `Images and Scripts > Images`.
2. Select the image to deploy.
3. From the Actions menu, select `Deploy Device Image`.
4. Select devices manually, by tags, or by CSV.
5. If needed, select `Show ISSU/ICU capable devices only`.
6. Choose common deployment options.
7. Choose conventional deployment options when the package uses conventional deployment.
8. Choose ISSU options only for devices and releases that support ISSU.
9. Review the summary.
10. Deploy now or schedule deployment.
11. Open the deployment job.
12. Confirm success for each device.

Warning: image deployment can reload devices or interrupt traffic. Confirm the
maintenance window, target device list, and rollback plan before deployment.

Warning: the deployment fails if the checksum values do not match. Verify the
checksum before you start a large deployment.

At a time, Junos Space can stage only one device image on a device. Staging a
new image replaces the previously staged image. An image that is already staged
reduces deployment time because Junos Space can start installation directly.

## Verify fleet jobs

Use this short check after discovery, resync, template deployment, or image
deployment.

Sources:

- Junos Space Network Management Platform Workspaces User Guide, Release 21.1, pages 96, 307, 355, and 474.

1. Open `Jobs > Job Management`.
2. Find the job ID from the workflow.
3. Double-click the job ID.
4. Review the per-device Description or Result Details field.
5. Export the result when a change record is required.
6. Return to Device Management.
7. Confirm connection status and managed status for the changed devices.

Caution: a green parent job can still hide a device-level warning. Read the
per-device result before you close the change.
