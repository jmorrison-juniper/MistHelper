"""Unit tests for ``build_body`` in ``src/firmware/upgrade_service.py``.

Why:
    The body is the exact JSON that the portal posts to the Mist cloud. The
    cloud reads four fields for a Junos device and three for a session smart
    router. An extra field is a silent contract break, because the cloud accepts
    the call and ignores the value, so the operator believes a setting took
    effect. These tests read the exact key set of the body for each shape.

    The file ``tests/unit/upgrade_portal/test_upgrade_service.py`` already
    proves the plain cases at its class ``TestBuildBody``. The tests below add
    the shapes that no test reads yet, and they add a table that names every
    key of every shape.
"""

from __future__ import annotations

import pytest

from src.firmware import upgrade_service
from src.firmware.upgrade_service import DeviceTarget, GatewayFamily, UpgradeOptions

MAC_SWITCH = "5c5b350e0001"
MAC_GATEWAY = "5c5b350e0002"
MAC_ACCESS_POINT = "5c5b350e0003"
SITE_ID = "11111111-1111-1111-1111-111111111111"

# The names that the cloud never reads on an upgrade body. A name below in a
# body means that the seam invented a field, and the cloud drops it in silence.
UNREAD_FIELD_NAMES = (
    "parallelism",
    "rules",
    "force",
    "enable_p2p",
    "phase",
    "targets",
    "upgrade_id",
    "reboot_in_progress",
    "site_id",
    "org_id",
    "name",
    "model",
    "macs",
    "device_type",
)


def make_target(
    mac: str = MAC_SWITCH,
    device_type: str = "switch",
    model: str = "EX4100-48P",
    version_target: str = "23.4R2-S3",
) -> DeviceTarget:
    """Return one device target for a body test.

    Why:
        Each test needs one target and changes one value. A helper keeps the
        test body short, so the reader sees the value under test.

    Args:
        mac: The device address with no separator.
        device_type: The Mist device type value.
        model: The device model text.
        version_target: The version that the operator wants.

    Returns:
        One device target.
    """
    return DeviceTarget(
        mac=mac,
        name=f"device-{mac[-4:]}",
        device_type=device_type,
        model=model,
        version_before="23.2R1",
        version_target=version_target,
        site_id=SITE_ID,
    )


# Each row names a family, a device type, the options, and the exact key set of
# the body. A key that the table omits must be absent from the body.
BODY_SHAPES: tuple[tuple[str, GatewayFamily, str, UpgradeOptions, frozenset[str]], ...] = (
    (
        "junos switch with the default options",
        GatewayFamily.JUNOS,
        "switch",
        UpgradeOptions(),
        frozenset({"device_ids", "version", "strategy", "reboot"}),
    ),
    (
        "junos gateway with the default options",
        GatewayFamily.JUNOS,
        "gateway",
        UpgradeOptions(),
        frozenset({"device_ids", "version", "strategy", "reboot"}),
    ),
    (
        "access point with the default options",
        GatewayFamily.JUNOS,
        "ap",
        UpgradeOptions(),
        frozenset({"device_ids", "version", "strategy"}),
    ),
    (
        "session smart router with a wanted reboot",
        GatewayFamily.SSR,
        "gateway",
        UpgradeOptions(),
        frozenset({"device_ids", "version", "strategy"}),
    ),
    (
        "session smart router with no reboot",
        GatewayFamily.SSR,
        "gateway",
        UpgradeOptions(reboot=False),
        frozenset({"device_ids", "version", "strategy", "reboot_at"}),
    ),
    (
        "junos switch with the file action",
        GatewayFamily.JUNOS,
        "switch",
        UpgradeOptions(junos_file_action=True),
        frozenset({"device_ids", "version", "strategy", "reboot", "snapshot"}),
    ),
    (
        "junos switch with the canary strategy",
        GatewayFamily.JUNOS,
        "switch",
        UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY),
        frozenset({"device_ids", "version", "strategy", "reboot", "canary_phases"}),
    ),
    (
        "access point with the canary strategy",
        GatewayFamily.JUNOS,
        "ap",
        UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY),
        frozenset({"device_ids", "version", "strategy", "canary_phases"}),
    ),
    (
        "junos switch with a start time",
        GatewayFamily.JUNOS,
        "switch",
        UpgradeOptions(start_time=1893456000),
        frozenset({"device_ids", "version", "strategy", "reboot", "start_time"}),
    ),
    (
        "session smart router with the canary strategy",
        GatewayFamily.SSR,
        "gateway",
        UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY),
        frozenset({"device_ids", "version"}),
    ),
    (
        "session smart router with the serial strategy",
        GatewayFamily.SSR,
        "gateway",
        UpgradeOptions(strategy=upgrade_service.STRATEGY_SERIAL),
        frozenset({"device_ids", "version", "strategy"}),
    ),
    (
        "session smart router with the file action",
        GatewayFamily.SSR,
        "gateway",
        UpgradeOptions(junos_file_action=True),
        frozenset({"device_ids", "version", "strategy"}),
    ),
    (
        "access point with the file action",
        GatewayFamily.JUNOS,
        "ap",
        UpgradeOptions(junos_file_action=True),
        frozenset({"device_ids", "version", "strategy"}),
    ),
)


class TestRebootRule:
    """Tests for rule one. The body sends a reboot field for a switch or a gateway only."""

    def test_sends_the_reboot_field_for_a_junos_gateway(self) -> None:
        """A Junos gateway reads the reboot field, so the body carries it."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SRX345")
        body = upgrade_service.build_body((target,), UpgradeOptions(), GatewayFamily.JUNOS)
        assert body["reboot"] is True

    def test_sends_a_false_reboot_field_for_a_junos_gateway(self) -> None:
        """The operator can hold the reboot of a Junos gateway, and the field says so."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SRX345")
        body = upgrade_service.build_body((target,), UpgradeOptions(reboot=False), GatewayFamily.JUNOS)
        assert body["reboot"] is False

    def test_sends_a_true_reboot_field_for_a_switch(self) -> None:
        """A switch reads the reboot field, and the default answer is a reboot."""
        body = upgrade_service.build_body((make_target(),), UpgradeOptions(), GatewayFamily.JUNOS)
        assert body["reboot"] is True

    def test_sends_no_reboot_field_for_a_session_smart_router_with_a_wanted_reboot(self) -> None:
        """The session smart router schema holds no reboot field and no reboot time field.

        The schema disables a reboot with a reboot time of minus one. A wanted
        reboot needs no field, so the body must carry neither name.
        """
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SSR120")
        body = upgrade_service.build_body((target,), UpgradeOptions(reboot=True), GatewayFamily.SSR)
        assert "reboot" not in body
        assert "reboot_at" not in body

    def test_sends_no_reboot_time_field_for_a_junos_device(self) -> None:
        """The reboot time field belongs to the session smart router schema alone."""
        body = upgrade_service.build_body((make_target(),), UpgradeOptions(reboot=False), GatewayFamily.JUNOS)
        assert "reboot_at" not in body


class TestJunosFileActionRule:
    """Tests for rule two. The body sends the Junos file action field for a Junos device only."""

    def test_sends_the_file_action_field_for_a_switch(self) -> None:
        """A switch accepts the Junos file action, so the body carries the field."""
        body = upgrade_service.build_body((make_target(),), UpgradeOptions(junos_file_action=True), GatewayFamily.JUNOS)
        assert body[upgrade_service._JUNOS_FILE_ACTION_KEY] is True

    def test_sends_no_file_action_field_when_the_operator_declined_it(self) -> None:
        """A declined file action sends no field, because the cloud reads a present field alone."""
        options = UpgradeOptions(junos_file_action=False)
        body = upgrade_service.build_body((make_target(),), options, GatewayFamily.JUNOS)
        assert upgrade_service._JUNOS_FILE_ACTION_KEY not in body

    def test_sends_no_file_action_field_for_a_session_smart_router(self) -> None:
        """The session smart router runs no Junos software, so it reads no Junos file action."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SSR120")
        body = upgrade_service.build_body((target,), UpgradeOptions(junos_file_action=True), GatewayFamily.SSR)
        assert upgrade_service._JUNOS_FILE_ACTION_KEY not in body

    def test_sends_no_file_action_field_for_an_access_point(self) -> None:
        """An access point runs no Junos software, so it reads no Junos file action."""
        target = make_target(mac=MAC_ACCESS_POINT, device_type="ap", model="AP45")
        body = upgrade_service.build_body((target,), UpgradeOptions(junos_file_action=True), GatewayFamily.JUNOS)
        assert upgrade_service._JUNOS_FILE_ACTION_KEY not in body


class TestCanaryPhaseRule:
    """Tests for rule three. The body sends a canary phase list whenever the strategy is canary."""

    def test_sends_the_phase_list_for_an_access_point(self) -> None:
        """An access point accepts the canary strategy, and the phase list travels with it."""
        target = make_target(mac=MAC_ACCESS_POINT, device_type="ap", model="AP45")
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY)
        body = upgrade_service.build_body((target,), options, GatewayFamily.JUNOS)
        assert body["canary_phases"] == list(upgrade_service._CANARY_PHASES)

    def test_sends_the_phase_list_for_a_junos_gateway(self) -> None:
        """A Junos gateway accepts the canary strategy, and the phase list travels with it."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SRX345")
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY)
        body = upgrade_service.build_body((target,), options, GatewayFamily.JUNOS)
        assert body["canary_phases"] == list(upgrade_service._CANARY_PHASES)

    def test_sends_no_phase_list_for_the_default_strategy(self) -> None:
        """The default strategy upgrades every device at once, so it needs no phase list."""
        body = upgrade_service.build_body((make_target(),), UpgradeOptions(), GatewayFamily.JUNOS)
        assert body["strategy"] == upgrade_service.STRATEGY_DEFAULT
        assert "canary_phases" not in body

    def test_sends_a_new_phase_list_object_for_each_call(self) -> None:
        """Two bodies hold two lists, so a change to one body changes no other body."""
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY)
        first = upgrade_service.build_body((make_target(),), options, GatewayFamily.JUNOS)
        second = upgrade_service.build_body((make_target(),), options, GatewayFamily.JUNOS)
        assert first["canary_phases"] == second["canary_phases"]
        assert first["canary_phases"] is not second["canary_phases"]

    def test_sends_no_phase_list_for_a_session_smart_router(self) -> None:
        """The session smart router schema offers no canary strategy, so it reads no phase list."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SSR120")
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY)
        body = upgrade_service.build_body((target,), options, GatewayFamily.SSR)
        assert "canary_phases" not in body

    def test_sends_no_strategy_word_to_a_session_smart_router_for_the_canary_strategy(self) -> None:
        """The body drops the strategy field, because that schema holds no canary strategy.

        The session smart router schema accepts the value ``big_bang`` and the
        value ``serial`` only. The body drops the phase list and the strategy
        word together, so the cloud reads no value that its schema omits. The
        module drops the word instead of a change to ``big_bang``, because a
        silent change would run a strategy that the operator never asked for.
        """
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SSR120")
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY)
        body = upgrade_service.build_body((target,), options, GatewayFamily.SSR)
        assert "strategy" not in body

    def test_sends_the_accepted_strategy_word_to_a_session_smart_router(self) -> None:
        """A word from the schema enumeration travels to a session smart router unchanged."""
        target = make_target(mac=MAC_GATEWAY, device_type="gateway", model="SSR120")
        for word in (upgrade_service.STRATEGY_DEFAULT, upgrade_service.STRATEGY_SERIAL):
            body = upgrade_service.build_body((target,), UpgradeOptions(strategy=word), GatewayFamily.SSR)
            assert body["strategy"] == word

    def test_sends_the_canary_word_to_a_junos_device(self) -> None:
        """The Junos path keeps the canary strategy, so the drop touches one family alone."""
        options = UpgradeOptions(strategy=upgrade_service.STRATEGY_CANARY)
        body = upgrade_service.build_body((make_target(),), options, GatewayFamily.JUNOS)
        assert body["strategy"] == upgrade_service.STRATEGY_CANARY


class TestNoUnreadFieldRule:
    """Tests for rule four. The body never carries a field that the cloud does not read."""

    @pytest.mark.parametrize(
        ("label", "family", "device_type", "options", "expected_keys"),
        BODY_SHAPES,
        ids=[row[0] for row in BODY_SHAPES],
    )
    def test_sends_the_exact_key_set_of_each_shape(
        self,
        label: str,
        family: GatewayFamily,
        device_type: str,
        options: UpgradeOptions,
        expected_keys: frozenset[str],
    ) -> None:
        """Each body shape holds an exact key set, with no extra key and no missing key.

        Args:
            label: The name of the shape, for the test report.
            family: The gateway family of the target.
            device_type: The Mist device type value.
            options: The operator options.
            expected_keys: Every key that the body must hold.
        """
        target = make_target(device_type=device_type)
        body = upgrade_service.build_body((target,), options, family)
        assert set(body) == set(expected_keys), label

    @pytest.mark.parametrize(
        ("label", "family", "device_type", "options", "expected_keys"),
        BODY_SHAPES,
        ids=[row[0] for row in BODY_SHAPES],
    )
    def test_sends_no_invented_field(
        self,
        label: str,
        family: GatewayFamily,
        device_type: str,
        options: UpgradeOptions,
        expected_keys: frozenset[str],
    ) -> None:
        """No body carries a name from the list of fields that the cloud drops.

        Args:
            label: The name of the shape, for the test report.
            family: The gateway family of the target.
            device_type: The Mist device type value.
            options: The operator options.
            expected_keys: Every key that the body must hold.
        """
        target = make_target(device_type=device_type)
        body = upgrade_service.build_body((target,), options, family)
        offenders = sorted(set(body) & set(UNREAD_FIELD_NAMES))
        assert offenders == [], f"{label} holds {offenders}"
        assert expected_keys.isdisjoint(UNREAD_FIELD_NAMES)

    def test_sends_no_start_time_field_when_the_operator_named_none(self) -> None:
        """A missing start time sends no field, because the cloud starts at once."""
        body = upgrade_service.build_body((make_target(),), UpgradeOptions(start_time=None), GatewayFamily.JUNOS)
        assert "start_time" not in body

    def test_sends_a_start_time_field_of_zero_when_the_operator_named_zero(self) -> None:
        """A start time of zero is a value, not a missing value, so the field travels."""
        body = upgrade_service.build_body((make_target(),), UpgradeOptions(start_time=0), GatewayFamily.JUNOS)
        assert body["start_time"] == 0


class TestBodyContent:
    """Tests for the three fields that every body carries."""

    def test_sends_one_device_identifier_for_each_target(self) -> None:
        """The device list holds one identifier for each target, in the order of the targets."""
        targets = (
            make_target(mac=MAC_SWITCH),
            make_target(mac=MAC_GATEWAY),
            make_target(mac=MAC_ACCESS_POINT),
        )
        body = upgrade_service.build_body(targets, UpgradeOptions(), GatewayFamily.JUNOS)
        device_ids = body["device_ids"]
        assert isinstance(device_ids, list)
        assert len(device_ids) == 3
        assert device_ids[0].endswith(MAC_SWITCH)
        assert device_ids[2].endswith(MAC_ACCESS_POINT)

    def test_reads_the_version_of_the_first_target(self) -> None:
        """One body carries one version field, so the first target sets the version.

        A caller must group the targets by version before the call. This test
        records the rule that makes that grouping necessary.
        """
        targets = (
            make_target(mac=MAC_SWITCH, version_target="23.4R2-S3"),
            make_target(mac=MAC_GATEWAY, version_target="21.4R3-S5"),
        )
        body = upgrade_service.build_body(targets, UpgradeOptions(), GatewayFamily.JUNOS)
        assert body["version"] == "23.4R2-S3"

    def test_reads_the_device_type_of_the_first_target(self) -> None:
        """The device type of the first target decides the reboot field.

        A caller must group the targets by device type before the call. A mixed
        group would send the fields of the first device type to every device.
        """
        targets = (
            make_target(mac=MAC_ACCESS_POINT, device_type="ap", model="AP45"),
            make_target(mac=MAC_SWITCH, device_type="switch"),
        )
        body = upgrade_service.build_body(targets, UpgradeOptions(), GatewayFamily.JUNOS)
        assert "reboot" not in body

    def test_raises_for_an_empty_target_list(self) -> None:
        """An empty target list is a caller error, so the function refuses the call."""
        with pytest.raises(ValueError, match="at least one target"):
            upgrade_service.build_body((), UpgradeOptions(), GatewayFamily.JUNOS)
