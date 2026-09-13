"""Device inventory test fixtures for Menu 12 audit tests.

Provides representative device records covering APs, switches, and
devices with missing optional fields. Used by both unit and integration
tests to ensure consistent test data.
"""

DEVICE_AP: dict[str, object] = {
    "id": "d1000000-0000-0000-0000-000000000001",
    "mac": "aabbccddeef1",
    "serial": "SN-AP-001",
    "model": "AP43",
    "type": "ap",
    "site_id": "s1000000-0000-0000-0000-000000000001",
    "org_id": "o1000000-0000-0000-0000-000000000001",
    "name": "Lobby-AP-1",
    "sku": "AP43-US",
    "hw_rev": "A1",
    "created_time": 1700000000,
    "modified_time": 1700100000,
    "magic": "CLAIM-AP-001",
}

DEVICE_SWITCH: dict[str, object] = {
    "id": "d2000000-0000-0000-0000-000000000002",
    "mac": "aabbccddeef2",
    "serial": "SN-SW-001",
    "model": "EX4400",
    "type": "switch",
    "site_id": "s1000000-0000-0000-0000-000000000001",
    "org_id": "o1000000-0000-0000-0000-000000000001",
    "name": "Core-SW-1",
    "sku": "EX4400-48T",
    "hw_rev": "B2",
    "created_time": 1700000000,
    "modified_time": 1700200000,
}

DEVICE_MISSING_OPTIONAL: dict[str, object] = {
    "id": "d3000000-0000-0000-0000-000000000003",
    "mac": "aabbccddeef3",
    "serial": "SN-GW-001",
    "model": "SRX320",
    "type": "gateway",
    "org_id": "o1000000-0000-0000-0000-000000000001",
}

ALL_DEVICES: list[dict[str, object]] = [DEVICE_AP, DEVICE_SWITCH, DEVICE_MISSING_OPTIONAL]


def make_device_fixtures(count: int) -> list[dict[str, object]]:
    """Generate N unique device records for bulk testing.

    Args:
        count: Number of device records to generate.

    Returns:
        List of device dictionaries with unique IDs and MACs.
    """
    devices: list[dict[str, object]] = []
    for index in range(count):
        device_id = f"d0000000-0000-0000-0000-{index:012d}"
        mac_hex = f"{index:012x}"
        devices.append(
            {
                "id": device_id,
                "mac": mac_hex,
                "serial": f"SN-BULK-{index:04d}",
                "model": "AP43",
                "type": "ap",
                "site_id": "s1000000-0000-0000-0000-000000000001",
                "org_id": "o1000000-0000-0000-0000-000000000001",
                "name": f"Bulk-Device-{index}",
                "sku": "AP43-US",
                "hw_rev": "A1",
                "created_time": 1700000000,
                "modified_time": 1700000000 + index,
            }
        )
    return devices
