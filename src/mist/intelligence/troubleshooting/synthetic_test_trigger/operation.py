"""Menu 283 operation for on-demand Mist synthetic tests."""

from __future__ import annotations  # WHY: keep annotations lazy for MistHelper menu imports.

import logging  # WHY: trace each operator prompt, API call, poll, and export.
import time  # WHY: bounded polling needs monotonic time and sleep.
from collections.abc import Callable  # WHY: tests inject prompt, selector, exporter, and clock seams.
from dataclasses import dataclass  # WHY: bundle runtime seams and keep constructors small.

from src.foundation.runtime.config.source_dependency_resolver import (
    SourceDependencyResolver,
)  # WHY: access shared session/exporter.
from src.foundation.support.utils.input_utils import (
    InputUtils,
)  # WHY: all interactive input must use the EOF-safe helper.
from src.interfaces.visualization.ui.prompt_utils import (
    PromptUtils,
)  # WHY: reuse the standard site and device prompt helpers.
from src.mist.intelligence.troubleshooting.synthetic_test_trigger.client import (
    SyntheticTestClient,
)  # WHY: API client seam.
from src.mist.intelligence.troubleshooting.synthetic_test_trigger.models import (
    DEFAULT_POLL_INTERVAL_SECONDS,
    DEFAULT_TIMEOUT_SECONDS,
    EXPORT_ENDPOINT_NAME,
    EXPORT_FILENAME,
    ExportRowBuilder,
    RequestBodyBuilder,
    ResultNormalizer,
    SyntheticTestRequest,
    SyntheticTestResult,
)

logger = logging.getLogger(__name__)  # WHY: callers can filter logs to this feature package.

InputReader = Callable[[str, str], str]  # WHY: tests inject deterministic prompt answers.
SiteSelector = Callable[[], str | None]  # WHY: tests inject a selected site without a CSV file.
DeviceSelector = Callable[[str, str], str | None]  # WHY: tests inject a selected device without inventory.
Exporter = Callable[[list[dict[str, object]], str, str, list[str]], bool]  # WHY: tests capture export rows.


class RuntimePromptReader:
    """Read operator input through the shared EOF-safe helper."""

    @staticmethod
    def read(prompt: str, context: str) -> str:
        """Return one trimmed operator answer."""
        answer = InputUtils.safe_input(prompt, context=context)  # WHY: shared helper handles EOF and interrupts.
        return answer.strip()  # WHY: prompt comparisons should ignore surrounding spaces.


@dataclass(frozen=True)
class SyntheticTestRuntime:
    """Bundle runtime dependencies for the trigger workflow."""

    client: SyntheticTestClient  # WHY: all Mist API calls go through this seam.
    site_selector: SiteSelector  # WHY: site prompt can be replaced by tests.
    device_selector: DeviceSelector  # WHY: device prompt can be replaced by tests.
    input_reader: InputReader  # WHY: parameter prompts can be replaced by tests.
    exporter: Exporter  # WHY: export can be captured in tests without writing files.
    sleep_fn: Callable[[float], None]  # WHY: tests must not wait for real poll intervals.
    monotonic_fn: Callable[[], float]  # WHY: tests control timeout behavior.

    @classmethod
    def from_runtime(cls) -> SyntheticTestRuntime:
        """Build runtime seams from the shared MistHelper dependencies."""
        client = SyntheticTestClient(SourceDependencyResolver.apisession)  # WHY: reuse the active Mist API session.
        return cls(  # WHY: keep construction in one typed place for menu entry.
            client=client,
            site_selector=PromptUtils.select_site_with_logging,
            device_selector=PromptUtils.select_device_id_from_inventory,
            input_reader=RuntimePromptReader.read,
            exporter=cls._export_rows,
            sleep_fn=time.sleep,
            monotonic_fn=time.monotonic,
        )

    @staticmethod
    def _export_rows(rows: list[dict[str, object]], filename: str, api_name: str, fieldnames: list[str]) -> bool:
        """Write rows through the shared DataExporter."""
        logger.info("Writing synthetic test trigger rows=%d to %s", len(rows), filename)  # WHY: action log.
        written = SourceDependencyResolver.DataExporter.write_with_format_selection(  # WHY: shared export path.
            rows,
            filename,
            api_function_name=api_name,
            fieldnames=fieldnames,
        )
        logger.debug("Synthetic test trigger export finished written=%s", written)  # WHY: result summary.
        return bool(written)  # WHY: operation reports export failure through a boolean.


class SyntheticTestTriggerRunner:
    """Run the prompts, trigger, poll, report, and export steps."""

    def __init__(self, runtime: SyntheticTestRuntime, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        """Store runtime seams and timeout controls."""
        self._runtime = runtime  # WHY: all side effects pass through injectable seams.
        self._timeout_seconds = timeout_seconds  # WHY: tests and environment can shorten the wait.

    def run(self) -> SyntheticTestResult | None:
        """Execute one on-demand synthetic test trigger."""
        logger.info("Menu #283: Starting on-demand synthetic test trigger")  # WHY: name the menu row in logs.
        request = self._select_request()  # WHY: prompt the operator before any API call.
        if request is None:  # WHY: selection or parameter validation can stop the run safely.
            return None  # WHY: no trigger was sent.
        if not self._confirm(request):  # WHY: the trigger must require explicit consent.
            logger.warning("Synthetic test trigger cancelled before API call")  # WHY: operator needs clear result.
            return None  # WHY: do not send a Mist API trigger.
        self._runtime.client.trigger(request)  # WHY: send the one authorized trigger.
        result = self._poll(request)  # WHY: wait for a result or a clear timeout.
        self._report(request, result)  # WHY: operator reads the result immediately.
        self._export(request, result)  # WHY: acceptance criteria require a CSV export.
        return result  # WHY: tests assert the final workflow state.

    def _select_request(self) -> SyntheticTestRequest | None:
        """Prompt the operator for site, scope, and parameters."""
        site_id = self._runtime.site_selector()  # WHY: reuse shared site selection behavior.
        if not site_id:  # WHY: no valid site means every endpoint would fail.
            logger.error("No site selected for synthetic test trigger")  # WHY: clear stop reason.
            return None  # WHY: stop before parameter prompts.
        scope_answer = self._runtime.input_reader(self._scope_prompt(), "synthetic_test_scope")  # WHY: choose flow.
        if scope_answer == "1":  # WHY: site scope starts a whole-site validation.
            return self._site_request(site_id)  # WHY: build site request.
        if scope_answer == "2":  # WHY: device scope starts one device test.
            return self._device_request(site_id, "all")  # WHY: allow AP, switch, or gateway.
        if scope_answer == "3":  # WHY: RADIUS scope must use a switch.
            return self._radius_request(site_id)  # WHY: build switch RADIUS request.
        logger.error("Unknown synthetic test scope answer '%s'", scope_answer[:20])  # WHY: reject unsafe guesses.
        return None  # WHY: stop before an unintended trigger.

    def _site_request(self, site_id: str) -> SyntheticTestRequest:
        """Build a site-level synthetic test request from prompts."""
        email = self._runtime.input_reader("Notification email (optional): ", "synthetic_site_email")  # WHY: optional.
        body = RequestBodyBuilder.site(email)  # WHY: body follows the OpenAPI `synthetictest` schema.
        summary = {"scope": "site", "site_id": site_id, "test_type": "site"}  # WHY: export uses safe request data.
        return SyntheticTestRequest("site", site_id, body, summary, poll_query={"by": "user"})  # WHY: poll search.

    def _device_request(self, site_id: str, device_type: str) -> SyntheticTestRequest | None:
        """Build a device-level synthetic test request from prompts."""
        device_id = self._runtime.device_selector(site_id, device_type)  # WHY: reuse inventory device selection.
        if not device_id:  # WHY: no valid device means the endpoint cannot run.
            logger.error("No device selected for synthetic test trigger")  # WHY: clear stop reason.
            return None  # WHY: stop before test parameter prompts.
        test_type = self._runtime.input_reader("Synthetic test type: ", "synthetic_device_type")  # WHY: required.
        fields = self._read_key_value_fields()  # WHY: optional fields vary by test type.
        body = RequestBodyBuilder.device(test_type, fields)  # WHY: body follows `synthetictest_device`.
        summary = self._request_summary("device", site_id, device_id, body)  # WHY: remove any secret fields.
        return SyntheticTestRequest("device", site_id, body, summary, device_id=device_id)  # WHY: dispatch context.

    def _radius_request(self, site_id: str) -> SyntheticTestRequest | None:
        """Build a switch RADIUS synthetic test request from prompts."""
        device_id = self._runtime.device_selector(site_id, "switch")  # WHY: the RADIUS check runs from a switch.
        if not device_id:  # WHY: no switch means no RADIUS test endpoint.
            logger.error("No switch selected for RADIUS synthetic test")  # WHY: clear stop reason.
            return None  # WHY: stop before credential prompts.
        user = self._runtime.input_reader("RADIUS username: ", "synthetic_radius_user")  # WHY: schema requires user.
        password = self._runtime.input_reader("RADIUS shared secret: ", "synthetic_radius_password")  # WHY: schema.
        profile = self._runtime.input_reader("Access profile [dot1x]: ", "synthetic_radius_profile")  # WHY: default.
        body = RequestBodyBuilder.radius(user, password, profile or "dot1x")  # WHY: body follows RADIUS schema.
        summary = self._request_summary("radius", site_id, device_id, body)  # WHY: removes the password field.
        return SyntheticTestRequest("radius", site_id, body, summary, device_id=device_id)  # WHY: dispatch context.

    def _confirm(self, request: SyntheticTestRequest) -> bool:
        """Return True only when the operator enters lowercase y."""
        logger.warning("Synthetic test request summary: %s", request.summary)  # WHY: show safe data before consent.
        answer = self._runtime.input_reader("Send this synthetic test now? [y/N]: ", "synthetic_confirm")  # WHY: AC.
        return answer == "y"  # WHY: every other answer cancels by design.

    def _poll(self, request: SyntheticTestRequest) -> SyntheticTestResult:
        """Poll until a complete result arrives or the timeout passes."""
        deadline = self._runtime.monotonic_fn() + self._timeout_seconds  # WHY: monotonic time avoids clock jumps.
        while self._runtime.monotonic_fn() <= deadline:  # WHY: bounded polling prevents endless runs.
            result = self._read_result(request)  # WHY: normalize one API poll.
            if result is not None:  # WHY: a completed result ends the loop.
                return result  # WHY: caller reports and exports the result.
            self._sleep_before_next_poll(deadline)  # WHY: avoid a tight API loop.
        return SyntheticTestResult.timeout(self._timeout_seconds)  # WHY: no result arrived before deadline.

    def _read_result(self, request: SyntheticTestRequest) -> SyntheticTestResult | None:
        """Return a completed result from one poll, or None."""
        response = self._runtime.client.poll_once(request)  # WHY: read one result endpoint.
        result = self._extract_result(request, response)  # WHY: site and device responses differ.
        if result is not None and not self._result_matches_request(request, result):  # WHY: ignore old site rows.
            return None  # WHY: caller must poll again until the triggered run appears.
        if result is None or not ResultNormalizer.is_complete(result):  # WHY: incomplete rows continue polling.
            return None  # WHY: caller sleeps and retries.
        return ResultNormalizer.to_result(result)  # WHY: caller needs one normalized result object.

    def _sleep_before_next_poll(self, deadline: float) -> None:
        """Sleep until the next poll without passing the deadline by much."""
        remaining = max(0.0, deadline - self._runtime.monotonic_fn())  # WHY: avoid negative sleep values.
        delay = min(DEFAULT_POLL_INTERVAL_SECONDS, remaining)  # WHY: stop promptly when timeout is near.
        if delay > 0:  # WHY: zero delay means the next loop will time out.
            self._runtime.sleep_fn(delay)  # WHY: injectable sleep keeps tests fast.

    def _export(self, request: SyntheticTestRequest, result: SyntheticTestResult) -> None:
        """Write one safe export row."""
        row = ExportRowBuilder.build(request, result)  # WHY: combine request summary and result safely.
        exported = self._runtime.exporter([row], EXPORT_FILENAME, EXPORT_ENDPOINT_NAME, ExportRowBuilder.FIELDNAMES)
        if not exported:  # WHY: failed writes need a visible operator error.
            logger.error("Synthetic test trigger could not write %s", EXPORT_FILENAME)  # WHY: name missing file.

    @staticmethod
    def _extract_result(request: SyntheticTestRequest, response: object) -> dict[str, object] | None:
        """Return the result row for the selected scope."""
        if request.scope == "site":  # WHY: site polling reads the search response.
            return ResultNormalizer.first_site_result(response)  # WHY: site result is inside results.
        return ResultNormalizer.device_result(response)  # WHY: device and RADIUS polling read one device result.

    @staticmethod
    def _result_matches_request(request: SyntheticTestRequest, result: dict[str, object]) -> bool:
        """Return True when one poll row belongs to this trigger request."""
        if request.scope != "site":  # WHY: device endpoints read the current result of the selected device.
            return True  # WHY: only the site search endpoint can return an unrelated historical row.
        if not SyntheticTestTriggerRunner._site_result_created_by_user(result):  # WHY: scheduled runs are unrelated.
            logger.debug("Ignoring synthetic test row with by=%s", result.get("by", ""))  # WHY: explain skip.
            return False  # WHY: keep polling for the manual run.
        if not SyntheticTestTriggerRunner._site_result_is_new(request, result):  # WHY: old rows predate trigger.
            logger.debug(  # WHY: explain why the poll continues without accepting a stale row.
                "Ignoring stale synthetic test row timestamp=%s triggered_at=%s",
                result.get("timestamp", ""),
                request.triggered_at,
            )
            return False  # WHY: keep polling until a fresh row arrives or timeout.
        return True  # WHY: row identity matches the request closely enough to report.

    @staticmethod
    def _site_result_created_by_user(result: dict[str, object]) -> bool:
        """Return True when Mist names the manual trigger as the creator."""
        creator = result.get("by")  # WHY: the live search row identifies scheduled runs as MARVIS.
        if creator is None:  # WHY: older payloads can omit the creator field.
            return True  # WHY: timestamp remains the required identity guard.
        return str(creator).lower() == "user"  # WHY: only the operator-triggered site run is valid here.

    @staticmethod
    def _site_result_is_new(request: SyntheticTestRequest, result: dict[str, object]) -> bool:
        """Return True when a site result timestamp is at or after the trigger."""
        timestamp = result.get("timestamp")  # WHY: live rows use this field for the result time.
        if timestamp is None:  # WHY: no timestamp means the row cannot be tied to this trigger.
            return False  # WHY: a timeout is safer than reporting an unrelated row.
        try:
            result_time = float(timestamp)  # WHY: Mist returns timestamps as JSON numbers.
        except (TypeError, ValueError):
            logger.debug("Ignoring synthetic test row with invalid timestamp=%s", timestamp)  # WHY: explain skip.
            return False  # WHY: invalid time cannot prove the row belongs to this request.
        return result_time >= request.triggered_at  # WHY: the accepted row must not predate the trigger.

    @staticmethod
    def _scope_prompt() -> str:
        """Return the operator prompt for the trigger scope."""
        return "Select synthetic test scope: 1) site 2) one device 3) RADIUS from one switch: "

    @staticmethod
    def _read_key_value_pairs(raw_answer: str) -> dict[str, str]:
        """Parse comma-separated key=value prompt input."""
        pairs: dict[str, str] = {}  # WHY: optional body fields start empty.
        for chunk in raw_answer.split(","):  # WHY: one prompt collects the variable optional fields.
            if "=" in chunk:  # WHY: ignore malformed entries instead of guessing.
                key, value = chunk.split("=", 1)  # WHY: values can contain later equals signs.
                pairs[key.strip()] = value.strip()  # WHY: strip spaces for OpenAPI field names.
        return pairs  # WHY: caller validates accepted keys.

    def _read_key_value_fields(self) -> dict[str, str]:
        """Prompt for optional device test fields."""
        prompt = "Optional fields as key=value pairs, comma separated (blank for none): "  # WHY: flexible schema.
        raw_answer = self._runtime.input_reader(prompt, "synthetic_device_fields")  # WHY: one EOF-safe prompt.
        return self._read_key_value_pairs(raw_answer)  # WHY: body builder validates each accepted key.

    @staticmethod
    def _request_summary(scope: str, site_id: str, device_id: str, body: dict[str, object]) -> dict[str, object]:
        """Return a safe request summary for logs and export."""
        safe_body = {key: value for key, value in body.items() if key != "password"}  # WHY: never export password.
        summary = {"scope": scope, "site_id": site_id, "device_id": device_id}  # WHY: core request identity.
        summary["test_type"] = str(body.get("type", scope))  # WHY: RADIUS endpoint has no `type` field.
        summary.update(safe_body)  # WHY: non-secret body fields help operators understand the request.
        return summary  # WHY: caller stores only this safe summary.

    @staticmethod
    def _report(request: SyntheticTestRequest, result: SyntheticTestResult) -> None:
        """Print the final result to the operator through logging."""
        logger.warning(  # WHY: warnings reach the default console in this project.
            "Synthetic test finished scope=%s site=%s device=%s status=%s timed_out=%s result=%s",
            request.scope,
            request.site_id,
            request.device_id or "",
            result.status,
            result.timed_out,
            result.raw,
        )


class SyntheticTestTrigger:
    """Menu handler for triggering one Mist synthetic test on demand."""

    @staticmethod
    def run() -> None:
        """Run menu 283 with shared runtime dependencies."""
        runtime = SyntheticTestRuntime.from_runtime()  # WHY: bind shared MistHelper dependencies at run time.
        runner = SyntheticTestTriggerRunner(runtime)  # WHY: keep workflow testable through runner seams.
        runner.run()  # WHY: the menu contract expects a no-argument handler.
