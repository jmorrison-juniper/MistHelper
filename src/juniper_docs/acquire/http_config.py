"""HTTP and TLS configuration for every harvester request.

This module holds the base origin, the request headers, the timeout, and the
polite delay. It also builds the SSL context for the three TLS modes. The
preferred mode verifies the chain through the repository Zscaler root CA. The
insecure mode is a configurable fallback that carries one justified annotation.
"""

from __future__ import annotations  # Enable modern union syntax on every annotation.

import logging  # Emit the loud warning when verification is disabled.
import ssl  # Build the SSL context for each TLS mode.
from pathlib import Path  # Locate the repository root CA file in a portable way.

_LOGGER = logging.getLogger(__name__)  # Module logger for the TLS decisions.


class HttpConfig:
    """Bundle the origin, headers, timeout, delay, and the chosen SSL context."""

    SITE = "https://www.juniper.net"  # Base origin for every documentation request.
    HEADERS = {"User-Agent": "Mozilla/5.0"}  # The site rejects a default agent string.
    TIMEOUT_SECONDS = 90  # Generous per-request timeout because some PDFs are large.
    INITIAL_TIMEOUT_SECONDS = 15  # Short timeout for a host that has not yet answered.
    DELAY_SECONDS = 1.0  # Polite pause so the crawl does not overload the host.
    CA_FILE_NAME = "zscaler-root-ca.crt"  # Corporate proxy root CA in the repository.

    def __init__(
        self,
        ssl_context: ssl.SSLContext,
        timeout_seconds: int = TIMEOUT_SECONDS,
        delay_seconds: float = DELAY_SECONDS,
        initial_timeout_seconds: int = INITIAL_TIMEOUT_SECONDS,
    ) -> None:
        """Store the SSL context, both timeouts, and the polite delay."""
        self.ssl_context = ssl_context  # The verified or insecure SSL context.
        self.timeout_seconds = timeout_seconds  # Seconds before a request times out.
        self.delay_seconds = delay_seconds  # Seconds to wait between two requests.
        self.initial_timeout_seconds = initial_timeout_seconds  # Short wait until a host answers.

    @classmethod
    def from_tls_mode(cls, mode: str, ca_path: Path | None = None) -> HttpConfig:
        """Return a config whose SSL context matches the requested TLS mode."""
        _LOGGER.info("Building the HTTP config for TLS mode %s", mode)  # Log the intent.
        context = cls.build_ssl_context(mode, ca_path)  # Select the SSL context.
        _LOGGER.debug("HTTP config ready with verify_mode %s", context.verify_mode)  # Result.
        return cls(context)  # Return the config with the default timeout and delay.

    @classmethod
    def build_ssl_context(cls, mode: str, ca_path: Path | None = None) -> ssl.SSLContext:
        """Return the SSL context for the TLS mode auto, verify, or insecure."""
        ca_file = cls._resolve_ca_path(ca_path)  # Find the corporate root CA file.
        if mode == "insecure":  # The operator forced verification off.
            return cls._insecure_context()  # Return the documented fallback context.
        if mode == "verify":  # The operator forced verification on.
            return cls._verified_context(ca_file)  # Always verify, never fall back.
        return cls._auto_context(ca_file)  # Auto: verify when the CA is present.

    @classmethod
    def _auto_context(cls, ca_file: Path | None) -> ssl.SSLContext:
        """Return a verified context when the CA is present, else the fallback."""
        if ca_file is not None and ca_file.exists():  # The corporate CA is available.
            _LOGGER.info("Using CA-verified TLS through %s", ca_file.name)  # Log intent.
            return cls._verified_context(ca_file)  # Verify the chain through the CA.
        _LOGGER.warning("Root CA %s is absent; TLS verification is OFF", cls.CA_FILE_NAME)
        return cls._insecure_context()  # Fall back only when no CA is present.

    @classmethod
    def _verified_context(cls, ca_file: Path | None) -> ssl.SSLContext:
        """Return a context that verifies the chain and trusts the corporate CA."""
        _LOGGER.info("Creating a verified SSL context")  # Log before the build.
        context = ssl.create_default_context()  # System trust store, CERT_REQUIRED.
        if ca_file is not None and ca_file.exists():  # Add the corporate root CA.
            context.load_verify_locations(cafile=str(ca_file))  # Trust the proxy root.
        _LOGGER.debug("Verified context built, check_hostname %s", context.check_hostname)
        return context  # A connection now verifies the server certificate chain.

    @staticmethod
    def _insecure_context() -> ssl.SSLContext:
        """Return an unverified context, the documented insecure fallback.

        Security note: this path disables certificate verification. It exists so
        the crawl still runs behind a proxy whose root CA does not validate on
        this host. The single annotation below is the only allowed suppression;
        the preferred fix is CA-verified TLS through the Zscaler root CA.
        """
        _LOGGER.warning("TLS verification is DISABLED; run only behind a trusted proxy")
        return ssl._create_unverified_context()  # nosec B323  # Documented fallback only.

    @classmethod
    def _resolve_ca_path(cls, ca_path: Path | None) -> Path | None:
        """Return the explicit CA path, or the repository root CA file."""
        if ca_path is not None:  # The caller named an explicit CA file.
            return ca_path  # Honor the operator choice.
        return Path(__file__).resolve().parents[3] / cls.CA_FILE_NAME  # Repo root CA.
