"""Tests for issue 1709 exception handler narrowing."""

from __future__ import annotations

import builtins
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from requests.exceptions import ConnectionError, Timeout

import MistHelper


class RaisingFuture:
    """Return one stored exception from ``result`` for import worker tests."""

    def __init__(self, error: BaseException) -> None:
        self.error = error  # Store the planned failure for the future result.

    def result(self) -> tuple[str, bool]:
        raise self.error  # Raise the exact failure so the handler surface is tested.


def test_get_installed_version_catches_package_absence(monkeypatch: pytest.MonkeyPatch) -> None:
    """The metadata reader catches the package-not-found signal and returns the old default."""
    from importlib.metadata import PackageNotFoundError

    monkeypatch.setattr(
        "importlib.metadata.version", MagicMock(side_effect=PackageNotFoundError("missing"))
    )  # Force absence.
    assert MistHelper._get_installed_version("missing") == ""  # Preserve the fail-open package check contract.


def test_get_installed_version_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The metadata reader lets an unexpected metadata defect escape."""
    monkeypatch.setattr("importlib.metadata.version", MagicMock(side_effect=AssertionError("boom")))  # Bad defect.
    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide an unrelated defect.
        MistHelper._get_installed_version("bad")  # Execute the narrowed handler site.


def test_latest_pypi_version_catches_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The PyPI reader catches network failures and returns the old default."""
    requests_stub = SimpleNamespace(get=MagicMock(side_effect=OSError("offline")))  # Simulate an offline host.
    original_import = builtins.__import__  # Keep the real importer for all other modules.

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        return requests_stub if name == "requests" else original_import(name, *args, **kwargs)  # Target requests only.

    monkeypatch.setattr(builtins, "__import__", fake_import)  # Route the deferred requests import to the stub.
    assert MistHelper._get_latest_pypi_version("requests") == ""  # Preserve the latest-unknown contract.


def test_latest_pypi_version_catches_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """The PyPI reader treats a timeout as an unknown latest version."""
    requests_stub = SimpleNamespace(get=MagicMock(side_effect=Timeout("synthetic timeout")))  # Simulate timeout.
    original_import = builtins.__import__  # Keep the real importer for all other modules.

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        return requests_stub if name == "requests" else original_import(name, *args, **kwargs)  # Target requests only.

    monkeypatch.setattr(builtins, "__import__", fake_import)  # Route the deferred requests import to the stub.
    assert MistHelper._get_latest_pypi_version("requests") == ""  # Preserve the latest-unknown contract.
    requests_stub.get.assert_called_once_with(  # Prove the timeout came from the product HTTP call.
        "https://pypi.org/pypi/requests/json",
        timeout=5,
    )


def test_latest_pypi_version_catches_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The PyPI reader treats a connection error as an unknown latest version."""
    requests_stub = SimpleNamespace(get=MagicMock(side_effect=ConnectionError("synthetic connection error")))  # Fail.
    original_import = builtins.__import__  # Keep the real importer for all other modules.

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        return requests_stub if name == "requests" else original_import(name, *args, **kwargs)  # Target requests only.

    monkeypatch.setattr(builtins, "__import__", fake_import)  # Route the deferred requests import to the stub.
    assert MistHelper._get_latest_pypi_version("requests") == ""  # Preserve the latest-unknown contract.
    requests_stub.get.assert_called_once_with(  # Prove the connection error came from the product HTTP call.
        "https://pypi.org/pypi/requests/json",
        timeout=5,
    )


def test_latest_pypi_version_reports_404_status(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The PyPI reader must report a 404 status and return the unknown-version value."""
    response = MagicMock(status_code=404)  # Model a missing package response from PyPI.
    response.raise_for_status.side_effect = OSError("404 not found")  # Force the product failure branch.
    requests_stub = SimpleNamespace(get=MagicMock(return_value=response))  # Stub the deferred requests import.
    original_import = builtins.__import__  # Keep the real importer for all other modules.

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        return requests_stub if name == "requests" else original_import(name, *args, **kwargs)  # Target requests only.

    monkeypatch.setattr(builtins, "__import__", fake_import)  # Route the deferred requests import to the stub.
    caplog.set_level("DEBUG", logger=MistHelper.logger.name)  # Capture the product status log.
    assert MistHelper._get_latest_pypi_version("missing") == ""  # A 404 keeps the latest version unknown.
    requests_stub.get.assert_called_once_with(  # Prove the status came from the product PyPI request.
        "https://pypi.org/pypi/missing/json",
        timeout=5,
    )
    response.json.assert_not_called()  # The product must not parse a 4xx body as a success payload.
    assert "PyPI returned status 404 for missing" in caplog.text  # The log must report the exact status.


def test_latest_pypi_version_catches_empty_json_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """The PyPI reader treats an empty JSON body as an unknown latest version."""
    response = MagicMock(status_code=200)  # Model a successful HTTP response with a bad body.
    response.raise_for_status.return_value = None  # Keep the product on the body-parse path.
    response.json.side_effect = ValueError(b"".decode())  # Model the empty JSON body parse failure.
    requests_stub = SimpleNamespace(get=MagicMock(return_value=response))  # Stub the deferred requests import.
    original_import = builtins.__import__  # Keep the real importer for all other modules.

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        return requests_stub if name == "requests" else original_import(name, *args, **kwargs)  # Target requests only.

    monkeypatch.setattr(builtins, "__import__", fake_import)  # Route the deferred requests import to the stub.
    assert MistHelper._get_latest_pypi_version("requests") == ""  # Preserve the latest-unknown contract.
    requests_stub.get.assert_called_once_with(  # Prove the product PyPI request path ran.
        "https://pypi.org/pypi/requests/json",
        timeout=5,
    )


def test_latest_pypi_version_catches_malformed_json_body(monkeypatch: pytest.MonkeyPatch) -> None:
    """The PyPI reader treats a malformed JSON body as an unknown latest version."""
    response = MagicMock(status_code=200)  # Model a successful HTTP response with a damaged body.
    response.raise_for_status.return_value = None  # Keep the product on the body-parse path.
    response.json.side_effect = ValueError("{not valid JSONDecodeError")  # Model the malformed JSON parse failure.
    requests_stub = SimpleNamespace(get=MagicMock(return_value=response))  # Stub the deferred requests import.
    original_import = builtins.__import__  # Keep the real importer for all other modules.

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        return requests_stub if name == "requests" else original_import(name, *args, **kwargs)  # Target requests only.

    monkeypatch.setattr(builtins, "__import__", fake_import)  # Route the deferred requests import to the stub.
    assert MistHelper._get_latest_pypi_version("requests") == ""  # Preserve the latest-unknown contract.
    requests_stub.get.assert_called_once_with(  # Prove the product PyPI request path ran.
        "https://pypi.org/pypi/requests/json",
        timeout=5,
    )


def test_latest_pypi_version_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The PyPI reader lets an unexpected requests defect escape."""
    requests_stub = SimpleNamespace(get=MagicMock(side_effect=AssertionError("boom")))  # Simulate an unrelated defect.
    original_import = builtins.__import__  # Keep the real importer for all other modules.

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        return requests_stub if name == "requests" else original_import(name, *args, **kwargs)  # Target requests only.

    monkeypatch.setattr(builtins, "__import__", fake_import)  # Route the deferred requests import to the stub.
    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._get_latest_pypi_version("requests")  # Execute the narrowed handler site.


def test_parse_requirements_file_catches_read_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The requirements parser catches file read errors and returns the old default."""
    target = str(tmp_path)  # Use pytest's temporary path, not the real repository tree.
    monkeypatch.setattr(builtins, "open", MagicMock(side_effect=OSError("denied")))  # Simulate an unreadable file.
    assert MistHelper._parse_requirements_file(target) == []  # Preserve the no-packages fallback.


def test_parse_requirements_file_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The requirements parser lets an unexpected parser defect escape."""
    target = str(tmp_path)  # Use pytest's temporary path, not the real repository tree.
    monkeypatch.setattr(builtins, "open", MagicMock(side_effect=AssertionError("boom")))  # Simulate a defect.
    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._parse_requirements_file(target)  # Execute the narrowed handler site.


def test_fallback_load_dotenv_catches_decode_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fallback dotenv loader catches decode failures."""
    error = UnicodeDecodeError("utf-8", b"x", 0, 1, "bad")  # Build the precise file decode failure.
    monkeypatch.setattr(builtins, "open", MagicMock(side_effect=error))  # Simulate a damaged dotenv file.
    MistHelper._fallback_load_dotenv()  # The loader must stay non-fatal during startup.


def test_fallback_load_dotenv_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fallback dotenv loader lets an unexpected parser defect escape."""
    monkeypatch.setattr(builtins, "open", MagicMock(side_effect=AssertionError("boom")))  # Simulate a defect.
    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._fallback_load_dotenv()  # Execute the narrowed handler site.


def test_install_one_dependency_catches_tool_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The dependency installer catches known tool errors and continues the batch."""
    manager = MistHelper.GlobalImportManager()  # Use the real manager to test the method surface.
    monkeypatch.setattr(manager, "_install_package_with_uv", MagicMock(side_effect=OSError("uv")))  # Tool failure.
    assert manager._install_one_dependency("requests", True) is False  # Preserve per-package fail-open behavior.


def test_install_one_dependency_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The dependency installer lets an unexpected defect escape."""
    manager = MistHelper.GlobalImportManager()  # Use the real manager to test the method surface.
    monkeypatch.setattr(manager, "_install_package_with_uv", MagicMock(side_effect=AssertionError("boom")))  # Defect.
    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        manager._install_one_dependency("requests", True)  # Execute the narrowed handler site.


def test_collect_import_result_catches_worker_error() -> None:
    """The import collector catches known worker failures and returns the old default."""
    manager = MistHelper.GlobalImportManager()  # Use the real manager to test the method surface.
    future = RaisingFuture(ImportError("missing"))  # Simulate a dependency import failure in a worker.
    assert manager._collect_import_result(future, {future: ("pkg", None)}, threading.Lock()) is None  # Fail open.


def test_collect_import_result_rejects_unexpected_error() -> None:
    """The import collector lets an unexpected worker defect escape."""
    manager = MistHelper.GlobalImportManager()  # Use the real manager to test the method surface.
    future = RaisingFuture(AssertionError("boom"))  # Simulate an unrelated worker defect.
    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        manager._collect_import_result(future, {future: ("pkg", None)}, threading.Lock())  # Execute handler site.


def test_wire_mistapi_module_catches_runtime_shape_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The mistapi wire step catches expected SDK shape failures."""
    manager = MistHelper.GlobalImportManager()  # Use the real manager to test the method surface.
    manager.imports["mistapi"] = object()  # Provide a placeholder module object.
    monkeypatch.setattr(manager, "_verify_mistapi_api_structure", MagicMock(side_effect=RuntimeError("shape")))  # SDK.
    original_mistapi = getattr(MistHelper, "mistapi", None)  # Preserve the SDK global for later tests.
    try:
        manager._wire_mistapi_module()  # The optional SDK wiring must stay non-fatal.
    finally:
        MistHelper.mistapi = original_mistapi  # Restore the SDK global without monkeypatch finalizer drift.


def test_wire_mistapi_module_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The mistapi wire step lets an unexpected SDK defect escape."""
    manager = MistHelper.GlobalImportManager()  # Use the real manager to test the method surface.
    manager.imports["mistapi"] = object()  # Provide a placeholder module object.
    monkeypatch.setattr(
        manager, "_verify_mistapi_api_structure", MagicMock(side_effect=AssertionError("boom"))
    )  # Defect.
    original_mistapi = getattr(MistHelper, "mistapi", None)  # Preserve the SDK global for later tests.
    try:
        with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
            manager._wire_mistapi_module()  # Execute the narrowed handler site.
    finally:
        MistHelper.mistapi = original_mistapi  # Restore the SDK global without monkeypatch finalizer drift.


def test_org_picker_catches_sdk_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The org picker catches expected SDK picker failures."""
    picker = MagicMock(side_effect=OSError("offline"))  # Simulate a network-backed SDK picker error.
    monkeypatch.setattr(MistHelper, "mistapi", SimpleNamespace(cli=SimpleNamespace(select_org=picker)))  # Stub SDK.
    MistHelper._invoke_mistapi_org_picker_and_apply()  # The login flow must stay controlled.


def test_org_picker_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The org picker lets an unexpected SDK defect escape."""
    picker = MagicMock(side_effect=AssertionError("boom"))  # Simulate an unrelated picker defect.
    monkeypatch.setattr(MistHelper, "mistapi", SimpleNamespace(cli=SimpleNamespace(select_org=picker)))  # Stub SDK.
    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._invoke_mistapi_org_picker_and_apply()  # Execute the narrowed handler site.


def test_check_token_rate_limit_catches_probe_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The token probe catches network failures and marks the token unavailable."""
    requests_stub = SimpleNamespace(get=MagicMock(side_effect=OSError("offline")))  # Simulate an offline host.
    original_import = builtins.__import__  # Keep the real importer for all other modules.

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        return requests_stub if name == "requests" else original_import(name, *args, **kwargs)  # Target requests only.

    monkeypatch.setattr(builtins, "__import__", fake_import)  # Route the deferred requests import to the stub.
    assert MistHelper._check_token_rate_limit("secret", "api.mist.com", "1/1") is True  # Preserve safe skip.


def test_check_token_rate_limit_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The token probe lets an unexpected requests defect escape."""
    requests_stub = SimpleNamespace(get=MagicMock(side_effect=AssertionError("boom")))  # Simulate an unrelated defect.
    original_import = builtins.__import__  # Keep the real importer for all other modules.

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        return requests_stub if name == "requests" else original_import(name, *args, **kwargs)  # Target requests only.

    monkeypatch.setattr(builtins, "__import__", fake_import)  # Route the deferred requests import to the stub.
    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._check_token_rate_limit("secret", "api.mist.com", "1/1")  # Execute the narrowed handler site.


def test_introspect_apisession_catches_signature_error() -> None:
    """The API session introspector catches unsupported callable signatures."""
    result = MistHelper._introspect_apisession_class(SimpleNamespace(APISession=42))  # int has no callable signature.
    assert result == (42, [])  # Preserve the empty-parameter fallback.


def test_introspect_apisession_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The API session introspector lets an unexpected inspect defect escape."""
    monkeypatch.setattr(MistHelper.inspect, "signature", MagicMock(side_effect=RuntimeError("boom")))  # Defect.
    with pytest.raises(RuntimeError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._introspect_apisession_class(SimpleNamespace(APISession=object))  # Execute handler site.


def test_log_session_attempt_traceback_catches_format_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The traceback logger catches secondary formatting failures."""
    monkeypatch.setattr("traceback.format_exception", MagicMock(side_effect=TypeError("bad trace")))  # Bad formatter.
    MistHelper._log_session_attempt_traceback(ValueError("primary"))  # Secondary trace failure must be non-fatal.


def test_log_session_attempt_traceback_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The traceback logger lets an unexpected formatter defect escape."""
    monkeypatch.setattr("traceback.format_exception", MagicMock(side_effect=AssertionError("boom")))  # Defect.
    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._log_session_attempt_traceback(ValueError("primary"))  # Execute the narrowed handler site.


def test_try_single_session_kwargs_catches_constructor_error() -> None:
    """The API session attempt catches expected constructor failures."""

    class FailingSession:
        def __init__(self, **_kwargs: str) -> None:
            raise TypeError("bad kwargs")  # Simulate an unsupported SDK constructor keyword.

    assert MistHelper._try_single_session_kwargs(FailingSession, {"token": "x"}, 1, 1) == (None, False)  # Fail open.


def test_try_single_session_kwargs_rejects_unexpected_error() -> None:
    """The API session attempt lets an unexpected constructor defect escape."""

    class FailingSession:
        def __init__(self, **_kwargs: str) -> None:
            raise AssertionError("boom")  # Simulate an unrelated constructor defect.

    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._try_single_session_kwargs(FailingSession, {"token": "x"}, 1, 1)  # Execute handler site.


def test_create_session_isolated_from_env_catches_constructor_error() -> None:
    """The filtered token constructor catches expected SDK failures."""

    class FailingSession:
        def __init__(self, **_kwargs: str) -> None:
            raise OSError("network")  # Simulate an SDK constructor network failure.

    assert MistHelper._create_session_isolated_from_env(FailingSession, {"apitoken": "x"}) is None  # Fail open.


def test_create_session_isolated_from_env_rejects_unexpected_error() -> None:
    """The filtered token constructor lets an unexpected SDK defect escape."""

    class FailingSession:
        def __init__(self, **_kwargs: str) -> None:
            raise AssertionError("boom")  # Simulate an unrelated constructor defect.

    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._create_session_isolated_from_env(FailingSession, {"apitoken": "x"})  # Execute handler site.


def test_try_session_fallback_catches_constructor_error() -> None:
    """The legacy session fallback catches expected SDK failures."""

    class FailingSession:
        def __init__(self) -> None:
            raise RuntimeError("sdk")  # Simulate the last-resort SDK session failure.

    assert MistHelper._try_session_fallback(SimpleNamespace(Session=FailingSession)) == (None, None)  # Fail open.


def test_try_session_fallback_rejects_unexpected_error() -> None:
    """The legacy session fallback lets an unexpected SDK defect escape."""

    class FailingSession:
        def __init__(self) -> None:
            raise AssertionError("boom")  # Simulate an unrelated constructor defect.

    with pytest.raises(AssertionError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._try_session_fallback(SimpleNamespace(Session=FailingSession))  # Execute handler site.


def test_setup_runtime_flags_catches_fast_attr_error() -> None:
    """The runtime flag setup catches a bad fast attribute and publishes False."""

    class Args:
        standalone = False  # Keep unrelated mode logic quiet during flag setup.
        test = False  # Keep test-mode logic quiet during flag setup.
        testinteractive = False  # Keep interactive-test logic quiet during flag setup.

        @property
        def fast(self) -> bool:
            raise AttributeError("fast")  # Simulate a broken argparse namespace seam.

    args = Args()  # Use a local class so the property affects only this test.
    MistHelper._setup_runtime_flags(args)  # Runtime setup must keep startup controlled.
    assert MistHelper.MainEntrypoint.context.fast_mode_enabled is False  # Preserve the safe default.


def test_setup_runtime_flags_rejects_unexpected_error() -> None:
    """The runtime flag setup lets an unexpected fast attribute defect escape."""

    class Args:
        standalone = False  # Keep unrelated mode logic quiet during flag setup.
        test = False  # Keep test-mode logic quiet during flag setup.
        testinteractive = False  # Keep interactive-test logic quiet during flag setup.

        @property
        def fast(self) -> bool:
            raise ValueError("boom")  # Simulate an unexpected argparse namespace defect.

    args = Args()  # Use a local class so the property affects only this test.
    with pytest.raises(ValueError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._setup_runtime_flags(args)  # Execute the narrowed handler site.


def test_configure_runtime_options_catches_emitter_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The runtime options setup catches telemetry emitter file failures."""
    args = SimpleNamespace(output_format="csv", debug=False)  # Provide only the fields this function reads.
    monkeypatch.setattr(MistHelper, "TelemetryEmitter", MagicMock(side_effect=OSError("denied")))  # File failure.
    MistHelper._configure_runtime_options(args)  # Runtime setup must keep telemetry optional.
    assert MistHelper.MainEntrypoint.context.progress_emitter is None  # Preserve the no-telemetry fallback.


def test_configure_runtime_options_rejects_unexpected_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """The runtime options setup lets an unexpected telemetry defect escape."""
    args = SimpleNamespace(output_format="csv", debug=False)  # Provide only the fields this function reads.
    monkeypatch.setattr(MistHelper, "TelemetryEmitter", MagicMock(side_effect=RuntimeError("boom")))  # Defect.
    with pytest.raises(RuntimeError):  # Prove the narrowed handler does not hide unrelated defects.
        MistHelper._configure_runtime_options(args)  # Execute the narrowed handler site.
