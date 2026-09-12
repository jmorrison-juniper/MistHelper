"""Unit tests for ENDPOINT_PRIMARY_KEY_STRATEGIES validation.

Duplicates the strategies dict from MistHelper.py to avoid import side effects
(research.md R1 pattern). Validates structural integrity of every entry.
"""

# ---------------------------------------------------------------------------
# Duplicated dict (R1: avoid MistHelper.py import side effects)
# ---------------------------------------------------------------------------
ENDPOINT_PRIMARY_KEY_STRATEGIES = {
    "getOrgInventory": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "mac", "serial", "model", "type"],
        "unique_constraints": [],
        "description": "Organization device inventory with stable UUID identifiers",
    },
    "listOrgSites": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "country_code", "address"],
        "unique_constraints": [],
        "description": "Organization sites with stable UUID identifiers",
    },
    "listSiteDevices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "mac", "serial", "model", "type", "name"],
        "unique_constraints": [],
        "description": "Site devices with stable UUID identifiers",
    },
    "getOrgDevices": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "site_id", "mac", "serial", "model", "type"],
        "unique_constraints": [],
        "description": "Organization devices with stable UUID identifiers",
    },
    "listOrgGatewayTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "type"],
        "unique_constraints": [],
        "description": "Gateway templates with stable UUID identifiers",
    },
    "listOrgNetworkTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Network templates with stable UUID identifiers",
    },
    "listOrgRfTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "band"],
        "unique_constraints": [],
        "description": "RF templates with stable UUID identifiers",
    },
    "listOrgSiteTemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Site templates with stable UUID identifiers",
    },
    "listOrgAptemplates": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "AP templates with stable UUID identifiers",
    },
    "listOrgSecPolicies": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name"],
        "unique_constraints": [],
        "description": "Security policies with stable UUID identifiers",
    },
    "listOrgPsks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "ssid"],
        "unique_constraints": [],
        "description": "Pre-shared keys with stable UUID identifiers",
    },
    "listOrgWebhooks": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["org_id", "name", "type"],
        "unique_constraints": [],
        "description": "Webhooks with stable UUID identifiers",
    },
    "searchOrgAlarms": {
        "type": "composite_pk",
        "primary_key": ["id", "org_id", "timestamp"],
        "indexes": ["org_id", "timestamp", "severity", "type", "site_id"],
        "unique_constraints": [],
        "description": "Organization alarms with composite key for time-series data",
    },
    "searchOrgDeviceEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "device_id", "timestamp"],
        "indexes": ["device_id", "timestamp", "type", "org_id", "site_id"],
        "unique_constraints": [],
        "description": "Device events with composite key for uniqueness",
    },
    "searchOrgClientEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "site_id", "timestamp"],
        "indexes": ["site_id", "timestamp", "type", "client_mac", "device_id"],
        "unique_constraints": [],
        "description": "Client events with composite key for uniqueness",
    },
    "searchOrgSystemEvents": {
        "type": "composite_pk",
        "primary_key": ["id", "org_id", "timestamp"],
        "indexes": ["org_id", "timestamp", "type"],
        "unique_constraints": [],
        "description": "System events with composite key for uniqueness",
    },
    "listOrgDevicesStats": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["device_id", "timestamp", "org_id", "site_id", "type"],
        "unique_constraints": [],
        "description": "Organization device statistics with composite key for metrics",
    },
    "listSiteDevicesStats": {
        "type": "composite_pk",
        "primary_key": ["device_id", "timestamp"],
        "indexes": ["device_id", "timestamp", "site_id", "type"],
        "unique_constraints": [],
        "description": "Site device statistics with composite key for metrics",
    },
    "listSiteWirelessClientsStats": {
        "type": "composite_pk",
        "primary_key": ["client_mac", "timestamp"],
        "indexes": ["client_mac", "timestamp", "site_id", "device_id"],
        "unique_constraints": [],
        "description": "Site wireless client statistics with composite key for metrics",
    },
    "searchOrgSwOrGwPorts": {
        "type": "composite_pk",
        "primary_key": ["device_id", "port_id", "timestamp"],
        "indexes": ["device_id", "port_id", "timestamp", "org_id"],
        "unique_constraints": [],
        "description": "Switch/gateway port statistics with composite key",
    },
    "searchSiteSwOrGwPorts": {
        "type": "composite_pk",
        "primary_key": ["device_id", "port_id", "timestamp"],
        "indexes": ["device_id", "port_id", "timestamp", "site_id"],
        "unique_constraints": [],
        "description": "Site switch/gateway port statistics with composite key",
    },
    "searchOrgPeerPathStats": {
        "type": "composite_pk",
        "primary_key": ["from_device", "to_device", "timestamp"],
        "indexes": ["from_device", "to_device", "timestamp", "org_id"],
        "unique_constraints": [],
        "description": "Peer path statistics with composite key",
    },
    "listSiteMaps": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "name", "type", "created_time", "modified_time"],
        "unique_constraints": [],
        "description": "Site maps with stable UUID identifiers",
    },
    "getSiteMap": {
        "type": "natural_pk",
        "primary_key": ["id"],
        "indexes": ["site_id", "name", "type"],
        "unique_constraints": [],
        "description": "Individual site map with stable UUID identifier",
    },
    "searchOrgWirelessClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "device_id", "ssid"],
        "unique_constraints": [],
        "description": "Wireless client data with composite key for time-series",
    },
    "searchOrgWiredClients": {
        "type": "composite_pk",
        "primary_key": ["mac", "timestamp"],
        "indexes": ["mac", "timestamp", "site_id", "device_id", "port_id"],
        "unique_constraints": [],
        "description": "Wired client data with composite key for time-series",
    },
    "getOrgLicensesSummary": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": ["org_id", "sku", "type"],
        "unique_constraints": [],
        "description": "License summary data (aggregated, no stable primary key)",
    },
    "sitesMissingInfrastructure": {
        "type": "natural_pk",
        "primary_key": ["site_id"],
        "indexes": ["site_name", "missing_types", "ap_count"],
        "unique_constraints": [],
        "description": "Sites with APs but missing switches or gateways",
    },
    "sitesWithOfflineInfrastructure": {
        "type": "natural_pk",
        "primary_key": ["site_id"],
        "indexes": ["site_name", "offline_switches", "offline_gateways"],
        "unique_constraints": [],
        "description": "Sites with APs where switches or gateways are offline",
    },
    "default": {
        "type": "auto_increment_with_unique",
        "primary_key": ["misthelper_internal_id"],
        "indexes": [],
        "unique_constraints": [],
        "description": "Fallback strategy with auto-increment primary key and unique constraint on API id",
    },
}

VALID_PK_TYPES = {"natural_pk", "composite_pk", "auto_increment_with_unique"}
REQUIRED_FIELDS = {"type", "primary_key", "indexes", "unique_constraints", "description"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestEndpointPrimaryKeyStrategies:
    """Validate structural integrity of ENDPOINT_PRIMARY_KEY_STRATEGIES."""

    def test_all_entries_have_required_fields(self):
        for endpoint, config in ENDPOINT_PRIMARY_KEY_STRATEGIES.items():
            missing = REQUIRED_FIELDS - set(config.keys())
            assert not missing, f"{endpoint} missing fields: {missing}"

    def test_all_types_are_valid(self):
        for endpoint, config in ENDPOINT_PRIMARY_KEY_STRATEGIES.items():
            assert config["type"] in VALID_PK_TYPES, f"{endpoint} has invalid type '{config['type']}'"

    def test_primary_key_is_non_empty_list(self):
        for endpoint, config in ENDPOINT_PRIMARY_KEY_STRATEGIES.items():
            pk = config["primary_key"]
            assert isinstance(pk, list), f"{endpoint} primary_key is not a list"
            assert len(pk) > 0, f"{endpoint} has empty primary_key"

    def test_primary_key_values_are_strings(self):
        for endpoint, config in ENDPOINT_PRIMARY_KEY_STRATEGIES.items():
            for key in config["primary_key"]:
                assert isinstance(key, str), f"{endpoint} primary_key contains non-string: {key}"

    def test_indexes_is_a_list(self):
        for endpoint, config in ENDPOINT_PRIMARY_KEY_STRATEGIES.items():
            assert isinstance(config["indexes"], list), f"{endpoint} indexes is not a list"

    def test_description_is_non_empty_string(self):
        for endpoint, config in ENDPOINT_PRIMARY_KEY_STRATEGIES.items():
            desc = config["description"]
            assert isinstance(desc, str) and len(desc) > 0, f"{endpoint} has empty or non-string description"

    def test_natural_pk_uses_id_field(self):
        """Natural PK entries should typically use 'id' or a known key."""
        for endpoint, config in ENDPOINT_PRIMARY_KEY_STRATEGIES.items():
            if config["type"] == "natural_pk":
                pk = config["primary_key"]
                assert len(pk) == 1, f"{endpoint} natural_pk should have exactly 1 primary key, got {pk}"

    def test_composite_pk_has_multiple_keys(self):
        """Composite PK entries should have 2+ keys for uniqueness."""
        for endpoint, config in ENDPOINT_PRIMARY_KEY_STRATEGIES.items():
            if config["type"] == "composite_pk":
                pk = config["primary_key"]
                assert len(pk) >= 2, f"{endpoint} composite_pk should have >=2 keys, got {pk}"

    def test_default_strategy_exists(self):
        assert "default" in ENDPOINT_PRIMARY_KEY_STRATEGIES
        default = ENDPOINT_PRIMARY_KEY_STRATEGIES["default"]
        assert default["type"] == "auto_increment_with_unique"

    def test_no_duplicate_endpoint_names(self):
        """Dict keys are inherently unique, but verify count matches."""
        keys = list(ENDPOINT_PRIMARY_KEY_STRATEGIES.keys())
        assert len(keys) == len(set(keys))
