"""Builds the SNMP MIB of the metrics gateway from the Mist OpenAPI file.

Why:
    A person wrote `documentation/mibs/MISTHELPER-MIB.mib` by hand. The hand
    work already made one defect. An earlier version of that file put each table
    one level too deep, so no table object was reachable by name. This package
    removes the hand editing. An engineer runs it after Mist ships a new
    OpenAPI file, and the MIB is correct again.

    The package reads three inputs and it writes one output:

    - `documentation/mist-api-openapi31json.json` gives the type, the
      description, and the proof that a Mist field still exists.
    - `src/metrics_gateway/catalog.py` gives the truth about the readings that
      the agent answers.
    - `data/mib_generator/oid_assignments.json` gives the number of each field,
      so a live OID never moves.

    The package holds five modules:

    - `document` reads the OpenAPI file and answers a question about one
      operation.
    - `schema` turns one response schema into a flat list of scalar fields.
    - `assignment` holds the allow list, the descriptor rule, and the OID
      ledger.
    - `mib` maps a field to an SNMP type and writes the SMIv2 text.
    - `runner` runs the generate action, the report action, and the check
      action.

Warning:
    This package reads the catalog. The catalog must never import this package.
    The SNMP responder answers a poll in milliseconds, and it must not import a
    module that reads a 16.6 MB file.
"""

from __future__ import annotations

from src.mib_generator.assignment import AllowList, AllowListEntry, DescriptorMaker, LedgerEntry, OidLedger
from src.mib_generator.document import OpenApiDocument
from src.mib_generator.mib import MibObject, MibWriter, SnmpTypeMapper
from src.mib_generator.runner import CandidateReport, MibGeneratorRunner
from src.mib_generator.schema import FieldRecord, SchemaFlattener

__all__ = [
    "AllowList",  # The checked-in selection of Mist endpoints.
    "AllowListEntry",  # One row of that selection.
    "CandidateReport",  # One line of the report action.
    "DescriptorMaker",  # The SMIv2 name rule.
    "FieldRecord",  # One scalar field of a selected schema.
    "LedgerEntry",  # One row of the OID ledger.
    "MibGeneratorRunner",  # The three actions.
    "MibObject",  # One object of the output MIB.
    "MibWriter",  # The SMIv2 text writer.
    "OidLedger",  # The number of every field, live or obsolete.
    "OpenApiDocument",  # The parsed OpenAPI file.
    "SchemaFlattener",  # The schema walker.
    "SnmpTypeMapper",  # The type rule.
]
