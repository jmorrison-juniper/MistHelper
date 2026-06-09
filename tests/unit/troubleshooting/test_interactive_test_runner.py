"""Unit tests for src.troubleshooting.interactive_test_runner."""

from __future__ import annotations

from unittest.mock import MagicMock

from src.troubleshooting.interactive_test_runner import InteractiveTestRunner


class _TelemetryStub:
    """Minimal telemetry stub for deterministic runner tests."""

    def __init__(self, _path: str) -> None:
        self.events = []

    @staticmethod
    def timestamped_path(_directory: str) -> str:
        return "data/test_events_stub.jsonl"

    def emit_test_skip(self, *args) -> None:
        self.events.append(("skip", args))

    def emit_test_start(self, *args) -> None:
        self.events.append(("start", args))

    def emit_test_pass(self, *args) -> None:
        self.events.append(("pass", args))

    def emit_test_fail(self, *args) -> None:
        self.events.append(("fail", args))

    def emit_test_summary(self, *args) -> None:
        self.events.append(("summary", args))

    def close(self) -> None:
        return None

    def enforce_retention(self) -> None:
        return None


class _OperationRegistryStub:
    """Operation registry stub exposing one interactive-safe option."""

    @staticmethod
    def interactive_safe_options(_all_options):
        return ["1"]

    @staticmethod
    def is_interactive_safe(option):
        return option == "1"

    @staticmethod
    def skip_reason(_option):
        return "skip"

    @staticmethod
    def skip_category(_option):
        return "interactive"


def test_execute_runs_interactive_option_successfully() -> None:
    """Runner should execute interactive-safe callable and return True on success."""
    called = {"value": False}

    def _option(site_id=None):
        called["value"] = site_id == "site-1"

    menu_actions = {"1": (_option, "Option One")}
    mistapi_module = MagicMock()
    site_response = MagicMock()
    site_response.data = [{"id": "site-1", "name": "Site One"}]
    mistapi_module.api.v1.orgs.sites.listOrgSites.return_value = site_response

    runner = InteractiveTestRunner(
        menu_actions=menu_actions,
        operation_registry=_OperationRegistryStub,
        telemetry_emitter_cls=_TelemetryStub,
        config_utils=MagicMock(),
        mistapi_module=mistapi_module,
        apisession=MagicMock(),
        org_id_getter=lambda: "org-1",
        org_id_setter=lambda _value: None,
    )

    result = runner.execute()

    assert result is True
    assert called["value"] is True
