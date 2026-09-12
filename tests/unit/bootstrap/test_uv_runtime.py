"""Wave 7 P2 coverage for src/bootstrap/uv_runtime.py (initiative #1018).

Covers every branch of ``UVRuntimeHelper`` static methods plus
``build_runtime_helpers`` factory:

- ``_parse_numeric_prefix``: digits-only, empty, leading digits + suffix, all
  non-digit, mixed segments.
- ``parse_version``: valid dotted numeric, non-numeric segments, exception
  fallback to ``(0,)`` sentinel.
- ``_split_operator_and_required``: each of the six operators, no operator ->
  ``(">=", "")``, 2-char operators matched before 1-char.
- ``_compare_versions``: every operator with matching + non-matching tuples,
  unknown operator returns True (legacy default).
- ``version_satisfies``: empty installed, no constraint, length-mismatched
  tuples right-padded with zeros, satisfied and violated comparisons.
- ``package_name_from_spec``: with each operator + plain package name +
  surrounding whitespace stripped.
- ``build_runtime_helpers``: returns dict wired to the three static methods.

All logic is pure: no MistHelper import, no filesystem, no subprocess.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of debug breadcrumbs.
from typing import Any  # WHY: annotate the runtime-helpers dict return type.

import pytest  # WHY: parametrize + caplog fixtures.

from src.bootstrap.uv_runtime import (  # WHY: direct SUT imports (module + factory).
    UVRuntimeHelper,
    build_runtime_helpers,
)


class TestParseNumericPrefix:
    """Cover every branch of the digit-prefix extractor helper."""

    @pytest.mark.parametrize(
        ("raw_part", "expected"),
        [
            ("42", 42),  # WHY: pure digits produce the integer value.
            ("0", 0),  # WHY: single-zero segment stays zero.
            ("12abc", 12),  # WHY: digits then alpha terminate at first non-digit.
            ("", 0),  # WHY: empty accumulator returns the legacy zero sentinel.
            ("abc", 0),  # WHY: no leading digits -> zero sentinel.
            ("3rc1", 3),  # WHY: prerelease-style tag stops at the first alpha.
            ("100dev", 100),  # WHY: multi-digit prefix preserved intact.
        ],
    )
    def test_prefix_returns_expected_int(self, raw_part: str, expected: int) -> None:
        """The helper stops accumulating at the first non-digit character."""
        assert UVRuntimeHelper._parse_numeric_prefix(raw_part) == expected  # WHY: exact int contract.


class TestParseVersion:
    """Cover valid, mixed, and failure paths of ``parse_version``."""

    def test_pure_numeric_dotted_version(self) -> None:
        """A clean ``X.Y.Z`` string parses to the matching int tuple."""
        assert UVRuntimeHelper.parse_version("1.2.3") == (1, 2, 3)  # WHY: baseline dotted-numeric contract.

    def test_two_segment_version(self) -> None:
        """Two-segment version returns a 2-tuple (no forced padding here)."""
        assert UVRuntimeHelper.parse_version("10.0") == (10, 0)  # WHY: no implicit third-segment fill.

    def test_single_segment_version(self) -> None:
        """Single-segment version returns a 1-tuple."""
        assert UVRuntimeHelper.parse_version("7") == (7,)  # WHY: no split -> one-element tuple.

    def test_segment_with_suffix_uses_numeric_prefix(self) -> None:
        """Segment with alpha suffix uses only its leading digits."""
        assert UVRuntimeHelper.parse_version("1.2.3rc1") == (1, 2, 3)  # WHY: 'rc1' collapses to 3.

    def test_all_non_numeric_segment_becomes_zero(self) -> None:
        """A pure-alpha segment collapses to the zero legacy sentinel per position."""
        assert UVRuntimeHelper.parse_version("abc.def") == (0, 0)  # WHY: matches legacy behavior.

    def test_broken_input_returns_zero_tuple(self) -> None:
        """Non-string input raises inside the try block and yields the sentinel ``(0,)``."""
        assert UVRuntimeHelper.parse_version(None) == (0,)  # type: ignore[arg-type]  # WHY: legacy contract.


class TestSplitOperatorAndRequired:
    """Cover every branch of the operator/required-version splitter."""

    @pytest.mark.parametrize(
        ("spec", "expected_operator", "expected_required"),
        [
            ("pkg>=1.2.3", ">=", "1.2.3"),  # WHY: 2-char operator matched before '>'.
            ("pkg<=2.0", "<=", "2.0"),  # WHY: 2-char operator matched before '<'.
            ("pkg==1.0", "==", "1.0"),  # WHY: 2-char equality operator.
            ("pkg!=1.0", "!=", "1.0"),  # WHY: 2-char inequality operator.
            ("pkg>0.5", ">", "0.5"),  # WHY: 1-char greater-than falls through.
            ("pkg<9", "<", "9"),  # WHY: 1-char less-than falls through.
            ("pkg", ">=", ""),  # WHY: no operator -> default '>=' + empty required.
            ("pkg>= 1.4 ", ">=", "1.4"),  # WHY: trailing whitespace stripped from required.
        ],
    )
    def test_split_returns_operator_and_required(
        self, spec: str, expected_operator: str, expected_required: str
    ) -> None:
        """The splitter returns the matched operator and the trimmed right-hand version."""
        operator, required = UVRuntimeHelper._split_operator_and_required(spec)  # WHY: parse under test.
        assert operator == expected_operator  # WHY: operator match contract.
        assert required == expected_required  # WHY: required trimmed contract.

    def test_split_emits_debug_log(self, caplog: pytest.LogCaptureFixture) -> None:
        """Every parse emits a debug breadcrumb naming the spec being parsed."""
        with caplog.at_level(logging.DEBUG, logger="root"):  # WHY: helper logs at DEBUG level.
            UVRuntimeHelper._split_operator_and_required("pkg>=1.0")  # WHY: any spec triggers the log.
        assert any("Parsing version spec" in rec.message for rec in caplog.records)  # WHY: log fired.


class TestCompareVersions:
    """Cover every operator branch of ``_compare_versions`` plus the fallback."""

    @pytest.mark.parametrize(
        ("installed", "required", "operator", "expected"),
        [
            ((1, 2, 3), (1, 2, 3), ">=", True),  # WHY: equal satisfies >=.
            ((1, 2, 3), (1, 2, 4), ">=", False),  # WHY: below fails >=.
            ((2, 0, 0), (1, 9, 9), ">", True),  # WHY: strictly greater satisfies >.
            ((1, 0, 0), (1, 0, 0), ">", False),  # WHY: equal fails > (strict).
            ((1, 0, 0), (2, 0, 0), "<=", True),  # WHY: below satisfies <=.
            ((3, 0, 0), (2, 0, 0), "<=", False),  # WHY: above fails <=.
            ((0, 9, 0), (1, 0, 0), "<", True),  # WHY: strictly less satisfies <.
            ((1, 0, 0), (1, 0, 0), "<", False),  # WHY: equal fails < (strict).
            ((1, 2, 3), (1, 2, 3), "==", True),  # WHY: tuples equal.
            ((1, 2, 3), (1, 2, 4), "==", False),  # WHY: differing tuples.
            ((1, 2, 3), (1, 2, 4), "!=", True),  # WHY: unequal satisfies !=.
            ((1, 2, 3), (1, 2, 3), "!=", False),  # WHY: equal fails !=.
            ((1, 0, 0), (1, 0, 0), "~=", True),  # WHY: unknown operator collapses to True (legacy).
        ],
    )
    def test_compare_returns_expected(
        self,
        installed: tuple[int, ...],
        required: tuple[int, ...],
        operator: str,
        expected: bool,
    ) -> None:
        """Every documented operator returns the expected boolean; unknown -> True."""
        assert UVRuntimeHelper._compare_versions(installed, required, operator) is expected  # WHY: bool contract.


class TestVersionSatisfies:
    """Cover the public spec-satisfaction driver end-to-end."""

    def test_empty_installed_returns_false(self) -> None:
        """An empty installed version cannot satisfy any constraint."""
        assert UVRuntimeHelper.version_satisfies("", ">=1.0") is False  # WHY: guard clause.

    def test_no_constraint_returns_true(self) -> None:
        """A spec that carries no version tail is trivially satisfied."""
        assert UVRuntimeHelper.version_satisfies("1.0", "pkg") is True  # WHY: no required version.

    def test_satisfied_gte(self) -> None:
        """Installed above required satisfies >= constraint."""
        assert UVRuntimeHelper.version_satisfies("2.0.0", "pkg>=1.5") is True  # WHY: gte satisfied.

    def test_violated_gte(self) -> None:
        """Installed below required violates >= constraint."""
        assert UVRuntimeHelper.version_satisfies("1.0.0", "pkg>=1.5") is False  # WHY: gte violated.

    def test_length_mismatch_padded_with_zeros(self) -> None:
        """Shorter tuple is right-padded with zeros so comparison is fair."""
        # "1" (1,) vs "1.0.0" (1,0,0) -> pad to (1,0,0) == (1,0,0) -> True.
        assert UVRuntimeHelper.version_satisfies("1", "pkg==1.0.0") is True  # WHY: pad-to-max-len contract.

    def test_length_mismatch_padded_installed_longer(self) -> None:
        """Installed longer than required is also normalized to matching length."""
        assert UVRuntimeHelper.version_satisfies("1.0.0", "pkg==1") is True  # WHY: pad both sides.

    def test_debug_log_emitted(self, caplog: pytest.LogCaptureFixture) -> None:
        """The comparison step emits a debug log with tuple form of both sides."""
        with caplog.at_level(logging.DEBUG, logger="root"):  # WHY: log level check.
            UVRuntimeHelper.version_satisfies("1.0.0", "pkg>=1.0.0")  # WHY: any comparison triggers log.
        assert any("Comparing installed=" in rec.message for rec in caplog.records)  # WHY: log fired.


class TestPackageNameFromSpec:
    """Cover every operator branch plus the plain-name and whitespace cases."""

    @pytest.mark.parametrize(
        ("spec", "expected"),
        [
            ("requests>=2.28", "requests"),  # WHY: 2-char '>=' strips version tail.
            ("requests<=3.0", "requests"),  # WHY: 2-char '<=' strips version tail.
            ("requests==2.28.1", "requests"),  # WHY: '==' strips version tail.
            ("requests!=2.28.1", "requests"),  # WHY: '!=' strips version tail.
            ("requests>2.0", "requests"),  # WHY: 1-char '>' strips version tail.
            ("requests<3.0", "requests"),  # WHY: 1-char '<' strips version tail.
            ("plainpkg", "plainpkg"),  # WHY: no operator leaves spec intact.
            ("  pkg>=1.0  ", "pkg"),  # WHY: surrounding whitespace stripped after operator split.
        ],
    )
    def test_extracts_package_name(self, spec: str, expected: str) -> None:
        """The extractor returns only the package name portion, trimmed."""
        assert UVRuntimeHelper.package_name_from_spec(spec) == expected  # WHY: name-only contract.


class TestBuildRuntimeHelpers:
    """The factory returns a dict wired to the three public static methods."""

    def test_returns_dict_with_three_expected_callables(self) -> None:
        """Factory returns a dict with the three documented keys mapped to the SUT methods."""
        helpers: dict[str, Any] = build_runtime_helpers()  # WHY: exercise the factory once.
        assert set(helpers) == {"parse_version", "version_satisfies", "package_name_from_spec"}  # WHY: key set.
        assert helpers["parse_version"] is UVRuntimeHelper.parse_version  # WHY: identity mapping.
        assert helpers["version_satisfies"] is UVRuntimeHelper.version_satisfies  # WHY: identity mapping.
        assert helpers["package_name_from_spec"] is UVRuntimeHelper.package_name_from_spec  # WHY: identity mapping.

    def test_helpers_are_callable_and_delegate(self) -> None:
        """The returned callables behave identically to the class-level statics."""
        helpers = build_runtime_helpers()  # WHY: fetch the DI bundle.
        assert helpers["parse_version"]("2.1") == (2, 1)  # WHY: proves the callable is the real method.
        assert helpers["version_satisfies"]("2.0", "pkg>=1.0") is True  # WHY: driver reachable through dict.
        assert helpers["package_name_from_spec"]("requests>=2.0") == "requests"  # WHY: name extractor reachable.
