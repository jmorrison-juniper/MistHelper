"""Single policy resolver for the menu 291 RRM dry-run mode.

Issue #4051 adopted this policy for the destructive RRM optimize and reset
operation. Silence from the operator must never authorize a change to
production radios, so an absent mode resolves to a forced dry run.

The precedence order is:

1. An explicit tri-state operation argument.
2. An explicit root CLI mode.
3. A truthy ``RRM_DRY_RUN`` value from the process environment.
4. Absence, which forces dry-run mode.

The process environment wins over ``.env`` because both startup loaders keep an
existing process value. ``RRM_DRY_RUN`` is a one-way safety control, so a false
or an invalid value never authorizes live mode. Live mode needs an explicit live
choice, and the typed action confirmation stays mandatory after that choice.

This module holds the only read of ``RRM_DRY_RUN`` in the product code. The
guard ``scripts/rrm_dry_run_read_guard.py`` fails when a second read appears.
"""

from __future__ import annotations  # WHY: support modern annotations without runtime cost.

import logging  # WHY: the operator needs a clear message when a forced dry run is in effect.
import os  # WHY: this module owns the only RRM_DRY_RUN environment read.

from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter this policy.

ENVIRONMENT_VARIABLE = "RRM_DRY_RUN"  # WHY: one constant names the accepted environment source.
TRUTHY_VALUES = frozenset({"1", "true", "yes", "dry-run"})  # WHY: accept the common truthy spellings.


class RrmDryRunPolicy:
    """Resolve the RRM dry-run mode from the ordered policy sources."""

    @staticmethod
    def resolve(dry_run: bool | None) -> bool:
        """Return True when the run must send no destructive Mist request."""
        logger.info("Resolving the RRM dry-run mode")  # WHY: action log before the policy decision.
        if dry_run is not None:  # WHY: an explicit operation argument is the highest authority.
            logger.debug("RRM dry-run mode from the explicit argument=%s", dry_run)  # WHY: decision summary.
            return dry_run  # WHY: the caller stated the mode, so no source below may change it.
        cli_mode = RrmDryRunPolicy._cli_mode()  # WHY: an explicit CLI mode is the next authority.
        if cli_mode is not None:  # WHY: only an explicit flag produces a value here.
            logger.debug("RRM dry-run mode from the explicit CLI flag=%s", cli_mode)  # WHY: decision summary.
            return cli_mode  # WHY: the operator stated the mode on the command line.
        if RrmDryRunPolicy._environment_requests_dry_run():  # WHY: a truthy value forces preview mode.
            logger.debug("RRM dry-run mode from the %s value=True", ENVIRONMENT_VARIABLE)  # WHY: decision summary.
            return True  # WHY: the environment may only make the run safer.
        logger.warning(
            "No explicit RRM mode was given, so a dry run is in effect. Pass --live-run to send the request.",
        )  # WHY: the operator must know why no change request ran and how to choose live mode.
        return True  # WHY: silence must never authorize a production radio change.

    @staticmethod
    def _cli_mode() -> bool | None:
        """Return the explicit root CLI mode, or None when no flag was given."""
        try:  # WHY: a direct source call can run before the host module binds.
            root_module = SourceDependencyResolver.root_module()  # WHY: root args live outside the source packages.
        except RuntimeError:  # WHY: tests and library imports run without a bound root module.
            return None  # WHY: an unbound root supplies no explicit mode.
        args = getattr(root_module, "args", None)  # WHY: CLI parsing stores the flags on args.
        mode = getattr(args, "dry_run", None)  # WHY: the parser stores None when neither flag is present.
        return None if mode is None else bool(mode)  # WHY: keep the tri-state and normalize the explicit values.

    @staticmethod
    def _environment_requests_dry_run() -> bool:
        """Return True only when the environment holds a truthy value."""
        raw_value = os.environ.get(ENVIRONMENT_VARIABLE, "")  # WHY: the only RRM_DRY_RUN read in the product code.
        requested = raw_value.strip().lower() in TRUTHY_VALUES  # WHY: a false or invalid value is not a live choice.
        logger.debug("%s requested dry-run=%s", ENVIRONMENT_VARIABLE, requested)  # WHY: result summary, no secret.
        return requested  # WHY: the caller treats False as "no opinion", never as "run live".
