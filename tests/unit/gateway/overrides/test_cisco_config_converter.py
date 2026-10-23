"""Test original IOS DNS conversion without a network or a source repository."""

import pytest

from src.interfaces.portals.cisco_config_converter.conversion import IOSDnsConverter
from src.interfaces.portals.cisco_config_converter.models import SourceConfiguration


class TestSourceConfiguration:
    """Reject invalid uploads before conversion."""

    @pytest.mark.parametrize("content", [b"", b" \n\t", b"\xff", b"ip\x00name"])
    def test_invalid_content(self, content: bytes) -> None:
        """Invalid text must not produce a proposal."""
        with pytest.raises(ValueError):
            SourceConfiguration.read("sample.cfg", content, "Branch", "standalone")

    @pytest.mark.parametrize("filename", ["../sample.cfg", "C:\\sample.cfg", "/sample.cfg", "sample.exe"])
    def test_invalid_filename(self, filename: str) -> None:
        """Path-like names and binary suffixes are invalid."""
        with pytest.raises(ValueError):
            SourceConfiguration.read(filename, b"hostname sample", "Branch", "spoke")

    @pytest.mark.parametrize("suffix", [".txt", ".conf", ".cfg", ".ios", ".config", ".log"])
    def test_suffixes(self, suffix: str) -> None:
        """Each documented text suffix remains accepted."""
        source = SourceConfiguration.read("sample" + suffix, b"hostname sample", "Branch", "spoke")
        assert source.content == "hostname sample"

    def test_exact_size_boundary(self) -> None:
        """Accept 16 MiB and reject one additional byte."""
        content = b"!" * (16 * 1024 * 1024)
        assert len(SourceConfiguration.read("sample.cfg", content, "Branch", "spoke").content) == len(content)
        with pytest.raises(ValueError, match="16 MiB"):
            SourceConfiguration.read("sample.cfg", content + b"!", "Branch", "spoke")

    @pytest.mark.parametrize(
        ("name", "kind"),
        [("", "spoke"), ("  ", "spoke"), ("a" * 121, "spoke"), ("Branch", "hub"), ("Branch\n", "spoke")],
    )
    def test_template_validation(self, name: str, kind: str) -> None:
        """Reject an invalid template identity."""
        with pytest.raises(ValueError):
            SourceConfiguration.read("sample.cfg", b"hostname sample", name, kind)


class TestIOSDnsConverter:
    """Check the supported subset and conservative handling of other syntax."""

    def test_supported_dns_and_unknown_commands(self) -> None:
        """Keep unique DNS values in order and report unsupported lines."""
        source = SourceConfiguration.read(
            "sample.cfg",
            b"ip name-server 192.0.2.1 198.51.100.2\nip name-server 192.0.2.1\nhostname branch",
            "Branch",
            "spoke",
        )
        proposal = IOSDnsConverter.convert(source)
        assert proposal["gateway_template"] == {
            "name": "Branch",
            "type": "spoke",
            "dns_servers": ["192.0.2.1", "198.51.100.2"],
        }
        assert len(proposal["unsupported_items"]) == 1
        assert len(proposal["known_gaps"]) == 3

    @pytest.mark.parametrize(
        "command",
        [
            "ip name-server",
            "ip name-server 999.1.1.1",
            "ip name-server 2001:db8::1",
            "ip name-server vrf management 192.0.2.1",
            " ip name-server 192.0.2.1",
            "no ip name-server 192.0.2.1",
        ],
    )
    def test_unsupported_directive(self, command: str) -> None:
        """Do not invent DNS values for unsupported syntax."""
        source = SourceConfiguration.read("sample.cfg", command.encode(), "Branch", "standalone")
        proposal = IOSDnsConverter.convert(source)
        assert "dns_servers" not in proposal["gateway_template"]
        assert len(proposal["unsupported_items"]) == 1

    def test_banner_is_not_global_configuration(self) -> None:
        """Ignore apparent DNS commands inside a multiline banner."""
        source = SourceConfiguration.read(
            "sample.cfg", b"banner motd ^C\nip name-server 192.0.2.3\n^C\nip name-server 192.0.2.4", "Branch", "spoke"
        )
        proposal = IOSDnsConverter.convert(source)
        assert proposal["gateway_template"]["dns_servers"] == ["192.0.2.4"]
        assert len(proposal["unsupported_items"]) == 3

    def test_punctuation_banner_delimiter(self) -> None:
        """A comment-like delimiter must end a banner before global DNS input."""
        source = SourceConfiguration.read(
            "sample.cfg", b"banner motd !\nip name-server 192.0.2.3\n!\nip name-server 192.0.2.4", "Branch", "spoke"
        )
        assert IOSDnsConverter.convert(source)["gateway_template"]["dns_servers"] == ["192.0.2.4"]
