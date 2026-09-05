"""Compare an injected stand-in against the call that the route really makes.

Why:
    Issue #1991 records a class of fault. A stand-in in the test suite answered a
    simpler shape than the real callee, the reader agreed with the stand-in, and
    both disagreed with the cloud. The whole suite stayed green while four
    blocking defects reached the first live journey.

    A stand-in is written by the same engineer who writes the reader, on the same
    day, from the same mental model. When the model is wrong, the test proves
    that two wrong things match.

    This module records the call that each route makes through each seam. A seam
    asks this module whether the injected stand-in can answer that call. A
    difference reaches the log at the point of use, and a test run raises.

    The record names the call and not the callee on purpose. Several seams fall
    back to an adapter inside the route rather than to the module function that
    the seam name suggests. The call is the one fact that both the stand-in and
    the fallback must satisfy, so the call is the contract.

    The check costs nothing in production. A seam holds a stand-in only when a
    caller injects one, so a real portal never reaches the comparison at all.
"""

from __future__ import annotations

import inspect
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from typing import Any

logger = logging.getLogger(__name__)  # The module logger, so every seam warning carries this name.

PACKAGE_ROOT = "src.upgrade_portal"  # The import root of the portal, the same root the routes use.
STRICT_VARIABLE = "UPGRADE_PORTAL_SEAM_STRICT"  # The test suite sets this, and production never does.
SENTINEL = object()  # One placeholder for a bind probe, because the probe never calls the stand-in.


class SeamShapeError(TypeError):
    """A stand-in cannot answer the call that its route makes."""


@dataclass(frozen=True)
class SeamCall:
    """One call that a route makes through a seam.

    Attributes:
        positional: The count of arguments the route passes by position.
        keywords: The keyword names the route always passes.
        extra_keywords: True when the route passes further names that it chooses at run time.
    """

    positional: int = 0
    keywords: tuple[str, ...] = ()
    extra_keywords: bool = False


@dataclass(frozen=True)
class SeamShape:
    """One seam, the calls its route makes, and the callable it falls back to.

    Attributes:
        config_key: The application configuration key that holds the stand-in.
        reader: The route module that reads this seam.
        calls: The accepted calls. A stand-in must answer at least one of them.
        fallback_module: The module path inside the portal package that holds the fallback.
        fallback_names: The accepted names of the fallback. The first match wins.
        note: One sentence that records why this seam is unusual.
    """

    config_key: str
    reader: str
    calls: tuple[SeamCall, ...]
    fallback_module: str | None = None
    fallback_names: tuple[str, ...] = ()
    note: str = ""


SEAM_SHAPES: tuple[SeamShape, ...] = (
    SeamShape(
        "MIST_READER",
        "select",
        (SeamCall(positional=1, extra_keywords=True),),
        "app.routes.select",
        ("default_cloud_read",),
        "The route passes the read name by position and every cloud parameter by keyword.",
    ),
    SeamShape(
        "DEVICE_READER",
        "select",
        (
            SeamCall(keywords=("session", "org_id", "site_id")),
            SeamCall(keywords=("org_id", "site_id")),
        ),
        "capture.devices",
        ("read_site_inventory", "read_inventory", "list_site_devices"),
        "`call_device_reader` reads the signature and drops the session when the seam names none.",
    ),
    SeamShape(
        "STATISTICS_READER",
        "select",
        (SeamCall(positional=2),),
        "capture.devices",
        ("read_device_statistics",),
    ),
    SeamShape(
        "SITE_LOCK_READER",
        "select",
        (SeamCall(positional=2),),
        "runtime.lock",
        ("read_site_locks", "read_locks", "lock_holders"),
    ),
    SeamShape(
        "CLOUD_LOGIN",
        "auth",
        (SeamCall(positional=3),),
        "app.routes.auth",
        ("default_cloud_login",),
    ),
    SeamShape(
        "CLOUD_TOKEN_SESSION",
        "auth",
        (SeamCall(positional=1),),
        "app.routes.auth",
        ("default_token_session",),
    ),
    SeamShape(
        "CLOUD_BROWSER_TOKEN_SESSION",
        "auth",
        (SeamCall(positional=2),),
        "app.routes.auth",
        ("default_browser_token_session",),
    ),
    SeamShape(
        "CLOUD_TOKEN_IDENTITY",
        "auth",
        (SeamCall(positional=1),),
        "app.routes.auth",
        ("default_token_identity",),
    ),
    SeamShape(
        "CAPTURE_RUNNER",
        "capture",
        (SeamCall(positional=1),),
        "app.routes.capture",
        ("default_runner",),
    ),
    SeamShape(
        "CAPTURE_LOADER",
        "capture and review",
        (SeamCall(positional=1),),
        None,
        (),
        "Two routes read this one key. Both call it with one capture key, and each falls back to "
        "a different store reader.",
    ),
    SeamShape(
        "CAPTURE_LISTER",
        "review",
        (SeamCall(positional=1),),
        "app.routes.review",
        ("store_capture_rows",),
        "`call_lister` adds the window keywords only when the seam declares both of them.",
    ),
    SeamShape(
        "RUN_LISTER",
        "review",
        (SeamCall(positional=1),),
        "app.routes.review",
        ("store_run_rows",),
        "The same window rule as the capture lister.",
    ),
    SeamShape(
        "RUN_LAUNCHER",
        "upgrade",
        (SeamCall(positional=1),),
        "app.wiring",
        ("start_upgrade_run",),
    ),
    SeamShape(
        "STOP_RUNNER",
        "upgrade",
        (SeamCall(positional=1),),
        "app.wiring",
        ("cancel_run",),
    ),
    SeamShape(
        "UPGRADE_VERSIONS",
        "upgrade",
        (SeamCall(positional=3),),
        "upgrade.options",
        ("read_model_versions",),
        "This seam also accepts a ready map. The comparison runs for a callable only.",
    ),
    SeamShape(
        "UPGRADE_OPTIONS_VIEW",
        "upgrade",
        (SeamCall(positional=3),),
        "upgrade.options",
        ("build_options_view",),
    ),
    SeamShape(
        "UPGRADE_OPTIONS_BUILDER",
        "upgrade",
        (SeamCall(positional=2),),
        None,
        (),
        "The route hands the run record and the request body. The module reader takes four values, "
        "so this seam has no fallback and the wiring leaves it empty on purpose.",
    ),
)

SHAPE_INDEX: dict[str, SeamShape] = {shape.config_key: shape for shape in SEAM_SHAPES}  # One lookup by key.


def strict_mode() -> bool:
    """Report whether a shape difference must raise instead of reaching the log.

    Why:
        A test run must fail on a difference, because a silent difference is the
        whole fault of issue #1991. A live portal must never fail on one, because
        a warning serves an operator better than a broken page.

    Returns:
        True when the strict environment variable holds a value.
    """
    return bool(os.environ.get(STRICT_VARIABLE))  # An unset variable reads as an empty string.


def fallback_callee(config_key: str) -> Callable[..., Any] | None:
    """Return the callable that the portal uses for one seam when no stand-in exists.

    Why:
        The portal imports these modules late, because the portal grew in stages
        and a route had to stay importable before its module landed. The same
        rule holds here, so an absent module leaves the audit quiet.

    Args:
        config_key: The configuration key of the seam.

    Returns:
        The fallback callable, or None when the seam records none.
    """
    shape = SHAPE_INDEX.get(config_key)  # An unknown key carries no record.
    if shape is None or shape.fallback_module is None:  # Two seams record no fallback on purpose.
        return None  # The caller then compares against the recorded call alone.
    try:  # The module may be absent in a trimmed install.
        module = import_module(f"{PACKAGE_ROOT}.{shape.fallback_module}")  # Late, as the routes do it.
    except ImportError:  # Not a fault, so no stack trace reaches the log.
        logger.info("seam_shapes: the module %s is not importable", shape.fallback_module)
        return None  # The caller then skips this half of the audit.
    for name in shape.fallback_names:  # The first published name wins, as the routes decide.
        candidate = getattr(module, name, None)  # A missing name reads as None.
        if callable(candidate):  # Guard against a name that holds something else.
            found: Callable[..., Any] = candidate  # The named type satisfies the strict return check.
            return found  # This is the callable a real portal would use.
    return None  # The module is present and holds none of the accepted names.


def accepts_extra_keywords(signature: inspect.Signature) -> bool:
    """Report whether a signature holds a variadic keyword parameter.

    Args:
        signature: The signature to read.

    Returns:
        True when the signature holds a `**kwargs` parameter.
    """
    return any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD  # The variadic keyword kind.
        for parameter in signature.parameters.values()  # Every declared parameter.
    )


def answers_call(signature: inspect.Signature, call: SeamCall) -> bool:
    """Report whether one signature can answer one recorded call.

    Args:
        signature: The signature of the stand-in or of the fallback.
        call: The call that the route makes.

    Returns:
        True when the signature accepts that call.
    """
    if call.extra_keywords and not accepts_extra_keywords(signature):  # The route chooses names at run time.
        return False  # A fixed name list cannot take them.
    probe = [SENTINEL] * call.positional  # One placeholder for each positional argument.
    named = dict.fromkeys(call.keywords, SENTINEL)  # One placeholder for each keyword argument.
    try:  # The bind proves the shape, and no call runs.
        signature.bind(*probe, **named)  # A placeholder never reaches any body.
    except TypeError:  # The signature cannot take this call.
        return False  # The caller reports the difference.
    return True  # The signature answers this call.


def read_signature(candidate: Any) -> inspect.Signature | None:
    """Read the signature of one callable, or report that it has none.

    Why:
        A built-in and a C callable answer no signature. That is not a fault of
        the stand-in, so the audit stays quiet for one.

    Args:
        candidate: The callable to read.

    Returns:
        The signature, or None when the callable publishes none.
    """
    try:  # A built-in raises here, and so does a callable with no introspection.
        return inspect.signature(candidate)  # The declared shape.
    except (TypeError, ValueError):  # Both mean the same thing to this audit.
        return None  # The caller then skips the comparison.


def describe_call(call: SeamCall) -> str:
    """Write one recorded call as a sentence, for a log line and for a test message.

    Args:
        call: The call to describe.

    Returns:
        One sentence that names the positional count and the keyword names.
    """
    parts = [f"{call.positional} positional arguments"]  # Every call names a count, even a count of zero.
    if call.keywords:  # A call with no keyword name needs no second clause.
        parts.append(f"the keywords {list(call.keywords)}")  # The names, in the order the route passes them.
    if call.extra_keywords:  # The route chooses these names at run time.
        parts.append("further keywords that the route chooses")  # So the stand-in needs a variadic parameter.
    return " and ".join(parts)  # One readable sentence for a log reader.


def shape_differences(config_key: str, candidate: Any) -> tuple[str, ...]:
    """List the reason one stand-in cannot answer the call of its seam.

    Args:
        config_key: The configuration key of the seam.
        candidate: The injected stand-in.

    Returns:
        One sentence when the stand-in answers no recorded call, empty otherwise.
    """
    shape = SHAPE_INDEX.get(config_key)  # An unknown key carries no record.
    signature = read_signature(candidate)  # None when the stand-in publishes none.
    if shape is None or signature is None:  # No record and no signature both mean no comparison.
        return ()  # An unreadable shape is not a difference.
    if any(answers_call(signature, call) for call in shape.calls):  # One accepted call is enough.
        return ()  # The stand-in fits.
    wanted = " or ".join(describe_call(call) for call in shape.calls)  # Name every accepted call.
    return (f"the route calls this seam with {wanted}, and the stand-in {signature} accepts none of them",)


def check_stand_in(config_key: str, candidate: Any) -> tuple[str, ...]:
    """Compare one injected stand-in against the call that its route makes.

    Why:
        Every seam of the portal calls this function the moment it reads a
        stand-in. A difference then reaches the log at the point of use, with the
        seam name, rather than as a wrong page far from its cause.

    Args:
        config_key: The configuration key of the seam.
        candidate: The injected stand-in.

    Returns:
        One sentence for each difference, empty when the stand-in fits.

    Raises:
        SeamShapeError: When strict mode is on and the stand-in fits no call.
    """
    if not callable(candidate):  # A seam keeps its own guard for a value that is not callable.
        return ()  # Nothing to compare.
    differences = shape_differences(config_key, candidate)  # Empty in the common case.
    if not differences:  # The quiet path, which every fitting stand-in takes.
        return ()  # The seam then uses the stand-in.
    for sentence in differences:  # One line for each, so a log reader needs no unpacking.
        logger.error("seam_shapes: the stand-in of the seam %s differs: %s", config_key, sentence)
    if strict_mode():  # A test run must fail here rather than pass on a wrong shape.
        raise SeamShapeError(f"The stand-in of the seam {config_key} differs. {' '.join(differences)}")
    return differences  # A live portal keeps working and carries the warning.
