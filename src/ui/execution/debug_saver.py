"""Replacement for ``MistHelperTUI._save_debug_result`` (CC=11)."""

from __future__ import annotations  # Enable PEP 563 postponed annotations for forward refs.

import json  # Serializer for the debug artifact payload.
import logging  # Structured action logs for the save workflow.
import os  # Filesystem path composition and directory creation.
from datetime import datetime  # Timestamp source for filename and payload metadata.
from typing import Any  # Generic typing for opaque API result values.

DEBUG_DIR = os.path.join("data", "tui_debug_results")  # Where debug artifacts land
_SECRET_TOKENS = ("pass", "token", "key", "secret")  # Substrings flagging secret-like keys


class DebugResultSaver:  # Owns the debug artifact write path for one API result.
    """Serialize a TUI API call (raw + parsed) to a timestamped JSON file."""

    def __init__(self, tui: Any) -> None:  # Accept owning TUI so we can read function_params later.
        """Store a back-reference to the owning TUI for access to function_params."""
        self._tui = tui  # Back-reference for function_params

    def save(self, func_name: str, raw_result: Any, parsed_data: Any) -> None:  # Public entry point.
        """Persist the debug artifact for one API call; logs on failure only."""
        logging.info("TUI: saving debug artifact for %s", func_name)  # Action log before write
        try:
            filepath = self._build_filepath(func_name)  # Compose artifact path under DEBUG_DIR
            payload = self._build_payload(func_name, raw_result, parsed_data)  # Compose JSON body
            with open(filepath, "w", encoding="utf-8") as handle:  # Open + dump in one transaction
                json.dump(payload, handle, indent=2, default=str)  # Persist artifact as pretty JSON.
            logging.debug("TUI_DEBUG: Raw result saved to %s", filepath)  # Action log after write
        except Exception as error:  # Never let debug saving raise
            logging.exception("TUI_DEBUG: Failed to save debug result: %s", error)  # Swallow + log.

    @staticmethod
    def _build_filepath(func_name: str) -> str:  # Compose timestamped path under DEBUG_DIR.
        """Compose the artifact file path under ``DEBUG_DIR`` with a timestamp."""
        os.makedirs(DEBUG_DIR, exist_ok=True)  # Ensure the directory exists
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Compact timestamp for filename
        return os.path.join(DEBUG_DIR, f"{func_name}_{timestamp}.json")  # Joined cross-platform path

    def _build_payload(self, func_name: str, raw_result: Any, parsed_data: Any) -> dict[str, Any]:  # Assemble JSON body.
        """Build the JSON-serializable artifact dict (with secret redaction)."""
        return {
            "function": func_name,  # Function name for the artifact
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),  # Same format as filename
            "parameters": self._redact_params(self._tui.function_params),  # Redacted captured params
            "raw_response": _Serializer.to_jsonable(raw_result),  # Recursive APIResponse -> dict
            "parsed_data": parsed_data,  # Already parsed payload
        }

    @staticmethod
    def _redact_params(function_params: dict[str, Any]) -> dict[str, Any]:  # Mask secret-shaped keys.
        """Replace secret-shaped parameter values with ``***REDACTED***``."""
        redacted: dict[str, Any] = {}  # Output dict
        for key, value in function_params.items():  # Walk captured parameters
            if any(token in key.lower() for token in _SECRET_TOKENS):  # Mask secret-shaped names
                redacted[key] = "***REDACTED***"  # Drop sensitive value before serialization.
            else:
                redacted[key] = _Serializer.to_jsonable(value)  # Otherwise serialize value
        return redacted  # Redacted mapping ready for JSON dump.


class _Serializer:  # Internal utility: recursive JSON-safe conversion.
    """Recursive object-to-JSON conversion preserving all attributes."""

    @classmethod
    def to_jsonable(cls, obj: Any) -> Any:  # Dispatch on runtime type to helper methods.
        """Return a JSON-serializable representation of ``obj``."""
        # WHY: dispatching primitive / dict / seq checks to helpers drops CC from 8 to 5.
        if cls._is_primitive(obj):  # Primitives short-circuit without recursion.
            return obj  # Return the primitive value untouched.
        if isinstance(obj, dict):  # Map each value through to_jsonable.
            return cls._dict_to_jsonable(obj)  # Delegate recursive dict conversion.
        if isinstance(obj, (list, tuple)):  # Both sequence forms flatten to a JSON list.
            return cls._sequence_to_jsonable(obj)  # Delegate recursive sequence conversion.
        if hasattr(obj, "__dict__"):  # Any object with attributes walks via _object_to_dict.
            return cls._object_to_dict(obj)  # Attribute walk for objects.
        return str(obj)  # Fallback: str() representation for exotic types.

    @staticmethod
    def _is_primitive(obj: Any) -> bool:
        """Return True for JSON-native scalar types that need no recursion."""
        return obj is None or isinstance(obj, (str, int, float, bool))  # Scalar leaf types.

    @classmethod
    def _dict_to_jsonable(cls, obj: dict[Any, Any]) -> dict[Any, Any]:
        """Recursively serialize each value in a mapping."""
        return {k: cls.to_jsonable(v) for k, v in obj.items()}  # Preserve keys; recurse on values.

    @classmethod
    def _sequence_to_jsonable(cls, obj: Any) -> list[Any]:
        """Recursively serialize each item in a list or tuple."""
        return [cls.to_jsonable(item) for item in obj]  # Flatten tuple/list into JSON list.

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
