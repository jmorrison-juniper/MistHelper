"""Parity tests for org packet capture compatibility path."""

from unittest.mock import MagicMock

from src.capture.org_capture_workflow import OrgCaptureWorkflow


def test_org_capture_workflow_calls_confirmation_and_execute() -> None:
    """Workflow drives through selection pipeline and executes confirmation callback."""
    manager = MagicMock()
    manager._fetch_org_mxedges.return_value = ([{"id": "mx-1", "name": "Edge 1"}], {})
    manager._display_and_select_mxedge.return_value = {"id": "mx-1", "name": "Edge 1"}
    manager._fetch_and_select_mxedge_port.return_value = ["eth0"]
    manager._get_tcpdump_expression_selection.return_value = ""
    manager._gather_org_capture_params.return_value = (30, 100, 128, "stream", None, None)
    manager._build_org_payload.return_value = {"type": "mxedge"}
    workflow = OrgCaptureWorkflow(manager=manager)
    workflow.run()
    manager._confirm_and_execute_org_capture.assert_called_once()
