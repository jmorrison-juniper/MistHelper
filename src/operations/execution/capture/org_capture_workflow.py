"""Org-level packet capture workflow orchestrator."""

from __future__ import annotations  # WHY: postponed annotation evaluation for forward-ref typing

from dataclasses import dataclass  # WHY: dataclass reduces boilerplate for manager binding
from typing import Any  # WHY: manager duck-typed to avoid cyclic import with PacketCaptureManager

_PARAM_DURATION = 0  # WHY: index of duration in the _gather_org_capture_params tuple result
_PARAM_NUM_PACKETS = 1  # WHY: index of packet count in the params tuple
_PARAM_MAX_PKT_LEN = 2  # WHY: index of max packet length in the params tuple
_PARAM_FORMAT = 3  # WHY: index of capture output format in the params tuple
_PARAM_TZSP_HOST = 4  # WHY: index of optional TZSP destination host in the params tuple
_PARAM_TZSP_PORT = 5  # WHY: index of optional TZSP destination port in the params tuple


@dataclass(frozen=True, slots=True)
class OrgCaptureWorkflow:  # WHY: frozen slotted bundle groups manager binding for the workflow
    """Coordinate org capture selection and payload creation with delegated manager helpers."""

    manager: Any  # WHY: PacketCaptureManager-like collaborator supplying prompt + API helpers

    def run(self) -> None:  # WHY: single-entry orchestrator invoked by PacketCaptureManager
        """Execute the full org capture workflow with parity-preserving prompts."""
        selection = self._collect_org_selection()  # WHY: gather mxedge/ports/tcpdump-expr choices upfront
        if selection is None:  # WHY: propagate user-cancel from the selection step
            return  # WHY: user aborted mxedge/port selection or the inventory fetch failed
        capture_config = self._collect_capture_config()  # WHY: gather duration/count/size + TZSP options
        if capture_config is None:  # WHY: propagate user-cancel from parameter prompts
            return  # WHY: user cancelled parameter prompts, abort before dispatching capture
        self._finalize_org_capture(selection, capture_config)  # WHY: build payload + confirm + dispatch

    def _collect_org_selection(self) -> tuple[Any, Any, str] | None:  # WHY: unify selection-prompt sequence
        """Prompt for mxedge, port and tcpdump expression. Return None if the user aborts."""
        fetched = self.manager._fetch_org_mxedges()  # WHY: retrieve org-scope mxedge inventory + stats
        if fetched is None:  # WHY: fetch failed or org has zero edges available
            return None  # WHY: no edges available or inventory fetch failed -> cancel workflow
        mxedges, stats_map = fetched  # WHY: destructure inventory list and per-edge stats mapping
        selected = self.manager._display_and_select_mxedge(mxedges, stats_map)  # WHY: interactive edge picker
        if selected is None:  # WHY: user pressed cancel on the edge picker prompt
            return None  # WHY: user cancelled the mxedge selection prompt
        selected_ports = self.manager._fetch_and_select_mxedge_port(selected)  # WHY: prompt ports on chosen edge
        if selected_ports is None:  # WHY: user pressed cancel on the port picker prompt
            return None  # WHY: user cancelled the port selection prompt
        tcpdump_expr = self.manager._get_tcpdump_expression_selection()  # WHY: optional BPF filter expression
        return selected, selected_ports, tcpdump_expr  # WHY: bundle collected choices for the finalizer

    def _collect_capture_config(self) -> dict[str, Any] | None:  # WHY: normalize params tuple into named dict
        """Gather capture params from the manager and normalize into a config dict."""
        params = self.manager._gather_org_capture_params()  # WHY: prompt duration/count/size/format/tzsp
        if params is None:  # WHY: user pressed cancel during the parameter prompts
            return None  # WHY: user cancelled the params prompts, propagate cancel upward
        return {  # WHY: normalize positional tuple into an explicit named config dict for build_payload
            "duration": params[_PARAM_DURATION],
            "num_packets": params[_PARAM_NUM_PACKETS],
            "max_pkt_len": params[_PARAM_MAX_PKT_LEN],
            "format": params[_PARAM_FORMAT],
            "tzsp_host": params[_PARAM_TZSP_HOST],
            "tzsp_port": params[_PARAM_TZSP_PORT],
        }

    def _finalize_org_capture(  # WHY: split terminal payload-build+confirm step out of run for STRUCT-LENGTH
        self,
        selection: tuple[Any, Any, str],
        capture_config: dict[str, Any],
    ) -> None:
        """Build the payload, print the summary and confirm+execute the org capture."""
        selected, selected_ports, tcpdump_expr = selection  # WHY: unpack bundle produced by selection step
        payload = self.manager._build_org_payload(  # WHY: construct API request payload from selection + config
            selected, selected_ports, tcpdump_expr, capture_config
        )
        self.manager._display_org_capture_summary(  # WHY: show final choices to user before dispatch
            payload, selected, selected_ports, tcpdump_expr
        )
        self.manager._confirm_and_execute_org_capture(payload)  # WHY: gate + dispatch capture request
