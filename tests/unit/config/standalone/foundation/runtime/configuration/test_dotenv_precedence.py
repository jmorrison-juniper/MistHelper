"""Tests for fallback .env precedence."""

from __future__ import annotations  # WHY: keep annotations lightweight during tests.

import os  # WHY: assertions inspect the environment after the fallback parser runs.

import pytest  # WHY: monkeypatch isolates each environment test.

import MistHelper  # WHY: tests exercise the root fallback parser used at startup.


def test_apply_dotenv_line_preserves_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fallback parser must not replace a value from the process environment."""
    monkeypatch.setenv("RRM_DRY_RUN", "true")  # WHY: model the higher-precedence process environment.
    MistHelper._apply_dotenv_line("RRM_DRY_RUN=false")  # WHY: model a conflicting lower-precedence .env value.
    assert os.environ["RRM_DRY_RUN"] == "true", "the process environment must win over .env"


def test_apply_dotenv_line_sets_an_absent_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """The fallback parser must still load an absent environment value."""
    monkeypatch.delenv("RRM_DRY_RUN", raising=False)  # WHY: prove the normal fallback load path.
    MistHelper._apply_dotenv_line("RRM_DRY_RUN=true")  # WHY: load the value from the .env line.
    assert os.environ["RRM_DRY_RUN"] == "true", "the fallback must load an absent value"
