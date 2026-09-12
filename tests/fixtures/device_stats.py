"""Device statistics test fixtures for Menu 13 audit tests.

Provides representative device stat records covering APs, switches,
gateways, and devices with missing optional fields. Used by both unit
and integration tests to ensure consistent test data.

Covers: US1, US2, US3 from spec-025.
"""

STAT_AP: dict[str, object] = {
    "device_id": "d1000000-0000-0000-0000-000000000001",
    "mac": "aabbccddeef1",
    "model": "AP43",
    "type": "ap",
    "site_id": "s1000000-0000-0000-0000-000000000001",
    "org_id": "o1000000-0000-0000-0000-000000000001",
    "name": "Lobby-AP-1",
    "status": "connected",
    "timestamp": 1700000000,
    "last_seen": 1700000000,
    "uptime": 86400,
    "cpu_stat": 12,
    "memory_stat": 45,
    "config_status": "synced",
}

STAT_SWITCH: dict[str, object] = {
    "device_id": "d2000000-0000-0000-0000-000000000002",
    "mac": "aabbccddeef2",
    "model": "EX4400",
    "type": "switch",
    "site_id": "s1000000-0000-0000-0000-000000000001",
    "org_id": "o1000000-0000-0000-0000-000000000001",
    "name": "Core-SW-1",
    "status": "connected",
    "timestamp": 1700000000,
    "last_seen": 1700000000,
    "uptime": 172800,
    "cpu_stat": 8,
    "memory_stat": 62,
    "config_status": "synced",
}

STAT_GATEWAY: dict[str, object] = {
    "device_id": "d3000000-0000-0000-0000-000000000003",
    "mac": "aabbccddeef3",
    "model": "SRX320",
    "type": "gateway",
    "site_id": "s1000000-0000-0000-0000-000000000001",
    "org_id": "o1000000-0000-0000-0000-000000000001",
    "name": "Edge-GW-1",
    "status": "connected",
    "timestamp": 1700000000,
    "last_seen": 1700000000,
    "uptime": 259200,
    "cpu_stat": 22,
    "memory_stat": 55,
    "config_status": "synced",
}

STAT_MINIMAL: dict[str, object] = {
    "device_id": "d4000000-0000-0000-0000-000000000004",
    "mac": "aabbccddeef4",
    "model": "AP33",
    "type": "ap",
    "org_id": "o1000000-0000-0000-0000-000000000001",
    "timestamp": 1700000000,
}

ALL_STATS: list[dict[str, object]] = [
    STAT_AP,
    STAT_SWITCH,
    STAT_GATEWAY,
    STAT_MINIMAL,
]


def make_device_stats_fixtures(count: int) -> list[dict[str, object]]:
    """Generate N unique device stat records for bulk testing.

    Args:
        count: Number of device stat records to generate.

    Returns:
        List of device stat dictionaries with unique IDs.
    """
    stats: list[dict[str, object]] = []
    for index in range(count):
        device_id = f"d0000000-0000-0000-0000-{index:012d}"
        mac_hex = f"{index:012x}"
        stats.append(
            {
                "device_id": device_id,
                "mac": mac_hex,
                "model": "AP43",
                "type": "ap",
                "site_id": "s1000000-0000-0000-0000-000000000001",
                "org_id": "o1000000-0000-0000-0000-000000000001",
                "name": f"Bulk-Device-{index}",
                "status": "connected",
                "timestamp": 1700000000,
                "last_seen": 1700000000,
                "uptime": 86400 + index,
                "cpu_stat": 10 + (index % 50),
                "memory_stat": 40 + (index % 30),
                "config_status": "synced",
            }
        )
    return stats
