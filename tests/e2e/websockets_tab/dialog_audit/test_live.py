"""Opt-in real portal form inspection. No live operation may start."""

import inspect  # Check the installed SDK observation path before the opt-in start.
import json  # Exercise real malformed JSON behavior without manufacturing a live failure.
import time  # Record actual inspection duration, not a predicted runtime.
from pathlib import Path  # Load the reviewed template's exact asset list.
from urllib.parse import urlsplit  # Normalize only the explicitly supplied origin.

import pytest  # Keep live work opt-in and report capability failures distinctly.
from playwright.sync_api import expect  # Normal-user visible state checks respect portal CSP.

from tests.e2e.websockets_tab.dialog_audit.support.inventory import InventoryBuilder  # Reconcile the real live catalog.
from tests.e2e.websockets_tab.dialog_audit.support.journeys import (
    DialogInspector,
    IsolatedPage,
)  # Normal-user controls.
from tests.e2e.websockets_tab.dialog_audit.support.policy import (
    LiveGate,
    LiveRequestPolicy,
    ReadonlyLifecyclePolicy,
    ReadScope,
)  # Default deny with one separately selected observation exception.
from tests.e2e.websockets_tab.dialog_audit.support.reporting import AuditReportWriter  # No raw targets or screenshots.
from tests.e2e.websockets_tab.dialog_audit.test_inventory import (
    LiveReadTrap,
)  # Reuse the independent no-network response trap.


class TestLive:
    """Read real forms and choices. Missing choices remain blocked, not defects."""

    def test_real_portal_dialogs(self, browser, audit_inventory, request):
        if request.config.getoption("--ws-audit-mode") != "live-inspection":
            pytest.skip("BLOCKED: live inspection requires explicit opt-in and an authorized URL.")  # Not a pass.
        supplied = request.config.getoption("--ws-audit-base-url")  # Never guess the portal or its test port.
        try:
            LiveGate.validate_url(supplied)  # Accept localhost:8055 or the user-selected isolated port.
            ReadScope.verify_sdk()  # All picker SDK implementations must still use GET.
        except (ValueError, ImportError, AttributeError, OSError):
            pytest.fail(
                "BLOCKED: the authorized origin or installed selector GET evidence is unavailable.", pytrace=False
            )  # No secrets.
        parsed = urlsplit(supplied)  # URL credentials and ambiguous path/query values were rejected.
        origin = f"{parsed.scheme}://{parsed.netloc}"  # Bind every forwarded GET to one exact origin.
        renderer = IsolatedPage(Path(__file__).resolve().parents[4], audit_inventory)  # Exact reviewed asset set.
        with browser.new_context(service_workers="block", accept_downloads=False) as context:
            policy = LiveRequestPolicy(origin, renderer.responses())  # No request starts before installation.
            policy.install(context)  # Block HTTP writes, unknown reads, redirects, and all WebSockets.
            page = context.new_page()  # Use no credentials file, screenshot, trace, or unguarded popup.
            page.set_default_timeout(15000)  # Bound every normal-user selection.
            self.inspect(page, policy, audit_inventory, request)  # Read-only inspection through real controls.
            assert policy.denied == []  # The actual browser must not attempt any unapproved handler.

    @staticmethod
    def inspect(page, policy, inventory, request):
        started = time.monotonic()  # Measure only this real read-only journey.
        try:
            page.goto(policy.origin + "/websockets", wait_until="domcontentloaded", timeout=15000)  # Real HTTP GET.
            page.locator(".ws-catalog-entry").first.wait_for()  # An unreachable/not-ready portal cannot pass.
            live = TestLive.catalog_inventory(policy.catalog, inventory)  # Fail closed on catalog/source drift.
            page.set_default_timeout(3000)  # Limit each live control failure before the total traversal deadline.
            visible = page.locator(".ws-catalog-entry").evaluate_all(
                "(nodes) => nodes.map(node => node.dataset.key)"
            )  # Real buttons.
            keys = [entry["key"] for entry in live["entries"]]  # Only reconciled public catalog keys.
            if InventoryBuilder.reconcile(keys, visible):
                pytest.fail(
                    "FAILED: the live catalog and rendered operations differ.", pytrace=False
                )  # No raw target data.
            records = DialogInspector(
                page, live, live=True
            ).inspect_all()  # Choose current site/map/device values only.
        except Exception:
            keys = [entry["key"] for entry in inventory["entries"]]  # Source denominator stays present after failure.
            records = [
                {
                    "key": key,
                    "status": "blocked",
                    "observations": [
                        "The live portal, catalog, or reviewed read-only dialog inspection was unavailable."
                    ],
                }
                for key in keys
            ]  # No raw browser exception or private URL enters evidence.
        report = AuditReportWriter.build(
            keys, records, time.monotonic() - started, inventory["sdk_version"]
        )  # Sanitized results.
        report["live_inspection"] = {
            **report["isolated_inspection"],
            "status": (
                "blocked"
                if policy.errors or any(record["status"] == "blocked" for record in records)
                else "failed" if any(record["status"] == "failed" for record in records) else "passed"
            ),
            "approved_get_attempts": policy.reads,
            "blocked_request_categories": policy.denied_categories,
            "read_blockers": policy.errors,
            "session_list": "substituted locally with no sessions",
            "theme_menu": "substituted locally with no themes",
            "handler_evidence": "reviewed checkout and installed SDK GET methods; deployed backend not attested",
            "picker_response_reuse": "approved live picker reads reused within this audit context only",
            "target_scope": "all returned sites and maps, serially; counts cover portal-returned choices only",
        }  # Disclose substitution.
        report["isolated_inspection"] = {
            "measured_dialogs": 0,
            "totals": {},
            "records": [],
            "status": "not-run",
        }  # No mixed evidence.
        destination = request.config.getoption("--ws-audit-artifacts")  # Evidence stays local and owner-only.
        if destination:
            AuditReportWriter.write(report, destination)  # Write before reporting any blocker or finding.
        TestLive.assert_results(records, policy)  # No skipped/blocked result becomes an audit pass.

    @staticmethod
    def catalog_inventory(payload, source):
        if not isinstance(payload, dict) or not payload.get("ready"):
            raise ValueError("The live catalog is unavailable or not ready.")  # Do not pretend forms ran.
        entries = payload.get("channels", []) + payload.get("utilities", [])  # Actual live catalog, never a fixture.
        expected = {entry["key"]: entry for entry in source["entries"]}  # Source is the independent revision oracle.
        if InventoryBuilder.reconcile(list(expected), [entry["key"] for entry in entries]):
            raise ValueError(
                "The live inventory differs from the reviewed source."
            )  # Unknown keys cannot authorize traffic.
        for entry in entries:
            if {key: value for key, value in entry.items() if key != "locked"} != {
                key: value for key, value in expected[entry["key"]].items() if key != "locked"
            }:
                raise ValueError(
                    "The live operation definition differs from the reviewed source."
                )  # Exact schema/purpose evidence.
        return {
            **source,
            "entries": entries,
            "payload": payload,
        }  # Preserve source definitions and real lock/readiness values.

    @staticmethod
    def assert_results(records, policy):
        if policy.denied:
            pytest.fail(
                "FAILED: the live page attempted an unapproved request. The guard blocked it.", pytrace=False
            )  # No bodies.
        if policy.errors or any(record["status"] == "blocked" for record in records):
            pytest.fail(
                "BLOCKED: an approved read failed or a selector has no available choices.", pytrace=False
            )  # No invented defect.
        failed = [record["key"] for record in records if record["status"] == "failed"]  # Public keys only.
        assert records and not failed, "FAILED: live dialog observations require review for keys " + ", ".join(
            failed
        )  # Full denominator.


class TestReadonlyLive:
    """One user-authorized observation subscription, not generalized live utility execution."""

    def test_site_device_stats_owned_lifecycle(self, browser, audit_inventory, request):
        if request.config.getoption("--ws-audit-mode") != "live-readonly":
            pytest.skip("Opt-in exact-key observation lifecycle was not selected.")
        self.verify_source(audit_inventory)  # Verify source and installed SDK path before any live traffic.
        supplied = request.config.getoption("--ws-audit-base-url")
        LiveGate.validate_url(supplied)  # Explicit same-origin URL; do not guess authentication.
        renderer = IsolatedPage(Path(__file__).resolve().parents[4], audit_inventory)
        started = time.monotonic()
        with browser.new_context(service_workers="block", accept_downloads=False) as context:
            policy = ReadonlyLifecyclePolicy(supplied.rstrip("/"), renderer.responses())
            policy.install(context)  # Route before page creation; all browser WebSockets remain denied.
            page = context.new_page()
            page.set_default_timeout(15000)
            outcome = "blocked"
            try:
                self.choose_and_observe(page, policy, audit_inventory)
                outcome = "passed" if "live" in policy.states else "blocked"
            except Exception:
                if "failed" in policy.states and not policy.lifecycle_errors:
                    outcome = "failed"  # A remote stream refusal is not a harness response-contract failure.
                else:
                    policy.lifecycle_errors.append("The bounded visible observation journey was unavailable.")
            finally:
                self.stop_owned(page, policy)  # Clean up only the response-issued own session, even after failure.
                if outcome != "failed" and (not policy.latest or policy.latest.get("state") != "stopped"):
                    outcome = "blocked"  # Stop verification is mandatory, not inferred from accepted POST.
                report = AuditReportWriter.build(
                    [entry["key"] for entry in audit_inventory["entries"]],
                    [{"key": entry["key"], "status": "skipped"} for entry in audit_inventory["entries"]],
                    sdk_version=audit_inventory["sdk_version"],
                )  # This targeted journey never claims all-form inspection in the same run.
                report["live_subscription"] = {
                    "key": policy.KEY,
                    "status": outcome,
                    "remote_stream": (
                        "failed"
                        if "failed" in policy.states
                        else "subscribed" if "live" in policy.states else "not-observed"
                    ),
                    "harness_validation": "failed" if policy.lifecycle_errors or policy.denied else "passed",
                    "states": sorted(policy.states),
                    "event_count": policy.event_count,
                    "output": (
                        "data" if policy.event_count else "no-data" if "live" in policy.states else "not-observed"
                    ),
                    "stopped_verified": bool(policy.latest and policy.latest.get("state") == "stopped"),
                    "message_reads": policy.message_reads,
                    "stop_attempts": policy.stop_attempts,
                    "duration_seconds": round(time.monotonic() - started, 3),
                    "errors": policy.lifecycle_errors,
                    "source": [
                        "ChannelStreamRunner/StartRequestChecker/SubscriptionCoordinator",
                        "mistapi.websockets.sites.DeviceStatsEvents",
                    ],
                }  # No IDs, labels, raw events, browser errors, screenshots, or credentials.
                destination = request.config.getoption("--ws-audit-artifacts")
                if destination:
                    AuditReportWriter.write(report, destination)
            assert policy.denied == [], "The guard blocked an unexpected browser request."
            assert "failed" not in policy.states, "FAILED: the owned remote observation stream reported failed."
            assert (
                not policy.lifecycle_errors and outcome == "passed"
            ), "BLOCKED: the exact observation subscription or owned stopped state was not verified."

    @staticmethod
    def verify_source(inventory):
        from mistapi.websockets.sites import DeviceStatsEvents  # Installed SDK, not a safety display label.

        from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog

        entry = next(item for item in inventory["entries"] if item["key"] == ReadonlyLifecyclePolicy.KEY)
        assert entry in inventory["payload"]["channels"]  # Server source classification, not JS-added entryType.
        assert "/sites/{site_id}/stats/devices" in inspect.getsource(DeviceStatsEvents.__init__)
        definition = ChannelCatalog().get(ReadonlyLifecyclePolicy.KEY)
        assert definition is not None and definition.build_paths(
            {"site_id": ("11111111-2222-3333-4444-555555555555",)}
        ) == (
            "/sites/11111111-2222-3333-4444-555555555555/stats/devices",
        )  # Actual server path builder.

    @staticmethod
    def choose_and_observe(page, policy, inventory):
        page.goto(policy.origin + "/websockets", wait_until="domcontentloaded")
        page.locator(".ws-catalog-entry").first.wait_for()
        TestLive.catalog_inventory(policy.catalog, inventory)  # Exact deployed catalog/source reconciliation.
        page.get_by_test_id("ws-catalog-entry-" + policy.KEY).click()
        control = page.locator('[data-ws-field="site_id"]')
        expect(control).not_to_contain_text("Loading...", timeout=15000)
        values = control.locator("option").evaluate_all("(nodes) => nodes.map(n => n.value).filter(Boolean)")
        selected = None
        for site in values:  # Try returned sites until actual reviewed device GET proves a populated site.
            resource = "/api/websockets/sites/" + site + "/devices"
            page.evaluate("(url) => fetch(url).then(r => r.json()).then(() => null)", resource)
            cached = policy.cache.get(resource)
            if cached and json.loads(cached[1]).get("rows"):
                selected = site
                break
        if selected is None:
            raise ValueError("No returned site has available devices.")  # Availability blocker, not a bug.
        control.select_option([selected])  # The actual repeatable site control, never hand-built remote paths.
        sites = json.loads(policy.cache["/api/operations/sites"][1])["sites"]
        row = next(item for item in sites if item["id"] == selected)
        policy.arm(selected, row.get("label") or row.get("name") or selected)
        page.locator("#wsStartButton").click()  # Only the exact actual UI body may leave the browser.
        expect(page.locator("#wsSessionState")).to_have_text("State: Live", timeout=15000)
        page.wait_for_timeout(5000)  # Bounded observation; zero events is a valid explicitly reported no-data result.
        assert policy.session_id is not None, "The exact start returned no owned session."

    @staticmethod
    def stop_owned(page, policy):
        if policy.session_id is None or (
            policy.latest and policy.latest.get("state") in {"stopped", "failed", "finished", "timed_out"}
        ):
            return  # No foreign or nonexistent session can be stopped.
        try:
            if page.locator("#wsStopButton").is_enabled():
                page.locator("#wsStopButton").click()  # Normal-user lifecycle first.
            elif not policy.stop_attempts:
                page.evaluate(
                    "(url) => fetch(url, {method:'POST'}).then(() => null)",
                    "/api/websockets/sessions/" + policy.session_id + "/stop",
                )  # Failure cleanup only; exact owned local close still passes the same guard.
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    page.evaluate(
                        "(url) => fetch(url).then(() => null)",
                        "/api/websockets/sessions/" + policy.session_id + "/messages?after=0&limit=500",
                    )  # Observe only the owned session when start-response validation prevented UI selection.
                    if policy.latest and policy.latest.get("state") == "stopped":
                        return
                    page.wait_for_timeout(200)
            expect(page.locator("#wsSessionState")).to_have_text("State: Stopped", timeout=5000)
        except Exception:
            policy.lifecycle_errors.append(
                "The owned session did not verify stopped within five seconds."
            )  # Full denominator.


class TestLiveResponseFailures:
    """Failure simulation remains local, even when the live test file is selected."""

    @pytest.mark.parametrize("status", [401, 403, 429, 500, 503])
    def test_http_4xx_and_5xx_response_is_blocked(self, status):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # No real endpoint or auth state exists.
        trap = LiveReadTrap("GET", policy.origin + "/api/websockets/catalog", status=status)  # HTTP failure mode.
        policy.handle(trap)  # Use the same guard as real inspection.
        assert trap.aborted and not trap.fulfilled and policy.catalog is None  # Refusal cannot supply a catalog.
        assert trap.transmitted == 1 and len(policy.errors) == 1  # One synthetic fetch, never a retry.

    def test_empty_body_response_is_blocked(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # Simulate locally, never against Mist.
        trap = LiveReadTrap("GET", policy.origin + "/api/websockets/catalog")  # Approved read only.
        trap.response.body = lambda: b""  # Empty body must not count as an empty catalog.
        policy.handle(trap)  # Reject before catalog assignment.
        assert trap.aborted and policy.catalog is None and len(policy.errors) == 1  # Explicit blocker.

    def test_malformed_json_response_is_blocked(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # No live request.
        trap = LiveReadTrap("GET", policy.origin + "/api/websockets/catalog")  # Synthetic response.

        def malformed_json():
            return json.loads("{")  # Raise real JSONDecodeError, not an arbitrary mock exception.

        trap.response.json = malformed_json  # Install local malformed response behavior.
        policy.handle(trap)  # The real guard must fail closed.
        assert trap.aborted and policy.catalog is None and len(policy.errors) == 1  # No false catalog success.
        assert policy.errors == ["Live read blocked: JSONDecodeError"]  # Validate the actual parser failure category.
