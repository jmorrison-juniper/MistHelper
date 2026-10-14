# Settings Contract

## Menu

Menu 305 is `DESTRUCTIVE: Organization Auto-Upgrade Policy`.
It supports single-organization and MSP multi-organization selection.
The operation affects every site in each selected organization.
It is not exposed as a safe portal operation or included in test sweeps.
A dedicated graphical workflow on port 8055 provides dynamic selectors, preview, confirmation, and results.

## Permitted mutations

Only these SDK writes are permitted:

- `mistapi.api.v1.orgs.setting.updateOrgSettings(session, org_id, body=body)`
- `mistapi.api.v1.sites.setting.updateSiteSettings(session, site_id, body=body)`

No firmware upgrade, scheduled upgrade, reboot, or device update endpoint may be called.
An enabled saved policy can cause a later cloud-managed upgrade. State this before confirmation.

## Organization body

AP: `auto_upgrade` contains the explicit enabled state, `version="custom"`, `custom_versions`, and the AP schedule.
Switch: `switch.auto_upgrade` contains the explicit enabled state, `custom_versions`, and retained snapshot controls.
SSR: `ssr.auto_upgrade` contains the explicit enabled state and `custom_versions`.
SRX: `juniper_srx.auto_upgrade` contains the explicit enabled state, `custom_versions`, and retained snapshot controls.
Preserve each named parent object's unrelated members.

## Site body

When the AP override exists, use `"-auto_upgrade": ""`.
When a nested override exists, send its complete parent object without the `auto_upgrade` member.
Do not send unrelated top-level fields or erase sibling fields.

## Confirmation

Require the exact word `CONFIGURE`. Blank input, yes/no, EOF, interrupt, and another word all cancel.
Dry run does not require confirmation because it performs no writes.

## Verification

Check response status and shape for every request.
Read the changed settings again. Verify selected model values and supported schedule fields.
Verify site overrides are absent and preserved siblings remain unchanged.
Reject any write result that cannot be verified.

## Failures and secrets

HTTP 4xx and 5xx results fail visibly with endpoint action, scope identifier, and status code.
Do not print an API body or exception string that can contain a credential.
Fail before writes when required reads are missing or malformed.
Keep full settings in memory and in private local backups only.
Do not expose backup content through portal data routes.

## Backup gate

Write all selected organization settings and every target site's settings before any Mist change.
Read each backup again and compare the parsed settings, record count, identifier, and content checksum.
Use exclusive file creation. Never replace an earlier backup.
Restrict directory and file permissions where the platform supports POSIX permissions.
If any backup cannot be verified, stop with zero settings writes.
Dry run creates no backup because it makes no settings change.
