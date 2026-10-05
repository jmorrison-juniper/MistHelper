"""Render real application HTML and inspect real controls without a listener."""

import importlib  # Read utility SDK facades independently from the form catalog.
import inspect  # SDK signatures and documentation describe client targeting.
import json  # Fulfill synthetic selector records without calling server handlers.
import logging  # Record normal-user inspection stages without selector values.
import mimetypes  # Serve tracked assets with their real MIME types.
import re  # Resolve exact template asset URLs and channel purpose terms.
import time  # Bound the complete live inventory traversal even after individual failures.

from playwright.sync_api import expect  # Wait through locators without requiring unsafe-eval under portal CSP.

from .inventory import OperationOracle  # Keep behavior evidence separate from rendered catalog text.

logger = logging.getLogger(__name__)  # Use bounded source-key evidence only.


class IsolatedPage:
    """No application service, execution endpoint, or server process is created."""

    SITE = "11111111-2222-3333-4444-555555555555"  # Synthetic values never represent real targets.
    MAP = "22222222-3333-4444-5555-666666666666"  # Synthetic map belongs only to the first site.
    OTHER_SITE = "33333333-4444-5555-6666-777777777777"  # Second parent proves stale values disappear.
    OTHER_MAP = "44444444-5555-6666-7777-888888888888"  # This map belongs only to the second site.

    def __init__(self, root, inventory):
        self.root, self.inventory = root, inventory  # Keep template and catalog from the same checkout.

    def render(self):
        from flask import Flask, render_template  # Use the real application template engine.

        from src.mist.realtime.websocket_streams.web.blueprint.registry import (
            WebSocketBlueprint,
        )  # Real route URLs and templates.

        logger.info("Rendering real WebSocket application template")  # No listener is started.
        app = Flask(__name__, template_folder=str(self.root / "web_portal/templates"))  # Load the real base template.
        app.register_blueprint(
            WebSocketBlueprint.create()
        )  # Register handlers for URL rendering only, never dispatch requests.
        app.config["PORTAL"] = {
            "title": "Isolated audit",
            "theme": "magenta",
            "accent_color": "#008080",
            "logo_url": "/static/img/logo-default.svg",
        }  # Synthetic config.
        app.jinja_env.globals["csrf_token"] = lambda: ""  # No secret or authentication state exists.
        for endpoint, path in (
            ("dashboard.dashboard", "/"),
            ("data.data_browser", "/data"),
            ("operations.operations_page", "/operations"),
            ("maps.maps_page", "/maps"),
        ):
            app.add_url_rule(path, endpoint=endpoint)  # Resolve base navigation links without calling handlers.
        with app.test_request_context("/websockets"):
            html = render_template("websockets_page.html")  # Real template and unchanged JavaScript only.
        logger.debug("Rendered %d HTML bytes", len(html))  # Do not log HTML.
        return html  # The browser receives this local response.

    def responses(self):
        html = self.render()  # Render before browser navigation.
        responses = {"/websockets": ("text/html", html)}  # Page reads never reach a socket.
        assets = set(
            re.findall(r'(?:src|href)="(/(?:static|websockets/assets)/[^"]+)"', html)
        )  # Exact real template dependencies.
        for path in assets:
            directory, name = (
                ("web_portal/static", path[8:])
                if path.startswith("/static/")
                else ("src/mist/realtime/websocket_streams/web/static", path[len("/websockets/assets/") :])
            )  # Resolve exact assets.
            file = self.root / directory / name  # Template paths are repository-controlled, not user input.
            responses[path] = (
                mimetypes.guess_type(file)[0] or "application/octet-stream",
                file.read_bytes(),
            )  # Missing assets fail.
        responses.update(self.selector_responses())  # Supply only deterministic synthetic picker data.
        responses["/api/themes"] = (
            "application/json",
            '{"themes": []}',
        )  # portal.js bootstrap reads the reviewed local theme handler.
        return responses  # No fallback to filesystem prefixes or remote requests.

    def selector_responses(self):
        row = {"id": self.SITE, "name": "Synthetic site"}  # Do not reuse a private site name.
        base = "/api/websockets/sites/" + self.SITE  # Bind every child response to its synthetic parent.
        data = {
            "/api/websockets/catalog": self.inventory["payload"],
            "/api/websockets/sessions": {"sessions": [], "limits": {"max_sessions": 0}},
            "/api/operations/sites": {"sites": [row, {"id": self.OTHER_SITE, "name": "Synthetic site"}]},
            base + "/maps": {"rows": [{"id": self.MAP, "name": "Synthetic map"}]},
            base + "/assets": {"rows": [{"id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "name": "Synthetic asset"}]},
        }  # Real read envelopes.
        data[base + "/devices"] = {
            "rows": [
                {"id": f"aaaaaaaa-bbbb-cccc-dddd-{number:012d}", "name": "Synthetic device", "family": family}
                for number, family in enumerate(("ap", "ex", "srx", "ssr"), start=1)
            ]
        }  # Exercise family filtering.
        data[base + "/maps/" + self.MAP + "/sdkclients"] = {
            "rows": [{"id": "bbbbbbbb-cccc-dddd-eeee-ffffffffffff", "name": "Synthetic SDK client"}]
        }  # Dependent read.
        data["/api/websockets/mxedges"] = {
            "rows": [{"id": "cccccccc-dddd-eeee-ffff-aaaaaaaaaaaa", "name": "Synthetic edge"}]
        }  # Organization-scoped read only.
        data["/api/websockets/mxedges?site_id=" + self.SITE] = data[
            "/api/websockets/mxedges"
        ]  # Exact approved synthetic query.
        data["/api/websockets/sites/" + self.OTHER_SITE + "/maps"] = {
            "rows": [{"id": self.OTHER_MAP, "name": "Synthetic map"}]
        }  # Separate parent scope.
        data["/api/websockets/sites/" + self.OTHER_SITE + "/maps/" + self.OTHER_MAP + "/sdkclients"] = {
            "rows": []
        }  # Empty dependent scope.
        return {
            path: ("application/json", json.dumps(payload)) for path, payload in data.items()
        }  # Never attach SDK clients.


class DialogInspector:
    """Inspect all forms using clicks and visible controls. Never submit."""

    def __init__(self, page, inventory, live=False):
        self.page, self.inventory = page, inventory  # Use the guarded browser and complete real inventory.
        self.oracle = OperationOracle(inventory)  # Independent source and SDK requirements.
        self.live = live  # Missing live choices are capability blockers, not synthetic test failures.

    def inspect_all(self):
        logger.info("Inspecting every real operation form")  # Log before the bounded catalog traversal.
        records = []  # Preserve a result or blocker for the complete inventory.
        deadline = (
            time.monotonic() + 90 if self.live else float("inf")
        )  # Reserve time inside the 120-second test bound.
        for entry in self.inventory["entries"]:
            if time.monotonic() >= deadline:
                records.append(
                    {
                        "key": entry["key"],
                        "status": "blocked",
                        "observations": ["The bounded live inspection deadline was reached."],
                    }
                )  # No lost denominator.
                continue  # Do not send further picker requests after the deadline.
            try:
                records.append(self.inspect(entry, deadline))  # Keep every operation in the denominator.
            except Exception as error:
                category = next(
                    (
                        label
                        for phrase, label in (
                            ("strict mode violation", "ambiguous-control"),
                            ("not attached", "detached-control"),
                            ("Timeout", "timeout"),
                            ("SyntaxError", "invalid-browser-expression"),
                            ("ReferenceError", "invalid-browser-reference"),
                            ("Content Security Policy", "browser-content-policy"),
                            ("unsafe-eval", "browser-content-policy"),
                            ("not a valid selector", "invalid-selector"),
                            ("Expected", "invalid-argument"),
                            ("is not a function", "invalid-browser-call"),
                        )
                        if phrase in str(error)
                    ),
                    type(error).__name__,
                )  # Retain fixed classifications, never raw private errors.
                records.append(
                    {
                        "key": entry["key"],
                        "status": "blocked",
                        "observations": ["Browser inspection blocked: " + category],
                    }
                )  # Never save raw browser errors or private values.
        logger.debug("Measured %d operation forms", len(records))  # Report real measured count.
        return records  # Caller writes partial evidence before asserting findings.

    def inspect(self, entry, deadline=float("inf")):
        key, problems = entry["key"], []  # Public keys and fixed observation text only.
        logger.info("Inspecting operation form %s", key)  # No target values enter logs.
        self.page.get_by_test_id("ws-catalog-entry-" + key).click()  # Normal-user selection, not direct JS invocation.
        if self.page.locator("#wsSelectedTitle").inner_text() != entry["name"]:
            problems.append("The selected title does not match the catalog.")  # Real rendering defect evidence.
        if (
            self.page.locator("#wsSelectedDescription").inner_text() != entry["description"]
            or not entry["description"].strip()
        ):
            problems.append(
                "The operation purpose is absent or differs from the catalog."
            )  # Compare actual visible text.
        problems.extend(self.field_problems(entry))  # Check independent requirements and real label associations.
        problems.extend(self.purpose_problems(entry))  # Do not require a client selector for site-wide streams.
        picker = (
            LivePickerInspector(self.page, deadline) if self.live else PickerInspector(self.page)
        )  # Inspect every available live parent instead of only the first site.
        picker_problems = picker.inspect(entry)  # Exercise parent changes and filtered choices.
        if not self.live:
            problems.extend(picker_problems)  # Isolated selector data guarantees available choices.
        disabled = bool(entry.get("locked")) or not self.inventory["payload"]["ready"]  # Readiness also blocks starts.
        if bool(self.page.locator("#wsStartButton").is_disabled()) != disabled:
            problems.append("The start control does not match the catalog lock state.")  # Inspection only.
        logger.debug("Completed form inspection with %d observations", len(problems))  # Bounded count.
        return {
            "key": key,
            "status": "failed" if problems else "blocked" if picker_problems else "passed",
            "observations": problems + (picker_problems if self.live else []),
            "selectors": picker.measurements,  # Names are source field names, never private site or device names.
            "sdk_signature_verified": self.oracle.verified(key),
            "cancel": "unsupported: no operation-form Cancel control",
            "ux_review": UtilityExperienceInspector(self.page, self.inventory).inspect(
                entry
            ),  # Independent UX evidence.
            "source": "src/mist/realtime/websocket_streams/web/static/websockets.js:selectEntry/renderStartForm",
            "reproduction": "Open WebSockets. Select catalog key "
            + key
            + ". Inspect the purpose and labeled fields. Do not start.",
        }  # Sanitized record.

    def field_problems(self, entry):
        problems = (
            ["Required source or SDK inputs are absent: " + ", ".join(sorted(self.oracle.missing(entry)))]
            if self.oracle.missing(entry)
            else []
        )  # Independent oracle.
        fields = entry.get("identifiers", entry.get("targets", [])) + entry.get(
            "fields", []
        )  # Every real catalog control.
        actual = self.page.locator("[data-ws-field]").evaluate_all(
            "(nodes) => nodes.map(node => node.dataset.wsField)"
        )  # Detect stale controls.
        if sorted(actual) != sorted(field["name"] for field in fields):
            problems.append(
                "The form retains stale fields or omits current fields."
            )  # Do not silently exclude the entry.
        for field in fields:
            control = self.page.get_by_test_id("ws-field-" + field["name"])  # Actual control anchor.
            if control.count() != 1:
                problems.append("A declared field has no unique rendered control.")  # Preserve all later entries.
                continue  # Missing controls cannot support the remaining assertions.
            label = self.page.locator('label[for="wsField-' + field["name"] + '"]')  # Accessible association.
            if label.count() != 1 or field["label"] not in label.inner_text():
                problems.append("A field has no matching visible label.")  # Do not save private choice text.
            if control.evaluate("(node) => node.required") != field["required"]:
                problems.append("A field does not enforce the declared required state.")  # Browser constraint evidence.
            if field.get("picker") and control.evaluate("(node) => node.multiple") != (
                field["name"] == entry.get("repeatable")
            ):
                problems.append("A selector has the wrong multiplicity.")  # Compare the real control to source.
        return problems  # All findings retain the operation key and source anchor.

    def purpose_problems(self, entry):
        definition = self.inventory["definitions"][entry["key"]]  # Inspect actual server channel purpose.
        if not hasattr(definition, "path_template"):
            return []  # Utility wording requires separate runner-body analysis, not name-based guessing.
        terms = {
            "assets": "asset",
            "clients": "client",
            "sdkclients": "sdk",
            "pcaps": "capture",
            "devices": "device",
            "mxedges": "edge",
        }  # Bounded source terms.
        resource = definition.path_template.split("/")[-1]  # Resource is independent from the display name.
        term = terms.get(resource)  # Diagnostics and command descriptions need separate evidence.
        if term and not re.search(re.escape(term), entry["description"], flags=re.IGNORECASE):
            return [
                "The purpose does not name the resource consumed by the server channel path."
            ]  # Actionable mismatch.
        return []  # No invented device or individual-client requirement.


class PickerInspector:
    """Use actual visible selectors without an execution path."""

    def __init__(self, page, timeout=15000):
        self.page = page  # Only an already guarded page can inspect choices.
        self.measurements = []  # Retain counts and field names, not labels or selector values.
        self.timeout = timeout  # Live failures cannot multiply into an unbounded catalog journey.

    def inspect(self, entry):
        problems = []  # Retain failures for each catalog entry, not a silent exclusion.
        fields = entry.get("identifiers", entry.get("targets", []))  # Picker order comes from the real catalog.
        for field in fields:
            if not field.get("picker"):
                continue  # Plain inputs have no dependent picker behavior.
            control = self.page.get_by_test_id("ws-field-" + field["name"])  # Use the real visible selector.
            if control.count() != 1:
                continue  # The missing-control finding is already recorded.
            expect(control).not_to_contain_text("Loading...", timeout=self.timeout)  # Respect the real portal CSP.
            options = control.locator('option:not([value=""])')  # Placeholder text is not a usable choice.
            self.measurements.append(
                {
                    "field": field["name"],
                    "available_choices": options.count(),
                    "required": control.evaluate("(node) => node.required"),
                    "multiple": control.evaluate("(node) => node.multiple"),
                }
            )  # Actual DOM evidence only.
            if options.count() == 0:
                problems.append(
                    "A selector has no available choice after its parent selection."
                )  # Cannot pass incomplete picker evidence.
                continue  # Do not force a value that the normal user cannot select.
            if field["picker"] == "devices" and entry.get("family"):
                families = options.evaluate_all(
                    "(nodes) => nodes.map(node => node.dataset.family)"
                )  # Read family metadata only.
                if set(families) != {entry["family"]}:
                    problems.append(
                        "The device selector includes the wrong device family."
                    )  # Detect purpose/target mismatch.
            control.select_option(
                options.first.get_attribute("value")
            )  # Normal-user selection triggers real dependent reads.
        return problems  # No start, capture, shell, or utility operation occurs.


class UtilityExperienceInspector:
    """Review client targeting from SDK behavior, not catalog picker declarations."""

    def __init__(self, page, inventory):
        self.page, self.definitions = page, inventory["definitions"]  # Retain actual SDK-linked definitions.

    def inspect(self, entry):
        findings = []  # UX gaps do not assert that an SDK operation fails.
        cancel_count = (
            self.page.locator("#wsStartForm").get_by_role("button", name="Cancel", exact=True).count()
        )  # Actual visible form.
        if cancel_count == 0:
            findings.append(
                {
                    "category": "user-story-gap",
                    "topic": "operation-cancel",
                    "evidence": (
                        "The operation form has no Cancel control. "
                        "Replacing a selection is not explicit cancellation."
                    ),
                    "source": "src/mist/realtime/websocket_streams/web/templates/websockets_page.html:wsStartForm",
                    "reproduction": "Open WebSockets. Select "
                    + entry["key"]
                    + ". Look for Cancel in the operation form. Do not start.",
                }
            )  # Public key only.
        definition = self.definitions[entry["key"]]  # Aggregate channels have no utility SDK function.
        if hasattr(definition, "function_name"):
            findings.extend(self.client_fields(definition, entry))  # Inspect SDK-linked client controls only.
        for finding in findings:
            finding["observed_purpose"] = self.page.locator(
                "#wsSelectedDescription"
            ).inner_text()  # Reconciled public catalog wording.
            finding["operation_key"] = entry["key"]  # Per-operation traceability without private targets.
            finding["tracked_issue"] = (
                3888 if finding["topic"] == "operation-cancel" else 3889
            )  # Existing parent-filed UX work; never create duplicate issues from report generation.
            if finding["topic"] == "client-choice-assistance":
                finding["wording_issue"] = 3890
                finding["wording_repair"] = {
                    "pull_request": 3891,
                    "status": "merged",
                    "evidence_scope": "This observation is against the unchanged 2900f56 base, not the merged repair.",
                }  # Preserve old wording evidence without claiming a merged repair remains broken.
        return {
            "status": "gap" if findings else "reviewed",
            "findings": findings,
            "functional_defect_confirmed": False,
        }  # Explicitly separate gaps from verified operation failures.

    def client_fields(self, definition, entry):
        module = importlib.import_module("mistapi.device_utils." + definition.family)  # Definition inspection only.
        function = getattr(module, definition.function_name)  # Never invoke the utility, including change utilities.
        documentation = inspect.getdoc(function) or ""  # Independent installed SDK purpose evidence.
        findings = []  # Include only supported client/MAC semantics.
        for parameter in inspect.signature(function).parameters.values():
            if parameter.name not in {"macs", "mac_address", "client_id", "client_mac"}:
                continue  # Do not mistake AP MAC or aggregate stream scope for a client target.
            control = self.page.get_by_test_id("ws-field-" + parameter.name)  # Inspect actual rendered input.
            if control.count() != 1:
                continue  # Missing input is already handled by the independent required-field oracle.
            actual = control.evaluate(
                "(node) => ({tag: node.tagName, type: node.type, "
                "picker: node.dataset.wsPicker || '', required: node.required})"
            )  # No typed values saved.
            optional = (
                parameter.default is not inspect.Parameter.empty
            )  # Signature is independent from catalog required flags.
            if actual["tag"] == "INPUT" and not actual["picker"]:
                findings.append(
                    self.observation(entry, parameter.name, optional, actual, documentation)
                )  # Measured UX gap.
        return findings  # Do not require a client selector on site/map-wide channels.

    @staticmethod
    def observation(entry, name, optional, actual, documentation):
        role = (
            "optional MAC-table filter"
            if "filter the MAC table" in documentation
            else "optional client-MAC targeting path"
        )  # SDK doc semantics.
        return {
            "category": "optional-enhancement" if optional else "user-story-gap",
            "topic": "client-choice-assistance",
            "field": name,
            "sdk_required": not optional,
            "sdk_role": role,
            "observed_control": actual,
            "evidence": (
                "This rendered input path needs manual identifier entry. " "It has no site-scoped client selector."
            ),
            "recommendation": (
                "Offer a site-scoped client choice when applicable. "
                "Preserve manual entry for disconnected clients and MAC-table filters."
            ),
            "source": [
                "src/mist/realtime/websocket_streams/catalog/utilities/utility_fields.py:_SPECS",
                "src/mist/realtime/websocket_streams/web/static/websockets.js:createInput",
            ],
            "sdk_source": (
                "mistapi/device_utils/__tools/mac.py:retrieveMacTable"
                if name == "mac_address"
                else "mistapi/device_utils/__tools/dhcp.py:releaseDhcpLeases"
            ),
            "purpose_review": (
                "The purpose names the operation but does not explain this optional MAC-table filter."
                if name == "mac_address"
                else "The purpose names the operation but does not explain valid DHCP target combinations."
            ),
            "reproduction": "Open WebSockets. Select "
            + entry["key"]
            + ". Inspect "
            + name
            + " and its label. Do not submit.",
        }  # No private targets.


class LivePickerInspector:
    """Traverse every site and map serially. Never submit or select an operation start."""

    def __init__(self, page, deadline):
        self.page, self.deadline = page, deadline  # Share the full audit deadline across operations.
        self.measurements = []  # Save source field names, counts and run-local ordinal scopes only.
        self.problems = []  # Family mismatches are not empty-target capability blockers.

    def inspect(self, entry):
        fields = [
            field for field in entry.get("identifiers", entry.get("targets", [])) if field.get("picker")
        ]  # Real hierarchy.
        self.visit(entry, fields, {})  # Traverse current parent choices, not a fixed synthetic scope.
        for field in fields:
            rows = [
                row for row in self.measurements if row["field"] == field["name"]
            ]  # Aggregate this field across all parents.
            if field["required"] and not any(row["available_choices"] > 0 for row in rows):
                self.problems.append(
                    "No available " + field["name"] + " choices across all inspected parent scopes."
                )  # Genuine emptiness.
        return self.problems  # A first empty site alone must not block a later valid site.

    def visit(self, entry, fields, scope):
        if not fields:
            return  # Only picker selection is part of this read-only traversal.
        if time.monotonic() >= self.deadline:
            raise TimeoutError("The bounded live picker inspection deadline was reached.")  # Stop further GETs.
        field = fields[0]  # Process parent fields before their dependent children.
        control = self.page.get_by_test_id("ws-field-" + field["name"])  # Actual normal-user control.
        expect(control).not_to_contain_text(
            "Loading...", timeout=15000
        )  # Match the approved GET timeout; the shared traversal deadline still bounds the run.
        options = control.locator('option:not([value=""])')  # Only user-selectable values define real scope.
        values = options.evaluate_all("(nodes) => nodes.map(node => node.value)")  # Private IDs stay in memory only.
        self.measurements.append(
            {
                "field": field["name"],
                "available_choices": len(values),
                "scope": scope,
                "required": field["required"],
                "multiple": control.evaluate("(node) => node.multiple"),
            }
        )  # No names.
        if field["picker"] == "devices" and entry.get("family"):
            families = options.evaluate_all(
                "(nodes) => nodes.map(node => node.dataset.family)"
            )  # Retain family checks.
            if any(family != entry["family"] for family in families):
                self.problems.append(
                    "The device selector includes the wrong device family."
                )  # Functional form finding.
        parents = field["picker"] in {"sites", "maps"}  # All sites/maps, but not every leaf device or client.
        for ordinal, value in enumerate(values if parents else values[:1], start=1):
            if control.input_value() != value or control.evaluate(
                "(node) => node.multiple && node.selectedOptions.length !== 1"
            ):
                control.select_option(value)  # Trigger child refresh only when the actual parent selection changes.
            child_scope = {**scope, field["picker"]: ordinal} if parents else scope  # Run-local aliases only.
            self.visit(entry, fields[1:], child_scope)  # Dependent waits inspect the refreshed controls serially.
