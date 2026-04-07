"""Unit tests for SSH host-key trust-on-first-use enrollment."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

_mh_path = Path(__file__).parents[2] / "MistHelper.py"
_spec = importlib.util.spec_from_file_location("MistHelper", _mh_path)
assert _spec is not None
assert _spec.loader is not None
MistHelper = importlib.util.module_from_spec(_spec)
sys.modules["MistHelper"] = MistHelper
try:
    _spec.loader.exec_module(MistHelper)
except SystemExit:
    pass


class FakeHostKeys:
    """Minimal host-key store used to exercise TOFU enrollment logic."""

    def __init__(self, known_hosts: dict[str, dict[str, object]] | None = None) -> None:
        self.known_hosts = known_hosts or {}

    def lookup(self, hostname: str) -> dict[str, object] | None:
        """Return a known-hosts mapping when the hostname exists."""
        return self.known_hosts.get(hostname)

    def add(self, hostname: str, key_name: str, host_key: object) -> None:
        """Add one hostname and key tuple to the fake store."""
        self.known_hosts[hostname] = {key_name: host_key}


class FakeClient:
    """Minimal SSH client surface used by the TOFU helper methods."""

    def __init__(self, host_keys: FakeHostKeys | None = None) -> None:
        self._host_keys = host_keys or FakeHostKeys()
        self.saved_path: str | None = None

    def get_host_keys(self) -> FakeHostKeys:
        """Return the fake host-key store."""
        return self._host_keys

    def save_host_keys(self, path: str) -> None:
        """Record the path that would receive the persisted known-hosts file."""
        self.saved_path = path


class TestSSHHostKeyTrustOnFirstUse(unittest.TestCase):
    """Validate the non-interactive TOFU enrollment behavior used by the SSH runner."""

    def setUp(self) -> None:
        self.runner = MistHelper.EnhancedSSHRunner(timeout=5)
        self.runner.managed_known_hosts_path = "data/ssh_known_hosts"

    def test_trust_host_on_first_use_adds_key_and_persists_store(self) -> None:
        fake_host_key = Mock()
        fake_host_key.get_name.return_value = "ssh-rsa"
        fake_host_key.asbytes.return_value = b"host-key-bytes"
        fake_client = FakeClient()
        self.runner.client = fake_client
        self.runner._fetch_remote_server_key = Mock(return_value=fake_host_key)

        self.runner._trust_host_on_first_use("switch1", 22)

        self.assertIsNotNone(fake_client.get_host_keys().lookup("switch1"))
        self.assertEqual(fake_client.saved_path, "data/ssh_known_hosts")
        self.runner._fetch_remote_server_key.assert_called_once_with("switch1", 22)

    def test_trust_host_on_first_use_skips_existing_host_key(self) -> None:
        fake_client = FakeClient(FakeHostKeys({"switch1": {"ssh-rsa": object()}}))
        self.runner.client = fake_client
        self.runner._fetch_remote_server_key = Mock()

        self.runner._trust_host_on_first_use("switch1", 22)

        self.runner._fetch_remote_server_key.assert_not_called()
        self.assertIsNone(fake_client.saved_path)

    def test_known_hosts_entry_name_includes_non_default_port(self) -> None:
        self.assertEqual(
            self.runner._known_hosts_entry_name("switch1", 2222),
            "[switch1]:2222",
        )


if __name__ == "__main__":
    unittest.main()
