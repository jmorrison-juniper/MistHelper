"""Wave 5 P2 coverage for src/device/device_utils.py (initiative #1018).

Covers all static methods of ``DeviceUtils``:
- ``get_all_ap_macs_from_site``: success/empty/exception branches.
- ``expand_port_range_string``: single, range, mixed, and multi-comma cases.
- ``_expand_one_port_part``: no-hyphen, unparsable, and valid range.
- ``_warn_degraded_identifier``: prior_fields empty (no warn) vs non-empty (warn).
- ``get_device_identifier``: name/serial/id/UNKNOWN fallback + warn behaviors.

Uses monkeypatch to inject a lazy MistHelper stub with an apisession attribute
and patches ``mistapi.api.v1.sites.devices.listSiteDevices`` for API calls.
No live network. MagicMock(spec=...) used where practical.
"""

from __future__ import annotations  # WHY: PEP 604 unions in test type hints.

import logging  # WHY: caplog verification of warning + info + exception logs.
import sys  # WHY: mint a fake MistHelper module into sys.modules for lazy-import to resolve.
import types  # WHY: build the fake MistHelper module cheaply.
from typing import Any  # WHY: satisfies both mypy strict + ruff B010 on dynamic module attrs.
from unittest.mock import MagicMock, patch  # WHY: mandatory spec= mocks + patch decorators.

import pytest  # WHY: monkeypatch + caplog fixtures.

from src.device.device_utils import DeviceUtils  # WHY: SUT direct import.


def _install_fake_mist_helper(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Replace sys.modules['MistHelper'] with a minimal stub exposing apisession."""
    mh: Any = types.ModuleType("MistHelper")  # WHY: Any typing satisfies both mypy strict + ruff B010 on dynamic attrs.
    mh.apisession = MagicMock(spec=object)  # WHY: opaque placeholder API session; SUT pass-through only.
    monkeypatch.setitem(sys.modules, "MistHelper", mh)  # WHY: lazy import returns this stub.
    return mh


class TestGetAllApMacsFromSite:
    """``get_all_ap_macs_from_site`` returns AP MACs list, empty on none/error."""

    def test_success_returns_ap_macs_list(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Two APs with macs → list of 2 macs; info + debug logs emitted."""
        _install_fake_mist_helper(monkeypatch)
        fake_resp = MagicMock(spec=object)  # WHY: opaque response object; only .data used.
        fake_resp.data = [{"mac": "aa"}, {"mac": "bb"}]  # WHY: two AP dicts with macs.
        with patch("src.device.device_utils.mistapi") as fake_mistapi:
            fake_mistapi.api.v1.sites.devices.listSiteDevices.return_value = fake_resp
            with caplog.at_level(logging.DEBUG):
                result = DeviceUtils.get_all_ap_macs_from_site("site-1")

        assert result == ["aa", "bb"]  # WHY: SUT extracts .mac from each dict.
        fake_mistapi.api.v1.sites.devices.listSiteDevices.assert_called_once()  # WHY: API called once.
        assert "Fetching all AP MACs for site: site-1" in caplog.text  # WHY: pre-action debug log.
        assert "Found 2 AP MACs at site" in caplog.text  # WHY: post-action info log.

    def test_ap_without_mac_is_filtered(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """APs missing a mac field are dropped from the returned list."""
        _install_fake_mist_helper(monkeypatch)
        fake_resp = MagicMock(spec=object)
        fake_resp.data = [{"mac": "aa"}, {"mac": ""}, {"other": "x"}]  # WHY: only one has mac.
        with patch("src.device.device_utils.mistapi") as fake_mistapi:
            fake_mistapi.api.v1.sites.devices.listSiteDevices.return_value = fake_resp
            result = DeviceUtils.get_all_ap_macs_from_site("site-1")
        assert result == ["aa"]  # WHY: falsy-mac and missing-mac entries dropped by `if ap.get("mac")`.

    def test_empty_response_returns_empty_and_warns(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Empty .data returns [] and logs warning."""
        _install_fake_mist_helper(monkeypatch)
        fake_resp = MagicMock(spec=object)
        fake_resp.data = []  # WHY: empty AP list.
        with patch("src.device.device_utils.mistapi") as fake_mistapi:
            fake_mistapi.api.v1.sites.devices.listSiteDevices.return_value = fake_resp
            with caplog.at_level(logging.WARNING):
                result = DeviceUtils.get_all_ap_macs_from_site("site-empty")

        assert result == []  # WHY: no APs → empty list.
        assert "No APs found for site_id: site-empty" in caplog.text  # WHY: contract warning.

    def test_exception_returns_empty_and_logs(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Any exception is swallowed; returns [] and logs the exception line."""
        _install_fake_mist_helper(monkeypatch)
        with patch("src.device.device_utils.mistapi") as fake_mistapi:
            fake_mistapi.api.v1.sites.devices.listSiteDevices.side_effect = RuntimeError("api boom")
            with caplog.at_level(logging.ERROR):
                result = DeviceUtils.get_all_ap_macs_from_site("site-x")

        assert result == []  # WHY: SUT contract: no crash, empty on failure.
        assert "Exception in DeviceUtils.get_all_ap_macs_from_site" in caplog.text  # WHY: log format.


class TestExpandPortRangeString:
    """``expand_port_range_string`` splits by comma then expands each part."""

    def test_single_port_literal_returns_singleton(self) -> None:
        """Single literal port name returns a one-element list."""
        assert DeviceUtils.expand_port_range_string("ge-0/0/0") == ["ge-0/0/0"]  # WHY: no comma, no range.

    def test_valid_range_expands(self) -> None:
        """ge-0/0/0-2 expands to three individual ports."""
        assert DeviceUtils.expand_port_range_string("ge-0/0/0-2") == [
            "ge-0/0/0",
            "ge-0/0/1",
            "ge-0/0/2",
        ]  # WHY: SUT-mandated expansion of range prefix/N-M.

    def test_multiple_ranges_comma_separated(self) -> None:
        """Two ranges separated by comma both expand and concat."""
        result = DeviceUtils.expand_port_range_string("ge-0/0/0-2, ge-0/1/2-3")
        assert result == [
            "ge-0/0/0",
            "ge-0/0/1",
            "ge-0/0/2",
            "ge-0/1/2",
            "ge-0/1/3",
        ]  # WHY: docstring example.

    def test_mixed_literal_and_range(self) -> None:
        """Mixed literal + range comma expression per docstring example."""
        result = DeviceUtils.expand_port_range_string("mge-0/2/0, xe-0/1/0-3")
        assert result == [
            "mge-0/2/0",
            "xe-0/1/0",
            "xe-0/1/1",
            "xe-0/1/2",
            "xe-0/1/3",
        ]  # WHY: docstring example verbatim.


class TestExpandOnePortPart:
    """``_expand_one_port_part`` handles literal (no hyphen), unparsable, and valid range tokens."""

    def test_no_hyphen_returns_literal(self) -> None:
        """No hyphen in token means literal port name."""
        assert DeviceUtils._expand_one_port_part("ge-0/0/0") == ["ge-0/0/0"]  # WHY: no `-` (well, there is
        # `-` after `ge` but not in `/N-M` shape); regex won't match → literal branch also fires.

    def test_unparsable_hyphenated_returns_literal(self) -> None:
        """Token with `-` but not matching the /N-M pattern is kept literal."""
        assert DeviceUtils._expand_one_port_part("weird-token") == ["weird-token"]  # WHY: regex miss.

    def test_valid_range_expands(self) -> None:
        """Regex-matching range expands numeric prefix/N-M inclusive."""
        assert DeviceUtils._expand_one_port_part("xe-0/1/3-5") == [
            "xe-0/1/3",
            "xe-0/1/4",
            "xe-0/1/5",
        ]  # WHY: inclusive range.


class TestWarnDegradedIdentifier:
    """``_warn_degraded_identifier`` warns only when prior_fields is non-empty."""

    def test_prior_fields_empty_skips_warn(self, caplog: pytest.LogCaptureFixture) -> None:
        """First-choice field succeeded → no warning."""
        with caplog.at_level(logging.WARNING):
            DeviceUtils._warn_degraded_identifier("val", "", "name")  # WHY: prior_fields empty → early return.
        assert caplog.text == ""  # WHY: no log line emitted.

    def test_prior_fields_non_empty_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """Fallback occurred → warning emitted with all three interpolated values."""
        with caplog.at_level(logging.WARNING):
            DeviceUtils._warn_degraded_identifier("SN-42", "name", "serial")  # WHY: degraded case.
        assert "Device SN-42 missing name field, using serial as identifier" in caplog.text  # WHY: format.


class TestGetDeviceIdentifier:
    """``get_device_identifier`` returns first non-empty of name/serial/id else UNKNOWN."""

    def test_name_present_returns_name(self) -> None:
        """Non-empty name is preferred."""
        assert DeviceUtils.get_device_identifier({"name": "alpha", "serial": "s", "id": "i"}) == "alpha"

    def test_falls_back_to_serial_when_name_blank(self, caplog: pytest.LogCaptureFixture) -> None:
        """Blank name → serial used; warn_on_missing=True emits degraded warning."""
        dev = {"name": "  ", "serial": "SN-1", "id": "id-1"}  # WHY: whitespace-only name is treated as blank.
        with caplog.at_level(logging.WARNING):
            assert DeviceUtils.get_device_identifier(dev, warn_on_missing=True) == "SN-1"
        assert "using serial as identifier" in caplog.text  # WHY: degraded warning emitted.

    def test_falls_back_to_id_when_name_and_serial_blank(self, caplog: pytest.LogCaptureFixture) -> None:
        """Blank name+serial → id used; warn_on_missing=True emits warning."""
        dev = {"name": "", "serial": "", "id": "the-id"}
        with caplog.at_level(logging.WARNING):
            result = DeviceUtils.get_device_identifier(dev, warn_on_missing=True)
        assert result == "the-id"  # WHY: final fallback field.
        assert "using id as identifier" in caplog.text  # WHY: degraded warning.

    def test_all_blank_returns_unknown_and_warns(self, caplog: pytest.LogCaptureFixture) -> None:
        """All three fields blank → UNKNOWN plus final warning line."""
        dev = {"name": "", "serial": "", "id": ""}
        with caplog.at_level(logging.WARNING):
            result = DeviceUtils.get_device_identifier(dev, warn_on_missing=True)
        assert result == "UNKNOWN"  # WHY: last-resort placeholder.
        assert "no name, serial, or id" in caplog.text  # WHY: final warning contract.

    def test_all_blank_without_warn_returns_unknown_silently(self, caplog: pytest.LogCaptureFixture) -> None:
        """warn_on_missing=False suppresses the final UNKNOWN warning."""
        dev = {"name": "", "serial": "", "id": ""}
        with caplog.at_level(logging.WARNING):
            result = DeviceUtils.get_device_identifier(dev, warn_on_missing=False)
        assert result == "UNKNOWN"  # WHY: still returns UNKNOWN.
        assert caplog.text == ""  # WHY: no warning emitted when flag off.

    def test_missing_key_treated_as_blank(self) -> None:
        """Missing key entirely (not present at all) uses .get default and falls back cleanly."""
        dev: dict[str, str] = {"id": "only-id"}  # WHY: no name, no serial → fallback to id.
        assert DeviceUtils.get_device_identifier(dev) == "only-id"
