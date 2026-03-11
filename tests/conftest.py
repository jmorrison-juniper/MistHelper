"""Pytest configuration for MistHelper test suite.

Provides test isolation: temp directories, no network, no .env loading.
Unit tests must run offline with zero API credentials in under 30 seconds.
"""

import os
import tempfile

import pytest


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory for test file output."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def tmp_jsonl_file(tmp_data_dir):
    """Provide a temporary JSONL file path for telemetry tests."""
    return str(tmp_data_dir / "test_events.jsonl")


@pytest.fixture(autouse=True)
def isolate_working_directory(tmp_path, monkeypatch):
    """Ensure tests never write to the real data/ directory."""
    monkeypatch.chdir(tmp_path)
