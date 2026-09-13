"""The two refusals that guard the rehearsal harness.

Why:
    Design decision 5 of ``specs/1992-upgrade-rehearsal/plan.md`` asks for two
    proofs. The rehearsal must reach no network, and it must write no firmware.
    A silent stand-in cannot prove either fact, because a missing call and a
    refused call look the same in a passing test.

    Each error names its own cause. A test that meets one of them reads the
    exact rule that the run broke, and the report names the line that broke it.
"""

from __future__ import annotations


class RehearsalError(Exception):
    """The parent of every refusal that the rehearsal harness raises."""


class RehearsalNetworkError(RehearsalError):
    """The rehearsal tried to open a network connection."""


class RehearsalFirmwareError(RehearsalError):
    """The rehearsal tried to write firmware to a device."""
