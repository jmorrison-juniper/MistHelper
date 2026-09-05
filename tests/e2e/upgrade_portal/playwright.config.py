"""Playwright settings for the browser tests of the upgrade capture portal.

Why:
    The interface test identifier contract fixes four Playwright settings for
    this feature. See ``specs/1823-upgrade-capture-portal/contracts/ui-testids.md``.
    This module holds the four values in one place, so the browser fixtures and
    a manual command read the same source. The repository holds no other
    Playwright configuration today, so this file starts the pattern.

    The file name holds a dot, so no module can import it by name. The browser
    fixtures load it by path. See ``conftest.py`` in this directory.
"""

from __future__ import annotations

from typing import Final

# WHY: The capture portal answers on port 8056. Every browser test opens this
# address. The value repeats in conftest.py, which reads it from here.
BASE_URL: Final[str] = "http://127.0.0.1:8056"

# WHY: The four keys use the Playwright names, so a reader can compare this
# table against the table in contracts/ui-testids.md line for line.
PLAYWRIGHT_CONFIG: Final[dict[str, str]] = {
    "screenshot": "only-on-failure",  # WHY: The specification asks for a screenshot on a failed test.
    "trace": "retain-on-failure",  # WHY: The specification asks for a trace on a failed test.
    "testIdAttribute": "data-testid",  # WHY: Makes get_by_test_id match the identifier contract.
    "baseURL": BASE_URL,  # WHY: The default portal port.
}


def command_line_options() -> list[str]:
    """Return the Playwright command-line options for this feature.

    Why:
        An operator runs the browser tests by hand during development. This
        function turns the settings above into the exact option list, so a
        manual run and an automated run behave the same way.

    Returns:
        The option strings in a stable order.
    """
    screenshot = PLAYWRIGHT_CONFIG["screenshot"]  # WHY: A local name keeps each option line short.
    trace = PLAYWRIGHT_CONFIG["trace"]  # WHY: The pytest option name is --tracing, not --trace.
    base_url = PLAYWRIGHT_CONFIG["baseURL"]  # WHY: The pytest option name is --base-url.
    return [  # WHY: Each setting maps onto one pytest-playwright option.
        f"--screenshot={screenshot}",
        f"--tracing={trace}",
        f"--base-url={base_url}",
    ]
