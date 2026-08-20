"""Unit tests for the environment settings of the upgrade capture portal.

Why:
    The portal factory takes no argument, so the process environment is the only
    source of a setting. A wrong default or a silent override changes the listen
    port, the browser poll rate, or the network guard. These tests hold every
    default to the literal value in ``src/upgrade_portal/app/config.py`` and
    prove that a bad override falls back instead of reaching the running portal.

    These tests also prove the credential rule of FR-009. The settings records
    carry the name of each password variable and never the password value. Every
    credential string below is an obvious sentinel, so no real credential can
    enter a test run or a log record. No test reads the ``.env`` file.
"""

from __future__ import annotations

import logging
from dataclasses import FrozenInstanceError, fields
from ipaddress import ip_network
from types import SimpleNamespace

import pytest

from src.upgrade_portal.app import config
from src.upgrade_portal.app.config import (
    ArangoSettings,
    PortalSettings,
    ProxySettings,
    RedisSettings,
    SettingsError,
    WebSettings,
    load_arango_settings,
    load_proxy_settings,
    load_redis_settings,
    load_settings,
    load_web_settings,
    read_allowed_networks,
    read_integer,
    read_network,
    read_poll_interval,
    read_port,
    read_post_check_mode,
    read_proxy_hops,
    read_secret_key,
    read_themes,
)

# WHY: Every variable the module reads. The clearing fixture walks this list, so
# a leftover shell variable cannot turn a default test into a false pass.
PORTAL_VARIABLES = (
    "CAPTURE_PORT",
    "CAPTURE_SECRET_KEY",
    "CAPTURE_THEMES",
    "CAPTURE_POLL_SECONDS",
    "CAPTURE_ALLOWED_IPS",
    "CAPTURE_PROXY_HOPS",
    "CAPTURE_POST_CHECK_MODE",
    "ARANGO_HOST",
    "ARANGO_DATABASE",
    "ARANGO_USERNAME",
    "ARANGO_ROOT_PASSWORD",
    "REDIS_HOST",
    "REDIS_USERNAME",
    "REDIS_PORT",
    "REDIS_PASSWORD",
)

# WHY: Obvious sentinels. A reader sees at once that these are not credentials,
# and a grep for either string finds only this file.
ARANGO_PASSWORD_SENTINEL = "sentinel-arango-password-never-a-real-secret"
REDIS_PASSWORD_SENTINEL = "sentinel-redis-password-never-a-real-secret"
SECRET_KEY_SENTINEL = "sentinel-session-key-never-a-real-secret"

# WHY: The two names the records must carry. The name is not a credential.
ARANGO_PASSWORD_NAME = "ARANGO_ROOT_PASSWORD"
REDIS_PASSWORD_NAME = "REDIS_PASSWORD"

# WHY: Values the port reader must refuse. Each entry covers one class of
# mistake: blank text, words, a decimal, a sign, a privileged port, and a port
# above the socket limit.
BAD_PORT_VALUES = (
    "",
    "   ",
    "not-a-port",
    "8056.0",
    "80.5",
    "0x1f",
    "eight thousand",
    "8056 9000",
    "-1",
    "-8056",
    "0",
    "80",
    "443",
    "1023",
    "65536",
    "99999",
    "4294967296",
)

# WHY: Values the poll reader must refuse. A wait under five seconds would flood
# the status endpoints, and text that is not a number carries no wait at all.
BAD_POLL_VALUES = ("", "  ", "thirty", "30.0", "4", "1", "0", "-1", "-30")


@pytest.fixture(autouse=True)
def _clear_portal_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every portal variable before one test runs.

    Why:
        A default test must read a default. The shell that starts pytest may
        already hold ``REDIS_HOST`` or ``ARANGO_HOST``, which would hide a wrong
        default. This fixture also guarantees that no test leaks a variable into
        the next test, so the suite passes in any order.

    Args:
        monkeypatch: The pytest patch helper. It restores each variable after
            the test ends.
    """
    for name in PORTAL_VARIABLES:
        monkeypatch.delenv(name, raising=False)  # WHY: The variable is often absent already.


class EnvironmentRecorder:
    """A stand-in for ``os.environ`` that records every key the module reads.

    Why:
        The module claims that it never reads a password value. A record of the
        keys proves that claim directly. An assertion on the returned settings
        alone could not tell a value that was read and dropped from a value that
        was never read.
    """

    def __init__(self, values: dict[str, str]) -> None:
        """Hold the environment values and start an empty read log.

        Args:
            values: The variables the fake environment holds.
        """
        self.values = values  # WHY: The answer for each key the module asks for.
        self.read_keys: list[str] = []  # WHY: The assertion walks this log.

    def get(self, key: str, default: str) -> str:
        """Return one value and record the key.

        Args:
            key: The variable name the module asks for.
            default: The answer when the fake environment holds no such key.

        Returns:
            The stored value, or the default.
        """
        self.read_keys.append(key)  # WHY: The read log is the whole point of this class.
        return self.values.get(key, default)


def collect_stored_text(settings: PortalSettings) -> list[str]:
    """Return the text of every field in every settings group.

    Why:
        The credential tests must search the whole settings tree, not one field.
        A future field would otherwise escape the search and could carry a
        password value without a failing test.

        The walk reads the group list from `PortalSettings` itself rather than
        naming each group, so a new group joins the credential search on the day
        it is added and no reader has to remember to update this helper.

    Args:
        settings: The settings record to walk.

    Returns:
        One string for each field value in every group.
    """
    stored: list[str] = []
    for group in fields(settings):  # WHY: The record names its own groups, so none can escape.
        record = getattr(settings, group.name)
        for field in fields(record):
            stored.append(str(getattr(record, field.name)))  # WHY: A tuple field needs the text form.
    return stored


def test_port_default_is_8056(monkeypatch: pytest.MonkeyPatch) -> None:
    """The listen port is 8056 when the operator sets nothing.

    Why:
        Port 8055 already serves the data browsing portal. A drift back to 8055
        would make the two portals fight for the same socket.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.delenv("CAPTURE_PORT", raising=False)  # WHY: The default path needs an absent variable.
    assert load_settings().web.port == 8056


def test_poll_interval_default_is_30_seconds() -> None:
    """The browser waits 30 seconds between two status calls.

    Why:
        The contract sets this rate. The portal polls instead of holding an open
        stream, because an open stream holds one request thread for each
        operator.
    """
    assert load_settings().web.poll_interval_seconds == 30


def test_themes_default_holds_the_two_shipped_stylesheets() -> None:
    """The theme list holds ``default`` and ``magenta`` in that order.

    Why:
        The page template builds the stylesheet link from a theme name. A name
        with no matching file would leave the page without a stylesheet.
    """
    assert load_settings().web.themes == ("default", "magenta")


def test_allow_list_default_is_empty() -> None:
    """The network allow list is empty when the operator sets nothing.

    Why:
        An empty list leaves the portal open, which matches the port 8055
        portal. The security layer registers no address hook for an empty list.
    """
    assert load_settings().web.allowed_networks == ()


def test_arango_defaults_name_the_container_service() -> None:
    """The primary store defaults point at the container service.

    Why:
        The portal runs beside ArangoDB in one container network. The service
        name works there without any operator setup.
    """
    arango = load_settings().arango
    assert arango.host == "http://arangodb:8529"
    assert arango.database == "misthelper"
    assert arango.username == "root"


def test_redis_defaults_name_the_container_service() -> None:
    """The lock store defaults point at the container service.

    Why:
        Redis holds the site lock. A wrong default host would let two operators
        drive one site at the same time.
    """
    redis = load_settings().redis
    assert redis.host == "redis-stack"
    assert redis.port == 6379


def test_module_constants_hold_the_documented_literals() -> None:
    """Each published constant equals the literal in the plan.

    Why:
        Other modules import these constants. A test against the literal catches
        a change that a test against the constant itself would miss.
    """
    assert config.DEFAULT_PORT == 8056
    assert config.DEFAULT_POLL_INTERVAL_SECONDS == 30
    assert config.DEFAULT_THEMES == ("default", "magenta")
    assert config.DEFAULT_ARANGO_HOST == "http://arangodb:8529"
    assert config.DEFAULT_ARANGO_DATABASE == "misthelper"
    assert config.DEFAULT_ARANGO_USERNAME == "root"
    assert config.DEFAULT_REDIS_HOST == "redis-stack"
    assert config.DEFAULT_REDIS_PORT == 6379
    assert config.LOWEST_ALLOWED_PORT == 1024
    assert config.HIGHEST_ALLOWED_PORT == 65535
    assert config.LOWEST_POLL_INTERVAL_SECONDS == 5
    assert config.SECRET_KEY_BYTES == 32


def test_variable_name_constants_hold_the_documented_names() -> None:
    """Each variable name constant equals the documented name.

    Why:
        The container file and the operator guide name these variables. A change
        to a constant would break an existing deployment without a warning.
    """
    assert config.PORT_VARIABLE == "CAPTURE_PORT"
    assert config.SECRET_KEY_VARIABLE == "CAPTURE_SECRET_KEY"
    assert config.THEMES_VARIABLE == "CAPTURE_THEMES"
    assert config.POLL_VARIABLE == "CAPTURE_POLL_SECONDS"
    assert config.ALLOWED_ADDRESSES_VARIABLE == "CAPTURE_ALLOWED_IPS"
    assert config.ARANGO_HOST_VARIABLE == "ARANGO_HOST"
    assert config.ARANGO_DATABASE_VARIABLE == "ARANGO_DATABASE"
    assert config.ARANGO_USERNAME_VARIABLE == "ARANGO_USERNAME"
    assert config.ARANGO_PASSWORD_VARIABLE == "ARANGO_ROOT_PASSWORD"
    assert config.REDIS_HOST_VARIABLE == "REDIS_HOST"
    assert config.REDIS_PORT_VARIABLE == "REDIS_PORT"
    assert config.REDIS_PASSWORD_VARIABLE == "REDIS_PASSWORD"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("9000", 9000),
        ("1024", 1024),
        ("65535", 65535),
        ("  9000  ", 9000),
        ("+9000", 9000),
        ("08056", 8056),
    ],
)
def test_capture_port_override_sets_the_listen_port(monkeypatch: pytest.MonkeyPatch, raw: str, expected: int) -> None:
    """A good ``CAPTURE_PORT`` value replaces the default.

    Why:
        An operator moves the portal when another service already holds 8056.
        The reader must accept the range edges and must ignore surrounding
        space, because a container file often adds a space after the equals
        sign.

    Args:
        monkeypatch: The pytest patch helper.
        raw: The text the operator puts in the variable.
        expected: The port the reader must return.
    """
    monkeypatch.setenv("CAPTURE_PORT", raw)
    assert load_settings().web.port == expected


@pytest.mark.parametrize("raw", BAD_PORT_VALUES)
def test_capture_port_falls_back_when_the_value_is_bad(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    """A bad ``CAPTURE_PORT`` value gives the default port 8056.

    Why:
        A typed mistake must not stop an operations tool. The portal reports the
        bad value and continues on the documented port.

    Args:
        monkeypatch: The pytest patch helper.
        raw: A value the reader must refuse.
    """
    monkeypatch.setenv("CAPTURE_PORT", raw)
    assert load_settings().web.port == 8056


@pytest.mark.parametrize("raw", BAD_PORT_VALUES)
def test_a_bad_capture_port_never_yields_a_nonsense_port(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    """A bad ``CAPTURE_PORT`` value never leaves the legal range.

    Why:
        A negative port, a zero port, or a port above 65535 would crash the
        socket bind at start. This test states the property once, so a new
        fallback path cannot return an impossible number.

    Args:
        monkeypatch: The pytest patch helper.
        raw: A value the reader must refuse.
    """
    monkeypatch.setenv("CAPTURE_PORT", raw)
    port = load_settings().web.port
    assert 1024 <= port <= 65535


def test_capture_port_unset_and_blank_give_the_same_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """An absent variable and a blank variable both give port 8056.

    Why:
        A container file that names the variable with no value must behave like
        a file that omits the variable. Any other behavior would surprise an
        operator.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.delenv("CAPTURE_PORT", raising=False)
    unset_port = load_settings().web.port
    monkeypatch.setenv("CAPTURE_PORT", "")
    assert load_settings().web.port == unset_port == 8056


def test_read_port_uses_the_default_the_caller_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    """``read_port`` falls back to the default of the caller, not to 8056.

    Why:
        The Redis port reader shares this function. A hard-coded fallback would
        point the lock store at the web port.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("REDIS_PORT", "not-a-port")
    assert read_port("REDIS_PORT", 6379) == 6379


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("12", 12), ("-3", -3), ("0", 0), ("no", 7), ("", 7), ("3.5", 7)],
)
def test_read_integer_returns_the_number_or_the_default(raw: str, expected: int) -> None:
    """``read_integer`` converts the text and never raises.

    Why:
        This helper holds no range rule. It converts only, so the range check
        stays in one place inside ``read_port`` and ``read_poll_interval``.

    Args:
        raw: The text from the environment.
        expected: The number the helper must return.
    """
    assert read_integer(raw, 7, "TEST_VARIABLE") == expected


@pytest.mark.parametrize(("raw", "expected"), [("60", 60), ("5", 5), ("  45  ", 45), ("3600", 3600)])
def test_poll_seconds_override_sets_the_wait(monkeypatch: pytest.MonkeyPatch, raw: str, expected: int) -> None:
    """A good ``CAPTURE_POLL_SECONDS`` value replaces the default wait.

    Why:
        A large site needs a slower poll. Five seconds is the fastest rate the
        status endpoints can carry, so the reader must accept that edge.

    Args:
        monkeypatch: The pytest patch helper.
        raw: The text the operator puts in the variable.
        expected: The wait the reader must return.
    """
    monkeypatch.setenv("CAPTURE_POLL_SECONDS", raw)
    assert load_settings().web.poll_interval_seconds == expected


@pytest.mark.parametrize("raw", BAD_POLL_VALUES)
def test_poll_seconds_falls_back_when_the_value_is_bad(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    """A bad ``CAPTURE_POLL_SECONDS`` value gives the contract wait of 30 seconds.

    Why:
        A wait of zero or a negative wait would turn the browser poll into a
        request flood against the status endpoints.

    Args:
        monkeypatch: The pytest patch helper.
        raw: A value the reader must refuse.
    """
    monkeypatch.setenv("CAPTURE_POLL_SECONDS", raw)
    assert load_settings().web.poll_interval_seconds == 30


@pytest.mark.parametrize("raw", BAD_POLL_VALUES)
def test_a_bad_poll_value_never_yields_a_flooding_wait(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    """A bad poll value never gives a wait under five seconds.

    Why:
        This test states the floor as a property. A new fallback path cannot
        return a wait that floods the status endpoints.

    Args:
        monkeypatch: The pytest patch helper.
        raw: A value the reader must refuse.
    """
    monkeypatch.setenv("CAPTURE_POLL_SECONDS", raw)
    assert read_poll_interval() >= 5


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("slate", ("slate",)),
        ("slate,amber", ("slate", "amber")),
        (" slate , amber ", ("slate", "amber")),
        ("slate,,amber,", ("slate", "amber")),
        ("default,magenta,slate", ("default", "magenta", "slate")),
    ],
)
def test_capture_themes_override_sets_the_theme_list(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: tuple[str, ...]
) -> None:
    """A ``CAPTURE_THEMES`` comma list replaces the shipped themes.

    Why:
        A site may ship its own stylesheet. The reader drops a blank entry,
        because a trailing comma is a common mistake in a comma list.

    Args:
        monkeypatch: The pytest patch helper.
        raw: The comma list the operator sets.
        expected: The theme names the reader must return.
    """
    monkeypatch.setenv("CAPTURE_THEMES", raw)
    assert load_settings().web.themes == expected


@pytest.mark.parametrize("raw", ["", "   ", ",", " , , ", ",,,"])
def test_capture_themes_falls_back_when_the_list_is_empty(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    """An empty ``CAPTURE_THEMES`` list gives the two shipped themes.

    Why:
        A page without a theme name has no stylesheet link. The fallback keeps
        every page readable.

    Args:
        monkeypatch: The pytest patch helper.
        raw: A list that holds no name.
    """
    monkeypatch.setenv("CAPTURE_THEMES", raw)
    assert read_themes() == ("default", "magenta")


def test_theme_list_is_a_tuple_of_plain_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """The theme list is a tuple of stripped strings.

    Why:
        The settings record is frozen, so the field must hold a fixed value. A
        list would let a request handler add a theme at run time.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("CAPTURE_THEMES", " slate , amber ")
    themes = load_settings().web.themes
    assert isinstance(themes, tuple)
    assert all(isinstance(name, str) for name in themes)
    assert all(name == name.strip() for name in themes)
    assert themes  # WHY: The reader must never hand the template an empty list.


def test_default_theme_list_holds_no_duplicate() -> None:
    """The shipped theme list names each stylesheet once.

    Why:
        The page renders one option for each name. A duplicate would show the
        same choice twice in the theme control.
    """
    themes = read_themes()
    assert len(set(themes)) == len(themes)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("10.0.0.0/8", ("10.0.0.0/8",)),
        ("10.0.0.0/8,192.0.2.0/24", ("10.0.0.0/8", "192.0.2.0/24")),
        (" 10.0.0.0/8 , 192.0.2.0/24 ", ("10.0.0.0/8", "192.0.2.0/24")),
        ("192.0.2.5", ("192.0.2.5/32",)),
        ("10.1.2.3/8", ("10.0.0.0/8",)),
        ("2001:db8::/32", ("2001:db8::/32",)),
    ],
)
def test_allowed_ips_override_parses_each_network(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: tuple[str, ...]
) -> None:
    """A ``CAPTURE_ALLOWED_IPS`` comma list becomes a tuple of networks.

    Why:
        An operations tool that drives a firmware upgrade needs a network guard
        in front of the sign-in page. The reader accepts a single address and a
        whole network, and it accepts both address families.

    Args:
        monkeypatch: The pytest patch helper.
        raw: The comma list the operator sets.
        expected: The text form of each network the reader must return.
    """
    monkeypatch.setenv("CAPTURE_ALLOWED_IPS", raw)
    assert load_settings().web.allowed_networks == tuple(ip_network(entry) for entry in expected)


def test_allowed_ips_drops_one_bad_entry_and_keeps_the_good_ones(monkeypatch: pytest.MonkeyPatch) -> None:
    """A bad entry drops out and the good entries stay.

    Why:
        One typed mistake must not remove the whole guard. The remaining
        networks still block every other address.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("CAPTURE_ALLOWED_IPS", "10.0.0.0/8,not-a-network,192.0.2.0/24")
    assert read_allowed_networks() == (ip_network("10.0.0.0/8"), ip_network("192.0.2.0/24"))


def test_an_all_bad_allow_list_stops_the_portal(monkeypatch: pytest.MonkeyPatch) -> None:
    """A list where every entry is bad stops the portal from starting.

    Why:
        An empty tuple tells the security layer to accept every client address.
        The reader must never build that tuple from a list the operator typed,
        because one typo would then remove the network guard and leave no sign
        of the loss. A refusal to start puts the fault in front of the operator.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("CAPTURE_ALLOWED_IPS", "not-a-network,also-wrong,999.999.999.999")
    with pytest.raises(SettingsError, match="CAPTURE_ALLOWED_IPS"):
        read_allowed_networks()


def test_an_unset_allow_list_leaves_the_portal_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unset variable gives an empty tuple and leaves the portal open.

    Why:
        The refusal above must fire for a typed list only. An operator who asks
        for no guard at all still gets the open portal that the port 8055 portal
        gives, so a developer can start the portal with no setup.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.delenv("CAPTURE_ALLOWED_IPS", raising=False)
    assert read_allowed_networks() == ()


def test_a_blank_allow_list_leaves_the_portal_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """A variable that holds separators only leaves the portal open.

    Why:
        A blank value and a stray comma carry no entry at all, so neither states
        an intent to guard the portal. Only a typed entry that fails to parse
        stops the portal.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("CAPTURE_ALLOWED_IPS", " , , ")
    assert read_allowed_networks() == ()


@pytest.mark.parametrize(
    ("entry", "expected"),
    [
        ("10.0.0.0/8", "10.0.0.0/8"),
        (" 192.0.2.1 ", "192.0.2.1/32"),
        ("10.1.2.3/8", "10.0.0.0/8"),
        ("2001:db8::1", "2001:db8::1/128"),
    ],
)
def test_read_network_accepts_an_address_and_a_network(entry: str, expected: str) -> None:
    """``read_network`` accepts a host address inside a network.

    Why:
        The reader uses loose mode, so an operator may write the address of one
        machine with a network mask. Strict mode would refuse that entry.

    Args:
        entry: One text entry from the comma list.
        expected: The text form of the network the reader must return.
    """
    assert read_network(entry) == ip_network(expected)


@pytest.mark.parametrize("entry", ["not-a-network", "", "   ", "10.0.0.0/33", "999.999.999.999", "10.0.0.0/8/16"])
def test_read_network_returns_none_for_text_that_names_no_network(entry: str) -> None:
    """``read_network`` answers None when the text names no network.

    Why:
        The caller drops a None entry and keeps the good ones. A raised error
        would stop the portal at start over one typed mistake.

    Args:
        entry: Text that names no network.
    """
    assert read_network(entry) is None


def test_secret_key_override_keeps_the_operator_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """A ``CAPTURE_SECRET_KEY`` value becomes the session key.

    Why:
        A stable key keeps every open session across a restart. A new key at
        each restart would sign the operator out during a live upgrade.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("CAPTURE_SECRET_KEY", SECRET_KEY_SENTINEL)
    assert load_settings().web.secret_key == SECRET_KEY_SENTINEL


@pytest.mark.parametrize("raw", ["", "   "])
def test_a_missing_secret_key_becomes_a_fresh_random_key(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    """A blank ``CAPTURE_SECRET_KEY`` gives a new random key at each read.

    Why:
        A developer can start the portal with no setup. The key must still be
        long and must differ at each read, so no build ships a fixed key.

    Args:
        monkeypatch: The pytest patch helper.
        raw: A value that holds no key.
    """
    monkeypatch.setenv("CAPTURE_SECRET_KEY", raw)
    first = read_secret_key()
    second = read_secret_key()
    assert first != second  # WHY: A fixed fallback key would sign every deployment alike.
    assert len(first) >= 32  # WHY: 32 random bytes encode to a longer text.


def test_the_secret_key_never_reaches_a_log_record(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The warning for a missing session key names the variable only.

    Why:
        FR-009 forbids the portal to write a credential value into a log record.
        The operator needs the variable name to fix the setup, and nothing more.

    Args:
        monkeypatch: The pytest patch helper.
        caplog: The pytest log capture helper.
    """
    monkeypatch.setenv("CAPTURE_SECRET_KEY", "")
    with caplog.at_level(logging.WARNING):
        key = read_secret_key()
    text = caplog.text
    assert "CAPTURE_SECRET_KEY" in text  # WHY: The operator needs the name to fix the setup.
    assert key not in text  # WHY: The generated key is a credential and must stay out of the log.


def test_a_bad_port_warning_names_the_variable(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The warning for a bad port names the variable and the fallback.

    Why:
        A silent fallback would leave the operator hunting for a portal on the
        wrong port. The warning must carry enough detail to fix the setup.

    Args:
        monkeypatch: The pytest patch helper.
        caplog: The pytest log capture helper.
    """
    monkeypatch.setenv("CAPTURE_PORT", "70000")
    with caplog.at_level(logging.WARNING):
        port = read_port("CAPTURE_PORT", 8056)
    assert port == 8056
    assert "CAPTURE_PORT" in caplog.text
    assert "70000" in caplog.text  # WHY: The operator needs the refused value.


def test_arango_overrides_replace_each_address_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """The three ArangoDB variables replace the three address defaults.

    Why:
        A deployment outside the container network points at another host and
        another database. The account name is not a credential, so the record
        may hold it.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("ARANGO_HOST", "http://arango.example.com:8529")
    monkeypatch.setenv("ARANGO_DATABASE", "upgrade_records")
    monkeypatch.setenv("ARANGO_USERNAME", "portal_reader")
    arango = load_arango_settings()
    assert arango.host == "http://arango.example.com:8529"
    assert arango.database == "upgrade_records"
    assert arango.username == "portal_reader"


@pytest.mark.parametrize(("raw", "expected"), [("6380", 6380), ("not-a-port", 6379), ("0", 6379), ("70000", 6379)])
def test_redis_overrides_replace_the_address_and_guard_the_port(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: int
) -> None:
    """The Redis variables replace the host and hold the port in range.

    Why:
        The lock store port passes through the same range check as the listen
        port, so a bad value cannot point the site lock at an impossible socket.

    Args:
        monkeypatch: The pytest patch helper.
        raw: The text the operator puts in ``REDIS_PORT``.
        expected: The port the reader must return.
    """
    monkeypatch.setenv("REDIS_HOST", "redis.example.com")
    monkeypatch.setenv("REDIS_PORT", raw)
    redis = load_redis_settings()
    assert redis.host == "redis.example.com"
    assert redis.port == expected


def test_the_settings_records_carry_the_password_variable_names(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each store record holds the name of its password variable.

    Why:
        A later module reads the password from the environment at connect time.
        The record therefore passes the name along and never the value.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("ARANGO_ROOT_PASSWORD", ARANGO_PASSWORD_SENTINEL)
    monkeypatch.setenv("REDIS_PASSWORD", REDIS_PASSWORD_SENTINEL)
    settings = load_settings()
    assert settings.arango.password_variable == ARANGO_PASSWORD_NAME
    assert settings.redis.password_variable == REDIS_PASSWORD_NAME


def test_no_password_value_reaches_the_settings_tree(monkeypatch: pytest.MonkeyPatch) -> None:
    """No field of the settings tree holds a password value.

    Why:
        FR-009 forbids the portal to store a credential value. The search covers
        every field of the three groups and the whole text form of the record,
        so a new field cannot carry a password value without a failing test.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("ARANGO_ROOT_PASSWORD", ARANGO_PASSWORD_SENTINEL)
    monkeypatch.setenv("REDIS_PASSWORD", REDIS_PASSWORD_SENTINEL)
    settings = load_settings()
    whole_record = repr(settings)  # WHY: The record text holds every nested field value.
    for sentinel in (ARANGO_PASSWORD_SENTINEL, REDIS_PASSWORD_SENTINEL):
        assert sentinel not in whole_record
        assert all(sentinel not in stored for stored in collect_stored_text(settings))


def test_a_password_value_never_changes_the_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """The settings are the same with and without a password value.

    Why:
        A settings tree that ignores the password value cannot leak it. This
        test compares the two records directly, so a future read of the value
        would show up as a difference.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("CAPTURE_SECRET_KEY", SECRET_KEY_SENTINEL)  # WHY: A fixed key makes the two records comparable.
    monkeypatch.delenv("ARANGO_ROOT_PASSWORD", raising=False)
    monkeypatch.delenv("REDIS_PASSWORD", raising=False)
    without_password = load_settings()
    monkeypatch.setenv("ARANGO_ROOT_PASSWORD", ARANGO_PASSWORD_SENTINEL)
    monkeypatch.setenv("REDIS_PASSWORD", REDIS_PASSWORD_SENTINEL)
    assert load_settings() == without_password


def test_load_settings_never_reads_a_password_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loader asks the environment for no password variable.

    Why:
        A value that the module never reads cannot leak. The recorder proves the
        stronger claim, because an assertion on the result alone could not tell
        a value that was read and dropped from a value that was never read.

    Args:
        monkeypatch: The pytest patch helper.
    """
    recorder = EnvironmentRecorder(
        {
            "ARANGO_ROOT_PASSWORD": ARANGO_PASSWORD_SENTINEL,
            "REDIS_PASSWORD": REDIS_PASSWORD_SENTINEL,
        }
    )
    # WHY: The module reads the environment through its own `os` name. A patch of
    # that name reaches this module only and leaves every other module alone.
    monkeypatch.setattr(config, "os", SimpleNamespace(environ=recorder))
    load_settings()
    assert recorder.read_keys  # WHY: An empty log would make the next two checks meaningless.
    assert ARANGO_PASSWORD_NAME not in recorder.read_keys
    assert REDIS_PASSWORD_NAME not in recorder.read_keys


@pytest.mark.parametrize("record_type", [WebSettings, ArangoSettings, RedisSettings, ProxySettings, PortalSettings])
def test_no_settings_field_is_named_after_a_password_value(record_type: type) -> None:
    """No field name promises a password value.

    Why:
        A field named ``password`` would invite a later change that stores the
        value. The store records name the variable instead, so the field name
        states the rule.

    Args:
        record_type: One of the five settings record classes.
    """
    names = [field.name for field in fields(record_type)]
    assert "password" not in names
    assert all(not name.endswith("_password") for name in names)
    assert all("token" not in name for name in names)


def test_the_arango_record_holds_exactly_four_fields() -> None:
    """The primary store record holds the four documented fields.

    Why:
        A fixed field list stops a silent addition of a credential field. The
        four names also keep the record inside the Five-Item Rule.
    """
    assert [field.name for field in fields(ArangoSettings)] == ["host", "database", "username", "password_variable"]


def test_the_redis_record_holds_exactly_three_fields() -> None:
    """The lock store record holds the three documented fields.

    Why:
        Redis holds the site lock only, so the record needs no database name and
        no account name.
    """
    assert [field.name for field in fields(RedisSettings)] == ["host", "port", "password_variable"]


def test_the_web_record_holds_exactly_five_fields() -> None:
    """The web record holds the five documented fields.

    Why:
        The Five-Item Rule caps this record at five fields. A sixth field would
        mean a new settings group.
    """
    assert [field.name for field in fields(WebSettings)] == [
        "port",
        "secret_key",
        "poll_interval_seconds",
        "themes",
        "allowed_networks",
    ]


@pytest.mark.parametrize(
    ("group_name", "field_name"),
    [("web", "port"), ("arango", "host"), ("redis", "port"), ("proxy", "trusted_hops")],
)
def test_the_settings_records_are_frozen(group_name: str, field_name: str) -> None:
    """A request handler cannot change a setting after the load.

    Why:
        The portal reads a setting on every request. A record that a handler
        could change would let one request move the port or the store address
        for every later request.

    Args:
        group_name: The name of one settings group.
        field_name: The name of one field inside that group.
    """
    record = getattr(load_settings(), group_name)
    with pytest.raises(FrozenInstanceError):
        setattr(record, field_name, "changed")  # WHY: The name sits in a variable, so ruff sees no fixed attribute.


def test_load_settings_matches_the_four_group_loaders() -> None:
    """The whole loader gives the same values as the four group loaders.

    Why:
        A caller may load one group alone. The two paths must agree, or a route
        module would read a different port than the listener uses.
    """
    settings = load_settings()
    assert settings.arango == load_arango_settings()
    assert settings.redis == load_redis_settings()
    assert settings.proxy == load_proxy_settings()
    web = load_web_settings()
    # WHY: The session key differs at each read when the operator sets none, so
    # this check leaves that one field out.
    assert settings.web.port == web.port
    assert settings.web.poll_interval_seconds == web.poll_interval_seconds
    assert settings.web.themes == web.themes
    assert settings.web.allowed_networks == web.allowed_networks


def test_load_settings_returns_the_four_groups() -> None:
    """The loader returns one record that holds the four groups.

    Why:
        The factory passes one object to the security layer and to each route
        module, which keeps every function inside the parameter limit.
    """
    settings = load_settings()
    assert isinstance(settings, PortalSettings)
    assert isinstance(settings.web, WebSettings)
    assert isinstance(settings.arango, ArangoSettings)
    assert isinstance(settings.redis, RedisSettings)
    assert isinstance(settings.proxy, ProxySettings)


def test_the_proxy_record_holds_exactly_one_field() -> None:
    """The deployment topology record holds the one documented field.

    Why:
        The count of proxies is the only fact the portal needs about what sits
        in front of it. A second field here would mean the record had grown into
        a description of the proxy itself, which the portal must not depend on.
    """
    assert [field.name for field in fields(ProxySettings)] == ["trusted_hops"]


def test_the_portal_record_holds_exactly_four_groups() -> None:
    """The whole settings record holds the four documented groups.

    Why:
        The Five-Item Rule caps this record at five groups. The list is fixed
        here so a new group is a deliberate change and not a silent one, and so
        the credential search in ``collect_stored_text`` covers every field.
    """
    assert [field.name for field in fields(PortalSettings)] == ["web", "arango", "redis", "proxy"]


def test_the_proxy_hop_default_is_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """The portal trusts no forwarded header when the operator sets nothing.

    Why:
        A forwarded header is text that any caller can send. A default above
        zero would make the portal read that text as the client address, and a
        forged value would then pass the network allow list. Zero is the only
        safe default.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.delenv("CAPTURE_PROXY_HOPS", raising=False)  # WHY: The default path needs an absent variable.
    assert load_settings().proxy.trusted_hops == 0


@pytest.mark.parametrize("raw", ["1", "2", "8"])
def test_a_legal_proxy_hop_count_reaches_the_record(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    """A count inside the legal range reaches the settings record unchanged.

    Why:
        The operator states the count of proxies, and the portal must honor it.
        A portal that lowered the count would read the wrong entry of the
        forwarded header and would refuse every real client.

    Args:
        monkeypatch: The pytest patch helper.
        raw: A count inside the legal range.
    """
    monkeypatch.setenv("CAPTURE_PROXY_HOPS", raw)
    assert read_proxy_hops() == int(raw)


@pytest.mark.parametrize("raw", ["", "   ", "one", "1.5", "-1", "9", "80"])
def test_a_bad_proxy_hop_count_falls_back_to_zero(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    """Every unusable count falls back to zero, never to a working guess.

    Why:
        This reader differs from every other reader in the module. The others
        fall back to a value that keeps the portal working. A guess above zero
        here would trust a header that no proxy wrote, so this reader falls back
        to the safe end instead. Each entry covers one class of mistake: an
        empty value, spaces, a word, a decimal, a negative count, one count
        above the ceiling, and a count far above it.

    Args:
        monkeypatch: The pytest patch helper.
        raw: A value the reader must refuse.
    """
    monkeypatch.setenv("CAPTURE_PROXY_HOPS", raw)
    assert read_proxy_hops() == 0


def test_a_bad_proxy_hop_warning_names_the_variable(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The warning for a count out of range names the value and the variable.

    Why:
        A silent fallback to zero would refuse every client behind the proxy and
        would give the operator no clue why. The warning must carry enough
        detail to fix the setup.

    Args:
        monkeypatch: The pytest patch helper.
        caplog: The pytest log capture helper.
    """
    monkeypatch.setenv("CAPTURE_PROXY_HOPS", "99")
    with caplog.at_level(logging.WARNING):
        assert read_proxy_hops() == 0
    assert "CAPTURE_PROXY_HOPS" in caplog.text  # WHY: The operator needs the name to fix the setup.
    assert "99" in caplog.text  # WHY: The refused value tells the operator what to correct.


def test_the_post_check_mode_default_is_automatic(monkeypatch: pytest.MonkeyPatch) -> None:
    """The portal starts the second capture itself when the operator sets nothing.

    Why:
        The customer chose the automatic capture. This test fails on the day
        somebody changes that default, which is exactly the alarm this seam
        needs.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.delenv("CAPTURE_POST_CHECK_MODE", raising=False)  # WHY: The default path needs an absent variable.
    assert read_post_check_mode() == "automatic"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", "automatic"),
        ("   ", "automatic"),
        ("automatic", "automatic"),
        ("manual", "manual"),
        ("Manual", "manual"),
        ("  manual  ", "manual"),
        ("atuomatic", "automatic"),
        ("off", "automatic"),
        ("true", "automatic"),
    ],
)
def test_the_post_check_mode_reader_maps_each_value(monkeypatch: pytest.MonkeyPatch, raw: str, expected: str) -> None:
    """Each value maps to one mode, and every unknown value maps to automatic.

    Why:
        The entries cover a blank value, spaces, the two known modes, a case
        the operator often writes, a padded value, a typo, and two words that
        look like a switch. Only ``manual`` turns the capture off, so a typo
        keeps the evidence that the upgrade worked.

    Args:
        monkeypatch: The pytest patch helper.
        raw: The value the operator set.
        expected: The mode the reader must return.
    """
    monkeypatch.setenv("CAPTURE_POST_CHECK_MODE", raw)
    assert read_post_check_mode() == expected


def test_an_unknown_post_check_mode_warns_with_the_value(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The warning for an unknown mode names the value and the variable.

    Why:
        A silent fallback would leave the operator waiting for a manual capture
        that the portal already took. The warning carries enough detail to fix
        the setting.

    Args:
        monkeypatch: The pytest patch helper.
        caplog: The pytest log capture helper.
    """
    monkeypatch.setenv("CAPTURE_POST_CHECK_MODE", "atuomatic")
    with caplog.at_level(logging.WARNING):
        assert read_post_check_mode() == "automatic"
    assert "CAPTURE_POST_CHECK_MODE" in caplog.text  # WHY: The operator needs the name to fix the setting.
    assert "atuomatic" in caplog.text  # WHY: The refused value tells the operator what to correct.


@pytest.mark.parametrize("raw", ["", "   ", "manual", "automatic"])
def test_a_known_post_check_mode_writes_no_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, raw: str
) -> None:
    """A blank value and a known mode both pass without a warning.

    Why:
        A warning on a normal setting trains the operator to skip the log. The
        reader warns for a value it refuses, and for nothing else.

    Args:
        monkeypatch: The pytest patch helper.
        caplog: The pytest log capture helper.
        raw: A value the reader accepts.
    """
    monkeypatch.setenv("CAPTURE_POST_CHECK_MODE", raw)
    with caplog.at_level(logging.WARNING):
        read_post_check_mode()
    assert "CAPTURE_POST_CHECK_MODE" not in caplog.text
