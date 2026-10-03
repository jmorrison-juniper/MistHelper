"""Unit tests for the transient full-page screenshot retry."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest

module = pytest.importorskip("tests.e2e.upgrade_portal.screenshot")


def test_screenshot_retries_the_known_chromium_protocol_failure(tmp_path: Path) -> None:
    """The known Chromium failure receives one retry."""
    page = Mock()
    page.screenshot.side_effect = [
        module.PlaywrightError("Protocol error (Page.captureScreenshot): Unable to capture screenshot"),
        None,
    ]
    path = tmp_path / "journey.png"

    module.capture_full_page_screenshot(page.screenshot, path=str(path), full_page=True)

    assert page.screenshot.call_count == 2
    page.screenshot.assert_called_with(path=str(path), full_page=True)


def test_screenshot_reraises_an_unrelated_playwright_failure(tmp_path: Path) -> None:
    """An unrelated browser failure must not receive a hidden retry."""
    page = Mock()
    error = module.PlaywrightError("Target page, context or browser has been closed")
    page.screenshot.side_effect = error

    with pytest.raises(module.PlaywrightError, match="browser has been closed"):
        module.capture_full_page_screenshot(
            page.screenshot,
            path=str(tmp_path / "journey.png"),
            full_page=True,
        )

    assert page.screenshot.call_count == 1


def test_page_wrapper_retries_direct_full_page_screenshots(tmp_path: Path) -> None:
    """Direct page screenshots receive the same narrow retry."""
    page = Mock()
    page.screenshot.side_effect = [
        module.PlaywrightError("Protocol error (Page.captureScreenshot): Unable to capture screenshot"),
        b"image",
    ]
    original_screenshot = page.screenshot
    wrapped = module.install_screenshot_retry(page)

    result = wrapped.screenshot(path=str(tmp_path / "direct.png"), full_page=True)

    assert result == b"image"
    assert original_screenshot.call_count == 2
