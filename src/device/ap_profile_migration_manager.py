"""AP-to-device-profile migration and revert manager (menus 207 and 208).

This module hosts ``APProfileMigrationManager``, a static-method class that
implements two destructive Mist operations:

* Menu 207 -- bulk-reassign every AP bound to one source device profile to a
  chosen target device profile, with a full pre-change JSON backup written
  under ``data/`` before any AP is touched.
* Menu 208 -- consume a backup file written by menu 207 and reassign each
  listed AP back to the original source device profile, with a JSONL audit
  line appended via the shared ``TelemetryEmitter``.

Why:
    Mist device profiles carry the AP's radio, SSID, and channel plan. When an
    operator wants to promote a fleet to a new profile (or roll back a bad
    change) the UI forces one-AP-at-a-time edits. This module packages the
    fleet-wide walk, the pre-change snapshot, and the round-trip revert into a
    single audited, resumable operation that a small team can trust with
    hundreds of APs.

Module-import must remain side-effect free (``--help`` guard):
    Only ``import`` statements at module scope; all I/O, prompts, and API
    calls live inside functions invoked from the menu dispatch table.
"""

# WHY: PEP 604 unions and forward references keep annotations concise on 3.13+.
from __future__ import annotations

# WHY: bounded retry backoff and progress-time seams live in stdlib only per the
# no-new-dependency constraint from plan.md.
import logging
from typing import Any

# WHY: module logger uses the dotted module path so operators can filter by
# ``src.device.ap_profile_migration_manager`` in the shared MistHelper logs.
_LOGGER = logging.getLogger(__name__)


class APProfileMigrationManager:
    """Static-method class for AP-to-device-profile migration and revert.

    Groups the two public entry points and their private helpers so the
    backup-file schema, the AP-record shape, and the bounded retry policy
    live in one place. Follows the same pattern as ``SiteConfigManager``
    (menu 174) and ``OrgSyntheticProbesManager`` (menu 206).

    Why:
        The migrate and revert operations share the backup-file schema, the
        AP-discovery walk, and the profile-lookup helper. Splitting them into
        two modules would duplicate these helpers without a clear boundary
        (per research.md Decision 6).
    """

    @staticmethod
    def migrate_aps_between_device_profiles(session: Any | None = None) -> None:
        """Menu 207 entry point -- bulk-migrate APs between two device profiles.

        Discovers every AP bound to a chosen source profile across every site
        in the selected organization, writes a full pre-change JSON backup
        under ``data/``, then per-AP PUTs each AP to the chosen target
        profile with bounded retry and stop-on-first-failure semantics.

        Why:
            Delivers the primary user story (US1) as a single audited
            operation. The per-AP PUT is required by FR-017 so a mid-run
            failure records the exact partial-success set for a later revert.

        Args:
            session: The ``mistapi`` API session. When ``None`` the entry
                point resolves the ambient MistHelper session from
                ``ConfigUtils`` (matches the menu-206 wiring pattern).

        Returns:
            ``None``. The operation prints its own end-of-run summary and
            writes the backup file to disk; the caller does not consume any
            return value.

        Raises:
            NotImplementedError: This is the T005 skeleton placeholder; the
                real implementation lands in T017-T025.
        """
        # WHY: skeleton placeholder -- real body lands in T025 (US1
        # implementation phase). Interrogate treats a raised NotImplementedError
        # as executable code, satisfying the 100 percent floor while making it
        # loud if the placeholder ever reaches production.
        raise NotImplementedError(
            "APProfileMigrationManager.migrate_aps_between_device_profiles is a"
            " T005 skeleton; implementation lands in T017-T025.",
        )

    @staticmethod
    def revert_ap_profile_migration(session: Any | None = None) -> None:
        """Menu 208 entry point -- revert a prior migration from its backup file.

        Reads a backup file written by menu 207 and reassigns each listed AP
        back to the original source device profile, with strict backup-schema
        validation, source-profile-still-exists guard, per-AP missing-AP
        tolerance, and a JSONL audit line appended via ``TelemetryEmitter``.

        Why:
            Delivers the safety-net user story (US2). Every migration should
            be reversible with the same tool and the same audit trail; the
            backup file plus the JSONL audit line together satisfy FR-019
            through FR-025.

        Args:
            session: The ``mistapi`` API session. When ``None`` the entry
                point resolves the ambient MistHelper session from
                ``ConfigUtils`` (matches the menu-206 wiring pattern).

        Returns:
            ``None``. The operation prints its own end-of-run summary and
            appends a single JSONL row to the shared telemetry stream; the
            caller does not consume any return value.

        Raises:
            NotImplementedError: This is the T005 skeleton placeholder; the
                real implementation lands in T036-T043.
        """
        # WHY: skeleton placeholder -- real body lands in T043 (US2
        # implementation phase). See the sibling migrate entry-point comment
        # for the interrogate-coverage rationale.
        raise NotImplementedError(
            "APProfileMigrationManager.revert_ap_profile_migration is a"
            " T005 skeleton; implementation lands in T036-T043.",
        )
