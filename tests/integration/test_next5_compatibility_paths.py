"""Integration guardrails for next-five decomposition compatibility."""

from __future__ import annotations

from MistHelper import PacketCaptureManager, SiteClientExporter, run_interactive_test
from tests.fixtures.next5_parity_baseline import NEXT5_TARGET_FUNCTIONS
from tests.integration.helpers.compatibility_assertions import (
    assert_callable_entrypoint,
    assert_target_mapping_complete,
)


def test_next5_entrypoints_remain_callable() -> None:
    """Verify next-five compatibility entrypoints remain callable from legacy module."""
    assert_callable_entrypoint(
        PacketCaptureManager._start_site_scan_capture_all_aps,
        "_start_site_scan_capture_all_aps",
    )
    assert_callable_entrypoint(PacketCaptureManager._wait_and_download_pcap, "_wait_and_download_pcap")
    assert_callable_entrypoint(PacketCaptureManager._wait_and_download_pcap_org, "_wait_and_download_pcap_org")
    assert_callable_entrypoint(SiteClientExporter.wifi_clients, "wifi_clients")
    assert_callable_entrypoint(run_interactive_test, "run_interactive_test")


def test_next5_target_name_matrix_is_fully_mapped() -> None:
    """Ensure required target names are represented by callable compatibility entrypoints."""
    target_mapping = {
        "_start_site_scan_capture_all_aps": PacketCaptureManager._start_site_scan_capture_all_aps,
        "_wait_and_download_pcap": PacketCaptureManager._wait_and_download_pcap,
        "_wait_and_download_pcap_org": PacketCaptureManager._wait_and_download_pcap_org,
        "wifi_clients": SiteClientExporter.wifi_clients,
        "run_interactive_test": run_interactive_test,
    }
    assert_target_mapping_complete(NEXT5_TARGET_FUNCTIONS, target_mapping)
