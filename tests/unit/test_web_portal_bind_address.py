"""Tests for the web portal bind address resolution.

Issue #1711 reported that the code built the all-interfaces address with
``".".join(("0",) * 4)``. That expression produces ``0.0.0.0`` and existed only
to hide the literal from bandit rule B104. The project standard forbids a
shortcut that silences a legitimate finding.

These tests hold the replacement behavior in place. A workstation binds to the
loopback address, a container binds to every interface, and ``WEB_HOST``
overrides both.
"""

import importlib
import inspect

import pytest


@pytest.fixture(scope="module")
def resolver():
    """Return the bind address resolver from the entry point module."""
    module = importlib.import_module("MistHelper")  # Load the entry point module.
    return module


@pytest.fixture(autouse=True)
def _clear_web_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove WEB_HOST so each test states the value it needs."""
    monkeypatch.delenv("WEB_HOST", raising=False)


def _set_container(monkeypatch: pytest.MonkeyPatch, module, value: bool) -> None:
    """Force the container detection answer for one test."""
    monkeypatch.setattr(module.EnvironmentUtils, "is_running_in_container", staticmethod(lambda: value))


def test_workstation_binds_to_loopback(resolver, monkeypatch: pytest.MonkeyPatch) -> None:
    """A workstation must keep the portal off the local network."""
    _set_container(monkeypatch, resolver, False)
    assert resolver._resolve_web_portal_host() == "127.0.0.1"


def test_container_binds_to_all_interfaces(resolver, monkeypatch: pytest.MonkeyPatch) -> None:
    """A container must accept the request the published port forwards."""
    _set_container(monkeypatch, resolver, True)
    assert resolver._resolve_web_portal_host() == "0.0.0.0"


def test_web_host_overrides_the_workstation_default(resolver, monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicit WEB_HOST wins on a workstation."""
    _set_container(monkeypatch, resolver, False)
    monkeypatch.setenv("WEB_HOST", "192.0.2.10")
    assert resolver._resolve_web_portal_host() == "192.0.2.10"


def test_web_host_overrides_the_container_default(resolver, monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicit WEB_HOST wins inside a container too."""
    _set_container(monkeypatch, resolver, True)
    monkeypatch.setenv("WEB_HOST", "127.0.0.1")
    assert resolver._resolve_web_portal_host() == "127.0.0.1"


def test_the_source_holds_no_address_building_expression() -> None:
    """The code must state the address, not assemble it to dodge a scanner.

    Issue #1711 exists because the old expression hid the literal from bandit.
    A future contributor must not reintroduce that pattern under any spelling.
    """
    source = inspect.getsource(importlib.import_module("MistHelper")._resolve_web_portal_host)
    # The join expression is the exact pattern the issue reported.
    assert '"."' not in source or "join" not in source
    assert "0.0.0.0" in source  # The literal must appear in plain text.


def test_the_nosec_marker_carries_a_justification() -> None:
    """A suppression must record the reason, not only silence the rule."""
    source = inspect.getsource(importlib.import_module("MistHelper")._resolve_web_portal_host)
    assert "nosec B104" in source  # The suppression is explicit and named.
    # The comment block above the bind states the container condition.
    assert "container" in source.lower()


def test_the_entry_point_uses_the_resolver() -> None:
    """The launcher must call the resolver rather than build its own address."""
    source = inspect.getsource(importlib.import_module("MistHelper")._launch_web_portal)
    assert "_resolve_web_portal_host()" in source
    assert "join" not in source  # No address assembly remains in the launcher.
