"""Shared parity fixtures for spec-196 next-five workflow compatibility tests."""

from __future__ import annotations

NEXT5_TARGET_FUNCTIONS = [
    "_start_site_scan_capture_all_aps",
    "_wait_and_download_pcap",
    "_wait_and_download_pcap_org",
    "wifi_clients",
    "run_interactive_test",
]

NEXT5_TARGET_TO_MODULE = {
    "_start_site_scan_capture_all_aps": "src.capture.multi_ap_scan_workflow.MultiApScanCaptureWorkflow",
    "_wait_and_download_pcap": "src.capture.site_pcap_wait_download_workflow.SitePcapWaitDownloadWorkflow",
    "_wait_and_download_pcap_org": "src.capture.org_pcap_wait_download_workflow.OrgPcapWaitDownloadWorkflow",
    "wifi_clients": "src.export.wifi_clients_exporter.WifiClientsExporter",
    "run_interactive_test": "src.troubleshooting.interactive_test_runner.InteractiveTestRunner",
}
