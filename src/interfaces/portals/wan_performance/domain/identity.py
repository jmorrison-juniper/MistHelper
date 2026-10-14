"""Validate WAN entity identities before a caller uses their route values."""

import re
from dataclasses import dataclass


class IdentityValidator:
    """Validate opaque source identifiers without changing their values."""

    IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
    PEER_MAC_PATTERN = re.compile(r"^(?:(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}|[0-9A-Fa-f]{12})$")

    @classmethod
    def identifier(cls, value: str, field_name: str) -> str:
        """Reject empty, unsafe, or oversized opaque source identifiers."""
        if not isinstance(value, str) or not cls.IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError(f"{field_name} must contain 1 through 128 safe characters.")
        if value in {".", ".."}:
            raise ValueError(f"{field_name} cannot be a path component.")
        return value

    @classmethod
    def peer_mac(cls, value: str) -> str:
        """Validate compact or colon-separated MACs without changing source values."""
        if not isinstance(value, str) or not cls.PEER_MAC_PATTERN.fullmatch(value):
            raise ValueError("peer_mac must use 12 hexadecimal digits or six colon-separated hexadecimal octets.")
        return value


@dataclass(frozen=True, slots=True)
class SiteIdentity:
    """Keep organization and site values together as one site identity."""

    org_id: str
    site_id: str

    def __post_init__(self) -> None:
        """Validate both parent values before constructing a site identity."""
        IdentityValidator.identifier(self.org_id, "org_id")
        IdentityValidator.identifier(self.site_id, "site_id")

    @property
    def natural_key(self) -> tuple[str, str]:
        """Return the source identity without adding a generated key."""
        return self.org_id, self.site_id

    def to_dict(self) -> dict[str, str]:
        """Return JSON-compatible source identity values."""
        return {"org_id": self.org_id, "site_id": self.site_id}


@dataclass(frozen=True, slots=True)
class GatewayIdentity:
    """Keep an opaque gateway value within its verified site context."""

    site: SiteIdentity
    gateway_id: str

    def __post_init__(self) -> None:
        """Validate the gateway value before route or storage use."""
        IdentityValidator.identifier(self.gateway_id, "gateway_id")

    @property
    def natural_key(self) -> tuple[str, str, str]:
        """Return the organization, site, and original gateway values."""
        return (*self.site.natural_key, self.gateway_id)

    def to_dict(self) -> dict[str, str]:
        """Return JSON-compatible identity values with their parent context."""
        return {**self.site.to_dict(), "gateway_id": self.gateway_id}


@dataclass(frozen=True, slots=True)
class CircuitIdentity:
    """Keep the exact WAN port name under its gateway identity."""

    gateway: GatewayIdentity
    port_name: str

    def __post_init__(self) -> None:
        """Validate the port name while retaining its slash separators."""
        if not isinstance(self.port_name, str) or not self.port_name.strip():
            raise ValueError("port_name must contain a non-empty source value.")
        if len(self.port_name) > 128 or any(ord(character) < 32 for character in self.port_name):
            raise ValueError("port_name must contain at most 128 printable characters.")
        if any(part in {".", ".."} for part in self.port_name.split("/")):
            raise ValueError("port_name cannot contain a path traversal component.")

    @property
    def natural_key(self) -> tuple[str, str, str, str]:
        """Return the full parent path and exact port name."""
        return (*self.gateway.natural_key, self.port_name)

    def to_dict(self) -> dict[str, str]:
        """Return JSON-compatible identity values with their parent context."""
        return {**self.gateway.to_dict(), "port_name": self.port_name}


@dataclass(frozen=True, slots=True)
class PeerPathIdentity:
    """Keep peer paths separate by their explicit tunnel identity."""

    gateway: GatewayIdentity
    port_name: str
    peer_mac: str
    tunnel_identity: str

    def __post_init__(self) -> None:
        """Validate peer fields without deriving an unverified tunnel key."""
        CircuitIdentity(self.gateway, self.port_name)
        IdentityValidator.peer_mac(self.peer_mac)
        IdentityValidator.identifier(self.tunnel_identity, "tunnel_identity")

    @property
    def natural_key(self) -> tuple[str, str, str, str, str, str]:
        """Return each parent and peer-path identity value."""
        return (*self.gateway.natural_key, self.port_name, self.peer_mac, self.tunnel_identity)

    def to_dict(self) -> dict[str, str]:
        """Return JSON-compatible identity values with their parent context."""
        return {
            **self.gateway.to_dict(),
            "port_name": self.port_name,
            "peer_mac": self.peer_mac,
            "tunnel_identity": self.tunnel_identity,
        }
