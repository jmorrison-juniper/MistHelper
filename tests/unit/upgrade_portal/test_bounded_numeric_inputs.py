"""Prove the three numeric reader decisions without a network connection."""

from __future__ import annotations

import logging
import sys
from unittest.mock import Mock, call

import pytest
from flask import Flask
from hypothesis import given, settings
from hypothesis import strategies as st

from src.interfaces.portals.upgrade_portal.api import numeric_input
from src.interfaces.portals.upgrade_portal.app.routes import capture, select
from src.interfaces.portals.upgrade_portal.capture import clients

INVALID_TEXT = [
    pytest.param("\u00b2", id="superscript"),
    pytest.param("\u0662", id="arabic-decimal"),
    pytest.param("\uff12", id="fullwidth-decimal"),
    pytest.param("1\u0662", id="mixed-digits"),
    pytest.param("9" * 5000, id="5000-nines"),
    pytest.param("0" * 5000, id="5000-zeros"),
    pytest.param("0" * 5000 + "2", id="5000-leading-zeros"),
    pytest.param("", id="empty"),
    pytest.param("word", id="word"),
    pytest.param("-2", id="minus"),
    pytest.param("++2", id="repeated-plus"),
    pytest.param("2.0", id="fraction"),
    pytest.param("2_0", id="separator"),
]


class TestClientPageLimit:
    """Keep the named fallback and the existing page size clamps."""

    @pytest.mark.parametrize("raw", INVALID_TEXT)
    def test_invalid_setting_uses_named_fallback(self, monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
        """Invalid text must not stop a real client page limit read."""
        monkeypatch.setenv("MIST_PAGE_LIMIT", raw)
        assert clients.page_limit() == 1000

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("0", 1),
            ("1", 1),
            ("2", 2),
            ("250", 250),
            ("999", 999),
            ("1000", 1000),
            ("1001", 1000),
            ("5000", 1000),
            ("000250", 250),
            (" \t0250\r\n", 250),
            ("\u20030250\u2003", 250),
            ("+250", 1000),
            ("   ", 1000),
            pytest.param("0" * 4299 + "1", 1, id="backend-leading-zero-boundary"),
        ],
    )
    def test_existing_setting_boundaries(self, monkeypatch: pytest.MonkeyPatch, raw: str, expected: int) -> None:
        """Valid representations keep their existing normalization and range decisions."""
        monkeypatch.setenv("MIST_PAGE_LIMIT", raw)
        assert clients.page_limit() == expected

    def test_absent_setting_uses_named_fallback(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An absent setting still selects the documented default."""
        monkeypatch.delenv("MIST_PAGE_LIMIT", raising=False)
        assert clients.page_limit() == clients.DEFAULT_PAGE_LIMIT
        assert clients.DEFAULT_PAGE_LIMIT == 1000

    def test_exhaustive_page_limit_corpus(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Check every usable page size and its adjacent clamp boundaries."""
        checked = 0
        for number in range(1002):
            for raw in (str(number), f"000{number}", f" \t{number}\n", f"000{number:04d}"):
                monkeypatch.setenv("MIST_PAGE_LIMIT", raw)
                assert clients.page_limit() == max(1, min(1000, number)), (number, len(raw))
                checked += 1
        assert checked == 4008
        print(f"The corpus checked {checked} page limit decisions.")

    @settings(max_examples=100, derandomize=True, database=None)
    @given(number=st.integers(min_value=0, max_value=10**60), zeros=st.integers(min_value=0, max_value=32))
    def test_ascii_page_limit_property(self, number: int, zeros: int) -> None:
        """Generated ASCII values keep the minimum, maximum, and leading zero rules."""
        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("MIST_PAGE_LIMIT", " \t" + "0" * zeros + str(number) + "\n")
            assert clients.page_limit() == max(1, min(1000, number))


class TestNumericReaderCorpus:
    """Exercise the existing readers rather than a new primitive alone."""

    def test_every_non_ascii_digit_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Check every Unicode digit that the original isdigit check accepts."""
        application = Flask(__name__)
        digits = [chr(code) for code in range(sys.maxunicode + 1) if chr(code).isdigit() and code > 127]
        checked = 0
        for raw in digits:
            with application.test_request_context(query_string={"offset": raw}):
                assert select.read_whole_number("offset", 7) == 7, hex(ord(raw))
            assert capture.read_tier({"tier": raw}) is None, hex(ord(raw))
            monkeypatch.setenv("MIST_PAGE_LIMIT", raw)
            assert clients.page_limit() == 1000, hex(ord(raw))
            checked += 3
        assert {"\u00b2", "\u0662", "\uff12"} <= set(digits)
        assert checked == len(digits) * 3
        print(f"The corpus checked {checked} reader decisions for {len(digits)} non-ASCII digits.")

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            (None, None),
            (True, None),
            (False, None),
            (2.0, None),
            ([], None),
            ({}, None),
            (2, 2),
            (3, 3),
            ("2", 2),
            ("3", 3),
            ("002", 2),
            ("003", 3),
            (" 2 ", None),
            ("+2", None),
            ("0", None),
            ("1", None),
            ("4", None),
            pytest.param("0" * 4299 + "2", 2, id="backend-leading-zero-boundary"),
        ],
    )
    def test_existing_tier_shapes(self, raw: object, expected: int | None) -> None:
        """The real tier membership reader keeps JSON and form value rules."""
        assert capture.read_tier({"tier": raw}) == expected
        assert capture.read_tier({}) == 2

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("0", 0),
            ("25", 25),
            ("0025", 25),
            ("+25", 25),
            (" \t+0025\r\n", 25),
            ("\u2003+0025\u2003", 25),
            (str(sys.maxsize), sys.maxsize),
            (str(sys.maxsize + 1), 7),
            pytest.param("0" * 4300, 0, id="backend-zero-boundary"),
        ],
    )
    def test_query_reader_boundaries(self, raw: str, expected: int) -> None:
        """The real request reader keeps its sign, whitespace, and fallback rules."""
        application = Flask(__name__)
        with application.test_request_context(query_string={"offset": raw}):
            assert select.read_whole_number("offset", 7) == expected

    @pytest.mark.parametrize("raw", INVALID_TEXT)
    def test_invalid_query_and_tier_readers(self, raw: str) -> None:
        """Each required damaged value reaches the real request and tier readers."""
        application = Flask(__name__)
        with application.test_request_context(query_string={"offset": raw}):
            assert select.read_whole_number("offset", 7) == 7
        assert capture.read_tier({"tier": raw}) is None

    def test_setting_diagnostics_do_not_include_raw_input(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A diagnostic must report the setting and count without exposing input."""
        raw = "9" * 5000
        monkeypatch.setenv("MIST_PAGE_LIMIT", raw)
        caplog.set_level(logging.DEBUG)
        assert clients.page_limit() == 1000
        assert "MIST_PAGE_LIMIT" in caplog.text
        assert "reason=too_long" in caplog.text
        assert "characters=5000" in caplog.text
        assert "checked=1" in caplog.text
        assert raw not in caplog.text


class TestWholeNumberGuard:
    """Prove rejection before conversion at the real reader call sites."""

    @pytest.mark.parametrize(
        "raw",
        [
            pytest.param("9" * 5000, id="5000-nines"),
            pytest.param("0" * 5000, id="5000-zeros"),
            pytest.param("0" * 5000 + "2", id="5000-leading-zeros"),
            pytest.param("9" * 20, id="unusable-significant-length"),
            pytest.param(str(sys.maxsize + 1), id="sequence-bound-plus-one"),
        ],
    )
    def test_no_reader_converts_unusable_text(self, monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
        """Patch the actual conversion boundary, not the old caller's unused name."""
        conversion = Mock(wraps=int)
        monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
        application = Flask(__name__)
        with application.test_request_context(query_string={"offset": raw}):
            assert select.read_whole_number("offset", 7) == 7
        assert conversion.call_count == 0
        assert capture.read_tier({"tier": raw}) is None
        assert conversion.call_count == 0
        monkeypatch.setenv("MIST_PAGE_LIMIT", raw)
        assert clients.page_limit() == 1000
        assert conversion.call_count == 0

    @pytest.mark.parametrize("raw", INVALID_TEXT)
    def test_primitive_rejects_invalid_text_before_conversion(self, monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
        """The shared guard must fail directly for every required invalid input."""
        conversion = Mock(wraps=int)
        monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
        assert numeric_input.AsciiWholeNumberReader(sys.maxsize, "probe").read(raw) is None
        assert conversion.call_count == 0

    @pytest.mark.parametrize(
        ("maximum", "raw", "expected"),
        [
            (0, "0", 0),
            (0, "1", None),
            (3, "003", 3),
            (3, "004", None),
            (1000, "01000", 1000),
            (1000, "01001", None),
            (sys.maxsize, str(sys.maxsize), sys.maxsize),
            (sys.maxsize, str(sys.maxsize + 1), None),
            pytest.param(3, "0" * 4299 + "2", 2, id="backend-leading-zero-boundary"),
        ],
    )
    def test_primitive_uses_caller_number_bound(self, maximum: int, raw: str, expected: int | None) -> None:
        """Ordinary leading zeros do not narrow the caller's usable value range."""
        assert numeric_input.AsciiWholeNumberReader(maximum, "probe").read(raw) == expected

    @pytest.mark.parametrize("active", [0, 640, 4300, 10000])
    def test_representation_uses_safe_backend_bound(self, monkeypatch: pytest.MonkeyPatch, active: int) -> None:
        """Read backend settings without changing the real system integer limit."""
        monkeypatch.setattr(numeric_input.sys, "get_int_max_str_digits", lambda: active)
        conversion = Mock(wraps=int)
        monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
        limit = min(active or 4300, 4300)
        reader = numeric_input.AsciiWholeNumberReader(3, "tier")
        assert reader.read("0" * limit) == 0
        assert conversion.call_args_list == [call("0")]
        conversion.reset_mock()
        assert reader.read("0" * (limit + 1)) is None
        assert conversion.call_count == 0

    @pytest.mark.parametrize(
        ("reader", "raw", "expected"),
        [("offset", str(sys.maxsize), sys.maxsize), ("tier", "003", 3), ("page_limit", "0001", 1)],
    )
    def test_each_reader_converts_a_usable_boundary_once(
        self, monkeypatch: pytest.MonkeyPatch, reader: str, raw: str, expected: int
    ) -> None:
        """The conversion recorder must detect real calls as well as refusals."""
        conversion = Mock(wraps=int)
        monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
        if reader == "offset":
            with Flask(__name__).test_request_context(query_string={"offset": raw}):
                assert select.read_whole_number("offset", 7) == expected
        elif reader == "tier":
            assert capture.read_tier({"tier": raw}) == expected
        else:
            monkeypatch.setenv("MIST_PAGE_LIMIT", raw)
            assert clients.page_limit() == expected
        assert conversion.call_args_list == [call(raw.lstrip("0"))]


class TestNumericReaderProperties:
    """Generate ASCII and non-ASCII inputs through all three real readers."""

    @settings(max_examples=100, derandomize=True, database=None)
    @given(
        raw=st.text(
            alphabet=st.characters(min_codepoint=128, categories=("Nd", "No")),
            min_size=1,
            max_size=40,
        )
    )
    def test_non_ascii_input_never_reaches_conversion(self, raw: str) -> None:
        """Generated Unicode number text always selects each caller's refusal."""
        application = Flask(__name__)
        with pytest.MonkeyPatch.context() as patches:
            conversion = Mock(wraps=int)
            patches.setattr(numeric_input, "int", conversion, raising=False)
            with application.test_request_context(query_string={"offset": raw}):
                assert select.read_whole_number("offset", 7) == 7
            assert capture.read_tier({"tier": raw}) is None
            patches.setenv("MIST_PAGE_LIMIT", raw)
            assert clients.page_limit() == 1000
            assert conversion.call_count == 0

    @settings(max_examples=100, derandomize=True, database=None)
    @given(number=st.integers(min_value=0, max_value=sys.maxsize), zeros=st.integers(min_value=0, max_value=32))
    def test_ascii_values_keep_caller_decisions(self, number: int, zeros: int) -> None:
        """Generated ASCII values keep offsets, tier membership, and page clamps."""
        raw = "0" * zeros + str(number)
        application = Flask(__name__)
        with application.test_request_context(query_string={"offset": f" \t+{raw}\n"}):
            assert select.read_whole_number("offset", 7) == number
        assert capture.read_tier({"tier": raw}) == (number if number in (2, 3) else None)
        with pytest.MonkeyPatch.context() as environment:
            environment.setenv("MIST_PAGE_LIMIT", f" \t{raw}\n")
            assert clients.page_limit() == max(1, min(1000, number))

    def test_every_representable_ascii_non_digit_is_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Check the complete ASCII non-digit corpus that the environment can store."""
        application = Flask(__name__)
        characters = [chr(code) for code in range(1, 128) if not chr(code).isdigit()]
        checked = 0
        for raw in characters:
            with application.test_request_context(query_string={"offset": raw}):
                assert select.read_whole_number("offset", 7) == 7, ord(raw)
            assert capture.read_tier({"tier": raw}) is None, ord(raw)
            monkeypatch.setenv("MIST_PAGE_LIMIT", raw)
            assert clients.page_limit() == 1000, ord(raw)
            checked += 3
        assert len(characters) == 117
        assert checked == 351
        print(f"The corpus checked {checked} reader decisions for {len(characters)} ASCII non-digits.")

    def test_nul_query_and_tier_text_are_refused(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The host cannot store NUL in an environment value, but request text can contain it."""
        conversion = Mock(wraps=int)
        monkeypatch.setattr(numeric_input, "int", conversion, raising=False)
        with Flask(__name__).test_request_context(query_string={"offset": "\x00"}):
            assert select.read_whole_number("offset", 7) == 7
        assert capture.read_tier({"tier": "\x00"}) is None
        assert conversion.call_count == 0
        print("The corpus checked 2 NUL request reader decisions. The environment cannot store NUL.")
