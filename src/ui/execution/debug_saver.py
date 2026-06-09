"""Replacement for ``MistHelperTUI._save_debug_result`` (CC=11)."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

DEBUG_DIR = os.path.join("data", "tui_debug_results")  # Where debug artifacts land
_SECRET_TOKENS = ("pass", "token", "key", "secret")  # Substrings flagging secret-like keys


class DebugResultSaver:
    """Serialize a TUI API call (raw + parsed) to a timestamped JSON file."""

    def __init__(self, tui: Any) -> None:
        """Store a back-reference to the owning TUI for access to function_params."""
        self._tui = tui  # Back-reference for function_params

    def save(self, func_name: str, raw_result: Any, parsed_data: Any) -> None:
        """Persist the debug artifact for one API call; logs on failure only."""
        logging.info("TUI: saving debug artifact for %s", func_name)  # Action log before write
        try:
            filepath = self._build_filepath(func_name)  # Compose artifact path under DEBUG_DIR
            payload = self._build_payload(func_name, raw_result, parsed_data)  # Compose JSON body
            with open(filepath, "w", encoding="utf-8") as handle:  # Open + dump in one transaction
                json.dump(payload, handle, indent=2, default=str)
            logging.debug("TUI_DEBUG: Raw result saved to %s", filepath)  # Action log after write
        except Exception as error:  # Never let debug saving raise
            logging.error("TUI_DEBUG: Failed to save debug result: %s", error, exc_info=True)

    @staticmethod
    def _build_filepath(func_name: str) -> str:
        """Compose the artifact file path under ``DEBUG_DIR`` with a timestamp."""
        os.makedirs(DEBUG_DIR, exist_ok=True)  # Ensure the directory exists
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Compact timestamp for filename
        return os.path.join(DEBUG_DIR, f"{func_name}_{timestamp}.json")  # Joined cross-platform path

    def _build_payload(self, func_name: str, raw_result: Any, parsed_data: Any) -> dict[str, Any]:
        """Build the JSON-serializable artifact dict (with secret redaction)."""
        return {
            "function": func_name,  # Function name for the artifact
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),  # Same format as filename
            "parameters": self._redact_params(self._tui.function_params),  # Redacted captured params
            "raw_response": _Serializer.to_jsonable(raw_result),  # Recursive APIResponse -> dict
            "parsed_data": parsed_data,  # Already parsed payload
        }

    @staticmethod
    def _redact_params(function_params: dict[str, Any]) -> dict[str, Any]:
        """Replace secret-shaped parameter values with ``***REDACTED***``."""
        redacted: dict[str, Any] = {}  # Output dict
        for key, value in function_params.items():  # Walk captured parameters
            if any(token in key.lower() for token in _SECRET_TOKENS):  # Mask secret-shaped names
                redacted[key] = "***REDACTED***"
            else:
                redacted[key] = _Serializer.to_jsonable(value)  # Otherwise serialize value
        return redacted


class _Serializer:
    """Recursive object-to-JSON conversion preserving all attributes."""

    @classmethod
    def to_jsonable(cls, obj: Any) -> Any:
        """Return a JSON-serializable representation of ``obj``."""
        if obj is None or isinstance(obj, (str, int, float, bool)):  # Primitives short-circuit
            return obj
        if isinstance(obj, dict):
            return {k: cls.to_jsonable(v) for k, v in obj.items()}  # Recurse dict
        if isinstance(obj, (list, tuple)):
            return [cls.to_jsonable(item) for item in obj]  # Recurse list/tuple
        if hasattr(obj, "__dict__"):
            return cls._object_to_dict(obj)  # Attribute walk for objects
        return str(obj)  # Fallback: str() representation

    @classmethod
    def _object_to_dict(cls, obj: Any) -> dict[str, Any]:
        """Walk an object's public attributes into a plain dict."""
        result: dict[str, Any] = {"__type__": type(obj).__name__}  # Tag with original type name
        for attr_name in dir(obj):  # Walk all attribute names
            if attr_name.startswith("_"):  # Skip private / dunder
                continue
            try:
                attr_value = getattr(obj, attr_name)  # Attempt attribute read
            except Exception:  # nosec B112 — defensive guard against descriptor errors
                continue  # Skip unreadable attribute
            if callable(attr_value):  # Skip methods
                continue
            result[attr_name] = cls.to_jsonable(attr_value)  # Recurse into value
        return result
