#!/usr/bin/env python3
"""Run pytest with preloaded lightweight stubs for problematic display libs.
This script installs minimal stub modules into sys.modules before importing pytest,
preventing ImportError during plugin discovery for packages like dash/plotly.

Usage: python tools/run_pytest_with_stubs.py [pytest-args...]
"""
from __future__ import annotations
import sys
import types

# Minimal stub for plotly.graph_objects.Figure to satisfy dash import path
plotly_mod = types.ModuleType("plotly")
graph_objects_mod = types.ModuleType("plotly.graph_objects")

class Figure:  # simple placeholder class
    pass

# Assign attributes
graph_objects_mod.Figure = Figure
plotly_mod.graph_objects = graph_objects_mod
# Register in sys.modules so imports find our stubs; also create a ModuleSpec-like attribute
plotly_mod.__spec__ = types.SimpleNamespace(name="plotly", loader=None, origin="<stub>")
graph_objects_mod.__spec__ = types.SimpleNamespace(name="plotly.graph_objects", loader=None, origin="<stub>")
sys.modules["plotly"] = plotly_mod
sys.modules["plotly.graph_objects"] = graph_objects_mod
sys.modules["plotly.graph_objs"] = graph_objects_mod

# Minimal stub for plotly.io
plotly_io = types.ModuleType("plotly.io")
sys.modules["plotly.io"] = plotly_io

# Minimal stub for _plotly_utils.utils (used by dash background callbacks)
plotly_utils_mod = types.ModuleType("_plotly_utils")
plotly_utils_utils = types.ModuleType("_plotly_utils.utils")

class PlotlyJSONEncoder:  # simple placeholder encoder
    def default(self, obj):
        # Fallback encoder behavior
        try:
            return obj.__dict__
        except Exception:
            return str(obj)

plotly_utils_utils.PlotlyJSONEncoder = PlotlyJSONEncoder
sys.modules["_plotly_utils"] = plotly_utils_mod
sys.modules["_plotly_utils.utils"] = plotly_utils_utils

# Monkeypatch importlib.metadata.version for 'plotly' to avoid MetadataNotFound
# when dash inspects installed distribution metadata during import. Returning a
# plausible version lets dash proceed while our lightweight stubs satisfy runtime
# imports. This avoids requiring plotly to be installed in the test venv.
try:
    import importlib.metadata as _importlib_metadata  # stdlib (Py3.8+)
except Exception:
    import importlib_metadata as _importlib_metadata

_orig_version = _importlib_metadata.version

def _patched_version(name: str, *args, **kwargs):
    if name == "plotly":
        return "5.14.0"  # plausible plotly version to satisfy dash checks
    return _orig_version(name, *args, **kwargs)

_importlib_metadata.version = _patched_version

# Optionally stub other visualization modules if needed (dash etc.)
# Leave actual dash import to real package; our plotly stubs are usually enough.

# Run pytest with provided args or default to tests/unit
import pytest

pytest_args = sys.argv[1:] or ["tests/unit", "-q", "-ra"]
exit_code = pytest.main(pytest_args)
sys.exit(exit_code)
