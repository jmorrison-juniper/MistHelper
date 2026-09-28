"""Prove the run owner check of the browser test portal with no browser and no network.

Why:
    Issue #3501. Each page fixture of the browser suite reads the health route
    of the test portal and calls this check. A stray portal of another run can
    answer on the same address, and the check must then fail. These direct
    tests prove each case, so the check can fail in the browser suite.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import pytest  # Check each refusal of the owner check.

from tests.support.upgrade_portal_e2e import RunOwnerHeaderCheck  # The check under test.

RUN_ID = "e2e-run-3501"  # The run that owns the portal of this test.
OTHER_RUN_ID = "e2e-run-other"  # The run of a stray portal on the same address.
OWNER_HEADER = "X-MistHelper-E2E-Run-ID"  # The header name as the test portal writes it.


def test_a_response_of_this_run_passes() -> None:
    """A response that names this run passes, and the check returns the owner."""
    check = RunOwnerHeaderCheck(RUN_ID)  # The check of this run.
    headers = {OWNER_HEADER: RUN_ID, "Content-Type": "text/plain"}  # A response of the correct portal.
    assert check.require(headers) == RUN_ID  # The check returns the owner that it read.


def test_a_response_of_another_run_fails_and_names_both_runs() -> None:
    """A response of another run fails, and the message names the header and both runs."""
    check = RunOwnerHeaderCheck(RUN_ID)  # The check of this run.
    with pytest.raises(AssertionError, match="names the run") as failure:  # A stray portal stops the fixture.
        check.require({OWNER_HEADER: OTHER_RUN_ID})  # The header names another run.
    message = str(failure.value)  # The text that the pytest report shows.
    assert OWNER_HEADER in message  # The reader learns which header failed.
    assert f"'{OTHER_RUN_ID}'" in message  # The reader learns the found run.
    assert f"'{RUN_ID}'" in message  # The reader learns the expected run.


def test_a_response_with_no_owner_header_fails() -> None:
    """A response with no owner header fails, and the message names a portal of another run."""
    check = RunOwnerHeaderCheck(RUN_ID)  # The check of this run.
    with pytest.raises(AssertionError, match=f"holds no {OWNER_HEADER} header") as failure:  # No owner.
        check.require({"Content-Type": "text/plain"})  # A response of a portal with no test header.
    assert "a portal of another run answered" in str(failure.value)  # The reader learns the cause.


@pytest.mark.parametrize("name", [OWNER_HEADER, OWNER_HEADER.lower(), OWNER_HEADER.upper()])
def test_the_check_reads_the_header_name_in_each_letter_case(name: str) -> None:
    """The check reads the owner header in each letter case of its name."""
    check = RunOwnerHeaderCheck(RUN_ID)  # The check of this run.
    assert check.require({name: RUN_ID}) == RUN_ID  # Playwright and urllib give different letter cases.


@pytest.mark.parametrize("expected", ["", "   "])
def test_an_empty_expected_run_is_refused(expected: str) -> None:
    """A check with an empty expected run is refused, because no response could name it."""
    with pytest.raises(ValueError, match="needs the identifier of this run"):  # Refuse the build.
        RunOwnerHeaderCheck(expected)  # An empty run cannot identify a portal.


def test_the_test_header_names_hold_each_test_header_in_small_letters() -> None:
    """The name list holds each test header in small letters, in sorted order, and no other header."""
    headers = {  # A response with two test headers and two other headers.
        OWNER_HEADER: RUN_ID,
        "X-MistHelper-E2E-Extra": "1",
        "Content-Type": "text/html",
        "X-Other": "2",
    }
    names = RunOwnerHeaderCheck.e2e_header_names(headers)  # The names that start with the test prefix.
    assert names == ("x-misthelper-e2e-extra", "x-misthelper-e2e-run-id")  # Sorted, small letters, no other.
