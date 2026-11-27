# Contract: Optional Lookups

## Rule

An optional lookup reads site names only to enrich output. Its failure must not stop the output. Each optional lookup follows these rules:

1. Catch only `APIFetchError`. Do not catch `Exception`, except where the row below names a broad catch that already exists.
2. Log exactly one warning line on failure. The line names the operation, the org ID, and the cause.
3. Keep the empty lookup or the fallback value named in the table.
4. Continue the operation.
5. Do not change the output when the read succeeds.

## Warning Template

Use this template for each optional lookup. Replace the `%s` fields with the operation, the org ID, and the cause at run time. Keep the text in ASCII.

`Optional site lookup failed in %s for org %s. Cause: %s. Continuing without site names.`

## Optional Lookups

| Caller | Location | Fallback after a failure | Source |
| - | - | - | - |
| `SiteNameLookup.fetch` | `src/mist/intelligence/reports/switch_scorecard/site_lookup.py` line 23 | Returns an empty dictionary. The three scorecards use it (rows R11 to R13). | R10 |
| Offline device report | `src/mist/intelligence/reports/offline_device_reporter.py` line 107 | Empty site lookup. Device rows show `Unknown Site` (row R15). The device statistics still load. | R14, R15 |
| Site device statistics name | `src/operations/exporting/export/site_device_exporter.py` line 141 | The site ID is the site name (row R17). The export continues. | R16, R17 |
| AP model export sites | `src/operations/exporting/export/sites_by_ap_model_exporter.py` line 173 | Empty site map (row R19). Each AP row keeps its site ID and leaves the site detail fields empty. The AP inventory read still raises. | R18, R19 |
| Devices site lookup | `src/operations/exporting/export/org_inventory_exporter.py` line 509, through the cache-miss path (line 530) and the non-fast path (line 557) | Empty site lookup inside `_build_site_lookup_from_api`. Device rows show the fallback `Unknown` (row R25). The inventory read still raises. | R21, R22, R23, R25 |
| Gateways site lookup | `src/operations/exporting/export/org_inventory_exporter.py` line 688 | `gateways_with_site_info` calls `_build_site_lookup_from_api`. Gateway rows show the fallback `Unknown` (row R26). The inventory read still raises. | R24, R26 |
| MSP site lookup | `src/operations/exporting/export/msp_inventory_exporter.py` line 358 | Empty lookup. The broad catch stays. The failure logs at warning level (rows R27 and R28). | R27, R28 |
| Prompt site cache | `src/interfaces/visualization/ui/prompt_utils.py` line 394 | Empty dictionary, from the existing `RuntimeError` catch (row R31). The existing warning stays. No code changes. | R30, R31, R32 |
| Firmware site lookup | `src/operations/execution/firmware/firmware_manager.py` line 3542 | The lookup clears. The existing warning at row R41 stays. No code changes. | R40, R41 |
| CSV generator in the fast path | `src/foundation/persistence/cache/cache_utils.py` line 103 | The generator failure returns `False`. The export then uses the optional lookup. No code changes. | R65 |

## Credential Rule

No warning contains a credential, a token, or a password. The warning carries the operation name, the org ID, and the cause only. Test I-13 checks this rule.
