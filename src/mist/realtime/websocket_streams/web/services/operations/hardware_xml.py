"""Own the fixed EX chassis-inventory preset and its output contracts."""

from __future__ import annotations  # Keep the preview selection immutable.

import hashlib  # Stable device suffixes prevent portable filename collisions.
import json  # Validate the native Junos JSON response without converting XML.
import re  # Recognize terminal framing and unsafe path characters.
import xml.etree.ElementTree as ET  # nosec B405  # The parser rejects DTD and entity declarations.
from collections.abc import Mapping  # Validate the browser request without coercion.
from dataclasses import dataclass  # Bind the selected format and parsed result to one operation.

from src.mist.realtime.websocket_streams.intake.fields.error import (
    StreamRequestError,
)  # Reject unsafe preset input at the request boundary.
from src.mist.realtime.websocket_streams.intake.start_request.models import (
    BatchTargetRequest,
)  # Normalize only the server-checked frozen target rows.


class HardwareOutputError(ValueError):
    """Represent a terminal response that cannot become a successful artifact."""


@dataclass(frozen=True, slots=True)
class HardwareXmlDocument:
    """Keep one validated native command response without changing its text."""

    xml: str = ""
    json: str = ""


@dataclass(frozen=True, slots=True)
class HardwareXmlSelection:
    """Keep the output format and UI revision selected for one preview."""

    output_format: str
    scope_revision: int


class HardwareXmlSupport:
    """Group bounded XML helpers so command, target, and artifact policies stay separate."""

    class Rules:
        """Set strict limits and patterns for terminal framing and XML validation."""

        MAX_XML_BYTES = 1_048_576
        MAX_TERMINAL_BYTES = 8 * 1_048_576
        ANSI = re.compile(r"(?:\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]|\x1b[@-_])")
        XML_ROOT = re.compile(r"<(?:[A-Za-z_][\w.-]*:)?(?:rpc-reply|chassis-inventory)(?:\s|>)")
        DTD_OR_ENTITY = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)\b", re.IGNORECASE)
        ROLE = re.compile(r"^\{(?:master|backup|primary|secondary|line|member)(?::\d+)?\}$")

        @classmethod
        def terminal_output(cls, raw: bytes, prompt: str, command: str) -> str:
            """Remove only checked terminal framing while retaining native document whitespace."""
            if len(raw) > cls.MAX_TERMINAL_BYTES:
                raise HardwareOutputError("The terminal response exceeds its bounded capture size.")
            try:
                text = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                raise HardwareOutputError("The terminal response is not valid UTF-8.") from error
            lines = cls.ANSI.sub("", text).splitlines(keepends=True)
            while lines and not lines[-1].strip():
                lines.pop()
            if not lines or lines[-1].strip() != prompt.strip():
                raise HardwareOutputError("The terminal response did not end at the verified prompt.")
            lines.pop()
            while lines and (not lines[-1].strip() or cls.ROLE.fullmatch(lines[-1].strip())):
                lines.pop()
            return "".join(lines).rstrip("\r\n")

    class TargetSelector:
        """Filter EX targets and collapse duplicate logical device rows."""

        @staticmethod
        def unique_targets(
            targets: tuple[BatchTargetRequest, ...],
        ) -> tuple[tuple[BatchTargetRequest, ...], dict[str, int]]:
            """Keep one stable device identity per site and report exclusions."""
            selected: dict[tuple[str, str, str], BatchTargetRequest] = {}
            excluded: dict[str, int] = {}
            for target in targets:
                identity = HardwareXmlSupport.TargetSelector._ex_identity(target, excluded)
                if identity is None:
                    continue
                key = HardwareXmlSupport.TargetSelector._target_key(identity)
                if key in selected:
                    excluded["duplicate_device"] = excluded.get("duplicate_device", 0) + 1
                    continue
                selected[key] = BatchTargetRequest(target.target_key, identity, target.request)
            ordered = tuple(sorted(selected.values(), key=lambda item: item.target_key))
            return ordered, excluded

        @staticmethod
        def _ex_identity(target: BatchTargetRequest, excluded: dict[str, int]) -> dict[str, object] | None:
            """Keep checked EX identity fields and count non-EX rows."""
            identity = dict(target.identity)
            if str(identity.get("device_type") or "").casefold() != "ex":
                excluded["incompatible_family"] = excluded.get("incompatible_family", 0) + 1
                return None
            status = identity.get("status")
            if status != "connected":
                reason = "offline" if status == "disconnected" else "unknown_status"
                excluded[reason] = excluded.get(reason, 0) + 1
                return None
            stable_id = str(
                identity.get("device_id") or target.request.target("device_id") or identity.get("target_id") or ""
            ).strip()
            if not stable_id:
                raise StreamRequestError("bad_request", "An EX target has no stable device identifier.")
            identity["device_id"] = stable_id
            return identity

        @staticmethod
        def _target_key(identity: Mapping[str, object]) -> tuple[str, str, str]:
            """Deduplicate by organization, site, and stable device identity."""
            return (
                str(identity.get("org_id") or ""),
                str(identity.get("site_id") or ""),
                str(identity["device_id"]).casefold(),
            )

    class Decoder:
        """Validate separate native XML and JSON replies after terminal framing removal."""

        @classmethod
        def decode_output(cls, raw: bytes, prompt: str, command: str) -> HardwareXmlDocument:
            """Validate the native response for exactly one server-owned command."""
            if command not in HardwareXmlPreset.COMMANDS.values():
                raise HardwareOutputError("The hardware command is not approved.")
            xml = cls._extract_xml(raw, prompt, command)
            if command == HardwareXmlPreset.COMMANDS["json"]:
                cls._parse_json(xml)
                return HardwareXmlDocument(json=xml)
            root = cls._parse_xml(xml)
            HardwareXmlSupport.Security.reject_secret_values(root)
            return HardwareXmlDocument(xml=xml)

        @classmethod
        def _extract_xml(cls, raw: bytes, prompt: str, command: str) -> str:
            """Decode chunks and remove only the known command and final prompt."""
            output = HardwareXmlSupport.Rules.terminal_output(raw, prompt, command)
            if HardwareXmlSupport.Rules.DTD_OR_ENTITY.search(output):
                raise HardwareOutputError("The hardware response contains a prohibited DTD or entity declaration.")
            if command == HardwareXmlPreset.COMMANDS["json"]:
                match = re.search(r"(?m)^\s*\{", output)
                if match is None:
                    raise HardwareOutputError("The terminal response contains no native hardware JSON.")
                return output[match.start() :].strip()
            root_match = HardwareXmlSupport.Rules.XML_ROOT.search(output)
            if root_match is None:
                raise HardwareOutputError("The terminal response contains no chassis inventory XML.")
            declaration = re.search(r"<\?xml\b", output[: root_match.start()], re.IGNORECASE)
            start = declaration.start() if declaration is not None else root_match.start()
            return output[start:].strip()

        @classmethod
        def _parse_xml(cls, xml: str) -> ET.Element:
            """Require bounded, entity-free XML with a chassis-inventory subtree."""
            if HardwareXmlSupport.Rules.DTD_OR_ENTITY.search(xml):
                raise HardwareOutputError("The hardware XML contains a prohibited DTD or entity declaration.")
            if not xml or len(xml.encode("utf-8")) > HardwareXmlSupport.Rules.MAX_XML_BYTES:
                raise HardwareOutputError("The hardware XML exceeds its per-file size limit.")
            try:
                root = ET.fromstring(xml, parser=ET.XMLParser())  # nosec B314  # DTDs and entities are rejected.
            except ET.ParseError as error:
                raise HardwareOutputError("The hardware XML is incomplete or malformed.") from error
            root_name = cls._local_name(root.tag)
            if root_name not in {"rpc-reply", "chassis-inventory"}:
                raise HardwareOutputError("The XML root is not a Junos chassis inventory reply.")
            if root_name == "rpc-reply" and not any(
                cls._local_name(element.tag) == "chassis-inventory" for element in root.iter()
            ):
                raise HardwareOutputError("The XML reply does not contain chassis inventory.")
            return root

        @staticmethod
        def _local_name(tag: object) -> str:
            """Return the local tag component for Junos root checks."""
            return str(tag).rsplit("}", 1)[-1].rsplit(":", 1)[-1]

        @staticmethod
        def _parse_json(output: str) -> None:
            """Require native Junos chassis inventory and reject unsafe or incomplete JSON."""
            if len(output.encode("utf-8")) > HardwareXmlSupport.Rules.MAX_XML_BYTES:
                raise HardwareOutputError("The hardware JSON exceeds its per-file size limit.")
            try:
                value = json.loads(output, parse_constant=HardwareXmlSupport.Security.reject_constant)
            except (ValueError, RecursionError) as error:
                raise HardwareOutputError("The native hardware JSON is incomplete or malformed.") from error
            inventory = value.get("chassis-inventory") if isinstance(value, dict) else None
            if (
                not isinstance(inventory, list)
                or not inventory
                or not all(isinstance(item, dict) for item in inventory)
            ):
                raise HardwareOutputError("The native JSON does not contain chassis inventory.")
            if not any(isinstance(item.get("chassis"), list) and item["chassis"] for item in inventory):
                raise HardwareOutputError("The native JSON chassis inventory is empty.")
            HardwareXmlSupport.Security.reject_secret_values(value)

    class ArtifactNames:
        """Build safe, portable artifact paths that remain unique across device names."""

        UNSAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")

        @classmethod
        def safe_paths(cls, identity: Mapping[str, object], output_format: str) -> tuple[str, ...]:
            """Use a sanitized host label and stable device suffix for each output."""
            if output_format not in HardwareXmlPreset.FORMATS:
                raise HardwareOutputError("The selected hardware output format is invalid.")
            device_id = str(identity.get("device_id") or identity.get("target_id") or "").strip()
            if not device_id:
                raise HardwareOutputError("The target has no stable device identifier.")
            hostname = str(identity.get("hostname") or identity.get("label") or "device").strip()
            if HardwareXmlSupport.Security.CREDENTIAL_TEXT.search(
                hostname
            ) or HardwareXmlSupport.Security.CREDENTIAL_TEXT.search(device_id):
                raise HardwareOutputError("The target identity contains a value that cannot be persisted safely.")
            stem = cls.UNSAFE_FILENAME.sub("-", hostname).strip("-.").casefold() or "device"
            safe_id = cls.UNSAFE_FILENAME.sub("-", device_id).strip("-.").casefold() or "device"
            suffix = hashlib.sha256(device_id.casefold().encode("utf-8")).hexdigest()[:12]
            stem = f"{stem[:64]}--{safe_id[:32]}-{suffix}"
            extensions = ("xml", "json") if output_format == "both" else (output_format,)
            return tuple(f"hardware/{stem}.{extension}" for extension in extensions)

    class Security:
        """Reject credentials without treating native inventory paths as log secrets."""

        CREDENTIAL_KEY = re.compile(
            r"(?i)(?:api[_-]?token|token|authorization|cookie|set-cookie|session|sid|password|passwd|secret|private[_-]?key)"
        )
        CREDENTIAL_TEXT = re.compile(
            r"(?i)\b(?:api[_-]?token|token|authorization|cookie|set-cookie|session|sid|password|passwd|secret|private[_-]?key)"
            r"\s*[:=]\s*\S+|\bbearer\s+\S+|\bwss?://\S+|PRIVATE KEY|https?://[^\s/@]+:[^\s/@]+@"
        )

        @staticmethod
        def reject_constant(value: str) -> object:
            """Reject nonstandard numeric values rather than saving invalid JSON."""
            raise ValueError("The native JSON contains an invalid numeric value.")

        @classmethod
        def reject_secret_values(cls, value: object) -> None:
            """Inspect parsed native values while preserving the original document bytes."""
            if isinstance(value, ET.Element):
                value = {
                    HardwareXmlSupport.Decoder._local_name(value.tag): (value.text, value.tail, value.attrib, *value)
                }
            if isinstance(value, Mapping):
                cls._mapping_values(value)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    cls.reject_secret_values(item)
            elif isinstance(value, str) and cls.CREDENTIAL_TEXT.search(value):
                raise HardwareOutputError("The hardware response contains a credential and cannot be saved.")

        @classmethod
        def _mapping_values(cls, values: Mapping[str, object]) -> None:
            """Reject credential field names before inspecting every nested native value."""
            for name, value in values.items():
                if cls.CREDENTIAL_KEY.fullmatch(HardwareXmlSupport.Decoder._local_name(name)):
                    raise HardwareOutputError("The hardware response contains a credential field and cannot be saved.")
                cls.reject_secret_values(value)


class HardwareXmlPreset:
    """Validate the dedicated preset and create its server-owned shell request."""

    NAME = "ex-hardware-xml"
    COMMAND = "show chassis hardware detail | display xml | no-more"
    COMMANDS = {
        "xml": "show chassis hardware detail | display xml | no-more",
        "json": "show chassis hardware detail | display json | no-more",
    }
    FORMATS = frozenset({"xml", "json", "both"})

    @staticmethod
    def empty_selection(values: Mapping[str, object], hardware: bool) -> None:
        """Explain a refused empty preview without concealing offline exclusions."""
        excluded = values.get("excluded", {})
        counts = excluded if isinstance(excluded, Mapping) else {}
        message = (
            f"No online EX switches. Excluded offline: {counts.get('offline', 0)}. "
            f"Unknown status: {counts.get('unknown_status', 0)}."
            if hardware
            else "The selection has no eligible targets."
        )
        raise StreamRequestError("bad_request", message, {"excluded": counts})

    @classmethod
    def is_selected(cls, output: Mapping[str, object] | None) -> bool:
        """Identify only the server-stored hardware operation snapshot."""
        return output is not None and output.get("preset") == cls.NAME

    def parse(self, body: object) -> HardwareXmlSelection:
        """Validate the exact preset request and default to XML."""
        if not isinstance(body, Mapping) or set(body) - {"preset", "format", "scope_revision"}:
            raise StreamRequestError("bad_request", "The hardware preset request has an unknown field.")
        if body.get("preset") != self.NAME:
            raise StreamRequestError("bad_request", "The hardware preset is not available.")
        output_format = body.get("format", "xml")
        revision = body.get("scope_revision")
        if not isinstance(output_format, str) or output_format not in self.FORMATS:
            raise StreamRequestError("bad_request", "Choose XML, JSON, or BOTH for hardware output.")
        if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
            raise StreamRequestError("bad_request", "The selection revision is not valid.")
        return HardwareXmlSelection(output_format, revision)

    def batch_request(self, selection: HardwareXmlSelection) -> dict[str, object]:
        """Build the existing shell batch request without browser-controlled targets."""
        return {
            "operation": {"kind": "shell", "key": "ex.createShellSession"},
            "selection": {"sites": {"mode": "all"}, "resources": {"mode": "all"}},
            "parameters": {},
            "commands": [
                self.COMMANDS[output_format]
                for output_format in (
                    ("xml", "json") if selection.output_format == "both" else (selection.output_format,)
                )
            ],
            "scope_revision": selection.scope_revision,
        }
