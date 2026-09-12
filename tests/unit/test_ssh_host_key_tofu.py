"""Unit tests for SSH host-key trust-on-first-use enrollment (T013b: targets SshConnector)."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from src.ssh.connection.connector import SshConnector  # T013b: TOFU logic lives here now


class FakeHostKeys:
    """Minimal host-key store used to exercise TOFU enrollment logic."""

    def __init__(self, known_hosts: dict[str, dict[str, object]] | None = None) -> None:
        self.known_hosts = known_hosts or {}  # In-memory map of host -> {keytype: key}

    def lookup(self, hostname: str) -> dict[str, object] | None:
        """Return a known-hosts mapping when the hostname exists."""
        return self.known_hosts.get(hostname)  # None if not present

    def add(self, hostname: str, key_name: str, host_key: object) -> None:
        """Add one hostname and key tuple to the fake store."""
        self.known_hosts[hostname] = {key_name: host_key}  # Overwrite or insert


class FakeClient:
    """Minimal SSH client surface used by the TOFU helper methods."""

    def __init__(self, host_keys: FakeHostKeys | None = None) -> None:
        self._host_keys = host_keys or FakeHostKeys()  # Fake known-hosts backing store
        self.saved_path: str | None = None  # Captures save_host_keys() path arg

    def get_host_keys(self) -> FakeHostKeys:
        """Return the fake host-key store."""
        return self._host_keys

    def save_host_keys(self, path: str) -> None:
        """Record the path that would receive the persisted known-hosts file."""
        self.saved_path = path  # Capture for assertion


class TestSshConnectorTrustOnFirstUse(unittest.TestCase):
    """Validate the non-interactive TOFU enrollment behavior used by SshConnector."""

    def setUp(self) -> None:
        self.connector = SshConnector(timeout=5)  # T013b: SshConnector instead of EnhancedSSHRunner
        self.connector.managed_known_hosts_path = "data/ssh_known_hosts"  # Inject test path

    def test_trust_host_on_first_use_adds_key_and_persists_store(self) -> None:
        """Unseen host key is fetched, enrolled, and persisted to the managed store."""
        fake_host_key = Mock()  # Stand-in for paramiko host key
        fake_host_key.get_name.return_value = "ssh-rsa"  # Required by add(name, ...)
        fake_host_key.asbytes.return_value = b"host-key-bytes"  # Required by SHA256 fingerprint
        fake_client = FakeClient()  # Empty known-hosts store
        self.connector._fetch_remote_server_key = Mock(return_value=fake_host_key)  # type: ignore[method-assign]

        self.connector._trust_host_on_first_use(fake_client, "switch1", 22)  # T013b: client passed in

        self.assertIsNotNone(fake_client.get_host_keys().lookup("switch1"))  # Key got enrolled
        self.assertEqual(fake_client.saved_path, "data/ssh_known_hosts")  # Persisted to managed file
        self.connector._fetch_remote_server_key.assert_called_once_with("switch1", 22)  # Fetched once

    def test_trust_host_on_first_use_skips_existing_host_key(self) -> None:
        """Known host keys are not re-fetched or re-persisted."""
        fake_client = FakeClient(FakeHostKeys({"switch1": {"ssh-rsa": object()}}))  # Pre-populated
        self.connector._fetch_remote_server_key = Mock()  # type: ignore[method-assign]

        self.connector._trust_host_on_first_use(fake_client, "switch1", 22)  # Should short-circuit

        self.connector._fetch_remote_server_key.assert_not_called()  # No fetch when already known
        self.assertIsNone(fake_client.saved_path)  # No save when nothing changed

    def test_known_hosts_entry_name_includes_non_default_port(self) -> None:
        """Non-22 ports are bracketed per OpenSSH known_hosts convention."""
        self.assertEqual(
            SshConnector._known_hosts_entry_name("switch1", 2222),  # T013b: now staticmethod on SshConnector
            "[switch1]:2222",
        )

    def test_known_hosts_entry_name_default_port(self) -> None:
        """Port 22 entries are unbracketed bare hostnames."""
        self.assertEqual(SshConnector._known_hosts_entry_name("switch1", 22), "switch1")


if __name__ == "__main__":
    unittest.main()
