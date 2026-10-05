"""Fail-closed inspection boundary. No request is forwarded in isolated mode."""

import hashlib  # Reject deployed scripts that differ from the reviewed checkout.
import importlib  # Verify the installed SDK read implementations without invoking them.
import inspect  # Read installed SDK source before enabling picker endpoints.
import json  # Match the single authorized JSON start body and decode in-memory response evidence.
import logging  # Record actions without request bodies or private identifiers.
import re  # Match only the own-session bounded polling query.
import socket  # Probe availability only when the user supplies a live URL.
from urllib.parse import urlsplit  # Compare exact origins and reject ambiguous URLs.
from uuid import UUID  # Accept only identifiers returned by approved parent reads.

logger = logging.getLogger(__name__)  # Keep evidence logs bounded and ASCII.


class BrowserRequestPolicy:
    """Fulfill exact reviewed reads. Deny everything else before transmission."""

    def __init__(self, origin, responses):
        self.origin = origin  # Bind responses to one synthetic origin.
        self.responses = responses  # Map exact paths to local response bodies.
        self.denied = []  # Store only methods, never URLs, identifiers, or request bodies.
        self.transmitted = 0  # No route in this class calls continue or fetch.
        self.delayed = {}  # Tests can hold approved local responses to reproduce stale picker replies.
        self.page_headers = {}  # Tests can apply the actual application CSP to locally rendered HTML.

    def allowed(self, method, url, redirected=False):
        parsed = urlsplit(url)  # Examine the complete destination before any action.
        origin = f"{parsed.scheme}://{parsed.netloc}"  # Include the exact port and authority.
        clean = not (parsed.fragment or parsed.username or "%" in parsed.path)  # No encoded aliases.
        resource = parsed.path + ("?" + parsed.query if parsed.query else "")  # Query approval is exact, not a prefix.
        return (
            method == "GET" and origin == self.origin and clean and not redirected and resource in self.responses
        )  # Exact read.

    def install(self, context):
        logger.info("Installing isolated browser request guard")  # Record before navigation is possible.
        context.route("**/*", self.handle)  # Include pages, popups, and background HTTP requests.
        context.route_web_socket("**/*", self.deny_socket)  # Never connect a browser WebSocket to a server.
        logger.debug("Installed HTTP and WebSocket guards")  # Record both boundaries.

    def handle(self, route):
        request = route.request  # Obtain metadata only, never inspect or log credential headers.
        logger.info("Checking isolated browser request")  # Log before the request decision.
        if not self.allowed(request.method, request.url, request.redirected_from is not None):
            self.denied.append(request.method)  # Keep private destinations out of failure output.
            route.abort("blockedbyclient")  # Abort before transmission, not after a server refusal.
        else:
            parsed = urlsplit(request.url)  # The complete resource already passed the exact-set check.
            resource = parsed.path + ("?" + parsed.query if parsed.query else "")  # Keep exact scoped selector queries.
            response = self.responses[resource]  # Use only local prebuilt evidence.
            status, content_type, body = (
                (200, *response) if len(response) == 2 else response
            )  # Keep synthetic error cases local.
            if resource in self.delayed:
                self.delayed[resource].append((route, content_type, body))  # Hold only a previously approved local GET.
            else:
                route.fulfill(
                    status=status,
                    content_type=content_type,
                    body=body,
                    headers=self.page_headers if resource == "/websockets" else {},
                )  # Never dispatch a Flask or Mist handler.
        logger.debug("Completed request guard decision")  # Report no raw response content.

    def deny_socket(self, route):
        logger.info("Blocking unsolicited browser WebSocket")  # Record the attempted transport.
        self.denied.append("WEBSOCKET")  # Record only its kind, not its private URL.
        route.close()  # Do not call connect_to_server, even for the synthetic origin.
        logger.debug("Blocked browser WebSocket before connection")  # Record the completed denial.


class LiveGate:
    """Availability is not permission. This audit cannot attest a deployed server."""

    @staticmethod
    def validate_url(url):
        if not url:
            raise ValueError("An explicitly authorized portal URL is required.")  # Never use a default.
        parsed = urlsplit(url)  # Do not print the URL or embed it in exception output.
        if parsed.username or parsed.password:
            raise ValueError("Portal URL credentials are prohibited.")  # Prevent secrets entering command evidence.
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "Use an authorized HTTP origin without a path, query, or fragment."
            )  # Reject ambiguous scope.
        return parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)  # Validate before a probe.

    @classmethod
    def preflight(cls, url):
        destination = cls.validate_url(url)  # Only an explicit user-selected origin can be contacted.
        logger.info("Checking authorized portal TCP availability")  # Do not include the host in logs.
        try:
            with socket.create_connection(destination, timeout=3):
                logger.debug("Portal TCP port accepted a connection")  # No HTTP data or credentials were sent.
        except OSError:
            logger.debug("Portal TCP availability check failed")  # Do not disclose resolver or host details.
            return "portal unreachable; no HTTP request or subscription was attempted."  # Block, never pass.
        return (
            "server read-handler evidence, authentication, and deployed safety guard are not verified."  # Stay blocked.
        )


class ReadScope:
    """Permit child reads only after approved parent responses name their scope."""

    def __init__(self):
        self.sites = set()  # Keep real identifiers in memory only.
        self.maps = {}  # Bind map identifiers to the site response that supplied them.

    def allowed(self, resource):
        parts = resource.split("/")  # Query strings are rejected by the browser policy.
        if len(parts) == 6 and parts[:4] == ["", "api", "websockets", "sites"]:
            return parts[4] in self.sites and parts[5] in {"devices", "maps", "assets"}  # Exact reviewed GETs.
        if len(parts) == 8 and parts[:4] == ["", "api", "websockets", "sites"]:
            return (
                parts[5] == "maps" and parts[7] == "sdkclients" and parts[6] in self.maps.get(parts[4], set())
            )  # Bound map.
        if resource.startswith("/api/websockets/mxedges?site_id="):
            return resource.split("=", 1)[1] in self.sites  # Only one exact registered site query.
        return False  # Unknown selector paths and session operations cannot become reads.

    def register(self, resource, payload):
        if not isinstance(payload, dict):
            raise ValueError("The approved picker returned an invalid response.")  # Never infer scope from HTML.
        rows = payload.get("sites" if resource == "/api/operations/sites" else "rows", [])  # Real handler envelopes.
        if not isinstance(rows, list) or len(rows) > 10000:
            raise ValueError("The picker response exceeded the bounded scope.")  # Refuse an unbounded traversal.
        identifiers = set()  # Collect only validated IDs, never names or labels.
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("The picker returned an invalid row.")  # Do not authorize malformed records.
            value = row.get("id")  # Parent scope comes from the actual portal response.
            if not isinstance(value, str) or str(UUID(value)) != value:
                raise ValueError("The picker returned an invalid identifier.")  # Refuse encoded or malformed IDs.
            identifiers.add(value)  # Keep private identifiers out of reports and logs.
        if resource == "/api/operations/sites":
            self.sites = identifiers  # Only the portal's selected organization supplies sites.
        elif resource.endswith("/maps"):
            self.maps[resource.split("/")[4]] = identifiers  # No cross-site maps are authorized.

    @staticmethod
    def verify_sdk():
        methods = (
            ("orgs.sites", "listOrgSites"),
            ("orgs.stats", "listOrgSiteStats"),
            ("sites.devices", "listSiteDevices"),
            ("sites.maps", "listSiteMaps"),
            ("sites.assets", "listSiteAssets"),
            ("sites.stats", "getSiteSdkStatsByMap"),
            ("sites.mxedges", "listSiteMxEdges"),
            ("orgs.mxedges", "listOrgMxEdges"),
        )  # These are the eight SDK calls in the reviewed picker handlers.
        logger.info("Verifying installed selector SDK read methods")  # Do not call any method or attach credentials.
        for namespace, name in methods:
            function = getattr(
                importlib.import_module("mistapi.api.v1." + namespace), name
            )  # Read installed definition.
            source = inspect.getsource(function)  # Missing source prevents approval.
            if ".mist_get(" not in source or any(
                term in source for term in (".mist_post(", ".mist_put(", ".mist_delete(", ".mist_patch(")
            ):
                raise ValueError("An installed selector SDK method is not a verified GET.")  # Fail closed on drift.
        logger.debug("Verified eight installed selector GET implementations")  # Version is recorded separately.


class LiveRequestPolicy(BrowserRequestPolicy):
    """Fetch exact read handlers only. Block redirects and every execution route."""

    def __init__(self, origin, responses):
        super().__init__(origin, responses)  # Reuse context-wide installation and WebSocket denial.
        self.scope = ReadScope()  # Scope grows only from approved live parent responses.
        self.errors = []  # Save bounded failure reasons, not private response bodies.
        self.catalog = None  # Store the real catalog for reconciliation after navigation.
        self.reads = 0  # Count permitted GET attempts separately from prohibited transmissions.
        self.denied_categories = []  # Fixed categories identify policy gaps without exposing request paths.
        self.cache = {}  # Reuse approved picker responses in this context only, never save private body data.

    def allowed(self, method, url, redirected=False):
        parsed = urlsplit(url)  # Validate origin and raw path before any transmission.
        resource = parsed.path + ("?" + parsed.query if parsed.query else "")  # Preserve exact query spelling.
        clean = not (parsed.fragment or parsed.username or "%" in parsed.path or redirected)  # No aliases or redirects.
        same_origin = f"{parsed.scheme}://{parsed.netloc}" == self.origin  # Do not send auth to another origin.
        bootstrap = {
            "/websockets",
            "/api/websockets/catalog",
            "/api/operations/sites",
            "/api/websockets/mxedges",
        }  # Reviewed reads.
        assets = {
            path for path in self.responses if path.startswith(("/static/", "/websockets/assets/"))
        }  # Exact template list.
        return (
            method == "GET"
            and same_origin
            and clean
            and (resource in bootstrap | assets or self.scope.allowed(resource))
        )  # Default deny.

    def handle(self, route):
        request = route.request  # Never log headers, URLs, or bodies.
        parsed = urlsplit(request.url)  # Obtain the exact reviewed resource key.
        resource = parsed.path + ("?" + parsed.query if parsed.query else "")  # Queries never widen endpoint scope.
        if (
            request.method == "GET"
            and f"{parsed.scheme}://{parsed.netloc}" == self.origin
            and resource in {"/api/websockets/sessions", "/api/themes"}
            and request.redirected_from is None
        ):
            content_type, body = self.responses[
                resource
            ]  # Hide unrelated sessions and fulfill theme bootstrap locally.
            route.fulfill(status=200, content_type=content_type, body=body)  # Never read or control live sessions.
            return  # These local substitutions are disclosed in the live report.
        if request.post_data or not self.allowed(request.method, request.url, request.redirected_from is not None):
            self.denied.append(request.method)  # Record a blocked request without private data.
            self.denied_categories.append(
                "unregistered-picker-scope"
                if resource.startswith("/api/websockets/sites/")
                else (
                    "unregistered-edge-scope"
                    if resource.startswith("/api/websockets/mxedges")
                    else (
                        "unreviewed-static-asset"
                        if resource.startswith("/static/")
                        else "unreviewed-api" if resource.startswith("/api/") else "unknown-resource"
                    )
                )
            )  # Do not save arbitrary URL text or query values.
            route.abort("blockedbyclient")  # Block before the prohibited handler receives a request.
            return  # There is no execution permission or body-based exception.
        self.fetch_read(route, resource)  # Only the approved GET set reaches this call.

    def fetch_read(self, route, resource):
        logger.info("Reading approved live inspection resource")  # Log before the bounded read.
        if resource in self.cache:
            cached = self.cache[resource]  # Prior approval still requires the current registered scope.
            if cached is None:
                route.abort("blockedbyclient")  # Do not retry a failed picker for every catalog entry.
            else:
                content_type, body = cached  # Raw response stays inside this browser context.
                route.fulfill(status=200, content_type=content_type, body=body)  # Reuse actual live read evidence.
            return  # Cached reads never create another server or Mist request.
        try:
            self.reads += 1  # Count a GET attempt, not a successful inspection.
            self.transmitted += 1  # Only approved GETs enter this branch. Isolated mode stays at zero.
            response = route.fetch(max_redirects=0, max_retries=0, timeout=15000)  # Never forward a redirect.
            if response.status != 200:
                raise ValueError("An approved live read was refused or redirected.")  # No login bypass or retries.
            if resource.startswith("/api/"):
                if not response.body():
                    raise ValueError(
                        "An approved live read returned an empty body."
                    )  # Never authorize scope from no data.
                payload = (
                    response.json()
                )  # Malformed JSON must stop inspection instead of silently inventing empty choices.
                if not isinstance(payload, dict):
                    raise ValueError(
                        "An approved live read returned invalid JSON."
                    )  # Reviewed API responses use objects.
            if resource.startswith(("/static/", "/websockets/assets/")):
                expected = self.responses[resource][1]  # Compare against reviewed real source assets.
                if hashlib.sha256(response.body()).digest() != hashlib.sha256(expected).digest():
                    raise ValueError(
                        "A deployed asset differs from the reviewed checkout."
                    )  # No unreviewed browser code.
            elif resource == "/api/websockets/catalog":
                self.catalog = payload  # Keep real catalog in memory for source reconciliation.
            elif resource == "/api/operations/sites" or resource.endswith("/maps"):
                self.scope.register(resource, payload)  # Bind future reads to returned site/map identifiers.
            if resource == "/api/operations/sites" or resource.startswith(
                ("/api/websockets/sites/", "/api/websockets/mxedges")
            ):
                self.cache[resource] = (
                    response.headers.get("content-type", "application/json"),
                    response.body(),
                )  # Context lifetime only.
            route.fulfill(response=response)  # Supply the verified read, never follow a redirect.
            logger.debug("Completed approved live inspection GET")  # No response body or IDs enter logs.
        except Exception as error:
            self.cache[resource] = None  # Do not flood a refused or failed handler with automatic retries.
            self.errors.append("Live read blocked: " + type(error).__name__)  # Sanitized reason.
            route.abort("blockedbyclient")  # Leave the dialog blocked, never start an operation to recover.


class ReadonlyLifecyclePolicy(LiveRequestPolicy):
    """Admit one exact observation start and only its returned session lifecycle."""

    KEY = "site.stats.devices"  # Not a catalog-wide read badge or utility permission.

    def __init__(self, origin, responses):
        super().__init__(origin, responses)  # Reuse reviewed GET/asset verification and default denial.
        self.expected_body = None  # Nothing may start until a populated returned site is chosen.
        self.start_attempted = False  # No retries or second sessions, even after a refused start.
        self.session_id = None  # Register ownership only from the exact successful start response.
        self.latest = None  # Private state remains in memory for owned list substitution.
        self.states = set()  # Record state names only, never session identifiers or message bodies.
        self.event_count, self.stop_attempts, self.message_reads = 0, 0, 0  # Safe lifecycle evidence.
        self.data_sequences = set()  # Deduplicate actual site-source events, excluding local lifecycle notices.
        self.lifecycle_errors = []  # Store fixed error categories only.

    def arm(self, site, label):
        self.expected_body = None  # A failed re-arm must not preserve a previous site's permission.
        if site not in self.scope.sites or self.start_attempted:
            raise ValueError("The selected site is not eligible.")  # Registered scope and one attempt only.
        cached = self.cache.get("/api/websockets/sites/" + site + "/devices")  # Actual approved picker GET.
        if not cached or not json.loads(cached[1]).get("rows"):
            raise ValueError("The selected site has no verified device choices.")  # No guessed populated target.
        self.expected_body = {
            "kind": "channel",
            "key": self.KEY,
            "targets": {"site_id": [site]},
            "parameters": {},
            "confirmation": None,
            "labels": {site: label},
        }  # Exact normal UI body, including inert local title labels.

    def handle(self, route):
        request = route.request  # Do not log body, headers, URLs, or returned content.
        parsed = urlsplit(request.url)  # Lifecycle permission binds to the exact origin and raw resource.
        clean = f"{parsed.scheme}://{parsed.netloc}" == self.origin and not (
            parsed.fragment or parsed.username or "%" in parsed.path or request.redirected_from
        )  # Reject aliases and redirects.
        if clean and parsed.path == "/api/websockets/sessions" and not parsed.query:
            if request.method == "GET" and not request.post_data:
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps({"sessions": [self.latest] if self.latest else [], "limits": {}}),
                )  # Never list another user's sessions or send their identifiers to the browser.
                return
            if request.method == "POST" and self.valid_start(request.post_data):
                self.start_attempted = True  # Consume permission before transmission, including failed responses.
                self.fetch_lifecycle(route, "start")
                return
        base = "/api/websockets/sessions/" + str(self.session_id)  # Only the own returned session is eligible.
        if clean and self.session_id:
            query = re.fullmatch(r"after=\d{1,12}&limit=500", parsed.query)  # Exact bounded UI cursor schema.
            if request.method == "GET" and parsed.path == base + "/messages" and query and not request.post_data:
                self.fetch_lifecycle(route, "messages")  # Fresh reads; never use picker response caching.
                return
            if (
                request.method == "POST"
                and parsed.path == base + "/stop"
                and not parsed.query
                and not request.post_data
            ):
                if self.stop_attempts == 0:
                    self.stop_attempts += 1  # Admit only one normal-user local close.
                    self.fetch_lifecycle(route, "stop")
                    return
        super().handle(route)  # Utilities, shell, captures, arbitrary starts and foreign sessions stay denied.

    def valid_start(self, raw):
        try:
            return (
                not self.start_attempted
                and self.expected_body is not None
                and json.loads(raw or "null") == self.expected_body
            )  # Exact target/key/kind/body, not merely a matching display name.
        except (ValueError, TypeError):
            return False  # Malformed JSON is denied before transmission.

    def fetch_lifecycle(self, route, action):
        try:
            response = route.fetch(max_redirects=0, max_retries=0, timeout=15000)  # No hidden replay of POSTs.
            if response.status != {"start": 201, "messages": 200, "stop": 202}[action]:
                raise ValueError("The owned lifecycle request was refused.")  # Do not expose backend errors.
            payload = response.json()  # Parse only in memory; never save raw response content.
            session = payload.get("session") if action == "messages" else payload
            if action == "start" and isinstance(session, dict):
                issued = session.get("session_id")
                if isinstance(issued, str) and re.fullmatch(r"[0-9a-f]{16}", issued):
                    self.session_id, self.latest = issued, session  # Preserve response-issued cleanup ownership first.
            if not isinstance(session, dict) or session.get("key") != self.KEY or session.get("kind") != "channel":
                raise ValueError("The owned session response differs from the reviewed channel.")
            identifier = session.get("session_id")
            if not isinstance(identifier, str) or not re.fullmatch(r"[0-9a-f]{16}", identifier):
                raise ValueError("The owned session response lacks a valid identifier.")
            if action == "start":
                self.session_id = identifier  # Keep only the response-issued ID, never derive or guess ownership.
            elif identifier != self.session_id:
                raise ValueError("The lifecycle response is not the owned session.")
            self.latest = session  # In-memory owned list substitution allows the ordinary UI to keep its card.
            state = session.get("state")
            if state not in {"connecting", "live", "stopping", "stopped", "finished", "timed_out", "failed"}:
                raise ValueError("The owned lifecycle state is unknown.")  # No arbitrary response text in reports.
            self.states.add(state)  # Fixed state names alone are safe evidence.
            if action == "messages":
                self.message_reads += 1
                if self.expected_body is None:
                    raise ValueError("The owned session lacks its original exact start body.")
                site = self.expected_body["targets"]["site_id"][0]
                self.data_sequences.update(
                    message["seq"]
                    for message in payload.get("messages", [])
                    if message.get("source") == site and isinstance(message.get("seq"), int)
                )  # Never mistake the local "connection opened" event for remote stats output.
                self.event_count = len(self.data_sequences)
            route.fulfill(response=response)  # Return actual owned output to the normal UI, never serialize it.
        except Exception as error:
            reason = (
                str(error)
                if isinstance(error, ValueError) and not isinstance(error, json.JSONDecodeError)
                else type(error).__name__
            )
            safe = {
                "The owned lifecycle request was refused.",
                "The owned session response differs from the reviewed channel.",
                "The owned session response lacks a valid identifier.",
                "The lifecycle response is not the owned session.",
                "The owned lifecycle state is unknown.",
                "The owned session lacks its original exact start body.",
            }
            self.lifecycle_errors.append(
                "Owned lifecycle blocked: " + (reason if reason in safe else type(error).__name__)
            )
            route.abort("blockedbyclient")  # No arbitrary recovery request, retry, or remote mutation.
