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

import json
import logging
import sys
import time
import types
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# WHY: the module-under-test lives here; the alias `apm_mod` gives short access
# to module-scope names (helpers, logger) when tests need to patch them.
from src.device import ap_profile_migration_manager as apm_mod
from src.device.ap_profile_migration_manager import APProfileMigrationManager

# WHY: caplog / patch(...) targets must use the dotted module path so the
# logger the code writes to matches the logger the test captures on.
_LOGGER_NAME = "src.device.ap_profile_migration_manager"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fake_mh(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Install a stub ``MistHelper`` module so lazy imports resolve here.

    Why:
        ``APProfileMigrationManager`` reaches ``ConfigUtils`` and
        ``InputUtils`` (and possibly ``PromptUtils``) via a call-time
        ``import MistHelper as _mh`` to avoid a circular import at module
        load. Registering a synthetic module in ``sys.modules`` lets every
        test stub only the attributes it needs.

    Args:
        monkeypatch: pytest's built-in ``sys.modules`` patcher.

    Returns:
        The synthetic ``MistHelper`` module the test can further customise.
    """
    module = types.ModuleType("MistHelper")
    # WHY: expose the same top-level names the real MistHelper.py exports so
    # the manager's lazy _get_config_utils()/_get_input_utils() helpers do
    # not raise AttributeError while the test is mocking behaviour.
    module.ConfigUtils = MagicMock()
    module.InputUtils = MagicMock()
    module.PromptUtils = MagicMock()
    module.apisession = types.SimpleNamespace(host=None, apitoken=None)
    # WHY: the default org-resolver returns a stable UUID so tests that do
    # not care about org selection get a deterministic value.
    module.ConfigUtils.get_cached_or_prompted_org_id.return_value = "203d3d02-dbc0-4c1b-bc44-13e2d1e1a1ff"
    # WHY: safe_input defaults to cancel; any test that needs MIGRATE / DRY-RUN
    # overrides side_effect on the mock explicitly.
    module.InputUtils.safe_input.return_value = ""
    monkeypatch.setitem(sys.modules, "MistHelper", module)
    return module


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Redirect the manager's ``data/`` writes to a per-test tmp dir.

    Why:
        The backup writer computes its target path under ``data/`` at the
        repo root; letting a unit test scribble there would pollute the
        real workspace and break INV-1 byte-stability on unrelated files.
        We monkeypatch a ``_DATA_DIR`` module constant (the implementation
        MUST honour it) and also ``chdir`` so a naive ``Path("data")``
        relative resolution ends up in the same place.

    Args:
        tmp_path: pytest's per-test temp directory.
        monkeypatch: pytest's env / attribute patcher.

    Returns:
        The temp ``data`` sub-directory the tests should point at.
    """
    d = tmp_path / "data"
    d.mkdir()
    # WHY: chdir keeps a Path("data") resolution consistent with the tmp path
    # even if the implementation forgets to honour an injected data_dir.
    monkeypatch.chdir(tmp_path)
    # WHY: expose an attribute the implementation MAY read; harmless when
    # the implementation instead accepts a data_dir argument.
    monkeypatch.setattr(apm_mod, "_DATA_DIR", str(d), raising=False)
    return d


def _profile(pid: str, name: str) -> dict[str, Any]:
    """Return a minimal Mist device-profile JSON payload.

    Why:
        Every test that mocks ``getOrgDeviceProfile`` returns a dict; a
        one-liner factory keeps the fixture data compact and consistent.

    Args:
        pid: The device-profile UUID.
        name: The device-profile human-readable name.

    Returns:
        A dict shaped like Mist's device-profile JSON (minimum fields the
        backup snapshot validators require).
    """
    return {"id": pid, "name": name, "type": "ap"}


def _ap_record(device_id: str, site_id: str, mac: str, hostname: str | None = None) -> dict[str, Any]:
    """Return one entry shaped per data-model §1.4 (``APRecord``).

    Why:
        Centralises the field set so a spec update (add/remove keys) only
        needs one edit here.

    Args:
        device_id: The AP device UUID.
        site_id: The site UUID the AP is under.
        mac: The AP MAC address in canonical Mist form.
        hostname: Optional AP hostname (may be ``None``).

    Returns:
        A dict shaped per ``data-model.md`` §1.4.
    """
    return {
        "device_id": device_id,
        "site_id": site_id,
        "mac": mac,
        "hostname": hostname,
    }


# ---------------------------------------------------------------------------
# Skeleton import check (kept from T006 — still valuable as a smoke test)
# ---------------------------------------------------------------------------


def test_placeholder_manager_importable() -> None:
    """Skeleton import check -- proves T005 wired the module up.

    Why:
        The US1 / US2 / US3 test tasks all add cases to this file. A single
        import-only case run in isolation confirms the module tree and the
        test discovery both agree that ``APProfileMigrationManager`` is
        addressable before any real test method depends on it.
    """
    # WHY: assert on the class rather than an instance because the manager is
    # a static-method container -- there is nothing to construct.
    assert APProfileMigrationManager is not None


# ---------------------------------------------------------------------------
# T009 -- refuse when source == target
# ---------------------------------------------------------------------------


def test_migrate_refuses_when_source_equals_target(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Selecting the same profile for source and target MUST refuse and issue zero PUTs.

    Why:
        FR-008 protects operators from a no-op destructive run whose only
        effect is a spurious "success" audit line. The refusal MUST be
        visible on stdout and MUST short-circuit before any AP is touched.
    """
    # WHY: force _pick_ap_device_profile to return the same profile twice.
    same_id = "aaaa1111-2222-3333-4444-555566667777"
    same = (same_id, "SharedProfile", _profile(same_id, "SharedProfile"))
    put_calls: list[Any] = []
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[same, same]),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=lambda *a, **kw: put_calls.append((a, kw))),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    out = capsys.readouterr().out
    # WHY: text-content assertion is deliberately lenient -- any wording that
    # names "source" and "target" satisfies FR-008; the exact string is
    # locked by the STE lint (T053), not by this test.
    assert "source" in out.lower() and "target" in out.lower(), f"Refusal must mention source/target; got: {out!r}"
    assert put_calls == [], f"Zero PUTs expected on refusal; got {len(put_calls)}"


# ---------------------------------------------------------------------------
# T010 -- report nothing-to-migrate when source is empty
# ---------------------------------------------------------------------------


def test_migrate_reports_nothing_to_migrate_when_source_empty(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty AP-discovery MUST print the short-circuit message; zero files and zero PUTs.

    Why:
        FR-010 requires an early exit when the source profile has no APs
        bound so the operator does not stare at a spinning progress bar for
        an empty fleet. Also proves no backup file is written when there is
        nothing to migrate (FR-011 negative side).
    """
    src = ("aaaa1111-2222-3333-4444-555566667777", "Source", _profile("aaaa1111-2222-3333-4444-555566667777", "Source"))
    tgt = ("bbbb1111-2222-3333-4444-555566667777", "Target", _profile("bbbb1111-2222-3333-4444-555566667777", "Target"))
    put_calls: list[Any] = []
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=[]),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=lambda *a, **kw: put_calls.append((a, kw))),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    out = capsys.readouterr().out
    assert (
        "No APs bound to source profile. Nothing to migrate." in out
    ), f"Expected exact short-circuit message; got: {out!r}"
    assert put_calls == [], "Zero PUTs expected on empty source"
    # WHY: FR-011 negative side -- no backup file must be written when there
    # is nothing to back up.
    assert (
        list(data_dir.glob("ap-profile-migration_*.json")) == []
    ), "No backup file should be written when the source profile is empty"


# ---------------------------------------------------------------------------
# T011 -- backup file MUST be written before the first PUT
# ---------------------------------------------------------------------------


def test_migrate_writes_backup_before_any_put(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """The backup file MUST land on disk before the first ``updateSiteDevice`` call.

    Why:
        FR-011 makes the backup file the single source of truth for a
        revert; a PUT issued before the file exists is unrecoverable. This
        test uses a shared call-order recorder to lock the ordering.
    """
    order: list[str] = []
    src = ("src-id", "SourceName", _profile("src-id", "SourceName"))
    tgt = ("tgt-id", "TargetName", _profile("tgt-id", "TargetName"))
    aps = [_ap_record("d1", "s1", "5c5b350e0001", "ap-1")]

    def _record_write(payload: dict[str, Any], data_dir_arg: str) -> str:
        """Record and return a fake backup path."""
        order.append("backup_write")
        return str(Path(data_dir_arg) / "ap-profile-migration_20260727T000000Z_src-id_to_tgt-id.json")

    def _record_put(*args: Any, **kwargs: Any) -> Any:
        """Record any updateSiteDevice call in order."""
        order.append("put")
        response = MagicMock()
        response.status_code = 200
        return response

    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch.object(APProfileMigrationManager, "_write_backup_file", side_effect=_record_write),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_record_put),
        patch("time.sleep"),  # WHY: never actually sleep in unit tests.
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: the first observed event MUST be the backup write; every put must
    # come after it.
    assert order, "Expected at least one recorded event"
    assert order[0] == "backup_write", f"Backup MUST precede first PUT; got order={order!r}"
    assert "put" in order, "Expected at least one PUT call after backup"


# ---------------------------------------------------------------------------
# T012 -- backup shape matches data-model §1.3
# ---------------------------------------------------------------------------


def test_migrate_backup_shape_matches_data_model_section_1_3(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """The written backup JSON MUST expose every top-level field per data-model §1.3.

    Why:
        FR-013 pins the on-disk backup schema; a silent drift would break
        the revert (menu 208) or every downstream forensic tool. This test
        drives the full entry point with two APs across two sites and
        loads the resulting file.
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "Source-Profile", _profile(src_id, "Source-Profile"))
    tgt = (tgt_id, "Target-Profile", _profile(tgt_id, "Target-Profile"))
    aps = [
        _ap_record("d1", "site-1", "5c5b350e0001", "ap-1"),
        _ap_record("d2", "site-2", "5c5b350e0002", None),
    ]

    def _ok_put(*args: Any, **kwargs: Any) -> Any:
        """Return a healthy 200 response for every PUT."""
        r = MagicMock()
        r.status_code = 200
        return r

    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_ok_put),
        patch("time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    files = list(data_dir.glob("ap-profile-migration_*.json"))
    assert len(files) == 1, f"Exactly one backup file expected; got {files!r}"
    payload = json.loads(files[0].read_text(encoding="utf-8"))

    # WHY: assert every required top-level field per data-model §1.3.
    assert payload["schema_version"] == 1
    assert isinstance(payload["org_id"], str) and payload["org_id"]
    assert isinstance(payload["migration_timestamp_utc"], str) and payload["migration_timestamp_utc"]
    assert payload["source_profile_id"] == src_id
    assert payload["target_profile_id"] == tgt_id
    assert payload["source_profile_snapshot"]["id"] == src_id  # rule 6
    assert payload["target_profile_snapshot"]["id"] == tgt_id  # rule 6
    assert isinstance(payload["aps_planned"], list) and len(payload["aps_planned"]) == 2
    for rec in payload["aps_planned"]:
        assert set(rec.keys()) >= {"device_id", "site_id", "mac", "hostname"}
    assert isinstance(payload["aps_reassigned"], list)
    assert payload["outcome"] in {"success", "partial", "failure"}
    assert "failure_detail" in payload  # None on success, dict on partial/failure


# ---------------------------------------------------------------------------
# T013 -- retry cadence [0.5, 1.0] on transient PUT failure
# ---------------------------------------------------------------------------


def test_migrate_retries_transient_put_failure_then_succeeds(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """A transient PUT failure MUST retry with the ``[0.5, 1.0]`` backoff sequence.

    Why:
        research.md Decision 2 pins the retry cadence as bounded and
        deterministic. The test observes ``time.sleep`` to lock the
        [0.5, 1.0] sequence; a silent tune to [1, 2] would break here.
    """
    src = ("src-id", "Src", _profile("src-id", "Src"))
    tgt = ("tgt-id", "Tgt", _profile("tgt-id", "Tgt"))
    aps = [_ap_record("d1", "site-1", "5c5b350e0001", "ap-1")]
    put_side = [OSError("boom"), OSError("boom-2"), MagicMock(status_code=200)]
    sleep_calls: list[float] = []

    def _sleep_spy(seconds: float) -> None:
        """Record every backoff interval requested by the retry loop."""
        sleep_calls.append(seconds)

    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=put_side),
        # WHY: stub pacing so this test only observes retry-backoff sleeps.
        # The pacing behaviour is validated separately by TR006-TR018.
        patch.object(APProfileMigrationManager, "_apply_pacing", return_value=None),
        patch("time.sleep", side_effect=_sleep_spy),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: only the retry backoffs should be observed. Progress-line loops
    # MUST NOT sleep in this manager (research Decision 2 keeps retries the
    # only sleep source).
    assert sleep_calls == [0.5, 1.0], f"Retry cadence MUST be [0.5, 1.0]; observed sleeps={sleep_calls!r}"
    # WHY: the successful third attempt records the AP as reassigned.
    files = list(data_dir.glob("ap-profile-migration_*.json"))
    assert files, "Backup file expected on success"
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["aps_reassigned"] == ["d1"]
    assert payload["outcome"] == "success"


# ---------------------------------------------------------------------------
# T014 -- stop-on-second-retry-exhaustion with partial-success record
# ---------------------------------------------------------------------------


def test_migrate_stops_on_second_retry_exhaustion_and_records_partial_success(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """Retry exhaustion on AP 2 MUST record APs 0/1 as success and stop before 3/4.

    Why:
        FR-017 requires a stop-on-first-failure policy so the on-disk
        backup exactly matches the state Mist is in when the run halts.
        A revert (menu 208) reads ``aps_reassigned`` to know which APs to
        roll back -- silently continuing past a failed AP would make the
        revert unsafe.
    """
    src = ("src-id", "Src", _profile("src-id", "Src"))
    tgt = ("tgt-id", "Tgt", _profile("tgt-id", "Tgt"))
    aps = [_ap_record(f"d{i}", "site-1", f"mac{i:012x}", f"ap-{i}") for i in range(5)]

    put_calls: list[tuple[Any, ...]] = []

    def _put_side(session: Any, site_id: str, device_id: str, body: Any) -> Any:
        """Succeed for d0/d1; always fail for d2; NEVER be called for d3/d4."""
        put_calls.append((site_id, device_id))
        if device_id in {"d0", "d1"}:
            r = MagicMock()
            r.status_code = 200
            return r
        raise OSError(f"always fails for {device_id}")

    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_put_side),
        patch("time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: d3 and d4 MUST NOT appear in the PUT log -- stop-on-first-failure.
    touched = {dev for (_site, dev) in put_calls}
    assert "d3" not in touched and "d4" not in touched, f"APs after the failed one MUST NOT be PUT; touched={touched!r}"

    files = list(data_dir.glob("ap-profile-migration_*.json"))
    assert files, "Backup file expected even on partial failure"
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["aps_reassigned"] == ["d0", "d1"]
    assert payload["outcome"] == "partial"
    fd = payload["failure_detail"]
    assert fd is not None
    assert fd["failed_device_id"] == "d2"
    assert fd["reassigned_count"] == 2
    assert fd["planned_count"] == 5


# ---------------------------------------------------------------------------
# T015 -- progress prints at N=1, every 10, and N=last
# ---------------------------------------------------------------------------


def test_migrate_progress_prints_at_least_every_10_aps(
    fake_mh: types.ModuleType,
    data_dir: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Progress lines MUST appear at N=1, every N%10==0, and at N=27 (last).

    Why:
        research.md Decision 3 and SC-004 require a visible progress cadence
        so operators watching a hundred-AP migration do not think the tool
        has hung. This test drives 27 APs and checks caplog for at least
        the required index set.
    """
    src = ("src-id", "Src", _profile("src-id", "Src"))
    tgt = ("tgt-id", "Tgt", _profile("tgt-id", "Tgt"))
    aps = [_ap_record(f"d{i}", "site-1", f"mac{i:012x}", f"ap-{i}") for i in range(27)]

    def _ok_put(*a: Any, **kw: Any) -> Any:
        """Return healthy 200 for every PUT."""
        r = MagicMock()
        r.status_code = 200
        return r

    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"
    caplog.set_level(logging.INFO, logger=_LOGGER_NAME)
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_ok_put),
        patch("time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: extract any "X of 27" pattern from INFO messages -- the exact
    # format is up to the implementation; we assert on the required indices.
    indices_seen: set[int] = set()
    for rec in caplog.records:
        text = rec.getMessage()
        for tok in ("1 of 27", "10 of 27", "20 of 27", "27 of 27"):
            if tok in text:
                indices_seen.add(int(tok.split(" ", 1)[0]))
    required = {1, 10, 20, 27}
    assert required.issubset(
        indices_seen
    ), f"Progress must include indices {sorted(required)}; saw {sorted(indices_seen)}"


# ---------------------------------------------------------------------------
# T016 -- US1 end-to-end with a mocked mistapi session
# ---------------------------------------------------------------------------


def test_us1_end_to_end_with_mocked_mistapi_session(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Full US1 flow against a mocked mistapi session with 2 sites and 3 APs.

    Why:
        Ties every private helper together and asserts the operator-visible
        contract: 3 APs reassigned, backup file written under the tmp
        ``data/`` dir, ``outcome == "success"``, and the printed summary
        names the source, the target, and the backup path (quickstart §1).
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "Data-Transfer-Profile", _profile(src_id, "Data-Transfer-Profile"))
    tgt = (tgt_id, "Main-Profile", _profile(tgt_id, "Main-Profile"))
    # WHY: 2 sites x 1-or-2 APs = 3 total APs bound to the source profile.
    aps = [
        _ap_record("d1", "site-1", "5c5b350e0001", "ap-1"),
        _ap_record("d2", "site-1", "5c5b350e0002", "ap-2"),
        _ap_record("d3", "site-2", "5c5b350e0003", "ap-3"),
    ]

    put_log: list[str] = []

    def _ok_put(session: Any, site_id: str, device_id: str, body: Any) -> Any:
        """Return healthy 200 and log the device_id for later assertion."""
        put_log.append(device_id)
        r = MagicMock()
        r.status_code = 200
        return r

    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_ok_put),
        patch("time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: every planned AP was PUT exactly once, in order.
    assert put_log == ["d1", "d2", "d3"]

    files = list(data_dir.glob("ap-profile-migration_*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["outcome"] == "success"
    assert payload["aps_reassigned"] == ["d1", "d2", "d3"]

    out = capsys.readouterr().out
    # WHY: summary must name source, target, and the backup file path (FR-018).
    assert "Data-Transfer-Profile" in out
    assert "Main-Profile" in out
    assert str(files[0]) in out or files[0].name in out


# ---------------------------------------------------------------------------
# US2 shared fixtures (T028-T035)
# ---------------------------------------------------------------------------


def _backup_fixture(**overrides: Any) -> dict[str, Any]:
    """Return a valid backup payload per data-model 1.3 for revert tests.

    Why:
        Centralises the required-field set so every US2 test can build a
        partial variant (missing schema, missing org_id, unknown id in
        aps_reassigned) via a single keyword override without repeating the
        base dict in every case.

    Args:
        **overrides: Fields to override on top of the baseline valid payload.
            Pass a mapping value to replace or add a field.

    Returns:
        A dict shaped per data-model 1.3 that a spec-conforming revert would
        accept unmodified.
    """
    # WHY: fixed IDs keep the produced backup filename stable across tests so
    # a follow-up glob under data_dir returns exactly one candidate.
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    base: dict[str, Any] = {
        "schema_version": 1,
        "org_id": "203d3d02-dbc0-4c1b-bc44-13e2d1e1a1ff",
        "migration_timestamp_utc": "2026-07-27T19:30:45Z",
        "source_profile_id": src_id,
        "target_profile_id": tgt_id,
        "source_profile_snapshot": {"id": src_id, "name": "Source-Profile", "type": "ap"},
        "target_profile_snapshot": {"id": tgt_id, "name": "Target-Profile", "type": "ap"},
        "aps_planned": [
            _ap_record("d1", "site-1", "5c5b350e0001", "ap-1"),
            _ap_record("d2", "site-1", "5c5b350e0002", "ap-2"),
        ],
        "aps_reassigned": ["d1", "d2"],
        "outcome": "success",
        "failure_detail": None,
    }
    for key, value in overrides.items():
        base[key] = value
    return base


def _write_backup(data_dir: Path, payload: dict[str, Any]) -> Path:
    """Write ``payload`` to disk under ``data_dir`` and return the Path.

    Why:
        Centralises the filename convention (data-model 1.1) so US2 tests do
        not each hand-roll a filename that could drift out of sync with the
        production writer helper.

    Args:
        data_dir: Directory under which to write the backup fixture.
        payload: Backup payload dict to serialise as JSON.

    Returns:
        The absolute Path of the file just written.
    """
    # WHY: use the source/target IDs from the payload so the filename stays
    # consistent with the on-disk convention even for the malformed fixtures.
    src = str(payload.get("source_profile_id", "src"))
    tgt = str(payload.get("target_profile_id", "tgt"))
    fname = f"ap-profile-migration_20260727T193045Z_{src}_to_{tgt}.json"
    p = data_dir / fname
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# T028 -- reject wrong schema_version
# ---------------------------------------------------------------------------


def test_revert_rejects_backup_with_wrong_schema_version(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A backup with ``schema_version = 99`` MUST refuse and issue zero PUTs.

    Why:
        FR-020 and data-model 1.6 rule 1 pin ``schema_version`` at 1. Any
        other value MUST be refused so a future backup format cannot silently
        roll APs to the wrong profile.
    """
    # WHY: build a fixture whose schema is intentionally out of range.
    payload = _backup_fixture(schema_version=99)
    backup_path = _write_backup(data_dir, payload)
    put_calls: list[Any] = []

    with (
        # WHY: create=True lets the patch land before the helper exists in
        # the skeleton, so this test can be authored before T037.
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch(
            "mistapi.api.v1.sites.devices.updateSiteDevice",
            side_effect=lambda *a, **kw: put_calls.append((a, kw)),
        ),
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    out = capsys.readouterr().out
    # WHY: name the exact field the operator must fix -- a generic "invalid
    # backup" message leaves the operator guessing which rule tripped.
    assert "schema_version" in out, f"Refusal MUST name schema_version; got: {out!r}"
    assert put_calls == [], f"Zero PUTs expected on schema refusal; got {len(put_calls)}"


# ---------------------------------------------------------------------------
# T029 -- reject when any required top-level field is missing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "missing_field",
    [
        "org_id",
        "source_profile_id",
        "target_profile_id",
        "migration_timestamp_utc",
        "aps_planned",
    ],
)
def test_revert_rejects_backup_with_missing_required_fields(
    missing_field: str,
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Removing any required top-level field MUST refuse and issue zero PUTs.

    Why:
        Data-model 1.6 rules 2-4 list five required top-level fields; the
        parametrized run exercises each one so a regression that skips a
        single rule is caught by the pytest summary rather than surfacing on
        a live revert against a corrupt backup.
    """
    # WHY: start from the valid base fixture and delete exactly one field.
    payload = _backup_fixture()
    del payload[missing_field]
    backup_path = _write_backup(data_dir, payload)
    put_calls: list[Any] = []

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch(
            "mistapi.api.v1.sites.devices.updateSiteDevice",
            side_effect=lambda *a, **kw: put_calls.append((a, kw)),
        ),
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    out = capsys.readouterr().out
    assert missing_field in out, f"Refusal MUST name the missing field {missing_field!r}; got: {out!r}"
    assert put_calls == [], f"Zero PUTs expected on missing-field refusal; got {len(put_calls)}"


# ---------------------------------------------------------------------------
# T030 -- reject when aps_reassigned lists an unknown device_id
# ---------------------------------------------------------------------------


def test_revert_rejects_backup_when_aps_reassigned_contains_unknown_id(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unknown ID in ``aps_reassigned`` MUST refuse the revert.

    Why:
        Data-model 1.6 rule 5 is a defensive check: a hand-edited backup
        MUST NOT convince the revert to PUT an AP that was never in the
        migration plan. This test injects an id that is not in ``aps_planned``
        and asserts refusal.
    """
    payload = _backup_fixture(aps_reassigned=["d1", "d2", "ghost-id-not-in-plan"])
    backup_path = _write_backup(data_dir, payload)
    put_calls: list[Any] = []

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch(
            "mistapi.api.v1.sites.devices.updateSiteDevice",
            side_effect=lambda *a, **kw: put_calls.append((a, kw)),
        ),
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    out = capsys.readouterr().out.lower()
    # WHY: the operator MUST see either the offending id or the field name so
    # they can locate the mismatch in the backup file.
    assert (
        "aps_reassigned" in out or "ghost-id-not-in-plan" in out
    ), f"Refusal MUST name aps_reassigned or the offending id; got: {out!r}"
    assert put_calls == [], f"Zero PUTs expected on unknown-id refusal; got {len(put_calls)}"


# ---------------------------------------------------------------------------
# T031 -- refuse when the source profile no longer exists in the org
# ---------------------------------------------------------------------------


def test_revert_refuses_when_source_profile_deleted_from_org(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A 404 on ``getOrgDeviceProfile`` MUST stop the revert with an audited failure.

    Why:
        FR-021 requires the revert to fail loudly (not silently) when the
        source profile the backup PUT-s back to has been deleted. The
        operator sees the profile id and a clear next-step message; the audit
        line records ``outcome == "failure"`` for downstream reporting.
    """
    payload = _backup_fixture()
    backup_path = _write_backup(data_dir, payload)
    put_calls: list[Any] = []

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        # WHY: patch the helper so the test does not depend on the exact
        # exception type raised by mistapi on a 404.
        patch.object(
            APProfileMigrationManager,
            "_verify_source_profile_exists",
            return_value=False,
            create=True,
        ),
        patch(
            "mistapi.api.v1.sites.devices.updateSiteDevice",
            side_effect=lambda *a, **kw: put_calls.append((a, kw)),
        ),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit") as mock_emit,
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    out = capsys.readouterr().out
    # WHY: operator MUST see the missing profile id so they can decide
    # whether to recreate it or hand-edit the backup file.
    assert payload["source_profile_id"] in out, f"Refusal MUST name the missing source profile id; got: {out!r}"
    assert put_calls == [], f"Zero PUTs expected when source profile missing; got {len(put_calls)}"

    # WHY: FR-025 -- one audit row MUST land even on this early-refusal path.
    assert mock_emit.call_count >= 1, "Audit emit MUST fire even when the source profile is missing"
    event = mock_emit.call_args.args[0]
    assert event["event_type"] == "ap_profile_migration_revert"
    assert event["outcome"] == "failure"


# ---------------------------------------------------------------------------
# T032 -- skip a missing AP and report partial success
# ---------------------------------------------------------------------------


def test_revert_skips_missing_ap_and_reports_partial(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One AP absent from Mist MUST count as ``missing`` and yield ``outcome == "partial"``.

    Why:
        FR-023 and data-model 2.2 require the missing-AP path to be tolerant
        (do not abort) but visible (name the missing AP in the summary and
        the audit line). This test drives 5 APs with the middle one
        returning ``"missing"``.
    """
    aps_planned = [_ap_record(f"d{i}", "site-1", f"mac{i:012x}", f"ap-{i}") for i in range(1, 6)]
    aps_reassigned = [rec["device_id"] for rec in aps_planned]
    payload = _backup_fixture(aps_planned=aps_planned, aps_reassigned=aps_reassigned)
    backup_path = _write_backup(data_dir, payload)

    reverted_calls: list[str] = []

    def _revert_side(session: Any, device_id: str, site_id: str, source_profile_id: str, **kw: Any) -> Any:
        """Return ``"missing"`` for d3; record every other id as reverted.

        Why:
            Simulates one AP that no longer exists in Mist; every other AP
            reverts successfully so the entry point must count 4 reverts and
            1 missing.
        """
        del session, site_id, source_profile_id, kw  # WHY: signature-only params.
        reverted_calls.append(device_id)
        if device_id == "d3":
            return "missing"
        return None

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch.object(APProfileMigrationManager, "_verify_source_profile_exists", return_value=True, create=True),
        patch.object(APProfileMigrationManager, "_confirm_revert", return_value="live", create=True),
        patch.object(APProfileMigrationManager, "_revert_one_ap", side_effect=_revert_side, create=True),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit") as mock_emit,
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    # WHY: every planned AP MUST be attempted -- FR-023 is tolerant, not
    # stop-on-failure.
    assert reverted_calls == ["d1", "d2", "d3", "d4", "d5"], f"Every AP must be attempted; got {reverted_calls!r}"

    out = capsys.readouterr().out
    # WHY: the missing AP MUST appear by id in the summary so the operator
    # can decide whether to hand-fix it.
    assert "d3" in out, f"Summary MUST name the missing AP by id; got: {out!r}"

    mock_emit.assert_called_once()
    event = mock_emit.call_args.args[0]
    assert event["event_type"] == "ap_profile_migration_revert"
    assert event["outcome"] == "partial"
    assert event["missing_count"] == 1
    assert event["reverted_count"] == 4
    assert event["failed_count"] == 0


# ---------------------------------------------------------------------------
# T033 -- never touch APs that are not listed in the backup
# ---------------------------------------------------------------------------


def test_revert_never_touches_aps_not_in_backup(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """Every ``updateSiteDevice`` call MUST target a ``device_id`` listed in ``aps_planned``.

    Why:
        FR-022 -- the revert MUST be contained to the backup's AP set even
        if the ambient org has grown new APs since the migration. This
        catches an implementation that accidentally iterates a live AP list
        instead of the backup's ``aps_reassigned`` list.
    """
    aps_planned = [
        _ap_record("d1", "site-1", "5c5b350e0001", "ap-1"),
        _ap_record("d2", "site-1", "5c5b350e0002", "ap-2"),
        _ap_record("d3", "site-2", "5c5b350e0003", "ap-3"),
    ]
    aps_reassigned = ["d1", "d2", "d3"]
    payload = _backup_fixture(aps_planned=aps_planned, aps_reassigned=aps_reassigned)
    backup_path = _write_backup(data_dir, payload)

    touched: list[str] = []

    def _ok_put(session: Any, site_id: str, device_id: str, body: Any) -> Any:
        """Record the device_id of every PUT and return a healthy 200."""
        del session, site_id, body  # WHY: signature-only params.
        touched.append(device_id)
        r = MagicMock()
        r.status_code = 200
        return r

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch.object(APProfileMigrationManager, "_verify_source_profile_exists", return_value=True, create=True),
        patch.object(APProfileMigrationManager, "_confirm_revert", return_value="live", create=True),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_ok_put),
        patch("time.sleep"),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit"),
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    planned_ids = {rec["device_id"] for rec in aps_planned}
    # WHY: subset assertion catches the failure mode this test is guarding
    # against -- any PUT outside the backup's id set fails the subset check.
    assert set(touched).issubset(planned_ids), f"PUT touched an AP outside the backup: touched={touched!r}"


# ---------------------------------------------------------------------------
# T034 -- one JSONL audit line via TelemetryEmitter, matches data-model 2.2
# ---------------------------------------------------------------------------


def test_revert_appends_jsonl_audit_line_via_telemetry_emitter(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """A successful revert MUST emit exactly one audit event matching data-model 2.2.

    Why:
        FR-025 requires the JSONL audit trail so downstream tooling can
        report on every revert without scraping the terminal. Locks the exact
        field set and the sentinel ``event_type``.
    """
    payload = _backup_fixture()
    backup_path = _write_backup(data_dir, payload)

    def _ok_put(session: Any, site_id: str, device_id: str, body: Any) -> Any:
        """Return a healthy 200 for every PUT."""
        del session, site_id, device_id, body  # WHY: signature-only params.
        r = MagicMock()
        r.status_code = 200
        return r

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch.object(APProfileMigrationManager, "_verify_source_profile_exists", return_value=True, create=True),
        patch.object(APProfileMigrationManager, "_confirm_revert", return_value="live", create=True),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_ok_put),
        patch("time.sleep"),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit") as mock_emit,
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    mock_emit.assert_called_once()
    event = mock_emit.call_args.args[0]
    # WHY: pin every field per data-model 2.2 so a silent drop of one field
    # breaks the audit consumer and is caught here first.
    required_keys = {
        "event_type",
        "timestamp_utc",
        "org_id",
        "backup_file_path",
        "source_profile_id",
        "planned_count",
        "reverted_count",
        "missing_count",
        "failed_count",
        "outcome",
    }
    assert required_keys.issubset(
        event.keys()
    ), f"Audit event MUST include every data-model 2.2 field; missing: {required_keys - set(event.keys())!r}"
    assert event["event_type"] == "ap_profile_migration_revert"
    assert event["outcome"] == "success"
    assert event["source_profile_id"] == payload["source_profile_id"]
    assert event["planned_count"] == len(payload["aps_planned"])
    assert event["reverted_count"] == len(payload["aps_reassigned"])


# ---------------------------------------------------------------------------
# T035 -- US2 end-to-end integration with mocked mistapi session
# ---------------------------------------------------------------------------


def test_us2_end_to_end_with_mocked_mistapi_session(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Full US2 flow: produced backup drives revert, all PUTs succeed, one audit row lands.

    Why:
        Ties every US2 helper together and locks the operator-visible
        contract: every listed AP is PUT with ``deviceprofile_id == source_id``,
        one audit row records ``outcome == "success"``, and the summary print
        names the backup path (quickstart Scenario 3).
    """
    aps_planned = [
        _ap_record("d1", "site-1", "5c5b350e0001", "ap-1"),
        _ap_record("d2", "site-1", "5c5b350e0002", "ap-2"),
        _ap_record("d3", "site-2", "5c5b350e0003", "ap-3"),
    ]
    aps_reassigned = ["d1", "d2", "d3"]
    payload = _backup_fixture(aps_planned=aps_planned, aps_reassigned=aps_reassigned)
    backup_path = _write_backup(data_dir, payload)
    src_id = payload["source_profile_id"]

    put_log: list[tuple[str, Any]] = []

    def _ok_put(session: Any, site_id: str, device_id: str, body: Any) -> Any:
        """Record (device_id, body) and return a healthy 200."""
        del session, site_id  # WHY: signature-only params.
        put_log.append((device_id, body))
        r = MagicMock()
        r.status_code = 200
        return r

    # WHY: stub safe_input directly for REVERT so the confirm helper -- which
    # may still delegate to the real safe_input -- returns "live".
    fake_mh.InputUtils.safe_input.return_value = "REVERT"

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch.object(APProfileMigrationManager, "_verify_source_profile_exists", return_value=True, create=True),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_ok_put),
        patch("time.sleep"),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit") as mock_emit,
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    # WHY: every AP MUST be PUT back to the source profile, in order.
    assert [dev for (dev, _body) in put_log] == ["d1", "d2", "d3"]
    for _dev, body in put_log:
        # WHY: every revert PUT MUST target the recorded source profile id.
        assert body == {"deviceprofile_id": src_id}, f"Wrong body={body!r}; want source_id={src_id!r}"

    mock_emit.assert_called_once()
    event = mock_emit.call_args.args[0]
    assert event["outcome"] == "success"
    assert event["reverted_count"] == 3
    assert event["missing_count"] == 0
    assert event["failed_count"] == 0

    out = capsys.readouterr().out
    # WHY: summary MUST name the backup path so the operator has a
    # copy-pasteable pointer to the audit source.
    assert str(backup_path) in out or backup_path.name in out, f"Summary MUST name the backup file; got: {out!r}"


# ---------------------------------------------------------------------------
# T046-T048 -- US3 dry-run tests
# ---------------------------------------------------------------------------


def test_migrate_dry_run_writes_no_file_and_issues_no_put(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DRY-RUN at the confirmation prompt MUST issue zero PUTs and write no file.

    Why:
        Locks FR-015 and SC-005 (Acceptance Scenario 1): the operator can
        preview a migration and see the exact AP list without any side
        effect. The printed line ``Dry run: no changes made`` is the
        operator-visible contract that no changes occurred.
    """
    # WHY: two Mist device profiles with different UUIDs so the source/target
    # equality guard does not short-circuit the flow before confirmation.
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "Data-Transfer-Profile", _profile(src_id, "Data-Transfer-Profile"))
    tgt = (tgt_id, "Main-Profile", _profile(tgt_id, "Main-Profile"))
    aps = [
        _ap_record("d1", "site-1", "5c5b350e0001", "ap-1"),
        _ap_record("d2", "site-1", "5c5b350e0002", "ap-2"),
    ]

    # WHY: safe_input returns DRY-RUN at the confirmation prompt so
    # _confirm_migration returns "dry_run" and the entry point takes the
    # preview short-circuit branch (FR-015).
    fake_mh.InputUtils.safe_input.return_value = "DRY-RUN"

    put_calls: list[Any] = []

    def _record_put(session: Any, site_id: str, device_id: str, body: Any) -> Any:
        """Record any PUT so the assertion below can prove none were made."""
        put_calls.append((site_id, device_id, body))
        r = MagicMock()
        r.status_code = 200
        return r

    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_record_put),
        patch("time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: FR-015 -- dry-run MUST issue zero PUTs.
    assert put_calls == [], f"Dry run MUST issue zero PUTs; got {put_calls!r}"

    # WHY: FR-015 -- dry-run MUST write no backup file.
    files = list(data_dir.glob("ap-profile-migration_*.json"))
    assert files == [], f"Dry run MUST write no backup file; got {files!r}"

    out = capsys.readouterr().out
    # WHY: STE-compliant operator-visible marker line -- proves the branch
    # was taken and the summary was suppressed.
    assert "Dry run: no changes made" in out, f"Missing dry-run marker in output: {out!r}"


def test_migrate_dry_run_ap_list_matches_live_run_plan(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pre-confirmation AP list block MUST be byte-identical between dry-run and live.

    Why:
        SC-005 -- the operator MUST see the same plan block whether they
        intend to preview or to apply, so a dry-run screenshot proves the
        upcoming live run is safe. Any drift between the two branches
        would defeat the whole point of the dry-run affordance.
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "Data-Transfer-Profile", _profile(src_id, "Data-Transfer-Profile"))
    tgt = (tgt_id, "Main-Profile", _profile(tgt_id, "Main-Profile"))
    aps = [
        _ap_record("d1", "site-1", "5c5b350e0001", "ap-1"),
        _ap_record("d2", "site-1", "5c5b350e0002", "ap-2"),
        _ap_record("d3", "site-2", "5c5b350e0003", "ap-3"),
        _ap_record("d4", "site-2", "5c5b350e0004", None),
        _ap_record("d5", "site-2", "5c5b350e0005", "ap-5"),
    ]

    def _extract_plan_block(out: str) -> str:
        """Return the plan block from stdout, up to the confirmation marker.

        Why:
            The plan block is everything from ``Planned migration:`` up to
            (but not including) ``Dry run:`` or the summary lines. Slicing
            here keeps the byte-compare focused on the plan itself and
            avoids capturing branch-specific summary text.
        """
        start = out.find("Planned migration:")
        assert start != -1, f"Missing 'Planned migration:' marker in: {out!r}"
        tail = out[start:]
        # WHY: cut at the first branch-specific marker so we compare only
        # the plan block itself, not the summary line the branches emit.
        # The live run appends "\nMigration summary:" after the plan; the
        # dry-run branch appends "Dry run: no changes made" instead.
        for marker in ("Dry run: no changes made", "\nMigration summary:"):
            idx = tail.find(marker)
            if idx != -1:
                return tail[:idx]
        return tail

    def _ok_put(session: Any, site_id: str, device_id: str, body: Any) -> Any:
        r = MagicMock()
        r.status_code = 200
        return r

    # --- Dry-run pass --------------------------------------------------------
    fake_mh.InputUtils.safe_input.return_value = "DRY-RUN"
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_ok_put),
        patch("time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())
    dry_out = capsys.readouterr().out
    dry_plan = _extract_plan_block(dry_out)

    # --- Live pass -----------------------------------------------------------
    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_ok_put),
        patch("time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())
    live_out = capsys.readouterr().out
    live_plan = _extract_plan_block(live_out)

    # WHY: byte-identical plan block -- SC-005 forbids any drift between
    # preview and apply for the pre-confirmation AP list.
    assert dry_plan == live_plan, f"Plan blocks diverge:\nDRY:\n{dry_plan!r}\nLIVE:\n{live_plan!r}"


def test_us3_end_to_end_dry_run_with_mocked_mistapi_session(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Full US3 flow: DRY-RUN across 2 sites and 3 APs writes nothing and PUTs nothing.

    Why:
        Quickstart Scenario 2 -- the integration-style test that pins the
        full public entry point against a fully mocked mistapi session.
        Guards the destructive-safety promise that the preview branch is
        genuinely inert on both the file system and the API.
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "Data-Transfer-Profile", _profile(src_id, "Data-Transfer-Profile"))
    tgt = (tgt_id, "Main-Profile", _profile(tgt_id, "Main-Profile"))
    aps = [
        _ap_record("d1", "site-1", "5c5b350e0001", "ap-1"),
        _ap_record("d2", "site-1", "5c5b350e0002", "ap-2"),
        _ap_record("d3", "site-2", "5c5b350e0003", "ap-3"),
    ]

    fake_mh.InputUtils.safe_input.return_value = "DRY-RUN"

    put_calls: list[Any] = []

    def _record_put(session: Any, site_id: str, device_id: str, body: Any) -> Any:
        put_calls.append((site_id, device_id, body))
        r = MagicMock()
        r.status_code = 200
        return r

    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("mistapi.api.v1.sites.devices.updateSiteDevice", side_effect=_record_put),
        patch("time.sleep"),
    ):
        # WHY: the entry point MUST return cleanly with no raised exception.
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: quickstart Scenario 2 -- zero PUTs and zero files under data/.
    assert put_calls == [], f"US3 end-to-end dry run MUST issue zero PUTs; got {put_calls!r}"
    assert list(data_dir.glob("ap-profile-migration_*.json")) == []

    out = capsys.readouterr().out
    assert "Dry run: no changes made" in out


# ---------------------------------------------------------------------------
# Rate-limiting addendum (specs/1029-ap-profile-migration/spec-addendum-rate-limiting.md)
# TR006-TR018: pacing behavior for menus 207 and 208
# ---------------------------------------------------------------------------


class _CacheTracker(dict):
    """A dict that counts assignments of ``initialized`` to ``False``.

    Why:
        The rate-limiting addendum feeds 429 responses to the PID limiter
        by setting ``_api_usage_cache["initialized"] = False``. Tests need
        to count how often that assignment fires without instrumenting
        the production module; a dict subclass captures it at the point
        of mutation.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize an empty tracker and set toggle_count to zero.

        Why:
            The parent ``dict`` __init__ handles keyword population; the
            override only adds the counter attribute.

        Args:
            *args: Forwarded to ``dict.__init__``.
            **kwargs: Forwarded to ``dict.__init__``.
        """
        super().__init__(*args, **kwargs)
        self.toggle_count = 0

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set ``key`` to ``value`` and count 429 signals.

        Why:
            The production 429 feedback path sets ``initialized`` to
            ``False`` exactly once per observed 429. Tests count those
            assignments to verify the throttle signal fired.

        Args:
            key: Dict key being assigned.
            value: New value for the key.
        """
        # WHY: only the False assignment on the "initialized" key counts as a
        # throttle signal; other writes to the cache are ignored.
        if key == "initialized" and value is False:
            self.toggle_count += 1
        super().__setitem__(key, value)


def _make_http_exception(status_code: int) -> Exception:
    """Build a mistapi-style exception carrying an HTTP status code.

    Why:
        The addendum's ``_is_429`` reads ``err.response.status_code``
        verbatim from ``api_data_fetcher._is_rate_limit_error``. Every
        pacing test that injects a 4xx/5xx PUT response uses this factory
        so the exception shape matches the detector exactly.

    Args:
        status_code: HTTP status code to attach to ``.response``.

    Returns:
        A plain ``Exception`` with a ``response`` attribute whose
        ``status_code`` matches the requested code.
    """
    exc = Exception(f"HTTP {status_code}")
    # WHY: SimpleNamespace mirrors the ``requests.Response`` shape that
    # mistapi exposes; the detector reads only ``.status_code``.
    exc.response = types.SimpleNamespace(status_code=status_code)  # type: ignore[attr-defined]
    return exc


def _seed_rate_limiter(fake_mh: types.ModuleType, delay: float = 0.0) -> MagicMock:
    """Install ``RateLimitingUtils`` and ``_api_usage_cache`` on ``fake_mh``.

    Why:
        Every pacing test extends the base ``fake_mh`` with two attributes
        that the manager's ``_apply_pacing`` and ``_signal_rate_limit_hit``
        helpers reach through the lazy ``import MistHelper as _mh`` idiom.
        Centralizing the extension keeps each test compact and consistent
        with the seams recorded in the addendum plan.

    Args:
        fake_mh: The synthetic MistHelper module produced by the fixture.
        delay: Fixed delay value the mocked limiter returns for every call.

    Returns:
        The mocked ``get_rate_limited_delay`` callable so a caller can
        override ``side_effect`` for exception injection (TR010).
    """
    fake_mh.RateLimitingUtils = MagicMock()
    fake_mh.RateLimitingUtils.get_rate_limited_delay.return_value = (None, delay)
    # WHY: use the tracker dict so the test can count 429 signals fed to the
    # limiter (assignment of "initialized" to False is the documented signal).
    fake_mh._api_usage_cache = _CacheTracker(
        initialized=True,
        used=0,
        limit=5000,
        last_updated=time.time(),
    )
    return fake_mh.RateLimitingUtils.get_rate_limited_delay


# ---------------------------------------------------------------------------
# TR006 -- pacing invoked exactly once per AP, before every PUT (US1)
# ---------------------------------------------------------------------------


def test_migrate_calls_get_rate_limited_delay_once_per_ap(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """Pacing MUST be invoked exactly once per planned AP, before every PUT.

    Why:
        FR-A01 -- the migrate loop consults the rate limiter before every
        PUT so a 10K-AP run self-throttles. This test locks the call
        count and the pacing-before-PUT order against the loop shape.
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "Data-Transfer-Profile", _profile(src_id, "Data-Transfer-Profile"))
    tgt = (tgt_id, "Main-Profile", _profile(tgt_id, "Main-Profile"))
    aps = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(20)]

    get_delay_mock = _seed_rate_limiter(fake_mh)
    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"

    call_order: list[str] = []

    def _track_delay(*args: Any, **kwargs: Any) -> Any:
        """Record a pacing entry and return zero delay."""
        del args, kwargs  # WHY: signature-only.
        call_order.append("pacing")
        return (None, 0.0)

    def _track_reassign(*args: Any, **kwargs: Any) -> None:
        """Record a PUT entry keyed by device id."""
        # WHY: signature-tolerant -- caller may pass positional or keyword.
        rec = args[1] if len(args) >= 2 else kwargs.get("rec")
        call_order.append("put:{}".format(rec["device_id"]))

    get_delay_mock.side_effect = _track_delay

    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch.object(APProfileMigrationManager, "_reassign_one_ap", side_effect=_track_reassign),
        patch("src.device.ap_profile_migration_manager.time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: FR-A01 -- exactly one pacing consult per planned AP.
    assert get_delay_mock.call_count == 20, f"expected 20 pacing calls, got {get_delay_mock.call_count}"
    # WHY: pacing precedes each PUT, so the recorded sequence alternates
    # pacing, put, pacing, put, ... for 20 iterations.
    assert len(call_order) == 40, f"expected 40 alternating entries, got {len(call_order)}: {call_order[:6]!r}"
    for i in range(20):
        assert call_order[i * 2] == "pacing", f"position {i * 2} expected pacing, got {call_order[i * 2]!r}"
        assert call_order[i * 2 + 1].startswith("put:"), (
            f"position {i * 2 + 1} expected put, got {call_order[i * 2 + 1]!r}"
        )


# ---------------------------------------------------------------------------
# TR007 -- 429 invalidates the api_usage_cache and never trips stop-on-failure (US1)
# ---------------------------------------------------------------------------


def test_migrate_429_invalidates_api_usage_cache(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """A 429 response MUST invalidate the cache; the loop MUST NOT halt.

    Why:
        FR-A03 and FR-A04 -- 429 is a throttle signal, not stop-on-failure.
        The manager feeds the signal to the PID limiter by invalidating
        the shared cache; the next iteration re-reads live usage from
        Mist and grows the delay.
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "src-name", _profile(src_id, "src-name"))
    tgt = (tgt_id, "tgt-name", _profile(tgt_id, "tgt-name"))
    aps = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(10)]

    _seed_rate_limiter(fake_mh)
    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"

    call_counter = {"n": 0}

    def _reassign_maybe_429(*args: Any, **kwargs: Any) -> None:
        """Raise 429 on the 3rd and 7th outer iteration; else succeed."""
        del args, kwargs  # WHY: signature-only.
        call_counter["n"] += 1
        if call_counter["n"] in (3, 7):
            raise _make_http_exception(429)

    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch.object(APProfileMigrationManager, "_reassign_one_ap", side_effect=_reassign_maybe_429),
        patch("src.device.ap_profile_migration_manager.time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    cache = fake_mh._api_usage_cache
    # WHY: FR-A03 -- 429 signals fire the cache-invalidation path.
    assert cache.toggle_count >= 2, f"expected >=2 cache invalidations for 2 429s, got {cache.toggle_count}"
    # WHY: FR-A04 -- 429 MUST NOT trigger stop-on-failure. The loop reached
    # the final AP; verify by checking all 10 outer iterations happened.
    assert call_counter["n"] == 10, f"expected loop to reach AP 10, got {call_counter['n']}"


# ---------------------------------------------------------------------------
# TR008 -- hermetic 100-AP run finishes in well under half a second (US1)
# ---------------------------------------------------------------------------


def test_migrate_hermetic_no_wall_clock_sleep(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """A 100-AP run MUST NOT sleep on wall clock; total pacing sum > 0.

    Why:
        FR-A07 -- pacing calls ``time.sleep`` by module-level reference so
        tests can patch it and complete in milliseconds. Regressions that
        switch to a non-patchable idiom would slow CI by seconds per file.
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "src-name", _profile(src_id, "src-name"))
    tgt = (tgt_id, "tgt-name", _profile(tgt_id, "tgt-name"))
    aps = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(100)]

    _seed_rate_limiter(fake_mh, delay=0.25)
    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"

    sleep_args: list[float] = []

    def _record_sleep(secs: float) -> None:
        """Record every pacing sleep argument so the test can sum them."""
        sleep_args.append(secs)

    start = time.perf_counter()
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch.object(APProfileMigrationManager, "_reassign_one_ap", return_value=None),
        patch("src.device.ap_profile_migration_manager.time.sleep", side_effect=_record_sleep),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())
    elapsed = time.perf_counter() - start

    # WHY: FR-A07 hermetic gate -- 100 APs run in well under half a second.
    assert elapsed < 0.5, f"hermetic run exceeded 0.5 s wall clock: {elapsed:.3f} s"
    # WHY: pacing was actually invoked (not silently skipped).
    assert sum(sleep_args) > 0.0, "sleep sum is zero; pacing did not fire"
    assert len(sleep_args) >= 100, f"expected >=100 sleep calls, got {len(sleep_args)}"


# ---------------------------------------------------------------------------
# TR009 -- HTTP 500 still halts stop-on-failure and never toggles cache (US1)
# ---------------------------------------------------------------------------


def test_migrate_non_429_still_halts_stop_on_failure(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """A 500 response MUST halt the loop and MUST NOT toggle the cache.

    Why:
        FR-A04 preserves the parent's stop-on-failure semantics for
        non-429 failures. This test locks the boundary: 500 halts,
        the cache is unchanged (500 is not routed through throttle feedback).
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "src-name", _profile(src_id, "src-name"))
    tgt = (tgt_id, "tgt-name", _profile(tgt_id, "tgt-name"))
    aps = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(50)]

    _seed_rate_limiter(fake_mh)
    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"

    call_counter = {"n": 0}

    def _reassign_500_on_42(*args: Any, **kwargs: Any) -> None:
        """Raise 500 on the 42nd outer iteration; else succeed."""
        del args, kwargs
        call_counter["n"] += 1
        if call_counter["n"] == 42:
            raise _make_http_exception(500)

    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch.object(APProfileMigrationManager, "_reassign_one_ap", side_effect=_reassign_500_on_42),
        patch("src.device.ap_profile_migration_manager.time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: FR-A04 -- loop halted at AP 42; the 43rd was never called.
    assert call_counter["n"] == 42, f"expected halt at 42, got {call_counter['n']} calls"
    # WHY: 500 MUST NOT invalidate the cache; that path is 429-only.
    cache = fake_mh._api_usage_cache
    assert cache.toggle_count == 0, "cache was invalidated on a non-429 failure"
    # WHY: the backup file records outcome partial per parent FR-017.
    files = list(data_dir.glob("ap-profile-migration_*.json"))
    assert len(files) == 1, f"expected exactly one backup file, got {len(files)}"
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["outcome"] == "partial"


# ---------------------------------------------------------------------------
# TR010 -- limiter exception falls back to 0.75 s and the loop continues (US1)
# ---------------------------------------------------------------------------


def test_migrate_limiter_exception_falls_back_and_continues(
    fake_mh: types.ModuleType,
    data_dir: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A limiter fault MUST NOT halt the loop; the pacing MUST fall back to 0.75 s.

    Why:
        FR-A06 -- the limiter is a diagnostic path, not a critical path.
        A ``RuntimeError`` from the PID math must be logged as a warning
        and swallowed with a fixed 0.75 s fallback so a 10K-AP run does
        not halt on a limiter regression.
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "src-name", _profile(src_id, "src-name"))
    tgt = (tgt_id, "tgt-name", _profile(tgt_id, "tgt-name"))
    aps = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(10)]

    get_delay_mock = _seed_rate_limiter(fake_mh)
    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"

    call_counter = {"n": 0}

    def _delay_or_raise(*args: Any, **kwargs: Any) -> Any:
        """Raise on the 5th consult; return a small delay otherwise."""
        del args, kwargs
        call_counter["n"] += 1
        if call_counter["n"] == 5:
            raise RuntimeError("PID corrupt")
        return (None, 0.1)

    get_delay_mock.side_effect = _delay_or_raise

    sleep_args: list[float] = []

    def _record_sleep(secs: float) -> None:
        """Record every pacing sleep argument so the test can inspect them."""
        sleep_args.append(secs)

    caplog.set_level(logging.WARNING, logger=_LOGGER_NAME)
    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch.object(APProfileMigrationManager, "_reassign_one_ap", return_value=None),
        patch("src.device.ap_profile_migration_manager.time.sleep", side_effect=_record_sleep),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: FR-A06 -- at least one WARNING names the 0.75 s fallback delay.
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING and "0.75" in r.getMessage()]
    assert len(warnings) >= 1, "expected a WARNING naming the 0.75 s fallback; got %r" % [
        r.getMessage() for r in caplog.records
    ]
    # WHY: the 5th pacing sleep argument equals the fallback constant.
    assert sleep_args[4] == pytest.approx(0.75), f"5th sleep arg expected 0.75, got {sleep_args[4]!r}"
    # WHY: the run completed all 10 APs (limiter fault MUST NOT halt).
    assert get_delay_mock.call_count == 10, f"expected 10 limiter consults, got {get_delay_mock.call_count}"


# ---------------------------------------------------------------------------
# TR011 -- revert pacing invoked exactly once per AP (US2)
# ---------------------------------------------------------------------------


def test_revert_calls_get_rate_limited_delay_once_per_ap(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """The revert loop MUST consult the limiter exactly once per AP.

    Why:
        FR-A02 -- parity with US1. The revert loop is equally exposed
        to a 10K-AP run and needs the same pacing discipline.
    """
    aps_planned = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(20)]
    aps_reassigned = [rec["device_id"] for rec in aps_planned]
    payload = _backup_fixture(aps_planned=aps_planned, aps_reassigned=aps_reassigned)
    backup_path = _write_backup(data_dir, payload)

    get_delay_mock = _seed_rate_limiter(fake_mh)
    fake_mh.InputUtils.safe_input.return_value = "REVERT"

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch.object(APProfileMigrationManager, "_verify_source_profile_exists", return_value=True, create=True),
        patch.object(APProfileMigrationManager, "_confirm_revert", return_value="live", create=True),
        patch.object(APProfileMigrationManager, "_revert_one_ap", return_value=None),
        patch("src.device.ap_profile_migration_manager.time.sleep"),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit"),
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    # WHY: FR-A02 -- one pacing call per revert AP.
    assert get_delay_mock.call_count == 20, f"expected 20 pacing calls, got {get_delay_mock.call_count}"


# ---------------------------------------------------------------------------
# TR012 -- revert 429 invalidates cache and audit line carries pacing (US2)
# ---------------------------------------------------------------------------


def test_revert_429_invalidates_api_usage_cache(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """A revert 429 MUST invalidate the cache and MUST NOT halt the loop.

    Why:
        FR-A02 and FR-A03 -- the revert loop feeds 429s to the PID limiter
        the same way US1 does, without escalating to stop-on-failure. The
        JSONL audit line records the count.
    """
    aps_planned = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(10)]
    aps_reassigned = [rec["device_id"] for rec in aps_planned]
    payload = _backup_fixture(aps_planned=aps_planned, aps_reassigned=aps_reassigned)
    backup_path = _write_backup(data_dir, payload)

    _seed_rate_limiter(fake_mh)
    fake_mh.InputUtils.safe_input.return_value = "REVERT"

    call_counter = {"n": 0}

    def _revert_maybe_429(*args: Any, **kwargs: Any) -> None:
        """Raise 429 on the 3rd and 7th revert; else succeed."""
        del args, kwargs
        call_counter["n"] += 1
        if call_counter["n"] in (3, 7):
            raise _make_http_exception(429)

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch.object(APProfileMigrationManager, "_verify_source_profile_exists", return_value=True, create=True),
        patch.object(APProfileMigrationManager, "_confirm_revert", return_value="live", create=True),
        patch.object(APProfileMigrationManager, "_revert_one_ap", side_effect=_revert_maybe_429),
        patch("src.device.ap_profile_migration_manager.time.sleep"),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit") as mock_emit,
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    cache = fake_mh._api_usage_cache
    # WHY: two 429s -> at least two cache invalidations.
    assert cache.toggle_count >= 2, f"expected >=2 cache invalidations, got {cache.toggle_count}"
    # WHY: loop reached all 10 APs (no halt).
    assert call_counter["n"] == 10, f"expected 10 revert calls, got {call_counter['n']}"
    # WHY: JSONL audit line carries pacing.http_429_seen == 2 per data-model 3.
    mock_emit.assert_called_once()
    event = mock_emit.call_args.args[0]
    assert "pacing" in event, f"audit event missing 'pacing' sub-dict; keys={sorted(event.keys())!r}"
    assert event["pacing"]["http_429_seen"] == 2, "expected pacing.http_429_seen==2, got {!r}".format(event["pacing"])


# ---------------------------------------------------------------------------
# TR013 -- revert hermetic 100-AP run under half a second (US2)
# ---------------------------------------------------------------------------


def test_revert_hermetic_no_wall_clock_sleep(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """A 100-AP revert MUST run in under 0.5 s wall clock.

    Why:
        FR-A07 parity for menu 208.
    """
    aps_planned = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(100)]
    aps_reassigned = [rec["device_id"] for rec in aps_planned]
    payload = _backup_fixture(aps_planned=aps_planned, aps_reassigned=aps_reassigned)
    backup_path = _write_backup(data_dir, payload)

    _seed_rate_limiter(fake_mh, delay=0.25)
    fake_mh.InputUtils.safe_input.return_value = "REVERT"

    sleep_args: list[float] = []

    def _record_sleep(secs: float) -> None:
        """Record every pacing sleep argument so the test can sum them."""
        sleep_args.append(secs)

    start = time.perf_counter()
    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch.object(APProfileMigrationManager, "_verify_source_profile_exists", return_value=True, create=True),
        patch.object(APProfileMigrationManager, "_confirm_revert", return_value="live", create=True),
        patch.object(APProfileMigrationManager, "_revert_one_ap", return_value=None),
        patch("src.device.ap_profile_migration_manager.time.sleep", side_effect=_record_sleep),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit"),
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())
    elapsed = time.perf_counter() - start

    assert elapsed < 0.5, f"hermetic revert exceeded 0.5 s wall clock: {elapsed:.3f} s"
    assert sum(sleep_args) > 0.0, "sleep sum is zero; pacing did not fire"
    assert len(sleep_args) >= 100, f"expected >=100 sleep calls, got {len(sleep_args)}"


# ---------------------------------------------------------------------------
# TR014 -- revert non-429 failure does NOT invalidate cache (US2)
# ---------------------------------------------------------------------------


def test_revert_non_429_error_does_not_toggle_cache(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """A 500 in the revert loop MUST NOT toggle the cache; the loop continues.

    Why:
        FR-A04 -- non-429 failures on the revert path are tolerated per
        parent FR-023 and MUST NOT be routed through throttle feedback.
    """
    aps_planned = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(10)]
    aps_reassigned = [rec["device_id"] for rec in aps_planned]
    payload = _backup_fixture(aps_planned=aps_planned, aps_reassigned=aps_reassigned)
    backup_path = _write_backup(data_dir, payload)

    _seed_rate_limiter(fake_mh)
    fake_mh.InputUtils.safe_input.return_value = "REVERT"

    call_counter = {"n": 0}

    def _revert_500_on_5(*args: Any, **kwargs: Any) -> None:
        """Raise 500 on the 5th revert; else succeed."""
        del args, kwargs
        call_counter["n"] += 1
        if call_counter["n"] == 5:
            raise _make_http_exception(500)

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch.object(APProfileMigrationManager, "_verify_source_profile_exists", return_value=True, create=True),
        patch.object(APProfileMigrationManager, "_confirm_revert", return_value="live", create=True),
        patch.object(APProfileMigrationManager, "_revert_one_ap", side_effect=_revert_500_on_5),
        patch("src.device.ap_profile_migration_manager.time.sleep"),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit"),
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    cache = fake_mh._api_usage_cache
    # WHY: 500 MUST NOT invalidate the cache; parent revert is tolerant but not throttled by 500.
    assert cache.toggle_count == 0, "cache was invalidated on a non-429 failure"
    # WHY: loop reached the end (parent FR-023 tolerance).
    assert call_counter["n"] == 10, f"expected 10 revert calls, got {call_counter['n']}"


# ---------------------------------------------------------------------------
# TR015 -- dry-run does not consult the rate limiter at all
# ---------------------------------------------------------------------------


def test_dry_run_does_not_consult_rate_limiter(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """Dry-run mode MUST NOT invoke the rate limiter at all.

    Why:
        FR-A08 -- dry-run issues zero PUTs; consulting the limiter would
        change the limiter's smoothed state and skew production runs.
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "src-name", _profile(src_id, "src-name"))
    tgt = (tgt_id, "tgt-name", _profile(tgt_id, "tgt-name"))
    aps = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(10)]

    get_delay_mock = _seed_rate_limiter(fake_mh)
    fake_mh.InputUtils.safe_input.return_value = "DRY-RUN"

    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch("src.device.ap_profile_migration_manager.time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: FR-A08 -- dry-run MUST NOT touch the limiter.
    assert get_delay_mock.call_count == 0, f"dry-run invoked the limiter {get_delay_mock.call_count} times"


# ---------------------------------------------------------------------------
# TR016 -- migrate summary carries the four pacing lines in the documented order
# ---------------------------------------------------------------------------


def test_summary_contains_pacing_lines(
    fake_mh: types.ModuleType,
    data_dir: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The migrate summary MUST print the four pacing lines in order.

    Why:
        FR-A09 and data-model-rate-limiting.md section 2 lock the
        operator-visible summary text so downstream tooling and human
        reviewers see a consistent block.
    """
    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "src-name", _profile(src_id, "src-name"))
    tgt = (tgt_id, "tgt-name", _profile(tgt_id, "tgt-name"))
    aps = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(5)]

    _seed_rate_limiter(fake_mh, delay=0.1)
    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"

    call_counter = {"n": 0}

    def _reassign_2_of_5_are_429(*args: Any, **kwargs: Any) -> None:
        """Raise 429 on the 2nd and 4th outer iteration; else succeed."""
        del args, kwargs
        call_counter["n"] += 1
        if call_counter["n"] in (2, 4):
            raise _make_http_exception(429)

    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch.object(APProfileMigrationManager, "_reassign_one_ap", side_effect=_reassign_2_of_5_are_429),
        patch("src.device.ap_profile_migration_manager.time.sleep"),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    out = capsys.readouterr().out
    # WHY: line prefix + integer -- puts_issued is per-iteration by TR024, so
    # the exact count depends on loop shape; format-only match is robust.
    assert "Total PUTs issued" in out, f"missing 'Total PUTs issued' line in:\n{out}"
    # WHY: exact substring for the 429 count (2 429s injected).
    assert "HTTP 429 responses seen  : 2" in out, f"missing 'HTTP 429 responses seen  : 2' in:\n{out}"
    # WHY: exact substring for the non-429 count (zero on this fixture).
    assert "Non-429 failures         : 0" in out, f"missing 'Non-429 failures         : 0' in:\n{out}"
    # WHY: mean and max floats to 3 dp per data-model section 2.
    assert "Rate limiter delay (s)   : mean=" in out, f"missing 'Rate limiter delay (s)' line in:\n{out}"
    assert "  max=" in out, f"missing 'max=' in delay line of:\n{out}"
    # WHY: order is Puts -> 429 -> Non429 -> Delay, per data-model section 2.
    idx_puts = out.index("Total PUTs issued")
    idx_429 = out.index("HTTP 429 responses seen")
    idx_non429 = out.index("Non-429 failures")
    idx_delay = out.index("Rate limiter delay (s)")
    assert idx_puts < idx_429 < idx_non429 < idx_delay, (
        f"summary lines out of order: puts={idx_puts}, 429={idx_429}, non429={idx_non429}, delay={idx_delay}"
    )


# ---------------------------------------------------------------------------
# TR017 -- JSONL audit line carries the pacing sub-dict per data-model section 3
# ---------------------------------------------------------------------------


def test_jsonl_audit_line_carries_pacing_subdict(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """The revert JSONL audit line MUST include the pacing sub-dict.

    Why:
        FR-A09 and data-model-rate-limiting.md section 3 lock the audit
        envelope. Downstream analytics consume the pacing sub-dict without
        a schema version bump because JSONL is additive.
    """
    aps_planned = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(5)]
    aps_reassigned = [rec["device_id"] for rec in aps_planned]
    payload = _backup_fixture(aps_planned=aps_planned, aps_reassigned=aps_reassigned)
    backup_path = _write_backup(data_dir, payload)

    _seed_rate_limiter(fake_mh, delay=0.1)
    fake_mh.InputUtils.safe_input.return_value = "REVERT"

    call_counter = {"n": 0}

    def _revert_2_of_5_are_429(*args: Any, **kwargs: Any) -> None:
        """Raise 429 on the 2nd and 4th revert; else succeed."""
        del args, kwargs
        call_counter["n"] += 1
        if call_counter["n"] in (2, 4):
            raise _make_http_exception(429)

    with (
        patch.object(APProfileMigrationManager, "_pick_backup_file", return_value=backup_path, create=True),
        patch.object(APProfileMigrationManager, "_verify_source_profile_exists", return_value=True, create=True),
        patch.object(APProfileMigrationManager, "_confirm_revert", return_value="live", create=True),
        patch.object(APProfileMigrationManager, "_revert_one_ap", side_effect=_revert_2_of_5_are_429),
        patch("src.device.ap_profile_migration_manager.time.sleep"),
        patch("src.analytics.telemetry_emitter.TelemetryEmitter.emit") as mock_emit,
    ):
        APProfileMigrationManager.revert_ap_profile_migration(session=MagicMock())

    mock_emit.assert_called_once()
    event = mock_emit.call_args.args[0]
    assert "pacing" in event, f"audit event missing pacing sub-dict; got keys: {sorted(event.keys())!r}"
    pacing = event["pacing"]
    # WHY: exactly five keys per data-model-rate-limiting.md section 3.
    expected_keys = {
        "puts_issued",
        "http_429_seen",
        "non_429_failures",
        "delay_seconds_mean",
        "delay_seconds_max",
    }
    assert set(pacing.keys()) == expected_keys, f"pacing key set mismatch: got {sorted(pacing.keys())!r}"
    assert pacing["http_429_seen"] == 2, f"expected pacing.http_429_seen==2, got {pacing['http_429_seen']!r}"
    assert pacing["non_429_failures"] == 0, (
        f"expected pacing.non_429_failures==0, got {pacing['non_429_failures']!r}"
    )
    # WHY: puts_issued is per-iteration (TR024); with 5 APs it is at least 5.
    assert isinstance(pacing["puts_issued"], int) and pacing["puts_issued"] >= 5
    assert isinstance(pacing["delay_seconds_mean"], float)
    assert isinstance(pacing["delay_seconds_max"], float)


# ---------------------------------------------------------------------------
# TR018 -- integration: real limiter engaged with a pre-seeded cache (US1)
# ---------------------------------------------------------------------------


def test_migrate_integration_real_limiter_seeded_cache(
    fake_mh: types.ModuleType,
    data_dir: Path,
) -> None:
    """Integration -- leave the real limiter engaged with a pre-seeded cache.

    Why:
        Research Q4 -- one integration-style test exercises the real
        ``RateLimitingUtils.get_rate_limited_delay`` math against a seeded
        cache so the addendum does not silently break the PID limiter's
        contract.
    """
    from src.utils.rate_limiting import RateLimitingUtils as _RealLimiter  # noqa: PLC0415

    # WHY: install the real limiter class (not a MagicMock) so the manager
    # exercises the PID math per research Q4.
    fake_mh.RateLimitingUtils = _RealLimiter
    # WHY: fresh last_updated so _needs_refresh returns False and the PID
    # math runs off the seeded values (no live API round-trip needed).
    fake_mh._api_usage_cache = _CacheTracker(
        initialized=True,
        used=4000,
        limit=5000,
        last_updated=time.time(),
    )

    src_id = "aaaa1111-2222-3333-4444-555566667777"
    tgt_id = "bbbb1111-2222-3333-4444-555566667777"
    src = (src_id, "src-name", _profile(src_id, "src-name"))
    tgt = (tgt_id, "tgt-name", _profile(tgt_id, "tgt-name"))
    aps = [_ap_record(f"d{i}", "site-1", f"5c5b350e{i:04x}") for i in range(50)]

    fake_mh.InputUtils.safe_input.return_value = "MIGRATE"

    sleep_args: list[float] = []

    def _record_sleep(secs: float) -> None:
        """Record every pacing sleep argument so the test can inspect them."""
        sleep_args.append(secs)

    with (
        patch.object(APProfileMigrationManager, "_pick_ap_device_profile", side_effect=[src, tgt]),
        patch.object(APProfileMigrationManager, "_discover_aps_on_source_profile", return_value=aps),
        patch.object(APProfileMigrationManager, "_reassign_one_ap", return_value=None),
        patch("src.device.ap_profile_migration_manager.time.sleep", side_effect=_record_sleep),
    ):
        APProfileMigrationManager.migrate_aps_between_device_profiles(session=MagicMock())

    # WHY: pacing was called 50 times (once per AP).
    assert len(sleep_args) == 50, f"expected 50 pacing sleeps, got {len(sleep_args)}"
    # WHY: real PID math produced a non-zero delay for at least one call
    # since the seeded cache reports 4000/5000 used (limiter should throttle).
    assert any(s > 0 for s in sleep_args), f"expected real limiter to produce a non-zero delay; got {sleep_args[:10]!r}"
