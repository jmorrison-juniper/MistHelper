"""Hypothesis property test for issue #429 logging f-string conversion.

Proves that converting a small canonical set of f-string patterns to
lazy `%s`-style logging arguments preserves the rendered string for any
input the project realistically uses. This complements the parity test
(which checks a frozen baseline of real call sites) by exhaustively
covering the format-spec / conversion semantics that the codemod will
have to emit.
"""

from __future__ import annotations  # Enable PEP 604 union syntax on Python 3.13.

import logging  # We render through LogRecord.getMessage(), same as production.

from hypothesis import given  # Property-based test framework.
from hypothesis import strategies as st


def _lazy_render(template: str, *args: object) -> str:
    """Render via LogRecord.getMessage() to exercise the real lazy path."""
    record = logging.LogRecord(  # Synthesize a record the way the framework does.
        name="issue429_property",
        level=logging.INFO,
        pathname=__file__,
        lineno=0,
        msg=template,
        args=args,
        exc_info=None,
    )
    return record.getMessage()  # The string the real logger would emit.


@given(value=st.text(min_size=0, max_size=50))  # Cover all string inputs including empty.
def test_plain_fstring_matches_lazy_string(value: str) -> None:
    """`f"x={value}"` and `"x=%s" % (value,)` must render identically."""
    eager = f"x={value}"  # Eager (pre-refactor) form.
    lazy = _lazy_render("x=%s", value)  # Lazy (post-refactor) form via LogRecord.
    assert eager == lazy  # Conversion preserves bytes for arbitrary strings.


@given(value=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_float_2f_format_spec_matches(value: float) -> None:
    """`f"{value:.2f}"` and `"%.2f" % (value,)` must render identically."""
    eager = f"{value:.2f}"  # Eager form with `.2f` spec.
    lazy = _lazy_render("%.2f", value)  # Lazy form using `%`-style equivalent.
    assert eager == lazy  # Numeric formatting must round-trip.


@given(value=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
def test_float_1f_format_spec_matches(value: float) -> None:
    """`f"{value:.1f}"` and `"%.1f" % (value,)` must render identically."""
    eager = f"{value:.1f}"  # Eager form with `.1f` spec.
    lazy = _lazy_render("%.1f", value)  # Lazy form using `%`-style equivalent.
    assert eager == lazy  # Single-decimal formatting must round-trip.


@given(value=st.integers(min_value=-(2**31), max_value=2**31 - 1))
def test_integer_d_format_spec_matches(value: int) -> None:
    """`f"{value:d}"` and `"%d" % (value,)` must render identically."""
    eager = f"{value:d}"  # Eager form with `d` spec.
    lazy = _lazy_render("%d", value)  # Lazy form using `%`-style equivalent.
    assert eager == lazy  # Integer formatting must round-trip.


@given(
    a=st.text(min_size=0, max_size=20),  # Cover empty + arbitrary strings.
    b=st.integers(min_value=-1000, max_value=1000),  # Cover negative + zero + positive ints.
)
def test_multi_arg_template_matches(a: str, b: int) -> None:
    """`f"a={a} b={b}"` and `"a=%s b=%d" % (a, b)` must render identically."""
    eager = f"a={a} b={b}"  # Eager form with two substitutions.
    lazy = _lazy_render("a=%s b=%d", a, b)  # Lazy form with two positional args.
    assert eager == lazy  # Multi-arg conversion must preserve order and formatting.


@given(value=st.one_of(st.integers(), st.text(min_size=0, max_size=30), st.floats(allow_nan=False)))
def test_str_conversion_matches(value: object) -> None:
    """`f"{value!s}"` and `"%s" % (value,)` must render identically."""
    eager = f"{value!s}"  # Eager form using `!s` explicit conversion.
    lazy = _lazy_render("%s", value)  # Lazy form -- `%s` is documented equivalent.
    assert eager == lazy  # Conversion preserves bytes for any str-able value.


@given(value=st.one_of(st.integers(), st.text(min_size=0, max_size=30)))
def test_repr_conversion_matches(value: object) -> None:
    """`f"{value!r}"` and `"%r" % (value,)` must render identically."""
    eager = f"{value!r}"  # Eager form using `!r` repr conversion.
    lazy = _lazy_render("%r", value)  # Lazy form -- `%r` is documented equivalent.
    assert eager == lazy  # repr conversion preserves bytes for any repr-able value.
