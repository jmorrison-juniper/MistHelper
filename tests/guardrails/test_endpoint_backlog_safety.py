"""Guard safety decisions for the endpoint backlog."""

from __future__ import annotations  # WHY: keep annotations stable during test collection.

from src.export.count_exporter import _MSP_OPS as COUNT_MSP_OPS  # WHY: safe count table under test.
from src.export.count_exporter import _ORG_OPS as COUNT_ORG_OPS  # WHY: safe count table under test.
from src.export.count_exporter import _SITE_OPS as COUNT_SITE_OPS  # WHY: safe count table under test.
from src.export.endpoint_family_exporter import ALL_STAGE_TWO_ENDPOINT_OPS  # WHY: safe family table under test.
from src.export.simple_endpoint_exporter import _MSP_OPS as SIMPLE_MSP_OPS  # WHY: safe simple table under test.
from src.export.simple_endpoint_exporter import _NONE_OPS as SIMPLE_NONE_OPS  # WHY: safe simple table under test.
from src.export.simple_endpoint_exporter import _ORG_OPS as SIMPLE_ORG_OPS  # WHY: safe simple table under test.
from src.export.simple_endpoint_exporter import _SITE_OPS as SIMPLE_SITE_OPS  # WHY: safe simple table under test.


def test_optimize_installer_rrm_is_not_in_safe_family_tables() -> None:
    """The radio optimization endpoint must stay out of safe endpoint families."""
    safe_family_tables = (  # WHY: issue #1366 covers every grouped safe endpoint table.
        COUNT_ORG_OPS,  # WHY: count menu 235 must not start radio optimization.
        COUNT_SITE_OPS,  # WHY: count menu 236 must not start radio optimization.
        COUNT_MSP_OPS,  # WHY: count menu 237 must not start radio optimization.
        SIMPLE_NONE_OPS,  # WHY: simple menu 259 must not start radio optimization.
        SIMPLE_ORG_OPS,  # WHY: simple menu 260 must not start radio optimization.
        SIMPLE_SITE_OPS,  # WHY: simple menu 261 must not start radio optimization.
        SIMPLE_MSP_OPS,  # WHY: simple menu 262 must not start radio optimization.
        ALL_STAGE_TWO_ENDPOINT_OPS,  # WHY: menus 263 through 268 must stay read-only.
    )
    operation_names = {entry.operation for table in safe_family_tables for entry in table}  # WHY: one set finds drift.
    assert "optimizeInstallerRrm" not in operation_names  # WHY: the endpoint changes live radio state.
