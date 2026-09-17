# Success Report Triage for Issue #2751

The parent inventory reports 582 success-report candidates. This slice read 32 candidate messages across 17 files.

## Counts

| Shape | Count |
|-------|-------|
| Correct announcement | 9 |
| Premature success claim | 2 |
| Correct completion report | 21 |

## Candidate Table

| File | Candidate | Shape | Decision |
|------|-----------|-------|----------|
| `src\refactors\wanprobe_config_manager.py` | `Menu #166 DESTRUCTIVE: Configure WAN Probe Override operation started` | Correct announcement | Keep. It announces the destructive workflow before work starts. |
| `src\refactors\wanprobe_config_manager.py` | `Template %s: Updated %s probe config` | Premature success claim | Change to `Template %s: Prepared %s probe config for API update`. The API write has not run yet. |
| `src\refactors\wanprobe_config_manager.py` | `Successfully updated template %s` | Correct completion report | Keep. It appears only after HTTP 200 from `updateOrgGatewayTemplate`. |
| `src\gateway\wan_probe_device_override_manager.py` | `Menu #167 DESTRUCTIVE: Configure WAN Probe on Device Port Overrides started` | Correct announcement | Keep. It announces the destructive workflow before work starts. |
| `src\gateway\wan_probe_device_override_manager.py` | `Device %s: Updated %s probe config` | Premature success claim | Change to `Device %s: Prepared %s probe config for API update`. The API write has not run yet. |
| `src\gateway\wan_probe_device_override_manager.py` | `Successfully updated device %s` | Correct completion report | Keep. It appears only after HTTP 200 from `updateSiteDevice`. |
| `src\gateway\wan_probe_device_override_manager.py` | `Menu #167 DESTRUCTIVE operation complete: %s devices updated` | Correct completion report | Keep. It summarizes result objects after the write loop. |
| `src\site\site_config_manager.py` | `Menu #171 DESTRUCTIVE: Create test sites from CSV operation started` | Correct announcement | Keep. It announces the create-site workflow before the confirmation gate. |
| `src\site\site_config_manager.py` | `Menu #171 complete: %s sites created, %s failed` | Correct completion report | Keep. It appears after create attempts and reports both buckets. |
| `src\site\site_config_manager.py` | `Menu #172 DESTRUCTIVE: Create country RF templates operation started` | Correct announcement | Keep. It announces the RF-template workflow before writes. |
| `src\site\site_config_manager.py` | `Menu #172 complete: %s templates created, %s sites assigned, %s failed` | Correct completion report | Keep. It appears after create, assign, and report steps. |
| `src\site\site_config_manager.py` | `Menu #173 DESTRUCTIVE: Create AP model device profiles operation started` | Correct announcement | Keep. It announces the device-profile workflow before writes. |
| `src\site\site_config_manager.py` | `Menu #173 complete: %s profiles created, %s failed` | Correct completion report | Keep. It appears after the creation loop. |
| `src\device\ap_profile_migration_manager.py` | `Menu #207 DESTRUCTIVE: migrate APs started` | Correct announcement | Keep. It announces the migration workflow before prompts and writes. |
| `src\device\ap_profile_migration_manager.py` | `Menu #208 DESTRUCTIVE: revert AP profile migration started` | Correct announcement | Keep. It announces the revert workflow before prompts and writes. |
| `src\firmware\firmware_manager.py` | `Successfully initiated SSR firmware upgrade at %s` | Correct completion report | Keep. It appears after HTTP 200 or HTTP 202 from the upgrade endpoint. |
| `src\upgrade_portal\app\routes\upgrade.py` | `upgrade: upgrade started for run %s with status %s` | Correct completion report | Keep. It evaluates after `start_upgrade` returns. A later issue owns signature failures on this route. |
| `src\upgrade_portal\app\routes\capture.py` | `capture: pre-upgrade capture for run %s completed with result` | Correct completion report | Keep. It appears after the service call returns a capture result. |
| `src\upgrade_portal\app\routes\capture.py` | `capture: started the capture %s of the site %s at tier %s` | Correct completion report | Keep. It appears after the progress record opens and the worker starts. |
| `src\upgrade_portal\runtime\containers.py` | `containers: the container %s started` | Correct completion report | Keep. It appears after the runtime command returns success. |
| `src\upgrade_portal\runtime\dependencies.py` | `preflight: the portal started %s and %s now answers` | Correct completion report | Keep. It appears after the service answers a client. |
| `src\utils\file_path_utils.py` | `Created template file: %s` | Correct completion report | Keep. It appears after the file closes without an exception. |
| `src\export\data_exporter.py` | `File I/O: Successfully wrote %s rows to %s` | Correct completion report | Keep. It appears after the helper writes the CSV without an exception. |
| `src\export\data_exporter.py` | `File I/O: Successfully wrote CSV header to %s` | Correct completion report | Keep. It appears after `writer.writeheader()` returns. |
| `src\org\org_ticket_manager.py` | `Ticket created: id=%s, status=%s` | Correct completion report | Keep. It appears after the create ticket response supplies data. |
| `src\org\org_ticket_manager.py` | `Ticket created successfully!` | Correct completion report | Keep. It appears after the create ticket response supplies data. |
| `src\org\org_ticket_manager.py` | `Menu 189: Ticket creation complete, id=%s` | Correct completion report | Keep. It appears after the ticket summary receives response data. |
| `src\wan_vpn_builder.py` | `VPN '%s' created successfully. ID: %s` | Correct completion report | Keep. It appears after `_create_vpn` returns a VPN record. |
| `src\wan_vpn_builder.py` | `VPN '%s' created with ID %s` | Correct completion report | Keep. It appears after `_create_vpn` returns a VPN record. |
| `src\refactors\wlanradius_timer_manager.py` | `Successfully updated site WLAN %s` | Correct completion report | Keep. It appears after HTTP 200 from `updateSiteWlan`. |
| `src\refactors\wlanradius_timer_manager.py` | `Successfully updated site template WLAN %s in template %s` | Correct completion report | Keep. It appears after HTTP 200 from `updateOrgSiteTemplate`. |
| `src\refactors\wlanradius_timer_manager.py` | `Successfully updated org WLAN %s` | Correct completion report | Keep. It appears after the response reporter sees HTTP 200. |

## Deferred Counts

| Deferred area | Count | Issue |
|---------------|-------|-------|
| Firmware, device, gateway, site, and WAN configuration candidates not repaired here | 99 | #2865 |
| Data, file, database, and export candidates | 114 | #2866 |
| Report, display, runtime, web portal, SSH, WebSocket, and remaining `MistHelper.py` candidates | 367 | #2867 |

The explicit rows in the parent inventory total 563. The `MistHelper.py` section reports 19 additional records. The deferred counts include those 19 records in the report and runtime area.
