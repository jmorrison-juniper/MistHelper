"""Menu operation 291 -- optimize or reset site RRM with plan capture."""

from __future__ import annotations  # WHY: support modern annotations without runtime cost.

import logging  # WHY: log each operator step and result.
import os  # WHY: read dry-run and settle-time environment settings.
import time  # WHY: wait for the site RRM settle period.
from collections.abc import Callable  # WHY: tests inject a no-wait sleeper.
from dataclasses import dataclass  # WHY: group operation dependencies under five parameters.
from typing import Any  # WHY: shared project dependencies are dynamic.

from src.config.source_dependency_resolver import SourceDependencyResolver
from src.site.rrm_reset.client import RrmResetClient
from src.site.rrm_reset.model import ACTION_OPTIMIZE, ACTION_RESET, RrmPlanDiffBuilder, RrmRunSettings
from src.site.rrm_reset.writer import RrmPlanWriter

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter this feature.


@dataclass(frozen=True)
class RrmResetDependencies:
    """Hold the runtime dependencies for the operation."""

    client: RrmResetClient  # WHY: all Mist API calls live behind one seam.
    writer: RrmPlanWriter  # WHY: all file and backend writes live behind one seam.
    prompt_utils: Any  # WHY: shared site selector owns site prompt behavior.
    input_utils: Any  # WHY: shared input helper handles EOF-safe prompts.
    sleeper: Callable[[int], None] = time.sleep  # WHY: tests inject a no-op wait.


class RrmResetOperation:
    """Run the destructive RRM optimize or reset workflow."""

    @staticmethod
    def run(dry_run: bool | None = None, dependencies: RrmResetDependencies | None = None) -> None:
        """Prompt for site and action, then capture the before and after plans."""
        logger.info("Menu #291: Starting site RRM optimize or reset plan capture")  # WHY: action log.
        deps = dependencies or RrmResetOperation._build_dependencies()  # WHY: production uses shared deps.
        site_id = RrmResetOperation._select_site(deps)  # WHY: every API call needs a site id.
        if not site_id:  # WHY: an operator can abort at site selection.
            return  # WHY: no selected site means no file and no Mist change.
        action = RrmResetOperation._ask_action(deps)  # WHY: operator chooses the destructive request.
        if not action:  # WHY: invalid action stops before file or request.
            return  # WHY: no safe default exists for a destructive action.
        settings = RrmRunSettings.build(action, RrmResetOperation._resolve_dry_run(dry_run))  # WHY: one config object.
        RrmResetOperation._execute(site_id, settings, deps)  # WHY: execute the ordered capture workflow.

    @staticmethod
    def _build_dependencies() -> RrmResetDependencies:
        """Build production dependencies from the shared resolver."""
        client = RrmResetClient(SourceDependencyResolver.apisession)  # WHY: active authenticated session.
        writer = RrmPlanWriter(  # WHY: shared exporter and processing helpers preserve project output behavior.
            SourceDependencyResolver.DataExporter, SourceDependencyResolver.DataProcessingUtils
        )
        return RrmResetDependencies(
            client, writer, SourceDependencyResolver.PromptUtils, SourceDependencyResolver.InputUtils
        )

    @staticmethod
    def _select_site(deps: RrmResetDependencies) -> str:
        """Return the selected site or an empty string."""
        logger.info("Prompting for the RRM target site")  # WHY: action log before operator prompt.
        site_id = deps.prompt_utils.select_site()  # WHY: reuse the shared site selector.
        logger.debug("RRM target site selected=%s", bool(site_id))  # WHY: do not log more than the site id state.
        if not site_id:  # WHY: no site means no operation.
            logger.error("No site selected. Aborting RRM optimize or reset.")  # WHY: clear operator message.
            return ""  # WHY: empty string signals abort.
        return str(site_id)  # WHY: SDK path parameters use text.

    @staticmethod
    def _ask_action(deps: RrmResetDependencies) -> str:
        """Return the selected action or an empty string."""
        logger.info("Prompting for RRM action")  # WHY: action log before operator prompt.
        answer = deps.input_utils.safe_input("Type OPTIMIZE or RESET for the RRM action: ", context="rrm_action")
        action = answer.strip().upper()  # WHY: accept lower case while preserving strict choices.
        if action not in {ACTION_OPTIMIZE, ACTION_RESET}:  # WHY: no default is safe for a destructive action.
            logger.error("Invalid RRM action. Enter OPTIMIZE or RESET.")  # WHY: operator needs the accepted words.
            return ""  # WHY: empty action signals abort.
        logger.debug("RRM action selected=%s", action)  # WHY: action word is not secret.
        return action  # WHY: downstream confirmation must match this value.

    @staticmethod
    def _resolve_dry_run(dry_run: bool | None) -> bool:
        """Return whether the operation must avoid destructive Mist requests."""
        if dry_run is not None:  # WHY: tests and integration can pass the value directly.
            return dry_run  # WHY: explicit caller value wins.
        env_value = os.environ.get("RRM_DRY_RUN", "")  # WHY: local dry-run support works before integration wiring.
        if env_value.strip().lower() in {"1", "true", "yes", "dry-run"}:  # WHY: common truthy values are accepted.
            return True  # WHY: environment asks for preview only.
        return RrmResetOperation._root_dry_run()  # WHY: CLI --dry-run can live on the root args object.

    @staticmethod
    def _root_dry_run() -> bool:
        """Return the root CLI dry-run value when the host module exposes it."""
        try:
            root_module = SourceDependencyResolver.root_module()  # WHY: root args live outside source packages.
        except RuntimeError:
            return False  # WHY: tests or imports can run without a bound root module.
        args = getattr(root_module, "args", None)  # WHY: CLI parsing stores flags on args.
        return bool(getattr(args, "dry_run", False))  # WHY: missing flag means normal mode.

    @staticmethod
    def _execute(site_id: str, settings: RrmRunSettings, deps: RrmResetDependencies) -> None:
        """Run the ordered before-request-after-diff workflow."""
        before_rows = deps.client.get_current_plan(site_id)  # WHY: before capture must precede any mutation.
        if not deps.writer.write_before(before_rows):  # WHY: no destructive request without durable before output.
            logger.error("RRM before capture failed. No Mist change request was sent.")  # WHY: safety message.
            return  # WHY: stop before the destructive request.
        if settings.dry_run:  # WHY: dry-run exists to prove the plan without mutation.
            logger.info("RRM dry-run complete. No Mist change request was sent.")  # WHY: clear preview result.
            return  # WHY: dry-run writes no after file because no change request ran.
        if not RrmResetOperation._confirm(settings.action, deps):  # WHY: typed confirmation gates mutation.
            return  # WHY: wrong confirmation stops before the destructive request.
        RrmResetOperation._send_request(site_id, settings, deps)  # WHY: mutation occurs only after before write.
        RrmResetOperation._write_after_and_diff(site_id, before_rows, settings, deps)  # WHY: complete evidence set.

    @staticmethod
    def _confirm(action: str, deps: RrmResetDependencies) -> bool:
        """Ask for the exact destructive confirmation word."""
        logger.info("Prompting for typed RRM confirmation")  # WHY: action log before confirmation.
        prompt = f"Type {action} to send this destructive RRM request: "  # WHY: prompt names the required word.
        answer = deps.input_utils.safe_input(prompt, context="rrm_confirmation").strip().upper()  # WHY: EOF-safe input.
        confirmed = answer == action  # WHY: exact action word is required.
        logger.debug("RRM confirmation accepted=%s", confirmed)  # WHY: result summary without sensitive data.
        if not confirmed:  # WHY: wrong word cancels the destructive step.
            logger.warning("RRM confirmation failed. No Mist change request was sent.")  # WHY: operator notice.
        return confirmed  # WHY: caller gates the request on this value.

    @staticmethod
    def _send_request(site_id: str, settings: RrmRunSettings, deps: RrmResetDependencies) -> None:
        """Send the selected destructive request."""
        body = settings.request_body()  # WHY: both OpenAPI schemas require bands.
        if settings.action == ACTION_OPTIMIZE:  # WHY: optimize and reset use different endpoints.
            deps.client.optimize(site_id, body)  # WHY: send optimize request.
            return  # WHY: one destructive request per run.
        deps.client.reset(site_id, body)  # WHY: RESET maps to reset radio config endpoint.

    @staticmethod
    def _write_after_and_diff(
        site_id: str,
        before_rows: list[dict[str, Any]],
        settings: RrmRunSettings,
        deps: RrmResetDependencies,
    ) -> None:
        """Wait, capture the after plan, and write the diff."""
        logger.info("Waiting %d seconds for RRM to settle", settings.settle_seconds)  # WHY: action log before wait.
        deps.sleeper(settings.settle_seconds)  # WHY: allow Mist to apply RRM changes before the after read.
        logger.debug("RRM settle wait finished seconds=%d", settings.settle_seconds)  # WHY: wait result summary.
        after_rows = deps.client.get_current_plan(site_id)  # WHY: after capture records the post-request state.
        deps.writer.write_after(after_rows)  # WHY: operator needs the complete after plan.
        diff_rows = RrmPlanDiffBuilder.build(before_rows, after_rows)  # WHY: focus the change report.
        deps.writer.write_diff(diff_rows)  # WHY: operator needs changed radios only.
        logger.info("RRM plan capture complete. Changed radios=%d", len(diff_rows))  # WHY: final result summary.
