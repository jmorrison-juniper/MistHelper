"""Contract tests for WebSocket utility trigger parity."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import importlib  # The test calls each SDK family facade.
import inspect  # The test reads SDK signatures for sample arguments.
import threading  # The recorder waits for SDK background trigger threads.

from src.websocket_streams.catalog.model import Safety  # The shell entry uses a separate trigger helper.
from src.websocket_streams.catalog.sdk_annotation import SdkAnnotation  # The test converts SDK enum values.
from src.websocket_streams.catalog.utilities.utility_catalog import UtilityCatalog  # Read the utility leaf class.
from src.websocket_streams.intake.start_request.models import (
    StartRequest,  # The trigger table accepts checked requests.
)
from src.websocket_streams.live.runners.utility.triggers.table import UtilityTriggerTable  # The table under test.


class RecordedResponse:
    """A fake SDK response for recorded trigger calls."""

    status_code = 599  # The SDK sees a failed trigger and does not open a websocket.
    data = {"detail": "recorded"}  # The SDK error path needs a dictionary body.
    headers: dict[str, str] = {}  # Generated SDK functions can read headers.


class RecordingSession:
    """Record SDK REST calls without a network."""

    def __init__(self) -> None:
        """Build one recording API session."""
        self.calls: list[tuple[str, str, object]] = []  # Keep recorded requests in arrival order.
        self.event = threading.Event()  # SDK trigger threads set this event.
        self._cloud_uri = "api.mist.com"  # The SDK websocket classes expect this private field.
        self._apitoken = ["token"]  # The SDK endpoint code expects a token list.
        self._apitoken_index = 0  # The SDK endpoint code reads the active token index.

    def mist_post(self, uri: str, body: object = None, *_args: object, **_kwargs: object) -> RecordedResponse:
        """Record one POST request.

        Args:
            uri: The request path.
            body: The request body.

        Returns:
            The fake recorded response.
        """
        self.calls.append(("POST", uri, body))  # Store method, path, and body.
        self.event.set()  # Wake the test after the SDK background thread records.
        return RecordedResponse()  # Prevent any network call.


class TestUtilityTriggerParity:
    """Compare owned trigger requests with the Mist SDK."""

    SITE_ID = "11111111-2222-3333-4444-555555555555"  # Stable site identifier for parity.
    DEVICE_ID = "00000000-0000-0000-1000-aabbccddeeff"  # Stable device identifier for parity.
    ORG_ID = "99999999-8888-7777-6666-555555555555"  # Stable organization identifier for parity.
    SAMPLES = {
        "host": "8.8.8.8",
        "count": 5,
        "size": 100,
        "vrf": "default",
        "network": "corp",
        "service_name": "svc",
        "ssid": "corp-ssid",
        "route_type": "bgp",
        "ip": "10.0.0.1",
        "neighbor": "10.0.0.2",
        "prefix": "10.0.0.0/24",
        "port_id": "ge-0/0/1",
        "port_ids": ["ge-0/0/1"],
        "macs": ["aabbccddeeff"],
        "mac_address": "aabbccddeeff",
        "ap_mac": "aabbccddeeff",
        "vlan_id": 10,
        "self_originate": True,
        "service_ids": ["svc1"],
        "interfaces": ["ge-0/0/1"],
        "tcpdump_expression": "icmp",
        "num_packets": 10,
        "max_pkt_len": 512,
        "band": "5",
        "protocol": "icmp",
        "node": "node0",
    }  # The samples match the research recorder values.

    def test_utility_trigger_table_matches_sdk_requests(self) -> None:
        """Compare every owned utility trigger request with the SDK."""
        table = UtilityTriggerTable()  # Build the owned trigger table.
        compared = 0  # Count measured keys for the guard assertion.
        for entry in UtilityCatalog().entries():  # Check each utility in catalog order.
            if entry.safety is Safety.SHELL:  # Shell triggers use a separate helper.
                continue  # The shell guard runs after the utility loop.
            sdk_call = self._sdk_call(entry)  # Record the SDK request offline.
            request = self._request(entry, sdk_call[2])  # Build the matching checked request.
            owned = table.request_for(request)  # Build the owned trigger request.
            assert (owned.method, owned.path, owned.body) == sdk_call  # The owned trigger must match the SDK.
            compared += 1  # Count each measured utility trigger.
        shell_call = self._sdk_shell_call()  # Record one SDK shell trigger.
        shell = table.shell_request(self.SITE_ID, self.DEVICE_ID)  # Build the owned shell trigger.
        assert (shell.method, shell.path, shell.body) == shell_call  # The owned shell trigger must match the SDK.
        compared += 1  # Count the shell trigger.
        print(f"Compared {compared} WebSocket utility trigger keys.")  # Report the guard measurement.
        assert compared >= 53, f"Compared only {compared} WebSocket utility trigger keys."  # Guard the contract.

    def _sdk_call(self, entry: object) -> tuple[str, str, object]:
        """Record the SDK request for one catalog entry.

        Args:
            entry: The utility catalog entry.

        Returns:
            The recorded SDK method, path, and body.
        """
        module = importlib.import_module(f"mistapi.device_utils.{entry.family}")  # Load the SDK family facade.
        function = getattr(module, entry.function_name)  # Read the SDK facade function.
        session = RecordingSession()  # Build one isolated recorder.
        kwargs = self._sdk_kwargs(entry, function, session)  # Build SDK arguments from samples.
        function(**kwargs)  # Trigger the SDK request path without a network.
        session.event.wait(3.0)  # Wait for the SDK background trigger thread.
        return session.calls[0]  # Each utility sends one trigger request.

    def _sdk_shell_call(self) -> tuple[str, str, object]:
        """Record one SDK shell trigger request.

        Returns:
            The recorded SDK method, path, and body.
        """
        module = importlib.import_module("mistapi.device_utils.ex")  # EX and SRX use the same shell helper.
        session = RecordingSession()  # Build one isolated recorder.
        try:  # The fake status makes the SDK raise after it records the REST call.
            module.createShellSession(session, site_id=self.SITE_ID, device_id=self.DEVICE_ID)  # Record shell trigger.
        except RuntimeError:  # The fake response intentionally stops the SDK.
            pass  # The recorded call is the evidence.
        method, path, body = session.calls[0]  # Read the recorded shell request.
        return method, path, {} if body is None else body  # Shell contract uses an empty body.

    def _sdk_kwargs(self, entry: object, function: object, session: RecordingSession) -> dict[str, object]:
        """Build SDK keyword arguments for one catalog entry.

        Args:
            entry: The utility catalog entry.
            function: The SDK facade function.
            session: The recording API session.

        Returns:
            Keyword arguments for the SDK call.
        """
        signature = inspect.signature(function)  # Read the SDK target parameters.
        kwargs: dict[str, object] = {"apisession": session}  # Every SDK call needs the API session.
        for name in ("site_id", "device_id", "org_id"):  # Add target identifiers that the SDK declares.
            if name in signature.parameters:  # The SDK function accepts this target.
                kwargs[name] = {  # Select the matching target sample for the SDK parameter.
                    "site_id": self.SITE_ID,
                    "device_id": self.DEVICE_ID,
                    "org_id": self.ORG_ID,
                }[name]
        for field in entry.fields:  # Add catalog sample parameters.
            if field.name in signature.parameters:  # Derived capture fields are converted below.
                self._add_field(kwargs, function, field)  # Convert enums to SDK enum objects.
        if "duration" in signature.parameters:  # Captures and screens use the research duration.
            kwargs["duration"] = 60  # The owned runner forces a 60 second capture.
        if "device_interfaces" in signature.parameters:  # Wired captures need nested interfaces.
            kwargs["device_interfaces"] = {self.DEVICE_ID: {"ge-0/0/1": None}}  # Match the runner conversion.
        return kwargs  # The caller invokes the SDK.

    def _add_field(self, kwargs: dict[str, object], function: object, field: object) -> None:
        """Add one sampled field to SDK keyword arguments.

        Args:
            kwargs: The keyword arguments under construction.
            function: The SDK facade function.
            field: The catalog field.
        """
        value = self.SAMPLES[field.name]  # Every catalog field has a parity sample.
        annotation = SdkAnnotation.hints(function).get(field.name)  # Read the SDK annotation for enums.
        enum_type = SdkAnnotation.enum_type(annotation)  # Find the enum type when present.
        if (  # Reject samples that do not fit the SDK enum.
            enum_type is not None and isinstance(value, str) and value not in {member.value for member in enum_type}
        ):  # Pick a valid enum.
            value = next(iter(enum_type)).value  # Match the recorder rule for a mismatched generic sample.
        kwargs[field.name] = (  # Store the SDK-shaped sample value for this field.
            enum_type(value) if enum_type is not None and isinstance(value, str) else value
        )  # Store value.

    def _request(self, entry: object, sdk_body: object) -> StartRequest:
        """Build a checked start request that matches the SDK sample call.

        Args:
            entry: The utility catalog entry.
            sdk_body: The recorded SDK body.

        Returns:
            A checked start request for the owned table.
        """
        parameters = {field.name: self._request_value(field, sdk_body) for field in entry.fields}  # Match SDK samples.
        if isinstance(sdk_body, dict) and "num_packets" not in sdk_body:  # Non-captures must omit capture defaults.
            parameters = {  # Drop capture defaults from non-capture SDK bodies.
                key: value for key, value in parameters.items() if key not in {"num_packets", "max_pkt_len"}
            }
        targets = {  # Provide every identifier that the trigger table can request.
            "org_id": (self.ORG_ID,),  # Include org routes.
            "site_id": (self.SITE_ID,),
            "device_id": (self.DEVICE_ID,),
            "mxedge_id": (self.DEVICE_ID,),
        }  # Provide every target used by the trigger table.
        return StartRequest("utility", entry, targets, parameters, "Utility")  # Return the checked request.

    def _request_value(self, field: object, sdk_body: object) -> object:
        """Return the checked request value that matches the recorded SDK body.

        Args:
            field: The catalog field.
            sdk_body: The recorded SDK body.

        Returns:
            The value for the checked start request.
        """
        if isinstance(sdk_body, dict) and field.name in sdk_body:  # Prefer the body value that the SDK sent.
            return sdk_body[field.name]  # This handles per-function enum defaults.
        if isinstance(sdk_body, dict) and field.name == "port_id" and "port" in sdk_body:  # SDK renames this field.
            return sdk_body["port"]  # Match cable and monitor traffic.
        return self.SAMPLES[field.name]  # Derived fields keep their explicit samples.
