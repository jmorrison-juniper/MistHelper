"""Guest portal SMS provider test feature package."""

from __future__ import annotations  # WHY: keep annotations consistent across this Python 3.13 package.

from src.mist.intelligence.troubleshooting.sms_provider_test.operation import (
    SmsProviderTest,
)  # WHY: expose the menu handler class.

__all__ = ["SmsProviderTest"]  # WHY: keep the package export surface to the menu handler only.
