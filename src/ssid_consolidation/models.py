from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class Phase1Matrix:
    site_id: str
    site_name: str
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    target_ssid_name: Optional[str] = None
    target_ssid_id: Optional[str] = None
    psk_detected: int = 0
    edge_cluster_id: Optional[str] = None
    edge_cluster_name: Optional[str] = None
    anomaly_code: Optional[str] = None
    collected_at: Optional[str] = None


@dataclass
class DeviationReport:
    cluster_id: str
    deviations: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class OperationLogEntry:
    id: Optional[int] = None
    phase: int = 0
    site_id: Optional[str] = None
    action: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
