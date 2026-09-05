# Phase 1 discovery for the managing-observium skill. PowerShell replaces jq, which is not installed here.
param(
    [string]$Url = $(if ($env:OBSERVIUM_URL) { $env:OBSERVIUM_URL } else { 'http://localhost:8668' }),
    [string]$User = $(if ($env:OBSERVIUM_USER) { $env:OBSERVIUM_USER } else { 'observium' }),
    [string]$Pass = $env:OBSERVIUM_PASS
)

if (-not $Pass) { throw 'Set OBSERVIUM_PASS or pass -Pass.' }

$securePassword = ConvertTo-SecureString $Pass -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential($User, $securePassword)

function Get-ObsEndpoint {
    param([string]$Endpoint)
    try {
        Invoke-RestMethod -Uri "$Url/api/v0/$Endpoint" -Credential $credential `
            -Headers @{Accept = 'application/json' } -AllowUnencryptedAuthentication -TimeoutSec 30
    }
    catch {
        # An empty or failed response is reportable data, not a reason to retry.
        Write-Host "  request failed: $($_.Exception.Message)"
        return $null
    }
}

function Get-Values {
    param($Container)
    if ($null -eq $Container) { return @() }
    if ($Container -is [System.Collections.IEnumerable] -and $Container -isnot [string]) { return @($Container) }
    return @($Container.PSObject.Properties.Value)
}

Write-Host '=== Devices ==='
$deviceValues = Get-Values (Get-ObsEndpoint 'devices').devices
$deviceValues | Select-Object -First 25 device_id, hostname, os,
@{n = 'state'; e = { if ($_.status -eq '1') { 'UP' } else { 'DOWN' } } } | Format-Table -AutoSize

Write-Host '=== Device Groups ==='
Get-Values (Get-ObsEndpoint 'groups/device').groups |
    Select-Object -First 15 group_id, group_name | Format-Table -AutoSize

Write-Host '=== Port Count by Device ==='
Get-Values (Get-ObsEndpoint 'ports').ports | Group-Object device_id |
    Sort-Object Count -Descending | Select-Object -First 15 Name, Count | Format-Table -AutoSize

Write-Host '=== Alert Checks ==='
Get-Values (Get-ObsEndpoint 'alerts/checks').checks |
    Select-Object -First 15 alert_test_id, alert_name, entity_type | Format-Table -AutoSize
