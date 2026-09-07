"""Prove a real SMIv2 parser accepts the generated module.

Every other check reads the MIB text with a regular expression. Only a
real parser proves that a monitoring system can load the file. This test
skips when `snmptranslate` is not on the machine (task T028).
"""

from __future__ import annotations

import shutil  # The tool lookup and the file copy both come from here.
import subprocess  # nosec B404 - the command name is fixed and no shell runs.
from pathlib import Path  # Path keeps the module name free of a separator.

import pytest  # The skip marker comes from pytest.

REPO_ROOT = Path(__file__).resolve().parents[2]  # The tests run from a temporary folder.
MIB_PATH = REPO_ROOT / "documentation" / "mibs" / "MISTHELPER-MIB.mib"  # The generated file.


def _snmptranslate_has_standard_mibs() -> bool:
    """Return True when snmptranslate can load the SNMPv2-SMI base module.

    Why:
        A CI runner may ship the binary without the standard MIB files.
        The test must skip in that case, not fail on a missing base module.
    """
    if shutil.which("snmptranslate") is None:  # The binary is absent, so skip.
        return False
    probe = subprocess.run(  # A real parse of the base module is the honest check.
        ["snmptranslate", "-m", "SNMPv2-SMI", "-Tp", "SNMPv2-SMI::enterprises"],
        capture_output=True,
        check=False,
    )
    return probe.returncode == 0  # The base module must load before any test MIB can.


@pytest.mark.skipif(
    not _snmptranslate_has_standard_mibs(),
    reason="snmptranslate or its standard MIBs are not on this machine",
)
def test_snmptranslate_parses_the_generated_mib(tmp_path: Path) -> None:
    """Prove Net-SNMP loads the module and prints the tree."""
    shutil.copy(MIB_PATH, tmp_path / "MISTHELPER-MIB.mib")  # The tool reads a whole folder of modules.
    command = [  # A fixed list keeps the shell out of the call.
        "snmptranslate",
        "-M",
        f"+{tmp_path}",
        "-m",
        "MISTHELPER-MIB",
        "-Tp",
        "MISTHELPER-MIB::mistHelperMIB",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603
    assert result.returncode == 0, result.stderr  # A parse error must fail the test loudly.
    assert "mistOrg" in result.stdout  # The tree must hold the org subtree by name.
