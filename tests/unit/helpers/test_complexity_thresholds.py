"""Complexity threshold parser tests for spec-196 evidence enforcement."""

from __future__ import annotations

import re


TARGET_NAMES = {
    "_start_site_scan_capture_all_aps",
    "_wait_and_download_pcap",
    "_wait_and_download_pcap_org",
    "wifi_clients",
    "run_interactive_test",
}


def parse_target_cc_values(radon_output: str) -> dict[str, int]:
    """Parse CC values for next-five target functions from radon output text."""
    pattern = re.compile(r"F\s+\d+:0\s+([a-zA-Z0-9_]+)\s+-\s+[A-Z]\s+\((\d+)\)")
    parsed = {}
    for match in pattern.finditer(radon_output):
        function_name = match.group(1)
        complexity_value = int(match.group(2))
        if function_name in TARGET_NAMES:
            parsed[function_name] = complexity_value
    return parsed


def test_parse_target_cc_values_extracts_known_targets() -> None:
    """Parser should collect CC values for next-five target function lines."""
    sample = "\n".join(
        [
            "F 7094:0 _start_site_scan_capture_all_aps - C (16)",
            "F 8223:0 _wait_and_download_pcap - C (15)",
            "F 8397:0 _wait_and_download_pcap_org - C (15)",
            "F 16092:0 wifi_clients - C (14)",
            "F 28046:0 run_interactive_test - C (13)",
        ]
    )
    parsed = parse_target_cc_values(sample)
    assert parsed["_start_site_scan_capture_all_aps"] == 16
    assert parsed["_wait_and_download_pcap"] == 15
    assert parsed["_wait_and_download_pcap_org"] == 15
    assert parsed["wifi_clients"] == 14
    assert parsed["run_interactive_test"] == 13


def test_parse_target_cc_values_ignores_non_target_entries() -> None:
    """Parser should ignore unrelated function entries."""
    sample = "F 100:0 unrelated_function - B (9)"
    parsed = parse_target_cc_values(sample)
    assert parsed == {}
