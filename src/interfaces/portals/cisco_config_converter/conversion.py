"""Convert only the documented global IPv4 DNS subset of IOS syntax."""

import ipaddress
import logging

from .models import ConversionProposal, GatewayTemplate, SourceConfiguration, UnsupportedItem

logger = logging.getLogger(__name__)


class IOSDnsConverter:
    """Preserve unsupported input without inferring device mappings."""

    @classmethod
    def convert(cls, source: SourceConfiguration) -> ConversionProposal:
        """Build a proposal without a network request or persistent output."""
        logger.info("Preparing an offline DNS proposal.")
        servers, unsupported = cls._commands(source.content)
        template: GatewayTemplate = {"name": source.name, "type": source.kind}
        if servers:
            template["dns_servers"] = servers
        proposal: ConversionProposal = {
            "gateway_template": template,
            "unsupported_items": unsupported,
            "known_gaps": [
                "Only global IPv4 ip name-server commands are converted.",
                "IPv6, hardware mappings, and all other settings remain unsupported.",
                "Cloud apply is unavailable. Unsupported values are omitted to protect credentials.",
            ],
        }
        logger.debug(
            "Prepared a proposal with %d DNS addresses and %d unsupported items.", len(servers), len(unsupported)
        )
        return proposal

    @classmethod
    def _commands(cls, content: str) -> tuple[list[str], list[UnsupportedItem]]:
        """Keep input order and exclude multiline banner content."""
        servers: list[str] = []
        unsupported: list[UnsupportedItem] = []
        delimiter = ""
        for number, line in enumerate(content.splitlines(), start=1):
            if not delimiter and (not line.strip() or line.lstrip().startswith("!")):
                continue
            values = cls._addresses(line) if not delimiter else []
            delimiter = cls._banner(line, delimiter)
            if values:
                servers.extend(value for value in values if value not in servers)
            else:
                unsupported.append(
                    {"line": number, "command": cls._label(line), "reason": "Unsupported command or context."}
                )
        return servers, unsupported

    @staticmethod
    def _addresses(line: str) -> list[str]:
        """Accept complete, unindented IPv4 directives only."""
        tokens = line.split()
        if line[:1].isspace() or tokens[:2] != ["ip", "name-server"] or len(tokens) < 3:
            return []
        try:
            return [str(ipaddress.IPv4Address(value)) for value in tokens[2:]]
        except ipaddress.AddressValueError:
            return []

    @staticmethod
    def _banner(line: str, delimiter: str) -> str:
        """Track the IOS banner delimiter without treating its body as commands."""
        if delimiter:
            return "" if delimiter in line else delimiter
        tokens = line.split(maxsplit=2)
        if len(tokens) != 3 or tokens[0] != "banner":
            return ""
        marker = tokens[2][:2] if tokens[2].startswith("^") else tokens[2][:1]
        return "" if marker in tokens[2][len(marker) :] else marker

    @staticmethod
    def _label(line: str) -> str:
        """Identify unsupported command families without exposing source values."""
        tokens = line.split()
        if tokens[:2] == ["ip", "name-server"]:
            return "ip name-server [values omitted]"
        return "[unsupported source line]"
