"""Settings, the live-call guard, and the service session for the Juniper service APIs.

The loader reads each setting from the process environment. The application
loads the git-ignored .env file into that environment at startup. The loader
names missing settings and never prints a value.
"""

from __future__ import annotations  # WHY: postponed annotations keep forward references readable on Python 3.13.

import logging  # WHY: action log before and after each settings read.
import os  # WHY: the default source of settings is the process environment.
import sys  # WHY: the automated test flags are read from the command line.
from collections.abc import Mapping  # WHY: tests inject a mapping instead of the real environment.
from dataclasses import dataclass, field  # WHY: an immutable settings record that hides its secrets.
from urllib.parse import urlsplit  # WHY: check the scheme and the host of each base address.

import requests  # WHY: one shared HTTP session for the gateway and the token request.

from src.foundation.runtime.config import (
    runtime_settings,  # WHY: read the shared test-mode flag without importing MistHelper.
)
from src.operations.exporting.juniper_rma.api.asset_service import (
    JuniperAssetService,  # WHY: the Asset API service for menu 304.
)
from src.operations.exporting.juniper_rma.api.case_service import (
    JuniperCaseService,  # WHY: the Case API service for menus 301 to 303.
)
from src.operations.exporting.juniper_rma.api.gateway import JuniperGatewayClient  # WHY: the one path to the network.
from src.operations.exporting.juniper_rma.api.messages import (  # WHY: envelopes and readers.
    RequestMessageBuilder,
    ResponseStatusReader,
)

logger = logging.getLogger(__name__)  # WHY: module logger so each settings event carries this source.


class JuniperSettingsError(ValueError):
    """A Juniper setting is missing or invalid. The message names the setting and never prints its value."""


@dataclass(frozen=True)
class JuniperSettings:
    """Validated Juniper settings. Secret and personal fields stay out of repr output."""

    app_id: str = field(repr=False)  # WHY: application identifier, hidden from repr output.
    customer_source_id: str = field(repr=False)  # WHY: source identifier that Juniper issues, hidden.
    client_id: str = field(repr=False)  # WHY: OAuth client identifier, hidden from repr output.
    client_secret: str = field(repr=False)  # WHY: OAuth client secret, hidden from repr output.
    user_id: str = field(repr=False)  # WHY: registered portal user, hidden from repr output.
    account_id: str = field(repr=False)  # WHY: account that owns the requests, hidden from repr output.
    contact_email: str = field(repr=False)  # WHY: contact e-mail, hidden from repr output.
    token_url: str  # WHY: OAuth token endpoint (HTTPS, allowed host).
    case_base_url: str  # WHY: Case API base address (HTTPS, allowed host).
    asset_base_url: str  # WHY: Asset API base address (HTTPS, allowed host).
    allowed_hosts: tuple[str, ...]  # WHY: the host allowlist that the gateway enforces.
    requests_per_second: float  # WHY: rate limit (R-10).
    retry_attempts: int  # WHY: attempts for a temporary failure (R-11).
    ca_bundle: str | None  # WHY: optional CA bundle for TLS inspection (R-13).
    retention_days: int  # WHY: age limit for stored personal fields (R-14).
    ticket_key_field: str  # WHY: Mist ticket field that matches the customer case number (O-1).


class JuniperSettingsLoader:
    """Read and check the Juniper settings from an environment mapping."""

    ALWAYS_REQUIRED = (  # WHY: names that every menu needs.
        "JUNIPER_APP_ID",
        "JUNIPER_CUSTOMER_SOURCE_ID",
        "JUNIPER_CLIENT_ID",
        "JUNIPER_CLIENT_SECRET",
        "JUNIPER_USER_ID",
        "JUNIPER_ACCOUNT_ID",
    )
    CONTACT_NAME = "JUNIPER_CONTACT_EMAIL"  # WHY: only the case calls need a contact (contract table).
    DEFAULT_OAUTH_ENDPOINT = "https://apigw.juniper.net/invoke/pub.apigateway.oauth2/getAccessToken"  # WHY: public URL.
    DEFAULT_CASE_BASE_URL = "https://apigw.juniper.net/css-caseapi/1.0"  # WHY: production Case base (O-9).
    DEFAULT_ASSET_BASE_URL = "https://apigw.juniper.net/css-asset/1.0"  # WHY: production Asset base (O-9).
    DEFAULT_ALLOWED_HOSTS = "apigw.juniper.net"  # WHY: the only host in the endpoints document.

    def __init__(self, environment: Mapping[str, str] | None = None) -> None:
        """Store the environment to read. The process environment is the default."""
        self._environment: Mapping[str, str] = (
            environment if environment is not None else os.environ
        )  # WHY: tests inject.

    def load(self, needs_contact_email: bool = True) -> JuniperSettings:
        """Return validated settings. Raise JuniperSettingsError that names the missing settings only."""
        logger.info("Loading Juniper settings (contact e-mail required: %s)", needs_contact_email)  # WHY: action log.
        required = list(self.ALWAYS_REQUIRED)  # WHY: start from the names that every menu needs.
        if needs_contact_email:  # WHY: the asset menu does not use a contact.
            required.append(self.CONTACT_NAME)  # WHY: the case calls need the contact.
        missing = [name for name in required if not self._read(name)]  # WHY: report every missing name at once.
        if missing:  # WHY: stop before any network call when a name is missing.
            raise JuniperSettingsError("Missing Juniper settings: " + ", ".join(missing))  # WHY: names only.
        settings = self._build(self._read(self.CONTACT_NAME))  # WHY: validate the rest and build the record.
        logger.debug(  # WHY: log the tuning values only, never a secret.
            "Juniper settings loaded: retries=%d rate=%.2f", settings.retry_attempts, settings.requests_per_second
        )
        return settings  # WHY: the validated record.

    def _build(self, contact_email: str) -> JuniperSettings:
        """Validate the optional settings and return the settings record."""
        allowed = self._allowed_hosts()  # WHY: every base address must use an allowed host.
        return JuniperSettings(
            app_id=self._read("JUNIPER_APP_ID"),  # WHY: application identifier from the environment.
            customer_source_id=self._read("JUNIPER_CUSTOMER_SOURCE_ID"),  # WHY: source identifier.
            client_id=self._read("JUNIPER_CLIENT_ID"),  # WHY: OAuth client identifier.
            client_secret=self._read("JUNIPER_CLIENT_SECRET"),  # WHY: OAuth client secret.
            user_id=self._read("JUNIPER_USER_ID"),  # WHY: registered portal user.
            account_id=self._read("JUNIPER_ACCOUNT_ID"),  # WHY: account that owns the requests.
            contact_email=contact_email,  # WHY: contact e-mail, empty when the menu does not need it.
            token_url=self._https_url("JUNIPER_TOKEN_URL", self.DEFAULT_OAUTH_ENDPOINT, allowed),  # WHY: checked URL.
            case_base_url=self._https_url(
                "JUNIPER_CASE_BASE_URL", self.DEFAULT_CASE_BASE_URL, allowed
            ),  # WHY: checked.
            asset_base_url=self._https_url(
                "JUNIPER_ASSET_BASE_URL", self.DEFAULT_ASSET_BASE_URL, allowed
            ),  # WHY: checked.
            allowed_hosts=allowed,  # WHY: the allowlist the gateway enforces.
            requests_per_second=self._bounded_float("JUNIPER_MAX_REQUESTS_PER_SECOND", "2", 0.5, 10.0),  # WHY: R-10.
            retry_attempts=self._bounded_int("JUNIPER_MAX_RETRY_ATTEMPTS", "3", 1, 5),  # WHY: R-11 range.
            ca_bundle=self._read("JUNIPER_CA_BUNDLE") or None,  # WHY: empty means the system trust store.
            retention_days=self._bounded_int("JUNIPER_PII_RETENTION_DAYS", "180", 1, 730),  # WHY: R-14 range.
            ticket_key_field=self._choice(
                "JUNIPER_TICKET_KEY_FIELD", "case_number", ("case_number", "id")
            ),  # WHY: O-1.
        )

    def _read(self, name: str) -> str:
        """Return the trimmed value of one setting, or an empty string when it is unset."""
        value = self._environment.get(name, "")  # WHY: a missing name reads as empty.
        return str(value).strip()  # WHY: spaces around a value are not part of it.

    def _read_or(self, name: str, default: str) -> str:
        """Return the setting value, or the default when the value is empty."""
        return self._read(name) or default  # WHY: an empty value counts as unset.

    def _allowed_hosts(self) -> tuple[str, ...]:
        """Return the lowercase host allowlist from JUNIPER_ALLOWED_HOSTS, or the default list."""
        raw = self._read_or("JUNIPER_ALLOWED_HOSTS", self.DEFAULT_ALLOWED_HOSTS)  # WHY: empty uses the default.
        hosts = tuple(item.strip().lower() for item in raw.split(",") if item.strip())  # WHY: normalize the list.
        if not hosts:  # WHY: an empty allowlist would block every call.
            raise JuniperSettingsError("JUNIPER_ALLOWED_HOSTS must name at least one host")  # WHY: names the setting.
        return hosts  # WHY: the normalized allowlist.

    def _https_url(self, name: str, default: str, allowed: tuple[str, ...]) -> str:
        """Return an HTTPS address whose host is on the allowlist. Name the setting when it fails."""
        value = self._read_or(name, default)  # WHY: an unset value uses the production default.
        parts = urlsplit(value)  # WHY: check the scheme and the host separately.
        host = (parts.hostname or "").lower()  # WHY: host names compare in lowercase.
        if parts.scheme != "https" or not host:  # WHY: only HTTPS addresses with a host are allowed.
            raise JuniperSettingsError(f"{name} must be an HTTPS address with a host name")  # WHY: names only.
        if host not in allowed:  # WHY: the host must be on JUNIPER_ALLOWED_HOSTS.
            raise JuniperSettingsError(f"The host in {name} is not in JUNIPER_ALLOWED_HOSTS")  # WHY: no host text.
        return value  # WHY: the checked address.

    def _bounded_float(self, name: str, default: str, low: float, high: float) -> float:
        """Return a number inside the range. Name the setting when the value fails."""
        raw = self._read_or(name, default)  # WHY: an unset value uses the default.
        try:  # WHY: a non-number is a setting error, not a crash.
            number = float(raw)  # WHY: the rate can carry a fraction.
        except ValueError as error:  # WHY: convert the parse error into a setting error.
            raise JuniperSettingsError(f"{name} must be a number") from error  # WHY: the setting name only.
        if not low <= number <= high:  # WHY: enforce the documented range.
            raise JuniperSettingsError(f"{name} must be between {low:g} and {high:g}")  # WHY: state the range.
        return number  # WHY: the checked value.

    def _bounded_int(self, name: str, default: str, low: int, high: int) -> int:
        """Return a whole number inside the range. Name the setting when the value fails."""
        raw = self._read_or(name, default)  # WHY: an unset value uses the default.
        try:  # WHY: a non-number is a setting error, not a crash.
            number = int(raw)  # WHY: the count is a whole number.
        except ValueError as error:  # WHY: convert the parse error into a setting error.
            raise JuniperSettingsError(f"{name} must be a whole number") from error  # WHY: the setting name only.
        if not low <= number <= high:  # WHY: enforce the documented range.
            raise JuniperSettingsError(f"{name} must be between {low} and {high}")  # WHY: state the range.
        return number  # WHY: the checked value.

    def _choice(self, name: str, default: str, options: tuple[str, ...]) -> str:
        """Return one of the allowed values. Name the setting when the value is not allowed."""
        value = self._read_or(name, default)  # WHY: an unset value uses the default.
        if value not in options:  # WHY: only the listed values are allowed.
            raise JuniperSettingsError(f"{name} must be one of: {', '.join(options)}")  # WHY: list the choices.
        return value  # WHY: the checked choice.


class JuniperLiveCallGuard:
    """Refuse live Juniper calls in the automated test modes unless JUNIPER_LIVE_TESTS is 1 (R-17)."""

    TEST_FLAGS = ("--test", "--testinteractive")  # WHY: the two automated modes of MistHelper.py.
    REFUSAL = (  # WHY: names the setting that lifts the refusal.
        "Juniper live calls are refused in automated test modes. "
        "Set JUNIPER_LIVE_TESTS=1 to allow one read-only check."
    )

    @classmethod
    def refusal_message(
        cls,
        environment: Mapping[str, str] | None = None,
        argv: list[str] | None = None,
    ) -> str | None:
        """Return the refusal text, or None when a live call may run."""
        env = environment if environment is not None else os.environ  # WHY: tests pass a mapping.
        args = argv if argv is not None else sys.argv  # WHY: tests pass the argument list.
        automated = any(flag in args for flag in cls.TEST_FLAGS) or bool(
            runtime_settings.IS_TEST_MODE
        )  # WHY: either signal.
        if not automated:  # WHY: an operator run may call the API.
            return None  # WHY: no refusal outside the automated modes.
        if str(env.get("JUNIPER_LIVE_TESTS", "")).strip() == "1":  # WHY: the explicit opt-in allows one check.
            return None  # WHY: the opt-in is set.
        return cls.REFUSAL  # WHY: the automated run must not call Juniper.


class JuniperServiceSession:
    """Hold one gateway and the two read-only services, built from one settings record."""

    def __init__(self, settings: JuniperSettings, http: requests.Session | None = None) -> None:
        """Build the gateway, the message builder, the reader, and both services."""
        self.settings = settings  # WHY: the workflows read the join field and the retention days.
        self._gateway = JuniperGatewayClient(settings, session=http)  # WHY: the single path to the network.
        builder = RequestMessageBuilder(settings)  # WHY: envelopes use the validated identifiers.
        reader = ResponseStatusReader()  # WHY: body status and fault reading.
        self.case = JuniperCaseService(self._gateway, builder, reader, settings.case_base_url)  # WHY: Case reads.
        self.asset = JuniperAssetService(self._gateway, builder, reader, settings.asset_base_url)  # WHY: Asset read.

    @classmethod
    def open(
        cls,
        needs_contact_email: bool = True,
        environment: Mapping[str, str] | None = None,
    ) -> JuniperServiceSession:
        """Load and check the settings, then return a ready session. Raise JuniperSettingsError when they fail."""
        settings = JuniperSettingsLoader(environment).load(needs_contact_email=needs_contact_email)  # WHY: validate.
        return cls(settings)  # WHY: build the services from the checked settings.

    @classmethod
    def open_for_menu(cls, needs_contact_email: bool = True) -> JuniperServiceSession | None:
        """Return a session for an operator menu, or None with the reason logged."""
        refusal = JuniperLiveCallGuard.refusal_message()  # WHY: the automated modes refuse live calls.
        if refusal is not None:  # WHY: stop before any setting is read.
            logger.warning("%s", refusal)  # WHY: tell the operator why the menu stopped.
            return None  # WHY: no session in a refused run.
        try:  # WHY: a missing or invalid setting stops the menu cleanly.
            return cls.open(needs_contact_email=needs_contact_email)  # WHY: the checked session.
        except JuniperSettingsError as error:  # WHY: names the setting, never the value.
            logger.error("%s", error)  # WHY: tell the operator what to fix.
            return None  # WHY: no session without valid settings.
