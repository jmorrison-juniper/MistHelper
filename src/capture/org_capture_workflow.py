"""Org-level packet capture workflow orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OrgCaptureWorkflow:
    """Coordinate org capture selection and payload creation with delegated manager helpers."""

    manager: Any

    def run(self) -> None:
        """Execute the full org capture workflow with parity-preserving prompts."""
        fetched = self.manager._fetch_org_mxedges()
        if fetched is None:
            return
        mxedges, stats_map = fetched
        selected = self.manager._display_and_select_mxedge(mxedges, stats_map)
        if selected is None:
            return
        selected_ports = self.manager._fetch_and_select_mxedge_port(selected)
        if selected_ports is None:
            return
        tcpdump_expr = self.manager._get_tcpdump_expression_selection()
        params = self.manager._gather_org_capture_params()
        if params is None:
            return
        capture_config = {
            "duration": params[0],
            "num_packets": params[1],
            "max_pkt_len": params[2],
            "format": params[3],
            "tzsp_host": params[4],
            "tzsp_port": params[5],
        }
        payload = self.manager._build_org_payload(selected, selected_ports, tcpdump_expr, capture_config)
        self.manager._display_org_capture_summary(payload, selected, selected_ports, tcpdump_expr)
        self.manager._confirm_and_execute_org_capture(payload)
