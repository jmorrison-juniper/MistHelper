<?php
/**
 * Discover every populated column of MISTHELPER-MIB's three tables as native
 * Observium sensors: sites, devices, and service level expectations (SLE).
 *
 * Why:
 *   The org-level scalars are few and fixed in number, so
 *   container/observium/20-add-mist-static-sensors.sh registers them through
 *   config.php's documented "static sensors" mechanism
 *   (https://docs.observium.org/statics/). The three tables below hold one
 *   row per Mist site, per Mist device, and per service level expectation.
 *   Those row counts change over time (a NOC adds a site, Mist retires a
 *   device), so a fixed config.php list would drift out of date. This file
 *   walks each table at discovery time instead, the same pattern every
 *   vendor file in this directory (for example checkpoint-mib.inc.php) uses
 *   for a device-reported table.
 *
 * Where this file runs:
 *   includes/discovery/sensors.inc.php loads one file per MIB name the
 *   device is known to support, and it ALSO always tries
 *   includes/discovery/sensors/<os>.inc.php and
 *   includes/discovery/sensors/<os_group>.inc.php ("Bodge for
 *   <os|os_group>[/*].inc.php loading" in include-dir-mib.inc.php). This
 *   device reports OS group "unix", so this file is named unix.inc.php and
 *   runs for every Linux/Unix device Observium discovers -- the guard clause
 *   immediately below is why that is safe.
 *
 * Polling:
 *   No polling-side file is needed. includes/polling/sensors.inc.php reads
 *   every sensor's own stored OID from the `sensors` table and re-polls it
 *   with a plain SNMP get, whether the row came from this file or from
 *   config.php. Discovery therefore fully owns this feature.
 */

// Guard: only continue for a device that answers the Mist scrape-health
// scalar. Every other Linux/Unix device Observium discovers reaches this
// file too, and one fast snmpget is the cheapest way to skip them.
$mist_probe = snmp_get_oid($device, '.1.3.6.1.4.1.8072.9999.9999.1.90.0', 'MISTHELPER-MIB');
if ($mist_probe === FALSE || !is_numeric(snmp_fix_numeric($mist_probe))) {
    return;
}

$mist_base = '.1.3.6.1.4.1.8072.9999.9999';  // The base OID every MISTHELPER-MIB reading sits under.

/**
 * Walk one MISTHELPER-MIB table and register a sensor for every numeric
 * column of every row.
 *
 * @param array  $device       The Observium device array.
 * @param string $base_oid     The MISTHELPER-MIB base OID (passed in rather than read from a
 *                              global, because this file runs inside whatever function
 *                              discovery.php uses to process one device, not the true global
 *                              scope, and `global` only ever reaches the true global scope).
 * @param string $entry_name   The MIB table entry name, for example 'mistSiteEntry'.
 * @param int    $subtree      The subtree number below $base_oid (2 = site, 3 = device, 4 = sle).
 * @param string $identity_key The array key of $entry_name that names the row (a site name, a device name, an SLE label).
 * @param string $row_label    A short word for the sensor description, for example 'Site'.
 * @param array  $columns      Map of column name => [column number, sensor class, multiplier].
 */
if (!function_exists('mist_discover_table')) {  // Guard: this file is include()-d, not include_once()-d, once
    // per Linux/Unix device a bulk `discovery.php` run touches, and a second `function` declaration in the
    // same PHP process is a fatal "Cannot redeclare" error.
function mist_discover_table($device, $base_oid, $entry_name, $subtree, $identity_key, $row_label, $columns)
{
    $rows = snmpwalk_cache_oid($device, $entry_name, [], 'MISTHELPER-MIB');
    foreach ($rows as $index => $row) {
        $identity = $row[$identity_key] ?? ("#" . $index);  // Fall back to the row number if the name is missing.
        foreach ($columns as $column_name => $spec) {
            [$column_number, $sensor_class, $multiplier] = $spec;
            if (!isset($row[$column_name]) || !is_numeric(snmp_fix_numeric($row[$column_name]))) {
                continue;  // This org's Mist Cloud data has no reading for this cell right now.
            }
            $oid   = "$base_oid.$subtree.1.$column_number.$index";
            $descr = "$row_label $identity: " . mist_readable_column($column_name);
            if ($sensor_class === 'status') {
                // An up/down (or similar named-state) reading belongs under Observium's Status
                // entity, not a Gauge sensor: it moves the row out of the far larger Gauge
                // listing, and Observium already colors a "down" status red on its own.
                //
                // The mib argument here MUST be the literal string 'STATIC', not
                // 'MISTHELPER-MIB'. get_states_definition() (includes/entities/status.inc.php)
                // reads $config['status']['static_states'][$type] only on that exact
                // 'STATIC' fast path -- the same path the documented static-status
                // feature (https://docs.observium.org/statics/) uses for a custom state
                // type. Any other mib value sends this to the standard MIB-derived state
                // lookup, which finds nothing for a type this MIB never declared, and the
                // status silently never gets created.
                discover_status_ng($device, 'STATIC', $column_name, $oid, $index, 'mist-device-up', $descr, $row[$column_name]);
            } else {
                discover_sensor_ng($device, $sensor_class, 'MISTHELPER-MIB', $column_name, $oid, $index, $descr, $multiplier, $row[$column_name]);
            }
        }
    }
}
}  // End the function_exists() guard for mist_discover_table().

/**
 * Turn a MIB column name into a short, human sensor description.
 *
 * Why: 'mistSiteApsConnected' means little to a NOC engineer at 3am.
 * 'APs connected' does not need the MIB open to read.
 *
 * @param string $column_name The MIB column name (a snmpwalk_cache_oid() array key).
 *
 * @return string The trailing part of the name, spaced out.
 */
if (!function_exists('mist_readable_column')) {  // Same reason as the guard above.
function mist_readable_column($column_name)
{
    $short = preg_replace('/^mist(Site|Device|Sle)/', '', $column_name);  // Drop the scope prefix.
    $short = preg_replace('/(?<!^)[A-Z]/', ' $0', $short);  // Split CamelCase into words.
    return trim($short);
}
}  // End the function_exists() guard for mist_readable_column().


// Sites: nine numeric columns, one row for every site the org holds.
mist_discover_table($device, $mist_base, 'mistSiteEntry', 2, 'mistSiteInfo', 'Site', [
    'mistSiteAps'               => [2, 'gauge', 1],
    'mistSiteApsConnected'      => [3, 'gauge', 1],
    'mistSiteSwitches'          => [4, 'gauge', 1],
    'mistSiteSwitchesConnected' => [5, 'gauge', 1],
    'mistSiteGateways'          => [6, 'gauge', 1],
    'mistSiteGatewaysConnected' => [7, 'gauge', 1],
    'mistSiteDevices'           => [8, 'gauge', 1],
    'mistSiteDevicesConnected'  => [9, 'gauge', 1],
    'mistSiteClients'           => [10, 'gauge', 1],
]);

// Devices: every access point, switch, and gateway the org holds. Some
// columns (client count, CPU, memory, power, temperature, byte counters)
// have no reading for this org's device mix today; the loop above skips a
// cell with no value rather than register a broken sensor, and it picks
// the column up on its own the day Mist starts returning it.
//
// mistDeviceUp uses the 'status' class (a special case mist_discover_table()
// recognizes above), not 'gauge', because an up/down reading is a named
// state, and Observium's own Status entity already colors "down" red.
mist_discover_table($device, $mist_base, 'mistDeviceEntry', 3, 'mistDeviceInfo', 'Device', [
    'mistDeviceUp'                                 => [2, 'status', 1],
    'mistDeviceUptimeSeconds'                       => [3, 'age', 1],
    'mistDeviceLastSeenTimestampSeconds'            => [4, 'gauge', 1],
    'mistDeviceClients'                             => [5, 'gauge', 1],
    'mistDeviceCpuUtilizationRatio'                 => [6, 'gauge', 0.0001],
    'mistDeviceMemoryUsedBytes'                     => [7, 'gauge', 1],
    'mistDeviceMemoryTotalBytes'                    => [8, 'gauge', 1],
    'mistDevicePowerBudgetWatts'                    => [9, 'gauge', 1],
    'mistDeviceCpuTemperatureCelsius'                => [10, 'temperature', 1],
    'mistDeviceReceivedBytesTotal'                   => [11, 'gauge', 1],
    'mistDeviceTransmittedBytesTotal'                => [12, 'gauge', 1],
    'mistDeviceCertificateExpiryTimestampSeconds'    => [13, 'gauge', 1],
]);

// Service level expectations: one row for each Mist SLE category (coverage,
// roaming, throughput, and so on). The row identity is mistSleIdentity, not
// an 'info' metric, because the catalog holds no text metric for this scope.
//
// mistSleRatio uses the 'quality_factor' class, not 'gauge', because a
// service level ratio is a quality measurement, and giving it its own class
// both reads correctly and moves it out of the Gauge listing.
mist_discover_table($device, $mist_base, 'mistSleEntry', 4, 'mistSleIdentity', 'SLE', [
    'mistSleUserMinutesTotal' => [1, 'gauge', 1],
    'mistSleUserMinutesOk'    => [2, 'gauge', 1],
    'mistSleRatio'            => [3, 'quality_factor', 0.0001],
]);

unset($mist_probe, $mist_base);

// EOF
