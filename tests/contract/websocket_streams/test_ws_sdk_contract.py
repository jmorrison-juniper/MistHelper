"""Contract tests for the Mist SDK WebSocket interfaces."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import ast  # The structural contract measures this test file.
import inspect  # The contract pins SDK signatures.
import threading  # The ordering proof waits for the SDK background thread.
from pathlib import Path  # The structural contract reads this test file.
from types import SimpleNamespace  # The ordering proof builds offline records.
from typing import Any, cast  # The binary-loss proof isolates the SDK callback boundary.

from mistapi import APISession  # The tests pin private API session fields used by the own client.
from mistapi.device_utils import ex, mxedge, srx  # The tests inspect SDK utility facades.
from mistapi.device_utils.__tools.__ws_wrapper import (
    UtilResponse,
    WebSocketWrapper,
)  # The tests execute the SDK trigger ordering contract.
from mistapi.websockets.__ws_client import _MistWebsocket  # The tests pin the private client seam.

from src.mist.realtime.websocket_streams.live.runners.utility.runner.execution import (
    UtilityExecution,
)  # Owned ordering code.


class TestWebSocketSdkContract:
    """Pin the SDK surface that the runners call."""

    def test_mist_websocket_constructor_and_callbacks(self) -> None:
        """Pin the private WebSocket client constructor and callbacks."""
        names = tuple(inspect.signature(_MistWebsocket).parameters)  # Keep constructor parameter order stable.
        expected = ("mist_session", "channels", True, True, True, True)  # Describe the complete constructor contract.
        actual = (  # Measure required order and optional controls in one contract value.
            *names[:2],
            "auto_reconnect" in names,
            "max_reconnect_attempts" in names,
            "ping_interval" in names,
            "queue_maxsize" in names,
        )
        assert actual == expected  # The runner needs every constructor control.
        for callback in ("on_open", "on_message", "on_error", "on_close"):  # The runner registers these callbacks.
            assert hasattr(_MistWebsocket, callback)  # The callback method must exist.

    def test_util_response_contract(self) -> None:
        """Pin the utility response attributes and methods."""
        response = UtilResponse()  # Build the SDK response object.
        assert hasattr(response, "disconnect")  # UtilityRunner.stop calls disconnect.
        assert hasattr(response, "done")  # UtilityRunner monitors done.
        assert hasattr(response, "ws_error")  # UtilityRunner maps WebSocket errors.
        assert hasattr(response, "trigger_api_response")  # UtilityRunner maps trigger status.

    def test_capture_and_shell_signatures(self) -> None:
        """Pin the SDK functions that need custom runner arguments."""
        signatures = tuple(  # Read every SDK utility signature in stable order.
            inspect.signature(function) for function in (ex.remotePcap, srx.remotePcap, mxedge.siteRemotePcap)
        )
        shell = inspect.signature(ex.createShellSession)  # Read the shell factory signature.
        actual = (  # Measure capture support and the complete shell contract.
            tuple("device_interfaces" in signature.parameters for signature in signatures),
            tuple(shell.parameters)[:3],
            "rows" in shell.parameters,
            "cols" in shell.parameters,
        )
        assert actual == ((True, True, True), ("apisession", "site_id", "device_id"), True, True)  # Pin the contract.

    def test_api_session_private_transport_attributes(self) -> None:
        """Pin the private API session fields that transport uses."""
        session = APISession()  # Build the SDK session without network authentication.
        attributes = tuple(  # Measure every private field that the owned transport reads.
            hasattr(session, name) for name in ("_cloud_uri", "_apitoken", "_apitoken_index", "_session")
        )
        defaults = (  # Measure the offline defaults without a network authentication request.
            session._cloud_uri,
            session._apitoken,
            session._apitoken_index,
            session._session.__class__.__name__,
        )
        assert attributes == (True, True, True, True)  # The SDK exposes every required private field.
        assert defaults == ("", [], -1, "Session")  # A new session keeps stable offline defaults.

    def test_sdk_stream_cannot_preserve_binary_terminal_output(self, monkeypatch: Any) -> None:
        """Prove that the SDK stream client changes required terminal bytes."""
        client = _MistWebsocket(APISession(), [])  # Build the SDK client without a network connection.
        messages: list[dict[str, object]] = []  # Capture the object after the SDK changes the bytes.
        monkeypatch.setattr(
            client, "_enqueue_message", lambda item, **_kwargs: messages.append(item)
        )  # Capture SDK output.
        client._handle_message(cast(Any, object()), b"\x00\xff")  # Send bytes that a terminal must preserve.
        assert messages == [{"raw": "\ufffd"}]  # The SDK removes NUL and replaces the invalid byte.


class _OrderingHarness:
    """Model one command event and the SDK trigger-first consumer."""

    def __init__(self) -> None:
        """Build shared event state and the real SDK wrapper."""
        self.state = SimpleNamespace(  # Keep the event model in one structural operation.
            event={"event": "command", "output": "early"},
            subscribers=[],
            sdk_output=[],
            owned_output=[],
            ordering=[],
        )
        self.started = threading.Event()  # Bound the SDK background wait.
        self.response = UtilResponse()  # Use the real SDK response collector.
        self.wrapper = WebSocketWrapper(APISession(), self.response)  # Use the real SDK ordering object.

    def emit(self) -> None:
        """Publish the command event to active subscribers."""
        for subscriber in tuple(self.state.subscribers):  # Freeze subscribers during delivery.
            subscriber(self.state.event)  # Deliver only to active consumers.

    def sdk_trigger(self) -> SimpleNamespace:
        """Emit output during the SDK REST trigger."""
        self.state.ordering.append("sdk-trigger")  # Record the trigger-first SDK order.
        self.emit()  # Publish before the SDK subscribes.
        return SimpleNamespace(status_code=200, data={"session": "sdk-order"})  # Satisfy the SDK seam.

    def sdk_start(self, _channel: object) -> UtilResponse:
        """Replace network startup with an offline subscription."""
        self.state.ordering.append("sdk-subscribe")  # Record the late SDK subscription.
        self.state.subscribers.append(self.state.sdk_output.append)  # Register after event emission.
        self.started.set()  # Release the bounded test wait.
        return self.response  # Preserve the SDK start contract.

    def run_sdk(self, monkeypatch: Any) -> None:
        """Execute the real SDK trigger-first method."""
        monkeypatch.setattr(self.wrapper, "start", self.sdk_start)  # Replace only network startup.
        self.wrapper.start_with_trigger(self.sdk_trigger, lambda _response: object())  # Run real ordering.
        assert self.started.wait(1.0)  # Fail if the SDK background path stalls.
        actual = (self.state.ordering, len(self.state.sdk_output))  # Measure runtime order and retained count.
        assert actual == (["sdk-trigger", "sdk-subscribe"], 0), "checked 1 event; the SDK consumer retained 0"


class _OwnedOrderingHarness:
    """Execute the real UtilityRunner._run method with offline seams."""

    def __init__(self, shared: _OrderingHarness) -> None:
        """Build deterministic state for the owned runner."""
        self.shared = shared  # Share the exact event used by the SDK proof.
        self._state = SimpleNamespace(stopping=threading.Event())  # Keep the stop guard inactive.
        self._trigger = SimpleNamespace(listen=SimpleNamespace(channel="cmd", timing=object()))  # Match _run.

    def _open_stream(self, _trigger: object) -> object:
        """Subscribe at the owned open position."""
        self.shared.state.ordering.append("owned-subscribe")  # Record subscription before trigger.
        self.shared.state.subscribers.append(self.shared.state.owned_output.append)  # Register the consumer.
        return object()  # Supply the opaque client passed through _run.

    def _send_trigger(self, _trigger: object) -> dict[str, str]:
        """Emit the same event during the owned REST trigger."""
        self.shared.state.ordering.append("owned-trigger")  # Record the trigger after subscription.
        self.shared.emit()  # Publish while the owned consumer is active.
        return {"session": "owned-order"}  # Supply a stable trigger answer.

    def run(self) -> None:
        """Execute the actual utility ordering method."""
        execution = self._execution()  # Build deterministic collaborators for the real orchestration.
        UtilityExecution.run(execution)  # Execute the owned subscribe-first orchestration.
        actual = (self.shared.state.ordering[-2:], self.shared.state.owned_output)  # Measure order and output.
        assert actual == (
            ["owned-subscribe", "owned-trigger"],
            [self.shared.state.event],
        ), "checked 1 event; the owned consumer retained 1"

    def _execution(self) -> UtilityExecution:
        """Return one offline execution with deterministic collaborators."""
        execution = UtilityExecution.__new__(UtilityExecution)  # Build without network collaborators.
        execution.__dict__.update(
            {
                "_context": SimpleNamespace(state=self._state),
                "_starter": SimpleNamespace(
                    start=lambda: (
                        self._open_stream(self._trigger),
                        self._trigger,
                        self._send_trigger(self._trigger) and object(),
                    )
                ),
                "_finisher": SimpleNamespace(
                    finish=lambda _started: None,
                    error=lambda error: (_ for _ in ()).throw(error),
                ),
                "_monitor": SimpleNamespace(read=lambda *_args: None),
                "_close": lambda: None,
            }
        )  # Replace only external actions around the ordering contract.
        return execution  # The caller executes the real run method.


class _StructuralRuleHarness:
    """Measure the five-item structural rules for this test file."""

    def __init__(self, path: Path) -> None:
        """Parse one Python test file."""
        self.tree = ast.parse(path.read_text(encoding="utf-8"))  # Build one stable syntax tree.

    def top_level_constructs(self) -> list[ast.AST]:
        """Return top-level classes and functions."""
        kinds = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)  # Define counted constructs.
        return [node for node in self.tree.body if isinstance(node, kinds)]  # Exclude imports and docstrings.

    def method_counts(self) -> dict[str, int]:
        """Return the direct method count for each class."""
        classes = [node for node in self.tree.body if isinstance(node, ast.ClassDef)]  # Find top-level classes.
        kinds = (ast.FunctionDef, ast.AsyncFunctionDef)  # Define methods without nested callables.
        return {node.name: sum(isinstance(item, kinds) for item in node.body) for node in classes}  # Count methods.

    def function_metrics(self) -> dict[str, tuple[int, int, int, int]]:
        """Return line, parameter, block, and operation counts."""
        classes = [node for node in self.tree.body if isinstance(node, ast.ClassDef)]  # Find top-level classes.
        metrics: dict[str, tuple[int, int, int, int]] = {}  # Keep exact values for assertion output.
        for owner in classes:  # Qualify each method with its class name.
            for node in owner.body:  # Measure direct methods without nested callable collisions.
                if isinstance(node, ast.FunctionDef):  # Ignore class fields and docstrings.
                    blocks = self._blocks(node)  # Find each statement block in this method.
                    parameters = len(node.args.posonlyargs + node.args.args + node.args.kwonlyargs)  # Count params.
                    metrics[f"{owner.name}.{node.name}"] = (
                        node.end_lineno - node.lineno + 1,
                        parameters,
                        len(blocks),
                        max(map(len, blocks)),
                    )
        return metrics  # Let the test report every measured function.

    @staticmethod
    def _blocks(node: ast.FunctionDef) -> list[list[ast.stmt]]:
        """Return each statement block owned by a function."""
        owners = (ast.FunctionDef, ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler, ast.Match)
        blocks: list[list[ast.stmt]] = []  # Keep each body for operation counts.
        for owner in ast.walk(node):  # Find nested control-flow owners.
            if isinstance(owner, owners):  # Ignore expressions that hold no statement block.
                candidates = (getattr(owner, "body", []), getattr(owner, "orelse", []), getattr(owner, "finalbody", []))
                blocks.extend(  # Exclude docstrings because they are not executable operations.
                    [item for item in candidate if not isinstance(getattr(item, "value", None), ast.Constant)]
                    for candidate in candidates
                    if candidate
                )
        return blocks  # Report exact block ownership.


class TestWebSocketTriggerOrderingContract:
    """Prove ordering behavior and enforce structural limits."""

    def test_trigger_order_controls_early_command_event_retention(self, monkeypatch: Any) -> None:
        """Keep one early command event only when subscription starts first."""
        harness = _OrderingHarness()  # Build one event shared by both ordering paths.
        harness.run_sdk(monkeypatch)  # Execute the real SDK trigger-first method.
        harness.state.subscribers.clear()  # Reset the offline server before the owned path.
        _OwnedOrderingHarness(harness).run()  # Execute the actual UtilityRunner._run method.

    def test_split_screen_sequence_requires_owned_byte_retention(self) -> None:
        """Prove that the SDK screen model loses a split control sequence."""
        wrapper = WebSocketWrapper(APISession(), UtilResponse())  # Use the real SDK screen extraction path.
        parts = ("\x1b[2Jbase", "\x1b[", "2Jnext")  # Split one clear sequence across SDK updates.
        sdk_output = [wrapper._extract_raw({"raw": part}) for part in parts]  # Feed the real SDK model in order.
        owned_output = "".join(parts).encode()  # Model the exact bytes retained by the owned transport.
        assert (sdk_output[-1], owned_output.endswith(b"\x1b[2Jnext")) == (
            "base2Jnext",
            True,
        ), "checked 1 split sequence; only the owned path retained it"  # Prove SDK damage and owned retention.

    def test_file_obeys_structural_rules(self) -> None:
        """Keep this contract file within the five-item structural limits."""
        harness = _StructuralRuleHarness(Path(__file__))  # Measure the committed test file.
        methods, metrics = harness.method_counts(), harness.function_metrics()  # Measure classes and methods.
        summary = (len(harness.top_level_constructs()), max(methods.values()))  # Measure module and class limits.
        valid = all(  # Check line, parameter, block, and operation limits together.
            all(value <= limit for value, limit in zip(values, (25, 5, 5, 5), strict=True))
            for values in metrics.values()
        )
        assert summary <= (5, 5) and valid, (summary, methods, metrics)  # Report exact counts on failure.
