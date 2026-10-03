"""Menu operation for showing SSR registration commands."""

from __future__ import annotations  # WHY: keep annotations import-safe during bootstrap.

import logging  # WHY: record operation action boundaries without logging secrets.
from pathlib import Path  # WHY: build Windows-safe output paths.
from typing import Any  # WHY: Mist response and resolver attributes are dynamic.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,
)  # WHY: access the shared session and org helper.
from src.foundation.support.utils.input_utils import InputUtils  # WHY: use EOF-safe input for the y/N write prompt.
from src.mist.resources.gateway.ssr_registration.client import SsrRegistrationClient  # WHY: isolate the Mist API call.
from src.mist.resources.gateway.ssr_registration.model import (
    RegistrationCommandSet,
)  # WHY: normalize and format response data.

logger = logging.getLogger(__name__)  # WHY: let operators filter operation log records by module.

FILE_NAME = "SsrRegistrationCommands.txt"  # WHY: the assignment requires this exact file name.
SHOW_PROMPT = (  # WHY: the console copy can land in a redirected stdout file, so the operator approves it first.
    "The registration commands hold a sensitive code. Print them to the console? (y/N): "
)
PROMPT = "Write registration commands to data/SsrRegistrationCommands.txt? (y/N): "  # WHY: protect sensitive text.


class SsrRegistrationCommands:
    """Print SSR registration commands and optionally write them to disk."""

    output_path = Path("data") / FILE_NAME  # WHY: all operator artifacts belong under the data directory.
    client_class = SsrRegistrationClient  # WHY: tests replace the client without network access.

    @staticmethod
    def run() -> None:
        """Run menu 288."""
        logger.info("Menu #288: Starting SSR registration command read")  # WHY: audit the menu entry.
        org_id = SsrRegistrationCommands._resolve_org_id()  # WHY: the API path requires the organization.
        response = SsrRegistrationCommands._read_commands(org_id)  # WHY: read before any write prompt.
        if not SsrRegistrationCommands._response_ok(response):  # WHY: non-2xx responses hold no usable command text.
            SsrRegistrationCommands._print_http_error(response)  # WHY: print status and stop without a traceback.
            return  # WHY: do not parse or write a failed response.
        text = SsrRegistrationCommands._format_response(response)  # WHY: create console text outside logging.
        if not text:  # WHY: an empty body cannot help the operator onboard a router.
            print("No SSR registration commands were returned.")  # WHY: give a clear operator result.
            return  # WHY: no text means no file should be written.
        if not SsrRegistrationCommands._confirm_show():  # WHY: the console copy is as sensitive as the file copy.
            SsrRegistrationCommands._print_declined_footer()  # WHY: explain why no sensitive code was printed.
            return  # WHY: an operator who declines the print also gets no file prompt.
        SsrRegistrationCommands._print_commands(text)  # WHY: print sensitive commands only after consent.
        if SsrRegistrationCommands._confirm_write():  # WHY: the file write is a second, separate consent.
            SsrRegistrationCommands._write_commands(text)  # WHY: persist the text only after confirmation.
        logger.debug("Menu #288: Finished SSR registration command read")  # WHY: action summary without secrets.

    @staticmethod
    def _resolve_org_id() -> str:
        """Return the active organization identifier."""
        logger.info("Resolving the organization for SSR registration commands")  # WHY: log before shared lookup.
        org_id = SourceDependencyResolver.ConfigUtils.get_cached_or_prompted_org_id()  # WHY: reuse MistHelper org flow.
        logger.debug("Resolved the organization for SSR registration commands org=%s", org_id)  # WHY: result summary.
        return str(org_id)  # WHY: format the path with text.

    @staticmethod
    def _read_commands(org_id: str) -> Any:
        """Read the registration commands from Mist."""
        logger.info("Creating the SSR registration command client")  # WHY: log before dependency construction.
        client = SsrRegistrationCommands.client_class(SourceDependencyResolver.apisession)  # WHY: use shared session.
        logger.debug("Created the SSR registration command client")  # WHY: construction finished.
        return client.fetch_commands(org_id)  # WHY: client logs the API action and status.

    @staticmethod
    def _response_ok(response: Any) -> bool:
        """Return whether a Mist response has a 2xx status."""
        status_code = getattr(response, "status_code", None)  # WHY: mistapi stores HTTP status here.
        return isinstance(status_code, int) and 200 <= status_code < 300  # WHY: every 2xx response is accepted.

    @staticmethod
    def _print_http_error(response: Any) -> None:
        """Print a concise HTTP error without a traceback."""
        status_code = getattr(response, "status_code", None)  # WHY: no status means no HTTP answer arrived.
        logger.warning("SSR registration command read failed with HTTP %s", status_code)  # WHY: log status only.
        print(f"The API returned HTTP {status_code}.")  # WHY: the operator needs the status code.

    @staticmethod
    def _format_response(response: Any) -> str:
        """Return printable command text from a successful response."""
        command_set = RegistrationCommandSet.from_payload(getattr(response, "data", None))  # WHY: normalize JSON.
        logger.debug("SSR registration command payload has_text=%s", command_set.has_text())  # WHY: no values logged.
        return command_set.to_text() if command_set.has_text() else ""  # WHY: suppress an empty title-only output.

    @staticmethod
    def _print_commands(text: str) -> None:
        """Print command text to the console without logging it."""
        line_count = len(text.splitlines())  # WHY: count lines without exposing command content.
        logger.info("Printing SSR registration commands to the console lines=%d", line_count)  # WHY: action log.
        print(text, end="")  # WHY: the operation exists so the operator can read and copy this text.
        logger.debug("Printed SSR registration commands to the console lines=%d", line_count)  # WHY: summary only.

    @staticmethod
    def _confirm_show() -> bool:
        """Return whether the operator approved the console print."""
        logger.info("Prompting for SSR registration command console print approval")  # WHY: action log before prompt.
        answer = InputUtils.safe_input(SHOW_PROMPT, default_value="N", context="ssr_registration_commands_show")
        approved = answer.strip().lower() == "y"  # WHY: only y or Y approves the sensitive console print.
        logger.debug("SSR registration command console print approved=%s", approved)  # WHY: log the decision only.
        return approved  # WHY: caller uses this guard before printing the code.

    @staticmethod
    def _confirm_write() -> bool:
        """Return whether the operator approved the file write."""
        logger.info("Prompting for SSR registration command file write approval")  # WHY: action log before prompt.
        answer = InputUtils.safe_input(PROMPT, default_value="N", context="ssr_registration_commands_write")
        approved = answer.strip().lower() == "y"  # WHY: only y or Y approves the sensitive file write.
        logger.debug("SSR registration command file write approved=%s", approved)  # WHY: log the decision only.
        return approved  # WHY: caller uses this guard before writing the file.

    @staticmethod
    def _write_commands(text: str) -> None:
        """Write command text to the protected data file."""
        path = SsrRegistrationCommands.output_path  # WHY: tests can replace the destination path.
        logger.info("Writing SSR registration commands to %s", path)  # WHY: log the destination, not the content.
        path.parent.mkdir(parents=True, exist_ok=True)  # WHY: a fresh worktree may not hold a data directory.
        path.write_text(text, encoding="utf-8")  # WHY: persist exact command text after approval.
        logger.debug("Wrote SSR registration commands to %s", path)  # WHY: confirm write without the secret.

    @staticmethod
    def _print_declined_footer() -> None:
        """Print the declined sensitive-output footer."""
        logger.info("SSR registration commands were not printed because write approval was declined")  # WHY: audit.
        print("Registration commands were not printed or written because they include a sensitive code.")  # WHY.
