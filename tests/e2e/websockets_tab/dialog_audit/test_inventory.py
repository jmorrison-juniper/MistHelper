"""Independent catalog, policy, and sanitized report contract tests."""

import json  # Raise the real parser exception for malformed response tests.
from copy import deepcopy  # Exercise changed inventory without changing the source catalog.
from types import SimpleNamespace  # Trap actual route decisions without a remote endpoint.

import pytest  # Parameterize negative policy cases with explicit expected outcomes.

from tests.e2e.websockets_tab.dialog_audit.support.inventory import InventoryBuilder, OperationOracle  # Source oracle.
from tests.e2e.websockets_tab.dialog_audit.support.policy import (
    BrowserRequestPolicy,
    LiveGate,
    LiveRequestPolicy,
    ReadonlyLifecyclePolicy,
    ReadScope,
)  # Test both boundaries before transmission.
from tests.e2e.websockets_tab.dialog_audit.support.reporting import AuditReportWriter  # Separate evidence modes.


class TestInventory:
    """Keep locked and unverified entries in the denominator."""

    def test_real_catalog_reconciliation(self, audit_inventory):
        entries = audit_inventory["entries"]  # Use the installed SDK catalog, not a reduced fixture.
        assert len(entries) >= 18  # Source has eighteen channels plus dynamic utilities.
        keys = [entry["key"] for entry in entries]  # Include locked utility entries.
        assert InventoryBuilder.reconcile(keys, keys) == []  # Require complete unique inventory.
        assert InventoryBuilder.reconcile(
            ["duplicate", "duplicate"], ["duplicate", "duplicate"]
        )  # Never accept matching duplicates.
        assert any(entry.get("locked") for entry in entries)  # Locked entries must remain inspectable.
        assert OperationOracle(audit_inventory).required("site.stats.clients") == {"site_id"}  # Site-wide stream.
        assert OperationOracle(audit_inventory).required("location.clients") == {
            "site_id",
            "map_id",
        }  # Map-wide stream.

    @pytest.mark.parametrize("actual", [["a"], ["a", "b", "b"], ["a", "b", "extra"]])  # Cover all inventory drift.
    def test_inventory_drift_is_not_a_pass(self, actual):
        assert InventoryBuilder.reconcile(["a", "b"], actual)  # Missing, duplicate, and extra keys must fail.

    def test_oracle_detects_missing_required_selector(self, audit_inventory):
        changed = deepcopy(audit_inventory)  # Preserve the real snapshot for other tests.
        entry = next(entry for entry in changed["entries"] if entry["key"] == "site.stats.clients")  # Real key.
        entry["identifiers"] = []  # Simulate catalog drift without changing the independent path oracle.
        assert OperationOracle(changed).missing(entry) == {"site_id"}  # Detect the absent selector.
        assert not OperationOracle(changed).verified("diag.asset")  # Unknown SDK channel stays unverified.

    def test_python_egress_is_denied_before_connection(self, audit_inventory):
        import socket  # The isolated inventory fixture installed guards before SDK discovery.

        assert audit_inventory["entries"]  # Prove discovery completed under the real egress guard.
        with pytest.raises(RuntimeError, match="denied"):
            socket.create_connection(("synthetic.invalid", 443), timeout=1)  # Refuse before DNS or TCP.
        with socket.socket() as connection:
            with pytest.raises(RuntimeError, match="denied"):
                connection.connect(("192.0.2.1", 443))  # Refuse a direct connection without transmitting.


class TestPolicy:
    """Unknown reads and every execution request remain denied."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("POST", "/api/websockets/sessions"),
            ("POST", "/api/websockets/sessions/other/stop"),
            ("DELETE", "/api/websockets/sessions/other"),
            ("POST", "/api/operations/run"),
            ("GET", "/api/websockets/sessions/other/download"),
            ("GET", "/api/websockets/sessions/other/terminal"),
            ("GET", "/api/websockets/sites/unknown/devices"),
            ("GET", "/websockets?next=https://example.invalid"),
            ("GET", "/%77ebsockets"),
            ("GET", "/unknown"),
        ],
    )  # Use synthetic destinations only, never probe prohibited live handlers.
    def test_execution_and_unknown_reads_are_denied(self, method, path):
        policy = BrowserRequestPolicy("https://audit.invalid", {"/websockets": ("text/html", "safe")})  # Exact set.
        assert not policy.allowed(method, "https://audit.invalid" + path)  # Decide before transmission.
        assert policy.transmitted == 0  # Inspection has no forwarding branch.

    def test_external_origin_and_redirect_are_denied(self):
        policy = BrowserRequestPolicy("https://audit.invalid", {"/websockets": ("text/html", "safe")})  # Exact set.
        assert policy.allowed("GET", "https://audit.invalid/websockets")  # Only the local response is available.
        assert not policy.allowed("GET", "https://example.invalid/websockets")  # A matching path is insufficient.
        assert not policy.allowed("GET", "https://audit.invalid/websockets", redirected=True)  # Deny redirect chains.
        assert not policy.allowed("POST", "https://audit.invalid/websockets")  # No method widening.

    def test_live_gate_rejects_credentials_and_missing_url(self):
        with pytest.raises(ValueError, match="authorized"):
            LiveGate.validate_url(None)  # No default live destination.
        with pytest.raises(ValueError, match="credentials"):
            LiveGate.validate_url("https://user:secret@example.invalid")  # Never accept URL secrets.

    def test_guard_aborts_before_transmission(self):
        policy = BrowserRequestPolicy(
            "https://audit.invalid", {"/websockets": ("text/html", "safe")}
        )  # Exact local response.
        for method, path in (
            ("POST", "/api/websockets/sessions"),
            ("GET", "/api/websockets/sessions/foreign/download"),
            ("POST", "/api/websockets/sessions/foreign/input"),
            ("GET", "/unknown"),
        ):
            trap = RequestTrap(method, "https://audit.invalid" + path)  # No socket or server exists.
            policy.handle(trap)  # Test the same guard invoked by Playwright routing.
            assert trap.aborted and trap.transmitted == 0 and not trap.fulfilled  # Independent forwarding trap.
        permitted = RequestTrap("GET", "https://audit.invalid/websockets")  # Test the approved path too.
        policy.handle(permitted)  # Fulfillment must not become forwarding.
        assert permitted.fulfilled and not permitted.aborted and permitted.transmitted == 0  # Local response only.


class RequestTrap:
    """Count forwarding independently of the policy's own bookkeeping."""

    def __init__(self, method, url):
        self.request = SimpleNamespace(method=method, url=url, redirected_from=None)  # Synthetic request metadata.
        self.aborted, self.fulfilled, self.transmitted = False, False, 0  # Independent outcomes.

    def abort(self, _reason):
        self.aborted = True  # The guard must reject the request here.

    def fulfill(self, **_response):
        self.fulfilled = True  # Approved reads stay local.

    def continue_(self, **_options):
        self.transmitted += 1  # Catch accidental forwarding, even if policy bookkeeping remains zero.

    def fetch(self, **_options):
        self.transmitted += 1  # Catch alternate forwarding through route.fetch.


class TestLivePolicy:
    """Exercise live GET forwarding and default denial without contacting a host."""

    def test_live_start_and_unknown_reads_never_transmit(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # User-supplied isolated ports are supported.
        for method, path in (
            ("POST", "/api/websockets/sessions"),
            ("POST", "/api/operations/run"),
            ("DELETE", "/api/websockets/sessions/foreign"),
            ("GET", "/unknown"),
            ("GET", "/api/websockets/sites/unknown/maps"),
        ):
            trap = LiveReadTrap(method, "http://localhost:9600" + path)  # Independent forwarding counter.
            policy.handle(trap)  # Execute the real live handler, not just the approval predicate.
            assert trap.aborted and trap.transmitted == 0  # Prohibited handlers never receive a request.
        assert policy.reads == 0  # No permitted GET attempt occurred.

    def test_scope_requires_real_parent_responses(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # Unknown parents are denied by default.
        site, mapping = "11111111-2222-3333-4444-555555555555", "22222222-3333-4444-5555-666666666666"  # Synthetic IDs.
        base = "/api/websockets/sites/" + site  # Bind the map response to its actual parent.
        assert not policy.allowed("GET", policy.origin + base + "/maps")  # No scope before the parent read.
        for path, payload in (
            ("/api/operations/sites", {"sites": [{"id": site}]}),
            (base + "/maps", {"rows": [{"id": mapping}]}),
        ):
            trap = LiveReadTrap("GET", policy.origin + path, payload)  # Synthetic approved read response.
            policy.handle(trap)  # Register scope only through the real guarded read flow.
            assert trap.fulfilled and not trap.aborted and trap.transmitted == 1  # Exactly one GET.
            assert trap.options == {"max_redirects": 0, "max_retries": 0, "timeout": 15000}  # No automatic followup.
        assert policy.allowed("GET", policy.origin + base + "/maps/" + mapping + "/sdkclients")  # Reviewed child path.
        assert not policy.allowed("GET", policy.origin + base + "/maps/" + site + "/sdkclients")  # Wrong map denied.
        assert not policy.allowed("GET", policy.origin + base + "/maps?extra=1")  # Unexpected query denied.

    def test_device_client_read_requires_approved_site_and_same_site_device(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # Use guarded synthetic responses only.
        site, other_site = "11111111-2222-3333-4444-555555555555", "33333333-4444-5555-6666-777777777777"
        device, other_device = "22222222-3333-4444-5555-666666666666", "44444444-5555-6666-7777-888888888888"
        client_id = "55555555-6666-7777-8888-999999999999"  # A client identifier never becomes a device grant.
        device_path = "/api/websockets/sites/" + site + "/devices"  # Device evidence has one site parent.
        client_path = device_path + "/" + device + "/clients"  # Exact approved child path.
        assert not policy.allowed("GET", policy.origin + client_path)  # No site or device evidence exists.
        for path, payload in (
            ("/api/operations/sites", {"sites": [{"id": site}, {"id": other_site}]}),
            (device_path, {"rows": [{"id": device}]}),
            ("/api/websockets/sites/" + other_site + "/devices", {"rows": [{"id": other_device}]}),
        ):
            trap = LiveReadTrap("GET", policy.origin + path, payload)  # Each parent response is synthetic.
            policy.handle(trap)  # Register evidence only after the guarded read.
            assert trap.fulfilled and trap.transmitted == 1  # Each parent is one approved read.
        permitted = LiveReadTrap(
            "GET", policy.origin + client_path, {"rows": [{"id": client_id}]}
        )  # Child identifiers cannot expand device scope.
        policy.handle(permitted)  # Exercise the actual request handler.
        assert permitted.fulfilled and permitted.transmitted == 1  # Exact same-site device read is allowed.
        client_as_device = LiveReadTrap(
            "GET", policy.origin + device_path + "/" + client_id + "/clients", {"rows": []}
        )  # A returned client ID cannot become device scope.
        policy.handle(client_as_device)
        assert client_as_device.aborted and client_as_device.transmitted == 0  # Client rows grant no parent access.
        policy.scope.devices[site].clear()  # Simulate a current site response that removes the device.
        cached = LiveReadTrap("GET", policy.origin + client_path, {"rows": []})  # The first response is cached.
        policy.handle(cached)  # Permission is checked before a cached response can be reused.
        assert cached.aborted and cached.transmitted == 0  # Stale cache data cannot restore removed scope.
        for path in (
            "/api/websockets/sites/" + other_site + "/devices/" + device + "/clients",
            device_path + "/" + other_device + "/clients",
        ):
            denied = LiveReadTrap("GET", policy.origin + path, {"rows": []})  # Cross-site and unrelated IDs.
            policy.handle(denied)  # Refuse the path before its route can fetch.
            assert denied.aborted and denied.transmitted == 0  # No disallowed request leaves the trap.

    def test_device_reads_require_an_authorized_site(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # No parent has been read.
        site, device = "11111111-2222-3333-4444-555555555555", "22222222-3333-4444-5555-666666666666"
        path = "/api/websockets/sites/" + site + "/devices"  # A device path cannot establish site scope.
        trap = LiveReadTrap("GET", policy.origin + path, {"rows": [{"id": device}]})
        policy.handle(trap)  # The guard blocks the child parent before transmission.
        assert trap.aborted and trap.transmitted == 0  # Unapproved site scope remains closed.
        with pytest.raises(ValueError, match="site"):
            policy.scope.register(path, {"rows": [{"id": device}]})  # Direct registration cannot bypass the parent.

    @pytest.mark.parametrize(
        "payload",
        [
            {"rows": [{"id": "22222222-3333-4444-5555-666666666666"}, {"id": "invalid"}]},
            {"rows": {}},
        ],
    )  # Invalid and empty responses cannot leave a partial or stale device grant.
    def test_bad_device_responses_fail_closed_without_partial_scope(self, payload):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # Begin with valid, guarded scope.
        site, device = "11111111-2222-3333-4444-555555555555", "22222222-3333-4444-5555-666666666666"
        site_read = LiveReadTrap(
            "GET", policy.origin + "/api/operations/sites", {"sites": [{"id": site}]}
        )  # Approve the site before devices.
        policy.handle(site_read)
        device_path = "/api/websockets/sites/" + site + "/devices"
        initial = LiveReadTrap("GET", policy.origin + device_path, {"rows": [{"id": device}]})
        policy.handle(initial)  # Seed one valid association before the bad refresh.
        policy.cache.pop(device_path)  # Force a new approved parent response instead of its valid cached body.
        refresh = LiveReadTrap("GET", policy.origin + device_path, payload)
        policy.handle(refresh)  # A failed refresh must not retain stale or partial grants.
        assert refresh.aborted and refresh.transmitted == 1  # The response is rejected after one guarded read.
        client_path = device_path + "/" + device + "/clients"
        assert not policy.allowed("GET", policy.origin + client_path)  # Invalid evidence clears device scope.

    def test_empty_device_response_is_no_data_without_client_permission(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})
        site, device = "11111111-2222-3333-4444-555555555555", "22222222-3333-4444-5555-666666666666"
        policy.handle(LiveReadTrap("GET", policy.origin + "/api/operations/sites", {"sites": [{"id": site}]}))
        path = "/api/websockets/sites/" + site + "/devices"
        policy.handle(LiveReadTrap("GET", policy.origin + path, {"rows": [{"id": device}]}))
        policy.cache.pop(path)
        empty = LiveReadTrap("GET", policy.origin + path, {"rows": []})
        policy.handle(empty)
        assert empty.fulfilled and not empty.aborted and empty.transmitted == 1
        assert policy.scope.devices[site] == set() and policy.errors == []
        assert not policy.allowed("GET", policy.origin + path + "/" + device + "/clients")

    def test_client_scope_denies_method_origin_query_redirect_and_encoded_path(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # One synthetic origin only.
        site, device = "11111111-2222-3333-4444-555555555555", "22222222-3333-4444-5555-666666666666"
        for path, payload in (
            ("/api/operations/sites", {"sites": [{"id": site}]}),
            ("/api/websockets/sites/" + site + "/devices", {"rows": [{"id": device}]}),
        ):
            policy.handle(LiveReadTrap("GET", policy.origin + path, payload))  # Approve both request parents.
        client_path = "/api/websockets/sites/" + site + "/devices/" + device + "/clients"
        denied_requests = [
            LiveReadTrap("POST", policy.origin + client_path),
            LiveReadTrap("PUT", policy.origin + client_path),
            LiveReadTrap("PATCH", policy.origin + client_path),
            LiveReadTrap("DELETE", policy.origin + client_path),
            LiveReadTrap("GET", policy.origin + client_path + "?limit=1"),
            LiveReadTrap("GET", "http://localhost:9601" + client_path),
            LiveReadTrap("GET", policy.origin + client_path.replace("/devices/", "/%64evices/")),
            LiveReadTrap("GET", policy.origin + client_path + "/delete"),
            LiveReadTrap("GET", policy.origin + client_path),
        ]
        denied_requests[-1].request.redirected_from = object()  # Redirected requests remain blocked.
        for trap in denied_requests:
            policy.handle(trap)  # Verify each decision at the pre-transmission boundary.
            assert trap.aborted and trap.transmitted == 0  # Every invalid request is blocked locally.
        assert policy.transmitted == 2  # Only the two approved parent reads were transmitted.

    def test_redirects_and_cross_origin_never_expand_permission(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # Exact origin includes the isolated port.
        assert not policy.allowed("GET", "http://localhost:9601/websockets")  # Same host alone is insufficient.
        assert not policy.allowed("GET", policy.origin + "/websockets", redirected=True)  # Deny redirected requests.
        trap = LiveReadTrap(
            "GET", policy.origin + "/websockets", status=302
        )  # Do not contact the redirect destination.
        policy.handle(trap)  # The first reviewed read may return a redirect.
        assert trap.aborted and not trap.fulfilled and trap.transmitted == 1  # Zero redirect followups.
        assert len(policy.errors) == 1  # Preserve the capability blocker instead of accepting a login redirect.

    def test_changed_assets_and_malformed_scope_are_blocked(self):
        policy = LiveRequestPolicy(
            "http://localhost:9600", {"/static/js/portal.js": ("text/javascript", b"reviewed")}
        )  # Exact asset.
        asset = LiveReadTrap("GET", policy.origin + "/static/js/portal.js")  # Synthetic mismatched deployed script.
        policy.handle(asset)  # Do not let the browser execute an unreviewed asset.
        assert asset.aborted and not asset.fulfilled  # The mismatch stays blocked.
        malformed = LiveReadTrap(
            "GET", policy.origin + "/api/operations/sites", {"sites": [{"id": "not-an-id"}]}
        )  # Invalid scope.
        policy.handle(malformed)  # Validate before allowing child reads.
        assert malformed.aborted and not policy.scope.sites  # No invalid parent can authorize a picker.
        assert not policy.allowed(
            "GET",
            policy.origin + "/api/websockets/sites/not-an-id/devices/22222222-3333-4444-5555-666666666666/clients",
        )  # Invalid site evidence cannot authorize a child read.

    def test_installed_sdk_reads_and_local_session_substitution(self, audit_inventory):
        assert audit_inventory["sdk_version"]  # Bind verification to the real installed catalog.
        ReadScope.verify_sdk()  # Read actual SDK source, never invoke it.
        policy = LiveRequestPolicy(
            "http://localhost:9600", {"/api/websockets/sessions": ("application/json", "{}")}
        )  # No live sessions.
        trap = LiveReadTrap("GET", policy.origin + "/api/websockets/sessions")  # Automatic page list request.
        policy.handle(trap)  # Fulfill locally rather than disclose another user's sessions.
        assert trap.fulfilled and trap.transmitted == 0 and policy.reads == 0  # No real list or session control.

    def test_client_sdk_method_drift_fails_source_verification(self, monkeypatch, caplog):
        """Reject a client SDK mutation before the harness can authorize live reads."""
        from tests.e2e.websockets_tab.dialog_audit.support import policy as policy_module

        with caplog.at_level("DEBUG", logger=policy_module.__name__):
            ReadScope.verify_sdk()
        assert "Verified 9 installed selector GET implementations" in caplog.text
        real_source = policy_module.inspect.getsource

        def changed_source(function):
            if function.__name__ == "searchSiteWiredClients":
                return "return session.mist_post(path)"
            return real_source(function)

        monkeypatch.setattr(policy_module.inspect, "getsource", changed_source)
        with pytest.raises(ValueError, match="not a verified GET"):
            ReadScope.verify_sdk()


class TestRejectedScopeEvidence:
    """Malformed parent records cannot authorize subsequent requests."""

    @pytest.mark.parametrize(
        "payload,reason",
        [
            ([], "invalid response"),
            ({"sites": {}}, "bounded scope"),
            ({"sites": [{}] * 10001}, "bounded scope"),
            ({"sites": ["not-a-row"]}, "invalid row"),
            ({"sites": [{"id": 1}]}, "invalid identifier"),
        ],
    )
    def test_parent_registration_rejects_bad_shapes(self, payload, reason):
        scope = ReadScope()
        with pytest.raises(ValueError, match=reason):
            scope.register("/api/operations/sites", payload)
        assert scope.sites == set() and scope.maps == {}
        assert not scope.allowed("/api/websockets/sites/unknown/maps")

    @pytest.mark.parametrize(
        "url", ["ftp://localhost:9600", "http://localhost:9600/path", "http://localhost:9600/?x=1"]
    )
    def test_nonorigin_urls_do_not_become_live_destinations(self, url):
        with pytest.raises(ValueError, match="authorized HTTP origin"):
            LiveGate.validate_url(url)

    def test_unsolicited_browser_socket_closes_without_connecting(self):
        closed = []
        policy = BrowserRequestPolicy("https://audit.invalid", {})
        route = SimpleNamespace(close=lambda: closed.append(True), connect_to_server=lambda: pytest.fail("Forbidden"))
        policy.deny_socket(route)
        assert closed == [True] and policy.denied == ["WEBSOCKET"] and policy.transmitted == 0


class LiveReadTrap(RequestTrap):
    """Count only approved reads and record redirect/retry settings."""

    def __init__(self, method, url, payload=None, status=200):
        super().__init__(method, url)  # Reuse independent abort and forwarding counters.
        self.request.post_data = None  # A legitimate inspection GET has no request body.
        self.response = SimpleNamespace(
            status=status, json=lambda: payload, body=lambda: b"changed", headers={"content-type": "application/json"}
        )  # Local trap response.
        self.options = {}  # Save only fixed network settings, never real request headers.

    def fetch(self, **options):
        self.transmitted += 1  # An approved live GET is distinct from forbidden traffic.
        self.options = options  # Ensure redirects and retries remain disabled.
        return self.response  # No actual network endpoint exists in this test.


class TestLiveReadFailures:
    """Malformed responses and HTTP refusals cannot grant picker scope."""

    @pytest.mark.parametrize("status", [400, 403, 429, 500, 503])
    def test_http_4xx_and_5xx_refusals_are_blocked(self, status):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # Synthetic destination only.
        trap = LiveReadTrap("GET", policy.origin + "/api/operations/sites", status=status)  # HTTP 4xx/5xx.
        policy.handle(trap)  # Exactly one approved GET, no retries or redirect followups.
        assert trap.aborted and not trap.fulfilled and trap.transmitted == 1  # Never expose a refusal as picker data.
        assert policy.scope.sites == set() and len(policy.errors) == 1  # Refusal cannot authorize child requests.

    def test_empty_body_is_blocked(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # No live server.
        trap = LiveReadTrap("GET", policy.origin + "/api/operations/sites")  # Approved parent path.
        trap.response.body = lambda: b""  # Reproduce an actual empty-body response.
        policy.handle(trap)  # Reject before scope registration.
        assert trap.aborted and not trap.fulfilled and policy.scope.sites == set()  # No false empty success.
        assert len(policy.errors) == 1  # Record an explicit read blocker.

    def test_malformed_json_is_blocked(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # Synthetic only.
        trap = LiveReadTrap("GET", policy.origin + "/api/operations/sites")  # Exact reviewed GET.

        def malformed_json():
            return json.loads("{")  # Exercise the actual JSONDecodeError contract.

        trap.response.json = malformed_json  # The response cannot be interpreted as valid scope.
        policy.handle(trap)  # Reject malformed JSON before permitting descendants.
        assert trap.aborted and not trap.fulfilled and policy.scope.sites == set()  # No registration.
        assert policy.errors == ["Live read blocked: JSONDecodeError"]  # Verify the parser failure category.


class TestReadCaching:
    """Reuse live picker evidence without extra requests or loss of scope checks."""

    def test_approved_picker_cache_does_not_forward_again(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # An isolated synthetic destination only.
        site = "11111111-2222-3333-4444-555555555555"  # Never use a real target in policy tests.
        first = LiveReadTrap("GET", policy.origin + "/api/operations/sites", {"sites": [{"id": site}]})  # Parent read.
        policy.handle(first)  # Approve and register the parent's actual response.
        repeated = LiveReadTrap("GET", policy.origin + "/api/operations/sites")  # Same approved resource.
        policy.handle(repeated)  # Reuse only the in-context response.
        assert first.transmitted == 1 and repeated.transmitted == 0 and repeated.fulfilled  # No repeated Mist reads.
        assert policy.reads == 1 and policy.scope.sites == {site}  # Real registered scope stays required.
        foreign = LiveReadTrap("GET", "http://localhost:9601/api/operations/sites")  # Cache must not widen origins.
        policy.handle(foreign)  # Apply approval before cache lookup.
        assert foreign.aborted and foreign.transmitted == 0  # Cross-origin reads cannot reuse cached permission.

    def test_failed_picker_is_not_retried(self):
        policy = LiveRequestPolicy("http://localhost:9600", {})  # No actual host is contacted.
        first = LiveReadTrap("GET", policy.origin + "/api/operations/sites", status=503)  # Refused approved read.
        repeated = LiveReadTrap(
            "GET", policy.origin + "/api/operations/sites"
        )  # Another catalog selection requests it.
        policy.handle(first)  # Record failure before normal-user selection repeats it.
        policy.handle(repeated)  # Fail closed from the in-context blocker.
        assert first.aborted and repeated.aborted and repeated.transmitted == 0  # No failed-handler flood.
        assert policy.reads == 1 and policy.errors  # Failure remains a blocker, not a successful cached read.


class TestReadonlyLifecyclePolicy:
    """Independent traps prove exact-body admission and response-issued ownership without live traffic."""

    SITE = "11111111-2222-3333-4444-555555555555"
    OWN = "2222222233334444"  # Production SessionBuilder emits secrets.token_hex(8), not UUID.

    @classmethod
    def armed(cls):
        policy = ReadonlyLifecyclePolicy("http://localhost:9600", {})
        policy.scope.sites.add(cls.SITE)  # Synthetic scope normally registered by the actual sites GET.
        policy.cache["/api/websockets/sites/" + cls.SITE + "/devices"] = (
            "application/json",
            json.dumps({"rows": [{"id": cls.OWN}]}),
        )  # Synthetic approved device response, no SDK invocation.
        policy.arm(cls.SITE, "Synthetic site")
        return policy

    @pytest.mark.parametrize(
        "change",
        [
            {"key": "site.stats.clients"},
            {"key": "ap.remotePcapWireless", "kind": "utility"},
            {"kind": "shell"},
            {"parameters": {"command": "synthetic"}},
            {"targets": {"site_id": ["33333333-4444-5555-6666-777777777777"]}},
            {"targets": {"site_id": [SITE], "device_id": [OWN]}},
            {"targets": {"site_id": [SITE, OWN]}},
            {"confirmation": "synthetic"},
            {"extra": True},
        ],
    )
    def test_arbitrary_start_bodies_are_rejected_before_transmission(self, change):
        policy = self.armed()
        trap = LiveReadTrap("POST", policy.origin + "/api/websockets/sessions", status=201)
        trap.request.post_data = json.dumps({**policy.expected_body, **change})
        policy.handle(trap)
        assert trap.aborted and trap.transmitted == 0 and policy.session_id is None
        assert policy.start_attempted is False  # A rejected body never consumes or sends an allowed start.

    @pytest.mark.parametrize("raw", ["", "{", "null", "[]"])  # Empty body and malformed JSON must fail closed.
    def test_malformed_start_is_rejected(self, raw):
        policy = self.armed()
        trap = LiveReadTrap("POST", policy.origin + "/api/websockets/sessions")
        trap.request.post_data = raw
        policy.handle(trap)
        assert trap.aborted and trap.transmitted == 0

    def test_one_start_owns_only_returned_session_and_stop(self):
        policy = self.armed()
        session = {"session_id": self.OWN, "kind": "channel", "key": policy.KEY, "state": "connecting"}
        trap = LiveReadTrap("POST", policy.origin + "/api/websockets/sessions", session, 201)
        trap.request.post_data = json.dumps(policy.expected_body)
        policy.handle(trap)
        assert trap.fulfilled and trap.transmitted == 1 and policy.session_id == self.OWN
        assert trap.options == {"max_redirects": 0, "max_retries": 0, "timeout": 15000}
        repeated = LiveReadTrap("POST", trap.request.url, session, 201)
        repeated.request.post_data = trap.request.post_data
        policy.handle(repeated)
        assert repeated.aborted and repeated.transmitted == 0  # No second start, even an identical body.
        for method, path in (
            ("POST", "/api/websockets/sessions/" + self.SITE + "/stop"),
            ("GET", "/api/websockets/sessions/" + self.SITE + "/messages?after=0&limit=500"),
            ("DELETE", "/api/websockets/sessions/" + self.OWN),
            ("POST", "/api/websockets/sessions/" + self.OWN + "/input"),
            ("GET", "/api/websockets/sessions/" + self.OWN + "/download"),
            ("GET", "/api/websockets/sessions/" + self.OWN + "/messages?after=0&limit=999999"),
        ):
            rejected = LiveReadTrap(method, policy.origin + path)
            policy.handle(rejected)
            assert rejected.aborted and rejected.transmitted == 0
        read = LiveReadTrap(
            "GET",
            policy.origin + "/api/websockets/sessions/" + self.OWN + "/messages?after=0&limit=500",
            {
                "session": {**session, "state": "live", "counters": {"received": 3}},
                "messages": [
                    {"seq": 1, "kind": "event", "source": None},  # A lifecycle note must not count as Mist data.
                    {"seq": 2, "source": self.SITE},
                    {"seq": 3, "source": self.SITE},
                ],
            },
        )
        policy.handle(read)
        assert read.fulfilled and read.transmitted == 1 and policy.event_count == 2
        stop = LiveReadTrap(
            "POST",
            policy.origin + "/api/websockets/sessions/" + self.OWN + "/stop",
            {**session, "state": "stopped"},
            202,
        )
        policy.handle(stop)
        assert stop.fulfilled and stop.transmitted == 1 and policy.latest["state"] == "stopped"
        assert policy.stop_attempts == 1 and policy.message_reads == 1

    @pytest.mark.parametrize("status", [302, 401, 429, 500, 503])  # Actual synthetic HTTP refusal responses.
    def test_refused_start_does_not_register_ownership_or_retry(self, status):
        policy = self.armed()
        trap = LiveReadTrap("POST", policy.origin + "/api/websockets/sessions", {}, status)
        trap.request.post_data = json.dumps(policy.expected_body)
        policy.handle(trap)
        assert trap.aborted and trap.transmitted == 1 and policy.session_id is None
        assert policy.lifecycle_errors == ["Owned lifecycle blocked: The owned lifecycle request was refused."]
        assert not policy.valid_start(trap.request.post_data)  # A refusal cannot silently retry its POST.


class TestReadonlySource:
    """Exercise the checked channel path and actual SUBSCRIBE frame without a remote service."""

    def test_checked_start_routes_only_stats_observation(self, audit_inventory):
        from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog
        from src.mist.realtime.websocket_streams.catalog.registry.stream_catalog import StreamCatalog
        from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import UtilityCatalog
        from src.mist.realtime.websocket_streams.intake.start_request.checker import StartRequestChecker
        from src.mist.realtime.websocket_streams.live.runners.channel.routing import ChannelSourceMap
        from src.mist.realtime.websocket_streams.live.runners.channel.runner import ChannelStreamRunner
        from src.mist.realtime.websocket_streams.live.sessions.manager.factory import RunnerFactory
        from src.mist.realtime.websocket_streams.live.transport.stream_client import SubscriptionCoordinator
        from tests.e2e.websockets_tab.dialog_audit.test_live import TestReadonlyLive

        TestReadonlyLive.verify_source(audit_inventory)  # Installed SDK and actual server path agree.
        policy = TestReadonlyLifecyclePolicy.armed()
        catalog = StreamCatalog(ChannelCatalog(), UtilityCatalog(), changes_enabled=False, shell_enabled=False)
        checked = StartRequestChecker(
            catalog,
            SimpleNamespace(describe_device=lambda *_args: pytest.fail("No utility device lookup is allowed.")),
            TestReadonlyLifecyclePolicy.SITE,
        ).check(policy.expected_body)
        assert checked.kind == "channel" and checked.key == "site.stats.devices" and checked.parameters == {}
        paths = ChannelSourceMap(checked).build()
        assert list(paths) == ["/sites/" + TestReadonlyLifecyclePolicy.SITE + "/stats/devices"]
        runner = RunnerFactory(SimpleNamespace(_cloud_uri="api.mist.com")).build(checked, SimpleNamespace())
        assert isinstance(runner, ChannelStreamRunner)  # Real dispatch; no utility or shell runner is constructed.
        runner.stop()  # No thread was started: the local stop only sets its owned event.
        assert runner._state.runtime.stop.is_set() and runner._state.runtime.client is None
        sent: list[str] = []
        coordinator = SubscriptionCoordinator(tuple(paths), lambda: 0, 1)
        pending = coordinator._start(SimpleNamespace(send=sent.append))  # Real production send logic, synthetic socket.
        assert pending == set(paths)
        assert [json.loads(frame) for frame in sent] == [{"subscribe": next(iter(paths))}]  # No trigger/action payload.


class TestReadonlyResponseBoundary:
    """Bad response evidence and URL aliases never widen observation permission."""

    @pytest.mark.parametrize("mode", ["external", "redirect", "query", "fragment"])
    def test_start_origin_and_redirect_must_be_exact(self, mode):
        policy = TestReadonlyLifecyclePolicy.armed()
        url = policy.origin + "/api/websockets/sessions"
        url = "http://localhost:9601/api/websockets/sessions" if mode == "external" else url
        url += "?extra=1" if mode == "query" else "#alias" if mode == "fragment" else ""
        trap = LiveReadTrap("POST", url)
        trap.request.post_data = json.dumps(policy.expected_body)
        trap.request.redirected_from = object() if mode == "redirect" else None
        policy.handle(trap)
        assert trap.aborted and trap.transmitted == 0 and policy.start_attempted is False

    def test_malformed_json_response_does_not_register_ownership(self):
        policy = TestReadonlyLifecyclePolicy.armed()
        trap = LiveReadTrap("POST", policy.origin + "/api/websockets/sessions", status=201)
        trap.request.post_data = json.dumps(policy.expected_body)

        def malformed():
            return json.loads("{")  # Actual JSONDecodeError, not a fabricated live server failure.

        trap.response.json = malformed
        policy.handle(trap)
        assert trap.aborted and trap.transmitted == 1 and policy.session_id is None
        assert policy.lifecycle_errors == ["Owned lifecycle blocked: JSONDecodeError"]

    def test_unpopulated_or_unknown_site_cannot_arm_start(self):
        policy = TestReadonlyLifecyclePolicy.armed()
        policy.cache.clear()  # No population evidence, although the site UUID was returned.
        with pytest.raises(ValueError, match="device choices"):
            policy.arm(TestReadonlyLifecyclePolicy.SITE, "Synthetic site")
        with pytest.raises(ValueError, match="eligible"):
            policy.arm(TestReadonlyLifecyclePolicy.OWN, "Synthetic site")
        assert policy.start_attempted is False and policy.session_id is None

    def test_response_validation_failure_preserves_created_session_for_cleanup(self):
        policy = TestReadonlyLifecyclePolicy.armed()
        session = {
            "session_id": TestReadonlyLifecyclePolicy.OWN,
            "key": policy.KEY,
            "kind": "channel",
            "state": "unexpected-private-text",
            "live": True,
        }
        start = LiveReadTrap("POST", policy.origin + "/api/websockets/sessions", session, 201)
        start.request.post_data = json.dumps(policy.expected_body)
        policy.handle(start)
        assert start.aborted and start.transmitted == 1 and policy.session_id == TestReadonlyLifecyclePolicy.OWN
        assert policy.lifecycle_errors == ["Owned lifecycle blocked: The owned lifecycle state is unknown."]
        assert policy.states == set()  # Unexpected raw response text cannot reach reports.
        stop = LiveReadTrap(
            "POST",
            policy.origin + "/api/websockets/sessions/" + policy.session_id + "/stop",
            {**session, "state": "stopped", "live": False},
            202,
        )
        policy.handle(stop)
        assert stop.fulfilled and stop.transmitted == 1 and policy.latest["state"] == "stopped"

    def test_production_hex_session_shape_rejects_uuid_without_false_ownership(self):
        policy = TestReadonlyLifecyclePolicy.armed()
        response = {
            "session_id": TestReadonlyLifecyclePolicy.SITE,
            "key": policy.KEY,
            "kind": "channel",
            "state": "connecting",
        }
        start = LiveReadTrap("POST", policy.origin + "/api/websockets/sessions", response, 201)
        start.request.post_data = json.dumps(policy.expected_body)
        policy.handle(start)
        assert start.aborted and policy.session_id is None
        assert policy.lifecycle_errors == [
            "Owned lifecycle blocked: The owned session response lacks a valid identifier."
        ]


class TestReports:
    """Blocked and missing evidence cannot count as measured dialogs."""

    def test_complete_report_keeps_modes_separate(self):
        report = AuditReportWriter.build(
            ["site.stats.clients"], [{"key": "site.stats.clients", "status": "passed"}]
        )  # Public keys only.
        assert report["isolated_inspection"]["measured_dialogs"] == 1  # Count actual supplied inspection records.
        assert report["live_inspection"]["status"] == "blocked"  # No live execution occurred.
        assert report["live_subscription"]["status"] == "blocked"  # Never infer live success from isolated records.

    @pytest.mark.parametrize("records", [[], [{"key": "other", "status": "passed"}]])  # Prevent denominator loss.
    def test_report_rejects_missing_inventory(self, records):
        with pytest.raises(ValueError, match="inventory"):
            AuditReportWriter.build(["site.stats.clients"], records)  # Incomplete evidence must fail.

    def test_report_rejects_unstructured_private_evidence(self):
        with pytest.raises(ValueError, match="fields"):
            AuditReportWriter.build(["a"], [{"key": "a", "status": "passed", "token": "private"}])  # No raw data.

    def test_report_redacts_identifiers_and_secret_assignments(self):
        # Use synthetic values only, never copied credentials or selector data.
        evidence = (
            "11111111-2222-3333-4444-555555555555 10.0.0.1 aa:bb:cc:dd:ee:ff token=synthetic-secret"  # Redaction input.
        )
        report = AuditReportWriter.build(
            ["a"], [{"key": "a", "status": "failed", "observations": [evidence]}]
        )  # Exercise actual writer boundary.
        observations = report["isolated_inspection"]["records"][0]["observations"]  # Exported, not raw, evidence.
        assert observations == [
            "<identifier> <identifier> <identifier> token=<redacted>"
        ]  # No identifiers or assignment values.

    def test_report_path_and_permissions(self, tmp_path):
        report = AuditReportWriter.build(
            ["a"], [{"key": "a", "status": "blocked"}]
        )  # Blockers stay outside pass totals.
        with pytest.raises(ValueError, match="restricted"):
            AuditReportWriter.write(report, tmp_path)  # Refuse an unapproved artifact destination.
        assert report["isolated_inspection"]["measured_dialogs"] == 0  # A blocker is not measured inspection.

    def test_real_restricted_writer_keeps_distinct_modes_and_permissions(self):
        import stat
        from pathlib import Path

        destination = Path(__file__).resolve().parents[4] / "test-artifacts" / "websocket-dialog-audit"
        report = AuditReportWriter.build(["synthetic"], [{"key": "synthetic", "status": "passed"}])
        previous = {
            name: (destination / name).read_bytes() if (destination / name).exists() else None
            for name in ("report.json", "report.md")
        }  # Do not replace retained measured evidence with this synthetic contract test.
        try:
            AuditReportWriter.write(report, destination)  # Actual approved boundary, not arbitrary tmpdir.
            saved = json.loads((destination / "report.json").read_text())
            assert stat.S_IMODE(destination.stat().st_mode) == 0o700
            assert stat.S_IMODE((destination / "report.json").stat().st_mode) == 0o600
        finally:
            for name, content in previous.items():
                if content is None:
                    (destination / name).unlink(missing_ok=True)
                else:
                    (destination / name).write_bytes(content)  # Restore owner-only pre-existing evidence unchanged.
        assert saved["inventory"] == ["synthetic"] and saved["isolated_inspection"]["measured_dialogs"] == 1
        assert saved["live_subscription"]["status"] == "blocked"
        with pytest.raises(ValueError, match="unknown status"):
            AuditReportWriter.build(["synthetic"], [{"key": "synthetic", "status": "invented"}])


class TestMeasuredCoverage:
    """Rendered forms and successful target selection are separate counts."""

    def test_rendered_form_with_empty_targets_is_measured_not_passed(self):
        report = AuditReportWriter.build(
            ["a"], [{"key": "a", "status": "blocked", "source": "reviewed source", "selectors": []}]
        )  # Full form measurement.
        summary = report["isolated_inspection"]  # Evidence mode stays separate from status.
        assert (
            summary["measured_dialogs"] == 1 and summary["totals"]["passed"] == 0
        )  # Never convert a blocker to a pass.
        assert summary["totals"]["blocked"] == 1  # Preserve target availability as an explicit blocker.
