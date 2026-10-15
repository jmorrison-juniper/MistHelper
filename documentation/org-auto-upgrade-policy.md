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
SSR model choices use the supported device-model catalog because the SSR version list has no model field.
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

Open **Operations**, then expand **Firmware Policies & Recovery** and select menu **305**.
The workflow occupies the right workspace beside the left menu.
The generic read-only operation runner continues to reject destructive menus.

Select the organization scope and device types, then load the available model versions.
Organization names appear before identifiers.
Check a supported model to reveal its version selector.
Versions sort by numeric components, highest first, including release and service suffixes.
All four supported hardware classes use the same model controls.
Each hardware group has a bounded scrolling model list. Every supported model remains available.
The AP schedule defaults to every day at `02:00`, in each site's time zone.
You must still select an explicit enabled or disabled state.

Select **Prepare verified backups** to read complete settings and verify every target backup.
Preparation changes no cloud settings. Progress appears below the controls.
The compact scope table sorts by site name and shows backup verification without private settings.
Confirmation appears only after all target backups pass verification.
Type `CONFIGURE`, then select **Apply verified settings plan**.
Changing a selection invalidates the prepared plan.
The portal clears its obsolete summary, verification table, and progress.
Active operations remain valid through request allowance waits.
The server refuses another browser's plan and refuses a second apply request for the same plan.
Workers on the same host share ownership checks and organization write locks through the same private `data/` directory.
Concurrent policy and restoration writes to the same cloud organization are refused.
Refresh the page to recover the operation's status.
Refresh also retains the prepared organization, hardware, version, and schedule choices.
Loading organization choices cannot invalidate a saved operation or replace its terminal status.
After a worker interruption, prepare a new plan. The server never repeats uncertain settings writes automatically.
Portal requests retain the existing CSRF and address access controls.

## Complete settings backups

Before the first settings write, the operation saves complete settings for every selected organization and every target site.
One unique JSON bundle contains all original settings, scope identifiers, a UTC timestamp, a record count, and a SHA-256 checksum.
The operation reads the file again and compares every original record and its checksum.
It also checks that firmware policy restoration accepts every saved policy.
If any backup cannot be written or verified, the operation sends zero settings writes.
If restoration cannot accept a record, preparation fails and confirmation remains hidden.
The portal distinguishes preparation failure from an unavailable status response.
Only a definite preparation failure reports that no settings changed.
See [restoration scope and limits](backup-restoration.md#exact-restoration-scope) for policy recovery rules.
Complete backups do not imply complete historical settings restoration.

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
It saves and verifies organization policies before removing site overrides.
It removes AP, switch, SSR, and SRX local overrides, including policy types not selected for organization changes.
Unselected organization policies remain unchanged.
Every replaced nested object retains its unrelated sibling settings.

The operation reads each changed setting again.
It requires selected organization values to match and site overrides to be absent.
Server-generated `modified_time` values can change after a settings write.

If a write or verification fails, the operation stops and reports partial completion.
The report separates verified organization changes, verified site changes, unchanged sites, failures, and remaining sites.
Saved changes can remain after a partial failure. The operation does not issue automatic retries or rollback writes.

The settings requests use the existing API usage tools and shared request allowance.
A long allowance wait reports an estimate rather than expiring an active operation.

## API contract

The SDK uses `getOrgSettings`, `updateOrgSettings`, `getSiteSetting`, and `updateSiteSettings`.
AP inheritance uses the Mist unset marker `"-auto_upgrade": ""`.
Nested policies are removed by replacing their complete parent object without the `auto_upgrade` member.

See the [menu API map](menu-api/README.md) for endpoint references.
Feature tests use mocked SDK transport and no production credential.
