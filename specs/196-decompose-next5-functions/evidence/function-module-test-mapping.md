# Function to Module to Test Mapping: Spec 196

## Target Ownership

| Original Function | Extracted Module | Owner Class | Facade Location | Owner |
| - | - | - | - | - |
| `_start_site_scan_capture_all_aps` | `src/capture/multi_ap_scan_workflow.py` | `MultiApScanCaptureWorkflow` | `MistHelper.py` | Packet-capture compatibility facade (`_LegacyPacketCaptureManager`) |
| `_wait_and_download_pcap` | `src/capture/site_pcap_wait_download_workflow.py` | `SitePcapWaitDownloadWorkflow` | `MistHelper.py` | Packet-capture compatibility facade (`_LegacyPacketCaptureManager`) |
| `_wait_and_download_pcap_org` | `src/capture/org_pcap_wait_download_workflow.py` | `OrgPcapWaitDownloadWorkflow` | `MistHelper.py` | Packet-capture compatibility facade (`_LegacyPacketCaptureManager`) |
| `wifi_clients` | `src/export/wifi_clients_exporter.py` | `WifiClientsExporter` | `MistHelper.py` | Site client export compatibility facade (`SiteClientExporter`) |
| `run_interactive_test` | `src/troubleshooting/interactive_test_runner.py` | `InteractiveTestRunner` | `MistHelper.py` | Interactive test compatibility facade (module-level entrypoint) |

## Test Coverage Mapping

| Target Function | Unit Tests | Integration Tests | Safety/Failure Coverage |
| - | - | - | - |
| `_start_site_scan_capture_all_aps` | `tests/unit/capture/test_multi_ap_scan_workflow.py` | `tests/integration/test_next5_compatibility_paths.py` | multi-AP early-exit + launch path assertions |
| `_wait_and_download_pcap` | `tests/unit/capture/test_site_pcap_wait_download_workflow.py` | `tests/integration/test_next5_compatibility_paths.py` | wait/download delegation path exercised with callback assertions |
| `_wait_and_download_pcap_org` | `tests/unit/capture/test_org_pcap_wait_download_workflow.py` | `tests/integration/test_next5_compatibility_paths.py` | org wait/download delegation path exercised with callback assertions |
| `wifi_clients` | `tests/unit/export/test_wifi_clients_exporter.py` | `tests/integration/test_next5_compatibility_paths.py` | no-site safe exit and merged session/client export path |
| `run_interactive_test` | `tests/unit/troubleshooting/test_interactive_test_runner.py` | `tests/integration/test_next5_compatibility_paths.py` | interactive-safe execution and site resolution path |

## Parity Coverage Summary

- Compatibility entrypoints preserved in `MistHelper.py` and exercised by `tests/integration/test_next5_compatibility_paths.py`.
- Extracted modules are directly unit-tested for delegated behavior and safe no-op/error paths.
- Broader packet-capture and runtime-coupling regressions executed to confirm no cross-module breakage.
