"""Offline behavior tests for the organization variable count export."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.operations.exporting.export.count_exporter import _ORG_OPS, CountExporter, _CountOp


@pytest.fixture
def fake_mist_helper() -> Any:
    """Return a fake host that records the organization count export."""
    module = MagicMock()  # WHY: the resolver reads several host collaborators.
    module.apisession = MagicMock()  # WHY: the SDK operation needs a session argument.
    return module  # WHY: each test injects the same host contract.


def _count_org_vars() -> _CountOp:
    """Return the registered organization variable count operation."""
    return next(operation for operation in _ORG_OPS if operation.operation == "countOrgVars")


class TestCountOrgVarsExport:
    """Cover selection, output, and refusal handling for countOrgVars."""

    def test_org_counts_exports_the_selected_variable_count(
        self,
        fake_mist_helper: Any,
    ) -> None:
        """The selected countOrgVars operation must call the SDK and write its rows."""
        operation_position = next(  # WHY: the menu selection must target the catalog row.
            position for position, operation in enumerate(_ORG_OPS, start=1) if operation.operation == "countOrgVars"
        )
        fake_mist_helper.InputUtils.safe_input.return_value = str(operation_position)  # WHY: select countOrgVars.
        fake_mist_helper.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-42"  # WHY: choose an org.
        sdk_callable = MagicMock(return_value={"result": [{"count": 3}]})  # WHY: isolate the SDK boundary.
        rows = [{"count": 3}]  # WHY: use a flat response that must reach the writer unchanged.
        with (  # WHY: replace all cloud and host dependencies with local fakes.
            patch(
                "src.operations.exporting.export.count_exporter.SourceDependencyResolver",
                fake_mist_helper,
            ),
            patch.object(CountExporter, "_resolve", return_value=sdk_callable),
            patch(
                "src.operations.exporting.export.count_exporter.mistapi.get_all",
                return_value=rows,
            ),
        ):
            CountExporter.org_counts()  # WHY: exercise the real prompt, SDK, and output flow.
        sdk_callable.assert_called_once_with(fake_mist_helper.apisession, "org-42")  # WHY: verify endpoint inputs.
        fake_mist_helper.DataExporter.write_with_format_selection.assert_called_once_with(
            rows,
            "countOrgVars_org-42.csv",
            api_function_name="countOrgVars",
        )  # WHY: verify exported data, filename, and endpoint identity.

    @pytest.mark.parametrize("status_code", [404, 503])
    def test_run_logs_http_refusals_without_writing(
        self,
        fake_mist_helper: Any,
        caplog: pytest.LogCaptureFixture,
        status_code: int,
    ) -> None:
        """An HTTP 4xx or 5xx response must be logged and must not produce output."""
        operation = _count_org_vars()  # WHY: target the new SDK operation.
        sdk_callable = MagicMock(side_effect=requests.HTTPError(f"HTTP {status_code}"))  # WHY: model an HTTP refusal.
        with (
            patch(
                "src.operations.exporting.export.count_exporter.SourceDependencyResolver",
                fake_mist_helper,
            ),
            patch.object(CountExporter, "_resolve", return_value=sdk_callable),
            caplog.at_level("ERROR"),
        ):
            CountExporter._run(operation, "org-42", "org-42")  # WHY: drive the existing failure handler.
        assert f"HTTP {status_code}" in caplog.text  # WHY: preserve the refusal status in operator logs.
        assert fake_mist_helper.DataExporter.write_with_format_selection.call_count == 0  # WHY: reject failed output.
