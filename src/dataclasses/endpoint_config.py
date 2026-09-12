"""EndpointConfig -- const-endpoint descriptor dataclass.

Extracted from MistHelper.py during initiative 1013 (Cat B, position 16).
Used exclusively by ``ConstDefinitionsExporter`` to describe each discovered
Mist const endpoint (name, module, function, output filename, description,
and optional special-handling flag). Callers continue to reach it through the
``MistHelper.EndpointConfig`` re-export alias.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on Python 3.9+.

from dataclasses import dataclass  # The standard library dataclass decorator.


@dataclass
class EndpointConfig:  # Const endpoint descriptor.
    """Configuration for a discovered const endpoint."""

    endpoint_name: str  # Endpoint name.
    module: object  # Source module.
    function_name: str  # API function name.
    filename: str  # Output filename.
    description: str  # Human description.
    modname: str  # Module path.
    special_handling: str | None = None  # 'all_models', 'all_countries', 'all_countries_channels', or None
