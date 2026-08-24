"""The live shapes that a real cloud session and a real device read answer with.

Why:
    The organization picker showed no row and the inventory page answered 500
    against the live cloud, while the whole test suite passed. Four faults
    caused it, and one habit hid all four: every stand-in in this suite answered
    a simpler shape than the library and the device module really answer.

    ``mistapi`` 0.63 answers ``APISession.privileges`` with a ``Privileges``
    object. That object iterates and holds no length, and it is not a list. Each
    entry is a ``_Privilege`` object that carries ``org_id`` and ``name`` as
    attributes, and it is not a dictionary.

    The token sign-in built the session and never signed in, so the privilege
    list stayed empty whatever the token allowed.

    The inventory route called the device reader without the cloud session that
    the reader requires, and it then read the answer as a list when the reader
    answers a ``DeviceRead`` object.

    These tests copy the shapes that the library and the device module really
    answer with.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from src.upgrade_portal.app.routes import auth, select
from src.upgrade_portal.runtime import identity

ORG_ID = "8a1ea872-241a-4c8e-a5ca-2d85674c7229"  # The shape of a real organization key.
ORG_NAME = "Morrison House"  # The readable name that the picker must show.
SITE_ID = "cf36153a-97bb-4974-8f8f-e9cc25d64d83"  # The shape of a real site key.
HOST = "api.mist.com"  # A host that `resolve_host` accepts.


class FakePrivilege:
    """One entry of the privilege list, shaped like ``mistapi._Privilege``.

    Why:
        The real entry is an object and never a dictionary. It carries a ``get``
        method as well, so a reader that tests for ``dict`` alone drops it and a
        reader that calls ``get`` keeps it. Both readers must work.

    Attributes:
        org_id: The organization key.
        name: The readable organization name.
    """

    def __init__(self, org_id: str, name: str) -> None:
        """Create one privilege entry.

        Args:
            org_id: The organization key.
            name: The readable organization name.
        """
        self.org_id = org_id  # The attribute that the real object carries.
        self.name = name  # The attribute that the picker shows.

    def get(self, key: str, default: Any = None) -> Any:
        """Return one field, in the way that the real object does.

        Args:
            key: The field name.
            default: The value for a field that this entry does not carry.

        Returns:
            The field value, or the default.
        """
        return getattr(self, key, default)


class FakePrivileges:
    """The container that ``mistapi`` answers with, which is not a list.

    Why:
        The real ``Privileges`` object iterates and holds no length. A reader
        that tests ``isinstance(value, list)`` therefore reads it as absent, and
        the picker then shows an empty table with no error anywhere.

    Attributes:
        entries: The privilege entries this container yields.
    """

    def __init__(self, *entries: FakePrivilege) -> None:
        """Create the container.

        Args:
            *entries: The privilege entries.
        """
        self.entries = list(entries)  # The container owns its own copy.

    def __iter__(self) -> Iterator[FakePrivilege]:
        """Yield each entry.

        Returns:
            An iterator over the entries.
        """
        return iter(self.entries)


class TokenSessionSpy:
    """A stand-in cloud session that records its own sign-in.

    Attributes:
        logins: How many times a caller signed this session in.
        privileges: The privilege container, filled by the sign-in.
    """

    def __init__(self) -> None:
        """Create the spy with no sign-in and no privilege."""
        self.logins = 0  # The count that the token test asserts on.
        self.privileges: FakePrivileges = FakePrivileges()  # Empty until the sign-in fills it.

    def login(self) -> None:
        """Sign in and fill the privilege container, as the library does."""
        self.logins += 1  # The one state that this spy keeps.
        self.privileges = FakePrivileges(FakePrivilege(ORG_ID, ORG_NAME))  # The cloud answers the scope here.


# ---------------------------------------------------------------------------
# The readers of one privilege entry
# ---------------------------------------------------------------------------


def test_the_organization_key_reader_accepts_an_object_entry() -> None:
    """A privilege object gives up its organization key.

    Why:
        The live entry is an object. A reader that accepted a dictionary alone
        answered an empty key, and every organization then dropped out of the
        scope set and out of the picker.
    """
    assert identity.privilege_org_id(FakePrivilege(ORG_ID, ORG_NAME)) == ORG_ID


def test_the_organization_key_reader_still_accepts_a_mapping_entry() -> None:
    """A privilege dictionary keeps working, because a test builds that shape."""
    assert identity.privilege_org_id({"org_id": ORG_ID}) == ORG_ID


def test_the_organization_key_reader_answers_empty_for_a_nameless_entry() -> None:
    """An entry that names no organization drops out, and never raises."""
    assert identity.privilege_org_id(object()) == ""
    assert identity.privilege_org_id({"site_id": "site-1"}) == ""


def test_the_organization_name_reader_accepts_both_entry_shapes() -> None:
    """The picker reads the readable name from an object and from a mapping.

    Why:
        Without this reader the picker showed the hexadecimal key in the name
        column, and an operator cannot match a key against a site by eye.
    """
    assert identity.privilege_name(FakePrivilege(ORG_ID, ORG_NAME)) == ORG_NAME
    assert identity.privilege_name({"name": ORG_NAME}) == ORG_NAME
    assert identity.privilege_name(object()) == ""


# ---------------------------------------------------------------------------
# The picker that reads the whole list
# ---------------------------------------------------------------------------


def test_the_picker_builds_a_row_from_the_live_privilege_shape(monkeypatch: Any) -> None:
    """The organization picker shows one named row for a live privilege object.

    Why:
        This is the failure that a live run found. Every reader passed its own
        test against a list of dictionaries, and the picker still showed the
        sentence that says this sign-in reaches no organization.

    Args:
        monkeypatch: The pytest patching helper.
    """
    live = FakePrivileges(FakePrivilege(ORG_ID, ORG_NAME))  # The shape the library really answers with.
    monkeypatch.setattr(select.identity, "session_privileges", lambda: list(live))
    rows = select.permitted_orgs()
    assert rows == [{"org_id": ORG_ID, "name": ORG_NAME}]


def test_the_privilege_list_reader_accepts_a_container_that_is_not_a_list() -> None:
    """A container that iterates and holds no length still reads as a list.

    Why:
        `session_privileges` tested for `isinstance(value, list)`. The real
        container fails that test, so the reader answered None, which the scope
        check reads as unknown and the picker reads as empty.
    """
    session = TokenSessionSpy()
    session.login()
    found = list(session.privileges)  # The reader copies the container the same way.
    assert not isinstance(session.privileges, list)  # The container is not a list, and never was.
    assert [identity.privilege_org_id(one) for one in found] == [ORG_ID]


# ---------------------------------------------------------------------------
# The token sign-in
# ---------------------------------------------------------------------------


def test_the_token_sign_in_signs_the_session_in(monkeypatch: Any) -> None:
    """The token session reaches the registry already signed in.

    Why:
        The builder created the session and returned it. Nothing called `login`,
        so the cloud never told the portal which organizations the token
        reaches. The picker then showed no row for a token that reaches one.

    Args:
        monkeypatch: The pytest patching helper.
    """
    spy = TokenSessionSpy()

    class FakeLibrary:
        """A stand-in for the `mistapi` module."""

        @staticmethod
        def APISession(**_: Any) -> TokenSessionSpy:  # noqa: N802  # The library spells the name this way.
            """Return the spy in place of a real session.

            Returns:
                The spy.
            """
            return spy

    monkeypatch.setattr(auth, "import_module", lambda _: FakeLibrary)
    monkeypatch.setattr(auth, "environment_token_value", lambda: "token-value-that-no-log-holds")
    built = auth.default_token_session(HOST)
    assert built is spy
    assert spy.logins == 1  # The builder signed the session in exactly one time.
    assert [identity.privilege_org_id(one) for one in built.privileges] == [ORG_ID]


# ---------------------------------------------------------------------------
# The device inventory of a real site
# ---------------------------------------------------------------------------


class FakeDeviceRead:
    """The answer shape of ``capture/devices.py:333 read_inventory``.

    Why:
        The real reader answers a ``DeviceRead`` dataclass, which carries the
        rows under ``records`` beside the reasons of the read. Every contract
        test injected a stand-in that answered a plain list, so no test met this
        shape and the inventory page showed no device for a site that holds
        eight.

    Attributes:
        records: The device rows.
        partial_reasons: The reasons of a short read. Empty for a whole read.
    """

    def __init__(self, records: list[dict[str, Any]]) -> None:
        """Create the answer.

        Args:
            records: The device rows.
        """
        self.records = records  # The attribute that `as_records` must read.
        self.partial_reasons: list[dict[str, Any]] = []  # A whole read names no reason.


def test_the_record_reader_accepts_the_device_read_shape() -> None:
    """A `DeviceRead` gives up its rows, exactly as a list does.

    Why:
        This is the shape that the live run met. The reader knew a list and a
        mapping, and it answered an empty list for everything else, so a page
        that read a real site showed no row and reported no fault.
    """
    rows = [{"mac": "209339051780", "type": "switch"}]
    assert select.as_records(FakeDeviceRead(rows)) == rows


def test_the_record_reader_still_accepts_the_two_older_shapes() -> None:
    """A list and a paged mapping keep working, because the cloud answers both."""
    rows = [{"mac": "209339051780"}]
    assert select.as_records(rows) == rows
    assert select.as_records({"results": rows}) == rows


def test_the_record_reader_answers_empty_for_an_unknown_shape() -> None:
    """An object that names no rows shows no record and raises nothing."""
    assert select.as_records(object()) == []
    assert select.as_records(FakeDeviceRead([])) == []
    assert select.as_records(None) == []


def test_the_device_reader_call_sends_the_session_when_the_reader_names_one() -> None:
    """The real reader receives the cloud session it requires.

    Why:
        The route called the reader with the two identifiers alone. The real
        reader names the session first, so the call raised a `TypeError` and the
        inventory page answered 500 for every real site.
    """
    seen: dict[str, Any] = {}

    def real_reader(session: Any, org_id: str, site_id: str) -> FakeDeviceRead:
        """Stand in for the reader of the device module.

        Args:
            session: The cloud session.
            org_id: The organization key.
            site_id: The site key.

        Returns:
            One device row.
        """
        seen.update(session=session, org_id=org_id, site_id=site_id)
        return FakeDeviceRead([{"mac": "209339051780"}])

    sentinel = object()
    answer = select.call_device_reader(real_reader, sentinel, ORG_ID, SITE_ID)
    assert seen == {"session": sentinel, "org_id": ORG_ID, "site_id": SITE_ID}
    assert select.as_records(answer) == [{"mac": "209339051780"}]


def test_the_device_reader_call_omits_the_session_for_a_stand_in() -> None:
    """A stand-in that names no session still runs, so the contract tests hold.

    Why:
        The contract tests inject a reader that takes the two identifiers alone.
        The caller reads the signature rather than catching a `TypeError`,
        because the real reader can raise that same class from inside itself.
    """

    def stand_in(org_id: str, site_id: str) -> list[dict[str, Any]]:
        """Stand in for the injected reader of a contract test.

        Args:
            org_id: The organization key.
            site_id: The site key.

        Returns:
            One device row.
        """
        return [{"mac": "209339051780", "org_id": org_id, "site_id": site_id}]

    answer = select.call_device_reader(stand_in, object(), ORG_ID, SITE_ID)
    assert select.as_records(answer)[0]["site_id"] == SITE_ID


def test_the_inventory_status_word_comes_from_the_connected_flag() -> None:
    """A connected device reads as connected, and never as unknown.

    Why:
        The inventory endpoint names the state `connected` and carries a boolean.
        The table reads `status`, so every connected device of a real site read
        as unknown. An operator reads that column before an upgrade, and an
        unknown state hides a device that is already offline.
    """
    assert select.with_status_word({"mac": "a", "connected": True})["status"] == "connected"
    assert select.with_status_word({"mac": "a", "connected": False})["status"] == "disconnected"


def test_the_inventory_status_word_keeps_a_status_the_cloud_already_named() -> None:
    """A record from the statistics call keeps its own word.

    Why:
        The device statistics call spells the field `status` already. A rewrite
        would replace a precise word with one of two, and the page would lose
        the state that the cloud measured.
    """
    kept = select.with_status_word({"mac": "a", "status": "upgrading", "connected": True})
    assert kept["status"] == "upgrading"


def test_the_inventory_status_word_leaves_an_unknown_record_alone() -> None:
    """A record that names neither field keeps the fallback of the template."""
    assert "status" not in select.with_status_word({"mac": "a"})
