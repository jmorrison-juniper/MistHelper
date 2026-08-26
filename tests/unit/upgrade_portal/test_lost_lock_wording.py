"""Proof that a lost site lock never reads as an upgrade that did not happen.

Why:
    The portal submits the upgrade to the Mist cloud, and the cloud then owns
    the work. A lost site lock stops the portal from writing to the site. It
    stops no firmware download and no reboot.

    The first build of this feature said only what was lost. The run record
    carried the sentence "the site lock changed hands or expired, so this run no
    longer holds the site", and the run page painted that sentence in a red
    banner. Nothing said that the upgrade continues.

    That combination creates the worst outcome of the whole feature. An operator
    reads a red banner, concludes the upgrade did not happen, and walks away. The
    devices then reboot hours later during business hours, and the operator has
    nothing that explains the reboot.

    The fix has three parts, and this file pins all three.

    1. Every sentence names the continuation. The loss and the continuation ride
       in one field, because `contracts/http-api.md` section 5 fixes the lock
       report as a whitelist of `state`, `message`, and `at`.

    2. No sentence names a failure, and no sentence names a cause the portal
       cannot prove. A beat learns that the lock is gone. It cannot tell a
       takeover from an expiry.

    3. The banner warns, and it never reports a failure. `flash-danger` is the
       class of a failed action, and this banner reports no failed action.

    No harness runs JavaScript in this suite. The browser half therefore reads
    the text of `portal.js`.
"""

from __future__ import annotations

from pathlib import Path

from src.upgrade_portal.upgrade import driver

# WHY: This file sits at tests/unit/upgrade_portal, so the root is three levels up.
REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / "src" / "upgrade_portal" / "app" / "assets" / "static" / "js" / "portal.js"

# WHY: The two sentences the driver writes onto the run record. One covers a lock
# that changed hands, and one covers a lock store that stopped answering.
SERVER_SENTENCES = (driver.LOCK_LOST_REASON, driver.LOCK_STORE_QUIET_REASON)

# WHY: The two facts that keep an operator at their desk. The upgrade is not
# over, and the devices have not finished rebooting.
CONTINUES_TEXT = "The upgrade continues in the cloud"
REBOOT_TEXT = "the devices still reboot"

# WHY: Words that turn a lock report into a report of an upgrade that did not
# happen. `cancel` matters as much as `fail`, because FR-038a gives `cancel` one
# meaning already: the stop control that drops the devices not yet started.
FAILURE_WORDS = ("fail", "abort", "cancel", "stop")

# WHY: A beat reads that the lock is gone and nothing more, so a named cause
# could be false. `contracts/site-lock.md` gives no way to tell the two apart.
UNPROVEN_CAUSE_WORDS = ("changed hands", "another operator", "expired")

# WHY: The class of a failed action, and the class this banner uses instead.
FAILURE_CLASS = "flash-danger"
WARNING_CLASS = "flash-item flash-warning"

# WHY: The name of the fallback sentence in portal.js. The browser shows it when
# a lock report carries no sentence of its own.
FALLBACK_NAME = "RUN_LOCK_LOST_TEXT"


def script_text() -> str:
    """Return the whole text of the browser script.

    Why:
        Three tests read the same file, and one read keeps them in step.

    Returns:
        The text of `portal.js`.
    """
    return SCRIPT_PATH.read_text(encoding="utf-8")


def fallback_sentence() -> str:
    """Return the fallback sentence that the browser shows.

    Why:
        The value spans two lines in the source, so a test cannot read it with
        one plain search. This reader takes every line from the assignment to
        the semicolon and joins the quoted parts.

    Returns:
        The sentence between the quotation marks of the assignment.
    """
    text = script_text()
    start = text.index("var " + FALLBACK_NAME)
    body = text[start : text.index(";", start)]
    return "".join(part for index, part in enumerate(body.split('"')) if index % 2 == 1)


class TestTheServerSentencesSayTheWorkContinues:
    """Both driver sentences carry the loss and the continuation together."""

    def test_every_sentence_says_the_upgrade_continues(self) -> None:
        """The operator must read that the cloud still holds the order."""
        for sentence in SERVER_SENTENCES:
            assert CONTINUES_TEXT in sentence

    def test_every_sentence_says_the_devices_still_reboot(self) -> None:
        """A reboot is the event that surprises an operator who walked away."""
        for sentence in SERVER_SENTENCES:
            assert REBOOT_TEXT in sentence

    def test_every_sentence_names_the_lost_lock(self) -> None:
        """The loss is still real, so the sentence still reports it."""
        for sentence in SERVER_SENTENCES:
            assert "no longer holds the site lock" in sentence

    def test_no_sentence_names_a_failure(self) -> None:
        """A lock report is no report of a failed upgrade."""
        for sentence in SERVER_SENTENCES:
            for word in FAILURE_WORDS:
                assert word not in sentence.lower()

    def test_no_sentence_names_a_cause_the_portal_cannot_prove(self) -> None:
        """A beat cannot tell a takeover from an expiry, so it names neither."""
        for sentence in SERVER_SENTENCES:
            for word in UNPROVEN_CAUSE_WORDS:
                assert word not in sentence.lower()

    def test_the_two_sentences_differ(self) -> None:
        """A reader still tells a takeover apart from a quiet lock store."""
        assert driver.LOCK_LOST_REASON != driver.LOCK_STORE_QUIET_REASON


class TestTheBrowserFallbackMatchesTheServer:
    """The sentence the browser supplies carries the same two facts."""

    def test_the_fallback_says_the_upgrade_continues(self) -> None:
        """A report with no sentence of its own still needs both facts."""
        assert CONTINUES_TEXT in fallback_sentence()

    def test_the_fallback_says_the_devices_still_reboot(self) -> None:
        """The browser half must never drop the fact the server half carries."""
        assert REBOOT_TEXT in fallback_sentence()

    def test_the_fallback_names_no_failure(self) -> None:
        """The browser must not add a word the server refused to write."""
        for word in FAILURE_WORDS:
            assert word not in fallback_sentence().lower()


class TestTheBannerWarnsAndReportsNoFailure:
    """The run banner uses the warning class, and never the failure class."""

    def test_the_run_lock_banner_uses_the_warning_class(self) -> None:
        """Color carries meaning, and red means an action that failed."""
        text = script_text()
        start = text.index("function runLockBanner")
        assert WARNING_CLASS in text[start : text.index("\n    }", start)]

    def test_the_run_lock_banner_never_uses_the_failure_class(self) -> None:
        """One red banner is enough to send an operator home."""
        text = script_text()
        start = text.index("function runLockBanner")
        assert FAILURE_CLASS not in text[start : text.index("\n    }", start)]

    def test_the_banner_still_announces_itself(self) -> None:
        """A softer color must not cost the operator the message.

        Why:
            The status region is polite, which holds a note until the screen
            reader rests. The run page polls every 30 seconds, so a polite note
            could wait a long time. The banner therefore keeps the alert role.
        """
        text = script_text()
        start = text.index("function runLockBanner")
        assert '"role", "alert"' in text[start : text.index("\n    }", start)]
