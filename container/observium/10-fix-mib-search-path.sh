#!/bin/bash
# Add the bundled IETF MIBs to the Net-SNMP search path on every container start.
#
# Why:
#   MISTHELPER-MIB.mib imports SNMPv2-SMI and SNMPv2-TC, the base definitions
#   every enterprise MIB needs for `enterprises`, `DisplayString`, and similar
#   building blocks. Debian ships no IETF MIB file with the `snmp` package, so
#   `mibdirs` in `/etc/snmp/snmp.conf` names only `/usr/share/snmp/mibs` and
#   `/opt/observium/mibs`. Observium already bundles the IETF set at
#   `/opt/observium/mibs/rfc`, but that folder is not on the search path, so
#   `snmptranslate` and `snmpwalk -m MISTHELPER-MIB` cannot resolve one name in
#   the MIB and report "Cannot adopt OID" for every entry.
#
#   This script runs on every container start, because `/etc/snmp/snmp.conf` is
#   not on a persistent volume. A manual fix inside a running container is lost
#   on the next `compose down`, and this project runs with no manual step.
#
# Where:
#   `my_init` (the container entrypoint) runs every executable file under
#   `/etc/my_init.d/` in name order before it starts Observium. This script
#   reaches that folder through a read-only bind mount in compose.yml.
set -e  # Stop on the first error, so a partial edit never reaches snmpd.conf.

SNMP_CONF="/etc/snmp/snmp.conf"  # The file that names the Net-SNMP MIB search path.
IETF_MIB_DIR="/opt/observium/mibs/rfc"  # The bundled IETF/IANA MIB set Observium already ships.
MARKER="# Written by 10-fix-mib-search-path.sh"  # Marks a file this script already wrote.

if grep -q "$MARKER" "$SNMP_CONF" 2>/dev/null; then  # A prior start on this same container already fixed the file.
    echo "[MIB-PATH] $SNMP_CONF already carries the fix. Nothing to do."
    exit 0
fi

# Overwrite the file outright instead of patching it. The base image ships this
# file with `mibs :` (disables every MIB) and `mibdirs` commented out, so a
# `sed` replace of an active `mibdirs` line silently matches nothing. Net-SNMP
# reads no other setting from this file that Observium depends on, so a full,
# deterministic rewrite is safe.
cat > "$SNMP_CONF" <<EOF
$MARKER
# Re-enable every MIB module. The base image disables all of them by default,
# because Debian ships no IETF MIB file under its own license.
mibs +ALL
# Search Observium's bundled vendor MIBs, then its bundled IETF/IANA set
# (SNMPv2-SMI, SNMPv2-TC, and similar), so MISTHELPER-MIB.mib resolves.
mibdirs /usr/share/snmp/mibs:/opt/observium/mibs:${IETF_MIB_DIR}
EOF
echo "[MIB-PATH] Rewrote $SNMP_CONF: enabled MIB loading and added $IETF_MIB_DIR to the search path."
