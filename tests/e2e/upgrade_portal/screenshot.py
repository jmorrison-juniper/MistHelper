"""Capture full-page browser evidence with one transient Chromium retry."""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from playwright.sync_api import Error as PlaywrightError

logger = logging.getLogger(__name__)
SCREENSHOT_RETRY_MESSAGE = "Unable to capture screenshot"


def capture_full_page_screenshot(screenshot: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Capture one full-page screenshot and retry the known protocol failure."""
    logger.info("Capture the full-page screenshot")
    try:
        result = screenshot(*args, **kwargs)
    except PlaywrightError as error:
        if SCREENSHOT_RETRY_MESSAGE not in str(error):
            raise
        logger.warning("Retry the full-page screenshot after a Chromium protocol failure")
        result = screenshot(*args, **kwargs)
    logger.debug("Captured the full-page screenshot")
    return result


def install_screenshot_retry(page: Any) -> Any:
    """Install the retry on one Playwright page and return that page."""
    original_screenshot = page.screenshot

    def screenshot(*args: Any, **kwargs: Any) -> Any:
        if kwargs.get("full_page") is not True:
            return original_screenshot(*args, **kwargs)
        return capture_full_page_screenshot(original_screenshot, *args, **kwargs)

    page.screenshot = screenshot
    return page
