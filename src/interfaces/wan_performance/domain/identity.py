"""Validate source identities before they enter collection or cache records."""

import re
from dataclasses import dataclass


class IdentityValidator:
    """Validate opaque identifiers without changing their source values."""

    IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")  # Bound route-safe identifiers.
    PEER_MAC_PATTERN = re.compile(
        r"^(?:(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}|[0-9A-Fa-f]{12})$"
    )  # Accept two MAC forms.

    @classmethod
    def identifier(cls, value: object, field_name: str) -> str:
        """Reject empty, unsafe, or oversized source identifiers."""
        if not isinstance(value, str) or not cls.IDENTIFIER_PATTERN.fullmatch(value):  # Check the whole value.
            raise ValueError(f"{field_name} must contain 1 through 128 safe characters.")  # Name the invalid field.
        if value in {".", ".."}:  # Do not accept path components as identifiers.
            raise ValueError(f"{field_name} cannot be a path component.")  # Stop before path use.
        return value  # Preserve the original source identifier.

    @classmethod
    def peer_mac(cls, value: object) -> str:
        """Validate a compact or colon-separated peer MAC."""
        if not isinstance(value, str) or not cls.PEER_MAC_PATTERN.fullmatch(value):  # Require a full MAC match.
            raise ValueError("peer_mac must contain 12 hex digits or six colon-separated octets.")  # Reject bad input.
        return value  # Keep the exact source representation.

    @staticmethod
    def port_name(value: object, field_name: str) -> str:
        """Validate a source port name without rejecting interface separators."""
        if not isinstance(value, str) or not value.strip():  # Require a source port value.
            raise ValueError(f"{field_name} must contain a non-empty source value.")  # Reject absent identifiers.
        if len(value) > 128 or any(ord(char) < 32 for char in value):  # Bound printable values.
            raise ValueError(f"{field_name} must contain at most 128 printable characters.")  # Reject control data.
        if any(part in {".", ".."} for part in value.split("/")):  # Reject traversal components.
            raise ValueError(f"{field_name} cannot contain a path traversal component.")  # Stop before path use.
        return value  # Preserve the exact source value.


@dataclass(frozen=True, slots=True)
class SiteIdentity:
    """Keep organization and site values together as one natural identity."""

    org_id: str
    site_id: str

    def __post_init__(self) -> None:
        """Validate parent values before a site identity is used."""
        IdentityValidator.identifier(self.org_id, "org_id")  # Validate organization scope.
        IdentityValidator.identifier(self.site_id, "site_id")  # Validate the selected site.

    @property
    def natural_key(self) -> tuple[str, str]:
        """Return source identity values without a generated key."""
        return (self.org_id, self.site_id)  # Preserve the API identity.

    def to_dict(self) -> dict[str, str]:
        """Return JSON-compatible source identity values."""
        return {"org_id": self.org_id, "site_id": self.site_id}  # Keep names stable for cache consumers.


@dataclass(frozen=True, slots=True)
class GatewayIdentity:
    """Keep an opaque gateway identifier inside its selected site."""

    site: SiteIdentity
    gateway_id: str

    def __post_init__(self) -> None:
        """Validate the gateway value before route or cache use."""
        IdentityValidator.identifier(self.gateway_id, "gateway_id")  # Reject unsafe gateway values.

    @property
    def natural_key(self) -> tuple[str, str, str]:
        """Return organization, site, and source gateway values."""
        return (*self.site.natural_key, self.gateway_id)  # Preserve parent context.

    def to_dict(self) -> dict[str, str]:
        """Return JSON-compatible identity values with parent context."""
        return {**self.site.to_dict(), "gateway_id": self.gateway_id}  # Include the parent identity.


@dataclass(frozen=True, slots=True)
class CircuitIdentity:
    """Keep a WAN port name under its gateway identity."""

    gateway: GatewayIdentity
    port_name: str

    def __post_init__(self) -> None:
        """Validate the port name while preserving slash separators."""
        IdentityValidator.port_name(self.port_name, "port_name")  # Preserve interface separators safely.

    @property
    def natural_key(self) -> tuple[str, str, str, str]:
        """Return the full source path and exact port name."""
        return (*self.gateway.natural_key, self.port_name)  # Keep the complete identity.

    def to_dict(self) -> dict[str, str]:
        """Return JSON-compatible identity values with parent context."""
        return {**self.gateway.to_dict(), "port_name": self.port_name}  # Keep the source field name.


@dataclass(frozen=True, slots=True)
class PeerPathIdentity:
    """Keep peer paths distinct by their complete tunnel identity."""

    gateway: GatewayIdentity
    port_name: str
    peer_port_id: str
    peer_mac: str
    tunnel_identity: str

    def __post_init__(self) -> None:
        """Validate local and remote path fields without deriving an identity."""
        CircuitIdentity(self.gateway, self.port_name)  # Validate the local port.
        CircuitIdentity(self.gateway, self.peer_port_id)  # Validate the remote port.
        IdentityValidator.peer_mac(self.peer_mac)  # Validate the remote peer MAC.
        IdentityValidator.identifier(self.tunnel_identity, "tunnel_identity")  # Validate the explicit tunnel key.

    @property
    def natural_key(self) -> tuple[str, ...]:
        """Return every source value that distinguishes a peer path."""
        return (
            *self.gateway.natural_key,
            self.port_name,
            self.peer_port_id,
            self.peer_mac,
            self.tunnel_identity,
        )  # Keep all path fields.

    def to_dict(self) -> dict[str, str]:
        """Return peer identity values with their site and gateway context."""
        return {  # Keep the remote path explicit for cache consumers.
            **self.gateway.to_dict(),  # Retain organization and gateway scope.
            "port_name": self.port_name,  # Preserve the local port.
            "peer_port_id": self.peer_port_id,  # Preserve the remote port.
            "peer_mac": self.peer_mac,  # Preserve the peer address.
            "tunnel_identity": self.tunnel_identity,  # Preserve the tunnel discriminator.
        }
