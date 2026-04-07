from dataclasses import dataclass, field


@dataclass
class Phase1Matrix:
    site_id: str
    site_name: str
    template_id: str | None = None
    template_name: str | None = None
    target_ssid_name: str | None = None
    target_ssid_id: str | None = None
    psk_detected: int = 0
    edge_cluster_id: str | None = None
    edge_cluster_name: str | None = None
    anomaly_code: str | None = None
    collected_at: str | None = None


@dataclass
class DeviationReport:
    cluster_id: str
    deviations: dict[str, dict[str, int]] = field(default_factory=dict)


@dataclass
class OperationLogEntry:
    id: int | None = None
    phase: int = 0
    site_id: str | None = None
    action: str | None = None
    status: str | None = None
    message: str | None = None
    timestamp: str | None = None
