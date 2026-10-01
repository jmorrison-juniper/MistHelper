"""Client session control package for Mist destructive client actions."""

from __future__ import annotations  # WHY: keep annotations stable during Python 3.13 imports.

from src.device.client_session_control.handler import ClientSessionControl  # WHY: expose menu entry class.

__all__ = ["ClientSessionControl"]  # WHY: define the public package surface for wiring imports.
