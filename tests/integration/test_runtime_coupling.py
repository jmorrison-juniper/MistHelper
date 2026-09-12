"""Runtime coupling harness for serial decomposition phase gates."""

from __future__ import annotations

import os
from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class RuntimeCouplingProfile:
    """Defines a runtime coupling profile used by phase-gate checks."""

    name: str
    phase_number: int
    target_group: str


RUNTIME_COUPLING_PROFILES: tuple[RuntimeCouplingProfile, ...] = (
    RuntimeCouplingProfile("phase_1", 1, "SiteInventoryHealthAnalyzer+SiteAnalyticsConfigurator"),
    RuntimeCouplingProfile("phase_2", 2, "TroubleshootUtils+SSHRunnerManager"),
    RuntimeCouplingProfile("phase_3", 3, "WAN2MigrationManager+WANProbeDeviceOverrideManager"),
    RuntimeCouplingProfile("phase_4", 4, "SiteConfigManager"),
    RuntimeCouplingProfile("phase_5", 5, "SiteExportUtils"),
    RuntimeCouplingProfile("phase_6", 6, "OrgDeviceInventorySummary"),
    RuntimeCouplingProfile("phase_7", 7, "GatewayExportUtils"),
    RuntimeCouplingProfile("phase_8", 8, "ServicePingManager"),
    RuntimeCouplingProfile("phase_9", 9, "PacketCaptureManager"),
)


def _selected_profile_names() -> set[str]:
    """Read optional phase profile selection from environment variable."""
    raw_profiles = os.getenv("RUNTIME_COUPLING_PROFILES", "").strip()
    if not raw_profiles:
        return {profile.name for profile in RUNTIME_COUPLING_PROFILES}
    return {value.strip() for value in raw_profiles.split(",") if value.strip()}


@pytest.mark.parametrize("profile", RUNTIME_COUPLING_PROFILES, ids=lambda profile: profile.name)
def test_runtime_coupling_profile_selection(profile: RuntimeCouplingProfile) -> None:
    """Ensure selected runtime profiles are valid and uniquely defined."""
    selected_profile_names = _selected_profile_names()
    if profile.name not in selected_profile_names:
        pytest.skip(f"Skipping {profile.name}; not selected in RUNTIME_COUPLING_PROFILES")

    assert profile.phase_number >= 1
    assert profile.target_group


def test_runtime_profile_names_are_unique() -> None:
    """Ensure no duplicate profile names exist in the harness."""
    names = [profile.name for profile in RUNTIME_COUPLING_PROFILES]
    assert len(names) == len(set(names)), "Runtime coupling profile names must be unique"


def test_runtime_profile_phase_numbers_are_unique() -> None:
    """Ensure phase numbers map 1:1 with profiles."""
    phase_numbers = [profile.phase_number for profile in RUNTIME_COUPLING_PROFILES]
    assert len(phase_numbers) == len(set(phase_numbers)), "Each phase number must appear once"


def test_runtime_profile_list_covers_all_9_phases() -> None:
    """Ensure harness includes all required decomposition phases."""
    phase_numbers = sorted(profile.phase_number for profile in RUNTIME_COUPLING_PROFILES)
    assert phase_numbers == [1, 2, 3, 4, 5, 6, 7, 8, 9]
