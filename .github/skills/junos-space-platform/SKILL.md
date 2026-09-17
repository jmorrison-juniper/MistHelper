---
name: junos-space-platform
description: >-
  Use when a user asks how to install, upgrade, back up, restore, operate,
  automate, or troubleshoot Junos Space Network Management Platform, Network
  Director, or Connectivity Services Director. Use for the fabric, database,
  roles, device discovery, device adoption, connection status, resync,
  configuration templates, bulk configuration deployment, image staging, image
  upgrade, topology, faults, performance, service orders, and REST API access.
  Require a cited Juniper source and a release for each procedure.
argument-hint: State the Junos Space release, application, task, device family, and whether the task changes many devices.
---

# Manage a Junos Space platform

Use this skill when a request concerns Junos Space Network Management Platform
or an application that runs on it. The applications in this skill are Network
Director and Connectivity Services Director.

This skill does not authorize a live change. A live fabric change, database
restore, mass configuration deployment, or device image upgrade needs the
normal MistHelper issue, review, and typed confirmation process.

The verified snapshot date is 2026-09-17. The staged manifest holds 163
documents and 87,652 pages. This skill indexes 8 source documents. Those
documents cover the subject without copying repeated older releases.

## 1. Decide whether this skill applies

Use this skill for these requests:

- Install or configure a Junos Space fabric node.
- Add a node to a Junos Space fabric.
- Upgrade Junos Space Network Management Platform.
- Back up or restore the Junos Space platform database.
- Plan user roles, domains, user sessions, or API access profiles.
- Discover devices, adopt devices, check connection status, or resync devices.
- Create or deploy a device template or a quick template.
- Import, stage, verify, deploy, or remove a device image.
- Use Network Director topology, fault, monitor, or deploy modes.
- Use Connectivity Services Director service views or service orders.
- Use a Junos Space, Network Director, or Connectivity Services Director REST API.

Do not use this skill for these requests:

- A live Mist API request. Use `managing-mist-api` for that task.
- A Junos device hardening command. Use `hardening-junos` for that task.
- Fiber, Observium, or Podman work.
- A Python speed change. Use `optimizing-python` for that task.

## 2. Load one reference

Read only the reference that the question needs.

| Task | Reference | Result |
| - | - | - |
| Choose a source, cite it, or search the staged corpus. | [Verification](./references/verification.md) | A source document, release, page, and path from the corpus index. |
| Install, expand, upgrade, back up, restore, or assign roles. | [Platform administration](./references/platform-administration.md) | A fabric, database, or role procedure with a warning. |
| Discover devices, resync devices, deploy configuration, or upgrade images. | [Fleet operations](./references/fleet-operations.md) | A device, template, or image procedure that can affect many devices. |
| Use Network Director, Connectivity Services Director, or an API. | [Director applications and API](./references/director-applications-and-api.md) | A mode, service, deployment, monitoring, or REST workflow. |
| Check the selected corpus rows. | [Corpus index](./references/corpus-index.csv) | A list of verified source documents and relative corpus paths. |

If two sources conflict, use this order:

1. The newest user guide for the product and task.
2. The newest API reference for the API task.
3. A complete software guide when the user guide does not hold the overview.
4. A release note only when it changes the procedure for the target release.
5. An older guide only when the newest guide does not cover the feature.

## 3. Warn before harm

Warning: a fabric change can interrupt the platform that manages the whole
fleet. Confirm the maintenance window and the recovery plan before you act.

Warning: a database restore puts all Junos Space nodes into maintenance mode.
All users except the maintenance administrator lose access during the restore.

Warning: a mass configuration deployment can change many devices at once. Review
the pending configuration and validate it before you deploy it.

Warning: a device image deployment can reload devices or interrupt traffic. Use
a staged image, verify the checksum, and confirm the target list first.

Warning: a negative quick template can delete device configuration. Read the
`DELETE` commands and the target device list before you deploy it.

## 4. Build the answer

Every answer must hold these parts:

1. State the Junos Space product and release.
2. State the workspace, mode, or REST root that the task uses.
3. State whether the action affects one device, many devices, or the fabric.
4. Give the shortest confirmed procedure that solves the task.
5. Cite the source document, release, and page for each procedure.
6. State any role requirement, credential requirement, or port requirement.
7. State the verification step that proves the action finished.

Use obvious placeholders in examples. Use `device.example.invalid`, `192.0.2.10`,
`REPLACE_WITH_USER`, and `REPLACE_WITH_TOKEN`. Do not use a real hostname,
address, credential, serial number, or customer name.

## 5. Use the corpus index

The corpus root is `C:\Users\jmorrison\Downloads\juniper-doc-archives\`.
The repository holds no Juniper document.

Use this procedure when the curated reference does not give enough detail.

1. Open [Corpus index](./references/corpus-index.csv).
2. Find the row for the product, topic, or file name.
3. Build the source path below the corpus root.
4. Open the Markdown file under the corpus root.
5. Search for the task heading.
6. Confirm that the page marker supports the page number.
7. Quote only the needed words when the exact vendor term matters.
8. Cite the document title, release, and page.

Caution: if the staged corpus is absent, the reader cannot verify the source.
State that the corpus is absent. Then answer only from the curated references.

## 6. Apply the product safety rules

Use these safety rules in each procedure:

- Require the `System Administrator` role for platform database backup or restore.
- Require the maintenance administrator credentials for maintenance mode tasks.
- Confirm that all Junos Space nodes use synchronized time before a platform upgrade.
- Confirm the device target list before discovery, template deployment, or image deployment.
- Confirm that device connection status is `Up` and managed status is `In Sync` before a deployment.
- Confirm that the image checksum status is `Valid` before an image deployment.
- Use API access profiles for RPC calls that use `exec-rpc`.

## 7. Answer common requests fast

Use these routes for common questions:

- Fabric node setup: read [Platform administration](./references/platform-administration.md#deploy-a-fabric-node).
- Platform upgrade: read [Platform administration](./references/platform-administration.md#upgrade-the-platform).
- Database backup or restore: read [Platform administration](./references/platform-administration.md#back-up-and-restore-the-database).
- Device discovery: read [Fleet operations](./references/fleet-operations.md#discover-devices).
- Device status or resync: read [Fleet operations](./references/fleet-operations.md#check-status-and-resync-a-device).
- Template deployment: read [Fleet operations](./references/fleet-operations.md#deploy-configuration-with-templates).
- Image staging and upgrade: read [Fleet operations](./references/fleet-operations.md#stage-and-deploy-device-images).
- Network Director topology: read [Director applications and API](./references/director-applications-and-api.md#use-network-director-topology-view).
- Network Director fault or performance view: read [Director applications and API](./references/director-applications-and-api.md#use-network-director-fault-and-monitor-views).
- Connectivity Services Director: read [Director applications and API](./references/director-applications-and-api.md#use-connectivity-services-director).
- REST API workflow: read [Director applications and API](./references/director-applications-and-api.md#use-rest-apis).

## 8. Report evidence

End each answer with an evidence block.

```text
Evidence:
- Junos Space: <title>, Release <release>, page <page> -- <claim>
- Repository: .github/skills/junos-space-platform/<file> -- <curated rule>
- Unverified: <claim> -- <missing source or next check>
```

If the user asks you to execute a live change, do not rely on this skill alone.
Use the repository workflow, tests, and human review rules before you change a
production management platform.
