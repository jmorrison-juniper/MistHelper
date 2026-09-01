"""Contract tests for the run create call and the upgrade options call.

Why:
    `tests/contract/upgrade_portal/test_upgrade_routes.py` proves the happy path
    of both calls and the two headline refusals. It does not prove the edge of
    either one: the tier default, the option defaults, a target list of the
    wrong shape, a repeated save, and the guard that sits in front of each path.
    A body shape that drifts breaks the browser with no server error at all, so
    these tests read the body key by key.

Scope:
    `POST /api/sites/<site_id>/runs`, `POST /api/runs`, and
    `POST /api/runs/<run_id>/options`. `contracts/http-api.md` section 5 fixes
    every status and every machine code below.

Fixtures:
    Every fixture lives in this file on purpose. `conftest.py` is shared with
    other test modules, and a run store belongs to these tests alone.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

from collections.abc import Iterator  # The signed-in fixtures yield and then clean up.
from typing import Any  # A run record and a request body are both free-form.

import pytest  # The test framework of the project.
from flask import Flask  # The application type of the portal.
from flask.testing import FlaskClient  # The client type that drives every request.
from werkzeug.test import TestResponse  # The answer type that every assertion reads.

from src.upgrade_portal.runtime import identity  # The real session guard, so the tests sign in for real.
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec  # The record layer owns every field.
from src.upgrade_portal.upgrade import options as options_module  # The module that the options route resolves.

# --------------------------------------------------------------------------
# The contract values. Each one repeats a line of the specification.
# --------------------------------------------------------------------------

RUN_STORE_KEY = "RUN_STORE"  # The seam that holds the run record store.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam that reads the site lock, named by `select.py`.
OPTIONS_BUILDER_KEY = "UPGRADE_OPTIONS_BUILDER"  # The seam that `upgrade/options.py` fills.
OPTIONS_VIEW_KEY = "UPGRADE_OPTIONS_VIEW"  # The seam that builds the device rows of the options page.

PROBE_EMAIL = "probe.operator@example.invalid"  # A reserved domain, so no real address appears.
ORG_ID = "00000000-0000-0000-0000-0000000000aa"  # Matches the shared organization of the other tests.
SITE_ID = "00000000-0000-0000-0000-0000000000bb"  # Matches the shared site of the other tests.
PROBE_MAC = "5c5b350e0001"  # The device of the shared inventory payload.

SELECTED_ORG_SESSION_KEY = "selected_org_id"  # The organization pick inside the signed session.
SELECTED_SITE_SESSION_KEY = "selected_site_id"  # The site pick inside the same signed session.

CREATE_PATH = f"/api/sites/{SITE_ID}/runs"  # The path that `contracts/http-api.md` section 5 names.
CREATE_ALT_PATH = "/api/runs"  # The path that `tasks.md` T151 names, which reads the session instead.
CREATE_ENDPOINT = "upgrade.create_run"  # The endpoint that answers both paths above.
OPTIONS_PATH_TEMPLATE = "/api/runs/{run_id}/options"  # The save call of the options page.
OPTIONS_PAGE_TEMPLATE = "/runs/{run_id}/options"  # The page itself, which carries no `/api` prefix.
START_PATH_TEMPLATE = "/api/runs/{run_id}/start"  # The begin action that stands after the options save.

OK_STATUS = 200  # The save succeeded.
CREATED_STATUS = 201  # The portal created one run record.
BAD_REQUEST_STATUS = 400  # The portal could not read the request.
NOT_AUTHENTICATED_STATUS = 401  # No signed-in session.
METHOD_NOT_ALLOWED_STATUS = 405  # The path accepts a post only.
CONFLICT_STATUS = 409  # The run exists and its state refuses the call.

NOT_AUTHENTICATED_CODE = "not_authenticated"  # `identity.require_session` answers this code.
CSRF_MISSING_CODE = "csrf_missing"  # `security.py` answers this code for a post with no token.
ORG_NOT_CHOSEN_CODE = "org_not_chosen"  # The session holds no organization at all.
SITE_NOT_CHOSEN_CODE = "site_not_chosen"  # The task path carries no site and the session holds none.
BAD_OPTION_CODE = "bad_option"  # `contracts/http-api.md` fixes this code for the options call.
PRE_CAPTURE_MISSING_CODE = "pre_capture_missing"  # FR-035 refuses a start with no saved pre-check.
RUN_NOT_READY_CODE = "run_not_ready"  # The run must reach the confirmation stage before it starts.

CONFIRM_WORD = "CONFIRM"  # FR-034 fixes this exact word, in these exact letters.

TIER_STANDARD = 2  # `contracts/http-api.md` states that the tier defaults to 2.
TIER_DEEP = 3  # The second tier the run record accepts.
UNKNOWN_TIER = 9  # A whole number outside the two tiers the record layer accepts.

# WHY: `contracts/http-api.md` section 5 fixes exactly these two answer fields
# for a created run. A third field would tell the browser something the contract
# never promised, and a reader of the contract would never look for it.
CREATE_ANSWER_FIELDS = {"run_id", "state"}

# WHY: The default of each option control, as `contracts/http-api.md` names it.
DEFAULT_OPTIONS = {"reboot": True, "junos_file_action": False, "strategy": "big_bang"}

# WHY: Delta U2 retires one select and two toggles for three radio groups, so
# #2101 shows every choice at once. The page draws each group under these
# identifiers. The saved body keeps the three field names above, so the run
# driver reads the same record as before.
STRATEGY_GROUP_ID = "upgrade-strategy-group"  # The radio group that replaces the strategy select.
REBOOT_GROUP_ID = "upgrade-reboot-group"  # The radio group that replaces the reboot toggle.
JUNOS_GROUP_ID = "upgrade-junos-file-action-group"  # The radio group that replaces the Junos toggle.
RADIO_OPTION_IDS = (
    "upgrade-strategy-big-bang",  # The strategy default, which upgrades every device at once.
    "upgrade-strategy-canary",  # The staged strategy, which upgrades a small set first.
    "upgrade-reboot-yes",  # The reboot default, which reboots each device after the write.
    "upgrade-reboot-no",  # The choice that holds the reboot for a later manual window.
    "upgrade-junos-file-action-yes",  # The choice that turns the Junos file action on.
    "upgrade-junos-file-action-no",  # The Junos file action default, which leaves it off.
)
RETIRED_CONTROL_IDS = (
    "upgrade-strategy-select",  # The retired select, which showed one strategy at a time.
    "upgrade-reboot-toggle",  # The retired reboot toggle, which hid the second choice.
    "upgrade-junos-file-action-toggle",  # The retired Junos toggle, which hid the second choice.
)

# WHY: Issue #2156 names nine control families in its own table. The page draws
# one control for each cloud field of those families, under these identifiers.
# A missing control sends the operator back to the cloud interface for a field
# that this portal claims to own.
ADVANCED_CONTROL_IDS = (
    "upgrade-advanced-options",  # The card that holds every control below.
    "upgrade-canary-phases",  # `canary_phases`
    "upgrade-max-failures",  # `max_failures`
    "upgrade-max-failure-percentage",  # `max_failure_percentage`
    "upgrade-reboot-at",  # `reboot_at`
    "upgrade-force-yes",  # `force`
    "upgrade-stable-version-yes",  # `version=stable`
    "upgrade-enable-p2p-yes",  # `enable_p2p`
    "upgrade-p2p-cluster-size",  # `p2p_cluster_size`
    "upgrade-p2p-parallelism",  # `p2p_parallelism`
    "upgrade-rrm-first-batch-percentage",  # `rrm_first_batch_percentage`
    "upgrade-rrm-max-batch-percentage",  # `rrm_max_batch_percentage`
    "upgrade-rrm-node-order",  # `rrm_node_order`
    "upgrade-rrm-mesh-upgrade",  # `rrm_mesh_upgrade`
    "upgrade-rrm-slow-ramp",  # `rrm_slow_ramp`
)

# WHY: Each body below holds one value that the documented schema refuses. The
# cloud refusal names no field, so the portal must refuse first and name the
# control that holds the fault.
REFUSED_ADVANCED_BODIES = (
    {"strategy": "canary", "max_failure_percentage": "101"},  # The schema fixes the range 0 to 100.
    {"strategy": "big_bang", "canary_phases": "25,50"},  # A phase list outside the staged strategy.
    {"strategy": "canary", "canary_phases": "25,50,100", "max_failures": "1,2"},  # One limit for each phase.
    {"strategy": "rrm", "rrm_node_order": "sideways"},  # A word outside the documented enumeration.
    {"strategy": "rrm", "rrm_mesh_upgrade": "at_once"},  # The same rule for the mesh word.
    {"reboot_at": "not-a-moment"},  # A reboot window that names no epoch second.
)

PROBE_MODEL = "EX4400-48P"  # The model of the one device of the stand-in site.
PROBE_VERSIONS = ["23.4R2-S4.11", "24.2R1.17"]  # The versions that the cloud names for that model.
PROBE_VERSION_TARGET = "24.2R1.17"  # The version that the operator picks in both tests below.

# WHY: `options.html` reads exactly these six names for each row of the target
# table. A row with a missing name draws a control with no version and no label,
# which is the defect that the two tests at the end of this file guard against.
PROBE_DEVICE_ROW: dict[str, Any] = {
    "mac": PROBE_MAC,
    "name": "Probe switch",
    "device_type": "switch",
    "model": PROBE_MODEL,
    "version_before": "23.4R2-S3.9",
    "version_target": "",
}

# WHY: The site inventory names a device type under `type` and a running version
# under `version`. `build_target_entry` performs that translation, so a stand-in
# inventory row must carry the cloud names and never the stored names.
PROBE_INVENTORY_ROW: dict[str, Any] = {
    "mac": PROBE_MAC,
    "name": "Probe switch",
    "type": "switch",
    "model": PROBE_MODEL,
    "version": "23.4R2-S3.9",
    "uptime": 1832140,
}

# WHY: The browser sends a mac and a version only, because `collectUpgradeTargets`
# reads those two values from each version control. The save call must widen this
# row into the whole target record that the run driver reads.
THIN_BODY: dict[str, Any] = {"targets": [{"mac": PROBE_MAC, "version_target": PROBE_VERSION_TARGET}]}


class RecordingRunStore:
    """Holds every run record of one test in one dictionary.

    Why:
        The routes ask for a `read_run` and a `write_run` pair. This stand-in
        gives both and reaches no database server, so a contract test runs with
        no ArangoDB server and no comma-separated value fallback file.
    """

    def __init__(self) -> None:
        """Start with no run record at all."""
        self.runs: dict[str, dict[str, Any]] = {}  # One entry for each run the test seeds or creates.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record, or None when no run holds the identifier.

        Args:
            run_id: The run key.

        Returns:
            A copy of the record, or None.
        """
        held = self.runs.get(run_id)  # An absent key reads as None, never a fault.
        return dict(held) if held is not None else None  # A copy stops a caller edit of the stored record.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Write one run record and report the true result.

        Args:
            run: The whole record, with the changed fields already in place.

        Returns:
            True, because this stand-in never refuses a write.
        """
        self.runs[str(run["run_id"])] = dict(run)  # A copy stops a later edit of the caller dictionary.
        return True  # The route then answers the operator.


class RefusingOptionsBuilder:
    """Refuses every option set with one plain sentence.

    Why:
        `contracts/http-api.md` fixes 400 `bad_option` for the options call, and
        the route reaches that answer only when the injected builder raises. No
        builder ships yet, so this stand-in supplies the refusal the contract
        names and proves that the route maps it to the documented code.
    """

    def __init__(self, reason: str) -> None:
        """Build the stand-in with the sentence it raises.

        Args:
            reason: The sentence the refusal carries.
        """
        self.reason = reason  # The route copies this text into the error envelope.

    def __call__(self, record: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        """Refuse the option set of one run.

        Args:
            record: The run record the options belong to.
            body: The request body of the options call.

        Returns:
            Nothing, because this stand-in always raises.

        Raises:
            ValueError: Always, because the whole point is the refusal path.
        """
        raise ValueError(self.reason)  # `options.BadOptionError` is a `ValueError`, so the route catches this.


class WarningOptionsBuilder:
    """Answers a fixed target list, option record, and warning list.

    Why:
        Issue #2003: only a builder that answers a real warning proves that
        `save_options` writes it onto the run record. No builder ships in a
        contract test, so this stand-in fills that role.
    """

    def __init__(self, warnings: list[str]) -> None:
        """Build the stand-in with the warning list it always answers.

        Args:
            warnings: The plain sentences the built options carry.
        """
        self.warnings = warnings  # The route must copy this list onto the record.

    def __call__(self, record: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        """Answer a thin target list, the default options, and the warning list.

        Args:
            record: The run record. This stand-in reads none of it.
            body: The request body of the save call.

        Returns:
            The three fields `built_options` always widens into a record.
        """
        return {
            "targets": list(body.get("targets", [])),
            "options": {"reboot": True, "junos_file_action": False, "strategy": "big_bang"},
            "warnings": list(self.warnings),
        }


class StandInOptionsView:
    """Answer one device row and one version list, and reach no cloud.

    Why:
        The options page drew only the rows that the run record already held,
        and a new run holds none. The page therefore drew no version control,
        the browser read none, and the save call stored an empty target list.
        This stand-in stands for the site inventory read that closes that loop.
    """

    def __init__(self) -> None:
        """Start with no recorded call."""
        self.calls: list[tuple[str, str]] = []  # The organization and the site of each call.

    def __call__(self, session: Any, org_id: str, site_id: str) -> dict[str, Any]:
        """Answer the two halves that the options page draws.

        Args:
            session: The cloud session. This stand-in reads none of it.
            org_id: The organization that holds the site.
            site_id: The site under upgrade.

        Returns:
            One device row and the version list of the model of that row.
        """
        self.calls.append((org_id, site_id))  # The test reads this list to prove the site scoped the read.
        return {"targets": [dict(PROBE_DEVICE_ROW)], "versions_by_model": {PROBE_MODEL: list(PROBE_VERSIONS)}}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def run_store() -> RecordingRunStore:
    """Return a fresh run record store.

    Returns:
        An empty recording store.
    """
    return RecordingRunStore()  # Each test starts with no run at all.


@pytest.fixture
def upgrade_app(portal_app: Flask, run_store: RecordingRunStore) -> Flask:
    """Return the portal application with the run store injected.

    Why:
        The create call and the options call both write a run record. The store
        sits behind a seam, so a contract test replaces it and reaches no
        database server. The lock reader answers a reachable store that holds no
        lock, because a held site already has its own test in
        `test_upgrade_routes.py`.

        The reader must name every site it was asked about. `lock_holder` reads
        an absent key as `unknown`, not as free, so an empty index means the
        store did not answer and `lock_refusal` then refuses the write with 503.
        `dict.fromkeys` gives each site a None holder, which is the shape a
        reachable store returns for a free site. See issue #1827 and pull
        request #1890.

    Args:
        portal_app: The real application from the shared fixture.
        run_store: The stand-in run record store.

    Returns:
        The application with the seams in place.
    """
    portal_app.config[RUN_STORE_KEY] = run_store  # No ArangoDB server runs in a contract test.
    # A reachable lock store that holds no lock. An empty index would read as an
    # unreachable store and every write below would answer 503.
    portal_app.config[LOCK_READER_KEY] = lambda org_id, site_ids: dict.fromkeys(site_ids)
    portal_app.config["WTF_CSRF_ENABLED"] = False  # One test below reads the untouched application instead.
    return portal_app  # Every test below drives this application.


@pytest.fixture
def registered_owner() -> Iterator[identity.SessionOwner]:
    """Register one operator and drop the record when the test ends.

    Why:
        The guard admits a request only when the signed session and the browser
        cookie both name a registered owner. The registry is a process global,
        so the fixture clears it again.

    Yields:
        The identity pair of the registered operator.
    """
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())  # The pair the guard checks.
    record = identity.OperatorSession(
        owner=owner,
        cloud_session=object(),  # A plain object states no scope, so every organization passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
    )
    identity.SESSION_REGISTRY.register(record)  # The guard reads the registry on every request.
    try:  # The test body runs with the owner in place.
        yield owner  # Every signed-in test reads this pair.
    finally:  # A leaked record would sign in a later test by accident.
        identity.SESSION_REGISTRY.drop(owner.key)  # The registry outlives the test, so clear it here.


def sign_in_client(client: FlaskClient, owner: identity.SessionOwner, org_id: str | None, site_id: str | None) -> None:
    """Give one client a signed session, an organization pick, and a site pick.

    Why:
        Two refusal tests below need a session that holds no organization or no
        site. A fixture that always writes both could never reach either code.

    Args:
        client: The Flask test client.
        owner: The registered operator.
        org_id: The chosen organization, or None to store none.
        site_id: The chosen site, or None to store none.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # Half of the guard.
    with client.session_transaction() as browser_session:  # The other half of the guard.
        browser_session[identity.SESSION_OWNER_KEY] = owner.key  # Names the registered owner.
        if org_id is not None:  # A test of `org_not_chosen` stores no organization at all.
            browser_session[SELECTED_ORG_SESSION_KEY] = org_id
        if site_id is not None:  # A test of `site_not_chosen` stores no site at all.
            browser_session[SELECTED_SITE_SESSION_KEY] = site_id


@pytest.fixture
def upgrade_client(upgrade_app: Flask, registered_owner: identity.SessionOwner) -> Iterator[FlaskClient]:
    """Return a signed-in client that already picked the organization and the site.

    Args:
        upgrade_app: The application with the seams injected.
        registered_owner: The identity pair of the registered operator.

    Yields:
        The Flask test client, with the session held open.
    """
    with upgrade_app.test_client() as client:  # The context manager holds the session across requests.
        sign_in_client(client, registered_owner, ORG_ID, SITE_ID)  # The state that every passing test needs.
        yield client  # Every test below drives this client.


@pytest.fixture
def signed_out_client(upgrade_app: Flask) -> Iterator[FlaskClient]:
    """Return a client that never signed in.

    Args:
        upgrade_app: The application with the seams injected.

    Yields:
        The Flask test client, with no session owner at all.
    """
    with upgrade_app.test_client() as client:  # The guard must refuse every request from this client.
        yield client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def seed_run(store: RecordingRunStore, state: str, **fields: Any) -> str:
    """Write one run record straight into the store and return its key.

    Why:
        A test of the options call needs a run that already exists. Driving the
        create route first would test that route twice and would hide the rule
        under test behind an unrelated failure.

    Args:
        store: The stand-in run record store.
        state: The state the seeded run holds.
        **fields: Any further record field the test needs.

    Returns:
        The key of the seeded run.
    """
    spec = RunSpec(ORG_ID, "Probe organization", SITE_ID, "Probe site", PROBE_EMAIL, "browser-probe")
    record = RunRecordBuilder().build(spec)  # The record layer owns every field and every default.
    record["state"] = state  # The test names the stage the run already reached.
    record.update(fields)  # The saved target list arrives here.
    store.write_run(record)  # The route reads this record through the seam.
    return str(record["run_id"])  # Every path below carries this key.


def read_error_code(response: TestResponse) -> str:
    """Return the `code` field of an error envelope.

    Why:
        `contracts/README.md` states that a test asserts on `code` and never on
        the message text, because the message may change with no contract change.

    Args:
        response: The answer of one refused request.

    Returns:
        The machine code, or an empty string when the body carries none.
    """
    body: Any = response.get_json()  # Every refusal of this portal answers JSON.
    return str(body.get("error", {}).get("code", "")) if isinstance(body, dict) else ""


def save_options(client: FlaskClient, run_id: str, body: dict[str, Any]) -> TestResponse:
    """Post one option set for one run.

    Args:
        client: The Flask test client.
        run_id: The run key.
        body: The request body of the options call.

    Returns:
        The portal answer.
    """
    return client.post(OPTIONS_PATH_TEMPLATE.format(run_id=run_id), json=body)


def stand_in_inventory(session: Any, org_id: str, site_id: str) -> Any:
    """Answer one site inventory that holds the one probe device.

    Why:
        The save call reads the site inventory to widen the two fields that the
        browser sends. This stand-in gives that read, so a contract test proves
        the widening and still reaches no cloud.

    Args:
        session: The cloud session. This stand-in reads none of it.
        org_id: The organization that holds the site.
        site_id: The site under upgrade.

    Returns:
        One inventory read with one record and no partial reason.
    """
    return options_module.InventoryRead([dict(PROBE_INVENTORY_ROW)], [])


# ---------------------------------------------------------------------------
# The registration and the guard of the create path
# ---------------------------------------------------------------------------


def test_the_create_endpoint_answers_both_documented_paths(upgrade_app: Flask) -> None:
    """One endpoint binds the contract path and the task path.

    Why:
        `contracts/http-api.md` section 5 names `/api/sites/<site_id>/runs` and
        `tasks.md` T151 names `/api/runs`. Two endpoints would drift apart, so
        the portal answers both paths from one handler.

    Args:
        upgrade_app: The application with the seams injected.
    """
    bound = {rule.rule for rule in upgrade_app.url_map.iter_rules() if rule.endpoint == CREATE_ENDPOINT}
    assert "/api/sites/<site_id>/runs" in bound  # The path of the contract.
    assert CREATE_ALT_PATH in bound  # The path of the task list.


def test_the_create_path_refuses_a_read(upgrade_client: FlaskClient) -> None:
    """A get on the create path answers 405, because the contract names a post only.

    Args:
        upgrade_client: The signed-in client.
    """
    assert upgrade_client.get(CREATE_PATH).status_code == METHOD_NOT_ALLOWED_STATUS


def test_a_create_with_no_session_is_refused(signed_out_client: FlaskClient) -> None:
    """A create call with no signed-in session answers 401 `not_authenticated`.

    Args:
        signed_out_client: A client that never signed in.
    """
    answer = signed_out_client.post(CREATE_PATH, json={"tier": TIER_STANDARD})
    assert answer.status_code == NOT_AUTHENTICATED_STATUS  # The guard refused before the handler ran.
    assert read_error_code(answer) == NOT_AUTHENTICATED_CODE  # One code for every unsigned request.


def test_a_create_with_no_token_is_refused(portal_app: Flask, registered_owner: identity.SessionOwner) -> None:
    """A create post with no token answers 400 `csrf_missing`.

    Why:
        `security.py` registers the token check for every post, and `TESTING`
        does not switch it off. This test runs against the untouched portal, so
        it proves that the create route sits behind the check.

    Args:
        portal_app: The portal application, with the token check still on.
        registered_owner: The identity pair of the registered operator.
    """
    with portal_app.test_client() as client:  # This application never saw the fixture that clears the check.
        sign_in_client(client, registered_owner, ORG_ID, SITE_ID)
        answer = client.post(CREATE_PATH, json={"tier": TIER_STANDARD})
    assert answer.status_code == BAD_REQUEST_STATUS  # The check refuses before the handler runs.
    assert read_error_code(answer) == CSRF_MISSING_CODE  # The browser reads this code and fetches a token.


# ---------------------------------------------------------------------------
# T128: the body of the create call
# ---------------------------------------------------------------------------


def test_a_create_with_no_body_takes_the_standard_tier(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A create call with no body at all answers 201 and reads tier 2.

    Why:
        `contracts/http-api.md` states that the tier defaults to 2. A default of
        3 would read the whole client list of a site that never asked for it.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    answer = upgrade_client.post(CREATE_PATH)  # No JSON body and no form field.
    assert answer.status_code == CREATED_STATUS  # An absent body is not a caller defect.
    run_id = str(answer.get_json()["run_id"])  # The key the record store now holds.
    assert run_store.runs[run_id]["tier"] == TIER_STANDARD  # The documented default reached the record.


def test_a_create_takes_the_deep_tier_when_the_body_asks_for_it(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A create call with tier 3 writes tier 3 into the run record.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    answer = upgrade_client.post(CREATE_PATH, json={"tier": TIER_DEEP})  # The second tier of the contract.
    run_id = str(answer.get_json()["run_id"])  # The key the record store now holds.
    assert run_store.runs[run_id]["tier"] == TIER_DEEP  # The pre-check capture reads this field.


def test_a_create_with_an_unknown_tier_falls_back_to_the_standard_tier(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A create call with an unknown tier answers 201 and reads tier 2.

    Why:
        `contracts/http-api.md` section 5 names no `bad_tier` code for this path,
        unlike the capture start path. The route therefore falls back instead of
        refusing. This test pins that difference, so a later reader sees that the
        silence is a decision and not an omission.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    answer = upgrade_client.post(CREATE_PATH, json={"tier": UNKNOWN_TIER})  # A number outside the two tiers.
    assert answer.status_code == CREATED_STATUS  # No refusal, because the contract names no refusal code.
    run_id = str(answer.get_json()["run_id"])  # The key the record store now holds.
    assert run_store.runs[run_id]["tier"] == TIER_STANDARD  # The safe default of the contract.


def test_a_create_answers_only_the_two_contract_fields(upgrade_client: FlaskClient) -> None:
    """The created run answers the run key and the state, and nothing else.

    Why:
        The browser reads both fields at once. A third field would promise the
        reader something the contract never fixed, and a later removal would
        then read as a breaking change.

    Args:
        upgrade_client: The signed-in client.
    """
    body: Any = upgrade_client.post(CREATE_PATH, json={"tier": TIER_STANDARD}).get_json()
    assert set(body) == CREATE_ANSWER_FIELDS  # Exactly the two fields of the contract.


def test_two_creates_answer_two_different_run_keys(upgrade_client: FlaskClient) -> None:
    """Two create calls build two separate runs.

    Why:
        FR-014 binds one run to one site, and it does not bind one site to one
        run over time. A repeated key would let a second pre-check overwrite the
        record of the first upgrade.

    Args:
        upgrade_client: The signed-in client.
    """
    first = str(upgrade_client.post(CREATE_PATH, json={"tier": TIER_STANDARD}).get_json()["run_id"])
    second = str(upgrade_client.post(CREATE_PATH, json={"tier": TIER_STANDARD}).get_json()["run_id"])
    assert first != second  # Each create call owns its own record.


def test_a_create_keeps_the_readable_names_the_body_carries(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A create call stores the readable organization name and site name.

    Why:
        The picker stores neither name in the session, and every later page
        shows both. The record keeps what the create call carried, so no page
        reads the cloud again to print a heading.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    body = {"tier": TIER_STANDARD, "org_name": "Probe organization", "site_name": "Probe site"}
    run_id = str(upgrade_client.post(CREATE_PATH, json=body).get_json()["run_id"])
    assert run_store.runs[run_id]["org_name"] == "Probe organization"  # The heading of every run page.
    assert run_store.runs[run_id]["site_name"] == "Probe site"  # The second half of the same heading.


def test_a_create_with_no_chosen_organization_is_refused(
    upgrade_app: Flask,
    registered_owner: identity.SessionOwner,
) -> None:
    """A create call from a session with no organization answers 400 `org_not_chosen`.

    Why:
        Every read of a run stays inside one organization. A run with no
        organization would carry no scope at all, so the portal refuses it
        before it writes a record.

    Args:
        upgrade_app: The application with the seams injected.
        registered_owner: The identity pair of the registered operator.
    """
    with upgrade_app.test_client() as client:  # A signed session that never picked an organization.
        sign_in_client(client, registered_owner, None, SITE_ID)
        answer = client.post(CREATE_PATH, json={"tier": TIER_STANDARD})
    assert answer.status_code == BAD_REQUEST_STATUS  # The scope is missing, so the caller must pick one.
    assert read_error_code(answer) == ORG_NOT_CHOSEN_CODE  # The browser sends the operator back to the picker.


def test_a_create_on_the_task_path_with_no_chosen_site_is_refused(
    upgrade_app: Flask,
    registered_owner: identity.SessionOwner,
) -> None:
    """A create call on `/api/runs` with no chosen site answers 400 `site_not_chosen`.

    Why:
        The task path carries no site in the path, so it reads the pick of the
        session. An empty pick would bind the run to no site at all, and FR-014
        binds every run to exactly one.

    Args:
        upgrade_app: The application with the seams injected.
        registered_owner: The identity pair of the registered operator.
    """
    with upgrade_app.test_client() as client:  # A signed session that never picked a site.
        sign_in_client(client, registered_owner, ORG_ID, None)
        answer = client.post(CREATE_ALT_PATH, json={"tier": TIER_STANDARD})
    assert answer.status_code == BAD_REQUEST_STATUS  # The site is missing, so the caller must pick one.
    assert read_error_code(answer) == SITE_NOT_CHOSEN_CODE  # A distinct word from `org_not_chosen`.


# ---------------------------------------------------------------------------
# T128: the body of the options call
# ---------------------------------------------------------------------------


def test_the_options_path_refuses_a_read(upgrade_client: FlaskClient, run_store: RecordingRunStore) -> None:
    """A get on the options path answers 405, because the contract names a post only.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")  # A run that a save call could change.
    assert upgrade_client.get(OPTIONS_PATH_TEMPLATE.format(run_id=run_id)).status_code == METHOD_NOT_ALLOWED_STATUS


def test_an_options_call_with_no_session_is_refused(
    signed_out_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """An options call with no signed-in session answers 401 `not_authenticated`.

    Args:
        signed_out_client: A client that never signed in.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")  # The run exists, so only the guard can refuse.
    answer = save_options(signed_out_client, run_id, {"targets": []})
    assert answer.status_code == NOT_AUTHENTICATED_STATUS  # The guard refused before the handler ran.
    assert read_error_code(answer) == NOT_AUTHENTICATED_CODE  # One code for every unsigned request.


def test_the_options_call_writes_the_documented_defaults(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """An options call that names no control writes the default of each one.

    Why:
        `contracts/http-api.md` section 5 fixes a default for every option
        control. A silent body must therefore reach the same record as a body
        that names each default by hand.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")  # The stage at which an operator picks a version.
    assert save_options(upgrade_client, run_id, {"targets": []}).status_code == OK_STATUS
    saved = run_store.runs[run_id]["options"]  # The record the confirmation page reads back.
    # WHY: The record holds the advanced groups of issue #2156 beside these
    # three fields. The contract fixes the default of each field below, so the
    # test reads them one by one and a later field never breaks it.
    for field, value in DEFAULT_OPTIONS.items():
        assert saved[field] == value  # Every documented default reached the record.


def test_the_options_call_keeps_a_cleared_reboot_and_a_chosen_strategy(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """An options call keeps the exact choice of the operator.

    Why:
        The confirmation page shows what the operator picked. A record that held
        a default instead would show a promise the run never keeps.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")  # The stage at which an operator picks a version.
    body = {"targets": [], "reboot": False, "junos_file_action": True, "strategy": "canary"}
    assert save_options(upgrade_client, run_id, body).status_code == OK_STATUS
    saved = run_store.runs[run_id]["options"]  # The record the confirmation page reads back.
    assert saved["reboot"] is False  # The operator cleared the control, so nothing reboots on its own.
    assert saved["strategy"] == "canary"  # The chosen strategy, and never the documented default.


def test_the_options_call_drops_a_target_list_of_the_wrong_shape(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """An options call with a target field that is not a list saves no target.

    Why:
        A hand-typed body reaches this route. An empty target list is safe,
        because a run with no target upgrades nothing. A fault page would tell
        the operator nothing at all.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")  # The stage at which an operator picks a version.
    answer = save_options(upgrade_client, run_id, {"targets": "every device"})  # Text, where a list belongs.
    assert answer.status_code == OK_STATUS  # A safe fallback, and never a fault page.
    assert answer.get_json()["targets"] == []  # No target at all, so the run upgrades nothing.


def test_the_options_call_drops_a_target_row_of_the_wrong_shape(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """An options call keeps every record row and drops every other row.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")  # The stage at which an operator picks a version.
    rows = [{"mac": PROBE_MAC, "version_target": "0.14.29216"}, PROBE_MAC]  # One record and one bare address.
    saved: Any = save_options(upgrade_client, run_id, {"targets": rows}).get_json()
    assert [row["mac"] for row in saved["targets"]] == [PROBE_MAC]  # The record row survived, and the text did not.


def test_a_second_options_call_replaces_the_first_choice(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A repeated options call replaces the saved targets instead of adding to them.

    Why:
        An operator often edits a version and saves the page again. A record
        that appended the second list would upgrade a device twice, once to each
        version, and the confirmation page would show a list nobody picked.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")  # The stage at which an operator picks a version.
    save_options(upgrade_client, run_id, {"targets": [{"mac": PROBE_MAC, "version_target": "0.14.29216"}]})
    second: Any = save_options(upgrade_client, run_id, {"targets": [{"mac": PROBE_MAC, "version_target": "0.15.1"}]})
    assert len(second.get_json()["targets"]) == 1  # One row for one device, and never two.
    assert run_store.runs[run_id]["targets"][0]["version_target"] == "0.15.1"  # The later choice wins.


def test_a_refused_option_answers_the_documented_code(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """An option the portal refuses answers 400 `bad_option`.

    Why:
        `contracts/http-api.md` section 5 fixes this code, and the route reaches
        it only when the injected options builder refuses. The stand-in supplies
        that refusal, so the code is proved before the real builder lands.

    Args:
        upgrade_app: The application with the seams injected.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    upgrade_app.config[OPTIONS_BUILDER_KEY] = RefusingOptionsBuilder("No such version for this model.")
    run_id = seed_run(run_store, "pre_capture_done", targets=[{"mac": PROBE_MAC}])  # A run with a saved target.
    answer = save_options(upgrade_client, run_id, {"targets": [{"mac": PROBE_MAC, "version_target": "9.9.9"}]})
    assert answer.status_code == BAD_REQUEST_STATUS  # The contract fixes 400 for a refused option.
    assert read_error_code(answer) == BAD_OPTION_CODE  # A distinct word from `run_not_found`.
    assert run_store.runs[run_id]["targets"] == [{"mac": PROBE_MAC}]  # The refused call kept the saved choice.


def test_a_saved_option_keeps_its_warning_list_for_the_confirm_page(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """An options call stores the same warning list it answers, for the confirm page.

    Why:
        Issue #2003: the confirm page loads the run record fresh, with no
        access to the answer body of an earlier save call. A save that answered
        a warning but never stored it left the confirm page with no way to show
        that warning, so the operator reached the last page before the upgrade
        with no warning at all.

    Args:
        upgrade_app: The application with the seams injected.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    warning_text = "3 access points always reboot with this build, no matter the reboot choice."
    upgrade_app.config[OPTIONS_BUILDER_KEY] = WarningOptionsBuilder([warning_text])
    run_id = seed_run(run_store, "pre_capture_done")  # The stage at which an operator picks a version.
    answer = save_options(upgrade_client, run_id, {"targets": []})
    assert answer.status_code == OK_STATUS  # A warning never refuses the save that reports it.
    assert answer.get_json()["warnings"] == [warning_text]  # The immediate answer already carried the warning.
    assert run_store.runs[run_id]["warnings"] == [warning_text]  # The stored record must carry the same list.


# ---------------------------------------------------------------------------
# T128: the pre-check guard that stands behind the options save
# ---------------------------------------------------------------------------


def test_a_start_with_no_saved_pre_check_answers_the_documented_code(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A start of a run with no saved pre-check answers 409 `pre_capture_missing`.

    Why:
        The options page hands the operator straight on to the confirmation page,
        so a saved option set reaches this guard next. `contracts/http-api.md`
        section 5 fixes 409 here, because a missing pre-check is a state conflict
        and never a defect of the request body. FR-035 makes the saved pre-check
        the one record that a later post-check compares against, so a start
        without it would leave the operator no way to read the result.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    saved_row = {"mac": PROBE_MAC, "version_target": "0.14.29216"}  # The row the options call saved.
    run_id = seed_run(run_store, "awaiting_confirmation", targets=[saved_row])  # No pre-check at all.
    path = START_PATH_TEMPLATE.format(run_id=run_id)
    answer = upgrade_client.post(path, json={"confirm": CONFIRM_WORD})  # The right word, so only FR-035 refuses.
    assert answer.status_code == CONFLICT_STATUS  # A state conflict, and never a caller defect.
    assert read_error_code(answer) == PRE_CAPTURE_MISSING_CODE  # The page then sends the operator to the pre-check.


def test_a_saved_plan_prepares_an_adopted_pre_check_for_confirmation(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A saved plan moves a verified adopted pre-check run to confirmation."""
    run_id = seed_run(run_store, "created", pre_capture_id="cap-probe")  # The standalone capture already completed.
    answer = save_options(upgrade_client, run_id, THIN_BODY)  # The operator saves the upgrade plan.
    assert answer.status_code == OK_STATUS  # The plan reaches the run record.
    assert run_store.runs[run_id]["state"] == "awaiting_confirmation"  # The start route may now send the upgrade.


def test_a_start_before_confirmation_names_the_required_recovery(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A premature start is not reported as an already-started upgrade."""
    run_id = seed_run(  # A damaged or old run can have a pre-check and targets without the confirmation state.
        run_store,
        "created",
        pre_capture_id="cap-probe",
        targets=[{"mac": PROBE_MAC, "version_target": PROBE_VERSION_TARGET}],
    )
    answer = upgrade_client.post(START_PATH_TEMPLATE.format(run_id=run_id), json={"confirm": CONFIRM_WORD})
    assert answer.status_code == CONFLICT_STATUS  # The run is recoverable, but it cannot start yet.
    assert read_error_code(answer) == RUN_NOT_READY_CODE  # The browser displays the state-specific cure.
    assert run_store.runs[run_id]["state"] == "created"  # A rejected start never changes the run state.


# ---------------------------------------------------------------------------
# T128: the device rows that the options page draws and then saves
# ---------------------------------------------------------------------------


def test_the_options_page_draws_a_version_control_for_every_device(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The options page draws one version control for each device of the site.

    Why:
        A new run record holds no target row, and the page drew only the rows
        that the record already held. The page therefore drew no version
        control, the browser read none, and the save call stored an empty
        target list. The run then reached no device at all. This test holds
        that loop shut.

    Args:
        upgrade_app: The application with the seams injected.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    view = StandInOptionsView()  # The test reads the call list of this object below.
    upgrade_app.config[OPTIONS_VIEW_KEY] = view  # The seam stands for the site inventory read.
    run_id = seed_run(run_store, "pre_capture_done")  # A fresh run, which holds no target row.
    answer = upgrade_client.get(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id))
    assert answer.status_code == OK_STATUS  # A page read never refuses a run that exists.
    page = answer.get_data(as_text=True)
    assert f'data-version-for="{PROBE_MAC}"' in page  # The one control that the browser reads.
    assert PROBE_VERSION_TARGET in page  # The version list of the model reached that control.
    assert "The run holds no device" not in page  # The empty table is the defect this test guards.
    assert view.calls == [(ORG_ID, SITE_ID)]  # One read, scoped to the site of the run.


def test_the_options_page_draws_a_radio_group_for_each_single_choice(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The options page draws a radio group for strategy, reboot, and Junos action.

    Why:
        Issue #2101 asked for a radio group in place of one select and two
        toggles. A radio group shows every choice at once, so the operator reads
        all options without opening a menu. Delta U2 fixes the group and option
        identifiers, and the three retired identifiers never render again.

    Args:
        upgrade_app: The application with the seams injected.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    view = StandInOptionsView()  # The seam stands for the site inventory read.
    upgrade_app.config[OPTIONS_VIEW_KEY] = view  # The page reads its device rows from this seam.
    run_id = seed_run(run_store, "pre_capture_done")  # The stage at which an operator picks options.
    answer = upgrade_client.get(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id))
    assert answer.status_code == OK_STATUS  # A page read never refuses a run that exists.
    page = answer.get_data(as_text=True)  # The rendered options page the browser receives.
    for group_id in (STRATEGY_GROUP_ID, REBOOT_GROUP_ID, JUNOS_GROUP_ID):
        assert f'data-testid="{group_id}"' in page  # Each single choice draws a radio group now.
    for option_id in RADIO_OPTION_IDS:
        assert f'data-testid="{option_id}"' in page  # Each radio option carries its own identifier.
    for retired_id in RETIRED_CONTROL_IDS:
        assert f'data-testid="{retired_id}"' not in page  # No retired identifier renders again.


def test_the_options_page_draws_the_three_type_version_controls(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The page renders typed controls and removes the retired global control."""
    view = StandInOptionsView()
    upgrade_app.config[OPTIONS_VIEW_KEY] = view
    run_id = seed_run(run_store, "pre_capture_done")
    page = upgrade_client.get(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)).get_data(as_text=True)
    for device_type in ("ap", "switch", "gateway"):
        assert f'data-testid="upgrade-version-select-{device_type}"' in page
    assert 'data-testid="upgrade-version-select-all"' not in page


def test_the_options_page_marks_known_firmware_mismatches_only(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A known difference has a marker, and an unknown version does not."""
    known = dict(
        PROBE_DEVICE_ROW,
        safe_target="24.2R1.17",
        target_source="model_fallback",
        firmware_mismatch=True,
    )
    unknown = dict(
        PROBE_DEVICE_ROW,
        mac="5c5b350e0002",
        version_before="",
        safe_target="24.2R1.17",
        target_source="model_fallback",
        firmware_mismatch=False,
    )
    upgrade_app.config[OPTIONS_VIEW_KEY] = lambda session, org_id, site_id: {
        "targets": [known, unknown],
        "versions_by_model": {PROBE_MODEL: list(PROBE_VERSIONS)},
        "type_selections": {},
    }
    run_id = seed_run(run_store, "pre_capture_done")
    page = upgrade_client.get(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)).get_data(as_text=True)
    assert f'data-testid="firmware-mismatch-{PROBE_MAC}"' in page
    assert 'data-testid="firmware-mismatch-5c5b350e0002"' not in page
    assert 'data-safe-target="24.2R1.17"' in page


def test_an_unavailable_target_is_rejected_without_replacing_the_saved_plan(
    upgrade_client: FlaskClient, run_store: RecordingRunStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A stale save returns `bad_option` and leaves the existing targets unchanged."""
    monkeypatch.setattr(options_module, "read_upgrade_inventory", stand_in_inventory)
    monkeypatch.setattr(options_module, "read_model_versions", lambda *args: {"AP45": ()})
    old_targets = [{"mac": PROBE_MAC, "version_target": PROBE_VERSION_TARGET}]
    run_id = seed_run(run_store, "pre_capture_done", targets=old_targets)
    answer = save_options(upgrade_client, run_id, {"targets": old_targets})
    assert answer.status_code == BAD_REQUEST_STATUS
    assert read_error_code(answer) == BAD_OPTION_CODE
    assert run_store.runs[run_id]["targets"] == old_targets


def test_a_thin_saved_row_widens_into_the_record_the_run_driver_reads(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A save call widens the two browser fields into the whole target record.

    Why:
        The browser sends a mac and a version only. `to_device_targets` reads
        `device_type` and `version_target` as plain subscripts, so a stored row
        of two fields raises and the run then builds no upgrade plan. The save
        call must read the site inventory and store the whole record.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
        monkeypatch: The fixture that points the module read at the stand-in.
    """
    monkeypatch.setattr(options_module, "read_upgrade_inventory", stand_in_inventory)
    monkeypatch.setattr(options_module, "read_model_versions", lambda *args: {PROBE_MODEL: tuple(PROBE_VERSIONS)})
    run_id = seed_run(run_store, "pre_capture_done")  # A fresh run, which holds no target row.
    answer = save_options(upgrade_client, run_id, THIN_BODY)
    assert answer.status_code == OK_STATUS  # A good option set never refuses.
    saved = run_store.runs[run_id]["targets"][0]  # The one row that the run driver reads.
    assert saved["device_type"] == "switch"  # The inventory named the type, and the browser never does.
    assert saved["version_target"] == PROBE_VERSION_TARGET  # The choice of the operator stands.
    assert saved["state"] == options_module.STATE_PENDING  # The driver reads this field on every device.


# ---------------------------------------------------------------------------
# Issue #2156: the advanced upgrade controls
# ---------------------------------------------------------------------------


def test_the_options_page_draws_every_advanced_control(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The options page draws one control for each advanced upgrade field.

    Why:
        Issue #2156 states that the portal exposed a subset of the cloud upgrade
        fields. An operator who needed a phase list, a failure limit, or a radio
        setting had to leave the portal and call the cloud by hand.

    Args:
        upgrade_app: The application with the seams injected.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    upgrade_app.config[OPTIONS_VIEW_KEY] = StandInOptionsView()  # The seam stands for the site inventory read.
    run_id = seed_run(run_store, "pre_capture_done")
    page = upgrade_client.get(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)).get_data(as_text=True)
    for test_id in ADVANCED_CONTROL_IDS:
        assert f'data-testid="{test_id}"' in page  # Every control of the issue table renders.


def test_the_options_page_marks_each_advanced_control_with_its_own_rule(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """Each advanced control names the device types and strategies that read it.

    Why:
        Issue #2156 asks the page to hide a control when its selected device
        type does not support it. The rule lives in the markup, because the
        content security policy blocks an inline script and portal.js therefore
        reads the rule from the attribute.

    Args:
        upgrade_app: The application with the seams injected.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    upgrade_app.config[OPTIONS_VIEW_KEY] = StandInOptionsView()
    run_id = seed_run(run_store, "pre_capture_done")
    page = upgrade_client.get(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)).get_data(as_text=True)
    assert 'data-requires-device-type="ap"' in page  # The radio and peer-to-peer controls.
    assert 'data-requires-device-type="switch gateway"' in page  # The separate reboot window.
    assert 'data-requires-strategy="canary"' in page  # The phase list and the per-phase failure count.
    assert 'data-requires-strategy="rrm"' in page  # Every radio resource management field.


def test_the_options_page_offers_the_two_new_strategy_words(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The strategy group offers the serial word and the radio word.

    Args:
        upgrade_app: The application with the seams injected.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    upgrade_app.config[OPTIONS_VIEW_KEY] = StandInOptionsView()
    run_id = seed_run(run_store, "pre_capture_done")
    page = upgrade_client.get(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)).get_data(as_text=True)
    assert 'data-testid="upgrade-strategy-serial"' in page  # One device at a time.
    assert 'data-testid="upgrade-strategy-rrm"' in page  # Access points in radio batches.


def test_an_advanced_choice_reaches_the_stored_option_record(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """A save call stores every advanced choice in its own nested group.

    Why:
        The run driver rebuilds the option record from the store, so a choice
        that never reached the store never reaches the cloud. The operator would
        read one plan on the page and the cloud would run another.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")
    body = {
        "targets": [],
        "strategy": "canary",
        "canary_phases": "25,50,100",
        "max_failure_percentage": "12",
        "force": True,
        "enable_p2p": True,
        "p2p_cluster_size": "12",
    }
    assert save_options(upgrade_client, run_id, body).status_code == OK_STATUS
    saved = run_store.runs[run_id]["options"]  # The record the run driver reads back.
    assert saved["force"] is True
    assert saved["canary"]["canary_phases"] == (25, 50, 100)  # The staged group holds its own fields.
    assert saved["canary"]["max_failure_percentage"] == 12
    assert saved["peer_to_peer"]["enable_p2p"] is True  # The peer-to-peer group holds its own fields.
    assert saved["peer_to_peer"]["p2p_cluster_size"] == 12


def test_a_refused_advanced_value_answers_the_documented_code(
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """An advanced value outside its documented range answers 400 `bad_option`.

    Why:
        Issue #2156 asks the server to validate every value. The browser is not
        the guard, because a hand-typed body reaches the same route.

    Args:
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    run_id = seed_run(run_store, "pre_capture_done")
    before = dict(run_store.runs[run_id]["options"])  # The record layer already seeded the defaults.
    for body in REFUSED_ADVANCED_BODIES:
        answer = save_options(upgrade_client, run_id, {"targets": [], **body})
        assert answer.status_code == BAD_REQUEST_STATUS  # The contract fixes 400 for a refused option.
        assert read_error_code(answer) == BAD_OPTION_CODE  # One code for every refused option.
    assert run_store.runs[run_id]["options"] == before  # No refused call ever wrote a partial record.


def test_a_saved_run_reopens_with_every_advanced_choice_shown(
    upgrade_app: Flask,
    upgrade_client: FlaskClient,
    run_store: RecordingRunStore,
) -> None:
    """The options page shows the advanced values that an earlier save stored.

    Why:
        Issue #2156 asks for a saved-run reload. An operator who edits one
        control and loses the other ten sends a plan that nobody reviewed.

    Args:
        upgrade_app: The application with the seams injected.
        upgrade_client: The signed-in client.
        run_store: The stand-in run record store.
    """
    upgrade_app.config[OPTIONS_VIEW_KEY] = StandInOptionsView()
    run_id = seed_run(run_store, "pre_capture_done")
    body = {"targets": [], "strategy": "canary", "canary_phases": "25,50,100", "p2p_cluster_size": "12"}
    assert save_options(upgrade_client, run_id, body).status_code == OK_STATUS
    page = upgrade_client.get(OPTIONS_PAGE_TEMPLATE.format(run_id=run_id)).get_data(as_text=True)
    assert 'value="25,50,100"' in page  # The phase control reopens with the saved list.
    assert 'value="12"' in page  # The download group control reopens with the saved count.
