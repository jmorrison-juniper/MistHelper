"""Environment settings for the upgrade capture portal.

Why:
    The application factory starts with no argument, because `wsgi_capture.py`
    and the menu 238 launcher both call `create_app()` with an empty argument
    list. This module therefore reads every setting from the process environment
    and returns one frozen record. A frozen record also stops a request handler
    from changing a setting while the portal runs.

    This module holds the name of each credential variable and never the value
    of a credential. FR-009 forbids the portal to show, log, or store a password
    value or a token value.
"""

import logging  # The portal logs with the standard library only.
import os  # The environment is the only source of a setting.
import re  # Checks that a theme name holds safe characters only.
import secrets  # Builds a session key when the operator sets none.
from dataclasses import dataclass  # Builds the frozen settings records.
from ipaddress import IPv4Network, IPv6Network, ip_network  # Parses the address allow list.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

Network = IPv4Network | IPv6Network  # One name for both address families.


class SettingsError(RuntimeError):
    """One setting names an access control that the portal cannot build.

    Why:
        Every other bad setting in this module falls back to a documented
        default, because one typo must not stop an operations tool. An access
        control is the one exception. A fallback there would open a portal that
        drives a firmware upgrade, and the operator would see no sign of it. The
        portal refuses to start instead, so the fault reaches the operator at
        the moment the fault appears.
    """


PORT_VARIABLE = "CAPTURE_PORT"  # The listen port of this portal.
SECRET_KEY_VARIABLE = "CAPTURE_SECRET_KEY"  # nosec B105  # WHY: this names an environment variable, not a key.
THEMES_VARIABLE = "CAPTURE_THEMES"  # A comma list of stylesheet names.
POLL_VARIABLE = "CAPTURE_POLL_SECONDS"  # The wait between two browser status calls.
ALLOWED_ADDRESSES_VARIABLE = "CAPTURE_ALLOWED_IPS"  # A comma list of networks.
PROXY_HOPS_VARIABLE = "CAPTURE_PROXY_HOPS"  # The count of trusted reverse proxies in front of the portal.
POST_CHECK_MODE_VARIABLE = "CAPTURE_POST_CHECK_MODE"  # Names who starts the second capture of a run.

ARANGO_HOST_VARIABLE = "ARANGO_HOST"  # The full URL of the primary store.
ARANGO_DATABASE_VARIABLE = "ARANGO_DATABASE"  # The database name inside that store.
ARANGO_USERNAME_VARIABLE = "ARANGO_USERNAME"  # The account name for the store.
ARANGO_PASSWORD_VARIABLE = "ARANGO_ROOT_PASSWORD"  # nosec B105  # WHY: this names a variable. No password sits here.

REDIS_HOST_VARIABLE = "REDIS_HOST"  # The host that holds the site lock.
REDIS_PORT_VARIABLE = "REDIS_PORT"  # The port of that host.
REDIS_PASSWORD_VARIABLE = "REDIS_PASSWORD"  # nosec B105  # WHY: this names an environment variable, not a password.

DEFAULT_PORT = 8056  # Port 8055 already serves the data browsing portal.
DEFAULT_POLL_INTERVAL_SECONDS = 30  # The contract sets the browser poll rate.
DEFAULT_THEMES = ("magenta", "default")  # The two stylesheets the portal ships. The first one is the default.
DEFAULT_ARANGO_HOST = "http://misthelper-arangodb:9529"  # The service name and port inside the container network.
DEFAULT_ARANGO_DATABASE = "misthelper"  # The database the other tools already use.
DEFAULT_ARANGO_USERNAME = "root"  # The account the container image creates.
DEFAULT_REDIS_HOST = "misthelper-redis"  # The service name inside the container network.
DEFAULT_REDIS_PORT = 9379  # The project Redis port. Not 6379, which every other project also publishes.
DEFAULT_PROXY_HOPS = 0  # No proxy. The socket address is the client address.

# WHY: The customer chose the automatic post-check capture. The two names below
# are the switch that hands that capture to the operator later. The driver holds
# the same two names at `upgrade/driver.py`, and this module names them again,
# because the settings module imports the standard library only.
POST_CHECK_AUTOMATIC = "automatic"  # The portal starts the second capture itself.
POST_CHECK_MANUAL = "manual"  # An operator starts the second capture.
POST_CHECK_MODES = (POST_CHECK_AUTOMATIC, POST_CHECK_MANUAL)  # Every mode the portal knows.
DEFAULT_POST_CHECK_MODE = POST_CHECK_AUTOMATIC  # The behavior of today, and the only safe fallback.

LOWEST_ALLOWED_PORT = 1024  # A port below this needs a privileged process to listen.
LOWEST_CONNECT_PORT = 1  # An outbound call needs no privilege, so every port is legal.
HIGHEST_ALLOWED_PORT = 65535  # The highest port number a socket accepts.
LOWEST_POLL_INTERVAL_SECONDS = 5  # A faster poll would flood the status endpoints.
HIGHEST_POLL_INTERVAL_SECONDS = 3600  # One hour. A larger number is a typo, not a rate an operator wants.
SECRET_KEY_BYTES = 32  # A 32-byte key matches the strength of the signing algorithm.
HIGHEST_PROXY_HOPS = 8  # No real deployment chains more proxies than this.
LOWEST_PROXY_HOPS = 0  # A negative count has no meaning.

# WHY: A theme name reaches a file path in layout.html. The template refuses a
# name that this list does not hold, so this pattern is the real guard. A name
# with a path separator, a dot, or a drive letter never enters the list.
THEME_NAME_PATTERN = re.compile(r"\A[A-Za-z0-9_-]{1,32}\Z")  # Letters, digits, hyphen, and underscore only.


@dataclass(frozen=True, slots=True)  # Frozen stops a request handler from changing a setting.
class WebSettings:
    """The listener, the session key, the poll rate, the themes, and the allow list.

    Why:
        The web layer needs these five values and no more. A separate record for
        each concern keeps every settings object inside the Five-Item Rule.

    Attributes:
        port: The listen port. The default is 8056.
        secret_key: The key that signs the browser session cookie.
        poll_interval_seconds: The wait between two browser status calls.
        themes: The name of each stylesheet the operator may choose.
        allowed_networks: The networks that may reach the portal. An empty tuple
            means the portal accepts every client address.
    """

    port: int  # The port that Gunicorn binds.
    secret_key: str  # The cookie signing key. No log line ever holds it.
    poll_interval_seconds: int  # The browser reads this value from the page.
    themes: tuple[str, ...]  # A tuple, because a frozen record needs a fixed value.
    allowed_networks: tuple[Network, ...]  # An empty tuple leaves the portal open.


@dataclass(frozen=True, slots=True)  # Frozen stops a request handler from changing a setting.
class ArangoSettings:
    """The address of the primary store and the name of its password variable.

    Why:
        The portal writes every capture and every run to ArangoDB. The record
        carries the name of the password variable and never the password value,
        because FR-009 forbids the portal to store a credential value.

    Attributes:
        host: The full URL of the database.
        database: The database name.
        username: The account name.
        password_variable: The name of the environment variable that holds the
            password. The record never holds the password itself.
    """

    host: str  # The full URL, with the scheme and the port.
    database: str  # The database name inside that host.
    username: str  # The account name. An account name is not a credential.
    password_variable: str  # The variable name only, never the password value.


@dataclass(frozen=True, slots=True)  # Frozen stops a request handler from changing a setting.
class RedisSettings:
    """The address of the lock store and the name of its password variable.

    Why:
        Redis holds the site lock and the run heartbeat only. The record carries
        the name of the password variable and never the password value.

    Attributes:
        host: The host name of the Redis service.
        port: The Redis port.
        password_variable: The name of the environment variable that holds the
            password. The record never holds the password itself.
    """

    host: str  # The service name inside the container network.
    port: int  # The port that the lock store listens on.
    password_variable: str  # The variable name only, never the password value.


@dataclass(frozen=True, slots=True)  # Frozen stops a request handler from changing a setting.
class ProxySettings:
    """The count of reverse proxies that stand in front of the portal.

    Why:
        This value describes what sits in front of the portal, not the portal
        itself, and the WSGI layer reads it before Flask starts. That is a
        different concern and a different layer from every field in
        `WebSettings`, so the value needs a record of its own.

        The count drives two security controls at once. It tells the portal
        which entry of `X-Forwarded-For` holds the true client address, which
        the network allow list then tests. It also tells the portal to read
        `X-Forwarded-Proto`, which decides whether a cookie carries the `Secure`
        flag. A wrong count breaks both controls, so one number drives both and
        the two can never disagree.

    Attributes:
        trusted_hops: The count of proxies the operator runs in front of the
            portal. Zero means no proxy, so the socket address is the client
            address and the portal ignores every forwarded header.
    """

    trusted_hops: int  # Zero means the portal trusts no forwarded header at all.


@dataclass(frozen=True, slots=True)  # Frozen stops a request handler from changing a setting.
class PortalSettings:
    """Every setting the portal needs, in four groups.

    Why:
        The factory passes one object to the security layer and to each route
        module. One object keeps every function inside the parameter limit.

    Attributes:
        web: The listener and the browser settings.
        arango: The primary store settings.
        redis: The lock store settings.
        proxy: The count of reverse proxies in front of the portal.
    """

    web: WebSettings  # The listener and the browser group.
    arango: ArangoSettings  # The primary store group.
    redis: RedisSettings  # The lock store group.
    proxy: ProxySettings  # The deployment topology group.


def load_settings() -> PortalSettings:
    """Read every portal setting from the process environment.

    Why:
        The factory takes no argument, so the environment is the only source of
        a setting. One entry point also gives the unit tests one place to patch.

    Returns:
        The four settings groups in one frozen record.
    """
    return PortalSettings(  # One call builds the whole tree, so no half-built record exists.
        web=load_web_settings(),  # The listener and the browser group.
        arango=load_arango_settings(),  # The primary store group.
        redis=load_redis_settings(),  # The lock store group.
        proxy=load_proxy_settings(),  # The deployment topology group.
    )


def load_web_settings() -> WebSettings:
    """Read the listener, the session key, the poll rate, the themes, and the allow list.

    Returns:
        The web settings group.
    """
    return WebSettings(
        port=read_port(PORT_VARIABLE, DEFAULT_PORT),  # A bad port falls back to 8056.
        secret_key=read_secret_key(),  # A missing key becomes a fresh random key.
        poll_interval_seconds=read_poll_interval(),  # A short wait falls back to 30 seconds.
        themes=read_themes(),  # An empty list falls back to the two shipped themes.
        allowed_networks=read_allowed_networks(),  # An empty list leaves the portal open.
    )


def load_arango_settings() -> ArangoSettings:
    """Read the ArangoDB address and the name of its password variable.

    Returns:
        The primary store settings group.
    """
    return ArangoSettings(
        host=os.environ.get(ARANGO_HOST_VARIABLE, DEFAULT_ARANGO_HOST),  # The container service by default.
        database=os.environ.get(ARANGO_DATABASE_VARIABLE, DEFAULT_ARANGO_DATABASE),  # The shared database.
        username=os.environ.get(ARANGO_USERNAME_VARIABLE, DEFAULT_ARANGO_USERNAME),  # The image account.
        password_variable=ARANGO_PASSWORD_VARIABLE,  # The name travels, never the value.
    )


def load_redis_settings() -> RedisSettings:
    """Read the Redis address and the name of its password variable.

    Returns:
        The lock store settings group.
    """
    return RedisSettings(
        host=os.environ.get(REDIS_HOST_VARIABLE, DEFAULT_REDIS_HOST),  # The container service by default.
        port=read_port(REDIS_PORT_VARIABLE, DEFAULT_REDIS_PORT, LOWEST_CONNECT_PORT),  # Outbound needs no privilege.
        password_variable=REDIS_PASSWORD_VARIABLE,  # The name travels, never the value.
    )


def load_proxy_settings() -> ProxySettings:
    """Read the count of reverse proxies in front of the portal.

    Returns:
        The deployment topology settings group.
    """
    return ProxySettings(
        trusted_hops=read_proxy_hops(),  # A bad value falls back to zero, which trusts no header.
    )


def read_proxy_hops() -> int:
    """Read the count of reverse proxies the operator runs in front of the portal.

    Why:
        A forwarded header is client-supplied text. The portal may trust it only
        as far as the operator states, and the operator states it here.

        A bad value falls back to zero, unlike the other readers in this module,
        which fall back to a working default. Zero is the safe end of this
        setting, not the convenient one: it makes the portal ignore every
        forwarded header and read the socket address instead. A guess above zero
        would trust a header that no proxy wrote, and a forged address would
        then pass the network allow list.

    Returns:
        The count of trusted proxies, from zero to `HIGHEST_PROXY_HOPS`.
    """
    raw = os.environ.get(PROXY_HOPS_VARIABLE, "").strip()  # An unset variable and a blank one mean the same thing.
    if not raw:  # The operator named no proxy.
        return DEFAULT_PROXY_HOPS  # Trust no forwarded header.
    hops = read_integer(raw, DEFAULT_PROXY_HOPS, PROXY_HOPS_VARIABLE)  # Text that is not a number falls back here.
    if LOWEST_PROXY_HOPS <= hops <= HIGHEST_PROXY_HOPS:  # A negative count and a huge count are both mistakes.
        return hops  # The value sits inside the legal range.
    logger.warning(
        "The proxy count %s in %s is out of range. The portal trusts no forwarded header.",  # Name the value.
        raw,
        PROXY_HOPS_VARIABLE,
    )
    return DEFAULT_PROXY_HOPS  # Fall back to the safe end, never to a guess.


def read_port(variable: str, default: int, lowest: int = LOWEST_ALLOWED_PORT) -> int:
    """Read one port number and keep it inside the legal range.

    Why:
        A bad value must not stop the portal. The portal reports the bad value
        and continues with the documented default.

        The lowest legal port differs by direction. A process needs privilege to
        listen below 1024, so the listen port keeps that floor. A process needs
        no privilege to call out to a low port, so an outbound port such as the
        Redis port passes the floor 1. A shared floor of 1024 would refuse a
        real Redis on a low port and would then connect to the default port
        instead, which is a different host service.

    Args:
        variable: The name of the environment variable.
        default: The port to use when the variable is empty or wrong.
        lowest: The lowest legal port. Pass LOWEST_CONNECT_PORT for an outbound
            port.

    Returns:
        The port number.
    """
    raw = os.environ.get(variable, "").strip()  # An unset variable and a blank one mean the same thing.
    if not raw:  # The operator set nothing.
        return default  # Use the documented default.
    port = read_integer(raw, default, variable)  # Text that is not a number falls back here.
    if lowest <= port <= HIGHEST_ALLOWED_PORT:  # A privileged or impossible port is a mistake.
        return port  # The value sits inside the legal range.
    logger.warning("The port %s in %s is out of range. The portal uses %s.", raw, variable, default)  # Then fall back.
    return default  # Continue, because a bad port must not stop the portal.


def read_integer(raw: str, default: int, variable: str) -> int:
    """Turn one environment value into a whole number.

    Why:
        The `int` builtin accepts an underscore as a digit separator, so the
        text `8_056` reads as the number 8056. An operator who types that
        underscore by mistake would get a port that the log line agrees with,
        and the mistake would stay hidden. This step refuses the separator and
        reports the raw text instead.

    Args:
        raw: The text from the environment.
        default: The number to use when the text is not a number.
        variable: The name of the environment variable, for the log line.

    Returns:
        The whole number.
    """
    try:  # An environment value is free text and may hold anything.
        if "_" in raw:  # The builtin reads an underscore as a digit separator.
            raise ValueError("A digit separator is not a number.")  # Treat it as bad text.
        return int(raw)  # The normal path for a value the operator set well.
    except ValueError:  # The text was not a number.
        logger.warning(
            "The value %s in %s is not a number. The portal uses %s.",  # The bad value reaches the log.
            raw,
            variable,
            default,
        )
        return default  # Continue with the documented default.


def read_secret_key() -> str:
    """Read the key that signs the browser session cookie.

    Why:
        A portal without a stable key drops every session at each restart. The
        portal builds a new key when the operator sets none, so a developer can
        start the portal with no setup. The portal logs the variable name only,
        never the key value.

    Returns:
        The session key.
    """
    stored = os.environ.get(SECRET_KEY_VARIABLE, "").strip()  # The value never reaches a log line.
    if stored:  # The operator set a stable key.
        return stored  # Every restart then keeps the open sessions.
    logger.warning(
        "The variable %s is empty. The portal signs the session with a new key.",  # The name only.
        SECRET_KEY_VARIABLE,
    )
    return secrets.token_urlsafe(SECRET_KEY_BYTES)  # A fresh key drops the open sessions.


def read_poll_interval() -> int:
    """Read the wait between two browser status calls.

    Why:
        The browser polls the status endpoints instead of holding an open
        stream, because an open stream holds one request thread for each
        operator. The contract sets the wait at 30 seconds.

    Returns:
        The wait in seconds.
    """
    raw = os.environ.get(POLL_VARIABLE, "").strip()  # An unset variable and a blank one mean the same thing.
    if not raw:  # The operator set nothing.
        return DEFAULT_POLL_INTERVAL_SECONDS  # The contract value.
    seconds = read_integer(raw, DEFAULT_POLL_INTERVAL_SECONDS, POLL_VARIABLE)  # Bad text falls back here.
    if LOWEST_POLL_INTERVAL_SECONDS <= seconds <= HIGHEST_POLL_INTERVAL_SECONDS:  # Both ends are wrong.
        return seconds  # The operator chose a rate the endpoints can carry.
    logger.warning(
        "The wait %s in %s is outside the range %s to %s. The portal uses %s.",  # The `%s` form keeps the record cheap.
        raw,
        POLL_VARIABLE,
        LOWEST_POLL_INTERVAL_SECONDS,
        HIGHEST_POLL_INTERVAL_SECONDS,
        DEFAULT_POLL_INTERVAL_SECONDS,
    )
    return DEFAULT_POLL_INTERVAL_SECONDS  # Continue with the contract value.


def read_post_check_mode() -> str:
    """Read who starts the post-check capture of a run.

    Why:
        The customer chose the automatic capture. A later change may hand that
        capture to the operator, and this variable is the switch. The default
        keeps the automatic capture, so a portal with no setting behaves as it
        behaves today.

        Warning: an unknown value falls back to the automatic capture. A typo
        that turned the capture off would leave the operator without the
        evidence that the upgrade worked.

    Returns:
        The mode ``automatic``, or the mode ``manual``.
    """
    raw = os.environ.get(POST_CHECK_MODE_VARIABLE, "").strip()  # An unset variable and a blank one are the same.
    if not raw:  # The operator set nothing.
        return DEFAULT_POST_CHECK_MODE  # The behavior of today.
    mode = raw.lower()  # An operator writes Manual as often as manual.
    if mode in POST_CHECK_MODES:  # The operator named a mode the portal knows.
        return mode  # The operator chose the mode of this portal.
    logger.warning(
        "The mode %s in %s is not a mode the portal knows. The portal uses %s.",  # The bad value reaches the log.
        raw,
        POST_CHECK_MODE_VARIABLE,
        DEFAULT_POST_CHECK_MODE,
    )
    return DEFAULT_POST_CHECK_MODE  # Continue with the capture that proves the upgrade worked.


def read_themes() -> tuple[str, ...]:
    """Read the name of each stylesheet the operator may choose.

    Why:
        A theme name reaches a file path in layout.html. That template refuses a
        name this list does not hold, so this list is the real guard. A name
        with a path separator or a dot would let a crafted value point the
        stylesheet link outside the theme folder, so this step drops such a
        name. The step also drops a repeated name, because a repeated name
        would show the same choice twice in the theme picker.

    Returns:
        The theme names. The tuple holds the two shipped themes when the
        operator sets none and when no name passes the check.
    """
    raw = os.environ.get(THEMES_VARIABLE, "")  # A comma list, or an empty string.
    names = tuple(name.strip() for name in raw.split(",") if name.strip())  # Drop a blank entry.
    safe = tuple(dict.fromkeys(name for name in names if THEME_NAME_PATTERN.fullmatch(name)))  # Keep the first order.
    for name in names:  # Report each name the check dropped, so the operator sees the cause.
        if name not in safe:  # The name held a character that a file path must not carry.
            logger.warning("The theme name %s in %s is not a safe name. The portal drops it.", name, THEMES_VARIABLE)
    if safe:  # At least one name passed the check.
        return safe  # The operator named the themes.
    return DEFAULT_THEMES  # Fall back to the two stylesheets the portal ships.


def read_allowed_networks() -> tuple[Network, ...]:
    """Read the networks that may reach the portal.

    Why:
        An operations tool that drives a firmware upgrade needs a network guard
        in front of the sign-in page. An unset variable keeps the portal open,
        which matches the behavior of the port 8055 portal.

        A variable that holds entries means something else. The operator asked
        for a guard. If no entry names a network, the portal must not fall back
        to an open door, because one typo would then remove the guard and leave
        no sign of the loss. The portal refuses to start instead.

    Returns:
        One entry for each valid network. An empty tuple means the operator
        asked for no guard at all.

    Raises:
        SettingsError: The variable holds entries and no entry names a network.
    """
    raw = os.environ.get(ALLOWED_ADDRESSES_VARIABLE, "")  # A comma list, or an empty string.
    entries = [entry for entry in raw.split(",") if entry.strip()]  # Drop a blank entry and a stray comma.
    if not entries:  # The operator asked for no guard at all.
        return ()  # An empty tuple leaves the portal open, as the port 8055 portal does.
    parsed = [read_network(entry) for entry in entries]  # A bad entry becomes None.
    networks = tuple(network for network in parsed if network is not None)  # Drop every bad entry.
    if not networks:  # The operator asked for a guard and no entry built one.
        raise SettingsError(
            f"The variable {ALLOWED_ADDRESSES_VARIABLE} holds {len(entries)} entries "
            f"and none of them names a network. Correct each entry, or clear the "
            f"variable to accept every client address."
        )
    return networks  # At least one network stands, so the guard exists.


def read_network(entry: str) -> Network | None:
    """Turn one text entry into a network.

    Args:
        entry: One address or one network in classless notation.

    Returns:
        The network, or None when the text is not a network.
    """
    text = entry.strip()  # A comma list often carries a space after each comma.
    try:  # The entry may hold a single address or a whole network.
        return ip_network(text, strict=False)  # Loose mode accepts a host address inside a network.
    except ValueError:  # The text named no network at all.
        logger.warning(
            "The entry %s in %s is not a network. The portal drops the entry.",  # One line for each bad entry.
            text,
            ALLOWED_ADDRESSES_VARIABLE,
        )
        return None  # The caller drops this entry and keeps the good ones.
