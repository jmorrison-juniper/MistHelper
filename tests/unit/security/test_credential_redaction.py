"""Tests for ``CredentialRedactor`` and for the site settings read boundary.

The suite proves the acceptance criteria of GitHub issue #2011:

1. A settings record reaches an export with no credential field.
2. The redaction covers a nested block and a list of blocks.
3. The redaction never changes the record the caller passed in.
4. An operational field survives the redaction unchanged.
"""

from unittest.mock import MagicMock, patch

from src.api.api_fetch_utils import APIFetchUtils
from src.security import CredentialRedactor

# One record shaped like the ``getSiteSetting`` answer that prompted the issue.
# The values are invented. No real credential appears in this repository.
_SETTINGS_RECORD = {
    "id": "site-abc",  # Operational field. It must survive.
    "name": "Morrison House Site",  # Operational field. It must survive.
    "switch_mgmt": {
        "root_password": "invented-switch-secret",  # Must be redacted.
        "config_revert_timer": 10,  # Operational field inside the same block.
    },
    "juniper_srx": {"root_password": "invented-srx-secret"},  # Must be redacted.
    "ssh_keys": ["ssh-rsa AAAAinvented"],  # Must be redacted as a whole list.
    "wids": {"repeated_auth_failures": {"duration": 60}},  # Untouched nested block.
    "vars": [
        {"name": "site_a", "psk": "invented-psk-one"},  # Must be redacted in a list.
        {"name": "site_b", "secret": "invented-shared-secret"},  # Must be redacted too.
    ],
}


def _collect_values(node: object) -> list[object]:
    """Return every scalar value found anywhere inside a nested structure."""
    if isinstance(node, dict):  # Walk each value of a dictionary.
        found: list[object] = []  # Accumulate the scalars of this subtree.
        for value in node.values():  # Visit every value under this node.
            found.extend(_collect_values(value))  # Recurse into the value.
        return found  # Hand the subtree result back.
    if isinstance(node, list):  # Walk each element of a list.
        found = []  # Accumulate the scalars of this list.
        for item in node:  # Visit every element.
            found.extend(_collect_values(item))  # Recurse into the element.
        return found  # Hand the list result back.
    return [node]  # A scalar is the leaf of the walk.


class TestIsCredentialKey:
    """Cover the key classifier that drives the redaction."""

    def test_exact_short_names_are_credentials(self) -> None:
        """A short key name matches only when it is exactly a credential name."""
        assert CredentialRedactor.is_credential_key("psk") is True
        assert CredentialRedactor.is_credential_key("key") is True
        assert CredentialRedactor.is_credential_key("token") is True

    def test_long_markers_match_inside_a_key(self) -> None:
        """A long marker matches as a substring, so a prefixed key still hits."""
        assert CredentialRedactor.is_credential_key("root_password") is True
        assert CredentialRedactor.is_credential_key("ROOT_PASSWORD") is True
        assert CredentialRedactor.is_credential_key("wxtunnel_secret") is True
        assert CredentialRedactor.is_credential_key("ssh_keys") is True

    def test_operational_fields_are_not_credentials(self) -> None:
        """A field an operator needs must never be redacted."""
        for name in ("name", "id", "keyword_list", "tokenizer", "country_code"):
            assert CredentialRedactor.is_credential_key(name) is False


class TestRedact:
    """Cover the record level redaction."""

    def test_no_credential_value_survives(self) -> None:
        """Acceptance criterion 1. No secret value remains anywhere in the copy."""
        safe = CredentialRedactor.redact(_SETTINGS_RECORD)
        values = _collect_values(safe)  # Flatten the whole structure to scalars.
        for secret in (
            "invented-switch-secret",
            "invented-srx-secret",
            "ssh-rsa AAAAinvented",
            "invented-psk-one",
            "invented-shared-secret",
        ):
            assert secret not in values

    def test_nested_and_list_blocks_are_redacted(self) -> None:
        """Acceptance criterion 2. A nested block and a list of blocks both clear."""
        safe = CredentialRedactor.redact(_SETTINGS_RECORD)
        token = CredentialRedactor.REDACTION_MARKER
        assert safe["switch_mgmt"]["root_password"] == token
        assert safe["juniper_srx"]["root_password"] == token
        assert safe["ssh_keys"] == token
        assert safe["vars"][0]["psk"] == token
        assert safe["vars"][1]["secret"] == token

    def test_input_record_is_unchanged(self) -> None:
        """Acceptance criterion 3. The caller keeps the record it passed in."""
        CredentialRedactor.redact(_SETTINGS_RECORD)
        assert _SETTINGS_RECORD["switch_mgmt"]["root_password"] == "invented-switch-secret"

    def test_operational_fields_survive(self) -> None:
        """Acceptance criterion 4. A field an operator needs is still readable."""
        safe = CredentialRedactor.redact(_SETTINGS_RECORD)
        assert safe["id"] == "site-abc"
        assert safe["name"] == "Morrison House Site"
        assert safe["switch_mgmt"]["config_revert_timer"] == 10
        assert safe["wids"]["repeated_auth_failures"]["duration"] == 60
        assert safe["vars"][0]["name"] == "site_a"

    def test_a_scalar_passes_through(self) -> None:
        """A non-record input must return unchanged rather than raise."""
        assert CredentialRedactor.redact("plain") == "plain"
        assert CredentialRedactor.redact(None) is None

    def test_redact_records_handles_a_list(self) -> None:
        """The list helper redacts every record it receives."""
        safe_list = CredentialRedactor.redact_records([_SETTINGS_RECORD, _SETTINGS_RECORD])
        assert len(safe_list) == 2
        for safe in safe_list:
            assert safe["switch_mgmt"]["root_password"] == CredentialRedactor.REDACTION_MARKER


class TestSiteSettingReadBoundary:
    """Prove the read boundary redacts before any caller can export the record."""

    def test_fetch_single_site_setting_redacts(self) -> None:
        """A settings record leaves the fetcher with no credential value."""
        response = MagicMock()  # Stand in for the mistapi response object.
        response.data = {  # A fresh copy, because the fetcher tags the record.
            "switch_mgmt": {"root_password": "invented-switch-secret"},
            "ssh_keys": ["ssh-rsa AAAAinvented"],
            "name": "kept",
        }
        with patch(
            "src.api.api_fetch_utils.mistapi.api.v1.sites.setting.getSiteSetting",
            return_value=response,
        ):
            config = APIFetchUtils._fetch_single_site_setting(
                MagicMock(), {"id": "site-abc", "name": "Morrison House Site"}
            )
        assert config is not None
        assert config["switch_mgmt"]["root_password"] == CredentialRedactor.REDACTION_MARKER
        assert config["ssh_keys"] == CredentialRedactor.REDACTION_MARKER
        assert config["name"] == "kept"  # The operational field survives.
        assert config["site_id"] == "site-abc"  # The tag still applies.
        assert config["site_name"] == "Morrison House Site"  # The tag still applies.

    def test_the_cloud_record_is_not_mutated(self) -> None:
        """The redaction copies, so a shared cloud payload keeps its own shape."""
        payload = {"switch_mgmt": {"root_password": "invented-switch-secret"}}
        response = MagicMock()
        response.data = payload
        with patch(
            "src.api.api_fetch_utils.mistapi.api.v1.sites.setting.getSiteSetting",
            return_value=response,
        ):
            APIFetchUtils._fetch_single_site_setting(MagicMock(), {"id": "s", "name": "n"})
        assert payload["switch_mgmt"]["root_password"] == "invented-switch-secret"
