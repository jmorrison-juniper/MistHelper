"""Unit tests for src/refactors/msp_privilege_detection.py.

Covers the public entry point ``detect_msp_privileges`` and each of the six
private helpers co-migrated in initiative 1015 T-05: ``_msp_fetch_user_data``,
``_msp_extract_from_user_data``, ``_msp_parse_one_privilege``,
``_msp_resolve_name``, ``_fetch_msp_name``, ``_extract_msp_name``.

Stubbing strategy
-----------------
The SUT does lazy imports of two mistapi endpoints:

    import mistapi.api.v1.self.self as self_api      # in _msp_fetch_user_data
    import mistapi.api.v1.msps.msps as msps_api      # in _fetch_msp_name

Because ``import a.b.c as x`` resolves ``x`` via *attribute access* on the
parent package (``mistapi.api.v1.msps.msps``), overriding only
``sys.modules[dotted]`` is not enough when the parent package already has an
attribute pointing at the real submodule. Sibling test modules also replace
``mistapi`` and its submodules with ``MagicMock`` at ``sys.modules`` level,
which can defeat ``patch("mistapi.a.b.c.func")`` string-target patches when
the whole suite is collected in the wrong order.

To defeat both failure modes we use an autouse fixture that force-loads the
real mistapi submodules AND restores the parent-package attribute chain
before each test. Individual tests then use ``_stub_callable`` to swap in a
``MagicMock`` for the exact function they exercise; ``_stub_callable`` also
sets the attribute on the parent package so the lazy-import alias
resolves to the stub.
"""

from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.refactors.msp_privilege_detection import (
    _extract_msp_name,
    _fetch_msp_name,
    _msp_extract_from_user_data,
    _msp_fetch_user_data,
    _msp_parse_one_privilege,
    _msp_resolve_name,
    detect_msp_privileges,
)

# The two lazy-import targets used by the SUT. Kept as constants for the fixture.
_MISTAPI_SELF = "mistapi.api.v1.self.self"
_MISTAPI_MSPS = "mistapi.api.v1.msps.msps"


@pytest.fixture(autouse=True)
def _restore_real_mistapi_modules() -> None:
    """Force real mistapi submodules to be present before each test.

    Sibling tests in this suite (e.g. ``test_csv_comparator``,
    ``test_wan2_variable``, ``test_routing_utils``, ``test_bulk_switch_upgrader``,
    ``test_ssid_template_consolidation``, ``test_device_utility_commands``,
    ``test_template_config``) install ``sys.modules['mistapi'] = MagicMock()``
    at MODULE-IMPORT time. Once that's in place, ``importlib.import_module
    ('mistapi.api.v1.msps.msps')`` simply walks attributes off the MagicMock
    and returns another MagicMock -- not the real module.

    The only reliable fix is to clear the ENTIRE mistapi subtree from
    ``sys.modules`` and force a fresh import. This runs before every one of
    OUR tests, so we never observe MagicMock-polluted state at the SUT's lazy
    imports. We deliberately do NOT restore the polluted state afterwards --
    leaving the real modules in place is strictly safer for downstream tests
    than reinstating a broken MagicMock.
    """
    # Purge any mistapi.* entries so importlib does a full re-import from disk.
    for key in [k for k in sys.modules if k == "mistapi" or k.startswith("mistapi.")]:
        del sys.modules[key]

    # Reimport the two lazy-import targets the SUT uses. This also populates
    # every ancestor package as a real module in sys.modules along the way.
    for dotted in (_MISTAPI_SELF, _MISTAPI_MSPS):
        real = importlib.import_module(dotted)
        # Belt-and-braces: also re-bind the leaf submodule as an attribute of
        # its parent package, since ``import a.b.c as alias`` reads ``alias``
        # from the parent's attributes.
        parent_path, _, leaf = dotted.rpartition(".")
        parent = sys.modules.get(parent_path)
        if parent is not None:
            setattr(parent, leaf, real)


# ---------------------------------------------------------------------------
# Stubbing helpers
# ---------------------------------------------------------------------------


@contextmanager
def _stub_callable(dotted_module: str, attr: str, replacement: Any):
    """Temporarily replace ``dotted_module.attr`` with ``replacement``.

    Sets the attribute both on the module object in ``sys.modules`` AND (for
    safety across import machinery quirks) on the parent-package attribute if
    the parent already has a reference to the same module. Restores the
    original attribute on exit.
    """
    module = sys.modules[dotted_module]
    _sentinel: Any = object()
    original = getattr(module, attr, _sentinel)
    setattr(module, attr, replacement)
    try:
        yield replacement
    finally:
        if original is _sentinel:
            try:
                delattr(module, attr)
            except AttributeError:
                pass
        else:
            setattr(module, attr, original)


def _stub_get_self(response: Any) -> Any:
    """Stub ``mistapi.api.v1.self.self.getSelf`` -> ``response``. Returns (ctx, mock)."""
    mock = MagicMock(return_value=response)
    return _stub_callable(_MISTAPI_SELF, "getSelf", mock), mock


def _stub_get_msp_details(response: Any = None, *, side_effect: Any = None) -> Any:
    """Stub ``mistapi.api.v1.msps.msps.getMspDetails``. Returns (ctx, mock)."""
    if side_effect is not None:
        mock = MagicMock(side_effect=side_effect)
    else:
        mock = MagicMock(return_value=response)
    return _stub_callable(_MISTAPI_MSPS, "getMspDetails", mock), mock


# ---------------------------------------------------------------------------
# _extract_msp_name
# ---------------------------------------------------------------------------


def test_extract_msp_name_returns_none_when_data_attr_missing() -> None:
    """Response without a .data attribute yields None."""
    response = object()  # bare object has no ``data`` attr; getattr default is None
    assert _extract_msp_name(response) is None


def test_extract_msp_name_returns_none_when_data_not_dict() -> None:
    """Non-dict response.data yields None."""
    response = SimpleNamespace(data=["not", "a", "dict"])
    assert _extract_msp_name(response) is None


def test_extract_msp_name_returns_none_when_name_not_str() -> None:
    """Non-string name field yields None."""
    response = SimpleNamespace(data={"name": 42})
    assert _extract_msp_name(response) is None


def test_extract_msp_name_returns_name_when_valid() -> None:
    """Valid string name in response.data is returned."""
    response = SimpleNamespace(data={"name": "Acme MSP"})
    assert _extract_msp_name(response) == "Acme MSP"


def test_extract_msp_name_returns_none_when_name_missing() -> None:
    """Missing name key in a dict payload yields None."""
    response = SimpleNamespace(data={"other": "field"})
    assert _extract_msp_name(response) is None


# ---------------------------------------------------------------------------
# _fetch_msp_name
# ---------------------------------------------------------------------------


def test_fetch_msp_name_returns_none_when_session_is_none() -> None:
    """Without a session, no lookup is attempted."""
    assert _fetch_msp_name("msp-1234abcd", None) is None


def test_fetch_msp_name_happy_path_returns_name() -> None:
    """getMspDetails response with a name populates the return value."""
    fake_response = SimpleNamespace(data={"name": "Acme MSP"})
    ctx, mock_get = _stub_get_msp_details(fake_response)
    with ctx:
        result = _fetch_msp_name("msp-1234abcd", session=MagicMock())
    assert result == "Acme MSP"
    mock_get.assert_called_once()


def test_fetch_msp_name_returns_none_on_exception() -> None:
    """Any exception during the API call degrades to None."""
    ctx, _ = _stub_get_msp_details(side_effect=RuntimeError("boom"))
    with ctx:
        result = _fetch_msp_name("msp-1234abcd", session=MagicMock())
    assert result is None


def test_fetch_msp_name_returns_none_when_response_malformed() -> None:
    """A response whose .data is not a dict yields None."""
    fake_response = SimpleNamespace(data=None)
    ctx, _ = _stub_get_msp_details(fake_response)
    with ctx:
        result = _fetch_msp_name("msp-1234abcd", session=MagicMock())
    assert result is None


# ---------------------------------------------------------------------------
# _msp_resolve_name
# ---------------------------------------------------------------------------


def test_msp_resolve_name_uses_grant_msp_name() -> None:
    """When the grant carries msp_name, it wins without any API call."""
    priv = {"msp_name": "From Grant"}
    ctx, mock_get = _stub_get_msp_details(None)
    with ctx:
        result = _msp_resolve_name("msp-1234abcd", priv, session=MagicMock())
    assert result == "From Grant"
    mock_get.assert_not_called()


def test_msp_resolve_name_uses_grant_name_when_msp_name_absent() -> None:
    """When msp_name is absent, ``name`` is used."""
    priv = {"name": "Backup Name"}
    ctx, mock_get = _stub_get_msp_details(None)
    with ctx:
        result = _msp_resolve_name("msp-1234abcd", priv, session=MagicMock())
    assert result == "Backup Name"
    mock_get.assert_not_called()


def test_msp_resolve_name_falls_back_to_fetch_when_unknown() -> None:
    """The literal 'Unknown' triggers the API fallback."""
    priv = {"msp_name": "Unknown"}
    fake_response = SimpleNamespace(data={"name": "Resolved via API"})
    ctx, _ = _stub_get_msp_details(fake_response)
    with ctx:
        result = _msp_resolve_name("msp-1234abcd", priv, session=MagicMock())
    assert result == "Resolved via API"


def test_msp_resolve_name_falls_back_to_short_label_when_api_returns_none() -> None:
    """If the API call fails, we derive a ``MSP-<short>`` label."""
    priv: dict = {}  # No name info at all
    ctx, _ = _stub_get_msp_details(side_effect=RuntimeError("nope"))
    with ctx:
        result = _msp_resolve_name("msp-1234abcd-rest", priv, session=MagicMock())
    assert result == "MSP-msp-1234"


def test_msp_resolve_name_falls_back_to_fetch_when_no_name_present() -> None:
    """Absent msp_name/name triggers the API fallback."""
    priv: dict = {"role": "admin"}
    fake_response = SimpleNamespace(data={"name": "Late Bound"})
    ctx, _ = _stub_get_msp_details(fake_response)
    with ctx:
        result = _msp_resolve_name("msp-1234abcd", priv, session=MagicMock())
    assert result == "Late Bound"


# ---------------------------------------------------------------------------
# _msp_parse_one_privilege
# ---------------------------------------------------------------------------


def test_parse_one_privilege_returns_none_for_non_dict() -> None:
    """Non-dict input is skipped."""
    assert _msp_parse_one_privilege("not a dict", session=MagicMock()) is None


def test_parse_one_privilege_returns_none_when_msp_id_missing() -> None:
    """A dict without msp_id is not an MSP grant."""
    assert _msp_parse_one_privilege({"scope": "org"}, session=MagicMock()) is None


def test_parse_one_privilege_returns_none_when_msp_id_not_str() -> None:
    """msp_id must be a string; ints are rejected."""
    priv = {"msp_id": 12345}
    assert _msp_parse_one_privilege(priv, session=MagicMock()) is None


def test_parse_one_privilege_builds_record_with_grant_name() -> None:
    """A valid MSP grant with msp_name is normalized without API calls."""
    priv = {
        "msp_id": "msp-1234abcd",
        "msp_name": "Acme MSP",
        "role": "admin",
        "scope": "msp",
    }
    ctx, mock_get = _stub_get_msp_details(None)
    with ctx:
        result = _msp_parse_one_privilege(priv, session=MagicMock())
    assert result == {
        "msp_id": "msp-1234abcd",
        "msp_name": "Acme MSP",
        "role": "admin",
        "scope": "msp",
    }
    mock_get.assert_not_called()


def test_parse_one_privilege_defaults_role_and_scope_when_missing() -> None:
    """Missing role/scope keys default to 'unknown'."""
    priv = {"msp_id": "msp-abcd0000", "msp_name": "Named"}
    result = _msp_parse_one_privilege(priv, session=MagicMock())
    assert result is not None
    assert result["role"] == "unknown"
    assert result["scope"] == "unknown"


def test_parse_one_privilege_triggers_resolve_name_fallback() -> None:
    """A grant without a name triggers _msp_resolve_name via getMspDetails."""
    priv = {"msp_id": "msp-1234abcd", "role": "admin", "scope": "msp"}
    fake_response = SimpleNamespace(data={"name": "Fetched Name"})
    ctx, _ = _stub_get_msp_details(fake_response)
    with ctx:
        result = _msp_parse_one_privilege(priv, session=MagicMock())
    assert result is not None
    assert result["msp_name"] == "Fetched Name"


# ---------------------------------------------------------------------------
# _msp_extract_from_user_data
# ---------------------------------------------------------------------------


def test_extract_from_user_data_returns_empty_when_no_privileges() -> None:
    """Empty or missing privileges yields an empty list."""
    assert _msp_extract_from_user_data({}, session=MagicMock()) == []
    assert _msp_extract_from_user_data({"privileges": []}, session=MagicMock()) == []


def test_extract_from_user_data_filters_non_msp_grants() -> None:
    """Only MSP-scoped grants are returned; org grants are filtered out."""
    user_data = {
        "privileges": [
            {"scope": "org", "role": "admin", "org_id": "org-1"},  # not an MSP grant
            {
                "msp_id": "msp-1111aaaa",
                "msp_name": "MSP One",
                "role": "admin",
                "scope": "msp",
            },
            "not-a-dict",  # ignored
            {
                "msp_id": "msp-2222bbbb",
                "msp_name": "MSP Two",
                "role": "read",
                "scope": "msp",
            },
        ]
    }
    result = _msp_extract_from_user_data(user_data, session=MagicMock())
    assert len(result) == 2
    assert {r["msp_id"] for r in result} == {"msp-1111aaaa", "msp-2222bbbb"}


# ---------------------------------------------------------------------------
# _msp_fetch_user_data
# ---------------------------------------------------------------------------


def test_msp_fetch_user_data_returns_none_when_response_falsy() -> None:
    """Falsy getSelf return produces None."""
    ctx, _ = _stub_get_self(None)
    with ctx:
        assert _msp_fetch_user_data(session=MagicMock()) is None


def test_msp_fetch_user_data_returns_none_when_no_data_attr() -> None:
    """Response without a .data attribute is treated as unusable."""

    class NoData:
        pass  # deliberately has no ``data`` attribute

    ctx, _ = _stub_get_self(NoData())
    with ctx:
        assert _msp_fetch_user_data(session=MagicMock()) is None


def test_msp_fetch_user_data_returns_none_when_data_not_dict() -> None:
    """Non-dict payload is rejected."""
    fake = SimpleNamespace(data=["list", "not", "dict"])
    ctx, _ = _stub_get_self(fake)
    with ctx:
        assert _msp_fetch_user_data(session=MagicMock()) is None


def test_msp_fetch_user_data_returns_dict_on_happy_path() -> None:
    """A valid dict payload is returned unchanged."""
    payload = {"privileges": [{"msp_id": "msp-1234abcd"}]}
    fake = SimpleNamespace(data=payload)
    ctx, _ = _stub_get_self(fake)
    with ctx:
        assert _msp_fetch_user_data(session=MagicMock()) == payload


# ---------------------------------------------------------------------------
# detect_msp_privileges (public entry point)
# ---------------------------------------------------------------------------


def test_detect_msp_privileges_returns_empty_when_session_is_none() -> None:
    """No session -> empty list, no API interaction."""
    assert detect_msp_privileges(None) == []


def test_detect_msp_privileges_returns_empty_when_session_is_falsy() -> None:
    """Falsy session values are treated as no session."""
    assert detect_msp_privileges(0) == []
    assert detect_msp_privileges("") == []


def test_detect_msp_privileges_returns_empty_when_fetch_returns_none() -> None:
    """When _msp_fetch_user_data returns None, empty list is returned."""
    ctx, _ = _stub_get_self(None)
    with ctx:
        assert detect_msp_privileges(session=MagicMock()) == []


def test_detect_msp_privileges_returns_empty_when_no_msp_grants() -> None:
    """Payload with only non-MSP privileges yields empty list."""
    fake = SimpleNamespace(data={"privileges": [{"scope": "org", "role": "admin", "org_id": "org-1"}]})
    ctx, _ = _stub_get_self(fake)
    with ctx:
        assert detect_msp_privileges(session=MagicMock()) == []


def test_detect_msp_privileges_returns_list_on_happy_path() -> None:
    """End-to-end: getSelf returns a valid MSP grant, list is returned."""
    fake = SimpleNamespace(
        data={
            "privileges": [
                {
                    "msp_id": "msp-1234abcd",
                    "msp_name": "Acme MSP",
                    "role": "admin",
                    "scope": "msp",
                }
            ]
        }
    )
    ctx, _ = _stub_get_self(fake)
    with ctx:
        result = detect_msp_privileges(session=MagicMock())
    assert result == [
        {
            "msp_id": "msp-1234abcd",
            "msp_name": "Acme MSP",
            "role": "admin",
            "scope": "msp",
        }
    ]


def test_detect_msp_privileges_returns_empty_on_exception() -> None:
    """Any unexpected exception during detection degrades to empty list."""
    ctx, _ = _stub_get_self(None)
    # Replace the stub's getSelf with one that raises so we exercise the outer except.
    with ctx:
        raising = MagicMock(side_effect=RuntimeError("network down"))
        with _stub_callable(_MISTAPI_SELF, "getSelf", raising):
            assert detect_msp_privileges(session=MagicMock()) == []


def test_detect_msp_privileges_returns_multiple_grants() -> None:
    """Multiple MSP grants in the payload are all returned."""
    fake = SimpleNamespace(
        data={
            "privileges": [
                {
                    "msp_id": "msp-aaaa0000",
                    "msp_name": "MSP A",
                    "role": "admin",
                    "scope": "msp",
                },
                {
                    "msp_id": "msp-bbbb1111",
                    "msp_name": "MSP B",
                    "role": "read",
                    "scope": "msp",
                },
            ]
        }
    )
    ctx, _ = _stub_get_self(fake)
    with ctx:
        result = detect_msp_privileges(session=MagicMock())
    assert len(result) == 2
    assert {r["msp_id"] for r in result} == {"msp-aaaa0000", "msp-bbbb1111"}
