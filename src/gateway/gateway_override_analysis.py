"""Compatibility alias module for gateway WAN override analyzer implementation."""

from src.gateway.gateway_override_analyzer import (
    GatewayOverrideAnalyzer,
    configure_gateway_override_analyzer_dependencies,
)

__all__ = [
    "GatewayOverrideAnalyzer",
    "configure_gateway_override_analyzer_dependencies",
]
