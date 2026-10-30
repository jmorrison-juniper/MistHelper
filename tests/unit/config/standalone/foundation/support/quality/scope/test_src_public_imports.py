"""Verify representative public imports after the source move."""  # Preserve the existing behavior.

from __future__ import annotations  # Use current annotation behavior in the import test.

from importlib import import_module  # Load each canonical module without adding compatibility imports.

PUBLIC_IMPORTS = {  # Select stable public symbols from the four new domains.
    "src.foundation.support.utils.operation_registry": "OperationRegistry",
    "src.interfaces.portals.upgrade_portal.app.factory": "create_app",
    "src.interfaces.monitoring.metrics_gateway.web": "create_app",
    "src.mist.realtime.websocket.manager": "WebSocketManager",
    "src.operations.execution.firmware.firmware_manager": "FirmwareManager",
    "src.operations.exporting.export.data_exporter": "DataExporter",
}  # Cover representative classes and factories without importing an old path.


def test_representative_public_symbols_import_from_canonical_modules() -> None:
    """Import each representative symbol from its canonical module."""  # Preserve the existing behavior.
    imported_symbols = {}  # Record each resolved symbol for measured test evidence.
    for module_name, symbol_name in PUBLIC_IMPORTS.items():  # Load every representative public import.
        module = import_module(module_name)  # Import the real moved implementation.
        imported_symbols[module_name] = getattr(
            module, symbol_name
        )  # Require the documented public symbol to remain present.
    assert len(imported_symbols) == len(
        PUBLIC_IMPORTS
    ), f"Imported {len(imported_symbols)} of {len(PUBLIC_IMPORTS)} public symbols"  # Report the measured import count.
