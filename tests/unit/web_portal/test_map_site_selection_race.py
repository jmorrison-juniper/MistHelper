"""Execute the Maps selection handler and prove its observation guard independently."""

from __future__ import annotations

import ast
import copy
import json
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)
TEMPLATE_PATH = Path(__file__).resolve().parents[3] / "web_portal" / "templates" / "map_viewer.html"


class MapSiteFacts:
    """Keep expected controls independent of the page and its request counter."""

    SITE_A = "11111111-2222-3333-4444-555555555555"
    SITE_B = "66666666-7777-8888-9999-000000000000"
    PLACEHOLDER = "Select a site and floor plan to view the map."
    ERROR = "Failed to load floor plans."
    FLOORS = {
        "a-old": {
            "id": "aaaaaaaa-bbbb-cccc-dddd-000000000001",
            "name": "A-old",
            "has_image": True,
            "width": 600,
            "height": 400,
        },
        "b": {
            "id": "aaaaaaaa-bbbb-cccc-dddd-000000000002",
            "name": "B-map",
            "has_image": False,
            "width": 900,
            "height": 500,
        },
        "a-new": {
            "id": "aaaaaaaa-bbbb-cccc-dddd-000000000003",
            "name": "A-new",
            "has_image": True,
            "width": 1200,
            "height": 700,
        },
    }

    @classmethod
    def success(cls, *floors: str) -> dict[str, object]:
        """Return a controlled HTTP reply with known floor plan facts."""
        return {"status": 200, "body": json.dumps({"maps": [cls.FLOORS[name] for name in floors]})}

    @classmethod
    def expected(
        cls, site: str, floors: tuple[str, ...] = (), disabled: bool = False, message: str = ""
    ) -> dict[str, object]:
        """Describe complete controls without reading production state."""
        options = [{"value": "", "label": "-- Select a map --", "width": None, "height": None, "selected": True}]
        for name in floors:
            floor = cls.FLOORS[name]
            options.append(
                {
                    "value": floor["id"],
                    "label": str(floor["name"]) + ("" if floor["has_image"] else " (no image)"),
                    "width": str(floor["width"]),
                    "height": str(floor["height"]),
                    "selected": False,
                }
            )
        return {
            "site": site,
            "options": options,
            "map": "",
            "disabled": disabled,
            "message": message or cls.PLACEHOLDER,
            "errorCount": int(message == cls.ERROR),
        }

    @classmethod
    def failures(cls) -> dict[str, dict[str, object]]:
        """Describe observable failures without copying the production decision."""
        return {
            "connection": {"status": 200, "body": "", "disconnect": True},
            "http-403": {"status": 403, "body": json.dumps({"maps": [cls.FLOORS["b"]]})},
            "http-503": {"status": 503, "body": json.dumps({"maps": [cls.FLOORS["b"]]})},
            "invalid-json": {"status": 200, "body": "{"},
            "empty-body": {"status": 200, "body": ""},
            "reported-error": {"status": 200, "body": json.dumps({"maps": [], "error": "Not authenticated"})},
            "error-with-maps": {"status": 200, "body": json.dumps({"maps": [cls.FLOORS["b"]], "error": "Refused"})},
            "null-response": {"status": 200, "body": "null"},
            "array-response": {"status": 200, "body": "[]"},
            "string-response": {"status": 200, "body": '"invalid"'},
            "missing-maps": {"status": 200, "body": "{}"},
            "null-maps": {"status": 200, "body": '{"maps":null}'},
            "string-maps": {"status": 200, "body": '{"maps":"invalid"}'},
            "object-maps": {"status": 200, "body": '{"maps":{}}'},
            "markup-error": {
                "status": 200,
                "body": '{"error":"<script>window.mapSiteErrorExecuted=true</script>","maps":[]}',
            },
            **cls.invalid_entries(),
        }

    @classmethod
    def invalid_entries(cls) -> dict[str, dict[str, object]]:
        """Put invalid records after a valid record to detect partial option lists."""
        failures: dict[str, dict[str, object]] = {}
        for field in ("id", "name", "has_image", "width", "height"):
            incomplete = dict(cls.FLOORS["b"])
            del incomplete[field]
            failures[f"missing-{field}"] = {
                "status": 200,
                "body": json.dumps({"maps": [cls.FLOORS["b"], incomplete]}),
            }
        for name, entry in (("null-entry", None), ("array-entry", []), ("string-entry", "invalid")):
            failures[name] = {"status": 200, "body": json.dumps({"maps": [cls.FLOORS["b"], entry]})}
        return failures


@dataclass
class MapSiteScenario:
    """Describe controlled completions and independent expected controls."""

    actions: list[dict[str, object]]
    expected: dict[str, object]
    sites: tuple[str, ...]
    stale_index: int = -1

    @classmethod
    def state(cls, latest: str) -> MapSiteScenario:
        """Prepare pending, complete, blank, and repeated choices from fixture facts."""
        facts = MapSiteFacts
        site = "" if latest == "blank" else facts.SITE_B
        actions: list[dict[str, object]] = [{"select": facts.SITE_A}, {"select": site}]
        sites = (facts.SITE_A,) if latest == "blank" else (facts.SITE_A, facts.SITE_B)
        current, floor = 1, "b"
        if latest.startswith("a-"):
            actions.extend(({"finish": 1, "reply": facts.success("b")}, {"select": facts.SITE_A}))
            sites, site, current, floor = (facts.SITE_A, facts.SITE_B, facts.SITE_A), facts.SITE_A, 2, "a-new"
        expected = facts.expected(site, disabled=True)
        if latest.endswith(("success", "failure")):
            success = latest.endswith("success")
            reply = facts.success(floor) if success else facts.failures()["reported-error"]
            actions.append({"finish": current, "reply": reply})
            expected = (
                facts.expected(site, (floor,)) if success else facts.expected(site, disabled=True, message=facts.ERROR)
            )
        return cls(actions, expected, sites)

    @classmethod
    def order(cls, order: str) -> MapSiteScenario:
        """Describe distinct response orders without consulting the shipped algorithm."""
        facts = MapSiteFacts
        if order == "a-blank-a":
            scenario = cls.state("blank")
            scenario.actions.extend(({"select": facts.SITE_A}, {"finish": 1, "reply": facts.success("a-new")}))
            scenario.expected, scenario.sites = facts.expected(facts.SITE_A, ("a-new",)), (facts.SITE_A, facts.SITE_A)
        else:
            scenario = cls.state("a-success" if order == "a-b-a" else "success")
        stale = {"finish": 0, "reply": facts.success("a-old")}
        if order == "a-before-b":
            scenario.actions.insert(2, stale)
            scenario.stale_index = 2
        else:
            scenario.actions.append(stale)
        return scenario


class MapListObservation:
    """Reject contaminated controls, incorrect request counts, and missing evidence."""

    @staticmethod
    def check(snapshot: object, expected: dict[str, object], ledger: object, sites: tuple[str, ...]) -> None:
        """Check independent expected controls and every observed request."""
        logger.info("The observation guard will check the controls and request evidence for 1 site journey")
        if not isinstance(snapshot, dict):
            raise ValueError("The control snapshot is missing or unreadable.")
        for field in ("site", "options", "map", "disabled", "message", "errorCount"):
            if field not in snapshot:
                raise ValueError(f"The control snapshot lacks {field}.")
        if not isinstance(ledger, list) or not ledger:
            raise ValueError("The request-order evidence is missing or empty.")
        if not sites:
            raise ValueError("The expected selection evidence is empty.")
        assert len(ledger) == len(sites), "The map-list request count differs from the selection count."
        for observed, site in zip(ledger, sites, strict=True):
            assert observed == {
                "site": site,
                "method": "GET",
                "path": f"/api/maps/site/{site}/maps",
            }, "The map-list request order, method, or path changed."
        assert snapshot == expected, f"The floor plan controls differ. Expected {expected!r}. Observed {snapshot!r}."
        logger.info(
            "The observation guard checked %d requests, %d nonblank selections, and 1 control snapshot",
            len(ledger),
            len(sites),
        )


class MapCoverageObservation:
    """Require actual execution of specified statements and guarded return branches."""

    @staticmethod
    def count(functions: list[dict[str, object]], position: int) -> int | None:
        """Read the innermost V8 function and block that contain one source offset."""
        candidates = []
        for function in functions:
            ranges = function.get("ranges")
            if not isinstance(ranges, list) or not ranges:
                raise ValueError("The coverage function lacks ranges.")
            outer = ranges[0]
            if outer["startOffset"] <= position < outer["endOffset"]:
                containing = [item for item in ranges if item["startOffset"] <= position < item["endOffset"]]
                block = min(containing, key=lambda item: item["endOffset"] - item["startOffset"])
                candidates.append((outer["endOffset"] - outer["startOffset"], block["count"]))
        return min(candidates)[1] if candidates else None

    @classmethod
    def check(cls, source: str, samples: list[dict[str, object]], positions: tuple[int, ...]) -> None:
        """Fail for missing input, absent ranges, or a required unexecuted statement."""
        if not source or not samples or not positions:
            raise ValueError("The coverage source, samples, or required positions are missing or empty.")
        measured = {position: 0 for position in positions}
        for sample in samples:
            functions = sample.get("functions")
            if not isinstance(functions, list) or not functions:
                raise ValueError("The coverage sample lacks functions.")
            for position in positions:
                if position < 0 or position >= len(source):
                    raise ValueError(f"The coverage position {position} lies outside the source.")
                count = cls.count(functions, position)
                if count is not None:
                    measured[position] += count
        missing = [position for position, count in measured.items() if count == 0]
        assert missing == [], f"Required JavaScript positions did not execute: {missing}."
        logger.info(
            "The coverage guard checked %d samples and %d executed source positions", len(samples), len(positions)
        )


class MapScriptRunner:
    """Run the shipped inline script with controlled asynchronous boundaries."""

    HARNESS = r"""
const fs = require('fs');
const vm = require('vm');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const pending = [], mutations = [], states = [];
const classList = () => ({add() {}, remove() {}});
function node() {
    return {value: '', textContent: '', dataset: {}, classList: classList(),
        children: [], appendChild(child) { this.children.push(child); }, addEventListener() {}};
}
const nodes = Object.fromEntries(
    ['siteSelect', 'mapSelect', 'mapImageNote', 'plotArea', 'devicePanel', 'theme-css', 'deviceCount']
    .map(id => [id, node()]));
nodes.mapPlaceholder = node();
let disabled = true;
Object.defineProperty(nodes.mapSelect, 'disabled', {
    get() { return disabled; },
    set(value) { mutations.push('disabled'); disabled = value; }
});
Object.defineProperty(nodes.mapSelect, 'innerHTML', {
    set() {
        mutations.push('options');
        this.children = [{value: '', textContent: '-- Select a map --', dataset: {}}];
        this.value = '';
    }
});
nodes.mapSelect.appendChild = function(child) { mutations.push('options'); this.children.push(child); };
nodes.plotArea.appendChild = function(child) { nodes[child.id] = child; };
const context = {
    document: {getElementById: id => nodes[id], createElement: node, addEventListener() {}},
    Plotly: {purge() {}},
    console: {info() {}, debug() {}, error() {}},
    fetch(url) {
        return new Promise((resolve, reject) => pending.push({url, resolve, reject}));
    }
};
vm.createContext(context);
vm.runInContext(input.source, context, {timeout: 1000});
function snapshot() {
    return {
        site: nodes.siteSelect.value,
        options: nodes.mapSelect.children.map(option => ({
            value: option.value, label: option.textContent,
            width: option.dataset.width === undefined ? null : String(option.dataset.width),
            height: option.dataset.height === undefined ? null : String(option.dataset.height),
            selected: option.value === nodes.mapSelect.value
        })),
        map: nodes.mapSelect.value, disabled: nodes.mapSelect.disabled,
        message: nodes.mapPlaceholder.textContent,
        errorCount: Number(nodes.mapPlaceholder.textContent === input.error)
    };
}
(async () => {
    for (const action of input.actions) {
        const before = mutations.length;
        if (Object.hasOwn(action, 'select')) {
            nodes.siteSelect.value = action.select;
            context.onSiteChange();
        } else {
            const call = pending[action.finish];
            if (!call) throw new Error('The requested completion has no pending request.');
            if (action.reply.disconnect) {
                call.reject(new TypeError('The simulated connection failed.'));
            } else {
                call.resolve({ok: action.reply.status >= 200 && action.reply.status < 300,
                    json: () => Promise.resolve().then(() => JSON.parse(action.reply.body))});
            }
        }
        await new Promise(resolve => setImmediate(resolve));
        states.push({snapshot: snapshot(), mutations: mutations.slice(before)});
    }
    process.stdout.write(JSON.stringify({
        states,
        requests: pending.map(call => ({
            site: call.url.split('/')[4], method: 'GET', path: call.url
        }))
    }));
})().catch(error => { console.error(error.stack); process.exitCode = 1; });
"""

    @staticmethod
    def read(path: Path = TEMPLATE_PATH) -> str:
        """Fail explicitly when the required template script cannot be read."""
        logger.info("The source guard will read 1 Maps template from %s", path)
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as error:
            raise ValueError(f"The Maps source input cannot be read: {path}.") from error
        start, end = source.find("<script>"), source.rfind("</script>")
        if start < 0 or end <= start or "function onSiteChange()" not in source:
            raise ValueError(f"The Maps source input has no selection script: {path}.")
        logger.info("The source guard checked 1 Maps source file")
        return source[start + len("<script>") : end]

    @classmethod
    def run(cls, actions: list[dict[str, object]]) -> dict[str, object]:
        """Complete real promises in the specified order, without replacing handlers."""
        executable = shutil.which("node")
        if executable is None:
            pytest.fail("Node is missing, so the required offline JavaScript execution cannot run.")
        payload = {"source": cls.read(), "actions": actions, "error": MapSiteFacts.ERROR}
        logger.info("The script runner will execute %d selection and completion actions in Node", len(actions))
        result = subprocess.run(
            [executable, "-e", cls.HARNESS],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=True,
            timeout=15,
        )
        observed = json.loads(result.stdout)
        assert isinstance(observed, dict), "The script execution produced no observation object."
        logger.debug(
            "The script runner executed %d actions and recorded %d requests", len(actions), len(observed["requests"])
        )
        return observed


class TestMapSiteSelectionRace:
    """Prove current and stale completions through the actual selection handler."""

    @pytest.mark.parametrize("order", ("a-after-b", "a-before-b", "a-b-a", "a-blank-a"))
    def test_latest_site_choice_controls_results(self, order: str) -> None:
        """An earlier occurrence must remain stale even when its site ID returns."""
        scenario = MapSiteScenario.order(order)
        observed = MapScriptRunner.run(scenario.actions)
        MapListObservation.check(
            observed["states"][-1]["snapshot"], scenario.expected, observed["requests"], scenario.sites
        )
        assert observed["states"][scenario.stale_index]["mutations"] == [], "An older response changed the controls."

    @pytest.mark.parametrize("failure", tuple(MapSiteFacts.failures()))
    def test_current_failure_remains_visible(self, failure: str) -> None:
        """No observable request failure can become a successful empty list."""
        actions = [{"select": MapSiteFacts.SITE_B}, {"finish": 0, "reply": MapSiteFacts.failures()[failure]}]
        observed = MapScriptRunner.run(actions)
        expected = MapSiteFacts.expected(MapSiteFacts.SITE_B, disabled=True, message=MapSiteFacts.ERROR)
        MapListObservation.check(
            observed["states"][-1]["snapshot"], expected, observed["requests"], (MapSiteFacts.SITE_B,)
        )
        assert observed["states"][-1]["snapshot"]["errorCount"] == 1

    @pytest.mark.parametrize("latest", ("pending", "success", "failure", "blank", "a-success", "a-failure"))
    @pytest.mark.parametrize("stale", ("success", *MapSiteFacts.failures()))
    def test_stale_completion_changes_nothing(self, latest: str, stale: str) -> None:
        """Old successes and every failure shape must leave the latest state alone."""
        scenario = MapSiteScenario.state(latest)
        scenario.actions.append(
            {
                "finish": 0,
                "reply": MapSiteFacts.success("a-old") if stale == "success" else MapSiteFacts.failures()[stale],
            }
        )
        observed = MapScriptRunner.run(scenario.actions)
        MapListObservation.check(
            observed["states"][-1]["snapshot"], scenario.expected, observed["requests"], scenario.sites
        )
        assert observed["states"][-1]["snapshot"] == observed["states"][-2]["snapshot"]
        assert observed["states"][-1]["mutations"] == []

    def test_a_valid_empty_list_enables_only_the_blank_option(self) -> None:
        """An empty successful list differs from a request failure."""
        observed = MapScriptRunner.run(
            [{"select": MapSiteFacts.SITE_B}, {"finish": 0, "reply": MapSiteFacts.success()}]
        )
        expected = MapSiteFacts.expected(MapSiteFacts.SITE_B)
        MapListObservation.check(
            observed["states"][-1]["snapshot"], expected, observed["requests"], (MapSiteFacts.SITE_B,)
        )
        assert observed["states"][-1]["snapshot"]["disabled"] is False

    def test_a_new_choice_clears_the_current_error(self) -> None:
        """Recovery resets the error before another request can complete."""
        actions = [
            {"select": MapSiteFacts.SITE_B},
            {"finish": 0, "reply": MapSiteFacts.failures()["reported-error"]},
            {"select": MapSiteFacts.SITE_A},
            {"finish": 1, "reply": MapSiteFacts.success("a-new")},
        ]
        observed = MapScriptRunner.run(actions)
        assert observed["states"][2]["snapshot"] == MapSiteFacts.expected(MapSiteFacts.SITE_A, disabled=True)
        MapListObservation.check(
            observed["states"][-1]["snapshot"],
            MapSiteFacts.expected(MapSiteFacts.SITE_A, ("a-new",)),
            observed["requests"],
            (MapSiteFacts.SITE_B, MapSiteFacts.SITE_A),
        )


class TestMapSiteCoverageGuard:
    """Coverage must reject independent missing or unexecuted inputs."""

    @pytest.mark.parametrize(
        "defect", ("none", "source", "samples", "positions", "ranges", "functions", "unexecuted", "outside")
    )
    def test_missing_or_unexecuted_coverage_cannot_pass(self, defect: str) -> None:
        """A known executed statement passes and each bad observation fails."""
        source, positions = "known_statement();", (0,)
        samples = [{"functions": [{"ranges": [{"startOffset": 0, "endOffset": len(source), "count": 1}]}]}]
        if defect == "none":
            MapCoverageObservation.check(source, samples, positions)
            assert MapCoverageObservation.count(samples[0]["functions"], 0) == 1
            return
        if defect == "unexecuted":
            samples[0]["functions"][0]["ranges"][0]["count"] = 0
            with pytest.raises(AssertionError, match="did not execute"):
                MapCoverageObservation.check(source, samples, positions)
            return
        if defect in ("source", "samples", "positions"):
            source, samples, positions = (
                ("", samples, positions)
                if defect == "source"
                else ((source, [], positions) if defect == "samples" else (source, samples, ()))
            )
        elif defect in ("ranges", "functions"):
            samples = [{"functions": [{"ranges": []}]}] if defect == "ranges" else [{"functions": []}]
        else:
            positions = (len(source),)
        with pytest.raises(ValueError, match="coverage"):
            MapCoverageObservation.check(source, samples, positions)
        logger.info("The coverage guard checked and rejected 1 input case: %s", defect)


class TestMapSiteObservationGuard:
    """The acceptance decision must fail for independently incorrect evidence."""

    @pytest.mark.parametrize("defect", ("a-contamination", "a1-revival", "duplicate", "enabled", "error-replacement"))
    def test_observation_guard_rejects_bad_controls(self, defect: str) -> None:
        """Known bad controls must fail without network access or production logic."""
        expected = MapSiteFacts.expected(MapSiteFacts.SITE_B, ("b",))
        observed = copy.deepcopy(expected)
        ledger = [{"site": MapSiteFacts.SITE_B, "method": "GET", "path": f"/api/maps/site/{MapSiteFacts.SITE_B}/maps"}]
        MapListObservation.check(expected, expected, ledger, (MapSiteFacts.SITE_B,))
        if defect == "a1-revival":
            expected = MapSiteFacts.expected(MapSiteFacts.SITE_A, ("a-new",))
            observed = MapSiteFacts.expected(MapSiteFacts.SITE_A, ("a-old",))
        elif defect in ("a-contamination", "duplicate"):
            replacement = MapSiteFacts.expected(MapSiteFacts.SITE_A, ("a-old",))["options"][1]
            observed["options"].append(replacement if defect != "duplicate" else observed["options"][1])
        elif defect == "enabled":
            observed["disabled"] = True
        else:
            expected = MapSiteFacts.expected(MapSiteFacts.SITE_B, disabled=True, message=MapSiteFacts.ERROR)
        with pytest.raises(AssertionError, match="floor plan controls differ"):
            MapListObservation.check(observed, expected, ledger, (MapSiteFacts.SITE_B,))
        logger.info("The observation guard checked and rejected 1 control case: %s", defect)

    @pytest.mark.parametrize("missing", ("snapshot", "field", "requests", "empty-requests", "selections"))
    def test_observation_guard_rejects_missing_evidence(self, missing: str) -> None:
        """Absent observations and zero measurements cannot produce a pass."""
        expected = MapSiteFacts.expected(MapSiteFacts.SITE_B)
        observed: object = dict(expected)
        ledger: object = [
            {"site": MapSiteFacts.SITE_B, "method": "GET", "path": f"/api/maps/site/{MapSiteFacts.SITE_B}/maps"}
        ]
        sites = (MapSiteFacts.SITE_B,)
        if missing == "snapshot":
            observed = None
        elif missing == "field":
            del observed["options"]
        elif missing in ("requests", "empty-requests"):
            ledger = None if missing == "requests" else []
        else:
            sites = ()
        with pytest.raises(ValueError, match="snapshot|evidence"):
            MapListObservation.check(observed, expected, ledger, sites)
        logger.info("The observation guard checked and rejected 1 missing-input case: %s", missing)

    @pytest.mark.parametrize("source", ("missing", "empty", "unrecognized", "unreadable"))
    def test_real_script_reader_rejects_invalid_inputs(self, tmp_path: Path, source: str) -> None:
        """A missing or unreadable source file must stop the required guard."""
        path = tmp_path / "invalid-map-source.html"
        if source == "unreadable":
            path.mkdir()
        elif source != "missing":
            path.write_text("" if source == "empty" else "<script>function unrelated() {}</script>", encoding="utf-8")
        with pytest.raises(ValueError, match="Maps source input"):
            MapScriptRunner.read(path)
        logger.info("The source guard checked and rejected 1 source-input case: %s", source)

    def test_observation_guard_rejects_wrong_request_order(self) -> None:
        """A correct control snapshot cannot conceal an incorrect request ledger."""
        expected = MapSiteFacts.expected(MapSiteFacts.SITE_B, ("b",))
        ledger = [{"site": MapSiteFacts.SITE_A, "method": "GET", "path": f"/api/maps/site/{MapSiteFacts.SITE_A}/maps"}]
        with pytest.raises(AssertionError, match="request order"):
            MapListObservation.check(expected, expected, ledger, (MapSiteFacts.SITE_B,))
        with pytest.raises(AssertionError, match="request count"):
            MapListObservation.check(expected, expected, ledger, (MapSiteFacts.SITE_A, MapSiteFacts.SITE_B))
        logger.info("The observation guard checked and rejected 2 request-order cases")

    @pytest.mark.parametrize("mode", ("1", "0", "unset", "true", "available"))
    def test_browser_import_guard_preserves_normal_skips_and_strict_failures(
        self, monkeypatch: pytest.MonkeyPatch, mode: str
    ) -> None:
        """Execute the actual import decision without a browser or missing environment."""
        path = Path(__file__).resolve().parents[2] / "e2e" / "web_portal" / "test_map_site_selection_race_journey.py"
        nodes = ast.parse(path.read_text(encoding="utf-8"), filename=str(path)).body
        guards = [node for node in nodes if isinstance(node, ast.Try)]
        assert len(guards) == 1, "The browser module must contain one required import decision."
        code = compile(ast.Module(body=guards, type_ignores=[]), str(path), "exec")
        calls: list[str] = []

        def missing_package(name: str, **_options: object) -> object:
            """Simulate only the package boundary, not the required import decision."""
            calls.append(name)
            if mode != "available":
                pytest.skip("The Playwright package is not installed.", allow_module_level=True)
            return object()

        monkeypatch.setattr(pytest, "importorskip", missing_package)
        monkeypatch.setenv("UPGRADE_PORTAL_E2E_STRICT", mode)
        if mode == "unset":
            monkeypatch.delenv("UPGRADE_PORTAL_E2E_STRICT")
        import os

        if mode == "available":
            exec(code, {"pytest": pytest, "os": os})
        else:
            failure = pytest.UsageError if mode == "1" else pytest.skip.Exception
            with pytest.raises(failure, match="Playwright package is not installed"):
                exec(code, {"pytest": pytest, "os": os})
        assert calls == ["playwright.sync_api"]
        logger.info("The browser import guard checked 1 package decision in mode %s", mode)
