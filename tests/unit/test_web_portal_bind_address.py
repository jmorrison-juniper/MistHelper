"""Unit tests for the web portal bind address resolver in MistHelper.py (issue #1711).

The resolver `_resolve_web_portal_host()` must return the loopback address on a
workstation, the all-interfaces address inside a container, and the `WEB_HOST`
value when an operator sets that variable. A guardrail test proves that the old
join expression, which hid the literal address from the security scanner, is
gone from the source file.
"""

from __future__ import annotations  # WHY: keep the annotation style equal to the rest of the suite.

import inspect  # WHY: the guardrail test reads the source of the resolver function.
from pathlib import Path  # WHY: the guardrail test locates MistHelper.py on disk.

import pytest  # WHY: the tests use the monkeypatch fixture for the environment and the container probe.

import MistHelper  # WHY: the resolver under test is a module-level function of the script.

CONTAINER_PROBE = "MistHelper.EnvironmentUtils.is_running_in_container"  # WHY: one name for the patch target.


def _force_container_state(monkeypatch: pytest.MonkeyPatch, in_container: bool) -> None:
    """Force the container probe to report the given state for one test."""
    monkeypatch.setattr(CONTAINER_PROBE, lambda: in_container)  # WHY: remove the real filesystem probe from the test.


class TestResolveWebPortalHost:
    """The resolver picks the bind address from the container state and the WEB_HOST variable."""

    def test_workstation_binds_to_loopback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without WEB_HOST and outside a container the resolver returns the loopback address."""
        monkeypatch.delenv("WEB_HOST", raising=False)  # WHY: an inherited value would mask the default.
        _force_container_state(monkeypatch, False)  # WHY: model a workstation run.
        assert MistHelper._resolve_web_portal_host() == "127.0.0.1"  # WHY: a workstation must not expose the port.

    def test_container_binds_to_all_interfaces(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without WEB_HOST and inside a container the resolver returns the all-interfaces address."""
        monkeypatch.delenv("WEB_HOST", raising=False)  # WHY: an inherited value would mask the default.
        _force_container_state(monkeypatch, True)  # WHY: model a container run.
        assert MistHelper._resolve_web_portal_host() == "0.0.0.0"  # WHY: a container needs an external bind.

    def test_web_host_overrides_the_workstation_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A WEB_HOST value replaces the loopback default on a workstation."""
        monkeypatch.setenv("WEB_HOST", "10.1.2.3")  # WHY: model an operator override.
        _force_container_state(monkeypatch, False)  # WHY: model a workstation run.
        assert MistHelper._resolve_web_portal_host() == "10.1.2.3"  # WHY: the override must win.

    def test_web_host_overrides_the_container_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A WEB_HOST value replaces the all-interfaces default inside a container."""
        monkeypatch.setenv("WEB_HOST", "192.0.2.10")  # WHY: model an operator override.
        _force_container_state(monkeypatch, True)  # WHY: model a container run.
        assert MistHelper._resolve_web_portal_host() == "192.0.2.10"  # WHY: the override must win.

    def test_empty_web_host_falls_back_to_the_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An empty WEB_HOST value is not an address, so the resolver uses the default."""
        monkeypatch.setenv("WEB_HOST", "")  # WHY: an empty value must not produce an empty bind address.
        _force_container_state(monkeypatch, False)  # WHY: model a workstation run.
        assert MistHelper._resolve_web_portal_host() == "127.0.0.1"  # WHY: the loopback default still applies.


class TestBindAddressSourceGuardrail:
    """The source states the bind address in plain form and carries the suppression comment."""

    def test_resolver_states_the_literal_address(self) -> None:
        """The resolver source contains the plain all-interfaces literal."""
        source = inspect.getsource(MistHelper._resolve_web_portal_host)  # WHY: read the shipped implementation.
        assert '"0.0.0.0"' in source  # WHY: the source must state the address in plain form for the scanner.

    def test_resolver_carries_a_justified_suppression(self) -> None:
        """The all-interfaces line carries a nosec B104 marker with a stated reason."""
        source = inspect.getsource(MistHelper._resolve_web_portal_host)  # WHY: read the shipped implementation.
        assert "# nosec B104" in source  # WHY: the project standard needs a recorded decision, not a hidden literal.
        assert "is_running_in_container()" in source  # WHY: the comment must state the container condition.

    def test_module_no_longer_builds_the_address_from_parts(self) -> None:
        """The old join expression that hid the literal from the scanner is gone."""
        script_path = Path(MistHelper.__file__)  # WHY: the guardrail reads the whole script, not one function.
        script_text = script_path.read_text(encoding="utf-8")  # WHY: a text scan catches a moved copy of the pattern.
        assert '".".join(("0",) * 4)' not in script_text  # WHY: an obfuscated address must never return.
