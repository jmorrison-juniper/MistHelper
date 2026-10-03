"""Single control for TLS certificate verification.

The application had seven independent decisions about certificate
verification. Five of them defaulted to insecure, and two defaulted to
secure. A reader could not tell which default applied to a given run.
This module holds one decision, so every caller agrees.

Warning: A disabled check lets any host present any certificate. The
traffic carries a live Mist API token. Disable the check only when a
corporate proxy inspects TLS, and prefer a mounted certificate
authority bundle instead.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)  # Module logger, because the root logger hides the source.

# The operator sets this variable to turn the check off. Absent means on.
SKIP_VERIFY_ENV_VAR = "MIST_SKIP_SSL_VERIFY"

# These tokens turn the check off. Every other value keeps the check on.
_DISABLE_TOKENS = frozenset({"true", "1", "yes", "on"})


class TLSVerificationPolicy:
    """Decide whether to verify a TLS certificate, and report the decision."""

    _warned = False  # Class flag, because one warning per run is enough.

    @staticmethod
    def skip_verification() -> bool:
        """Return True only when the operator asked to skip the check.

        The default is secure. An unset variable keeps verification on.
        """
        raw = os.environ.get(SKIP_VERIFY_ENV_VAR, "").strip().lower()  # Absent reads as an empty string.
        skip = raw in _DISABLE_TOKENS  # Opt in only, because an unknown value must stay secure.
        if skip:  # Announce the weakened state, because a silent bypass hides itself.
            TLSVerificationPolicy.warn_once()  # Emit the operator warning one time.
        return skip  # Callers invert this to build a verify flag.

    @staticmethod
    def verify_enabled() -> bool:
        """Return True when the caller must verify the certificate."""
        return not TLSVerificationPolicy.skip_verification()  # Positive form for a requests verify flag.

    @staticmethod
    def warn_once() -> None:
        """Log one WARNING for the run that TLS verification is off."""
        if TLSVerificationPolicy.reported():  # Skip a repeat, because a loop would flood the log.
            return  # Nothing more to do for this run.
        TLSVerificationPolicy._warned = True  # Latch before the log call, because the log can raise.
        logger.warning(  # ASCII only, because the project forbids Unicode in a log line.
            "TLS certificate verification is OFF because %s is set. "
            "An attacker on the network path can read the Mist API token. "
            "Unset %s, or mount the corporate certificate authority bundle instead.",
            SKIP_VERIFY_ENV_VAR,
            SKIP_VERIFY_ENV_VAR,
        )

    @staticmethod
    def reported() -> bool:
        """Return True when this run already logged the warning."""
        return TLSVerificationPolicy._warned  # Read the latch for the caller and the tests.

    @staticmethod
    def reset() -> None:
        """Clear the warning latch so a test can observe the first warning."""
        TLSVerificationPolicy._warned = False  # Tests need a clean latch between cases.
