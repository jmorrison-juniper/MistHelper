"""Interactive handler for client CoA, reauthentication, and disconnect."""

from __future__ import annotations  # WHY: keep annotations lazy for dependency callables.

import logging  # WHY: action logging is required around prompts, validation, and calls.
from collections.abc import Callable, Mapping  # WHY: dependency types stay small and explicit.
from dataclasses import dataclass  # WHY: dependencies are bundled to keep run() arity low.
from datetime import UTC, datetime  # WHY: audit rows require UTC timestamps.
from typing import Any  # WHY: Mist SDK session and fake sessions are externally owned objects.

from src.foundation.support.utils.input_utils import InputUtils  # WHY: use the canonical EOF-safe input helper.
from src.interfaces.visualization.ui.prompt_utils import PromptUtils  # WHY: reuse existing site selection flow.
from src.mist.resources.device.client_session_control.actions import (  # WHY: handler needs catalog and SDK client.
    ActionDefinition,
    MistSessionControlApiClient,
    get_action,
    list_actions,
)
from src.mist.resources.device.client_session_control.audit import (
    ClientSessionAuditWriter,
)  # WHY: default CSV audit writer.
from src.mist.resources.device.client_session_control.models import (  # Import the moved dependency.
    ClientSessionControlLogRow,
    ClientSessionControlRequest,
    Confirmation,
    build_confirmation,
    build_target,
)

logger = logging.getLogger(__name__)  # WHY: module logger traces the interactive operation.
PrintFn = Callable[[str], None]  # WHY: print dependency is injectable for tests.
SafeInputFn = Callable[..., str]  # WHY: InputUtils.safe_input accepts keyword context values.
SelectSiteFn = Callable[[Any, str], str | Mapping[str, str] | None]  # WHY: tests can return a named site mapping.


@dataclass(frozen=True)
class HandlerDependencies:  # WHY: dependency bundle keeps ClientSessionControl.run() under five parameters.
    """Injected dependencies for the client session control handler."""

    select_site_fn: SelectSiteFn  # WHY: site picker boundary.
    safe_input_fn: SafeInputFn  # WHY: EOF-safe operator input boundary.
    print_fn: PrintFn  # WHY: output boundary for previews and results.
    audit_writer: ClientSessionAuditWriter  # WHY: durable audit boundary.
    api_client: MistSessionControlApiClient  # WHY: Mist SDK boundary.


class ClientSessionControl:  # WHY: required class based handler for menu 286.
    """Run the client session control operation."""

    @staticmethod
    def run(
        apisession: Any,
        org_id: str,
        dry_run: bool = False,
        dependencies: HandlerDependencies | None = None,
    ) -> str:
        """Run one client session control flow and return the result key."""
        deps = dependencies or ClientSessionControl._default_dependencies()  # WHY: runtime uses real dependencies.
        logger.info("Starting client session control flow")  # WHY: before the interactive operation.
        site = ClientSessionControl._select_site(deps, apisession, org_id)  # WHY: site is required first.
        if site is None:  # WHY: no selected site means no request can be built.
            return ClientSessionControl._report(deps, "validation_failed", "No site selected.")  # WHY: stop safely.
        try:
            result = ClientSessionControl._run_selected_flow(deps, apisession, site, dry_run)  # WHY: main flow.
        except ValueError as error:
            result = ClientSessionControl._report(deps, "validation_failed", str(error))  # WHY: safe stop.
        logger.debug("Completed client session control flow with result %s", result)  # WHY: after operation.
        return result  # WHY: tests and menu wrappers can inspect the final result.

    @staticmethod
    def _default_dependencies() -> HandlerDependencies:
        """Build default runtime dependencies for the menu handler."""
        logger.info("Building default client session control dependencies")  # WHY: before dependency construction.
        dependencies = HandlerDependencies(  # WHY: bundle all side effect boundaries in one object.
            select_site_fn=ClientSessionControl._select_site_from_prompt,  # WHY: existing site selector.
            safe_input_fn=InputUtils.safe_input,  # WHY: canonical EOF-safe prompt helper.
            print_fn=print,  # WHY: default operator output sink.
            audit_writer=ClientSessionAuditWriter(),  # WHY: default CSV audit file under data/.
            api_client=MistSessionControlApiClient(),  # WHY: default Mist SDK client.
        )
        logger.debug("Built default client session control dependencies")  # WHY: after dependency construction.
        return dependencies  # WHY: run() consumes this bundle.

    @staticmethod
    def _select_site_from_prompt(_session: Any, _org_id: str) -> str | Mapping[str, str] | None:
        """Select one Mist site using the existing prompt utility."""
        logger.info("Prompting for client session control site")  # WHY: before site prompt.
        site_id = PromptUtils.select_site_with_logging()  # WHY: reuse the repository site selection pattern.
        if site_id:  # WHY: the existing prompt returns only the id, so read its CSV name after selection.
            site_record = ClientSessionControl._site_record_from_csv(site_id)  # WHY: preserve the chosen site name.
            logger.debug("Site prompt completed with named selection=%s", bool(site_record))  # WHY: after lookup.
            return site_record  # WHY: downstream preview and audit rows need the name and id.
        logger.debug("Site prompt completed with selected=%s", bool(site_id))  # WHY: after site prompt.
        return site_id  # WHY: handler normalizes string site IDs into site records.

    @staticmethod
    def _site_record_from_csv(site_id: str) -> dict[str, str]:
        """Return the selected site id and name from the generated site CSV."""
        logger.info("Reading selected client session control site name")  # WHY: before CSV lookup.
        index_to_site, _name_to_site = PromptUtils._load_site_csv_maps("SiteList.csv")  # WHY: same CSV as prompt.
        for site in index_to_site.values():  # WHY: find the row that owns the selected id.
            if str(site.get("id", "")).strip() == site_id:  # WHY: match the exact selected site identifier.
                site_name = str(site.get("name", site_id)).strip() or site_id  # WHY: guarantee display text.
                logger.debug("Resolved selected site name for client session control")  # WHY: after lookup.
                return {"id": site_id, "name": site_name}  # WHY: mapping path keeps name in preview and CSV.
        logger.debug("Selected site name was absent from SiteList.csv")  # WHY: after failed lookup.
        return {"id": site_id, "name": site_id}  # WHY: keep the old fallback when the CSV lacks the row.

    @staticmethod
    def _select_site(
        deps: HandlerDependencies,
        apisession: Any,
        org_id: str,
    ) -> tuple[str, str] | None:
        """Return the selected site id and name."""
        logger.info("Selecting site for client session control request")  # WHY: before dependency call.
        selected_site = deps.select_site_fn(apisession, org_id)  # WHY: inject site picker for tests and runtime.
        site = ClientSessionControl._coerce_site(selected_site)  # WHY: support string IDs and mapping fakes.
        logger.debug("Selected site present=%s", site is not None)  # WHY: after dependency call.
        return site  # WHY: next step needs site id and name.

    @staticmethod
    def _coerce_site(selected_site: str | Mapping[str, str] | None) -> tuple[str, str] | None:
        """Convert site picker output into a site id and name pair."""
        logger.info("Normalizing selected site record")  # WHY: before site data transformation.
        if selected_site is None:  # WHY: operator cancelled or entered an invalid site.
            logger.debug("No site record was selected")  # WHY: after empty transformation.
            return None  # WHY: caller stops safely.
        if isinstance(selected_site, str):  # WHY: existing PromptUtils returns only the site ID.
            logger.debug("Selected site record is a string site id")  # WHY: after type check.
            return selected_site, selected_site  # WHY: use the site ID as the audit name fallback.
        site_id = str(selected_site.get("id", "")).strip()  # WHY: fakes or future selectors can return mappings.
        site_name = str(selected_site.get("name", site_id)).strip()  # WHY: audit rows prefer readable names.
        if not site_id:  # WHY: empty site ID cannot build a Mist endpoint.
            logger.debug("Selected site mapping had no site id")  # WHY: after invalid mapping check.
            return None  # WHY: caller stops safely.
        logger.debug("Normalized selected site record for site %s", site_id)  # WHY: after transformation.
        return site_id, site_name or site_id  # WHY: guarantee a non-empty display name.

    @staticmethod
    def _run_selected_flow(
        deps: HandlerDependencies,
        apisession: Any,
        site: tuple[str, str],
        dry_run: bool,
    ) -> str:
        """Run prompts and dispatch for a selected site."""
        action = ClientSessionControl._prompt_action(deps)  # WHY: action determines target type and SDK call.
        request = ClientSessionControl._prompt_request(deps, site, action, dry_run)  # WHY: build validated request.
        confirmation = ClientSessionControl._prompt_confirmation(deps, request)  # WHY: typed target gate.
        if not confirmation.matched:  # WHY: mismatch must stop before dry run or live call.
            return ClientSessionControl._stop_for_confirmation(deps, request)  # WHY: audit and report failure.
        if dry_run:  # WHY: dry run previews and sends no Mist request.
            return ClientSessionControl._dry_run(deps, request)  # WHY: audit and report dry run.
        return ClientSessionControl._send_live(deps, apisession, request)  # WHY: confirmation passed for live request.

    @staticmethod
    def _prompt_action(deps: HandlerDependencies) -> ActionDefinition:
        """Prompt for one supported action."""
        logger.info("Prompting for client session control action")  # WHY: before action prompt.
        ClientSessionControl._print_action_menu(deps)  # WHY: show supported destructive actions.
        raw_action = deps.safe_input_fn(  # WHY: prompt through the EOF-safe injected helper.
            "Enter action number or key: ",
            context="client_session_control_action",
        )
        action = get_action(str(raw_action))  # WHY: validate the operator action choice.
        logger.debug("Selected client session control action %s", action.action_key)  # WHY: after prompt.
        return action  # WHY: caller needs action metadata.

    @staticmethod
    def _print_action_menu(deps: HandlerDependencies) -> None:
        """Print the supported action choices."""
        logger.info("Printing client session control action menu")  # WHY: before output.
        deps.print_fn("Client session control actions:")  # WHY: heading for operator choice.
        for index, action in enumerate(list_actions(), start=1):  # WHY: one based operator menu.
            deps.print_fn(f"{index}. {action.label} ({action.action_key})")  # WHY: display number and stable key.
        logger.debug("Printed client session control action menu")  # WHY: after output.

    @staticmethod
    def _prompt_request(
        deps: HandlerDependencies,
        site: tuple[str, str],
        action: ActionDefinition,
        dry_run: bool,
    ) -> ClientSessionControlRequest:
        """Prompt for the target and build a validated request."""
        logger.info("Prompting for client session control target")  # WHY: before target prompt.
        prompt_text = ClientSessionControl._target_prompt(action)  # WHY: target type controls prompt wording.
        raw_target = deps.safe_input_fn(prompt_text, context="client_session_control_target")  # WHY: EOF-safe input.
        target = build_target(action.target_type, str(raw_target))  # WHY: validate before confirmation.
        request = ClientSessionControlRequest(site[0], site[1], action, target, dry_run)  # WHY: bundle request.
        deps.print_fn(f"Selected action: {action.label}")  # WHY: operator must review selected action.
        deps.print_fn(f"Normalized target: {target.display_value}")  # WHY: operator must type this exact value.
        logger.debug("Built client session control request for action %s", action.action_key)  # WHY: after prompt.
        return request  # WHY: caller proceeds to confirmation.

    @staticmethod
    def _target_prompt(action: ActionDefinition) -> str:
        """Return the target prompt for the selected action."""
        logger.info("Building target prompt for client session control")  # WHY: before text transformation.
        label = "rogue BSSID" if action.target_type == "rogue_bssid" else "client MAC"  # WHY: clear prompt.
        prompt = f"Enter {label}: "  # WHY: ask for the exact required target type.
        logger.debug("Built target prompt for target type %s", action.target_type)  # WHY: after text transformation.
        return prompt  # WHY: prompt caller uses this text.

    @staticmethod
    def _prompt_confirmation(deps: HandlerDependencies, request: ClientSessionControlRequest) -> Confirmation:
        """Prompt for exact typed target confirmation."""
        logger.info("Prompting for client session control confirmation")  # WHY: before destructive confirmation.
        prompt = f"Type {request.target.display_value} again to confirm: "  # WHY: exact normalized target gate.
        raw_confirmation = deps.safe_input_fn(prompt, context="client_session_control_confirmation")  # WHY: EOF-safe.
        confirmation = build_confirmation(  # WHY: normalize and compare the operator confirmation.
            request.target.normalized_value,
            str(raw_confirmation),
        )
        logger.debug("Confirmation prompt completed with matched=%s", confirmation.matched)  # WHY: after prompt.
        return confirmation  # WHY: caller decides whether to continue.

    @staticmethod
    def _stop_for_confirmation(deps: HandlerDependencies, request: ClientSessionControlRequest) -> str:
        """Audit and report a failed destructive confirmation."""
        message = "Confirmation failed. No Mist request was sent."  # WHY: clear safety result for operator.
        row = ClientSessionControl._row(request, False, "confirmation_failed", message)  # WHY: audit failed attempt.
        ClientSessionControl._write_audit(deps, row)  # WHY: one row per request attempt.
        return ClientSessionControl._report(deps, "confirmation_failed", message)  # WHY: final operator result.

    @staticmethod
    def _dry_run(deps: HandlerDependencies, request: ClientSessionControlRequest) -> str:
        """Preview a request and write a dry run audit row."""
        logger.info("Preparing client session control dry run preview")  # WHY: before preview output.
        preview = ClientSessionControl._preview_text(request)  # WHY: build the request that would be sent.
        deps.print_fn(preview)  # WHY: operator must see the request details.
        logger.debug("Printed dry run preview for operation %s", request.action.operation_id)  # WHY: after output.
        row = ClientSessionControl._row(request, True, "dry_run", "Dry run. No Mist request was sent.")  # WHY.
        ClientSessionControl._write_audit(deps, row)  # WHY: dry run is still one request attempt.
        return ClientSessionControl._report(deps, "dry_run", "Dry run complete. No Mist request was sent.")  # WHY.

    @staticmethod
    def _send_live(deps: HandlerDependencies, apisession: Any, request: ClientSessionControlRequest) -> str:
        """Send a confirmed live Mist request and audit the result."""
        logger.info("Sending confirmed client session control request")  # WHY: before live API call.
        try:
            response = deps.api_client.send(  # WHY: call injected Mist client once after exact confirmation.
                apisession,
                request.site_id,
                request.action.action_key,
                request.target.normalized_value,
            )
        except Exception as error:
            logger.exception("Client session control Mist request failed")  # WHY: full exception context.
            return ClientSessionControl._mist_failure(deps, request, str(error))  # WHY: audit and report failure.
        if ClientSessionControl._response_failed(response):  # WHY: HTTP error responses are Mist failures.
            return ClientSessionControl._mist_failure(deps, request, "Mist request returned an error.")  # WHY: fail.
        logger.debug("Confirmed client session control request completed")  # WHY: after live API call.
        row = ClientSessionControl._row(request, True, "success", "Request completed.")  # WHY: success audit row.
        ClientSessionControl._write_audit(deps, row)  # WHY: durable audit before reporting success.
        return ClientSessionControl._report(deps, "success", "Success. Request completed.")  # WHY: final result.

    @staticmethod
    def _mist_failure(deps: HandlerDependencies, request: ClientSessionControlRequest, message: str) -> str:
        """Audit and report a Mist failure."""
        row = ClientSessionControl._row(request, True, "mist_failure", message)  # WHY: capture failed live attempt.
        ClientSessionControl._write_audit(deps, row)  # WHY: failed live attempts require one audit row.
        return ClientSessionControl._report(deps, "mist_failure", f"Mist failure. {message}")  # WHY: report failure.

    @staticmethod
    def _response_failed(response: object) -> bool:
        """Return True when a Mist SDK response indicates failure."""
        logger.info("Checking client session control Mist response")  # WHY: before response inspection.
        status_code = getattr(response, "status_code", 200)  # WHY: old fakes may omit status and imply success.
        failed = isinstance(status_code, int) and status_code >= 400  # WHY: HTTP 4xx and 5xx are failures.
        logger.debug("Mist response failure state is %s", failed)  # WHY: after response inspection.
        return failed  # WHY: caller chooses success or failure flow.

    @staticmethod
    def _preview_text(request: ClientSessionControlRequest) -> str:
        """Build the dry run request preview text."""
        logger.info("Building client session control dry run text")  # WHY: before preview transformation.
        preview = (  # WHY: one multi-line string gives the operator all request fields.
            "Dry run request preview\n"
            f"Operation ID: {request.action.operation_id}\n"
            f"Site: {request.site_name} ({request.site_id})\n"
            f"Action: {request.action.label}\n"
            f"Target: {request.target.normalized_value}"
        )
        logger.debug("Built dry run preview for action %s", request.action.action_key)  # WHY: after transformation.
        return preview  # WHY: caller prints this text.

    @staticmethod
    def _row(
        request: ClientSessionControlRequest,
        confirmed: bool,
        result: str,
        message: str,
    ) -> ClientSessionControlLogRow:
        """Build one audit row with the current UTC time."""
        logger.info("Building timestamped client session control audit row")  # WHY: before timestamp creation.
        timestamp_utc = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")  # WHY: UTC.
        row = request.log_row(confirmed, result, message, timestamp_utc)  # WHY: delegate field mapping to model.
        logger.debug("Built timestamped audit row for result %s", result)  # WHY: after row construction.
        return row  # WHY: caller writes this row.

    @staticmethod
    def _write_audit(deps: HandlerDependencies, row: ClientSessionControlLogRow) -> None:
        """Write one audit row through the injected writer."""
        logger.info("Writing client session control audit through handler")  # WHY: before audit boundary.
        deps.audit_writer.write(row)  # WHY: one durable row per request attempt.
        logger.debug("Client session control audit write completed for %s", row.result)  # WHY: after boundary.

    @staticmethod
    def _report(deps: HandlerDependencies, result: str, message: str) -> str:
        """Print the final result and return its result key."""
        logger.info("Reporting client session control result %s", result)  # WHY: before final output.
        deps.print_fn(message)  # WHY: operator needs one clear final result line.
        logger.debug("Reported client session control result %s", result)  # WHY: after final output.
        return result  # WHY: tests and callers inspect this stable key.
