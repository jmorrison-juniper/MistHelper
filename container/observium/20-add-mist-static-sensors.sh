#!/bin/bash
# Register the Mist Cloud health metrics as native Observium "static sensors."
#
# Why:
#   MISTHELPER-MIB.mib installs correctly and Net-SNMP tools translate every OID
#   under it (documented and verified separately). It still carries no built-in
#   Observium discovery/polling code, because Observium Community Edition ships
#   a closed, pre-compiled catalog of vendor MIBs (see /os/ in the web UI, and
#   /opt/observium/includes/definitions/definitions.dat) that only Observium's
#   own build process can extend. The one CE feature meant for exactly this
#   case, "Custom OID" (https://docs.observium.org/customoid/), is a
#   Subscription Edition feature and is not present in this image.
#
#   Observium's own documentation names the Community Edition equivalent:
#   "static sensors" (https://docs.observium.org/statics/). The discovery code
#   for it already ships in CE, unconditionally, at
#   includes/discovery/sensors.inc.php ("Detect static sensors" block). An
#   operator turns it on by adding entries to config.php, the same file the
#   web-based settings page writes to, so this is a supported extension point
#   and not a patch to Observium's own code.
#
#   This script writes that config.php block, so a NOC engineer never has to
#   type it by hand, and it survives every `compose down` / `compose up`.
#
# Where:
#   `my_init` runs every executable file under /etc/my_init.d/ in name order
#   before it starts Observium. This script reaches that folder through a
#   read-only bind mount in compose.yml. config.php itself lives on the
#   `misthelper-observium-config` volume, so a first-time write here persists
#   across every later restart without repeating the work (see the marker
#   check below).
set -e  # Stop on the first error, so a partial edit never reaches config.php.

CONFIG_PHP="/config/config.php"  # The persisted Observium settings file (symlinked from /opt/observium/config.php).
MARKER="MISTHELPER_STATIC_SENSORS_V2"  # Bumped only if the sensor set below changes shape.

if [ ! -f "$CONFIG_PHP" ]; then  # A missing file means Observium has not finished its first boot yet.
    echo "[MIST-SENSORS] ERROR: $CONFIG_PHP not found. Observium may not be initialized yet." >&2
    exit 1
fi

if grep -q "$MARKER" "$CONFIG_PHP"; then  # A prior start already appended this block.
    echo "[MIST-SENSORS] $CONFIG_PHP already carries the Mist static sensors. Nothing to do."
    exit 0
fi

# Append a self-contained PHP block. It looks the device up by hostname at
# config load time instead of a hard-coded device_id, because device_id
# changes if the device is ever deleted and re-added.
cat >> "$CONFIG_PHP" <<'EOF'

// $MARKER
// Static sensors for the MistHelper Cloud metrics gateway (see
// container/observium/20-add-mist-static-sensors.sh for the full reason).
// Looked up by hostname, not a fixed device_id, so a later re-add of the
// device does not require a manual edit here.
$mist_device_id = NULL;
// mysqli treats the literal string "localhost" as a request for a Unix socket,
// not TCP. This image runs MariaDB with no socket file, only TCP on 127.0.0.1,
// so a plain mysqli_connect($config['db_host'], ...) fails with "No such file
// or directory" even though Observium's own framework connects fine (it forces
// TCP internally). Normalize the host here instead of guessing its method.
$mist_db_host = ($config['db_host'] === 'localhost') ? '127.0.0.1' : $config['db_host'];
$mist_db_link = @mysqli_connect($mist_db_host, $config['db_user'], $config['db_pass'], $config['db_name']);
if ($mist_db_link) {
    $mist_result = mysqli_query($mist_db_link, "SELECT device_id FROM devices WHERE hostname = 'misthelper-app' LIMIT 1");
    if ($mist_result && ($mist_row = mysqli_fetch_assoc($mist_result))) {
        $mist_device_id = (int)$mist_row['device_id'];
    }
    mysqli_close($mist_db_link);
}
if ($mist_device_id) {
    // mistOrg subtree of MISTHELPER-MIB.mib: .1.3.6.1.4.1.8072.9999.9999.1.<column>.0
    $mist_base = '.1.3.6.1.4.1.8072.9999.9999.1';
    $config['sensors']['static'][] = ['device_id' => $mist_device_id, 'class' => 'gauge', 'oid' => $mist_base . '.2.0', 'descr' => 'Mist sites', 'multiplier' => 1];
    $config['sensors']['static'][] = ['device_id' => $mist_device_id, 'class' => 'gauge', 'oid' => $mist_base . '.5.0', 'descr' => 'Mist devices connected', 'multiplier' => 1];
    $config['sensors']['static'][] = ['device_id' => $mist_device_id, 'class' => 'gauge', 'oid' => $mist_base . '.6.0', 'descr' => 'Mist devices disconnected', 'multiplier' => 1];
    $config['sensors']['static'][] = ['device_id' => $mist_device_id, 'class' => 'gauge', 'oid' => $mist_base . '.90.0', 'descr' => 'Mist scrape success', 'multiplier' => 1];
    $config['sensors']['static'][] = ['device_id' => $mist_device_id, 'class' => 'age', 'oid' => $mist_base . '.91.0', 'descr' => 'Mist scrape age', 'multiplier' => 1];
}
unset($mist_device_id, $mist_db_host, $mist_db_link, $mist_result, $mist_row, $mist_base);
// End MistHelper static sensors
EOF
sed -i "s/\$MARKER/$MARKER/" "$CONFIG_PHP"  # Turn the literal placeholder into the real marker the check above reads.
echo "[MIST-SENSORS] Appended the Mist static sensor block to $CONFIG_PHP."
