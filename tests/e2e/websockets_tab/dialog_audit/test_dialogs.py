"""Normal-user inspection of every real catalog form, without submission."""

import time  # Measure actual inspection duration.

from tests.e2e.websockets_tab.dialog_audit.support.inventory import InventoryBuilder  # Complete inventory.
from tests.e2e.websockets_tab.dialog_audit.support.journeys import (
    DialogInspector,
    IsolatedPage,
    LivePickerInspector,
    UtilityExperienceInspector,
)  # Actual catalog controls.
from tests.e2e.websockets_tab.dialog_audit.support.reporting import AuditReportWriter  # Separate blockers.


class TestDialogs:
    """A nonempty measured denominator is mandatory."""

    def test_every_real_form(self, audit_page, audit_inventory, request):
        page, policy = audit_page  # Routing was installed before navigation.
        expected = [entry["key"] for entry in audit_inventory["entries"]]  # Include every locked utility.
        visible = page.locator(".ws-catalog-entry").evaluate_all(
            "(nodes) => nodes.map(node => node.dataset.key)"
        )  # Rendered keys.
        assert not InventoryBuilder.reconcile(expected, visible)  # Detect missing, duplicate, and extra buttons.
        started = time.monotonic()  # Start the bounded measurement before dialog traversal.
        records = DialogInspector(page, audit_inventory).inspect_all()  # Never click an operation start button.
        report = AuditReportWriter.build(
            expected, records, time.monotonic() - started, audit_inventory["sdk_version"]
        )  # Actual duration and SDK.
        cancel_supported = "supported: 1 visible operation-form Cancel control"  # Current form contract.
        assert all(
            record["cancel"] == cancel_supported for record in records
        )  # Preserve visible cancellation evidence.
        assert not any(
            finding["topic"] == "operation-cancel" for record in records for finding in record["ux_review"]["findings"]
        )  # Existing visible Cancel controls are not missing.
        destination = request.config.getoption("--ws-audit-artifacts")  # Saving evidence is opt-in.
        if destination:
            AuditReportWriter.write(report, destination)  # Write restricted JSON and sanitized Markdown only.
        assert (
            report["isolated_inspection"]["measured_dialogs"] == len(expected) > 0
        )  # Prove measured nonempty forms, not just blockers.
        assert any(record.get("selectors") for record in records)  # Prove choices were measured, not only titles.
        assert policy.transmitted == 0  # All approved reads were local responses.
        assert not policy.denied  # Unexpected automatic requests require review.
        failures = [
            record for record in records if record["status"] == "failed"
        ]  # Keep actionable public observations.
        assert not failures, failures  # Fail after all forms and the partial report are recorded.

    def test_cancel_measurement_matches_utility_review(self, audit_page, audit_inventory, monkeypatch):
        page, policy = audit_page  # Use the browser route guard and synthetic selector data.
        original_count = UtilityExperienceInspector.visible_cancel_count  # Keep the real visibility measurement.
        cases = (
            ("visible", "site.stats.clients", "supported: 1 visible operation-form Cancel control", False),
            ("hidden", "location.clients", "unsupported: no visible operation-form Cancel control (0)", True),
            ("missing", "diag.sdkclient", "unsupported: no visible operation-form Cancel control (0)", True),
            (
                "duplicate",
                "site.stats.devices",
                "unsupported: multiple visible operation-form Cancel controls (2)",
                False,
            ),
        )  # Exercise each rendered control state with a distinct operation form.
        for index, (mutation, key, expected_cancel, missing_finding) in enumerate(cases):
            entry = next(item for item in audit_inventory["entries"] if item["key"] == key)  # Real catalog entry.

            def mutate_and_count(inspector, state=mutation):
                controls = page.locator("#wsStartForm [data-testid='ws-cancel-selection-button']")
                if state == "hidden":
                    controls.first.evaluate("(node) => { node.hidden = true; }")
                elif state == "missing":
                    controls.first.evaluate("(node) => node.remove()")
                elif state == "duplicate":
                    controls.first.evaluate("(node) => node.parentElement.appendChild(node.cloneNode(true))")
                return original_count(inspector)  # Count the real rendered result after this synthetic mutation.

            monkeypatch.setattr(
                UtilityExperienceInspector, "visible_cancel_count", mutate_and_count
            )  # Mutate only the local page before the real measurement.
            record = DialogInspector(page, audit_inventory).inspect(entry)  # Inspect without submitting the form.
            topics = [finding["topic"] for finding in record["ux_review"]["findings"]]  # Shared UX evidence.
            assert record["cancel"] == expected_cancel  # Report the exact visible control count.
            assert ("operation-cancel" in topics) is missing_finding  # Share the count with UX findings.
            if index < len(cases) - 1:
                page.reload()  # Reset static form controls before the next synthetic browser state.
        assert policy.transmitted == 0 and not policy.denied  # No live or mutation request is sent.

    def test_forbidden_browser_requests_never_leave_context(self, audit_page):
        page, policy = audit_page  # Use the same installed route boundary as the inspection.
        result = page.evaluate("""async () => {
            const result = [];
            for (const [method, path] of [
                ['POST', '/api/websockets/sessions'],
                ['POST', '/api/operations/run'],
                ['GET', '/api/websockets/sessions/foreign/download'],
                ['POST', '/api/websockets/sessions/foreign/input']
            ]) {
                try { await fetch(path, {method}); result.push('sent'); }
                catch { result.push('blocked'); }
            }
            return result;
        }""")  # Exercise actual browser requests without calling any server handler.
        assert result == ["blocked"] * 4  # Failed requests alone are insufficient without counters.
        assert len(policy.denied) == 4  # Prove each request reached the pre-transmission guard.
        assert policy.transmitted == 0  # No forwarding branch or remote server exists.

    def test_empty_and_failed_site_picker(self, audit_page):
        page, policy = audit_page  # Change selector data only, not the real dialog implementation.
        for payload in ('{"sites":[]}', '{"error":"Synthetic selector failure."}'):
            policy.responses["/api/operations/sites"] = ("application/json", payload)  # Use synthetic failure evidence.
            page.get_by_test_id("ws-catalog-entry-site.stats.clients").click()  # Build the real site picker.
            picker = page.get_by_test_id("ws-field-site_id")  # Read the actual required control.
            picker.locator("option").first.wait_for()  # Allow the async response to update the control.
            page.wait_for_function(
                "!document.querySelector('#wsField-site_id').textContent.includes('Loading...')"
            )  # Bound wait.
            assert picker.evaluate(
                "(node) => node.required && !node.checkValidity()"
            )  # Empty choice blocks submission.
            assert policy.transmitted == 0  # The failed selector never contacts Mist.

    def test_abandonment_removes_stale_controls(self, audit_page):
        page, policy = audit_page  # Work only through guarded real controls.
        page.get_by_test_id("ws-catalog-entry-diag.sdkclient").click()  # Show site, map, and client fields.
        page.get_by_test_id("ws-catalog-entry-org.insights.summary").click()  # Replace the form as a normal user.
        assert (
            page.locator("[data-ws-field]").count() == 0
        )  # Organization-wide streams have no individual target picker.
        assert policy.transmitted == 0 and not policy.denied  # Abandonment must not start an operation.
        cancel_control = page.get_by_role("button", name="Cancel", exact=True)
        assert (
            cancel_control.count() == 1 and cancel_control.is_visible()
        )  # Selected operations expose one visible Cancel control.

    def test_delayed_map_reply_cannot_replace_new_parent(self, audit_page):
        page, policy = audit_page  # Synthetic responses exercise unchanged picker serial handling.
        path = "/api/websockets/sites/" + IsolatedPage.SITE + "/maps"  # Exact approved first-parent read.
        policy.delayed[path] = []  # Hold the old response without forwarding it.
        page.get_by_test_id("ws-catalog-entry-location.clients").click()  # Build the real map picker.
        page.get_by_test_id("ws-field-site_id").select_option(IsolatedPage.SITE)  # Trigger the held old reply.
        page.wait_for_timeout(50)  # Let the guarded request reach the local route callback.
        assert len(policy.delayed[path]) == 1  # Prove an old response is held, not merely a fast successful race.
        page.get_by_test_id("ws-field-site_id").select_option(
            IsolatedPage.OTHER_SITE
        )  # Change the parent before the reply.
        page.wait_for_function(
            "!!document.querySelector('#wsField-map_id option[value=\"44444444-5555-6666-7777-888888888888\"]')"
        )  # Wait for new-parent data.
        for route, content_type, body in policy.delayed[path]:
            route.fulfill(status=200, content_type=content_type, body=body)  # Deliver the delayed local read only.
        page.wait_for_timeout(50)  # Allow the real serial rejection callback to execute.
        choices = page.get_by_test_id("ws-field-map_id").locator('option:not([value=""])')  # Current visible options.
        assert (
            choices.count() == 1 and choices.first.get_attribute("value") == IsolatedPage.OTHER_MAP
        )  # Reject stale scope.
        assert policy.transmitted == 0 and not policy.denied  # Neither selection starts a stream.


class TestContentPolicy:
    """The real portal CSP must not require a browser-security bypass."""

    def test_picker_inspection_respects_application_csp(self, audit_page, audit_inventory):
        from web_portal.services.config import SecurityMiddleware  # Use the actual production CSP definition.

        page, policy = audit_page  # Keep the context-wide egress guard installed.
        policy.page_headers = {"Content-Security-Policy": SecurityMiddleware.CSP_POLICY}  # Do not weaken the policy.
        page.reload()  # Serve real template/assets under the same content policy as the live portal.
        page.locator(".ws-catalog-entry").first.wait_for()  # Require the actual catalog to render again.
        keys = {"site.stats.clients", "location.clients", "diag.sdkclient"}  # Exercise each dependent picker depth.
        selected = {
            **audit_inventory,
            "entries": [entry for entry in audit_inventory["entries"] if entry["key"] in keys],
        }  # Real definitions only.
        records = DialogInspector(page, selected).inspect_all()  # Locator waits must not depend on unsafe-eval.
        assert len(records) == 3 and all(record["status"] == "passed" for record in records)  # All three real forms.
        assert policy.transmitted == 0 and not policy.denied  # No remote reads or operation submission.


class TestUtilityExperience:
    """Client-choice gaps must not depend on catalog picker declarations."""

    def test_sdk_client_paths_have_per_operation_dom_evidence(self, audit_page, audit_inventory):
        page, policy = audit_page  # Use real assets, never submit a change utility.
        keys = {
            "ex.releaseDhcpLeases",
            "srx.releaseDhcpLeases",
            "ssr.releaseDhcpLeases",
            "ex.retrieveMacTable",
        }  # SDK evidence.
        for entry in audit_inventory["entries"]:
            if entry["key"] not in keys:
                continue  # Aggregate streams and AP MAC inputs have different meanings.
            page.get_by_test_id("ws-catalog-entry-" + entry["key"]).click()  # Normal-user form inspection only.
            review = UtilityExperienceInspector(page, audit_inventory).inspect(
                {"key": entry["key"]}
            )  # No catalog fields given.
            client = [
                item for item in review["findings"] if item["topic"] == "client-choice-assistance"
            ]  # Independent SDK+DOM evidence.
            assert not client  # The rendered client helper closes this optional-enhancement gap.
            assert review["status"] == "reviewed" and not review["functional_defect_confirmed"]
            if entry["key"].startswith("ex."):
                field_name = "mac_address" if entry["key"] == "ex.retrieveMacTable" else "macs"
                field = page.get_by_test_id("ws-field-" + field_name)
                assert field.input_value() == ""
                assert field.is_editable() and field.get_attribute("required") is None
                assert page.get_by_test_id("ws-client-options").evaluate("(node) => node.multiple") == (
                    field_name == "macs"
                )
            else:
                assert page.get_by_test_id("ws-client-options").count() == 0
                assert page.get_by_test_id("ws-client-manual-guidance").is_visible()
        assert policy.transmitted == 0 and not policy.denied  # Inspection did not trigger a utility.

    def test_aggregate_streams_and_ap_mac_are_not_client_targets(self, audit_page, audit_inventory):
        page, policy = audit_page  # Keep the request boundary installed.
        for key in ("site.stats.clients", "location.clients", "ap.remotePcapWireless"):
            page.get_by_test_id("ws-catalog-entry-" + key).click()  # Inspect without starting stream or capture.
            cancel_control = page.get_by_role("button", name="Cancel", exact=True)
            assert cancel_control.is_visible()  # Every selected operation keeps explicit cancellation available.
            review = UtilityExperienceInspector(page, audit_inventory).inspect(
                {"key": key}
            )  # Source and SDK semantics only.
            assert not any(
                item["topic"] == "client-choice-assistance" for item in review["findings"]
            )  # No client-picker invention.
            assert not any(
                item["topic"] == "operation-cancel" for item in review["findings"]
            )  # The visible control closes the cancellation gap without inventing a client target.
        assert policy.transmitted == 0 and not policy.denied  # No remote traffic or execution.


class TestLiveParentCoverage:
    """A first empty site must not hide a valid later parent."""

    def test_traverses_all_sites_without_reselecting_unchanged_parent(self, audit_page, audit_inventory):
        page, policy = audit_page  # Real controls with deterministic local responses.
        first = "/api/websockets/sites/" + IsolatedPage.SITE + "/maps"  # First synthetic site is empty.
        policy.responses[first] = ("application/json", '{"rows": []}')  # Reproduce genuine first-parent emptiness.
        entry = next(item for item in audit_inventory["entries"] if item["key"] == "location.clients")  # Real form.
        page.get_by_test_id("ws-catalog-entry-location.clients").click()  # No execution.
        inspector = LivePickerInspector(page, time.monotonic() + 20)  # Shared bounded traversal.
        assert inspector.inspect(entry) == []  # Later site's map must satisfy target availability.
        maps = [row for row in inspector.measurements if row["field"] == "map_id"]  # Actual counts per parent.
        assert [row["available_choices"] for row in maps] == [0, 1]  # Both sites are measured, not only the first.
        assert [row["scope"] for row in maps] == [{"sites": 1}, {"sites": 2}]  # No private identifier saved.
        assert inspector.inspect(entry) == []  # Repeat inspection must not expect refresh for unchanged parent.
        assert policy.transmitted == 0 and policy.denied == []  # No live request or operation start.

    def test_all_maps_refresh_client_choices_serially(self, audit_page, audit_inventory):
        page, policy = audit_page  # Test actual parent-change behavior, not the catalog oracle.
        base = "/api/websockets/sites/" + IsolatedPage.SITE  # Exact synthetic first-site scope.
        policy.responses[base + "/maps"] = (
            "application/json",
            '{"rows":[{"id":"'
            + IsolatedPage.MAP
            + '","name":"First"},{"id":"'
            + IsolatedPage.OTHER_MAP
            + '","name":"Second"}]}',
        )  # Two maps.
        policy.responses[base + "/maps/" + IsolatedPage.OTHER_MAP + "/sdkclients"] = (
            "application/json",
            '{"rows": []}',
        )  # Empty later map.
        entry = next(
            item for item in audit_inventory["entries"] if item["key"] == "diag.sdkclient"
        )  # Real three-level picker.
        page.get_by_test_id("ws-catalog-entry-diag.sdkclient").click()  # Normal-user form selection.
        inspector = LivePickerInspector(page, time.monotonic() + 20)  # Bound every scope traversal.
        assert inspector.inspect(entry) == []  # A populated map remains available despite other empty maps.
        clients = [row for row in inspector.measurements if row["field"] == "sdkclient_id"]  # Each site/map path.
        assert [row["available_choices"] for row in clients] == [1, 0, 0]  # Include every returned map.
        assert [row["scope"] for row in clients] == [
            {"sites": 1, "maps": 1},
            {"sites": 1, "maps": 2},
            {"sites": 2, "maps": 1},
        ]  # Counts only.
        assert policy.transmitted == 0 and policy.denied == []  # No private or operation traffic.


class TestReadonlyBrowser:
    """Exercise the actual start/output/stop UI with a zero-network synthetic transport."""

    def test_exact_ui_lifecycle_with_no_remote_data(self, browser, audit_inventory, monkeypatch):
        import json  # Synthetic envelopes only; no live payload is persisted.
        from pathlib import Path
        from types import SimpleNamespace
        from urllib.parse import urlsplit

        from playwright.sync_api import Route

        from tests.e2e.websockets_tab.dialog_audit.support.policy import ReadonlyLifecyclePolicy
        from tests.e2e.websockets_tab.dialog_audit.test_live import TestReadonlyLive

        renderer = IsolatedPage(Path(__file__).resolve().parents[4], audit_inventory)
        policy = ReadonlyLifecyclePolicy("https://audit.invalid", renderer.responses())
        session = {
            "session_id": "2222222233334444",
            "key": policy.KEY,
            "kind": "channel",
            "state": "live",
            "live": True,
            "counters": {"received": 1},
            "output": "json",
        }  # Synthetic owned channel; its one message is a lifecycle notice, not remote stats.
        requests = []  # Record public resource categories, never actual production URLs.

        def local_fetch(route, **options):
            assert options == {"max_redirects": 0, "max_retries": 0, "timeout": 15000}
            path = urlsplit(route.request.url).path
            requests.append("start" if path.endswith("/sessions") else "stop" if path.endswith("/stop") else "read")
            if route.request.method == "POST":
                if path.endswith("/stop"):
                    session.update(state="stopped", live=False)
                payload, status = dict(session), 202 if path.endswith("/stop") else 201
                content_type, body = "application/json", json.dumps(payload).encode()
            elif path.endswith("/messages"):
                payload = {
                    "session": dict(session),
                    "messages": [{"seq": 1, "kind": "event", "source": None}],
                    "next_after": 1,
                }
                content_type, body, status = "application/json", json.dumps(payload).encode(), 200
            else:
                content_type, raw = policy.responses[path]
                body, status = raw.encode() if isinstance(raw, str) else raw, 200
            return SimpleNamespace(
                status=status,
                headers={"content-type": content_type},
                body=lambda: body,
                json=lambda: json.loads(body),
            )  # No network branch, SDK call or listener exists.

        original_fulfill = Route.fulfill

        def local_fulfill(route, **options):
            response = options.pop("response", None)
            if response is not None:
                options.update(status=response.status, body=response.body(), headers=response.headers)
            return original_fulfill(route, **options)

        monkeypatch.setattr(Route, "fetch", local_fetch)  # Trap actual forwarding independently of policy counters.
        monkeypatch.setattr(Route, "fulfill", local_fulfill)  # Adapt only the synthetic APIResponse boundary.
        with browser.new_context(service_workers="block") as context:
            policy.install(context)
            page = context.new_page()
            TestReadonlyLive.choose_and_observe(page, policy, audit_inventory)
            TestReadonlyLive.stop_owned(page, policy)
            assert policy.latest is not None and policy.latest["state"] == "stopped" and "live" in policy.states
            assert policy.event_count == 0 and policy.message_reads >= 1  # Notices do not fabricate data.
            assert requests.count("start") == 1 and requests.count("stop") == 1
            assert policy.denied == [] and policy.lifecycle_errors == []


class TestInspectorFailureEvidence:
    """Measure negative real-form paths without forwarding requests or changing production assets."""

    def test_live_mode_all_catalog_scopes_records_empty_everywhere(self, audit_page, audit_inventory):
        page, policy = audit_page
        policy.responses["/api/websockets/sites/" + IsolatedPage.OTHER_SITE + "/devices"] = (
            "application/json",
            '{"rows":[]}',
        )  # Give every returned parent a deterministic reviewed response.
        policy.responses["/api/websockets/sites/" + IsolatedPage.OTHER_SITE + "/assets"] = (
            "application/json",
            '{"rows":[]}',
        )
        policy.responses["/api/websockets/mxedges"] = ("application/json", '{"rows":[]}')
        for site in (IsolatedPage.SITE, IsolatedPage.OTHER_SITE):
            policy.responses["/api/websockets/mxedges?site_id=" + site] = ("application/json", '{"rows":[]}')
        records = DialogInspector(page, audit_inventory, live=True).inspect_all()
        assert len(records) == len(audit_inventory["entries"]) == 70
        blocked = {record["key"] for record in records if record["status"] == "blocked"}
        assert blocked == {"mxedge.orgRemotePcap", "mxedge.siteRemotePcap"}
        assert all(record["status"] in {"passed", "blocked"} for record in records)
        assert all("source" in record for record in records)  # All forms rendered, including empty target scopes.
        assert policy.transmitted == 0 and policy.denied == []

    def test_expired_deadline_keeps_every_operation_as_blocked(self, audit_page, audit_inventory, monkeypatch):
        from types import SimpleNamespace

        page, policy = audit_page
        inspector = DialogInspector(page, audit_inventory, live=True)
        clock = iter([0, 1000] + [1000] * len(audit_inventory["entries"]))
        monkeypatch.setattr(
            "tests.e2e.websockets_tab.dialog_audit.support.journeys.time",
            SimpleNamespace(monotonic=lambda: next(clock)),
        )  # Replace this module's clock only; do not disrupt Playwright or pytest timers.
        records = inspector.inspect_all()  # Expiry precedes any operation click or selector request.
        assert len(records) == 72 and {record["status"] for record in records} == {"blocked"}
        assert all(
            record["observations"] == ["The bounded live inspection deadline was reached."] for record in records
        )
        assert policy.transmitted == 0 and policy.denied == []

    def test_missing_and_misconfigured_visible_controls_are_findings(self, audit_page, audit_inventory):
        page, policy = audit_page
        inspector = DialogInspector(page, audit_inventory)
        entry = next(item for item in audit_inventory["entries"] if item["key"] == "location.clients")
        page.get_by_test_id("ws-catalog-entry-location.clients").click()
        page.get_by_test_id("ws-field-site_id").select_option(IsolatedPage.SITE)
        page.get_by_test_id("ws-field-map_id").locator('option:not([value=""])').first.wait_for()
        page.locator('label[for="wsField-site_id"]').evaluate("(node) => node.textContent = 'Wrong label'")
        page.get_by_test_id("ws-field-site_id").evaluate("(node) => { node.required = false; node.multiple = true; }")
        page.get_by_test_id("ws-field-map_id").evaluate("(node) => node.remove()")
        problems = inspector.field_problems(entry)
        assert "The form retains stale fields or omits current fields." in problems
        assert "A declared field has no unique rendered control." in problems
        assert "A field has no matching visible label." in problems
        assert "A field does not enforce the declared required state." in problems
        assert "A selector has the wrong multiplicity." in problems
        assert policy.transmitted == 0 and policy.denied == []

    def test_source_resource_purpose_and_missing_client_control(self, audit_page, audit_inventory):
        page, policy = audit_page
        inspector = DialogInspector(page, audit_inventory)
        entry = next(item for item in audit_inventory["entries"] if item["key"] == "site.stats.devices")
        assert inspector.purpose_problems({**entry, "description": "An unrelated stream."}) == [
            "The purpose does not name the resource consumed by the server channel path."
        ]  # Independent server-path semantics, not a catalog equality assertion.
        utility = next(item for item in audit_inventory["entries"] if item["key"] == "ex.retrieveMacTable")
        page.get_by_test_id("ws-catalog-entry-" + utility["key"]).click()
        page.get_by_test_id("ws-field-mac_address").evaluate("(node) => node.remove()")
        review = UtilityExperienceInspector(page, audit_inventory).inspect(utility)
        cancel_control = page.get_by_role("button", name="Cancel", exact=True)
        assert cancel_control.is_visible()  # A separate missing client field does not hide form cancellation.
        assert not any(
            finding["topic"] == "operation-cancel" for finding in review["findings"]
        )  # The audit no longer reports the repaired cancellation gap.
        assert "A declared field has no unique rendered control." in inspector.field_problems(utility)
        assert policy.transmitted == 0 and policy.denied == []

    def test_empty_missing_and_nonpicker_controls_do_not_get_forced_values(self, audit_page, audit_inventory):
        from tests.e2e.websockets_tab.dialog_audit.support.journeys import PickerInspector

        page, policy = audit_page
        entry = next(item for item in audit_inventory["entries"] if item["key"] == "site.stats.clients")
        policy.responses["/api/operations/sites"] = ("application/json", '{"sites":[]}')
        page.get_by_test_id("ws-catalog-entry-" + entry["key"]).click()
        inspector = PickerInspector(page)
        assert inspector.inspect(entry) == ["A selector has no available choice after its parent selection."]
        page.get_by_test_id("ws-field-site_id").evaluate("(node) => node.remove()")
        assert PickerInspector(page).inspect(entry) == []  # Missing control is reported by field_problems.
        assert PickerInspector(page).inspect({"identifiers": [{"name": "synthetic"}]}) == []
        assert policy.transmitted == 0 and policy.denied == []

    def test_parent_deadline_and_family_mismatch_are_not_success(self, audit_page, audit_inventory):
        import pytest

        from tests.e2e.websockets_tab.dialog_audit.support.journeys import PickerInspector

        page, policy = audit_page
        entry = next(item for item in audit_inventory["entries"] if item["key"] == "ex.retrieveMacTable")
        page.get_by_test_id("ws-catalog-entry-" + entry["key"]).click()
        page.get_by_test_id("ws-field-site_id").select_option(IsolatedPage.SITE)
        devices = page.get_by_test_id("ws-field-device_id")
        devices.locator('option:not([value=""])').first.wait_for(state="attached")
        devices.locator('option:not([value=""])').evaluate_all("(nodes) => nodes.forEach(n => n.dataset.family = 'ap')")
        child = {**entry, "targets": [field for field in entry["targets"] if field["name"] == "device_id"]}
        assert PickerInspector(page).inspect(child) == ["The device selector includes the wrong device family."]
        assert LivePickerInspector(page, time.monotonic() + 5).inspect(child) == [
            "The device selector includes the wrong device family."
        ]
        with pytest.raises(TimeoutError, match="deadline"):
            LivePickerInspector(page, 0).inspect(entry)
        assert policy.transmitted == 0 and policy.denied == []

    def test_browser_failure_keeps_denominator_and_redacts_exception(self, audit_page, audit_inventory, monkeypatch):
        page, policy = audit_page
        selected = {**audit_inventory, "entries": audit_inventory["entries"][:2]}
        inspector = DialogInspector(page, selected)
        failures = iter(
            [
                RuntimeError("strict mode violation: synthetic private label must not appear"),
                ValueError("synthetic private browser error must not appear"),
            ]
        )

        def reject_inspection(_entry, _deadline):
            raise next(failures)  # Synthetic browser seam only; no network or production alteration.

        monkeypatch.setattr(inspector, "inspect", reject_inspection)
        records = inspector.inspect_all()
        assert [record["key"] for record in records] == [entry["key"] for entry in selected["entries"]]
        assert [record["observations"] for record in records] == [
            ["Browser inspection blocked: ambiguous-control"],
            ["Browser inspection blocked: ValueError"],
        ]  # Fixed classifications, never raw browser error strings.
        assert {record["status"] for record in records} == {"blocked"}
        assert policy.transmitted == 0 and policy.denied == []
