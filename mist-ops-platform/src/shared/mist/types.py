"""Mist entity type mappings and endpoint routing table.

Maps platform entity types to mistapi SDK read/write methods (R-05).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True, slots=True)
class MistEndpoint:
    """Maps a Mist entity type to its SDK read/write paths."""

    entity_type: str
    api_module: str
    read_method: str
    write_method: str
    id_params: tuple[str, ...]


# -----------------------------------------------------------------------
# Central routing table — one entry per managed entity type
# Sorted alphabetically for easy lookup (R-05 table from research.md)
# -----------------------------------------------------------------------
ENTITY_ENDPOINT_MAP: dict[str, MistEndpoint] = {
    "ap_template": MistEndpoint(
        entity_type="ap_template",
        api_module="orgs.aptemplates",
        read_method="getOrgAptemplate",
        write_method="updateOrgAptemplate",
        id_params=("org_id", "aptemplate_id"),
    ),
    "device": MistEndpoint(
        entity_type="device",
        api_module="sites.devices",
        read_method="getSiteDevice",
        write_method="updateSiteDevice",
        id_params=("site_id", "device_id"),
    ),
    "device_profile": MistEndpoint(
        entity_type="device_profile",
        api_module="orgs.deviceprofiles",
        read_method="getOrgDeviceProfile",
        write_method="updateOrgDeviceProfile",
        id_params=("org_id", "deviceprofile_id"),
    ),
    "gateway_template": MistEndpoint(
        entity_type="gateway_template",
        api_module="orgs.gatewaytemplates",
        read_method="getOrgGatewayTemplate",
        write_method="updateOrgGatewayTemplate",
        id_params=("org_id", "gatewaytemplate_id"),
    ),
    "nac_rule": MistEndpoint(
        entity_type="nac_rule",
        api_module="orgs.nacrules",
        read_method="getOrgNacRule",
        write_method="updateOrgNacRule",
        id_params=("org_id", "nacrule_id"),
    ),
    "network": MistEndpoint(
        entity_type="network",
        api_module="orgs.networks",
        read_method="getOrgNetwork",
        write_method="updateOrgNetwork",
        id_params=("org_id", "network_id"),
    ),
    "network_template": MistEndpoint(
        entity_type="network_template",
        api_module="orgs.networktemplates",
        read_method="getOrgNetworkTemplate",
        write_method="updateOrgNetworkTemplate",
        id_params=("org_id", "networktemplate_id"),
    ),
    "org_wlan": MistEndpoint(
        entity_type="org_wlan",
        api_module="orgs.wlans",
        read_method="getOrgWlan",
        write_method="updateOrgWlan",
        id_params=("org_id", "wlan_id"),
    ),
    "rf_template": MistEndpoint(
        entity_type="rf_template",
        api_module="orgs.rftemplates",
        read_method="getOrgRfTemplate",
        write_method="updateOrgRfTemplate",
        id_params=("org_id", "rftemplate_id"),
    ),
    "security_policy": MistEndpoint(
        entity_type="security_policy",
        api_module="orgs.secpolicies",
        read_method="getOrgSecPolicy",
        write_method="updateOrgSecPolicy",
        id_params=("org_id", "secpolicy_id"),
    ),
    "service_policy": MistEndpoint(
        entity_type="service_policy",
        api_module="orgs.servicepolicies",
        read_method="getOrgServicePolicy",
        write_method="updateOrgServicePolicy",
        id_params=("org_id", "servicepolicy_id"),
    ),
    "site_info": MistEndpoint(
        entity_type="site_info",
        api_module="sites.site",
        read_method="getSiteInfo",
        write_method="updateSiteInfo",
        id_params=("site_id",),
    ),
    "site_setting": MistEndpoint(
        entity_type="site_setting",
        api_module="sites.setting",
        read_method="getSiteSetting",
        write_method="updateSiteSettings",
        id_params=("site_id",),
    ),
    "site_wlan": MistEndpoint(
        entity_type="site_wlan",
        api_module="sites.wlans",
        read_method="getSiteWlan",
        write_method="updateSiteWlan",
        id_params=("site_id", "wlan_id"),
    ),
}


class MistEntityRegistry:
    """Lookup service for Mist entity endpoint metadata."""

    _map: ClassVar[dict[str, MistEndpoint]] = ENTITY_ENDPOINT_MAP

    @classmethod
    def get(cls, entity_type: str) -> MistEndpoint:
        """Return the endpoint record for *entity_type* or raise."""
        try:
            return cls._map[entity_type]
        except KeyError as exc:
            msg = f"Unknown entity type: {entity_type!r}"
            raise ValueError(msg) from exc

    @classmethod
    def entity_types(cls) -> list[str]:
        """Return sorted list of all registered entity types."""
        return sorted(cls._map)

    @classmethod
    def has(cls, entity_type: str) -> bool:
        """Check whether *entity_type* is registered."""
        return entity_type in cls._map
