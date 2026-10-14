# Organization auto-upgrade policy: Menu 305

Menu 305 saves organization firmware versions by model and removes every supported local site override.
It does not send a firmware upgrade, reboot, or device-push request.

Warning: enabled policies can cause later cloud-managed upgrades. These upgrades can interrupt network service.

## Supported policy types

| Device type | Organization setting | Schedule |
| - | - | - |
| Access point | `auto_upgrade` | Day and time, in each site's time zone |
| Switch | `switch.auto_upgrade` | No schedule field |
| SSR | `ssr.auto_upgrade` | No schedule field. Applies at initial device onboarding |
| SRX | `juniper_srx.auto_upgrade` | No schedule field. Applies at initial device onboarding |

Choose each model version from the available firmware list.
An MSP run offers only model versions available in every selected organization.
SSR model choices come from gateway inventory because the SSR version list has no model field.
The operation does not invent a version when the API provides none.

## CLI workflow

1. Select menu 305, or run `python MistHelper.py --menu 305 --dry-run`.
2. Select the current organization or use the existing MSP organization selectors.
3. Select the device types and models to configure.
4. Select one available version for each selected model.
5. Type `ENABLE` or `DISABLE` for each selected policy.
6. For access points, enter a day and `HH:MM` time, or explicitly enter `any`.
7. Review every organization, every site, and the selected policies.
8. To apply the displayed settings, type `CONFIGURE`.

A blank answer, EOF, interrupt, or another confirmation word cancels without a settings write.
A dry run creates no backup file and sends no settings write.
Menu 168 remains unchanged.

## Operations portal

The numbered-menu portal on port 8055 contains a link named `305: Organization auto-upgrade policy`.
The link opens a dedicated graphical workflow. The generic read-only operation runner continues to reject destructive menus.

Select the organization scope and device types, then load the available model versions.
Dynamic controls show model choices, version choices, enabled state, and the AP schedule.
Select `Preview / dry run` to read complete settings and review every target.
The preview changes no settings and creates no backup.

To apply the displayed plan, type `CONFIGURE`, then select `Verify all backups and apply settings`.
Changing any selection invalidates the preview. A preview expires after ten minutes.
The server refuses another browser's preview and refuses a second apply request for the same preview.
Portal requests retain the existing CSRF and address access controls.

## Complete settings backups

Before the first settings write, the operation saves complete settings for every selected organization and every target site.
One unique JSON bundle contains all original settings, scope identifiers, a UTC timestamp, a record count, and a SHA-256 checksum.
The operation reads the file again and compares every original record and its checksum.
If any backup cannot be written or verified, the operation sends zero settings writes.

Backups remain under `data/.firmware-policy-backups/`.
The operation never overwrites an earlier backup.
POSIX directories use mode `0700`, and files use mode `0600`.
On Windows, use a private account-controlled `data/` directory because Windows manages access through inherited permissions.

Warning: full settings backups can contain credentials. Do not share them or commit them.

The portal excludes backups from file listing, preview, download, and output discovery.
Backup contents never enter browser responses or logs.
Retain a backup until you verify the final cloud settings.
This operation does not automatically restore a backup.

## Apply order and failure results

The operation checks that current settings still match the preview before creating backups.
It checks settings again before each write.
It saves and verifies each organization policy before removing that organization's site overrides.
It removes AP, switch, SSR, and SRX local overrides, including policy types not selected for organization changes.
Unselected organization policies remain unchanged.
Every replaced nested object retains its unrelated sibling settings.

The operation reads each changed setting again.
It requires selected organization values to match and site overrides to be absent.
Server-generated `modified_time` values can change after a settings write.

If a write or verification fails, the operation stops and reports partial completion.
The report separates verified organization changes, verified site changes, unchanged sites, failures, and remaining sites.
Saved changes can remain after a partial failure. The operation does not issue automatic retries or rollback writes.

## API contract

The SDK uses `getOrgSettings`, `updateOrgSettings`, `getSiteSetting`, and `updateSiteSettings`.
AP inheritance uses the Mist unset marker `"-auto_upgrade": ""`.
Nested policies are removed by replacing their complete parent object without the `auto_upgrade` member.

See the [menu API map](menu-api/README.md) for endpoint references.
Feature tests use mocked SDK transport and no production credential.
