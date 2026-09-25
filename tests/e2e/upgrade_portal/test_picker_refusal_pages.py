"""Browser journeys for issue #3240: a picker refusal stays inside the picker page.

Why:
    The organization picker, the mode picker, and the multi-site site picker
    each send a plain form post. A refused post answered the JSON envelope, and
    the browser showed that envelope as the whole page. The operator then had
    no layout, no link, and no form. These journeys drive a real browser
    through each refusal. Each journey proves the caution sentence inside the
    picker page and no raw JSON page.

    No journey starts an operation, so no journey needs a cleanup step.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import re  # Match the address of each page of the journey.
from pathlib import Path  # Build the path of each screenshot.
from typing import Any  # Playwright objects carry no stable static type here.
from urllib.parse import urlsplit  # Read the path of each page address.

import pytest  # Supplies the skip when Playwright is missing.

sync_api = pytest.importorskip(
    "playwright.sync_api", reason="Playwright is not installed."
)  # The journeys need Playwright.

ORG_PATH = "/select/org"  # The organization picker.
MODE_PATH = "/select/mode"  # The mode picker.
SITE_PATH = "/select/site"  # The site picker.
SITE_PAGE = re.compile(r".*/select/site$")  # The address of the site picker.
OPTIONS_PAGE = re.compile(r".*/upgrade/org/options$")  # The address of the options page.
ORG_ID = "11111111-1111-1111-1111-111111111111"  # The stand-in organization of `conftest.py`.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The first stand-in site of `conftest.py`.
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"  # The second stand-in site of `conftest.py`.
ABSENT_SITE_ID = "00000000-0000-0000-0000-0000000000dd"  # A site that the stand-in organization does not hold.
SITES_SENTENCE = "Choose one or more sites for the multi-site operation."  # The empty site choice.
SITE_NOT_FOUND_SENTENCE = "The portal found no such site in this organization."  # The unknown site.
MODE_SENTENCE = "Choose a single-site or a multi-site operation."  # The missing mode.
ORG_SENTENCE = "Choose an organization before you read the site list."  # The missing organization.
CAUTION_ITEM = ".flash-item.flash-warning"  # One flashed caution sentence inside the message region.
CAUTION_PREFIX = '"Caution: "'  # The value that `portal.css` gives the prefix of a caution.
RAW_ENVELOPE = '{"error":'  # The text that a raw JSON page of a refusal shows. The JSON viewer adds a line first.
REDIRECT_STATUS = 303  # See Other, so the browser reads the picker with GET.


class PickerSteps:
    """Drive the three picker forms of the capture portal."""

    @staticmethod
    def open_multi_site_picker(page: Any) -> None:
        """Choose the multi-site mode, and open the site page with no site selected.

        Args:
            page: The browser page of the operator.
        """
        page.goto(MODE_PATH, wait_until="domcontentloaded")  # The journey starts at the mode choice.
        page.get_by_test_id("mode-multi-site").check()  # The operator selects many sites.
        page.get_by_test_id("mode-continue").click()  # The mode post must advance.
        page.wait_for_url(SITE_PAGE)  # The site page must open.
        for site_id in (SITE_ID, SECOND_SITE_ID):  # An earlier journey can leave a stored site set.
            page.get_by_test_id(f"site-select-{site_id}").uncheck()  # Start with no site selected.

    @staticmethod
    def submit(page: Any, control: str, post_path: str) -> Any:
        """Click one submit control, and return the form post after the next page loads.

        Why:
            The refused post and the page after it share one address, so no
            address change marks the end of the step. The load event of the
            next document marks the end with the old code and with the fix.

        Args:
            page: The browser page of the operator.
            control: The test identifier of the submit control.
            post_path: The path that the form posts to.

        Returns:
            The request of the form post.
        """

        def is_form_post(request: Any) -> bool:  # Match only the post of this form.
            return request.method == "POST" and urlsplit(request.url).path == post_path  # The exact path.

        with page.expect_request(is_form_post) as posted:  # Record the post of the form.
            with page.expect_event("load"):  # Wait for the document that the post opens.
                page.get_by_test_id(control).click()  # The operator sends the form.
        return posted.value  # The request, with its answer.

    @staticmethod
    def caution_sentences(page: Any) -> list[str]:
        """Return the text of each caution sentence in the message region.

        Args:
            page: The browser page of the operator.

        Returns:
            The text of each caution sentence, in page order.
        """
        region = page.get_by_test_id("flash-message")  # The shared message region of the layout.
        return [text.strip() for text in region.locator(CAUTION_ITEM).all_inner_texts()]  # No prefix text.

    @staticmethod
    def assert_picker_page(page: Any, path: str, sentence: str) -> None:
        """Prove that the refusal opened the picker page with one caution sentence.

        Args:
            page: The browser page of the operator.
            path: The path of the picker that corrects the choice.
            sentence: The refusal sentence that the page must show.
        """
        sync_api.expect(page.get_by_test_id("flash-message")).to_contain_text(sentence)  # The layout shows it.
        body_text = page.locator("body").inner_text()  # A raw JSON page shows the envelope as text.
        prefix = page.locator(CAUTION_ITEM).first.evaluate(
            "(node) => getComputedStyle(node, '::before').content"
        )  # The prefix that names the level without color.
        assert urlsplit(page.url).path == path, f"The refusal opened {page.url}."
        assert RAW_ENVELOPE not in body_text, "The browser shows a raw JSON page."
        assert PickerSteps.caution_sentences(page) == [sentence]
        assert prefix == CAUTION_PREFIX, f"The caution prefix reads {prefix}."


class TestPickerRefusalPages:
    """Prove that each picker refusal keeps the operator inside the picker."""

    def test_an_empty_site_choice_stays_on_the_site_page(self, page: Any, tmp_path: Path) -> None:
        """An empty site choice shows the caution, and the next choice continues (US1)."""
        PickerSteps.open_multi_site_picker(page)  # The site page with no site selected.
        posted = PickerSteps.submit(page, "multi-site-continue", SITE_PATH)  # The empty choice.
        page.screenshot(path=str(tmp_path / "3240-empty-site-choice.png"), full_page=True)  # Visual proof.
        assert posted.response().status == REDIRECT_STATUS  # FR-001: the portal answers a redirect.
        PickerSteps.assert_picker_page(page, SITE_PATH, SITES_SENTENCE)  # FR-002: one caution sentence.
        page.reload(wait_until="domcontentloaded")  # A reload reads the page with GET.
        assert PickerSteps.caution_sentences(page) == []  # The sentence shows one time only.
        page.get_by_test_id(f"site-select-{SITE_ID}").check()  # The operator corrects the choice.
        page.get_by_test_id("multi-site-continue").click()  # The corrected choice must advance.
        page.wait_for_url(OPTIONS_PAGE)  # The options page must open.
        page.go_back(wait_until="domcontentloaded")  # The history holds GET entries only.
        page.screenshot(path=str(tmp_path / "3240-back-to-site-page.png"), full_page=True)  # Visual proof.
        sync_api.expect(page.get_by_test_id("multi-site-form")).to_be_visible()  # The form works again.
        assert urlsplit(page.url).path == SITE_PATH  # The back step opens the site page.
        assert PickerSteps.caution_sentences(page) == []  # No old refusal returns.

    def test_a_changed_site_identifier_names_the_unknown_site(self, page: Any, tmp_path: Path) -> None:
        """A site identifier that the organization does not hold shows its caution (US1)."""
        PickerSteps.open_multi_site_picker(page)  # The site page with no site selected.
        box = page.get_by_test_id(f"site-select-{SITE_ID}")  # The box of the first stand-in site.
        box.evaluate("(node, value) => { node.value = value; }", ABSENT_SITE_ID)  # A stale page value.
        box.check()  # The operator selects the stale value.
        posted = PickerSteps.submit(page, "multi-site-continue", SITE_PATH)  # The unknown site choice.
        page.screenshot(path=str(tmp_path / "3240-unknown-site-choice.png"), full_page=True)  # Visual proof.
        assert posted.response().status == REDIRECT_STATUS  # FR-001: the portal answers a redirect.
        PickerSteps.assert_picker_page(page, SITE_PATH, SITE_NOT_FOUND_SENTENCE)  # FR-005: the site page.

    def test_a_mode_change_in_a_second_tab_returns_to_the_mode_page(self, page: Any, tmp_path: Path) -> None:
        """A mode change in a second tab sends the first tab to the mode page (US2)."""
        PickerSteps.open_multi_site_picker(page)  # Tab A shows the multi-site site page.
        second = page.context.new_page()  # Tab B shares the session cookie of tab A.
        try:
            second.goto(MODE_PATH, wait_until="domcontentloaded")  # Tab B opens the mode page.
            second.get_by_test_id("mode-single-site").check()  # Tab B changes the mode.
            second.get_by_test_id("mode-continue").click()  # The mode post stores the change.
            second.wait_for_url(SITE_PAGE)  # The single-site site page opens in tab B.
        finally:
            second.close()  # A tab left open holds a browser target for the whole run.
        page.get_by_test_id(f"site-select-{SITE_ID}").check()  # Tab A still shows the multi-site form.
        posted = PickerSteps.submit(page, "multi-site-continue", SITE_PATH)  # The post meets the new mode.
        page.screenshot(path=str(tmp_path / "3240-second-tab-mode-change.png"), full_page=True)  # Visual proof.
        assert posted.response().status == REDIRECT_STATUS  # FR-001: the portal answers a redirect.
        PickerSteps.assert_picker_page(page, MODE_PATH, MODE_SENTENCE)  # FR-005: the mode page.
        sync_api.expect(page.get_by_test_id("mode-single-site")).to_be_checked()  # The page shows the stored mode.

    def test_an_empty_mode_choice_stays_on_the_mode_page(self, page: Any, tmp_path: Path) -> None:
        """A mode post with no mode shows the caution on the mode page (US2)."""
        page.goto(MODE_PATH, wait_until="domcontentloaded")  # The mode page of the stand-in organization.
        for control in ("mode-single-site", "mode-multi-site"):  # The browser check stops an empty post.
            page.get_by_test_id(control).evaluate(
                "(node) => { node.required = false; node.checked = false; }"
            )  # Remove the browser check, so the post reaches the server check.
        posted = PickerSteps.submit(page, "mode-continue", MODE_PATH)  # The empty mode choice.
        page.screenshot(path=str(tmp_path / "3240-empty-mode-choice.png"), full_page=True)  # Visual proof.
        assert posted.response().status == REDIRECT_STATUS  # FR-001: the portal answers a redirect.
        PickerSteps.assert_picker_page(page, MODE_PATH, MODE_SENTENCE)  # FR-002: one caution sentence.

    def test_an_empty_organization_choice_stays_on_the_organization_page(self, page: Any, tmp_path: Path) -> None:
        """An organization post with no organization shows the caution (US3)."""
        page.goto(ORG_PATH, wait_until="domcontentloaded")  # The organization picker.
        field = page.locator(f"form:has([data-testid='org-select-{ORG_ID}']) input[name='org_id']")  # The row field.
        field.evaluate("(node) => { node.value = ''; }")  # A damaged page sends no organization.
        posted = PickerSteps.submit(page, f"org-select-{ORG_ID}", ORG_PATH)  # The empty choice.
        page.screenshot(path=str(tmp_path / "3240-empty-org-choice.png"), full_page=True)  # Visual proof.
        assert posted.response().status == REDIRECT_STATUS  # FR-001: the portal answers a redirect.
        PickerSteps.assert_picker_page(page, ORG_PATH, ORG_SENTENCE)  # FR-005: the organization page.
        sync_api.expect(page.get_by_test_id(f"org-select-{ORG_ID}")).to_be_visible()  # The picker works again.
