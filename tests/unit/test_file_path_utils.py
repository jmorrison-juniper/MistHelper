"""Unit tests for src.utils.file_path_utils.FilePathUtils.

Covers both @staticmethod entry points end-to-end using tmp_path:
- get_csv_path: bare name normalization, explicit-directory passthrough, data/ auto-create.
- create_csv_template: header-row write, missing-headers no-write, sample_data discard,
  IO failure re-raise.
"""

from __future__ import annotations  # PEP 604 unions in type hints.

import csv  # Read back the header row for round-trip assertions.
import os  # cwd manipulation + path assertions.
from unittest.mock import patch  # Force open() to raise for the failure-path test.

import pytest  # Fixtures + expected-exception assertions.

from src.utils.file_path_utils import FilePathUtils  # System under test.


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Redirect the module's data/ scratch dir to a tmp path per-test."""
    monkeypatch.chdir(tmp_path)  # Any relative 'data/' becomes tmp_path/data/.
    yield tmp_path  # Hand the sandbox to the test body.


# ---------------------------------------------------------------------------
# get_csv_path
# ---------------------------------------------------------------------------


def test_get_csv_path_bare_name_joins_under_data():
    """Bare filenames should be joined under the data/ directory."""
    result = FilePathUtils.get_csv_path("SiteList.csv")  # Bare name; no directory component.
    assert result == os.path.join("data", "SiteList.csv")  # Portable join under data/.


def test_get_csv_path_creates_data_dir(_isolate_cwd):
    """Calling get_csv_path must create data/ on first use."""
    FilePathUtils.get_csv_path("anything.csv")  # Trigger data/ auto-create.
    assert (_isolate_cwd / "data").is_dir()  # data/ now exists under tmp cwd.


def test_get_csv_path_idempotent_on_existing_dir(_isolate_cwd):
    """Repeated calls must not raise even when data/ already exists."""
    (_isolate_cwd / "data").mkdir()  # Pre-create data/ to prove idempotence.
    result = FilePathUtils.get_csv_path("again.csv")  # Should not raise on existing dir.
    assert result == os.path.join("data", "again.csv")  # Path still normalizes.


def test_get_csv_path_explicit_dir_returns_verbatim():
    """When the caller passes a path with a directory, respect it verbatim."""
    explicit = os.path.join("elsewhere", "custom.csv")  # Contains a directory component.
    assert FilePathUtils.get_csv_path(explicit) == explicit  # No re-anchoring under data/.


def test_get_csv_path_nested_explicit_dir_returns_verbatim(_isolate_cwd):
    """Deep explicit paths should also pass through untouched."""
    explicit = str(_isolate_cwd / "sub" / "dir" / "file.csv")  # Absolute nested path.
    assert FilePathUtils.get_csv_path(explicit) == explicit  # Preserved as-is.


# ---------------------------------------------------------------------------
# create_csv_template
# ---------------------------------------------------------------------------


def test_create_csv_template_writes_header_row(_isolate_cwd):
    """Providing headers must emit a single header row to the file."""
    headers = ["col_a", "col_b", "col_c"]  # Header row to persist.
    path = FilePathUtils.create_csv_template("template.csv", headers=headers)  # Write template.
    assert path == os.path.join("data", "template.csv")  # Returned path is data/-anchored.
    with open(path, encoding="utf-8", newline="") as f:  # Read the written file back.
        rows = list(csv.reader(f))  # Parse the CSV rows.
    assert rows == [headers]  # Only the header row was written.


def test_create_csv_template_no_headers_writes_empty_file(_isolate_cwd):
    """Omitting headers must produce an empty (zero-byte) CSV placeholder."""
    path = FilePathUtils.create_csv_template("empty.csv")  # No header list supplied.
    assert os.path.getsize(path) == 0  # File exists but has no content.


def test_create_csv_template_sample_data_ignored(_isolate_cwd):
    """The sample_data parameter must be discarded even when passed."""
    path = FilePathUtils.create_csv_template(
        "ignored.csv",
        headers=["only", "the", "headers"],
        sample_data=[["should", "be", "dropped"]],  # Intentionally provided but must not be written.
    )
    with open(path, encoding="utf-8", newline="") as f:  # Read written file.
        rows = list(csv.reader(f))  # Parse.
    assert rows == [["only", "the", "headers"]]  # Sample data was discarded.


def test_create_csv_template_reraises_on_io_error(_isolate_cwd):
    """When the underlying open() fails, the error must be re-raised."""
    with patch("src.utils.file_path_utils.open", side_effect=PermissionError("nope")):  # Force IO failure.
        with pytest.raises(PermissionError):  # Caller must observe the exception.
            FilePathUtils.create_csv_template("boom.csv", headers=["x"])  # Trigger the failure path.


def test_create_csv_template_places_bare_name_under_data(_isolate_cwd):
    """Bare filenames must still land under data/ when the template is written."""
    path = FilePathUtils.create_csv_template("bare.csv", headers=["only"])  # Bare name write.
    assert os.path.commonpath([path, "data"]) == "data"  # File resides under data/.
