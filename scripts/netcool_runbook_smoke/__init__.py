"""Read-only smoke test of the Mist NetCool alarm integration runbook.

The package checks the runbook, the OpenAPI file, and one live Mist organization. It sends
GET requests only. Why: the operator needs one command that proves each runbook path and each
live fact before the runbook is used in a network operations center.
"""

__version__ = "1.0.0"  # Tool version that the evidence record reports.
