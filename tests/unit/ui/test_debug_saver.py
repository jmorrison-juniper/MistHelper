"""Unit tests for src/ui/execution/debug_saver.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ui.execution.debug_saver import DEBUG_DIR, DebugResultSaver, _Serializer


@pytest.fixture(autouse=True)
def _isolated_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run each test inside an isolated tmp dir so DEBUG_DIR is throwaway."""
    monkeypatch.chdir(tmp_path)  # Sandboxed working dir
    return tmp_path


def test_save_writes_json_artifact(tui_stub, _isolated_cwd: Path) -> None:
    """save() creates a timestamped JSON file under data/tui_debug_results/."""
    tui_stub.function_params = {"org_id": "abc"}  # Simulate captured params
    DebugResultSaver(tui_stub).save("listOrgs", {"data": 1}, {"parsed": True})  # Trigger save
    files = list((_isolated_cwd / DEBUG_DIR).glob("listOrgs_*.json"))  # Find artifact
    assert len(files) == 1  # Exactly one artifact
    payload = json.loads(files[0].read_text(encoding="utf-8"))  # Read it back
    assert payload["function"] == "listOrgs"  # Function name preserved
    assert payload["parameters"] == {"org_id": "abc"}  # Params captured
    assert payload["raw_response"] == {"data": 1}  # Raw preserved
    assert payload["parsed_data"] == {"parsed": True}  # Parsed preserved


def test_save_redacts_secret_params(tui_stub, _isolated_cwd: Path) -> None:
    """Parameter names containing secret tokens are redacted to ***REDACTED***."""
    tui_stub.function_params = {  # Mix of clean + secret-shaped names
        "username": "alice",
        "password": "s3cret",
        "api_token": "tok",
        "x_api_key": "k",
        "client_secret": "sh",
    }
    DebugResultSaver(tui_stub).save("login", "raw", "parsed")  # Trigger save
    artifact = json.loads(next((_isolated_cwd / DEBUG_DIR).glob("login_*.json")).read_text(encoding="utf-8"))
    params = artifact["parameters"]  # Pull redaction result
    assert params["username"] == "alice"  # Clean name preserved
    assert params["password"] == "***REDACTED***"  # Redacted
    assert params["api_token"] == "***REDACTED***"  # Redacted
    assert params["x_api_key"] == "***REDACTED***"  # Redacted
    assert params["client_secret"] == "***REDACTED***"  # Redacted


def test_save_swallows_write_failure(
    tui_stub, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A serialization failure is logged but does NOT propagate."""
    tui_stub.function_params = {}  # No params

    def _boom(*_a, **_kw) -> None:  # noqa: ANN001
        raise OSError("disk full")

    monkeypatch.setattr("builtins.open", _boom)  # Force open() to fail
    with caplog.at_level("ERROR"):  # Capture error log
        DebugResultSaver(tui_stub).save("fn", None, None)  # Should not raise
    assert any("Failed to save debug result" in r.message for r in caplog.records)


def test_serializer_handles_primitives() -> None:
    """Primitive values pass through unchanged."""
    assert _Serializer.to_jsonable(None) is None  # None
    assert _Serializer.to_jsonable(42) == 42  # int
    assert _Serializer.to_jsonable("abc") == "abc"  # str
    assert _Serializer.to_jsonable(True) is True  # bool
    assert _Serializer.to_jsonable(3.14) == 3.14  # float


def test_serializer_walks_dict_and_list() -> None:
    """Nested dicts/lists are serialized recursively."""
    payload = {"a": [1, 2, {"b": "c"}], "d": (4, 5)}  # Mixed structure
    expected = {"a": [1, 2, {"b": "c"}], "d": [4, 5]}  # Tuples become lists
    assert _Serializer.to_jsonable(payload) == expected


def test_serializer_object_to_dict_includes_attrs_and_type() -> None:
    """Objects with __dict__ are converted to attribute dicts tagged with __type__."""

    class Sample:  # Minimal value object
        def __init__(self) -> None:
            self.name = "alice"  # Public attribute
            self.count = 3  # Another public attribute
            self._private = "hidden"  # Should be skipped (underscore prefix)

        def method(self) -> None:  # Callable -> skipped
            pass

    result = _Serializer.to_jsonable(Sample())  # Run the serializer
    assert result["__type__"] == "Sample"  # Type tag present
    assert result["name"] == "alice"  # Public attr captured
    assert result["count"] == 3  # Public attr captured
    assert "_private" not in result  # Underscore attr skipped
    assert "method" not in result  # Callable skipped


def test_serializer_falls_back_to_str() -> None:
    """Objects without __dict__ fall back to str() (e.g., set)."""

    class _NoDict:
        __slots__ = ()  # No __dict__

        def __str__(self) -> str:  # pragma: no cover - tiny passthrough
            return "no-dict-instance"

    assert _Serializer.to_jsonable(_NoDict()) == "no-dict-instance"


def test_serializer_skips_attribute_access_errors() -> None:
    """An attribute that raises on access is skipped without aborting."""

    class _Raising:
        def __init__(self) -> None:
            self.ok = 1  # Normal attribute

        @property
        def boom(self) -> int:
            raise RuntimeError("nope")  # Always raises

    out = _Serializer.to_jsonable(_Raising())  # Should not raise
    assert out["ok"] == 1  # Clean attribute preserved
    assert "boom" not in out  # Raising one skipped
