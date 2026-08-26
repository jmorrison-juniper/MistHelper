"""Import smoke tests for the two script packages that use openai.

These tests load the packages and assert that the names each package
imports from openai still exist on the installed version. The tests
need no API key and no network call.

A green run proves that a major openai bump did not remove a name the
scripts depend on. Issue #1948 records the motivation.
"""

import types

import pytest

openai = pytest.importorskip(  # Skip the test if openai is not installed.
    "openai",
    reason="openai is not installed in this environment. The test runs in CI.",
)


def test_openai_exposes_openai_class() -> None:
    """Assert that the OpenAI class still exists on the installed openai package.

    Both script packages import OpenAI at module scope. A major bump that
    renames or removes the class would break the scripts before any operator
    notices.
    """
    assert hasattr(
        openai, "OpenAI"
    ), (  # Both scripts import OpenAI from openai.
        "openai.OpenAI is missing. The scripts/mist_ideas_* packages cannot import it."
    )
    assert isinstance(  # Confirm the attribute is a class, not a non-callable.
        openai.OpenAI, type
    ), "openai.OpenAI is not a class. The scripts expect a callable client constructor."


def test_openai_exposes_rate_limit_error() -> None:
    """Assert that RateLimitError still exists on the installed openai package.

    scripts/mist_ideas_analyzer_pkg/__init__.py imports RateLimitError at
    line 41 to catch rate-limit responses from the API. A bump that removes
    or renames that exception would raise an ImportError at startup.
    """
    assert hasattr(
        openai, "RateLimitError"
    ), "openai.RateLimitError is missing. mist_ideas_analyzer_pkg cannot import it."  # analyzer imports RateLimitError.
    assert issubclass(  # Confirm the attribute is an exception subclass.
        openai.RateLimitError, BaseException
    ), "openai.RateLimitError is not an exception. The scripts expect it to be catchable."


def test_analyzer_package_imports() -> None:
    """Assert that the analyzer package loads without a ModuleNotFoundError.

    scripts/mist_ideas_analyzer_pkg/__init__.py imports openai at module
    scope on line 41. If openai is installed and its public names are intact,
    the package must import cleanly.
    """
    import scripts.mist_ideas_analyzer_pkg as pkg  # Import the real package to verify it loads.

    assert isinstance(
        pkg, types.ModuleType
    ), "scripts.mist_ideas_analyzer_pkg did not load as a module."  # Confirm the import returned a module.


def test_distiller_package_imports() -> None:
    """Assert that the distiller package loads without a ModuleNotFoundError.

    scripts/mist_ideas_distiller_v2_pkg/__init__.py imports openai at module
    scope on line 32. If openai is installed and its public names are intact,
    the package must import cleanly.
    """
    import scripts.mist_ideas_distiller_v2_pkg as pkg  # Import the real package to verify it loads.

    assert isinstance(
        pkg, types.ModuleType
    ), "scripts.mist_ideas_distiller_v2_pkg did not load as a module."  # Confirm the import returned a module.
