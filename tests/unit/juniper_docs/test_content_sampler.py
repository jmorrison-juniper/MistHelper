"""Unit tests for the content sampler (T034, FR-022, FR-025)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.juniper_docs.classify.content_sampler import ContentSampler
from tests.unit.juniper_docs.conftest import FIXTURES


def test_sampler_reads_up_to_the_page_cap() -> None:
    """The sampler reads the title, the contents, and the first body pages."""
    text = ContentSampler(max_sample_pages=8).sample(FIXTURES / "sample_uncategorized.pdf")
    assert "SRX Series Configuration" in text  # The title page is in the sample.
    assert "UNIQUE-BODY-MARKER-DO-NOT-PERSIST-7F3A" in text  # A page within the cap.
    assert "OUTSIDE-SAMPLE-9Z" not in text  # Page nine is beyond the eight-page cap.


def test_sampler_returns_one_string() -> None:
    """The sampler returns the bounded sample as a single string."""
    text = ContentSampler().sample(FIXTURES / "sample_uncategorized.pdf")  # Read the sample.
    assert isinstance(text, str)  # The sample is one local string.


def test_sampler_returns_empty_for_an_image_only_pdf() -> None:
    """A PDF with no readable text yields an empty sample for the fallback."""
    text = ContentSampler().sample(FIXTURES / "image_only.pdf")  # Read the image-only PDF.
    assert text.strip() == ""  # No readable text means an empty sample.


def test_sampler_returns_empty_for_a_missing_file(tmp_path: Path) -> None:
    """A missing or malformed file yields an empty sample without a crash."""
    text = ContentSampler().sample(tmp_path / "absent.pdf")  # Point at a missing file.
    assert text == ""  # A read failure yields an empty sample (FR-025).


def test_sampler_returns_empty_when_the_library_is_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    """An absent pdfplumber library disables sampling and yields the fallback."""

    def _raise_import(_name: str) -> object:
        """Raise ImportError to simulate a missing pdfplumber library."""
        raise ImportError("pdfplumber is not installed")  # The absent-library signal.

    monkeypatch.setattr(
        "src.juniper_docs.classify.content_sampler.importlib.import_module", _raise_import
    )  # Force the import to fail.
    text = ContentSampler().sample(FIXTURES / "sample_uncategorized.pdf")  # Sample the PDF.
    assert text == ""  # A missing library yields an empty sample.
