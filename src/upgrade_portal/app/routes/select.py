"""The organization picker, the site picker, and the site inventory reader.

Why:
    Stage two of the operator journey answers one question: which site does this
    upgrade run act on? FR-012 asks for a searchable site list. FR-014 binds one
    run to one site. FR-015 asks the selection layer to accept a list of sites
    later, with no change to the capture logic. Every function below therefore
    works on a list of site records, even where the page shows one row.

Route names:
    Another module renders the templates and the browser script against these
    endpoint names, so the names are a contract and no rename is safe:
    `select.org_page`, `select.choose_org`, `select.sites_page`,
    `select.list_sites`, and `select.site_inventory`.

Two paths, one site list:
    `contracts/http-api.md` names `GET /api/sites` and holds the organization in
    the session. `tasks.md` names `GET /api/orgs/<org_id>/sites` and holds the
    organization in the path. Both rules bind to `select.list_sites`, so the two
    documents agree and neither path repeats a line of logic.

Seams:
    One module of this feature arrives after this one. `capture.devices` reads
    the device list of a site. This module reaches it through a seam: an
    injected callable in the application configuration first, then a late
    import of the real module. Nothing here imports that module while this
    module loads, so the portal starts today and picks up the device module on
    the day it lands.

    `runtime.lock` is built, so the lock endpoints below import it plainly. The
    import adds no cycle, because `runtime.lock` reaches `app/config.py` alone
    and that module imports the standard library only. The site list keeps its
    `SITE_LOCK_READER` seam, and the lock endpoints reach the store through the
    `LOCK_STORE_CLIENT` seam instead. A contract test then drives the real lock
    rules against a stand-in store and needs no Redis server.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # The portal logs with the standard library only.
from collections.abc import Callable  # Types each injected seam.
from dataclasses import dataclass  # Builds the frozen view model of the organization picker.
from importlib import import_module  # Imports a later module late, never at load.
from types import ModuleType  # The return type of a late import.
from typing import Any  # A cloud payload and an injected seam are both free-form.
from urllib.parse import urlencode  # Escapes the filter text inside a paging link.

from flask import Blueprint, Response, current_app, jsonify, render_template, request, session  # The framework.
from jinja2 import TemplateNotFound  # Marks a template that a later module still builds.

from ...runtime import identity, lock  # The session guard, and the site lock that FR-072 to FR-083 fix.
from ..factory import build_error_envelope, json_error  # The one error envelope that the contract allows.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

select_bp = Blueprint("select", __name__)  # No URL prefix, because the paths span `/select` and `/api`.

# Each route declares a full path, so a reader finds the whole path in one place.
ORG_PAGE_PATH = "/select/org"  # The organization picker, and the post that stores the pick.
SITE_PAGE_PATH = "/select/site"  # The site picker for the chosen organization.
SITE_INVENTORY_PAGE_PATH = "/select/site/<site_id>"  # The device list of one site, as a page.
SITES_API_PATH = "/api/sites"  # The site list, with the organization in the session.
ORG_SITES_API_PATH = "/api/orgs/<org_id>/sites"  # The same list, with the organization in the path.
INVENTORY_API_PATH = "/api/sites/<site_id>/inventory"  # The device list of one site.
LOCK_API_PATH = "/api/sites/<site_id>/lock"  # The acquire, the resume, the takeover, and the release.
HEARTBEAT_API_PATH = "/api/sites/<site_id>/lock/heartbeat"  # The beat that keeps one lock alive.

SELECTED_ORG_KEY = "selected_org_id"  # The field inside the signed browser session.
SELECTED_SITE_KEY = "selected_site_id"  # The site pick, in the same signed session.
ORG_FIELD = "org_id"  # The body field that carries the pick.
FILTER_FIELD = "q"  # The optional text filter of the site list and of the organization picker.
NEXT_AFTER_ORG = SITE_PAGE_PATH  # The page the browser opens after a successful pick.
OFFSET_FIELD = "offset"  # The query argument that names the first row of the wanted page.

# `contracts/http-api.md:53` asks the organization picker to page and to filter
# inside the portal. The privilege list arrives whole with the cloud session, so
# both steps run over a list the portal already holds and cost no cloud read.
# The capture history page holds the same number of rows, so the two pages read
# alike and an operator learns one habit instead of two.
ORG_PAGE_SIZE = 25  # The number of organization rows one page holds.

# `contracts/ui-testids.md` names `org-search`, `org-row-{org_id}`, and
# `org-select-{org_id}`, and it names no paging control for this page. The two
# values below follow the `history-page-next` and `history-page-previous` shape
# of that same file, so the picker and the history page spell one idea one way.
ORG_NEXT_TEST_ID = "org-page-next"  # The control that opens the later page.
ORG_PREVIOUS_TEST_ID = "org-page-previous"  # The control that opens the earlier page.

ORG_TEMPLATE = "select/orgs.html"  # The organization picker page.
SITE_TEMPLATE = "select/sites.html"  # The site picker page.
INVENTORY_TEMPLATE = "select/inventory.html"  # The device list of one site.
FALLBACK_TEMPLATE = "layout.html"  # The shell page, shown while a picker template is still missing.

MIST_READER_KEY = "MIST_READER"  # A test injects one callable here and reaches no network.
DEVICE_READER_KEY = "DEVICE_READER"  # The seam for `capture.devices`.
LOCK_READER_KEY = "SITE_LOCK_READER"  # The seam for `runtime.lock`.

PACKAGE_ROOT = __name__.rsplit(".", maxsplit=3)[0]  # Three levels up from `app.routes.select`.
DEVICES_MODULE = "capture.devices"  # Built by the device read work of this phase.
LOCK_MODULE = "runtime.lock"  # Built by the site lock work of this phase.

# The device module may publish its reader under any of these names. The first
# match wins, which mirrors `factory.BLUEPRINT_ATTRIBUTES` and needs no
# registration list inside the device module.
DEVICE_READER_ATTRIBUTES = ("read_site_inventory", "read_inventory", "list_site_devices")  # First match wins.
LOCK_READER_ATTRIBUTES = ("read_site_locks", "read_locks", "lock_holders")  # The same rule for the lock module.

# The site list is one page for the operator, so one call must return every site.
# A larger limit costs one request and saves a second round trip.
SITE_LIST_LIMIT = 1000  # One request then fills the whole picker.

# The read name travels as text, so a test can inject one callable for every
# read. The tuple holds the module that owns the call and the name of the call.
CLOUD_READS: dict[str, tuple[str, str]] = {
    "listOrgSites": ("mistapi.api.v1.orgs.sites", "listOrgSites"),  # The site records of one organization.
    "listOrgSiteStats": ("mistapi.api.v1.orgs.stats", "listOrgSiteStats"),  # The device count of each site.
}

# Warning: `type="all"` on `searchOrgDevices` can break the read. That value is
# legal on `listSiteDevicesStats` only. This module passes no device type at
# all, because the device module owns every device read and owns that parameter
# with it.
DEVICE_TYPES = ("ap", "gateway", "switch")  # FR-013 names these three types and no other.

# The cloud names a device type in the singular. `data-model.md` section 3.6
# names the count field in the plural. The two names differ, so the map holds
# the one place that joins them. Without the map the page reads a key that the
# route never writes, and every count shows the fallback value instead.
TYPE_COUNT_FIELDS = {"ap": "access_points", "gateway": "gateways", "switch": "switches"}  # Cloud to page.
TOTAL_FIELD = "devices_total"  # `data-model.md` section 3.6 fixes this name.

DEVICE_COUNT_FIELD = "num_devices"  # The site statistics record names the whole count here.
DEVICE_COUNT_PARTS = ("num_ap", "num_switch", "num_gateway")  # The fallback, summed when the whole count is absent.

# `contracts/site-lock.md:118` asks a read-only page to mark the lock state
# unknown when the lock store does not answer. A row that carries only a holder
# address cannot say that, because a free site and an unreadable site both hold
# None. These three words give the row a third state, and `locked_by` keeps the
# two meanings that `contracts/http-api.md:79-80` fixes for it.
LOCK_STATE_FREE = "free"  # The lock store answered and named no holder.
LOCK_STATE_LOCKED = "locked"  # The lock store answered and named a holder.
LOCK_STATE_UNKNOWN = "unknown"  # The lock store did not answer, so the portal cannot tell.

# `partials/lock_banner.html` names a fourth word that the site list cannot
# reach. The lock store answers one address for each site, and several browsers
# of one operator share that address. Only the signed session of this browser
# holds the token, so only a page of this browser can report the fourth state.
LOCK_STATE_HELD = "held"  # This browser holds the lock, and the banner shows the release control.

# Warning: a second spelling of the organization scope rule can become a
# security defect. `runtime/identity.py` owns that rule, the
# `org_not_permitted` code, the refusal sentence, and the 403 status. This
# module names none of the four.
ORG_NOT_CHOSEN = "org_not_chosen"  # The request named no organization and the session holds none.
SITE_NOT_FOUND = "site_not_found"  # `contracts/http-api.md` fixes this code for the inventory.

ORG_NOT_CHOSEN_MESSAGE = "Choose an organization before you read the site list."  # The operator reads this.
SITE_NOT_FOUND_MESSAGE = "The portal found no such site in this organization."  # The same text for both paths.

OK_STATUS = 200  # The answer for a read that succeeded.
BAD_REQUEST_STATUS = 400  # The portal could not read the request.
NOT_FOUND_STATUS = 404  # No such site inside the chosen organization.
CONFLICT_STATUS = 409  # Another operator holds the site, or the caller lost the lock it named.
SERVER_ERROR_STATUS = 500  # A part of the portal is missing, so the read cannot run.
UNAVAILABLE_STATUS = 503  # The lock store did not answer a write, and no fallback is allowed.
REDIRECT_STATUS = 303  # See Other, so the browser reads the next page with GET and never repeats the post.

# One post serves a browser form and a script, so the answer follows one rule.
# The names below hold the two media types and the header that a script sets.
BROWSER_MIME = "text/html"  # A browser form post states this type first.
SCRIPT_MIME = "application/json"  # The portal script asks for this type.
SCRIPT_HEADER = "X-Requested-With"  # A script marks its own request with this header.
SCRIPT_HEADER_VALUE = "XMLHttpRequest"  # The one value that names a script request.
LOCATION_HEADER = "Location"  # The header that carries the next page of a redirect.


def load_optional_module(suffix: str) -> ModuleType | None:
    """Import one portal module that a later stage may still be building.

    Why:
        The portal grows in stages, and this module ships before the device
        module and the lock module. A late import by text keeps this module
        importable today. The name is text, so no static check reaches for a
        file that does not exist yet.

    Args:
        suffix: The module path inside the portal package.

    Returns:
        The module, or None when the module is not built yet.
    """
    try:  # The module arrives in a later stage of this phase.
        return import_module(f"{PACKAGE_ROOT}.{suffix}")  # The late import keeps this module loadable.
    except ImportError:  # Expected while the portal grows, so this is not a fault.
        logger.info("select: the module %s is not built yet", suffix)  # One line, no stack trace.
        return None  # The caller degrades and keeps the page working.


def find_attribute(module: ModuleType | None, names: tuple[str, ...]) -> Callable[..., Any] | None:
    """Find the first callable that one module publishes under a known name.

    Why:
        This module and the device module belong to two separate work streams.
        A tuple of accepted names lets the device module choose its own name
        without a change here.

    Args:
        module: The imported module, or None.
        names: The accepted attribute names, in order of preference.

    Returns:
        The first callable found, or None.
    """
    if module is None:  # The module is not built yet.
        return None  # The caller degrades.
    for name in names:  # The first match wins.
        candidate: Any = getattr(module, name, None)  # A missing name reads as None.
        if callable(candidate):  # Guard against a name that holds something else.
            found: Callable[..., Any] = candidate  # The named type satisfies the strict return check.
            return found  # The module publishes its reader under this name.
    return None  # The module holds no reader under any accepted name.


def injected_seam(config_key: str) -> Callable[..., Any] | None:
    """Return the callable that the application configuration holds for one seam.

    Why:
        A contract test injects a stand-in here and reaches no network and no
        Redis server. The injection wins over the late import, so a test never
        depends on the build order of the other modules.

    Args:
        config_key: The configuration key of the seam.

    Returns:
        The injected callable, or None when the configuration holds none.
    """
    candidate: Any = current_app.config.get(config_key)  # An unset key reads as None.
    return candidate if callable(candidate) else None  # A value that is not callable counts as unset.


def cloud_reader() -> Callable[..., Any]:
    """Return the callable that performs one Mist cloud read.

    Why:
        Every cloud read of this module travels through one named seam. A test
        injects a stand-in and asserts on the read name and the parameters, with
        no socket and no cloud account.

    Returns:
        The injected reader, or the reader that calls the cloud.
    """
    return injected_seam(MIST_READER_KEY) or default_cloud_read  # The injection wins over the cloud.


def default_cloud_read(name: str, **parameters: Any) -> list[dict[str, Any]]:
    """Read one paged cloud list through the Mist software development kit.

    Why:
        The read name travels as text, so the seam above stays simple and a test
        can answer any read by name. This function turns that name into the one
        call that owns it, and it collects every page before it answers.

    Args:
        name: The name of the cloud read.
        **parameters: The call parameters, such as the organization identifier.

    Returns:
        Every record of the read, or an empty list when the read cannot run.
    """
    target = CLOUD_READS.get(name)  # An unknown name reads as None.
    record = identity.current_session()  # The cloud session of this operator.
    if target is None or record is None:  # A caller defect, or a request with no session.
        logger.warning("select: no cloud read is bound to the name %s", name)  # Name the read, never a token.
        return []  # An empty list keeps the page working and shows no site.
    call: Any = getattr(import_module(target[0]), target[1])  # The software development kit owns the call.
    org_id = str(parameters.get(ORG_FIELD, ""))  # Every read of this module is organization-scoped.
    page = call(record.cloud_session, org_id=org_id, limit=SITE_LIST_LIMIT)  # The first page of the read.
    return collect_pages(record.cloud_session, page)  # Every later page travels through the same helper.


def collect_pages(cloud_session: Any, response: Any) -> list[dict[str, Any]]:
    """Gather every page of one cloud list response.

    Why:
        A large organization holds more sites than one page carries. The
        pagination helper of the software development kit returns an empty list
        when the answer holds an unexpected shape. This function therefore keeps
        the first page whenever the helper returns less than the first page did.

    Args:
        cloud_session: The Mist session that made the call.
        response: The response object of the first page.

    Returns:
        Every record of every page.
    """
    first = as_records(getattr(response, "data", None))  # The first page, whatever the helper does next.
    pagination: Any = getattr(import_module("mistapi"), "get_all", None)  # The helper walks the later pages.
    if pagination is None:  # An older software development kit holds no helper.
        return first  # One page is still a correct answer for a small organization.
    gathered = as_records(pagination(mist_session=cloud_session, response=response))  # Every page, in one call.
    return gathered if len(gathered) >= len(first) else first  # A shrunken answer means the helper gave up.


def as_records(payload: Any) -> list[dict[str, Any]]:
    """Read one cloud payload as a list of records.

    Why:
        A cloud read answers with a list, or with an object that holds the list
        under `results`. One reader keeps every caller free of that difference,
        and an unexpected shape becomes an empty list instead of a fault.

    Args:
        payload: The value that a cloud read returned.

    Returns:
        One dictionary for each record.
    """
    if isinstance(payload, list):  # The common shape of a list endpoint.
        return [entry for entry in payload if isinstance(entry, dict)]  # Drop an entry of another type.
    if isinstance(payload, dict):  # A paged endpoint wraps the list under one key.
        return as_records(payload.get("results"))  # One step down, and never a second one.
    return []  # An unexpected shape shows no record and raises nothing.


def org_refusal(chosen: str) -> tuple[Response, int] | None:
    """Return the refusal envelope when one organization fails a check.

    Why:
        The picker post and the site list run the same two checks: the request
        must name an organization, and the cloud session must reach it. One
        helper holds both checks, so the two routes cannot drift apart and the
        contract keeps one code for each refusal.

        The second check lives in `runtime.identity` and nowhere else. This
        module held a copy of that rule, of the `org_not_permitted` code, and of
        the refusal sentence. Two copies of one authorization rule drift apart,
        so the runtime layer is the one owner and this function asks it.

    Args:
        chosen: The organization identifier, or an empty value.

    Returns:
        The refusal envelope, or None when the organization passes both checks.
    """
    if not chosen:  # Neither the request body nor the session named an organization.
        return json_error(BAD_REQUEST_STATUS, ORG_NOT_CHOSEN, ORG_NOT_CHOSEN_MESSAGE)  # The contract fixes this.
    return identity.org_scope_refusal(chosen)  # One owner builds the 403 envelope, with one code and one sentence.


def permitted_orgs() -> list[dict[str, str]]:
    """Return one record for each organization that the cloud session may reach.

    Why:
        FR-012 asks for a picker, and a managed service provider account reaches
        many organizations. The picker needs a name beside each identifier, so
        this function reads both out of the cloud session privilege list.

    Returns:
        One record for each organization, sorted by name.
    """
    privileges = identity.session_privileges() or []  # A session with no privilege list shows an empty picker.
    found: dict[str, str] = {}  # One entry for each organization, so a repeated privilege counts once.
    for entry in privileges:  # One pass over the privilege list of this operator.
        add_org_entry(found, entry)  # The helper drops an entry that names no organization.
    ordered = sorted(found.items(), key=lambda pair: pair[1])  # The picker lists the organizations by name.
    return [{ORG_FIELD: key, "name": name} for key, name in ordered]  # One record for each picker row.


def add_org_entry(found: dict[str, str], entry: Any) -> None:
    """Add one privilege record to the organization index.

    Why:
        One operator often holds several privileges inside one organization. The
        index keeps the first name it meets, so the picker shows one row for
        each organization and never a repeated row.

    Args:
        found: The index to add to. The function edits this dictionary in place.
        entry: One entry of the cloud session privilege list.
    """
    org_id = identity.privilege_org_id(entry)  # A blank identifier means the entry names no organization.
    if not org_id:  # A site-scoped entry with no organization cannot fill a picker row.
        return  # Drop the entry and keep the rest.
    name = str(entry.get("name", org_id)) if isinstance(entry, dict) else org_id  # The identifier is the fallback.
    found.setdefault(org_id, name)  # The first name wins, so a repeated privilege adds no second row.


def org_display_name(org_id: str) -> str:
    """Return the readable name of one organization.

    Why:
        The site picker names the organization in its heading. The cloud session
        privilege list already carries that name, so the heading costs no extra
        cloud read.

    Args:
        org_id: The organization to name.

    Returns:
        The name, or the identifier when the privilege list carries no name.
    """
    for entry in permitted_orgs():  # The same list that fills the organization picker.
        if entry[ORG_FIELD] == org_id:  # The organization of this request.
            return entry["name"]  # The readable name of the heading.
    return org_id  # A privilege list with no name still fills the heading.


def resolve_org(org_id: str | None) -> str | None:
    """Return the organization that the current request acts on.

    Why:
        Two paths reach the site list. One carries the organization in the path
        and one holds it in the session. This function is the single point where
        that difference ends, so no handler below repeats the rule.

    Args:
        org_id: The identifier from the path, or None.

    Returns:
        The organization identifier, or None when neither source holds one.
    """
    if org_id:  # The path named the organization, so the path wins.
        return org_id  # An explicit value always beats a stored one.
    stored: Any = session.get(SELECTED_ORG_KEY)  # The pick that `choose_org` stored.
    return stored if isinstance(stored, str) and stored else None  # A damaged field reads as no pick.


def read_chosen_org() -> str:
    """Read the organization identifier out of the current request body.

    Why:
        The browser script posts a JSON body and a plain form post carries the
        same field. One reader accepts both, so the page works with the script
        and without it.

    Returns:
        The identifier, or an empty string when the body names none.
    """
    payload: Any = request.get_json(silent=True)  # A body that is not JSON reads as None, never a fault.
    if isinstance(payload, dict) and isinstance(payload.get(ORG_FIELD), str):  # The script path.
        return str(payload[ORG_FIELD]).strip()  # A stray space must not reach the session.
    return str(request.form.get(ORG_FIELD, "")).strip()  # The plain form path.


def store_chosen_org(org_id: str) -> None:
    """Record the chosen organization in the signed browser session.

    Why:
        Flask signs the session, so the browser cannot change the pick. The site
        list then needs no organization in its path, which is the shape that
        `contracts/http-api.md` names. A changed organization also drops the
        stored site, because a site never spans two organizations.

    Args:
        org_id: The organization identifier the operator picked.
    """
    if session.get(SELECTED_ORG_KEY) != org_id:  # A changed organization makes the stored site wrong.
        clear_chosen_site()  # The operator must not carry a site across an organization boundary.
    session[SELECTED_ORG_KEY] = org_id  # The signed session carries the pick to every later request.
    logger.info("select: the operator chose the organization %s", org_id)  # An identifier is not personal data.


def clear_chosen_site() -> None:
    """Drop any stored site pick from the signed browser session.

    Why:
        A site belongs to one organization. If the stored site outlived an
        organization change, a later route would read a site the operator may
        no longer reach. The ownership check would then refuse it as a fault
        rather than as a stale pick.
    """
    session.pop(SELECTED_SITE_KEY, None)  # A missing key is the normal case, so the default stays.


def store_chosen_site(site_id: str) -> None:
    """Record the chosen site in the signed browser session.

    Why:
        The capture and upgrade routes need the site the operator is working
        on. Only the ownership check knows the pick is safe, so the caller
        stores it after that check passes and never before.

    Args:
        site_id: The site identifier the operator opened.
    """
    session[SELECTED_SITE_KEY] = site_id  # The signed session carries the pick to every later request.


def wants_browser_page() -> bool:
    """Report whether the current request asks for a page instead of JSON.

    Why:
        One post serves two clients. The portal script sends `fetch` and reads
        a JSON body. A plain form post needs a new page, because a browser
        shows a JSON body as raw text. This function holds the single rule that
        separates the two, so every route of this module answers the same way.
        The script header wins over the `Accept` header, because a script
        inside a browser page inherits the header of that page.

    Returns:
        True when the request states a preference for an HTML page.
    """
    if request.headers.get(SCRIPT_HEADER, "") == SCRIPT_HEADER_VALUE:  # The script names itself.
        return False  # A script always reads JSON, whatever the page header states.
    preferred = request.accept_mimetypes.best_match((SCRIPT_MIME, BROWSER_MIME))  # None means no preference.
    return preferred == BROWSER_MIME  # Only a stated preference for HTML earns a page.


def next_page_answer() -> Response | tuple[Response, int]:
    """Answer one successful pick, as a page redirect or as a JSON body.

    Why:
        `wants_browser_page` holds the negotiation rule, and this function
        holds the two answers that follow from it. The route then reads as one
        line, and a later route that needs the same choice reuses this one.

    Returns:
        The redirect to the next page, or the next path as a JSON body.
    """
    if wants_browser_page():  # A browser form post cannot read a JSON body.
        return Response(status=REDIRECT_STATUS, headers={LOCATION_HEADER: NEXT_AFTER_ORG})  # The next page.
    return jsonify({"next": NEXT_AFTER_ORG}), OK_STATUS  # The script opens the site picker next.


def lock_reader() -> Callable[..., Any] | None:
    """Return the callable that reads the site lock holders.

    Why:
        The lock module arrives after this one, so the seam keeps the site
        picker working today and finds the real reader on the day it lands.

    Returns:
        The injected reader, the reader of the lock module, or None when neither
        exists yet.
    """
    injected = injected_seam(LOCK_READER_KEY)  # A contract test injects a stand-in here.
    if injected is not None:  # The injection wins, so no import runs at all.
        return injected  # The test then reaches no lock store.
    module = load_optional_module(LOCK_MODULE)  # None while the lock module is still building.
    return find_attribute(module, LOCK_READER_ATTRIBUTES)  # None until that module publishes a reader.


def read_site_locks(org_id: str, site_ids: list[str]) -> dict[str, str | None]:
    """Return the address of the operator that holds each site lock.

    Why:
        `contracts/site-lock.md` states that a read never needs the lock and that
        an unreachable store must not stop a read-only page. A failure below
        therefore answers an empty index and raises nothing.

    Args:
        org_id: The organization that owns the sites.
        site_ids: The sites to ask about.

    Returns:
        One entry for each site the lock store answered about, because
        `runtime/lock.py` answers one entry for each site it can reach. A None
        value means no lock exists. An absent entry means the state is unknown.
    """
    reader = lock_reader()  # None while the lock module is still building.
    if reader is None:  # The lock module is not built yet.
        return {}  # Every site then reads as unknown, because no lock store can answer.
    try:  # The lock store sits on a network and may not answer.
        return dict(reader(org_id, site_ids))  # The reader owns the Redis call and the key shape.
    except Exception:  # A read-only page must survive an unreachable lock store.
        logger.warning("select: the lock store did not answer, so every site shows an unknown state")  # No trace.
        return {}  # Continue, because viewing must not need Redis.


def site_lock_state(site_id: str, locks: dict[str, str | None]) -> str:
    """Name the lock state of one site.

    Why:
        A free site and a site that the portal could not read both answer None
        from the holder index, so the holder alone cannot tell them apart. An
        operator who reads free on an unreadable site may walk into a site that
        another operator holds. `contracts/site-lock.md:118` asks the page to
        mark that state unknown, so this function names three states, not two.

    Args:
        site_id: The site to name.
        locks: The holder of each site that the lock store answered about.

    Returns:
        One of `free`, `locked`, or `unknown`.
    """
    if site_id not in locks:  # The lock store answered nothing about this site.
        return LOCK_STATE_UNKNOWN  # The portal cannot tell, so it must not report free.
    return LOCK_STATE_LOCKED if locks[site_id] else LOCK_STATE_FREE  # An address names the holder.


def part_count(entry: dict[str, Any], field: str) -> int:
    """Read one whole-number field out of a site statistics record.

    Args:
        entry: The site statistics record.
        field: The field to read.

    Returns:
        The count, or zero when the field is absent or holds another type.
    """
    value: Any = entry.get(field)  # A cloud record may hold any type at all.
    return value if isinstance(value, int) else 0  # A missing count reads as zero, never as a fault.


def read_device_count(entry: dict[str, Any]) -> int:
    """Read the device count of one site statistics record.

    Why:
        The cloud reports one whole count for most sites. Where that field is
        absent, the sum of the three device type counts gives the same number.

    Args:
        entry: The site statistics record.

    Returns:
        The count of devices at that site.
    """
    whole: Any = entry.get(DEVICE_COUNT_FIELD)  # The field the cloud fills for most sites.
    if isinstance(whole, int):  # The cloud reported the whole count.
        return whole  # No sum needed.
    return sum(part_count(entry, field) for field in DEVICE_COUNT_PARTS)  # The fallback path.


def build_count_index(stats: list[dict[str, Any]]) -> dict[str, int]:
    """Build the device count of each site, keyed by the site identifier.

    Why:
        One organization-wide statistics call answers every row of the page. A
        call for each site would send one request for each row and would slow
        the picker of a large organization.

    Args:
        stats: The site statistics records.

    Returns:
        The device count of each site.
    """
    return {str(entry.get("id", "")): read_device_count(entry) for entry in stats}  # One pass over the records.


def build_site_row(site: dict[str, Any], counts: dict[str, int], locks: dict[str, str | None]) -> dict[str, Any]:
    """Build one row of the site list.

    Args:
        site: The site record from the cloud.
        counts: The device count of each site.
        locks: The address of the operator that holds each site lock.

    Returns:
        The five fields of one row. `contracts/http-api.md:77` names the first
        four. `lock_state` adds the third lock state that
        `contracts/site-lock.md:118` asks a read-only page to show.
    """
    site_id = str(site.get("id", ""))  # The row key, used by the count index and the lock index.
    return {
        "site_id": site_id,  # The identifier that the inventory path then carries.
        "name": str(site.get("name", "")),  # The text that the picker shows and that the filter reads.
        "device_count": counts.get(site_id, 0),  # An unknown site reads as zero devices.
        "locked_by": locks.get(site_id),  # None means no lock exists, which the contract states.
        "lock_state": site_lock_state(site_id, locks),  # `free`, `locked`, or `unknown`, and never a guess.
    }


def build_site_rows(org_id: str) -> list[dict[str, Any]]:
    """Build one row for each site of one organization.

    Why:
        Three reads fill one page: the site records, the device counts, and the
        lock holders. Each read answers for the whole organization, so the page
        costs three requests and never one request for each row.

    Args:
        org_id: The organization to read.

    Returns:
        One row for each site.
    """
    read = cloud_reader()  # One seam for both cloud reads.
    sites = as_records(read("listOrgSites", org_id=org_id))  # The name and the identifier of each site.
    counts = build_count_index(as_records(read("listOrgSiteStats", org_id=org_id)))  # The device count of each site.
    locks = read_site_locks(org_id, [str(site.get("id", "")) for site in sites])  # An absent entry reads unknown.
    return [build_site_row(site, counts, locks) for site in sites]  # One row for each site, in cloud order.


def apply_text_filter(rows: list[dict[str, Any]], needle: str) -> list[dict[str, Any]]:
    """Keep the rows whose name or identifier holds one text fragment.

    Why:
        FR-012 asks for a searchable list. The portal filters here, so a large
        organization sends one cloud read and then filters each keystroke with
        no second request.

    Args:
        rows: The rows to filter.
        needle: The text the operator typed. An empty value keeps every row.

    Returns:
        The rows that match.
    """
    text = needle.strip().casefold()  # One spelling, so a capital letter still matches.
    if not text:  # The operator typed nothing.
        return rows  # Keep every row.
    return [row for row in rows if row_matches(row, text)]  # One pass over the rows.


def row_matches(row: dict[str, Any], text: str) -> bool:
    """Report whether one row holds a text fragment in its name or identifier.

    Args:
        row: The row to test.
        text: The lower-case fragment the operator typed.

    Returns:
        True when the name or the identifier holds the fragment.
    """
    return text in str(row["name"]).casefold() or text in str(row["site_id"]).casefold()  # Either field matches.


def device_reader() -> Callable[..., Any] | None:
    """Return the callable that reads the device inventory of one site.

    Why:
        The device read work lives in its own module and arrives after this one.
        This seam keeps the route bound to its endpoint name today, and the route
        answers a plain fault until the device module lands.

    Returns:
        The injected reader, the reader of the device module, or None when
        neither exists yet.
    """
    injected = injected_seam(DEVICE_READER_KEY)  # A contract test injects a stand-in here.
    if injected is not None:  # The injection wins, so no import runs at all.
        return injected  # The test then reaches no cloud account.
    module = load_optional_module(DEVICES_MODULE)  # None while the device module is still building.
    return find_attribute(module, DEVICE_READER_ATTRIBUTES)  # None until that module publishes a reader.


def build_type_counts(devices: list[dict[str, Any]]) -> dict[str, int]:
    """Count the devices of each type, and the whole list.

    Why:
        FR-013 offers the operator a device type filter with three values, so the
        page needs a count for each of the three. The whole count travels beside
        them, because the page shows it above the filter.

    Args:
        devices: The device records of one site.

    Returns:
        One count for each device type, and the whole count.
    """
    counts = dict.fromkeys(TYPE_COUNT_FIELDS.values(), 0)  # Every type appears, even a type with no device.
    for device in devices:  # One pass over the device records.
        kind = str(device.get("type", "")).casefold()  # The cloud writes the type in lower case already.
        field = TYPE_COUNT_FIELDS.get(kind)  # A type outside the three named types adds no key of its own.
        if field is not None:  # The record names one of the three types.
            counts[field] += 1  # One more device of this type.
    counts[TOTAL_FIELD] = len(devices)  # The whole count, which no type filter changes.
    return counts  # The page reads each entry by name.


def read_inventory(org_id: str, site_id: str) -> dict[str, Any] | None:
    """Read the device list and the device counts of one site.

    Why:
        The device module owns every device read, including the physical view
        and the device type parameter of the statistics call. This function asks
        that module and shapes the answer for the contract.

    Args:
        org_id: The organization that owns the site.
        site_id: The site to read.

    Returns:
        The device list and the counts, or None when the device module is not
        built yet.
    """
    reader = device_reader()  # None while the device module is still building.
    if reader is None:  # The portal cannot answer this read at all.
        logger.error("select: the device module is not built, so the read cannot run")  # The caller answers.
        return None  # The caller answers the plain fault envelope.
    devices = as_records(reader(org_id=org_id, site_id=site_id))  # The device module owns every call parameter.
    return {"devices": devices, "counts": build_type_counts(devices)}  # The shape the contract names.


def inventory_parts(org_id: str, site_id: str) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Return the device list and the device counts of one site for a page.

    Why:
        The inventory page must render even while the device module is still
        building. This reader turns a missing module into an empty table and an
        empty count index, so the page never raises and never shows a fault.

    Args:
        org_id: The organization that owns the site.
        site_id: The site to read.

    Returns:
        The device records, and the count of each device type.
    """
    inventory = read_inventory(org_id, site_id)  # None means the device module is not built yet.
    if inventory is None:  # A missing module still renders the empty table.
        return [], {}  # The page shows its own fallback for a missing count.
    devices: list[dict[str, Any]] = inventory["devices"]  # The records that the device table reads.
    counts: dict[str, int] = inventory["counts"]  # One count for each device type, and the whole count.
    return devices, counts  # The page reads both by name.


def find_site(site_id: str, org_id: str) -> dict[str, Any] | None:
    """Return the record of one site of one organization.

    Why:
        The inventory page needs the site name, and every inventory path needs
        the scope check. Both answers come out of the same list, so one cloud
        read serves both. Two separate helpers would read the same list twice
        for one page.

    Args:
        site_id: The site the request named.
        org_id: The organization of the current session.

    Returns:
        The site record, or None when the organization holds no such site.
    """
    sites = as_records(cloud_reader()("listOrgSites", org_id=org_id))  # The site records of this organization.
    for site in sites:  # One pass, because the first match ends the search.
        if str(site.get("id", "")) == site_id:  # The one site the request named.
            return site  # The caller reads the name out of this record.
    return None  # The organization holds no such site.


def site_belongs_to_org(site_id: str, org_id: str) -> bool:
    """Report whether one site sits inside one organization.

    Why:
        A stale link and a hand-typed path both reach this route. The check runs
        before any device read, so an operator cannot read a site of another
        organization through a guessed identifier.

    Args:
        site_id: The site the request named.
        org_id: The organization of the current session.

    Returns:
        True when the organization holds that site.
    """
    return find_site(site_id, org_id) is not None  # The record itself is the proof.


def render_page(name: str, **context: Any) -> str:
    """Render one picker page, and fall back while a template is still missing.

    Why:
        The picker templates belong to another work stream and arrive after this
        module. Without the fallback each picker path would answer a fault today.
        The fallback shows the portal shell instead, so the operator sees a page
        and the log names the missing template.

    Args:
        name: The template to render.
        **context: The values the template reads.

    Returns:
        The rendered page.
    """
    try:  # The template arrives in a later stage of this phase.
        return render_template(name, **context)  # The normal path once the template lands.
    except TemplateNotFound:  # Expected while the portal grows, so this is not a fault.
        logger.warning("select: the template %s is not built yet, so the shell page answered", name)  # No trace.
        return render_template(FALLBACK_TEMPLATE, **context)  # The shell page always exists.


@dataclass(frozen=True, slots=True)
class OrgPickerView:
    """One page of the organization picker, as the template shows it.

    Why:
        `contracts/http-api.md:53` asks the picker to page and to filter inside
        the portal. Both steps are rules, and a rule inside a template needs a
        browser to test it. This record carries the settled answer of each rule,
        so the page prints a value and never compares a number.

    Attributes:
        rows: The organization records of this page.
        total: The number of organizations that the filter kept.
        page_size: The number of rows one page holds.
        offset: The number of rows that the earlier pages hold.
        query: The text that the operator filtered by. Empty when none.
        has_next: True when a later page exists.
        has_previous: True when an earlier page exists.
        next_url: The path of the later page. Empty when no later page exists.
        previous_url: The path of the earlier page. Empty when none exists.
    """

    rows: tuple[dict[str, str], ...] = ()  # The rows of this page alone.
    total: int = 0  # The count after the filter, which the paging counts against.
    page_size: int = ORG_PAGE_SIZE  # The page holds this many rows at most.
    offset: int = 0  # The first row of this page, counted from zero.
    query: str = ""  # The filter text, which also picks the sentence an empty page shows.
    has_next: bool = False  # Enables the later-page control.
    has_previous: bool = False  # Enables the earlier-page control.
    next_url: str = ""  # The href of the later-page control.
    previous_url: str = ""  # The href of the earlier-page control.


def org_row_matches(row: dict[str, str], text: str) -> bool:
    """Report whether one organization row holds a text fragment.

    Why:
        `row_matches` reads `site_id`, so it cannot test an organization row.
        This function reads the two fields that the picker shows, and an
        operator may filter by either the name or the identifier.

    Args:
        row: The organization row to test.
        text: The lower-case fragment that the operator typed.

    Returns:
        True when the name or the identifier holds the fragment.
    """
    name = str(row.get("name", "")).casefold()  # One spelling, so a capital letter still matches.
    return text in name or text in str(row.get(ORG_FIELD, "")).casefold()  # Either field matches.


def filter_org_rows(rows: list[dict[str, str]], needle: str) -> list[dict[str, str]]:
    """Keep the organization rows whose name or identifier holds one fragment.

    Why:
        `contracts/http-api.md:53` asks the picker to filter inside the portal.
        The filter runs before the paging, so a match on a later page still
        reaches the operator. A filter that ran after the paging would search
        one page and would hide every other match.

    Args:
        rows: The organization rows to filter.
        needle: The text the operator typed. An empty value keeps every row.

    Returns:
        The rows that match.
    """
    text = needle.strip().casefold()  # One spelling, so a capital letter still matches.
    if not text:  # The operator typed nothing.
        return rows  # Keep every row.
    return [row for row in rows if org_row_matches(row, text)]  # One pass over the rows.


def read_whole_number(field: str, fallback: int) -> int:
    """Read one whole number out of the query string of the current request.

    Why:
        A paging link is a path, so an operator may edit it by hand. A value
        that is not a number, or a value below zero, must read as the fallback
        instead of reaching the slice and showing a page from the wrong end.

    Args:
        field: The query argument to read.
        fallback: The value to return when the argument is absent or damaged.

    Returns:
        The value, which is never below zero.
    """
    raw = request.args.get(field, "").strip()  # An absent argument reads as an empty string.
    if not raw.lstrip("+").isdigit():  # A sign, a fraction, or a word is not a row count.
        return fallback  # The damaged link falls back, and the page still renders.
    return int(raw)  # The text holds digits alone, so the value is not below zero.


def org_page_url(offset: int, needle: str) -> str:
    """Build the path of one page of the organization picker.

    Why:
        A paging link must carry the filter. A link that dropped it would widen
        the list on the second page, and the operator would read that as a
        filter that stopped working.

    Args:
        offset: The number of rows that the earlier pages hold.
        needle: The text that the operator filtered by.

    Returns:
        The path of that page, with its query arguments.
    """
    query: dict[str, str] = {OFFSET_FIELD: str(max(offset, 0))}  # Never ask for a row before the first one.
    if needle:  # An empty filter adds no argument, so the plain path stays short.
        query[FILTER_FIELD] = needle  # `urlencode` escapes a space and a special character.
    return f"{ORG_PAGE_PATH}?{urlencode(query)}"  # The one path that `contracts/http-api.md:50` fixes.


def build_org_view(rows: list[dict[str, str]], offset: int, needle: str) -> OrgPickerView:
    """Build the view model of one page of the organization picker.

    Why:
        FR-011 asks for a picker of every organization that a provider login may
        reach, and `contracts/http-api.md:53` asks that picker to page and to
        filter inside the portal. The filter runs first and the slice runs
        second, so a match on a later page still reaches the operator.

    Args:
        rows: Every organization that the cloud session may reach.
        offset: The number of rows that the earlier pages hold.
        needle: The text that the operator filtered by.

    Returns:
        The view model of that page.
    """
    kept = filter_org_rows(rows, needle)  # The filter runs first, so the paging walks the matches alone.
    total = len(kept)  # The count after the filter, which both controls count against.
    start = min(max(offset, 0), total)  # A link past the end shows an empty page, never a page from the far end.
    page = tuple(kept[start : start + ORG_PAGE_SIZE])  # The rows of this page alone.
    return build_org_page_view(page, start, total, needle)  # The second half holds the field list.


def build_org_page_view(page: tuple[dict[str, str], ...], start: int, total: int, needle: str) -> OrgPickerView:
    """Build the picker view model out of one page that `build_org_view` cut.

    Args:
        page: The rows of this page.
        start: The clamped offset of this page.
        total: The number of rows that the filter kept.
        needle: The text that the operator filtered by.

    Returns:
        The view model, with the state of each control settled.
    """
    seen = start + len(page)  # The rows of this page and of every earlier page.
    return OrgPickerView(  # `page_size` keeps its default, which is `ORG_PAGE_SIZE`.
        rows=page,  # The template walks these rows and no others.
        total=total,  # The note beside the table prints this count.
        offset=start,  # The clamped value, so the note matches the rows on screen.
        query=needle,  # The field shows the filter that produced this page.
        has_next=seen < total,  # A later page exists when the walk has not reached the end.
        has_previous=start > 0,  # An earlier page exists when this page starts past the first row.
        next_url=org_page_url(seen, needle) if seen < total else "",  # An absent page carries no path.
        previous_url=org_page_url(start - ORG_PAGE_SIZE, needle) if start else "",  # The clamp guards the floor.
    )


@select_bp.get(ORG_PAGE_PATH)
@identity.require_session
def org_page() -> str:
    """Show the organization picker.

    Why:
        FR-011 starts the journey here. A managed service provider account
        reaches many organizations, so the page lists every organization that
        the cloud session may act on. `contracts/http-api.md:53` asks that list
        to page and to filter inside the portal, so a long list arrives one page
        at a time and each filter costs no cloud read.

        The filter runs here and not in the browser alone. The browser script
        hides a row of the page on screen, so a browser filter with no portal
        filter would search one page and would hide every match that sits on a
        later page.

    Returns:
        The rendered picker page.
    """
    needle = request.args.get(FILTER_FIELD, "").strip()  # An absent argument reads as no filter.
    offset = read_whole_number(OFFSET_FIELD, 0)  # A damaged link reads as the first page.
    view = build_org_view(permitted_orgs(), offset, needle)  # The builder settles the filter and the paging.
    return render_page(ORG_TEMPLATE, organizations=view.rows, org_view=view)  # The page prints settled values.


@select_bp.post(ORG_PAGE_PATH)
@identity.require_session
def choose_org() -> Response | tuple[Response, int]:
    """Store the organization that the operator picked.

    Why:
        Every later read holds the organization in the signed session, so the
        scope check runs at the one point where the pick enters the session.

        One post serves two clients, so `wants_browser_page` holds the rule: a
        request earns a page only when its `Accept` header prefers `text/html`
        and no `X-Requested-With: XMLHttpRequest` header marks a script. A page
        request reads a 303 redirect to the path that `contracts/http-api.md`
        names next, and every other post reads the `{"next": ...}` body of that
        same contract. A refusal keeps the JSON envelope for both clients,
        because the contract fixes one error shape for every caller.

    Returns:
        The redirect, the next path as JSON, or the refusal envelope.
    """
    chosen = read_chosen_org()  # An empty value means the body named no organization.
    refusal = org_refusal(chosen)  # None means the pick passed both checks.
    if refusal is not None:  # The body named no organization, or named one out of scope.
        return refusal  # The contract fixes the code of both refusals.
    store_chosen_org(chosen)  # The signed session carries the pick to every later request.
    return next_page_answer()  # The rule above chooses the redirect or the JSON body.


@select_bp.get(SITE_PAGE_PATH)
@identity.require_session
def sites_page() -> str:
    """Show the site picker for the chosen organization.

    Why:
        FR-014 binds one run to one site, so the operator picks the site before
        any capture starts. The page carries its rows already, so the operator
        reads the list without a second request. An earlier version passed the
        organization alone, so the table rendered empty every time.

    Returns:
        The rendered picker page.
    """
    chosen = resolve_org(None)  # None means the operator has picked no organization yet.
    if chosen is None:  # The picker cannot list a site without an organization.
        return render_page(SITE_TEMPLATE, sites=[], org_id="", org_name="")  # An empty table, and no fault.
    rows = apply_text_filter(build_site_rows(chosen), request.args.get(FILTER_FIELD, ""))  # The optional filter.
    name = org_display_name(chosen)  # The heading names the organization, not only its identifier.
    return render_page(SITE_TEMPLATE, sites=rows, org_id=chosen, org_name=name)  # The picker page itself.


@select_bp.get(SITE_INVENTORY_PAGE_PATH)
@identity.require_session
def site_inventory_page(site_id: str) -> tuple[str, int]:
    """Show the device list of one site as a page.

    Why:
        FR-013 asks the operator to read the inventory before any capture
        starts, and this route serves the page even when no script runs.

    Args:
        site_id: The site the path named.

    Returns:
        The rendered page and its status.
    """
    org_id = resolve_org(None) or ""  # An empty value means the operator has picked no organization.
    site = find_site(site_id, org_id) if org_id else None  # None means no pick, or another organization.
    if site is None:  # The operator may not read this site through this path.
        logger.info("select: the site %s is outside the chosen organization", site_id)  # The picker answers.
        return render_page(SITE_TEMPLATE, sites=[], org_id=org_id, org_name=""), NOT_FOUND_STATUS  # No row.
    store_chosen_site(site_id)  # The ownership check passed, so the pick is safe to store.
    devices, counts = inventory_parts(org_id, site_id)  # An empty pair means the device module is missing.
    name = str(site.get("name", site_id))  # The identifier fills the heading when the record carries no name.
    return (  # The device table of one site, with its own status.
        render_page(INVENTORY_TEMPLATE, site_id=site_id, site_name=name, devices=devices, counts=counts),
        OK_STATUS,
    )


@select_bp.get(SITES_API_PATH)
@select_bp.get(ORG_SITES_API_PATH)
@identity.require_session
def list_sites(org_id: str | None = None) -> tuple[Response, int]:
    """List the sites of one organization, with the device count and the lock state.

    Why:
        Two documents name two paths for this one list. `contracts/http-api.md`
        holds the organization in the session, and `tasks.md` holds it in the
        path. `resolve_org` is the one point where that difference ends.

        Reading this list never needs the site lock. The lock state travels as a
        plain field, so the page shows a busy site without taking it.

    Args:
        org_id: The organization from the path. The session supplies the value
            when the path carries none.

    Returns:
        The site rows, or the refusal envelope.
    """
    chosen = resolve_org(org_id) or ""  # An empty value means neither source named an organization.
    refusal = org_refusal(chosen)  # None means the organization passed both checks.
    if refusal is not None:  # One check refused, so the contract fixes the answer.
        return refusal  # The refusal envelope, already shaped.
    rows = apply_text_filter(build_site_rows(chosen), request.args.get(FILTER_FIELD, ""))  # The optional filter.
    return jsonify({"sites": rows}), OK_STATUS  # The one shape the contract names.


@select_bp.get(INVENTORY_API_PATH)
@identity.require_session
def site_inventory(site_id: str) -> tuple[Response, int]:
    """List the devices of one site, with a count for each device type.

    Why:
        The operator reads the inventory before the capture starts, so the page
        shows what the run will act on. The site check runs before the device
        read, so a site of another organization answers `site_not_found` and
        never a device record.

    Args:
        site_id: The site the path named.

    Returns:
        The device list and the counts, or the refusal envelope.
    """
    org_id = resolve_org(None)  # The inventory path carries no organization, so the session answers.
    if org_id is None or not site_belongs_to_org(site_id, org_id):  # No pick, or a site of another organization.
        return json_error(NOT_FOUND_STATUS, SITE_NOT_FOUND, SITE_NOT_FOUND_MESSAGE)  # The contract fixes this.
    store_chosen_site(site_id)  # The ownership check passed, so the pick is safe to store.
    inventory = read_inventory(org_id, site_id)  # None means the device module is not built yet.
    if inventory is None:  # A part of the portal is missing, so the read cannot run.
        return json_error(SERVER_ERROR_STATUS)  # The plain fault envelope, with no detail for the caller.
    return jsonify(inventory), OK_STATUS  # The one shape the contract names.


# --------------------------------------------------------------------------
# The site lock. FR-072 to FR-083, and `contracts/site-lock.md`.
# --------------------------------------------------------------------------

LOCK_CLIENT_KEY = "LOCK_STORE_CLIENT"  # A contract test injects a stand-in store here and needs no Redis server.
LOCK_RECORDS_KEY = "site_lock_records"  # The signed session holds one lock record for each site this browser took.

TOKEN_FIELD = "lock_token"  # nosec B105  # WHY: `contracts/http-api.md` names this body field. It holds no token.
CONFIRM_FIELD = "confirm"  # The body field that carries the word the operator typed.
RUN_FIELD = "run_id"  # The run the lock protects. An empty value means the operator took the site before the run.

LOCK_FAILED_CODE = "site_lock_failed"  # The base code, used when a later error class carries no code of its own.
SITE_LOCKED_CODE = "site_locked"  # `contracts/site-lock.md:58` fixes this code and the 409 status.
LOCK_LOST_CODE = "lock_lost"  # `contracts/site-lock.md:82` and line 95 fix this code and the 409 status.
CONFIRMATION_REQUIRED_CODE = "confirmation_required"  # `contracts/site-lock.md:59` fixes this code and the 400.
LOCK_STORE_DOWN_CODE = "lock_store_unreachable"  # `contracts/site-lock.md:116` answers 503 and forbids a fallback.

LOCK_LOST_MESSAGE = "This session no longer holds the site. Take the site again before you continue."  # The cure.

# `contracts/site-lock.md` fixes one status for each code. The map holds that
# rule once, so no handler below repeats it and no two handlers disagree.
LOCK_ERROR_STATUS = {
    SITE_LOCKED_CODE: CONFLICT_STATUS,  # Another operator is active on the site right now.
    LOCK_LOST_CODE: CONFLICT_STATUS,  # The token this caller named is no longer the stored one.
    CONFIRMATION_REQUIRED_CODE: BAD_REQUEST_STATUS,  # The operator must type a word first.
    LOCK_STORE_DOWN_CODE: UNAVAILABLE_STATUS,  # The store did not answer, and a write fails closed.
    LOCK_FAILED_CODE: CONFLICT_STATUS,  # An unnamed lock failure still refuses the write.
}


def lock_body() -> dict[str, Any]:
    """Read the body of the current lock request as a dictionary.

    Why:
        The portal script posts JSON and a plain form post carries the same
        fields. A body of another shape reads as an empty body, so a handler
        answers its own refusal and never a fault page.

    Returns:
        The body fields, or an empty dictionary.
    """
    payload: Any = request.get_json(silent=True)  # A body that is not JSON reads as None, never a fault.
    if isinstance(payload, dict):  # The browser script path.
        return payload  # The fields arrive as the script sent them.
    return dict(request.form)  # The plain form path, and an empty dictionary for an empty body.


def lock_client() -> Any:
    """Return the store client that every lock call of this module uses.

    Why:
        A contract test injects a stand-in store here, so the test drives the
        real acquire rule, the real compare-and-extend, and the real
        compare-and-delete with no Redis server. An unset key answers None, and
        `runtime.lock` then opens the shared client of the worker.

    Returns:
        The injected store client, or None.
    """
    return current_app.config.get(LOCK_CLIENT_KEY)  # An unset key reads as None, which the lock module accepts.


def build_lock_request(org_id: str, site_id: str) -> lock.LockRequest | None:
    """Build the lock request of the current caller.

    Why:
        FR-073 pairs the work email address with the browser identity, so one
        operator may hold several sites in several tabs at one time. The pair
        comes from the session guard and never from the request body, because a
        body value would let a caller name another operator.

    Args:
        org_id: The organization of the current session.
        site_id: The site the path named.

    Returns:
        The request, or None when the session carries no owner.
    """
    owner = identity.current_owner()  # The session guard already refused an unsigned request.
    if owner is None:  # No owner means no identity to grant a site to.
        return None  # The caller answers the 401 envelope.
    body = lock_body()  # One read of the body, shared by both fields below.
    return lock.LockRequest(
        org_id=org_id,  # The organization half of the Redis key.
        site_id=site_id,  # The site half of the same key.
        owner=owner,  # FR-073 pairs the address with the browser.
        run_id=str(body.get(RUN_FIELD, "")),  # An empty value means no run exists yet.
        confirmation_text=str(body.get(CONFIRM_FIELD, "")),  # FR-079 fixes the letter case, so nothing changes here.
    )


def holder_details(site_id: str) -> dict[str, Any]:
    """Describe the operator that holds one site, for a refusal body.

    Why:
        `contracts/http-api.md:103` asks a `site_locked` refusal to carry the
        address of the holder and the seconds left of the cooldown. The page
        shows both, so the waiting operator reads who holds the site and how
        long the wait lasts before a takeover becomes possible.

    Args:
        site_id: The site the path named.

    Returns:
        The address of the holder and the seconds left of the cooldown.
    """
    org_id = resolve_org(None) or ""  # The refusal names the same organization the request acted on.
    held = lock.read_lock(org_id, site_id, client=lock_client())  # A read never raises, so a dead store answers None.
    if held is None:  # The lock expired between the refusal and this read.
        return {"actor_email": None, "cooldown_remaining": 0}  # No holder, and no wait left.
    remaining = lock.COOLDOWN_SECONDS - held.age_seconds()  # The seconds before the holder counts as quiet.
    return {"actor_email": held.owner.actor_email, "cooldown_remaining": max(0, int(remaining))}  # Never below zero.


def lock_failure_details(site_id: str, code: str, error: Exception) -> dict[str, Any] | None:
    """Build the detail block of one lock refusal.

    Why:
        Two refusals need a detail block and the rest need none. A refused
        takeover must name the exact word, because FR-079 asks for `CONFIRM`
        and FR-080 asks for `continue`. A page that shows one word for both
        cases teaches the returning operator to type the wrong text.

    Args:
        site_id: The site the path named.
        code: The machine code of the refusal.
        error: The failure the lock module raised.

    Returns:
        The detail block, or None when the refusal needs none.
    """
    if code == CONFIRMATION_REQUIRED_CODE:  # The operator must type a word before the portal moves the lock.
        return {"needed_text": str(getattr(error, "needed_text", ""))}  # The page prints this exact word.
    if code == SITE_LOCKED_CODE:  # Another operator is active on the site.
        return holder_details(site_id)  # The address of the holder and the seconds left of the cooldown.
    return None  # Every other refusal carries the code and the sentence alone.


def lock_failure_answer(site_id: str, error: lock.SiteLockError) -> tuple[Response, int]:
    """Turn one lock failure into the refusal the contract fixes.

    Why:
        Every failure class of `runtime.lock` carries its own machine code, so
        one handler maps every failure and no route repeats the mapping. The
        sentence comes from the failure itself, which keeps the operator text
        beside the rule that raised it.

    Args:
        site_id: The site the path named.
        error: The failure the lock module raised.

    Returns:
        The refusal envelope and its status.
    """
    code = str(getattr(error, "code", LOCK_FAILED_CODE))  # Every class of the lock module names its own code.
    status = LOCK_ERROR_STATUS.get(code, CONFLICT_STATUS)  # An unmapped code still refuses the write.
    details = lock_failure_details(site_id, code, error)  # None for a refusal that needs no detail block.
    return jsonify(build_error_envelope(code, str(error), details)), status  # The one error shape of the contract.


def lock_lost_answer() -> tuple[Response, int]:
    """Refuse a beat or a release that names a lock this session no longer holds.

    Why:
        The session copy of the record is the first check, and the compare
        inside the store is the second. Both answer one code, so the page shows
        one sentence whichever check refused.

    Returns:
        The refusal envelope and the 409 status.
    """
    body = build_error_envelope(LOCK_LOST_CODE, LOCK_LOST_MESSAGE)  # No detail block, because no cure needs one.
    return jsonify(body), CONFLICT_STATUS  # `contracts/site-lock.md:82` and line 95 fix this status.


def stored_lock_records() -> dict[str, Any]:
    """Return the lock records the signed session holds, keyed by site.

    Why:
        FR-074 lets one session owner hold several sites at one time, so the
        session holds an index and never one record. A damaged field reads as
        an empty index, so a hand-edited cookie loses a lock instead of raising.

    Returns:
        One stored record for each site this browser took.
    """
    stored: Any = session.get(LOCK_RECORDS_KEY)  # An absent key reads as None.
    return stored if isinstance(stored, dict) else {}  # A field of another type states that this browser holds none.


def store_lock_record(site_id: str, record: lock.LockRecord) -> None:
    """Record one granted lock in the signed browser session.

    Why:
        A beat and a release both need the whole record, because the store
        keeps `run_id` and `acquired_at` across a beat. The browser sends the
        token alone, so the session holds the rest. Flask signs the session, so
        the browser cannot edit a stored record into another operator.

    Args:
        site_id: The site the lock covers.
        record: The record the store now holds.
    """
    records = stored_lock_records()  # The sites this browser already holds.
    records[site_id] = record.to_json()  # One JSON text for each site, which the reader below decodes.
    session[LOCK_RECORDS_KEY] = records  # The signed session carries the index to every later request.


def drop_lock_record(site_id: str) -> None:
    """Forget the stored lock record of one site.

    Args:
        site_id: The site the session no longer holds.
    """
    records = stored_lock_records()  # The sites this browser still holds.
    records.pop(site_id, None)  # A missing entry is the normal case after a lost lock, so the default stays.
    session[LOCK_RECORDS_KEY] = records  # The signed session carries the shortened index onward.


def held_record(site_id: str) -> lock.LockRecord | None:
    """Return the record this session holds for one site, when the token agrees.

    Why:
        `contracts/http-api.md` section 3 asks the caller to send the token
        with a beat and with a release. The check here refuses a token that
        does not match the session copy, so a caller cannot beat a lock that
        another tab of the same browser holds.

    Args:
        site_id: The site the path named.

    Returns:
        The record, or None when this session holds no matching lock.
    """
    stored = stored_lock_records().get(site_id)  # None means this browser took no lock on that site.
    record = lock.LockRecord.from_json(str(stored)) if isinstance(stored, str) else None  # Damaged text reads None.
    if record is None:  # No stored record, or a record the reader could not decode.
        return None  # The caller answers `lock_lost`.
    token = str(lock_body().get(TOKEN_FIELD, ""))  # The token the caller sent back.
    return record if token == record.lock_token else None  # A token that differs matches no lock this session holds.


def session_lock_record(site_id: str) -> lock.LockRecord | None:
    """Return the lock record that this browser stored for one site.

    Why:
        `held_record` answers the same question for a write, and it also
        compares the token in the request body. A page render carries no body,
        so a page needs this reader instead. The read never raises, because a
        damaged session field must cost the page nothing.

    Args:
        site_id: The site the page acts on.

    Returns:
        The stored record, or None when this browser holds no usable record.
    """
    try:  # The session read needs a request, and a damaged field must not hide a page.
        stored = stored_lock_records().get(site_id)  # None means this browser took no lock on that site.
    except Exception:  # A page render must survive every fault of the session layer.
        logger.warning("select: the session held no readable lock index, so site %s reads as unknown", site_id)
        return None  # The banner then falls back to the state that the lock store reports.
    if not isinstance(stored, str):  # A value of another type states that this browser holds no lock.
        return None  # The banner then falls back to the state that the lock store reports.
    return lock.LockRecord.from_json(stored)  # Damaged text reads as None and raises nothing.


def lock_cooldown_seconds(org_id: str, site_id: str) -> int:
    """Return the seconds left before a takeover of one site becomes possible.

    Why:
        FR-078 gives an abandoned session a 5 minute cooldown, and the waiting
        operator needs to watch that wait shrink. `holder_details` answers the
        same number inside a refusal body, so the banner and the refusal never
        disagree about one site.

    Args:
        org_id: The organization that owns the site.
        site_id: The site the page acts on.

    Returns:
        The whole seconds that remain, and zero when the portal knows no holder.
    """
    try:  # `contracts/site-lock.md:118` says a read never needs the lock store.
        held = lock.read_lock(org_id, site_id, client=lock_client())  # None for a free site or a dead store.
    except Exception:  # A page render must survive a store that answers nothing.
        logger.warning("select: the lock store did not answer the cooldown of site %s", site_id)  # No trace.
        return 0  # A wait the portal cannot measure reads as no wait at all.
    if held is None:  # No holder, so no operator waits for anything.
        return 0  # The banner hides the cooldown line on this value.
    return max(0, round(lock.COOLDOWN_SECONDS - held.age_seconds()))  # The value never falls below zero.


def takeover_word(holder: str) -> str:
    """Name the word that a takeover of one site needs first.

    Why:
        FR-079 asks a different operator to type `CONFIRM`, because a takeover
        erases the in-flight data of the operator that left. FR-080 asks the
        same operator, who returns to an abandoned session of their own, to type
        `continue` instead. This answer is the first guess alone. The server
        names the needed word again on a `confirmation_required` refusal.

    Args:
        holder: The work email address of the operator that holds the site.

    Returns:
        The resume word for the current operator, and the takeover word for
        every other operator.
    """
    try:  # The identity read needs a request, and a page must render without one.
        owner = identity.current_owner()  # None when the request carries no valid session.
    except Exception:  # A fault of the session layer means no match, which is the safe answer.
        owner = None  # The page then shows the word that FR-079 fixes.
    address = owner.actor_email if owner is not None else ""  # An empty address matches no holder.
    if not address or not holder:  # One empty half cannot prove that the two operators are one person.
        return lock.TAKEOVER_CONFIRMATION_TEXT  # FR-079 fixes this word for every other operator.
    try:  # `normalize_email` refuses a malformed address, and the lock store may hold one.
        same_person = identity.normalize_email(address) == identity.normalize_email(holder)  # One spelling.
    except ValueError:  # A malformed address proves no match, so the stricter word stands.
        return lock.TAKEOVER_CONFIRMATION_TEXT  # FR-079 fixes this word for every other operator.
    if same_person:  # The operator returns to a quiet session of their own.
        return lock.RESUME_CONFIRMATION_TEXT  # FR-080 asks the returning operator for the lighter word.
    return lock.TAKEOVER_CONFIRMATION_TEXT  # FR-079 fixes this word for every other operator.


def lock_banner_context(org_id: str, site_id: str) -> dict[str, Any]:
    """Build the six values that the site lock banner of one page reads.

    Why:
        Three pages write to a site: the capture page, the options page, and the
        run page. All three show one banner, so one builder must answer for all
        three. A second copy of these rules inside a route would let two pages
        disagree about who holds one site.

        `site_lock_state` reports `free`, `locked`, and `unknown` alone. It reads
        the lock store, and the store names one address for each site. It cannot
        report `held`, because several browsers of one operator share that
        address. The signed session of this browser holds the token, so this
        builder reads the session first and the store second.

        `contracts/site-lock.md:118` states that a read never needs the lock
        store. Every store read below therefore fails open, and a store that
        answers nothing renders the banner in the `unknown` state.

    Args:
        org_id: The organization that owns the site. An empty value reads as
            `unknown`, because the lock key needs both halves.
        site_id: The site the page acts on.

    Returns:
        The six values that `partials/lock_banner.html` names in its header.
    """
    held = session_lock_record(site_id)  # None means this browser stored no lock for the site.
    if held is not None and held.lock_token:  # A stored token is the one proof that this browser holds the site.
        holder = held.owner.actor_email  # The banner may show this address, and no log line may hold it.
        return build_lock_banner(site_id, LOCK_STATE_HELD, holder, 0, held.lock_token)  # No wait for the holder.
    try:  # `read_site_locks` absorbs a dead store, and the seam lookup itself may still fail.
        locks = read_site_locks(org_id, [site_id]) if org_id else {}  # No organization means no readable key.
    except Exception:  # A page render must survive every fault of the lock seam.
        logger.warning("select: the lock seam did not answer, so site %s reads as unknown", site_id)  # No trace.
        locks = {}  # An empty index marks the state unknown, which is what the contract asks for.
    state = site_lock_state(site_id, locks)  # One of `free`, `locked`, or `unknown`.
    holder = str(locks.get(site_id) or "")  # Empty for a free site and for a site the portal cannot read.
    wait = lock_cooldown_seconds(org_id, site_id) if state == LOCK_STATE_LOCKED else 0  # Only a holder makes a wait.
    return build_lock_banner(site_id, state, holder, wait, "")  # This browser holds no token on this path.


def build_lock_banner(site_id: str, state: str, holder: str, cooldown: int, token: str) -> dict[str, Any]:
    """Shape the six banner values into the names that the partial reads.

    Why:
        `partials/lock_banner.html` fixes six variable names in its own header.
        One builder holds those names, so `lock_banner_context` states each rule
        once and no route spells a name a second way.

    Args:
        site_id: The site the banner covers.
        state: One of `free`, `locked`, `held`, or `unknown`.
        holder: The work email address of the holder. Empty when none is known.
        cooldown: The seconds left before a takeover becomes possible.
        token: The lock token this browser holds. Empty when it holds none.

    Returns:
        The template context of the banner.
    """
    return {
        "site_id": site_id,  # The three lock calls of `portal.js` build their path from this value.
        "lock_state": state,  # The banner writes one sentence for each state.
        "lock_holder": holder,  # The waiting operator reads this address and knows whom to ask.
        "lock_cooldown": cooldown,  # Zero hides the cooldown line of the banner.
        "lock_token": token,  # An empty value stops the heartbeat before it starts.
        "lock_confirm_word": takeover_word(holder),  # The first guess, which a refusal may replace.
    }


def lock_grant_body(grant: lock.LockGrant) -> dict[str, Any]:
    """Shape the answer of one granted lock.

    Why:
        `contracts/http-api.md:99` names the token and the remaining life.
        `contracts/site-lock.md:57` adds the state, so the page can tell a
        fresh acquisition from a resumed run and from a takeover.

    Args:
        grant: The grant the lock module answered.

    Returns:
        The three fields of a granted lock.
    """
    return {
        "lock_token": grant.record.lock_token,  # The browser sends this value back with every beat.
        "expires_in": grant.expires_in,  # The seconds the lock lives without a beat.
        "state": grant.state.value,  # One of `acquired`, `resume`, or `takeover`.
    }


@select_bp.post(LOCK_API_PATH)
@identity.require_session
def take_site_lock(site_id: str) -> tuple[Response, int]:
    """Take the lock on one site, resume a run, or take the site over.

    Why:
        FR-076 grants the site to exactly one session owner even when two
        requests arrive together, and FR-077 blocks every write of a different
        owner. One endpoint serves all three ways in, because
        `contracts/http-api.md` section 3 names one path and the typed word in
        the body decides which way the lock module takes.

    Args:
        site_id: The site the path named.

    Returns:
        The token and the state, or the refusal envelope.
    """
    org_id = resolve_org(None)  # The lock path carries no organization, so the session answers.
    if org_id is None:  # The key needs both halves, so no lock may move yet.
        return json_error(BAD_REQUEST_STATUS, ORG_NOT_CHOSEN, ORG_NOT_CHOSEN_MESSAGE)  # The contract fixes this.
    ask = build_lock_request(org_id, site_id)  # None means the session carries no owner.
    if ask is None:  # The guard above passed, so this state is rare and still needs an answer.
        return identity.not_authenticated_response()  # The one envelope that names a missing session.
    try:  # Every write of the lock module fails closed, so each failure carries a code.
        grant = lock.acquire_site_lock(ask, client=lock_client())  # The store decides the race, never this route.
    except lock.SiteLockError as error:  # One base class covers every refusal of the lock module.
        return lock_failure_answer(site_id, error)  # The map above fixes the status of each code.
    store_lock_record(site_id, grant.record)  # The beat and the release both read this record back.
    store_chosen_site(site_id)  # The operator now drives this site, so the later routes read the same pick.
    return jsonify(lock_grant_body(grant)), OK_STATUS  # The one shape the contract names.


@select_bp.post(HEARTBEAT_API_PATH)
@identity.require_session
def beat_site_lock(site_id: str) -> tuple[Response, int]:
    """Extend the life of a lock this session still holds.

    Why:
        FR-078 gives an abandoned session a 5 minute cooldown, and the beat is
        what tells the portal that a session is not abandoned. The compare and
        the extend run as one step inside the store, so a beat cannot extend a
        lock that already changed hands.

    Args:
        site_id: The site the path named.

    Returns:
        The remaining life, or the refusal envelope.
    """
    org_id = resolve_org(None)  # The beat path carries no organization, so the session answers.
    record = held_record(site_id) if org_id is not None else None  # None means this session holds no matching lock.
    if org_id is None or record is None:  # Nothing to extend, so the page must take the site again.
        return lock_lost_answer()  # `contracts/site-lock.md:82` fixes this code and this status.
    try:  # A beat fails closed, because a portal that assumes a lock is worse than one that refuses.
        remaining = lock.refresh_site_lock(lock.build_key(org_id, site_id), record, client=lock_client())
    except lock.SiteLockError as error:  # The store refused, or the token no longer matches the stored one.
        drop_lock_record(site_id)  # This session lost the site, so the stored record must not survive.
        return lock_failure_answer(site_id, error)  # The map above fixes the status of each code.
    return jsonify({"expires_in": remaining}), OK_STATUS  # The one shape the contract names.


@select_bp.delete(LOCK_API_PATH)
@identity.require_session
def free_site_lock(site_id: str) -> tuple[Response, int]:
    """Give up a lock this session still holds.

    Why:
        `contracts/site-lock.md:97` releases the lock when a run reaches
        `complete`, `stopped`, or `failed`. A closed browser releases nothing,
        because the run continues without the browser.

    Args:
        site_id: The site the path named.

    Returns:
        The release answer, or the refusal envelope.
    """
    org_id = resolve_org(None)  # The release path carries no organization, so the session answers.
    record = held_record(site_id) if org_id is not None else None  # None means this session holds no matching lock.
    if org_id is None or record is None:  # Nothing to release, so the caller already lost the site.
        return lock_lost_answer()  # `contracts/site-lock.md:95` fixes this code and this status.
    try:  # The compare and the delete run as one step, so a release cannot free another operator.
        lock.release_site_lock(lock.build_key(org_id, site_id), record, client=lock_client())
    except lock.SiteLockError as error:  # The store refused, or the token no longer matches the stored one.
        drop_lock_record(site_id)  # This session lost the site either way, so the stored record must go.
        return lock_failure_answer(site_id, error)  # The map above fixes the status of each code.
    drop_lock_record(site_id)  # The site is free, so this browser holds no record of it.
    return jsonify({"released": True}), OK_STATUS  # The one shape the contract names.
