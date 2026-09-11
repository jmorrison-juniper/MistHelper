"""Prove the token life outlives the site lock it renews.

Why:
    Issue #2110 records a portal log that held 228 refusals, one each minute.
    The renewal beat posts every 60 seconds and each post carries the cross-site
    request forgery token. `flask-wtf` defaults the token life to 3600 seconds,
    which equals `LOCK_TTL_SECONDS`. The two therefore expired together, every
    beat after the first hour answered 400, and the site lock died with no
    renewal.

    A real cascade runs longer than one hour, because the settle gate allows 60
    minutes for each device. The token must therefore outlive the work, and
    these tests hold that rule so a later change cannot undo it by accident.
"""

from __future__ import annotations

from src.upgrade_portal.app import factory
from src.upgrade_portal.runtime import lock

BEAT_SECONDS = 60  # The beat period that `portal.js` and `runtime.lock` both name.
ONE_HOUR = 3600  # The old token life, and the value the framework still defaults to.


class TestTokenLifeOutlivesTheLock:
    """The token must survive longer than the lock that the beat renews."""

    def test_the_token_life_is_set_and_not_left_to_the_framework(self) -> None:
        """An unset value falls back to one hour, which is the defect."""
        assert factory.CSRF_TOKEN_SECONDS is not None  # The portal states the value itself.

    def test_the_token_outlives_the_site_lock(self) -> None:
        """A token that dies with the lock leaves no beat to renew it."""
        assert factory.CSRF_TOKEN_SECONDS > lock.LOCK_TTL_SECONDS

    def test_the_token_no_longer_equals_the_framework_default(self) -> None:
        """The two equal values are the exact shape of issue #2110."""
        assert factory.CSRF_TOKEN_SECONDS != ONE_HOUR

    def test_the_token_covers_a_long_cascade(self) -> None:
        """The settle gate allows 60 minutes for each device, so one hour is not enough.

        A site holds several device families, and the cascade runs them in turn.
        Four hours is a modest floor for that work.
        """
        four_hours = 4 * ONE_HOUR
        assert factory.CSRF_TOKEN_SECONDS >= four_hours

    def test_the_token_covers_many_beats(self) -> None:
        """The beat must be able to run many times before the token expires."""
        beats_before_expiry = factory.CSRF_TOKEN_SECONDS // BEAT_SECONDS
        assert beats_before_expiry >= 240  # Four hours of beats, at one each minute.


class TestTheApplicationCarriesTheValue:
    """The constant means nothing unless the application reads it."""

    def test_the_built_application_sets_the_token_life(self) -> None:
        """A reader of `app.config` must find the portal value, not the default."""
        app = factory.create_app()
        assert app.config["WTF_CSRF_TIME_LIMIT"] == factory.CSRF_TOKEN_SECONDS

    def test_the_built_application_outlives_the_lock(self) -> None:
        """The end to end rule, read from the live configuration."""
        app = factory.create_app()
        assert app.config["WTF_CSRF_TIME_LIMIT"] > lock.LOCK_TTL_SECONDS
