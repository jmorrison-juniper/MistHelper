"""Tests for the MistHelper attribute proxy in `src/firmware/firmware_manager.py`.

`MistHelper.py` can stop part way through its module body when a dependency is
absent. The half-built module stays in `sys.modules`, so a plain `getattr`
reports a missing attribute and hides the real cause. These tests hold the proxy
to the rule that it reports the recorded cause. See issue #1923.
"""

from __future__ import annotations

import sys
import types

import pytest

from src.firmware.firmware_manager import (
    _IMPORT_ERROR_ATTRIBUTE,
    _MISTHELPER_MODULE_NAME,
    _MistHelperProxy,
)


@pytest.fixture
def stub_misthelper_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Install an empty stand-in for `MistHelper` and remove it after the test."""
    module = types.ModuleType(_MISTHELPER_MODULE_NAME)  # Build an empty module, so no name binds by accident.
    monkeypatch.setitem(sys.modules, _MISTHELPER_MODULE_NAME, module)  # Install it, because the proxy imports by name.
    return module  # Give the test the module, so it can bind or record on it.


class TestMistHelperProxyPartialImport:
    """The proxy must name the real cause when the module stopped part way."""

    def test_reports_the_recorded_import_failure(self, stub_misthelper_module: types.ModuleType) -> None:
        """A recorded dependency failure appears in the message, not a bare miss."""
        cause = ModuleNotFoundError("No module named 'paramiko'")  # Build the exact cause from issue #1923.
        setattr(stub_misthelper_module, _IMPORT_ERROR_ATTRIBUTE, cause)  # Record it, as tests/conftest.py does.
        proxy = _MistHelperProxy()  # Build the proxy under test.

        with pytest.raises(AttributeError) as error_info:  # The proxy must still raise AttributeError.
            _ = proxy.InputUtils  # Ask for the name that issue #1923 reports as missing.

        message = str(error_info.value)  # Read the message, because the message is the defect.
        assert "paramiko" in message  # The real cause must appear, so the reader looks in the right place.
        assert "ModuleNotFoundError" in message  # The class of the cause must appear.
        assert "bootstrap_worktree.py" in message  # The repair step must appear.
        assert error_info.value.__cause__ is cause  # The chain must keep the original exception.

    def test_keeps_the_original_error_when_the_module_loaded(self, stub_misthelper_module: types.ModuleType) -> None:
        """With no recorded failure the proxy reports the plain missing name."""
        proxy = _MistHelperProxy()  # Build the proxy under test.

        with pytest.raises(AttributeError) as error_info:  # A truly absent name still raises.
            _ = proxy.NameThatDoesNotExist  # Ask for a name that no module binds.

        message = str(error_info.value)  # Read the message for the plain case.
        assert "has no attribute" in message  # Keep the standard text, because the module did load.
        assert "bootstrap_worktree.py" not in message  # Do not offer a repair step that does not apply.

    def test_forwards_a_bound_attribute(self, stub_misthelper_module: types.ModuleType) -> None:
        """A bound name resolves through the proxy without change."""
        stub_misthelper_module.InputUtils = "bound-value"  # Bind a name, so the lookup succeeds.
        proxy = _MistHelperProxy()  # Build the proxy under test.

        assert proxy.InputUtils == "bound-value"  # The proxy must return the live value.

    def test_reports_a_failed_import_of_the_module_itself(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An ImportError from the import call becomes a named AttributeError."""
        cause = ModuleNotFoundError("No module named 'paramiko'")  # Build the cause the import would raise.

        def raise_import_error(name: str) -> types.ModuleType:
            """Stand in for importlib.import_module and always fail."""
            raise cause  # Raise the prepared cause, so the proxy sees a failed import.

        monkeypatch.setattr("src.firmware.firmware_manager.importlib.import_module", raise_import_error)  # Install it.
        proxy = _MistHelperProxy()  # Build the proxy under test.

        with pytest.raises(AttributeError) as error_info:  # The proxy must not leak ImportError to the caller.
            _ = proxy.InputUtils  # Ask for any name, because the import fails first.

        assert "paramiko" in str(error_info.value)  # The real cause must appear in the message.
        assert error_info.value.__cause__ is cause  # The chain must keep the original exception.
