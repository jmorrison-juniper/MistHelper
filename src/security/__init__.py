"""Security helpers that protect data before it leaves the cloud read boundary.

The package holds one class today. ``CredentialRedactor`` removes a device
credential from a Mist settings record. Add a new module here when a control
must apply to every caller instead of one call site.
"""

from src.security.credential_redaction import CredentialRedactor  # Re-export the one public class.

__all__ = ["CredentialRedactor"]  # Name the supported import surface for a reader and for a linter.
