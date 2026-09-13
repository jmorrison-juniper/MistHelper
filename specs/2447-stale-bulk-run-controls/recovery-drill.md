# Recovery Drill Evidence

This record covers tasks T098, T099, and T100.

It records a safe inspection of the backup.

It does not record a restore execution.

Warning: do not restore this backup to production. A live restore can cause the loss of every upgrade run record.

## Backup Location

Backup path: `C:\Users\jmorrison\.copilot\session-state\3dcc9a48-c9ef-438b-bd2f-ba48cd6f77cf\files\arangodb-backup-2447`

The inspection read each structure file and each compressed data file.

No command wrote to ArangoDB during this inspection.

## Backup Contents

| Collection | Records |
| - | -: |
| `alarm_templates` | 0 |
| `AlarmTemplateAssignedToSite` | 0 |
| `AlarmTemplateBelongsToOrg` | 0 |
| `capture_for_run` | 15 |
| `config_snapshots` | 144 |
| `ConfigSnapshotForEntity` | 144 |
| `device_profiles` | 0 |
| `DeviceConnectedToDevice` | 0 |
| `DeviceHasPort` | 0 |
| `devices` | 13 |
| `DeviceUsesProfile` | 0 |
| `events` | 3 |
| `evpn_topologies` | 0 |
| `EvpnBelongsToSite` | 0 |
| `fake_list` | 12 |
| `getOrgInventory` | 13 |
| `getOrgTicket` | 2 |
| `listOrgSites` | 144 |
| `mx_tunnels` | 0 |
| `mxclusters` | 0 |
| `MxEdgeBelongsToCluster` | 0 |
| `MxTunnelUsesCluster` | 0 |
| `nac_portals` | 0 |
| `nac_rules` | 0 |
| `nac_tags` | 0 |
| `NACRuleMatchesSite` | 0 |
| `NACRuleMatchesSiteGroup` | 0 |
| `NACRuleUsesTag` | 0 |
| `NACTagBelongsToPortal` | 0 |
| `NetworkBelongsToOrg` | 0 |
| `networks` | 0 |
| `OrgContainsDevice` | 13 |
| `OrgContainsSite` | 144 |
| `orgDeviceFirmwareSummary` | 20 |
| `orgDeviceModelSummary` | 20 |
| `orgDeviceVersionPerModel` | 20 |
| `orgs` | 2 |
| `ports` | 0 |
| `ProfileAppliedToSite` | 0 |
| `ProfileAppliedToSiteGroup` | 0 |
| `PSKBelongsToSite` | 0 |
| `PSKBelongsToWlan` | 0 |
| `psks` | 0 |
| `searchOrgDeviceEvents` | 3 |
| `searchOrgJsiPbn` | 275 |
| `searchOrgJsiSirt` | 17 |
| `security_policies` | 0 |
| `SecurityPolicyAssignedToSite` | 0 |
| `SecurityPolicyBelongsToOrg` | 0 |
| `ServiceBelongsToOrg` | 0 |
| `ServicePolicyUsesService` | 0 |
| `services` | 0 |
| `SiteBelongsToSiteGroup` | 5 |
| `SiteContainsDevice` | 12 |
| `SiteGroupContainsSite` | 0 |
| `sitegroups` | 3 |
| `sites` | 144 |
| `ssidBroadcastGapReport` | 144 |
| `TemplateAppliedToSite` | 0 |
| `TemplateAppliedToSiteGroup` | 0 |
| `TemplateAssignedToSite` | 288 |
| `templates` | 0 |
| `upgrade_captures` | 26 |
| `upgrade_readiness` | 1 |
| `upgrade_runs` | 60 |
| `VpnBelongsToOrg` | 0 |
| `vpns` | 0 |
| `WlanBelongsToSite` | 0 |
| `wlans` | 0 |
| `WlanUsesMxTunnel` | 0 |
| `WlanUsesTemplate` | 0 |
| `wx_rules` | 0 |
| `wx_tags` | 0 |
| `WxRuleAllowsDstTag` | 0 |
| `WxRuleBelongsToTemplate` | 0 |
| `WxRuleDeniesDstTag` | 0 |
| `WxRuleMatchesSrcTag` | 0 |

## Key Collections

The backup contains `upgrade_runs` with 60 records.

The backup contains `upgrade_captures` with 26 records.

The backup contains `capture_for_run` with 15 edge records.

The backup does not contain `upgrade_run_actions`.

This absence means an isolated restore cannot verify action records from this backup.

## Indexes Read From The Backup

The `upgrade_runs` structure file lists these indexes.

| Name | Fields | Unique |
| - | - | - |
| `idx_upgrade_runs_site_id_created_at` | `site_id, created_at` | false |
| `idx_upgrade_runs_state` | `state` | false |
| `idx_upgrade_runs_actor_email_created_at` | `actor_email, created_at` | false |

The `upgrade_captures` structure file lists these indexes.

| Name | Fields | Unique |
| - | - | - |
| `idx_upgrade_captures_site_id_started_at` | `site_id, started_at` | false |
| `idx_upgrade_captures_run_id_ordinal` | `run_id, ordinal` | false |
| `idx_upgrade_captures_org_id_started_at` | `org_id, started_at` | false |
| `idx_upgrade_captures_actor_email` | `actor_email` | false |

The backup does not include the action composite index.

An operator must verify that index after feature schema creation.

## Sample Records Read From The Backup

### `upgrade_runs`

```json
[
  {
    "_id": "upgrade_runs/run-1fd6a796bac14b7fad49bae6338aa745",
    "_key": "run-1fd6a796bac14b7fad49bae6338aa745",
    "_rev": "_mDal2Dq---",
    "created_at": "2026-08-31T09:28:54.733879+00:00",
    "org_id": "8a1ea872-241a-4c8e-a5ca-2d85674c7229",
    "run_id": "run-1fd6a796bac14b7fad49bae6338aa745",
    "site_id": "cf36153a-97bb-4974-8f8f-e9cc25d64d83",
    "state": "awaiting_confirmation",
    "updated_at": "2026-08-31T09:30:26.243289+00:00"
  },
  {
    "_id": "upgrade_runs/run-5cc9fa45cda44e66864534928760bcb6",
    "_key": "run-5cc9fa45cda44e66864534928760bcb6",
    "_rev": "_mDipdc----",
    "created_at": "2026-08-31T18:52:39.385220+00:00",
    "org_id": "8a1ea872-241a-4c8e-a5ca-2d85674c7229",
    "run_id": "run-5cc9fa45cda44e66864534928760bcb6",
    "site_id": "cf36153a-97bb-4974-8f8f-e9cc25d64d83",
    "state": "awaiting_confirmation",
    "updated_at": "2026-08-31T18:53:37.596529+00:00"
  },
  {
    "_id": "upgrade_runs/run-9c244885a6344171a8b36cc0d54a73db",
    "_key": "run-9c244885a6344171a8b36cc0d54a73db",
    "_rev": "_mD4kOTW---",
    "created_at": "2026-08-31T22:06:08.346500+00:00",
    "org_id": "8a1ea872-241a-4c8e-a5ca-2d85674c7229",
    "run_id": "run-9c244885a6344171a8b36cc0d54a73db",
    "site_id": "cf36153a-97bb-4974-8f8f-e9cc25d64d83",
    "state": "awaiting_confirmation",
    "updated_at": "2026-09-01T20:25:49.116602+00:00"
  }
]
```
### `upgrade_captures`

```json
[
  {
    "_id": "upgrade_captures/cap-bb14061de58045e4995bb2ad8d7a77df-01",
    "_key": "cap-bb14061de58045e4995bb2ad8d7a77df-01",
    "_rev": "_mDajDzS---",
    "capture_id": "cap-bb14061de58045e4995bb2ad8d7a77df-01",
    "org_id": "8a1ea872-241a-4c8e-a5ca-2d85674c7229",
    "run_id": "",
    "site_id": "cf36153a-97bb-4974-8f8f-e9cc25d64d83",
    "state": "verified"
  },
  {
    "_id": "upgrade_captures/cap-314702fc5b2f4cf3b6614de8f4f6487a-01",
    "_key": "cap-314702fc5b2f4cf3b6614de8f4f6487a-01",
    "_rev": "_mDinBAy---",
    "capture_id": "cap-314702fc5b2f4cf3b6614de8f4f6487a-01",
    "org_id": "8a1ea872-241a-4c8e-a5ca-2d85674c7229",
    "run_id": "",
    "site_id": "cf36153a-97bb-4974-8f8f-e9cc25d64d83",
    "state": "verified"
  },
  {
    "_id": "upgrade_captures/cap-a1ad981bfa7f4641b46b16d27f9587b5-01",
    "_key": "cap-a1ad981bfa7f4641b46b16d27f9587b5-01",
    "_rev": "_mDkHvhm---",
    "capture_id": "cap-a1ad981bfa7f4641b46b16d27f9587b5-01",
    "org_id": "8a1ea872-241a-4c8e-a5ca-2d85674c7229",
    "run_id": "",
    "site_id": "cf36153a-97bb-4974-8f8f-e9cc25d64d83",
    "state": "verified"
  }
]
```
### `capture_for_run`

```json
[
  {
    "_id": "capture_for_run/edge-cap-bb14061de58045e4995bb2ad8d7a77df-01",
    "_key": "edge-cap-bb14061de58045e4995bb2ad8d7a77df-01",
    "_rev": "_mDakcs2---"
  },
  {
    "_id": "capture_for_run/edge-cap-314702fc5b2f4cf3b6614de8f4f6487a-01",
    "_key": "edge-cap-314702fc5b2f4cf3b6614de8f4f6487a-01",
    "_rev": "_mDioklq---"
  },
  {
    "_id": "capture_for_run/edge-cap-e1d73623c6a64051a8a0d70bf129ce9d-01",
    "_key": "edge-cap-e1d73623c6a64051a8a0d70bf129ce9d-01",
    "_rev": "_mDlZtd6---"
  }
]
```

## Restore Command For An Isolated Target

Use a disposable ArangoDB instance on a nonproduction port.

Replace the password variable with the isolated target password.

Do not reuse the production endpoint, database, or volume.

```powershell
arangorestore `
  --server.endpoint tcp://127.0.0.1:9530 `
  --server.database misthelper_recovery_2447 `
  --server.username root `
  --server.password "$env:ARANGO_RECOVERY_ROOT_PASSWORD" `
  --input-directory "C:\Users\jmorrison\.copilot\session-state\3dcc9a48-c9ef-438b-bd2f-ba48cd6f77cf\files\arangodb-backup-2447" `
  --create-database true `
  --overwrite true
```

Caution: run the command only against the isolated endpoint. The command can replace collections in its target database.

## Restore Verification Steps

Run these checks only on the isolated target.

1. Count each restored collection and compare it with the table above.

2. Verify that `upgrade_runs` has 60 records.

3. Verify that each sampled `_key` exists after restore.

4. Verify the three `upgrade_runs` indexes from this record.

5. Verify the four `upgrade_captures` indexes from this record.

6. Verify that sample run records keep `_key`, `run_id`, and `state`.

7. Verify sample capture records keep `_key`, `capture_id`, and `state`.

8. After schema creation, verify `upgrade_run_actions` and its actor indexes.

9. After action records exist, verify sample action records link to `upgrade_runs`.

10. Confirm that no restore command targets the production database.

## Retention Rule

The first release retains each action record while its referenced run record exists.

The feature installs no automatic cleanup for action records.

This rule comes from `spec.md`, `data-model.md`, and `research.md`.

## Verified And Pending Steps

Verified by inspection:

- The backup folder exists at the recorded path.

- Each structure file has a matching data file.

- The record counts in the table come from the compressed data files.

- The run and capture index lists come from the structure files.

- Sample records were read from the compressed data files.

- The backup does not contain `upgrade_run_actions`.


Pending operator steps:

- Restore the backup to an isolated ArangoDB target.

- Compare restored counts with the measured counts.

- Verify restored keys, indexes, and sample records.

- Verify action collection indexes after feature schema creation.

- Verify linked action records after an isolated target contains actions.

