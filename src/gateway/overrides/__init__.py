"""WAN override analysis collaborators for GatewayOverrideAnalyzer."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

from .device_data_fetcher import DeviceDataFetcher  # Fetches live port/stats per device
from .override_classifier import OverrideClassifier  # Decides per-row which ports are overridden
from .override_report_writer import OverrideReportWriter  # Persists final CSV + console summary
from .wan_override_walker import WanOverrideWalker  # Top-level façade orchestrator

__all__ = [  # Explicit public surface for the overrides submodule
    "DeviceDataFetcher",
    "OverrideClassifier",
    "OverrideReportWriter",
    "WanOverrideWalker",
]
