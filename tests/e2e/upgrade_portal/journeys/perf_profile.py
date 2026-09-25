"""Profile upgrade portal routes with Flask test client and cProfile."""

from __future__ import annotations

import argparse
import cProfile
import io
import json
import os
import pstats
import statistics
import time
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

PROFILE_REPEATS = 50
SCALE_SITE_COUNT = 150
SCALE_DEVICES_PER_SITE = 20
REPO_ROOT = Path(__file__).parents[4]  # Keep artifacts in the worktree, not the pytest run directory.
ARTIFACT_ROOT = REPO_ROOT / "data" / "test-artifacts" / "upgrade-portal-journeys" / "upj-perf"
DEFAULT_OUTPUT = ARTIFACT_ROOT / "perf-results.json"
SITE_ID = "22222222-2222-2222-2222-222222222222"
SECOND_SITE_ID = "33333333-3333-3333-3333-333333333333"
ORG_ID = "11111111-1111-1111-1111-111111111111"
PREPARED_RUN_ID = "e2e-prepared-run-0001"
START_READY_RUN_ID = "e2e-start-ready-run-0001"


class SeamCounter:
    """Count seam calls while the profiler measures a route."""

    def __init__(self) -> None:
        self.counts: Counter[str] = Counter()  # Keep one counter for every seam name.

    def wrap(self, name: str, function: Callable[..., Any]) -> Callable[..., Any]:
        """Return a counting callable that preserves the wrapped result."""

        def counted(*args: Any, **kwargs: Any) -> Any:
            self.counts[name] += 1  # Count each seam call inside the profiled route.
            return function(*args, **kwargs)  # Preserve the original stand-in behavior.

        return counted  # Flask reads this callable from app configuration.

    def snapshot(self) -> dict[str, int]:
        """Return and reset the current seam call counts."""
        current = dict(self.counts)  # Copy the values before reset.
        self.counts.clear()  # Start the next route with an empty counter.
        return current  # The caller stores these counts beside the profile.


def _summary(values: list[float]) -> dict[str, float]:
    """Return median and maximum milliseconds for one route."""
    return {"median_ms": round(statistics.median(values), 3), "max_ms": round(max(values), 3)}  # Small stable output.


def _configure_environment() -> Any:
    """Import the E2E conftest and install the child environment values."""
    from tests.e2e.upgrade_portal import conftest  # Import without the gate first, so no module app builds.

    child = conftest._child_environment()  # Read the same child environment that the server process receives.
    os.environ.update(child)  # Give the test client the same session gate and cookie key.
    return conftest  # The caller builds the stand-in Flask app from this module.


def _set_cookie(client: Any, cookie: dict[str, str]) -> None:
    """Set one Flask test client cookie across Flask versions."""
    try:
        client.set_cookie(cookie["name"], cookie["value"], domain="localhost")  # Flask 3 form.
    except TypeError:
        client.set_cookie("localhost", cookie["name"], cookie["value"])  # Older Flask form.


def _signed_client(app: Any, conftest: Any) -> Any:
    """Build a signed firmware-operator test client."""
    client = app.test_client()  # The client binds no port and opens no socket.
    for cookie in conftest.firmware_operator_cookies():  # Reuse the same signed cookie pair as Playwright.
        _set_cookie(client, cookie)  # Install each cookie in the test client jar.
    return client  # The routes now see a signed operator session.


def _prepare_single_site(client: Any) -> None:
    """Store single-site context through the signed session."""
    from src.upgrade_portal.app.routes import select  # Read the session key constants.
    from src.upgrade_portal.runtime import identity  # Update the process-local operator record.
    from tests.e2e.upgrade_portal import conftest  # Read the firmware operator identity.

    owner = identity.build_owner(conftest.FIRMWARE_EMAIL, conftest.FIRMWARE_BROWSER_ID)  # Match the signed cookies.
    record = identity.SESSION_REGISTRY.get(owner.key)  # Read the registered stand-in operator.
    if record is not None:
        record.selected_site_ids = ()  # Clear multi-site targets for single-site routes.
    with client.session_transaction() as session_data:
        session_data[select.SELECTED_ORG_KEY] = ORG_ID  # Keep the selected organization in the signed session.
        session_data[select.SELECTED_MODE_KEY] = select.SINGLE_SITE_MODE  # Store the single-site mode.
        session_data[select.SELECTED_SITE_KEY] = SITE_ID  # Store the selected site.


def _prepare_multi_site(client: Any, site_ids: list[str]) -> None:
    """Store multi-site context through the signed session and operator record."""
    from src.upgrade_portal.app.routes import select  # Read the session key constants.
    from src.upgrade_portal.runtime import identity  # Update the process-local operator record.
    from tests.e2e.upgrade_portal import conftest  # Read the firmware operator identity.

    owner = identity.build_owner(conftest.FIRMWARE_EMAIL, conftest.FIRMWARE_BROWSER_ID)  # Match the signed cookies.
    record = identity.SESSION_REGISTRY.get(owner.key)  # Read the registered stand-in operator.
    if record is not None:
        record.selected_site_ids = tuple(site_ids)  # Store multi-site targets outside the cookie.
    with client.session_transaction() as session_data:
        session_data[select.SELECTED_ORG_KEY] = ORG_ID  # Keep the selected organization in the signed session.
        session_data[select.SELECTED_MODE_KEY] = select.MULTI_SITE_MODE  # Store the organization mode.
        session_data.pop(select.SELECTED_SITE_KEY, None)  # Remove the single-site pick.


def _option_body() -> dict[str, Any]:
    """Return a valid multi-device option body."""
    return {
        "selected_types": ["ap", "switch", "gateway"],
        "version": "0.15.1",
        "version_ap": "0.15.1",
        "version_switch": "0.15.1",
        "version_gateway": "0.15.1",
        "strategy": "canary",
        "canary_phases": "10,100",
        "max_failure_percentage": "5",
        "reboot": "yes",
        "junos_file_action": "yes",
    }  # Match the browser form with JSON field names.


def _profile_route(
    client: Any, method: str, path: str, repeats: int, body: dict[str, Any] | None = None
) -> tuple[dict[str, Any], str]:
    """Profile one route and return timing and cumulative call output."""
    profiler = cProfile.Profile()  # cProfile gives deterministic call attribution.
    timings: list[float] = []  # Store uncorrected profiled route wall time.

    def call_once() -> int:
        started = time.perf_counter()  # Measure the Flask route wall time.
        response = client.get(path) if method == "GET" else client.post(path, json=body or {})  # Call one route.
        timings.append((time.perf_counter() - started) * 1000.0)  # Store elapsed milliseconds.
        return response.status_code  # Keep a status code proof.

    statuses: list[int] = []  # Record every response status.
    profiler.enable()  # Start profiling the route loop.
    for _index in range(repeats):  # Repeat to include template and route costs.
        statuses.append(call_once())  # Call the route and keep its status.
    profiler.disable()  # Stop profiling before formatting output.
    stream = io.StringIO()  # Collect pstats text without a temporary file.
    pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats("cumtime").print_stats(15)  # Top cumulative time.
    result = {
        "method": method,
        "path": path,
        "repeats": repeats,
        "statuses": statuses,
        "time": _summary(timings),
    }  # Summary.
    return result, stream.getvalue()  # Return both the numeric and profile evidence.


def _large_cloud_reader(name: str, **parameters: Any) -> list[dict[str, Any]]:
    """Return a large synthetic organization without a network call."""
    del parameters  # The synthetic organization ignores request parameters.
    sites = [
        {"id": f"scale-site-{index:04d}", "name": f"Scale Site {index:04d}"} for index in range(SCALE_SITE_COUNT)
    ]  # Build 150 sites.
    if name == "listOrgSites":  # The site picker reads this list.
        return sites  # Return all synthetic sites.
    if name == "listOrgSiteStats":  # The picker also reads device counts.
        return [{"id": site["id"], "num_devices": SCALE_DEVICES_PER_SITE} for site in sites]  # Return counts.
    return []  # Unknown cloud reads stay empty.


def _large_device_reader(**parameters: Any) -> list[dict[str, Any]]:
    """Return twenty synthetic devices for one site."""
    site_id = str(parameters.get("site_id") or SITE_ID)  # Preserve the requested site identifier.
    kinds = ["ap", "switch", "gateway"]  # Use the three families that the portal supports.
    devices = []  # Build a fresh list, so callers cannot mutate a global fixture.
    for index in range(SCALE_DEVICES_PER_SITE):  # Keep a fixed device count for every site.
        kind = kinds[index % len(kinds)]  # Spread families across the synthetic inventory.
        devices.append(
            {
                "id": f"{site_id}-device-{index:04d}",
                "name": f"Scale {kind} {index:04d}",
                "type": kind,
                "mac": f"02aa{index:08x}",
                "model": f"SCALE-{kind.upper()}",
                "serial": f"SCALE{index:04d}",
                "ip": f"192.0.2.{(index % 250) + 1}",
                "version": "0.14.29216",
                "status": "connected",
                "site_id": site_id,
            }
        )  # Append a complete stand-in device row.
    return devices  # Return the synthetic device inventory.


def _large_version_map() -> dict[str, tuple[str, str]]:
    """Return firmware choices for each synthetic model."""
    return {f"SCALE-{kind.upper()}": ("0.14.29216", "0.15.1") for kind in ("ap", "switch", "gateway")}  # Match models.


def _large_options_view(_session: Any, _org_id: str, site_id: str) -> dict[str, Any]:
    """Build the route's options view from synthetic devices."""
    from src.upgrade_portal.upgrade import options  # Import the shipped option builder.

    by_model = _large_version_map()  # Build the version map once per site.
    devices = _large_device_reader(site_id=site_id)  # Build devices for this site.
    return {"targets": options.build_version_options(devices, by_model), "versions_by_model": by_model}  # Return view.


def _large_options_builder(_record: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    """Build saved options from synthetic devices."""
    from dataclasses import asdict  # Convert the shipped options dataclass.

    from src.upgrade_portal.upgrade import options  # Import the shipped target builder.

    choices = body.get("targets")  # Read explicit targets when the browser sends them.
    rows = [one for one in choices if isinstance(one, dict)] if isinstance(choices, list) else []  # Keep rows only.
    entries = options.build_targets(_large_device_reader(site_id=SITE_ID), rows)  # Build full target rows.
    return {
        "targets": entries,
        "options": asdict(options.build_options(body)),
        "warnings": list(options.target_warnings(entries)),
    }  # Return record.


def _install_counted_seams(app: Any, conftest: Any, counter: SeamCounter) -> None:
    """Install counting wrappers around the stand-in seams."""
    from src.upgrade_portal.app.routes import org_upgrade, select, upgrade  # Import configuration keys.

    app.config[select.MIST_READER_KEY] = counter.wrap("cloud_reader", conftest.stand_in_cloud_read)  # Count site reads.
    app.config[select.DEVICE_READER_KEY] = counter.wrap(
        "device_reader", conftest.stand_in_device_read
    )  # Count inventory reads.
    app.config[upgrade.OPTIONS_VIEW_KEY] = counter.wrap(
        "options_view", conftest.stand_in_options_view
    )  # Count single options reads.
    app.config[upgrade.OPTIONS_BUILDER_KEY] = counter.wrap(
        "options_builder", conftest.stand_in_options_builder
    )  # Count save reads.
    app.config[upgrade.VERSIONS_KEY] = counter.wrap(
        "versions_reader", lambda *_args: conftest.stand_in_version_map()
    )  # Count versions.
    app.config[org_upgrade.OPTIONS_VIEW_CONFIG_KEY] = counter.wrap(
        "org_options_view", conftest.stand_in_options_view
    )  # Count org reads.
    app.config[org_upgrade.OPTIONS_BUILDER_CONFIG_KEY] = counter.wrap(
        "org_options_builder", lambda _s, _o, _i, b: conftest.stand_in_options_builder({}, b)
    )  # Count org saves.


def _install_large_seams(app: Any, counter: SeamCounter) -> None:
    """Replace cloud and device seams with large synthetic data."""
    from src.upgrade_portal.app.routes import org_upgrade, select, upgrade  # Import configuration keys.

    app.config[select.MIST_READER_KEY] = counter.wrap("cloud_reader", _large_cloud_reader)  # Count large site reads.
    app.config[select.DEVICE_READER_KEY] = counter.wrap(
        "device_reader", _large_device_reader
    )  # Count large device reads.
    app.config[upgrade.OPTIONS_VIEW_KEY] = counter.wrap(
        "options_view", _large_options_view
    )  # Count large single options.
    app.config[upgrade.OPTIONS_BUILDER_KEY] = counter.wrap(
        "options_builder", _large_options_builder
    )  # Count large saves.
    app.config[upgrade.VERSIONS_KEY] = counter.wrap(
        "versions_reader", lambda *_args: _large_version_map()
    )  # Count version reads.
    app.config[org_upgrade.OPTIONS_VIEW_CONFIG_KEY] = counter.wrap(
        "org_options_view", _large_options_view
    )  # Count per-site org view calls.
    app.config[org_upgrade.OPTIONS_BUILDER_CONFIG_KEY] = counter.wrap(
        "org_options_builder", lambda _s, _o, i, b: _large_options_builder({}, b)
    )  # Count org saves.


def _profile_set(client: Any, counter: SeamCounter) -> list[dict[str, Any]]:
    """Profile the standard route set."""
    route_specs = [
        ("site-picker", "GET", "/select/site", None),
        ("inventory", "GET", f"/select/site/{SITE_ID}", None),
        ("single-options", "GET", f"/runs/{PREPARED_RUN_ID}/options", None),
        ("single-confirm", "GET", f"/runs/{PREPARED_RUN_ID}/confirm", None),
        ("single-run", "GET", f"/runs/{START_READY_RUN_ID}", None),
        ("org-options", "GET", "/upgrade/org/options", None),
        ("org-save-options", "POST", "/api/org-upgrades/options", _option_body()),
        ("org-confirm", "GET", "/upgrade/org/confirm", None),
    ]  # Cover the route families that the browser opens.
    results = []  # Store route profiles.
    for name, method, path, body in route_specs:  # Measure each route separately.
        profile, top = _profile_route(client, method, path, PROFILE_REPEATS, body)  # Run cProfile.
        profile["name"] = name  # Name the route in output.
        profile["seam_calls_per_request"] = {
            key: round(value / PROFILE_REPEATS, 3) for key, value in counter.snapshot().items()
        }  # Normalize calls.
        profile["top_cumulative"] = top  # Keep the top 15 functions.
        results.append(profile)  # Save this route.
    return results  # Return all route profiles.


def _profile_large_set(app: Any, conftest: Any) -> list[dict[str, Any]]:
    """Profile large organization pages and report scale behavior."""
    counter = SeamCounter()  # Count synthetic seam calls.
    _install_large_seams(app, counter)  # Replace stand-ins with large readers.
    client = _signed_client(app, conftest)  # Build a fresh signed client after seams change.
    large_sites = [f"scale-site-{index:04d}" for index in range(SCALE_SITE_COUNT)]  # Select all synthetic sites.
    _prepare_multi_site(client, large_sites)  # Store the large site set in the operator record.
    route_specs = [
        ("scale-site-picker", "GET", "/select/site", None),
        ("scale-inventory", "GET", f"/select/site/{large_sites[0]}", None),
        ("scale-org-options", "GET", "/upgrade/org/options", None),
        ("scale-org-save-options", "POST", "/api/org-upgrades/options", _option_body()),
        ("scale-org-confirm", "GET", "/upgrade/org/confirm", None),
    ]  # Cover the requested scaled views.
    results = []  # Store scale route profiles.
    for name, method, path, body in route_specs:  # Measure each scale route.
        profile, top = _profile_route(client, method, path, 10, body)  # Fewer repeats keep total time bounded.
        profile["name"] = name  # Name the route in output.
        profile["input_sites"] = SCALE_SITE_COUNT  # Record the site count.
        profile["input_devices_per_site"] = SCALE_DEVICES_PER_SITE  # Record device count per site.
        profile["seam_calls_per_request"] = {
            key: round(value / 10, 3) for key, value in counter.snapshot().items()
        }  # Normalize calls.
        profile["top_cumulative"] = top  # Keep the top 15 functions.
        results.append(profile)  # Save this scale result.
    return results  # Return all scale profiles.


def main() -> None:
    """Run the profile and merge results into the shared JSON file."""
    parser = argparse.ArgumentParser(description="Profile upgrade portal routes.")  # Parse a custom output path.
    parser.add_argument("--out", default=str(DEFAULT_OUTPUT), help="Result JSON path.")  # Keep one artifact path.
    args = parser.parse_args()  # Read command-line arguments.
    out_path = Path(args.out)  # Convert output path to a Path object.
    out_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure the artifact directory exists.
    conftest = _configure_environment()  # Install the safe E2E environment.
    app = conftest.build_stand_in_app()  # Build the no-cloud Flask app.
    counter = SeamCounter()  # Count normal stand-in seam calls.
    _install_counted_seams(app, conftest, counter)  # Install seam counters.
    client = _signed_client(app, conftest)  # Create a signed client for route calls.
    _prepare_single_site(client)  # Store single-site context before single routes.
    _prepare_multi_site(client, [SITE_ID, SECOND_SITE_ID])  # Store multi-site context before organization routes.
    normal_profiles = _profile_set(client, counter)  # Profile normal-size pages.
    scale_profiles = _profile_large_set(app, conftest)  # Profile large synthetic pages.
    data = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}  # Preserve browser results.
    data["server_profiles"] = normal_profiles  # Add standard cProfile results.
    data["scale_profiles"] = scale_profiles  # Add scale cProfile results.
    out_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")  # Write merged raw evidence.
    print(
        json.dumps({"out": str(out_path), "profiles": len(normal_profiles), "scale_profiles": len(scale_profiles)})
    )  # Print concise proof.


if __name__ == "__main__":
    main()  # Run the profiler when called as a script.
