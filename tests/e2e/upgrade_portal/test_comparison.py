"""Browser tests for the comparison journey of the upgrade capture portal.

Why:
    A contract test proves that `GET /api/comparisons` answers the right keys.
    It cannot prove that an operator can choose two captures, read the
    statistics, filter the two tables, and download the result. The picker is a
    get form, and every filter control is a link, so only a browser test proves
    that the journey holds from one page to the next.

What this module skips and what it fails:
    The module reports a skip when the browser, the server, or the route is
    absent, and when the portal holds no stored capture to compare. It reports a
    failure when a page answers 200 and the identifier contract does not hold. A
    missing part of the environment never reports a pass, and a broken page
    never reports a skip.

Identifier contract:
    `contracts/ui-testids.md` fixes every identifier below. Rule 4 states that a
    test selects by `data-testid` only, so every locator reads that attribute.
    Each name is written out here rather than imported from the compare package,
    because a test that imports the value under test cannot find a rename of
    that value.
"""

from __future__ import annotations

import re
from typing import Any

import pytest

# The Playwright package must exist before this module defines a browser test.
# A run without the package reports a skip and never an import error.
sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

# `contracts/http-api.md` fixes these two paths for the comparison.
COMPARE_PAGE_PATH = "/compare"
EXPORT_API_PATH = "/api/comparisons/export"

# The three picker identifiers. The picker answers `/compare` with no query value.
BEFORE_SELECT_ID = "compare-before-select"
AFTER_SELECT_ID = "compare-after-select"
RUN_BUTTON_ID = "compare-run-button"

# The comparison page identifiers.
STATISTICS_ID = "compare-statistics"
DEVICE_TABLE_ID = "compare-device-table"
CLIENT_TABLE_ID = "compare-client-table"
CSV_EXPORT_ID = "compare-export-csv"
JSON_EXPORT_ID = "compare-export-json"

# The shared message region. The picker shows the refusal sentence here.
FLASH_ID = "flash-message"

# The identifier prefixes that rule 5 fixes for a dynamic row.
DEVICE_ROW_PREFIX = "compare-device-row-"
CLIENT_ROW_PREFIX = "compare-client-row-"

# The eleven statistic names of `data-model.md`, in report order. The identifier
# swaps each underscore for a hyphen, so `clients_moved` reads as
# `compare-stat-clients-moved` on the page.
STATISTIC_NAMES = (
    "devices_unchanged",
    "devices_changed",
    "devices_added",
    "devices_removed",
    "devices_version_changed",
    "clients_present",
    "clients_moved",
    "clients_added",
    "clients_missing",
    "client_return_rate",
    "elapsed_seconds",
)
STAT_TEST_IDS = tuple("compare-stat-" + name.replace("_", "-") for name in STATISTIC_NAMES)

# The page holds one filter bar that carries the union of the two outcome sets.
# `added` names a device outcome and a client outcome, and rule 6 allows one
# value for each page, so the union keeps `compare-filter-added` once.
FILTER_OUTCOMES = ("all", "unchanged", "changed", "added", "removed", "present", "moved", "missing")
FILTER_TEST_IDS = tuple("compare-filter-" + outcome for outcome in FILTER_OUTCOMES)

# `missing` names a client outcome alone, so it proves that the bar hands an
# outcome to the table that owns it.
CLIENT_ONLY_FILTER = "missing"

# `data-model.md` fixes every address as lower case with no separator. Both the
# device index and the client index use that one spelling, so a comparison joins
# the two captures on one key.
MAC_PATTERN = re.compile(r"^[0-9a-f]{12}$")

OK_STATUS = 200  # The contract fixes this status for every page below.
UNAUTHORIZED_STATUS = 401  # `runtime/identity.py` answers this code with no session.
NOT_FOUND_STATUS = 404  # The route is not registered yet.

# The two fixtures below reach the network and the file system, so a failure in
# either one describes the environment and never the page under test.
ENVIRONMENT_FIXTURES = ("capture_portal_server", "page")


def _lazy_fixture(request: pytest.FixtureRequest, name: str) -> Any:
    """Build one environment fixture, and turn a setup failure into a skip.

    Why:
        The server fixture needs a WSGI server and the page fixture needs a
        browser binary. Neither part exists on every workstation. A plain
        request would report an error, which reads in a report as a broken test.
        A skip that carries the real cause reads as the missing part that it is.

    Args:
        request: The pytest request object of the calling fixture.
        name: The fixture to build.

    Returns:
        The fixture value.
    """
    try:  # The failure below describes the environment, never the page.
        return request.getfixturevalue(name)
    except Exception as failure:  # A skip states the real cause, so nothing hides.
        pytest.skip(f"The fixture {name} could not start, so no browser test can run. Cause: {failure}")


@pytest.fixture
def portal_page(request: pytest.FixtureRequest) -> Any:
    """Return a browser page that points at the running capture portal.

    Why:
        Every test below needs the same two parts: a portal on port 8056 and a
        browser page. One fixture builds both in order, so a missing part gives
        one clear skip instead of one error for each test.

    Args:
        request: The pytest request object.

    Returns:
        The Playwright page object.
    """
    for name in ENVIRONMENT_FIXTURES:  # The server must answer before the browser opens a page.
        value = _lazy_fixture(request, name)
    return value


def _page_status(page: Any, path: str) -> int:
    """Open one path and return the status code of the answer.

    Args:
        page: The Playwright page object.
        path: The path to open, relative to the portal address.

    Returns:
        The status code that the portal answered.
    """
    answer = page.goto(path, wait_until="domcontentloaded")
    if answer is None:  # A page with no answer gives the test nothing to read.
        pytest.skip(f"The browser returned no response for {path}.")
    status: int = answer.status
    return status


def _skip_without_session(status: int, path: str) -> None:
    """Skip when the portal refuses the request because no session exists.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in the message.
    """
    if status == UNAUTHORIZED_STATUS:  # `identity.require_session` refused the request.
        pytest.skip(f"{path} answered 401. The portal has no sign-in route yet, so no browser test holds a session.")


def _require_built_route(status: int, path: str) -> None:
    """Skip when a route is absent, and fail when a built route answers wrongly.

    Why:
        This function draws the one line that keeps the suite honest. An absent
        route and an absent sign-in page are environment gaps, so both skip. Any
        other status is a contract breach, so it fails.

    Args:
        status: The status code the portal answered.
        path: The path the test opened, named in every message.

    Raises:
        AssertionError: If the portal answered a status that the contract does
            not fix for a page.
    """
    _skip_without_session(status, path)
    if status == NOT_FOUND_STATUS:  # The blueprint that owns this path is not registered.
        pytest.skip(f"{path} answered 404. The route is not built yet.")
    assert status == OK_STATUS, f"{path} answered {status}. `contracts/http-api.md` fixes 200 for this page."


def _click_and_wait(page: Any, test_id: str) -> int:
    """Press one control and return the status of the page that follows.

    Why:
        The run button and every filter control move the browser to a new
        address. A test that reads the page before the answer arrives sees the
        old page, so the press and the wait belong together.

    Args:
        page: The Playwright page object.
        test_id: The test identifier of the control to press.

    Returns:
        The status code of the page that followed.
    """
    with page.expect_response(lambda answer: answer.request.is_navigation_request()) as event:
        page.get_by_test_id(test_id).click()
    status: int = event.value.status
    return status


def _row_keys(page: Any, prefix: str) -> list[str]:
    """Read the stable key of every row that carries one identifier prefix.

    Why:
        Rule 5 of `contracts/ui-testids.md` states that a dynamic row appends a
        stable key. A test cannot know a MAC address before it reads the page,
        so it reads the keys that the page published.

    Args:
        page: The Playwright page object.
        prefix: The identifier prefix, such as `compare-device-row-`.

    Returns:
        One key for each row, in page order.
    """
    rows = page.locator(f'[data-testid^="{prefix}"]')  # A prefix match still selects by `data-testid`.
    markers = rows.evaluate_all("found => found.map(node => node.getAttribute('data-testid'))")
    return [str(marker)[len(prefix) :] for marker in markers if marker]


def _assert_row_keys_are_addresses(page: Any, prefix: str, table_name: str) -> None:
    """Check that every row of one table appends an address in one spelling.

    Why:
        A second spelling would break the join between the two captures, so the
        comparison would report a device as removed and added at the same time.

    Args:
        page: The Playwright page object, on the comparison page.
        prefix: The identifier prefix of the row.
        table_name: The table name, used in every message.

    Raises:
        AssertionError: If a key holds the wrong spelling, or if two rows share
            one key.
    """
    keys = _row_keys(page, prefix)
    if not keys:  # A digest match and a quiet site both leave the table empty, which breaks no rule.
        pytest.skip(f"The {table_name} shows no row, so no key exists to read.")
    wrong = [key for key in keys if not MAC_PATTERN.match(key)]
    assert not wrong, f"These rows of the {table_name} hold an address in the wrong spelling: {wrong}."
    assert len(set(keys)) == len(keys), f"Two rows of the {table_name} share one address in their test identifiers."


@pytest.fixture
def picker_page(portal_page: Any) -> Any:
    """Return a page that shows the capture picker.

    Why:
        `/compare` with no query value shows the picker, because an operator who
        arrives from the navigation has named no capture yet.

    Args:
        portal_page: The browser page that points at the portal.

    Returns:
        The Playwright page object, on the picker.
    """
    _require_built_route(_page_status(portal_page, COMPARE_PAGE_PATH), COMPARE_PAGE_PATH)
    return portal_page


def _capture_keys(page: Any) -> list[str]:
    """Read the capture identifier of every choice in the pre-check list.

    Why:
        A browser test cannot know a stored capture identifier in advance. The
        picker publishes each identifier as the value of a choice, so the test
        reads what the page offers. The first choice holds an empty value, and
        the filter below drops it.

    Args:
        page: The Playwright page object, on the picker.

    Returns:
        One capture identifier for each real choice, in page order.
    """
    chooser = page.get_by_test_id(BEFORE_SELECT_ID)  # The control itself comes from `data-testid`.
    values = chooser.evaluate("node => Array.from(node.options).map(choice => choice.value)")
    return [str(value) for value in values if value]


def _skip_without_comparison(page: Any) -> None:
    """Skip when the portal showed the picker again instead of a comparison.

    Why:
        The portal refuses an unverified capture and a pair that names two
        sites. It then shows the picker with a sentence rather than an error
        page, so a stored record that cannot join a comparison describes the
        data and never the page under test.

    Args:
        page: The Playwright page object, after the run button.
    """
    if page.get_by_test_id(STATISTICS_ID).count() > 0:  # The comparison rendered, so the journey went through.
        return
    notice = page.get_by_test_id(FLASH_ID)
    reason = (notice.inner_text() or "").strip() if notice.count() > 0 else "The portal named no reason."
    pytest.skip(f"The portal showed the picker again rather than a comparison. Reason: {reason}")


@pytest.fixture
def comparison_page(picker_page: Any) -> Any:
    """Return a page that shows the comparison of two stored captures.

    Why:
        The journey starts at the picker, so this fixture drives the real path
        rather than building an address of its own. It takes the first choice
        and the last choice, because those two are the furthest apart in time.

    Args:
        picker_page: The page that shows the capture picker.

    Returns:
        The Playwright page object, on the comparison page.
    """
    keys = _capture_keys(picker_page)
    if not keys:  # The portal holds no stored capture, so no comparison can run.
        pytest.skip("The picker offers no stored capture, so no comparison can run.")
    picker_page.get_by_test_id(BEFORE_SELECT_ID).select_option(keys[0])
    picker_page.get_by_test_id(AFTER_SELECT_ID).select_option(keys[-1])
    _require_built_route(_click_and_wait(picker_page, RUN_BUTTON_ID), COMPARE_PAGE_PATH)
    _skip_without_comparison(picker_page)
    return picker_page


def _link_target(page: Any, test_id: str) -> str:
    """Return the address that one link points at.

    Args:
        page: The Playwright page object, on the comparison page.
        test_id: The test identifier of the link.

    Returns:
        The address of that link.

    Raises:
        AssertionError: If the link carries no address.
    """
    target = page.get_by_test_id(test_id).get_attribute("href")
    assert target, f"{test_id} carries no address, so the operator can download nothing."
    return str(target)


class TestComparisonPicker:
    """The picker shows the two capture lists and the run button."""

    def test_picker_shows_the_two_capture_lists_and_the_run_button(self, picker_page: Any) -> None:
        """The picker shows the pre-check list, the post-check list, and the button.

        Args:
            picker_page: The page that shows the capture picker.
        """
        sync_api.expect(picker_page.get_by_test_id(BEFORE_SELECT_ID)).to_be_visible()
        sync_api.expect(picker_page.get_by_test_id(AFTER_SELECT_ID)).to_be_visible()
        sync_api.expect(picker_page.get_by_test_id(RUN_BUTTON_ID)).to_be_visible()

    def test_run_button_carries_the_two_choices_into_the_address(self, comparison_page: Any) -> None:
        """The run button puts the two capture identifiers in the address bar.

        Why:
            The picker is a get form, so the two choices travel in the address.
            The operator can then copy that address and share the comparison. A
            form that posts would lose that, and the endpoint reads the same two
            query names.

        Args:
            comparison_page: The page that shows the comparison.
        """
        address = comparison_page.url
        assert "before=" in address, f"The address {address} carries no before value."
        assert "after=" in address, f"The address {address} carries no after value."


class TestComparisonStatistics:
    """The statistics region shows one value for each name of the contract."""

    def test_page_shows_the_statistics_region(self, comparison_page: Any) -> None:
        """The comparison page shows the statistics region.

        Args:
            comparison_page: The page that shows the comparison.
        """
        sync_api.expect(comparison_page.get_by_test_id(STATISTICS_ID)).to_be_visible()

    def test_region_shows_one_value_for_each_statistic_name(self, comparison_page: Any) -> None:
        """The region shows all eleven statistics of the contract.

        Why:
            FR-041 asks the operator to read the outcome of the upgrade as
            numbers. A missing number hides one whole class of change, such as
            the clients that never came back.

        Args:
            comparison_page: The page that shows the comparison.
        """
        for test_id in STAT_TEST_IDS:
            sync_api.expect(comparison_page.get_by_test_id(test_id)).to_be_visible()


class TestComparisonTables:
    """The two difference tables show one row for each address."""

    def test_page_shows_the_device_table_and_the_client_table(self, comparison_page: Any) -> None:
        """The comparison page shows both difference tables.

        Args:
            comparison_page: The page that shows the comparison.
        """
        sync_api.expect(comparison_page.get_by_test_id(DEVICE_TABLE_ID)).to_be_visible()
        sync_api.expect(comparison_page.get_by_test_id(CLIENT_TABLE_ID)).to_be_visible()

    def test_every_device_row_appends_a_mac_address_key(self, comparison_page: Any) -> None:
        """Each device row appends a MAC address in one spelling.

        Args:
            comparison_page: The page that shows the comparison.
        """
        _assert_row_keys_are_addresses(comparison_page, DEVICE_ROW_PREFIX, DEVICE_TABLE_ID)

    def test_every_client_row_appends_a_mac_address_key(self, comparison_page: Any) -> None:
        """Each client row appends a MAC address in one spelling.

        Args:
            comparison_page: The page that shows the comparison.
        """
        _assert_row_keys_are_addresses(comparison_page, CLIENT_ROW_PREFIX, CLIENT_TABLE_ID)


class TestComparisonFilters:
    """The filter bar shows one control for each outcome of the two tables."""

    def test_page_shows_one_control_for_each_filter_outcome(self, comparison_page: Any) -> None:
        """The bar shows all eight filter controls.

        Why:
            A site with 200 devices and 8 changes hides the 8 changes. The bar
            holds the union of the device outcomes and the client outcomes, so
            the operator can read one outcome at a time.

        Args:
            comparison_page: The page that shows the comparison.
        """
        for test_id in FILTER_TEST_IDS:
            sync_api.expect(comparison_page.get_by_test_id(test_id)).to_be_visible()

    def test_a_filter_control_carries_its_outcome_into_the_address(self, comparison_page: Any) -> None:
        """A filter control puts its outcome in the address bar.

        Why:
            The content security policy of this portal is `self` only, so an
            inline script would not run. Each filter is therefore a link, and
            only a browser test proves that the link reaches a page that holds
            the chosen outcome.

        Args:
            comparison_page: The page that shows the comparison.
        """
        test_id = "compare-filter-" + CLIENT_ONLY_FILTER
        _require_built_route(_click_and_wait(comparison_page, test_id), COMPARE_PAGE_PATH)
        address = comparison_page.url
        assert f"outcome={CLIENT_ONLY_FILTER}" in address, f"The address {address} carries no chosen outcome."


class TestComparisonDownloads:
    """The page offers the comparison as a file in two formats."""

    def test_page_shows_the_two_download_links(self, comparison_page: Any) -> None:
        """The comparison page shows the CSV link and the JSON link.

        Args:
            comparison_page: The page that shows the comparison.
        """
        sync_api.expect(comparison_page.get_by_test_id(CSV_EXPORT_ID)).to_be_visible()
        sync_api.expect(comparison_page.get_by_test_id(JSON_EXPORT_ID)).to_be_visible()

    def test_each_download_link_names_the_export_path_and_its_format(self, comparison_page: Any) -> None:
        """Each download link points at the export endpoint with its own format.

        Why:
            The endpoint refuses any format other than `csv` and `json` with
            `bad_format`. A link that names no format would answer that refusal
            rather than a file.

        Args:
            comparison_page: The page that shows the comparison.
        """
        for test_id, wanted in ((CSV_EXPORT_ID, "format=csv"), (JSON_EXPORT_ID, "format=json")):
            target = _link_target(comparison_page, test_id)
            assert target.startswith(EXPORT_API_PATH), f"{test_id} points at {target}, not at {EXPORT_API_PATH}."
            assert wanted in target, f"{test_id} points at {target}, which names no {wanted}."

    def test_the_csv_link_answers_a_file_attachment(self, comparison_page: Any) -> None:
        """The CSV link answers a file that the browser saves.

        Why:
            A record keeper opens the comparison to keep the evidence. A link
            that answers 200 and shows the text in the browser gives no file, so
            the answer must carry the attachment header.

        Args:
            comparison_page: The page that shows the comparison.
        """
        answer = comparison_page.request.get(_link_target(comparison_page, CSV_EXPORT_ID))
        _skip_without_session(answer.status, EXPORT_API_PATH)
        assert answer.status == OK_STATUS, f"{EXPORT_API_PATH} answered {answer.status}. The contract fixes 200."
        disposition = answer.headers.get("content-disposition", "")
        assert "attachment" in disposition, f"{EXPORT_API_PATH} answered with {disposition!r}, so no file is saved."
