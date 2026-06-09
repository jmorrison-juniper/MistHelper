"""Integration guardrails for top-5 decomposition compatibility."""

from MistHelper import (
    GatewayExportUtils,
    OrgAlarmEventExporter,
    _early_dependency_check,
    _LegacyPacketCaptureManager,
)


def test_top5_entrypoints_remain_callable() -> None:
    """Verify decomposed top-5 compatibility entrypoints are still callable."""
    assert callable(_early_dependency_check)
    assert callable(_LegacyPacketCaptureManager._execute_site_capture_loop)
    assert callable(_LegacyPacketCaptureManager.start_org_packet_capture)
    assert callable(OrgAlarmEventExporter.device_events_52w)
    assert callable(GatewayExportUtils.with_wan_overrides)


def test_top5_target_name_matrix_is_fully_mapped() -> None:
    """Ensure the canonical top-5 target list maps to concrete callable entrypoints."""
    top5_target_names = [
        "_early_dependency_check",
        "_execute_site_capture_loop",
        "start_org_packet_capture",
        "device_events_52w",
        "with_wan_overrides",
    ]
    target_mapping = {
        "_early_dependency_check": _early_dependency_check,
        "_execute_site_capture_loop": _LegacyPacketCaptureManager._execute_site_capture_loop,
        "start_org_packet_capture": _LegacyPacketCaptureManager.start_org_packet_capture,
        "device_events_52w": OrgAlarmEventExporter.device_events_52w,
        "with_wan_overrides": GatewayExportUtils.with_wan_overrides,
    }
    assert set(top5_target_names) == set(target_mapping)
    for target_name in top5_target_names:
        assert callable(target_mapping[target_name])
