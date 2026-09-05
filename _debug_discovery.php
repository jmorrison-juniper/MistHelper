<?php
// Diagnostic: reproduce discovery-sensors-unix.inc.php's logic with visible output.
$config['mibs']['MISTHELPER-MIB']['mib_dir'] = 'mibs';  // Test fix: register our MIB's real directory.
echo "computed mibdirs: " . snmp_mib2mibdirs('MISTHELPER-MIB') . "\n";

$device = device_by_id_cache(6);
var_dump($device['device_id'], $device['hostname'], $device['os'], $device['os_group']);

$mist_probe = snmp_get_oid($device, '.1.3.6.1.4.1.8072.9999.9999.1.90.0', 'MISTHELPER-MIB');
echo "PROBE RESULT: ";
var_dump($mist_probe);
echo "is_numeric(fix_numeric): ";
var_dump(is_numeric(snmp_fix_numeric($mist_probe)));

echo "--- site walk (numeric OID) ---\n";
$rows2 = snmpwalk_cache_oid($device, '.1.3.6.1.4.1.8072.9999.9999.2.1', [], 'MISTHELPER-MIB');
echo "Row count (numeric): " . count($rows2) . "\n";
$first_key2 = array_key_first($rows2);
if ($first_key2 !== null) {
    print_r($rows2[$first_key2]);
}

echo "--- raw snmp_walk debug ---\n";
$raw = snmp_walk($device, 'mistSiteEntry', snmp_gen_options('snmpwalk', OBS_SNMP_ALL), 'MISTHELPER-MIB', NULL, OBS_SNMP_ALL);
var_dump($raw);
$raw2 = snmp_walk($device, '.1.3.6.1.4.1.8072.9999.9999.2.1', snmp_gen_options('snmpwalk', OBS_SNMP_ALL), 'MISTHELPER-MIB', NULL, OBS_SNMP_ALL);
var_dump($raw2);
