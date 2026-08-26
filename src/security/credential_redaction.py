"""Redact a device credential before a Mist settings record leaves the read boundary.

Why this module exists:
    ``getSiteSetting`` and ``getOrgSettings`` answer a record that carries device
    credentials in clear text. The record holds ``switch_mgmt.root_password``,
    ``juniper_srx.root_password``, and ``ssh_keys``. MistHelper exports what it
    reads, so an unredacted record reaches ``data/AllSiteConfigs.csv``, SQLite,
    ArangoDB, and Redis.

    A redaction at each call site is easy to forget. A new export path would then
    leak again. This module redacts at the read boundary instead, so every
    current caller and every future caller inherits the control.

Reference: GitHub issue #2011.
"""

import copy  # Deep copy so the caller keeps an unchanged input record.
import logging  # Action logging, per the project observability rule.
from typing import Any  # The Mist payload shape is dynamic, so the values stay Any.


class CredentialRedactor:
    """Replace every credential value in a Mist settings record with a fixed token.

    The class holds static methods only. It carries no instance state, because a
    redaction rule must answer the same way for every caller.
    """

    # One fixed replacement value. The name avoids the words password, token, and
    # secret, because a static analyzer reads such a name as a credential holder.
    REDACTION_MARKER = "[REDACTED]"  # A reader can grep for this exact string.

    # A key that contains one of these words holds secret material. Each word is
    # long enough that it cannot match an unrelated operational field.
    _SUBSTRING_MARKERS: frozenset[str] = frozenset(
        {
            "password",  # switch_mgmt.root_password and juniper_srx.root_password
            "passphrase",  # Wi-Fi passphrase on a WLAN record
            "secret",  # shared_secret, wxtunnel_secret, and client_secret
            "private_key",  # Certificate private key material
            "ssh_keys",  # Site level SSH key list
            "api_token",  # Cloud API token
            "apitoken",  # The same token without a separator
            "credential",  # Any explicit credential blob
        }
    )

    # A key that equals one of these names holds secret material. These names are
    # short, so an exact match prevents a false hit on a longer unrelated key.
    _EXACT_KEYS: frozenset[str] = frozenset(
        {
            "psk",  # Pre-shared key
            "key",  # A bare key field carries the secret itself
            "token",  # A bare token field carries the secret itself
            "wep_key",  # Legacy WEP key
            "auth_key",  # Authentication key on a tunnel record
            "preshared_key",  # Pre-shared key under its long name
        }
    )

    @staticmethod
    def is_credential_key(key: str) -> bool:
        """Report whether a record key holds secret material.

        Args:
            key: The record key to test. The test ignores letter case.

        Returns:
            True when the key holds secret material, and False otherwise.
        """
        lowered = key.lower()  # Compare in one case, because Mist mixes both cases.
        if lowered in CredentialRedactor._EXACT_KEYS:  # Short names need an exact match.
            return True  # The key is a known credential field.
        return any(  # A long marker is safe as a substring test.
            marker in lowered for marker in CredentialRedactor._SUBSTRING_MARKERS
        )

    @staticmethod
    def _redact_in_place(node: Any, hits: list[str], path: str = "") -> Any:
        """Walk one node of the record and replace every credential value.

        Args:
            node: The current dictionary, list, or scalar value.
            hits: Accumulator that collects the path of each redacted key.
            path: Dotted path of the current node, used only for the log record.

        Returns:
            The node with every credential value replaced.
        """
        if isinstance(node, dict):  # A dictionary can hold a credential key directly.
            for key, value in node.items():  # Test each key before the walk continues.
                child_path = f"{path}.{key}" if path else str(key)  # Build the audit path.
                if isinstance(key, str) and CredentialRedactor.is_credential_key(key):
                    node[key] = CredentialRedactor.REDACTION_MARKER  # Drop the secret value.
                    hits.append(child_path)  # Record the path, never the value.
                    continue  # The subtree is gone, so no deeper walk is needed.
                CredentialRedactor._redact_in_place(value, hits, child_path)  # Walk deeper.
        elif isinstance(node, list):  # A list can hold a nested settings block.
            for index, item in enumerate(node):  # Walk each element under its index.
                CredentialRedactor._redact_in_place(item, hits, f"{path}[{index}]")
        return node  # Scalars need no change, so return the node either way.

    @staticmethod
    def redact(record: Any) -> Any:
        """Return a copy of one record with every credential value replaced.

        Args:
            record: A Mist settings record, normally a dictionary.

        Returns:
            A deep copy with every credential value replaced by the token. The
            input record is never changed.
        """
        logging.debug("Redacting credentials in one settings record")  # BEFORE the walk.
        if not isinstance(record, (dict, list)):  # A scalar carries no key to test.
            return record  # Return it unchanged.
        safe_record = copy.deepcopy(record)  # Copy first, so the caller keeps the original.
        hits: list[str] = []  # Collect each redacted path for the log record.
        CredentialRedactor._redact_in_place(safe_record, hits)  # Do the walk.
        if hits:  # Only log when the record really carried a credential.
            logging.info(  # AFTER the walk. Log the paths, never the values.
                "Redacted %s credential field(s) before export: %s",
                len(hits),
                ", ".join(sorted(hits)),
            )
        return safe_record  # Hand back the safe copy.

    @staticmethod
    def redact_records(records: list[Any]) -> list[Any]:
        """Return a copy of a record list with every credential value replaced.

        Args:
            records: A list of Mist settings records.

        Returns:
            A new list of redacted copies. The input list is never changed.
        """
        logging.info("Redacting credentials in %s settings record(s)", len(records))  # BEFORE.
        safe_records = [CredentialRedactor.redact(record) for record in records]  # Redact each one.
        logging.debug("Redaction complete for %s record(s)", len(safe_records))  # AFTER.
        return safe_records  # Hand back the safe list.
