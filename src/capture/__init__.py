"""Capture package init with lazy imports to avoid heavy runtime deps on import.

Importing `requests` and other network libraries at package import time causes
pytest collection to fail when those optional deps aren't available. Export
the public symbols lazily so unit tests that don't exercise capture code can
import the package without pulling heavy dependencies.
"""

from importlib import import_module  # Lazy import helper


def __getattr__(name: str):
	"""Lazy-load capture submodules on attribute access.

	This defers importing heavy modules (packet_capture) until tests actually
	need them, reducing import-time side effects during collection.
	"""
	if name == "PacketCaptureManager":
		mod = import_module("src.capture.packet_capture")  # Import when requested
		val = getattr(mod, "PacketCaptureManager")
		globals()[name] = val  # Cache for subsequent accesses
		return val
	raise AttributeError(name)


def __dir__():
	return ["PacketCaptureManager"]

__all__ = ["PacketCaptureManager"]
