"""Cancel one multi-site operation in a real browser, and wait for the reads that follow.

Why:
    Issue #3245. The page script sends the cancel with a fetch call, and then
    it reloads the page. The address does not change, so an address wait
    returns at once. A reload of the test that comes too early cuts off the
    reload of the script, and the page can show a state from before the cancel.

    The stand-in cloud hid this race before. Each later job used the
    identifier of a cancelled job, so each later read reported "cancelled"
    before the test cancelled anything. Now each job holds its own identifier,
    so each journey waits for its own cancel.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each cancel step without a device address or a secret.
import re  # Match the address of the progress page.
from typing import Any  # Playwright objects carry no stable static type here.

import pytest  # Skip the importing test module when Playwright is not installed.

sync_api = pytest.importorskip(
    "playwright.sync_api", reason="Playwright is not installed."
)  # The helper needs Playwright.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

JOB_PATH = re.compile(r".*/upgrade/org/jobs/(org-run-[0-9a-f]+)$")  # The progress page of one operation.
RELOAD_TIMEOUT_MS = 15_000  # The cancel of five stand-in child jobs and the script reload end well inside this.


class OrgCancelSteps:
    """Cancel a multi-site operation, and wait until the page shows the end state."""

    @staticmethod
    def is_cancel_answer(answer: Any) -> bool:
        """Return True for the answer to the cancel request that the page script sends.

        Args:
            answer: One network answer of the browser page.
        """
        return answer.request.method == "POST" and answer.url.endswith("/cancel")  # The fetch call of the form.

    @classmethod
    def cancel(cls, page: Any) -> None:
        """Cancel the operation on its progress page, and wait until every child job ended.

        Why:
            Issue #3220. The portal keeps the site locks of an operation until
            each child job ends. The cancel ends each stand-in child job, and
            the reload reads each child job again, so both sites go back for
            the later browser tests.

            The helper waits for the load event of the new document. The page
            answer arrives before the new document attaches, so a reload at
            that moment finds no page.

        Args:
            page: The browser page on the progress page of the operation.
        """
        logger.info("Cancel the multi-site operation of the page %s", page.url)  # Log before the cancel.
        page.get_by_test_id("org-upgrade-cancel-confirmation").fill("CANCEL")  # The typed confirmation word.
        with page.expect_event("load", timeout=RELOAD_TIMEOUT_MS):  # The script reloads the page after the answer.
            with page.expect_response(cls.is_cancel_answer) as cancel_answer:  # The fetch call of the script.
                page.get_by_test_id("org-upgrade-cancel").click()  # The script sends the cancel request.
        status = cancel_answer.value.status  # The HTTP status of the cancel answer.
        assert cancel_answer.value.ok, f"The portal refused the cancel with HTTP {status}"  # Stop on a refusal.
        page.reload(wait_until="domcontentloaded")  # The server reads every child job again.
        sync_api.expect(page.locator("[data-org-upgrade-field='status']")).to_have_text(
            "cancelled"
        )  # The page shows the cancel.
        logger.debug("The multi-site operation ended with HTTP %s on the cancel", status)  # Log after the cancel.
