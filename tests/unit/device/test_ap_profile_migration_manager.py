"""Unit tests for ``APProfileMigrationManager`` (menus 207 and 208).

This test module hosts every unit and integration-style test for the
AP-to-device-profile migration and revert feature (specs/1029-ap-profile-migration).

Why:
    One test file per manager class keeps the test tree parallel to the
    source tree and matches the ``tests/unit/device/`` convention used by
    ``test_arp_command_manager.py`` and ``test_device_reboot_manager.py``.
    Every case in this file starts by importing the manager and mocking the
    ``mistapi`` session; no live API traffic is issued.
"""

# WHY: forward-refs keep the annotations readable and let pytest introspect the
# test names without evaluating the module-level types.
from __future__ import annotations


def test_placeholder_manager_importable() -> None:
    """Skeleton import check -- proves T005 wired the module up.

    Why:
        The US1 / US2 / US3 test tasks all add cases to this file. A single
        import-only case run in isolation confirms the module tree and the
        test discovery both agree that ``APProfileMigrationManager`` is
        addressable before any real test method depends on it.
    """
    # WHY: local import keeps module-import side effects out of the test-
    # collection phase (matches the module docstring's --help guard).
    from src.device.ap_profile_migration_manager import (
        APProfileMigrationManager,
    )

    # WHY: assert on the class rather than an instance because the manager is
    # a static-method container -- there is nothing to construct.
    assert APProfileMigrationManager is not None
